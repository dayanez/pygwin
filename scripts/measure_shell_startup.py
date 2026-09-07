"""One-off measurement script: cold-process time to construct pygwin's Shell
object under different $SHELL_TYPE values. Not part of the package; used to
produce the before/after numbers ROADMAP.md's startup work calls for."""

import statistics
import subprocess
import sys

RUNS = 7

CODE = """
import time
t0 = time.perf_counter()
import pygwin.main as m
from pygwin.built_ins import XSH
from pygwin.execer import Execer
execer = Execer(filename="<stdin>")
XSH.load(ctx={{}}, execer=execer)
from pygwin.shell import Shell
try:
    shell = Shell(execer, ctx={{}}, shell_type={shell_type!r})
except Exception:
    # This dev shell has no real Windows console, so constructing an
    # actual PromptSession fails here regardless. By this point
    # prompt_toolkit (if selected) has already been fully imported, which
    # is the cost this measurement cares about.
    pass
t1 = time.perf_counter()
print(t1 - t0)
"""


def measure(shell_type):
    times = []
    for _ in range(RUNS):
        out = subprocess.run(
            [sys.executable, "-c", CODE.format(shell_type=shell_type)],
            capture_output=True,
            text=True,
        )
        if out.returncode != 0:
            print(out.stdout, out.stderr)
            raise SystemExit(1)
        times.append(float(out.stdout.strip().splitlines()[-1]))
    return times


for label, shell_type in [("best (old default)", "best"), ("readline (new default)", "readline"), ("unset (actual new default)", None)]:
    times = measure(shell_type)
    ms = [t * 1000 for t in times]
    print(
        f"{label:32s} median={statistics.median(ms):6.1f}ms  "
        f"min={min(ms):6.1f}ms  max={max(ms):6.1f}ms  runs={ms}"
    )
