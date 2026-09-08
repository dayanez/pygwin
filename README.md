<p align="center">
  <img src="docs/_static/pygwin_terminal_icon_256.png" alt="pygwin logo" width="120">
</p>

# pygwin

A Shell enviroment with the idea of minmal and pragmatic. 

Pygwin plans to provide, live CPU and memory telemetry in the prompt.
Automatic, transparent tuning of the heavy commands you run every day. A shell you can
install by clicking one `.exe`, not by standing up a Python environment first.

This README covers what pygwin is, how to run it today, and how to use what is
already built. For the deep technical reasoning behind a specific change, real
measurements included, see this repository's git history and
[CHANGELOG.md](CHANGELOG.md).

## Table of contents

- [Why pygwin](#why-pygwin)
- [Status](#status)
- [Installation](#installation)
- [Quickstart](#quickstart)
- [Wiki](#wiki)
  - [Running pygwin](#running-pygwin)
  - [Built on xonsh's engine](#built-on-xonshs-engine)
  - [Configuration](#configuration)
  - [Extending pygwin: pgtribs](#extending-pygwin-pgtribs)
  - [The coreutils bundled in](#the-coreutils-bundled-in)
  - [System observability: the sysinfo pgtrib](#system-observability-the-sysinfo-pgtrib)
  - [Process auto-tuning: the autotune pgtrib](#process-auto-tuning-the-autotune-pgtrib)
  - [Command line reference](#command-line-reference)
- [Performance philosophy](#performance-philosophy)
- [Building the standalone executable](#building-the-standalone-executable)
- [Repository layout](#repository-layout)
- [Contributing](#contributing)
- [License](#license)
- [Credits](#credits)

## Why pygwin

Most shells make you choose between power and speed. `cmd.exe` and PowerShell start
fast and know nothing about Python. A Python REPL knows Python and nothing about being
a shell. 

pygwin takes that foundation and points it at two goals that a general-purpose,
cross-platform shell cannot fully commit to:

1. **Fast and lean** A default configuration that does not spend your
   launch time probing bash and zsh for environment variables you do not have, or
   importing an interactive line editor you might not need.
2. **A shell that watches your machine, not just your commands.** Background system
   telemetry and workflow-aware process tuning, built in, not bolted on with a script
   you have to remember to run.


## Installation

pygwin targets most operating systems. It plans to be a cross-platform engine, but Windows is the platform
this is tuned and tested for.

### From source (today)

```
git clone https://github.com/dayanez/pygwin.git
cd pygwin
pip install -e ".[full]"
python scripts/build_parser_tables.py
```

That last line is optional but recommended: pygwin's parser tables are generated on
first use and cached from then on, but generating them from scratch takes about 1.8
seconds. Skipping this step just means whatever command you type first pays that
cost once, silently, instead of paying it here with an explanation.

The `[full]` extra pulls in the interactive line editor (`prompt_toolkit`) and syntax
highlighting (`pygments`). pygwin still defaults to its own fast `readline` backend
even with `[full]` installed; add `$SHELL_TYPE = 'prompt_toolkit'` (or `'best'`) to
your [`~/.pygwinrc`](#configuration) to actually use the richer editor once it's
installed. On Windows, plain `pip install pygwin` (no extras) also pulls in
[`pyreadline3`](https://pypi.org/project/pyreadline3/), since Windows ships no
`readline` module of its own and the default backend needs a real one to be worth
using.

### Standalone executable

Every release publishes a Nuitka-compiled `pygwin.exe` for Windows under this
repository's [Releases](https://github.com/dayanez/pygwin/releases) page. Download it,
run it, no Python installation required. See
[Building the standalone executable](#building-the-standalone-executable) for how it is
built, and its current limitations.

## Quickstart

```
pygwin
```

drops you into an interactive session. From there:

```xsh
# Run Python directly.
print("hello from pygwin")

# Run subprocess commands directly, no different from any other shell.
ls -la

# Mix both in the same expression.
files = $(ls -la).split('\n')
print(len(files))

# Check the version and confirm you are on pygwin.
pygwin --version
```

Exit with `exit`, `Ctrl-D`, or `Ctrl-Z` then Enter on Windows.

## Wiki

### Running pygwin

The installed command is `pygwin`, not `xonsh`. If you installed with `pip install -e
".[full]"` inside a virtual environment, either activate the environment first or call
`.venv\Scripts\pygwin.exe` directly.

Run a single command and exit, without an interactive session:

```
pygwin -c "print(1 + 1)"
```

Run a script file:

```
pygwin myscript.xsh
```


### Configuration

pygwin's run control file is `~/.pygwinrc`, and only `~/.pygwinrc`; an existing
`~/.xonshrc` from a real xonsh install (or an older pygwin install) is not read
automatically, so migrate anything you want kept into a new `~/.pygwinrc` by hand.
Anything you could put in a `.xonshrc` file works in a `.pygwinrc` too: environment
variables, aliases, prompt customization, and pgtrib loading, as long as the
pgtrib itself is one pygwin actually ships (real xonsh xontribs like `sysstats`
are not bundled; pygwin's own equivalent for live CPU/memory telemetry is
`sysinfo`, see below).

A minimal example:

```xsh
# Set a custom prompt.
$PROMPT = '{env_name}{BOLD_GREEN}{user}@{hostname}{RESET} {cwd} ) '

# Add an alias.
aliases['gs'] = 'git status'

# Load a pgtrib.
pgtrib load coreutils
```

### Extending pygwin: pgtribs

pygwin inherits a plugin system. A pgtrib is a Python or `.xsh`
file that defines a `_load_pgtrib_(xsh, **_)` function and registers aliases, prompt
fields, or event hooks. This is also how pygwin adds its own features without editing
core files: see `pgtrib/coreutils.py` in this repository for a simple example that
registers the bundled coreutils aliases.

List what is available and loaded:

```
pgtrib list
```

Load one manually:

```
pgtrib load <name>
```

Every pygwin-only feature, telemetry, auto-tuning, cached process lookups, ships as
a pgtrib or a new top-level module, not a patch scattered across existing core
files.

### The coreutils bundled in

pygwin ships cross-platform, pure-Python reimplementations of common Unix utilities,
: `cat`, `echo`, `pwd`, `tee`, `tty`, `uname`, `uptime`, `umask`,
and `yes`. They are not loaded by default. Load them with:

```
pgtrib load coreutils
```

These avoid spawning a real subprocess for simple operations and work identically on
Windows, macOS, and Linux.

### System observability: the sysinfo pgtrib

The first piece of pygwin's actual differentiator: live CPU and memory telemetry,
exposed both in the prompt and as a `pygwin-top` command. It ships in the box but is
not loaded by default, since it needs `psutil`, an optional dependency:

```
pip install "pygwin[observability]"   # or pip install "pygwin[full]", which includes it
pgtrib load sysinfo
```

Once loaded, a background thread polls CPU and memory usage every couple of seconds
and never blocks the prompt: reading the latest sample is a cheap in-memory lookup,
not a fresh syscall. Two new prompt fields become available:

```xsh
$PROMPT = $PROMPT.replace("{prompt_end}", "{cpu}% cpu {mem}% mem {prompt_end}")
```

And a live-refreshing process view, similar to `top` or `htop`, is available as:

```
pygwin-top
```

Press Ctrl+C to exit it. It is a separate, on-demand foreground command: unlike the
prompt-field telemetry thread, it is allowed to block while it runs, since the user
asked for it directly.

### Process auto-tuning: the autotune pgtrib

Also opt-in, also needs `psutil` (the same `observability` extra covers it):

```
pgtrib load autotune
```

Once loaded, right after any command known to be typically CPU-heavy (compilers,
build tools, renderers, encoders, archivers, a fixed list covering things like
`gcc`, `rustc`, `cargo`, `msbuild`, `ffmpeg`, `blender`, `7z`, `docker`) finishes
launching, pygwin nudges its OS priority down a notch so it doesn't make the rest of
the shell feel sluggish while it runs. It never does this quietly:

```
pygwin: lowered priority of 'ffmpeg.exe' (pid 12345) to keep the shell responsive.
Run 'pygwin-tune restore 12345' to undo.
```

```
pygwin-tune list             # see everything currently adjusted this session
pygwin-tune restore 12345    # put one process back to its original priority
pygwin-tune restore all      # put everything back
```

Nothing here is permanent: it only ever changes a live process's own priority, which
disappears the moment that process exits either way. The list of recognized command
names can be overridden with `$PYGWIN_AUTOTUNE_COMMANDS` (an iterable of names) if
the defaults don't match what actually runs heavy on your machine.

### Command line reference

| Flag | What it does |
|---|---|
| `pygwin` | Start an interactive session. |
| `pygwin -c "<code>"` | Run a single command or expression and exit. |
| `pygwin <script.xsh>` | Run a script file. |
| `pygwin -V`, `pygwin --version` | Print the pygwin version. |
| `pygwin -h`, `pygwin --help` | Print help, including the `format`, `check`, and `lint` subcommands. |
| `pygwin format` | Format pygwin source files. |
| `pygwin check` | Check source files for syntax errors without running them. |
| `pygwin lint` | Lint source files for likely mistakes. |

## Performance philosophy

A shell like xonsh which aims for a similar goal, typically takes somewhere in the range of 150 to 300 milliseconds to
reach an interactive prompt, because it imports a genuinely large amount on startup:
`prompt_toolkit`, foreign shell detection for bash, zsh, and `cmd.exe`, a rich history
backend, and the xontrib plugin scanner, all before you type anything.

pygwin's position is not that a Python shell should try to match a native C or Go
shell's single-digit-millisecond startup. That is not a fight Python wins, and chasing
it would mean stripping away the parts of xonsh that make it worth using in the first
place. Instead, the work was to find and fix the real, measured, avoidable costs:

- `readline`, not `prompt_toolkit`, is the default interactive backend.
  `prompt_toolkit` stays strictly opt-in even when it's installed. This also meant
  fixing an eager import that pulled in `prompt_toolkit` just to compute the default
  `$PROMPT`, regardless of which backend was actually selected. Measured with
  `scripts/measure_shell_startup.py`: shell construction went from about 322ms to
  about 246ms.
- Several modules that loaded unconditionally on every launch (an OS-detection call
  that shelled out to WMI on Windows, `sqlite3` for a history backend that isn't the
  default, `ctypes` and `shutil` outside the one function each that used them) now
  load lazily instead. Measured with `python -X importtime -c "import pygwin.main"`:
  cumulative import time went from about 278ms to about 100ms.
- Foreign shell (bash/zsh/`cmd.exe`) environment probing was checked and found to
  already be opt-in only, never automatic at startup; there was nothing to fix.
- Replacing the default JSON history backend with something lighter was investigated
  and deliberately not done: constructing it measures at under 1ms, so there was no
  real cost to justify rewriting it.

Where pygwin spends its complexity budget instead is observability: a background
telemetry thread, transparent process tuning for heavy commands, and cached binary
resolution. A shell that is merely fast is a solved problem. A shell that is fast
enough and also tells you what your machine is doing is the actual goal here.

## Building the standalone executable

Releases are built with [Nuitka](https://nuitka.net/), which compiles pygwin's Python
source to C and links it into a native Windows executable. The build workflow lives at
`.github/workflows/cd.yml` and runs on every tagged release.

To build locally:

```
pip install -e ".[full]"
pip install nuitka zstandard
python scripts/build_parser_tables.py
python -m nuitka --standalone --onefile --onefile-cache-mode=cached --output-filename=pygwin.exe --enable-plugin=no-qt --no-deployment-flag=self-execution --company-name=pygwin --product-name=pygwin --windows-icon-from-ico=docs/_static/pygwin.ico --include-module=pygwin.parser_table --include-module=pygwin.completion_parser_table --include-package=pgtrib --include-package=pgcompletions pygwin/__main__.py
```

`--windows-icon-from-ico` is optional (drop it and Nuitka falls back to a generic
executable icon) but is what gives `pygwin.exe` its logo in Explorer and the taskbar;
the CD workflow always passes it.

Building locally uses every CPU core by default, which can make the machine sluggish for
several minutes. Add `--jobs=N` (or a negative number, meaning "all cores minus N") to
cap it, e.g. `--jobs=-4` to leave 4 cores free.

Both extra lines matter, not just the Nuitka invocation. Skip the table pre-build and
Nuitka simply won't find it (parser tables are generated on first use, and don't exist
until then); skip the `--include-module` flags and Nuitka's static import scanner won't
notice the pre-built tables exist at all, since PLY loads them by a dynamic string
module name, not a literal `import` statement. Without both, the compiled `pygwin.exe`
regenerates its parser tables from scratch on every single launch, adding about 1.8
seconds to it, silently.

`--onefile-cache-mode=cached` matters too, for a different reason. Onefile mode's
default (`auto`) infers `temporary` extraction whenever the tempdir spec has any
runtime-dependent part, and Nuitka's own default spec
(`{TEMP}/onefile_{PID}_{TIME_US}_{RANDOM}`) always does. That means every launch of
`pygwin.exe`, without this flag, fully re-extracts the whole payload to a brand-new
temp folder and deletes it on exit, with no warm-cache benefit between runs at all.
`cached` reuses the extracted contents across runs instead. `cached` mode also
changes the default extraction path to include a company/product name, so
`--company-name`/`--product-name` must be set too or Nuitka refuses to build.

`--include-package=pgtrib`/`--include-package=pgcompletions` matter for the same
reason the parser tables do: both packages are loaded entirely by dynamic,
string-based `importlib` lookups (`pgtrib load <name>`, and command-name-based
completer discovery), never a literal `import pgtrib.sysinfo`-style statement
anywhere in the codebase, so Nuitka's static import scanner has no way to know
either package exists at all. Without these flags, the compiled `pygwin.exe`
cannot load any pgtrib, including `sysinfo` and `autotune`, or any command
completer from `pgcompletions`, and fails with `ModuleNotFoundError` the moment
something tries.

Measured directly against a real compiled `pygwin.exe`, on this dev machine: first
run (cold, nothing cached yet) about 900ms to 1s; every run after that about
480-500ms, reusing the cache directory instead of re-extracting. Before
`--onefile-cache-mode=cached`, every single run, cold or not, took about 900ms, since
there was no warm-cache benefit at all. Installing the `zstandard` package before
building (`pip install zstandard`) also lets Nuitka compress the onefile payload,
which cut this build from about 74MB uncompressed to a 19MB `.exe`.

That 19MB, ~490ms build installs with `pip install -e ".[full]"` (prompt_toolkit,
pygments, and psutil for the `sysinfo`/`autotune` pgtribs, all bundled in). A build
from a plain `pip install -e .` instead, with none of those, measured smaller (11MB)
and faster (about 400ms steady-state) in the same test, but can't run `best`-shell
mode or the observability pgtribs at all, since the code they need was never
importable at compile time. The CD workflow ships the `[full]` build so the
compiled `.exe` has every feature the source install does; the 30 to 60 millisecond
target mentioned above is about interpreter startup and shell construction inside a
running Python process, not the onefile `.exe`'s own extract-and-launch overhead,
which is a separate cost specific to this distribution method.

## Repository layout

```
pygwin/         the shell engine, parser, and built-in shells (a renamed fork of xonsh's own xonsh/)
pgtrib/         plugin extensions, including pygwin's own additions
pgcompletions/  completion providers for external commands
tests/          the pytest suite
docs/           upstream Sphinx documentation source, plus docs/index.html (this project's
                GitHub Pages site, a separate, unrelated static page)
```

See [AGENTS.md](AGENTS.md) for the full breakdown and the rule that governs where new
code belongs.

## Contributing

pygwin is a personal daily-driver project, not a team codebase, If there is an issue, contact me via dommcpro@gmail.com and or make an issue and pull request. 

## License

pygwin is licensed under the [GNU General Public License v3.0 or later](LICENSE). It
must remain open source. That is a license condition, not a preference.

## Credits

pygwin is a fork of [xonsh](https://github.com/xonsh/xonsh), built by the xonsh
developers and its community. See [CREDITS.md](CREDITS.md) for the full attribution,
including the original license text this fork is built on top of.
