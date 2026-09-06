# Roadmap

pygwin is being built in two phases. Phase one is the rebrand and the scaffolding: a
working repository, a CI pipeline, a release process, and a place to publish docs.
Phase two is the actual performance and observability work that pygwin exists for.
This file tracks both, in place of GitHub issues, which this project does not use
internally (see AGENTS.md).

## Phase one: scaffold (done)

- [x] Fork xonsh's source into this repository, with a clean, single-author git history.
- [x] Rebrand the CLI entry point, `--version` string, and interactive banner to pygwin,
      while keeping the internal package name `xonsh` so future patches stay small and
      diffable against upstream.
- [x] GPL-3.0 license, with the original xonsh BSD notice preserved in CREDITS.md.
- [x] CI workflow (lint and test).
- [x] CD workflow (build and publish a Windows Nuitka executable on release).
- [x] Minimal GitHub Pages site.
- [x] AGENTS.md for coding agents working on this repo.

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

- [ ] A Nuitka standalone build that a user can download and double-click, no Python
      install required, once phase two has actually trimmed what gets compiled in.
- [ ] Re-evaluate release size and startup time after the phase-two work above lands;
      the first Nuitka release (see the Releases page) is a baseline, not the target.

All of this belongs in new files under `xontrib/`, `xompletions/`, or a new top-level
module, per AGENTS.md's one rule. It does not belong in edits scattered across
`xonsh/`'s existing files.
