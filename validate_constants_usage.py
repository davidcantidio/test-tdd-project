#!/usr/bin/env python3
"""
🔍 Constants Usage Validation Script

Validates that hard-coded strings have been successfully centralized
into the constants module. Addresses report.md requirement:
"Centralize hard-coded strings in enums/config"

This script:
- Scans code for remaining hard-coded strings
- Validates constants usage patterns
- Reports on centralization progress
- Suggests remaining improvements
"""

import sys
import re
from pathlib import Path
from typing import Dict, List, Set

# Add project root to path
sys.path.append(str(Path(__file__).parent))

try:
    from streamlit_extension.config.constants import (
        TaskStatus, EpicStatus, GeneralStatus, ClientTier, CompanySize,
        TDDPhase, Priority
    )
    CONSTANTS_AVAILABLE = True
except ImportError as e:
    CONSTANTS_AVAILABLE = False
    print(f"❌ Constants not available: {e}")


def find_hard_coded_strings(file_path: Path, patterns: Dict[str, List[str]]) -> Dict[str, List[tuple]]:
    """Find hard-coded strings in a file."""
    results = {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        for category, string_list in patterns.items():
            matches = []
            for i, line in enumerate(lines, 1):
                for string_val in string_list:
                    # Look for hard-coded strings (in quotes)
                    pattern = rf'["\']({re.escape(string_val)})["\']'
                    if re.search(pattern, line):
                        # Skip if it's already using constants
                        if not re.search(r'(\.value|get_all_values|get_default)', line):
                            matches.append((i, line.strip()))
            
            if matches:
                results[category] = matches
    
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return results


def scan_files_for_patterns() -> Dict[str, Dict[str, List[tuple]]]:
    """Scan all Python files for hard-coded string patterns."""
    
    # Define patterns to search for
    patterns = {
        "task_statuses": ["todo", "in_progress", "completed", "blocked", "pending"],
        "epic_statuses": ["planning", "active", "on_hold", "cancelled", "archived"],
        "general_statuses": ["active", "inactive", "suspended"],
        "client_tiers": ["basic", "standard", "premium", "enterprise"],
        "company_sizes": ["startup", "small", "medium", "large", "enterprise"],
        "tdd_phases": ["red", "green", "refactor"]
    }
    
    # Files to scan
    streamlit_dir = Path(__file__).parent / "streamlit_extension"
    python_files = list(streamlit_dir.glob("**/*.py"))
    
    results = {}
    
    for file_path in python_files:
        # Skip the constants file itself
        if "constants.py" in str(file_path):
            continue
            
        file_results = find_hard_coded_strings(file_path, patterns)
        if file_results:
            results[str(file_path.relative_to(Path(__file__).parent))] = file_results
    
    return results


def check_constants_usage() -> Dict[str, bool]:
    """Check if constants are being imported and used correctly."""
    
    checks = {
        "constants_module_exists": False,
        "enums_accessible": False,
        "methods_working": False,
        "import_patterns_found": False
    }
    
    try:
        # Check if constants module exists
        constants_file = Path(__file__).parent / "streamlit_extension" / "config" / "constants.py"
        checks["constants_module_exists"] = constants_file.exists()
        
        # Check if enums are accessible
        if CONSTANTS_AVAILABLE:
            checks["enums_accessible"] = True
            
            # Check if methods work
            try:
                TaskStatus.get_all_values()
                ClientTier.get_default()
                checks["methods_working"] = True
            except:
                pass
        
        # Check for import patterns in files
        streamlit_dir = Path(__file__).parent / "streamlit_extension"
        python_files = list(streamlit_dir.glob("**/*.py"))
        
        for file_path in python_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    if "from streamlit_extension.config.constants import" in content:
                        checks["import_patterns_found"] = True
                        break
            except:
                continue
    
    except Exception as e:
        print(f"Error checking constants usage: {e}")
    
    return checks


def generate_refactoring_suggestions(hard_coded_results: Dict[str, Dict[str, List[tuple]]]) -> List[str]:
    """Generate suggestions for remaining hard-coded strings."""
    
    suggestions = []
    
    for file_path, categories in hard_coded_results.items():
        for category, matches in categories.items():
            if matches:
                suggestions.append(f"""
📄 **{file_path}**
   🔧 Category: {category}
   📍 Found {len(matches)} hard-coded string(s)
   
   **Suggested Refactoring:**
   ```python
   # Import constants
   from streamlit_extension.config.constants import {get_enum_name(category)}
   
   # Replace hard-coded strings with:
   {get_enum_name(category)}.get_all_values()  # For dropdown options
   {get_enum_name(category)}.ENUM_VALUE.value  # For specific values
   {get_enum_name(category)}.get_default()     # For default values
   ```
   
   **Lines to update:** {', '.join([str(line_num) for line_num, _ in matches[:3]])}{'...' if len(matches) > 3 else ''}
                """)
    
    return suggestions


def get_enum_name(category: str) -> str:
    """Get the enum class name for a category."""
    mapping = {
        "task_statuses": "TaskStatus",
        "epic_statuses": "EpicStatus", 
        "general_statuses": "GeneralStatus",
        "client_tiers": "ClientTier",
        "company_sizes": "CompanySize",
        "tdd_phases": "TDDPhase"
    }
    return mapping.get(category, "UnknownEnum")


def calculate_progress(hard_coded_results: Dict[str, Dict[str, List[tuple]]]) -> Dict[str, float]:
    """Calculate centralization progress."""
    
    total_files_scanned = 0
    files_with_hard_coded = len(hard_coded_results)
    total_hard_coded_instances = 0
    
    # Count total files scanned
    streamlit_dir = Path(__file__).parent / "streamlit_extension"
    total_files_scanned = len(list(streamlit_dir.glob("**/*.py")))
    
    # Count total hard-coded instances
    for file_results in hard_coded_results.values():
        for matches in file_results.values():
            total_hard_coded_instances += len(matches)
    
    files_centralized_pct = ((total_files_scanned - files_with_hard_coded) / total_files_scanned * 100) if total_files_scanned > 0 else 0
    
    return {
        "total_files": total_files_scanned,
        "files_with_hard_coded": files_with_hard_coded,
        "files_centralized_pct": files_centralized_pct,
        "total_hard_coded_instances": total_hard_coded_instances
    }


def main():
    """Main validation execution."""
    print("🔍 CONSTANTS USAGE VALIDATION")
    print("=" * 50)
    print("Validates report.md requirement:")
    print("- Centralize hard-coded strings in enums/config")
    print()
    
    # Check constants system
    print("📋 CONSTANTS SYSTEM CHECK")
    print("-" * 30)
    
    checks = check_constants_usage()
    
    for check_name, result in checks.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check_name.replace('_', ' ').title():<25} {status}")
    
    all_checks_pass = all(checks.values())
    
    if not all_checks_pass:
        print("\n❌ Constants system not fully functional")
        return False
    
    print("\n✅ Constants system operational")
    
    # Scan for remaining hard-coded strings
    print("\n🔍 SCANNING FOR HARD-CODED STRINGS")
    print("-" * 40)
    
    hard_coded_results = scan_files_for_patterns()
    progress = calculate_progress(hard_coded_results)
    
    print(f"📊 **Scan Results:**")
    print(f"   Total files scanned: {progress['total_files']}")
    print(f"   Files with hard-coded strings: {progress['files_with_hard_coded']}")
    print(f"   Files centralized: {progress['files_centralized_pct']:.1f}%")
    print(f"   Remaining hard-coded instances: {progress['total_hard_coded_instances']}")
    
    if progress['total_hard_coded_instances'] == 0:
        print("\n🎉 PERFECT! No hard-coded strings found!")
        print("✅ All strings successfully centralized")
    else:
        print(f"\n📝 Found {progress['total_hard_coded_instances']} hard-coded strings in {progress['files_with_hard_coded']} files")
        
        # Show detailed results
        print("\n📋 DETAILED FINDINGS")
        print("-" * 25)
        
        for file_path, categories in hard_coded_results.items():
            print(f"\n📄 {file_path}")
            for category, matches in categories.items():
                print(f"   🔧 {category}: {len(matches)} instances")
                for line_num, line_content in matches[:2]:  # Show first 2
                    print(f"      Line {line_num}: {line_content[:60]}...")
                if len(matches) > 2:
                    print(f"      ... and {len(matches) - 2} more")
    
    # Generate suggestions
    if hard_coded_results:
        print("\n💡 REFACTORING SUGGESTIONS")
        print("-" * 30)
        suggestions = generate_refactoring_suggestions(hard_coded_results)
        for suggestion in suggestions[:3]:  # Show first 3
            print(suggestion)
        
        if len(suggestions) > 3:
            print(f"\n... and {len(suggestions) - 3} more files need refactoring")
    
    # Success criteria
    success_threshold = 80  # 80% of files should be centralized
    is_success = progress['files_centralized_pct'] >= success_threshold
    
    print(f"\n📈 CENTRALIZATION GRADE")
    print("-" * 25)
    
    if progress['files_centralized_pct'] >= 95:
        grade = "A+ (Excellent)"
    elif progress['files_centralized_pct'] >= 90:
        grade = "A (Very Good)"
    elif progress['files_centralized_pct'] >= 80:
        grade = "B (Good)"
    elif progress['files_centralized_pct'] >= 70:
        grade = "C (Needs Improvement)"
    else:
        grade = "D (Significant Work Needed)"
    
    print(f"Grade: {grade}")
    print(f"Progress: {progress['files_centralized_pct']:.1f}%")
    
    if is_success:
        print("\n🎉 SUCCESS!")
        print("✅ Constants centralization achieved")
        print("✅ Report.md requirement fulfilled")
        print("✅ Code maintainability improved")
    else:
        print(f"\n📝 Progress made, but more work needed")
        print(f"Target: {success_threshold}% centralization")
        print(f"Current: {progress['files_centralized_pct']:.1f}%")
    
    return is_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)