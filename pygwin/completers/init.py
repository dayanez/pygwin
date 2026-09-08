"""Constructor for pygwin completer objects."""

import collections

import pygwin.platform_info as xp
from pygwin.completers._aliases import complete_aliases
from pygwin.completers.base import complete_base
from pygwin.completers.bash import complete_from_bash
from pygwin.completers.commands import (
    complete_end_proc_keywords,
    complete_end_proc_tokens,
    complete_pgcompletions,
    complete_skipper,
)
from pygwin.completers.emoji import complete_emoji
from pygwin.completers.environment import complete_environment_vars
from pygwin.completers.imports import complete_import
from pygwin.completers.man import complete_from_man
from pygwin.completers.path import complete_path
from pygwin.completers.python import complete_pygwin_imp, complete_python


def default_completers(cmd_cache):
    """Creates a copy of the default completers."""
    defaults = [
        # non-exclusive completers:
        ("end_proc_tokens", complete_end_proc_tokens),
        ("end_proc_keywords", complete_end_proc_keywords),
        ("environment_vars", complete_environment_vars),
        # exclusive completers:
        ("base", complete_base),
        ("skip", complete_skipper),
        ("alias", complete_aliases),
        ("pgcompleter", complete_pgcompletions),
        ("import", complete_import),
    ]

    # On Windows, bash/man completers are skipped: the available bash
    # (WSL or Git Bash) operates in a different environment, and spawning
    # it corrupts the Windows console mode, breaking arrow keys in
    # prompt-toolkit.
    if not xp.ON_WINDOWS:
        for cmd, func in [
            ("bash", complete_from_bash),
            ("man", complete_from_man),
        ]:
            if cmd in cmd_cache:
                defaults.append((cmd, func))

    defaults.extend(
        [
            ("emoji", complete_emoji),
            ("pygwin_imp", complete_pygwin_imp),
            ("python", complete_python),
            ("path", complete_path),
        ]
    )
    return collections.OrderedDict(defaults)
