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
- [x] Measure before and after every change above. "Feels faster" is not a metric;
      wall-clock startup time and RSS at prompt are. Every bullet above already
      carries real before/after numbers (measured with `-X importtime`, direct
      `time.perf_counter()` timing, or `scripts/measure_shell_startup.py`), so this
      is satisfied as a record of what was done, not a separate task. It stays true
      as a standing rule for any future change to this section.

### System observability (pygwin's actual differentiator)

- [x] A background `psutil`-backed telemetry thread (CPU, memory) that never blocks
      the prompt, exposed as prompt fields and a `pygwin-top`-style command. Shipped
      as a new, self-contained `xontrib/sysinfo.py` (not loaded by default; requires
      `psutil`, added as the new `observability` extra and pulled into `full`),
      following AGENTS.md's rule rather than touching `pygwin/prompt/base.py` or
      `environ.py` directly.
      Design: a `SysTelemetry` class owns one daemon thread and a lock-protected
      snapshot (cpu percent, memory percent, memory used/total in GiB), polled every
      2 seconds. `psutil.cpu_percent(interval=None)` reports the delta since the
      previous call rather than sleeping to measure, so the only blocking wait in the
      whole design is the background thread's own `Event.wait()` between polls;
      anything reading `snapshot()` (prompt fields, in particular) only ever touches
      an already-computed value behind a lock held for microseconds. Two prompt
      fields (`cpu`, `mem`) are registered directly into `$PROMPT_FIELDS` from
      `_load_xontrib_`, the same public mechanism the docs already tell end users to
      use for their own custom fields (see `docs/prompt.rst`), rather than editing
      `PromptFields.load_initial()`. If `psutil` is not installed, `_load_xontrib_`
      prints one explanatory line and returns without starting anything, rather than
      failing loudly or leaving a half-registered field.
      `pygwin-top` reuses the same `psutil` dependency but intentionally does not
      read the shared snapshot: it is a foreground command the user runs on purpose,
      so unlike the passive telemetry thread it is allowed to block on its own 1
      second refresh loop until Ctrl+C, and it also tracks per-process CPU% (which
      the prompt-field snapshot does not). Found and fixed a real bug while building
      it: `psutil.process_iter()` hands back a fresh `Process` object every call, and
      `Process.cpu_percent()` needs two calls on the *same* object to report a real
      delta, so a naive `process_iter(["cpu_percent"])` loop silently reports 0.0%
      for every process on every refresh. Fixed by keeping one persistent
      `{pid: Process}` dict across refreshes. Verified against the real dev machine,
      not just tests: watched `pygwin-top` correctly rank `python.exe` and `dwm.exe`
      above idle processes across two live refreshes.
      Tested with a real background thread and a real mocked `xession` fixture in
      `tests/test_sysinfo_xontrib.py` (9 tests: thread start/stop/idempotency, a real
      snapshot populating within a 2 second deadline, prompt-field registration and
      removal on load/unload, and the zero-vs-none formatting distinction, since
      `PromptField`'s default `__format__` treats a real `0%` reading the same as
      "no value yet" and had to be overridden).
      Not done in this bullet, and deliberately left for later: thermals (`psutil`'s
      `sensors_temperatures()` is Linux-only in practice and does not exist at all in
      some `psutil` builds on Windows, so "where available" in the original roadmap
      wording means "not on this project's primary platform today"), and whether
      `sysinfo` should be autoloaded by default rather than opt-in (`coreutils`, the
      only other in-tree xontrib, is also opt-in only, so this matches existing
      precedent rather than introducing a new one; worth revisiting once there is
      real usage to react to).
- [x] Smart process auto-tuning: detect known-heavy commands (compiles, renders,
      encodes) and offer to adjust their priority or CPU affinity, transparently and
      reversibly, never silently.
      Shipped as another new, self-contained xontrib, `xontrib/autotune.py`, again
      not loaded by default, needing no edits to `pygwin/procs/specs.py` or any other
      core file: `SubprocSpec.run()` already fires an `on_post_spec_run` event
      (`spec=`, `proc=`) right after every subprocess spawns, which turned out to be
      exactly the extension point this needed, built for general-purpose use rather
      than for this feature specifically.
      Detection is name-based, matching the roadmap wording ("known-heavy commands")
      rather than a live CPU-usage heuristic: a fixed set of compiler, build-tool,
      renderer, encoder, and archiver basenames (`gcc`, `rustc`, `cargo`, `msbuild`,
      `ffmpeg`, `blender`, `7z`, `docker`, and others), overridable via
      `$PYGWIN_AUTOTUNE_COMMANDS` without a formal `environ.py` entry, the same
      pattern `sysinfo` already established for its poll interval.
      The adjustment itself is a priority nudge, not CPU-affinity pinning: on Windows,
      `psutil.Process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)`; on POSIX, a niceness
      of 10. Deliberately not touching affinity in this first pass, since forcing a
      heavy process onto a subset of cores can genuinely slow it down on some
      workloads rather than just deprioritize it, a real tradeoff that needs its own
      justification, not a default.
      "Transparently and reversibly, never silently" is met by construction rather
      than by an interactive confirmation prompt: the whole feature is opt-in
      (`xontrib load autotune`), every adjustment prints exactly what changed and the
      command to undo it, and undoing it is a real, tested round trip
      (`pygwin-tune restore <pid>`, or `pygwin-tune list` to see what is currently
      adjusted). A blocking yes/no prompt was considered and rejected: it would
      steal stdin from the very command it's asking about, and would be actively
      hostile in scripts and pipelines.
      Found the single highest-stakes bug case by reading `pygwin/procs/proxies.py`
      before writing any code, per AGENTS.md's note that `pygwin/procs/` deserves
      execution-safety-level care: `ProcProxy` (the Popen stand-in for unthreadable
      callable aliases) sets its own `.pid` to `os.getpid()`, pygwin's own process.
      A naive implementation would, on the right alias name match, deprioritize the
      entire running shell. Guarded explicitly against `pid == os.getpid()`, and
      wrote a test that fakes `psutil.Process` to raise if it is ever called at all
      for that case, not just asserting the end state.
      Verified two ways beyond unit tests: a real subprocess spawned in-test, reniced,
      confirmed changed via `psutil`, and confirmed restored to its exact original
      value; and a real end-to-end run through an actual compiled pygwin session
      (`pygwin -c "..."`, `xontrib load autotune` then a matched subprocess),
      confirming the real `on_post_spec_run` event delivers `spec`/`proc` in the
      shape this code assumes and the transparency message prints for real.
      14 tests in `tests/test_autotune_xontrib.py`.
- [x] Cached binary path and environment lookups, so resolving external commands does
      not repeat filesystem work every single invocation.
      Measured first, per this file's own rule: `pygwin.procs.executables.locate_executable`
      is the real hot path (called from `procs/specs.py` for every subprocess command),
      and there was already a `CommandsCache` class with mtime-based directory caching,
      but its own docstring says it is "NOT RECOMMENDED" for single-command resolution
      in favor of `locate_executable`, which turned out not to use that cache at all.
      Timed directly on a dev machine with a real 35-entry `$PATH`: 200 calls to
      `locate_executable("git")` took ~10.06ms each, of which ~9.28ms was
      `clear_paths()` (`os.path.realpath` + `os.path.isdir` on every `$PATH` entry),
      re-run from scratch on every single call even though `$PATH` essentially never
      changes mid-session.
      First fix attempt cached `get_paths()`, the function `CommandsCache` calls, but
      re-measuring showed almost no change (~9.93ms). Reading `locate_file_in_path_env`
      (what `locate_executable` actually calls) showed why: it calls `clear_paths()`
      directly and never goes through `get_paths()` at all, so the two functions were
      duplicating the same filesystem work independently. Added one shared,
      order-preserving cache (`_cached_clear_paths`, keyed on the raw `$PATH` tuple) and
      had both call sites use it; `get_paths()` still reverses its result afterward,
      preserving its existing contract for `CommandsCache` and other callers, while
      `locate_file_in_path_env` gets the un-reversed, priority-preserving order it
      always relied on. Respects the existing `$ENABLE_COMMANDS_CACHE` toggle, matching
      its documented "disables the caching mechanism" behavior.
      Re-measured after the real fix: `locate_executable("git")` dropped to ~1.27ms per
      call, an ~87% reduction. The remaining cost is the actual per-name stat check
      across `$PATH` directories, not redundant re-validation of `$PATH` itself; going
      further would mean giving every directory the same always-on listing cache
      `$PYGWIN_COMMANDS_CACHE_READ_DIR_ONCE` already offers as an opt-in today, which is
      a bigger correctness-sensitive change (stale listings if a directory's contents
      change mid-session) left for later rather than folded into this fix.
      Verified the cache actually caches and actually invalidates, not just that the
      numbers looked right: `tests/procs/test_executables.py` gained tests that count
      real `clear_paths()` calls (asserting an unchanged `$PATH` triggers exactly one),
      confirm a `$PATH` change is picked up on the very next call with no manual
      cache-reset, confirm `locate_executable` itself (not just `get_paths()`) finds a
      newly-added `$PATH` directory immediately, and confirm `$ENABLE_COMMANDS_CACHE =
      False` bypasses the cache entirely.

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
- [x] Re-evaluate release size and startup time after the phase-two work above
      landed. Found the real cause by reading Nuitka's own `--help` text rather than
      guessing: the build command in both the README and `cd.yml` never set
      `--onefile-cache-mode`. Nuitka's default (`auto`) infers `temporary` extraction
      whenever the tempdir spec has a runtime-dependent part, and the default spec
      (`{TEMP}/onefile_{PID}_{TIME_US}_{RANDOM}`) always does, so every single launch
      fully re-extracted the whole payload to a brand-new temp folder and deleted it
      on exit, with zero warm-cache benefit between runs. Measured directly on a real
      compiled `pygwin.exe`, before this fix: all 6 runs ~900ms, no first-run-slow-
      then-fast pattern at all, confirming the theory. This is also almost certainly
      what the earlier "~190-200ms subsequent runs" number above was missing: that
      number implies caching was in effect when it was measured, which the checked-in
      build command never actually did.
      Fixed by adding `--onefile-cache-mode=cached` to both the README and `cd.yml`.
      This alone wasn't enough to get a working build: `cached` mode changes the
      default extraction path to `{CACHE_DIR}\{COMPANY}\{PRODUCT}\{VERSION}`, so
      Nuitka refuses to build at all unless `--company-name`, `--product-name`, and
      `--file-version`/`--product-version` are also set. Found this by actually
      running the build, not by reading docs speculatively; added all four flags
      (version derived from `pygwin.__version__` at build time in `cd.yml`, so it
      never drifts from the package version).
      Verified against a real rebuilt binary: first run ~900ms-1s (cold, nothing
      cached), every run after that ~480-500ms, correctly reusing
      `%LOCALAPPDATA%\pygwin\pygwin\<version>\pygwin.exe` instead of re-extracting.
      About a 45% cut to steady-state startup versus the unfixed build.
      Also found, incidentally, while reading the build log rather than looking for
      it: Nuitka's onefile mode silently can't compress its payload without the
      `zstandard` package installed, and neither the README nor `cd.yml` had it.
      Installing it and rebuilding cut this same build from 74MB uncompressed to a
      19MB `.exe`, with no code change and no functionality lost. Added
      `pip install ... zstandard` alongside the existing `pip install nuitka` step in
      both places.
      Measured one more real tradeoff before settling on what to ship: a build from
      a plain `pip install -e .` (no `[full]` extra, so no `prompt_toolkit`,
      `pygments`, or `psutil`) came out smaller (11MB) and faster (~400ms
      steady-state) than the `[full]` build (19MB, ~490ms), but can't run
      `best`-shell mode or the `sysinfo`/`autotune` xontribs at all, since Nuitka
      never sees code that was never importable at compile time. Kept `[full]` in
      `cd.yml` rather than trading away the observability features this project is
      actually for, since a smaller `.exe` that can't do what the README advertises
      isn't a real win; documented the actual numbers and the tradeoff in the README
      instead of quietly picking one.
      Fixed one more real, unrelated bug found while auditing this: `pygwin/__init__.py`'s
      `__version__` had been left at `0.24.2`, xonsh's own version number, since the
      very first rebrand commit; `pygwin --version` was reporting a version that had
      never matched this project's own release tags. Bumped to match the version
      this release actually ships as.

All of this belongs in new files under `xontrib/`, `xompletions/`, or a new top-level
module where that's a real option, per AGENTS.md's one rule. It does not belong in
edits scattered across `pygwin/`'s existing files without good reason.
