<p align="center">
  <img src="docs/_static/pygwin_terminal_icon_256.png" alt="pygwin logo" width="120">
</p>

# pygwin

Aims to be a Python-powered shell. You get real Python and subprocess commands mixed freely in one interactive session, plus other features such as  `sysinfo` pgtrib for live CPU/memory telemetry in the prompt, and an `autotune` pgtrib that quietly lowers the OS priority of heavy commands (compilers,encoders, build tools) while they run so the rest of the shell stays responsive. Both are optional and off by default.

For the full command reference, configuration options, and everything else pygwin can do, see the
docs in [`docs/`](docs/) and [CHANGELOG.md](CHANGELOG.md).

## Installation

### From source

```
git clone https://github.com/dayanez/pygwin.git
cd pygwin
pip install -e ".[full]"
pygwin
```

### Standalone executable

Every release publishes a compiled `pygwin.exe` for Windows under this repository's
[Releases](https://github.com/dayanez/pygwin/releases) page. Download it and run it — no Python
installation required.

## Contributing

pygwin is a personal project I am working on by myself. So, if something's broken or you want
to propose a change, open an issue or a pull request, or reach me at dommcpro@gmail.com.

## License

pygwin is licensed under the [GNU General Public License v3.0 or later](LICENSE). It must remain
open source. That is a license condition, not a preference.

pygwin is a fork of [xonsh](https://github.com/xonsh/xonsh), built by the xonsh developers and its
community. See [CREDITS.md](CREDITS.md) for full attribution.
