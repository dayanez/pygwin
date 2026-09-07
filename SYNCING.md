# Syncing with upstream xonsh

pygwin is a fork of [xonsh](https://github.com/xonsh/xonsh). It started as a light
rebrand that kept xonsh's internal package name specifically so future upstream merges
would stay small. That plan changed early in this project's history: the whole
codebase, package name, runtime magic globals, environment variable names, and
internal class names were all renamed from xonsh to pygwin. This file explains both
periods honestly, what that rename actually touched, and what it costs for syncing
with upstream going forward.

## The rename, and what it means for merging upstream

Read this before assuming a future `git merge upstream/main` will be painless. It
will not be.

Every file under what is now `pygwin/` (originally `xonsh/`) had every occurrence of
`xonsh` (in any casing: `xonsh`, `Xonsh`, `XONSH`) mechanically renamed to `pygwin`
(`pygwin`, `Pygwin`, `PYGWIN`), with two deliberate, narrow exceptions kept for
compatibility with the wider xonsh plugin ecosystem:

- The callable-alias protocol attributes `__xonsh_threadable__` and
  `__xonsh_capturable__`, a documented convention from upstream xonsh that a
  third-party alias function may already rely on. Renaming pygwin's own check for
  these would silently stop honoring that convention for anyone reusing an
  existing xonsh alias, with no error, just wrong behavior. See `pygwin/aliases.py`
  and `pygwin/procs/specs.py`.
- Shebang and interpreter-name recognition: a script whose shebang says
  `#!/usr/bin/env xonsh`, or a shebang-less script resolved via the POSIX no-shebang
  fallback, is still recognized and run with `python -m pygwin`. See
  `pygwin/procs/specs.py`'s `_un_shebang` and `get_script_subproc_command`.

Everything else that said `xonsh` now says `pygwin`, including:

- The Python package itself: `pygwin/` (was `xonsh/`), imported as `import
  pygwin.foo`, not `import xonsh.foo`.
- The `__xonsh__` runtime magic global the parser compiles subprocess mode, path
  literals, macros, and `$ENVVAR` access down to. It is `__pygwin__` now, set up in
  `pygwin/built_ins.py` and emitted by `pygwin/parsers/base.py` and
  `pygwin/parsers/ast.py`. Both sides of this contract must match exactly, or
  those features fail at first use with a bare `NameError`, not at import time.
- Every `$XONSH_*` environment variable, now `$PYGWIN_*` (`$PYGWIN_INTERACTIVE`,
  `$PYGWIN_DATA_DIR`, `$PYGWIN_HISTORY_BACKEND`, and about ninety others). The
  default data, cache, and config directories that used to be named `xonsh` on disk
  (`$XDG_DATA_HOME/xonsh`, `/etc/xonsh`, and so on) are named `pygwin` now.
- The run control file. The primary path is `~/.pygwinrc`
  (`$PYGWIN_CONFIG_DIR/rc.xsh` is the XDG-style equivalent); `get_home_xonshrc_path()`
  in `pygwin/environ.py` falls back to `~/.xonshrc` if a `.pygwinrc` doesn't exist but
  a `.xonshrc` does, so an existing xonsh rc file keeps working without a manual
  migration step.
- Every `Xonsh`-prefixed class and exception name (`XonshSession` to
  `PygwinSession`, `XonshError` to `PygwinError`, `XonshLexer` to `PygwinLexer`, and
  about twenty others).
- Every function and variable named after xonsh (`get_current_xonsh` to
  `get_current_pygwin`, `xonsh_data_dir` to `pygwin_data_dir`, the `xxonsh` alias to
  `xpygwin`, and so on), plus the pytest fixtures used across `tests/`
  (`xonsh_session` to `pygwin_session`, `xonsh_execer` to `pygwin_execer`).
- User-facing strings: error message prefixes (`"xonsh: ..."` to `"pygwin: ..."`),
  the process title set via `setproctitle`, the pygments lexer name and aliases
  (`pygwin` and `pygwincon` added alongside the kept `xonsh`/`xonshcon` aliases so
  existing ```` ```xonsh ```` code fences keep highlighting), the `pytest11`,
  `virtualenv.activate`, and `xonsh.xontribs`-style entry-point group names in
  `pyproject.toml` (the xontrib entry-point group is `pygwin.xontribs` now; see
  `pygwin/xontribs.py`).
- Real citations to specific historical PRs, issues, and third-party projects by
  name or URL (`https://github.com/xonsh/xonsh/issues/NNNN`, `xonsh PR #6192`, the
  `anki-code/xonsh-flatpak` project) were deliberately left unrenamed, because they
  are factual references to the real upstream project, not this fork.
- One pun-based Easter-egg tagline block in `pygwin/xonfig.py` (the ones built
  around "xonsh" sounding like "conch") was deliberately left unrenamed too, since
  the jokes don't survive translation and are worth keeping as a nod to where this
  shell came from.

The practical upshot: `pygwin/` is no longer a near-identical copy of xonsh's
`xonsh/` with a couple of branding strings changed. It is a genuine fork with a
large, mechanical, but total diff against upstream. A `git merge upstream/main` will
conflict on nearly every file either side touched, and resolving those conflicts
means re-applying the pygwin naming to whatever changed upstream, file by file, not
a clean three-way merge. That is a deliberate tradeoff this project's owner chose,
in exchange for a codebase that is consistently and correctly branded pygwin
throughout, including the parts a user or a debugger actually sees (tracebacks,
error messages, env var names, rc files). Don't try to quietly reintroduce the
`xonsh` name into new code "to keep merges easier"; that ship has sailed, and mixing
conventions is worse than either one consistently.

## Setting up the upstream remote

This repository was created from a shallow, single-commit copy of xonsh's `main`
branch (no upstream history was kept, so that pygwin's own git log has one author).
To pull in future xonsh changes for reference or to port a specific fix, add the
upstream repository as a remote and fetch its full history:

```
git remote add upstream https://github.com/xonsh/xonsh.git
git fetch upstream
git merge upstream/main --allow-unrelated-histories
```

Expect heavy conflicts throughout `pygwin/`, `xontrib/`, and `xompletions/` for the
reasons above. For most upstream fixes, it will be less painful to read the upstream
diff and manually port the fix into pygwin's already-renamed code than to resolve a
full merge.

## Other files that have diverged from upstream, and why

Beyond the wholesale rename above, these files changed for reasons specific to being
a different project rather than a mechanical renaming:

| File | What changed | Why |
|---|---|---|
| `pyproject.toml` | `name`, `description`, `authors`, `maintainers`, `license`, `readme` target, `[project.urls]`, `[project.scripts]`, `[tool.setuptools]` package lists, and all entry-point groups renamed to match the `pygwin` package. | Rebranding the package metadata and CLI surface to match the renamed package. |
| `pygwin/main.py` (`xonsh/main.py`) | The `-V`/`--version` output string and the `ArgumentParser` description/epilog text shown by `pygwin --help`. | User-facing CLI strings naming the shell. |
| `LICENSE` | Replaced xonsh's BSD 2-Clause text with the GNU GPL-3.0 text. | pygwin is licensed under the GPL so that it, and anything built on it, must always stay open source. The original BSD notice is preserved in full in `CREDITS.md`, as BSD requires and as GPL relicensing of a BSD-licensed work permits. |
| `README.md`, `CHANGELOG.md` | Replaced with pygwin's own. | Upstream's README and changelog describe the xonsh project, its own release history, and its own community; they do not describe this fork. |
| `AUTHORS.rst`, `.authors.yml`, `.mailmap`, `CONTRIBUTING.md`, `AI_POLICY.md`, `CLAUDE.md` | Removed. | These describe xonsh's own contributor process and community policy, which pygwin, a personal daily-driver project, does not run. The contributor record they held stays canonical in the upstream xonsh repository; see `CREDITS.md`. |
| `.release-please-manifest.json`, `release-please-config.json`, `.github/workflows/release-please.yml`, `.github/workflows/publish.yml`, `.github/workflows/nightly-build.yml` | Removed. | Upstream's automated release and PyPI publishing pipeline. pygwin ships its own releases as a Nuitka-built Windows executable via `.github/workflows/cd.yml`, on a manual cadence, not an automated one. |
| `.github/workflows/docs.yml` | Removed. | Upstream's Sphinx documentation build and publish pipeline. pygwin's GitHub Pages site is a single static `docs/index.html`, deployed by `.github/workflows/pages.yml`. |
| `.github/workflows/nix-build.yml`, `.github/workflows/update-flake-lock.yml`, `flake.nix`, `flake.lock`, `nix/`, `appimage/`, `ci/condarc.yml`, `.devcontainer/`, `xonsh-in-docker.py`, `adsfund.json` | Removed. | Distribution channels and CI infrastructure (Nix, conda, AppImage, devcontainers, Docker demo scripts, ads funding metadata) that do not apply to a Windows-first, Nuitka-distributed personal shell. |
| `.github/workflows/test.yml` | Replaced by `.github/workflows/ci.yml`. | Same purpose (lint plus pytest on push/PR to `main`), rewritten against pygwin's own tooling and OS matrix rather than upstream's. |
| `.github/workflows/check-pr-title.yml` | Removed. | pygwin does not accept pull requests; see `AGENTS.md`. |
| `pygwin/platform.py` -> `pygwin/platform_info.py` | Renamed (originally as `xonsh/platform.py` -> `xonsh/platform_info.py`, before the wholesale rename moved it under `pygwin/`). | Works around a real bug in Nuitka's standalone compiler: a package submodule that shares its exact basename with a stdlib module (`platform.py` vs. Python's own `platform`) gets its bare `import platform` statement resolved back to itself by Nuitka's compiled import table, instead of to the real stdlib module. Confirmed directly (the object handed back carried the submodule's own attributes, not stdlib's), reproduces in both Nuitka onefile and standalone modes, does not reproduce under plain CPython, and is not escapable from pure Python source (even `importlib.import_module("platform")` gets intercepted the same way). |
| Scripts renamed: `scripts/xon.sh` -> `scripts/pygwin.sh`, `scripts/xonsh.ps1` -> `scripts/pygwin.ps1`, `xompletions/_xonsh.py` -> `xompletions/_pygwin.py`, `pygwin/webconfig/xonsh_data.py` -> `pygwin/webconfig/pygwin_data.py`, `tests/test_xonsh.xsh` -> `tests/test_pygwin.xsh` | Renamed to match what they contain or complete. | The launcher scripts invoke `python -m pygwin` now; `xompletions/_pygwin.py` is discovered by basename to provide completions for the `pygwin` command; `pygwin_data.py` matches its module's own import name used by `pygwin/webconfig/routes.py`. |
| New: `AGENTS.md`, `SYNCING.md`, `ROADMAP.md`, `CREDITS.md` | Added. | pygwin-specific process and attribution documentation with no xonsh upstream equivalent. |
| `docs/` (Sphinx source) | Given the same mechanical rename as the rest of the codebase, then audited later to finish it: `xonsh_session.rst`/`xonsh_projects.rst`/`xonshrc.{rst,py,xsh}`/`xonshconfig.json` renamed to their `pygwin`-named equivalents (their content already said pygwin; only the filenames, and the env vars inside `xonshrc.xsh`, had been missed, which had left real broken `:doc:`/`:download:`/`literalinclude` references). Also removed rather than relabeled: the entire unused upstream marketing site (`docs/_templates/index.html` and its `landing`/`landing2` asset trees, plus `xonsh-demo.gif` and similar demo images) since it is not built or served by anything in this repo and is full of real xonsh stats and community links that would become false claims if merely relabeled `pygwin`; `docs/install_mamba.rst`, `docs/appimage.rst`, `docs/containers.rst`, and the mamba/WinGet/Flatpak/Docker/AppImage/conda sections of `docs/install.rst`, none of which pygwin actually ships (see the nix/conda/AppImage removal above); `docs/contact.rst`, `docs/links.rst`, `docs/contributing.rst`, and the community/sponsor/PR-review bullets in `docs/contents.rst` and `docs/developer.rst`, which presented pygwin as having xonsh's own Zulip/Mastodon/Gitter/sponsors/merch/PR process; and the `runthis` Sphinx extension, which pointed at a live third-party server (`runthis.xonsh.org`) pygwin has no relationship to. | This tree is still not built or served by anything in this repo (see below), but it shouldn't say `xonsh` throughout a `pygwin` repo, and it shouldn't describe processes or infrastructure this fork doesn't actually have either. |
| `pygwin/webconfig/index.html`, `pygwin/webconfig/js/xonsh_sticker*` | The `xonfig` web wizard's page title and navbar brand text changed from "Xonsh" to "Pygwin"; the `xonsh_sticker.svg`/`xonsh_sticker_mini.png` logo image was removed rather than relabeled, since pygwin has no equivalent logo to replace it with. | Same reasoning as the `docs/` marketing assets above: a real, live-served page shouldn't say Xonsh, and there's nothing honest to rename the mascot artwork to. |

## What has never diverged structurally

The file layout, the parser/execer architecture, the shell backends, the completion
system, and effectively all of xonsh's actual logic. This is a rename, not a
rewrite: every function does what its xonsh equivalent did, under a new name.
`tests/`, `setup.cfg`, `conftest.py`, `MANIFEST.in`, `.pre-commit-config.yaml`,
`.coveragerc`, `.gitattributes`, `.gitignore`, and `docs/` (present but unbuilt) all
exist and are organized exactly as upstream's, just renamed in place.

## Sync cadence

There is no fixed cadence. Given the rename, treat "syncing with upstream" as
"reading upstream's diff for a specific fix or feature and porting it by hand into
pygwin's renamed code," not as running `git merge` and resolving what comes up.
Update this file if you port something that changes what's listed above.
