import importlib
from pathlib import Path
from unittest.mock import patch
from typing import Callable, Protocol, cast


class AgentsModule(Protocol):
    NOTE_DIR: Path

    def _load_note_file(self, filename: str) -> str | None: ...

    def get_me_content(self) -> str | None: ...


agents = cast(AgentsModule, cast(object, importlib.import_module("outo.agents")))

_load_note_file = cast(Callable[[str], str | None], getattr(agents, "_load_note_file"))
get_me_content = cast(Callable[[], str | None], getattr(agents, "get_me_content"))


def _write_note(note_dir: Path, filename: str, content: str) -> Path:
    path = note_dir / filename
    _ = path.write_text(content, encoding="utf-8")
    return path


class TestLoadNoteFile:
    def test_missing_file_returns_none(self, tmp_path: Path):
        with patch.object(agents, "NOTE_DIR", tmp_path):
            assert _load_note_file("missing.md") is None

    def test_empty_file_returns_none(self, tmp_path: Path):
        _ = _write_note(tmp_path, "empty.md", "   \n\n")

        with patch.object(agents, "NOTE_DIR", tmp_path):
            assert _load_note_file("empty.md") is None

    def test_comment_only_file_returns_none(self, tmp_path: Path):
        _ = _write_note(
            tmp_path,
            "comments.md",
            "# heading\n<!-- comment -->\n> quote\n\n# another heading\n",
        )

        with patch.object(agents, "NOTE_DIR", tmp_path):
            assert _load_note_file("comments.md") is None

    def test_substantive_file_returns_content(self, tmp_path: Path):
        content = "# heading\nReal note line\n> quote\n"
        _ = _write_note(tmp_path, "note.md", content)

        with patch.object(agents, "NOTE_DIR", tmp_path):
            assert _load_note_file("note.md") == content.strip()


class TestGetMeContent:
    def test_returns_none_when_me_missing(self, tmp_path: Path):
        with patch.object(agents, "NOTE_DIR", tmp_path):
            assert get_me_content() is None

    def test_returns_none_when_me_empty(self, tmp_path: Path):
        _ = _write_note(tmp_path, "me.md", "\n  \n")

        with patch.object(agents, "NOTE_DIR", tmp_path):
            assert get_me_content() is None

    def test_returns_content_when_me_has_substance(self, tmp_path: Path):
        _ = _write_note(tmp_path, "me.md", "I prefer concise responses.")

        with patch.object(agents, "NOTE_DIR", tmp_path):
            assert get_me_content() == "I prefer concise responses."
