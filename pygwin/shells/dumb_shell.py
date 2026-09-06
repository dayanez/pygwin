"""A dumb shell for when $TERM == 'dumb', which usually happens in emacs."""

from pygwin.built_ins import XSH
from pygwin.shells.readline_shell import ReadlineShell


class DumbShell(ReadlineShell):
    """A dumb shell for when $TERM == 'dumb', which usually happens in emacs."""

    def __init__(self, *args, **kwargs):
        XSH.env["PYGWIN_COLOR_STYLE"] = "emacs"
        super().__init__(*args, **kwargs)
