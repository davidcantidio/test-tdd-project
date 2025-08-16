from __future__ import annotations

"""Utilities for cleaning cache directories and repository artifacts."""

from pathlib import Path
import shutil
from typing import Iterable
import sqlite3


class CacheCleanup:
    """Handle removal of temporary cache directories and gitignore updates."""

    def __init__(self, base_path: Path | str = "."):
        self.base_path = Path(base_path)

    def remove_streamlit_cache(self) -> None:
        """Remove Streamlit cache directories."""
        for target in [".streamlit_cache", ".streamlit"]:
            path = self.base_path / target
            if path.exists():
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()

    def clean_temp_files(self) -> None:
        """Remove Python cache files and temporary directories."""
        for pattern in ("**/__pycache__", "**/*.pyc", "**/.pytest_cache"):
            for item in self.base_path.glob(pattern):
                if item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)
                else:
                    item.unlink(missing_ok=True)

    def update_gitignore(self) -> None:
        """Update .gitignore with cache patterns."""
        gitignore = self.base_path / ".gitignore"
        entries = [".streamlit_cache/", "__pycache__/", "*.pyc", ".pytest_cache/"]
        lines = []
        if gitignore.exists():
            lines = gitignore.read_text().splitlines()
        updated = False
        for entry in entries:
            if entry not in lines:
                lines.append(entry)
                updated = True
        if updated:
            gitignore.write_text("\n".join(lines) + "\n")

    def validate_cleanup(self) -> bool:
        """Validate that cache directories have been removed."""
        return not (self.base_path / ".streamlit_cache").exists()


class DataCleanup:
    """Basic data cleanup operations for SQLite databases."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def remove_orphaned_records(self) -> None:
        """Remove orphaned task records without valid epic references."""
        self.conn.execute(
            "DELETE FROM framework_tasks WHERE epic_id NOT IN (SELECT id FROM framework_epics)"
        )
        self.conn.commit()

    def normalize_data(self) -> None:
        """Normalize empty status fields to default values."""
        self.conn.execute(
            "UPDATE framework_epics SET status='pending' WHERE status IS NULL OR status=''"
        )
        self.conn.commit()

    def fix_inconsistencies(self) -> None:
        """Fix data inconsistencies like NULL priority values."""
        self.conn.execute(
            "UPDATE framework_epics SET priority=1 WHERE priority IS NULL"
        )
        self.conn.commit()

    def vacuum_database(self) -> None:
        """Vacuum database to reclaim space and optimize storage."""
        self.conn.execute("VACUUM")


class RepositoryCleanup:
    """Placeholder for repository cleanup operations."""

    def clean_git_history(self) -> None:  # pragma: no cover - demonstration only
        """Clean git history (placeholder implementation)."""
        pass

    def remove_large_files(self) -> None:  # pragma: no cover - demonstration only
        """Remove large files from repository (placeholder implementation)."""
        pass

    def optimize_repository(self) -> None:  # pragma: no cover - demonstration only
        """Optimize repository structure (placeholder implementation)."""
        pass