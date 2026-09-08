# Changelog

All notable changes to pygwin are recorded here. This file starts from pygwin's own
first commit; for xonsh's history before the fork, see
[xonsh's changelog](https://github.com/xonsh/xonsh/blob/main/CHANGELOG.md).

## Unreleased

- Fixed three real cross-platform bugs in the `autotune` xontrib, all found by CI's
  first real run against it (the commits that added it sat local-only, verified only
  on this project's own Windows machine, until this session pushed `main`):
  `_basename_no_exe()` didn't understand a path using the other platform's
  separator, `pygwin-tune restore` silently reported success even when the OS
  refused an unprivileged POSIX process permission to lower its own niceness back
  down, and a test asserted a relative priority change that GitHub's Windows
  runners could make vacuously fail. See this repository's git history for the
  full detail on each.
- Closed the last open item in ROADMAP.md (replacing the default history backend)
  as a deliberate decision, not a dropped task: `JsonHistory()` construction
  measures at under 1ms, so there is no real cost to justify rewriting it. Every
  item in ROADMAP.md is now checked off, so the file was removed; its content
  isn't lost, each item's outcome is recorded in this file's dated release
  entries, and the full investigation detail lives on in git history on the
  commits that closed each item out. See SYNCING.md for the record of its
  removal.

## v0.2.0

- Added `xontrib/sysinfo.py`: a background `psutil`-backed telemetry thread
  (CPU, memory) exposed as `cpu`/`mem` prompt fields and a `pygwin-top`
  command, never blocking the prompt on a syscall. Opt-in, via the new
  `observability` extra.
- Added `xontrib/autotune.py`: detects known CPU-heavy commands (compilers,
  build tools, renderers, encoders, archivers) via the `on_post_spec_run`
  event and nudges their OS priority down a notch, transparently and
  reversibly (`pygwin-tune list`/`restore`), never silently. Guards against
  ever deprioritizing pygwin's own process.
- Cached `$PATH` resolution behind `locate_executable()`, so resolving an
  external command doesn't re-stat every `$PATH` directory on every single
  subprocess call. Cut `locate_executable("git")` from about 10ms to about
  1.3ms per call in local measurements.
- Removed the last two runtime-recognized traces of xonsh, at the project
  owner's request: the callable-alias protocol attributes are
  `__pygwin_threadable__`/`__pygwin_capturable__` now (not `__xonsh_*`), and
  pygwin no longer recognizes an `xonsh` shebang or interpreter name.
  `~/.pygwinrc` no longer falls back to `~/.xonshrc` either. Nothing named
  `xonsh` is recognized by pygwin at runtime anymore; only factual citations
  to the real upstream project and its ecosystem remain, documented in
  SYNCING.md.
- Finished the `docs/` rename: files whose names still said `xonsh` while
  their content already said pygwin (`xonsh_session.rst`, `xonshrc.rst`, and
  others) are renamed, and content describing infrastructure or community
  processes pygwin doesn't have (xonsh's marketing site, WinGet/Flatpak/
  conda/AppImage install docs, Zulip/Mastodon/sponsors links) was removed
  rather than relabeled.
- Fixed several smaller rename leftovers found while auditing the above:
  `run-tests.xsh` was setting an env var that no longer exists, a handful of
  README/rst files still described "Xonsh" in prose, and a few docs pages
  mislabeled real third-party xonsh-only projects (a Sublime package, a VS
  Code extension) as pygwin's own, including two install commands that
  didn't actually work.
- Fixed the Nuitka onefile build never actually benefiting from a warm
  cache: it never set `--onefile-cache-mode`, so Nuitka's default inferred
  temporary extraction and fully re-extracted the whole payload, deleting it
  again, on every single launch. Added `--onefile-cache-mode=cached` (which
  also required setting `--company-name`/`--product-name`/`--file-version`,
  since that mode changes the default extraction path to include them).
  Verified against a real rebuilt `pygwin.exe`: first run about 900ms to 1s,
  every run after that about 480-500ms, actually reusing the cache
  directory. Also installed the `zstandard` package before building, which
  let Nuitka compress the onefile payload; cut the same build from 74MB to
  19MB with no code change.
- Fixed `__version__` (`pygwin/__init__.py`): it had been left at `0.24.2`,
  xonsh's own version number at the time of the fork, since the very first
  rebrand commit. `pygwin --version` now reports a version that actually
  matches this project's own release tags.

## v0.1.1

- Made `readline` the default interactive shell backend instead of
  `prompt_toolkit` (`$SHELL_TYPE` now defaults to `readline`, not `best`).
  Also fixed `$PROMPT`'s default value being computed eagerly at
  class-definition time, which imported `prompt_toolkit` regardless of the
  selected backend, and added `pyreadline3` as a Windows-conditional base
  dependency, since Windows ships no stdlib `readline` at all. About a 75ms,
  23% cut to shell construction time in local measurements.
- Lazy-imported several heavy modules that were loading unconditionally on
  every launch: `platform_info.py`'s OS checks now use `sys.platform`
  instead of `platform.system()` (which shells out to WMI on Windows),
  `sqlite3` only loads if the sqlite history backend is actually selected,
  and `ctypes`/`shutil` only load inside the specific functions that use
  them. Cut `pygwin.main`'s cumulative import time from about 278ms to about
  100ms in local `-X importtime` profiling.
- Fixed a real bug in the already-shipped v0.1.0 release: the compiled
  `pygwin.exe` bundled no pre-built parser tables, so every single command
  hung for about 1.8 seconds regenerating them via PLY's LALR table
  generation. Added `scripts/build_parser_tables.py`, wired it into the CD
  workflow, and added explicit `--include-module` flags so Nuitka's static
  import scanner actually bundles the pre-built tables (PLY loads them by a
  dynamic string name, which Nuitka can't see on its own). First run after
  this fix: about 583ms; subsequent runs: about 190-200ms.

## v0.1.0

- Forked xonsh into pygwin: renamed the CLI entry point and `--version` string,
  replaced the license and README, and set up CI, a Nuitka-based release build, and
  a GitHub Pages site.
- Renamed the entire codebase from xonsh to pygwin: the Python package itself
  (`xonsh/` to `pygwin/`), the `__xonsh__` runtime global (to `__pygwin__`), every
  `$XONSH_*` environment variable (to `$PYGWIN_*`), and every `Xonsh`-prefixed class
  and function name. See SYNCING.md.
- Removed the remaining xonsh compatibility exceptions from the rename above: the
  callable-alias protocol attributes are `__pygwin_threadable__`/
  `__pygwin_capturable__` now, not `__xonsh_threadable__`/`__xonsh_capturable__`; a
  `#!/usr/bin/env xonsh` shebang is no longer recognized, only `pygwin`; and
  `~/.pygwinrc` no longer falls back to an existing `~/.xonshrc`. Also fixed two
  accidental leftovers found while auditing this: `get_home_pygwinrc_path()`'s
  `.xonshrc` fallback had been silently broken by the original rename (it checked
  `.pygwinrc` three times instead of ever falling back, so it was already
  effectively dead code), and the pygments lexer aliases had been over-renamed into
  duplicate `pygwin`/`pygwincon` entries instead of a real `pygwin`/`xonsh` pair,
  now de-duplicated. Nothing named `xonsh` is recognized by pygwin at runtime
  anymore; only factual citations to the real upstream project's URLs and the
  license attribution in CREDITS.md remain. See SYNCING.md.
- Along the way, found and fixed a real bug in Nuitka's standalone compiler
  (a package submodule sharing a stdlib module's basename gets resolved to itself)
  by renaming `platform.py` to `platform_info.py`, and fixed a pyproject.toml bug
  where self-referencing optional-dependency groups were silently pulling the real
  xonsh package down from PyPI instead of resolving to this fork.
- Disabled the interactive welcome message by default
  (`$XONSH_SUPPRESS_WELCOME`/`$PYGWIN_SUPPRESS_WELCOME` now defaults to `True`), so
  `pygwin` starts a plain interactive session with no banner or first-run prompt.
