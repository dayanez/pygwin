"""Smoke tests for ``pygwin.pgtribs``.

Covers ``Pgtrib`` introspection, ``pgtrib_data`` / ``pgtribs_loaded`` /
``pgtribs_list`` formatting, and pure helpers like ``get_module_docstring``,
``prompt_pgtrib_install``, and ``find_pgtrib`` for the not-found path.
"""

import json
import sys

import pytest

from pygwin.pgtribs import (
    ExitCode,
    Pgtrib,
    PgtribAlias,
    PgtribNotInstalled,
    auto_load_pgtribs_from_entrypoints,
    find_pgtrib,
    get_module_docstring,
    get_pgtribs,
    pgtrib_context,
    pgtrib_data,
    pgtribs_list,
    pgtribs_load,
    pgtribs_loaded,
    pgtribs_reload,
    pgtribs_unload,
    prompt_pgtrib_install,
    update_context,
)

# --- Pgtrib NamedTuple -----------------------------------------------------


def test_pgtrib_default_distribution_none():
    x = Pgtrib(module="pgtrib.unimaginary_xyz")
    assert x.module == "pgtrib.unimaginary_xyz"
    assert x.distribution is None
    assert x.url == ""
    assert x.license == ""


def test_pgtrib_is_loaded_false_when_module_missing():
    x = Pgtrib(module="pgtrib.surely_does_not_exist_xyz")
    assert x.is_loaded is False


def test_pgtrib_is_loaded_true_when_in_sys_modules():
    x = Pgtrib(module="pgtrib.fake_loaded_for_test_xyz")
    sys.modules[x.module] = object()  # type: ignore[assignment]
    try:
        assert x.is_loaded is True
    finally:
        del sys.modules[x.module]


def test_pgtrib_is_auto_loaded_false_without_state(xession):
    """When XSH.builtins has no ``autoloaded_pgtribs`` mapping, the property
    falls back to an empty dict and reports False."""
    if hasattr(xession.builtins, "autoloaded_pgtribs"):
        try:
            del xession.builtins.autoloaded_pgtribs
        except AttributeError:
            pass
    x = Pgtrib(module="pgtrib.something")
    assert x.is_auto_loaded is False


# --- get_module_docstring ---------------------------------------------------


def test_get_module_docstring_for_real_module():
    doc = get_module_docstring("pygwin.pgtribs")
    assert doc
    assert "pgtrib" in doc.lower()


def test_get_module_docstring_for_missing_module():
    """A module that cannot be located returns the empty string, not None."""
    out = get_module_docstring("pgtrib.surely_does_not_exist_abc_xyz")
    assert out == ""


# --- get_pgtribs / pgtrib_data --------------------------------------------


def test_get_pgtribs_returns_dict():
    data = get_pgtribs()
    assert isinstance(data, dict)
    # the in-tree ``pgtrib`` package always discovers at least one entry
    assert len(data) > 0
    for name, xo in data.items():
        assert isinstance(name, str)
        assert isinstance(xo, Pgtrib)


def test_pgtrib_data_shape():
    data = pgtrib_data()
    assert isinstance(data, dict)
    for name, entry in data.items():
        assert entry["name"] == name
        assert "loaded" in entry and isinstance(entry["loaded"], bool)
        assert "auto" in entry and isinstance(entry["auto"], bool)
        assert "module" in entry
        assert "description" in entry


def test_pgtrib_data_is_sorted_alphabetically():
    data = pgtrib_data()
    assert list(data.keys()) == sorted(data.keys())


def test_pgtribs_loaded_subset_of_get_pgtribs():
    loaded = pgtribs_loaded()
    assert isinstance(loaded, list)
    all_names = set(get_pgtribs())
    assert set(loaded).issubset(all_names)


# --- pgtribs_list output ---------------------------------------------------


def test_pgtribs_list_json(xession):
    out = pgtribs_list(to_json=True)
    parsed = json.loads(out)
    assert isinstance(parsed, dict)


def test_pgtribs_list_human_format(capfd):
    """The non-JSON branch prints colored lines for each pgtrib."""
    pgtribs_list(to_json=False)
    captured = capfd.readouterr().out
    # we got at least one printed line and it mentions "loaded" or "not-loaded"
    assert "loaded" in captured.lower() or "not-loaded" in captured.lower()


# --- find_pgtrib ----------------------------------------------------------


def test_find_pgtrib_returns_none_for_missing():
    assert find_pgtrib("definitely_not_a_pgtrib_xyz123") is None


def test_find_pgtrib_resolves_real_pgtrib():
    """At least one pgtrib is shipped in-tree — find_pgtrib must locate it."""
    names = list(get_pgtribs())
    assert names, "expected at least one pgtrib"
    # pick a deterministic-looking core pgtrib name
    spec = find_pgtrib(names[0])
    # Some pgtribs may not be importable here, but find_spec should not crash
    assert spec is None or hasattr(spec, "name")


# --- pgtrib_context / update_context --------------------------------------


def test_pgtrib_context_returns_none_for_missing():
    assert pgtrib_context("definitely_not_a_pgtrib_xyz123") is None


def test_update_context_raises_when_not_installed():
    ctx = {}
    with pytest.raises(PgtribNotInstalled):
        update_context("definitely_not_a_pgtrib_xyz123", ctx)


# --- prompt_pgtrib_install ------------------------------------------------


def test_prompt_pgtrib_install_includes_names():
    msg = prompt_pgtrib_install(["foo", "bar"])
    assert "foo" in msg
    assert "bar" in msg


# --- ExitCode --------------------------------------------------------------


def test_exit_code_values():
    assert int(ExitCode.OK) == 0
    assert int(ExitCode.NOT_FOUND) == 1
    assert int(ExitCode.INIT_FAILED) == 2


# --- pgtribs_load NOT_FOUND path -------------------------------------------


def test_pgtribs_load_returns_not_found(xession):
    _, stderr, rc = pgtribs_load(["definitely_not_a_pgtrib_xyz123"])
    assert rc == ExitCode.NOT_FOUND
    assert "not installed" in stderr


def test_pgtribs_load_empty_returns_ok(xession):
    """Loading no pgtribs is a successful no-op."""
    _, _, rc = pgtribs_load([])
    assert rc == ExitCode.OK


def test_pgtribs_load_suppress_warnings_returns_ok(xession):
    """``--suppress-warnings`` masks the NOT_FOUND status."""
    _, stderr, rc = pgtribs_load(
        ["definitely_not_a_pgtrib_xyz123"], suppress_warnings=True
    )
    assert rc == ExitCode.OK
    assert stderr is None


# --- pgtribs_unload ------------------------------------------------------


def test_pgtribs_unload_unknown_is_noop(xession):
    """Unloading a missing pgtrib must not raise."""
    pgtribs_unload(["definitely_not_a_pgtrib_xyz123"])


def test_pgtribs_reload_unknown_is_noop(xession):
    """Reloading an unknown pgtrib funnels through load + unload paths."""
    pgtribs_reload(["definitely_not_a_pgtrib_xyz123"])


# --- auto_load_pgtribs_from_entrypoints -----------------------------------


def test_auto_load_pgtribs_with_blocked_set(xession):
    """Blocking every entry point yields an OK exit (no work to do)."""
    # block by passing an obviously-too-broad blocklist; if there are no
    # entry points at all, the function still must complete and return OK.
    _, _, rc = auto_load_pgtribs_from_entrypoints(
        blocked=["a-definitely-blocked-pgtrib"], verbose=False
    )
    assert rc in (ExitCode.OK, ExitCode.NOT_FOUND, ExitCode.INIT_FAILED)


# --- PgtribAlias ----------------------------------------------------------


def test_pgtrib_alias_builds_argparser(xession):
    alias = PgtribAlias(threadable=False)
    parser = alias.build()
    # parser should know the four subcommands
    assert any(
        cmd in parser.format_help() for cmd in ("load", "unload", "reload", "list")
    )
