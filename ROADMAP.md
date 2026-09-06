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

None of this is done yet. It is what pygwin is for, and it is real, multi-session work,
not a checklist to rush through in one pass.

### Startup and memory

- [ ] Make `readline` the default interactive shell backend instead of `prompt_toolkit`,
      and make prompt_toolkit strictly opt-in (`pygwin[full]`) rather than the default
      install target.
- [ ] Lazy-import heavy modules (subprocess helpers, `inspect`, `json`, `pathlib` usage
      in cold paths, the ply-based parser) so they load on first use, not on every launch.
- [ ] Skip foreign shell (bash/zsh/cmd) environment probing on startup unless explicitly
      requested; it costs a process spawn nobody asked for on most launches.
- [ ] Replace the default history backend with a lightweight append-only or in-memory
      option, keeping SQLite/JSON history as an opt-in xontrib for people who want it.
- [ ] Pre-build and ship the parser tables instead of regenerating them at import time.
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
