"""pgtrib tests, such as they are"""

import importlib.util
import os
import sys

import pytest

from pygwin.pgtribs import (
    pgtrib_context,
    pgtribs_load,
    pgtribs_loaded,
    pgtribs_main,
    pgtribs_reload,
    pgtribs_unload,
)


@pytest.fixture
def tmpmod(tmpdir):
    """
    Same as tmpdir but also adds/removes it to the front of sys.path.

    Also cleans out any modules loaded as part of the test.
    """
    sys.path.insert(0, str(tmpdir))
    loadedmods = set(sys.modules.keys())
    try:
        yield tmpdir
    finally:
        del sys.path[0]
        newmods = set(sys.modules.keys()) - loadedmods
        for m in newmods:
            del sys.modules[m]


def test_noall(tmpmod):
    """
    Tests what get's exported from a module without __all__
    """

    with tmpmod.mkdir("pgtrib").join("spameggs.py").open("w") as x:
        x.write(
            """
spam = 1
eggs = 2
_foobar = 3
"""
        )

    ctx = pgtrib_context("spameggs")
    assert ctx == {"spam": 1, "eggs": 2}


def test_withall(tmpmod):
    """
    Tests what get's exported from a module with __all__
    """

    with tmpmod.mkdir("pgtrib").join("spameggs.py").open("w") as x:
        x.write(
            """
__all__ = 'spam', '_foobar'
spam = 1
eggs = 2
_foobar = 3
"""
        )

    ctx = pgtrib_context("spameggs")
    assert ctx == {"spam": 1, "_foobar": 3}


def test_xshpgtrib(tmpmod):
    """
    Test that .xsh pgtribs are loadable
    """
    with tmpmod.mkdir("pgtrib").join("script.xsh").open("w") as x:
        x.write(
            """
hello = 'world'
"""
        )

    ctx = pgtrib_context("script")
    assert ctx == {"hello": "world"}


def test_pgtrib_load(tmpmod):
    """
    Test that .xsh pgtribs are loadable
    """
    with tmpmod.mkdir("pgtrib").join("script.xsh").open("w") as x:
        x.write(
            """
hello = 'world'
"""
        )

    pgtribs_load(["script"])
    assert "script" in pgtribs_loaded()


def test_pgtrib_load_after_dir_cached(tmpmod):
    """A pgtrib file written after importlib already cached its parent
    directory must still load.

    ``pgtribs_load`` calls ``importlib.invalidate_caches()`` first.
    Regression for a filesystem-dependent flake: ``FileFinder`` keeps a
    per-directory cache keyed by mtime, and on a coarse-mtime filesystem a
    freshly written pgtrib could be missed, so the load silently did
    nothing.
    """
    xdir = tmpmod.mkdir("pgtrib")
    # Prime importlib's FileFinder cache while the directory is empty.
    assert importlib.util.find_spec("pgtrib.latecomer") is None
    xdir.join("latecomer.py").write("hello = 'world'\n")
    # Emulate a coarse-mtime filesystem: tell the cached finder the
    # directory is already up to date so it will not rescan on its own.
    finder = sys.path_importer_cache.get(str(xdir))
    if finder is not None:
        finder._path_mtime = os.stat(str(xdir)).st_mtime
        # Sanity check: without invalidation the new file stays invisible.
        assert importlib.util.find_spec("pgtrib.latecomer") is None

    pgtribs_load(["latecomer"])
    assert "latecomer" in pgtribs_loaded()


def test_pgtrib_unload(tmpmod, xession):
    with tmpmod.mkdir("pgtrib").join("script.py").open("w") as x:
        x.write(
            """
hello = 'world'

def _unload_pgtrib_(xsh): del xsh.ctx['hello']
"""
        )

    pgtribs_load(["script"])
    assert "script" in pgtribs_loaded()
    assert "hello" in xession.ctx
    pgtribs_unload(["script"])
    assert "script" not in pgtribs_loaded()
    assert "hello" not in xession.ctx


def test_pgtrib_reload(tmpmod, xession):
    with tmpmod.mkdir("pgtrib").join("script.py").open("w") as x:
        x.write(
            """
hello = 'world'

def _unload_pgtrib_(xsh): del xsh.ctx['hello']
"""
        )

    pgtribs_load(["script"])
    assert "script" in pgtribs_loaded()
    assert xession.ctx["hello"] == "world"

    with tmpmod.join("pgtrib").join("script.py").open("w") as x:
        x.write(
            """
hello = 'world1'

def _unload_pgtrib_(xsh): del xsh.ctx['hello']
"""
        )
    pgtribs_reload(["script"])
    assert "script" in pgtribs_loaded()
    assert xession.ctx["hello"] == "world1"


def test_pgtrib_load_dashed(tmpmod):
    """
    Test that .xsh pgtribs are loadable
    """
    with tmpmod.mkdir("pgtrib").join("scri-pt.xsh").open("w") as x:
        x.write(
            """
hello = 'world'
"""
        )

    pgtribs_load(["scri-pt"])
    assert "scri-pt" in pgtribs_loaded()


def test_pgtrib_list(xession, capsys):
    pgtribs_main(["list"])
    out, err = capsys.readouterr()
    assert "coreutils" in out


def test_pgtrib_info(xession, capsys):
    pgtribs_main(["info", "coreutils"])
    out, _ = capsys.readouterr()
    assert "Name" in out and "coreutils" in out
    assert "Source" in out and "pgtrib.coreutils" in out
    assert "coreutils.py" in out  # file path
    assert "Description" in out
    assert "Loaded" in out


def test_pgtrib_info_unknown(xession, capsys):
    rc = pgtribs_main(["info", "nope-this-pgtrib-does-not-exist"])
    out, _ = capsys.readouterr()
    assert "not installed" in out
    assert rc == 1


def test_pgtrib_info_xsh_file(tmpmod, xession, capsys):
    """`.xsh` pgtribs aren't visible to ``importlib.util.find_spec``.
    ``pgtrib info`` must fall back to scanning the namespace package's
    physical locations and report the actual file path — not "(builtin)".
    """
    tmpmod.mkdir("pgtrib").join("xshmod.xsh").write("echo hi\n")

    pgtribs_main(["info", "xshmod"])
    out, _ = capsys.readouterr()
    assert "xshmod.xsh" in out
    assert "(builtin)" not in out
