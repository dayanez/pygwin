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

# pid -> the psutil-reported priority/niceness it had before this pgtrib
# touched it, so `pygwin-tune restore` can put it back exactly.
_original_priority: "dict[int, int]" = {}


def _basename_no_exe(path: str) -> str:
    # Deliberately not os.path.basename(): that only understands the host
    # platform's own separator, so a Windows-style path (backslashes)
    # passed on POSIX, or vice versa, would come back unsplit. binary_loc
    # values are always real, host-native paths in production, but the
    # basename logic itself has no reason to depend on the host OS.
    name = path.replace("\\", "/").rsplit("/", 1)[-1].lower()
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
    # direction the initial adjustment moves in, so lowering never needs
    # elevated privileges on either platform. Restoring back down afterward
    # is the opposite direction on POSIX, though: an unprivileged process
    # cannot lower its own niceness back toward the original value without
    # CAP_SYS_NICE (or being root), so `pygwin-tune restore` can genuinely
    # fail there. See _tune()'s restore branch, which reports that
    # truthfully via its return code rather than assuming it always works.
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
        all_restored = True
        for raw_pid in pids:
            try:
                pid = int(raw_pid)
            except ValueError:
                print(f"pygwin-tune: {raw_pid!r} is not a pid.")
                all_restored = False
                continue
            original = _original_priority.pop(pid, None)
            if original is None:
                print(f"pygwin-tune: pid {pid} was not auto-tuned.")
                all_restored = False
                continue
            try:
                psutil.Process(pid).nice(original)
                print(f"pygwin-tune: restored pid {pid} to priority {original}.")
            except (psutil.NoSuchProcess, psutil.AccessDenied) as ex:
                # On POSIX, only a privileged process can *lower* a
                # niceness value back down; an unprivileged restore back
                # to a normal-or-higher priority genuinely can fail here,
                # not just in theory. Report it truthfully via the return
                # code rather than claiming success.
                print(f"pygwin-tune: could not restore pid {pid}: {ex}")
                all_restored = False
        return 0 if all_restored else 1

    print("usage: pygwin-tune [list | restore <pid> | restore all]")
    return 1


def _load_pgtrib_(xsh: PygwinSession, **_):
    xsh.builtins.events.on_post_spec_run(_on_post_spec_run)
    xsh.aliases["pygwin-tune"] = _tune


def _unload_pgtrib_(xsh: PygwinSession, **_):
    xsh.builtins.events.on_post_spec_run.discard(_on_post_spec_run)
    xsh.aliases.pop("pygwin-tune", None)
    _original_priority.clear()
