"""Tests for PygwinList — extended list returned by glob operations."""

import pathlib

import pytest

from pygwin.built_ins import PygwinList


class TestBasics:
    def test_is_list(self):
        xl = PygwinList([1, 2, 3])
        assert isinstance(xl, list)

    def test_empty(self):
        xl = PygwinList()
        assert len(xl) == 0
        assert xl.unique() == []
        assert xl.sorted() == []
        assert xl.files() == []
        assert xl.dirs() == []
        assert xl.exists() == []
        assert xl.paths() == []
        assert xl.filter(lambda x: True) == []

    def test_returns_pygwin_list(self):
        xl = PygwinList(["a", "b"])
        assert type(xl.unique()) is PygwinList
        assert type(xl.sorted()) is PygwinList
        assert type(xl.filter(lambda x: True)) is PygwinList
        assert type(xl.paths()) is PygwinList


class TestUnique:
    def test_deduplicates(self):
        assert PygwinList(["a", "b", "a", "c"]).unique() == ["a", "b", "c"]

    def test_preserves_order(self):
        assert PygwinList(["c", "a", "c", "b"]).unique() == ["c", "a", "b"]

    def test_with_tuples(self):
        xl = PygwinList([("a", "1"), ("b", "2"), ("a", "1")])
        assert xl.unique() == [("a", "1"), ("b", "2")]

    def test_with_paths(self):
        xl = PygwinList([pathlib.Path("a"), pathlib.Path("b"), pathlib.Path("a")])
        assert xl.unique() == [pathlib.Path("a"), pathlib.Path("b")]


class TestSorted:
    def test_alphabetical(self):
        assert PygwinList(["c", "a", "b"]).sorted() == ["a", "b", "c"]

    def test_reverse(self):
        assert PygwinList(["a", "b", "c"]).sorted(reverse=True) == ["c", "b", "a"]

    def test_key(self):
        assert PygwinList(["bb", "a", "ccc"]).sorted(key=len) == ["a", "bb", "ccc"]

    def test_tuples(self):
        xl = PygwinList([("b", "1"), ("a", "2")])
        assert xl.sorted() == [("a", "2"), ("b", "1")]


class TestFilter:
    def test_basic(self):
        xl = PygwinList(["foo.py", "bar.txt", "baz.py"])
        assert xl.filter(lambda x: x.endswith(".py")) == ["foo.py", "baz.py"]

    def test_tuples(self):
        xl = PygwinList([("src", "a.py"), ("test", "b.py")])
        assert xl.filter(lambda t: t[0] == "src") == [("src", "a.py")]


class TestPaths:
    def test_converts(self):
        result = PygwinList(["a.py", "b/c.py"]).paths()
        assert result == [pathlib.Path("a.py"), pathlib.Path("b/c.py")]
        assert all(isinstance(p, pathlib.Path) for p in result)

    def test_rejects_tuples(self):
        xl = PygwinList([("a", "b")])
        with pytest.raises(TypeError, match="select"):
            xl.paths()


class TestSelect:
    def test_picks_element(self):
        xl = PygwinList([("a", "1"), ("b", "2")])
        assert xl.select(0) == ["a", "b"]
        assert xl.select(1) == ["1", "2"]

    def test_skips_none(self):
        xl = PygwinList([("a", "x"), ("b", None)])
        assert xl.select(1) == ["x"]

    def test_passthrough_strings(self):
        xl = PygwinList(["a", "b"])
        assert xl.select(0) == ["a", "b"]

    def test_returns_pygwin_list(self):
        xl = PygwinList([("a", "b")])
        assert type(xl.select(0)) is PygwinList


class TestFilesystem:
    def test_files(self, tmp_path):
        (tmp_path / "a.txt").touch()
        (tmp_path / "subdir").mkdir()
        xl = PygwinList([str(tmp_path / "a.txt"), str(tmp_path / "subdir")])
        assert xl.files() == [str(tmp_path / "a.txt")]

    def test_dirs(self, tmp_path):
        (tmp_path / "a.txt").touch()
        (tmp_path / "subdir").mkdir()
        xl = PygwinList([str(tmp_path / "a.txt"), str(tmp_path / "subdir")])
        assert xl.dirs() == [str(tmp_path / "subdir")]

    def test_exists(self, tmp_path):
        (tmp_path / "a.txt").touch()
        xl = PygwinList([str(tmp_path / "a.txt"), str(tmp_path / "gone.txt")])
        assert xl.exists() == [str(tmp_path / "a.txt")]

    def test_rejects_tuples(self, tmp_path):
        xl = PygwinList([("a", "b")])
        for method in ("files", "dirs", "exists", "paths", "hidden", "visible"):
            with pytest.raises(TypeError, match="select"):
                getattr(xl, method)()


class TestHiddenVisible:
    def test_visible(self, tmp_path):
        (tmp_path / "visible").touch()
        (tmp_path / ".hidden").touch()
        xl = PygwinList([str(tmp_path / "visible"), str(tmp_path / ".hidden")])
        assert xl.visible() == [str(tmp_path / "visible")]

    def test_hidden(self, tmp_path):
        (tmp_path / "visible").touch()
        (tmp_path / ".hidden").touch()
        xl = PygwinList([str(tmp_path / "visible"), str(tmp_path / ".hidden")])
        assert xl.hidden() == [str(tmp_path / ".hidden")]

    def test_empty(self):
        assert PygwinList().visible() == []
        assert PygwinList().hidden() == []


class TestChaining:
    def test_full_chain(self, tmp_path):
        (tmp_path / "a.py").touch()
        (tmp_path / "b.py").touch()
        (tmp_path / "c.txt").touch()
        xl = PygwinList(
            [
                str(tmp_path / "b.py"),
                str(tmp_path / "a.py"),
                str(tmp_path / "a.py"),
                str(tmp_path / "gone.py"),
                str(tmp_path / "c.txt"),
            ]
        )
        result = xl.exists().unique().sorted().paths()
        assert result == [
            pathlib.Path(tmp_path / "a.py"),
            pathlib.Path(tmp_path / "b.py"),
            pathlib.Path(tmp_path / "c.txt"),
        ]

    def test_select_then_chain(self):
        xl = PygwinList([("dir", "a.py"), ("dir", "b.py"), ("dir", "a.py")])
        assert xl.select(1).unique().sorted() == ["a.py", "b.py"]
