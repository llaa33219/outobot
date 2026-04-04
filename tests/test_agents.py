import importlib
from pathlib import Path
from unittest.mock import patch
from typing import Callable, Protocol, cast


class AgentsModule(Protocol):
    NOTE_DIR: Path

    def _load_note_file(self, filename: str) -> str | None: ...

    def get_me_content(self) -> str | None: ...

    def get_important_content(self) -> str | None: ...

    def get_note_catalog(self) -> str: ...

    def build_note_extra_instructions(self) -> str | None: ...


agents = cast(AgentsModule, cast(object, importlib.import_module("outo.agents")))

_load_note_file = cast(Callable[[str], str | None], getattr(agents, "_load_note_file"))
get_me_content = cast(Callable[[], str | None], getattr(agents, "get_me_content"))
get_important_content = cast(
    Callable[[], str | None], getattr(agents, "get_important_content")
)
get_note_catalog = cast(Callable[[], str], getattr(agents, "get_note_catalog"))
build_note_extra_instructions = cast(
    Callable[[], str | None], getattr(agents, "build_note_extra_instructions")
)


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


class TestGetImportantContent:
    def test_returns_none_when_important_missing(self, tmp_path: Path):
        with patch.object(agents, "NOTE_DIR", tmp_path):
            assert get_important_content() is None

    def test_returns_none_when_important_empty(self, tmp_path: Path):
        _ = _write_note(tmp_path, "important.md", "\n  \n")

        with patch.object(agents, "NOTE_DIR", tmp_path):
            assert get_important_content() is None

    def test_returns_content_when_important_has_substance(self, tmp_path: Path):
        _ = _write_note(tmp_path, "important.md", "User prefers short answers.")

        with patch.object(agents, "NOTE_DIR", tmp_path):
            assert get_important_content() == "User prefers short answers."


class TestGetNoteCatalog:
    def test_returns_empty_string_when_no_extra_notes(self, tmp_path: Path):
        _ = _write_note(tmp_path, "me.md", "I am direct.")
        _ = _write_note(tmp_path, "important.md", "User likes bullets.")
        _ = _write_note(tmp_path, "README.md", "Ignore me.")

        with patch.object(agents, "NOTE_DIR", tmp_path):
            assert get_note_catalog() == ""

    def test_returns_sorted_catalog_for_extra_notes(self, tmp_path: Path):
        _ = _write_note(tmp_path, "project-alpha.md", "Project alpha details.")
        _ = _write_note(tmp_path, "api-patterns.md", "API patterns.")
        _ = _write_note(tmp_path, "README.md", "Ignore me.")

        with patch.object(agents, "NOTE_DIR", tmp_path):
            catalog = get_note_catalog()

        assert (
            catalog.startswith(
                "\n\nOther note files (read on demand: cat ~/.outobot/note/<filename>):"
            )
            is True
        )
        assert "- api-patterns.md" in catalog
        assert "- project-alpha.md" in catalog
        assert "README.md" not in catalog


class TestBuildNoteExtraInstructions:
    def test_returns_first_time_hint_when_no_notes_exist(self, tmp_path: Path):
        with patch.object(agents, "NOTE_DIR", tmp_path):
            message = build_note_extra_instructions()

        assert message is not None
        assert "## me.md (Agent Identity — MANDATORY)" in message
        assert "FIRST-TIME SETUP" in message
        assert "important.md" not in message

    def test_includes_me_only(self, tmp_path: Path):
        _ = _write_note(tmp_path, "me.md", "I speak concisely.")

        with patch.object(agents, "NOTE_DIR", tmp_path):
            message = build_note_extra_instructions()

        assert message is not None
        assert "## me.md (Agent Identity — MANDATORY)" in message
        assert "I speak concisely." in message
        assert "FIRST-TIME SETUP" not in message
        assert "important.md (User Context" not in message

    def test_includes_important_and_me_hint(self, tmp_path: Path):
        _ = _write_note(tmp_path, "important.md", "User prefers short answers.")

        with patch.object(agents, "NOTE_DIR", tmp_path):
            message = build_note_extra_instructions()

        assert message is not None
        assert "## me.md (Agent Identity — MANDATORY)" in message
        assert "FIRST-TIME SETUP" in message
        assert "## important.md (User Context — MANDATORY)" in message
        assert "User prefers short answers." in message

    def test_includes_both_core_notes_in_order(self, tmp_path: Path):
        _ = _write_note(tmp_path, "me.md", "I am direct.")
        _ = _write_note(tmp_path, "important.md", "User likes bullets.")

        with patch.object(agents, "NOTE_DIR", tmp_path):
            message = build_note_extra_instructions()

        assert message is not None
        assert "I am direct." in message
        assert "User likes bullets." in message
        assert "FIRST-TIME SETUP" not in message
        assert message.index("## me.md (Agent Identity — MANDATORY)") < message.index(
            "## important.md (User Context — MANDATORY)"
        )

    def test_includes_note_catalog_for_other_md_files(self, tmp_path: Path):
        _ = _write_note(tmp_path, "me.md", "I am direct.")
        _ = _write_note(tmp_path, "project-alpha.md", "Project alpha details.")
        _ = _write_note(tmp_path, "api-patterns.md", "API patterns.")
        _ = _write_note(tmp_path, "README.md", "Ignore me.")

        with patch.object(agents, "NOTE_DIR", tmp_path):
            message = build_note_extra_instructions()

        assert message is not None
        assert "Other note files (read on demand" in message
        assert "- api-patterns.md" in message
        assert "- project-alpha.md" in message
        assert "README.md" not in message
