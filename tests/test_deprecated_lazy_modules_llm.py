"""Smoke tests for the deprecated ``pygwin.lazyimps`` / ``pygwin.lazyjson`` shims.

Both modules emit a DeprecationWarning on import and re-export the names from
``pygwin.lib.lazyimps`` / ``pygwin.lib.lazyjson``. The shims exist purely so old
``from pygwin.lazyimps import …`` user code keeps working.
"""

import importlib
import sys
import warnings


def _reimport(name):
    """Drop ``name`` from sys.modules so the import warning fires again."""
    sys.modules.pop(name, None)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        mod = importlib.import_module(name)
    return mod, caught


def test_lazyimps_shim_warns_and_reexports():
    mod, caught = _reimport("pygwin.lazyimps")
    assert any(issubclass(w.category, DeprecationWarning) for w in caught)
    # everything that lives in pygwin.lib.lazyimps is now reachable via the shim
    from pygwin.lib import lazyimps as canonical

    for name in ("pygments", "pyghooks", "pty", "termios"):
        if hasattr(canonical, name):
            assert getattr(mod, name) is getattr(canonical, name)


def test_lazyjson_shim_warns_and_reexports():
    mod, caught = _reimport("pygwin.lazyjson")
    assert any(issubclass(w.category, DeprecationWarning) for w in caught)
    from pygwin.lib import lazyjson as canonical

    # the public API symbols all show up on the shim
    for name in ("LazyJSON", "LJNode", "ljdump", "ljload"):
        if hasattr(canonical, name):
            assert getattr(mod, name) is getattr(canonical, name)


def test_lazyimps_shim_docstring_marks_deprecation():
    """The shim's module docstring tells users which canonical path to import."""
    mod, _ = _reimport("pygwin.lazyimps")
    assert mod.__doc__ is not None
    assert "DEPRECATED" in mod.__doc__.upper()


def test_lazyjson_shim_docstring_marks_deprecation():
    mod, _ = _reimport("pygwin.lazyjson")
    assert mod.__doc__ is not None
    assert "DEPRECATED" in mod.__doc__.upper()
