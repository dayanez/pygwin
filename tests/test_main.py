"""Tests the pygwin main function."""

import builtins
import gc
import json
import os
import os.path
import sys
import tempfile
import uuid
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryFile

import pytest

import pygwin.main
from pygwin.main import PygwinMode
from pygwin.platform_info import os_environ
from pygwin.pytest.tools import ON_WINDOWS, TEST_DIR, skip_if_on_windows


def Shell(*args, **kwargs):
    pass


@pytest.fixture
def shell(xession, monkeypatch):
    """Pygwin Shell Mock"""
    gc.collect()
    Shell.shell_type_aliases = {"rl": "readline"}
    monkeypatch.setattr(pygwin.main, "Shell", Shell)


@pytest.fixture(autouse=True)
def empty_pygwinrc(monkeypatch):
    # Don't use the local machine's pygwinrc
    empty_file_path = "NUL" if ON_WINDOWS else "/dev/null"
    monkeypatch.setitem(os.environ, "PYGWINRC", empty_file_path)


def test_premain_no_arg(shell, monkeypatch, xession):
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    pygwin.main.premain([])
    assert xession.env.get("PYGWIN_LOGIN")


def test_premain_interactive(shell, xession):
    pygwin.main.premain(["-i"])
    assert xession.env.get("PYGWIN_INTERACTIVE")


def test_premain_login_command(shell, xession):
    pygwin.main.premain(["-l", "-c", 'echo "hi"'])
    assert xession.env.get("PYGWIN_LOGIN")


def test_premain_login(shell, xession):
    pygwin.main.premain(["-l"])
    assert xession.env.get("PYGWIN_LOGIN")


def test_premain_D(shell, xession):
    # Set variables.
    pygwin.main.premain(["-DTEST1=1616", "-DTEST2=LOL"])
    assert xession.env.get("TEST1") == "1616"
    assert xession.env.get("TEST2") == "LOL"

    # Unknown variable.
    pygwin.main.premain(["-DORIGIN_VAR"])
    assert xession.env.get("ORIGIN_VAR") is None

    # Inherit variable.
    os.environ["ORIGIN_VAR"] = "origin_val"
    pygwin.main.premain(["--no-env", "-DORIGIN_VAR"])
    assert xession.env.get("ORIGIN_VAR") == "origin_val"


def test_premain_custom_rc(shell, tmpdir, monkeypatch, xession):
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setitem(os.environ, "PYGWIN_CACHE_SCRIPTS", "False")
    f = tmpdir.join("wakkawakka")
    f.write("print('hi')")
    args = pygwin.main.premain(["--rc", f.strpath])
    assert args.mode == PygwinMode.interactive
    assert f.strpath in xession.rc_files


@pytest.mark.skipif(
    ON_WINDOWS and sys.version_info[:3] == "3.8",
    reason="weird failure on py38+windows",
)
def test_rc_with_modules(shell, tmpdir, monkeypatch, capsys, xession):
    """Test that an RC file can load modules inside the same folder it is located in."""

    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setitem(os.environ, "PYGWIN_CACHE_SCRIPTS", "False")

    tmpdir.join("my_python_module.py").write("print('Hello,')")
    tmpdir.join("my_pygwin_module.xsh").write("print('World!')")
    rc = tmpdir.join("rc.xsh")
    rc.write("from my_python_module import *\nfrom my_pygwin_module import *")
    pygwin.main.premain(["--rc", rc.strpath])

    assert rc.strpath in xession.rc_files

    stdout, stderr = capsys.readouterr()
    assert "Hello,\nWorld!" in stdout
    assert len(stderr) == 0

    # Check that the temporary rc's folder is not left behind on the path
    assert tmpdir.strpath not in sys.path


def test_python_rc(shell, tmpdir, monkeypatch, capsys, xession, mocker):
    """Test that python based control files are executed using Python's parser"""

    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setitem(os.environ, "PYGWIN_CACHE_SCRIPTS", "False")

    # spy on pygwin's compile method
    spy = mocker.spy(xession.execer, "compile")

    rc = tmpdir.join("rc.py")
    rc.write("print('Hello World!')")
    pygwin.main.premain(["--rc", rc.strpath])

    assert rc.strpath in xession.rc_files

    stdout, stderr = capsys.readouterr()
    assert "Hello World!" in stdout
    assert len(stderr) == 0

    # Check that the temporary rc's folder is not left behind on the path
    assert tmpdir.strpath not in sys.path
    assert not spy.called


def test_rcdir(shell, tmpdir, monkeypatch, capsys):
    """
    Test that files are loaded from an rcdir, after a normal rc file,
    and in lexographic order.
    """

    rcdir = tmpdir.join("rc.d")
    rcdir.mkdir()
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setitem(os.environ, "PYGWINRC_DIR", str(rcdir))
    monkeypatch.setitem(os.environ, "PYGWINRC", str(tmpdir.join("rc.xsh")))
    monkeypatch.setitem(os.environ, "PYGWIN_CACHE_SCRIPTS", "False")

    rcdir.join("2.xsh").write("print('2.xsh')")
    rcdir.join("0.xsh").write("print('0.xsh')")
    rcdir.join("1.xsh").write("print('1.xsh')")
    tmpdir.join("rc.xsh").write("print('rc.xsh')")

    pygwin.main.premain([])
    stdout, stderr = capsys.readouterr()

    assert "rc.xsh\n0.xsh\n1.xsh\n2.xsh" in stdout
    assert len(stderr) == 0


def test_rcdir_cli(shell, tmpdir, xession, monkeypatch):
    """Test that --rc DIR works"""
    rcdir = tmpdir.join("rcdir")
    rcdir.mkdir()
    rc = rcdir.join("test.xsh")
    rc.write("print('test.xsh')")

    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    xargs = pygwin.main.premain(["--rc", rcdir.strpath])
    assert len(xargs.rc) == 1 and xargs.rc[0] == rcdir.strpath
    assert rc.strpath in xession.rc_files


def test_rcdir_empty(shell, tmpdir, monkeypatch, capsys):
    """Test that an empty PYGWINRC_DIR is not an error"""

    rcdir = tmpdir.join("rc.d")
    rcdir.mkdir()
    rc = tmpdir.join("rc.xsh")
    rc.write_binary(b"")
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setitem(os.environ, "PYGWINRC", str(rc))
    monkeypatch.setitem(os.environ, "PYGWINRC_DIR", str(rcdir))

    pygwin.main.premain([])
    stdout, stderr = capsys.readouterr()
    assert len(stderr) == 0


# the parameterisation is a list of pygwin args, followed by the list
# of RC files (see function body) expected to be loaded in order
# note that a tty is not faked, so this will default to non-interactive
# (skipped on windows because PYGWINRC="/path/to/f1.xsh:/path/to/f2.xsh"
# doesn't appear to work, while it does on other platforms)
@pytest.mark.skipif(ON_WINDOWS, reason="Issue with multi-file PYGWINRC")
@pytest.mark.parametrize(
    ["args", "expected"],
    [
        # non-interactive, nothing loading
        [[], []],
        # interactive, normal PYGWINRC and PYGWINRC_DIR
        [["-i"], ["F0", "F1", "D0", "D1"]],
        # --no-rc wins over -i
        [["--no-rc", "-i"], []],
        # --no-rc wins over -i --rc
        [["--no-rc", "-i", "--rc", "<R0>"], []],
        # --rc does nothing in non-interactive mode
        [["--rc", "<R0>"], []],
        # but is respected in interactive
        [["-i", "--rc", "<R0>"], ["R0"]],
        # multiple invocations of --rc only use the last
        [["-i", "--rc", "<R0>", "--rc", "<R1>"], ["R1"]],
        # but multiple RC files can be specified after --rc
        [["-i", "--rc", "<R0>", "<R1>"], ["R0", "R1"]],
        # including the same file twice
        [["-i", "--rc", "<R0>", "<R0>"], ["R0", "R0"]],
        # scripts are non-interactive
        [["<SC>"], ["SC"]],
        # but -i will load the normal environment with a script
        [["-i", "<SC>"], ["F0", "F1", "D0", "D1", "SC"]],
        # no-rc has no effect on a script
        [["--no-rc", "<SC>"], ["SC"]],
        # but does prevent RC loading in -i mode
        [["--no-rc", "-i", "<SC>"], ["SC"]],
        # --rc doesn't work here because a script is non-interactive
        [["--rc", "<R0>", "--", "<SC>"], ["SC"]],
        # unless forced with -i
        [["-i", "--rc", "<R0>", "--", "<SC>"], ["R0", "SC"]],
        # --no-rc also wins here
        [["-i", "--rc", "<R0>", "--no-rc", "--", "<SC>"], ["SC"]],
        # single commands are non-interactive
        [["-c", "pass"], []],
        # but load RCs with -i
        [["-i", "-c", "pass"], ["F0", "F1", "D0", "D1"]],
        # --rc ignores without -i
        [["--rc", "<R0>", "-c", "pass"], []],
        # but used with -i
        [["-i", "--rc", "<R0>", "-c", "pass"], ["R0"]],
    ],
    ids=lambda ae: " ".join(ae),
)
def test_script_startup(shell, tmpdir, monkeypatch, capsys, args, expected):
    """
    Test the correct scripts are loaded, in the correct order, for
    different combinations of CLI arguments. See
    https://github.com/xonsh/xonsh/issues/4096

    This sets up a standard set of RC files which will be loaded,
    and tests whether they print their payloads at all, or in the right
    order, depending on the CLI arguments chosen.
    """
    rcdir = tmpdir.join("rc.d")
    rcdir.mkdir()
    # PYGWINRC_DIR files, in order
    rcdir.join("d0.xsh").write("print('D0')")
    rcdir.join("d1.xsh").write("print('D1')")
    # PYGWINRC files, in order
    f0 = tmpdir.join("f0.xsh")
    f0.write("print('F0')")
    f1 = tmpdir.join("f1.xsh")
    f1.write("print('F1')")
    # RC files which can be explicitly loaded with --rc
    r0 = tmpdir.join("r0.xsh")
    r0.write("print('R0')")
    r1 = tmpdir.join("r1.xsh")
    r1.write("print('R1')")
    # a (non-RC) script which can be loaded
    sc = tmpdir.join("sc.xsh")
    sc.write("print('SC')")

    monkeypatch.setitem(os.environ, "PYGWINRC", f"{f0}:{f1}")
    monkeypatch.setitem(os.environ, "PYGWINRC_DIR", str(rcdir))

    # replace <RC> with the path to rc.xsh and <SC> with sc.xsh
    args = [
        a.replace("<R0>", str(r0)).replace("<R1>", str(r1)).replace("<SC>", str(sc))
        for a in args
    ]

    # since we only test pygwin.premain here, a script file (SC)
    # won't actually get run here, so won't appear in the stdout,
    # so don't check for it (but check for a .file in the parsed args)
    check_for_script = "SC" in expected
    expected = [e for e in expected if e != "SC"]

    xargs = pygwin.main.premain(args)
    stdout, stderr = capsys.readouterr()
    assert "\n".join(expected) in stdout
    if check_for_script:
        assert xargs.file is not None


def test_rcdir_ignored_with_rc(shell, tmpdir, monkeypatch, capsys, xession):
    """Test that --rc suppresses loading PYGWINRC_DIRs"""

    rcdir = tmpdir.join("rc.d")
    rcdir.mkdir()
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setitem(os.environ, "PYGWINRC_DIR", str(rcdir))
    rcdir.join("rcd.xsh").write("print('RCDIR')")
    tmpdir.join("rc.xsh").write("print('RCFILE')")

    pygwin.main.premain(["--rc", str(tmpdir.join("rc.xsh"))])
    stdout, stderr = capsys.readouterr()
    assert "RCDIR" not in stdout
    assert "RCFILE" in stdout
    assert str(rcdir.join("rcd.xsh")) not in xession.rc_files


@pytest.mark.skipif(ON_WINDOWS, reason="See https://github.com/xonsh/xonsh/issues/3936")
def test_rc_with_modified_path(shell, tmpdir, monkeypatch, capsys, xession):
    """Test that an RC file can edit the sys.path variable without losing those values."""

    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setitem(os.environ, "PYGWIN_CACHE_SCRIPTS", "False")

    rc = tmpdir.join("rc.xsh")
    rc.write(f"import sys\nsys.path.append('{tmpdir.strpath}')\nprint('Hello, World!')")
    pygwin.main.premain(["--rc", rc.strpath])

    assert rc.strpath in xession.rc_files

    stdout, stderr = capsys.readouterr()
    assert "Hello, World!" in stdout
    assert len(stderr) == 0

    # Check that the path that was explicitly added is not accidentally deleted
    assert tmpdir.strpath in sys.path


def test_rc_with_failing_module(shell, tmpdir, monkeypatch, capsys, xession):
    """Test that an RC file which imports a module that throws an exception ."""

    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setitem(os.environ, "PYGWIN_CACHE_SCRIPTS", "False")

    tmpdir.join("my_failing_module.py").write("raise RuntimeError('Unexpected error')")
    rc = tmpdir.join("rc.xsh")
    rc.write("from my_failing_module import *")
    pygwin.main.premain(["--rc", rc.strpath])

    assert rc.strpath not in xession.rc_files

    stdout, stderr = capsys.readouterr()
    assert len(stdout) == 0
    assert "Unexpected error" in stderr

    # Check that the temporary rc's folder is not left behind on the path
    assert tmpdir.strpath not in sys.path


def test_no_rc_with_script(shell, tmpdir):
    args = pygwin.main.premain(["tests/sample.xsh"])
    assert not (args.mode == PygwinMode.interactive)


def test_force_interactive_rc_with_script(shell, tmpdir, xession):
    pygwin.main.premain(["-i", "tests/sample.xsh"])
    assert xession.env.get("PYGWIN_INTERACTIVE")


def test_force_interactive_custom_rc_with_script(shell, tmpdir, monkeypatch, xession):
    """Calling a custom RC file on a script-call with the interactive flag
    should run interactively
    """
    monkeypatch.setitem(os.environ, "PYGWIN_CACHE_SCRIPTS", "False")
    f = tmpdir.join("wakkawakka")
    f.write("print('hi')")
    args = pygwin.main.premain(
        ["-i", "--rc", f.strpath, str(Path(__file__).parent / "sample.xsh")]
    )
    assert args.mode == PygwinMode.interactive
    assert f.strpath in xession.rc_files


def test_force_interactive_custom_rc_with_script_and_no_rc(
    shell, tmpdir, monkeypatch, xession
):
    monkeypatch.setitem(os.environ, "PYGWIN_CACHE_SCRIPTS", "False")
    f = tmpdir.join("wakkawakka")
    f.write("print('hi')")
    args = pygwin.main.premain(
        ["-i", "--no-rc", "--rc", f.strpath, str(Path(__file__).parent / "sample.xsh")]
    )
    assert args.mode == PygwinMode.interactive
    assert len(xession.rc_files) == 0


def test_custom_rc_with_script(shell, tmpdir, xession):
    """Calling a custom RC file on a script-call without the interactive flag
    should not run interactively
    """
    f = tmpdir.join("wakkawakka")
    f.write("print('hi')")
    args = pygwin.main.premain(
        ["--rc", f.strpath, str(Path(__file__).parent / "sample.xsh")]
    )
    assert not (args.mode == PygwinMode.interactive)
    assert f.strpath in xession.rc_files


def test_custom_rc_with_script_and_no_rc(shell, tmpdir, xession):
    """Calling a custom RC file on a script-call without the interactive flag and no-rc
    should not run interactively and should not have any rc_files
    """
    f = tmpdir.join("wakkawakka")
    f.write("print('hi')")
    args = pygwin.main.premain(
        ["--no-rc", "--rc", f.strpath, str(Path(__file__).parent / "sample.xsh")]
    )
    assert not (args.mode == PygwinMode.interactive)
    assert len(xession.rc_files) == 0


def test_premain_no_rc(shell, tmpdir, xession):
    pygwin.main.premain(["--no-rc"])
    assert len(xession.rc_files) == 0


def test_premain_no_rc_interactive(shell, tmpdir, xession):
    pygwin.main.premain(["--no-rc", "-i"])
    assert len(xession.rc_files) == 0


@pytest.mark.parametrize(
    "arg", ["", "-i", "-vERSION", "-hAALP", "TTTT", "-TT", "--TTT"]
)
def test_premain_with_file_argument(arg, shell, xession):
    pygwin.main.premain(["tests/sample.xsh", arg])
    assert not (xession.env.get("PYGWIN_INTERACTIVE"))


def test_premain_interactive__with_file_argument(shell, xession):
    pygwin.main.premain(["-i", "tests/sample.xsh"])
    assert xession.env.get("PYGWIN_INTERACTIVE")


@pytest.mark.parametrize("case", ["----", "--hep", "-TT", "--TTTT"])
def test_premain_invalid_arguments(shell, case, capsys):
    with pytest.raises(SystemExit):
        pygwin.main.premain([case])
    assert "unrecognized argument" in capsys.readouterr()[1]


def test_premain_timings_arg(shell):
    pygwin.main.premain(["--timings"])


@skip_if_on_windows
@pytest.mark.parametrize(
    ("env_shell", "rc_shells", "exp_shell"),
    [
        ("", [], ""),
        ("/argle/bash", [], "/argle/bash"),
        ("/bin/pygwin", [], ""),
        (
            "/argle/bash",
            ["/argle/pygwin", "/argle/dash", "/argle/sh", "/argle/bargle"],
            "/argle/bash",
        ),
        (
            "",
            ["/argle/pygwin", "/argle/dash", "/argle/sh", "/argle/bargle"],
            "/argle/dash",
        ),
        ("", ["/argle/pygwin", "/argle/screen", "/argle/sh"], "/argle/sh"),
        ("", ["/argle/pygwin", "/argle/screen"], ""),
    ],
)
@skip_if_on_windows
def test_pygwin_failback(
    env_shell,
    rc_shells,
    exp_shell,
    shell,
    xession,
    monkeypatch,
    monkeypatch_stderr,
):
    failback_checker = []

    def mocked_main(*args):
        raise Exception("A fake failure")

    monkeypatch.setattr(pygwin.main, "main_pygwin", mocked_main)

    def mocked_execlp(f, *args):
        failback_checker.append(f)
        failback_checker.append(args[0])

    monkeypatch.setattr(os, "execlp", mocked_execlp)
    monkeypatch.setattr(os.path, "exists", lambda x: True)
    monkeypatch.setattr(
        sys, "argv", ["/bin/pygwin", "-i"]
    )  # has to look like real path

    @contextmanager
    def mocked_open(*args):
        yield rc_shells

    monkeypatch.setattr(builtins, "open", mocked_open)

    monkeypatch.setenv("SHELL", env_shell)

    try:
        pygwin.main.main()  # if main doesn't raise, it did try to invoke a shell
        assert failback_checker[0] == exp_shell
        assert failback_checker[1] == failback_checker[0]
    except Exception as e:
        if len(e.args) and "A fake failure" in str(
            e.args[0]
        ):  # if it did raise expected exception
            assert len(failback_checker) == 0  # then it didn't invoke a shell
        else:
            raise e  # it raised something other than the test exception,


def test_pygwin_failback_single(shell, monkeypatch, monkeypatch_stderr):
    class FakeFailureError(Exception):
        pass

    def mocked_main(*args):
        raise FakeFailureError()

    monkeypatch.setattr(pygwin.main, "main_pygwin", mocked_main)
    monkeypatch.setattr(sys, "argv", ["pygwin", "-c", "echo", "foo"])

    with pytest.raises(FakeFailureError):
        pygwin.main.main()


def test_pygwin_failback_script_from_file(shell, monkeypatch, monkeypatch_stderr):
    checker = []

    def mocked_execlp(f, *args):
        checker.append(f)

    monkeypatch.setattr(os, "execlp", mocked_execlp)

    script = os.path.join(TEST_DIR, "scripts", "raise.xsh")
    monkeypatch.setattr(sys, "argv", ["pygwin", script])

    # changed in #4662: User-Code exceptions are now caught in main and handled there
    # => we expect that no exception is thrown

    assert len(checker) == 0


def test_pygwin_no_file_returncode(shell, monkeypatch, monkeypatch_stderr):
    monkeypatch.setattr(sys, "argv", ["pygwin", "foobazbarzzznotafileatall.xsh"])
    with pytest.raises(SystemExit):
        pygwin.main.main()


def test_auto_loading_pgtribs(xession, shell, mocker):
    # GIVEN a pgtrib is installed
    from importlib.metadata import EntryPoint

    group = "pygwin.pgtribs"

    mocker.patch(
        "importlib.metadata.entry_points",
        autospec=True,
        return_value={
            group: [EntryPoint(name="test", group=group, value="test.module")]
        },
    )
    pgtribs_load = mocker.patch("pygwin.pgtribs.pgtribs_load")

    # AND auto-loading pgtribs is enabled by default
    assert xession.env["PGTRIBS_AUTOLOAD_DISABLED"] is False

    # WHEN pygwin is initialized
    pygwin.main.premain([])

    # THEN auto-loading pgtribs is still enabled
    assert xession.env["PGTRIBS_AUTOLOAD_DISABLED"] is False

    # AND installed pgtrib should be auto-loaded
    assert xession.builtins.autoloaded_pgtribs == {"test": "test.module"}
    pgtribs_load.assert_called()


def test_pgtribs_autoload_disabled_in_custom_rc(xession, shell, mocker, tmpdir):
    """As a Pygwin user, if I set `$PGTRIBS_AUTOLOAD_DISABLED = True`
    in my RC file, then Pgtribs should not be auto-loaded.

    https://github.com/xonsh/xonsh/issues/5872
    """
    # GIVEN a pgtrib is installed
    from importlib.metadata import EntryPoint

    group = "pygwin.pgtribs"
    mocker.patch(
        "importlib.metadata.entry_points",
        autospec=True,
        return_value={
            group: [EntryPoint(name="test", group=group, value="test.module")]
        },
    )
    pgtribs_load = mocker.patch("pygwin.pgtribs.pgtribs_load")

    # AND auto-loading pgtribs is disabled in a custom RC file
    f = tmpdir.join("wakkawakka")
    f.write("$PGTRIBS_AUTOLOAD_DISABLED = True\n")

    # AND auto-loading pgtribs is not explicitly disabled
    assert xession.env["PGTRIBS_AUTOLOAD_DISABLED"] is False

    # WHEN pygwin is initialized
    pygwin.main.premain(["--rc", f.strpath])

    # THEN custom RC file should have been processed
    assert f.strpath in xession.rc_files
    assert xession.env["PGTRIBS_AUTOLOAD_DISABLED"] is True

    # AND installed pgtrib should not be auto-loaded
    assert not hasattr(xession.builtins, "autoloaded_pgtribs")
    pgtribs_load.assert_not_called()


def test_script_normal_file(xession, monkeypatch, capsys, tmpdir):
    script_path = tmpdir / "script.xsh"
    with open(script_path, "w") as script:
        script.write("print('Hello, World!')")
    monkeypatch.setattr(sys, "argv", ["pygwin", str(script_path)])

    with pytest.raises(SystemExit, match="0"):
        pygwin.main.main()

    stdout, stderr = capsys.readouterr()
    assert "Hello, World!" in stdout


def _has_dev_fd_n():
    """True iff ``/dev/fd/<N>`` resolves for an arbitrary open fd (N > 2).

    Linux always exposes this via procfs; macOS exposes it via devfs;
    FreeBSD only does so when ``fdescfs`` is explicitly mounted at
    ``/dev/fd`` (the default install only populates 0/1/2). Windows
    has no equivalent at all.
    """
    if ON_WINDOWS:
        return False
    try:
        with TemporaryFile() as probe:
            return os.path.exists(f"/dev/fd/{probe.fileno()}")
    except OSError:
        return False


@pytest.mark.skipif(
    not _has_dev_fd_n(),
    reason="Platform does not expose /dev/fd/<N> for arbitrary fds "
    "(Windows, or FreeBSD without fdescfs mounted).",
)
def test_script_file_descriptor(xession, monkeypatch, capsys):
    with TemporaryFile("w+t") as script:
        script.write("print('Hello, World!')")
        script.seek(0)
        monkeypatch.setattr(sys, "argv", ["pygwin", f"/dev/fd/{script.fileno()}"])

        with pytest.raises(SystemExit, match="0"):
            pygwin.main.main()

        stdout, stderr = capsys.readouterr()
        assert "Hello, World!" in stdout


def test_script_directory(xession, monkeypatch, capsys, tmpdir):
    monkeypatch.setattr(sys, "argv", ["pygwin", str(tmpdir)])

    with pytest.raises(SystemExit, match="1"):
        pygwin.main.main()

    stdout, stderr = capsys.readouterr()
    assert "Is a directory." in stdout


def test_script_missing_file(xession, monkeypatch, capsys, tmpdir):
    monkeypatch.setattr(sys, "argv", ["pygwin", str(tmpdir / "invalid.xsh")])

    with pytest.raises(SystemExit, match="1"):
        pygwin.main.main()

    stdout, stderr = capsys.readouterr()
    assert "No such file." in stdout


def test_premain_save_origin_env(shell, xession):
    origin_env = os_environ

    with tempfile.TemporaryDirectory() as tmp:
        xession.env["PYGWIN_DATA_DIR"] = tmp

        pygwin.main.premain(["--save-origin-env"])
    assert "PYGWIN_ORIGIN_ENV_FILE" in xession.env

    data_dir = xession.env.get("PYGWIN_DATA_DIR", None)
    env_file_name = Path(data_dir) / f"origin-env-{xession.sessionid}.json"

    assert xession.env["PYGWIN_ORIGIN_ENV_FILE"] == str(env_file_name)
    assert origin_env == json.loads(env_file_name.read_text())


def test_premain_load_origin_error(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["pygwin", "--load-origin-env"])
    with pytest.raises(SystemExit, match="1"):
        pygwin.main.main()

    _, stderr = capsys.readouterr()
    assert "pygwin: No env file to restore" in stderr


def test_premain_load_origin_env(shell, xession, capsys):
    with tempfile.TemporaryDirectory() as tmp:
        env_file_name = Path(tmp) / f"origin-env-{uuid.uuid4()}.json"
        os.environ["ABCD"] = "DEF"
        env_file_name.write_text(json.dumps(dict(os_environ)))
        os.environ["PYGWIN_ORIGIN_ENV_FILE"] = str(env_file_name)
        os.environ["ABCD"] = "000"
        pygwin.main.premain(["--load-origin-env"])
        assert xession.env["ABCD"] == "DEF"
