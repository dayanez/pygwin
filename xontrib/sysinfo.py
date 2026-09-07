"""System observability: a background telemetry thread, prompt fields, and
the ``pygwin-top`` command.

Polls CPU and memory usage on a background thread so prompt rendering never
blocks on a syscall. Requires ``psutil``, an optional dependency (the
``observability`` extra, also pulled in by ``full``); if it is not
installed, loading this xontrib prints one line explaining that and does
nothing else.
"""

import contextlib
import threading
import time
import typing as tp

from pygwin.built_ins import PygwinSession
from pygwin.prompt.base import PromptField

_POLL_INTERVAL = 2.0


class _Snapshot(tp.NamedTuple):
    cpu_percent: "float|None"
    mem_percent: "float|None"
    mem_used_gb: "float|None"
    mem_total_gb: "float|None"


_EMPTY_SNAPSHOT = _Snapshot(None, None, None, None)


class SysTelemetry:
    """Owns the background polling thread and the latest snapshot.

    ``psutil.cpu_percent(interval=None)`` is non-blocking: it reports the
    average since the previous call rather than sleeping to measure, so the
    blocking wait lives entirely in this thread's own loop, never on
    whichever thread reads ``snapshot()``.
    """

    def __init__(self, interval: float = _POLL_INTERVAL):
        self.interval = interval
        self._lock = threading.Lock()
        self._snapshot = _EMPTY_SNAPSHOT
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> bool:
        """Starts the background thread. Returns False if psutil is missing."""
        try:
            import psutil  # noqa: F401
        except ImportError:
            return False
        if self._thread is not None:
            return True
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run, name="pygwin-sysinfo", daemon=True
        )
        self._thread.start()
        return True

    def stop(self, timeout: float = 1.0) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
            self._thread = None

    def _run(self) -> None:
        import psutil

        psutil.cpu_percent(interval=None)  # first call is meaningless, primes it
        while not self._stop.is_set():
            try:
                cpu = psutil.cpu_percent(interval=None)
                vm = psutil.virtual_memory()
                with self._lock:
                    self._snapshot = _Snapshot(
                        cpu_percent=cpu,
                        mem_percent=vm.percent,
                        mem_used_gb=vm.used / (1024**3),
                        mem_total_gb=vm.total / (1024**3),
                    )
            except Exception:
                pass
            self._stop.wait(self.interval)

    def snapshot(self) -> _Snapshot:
        with self._lock:
            return self._snapshot


_telemetry = SysTelemetry()


class _SysInfoField(PromptField):
    """Reads the shared telemetry snapshot; never touches psutil itself."""

    attr = "cpu_percent"
    digits = 0

    def update(self, ctx) -> None:
        val = getattr(_telemetry.snapshot(), self.attr)
        self.value = None if val is None else round(val, self.digits)

    def __format__(self, format_spec: str) -> str:
        # Overrides PromptField's `if self.value:` check, which would hide
        # a real 0% reading the same way it hides "no value yet".
        if self.value is None:
            return ""
        return self.prefix + format(self.value, format_spec) + self.suffix


def _top(args=None):
    """``pygwin-top``: a live, refreshing CPU/memory/process view.

    Foreground command the user runs on purpose, so unlike the telemetry
    thread it is allowed to block until Ctrl+C; it does its own psutil
    calls rather than reading the shared snapshot, so it can also list
    per-process usage, which the prompt-field snapshot does not track.
    """
    try:
        import psutil
    except ImportError:
        print(
            "pygwin-top: psutil is not installed. "
            "Install it with `xpip install pygwin[observability]`."
        )
        return 1

    # psutil.Process.cpu_percent(interval=None) reports the delta since the
    # *same Process object's* previous call; process_iter() hands back a new
    # Process each time it's called, so tracking must reuse one persistent
    # dict of Process objects across refreshes, or every reading is a
    # meaningless first-call 0.0.
    tracked: dict[int, psutil.Process] = {}

    try:
        psutil.cpu_percent(interval=None)
        while True:
            for pid in psutil.pids():
                if pid not in tracked:
                    with contextlib.suppress(psutil.NoSuchProcess, psutil.AccessDenied):
                        proc = psutil.Process(pid)
                        proc.cpu_percent(interval=None)  # prime the baseline
                        tracked[pid] = proc
            for pid in list(tracked):
                if not tracked[pid].is_running():
                    del tracked[pid]

            time.sleep(1)
            cpu = psutil.cpu_percent(interval=None)
            vm = psutil.virtual_memory()

            rows = []
            for pid, proc in tracked.items():
                with contextlib.suppress(psutil.NoSuchProcess, psutil.AccessDenied):
                    rows.append((pid, proc.cpu_percent(interval=None), proc.name()))
            rows.sort(key=lambda r: r[1], reverse=True)

            print("\x1b[2J\x1b[H", end="")  # clear screen, home cursor
            print("pygwin-top   (Ctrl+C to exit)")
            print(f"CPU   {cpu:5.1f}%")
            print(
                f"Mem   {vm.percent:5.1f}%   "
                f"{vm.used / (1024**3):.1f} GiB / {vm.total / (1024**3):.1f} GiB"
            )
            print()
            print(f"{'PID':>8}  {'CPU%':>6}  NAME")
            for pid, cpu_pct, name in rows[:10]:
                print(f"{pid:>8}  {cpu_pct:>6.1f}  {name}")
    except KeyboardInterrupt:
        print()
        return 0


def _load_xontrib_(xsh: PygwinSession, **_):
    started = _telemetry.start()
    if not started:
        print(
            "sysinfo: psutil is not installed, prompt fields and pygwin-top "
            "will not be available. Install it with `xpip install pygwin[observability]`."
        )
        return

    xsh.env["PROMPT_FIELDS"]["cpu"] = _SysInfoField(attr="cpu_percent", name="cpu")
    xsh.env["PROMPT_FIELDS"]["mem"] = _SysInfoField(attr="mem_percent", name="mem")
    xsh.aliases["pygwin-top"] = _top


def _unload_xontrib_(xsh: PygwinSession, **_):
    _telemetry.stop()
    xsh.env["PROMPT_FIELDS"].pop("cpu", None)
    xsh.env["PROMPT_FIELDS"].pop("mem", None)
    xsh.aliases.pop("pygwin-top", None)
