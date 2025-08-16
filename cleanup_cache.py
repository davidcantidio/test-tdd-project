#!/usr/bin/env python3
"""
Repository Cache Cleanup Script
Removes Streamlit cache artifacts and other temporary files
"""

import os
import shutil
from pathlib import Path
from typing import List, Tuple


class RepositoryCleanup:
    """Repository cleanup utility"""

    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root).resolve()
        self.removed_files: List[str] = []
        self.removed_dirs: List[str] = []
        self.errors: List[str] = []

    def _should_skip(self, path: Path) -> bool:
        """Return True if path is inside .git directory."""
        return ".git" in path.parts

    def find_cache_artifacts(self) -> List[Path]:
        """Find all cache artifacts in repository"""
        patterns = [
            "**/.streamlit_cache/",
            "**/streamlit_cache/",
            "**/__streamlit__/",
            "**/.streamlit/",
            "**/__pycache__/",
            "**/*.pyc",
            "**/*.pyo",
            "**/*.pyd",
            "**/logs/",
            "**/temp/",
            "**/tmp/",
            "**/.cache/",
            "**/*.log",
            "**/*~",
            "**/.DS_Store",
            "**/Thumbs.db",
        ]

        artifacts: List[Path] = []
        for pattern in patterns:
            matches = list(self.repo_root.glob(pattern))
            artifacts.extend(matches)
        return artifacts

    def clean_cache_files(self, dry_run: bool = False) -> Tuple[int, int]:
        """Clean cache files and directories"""
        artifacts = self.find_cache_artifacts()
        files_removed = 0
        dirs_removed = 0

        for artifact in artifacts:
            if self._should_skip(artifact):
                continue
            try:
                if artifact.is_file():
                    if not dry_run:
                        artifact.unlink()
                        self.removed_files.append(str(artifact))
                    files_removed += 1
                    print(f"{'[DRY RUN] Would remove' if dry_run else 'Removed'} file: {artifact}")
                elif artifact.is_dir():
                    if not dry_run:
                        shutil.rmtree(artifact)
                        self.removed_dirs.append(str(artifact))
                    dirs_removed += 1
                    print(f"{'[DRY RUN] Would remove' if dry_run else 'Removed'} directory: {artifact}")
            except Exception as e:
                error_msg = f"Error removing {artifact}: {e}"
                self.errors.append(error_msg)
                print(f"❌ {error_msg}")

        return files_removed, dirs_removed

    def clean_database_artifacts(self, dry_run: bool = False) -> int:
        """Clean database temporary files"""
        db_patterns = ["**/*.db-journal", "**/*.db-wal", "**/*.db-shm"]

        removed = 0
        for pattern in db_patterns:
            matches = list(self.repo_root.glob(pattern))
            for match in matches:
                if self._should_skip(match):
                    continue
                try:
                    if not dry_run:
                        match.unlink()
                        self.removed_files.append(str(match))
                    removed += 1
                    print(f"{'[DRY RUN] Would remove' if dry_run else 'Removed'} DB artifact: {match}")
                except Exception as e:
                    self.errors.append(f"Error removing {match}: {e}")
        return removed

    def generate_report(self) -> str:
        """Generate cleanup report"""
        report = f"""
🧹 REPOSITORY CLEANUP REPORT
{'='*50}

📊 SUMMARY:
- Files removed: {len(self.removed_files)}
- Directories removed: {len(self.removed_dirs)}
- Errors encountered: {len(self.errors)}

📁 REMOVED FILES:
{chr(10).join(f"  - {f}" for f in self.removed_files[:10])}
{'  - ... and more' if len(self.removed_files) > 10 else ''}

📂 REMOVED DIRECTORIES:
{chr(10).join(f"  - {d}" for d in self.removed_dirs)}

❌ ERRORS:
{chr(10).join(f"  - {e}" for e in self.errors)}

✅ CLEANUP COMPLETE!
"""
        return report


def main() -> None:
    """Main cleanup script"""
    import argparse

    parser = argparse.ArgumentParser(description="Repository Cache Cleanup")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be removed")
    parser.add_argument("--repo", default=".", help="Repository root path")
    args = parser.parse_args()

    print("🧹 Repository Cache Cleanup Starting...")
    print("=" * 50)

    cleanup = RepositoryCleanup(args.repo)

    # Clean cache artifacts
    files, dirs = cleanup.clean_cache_files(dry_run=args.dry_run)

    # Clean database artifacts
    db_files = cleanup.clean_database_artifacts(dry_run=args.dry_run)

    # Generate report
    print(cleanup.generate_report())

    if args.dry_run:
        print("🔍 DRY RUN COMPLETE - No files were actually removed")
        print("Run without --dry-run to perform actual cleanup")
    else:
        print("✅ CLEANUP COMPLETE")


if __name__ == "__main__":
    main()
