"""Prints the pygwin interactive welcome banner.

This is the one place pygwin's own branding shows up at runtime. Everything
else in an interactive session is unmodified xonsh, loaded through the
standard xontrib entry point mechanism so this file never has to touch
xonsh's own source.
"""

from xonsh.built_ins import XonshSession

BANNER = """pygwin {version}  (xonsh core)
A Windows-first, Python-powered shell. Type `pygwin --help` or `? topic` for help.
"""


def _load_xontrib_(xsh: XonshSession, **_):
    import sys

    if not xsh.env.get("XONSH_INTERACTIVE", False):
        return
    if not sys.stdout.isatty():
        # Autoload can fire during non-interactive premain() calls (tests,
        # embedding, `--rc` loading) whenever $XONSH_INTERACTIVE happens to
        # be set. Only greet a real terminal.
        return

    from xonsh import __version__

    print(BANNER.format(version=__version__))
