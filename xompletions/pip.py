"""Completers for pip."""

from pygwin.completers.tools import comp_based_completer
from pygwin.parsers.completion_context import CommandContext


def pygwin_complete(ctx: CommandContext):
    """Completes python's package manager pip."""

    return comp_based_completer(ctx, PIP_AUTO_COMPLETE="1")
