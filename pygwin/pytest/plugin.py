"""Pytest plugin for testing Pygwin.

These fixture names are Public API and need to be handled carefully as there are Xontribs dependent on them for testing
"""

import builtins
import importlib
import os
import sys
import types
from pathlib import Path
from traceback import extract_tb, format_list
from unittest.mock import MagicMock

import pytest

from pygwin import commands_cache
from pygwin.aliases import Aliases
from pygwin.built_ins import XSH, PygwinSession
from pygwin.completer import Completer
from pygwin.events import events
from pygwin.execer import Execer
from pygwin.main import setup
from pygwin.parsers.completion_context import CompletionContextParser
from pygwin.procs.jobs import get_tasks

from .tools import DummyHistory, DummyShell, copy_env, sp


def pytest_configure(config):
    setup(history_backend="dummy")


def pytest_collection_modifyitems(items):
    """Move xsh test first to work around a bug in normal
    pytest cleanup. The order of tests are otherwise preserved.
    """
    items.sort(key=lambda item: -isinstance(item, XshFunction))


def _limited_traceback(excinfo):
    """Return a formatted traceback with all the stack
    from this frame (i.e __file__) up removed
    """
    tb = extract_tb(excinfo.tb)
    try:
        idx = [__file__ in e for e in tb].index(True)
        return format_list(tb[idx + 1 :])
    except ValueError:
        return format_list(tb)


def pytest_collect_file(file_path: Path, parent):
    if file_path.suffix.lower() == ".xsh" and file_path.name.startswith("test_"):
        return XshFile.from_parent(parent, path=file_path)


class XshFile(pytest.File):
    def collect(self):
        sys.path.append(str(self.path.parent))
        mod = importlib.import_module(self.path.stem)
        sys.path.pop(0)
        tests = [t for t in dir(mod) if t.startswith("test_")]
        for test_name in tests:
            obj = getattr(mod, test_name)
            if hasattr(obj, "__call__"):  # noqa
                yield XshFunction.from_parent(
                    self, name=test_name, test_func=obj, test_module=mod
                )


class XshFunction(pytest.Item):
    def __init__(self, name, parent, test_func, test_module):
        super().__init__(name, parent)
        self._test_func = test_func
        self._test_module = test_module

    def runtest(self, *args, **kwargs):
        # `xession`/`pygwin_session` fixtures call `XSH.unload()` on teardown,
        # which removes `builtins.__pygwin__`. Under pytest-xdist a worker
        # can be assigned a session-using test before an .xsh test, so the
        # initial `pytest_configure` setup is no longer in effect by the
        # time we run. `setup()` is idempotent — it no-ops when __pygwin__
        # is already present.
        if not hasattr(builtins, "__pygwin__"):
            setup(history_backend="dummy")
        self._test_func(*args, **kwargs)

    def repr_failure(self, excinfo, **_):
        """called when self.runtest() raises an exception."""
        formatted_tb = _limited_traceback(excinfo)
        formatted_tb.insert(0, "pygwin execution failed\n")
        formatted_tb.append(f"{excinfo.type.__name__}: {excinfo.value}")
        return "".join(formatted_tb)

    def reportinfo(self):
        return self.path, 0, f"pygwin test: {self.name}"


@pytest.fixture
def source_path():
    """Get the pygwin source path."""
    pwd = os.path.dirname(__file__)
    return os.path.dirname(pwd)


@pytest.fixture
def pygwin_execer(monkeypatch, pygwin_session):
    """Initiate the Execer with a mocked nop `load_builtins`"""
    yield pygwin_session.execer


@pytest.fixture
def pygwin_execer_exec(pygwin_execer):
    def factory(input, **kwargs):
        pygwin_execer.exec(input, **kwargs)
        return True

    return factory


@pytest.fixture
def pygwin_execer_parse(pygwin_execer):
    def factory(input):
        tree = XSH.execer.parse(input, ctx=None)
        return tree

    return factory


@pytest.fixture
def mock_executables_in(xession, tmp_path, monkeypatch):
    def _factory(binaries: list[str]):
        xession.env["PATH"] = [tmp_path]
        exec_mock = MagicMock(return_value=binaries)
        monkeypatch.setattr(commands_cache, "executables_in", exec_mock)
        return exec_mock

    return _factory


@pytest.fixture
def patch_locate_binary(monkeypatch):
    def locate_binary(self, name, *args):
        return str(Path(__file__).parent.parent.parent / "tests" / "bin" / name)

    def factory(cc: commands_cache.CommandsCache):
        monkeypatch.setattr(cc, "locate_binary", types.MethodType(locate_binary, cc))
        return cc

    return factory


@pytest.fixture
def monkeypatch_stderr(monkeypatch):
    """Monkeypath sys.stderr with no ResourceWarning."""
    with open(os.devnull, "w") as fd:
        monkeypatch.setattr(sys, "stderr", fd)
        yield


@pytest.fixture
def pygwin_events():
    yield events
    for name, oldevent in vars(events).items():
        # Heavily based on transmogrification
        species = oldevent.species
        newevent = events._mkevent(species, species.__doc__)
        setattr(events, name, newevent)


@pytest.fixture(scope="session")
def session_os_env():
    """Env with values from os.environ like real session"""
    from pygwin.environ import Env, default_env

    return Env(default_env())


@pytest.fixture(scope="session")
def session_env():
    """Env with some initial values that doesn't load from os.environ"""
    from pygwin.environ import Env

    initial_vars = {
        "UPDATE_OS_ENVIRON": False,
        "PYGWIN_DEBUG": 1,
        "PYGWIN_COLOR_STYLE": "default",
        "VC_BRANCH_TIMEOUT": 1,
        "PYGWIN_ENCODING": "utf-8",
        "PYGWIN_ENCODING_ERRORS": "strict",
        "COMMANDS_CACHE_SAVE_INTERMEDIATE": False,
    }
    env = Env(initial_vars)
    return env


@pytest.fixture(scope="session")
def session_execer():
    return Execer()


@pytest.fixture
def os_env(session_os_env):
    """A mutable copy of Original session_os_env"""

    return copy_env(session_os_env)


@pytest.fixture
def env(tmp_path, session_env):
    """a mutable copy of session_env"""
    env_copy = copy_env(session_env)
    initial_vars = {"PYGWIN_DATA_DIR": str(tmp_path), "PYGWIN_CACHE_DIR": str(tmp_path)}

    env_copy.update(initial_vars)
    return env_copy


@pytest.fixture
def pygwin_session(pygwin_events, session_execer, os_env, monkeypatch):
    """a fixture to use where PygwinSession is fully loaded without any mocks"""

    XSH.load(
        ctx={},
        execer=session_execer,
        env=os_env,
    )
    yield XSH
    XSH.unload()
    get_tasks().clear()  # must do this to enable resetting all_jobs


@pytest.fixture
def mock_pygwin_session(monkeypatch, pygwin_events, pygwin_session, env):
    """Mock out most of the builtins pygwin attributes."""

    # make sure that all other fixtures call this mock only one time
    session = []

    def factory(*attrs_to_skip: str):
        """

        Parameters
        ----------
        attrs_to_skip
            do not mock the given attributes

        Returns
        -------
        PygwinSession
            with most of the attributes mocked out
        """
        if session:
            raise RuntimeError("The factory should be called only once per test")

        aliases = None if "aliases" in attrs_to_skip else Aliases()
        for attr, val in [
            ("env", env),
            ("shell", DummyShell()),
            ("help", lambda x: x),
            ("exit", None),
            ("history", DummyHistory()),
            (
                "commands_cache",
                commands_cache.CommandsCache(env, aliases),
            ),  # since env,aliases change , patch cmds-cache
            # ("subproc_captured", sp),
            ("subproc_uncaptured", sp),
            ("subproc_captured_stdout", sp),
            ("subproc_captured_inject", sp),
            ("subproc_captured_object", sp),
            ("subproc_captured_hiddenobject", sp),
        ]:
            if attr in attrs_to_skip:
                continue
            monkeypatch.setattr(pygwin_session, attr, val)

        for attr, val in [
            ("evalx", eval),
            ("execx", None),
            ("compilex", None),
            # Unlike all the other stuff, this has to refer to the "real" one because all modules that would
            # be firing events on the global instance.
            ("events", pygwin_events),
        ]:
            # attributes to builtins are dynamicProxy and should pickup the following
            monkeypatch.setattr(pygwin_session.builtins, attr, val)

        session.append(pygwin_session)
        return pygwin_session

    yield factory
    session.clear()


@pytest.fixture
def xession(mock_pygwin_session) -> PygwinSession:
    """Mock out most of the builtins pygwin attributes."""
    return mock_pygwin_session()


@pytest.fixture
def xsh_with_aliases(mock_pygwin_session) -> PygwinSession:
    """Pygwin mock-session with default set of aliases"""
    return mock_pygwin_session("aliases")


@pytest.fixture
def xsh_with_env(mock_pygwin_session) -> PygwinSession:
    """Pygwin mock-session with os.environ"""
    return mock_pygwin_session("env")


@pytest.fixture(scope="session")
def completion_context_parse():
    return CompletionContextParser().parse


@pytest.fixture(scope="session")
def completer_obj():
    return Completer()


@pytest.fixture
def check_completer(completer_obj):
    """Helper function to run completer and parse the results as set of strings"""
    completer = completer_obj

    def _factory(
        line: str, prefix: "None|str" = "", send_original=False, complete_fn=None
    ):
        """

        Parameters
        ----------
        line
        prefix
        send_original
            if True, return the original result from the completer (e.g. RichCompletion instances ...)
        complete_fn
            if given, use that to get the completions

        Returns
        -------
            completions as set of string if not send
        """
        if prefix is not None:
            line += " " + prefix
        if complete_fn is None:
            completions, _ = completer.complete_line(line)
        else:
            ctx = completer_obj.parse(line)
            out = complete_fn(ctx)
            if isinstance(out, tuple):
                completions = out[0]
            else:
                completions = out
        values = {getattr(i, "value", i).strip() for i in completions}

        if send_original:
            # just return the bare completions without appended-space for easier assertions
            return values, completions

        return values

    return _factory


@pytest.fixture
def ptk_shell(pygwin_execer):
    from prompt_toolkit.input import create_pipe_input
    from prompt_toolkit.output import DummyOutput

    from pygwin.shells.ptk_shell import PromptToolkitShell

    out = DummyOutput()
    with create_pipe_input() as inp:
        shell = PromptToolkitShell(
            execer=pygwin_execer, ctx={}, ptk_args={"input": inp, "output": out}
        )
        yield inp, out, shell


@pytest.fixture
def readline_shell(pygwin_execer, tmpdir, mocker):
    from pygwin.shells.readline_shell import ReadlineShell

    inp_path = tmpdir / "in"
    inp = inp_path.open("w+")
    out_path = tmpdir / "out"
    out = out_path.open("w+")

    shell = ReadlineShell(execer=pygwin_execer, ctx={}, stdin=inp, stdout=out)
    mocker.patch.object(shell, "_load_remaining_input_into_queue")
    yield shell
    inp.close()
    out.close()


@pytest.fixture
def load_xontrib():
    to_unload = []

    def wrapper(*names: str):
        from pygwin.xontribs import xontrib_data, xontribs_load

        xo_data = xontrib_data()

        for name in names:
            module = xo_data[name]["module"]
            if module not in sys.modules:
                to_unload.append(module)

            _, stderr, res = xontribs_load([module], full_module=True)
            if stderr:
                raise Exception(f"Failed to load xontrib: {stderr}")
        return

    yield wrapper

    for mod in to_unload:
        del sys.modules[mod]
