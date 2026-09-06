"""Testing for ``pygwin.shells.Shell``"""

import os

from pygwin.history.dummy import DummyHistory
from pygwin.history.json import JsonHistory
from pygwin.history.sqlite import SqliteHistory
from pygwin.shell import Shell


def test_shell_with_json_history(xession, pygwin_execer, tmpdir_factory):
    """
    Check that shell successfully load JSON history from file.
    """
    tempdir = str(tmpdir_factory.mktemp("history"))

    history_file = os.path.join(tempdir, "history.json")
    h = JsonHistory(filename=history_file)
    h.append(
        {
            "inp": "echo Hello world 1\n",
            "rtn": 0,
            "ts": [1615887820.7329783, 1615887820.7513437],
        }
    )
    h.append(
        {
            "inp": "echo Hello world 2\n",
            "rtn": 0,
            "ts": [1615887820.7329783, 1615887820.7513437],
        }
    )
    h.flush()

    xession.env.update(
        dict(
            PYGWIN_DATA_DIR=tempdir,
            PYGWIN_INTERACTIVE=True,
            PYGWIN_HISTORY_BACKEND="json",
            PYGWIN_HISTORY_FILE=history_file,
            # PYGWIN_DEBUG=1  # to show errors
        )
    )

    Shell(pygwin_execer, shell_type="none")

    assert len([i for i in xession.history.all_items()]) == 2


def test_shell_with_sqlite_history(xession, pygwin_execer, tmpdir_factory):
    """
    Check that shell successfully load SQLite history from file.
    """
    tempdir = str(tmpdir_factory.mktemp("history"))

    history_file = os.path.join(tempdir, "history.sqlite")
    h = SqliteHistory(filename=history_file)
    h.append(
        {
            "inp": "echo Hello world 1\n",
            "rtn": 0,
            "ts": [1615887820.7329783, 1615887820.7513437],
        }
    )
    h.append(
        {
            "inp": "echo Hello world 2\n",
            "rtn": 0,
            "ts": [1615887820.7329783, 1615887820.7513437],
        }
    )
    h.flush()

    xession.env.update(
        dict(
            PYGWIN_DATA_DIR=tempdir,
            PYGWIN_INTERACTIVE=True,
            PYGWIN_HISTORY_BACKEND="sqlite",
            PYGWIN_HISTORY_FILE=history_file,
            # PYGWIN_DEBUG=1  # to show errors
        )
    )

    Shell(pygwin_execer, shell_type="none")

    assert len([i for i in xession.history.all_items()]) == 2


def test_shell_with_dummy_history_in_not_interactive(xession, pygwin_execer):
    """
    Check that shell use Dummy history in not interactive mode.
    """
    xession.env["PYGWIN_INTERACTIVE"] = False
    xession.history = None
    Shell(pygwin_execer, shell_type="none")
    assert isinstance(xession.history, DummyHistory)
