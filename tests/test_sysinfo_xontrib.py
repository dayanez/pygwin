"""Tests for the ``sysinfo`` xontrib: the background telemetry thread,
its prompt fields, and the ``pygwin-top`` alias registration.
"""

import sys
import time

import pytest

from xontrib import sysinfo


@pytest.fixture(autouse=True)
def _stop_telemetry_after():
    yield
    sysinfo._telemetry.stop()


def test_telemetry_start_returns_true_when_psutil_present():
    assert sysinfo._telemetry.start() is True


def test_telemetry_start_returns_false_when_psutil_missing(monkeypatch):
    # sys.modules[name] = None makes `import name` raise ImportError, the
    # standard way to simulate a missing module without actually uninstalling it.
    monkeypatch.setitem(sys.modules, "psutil", None)
    assert sysinfo._telemetry.start() is False
    assert sysinfo._telemetry._thread is None


def test_load_xontrib_prints_and_skips_when_psutil_missing(
    xession, monkeypatch, capsys
):
    monkeypatch.setitem(sys.modules, "psutil", None)
    sysinfo._load_xontrib_(xession)
    fields = xession.env["PROMPT_FIELDS"]
    assert "cpu" not in fields
    assert "mem" not in fields
    assert "pygwin-top" not in xession.aliases
    assert "psutil is not installed" in capsys.readouterr().out


def test_telemetry_snapshot_populates_after_a_poll():
    sysinfo._telemetry.interval = 0.05
    sysinfo._telemetry.start()
    deadline = time.monotonic() + 2.0
    snap = sysinfo._telemetry.snapshot()
    while snap.cpu_percent is None and time.monotonic() < deadline:
        time.sleep(0.05)
        snap = sysinfo._telemetry.snapshot()
    assert snap.cpu_percent is not None
    assert snap.mem_percent is not None
    assert snap.mem_used_gb is not None
    assert snap.mem_total_gb is not None


def test_telemetry_stop_joins_thread():
    sysinfo._telemetry.start()
    sysinfo._telemetry.stop()
    assert sysinfo._telemetry._thread is None


def test_telemetry_start_is_idempotent():
    assert sysinfo._telemetry.start() is True
    first_thread = sysinfo._telemetry._thread
    assert sysinfo._telemetry.start() is True
    assert sysinfo._telemetry._thread is first_thread


def test_sysinfo_field_formats_zero_as_visible_not_empty():
    field = sysinfo._SysInfoField(attr="cpu_percent", name="cpu")
    field.value = 0
    assert format(field, "") == "0"


def test_sysinfo_field_formats_none_as_empty():
    field = sysinfo._SysInfoField(attr="cpu_percent", name="cpu")
    field.value = None
    assert format(field, "") == ""


def test_load_xontrib_registers_fields_and_alias(xession):
    sysinfo._load_xontrib_(xession)
    try:
        fields = xession.env["PROMPT_FIELDS"]
        assert "cpu" in fields
        assert "mem" in fields
        assert "pygwin-top" in xession.aliases
    finally:
        sysinfo._unload_xontrib_(xession)


def test_unload_xontrib_removes_fields_and_alias(xession):
    sysinfo._load_xontrib_(xession)
    sysinfo._unload_xontrib_(xession)
    fields = xession.env["PROMPT_FIELDS"]
    assert "cpu" not in fields
    assert "mem" not in fields
    assert "pygwin-top" not in xession.aliases


def test_load_xontrib_field_value_reflects_snapshot(xession):
    sysinfo._telemetry.interval = 0.05
    sysinfo._load_xontrib_(xession)
    try:
        fields = xession.env["PROMPT_FIELDS"]
        deadline = time.monotonic() + 2.0
        while (
            sysinfo._telemetry.snapshot().cpu_percent is None
            and time.monotonic() < deadline
        ):
            time.sleep(0.05)
        cpu_field = fields.pick("cpu")
        assert cpu_field.value is not None
        assert isinstance(format(cpu_field, ""), str)
    finally:
        sysinfo._unload_xontrib_(xession)
