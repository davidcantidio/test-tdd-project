#!/usr/bin/env python3
"""
Validate .gitignore patterns are working correctly
"""

import subprocess
import sys
from pathlib import Path


def test_gitignore_patterns() -> bool:
    """Test that gitignore patterns work correctly"""

    test_files = [
        ".streamlit_cache/test.txt",
        "__pycache__/test.pyc",
        "logs/test.log",
        ".DS_Store",
        "temp/test.tmp",
    ]

    for test_file in test_files:
        Path(test_file).parent.mkdir(parents=True, exist_ok=True)
        Path(test_file).touch()

    result = subprocess.run([
        "git",
        "status",
        "--porcelain",
    ], capture_output=True, text=True)

    ignored_count = 0
    for test_file in test_files:
        if test_file not in result.stdout:
            ignored_count += 1
            print(f"✅ {test_file} - properly ignored")
        else:
            print(f"❌ {test_file} - NOT ignored")

    for test_file in test_files:
        p = Path(test_file)
        if p.exists():
            p.unlink()
        parent = p.parent
        if parent.exists() and not any(parent.iterdir()):
            parent.rmdir()

    print(f"\n📊 GITIGNORE VALIDATION: {ignored_count}/{len(test_files)} patterns working")
    return ignored_count == len(test_files)


if __name__ == "__main__":
    success = test_gitignore_patterns()
    sys.exit(0 if success else 1)
