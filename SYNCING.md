# Syncing with upstream xonsh

pygwin is a light fork of [xonsh](https://github.com/xonsh/xonsh). This file is the
single source of truth for what has ever diverged from upstream, and why, so that
pulling in future xonsh changes stays a small, predictable diff instead of an
archaeology project.

## Setting up the upstream remote

This repository was created from a shallow, single-commit copy of xonsh's `main`
branch (no upstream history was kept, so that pygwin's own git log has one author).
To pull in future xonsh changes, add the upstream repository as a remote and fetch
its full history before merging:

```
git remote add upstream https://github.com/xonsh/xonsh.git
git fetch upstream
git merge upstream/main --allow-unrelated-histories
```

Expect conflicts only in the files listed below; everything else under `xonsh/`,
`xontrib/`, and `xompletions/` should merge cleanly because pygwin does not edit it.

## Files that have diverged from upstream, and why

| File | What changed | Why |
|---|---|---|
| `pyproject.toml` | `name`, `description`, `authors`, `maintainers`, `license`, `readme` target, `[project.urls]`, and `[project.scripts]` (entry points renamed from `xonsh`/`xonsh-cat`/`xonsh-uname`/`xonsh-uptime` to `pygwin`/`pygwin-cat`/`pygwin-uname`/`pygwin-uptime`). Added a new `[project.entry-points."xonsh.xontribs"]` entry for `banner = "xontrib.banner"`. | Rebranding the package metadata and CLI surface without touching the internal `xonsh` package name, so the bulk of the file's dependency and tooling configuration stays untouched and mergeable. |
| `xonsh/main.py` | The `-V`/`--version` output string, and the `ArgumentParser` description and epilog text shown by `pygwin --help` / `pygwin format --help` / etc. | These are the only user-facing CLI strings that name the shell; everything else in this file is upstream's argument parsing logic and is untouched. |
| `LICENSE` | Replaced xonsh's BSD 2-Clause text with the GNU GPL-3.0 text. | pygwin is licensed under the GPL so that it, and anything built on it, must always stay open source. The original BSD notice is preserved in full in `CREDITS.md`, as BSD requires and as GPL relicensing of a BSD-licensed work permits. |
| `README.md`, `CHANGELOG.md` | Replaced with pygwin's own. | Upstream's README and changelog describe the xonsh project, its own release history, and its own community; they do not describe this fork. |
| `AUTHORS.rst`, `.authors.yml`, `.mailmap`, `CONTRIBUTING.md`, `AI_POLICY.md`, `CLAUDE.md` | Removed. | These describe xonsh's own contributor process and community policy, which pygwin, a personal daily-driver project, does not run. The contributor record they held stays canonical in the upstream xonsh repository; see `CREDITS.md`. |
| `.release-please-manifest.json`, `release-please-config.json`, `.github/workflows/release-please.yml`, `.github/workflows/publish.yml`, `.github/workflows/nightly-build.yml` | Removed. | Upstream's automated release and PyPI publishing pipeline. pygwin ships its own releases as a Nuitka-built Windows executable via `.github/workflows/cd.yml`, on a manual cadence, not an automated one. |
| `.github/workflows/docs.yml` | Removed. | Upstream's Sphinx documentation build and publish pipeline. pygwin's GitHub Pages site is a single static `docs/index.html`, deployed by `.github/workflows/pages.yml`. |
| `.github/workflows/nix-build.yml`, `.github/workflows/update-flake-lock.yml`, `flake.nix`, `flake.lock`, `nix/`, `appimage/`, `ci/condarc.yml`, `.devcontainer/`, `xonsh-in-docker.py`, `adsfund.json` | Removed. | Distribution channels and CI infrastructure (Nix, conda, AppImage, devcontainers, Docker demo scripts, ads funding metadata) that do not apply to a Windows-first, Nuitka-distributed personal shell. |
| `.github/workflows/test.yml` | Replaced by `.github/workflows/ci.yml`. | Same purpose (lint plus pytest on push/PR to `main`), rewritten against pygwin's own tooling and OS matrix rather than upstream's. |
| `.github/workflows/check-pr-title.yml` | Removed. | pygwin does not accept pull requests; see `AGENTS.md`. |
| New: `xontrib/banner.py` | Added. | Prints the pygwin interactive welcome banner via the standard xontrib entry point mechanism, so no existing xonsh file needed to change to add branded startup text. |
| New: `AGENTS.md`, `SYNCING.md`, `ROADMAP.md`, `CREDITS.md` | Added. | pygwin-specific process and attribution documentation with no xonsh upstream equivalent. |

## What has never diverged

Everything under `xonsh/` other than the two lines in `main.py` above. Everything
under `xompletions/`. All existing files under `xontrib/` other than the new
`banner.py`. `tests/`, `setup.cfg`, `conftest.py`, `MANIFEST.in`, `.pre-commit-config.yaml`,
`.coveragerc`, `.gitattributes`, `.gitignore`, and the upstream `docs/` Sphinx source
tree (present but unbuilt; see the table above).

## Sync cadence

There is no fixed cadence yet. Pull from upstream when a specific xonsh fix or feature
is wanted, or when phase two of `ROADMAP.md` is about to touch a file that has drifted
far enough from upstream that a later merge would be painful otherwise. Every sync
merge should update this file if it touches anything not already listed above.
