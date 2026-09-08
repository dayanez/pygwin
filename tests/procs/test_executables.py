import os

from pygwin.environ import Env
from pygwin.platform_info import ON_WINDOWS
from pygwin.procs import executables as executables_mod
from pygwin.procs.executables import (
    _cached_dir_contains,
    _stable_dir_cache,
    get_paths,
    get_possible_names,
    locate_executable,
    locate_file,
    locate_relative_path,
)
from pygwin.tools import chdir


def test_get_possible_names():
    env = Env(PATHEXT=[".EXE", ".COM"])
    result = get_possible_names("file", env)
    assert result[0] == "file"
    assert "file.exe" in result
    assert "file.com" in result
    result_upper = get_possible_names("FILE", env)
    assert result_upper[0] == "FILE"
    assert "FILE.EXE" in result_upper
    assert "FILE.COM" in result_upper


def test_get_paths(tmpdir):
    bindir1 = str(tmpdir.mkdir("bindir1"))
    bindir2 = str(tmpdir.mkdir("bindir2"))
    env = Env(PATH=[bindir1, bindir2, bindir1, "nodir"])
    assert get_paths(env) == (bindir2, bindir1)


def test_cached_clear_paths_reuses_result_until_path_changes(tmpdir, monkeypatch):
    """clear_paths() does real realpath()/isdir() filesystem work; it should
    only be re-run when the raw $PATH value actually changes, not on every
    single call with the same $PATH."""
    bindir1 = str(tmpdir.mkdir("bindir1"))
    bindir2 = str(tmpdir.mkdir("bindir2"))
    env = Env(PATH=[bindir1, bindir2])

    calls = []
    real_clear_paths = executables_mod.clear_paths

    def counting_clear_paths(paths):
        calls.append(tuple(paths))
        return real_clear_paths(paths)

    monkeypatch.setattr(executables_mod, "clear_paths", counting_clear_paths)
    executables_mod._clear_paths_cache_key = None

    first = get_paths(env)
    second = get_paths(env)
    assert first == second == (bindir2, bindir1)
    assert len(calls) == 1, "unchanged $PATH must not be re-scanned"

    # Changing $PATH must be picked up immediately, without any manual
    # cache-clearing.
    bindir3 = str(tmpdir.mkdir("bindir3"))
    env.update({"PATH": [bindir1, bindir3]})
    third = get_paths(env)
    assert third == (bindir3, bindir1)
    assert len(calls) == 2, "a changed $PATH must trigger a re-scan"


def test_cached_clear_paths_respects_enable_commands_cache(tmpdir, monkeypatch):
    """Setting $ENABLE_COMMANDS_CACHE = False must disable this cache too,
    matching its documented "disables the caching mechanism" behavior."""
    bindir = str(tmpdir.mkdir("bindir"))
    env = Env(PATH=[bindir], ENABLE_COMMANDS_CACHE=False)

    calls = []
    real_clear_paths = executables_mod.clear_paths
    monkeypatch.setattr(
        executables_mod,
        "clear_paths",
        lambda paths: calls.append(1) or real_clear_paths(paths),
    )
    executables_mod._clear_paths_cache_key = None

    get_paths(env)
    get_paths(env)
    assert len(calls) == 2, "caching must be bypassed when disabled"


def test_locate_executable_finds_newly_added_path_dir(tmpdir, xession):
    """The hot path used to resolve every subprocess command must also
    benefit from the cache, and must still notice a $PATH change without
    needing an explicit cache reset."""
    bindir1 = tmpdir.mkdir("bindir1")
    bindir2 = tmpdir.mkdir("bindir2")
    name = "onlyinbindir2.EXE" if ON_WINDOWS else "onlyinbindir2"
    (f := bindir2 / name).write_text("binary", encoding="utf8")
    os.chmod(f, 0o777)
    pathext = [".EXE"] if ON_WINDOWS else []

    executables_mod._clear_paths_cache_key = None

    with xession.env.swap(PATH=[str(bindir1)], PATHEXT=pathext):
        assert locate_executable(name) is None
        with xession.env.swap(PATH=[str(bindir1), str(bindir2)], PATHEXT=pathext):
            assert locate_executable(name) is not None


def test_locate_executable(tmpdir, xession):
    bindir0 = tmpdir.mkdir("bindir0")  # current working directory
    bindir1 = tmpdir.mkdir("bindir1")
    bindir2 = tmpdir.mkdir("bindir2")
    bindir3 = tmpdir.mkdir("bindir3")
    bindir2.mkdir("subdir")
    executables = ["file1.EXE", "file2.COM", "file2.EXE", "file3"]
    not_executables = ["file4.EXE", "file5"]
    for exefile in executables + not_executables:
        f = bindir2 / exefile
        f.write_text("binary", encoding="utf8")
        if exefile in executables:
            os.chmod(f, 0o777)

    # Test current working directory.
    (bindir0 / "cwd_non_bin_file").write_text("binary", encoding="utf8")
    (f := bindir0 / "cwd_bin_file.EXE").write_text("binary", encoding="utf8")
    os.chmod(f, 0o777)

    # Test overlapping file names in different bin directories.
    (f := bindir3 / "file3").write_text("binary", encoding="utf8")
    os.chmod(f, 0o777)

    pathext = [".EXE", ".COM"] if ON_WINDOWS else []
    sep = os.path.sep

    with (
        xession.env.swap(
            PATH=[str(bindir1), str(bindir2), str(bindir3)], PATHEXT=pathext
        ),
        chdir(str(bindir0)),
    ):
        # From current working directory
        assert locate_executable(f".{sep}cwd_non_bin_file") is None
        assert locate_executable(f".{sep}cwd_bin_file.EXE")
        assert locate_executable(f"..{sep}bindir0{sep}cwd_bin_file.EXE")
        assert locate_executable(str(bindir0 / "cwd_bin_file.EXE"))
        if ON_WINDOWS:
            assert locate_executable(f".{sep}cwd_bin_file")
            assert locate_executable(str(bindir0 / "cwd_bin_file"))
            assert locate_executable(f"..{sep}bindir0{sep}cwd_bin_file")

            # PATHEXT resolution must return the path WITH the matched extension
            # so that CreateProcess can find the file (it only auto-appends .exe)
            result = locate_executable(f".{sep}cwd_bin_file")
            assert result.endswith("cwd_bin_file.exe"), (
                f"PATHEXT resolution should include extension: {result}"
            )

        # From PATH
        assert locate_executable("file1.EXE")
        assert locate_executable("nofile") is None
        assert locate_executable("file5") is None
        assert locate_executable("subdir") is None
        if ON_WINDOWS:
            assert locate_executable("file1")
            assert locate_executable("file4")
            assert locate_executable("file2").endswith("file2.exe")
        else:
            assert locate_executable("file3").find("bindir2") > 0
            assert locate_executable("file1") is None
            assert locate_executable("file4") is None
            assert locate_executable("file2") is None


def test_locate_relative_path_returns_found_name(tmpdir, xession):
    """When PATHEXT finds a file with extension, the returned path must include that extension."""
    bindir = tmpdir.mkdir("reldir")
    # use lowercase extension: get_possible_names lowercases extensions for lowercase input
    (f := bindir / "myapp.exe").write_text("binary", encoding="utf8")
    os.chmod(f, 0o777)

    pathext = [".EXE"]
    with xession.env.swap(PATH=[], PATHEXT=pathext), chdir(str(bindir)):
        result = locate_relative_path("./myapp", use_pathext=True)
        assert result is not None
        assert os.path.basename(result) == "myapp.exe"


def test_locate_file(tmpdir, xession):
    bindir1 = tmpdir.mkdir("bindir1")
    bindir2 = tmpdir.mkdir("bindir2")
    bindir3 = tmpdir.mkdir("bindir3")
    file = bindir2 / "findme"
    file.write_text("", encoding="utf8")
    with xession.env.swap(PATH=[str(bindir1), str(bindir2), str(bindir3)]):
        f = locate_file("findme")
        assert str(f) == str(file)


def test_stable_dir_cache(tmpdir, xession):
    """Directories in $PYGWIN_COMMANDS_CACHE_READ_DIR_ONCE are scanned once
    and subsequent lookups use the cached frozenset instead of stat()."""
    stable = tmpdir.mkdir("stable")
    (f := stable / "runme.EXE").write_text("binary", encoding="utf8")
    os.chmod(f, 0o777)

    pathext = [".EXE"] if ON_WINDOWS else []
    stable_str = str(stable)

    # Reset module-level cache state from previous tests
    executables_mod._stable_prefixes_source = None
    executables_mod._stable_prefixes = ()
    _stable_dir_cache.clear()
    executables_mod._stable_dir_reported.clear()

    # --- Without caching: dir is not in CACHE_READ_DIR_ONCE ---
    with xession.env.swap(
        PATH=[stable_str],
        PATHEXT=pathext,
        PYGWIN_COMMANDS_CACHE_READ_DIR_ONCE=[],
    ):
        result = locate_executable("runme.EXE")
        assert result is not None
        assert "runme" in result.lower()
        # _cached_dir_contains returns None for non-stable dirs
        assert _cached_dir_contains(stable_str, "runme.EXE") is None
        assert stable_str not in _stable_dir_cache

    # --- With caching: add the dir to CACHE_READ_DIR_ONCE ---
    with xession.env.swap(
        PATH=[stable_str],
        PATHEXT=pathext,
        PYGWIN_COMMANDS_CACHE_READ_DIR_ONCE=[stable_str],
    ):
        result = locate_executable("runme.EXE")
        assert result is not None
        assert "runme" in result.lower()
        # Dir is now cached
        assert stable_str in _stable_dir_cache
        assert "runme.exe" in _stable_dir_cache[stable_str]
        # Subsequent lookup returns from cache (found=True)
        cached = _cached_dir_contains(stable_str, "runme.EXE")
        assert cached is not None
        found, _populated = cached
        assert found is True
        # Non-existent file returns (False, ...)
        cached_miss = _cached_dir_contains(stable_str, "nope.EXE")
        assert cached_miss is not None
        assert cached_miss[0] is False


def test_stable_dir_cache_skips_directories(tmpdir, xession):
    """A directory inside a cached $PATH entry must not be returned
    by locate_executable — even when the directory has +x permission."""
    stable = tmpdir.mkdir("stable")
    # Create a subdirectory named "man" (like coreutils gnubin/man)
    stable.mkdir("man")
    # Create a real executable so the dir is not empty
    exe_name = "ls.EXE" if ON_WINDOWS else "ls"
    (f := stable / exe_name).write_text("binary", encoding="utf8")
    os.chmod(f, 0o777)

    stable_str = str(stable)
    pathext = [".EXE"] if ON_WINDOWS else []

    executables_mod._stable_prefixes_source = None
    executables_mod._stable_prefixes = ()
    _stable_dir_cache.clear()
    executables_mod._stable_dir_reported.clear()

    with xession.env.swap(
        PATH=[stable_str],
        PATHEXT=pathext,
        PYGWIN_COMMANDS_CACHE_READ_DIR_ONCE=[stable_str],
    ):
        # "man" is a directory — must not be found
        assert locate_executable("man") is None
        # executable file must be found
        assert locate_executable(exe_name) is not None
