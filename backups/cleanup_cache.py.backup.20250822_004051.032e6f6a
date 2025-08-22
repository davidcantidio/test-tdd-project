#!/usr/bin/env python3
"""
Cache Cleanup Script
Removes cache artifacts and cleans up the repository.
"""

import os
import shutil
import glob
from pathlib import Path
from typing import List, Dict


def find_cache_files() -> Dict[str, List[str]]:
    """Find all cache files and directories in the project."""
    cache_patterns = {
        'python_cache': ['**/__pycache__', '**/*.pyc', '**/*.pyo'],
        'streamlit_cache': ['**/.streamlit_cache', '**/streamlit_cache', '**/.streamlit'],
        'pytest_cache': ['**/.pytest_cache', '**/.cache'],
        'coverage_cache': ['**/.coverage', '**/htmlcov', '**/.coverage.*'],
        'other_cache': ['**/*_cache.json', '**/*.cache', '**/logs'],
        'temp_files': ['**/*.tmp', '**/*.temp', '**/*.log']
    }

    found_files = {}
    for category, patterns in cache_patterns.items():
        found_files[category] = []
        for pattern in patterns:
            found_files[category].extend(glob.glob(pattern, recursive=True))

    return found_files


def remove_cache_files(dry_run: bool = False) -> Dict[str, int]:
    """Remove cache files and return counts."""
    cache_files = find_cache_files()
    removed_counts = {}

    for category, files in cache_files.items():
        removed_counts[category] = 0

        for file_path in files:
            try:
                if os.path.isfile(file_path):
                    if not dry_run:
                        os.remove(file_path)
                    removed_counts[category] += 1
                    print(f"{'[DRY RUN] ' if dry_run else ''}Removed file: {file_path}")

                elif os.path.isdir(file_path):
                    if not dry_run:
                        shutil.rmtree(file_path)
                    removed_counts[category] += 1
                    print(f"{'[DRY RUN] ' if dry_run else ''}Removed directory: {file_path}")

            except Exception as e:
                print(f"Error removing {file_path}: {e}")

    return removed_counts


def check_gitignore_coverage() -> List[str]:
    """Check if .gitignore covers all cache patterns."""
    gitignore_path = Path('.gitignore')

    if not gitignore_path.exists():
        return ["No .gitignore file found"]

    with open(gitignore_path, 'r') as f:
        gitignore_content = f.read()

    missing_patterns = []
    required_patterns = [
        '__pycache__/',
        '.streamlit_cache/',
        '.pytest_cache/',
        '.coverage',
        '*.log',
        '*.cache',
        '.cache/',
        '*.tmp'
    ]

    for pattern in required_patterns:
        if pattern not in gitignore_content:
            missing_patterns.append(pattern)

    return missing_patterns


def get_repository_size() -> Dict[str, float]:
    """Calculate repository size breakdown."""
    sizes = {}

    # Calculate cache size
    cache_files = find_cache_files()
    cache_size = 0
    for files in cache_files.values():
        for file_path in files:
            if os.path.exists(file_path):
                if os.path.isfile(file_path):
                    cache_size += os.path.getsize(file_path)
                elif os.path.isdir(file_path):
                    for dirpath, dirnames, filenames in os.walk(file_path):
                        for filename in filenames:
                            filepath = os.path.join(dirpath, filename)
                            try:
                                cache_size += os.path.getsize(filepath)
                            except OSError:
                                pass

    # Calculate total repository size
    total_size = 0
    for dirpath, dirnames, filenames in os.walk('.'):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            try:
                total_size += os.path.getsize(filepath)
            except OSError:
                pass

    sizes['cache_size_mb'] = cache_size / (1024 * 1024)
    sizes['total_size_mb'] = total_size / (1024 * 1024)
    sizes['cache_percentage'] = (cache_size / total_size * 100) if total_size > 0 else 0

    return sizes


def main():
    """Main cleanup function."""
    print("🧹 Cache Cleanup Tool")
    print("=" * 50)

    # Check current state
    print("\n📊 Repository Analysis:")
    sizes = get_repository_size()
    print(f"Total repository size: {sizes['total_size_mb']:.2f} MB")
    print(f"Cache files size: {sizes['cache_size_mb']:.2f} MB")
    print(f"Cache percentage: {sizes['cache_percentage']:.1f}%")

    # Check .gitignore coverage
    print("\n🔍 GitIgnore Analysis:")
    missing_patterns = check_gitignore_coverage()
    if missing_patterns:
        print("⚠️ Missing patterns in .gitignore:")
        for pattern in missing_patterns:
            print(f"  - {pattern}")
    else:
        print("✅ All cache patterns covered in .gitignore")

    # Show what would be removed (dry run)
    print("\n🔍 Cache Files Found:")
    cache_files = find_cache_files()
    total_files = sum(len(files) for files in cache_files.values())

    if total_files == 0:
        print("✅ No cache files found - repository is clean!")
        return

    for category, files in cache_files.items():
        if files:
            print(f"  {category}: {len(files)} items")

    print(f"\nTotal cache items: {total_files}")

    # Ask for confirmation
    response = input("\n🗑️ Remove all cache files? (y/N): ").strip().lower()

    if response in ['y', 'yes']:
        print("\n🧹 Cleaning cache files...")
        removed_counts = remove_cache_files(dry_run=False)

        total_removed = sum(removed_counts.values())
        print(f"\n✅ Cleanup complete! Removed {total_removed} items")

        # Show final sizes
        print("\n📊 Final Repository Analysis:")
        final_sizes = get_repository_size()
        print(f"Total repository size: {final_sizes['total_size_mb']:.2f} MB")
        print(f"Cache files size: {final_sizes['cache_size_mb']:.2f} MB")
        print(f"Space saved: {sizes['cache_size_mb'] - final_sizes['cache_size_mb']:.2f} MB")

    else:
        print("❌ Cleanup cancelled")


if __name__ == "__main__":
    main()
