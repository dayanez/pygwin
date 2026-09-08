"""Tests for the ``autotune`` xontrib: detecting known-heavy commands after
they spawn, nudging their priority down, and reversing it via
``pygwin-tune``.
"""

import os
import sys
import types

import pytest

import pygwin.platform_info as xp
from xontrib import autotune


@pytest.fixture(autouse=True)
def _clear_state_after():
    yield
    autotune._original_priority.clear()


def _fake_spec(binary_loc, alias=None):
    return types.SimpleNamespace(binary_loc=binary_loc, alias=alias)


def _fake_proc(pid):
    return types.SimpleNamespace(pid=pid)


def test_basename_no_exe_strips_extension_and_lowercases():
    assert autotune._basename_no_exe(r"C:\tools\FFMPEG.EXE") == "ffmpeg"
    assert autotune._basename_no_exe("/usr/bin/gcc") == "gcc"


def test_never_touches_pygwins_own_pid(monkeypatch):
    """The single most important guard: ProcProxy reuses os.getpid() for
    unthreadable callable aliases. Renicing that would deprioritize the
    whole shell, not some child process. Fakes psutil.Process to explode
    if it's ever called, so the guard is proven, not just plausible."""

    def _boom(pid):
        raise AssertionError(f"psutil.Process must never be called for {pid}")

    monkeypatch.setitem(sys.modules, "psutil", types.SimpleNamespace(Process=_boom))
    spec = _fake_spec(binary_loc=r"C:\bin\ffmpeg.exe")
    proc = _fake_proc(os.getpid())
    autotune._on_post_spec_run(spec=spec, proc=proc)
    assert autotune._original_priority == {}


def test_skips_when_proc_has_no_pid():
    spec = _fake_spec(binary_loc=r"C:\bin\ffmpeg.exe")
    proc = _fake_proc(None)
    autotune._on_post_spec_run(spec=spec, proc=proc)
    assert autotune._original_priority == {}


def test_skips_callable_aliases():
    spec = _fake_spec(binary_loc=None, alias=lambda args: None)
    proc = _fake_proc(99999)
    autotune._on_post_spec_run(spec=spec, proc=proc)
    assert autotune._original_priority == {}


def test_skips_commands_not_on_the_heavy_list():
    spec = _fake_spec(binary_loc=r"C:\bin\notepad.exe")
    proc = _fake_proc(99999)
    autotune._on_post_spec_run(spec=spec, proc=proc)
    assert autotune._original_priority == {}


def test_skips_when_psutil_missing(monkeypatch):
    monkeypatch.setitem(sys.modules, "psutil", None)
    spec = _fake_spec(binary_loc=r"C:\bin\ffmpeg.exe")
    proc = _fake_proc(99999)
    autotune._on_post_spec_run(spec=spec, proc=proc)
    assert autotune._original_priority == {}


def test_lowers_priority_of_a_real_heavy_command():
    """Runs this test process's own interpreter as a stand-in: spawn a real
    child, point autotune at its own name via a monkeypatched heavy-list
    entry, and confirm its actual OS priority changes.

    Restoring it back is only unconditionally verified on Windows. On
    POSIX, lowering niceness (this feature's whole first move) never needs
    privilege, but raising it back toward the original value afterward
    does: an unprivileged process cannot un-nice itself without
    CAP_SYS_NICE or root. Running as root in CI would make the restore
    assertion pass for the wrong reason (privilege, not correctness), so
    this only asserts full restore round-trips on Windows, and asserts the
    honest failure path (a nonzero return code, the niceness left
    unchanged) on POSIX when not running as root.
    """
    import subprocess
    import time

    import psutil

    can_restore = xp.ON_WINDOWS or (hasattr(os, "geteuid") and os.geteuid() == 0)

    proc = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(5)"],
    )
    try:
        time.sleep(0.2)  # let it actually start
        exe_name = autotune._basename_no_exe(sys.executable)
        heavy = frozenset(autotune.DEFAULT_HEAVY_COMMANDS | {exe_name})
        original_class = psutil.Process(proc.pid).nice()

        spec = _fake_spec(binary_loc=sys.executable)
        _real_heavy_commands = autotune._heavy_commands
        autotune._heavy_commands = lambda: heavy
        try:
            autotune._on_post_spec_run(spec=spec, proc=proc)
        finally:
            autotune._heavy_commands = _real_heavy_commands

        assert proc.pid in autotune._original_priority
        assert autotune._original_priority[proc.pid] == original_class
        lowered = psutil.Process(proc.pid).nice()
        # Not `lowered != original_class`: some CI runners already start
        # child processes at (or below) the target lowered value, which
        # would make that comparison vacuously fail even though autotune
        # did exactly what it was supposed to. Assert the real thing this
        # feature promises instead: the process ends up at the specific
        # lowered value, whatever it started at.
        assert lowered == autotune._lowered_priority_value(psutil)

        rc = autotune._tune(["restore", str(proc.pid)])
        restored = psutil.Process(proc.pid).nice()
        if can_restore:
            assert rc == 0
            assert restored == original_class
        else:
            assert rc == 1
            assert restored == lowered
    finally:
        proc.kill()
        proc.wait(timeout=5)


def test_tune_list_reports_nothing_when_empty(capsys):
    rc = autotune._tune([])
    assert rc == 0
    assert "nothing has been auto-tuned" in capsys.readouterr().out


def test_tune_restore_unknown_pid_reports_it(capsys):
    rc = autotune._tune(["restore", "424242"])
    assert rc == 1
    assert "was not auto-tuned" in capsys.readouterr().out


def test_tune_without_psutil(monkeypatch, capsys):
    monkeypatch.setitem(sys.modules, "psutil", None)
    rc = autotune._tune([])
    assert rc == 1
    assert "psutil is not installed" in capsys.readouterr().out


def test_load_xontrib_registers_handler_and_alias(xession):
    autotune._load_xontrib_(xession)
    try:
        assert autotune._on_post_spec_run in xession.builtins.events.on_post_spec_run
        assert "pygwin-tune" in xession.aliases
    finally:
        autotune._unload_xontrib_(xession)


def test_unload_xontrib_removes_handler_and_alias(xession):
    autotune._load_xontrib_(xession)
    autotune._unload_xontrib_(xession)
    assert autotune._on_post_spec_run not in xession.builtins.events.on_post_spec_run
    assert "pygwin-tune" not in xession.aliases


def test_heavy_commands_respects_env_override(xession):
    xession.env["PYGWIN_AUTOTUNE_COMMANDS"] = ["notepad"]
    assert autotune._heavy_commands() == {"notepad"}


def test_heavy_commands_default_when_unset(xession):
    assert autotune._heavy_commands() == autotune.DEFAULT_HEAVY_COMMANDS
