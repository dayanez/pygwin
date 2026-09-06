# pygwin

A Windows-first, Python-powered shell and system observability console. pygwin is a
fork of [xonsh](https://github.com/xonsh/xonsh): the same battle-tested Python shell
engine and parser, renamed throughout, wearing a leaner default configuration and a
different mission.

xonsh already proved that a shell can run real Python, mixed freely with subprocess
calls, in one interactive session. pygwin starts from that and asks a second question:
what does a shell look like if it is also the tool you reach for to understand what
your machine is doing while it does it? Live CPU and memory telemetry in the prompt.
Automatic, transparent tuning of the heavy commands you run every day. A shell you can
install by clicking one `.exe`, not by standing up a Python environment first.

If you want the deep technical reasoning and the phase-by-phase build plan, see
[ROADMAP.md](ROADMAP.md). This README covers what pygwin is, how to run it today, and
how to use what is already built.

## Table of contents

- [Why pygwin](#why-pygwin)
- [Status](#status)
- [Installation](#installation)
- [Quickstart](#quickstart)
- [Wiki](#wiki)
  - [Running pygwin](#running-pygwin)
  - [Built on xonsh's engine](#built-on-xonshs-engine)
  - [Configuration](#configuration)
  - [Extending pygwin: xontribs](#extending-pygwin-xontribs)
  - [The coreutils bundled in](#the-coreutils-bundled-in)
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
a shell. xonsh already closed that gap: it is a real shell with real Python semantics,
subprocess syntax, and a plugin system, all at once.

pygwin takes that foundation and points it at two goals that a general-purpose,
cross-platform shell cannot fully commit to:

1. **Fast, lean, Windows-first.** A default configuration that does not spend your
   launch time probing bash and zsh for environment variables you do not have, or
   importing an interactive line editor you might not need.
2. **A shell that watches your machine, not just your commands.** Background system
   telemetry and workflow-aware process tuning, built in, not bolted on with a script
   you have to remember to run.

Neither of those is finished. See [Status](#status).

## Status

pygwin is in an early, honest state. What exists today:

- A working fork of xonsh, renamed throughout: install it, run `pygwin`, and you have
  a full xonsh-class shell under its own name, top to bottom.
- A CI pipeline that lints and tests every push and pull request.
- A CD pipeline that builds a standalone Windows `.exe` with [Nuitka](https://nuitka.net/)
  on release.
- This README, [ROADMAP.md](ROADMAP.md), [SYNCING.md](SYNCING.md), and
  [AGENTS.md](AGENTS.md) as the documentation and process backbone.

What does not exist yet, and is tracked honestly rather than oversold:

- The actual startup-time and memory stripping work (dropping `prompt_toolkit` as the
  default backend, lazy imports, a lighter history backend). Today's release still
  starts up like xonsh does, because it mostly still is xonsh.
- The live telemetry prompt, process auto-tuning, and cached subprocess proxying
  features that motivate this project in the first place.

Read [ROADMAP.md](ROADMAP.md) for the full plan and its reasoning. This is a
daily-driver project built and maintained by one person, not a company or a team, so
progress happens in real, dated commits rather than a marketing timeline.

## Installation

pygwin targets **Windows first**, Python 3.11 or newer. It also runs anywhere xonsh
does, since it is built on the same cross-platform engine, but Windows is the platform
this fork is tuned and tested for.

### From source (today)

```
git clone https://github.com/dayanez/pygwin.git
cd pygwin
pip install -e ".[full]"
```

The `[full]` extra pulls in the interactive line editor (`prompt_toolkit`) and syntax
highlighting (`pygments`). Without it, pygwin still runs, using Python's built-in
readline-style input instead.

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

### Built on xonsh's engine

pygwin is a fork of xonsh's parser, execer, and shell engine, not a rewrite. Every
function does what its xonsh equivalent did; the whole codebase, including the
Python package name, the environment variable names, and internal class names, was
renamed from xonsh to pygwin throughout. See [SYNCING.md](SYNCING.md) for exactly
what that rename touched, what was deliberately kept for compatibility (a couple of
xonsh's plugin-alias protocol details, and recognizing `#!/usr/bin/env xonsh`
shebangs), and what it costs going forward (pulling in upstream xonsh fixes now means
porting them by hand, not a clean merge).

Practically, this means almost everything written about xonsh's own language and
semantics still applies to pygwin: Python-in-the-shell syntax, subprocess mode,
the prompt formatting language, the xontrib plugin model. The specifics that changed
are the package name, the `$PYGWIN_*` environment variable names (where xonsh used
`$XONSH_*`), and the `~/.pygwinrc` config file name. pygwin does not attempt to
duplicate xonsh's own documentation here. What this README documents is what is
different: the name, the defaults, and the roadmap.

### Configuration

pygwin's primary run control file is `~/.pygwinrc`. If that doesn't exist but an
`~/.xonshrc` does (carried over from xonsh, or from an older pygwin install), pygwin
reads that instead, so nothing breaks on upgrade. Anything you could put in a
`.xonshrc` file works in a `.pygwinrc` too: environment variables, aliases, prompt
customization, and xontrib loading.

A minimal example:

```xsh
# Set a custom prompt.
$PROMPT = '{env_name}{BOLD_GREEN}{user}@{hostname}{RESET} {cwd} ) '

# Add an alias.
aliases['gs'] = 'git status'

# Load an xontrib.
xontrib load coreutils
```

### Extending pygwin: xontribs

pygwin inherits xonsh's plugin system, called xontribs. A xontrib is a Python or `.xsh`
file that defines a `_load_xontrib_(xsh, **_)` function and registers aliases, prompt
fields, or event hooks. This is also how pygwin adds its own features without editing
core files: see `xontrib/coreutils.py` in this repository for a simple example that
registers the bundled coreutils aliases.

List what is available and loaded:

```
xontrib list
```

Load one manually:

```
xontrib load <name>
```

Every feature on the [roadmap](ROADMAP.md), telemetry, auto-tuning, cached process
lookups, is planned as a xontrib or a new top-level module, not a patch scattered
across existing core files.

### The coreutils bundled in

pygwin ships cross-platform, pure-Python reimplementations of common Unix utilities,
inherited from xonsh: `cat`, `echo`, `pwd`, `tee`, `tty`, `uname`, `uptime`, `umask`,
and `yes`. They are not loaded by default. Load them with:

```
xontrib load coreutils
```

These avoid spawning a real subprocess for simple operations and work identically on
Windows, macOS, and Linux.

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

xonsh, unmodified, typically takes somewhere in the range of 150 to 300 milliseconds to
reach an interactive prompt, because it imports a genuinely large amount on startup:
`prompt_toolkit`, foreign shell detection for bash, zsh, and `cmd.exe`, a rich history
backend, and the xontrib plugin scanner, all before you type anything.

pygwin's position is not that a Python shell should try to match a native C or Go
shell's single-digit-millisecond startup. That is not a fight Python wins, and chasing
it would mean stripping away the parts of xonsh that make it worth using in the first
place. The realistic target, once the work described in [ROADMAP.md](ROADMAP.md) lands,
is closer to 30 to 60 milliseconds: a readline-based default backend instead of
`prompt_toolkit`, lazy imports for anything not needed on the cold path, no foreign
shell probing unless asked for, and a lighter default history backend.

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
pip install nuitka
python -m nuitka --standalone --onefile --output-filename=pygwin.exe --enable-plugin=no-qt --no-deployment-flag=self-execution pygwin/__main__.py
```

The current release is a baseline: it compiles today's codebase as-is, not the
stripped-down build described in the roadmap. Expect it to be sizable
and its startup time to reflect xonsh's own, not the 30 to 60 millisecond target above.
Rebuilding after the phase-two work in [ROADMAP.md](ROADMAP.md) lands is itself a
roadmap item.

## Repository layout

```
pygwin/       the shell engine, parser, and built-in shells (a renamed fork of xonsh's own xonsh/)
xontrib/      plugin extensions, including pygwin's own additions
xompletions/  completion providers for external commands
tests/        the pytest suite
docs/         upstream Sphinx documentation source, plus docs/index.html (this project's
              GitHub Pages site, a separate, unrelated static page)
```

See [AGENTS.md](AGENTS.md) for the full breakdown and the rule that governs where new
code belongs.

## Contributing

pygwin is a personal daily-driver project, not a team codebase, and it does not accept
issues or pull requests. If you want a different feature set, fork it, the same way
this project forked xonsh: openly, with credit, under a license that requires both.

## License

pygwin is licensed under the [GNU General Public License v3.0 or later](LICENSE). It
must remain open source. That is a license condition, not a preference.

## Credits

pygwin is a fork of [xonsh](https://github.com/xonsh/xonsh), built by the xonsh
developers and its community. See [CREDITS.md](CREDITS.md) for the full attribution,
including the original license text this fork is built on top of.
