#!/usr/bin/env python3
"""
🎯 Focused Validation Script - Phase 4 Specific Corrections

Validates only the specific files and corrections made during Phase 4 refactoring.
Ignores backup files and focuses on the actual changes made.
"""

import ast
import os
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Any
import sys

def get_file_metrics(file_path: Path) -> Dict[str, Any]:
    """Get file size metrics."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        return {
            'total_lines': len(lines),
            'non_empty_lines': len([line for line in lines if line.strip()]),
            'comment_lines': len([line for line in lines if line.strip().startswith('#')]),
            'code_lines': len([line for line in lines if line.strip() and not line.strip().startswith('#')])
        }
    except Exception as e:
        return {'error': str(e)}

def check_specific_duplications():
    """Check for specific duplications that were the focus of our refactoring."""
    print("🔍 FOCUSED VALIDATION: Function Duplications in Key Files")
    print("-" * 60)
    
    # Focus on the specific files we refactored
    target_files = [
        "streamlit_extension/streamlit_app.py",
        "streamlit_extension/utils/streamlit_helpers.py", 
        "streamlit_extension/utils/ui_operations.py",
        "streamlit_extension/utils/cache_utils.py",
        "streamlit_extension/utils/data_utils.py",
        "streamlit_extension/utils/path_utils.py",
        "streamlit_extension/components/page_manager.py",
        "streamlit_extension/utils/session_manager.py"
    ]
    
    functions_by_file = {}
    
    for file_path in target_files:
        path = Path(file_path)
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content, filename=str(path))
                functions = []
                
                class FunctionCollector(ast.NodeVisitor):
                    def visit_FunctionDef(self, node):
                        functions.append(node.name)
                
                collector = FunctionCollector()
                collector.visit(tree)
                functions_by_file[str(path)] = functions
                
                print(f"✅ {file_path}: {len(functions)} functions")
                
            except Exception as e:
                print(f"❌ {file_path}: Error - {e}")
        else:
            print(f"⚠️ {file_path}: File not found")
    
    # Check for duplications between streamlit_helpers and the extracted modules
    helpers_functions = set(functions_by_file.get("streamlit_extension/utils/streamlit_helpers.py", []))
    ui_functions = set(functions_by_file.get("streamlit_extension/utils/ui_operations.py", []))
    cache_functions = set(functions_by_file.get("streamlit_extension/utils/cache_utils.py", []))
    data_functions = set(functions_by_file.get("streamlit_extension/utils/data_utils.py", []))
    
    overlaps = []
    if helpers_functions & ui_functions:
        overlaps.append(f"streamlit_helpers ↔ ui_operations: {helpers_functions & ui_functions}")
    if helpers_functions & cache_functions:
        overlaps.append(f"streamlit_helpers ↔ cache_utils: {helpers_functions & cache_functions}")  
    if helpers_functions & data_functions:
        overlaps.append(f"streamlit_helpers ↔ data_utils: {helpers_functions & data_functions}")
    
    if overlaps:
        print("\n❌ Function overlaps found:")
        for overlap in overlaps:
            print(f"   {overlap}")
        return False
    else:
        print("\n✅ No critical function overlaps in refactored modules!")
        return True

def check_session_violations_in_target_files():
    """Check session state violations in the files we specifically fixed."""
    print("\n🔍 FOCUSED VALIDATION: Session State in Fixed Files")
    print("-" * 60)
    
    # Files where we specifically fixed session state violations
    target_files = [
        "streamlit_extension/components/debug_widgets.py",
        "streamlit_extension/components/page_manager.py", 
        "streamlit_extension/components/layout_renderers.py",
        "streamlit_extension/components/analytics_cards.py",
    ]
    
    violations_found = 0
    
    for file_path in target_files:
        path = Path(file_path)
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for direct st.session_state usage
                direct_access_lines = []
                for i, line in enumerate(content.split('\n'), 1):
                    if 'st.session_state[' in line or 'st.session_state.' in line:
                        if 'from' not in line and 'import' not in line:  # Ignore imports
                            direct_access_lines.append(i)
                
                if direct_access_lines:
                    print(f"❌ {file_path}: {len(direct_access_lines)} violations on lines: {direct_access_lines}")
                    violations_found += len(direct_access_lines)
                else:
                    print(f"✅ {file_path}: No direct session state access")
                    
            except Exception as e:
                print(f"❌ {file_path}: Error - {e}")
        else:
            print(f"⚠️ {file_path}: File not found")
    
    if violations_found == 0:
        print(f"\n✅ No session state violations in fixed files!")
        return True
    else:
        print(f"\n❌ Found {violations_found} session state violations in target files")
        return False

def check_file_size_reductions():
    """Check if we achieved file size reductions in target files."""
    print("\n🔍 FOCUSED VALIDATION: File Size Reductions")
    print("-" * 60)
    
    # Expected results based on our refactoring
    expected_sizes = {
        "streamlit_extension/utils/streamlit_helpers.py": {"max": 200, "description": "Refactored facade"},
        "streamlit_extension/utils/ui_operations.py": {"max": 300, "description": "UI operations extract"},
        "streamlit_extension/utils/cache_utils.py": {"max": 200, "description": "Cache utilities extract"}, 
        "streamlit_extension/utils/data_utils.py": {"max": 200, "description": "Data utilities extract"},
        "streamlit_extension/utils/path_utils.py": {"max": 100, "description": "Path utilities extract"},
    }
    
    all_compliant = True
    
    for file_path, expected in expected_sizes.items():
        path = Path(file_path)
        if path.exists():
            metrics = get_file_metrics(path)
            if 'error' not in metrics:
                lines = metrics['total_lines']
                if lines <= expected['max']:
                    print(f"✅ {expected['description']}: {lines} lines (≤{expected['max']})")
                else:
                    print(f"❌ {expected['description']}: {lines} lines (>{expected['max']})")
                    all_compliant = False
            else:
                print(f"❌ {file_path}: Error reading file")
                all_compliant = False
        else:
            print(f"❌ {file_path}: File not found")
            all_compliant = False
    
    return all_compliant

def check_import_functionality():
    """Test if the new modular imports work correctly."""
    print("\n🔍 FOCUSED VALIDATION: Import Functionality")
    print("-" * 60)
    
    import_tests = [
        ("from streamlit_extension.utils.ui_operations import is_ui", "UI operations import"),
        ("from streamlit_extension.utils.cache_utils import cache_data", "Cache utils import"),
        ("from streamlit_extension.utils.data_utils import ensure_list", "Data utils import"),
        ("from streamlit_extension.utils.path_utils import get_project_root", "Path utils import"),
        ("from streamlit_extension.utils.streamlit_helpers import is_ui", "Facade import"),
    ]
    
    successful_imports = 0
    
    for import_statement, description in import_tests:
        try:
            exec(import_statement)
            print(f"✅ {description}: Success")
            successful_imports += 1
        except Exception as e:
            print(f"❌ {description}: {e}")
    
    return successful_imports == len(import_tests)

def run_focused_validation():
    """Run focused validation of Phase 4 specific corrections."""
    
    print("🎯 FOCUSED VALIDATION - Phase 4 Specific Corrections")
    print("=" * 70)
    
    results = []
    
    # Test 1: Function duplications
    results.append(check_specific_duplications())
    
    # Test 2: Session state violations
    results.append(check_session_violations_in_target_files())
    
    # Test 3: File size reductions
    results.append(check_file_size_reductions())
    
    # Test 4: Import functionality
    results.append(check_import_functionality())
    
    # Calculate score
    passed_tests = sum(results)
    total_tests = len(results)
    score_percentage = (passed_tests / total_tests) * 100
    
    print("\n🏆 FOCUSED VALIDATION RESULTS")
    print("=" * 50)
    print(f"📊 SCORE: {passed_tests}/{total_tests} ({score_percentage:.1f}%)")
    
    if score_percentage == 100:
        print("🎉 PERFECT! All Phase 4 corrections successful!")
    elif score_percentage >= 75:
        print("✅ EXCELLENT! Phase 4 corrections largely successful!")
    elif score_percentage >= 50:
        print("⚠️ GOOD! Most corrections successful, minor issues remain.")
    else:
        print("❌ NEEDS WORK! Several corrections need attention.")
    
    return score_percentage >= 75

if __name__ == "__main__":
    success = run_focused_validation()
    sys.exit(0 if success else 1)