# Changelog

All notable changes to pygwin are recorded here. This file starts from pygwin's own
first commit; for xonsh's history before the fork, see
[xonsh's changelog](https://github.com/xonsh/xonsh/blob/main/CHANGELOG.md).

## Unreleased

- Forked xonsh into pygwin: renamed the CLI entry point and `--version` string,
  replaced the license and README, and set up CI, a Nuitka-based release build, and
  a GitHub Pages site.
- Renamed the entire codebase from xonsh to pygwin: the Python package itself
  (`xonsh/` to `pygwin/`), the `__xonsh__` runtime global (to `__pygwin__`), every
  `$XONSH_*` environment variable (to `$PYGWIN_*`), and every `Xonsh`-prefixed class
  and function name. Kept two narrow compatibility exceptions (the callable-alias
  protocol attributes, and recognizing `#!/usr/bin/env xonsh` shebangs) so scripts
  and aliases written for xonsh mostly keep working. See SYNCING.md.
- Along the way, found and fixed a real bug in Nuitka's standalone compiler
  (a package submodule sharing a stdlib module's basename gets resolved to itself)
  by renaming `platform.py` to `platform_info.py`, and fixed a pyproject.toml bug
  where self-referencing optional-dependency groups were silently pulling the real
  xonsh package down from PyPI instead of resolving to this fork.
- Disabled the interactive welcome message by default
  (`$XONSH_SUPPRESS_WELCOME`/`$PYGWIN_SUPPRESS_WELCOME` now defaults to `True`), so
  `pygwin` starts a plain interactive session with no banner or first-run prompt.
