"""Process auto-tuning: notice known CPU-heavy commands (compilers,
renderers, encoders, archivers) right after they launch and nudge their
priority down a notch, so a `cargo build` or `ffmpeg` run in one pane
doesn't make everything else in the shell feel sluggish.

Never silent: every adjustment prints what it did and the exact command to
undo it. Never permanent: it only ever changes the live OS process's own
priority, which disappears the moment that process exits; nothing is
written to disk or to the registry.
"""

import os

import pygwin.platform_info as xp
from pygwin.built_ins import XSH, PygwinSession

# Basenames (case-insensitive, ".exe" optional) of commands treated as
# typically CPU-heavy: compilers and build tools, renderers and encoders,
# and archivers. Override with $PYGWIN_AUTOTUNE_COMMANDS (an iterable of
# names) rather than editing this list.
DEFAULT_HEAVY_COMMANDS = frozenset(
    {
        "cl",
        "gcc",
        "g++",
        "cc",
        "clang",
        "clang++",
        "rustc",
        "cargo",
        "javac",
        "tsc",
        "msbuild",
        "nmake",
        "make",
        "cmake",
        "ninja",
        "ffmpeg",
        "ffprobe",
        "blender",
        "handbrake",
        "handbrakecli",
        "7z",
        "7za",
        "tar",
        "docker",
        "webpack",
    }
)

# pid -> the psutil-reported priority/niceness it had before this xontrib
# touched it, so `pygwin-tune restore` can put it back exactly.
_original_priority: "dict[int, int]" = {}


def _basename_no_exe(path: str) -> str:
    name = os.path.basename(path).lower()
    if name.endswith(".exe"):
        name = name[:-4]
    return name


def _heavy_commands() -> "frozenset[str]|set[str]":
    configured = XSH.env.get("PYGWIN_AUTOTUNE_COMMANDS")
    if configured:
        return {str(c).lower() for c in configured}
    return DEFAULT_HEAVY_COMMANDS


def _lowered_priority_value(psutil_mod):
    # Windows priority classes are a fixed enum; POSIX niceness is a scale
    # from -20 (highest) to 19 (lowest), and unprivileged users may only
    # ever raise it (deprioritize), never lower it, which is exactly the
    # direction this feature moves in, so no elevated privileges are needed
    # on either platform.
    return psutil_mod.BELOW_NORMAL_PRIORITY_CLASS if xp.ON_WINDOWS else 10


def _on_post_spec_run(spec=None, proc=None, **_):
    if spec is None or proc is None:
        return
    if callable(getattr(spec, "alias", None)):
        return  # an in-process Python alias, not a real OS subprocess
    binary_loc = getattr(spec, "binary_loc", None)
    if not binary_loc:
        return

    pid = getattr(proc, "pid", None)
    if pid is None or pid == os.getpid():
        # ProcProxy (an unthreadable callable alias's process stand-in)
        # reuses pygwin's own pid. Never touch that under any circumstance.
        return

    if _basename_no_exe(binary_loc) not in _heavy_commands():
        return

    try:
        import psutil
    except ImportError:
        return

    try:
        proc_handle = psutil.Process(pid)
        original = proc_handle.nice()
        proc_handle.nice(_lowered_priority_value(psutil))
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return

    _original_priority[pid] = original
    name = os.path.basename(binary_loc)
    print(
        f"pygwin: lowered priority of '{name}' (pid {pid}) to keep the shell "
        f"responsive. Run 'pygwin-tune restore {pid}' to undo."
    )


def _tune(args=None):
    """``pygwin-tune``: list or undo this session's auto-tuning."""
    args = list(args or [])
    try:
        import psutil
    except ImportError:
        print("pygwin-tune: psutil is not installed.")
        return 1

    if not args or args[0] == "list":
        if not _original_priority:
            print("pygwin-tune: nothing has been auto-tuned this session.")
            return 0
        for pid, original in _original_priority.items():
            print(f"  pid {pid}: original priority was {original}")
        return 0

    if args[0] == "restore" and len(args) > 1:
        pids = list(_original_priority) if args[1] == "all" else [args[1]]
        for raw_pid in pids:
            try:
                pid = int(raw_pid)
            except ValueError:
                print(f"pygwin-tune: {raw_pid!r} is not a pid.")
                continue
            original = _original_priority.pop(pid, None)
            if original is None:
                print(f"pygwin-tune: pid {pid} was not auto-tuned.")
                continue
            try:
                psutil.Process(pid).nice(original)
                print(f"pygwin-tune: restored pid {pid} to priority {original}.")
            except (psutil.NoSuchProcess, psutil.AccessDenied) as ex:
                print(f"pygwin-tune: could not restore pid {pid}: {ex}")
        return 0

    print("usage: pygwin-tune [list | restore <pid> | restore all]")
    return 1


def _load_xontrib_(xsh: PygwinSession, **_):
    xsh.builtins.events.on_post_spec_run(_on_post_spec_run)
    xsh.aliases["pygwin-tune"] = _tune


def _unload_xontrib_(xsh: PygwinSession, **_):
    xsh.builtins.events.on_post_spec_run.discard(_on_post_spec_run)
    xsh.aliases.pop("pygwin-tune", None)
    _original_priority.clear()
