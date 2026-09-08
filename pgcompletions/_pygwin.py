"""Completer for ``pygwin`` command using its ``argparser``"""

from pygwin.cli_utils import ArgparseCompleter
from pygwin.parsers.completion_context import CommandContext


def pygwin_complete(command: CommandContext):
    """Completer for ``pygwin`` command using its ``argparser``"""

    from pygwin.main import parser

    completer = ArgparseCompleter(parser, command=command)
    return completer.complete(), False
