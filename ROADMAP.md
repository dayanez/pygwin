# Roadmap

pygwin is being built in two phases. Phase one is the rebrand and the scaffolding: a
working repository, a CI pipeline, a release process, and a place to publish docs.
Phase two is the actual performance and observability work that pygwin exists for.
This file tracks both, in place of GitHub issues, which this project does not use
internally (see AGENTS.md).

## Phase one: scaffold and rebrand (done)

- [x] Fork xonsh's source into this repository, with a clean, single-author git history.
- [x] Rebrand the CLI entry point and `--version` string to pygwin.
- [x] Full rename: the Python package itself (`xonsh/` to `pygwin/`), the `__xonsh__`
      runtime global (to `__pygwin__`), every `$XONSH_*` environment variable (to
      `$PYGWIN_*`), and every `Xonsh`-prefixed class and function name, renamed
      throughout rather than kept for merge-friendliness. See SYNCING.md for the full
      account and what it costs going forward.
- [x] Silent startup by default: no welcome banner, no first-run message
      (`$XONSH_SUPPRESS_WELCOME` defaults to `True`).
- [x] GPL-3.0 license, with the original xonsh BSD notice preserved in CREDITS.md.
- [x] CI workflow (lint and test).
- [x] CD workflow definition (build a Windows Nuitka executable on release); an actual
      tagged release with a working `.exe` attached is still pending, see Distribution
      below.
- [x] Minimal GitHub Pages site.
- [x] AGENTS.md for coding agents working on this repo.

## Known rough edge from the rename

`virtualenv` ships its own built-in xonsh activator (baked into the `virtualenv`
package itself, unrelated to whether real xonsh is installed) that also targets
`activate.xsh`, the same filename pygwin's own activator writes. Running plain
`virtualenv <dir>` without pinning `--activators pygwin` lets both run, and
whichever runs last silently overwrites the other's file: if virtualenv's built-in
one wins, the resulting `activate.xsh` is compiled for xonsh's `__xonsh__` global
and fails with `NameError: name '__xonsh__' is not defined` when sourced under
pygwin. Until this has a real fix (either getting pygwin's activator to take
precedence, or writing to a distinct filename), the workaround is
`virtualenv <dir> --activators pygwin`. See `tests/test_virtualenv_activator.py`.

## Phase two: the actual point of pygwin

This is what pygwin is for, and it is real, multi-session work, not a checklist to
rush through in one pass.

### Startup and memory

- [x] Make `readline` the default interactive shell backend instead of `prompt_toolkit`.
      `$SHELL_TYPE` now defaults to `readline` instead of `best`; `best` still means
      "richest shell actually available" for anyone who explicitly asks for it.
      prompt_toolkit was never a required dependency (`dependencies = []`, it only
      arrives via the `full`/`ptk`/`bestshell` extras), so this was really about the
      *runtime* default, not the install-time one.
      Found a second, more important bug on the way: `$PROMPT`'s default value was
      computed eagerly at class-definition time (`pygwin/environ.py`'s `PromptSetting`
      called `prompt.default_prompt()` inline), and on Windows that function checks
      `win_ansi_support()`, which imports prompt_toolkit outright if it happens to be
      installed, regardless of which shell backend actually gets used. So merely
      importing `pygwin.environ` (every launch does) paid prompt_toolkit's import cost
      even under the new "readline by default" setting. Fixed by deferring it through
      the existing `@default_value` lazy-default mechanism (see `_default_prompt_value`
      in `environ.py`), the same pattern already used for `$XONSH_DATA_DIR` and friends.
      Also found, while measuring: Windows ships no stdlib `readline` module at all, so
      making readline the default only works if there's a real implementation behind
      it. Added `pyreadline3` as a Windows-conditional *base* dependency (not an opt-in
      extra the way upstream xonsh treats `gnureadline` on macOS), since a "Windows-first"
      shell whose default backend silently degrades to no line editing on Windows
      defeats the point.
      Measured with `scripts/measure_shell_startup.py` (median of 7 runs, cold
      subprocess each time, `prompt_toolkit` installed via `[full]` so the old default
      genuinely would have picked it): `best` (old default) ~322ms to construct the
      shell object vs `readline` (new default) ~246-249ms. About a 75ms, 23% cut, from
      this one change plus its two follow-on fixes. The 30-60ms target in the README
      is the *end* state after the rest of this section too, not from this alone.
- [x] Lazy-import heavy modules (subprocess helpers, `inspect`, `json`, `pathlib` usage
      in cold paths, the ply-based parser) so they load on first use, not on every launch.
      Four concrete wins landed, found by profiling with `python -X importtime -c
      "import pygwin.main"` rather than guessing:
      - `ON_DARWIN`/`ON_LINUX`/`ON_WINDOWS` in `platform_info.py` used
        `platform.system()`, while every other OS check in the same file
        (`ON_CYGWIN`, `ON_MSYS`, the BSD variants) already correctly used the free
        `sys.platform`/`os.name` string checks. On Windows with Python 3.12+,
        `platform.system()` calls `uname()`, which shells out to WMI
        (`_wmi.exec_query`) and cost ~85ms on its own, made worse by `if
        ON_WINDOWS:` blocks at module scope in the same file forcing that
        "lazy" bool to resolve immediately at import time anyway. Switched all
        three to `sys.platform`, matching the pattern the rest of the file
        already used. `pygwin.platform_info` import time: ~130ms to ~38-45ms.
      - `pygwin/history/main.py` unconditionally imported
        `pygwin.history.sqlite` (and therefore `sqlite3`, a compiled stdlib
        extension) at module level, even though `json` is the default history
        backend. Made the `"sqlite"` entry in `HISTORY_BACKENDS` a lazy
        dotted-path string that `construct_history()` resolves via
        `importlib` only when sqlite is actually requested, preserving the
        original silent-fallback behavior for systems where sqlite3 isn't
        available at all.
      A third, bigger candidate was found and *deliberately not touched*:
      `pygwin/procs/__init__.py` unconditionally imports `proxies` (comment:
      `# Fix https://github.com/xonsh/xonsh/pull/5437`), which drags in
      `platform_info`, `ctypes`, `shutil`, `tools`, `built_ins`, `cli_utils`,
      the completers/parsers stack, and more, about 88ms of the remaining
      ~170ms total. Checked upstream PR #5437 before touching it: it's a
      specific, hard-won fix for "I/O operation on closed file" / "Bad file
      descriptor" exceptions after running callable aliases multiple times,
      the kind of bug that would not show up in a quick before/after test run
      here but would hit real users after extended use. Deferring this
      import safely would need real understanding of the descriptor-ordering
      issue that PR fixed, not just moving the import statement, so it's
      left alone for now rather than gambled on.
      A fourth win: `platform_info.py` imported `ctypes` and `shutil` at
      module level (~12ms and ~9ms respectively, the latter via `shutil`'s
      own `bz2`/`lzma` imports), but every actual use of both is confined to
      one function each (`LIBC()`, used only by `xoreutils/uptime.py` and
      `platforms/macutils.py`; `path_bshell()`, used only by the
      shebang-less-script fallback in `procs/specs.py`), neither called at
      startup. Moved both imports inside their functions. `platform_info`
      import time: ~38-45ms to ~21ms. Verified `LIBC` and `path_bshell()`
      still resolve correctly after the change, not just that tests pass.
      `pygwin.main`'s total cumulative import time across all four fixes in
      this bullet: ~278ms to ~100ms in local `-X importtime` profiling
      (numbers shift with OS file-cache state; treat as directional, not
      absolute).
      Still open from this bullet: `inspect` usage in `pygwin.tools`, and
      whatever's left in `pathlib`/the ply-based parser. Diminishing returns
      at this point: individually small (single-digit ms), and the one
      remaining large chunk (`pygwin.procs.proxies`'s ~54ms subtree) is the
      high-risk one documented above, not something left to casually pick
      off.
- [x] Skip foreign shell (bash/zsh/cmd) environment probing on startup unless explicitly
      requested. Checked: this was already the case. `foreign_shell_data()` (in
      `pygwin/foreign_shells.py`) is only ever called from the explicit
      `source-bash`/`source-zsh`/`source-foreign` aliases or the interactive
      `xonfig wizard`, never automatically at startup. The only startup-path
      references to a variable named `foreign_shell` are in `main.py`'s
      crash-fallback exec (searching `/etc/shells` for something to hand off to
      if pygwin itself fails to start), an unrelated mechanism that happens to
      share a name. Nothing to fix here; this bullet was based on the original
      "here's how to speed up xonsh" pitch this project started from, which
      turned out not to describe this codebase's actual current behavior.
- [ ] Replace the default history backend with a lightweight append-only or in-memory
      option, keeping SQLite/JSON history as an opt-in xontrib for people who want it.
      Investigated before writing any code, per this file's own "measure before and
      after" rule: measured `JsonHistory()` construction directly at **0.86ms**, and
      after the sqlite lazy-load fix above, `pygwin.history.main`'s import cost is
      down to a modest ~10ms cumulative, most of which is legitimate (diff_history,
      JSON encoding). Writing a whole new backend class to replace a sub-millisecond
      cost isn't justified by data; that would be exactly the kind of unverified,
      speculative work this file exists to avoid. If there's a real case for a
      lighter default, it's more likely in *sustained per-command* behavior over a
      long session (buffered writes, the background flush thread) than in anything
      that shows up in a startup profile, and would need a different kind of
      measurement (a long-running session benchmark) to justify before building
      anything. Left undone rather than done badly.
- [x] Pre-build and ship the parser tables instead of regenerating them at import time.
      Found the real problem isn't import time, it's *first parse* time:
      `parser_table.py`/`completion_parser_table.py` are gitignored build
      artifacts, generated by PLY the first time anything actually gets
      parsed, then cached on disk from then on. Measured directly: with the
      tables missing, that first parse takes **~1.8 seconds** (full LALR
      table generation for the whole grammar). Confirmed this hit both of
      pygwin's real distribution paths, silently:
      - `pip install -e .` (our own documented "from source" install) never
        triggered table generation; verified by checking for the "Building
        lexer and parser tables" message `setup.py`'s legacy build hooks
        print, which never appeared across dozens of editable installs this
        session. Modern editable installs don't run those hooks.
      - The already-shipped v0.1.0 Nuitka release was built from a fresh CI
        checkout, where these gitignored files don't exist, so the compiled
        `pygwin.exe` almost certainly bundled no tables either, meaning
        every downloader's first command would hang for ~1.8s with zero
        explanation.
      Added `scripts/build_parser_tables.py` (reusable) and wired it into
      `.github/workflows/cd.yml` as a step before the Nuitka build.
      Pre-building alone was not enough, and was verified against a real
      compiled binary rather than assumed: the first attempt still hung for
      ~1.9s on *every* run, because PLY loads the table module by a dynamic
      string name (`tabmodule=`), which Nuitka's static import scanner
      cannot see, so it never bundled the pre-built file at all. Fixed by
      adding explicit `--include-module=pygwin.parser_table
      --include-module=pygwin.completion_parser_table` to the Nuitka
      invocation (both `cd.yml` and the README's local-build instructions).
      Verified against the actual compiled `pygwin.exe` this time: first run
      ~583ms, subsequent runs ~190-200ms, no regeneration hang. Documented
      the table pre-build step as recommended after `pip install -e .` in
      the README too, since that path still has no automatic hook. The
      already-published v0.1.0 release still has this bug; a v0.1.1 (or
      later) release is needed to actually fix it for anyone who already
      downloaded v0.1.0.
- [ ] Measure before and after every change above. "Feels faster" is not a metric;
      wall-clock startup time and RSS at prompt are.

### System observability (pygwin's actual differentiator)

- [ ] A background `psutil`-backed telemetry thread (CPU, memory, thermals where
      available) that never blocks the prompt, exposed as prompt fields and a
      `pygwin-top`-style command.
- [ ] Smart process auto-tuning: detect known-heavy commands (compiles, renders,
      encodes) and offer to adjust their priority or CPU affinity, transparently and
      reversibly, never silently.
- [ ] Cached binary path and environment lookups, so resolving external commands does
      not repeat filesystem work every single invocation.

### Distribution

- [x] A working Nuitka onefile build: `pygwin.exe`, no Python install required.
      Getting here took two real fixes beyond just running the compile: the Nuitka
      module-name-collision bug documented in SYNCING.md (`platform.py` to
      `platform_info.py`), and Nuitka needs to be pointed at `pygwin/__main__.py`,
      not `pygwin/main.py`, since `main.py` only defines `main()` and never calls
      it, the actual `if __name__ == "__main__"`-equivalent call lives in
      `__main__.py`. Verified against the actual compiled binary, not just source:
      `--version`, `-c` execution, subprocess capture, subshells, `$ENVVAR` access,
      and path literals all work.
- [ ] Re-evaluate release size and startup time after the phase-two work below
      lands; the current build is a baseline (compiles today's codebase as-is, not
      yet stripped down), not the target.

All of this belongs in new files under `xontrib/`, `xompletions/`, or a new top-level
module where that's a real option, per AGENTS.md's one rule. It does not belong in
edits scattered across `pygwin/`'s existing files without good reason.
