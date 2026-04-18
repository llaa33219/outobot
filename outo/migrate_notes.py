"""
Note-to-outowiki migration utility.

Migrates existing note files from ~/.outobot/note/ into outowiki memory
by creating synthetic conversations and calling outowiki.record().

Usage:
    python -m outo.migrate_notes [--dry-run]
"""

import argparse
import logging
import sys
from pathlib import Path

from outo.agents import NOTE_DIR
from outo.memory import MemoryManager, _conversation_to_record_content
from outo.providers import ProviderManager

logger = logging.getLogger(__name__)

CONFIG_DIR = Path.home() / ".outobot" / "config"

SKIP_FILES = {"me.md"}


def migrate_note_file(
    filepath: Path,
    memory_manager: MemoryManager,
    dry_run: bool = False,
) -> bool:
    """Migrate a single note file into outowiki. Returns True on success."""
    try:
        content = filepath.read_text(encoding="utf-8").strip()
    except OSError as e:
        logger.error("Failed to read %s: %s", filepath.name, e)
        return False

    if not content:
        logger.info("Skipping %s: empty file", filepath.name)
        return False

    note_name = filepath.stem.replace("-", " ").replace("_", " ")

    conversation: list[dict[str, str]] = [
        {
            "role": "user",
            "content": (
                f"Here are my notes about '{note_name}'. "
                f"Please remember this information:\n\n{content}"
            ),
        },
        {
            "role": "assistant",
            "content": (
                f"I've noted your information about '{note_name}'. "
                "I'll remember these details for future reference."
            ),
        },
    ]

    if dry_run:
        print(f"  [dry-run] Would migrate: {filepath.name} ({len(content)} chars)")
        return True

    if not memory_manager.is_available:
        logger.error("outowiki is not available — cannot migrate")
        return False

    wiki = memory_manager._outowiki
    if wiki is None:
        logger.error("outowiki instance is None — cannot migrate")
        return False

    try:
        record_content = _conversation_to_record_content(conversation)
        if record_content:
            wiki.record(record_content, metadata={"type": "conversation", "source": "migration"})
        print(f"  Migrated: {filepath.name} ({len(content)} chars)")
        return True
    except Exception as e:
        logger.error("Failed to migrate %s: %s", filepath.name, e)
        return False


def main() -> None:

    parser = argparse.ArgumentParser(
        description="Migrate note files from ~/.outobot/note/ into outowiki memory.",
    )
    _ = parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview migration without actually storing anything.",
    )
    args = parser.parse_args()
    dry_run: bool = bool(args.dry_run)

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    if not NOTE_DIR.exists():
        print(f"Note directory not found: {NOTE_DIR}")
        sys.exit(1)

    note_files = sorted(f for f in NOTE_DIR.glob("*.md") if f.name not in SKIP_FILES)

    if not note_files:
        print("No note files to migrate.")
        sys.exit(0)

    print(f"Found {len(note_files)} note file(s) in {NOTE_DIR}")
    if dry_run:
        print("Running in dry-run mode (no changes will be made)\n")
    else:
        print()

    provider_manager = ProviderManager(CONFIG_DIR)
    memory_manager = MemoryManager(
        config_dir=CONFIG_DIR,
        provider_manager=provider_manager,
    )

    if not dry_run and not memory_manager.is_available:
        print(
            "Error: outowiki is not available. Check memory configuration in settings."
        )
        sys.exit(1)

    migrated = 0
    skipped = 0

    for filepath in note_files:
        success = migrate_note_file(filepath, memory_manager, dry_run=dry_run)
        if success:
            migrated += 1
        else:
            skipped += 1

    print(f"\nDone: {migrated} migrated, {skipped} skipped.")
    if not dry_run and migrated > 0:
        print("Note files have been preserved (not deleted).")


if __name__ == "__main__":
    main()
