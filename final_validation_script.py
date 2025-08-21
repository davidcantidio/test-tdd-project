#!/usr/bin/env python3
"""
🔍 Final Validation Script - Phase 4 Refactoring

Comprehensive AST-based validation of all corrections made during refactoring.
Validates:
- Function duplications eliminated
- Session state violations fixed  
- File size compliance
- Import integrity
"""

import ast
import os
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Set, Any
import sys

class FinalValidationAnalyzer(ast.NodeVisitor):
    def __init__(self):
        # Function duplication tracking
        self.functions = defaultdict(list)
        
        # Session state violation tracking
        self.session_violations = []
        
        # Import tracking
        self.imports = []
        
        # Current file being analyzed
        self.current_file = ""

    def visit_FunctionDef(self, node):
        # Track function definitions for duplication analysis
        self.functions[node.name].append({
            'file': self.current_file,
            'line': node.lineno,
            'args': len(node.args.args) if node.args else 0
        })
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node):
        # Track async function definitions too
        self.functions[node.name].append({
            'file': self.current_file,
            'line': node.lineno,
            'args': len(node.args.args) if node.args else 0,
            'async': True
        })
        self.generic_visit(node)
    
    # TODO: Consider extracting this block into a separate method
    # TODO: Consider extracting this block into a separate method
    def visit_Attribute(self, node):
        # Detect session state violations (st.session_state direct access)
        if (isinstance(node.value, ast.Name) and 
            node.value.id == 'st' and 
            node.attr == 'session_state'):
            self.session_violations.append({
                'file': self.current_file,
                'line': node.lineno,
                'context': 'st.session_state direct access'
            })
        
        # Detect session_state dictionary access
        if (isinstance(node.value, ast.Attribute) and
            isinstance(node.value.value, ast.Name) and
            node.value.value.id == 'st' and
            node.value.attr == 'session_state'):
            self.session_violations.append({
                'file': self.current_file,
                'line': node.lineno,
                'context': 'st.session_state dictionary access'
            })
        
        self.generic_visit(node)
    
    def visit_Subscript(self, node):
        # Detect st.session_state["key"] patterns
        if (isinstance(node.value, ast.Attribute) and
            isinstance(node.value.value, ast.Name) and
            node.value.value.id == 'st' and
            node.value.attr == 'session_state'):
            self.session_violations.append({
                'file': self.current_file,
                'line': node.lineno,
                'context': 'st.session_state subscript access'
            })
        self.generic_visit(node)
    
    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append({
                'file': self.current_file,
                'line': node.lineno,
                'module': alias.name,
                'type': 'import'
            })
        self.generic_visit(node)
    
# TODO: Consider extracting this block into a separate method
    
# TODO: Consider extracting this block into a separate method
    
    def visit_ImportFrom(self, node):
        if node.module:
            for alias in node.names:
                self.imports.append({
                    'file': self.current_file,
                    'line': node.lineno,
                    'module': node.module,
                    'name': alias.name,
                    'type': 'from_import'
                })
        self.generic_visit(node)


# TODO: Consider extracting this block into a separate method
# TODO: Consider extracting this block into a separate method
def analyze_file(file_path: Path, analyzer: FinalValidationAnalyzer) -> bool:
    """Analyze a single Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=str(file_path))
        analyzer.current_file = str(file_path)
        analyzer.visit(tree)
        return True
        
    except SyntaxError as e:
        print(f"❌ Syntax error in {file_path}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error analyzing {file_path}: {e}")
        return False


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


# TODO: Consider extracting this block into a separate method

# TODO: Consider extracting this block into a separate method

def run_final_validation():
    """Run comprehensive validation of refactoring."""
    
    print("🔍 FINAL VALIDATION - Phase 4 Refactoring")
    print("=" * 60)
    
    # Target directory
    streamlit_dir = Path("streamlit_extension")
    if not streamlit_dir.exists():
        print(f"❌ Directory not found: {streamlit_dir}")
        return False
    
    # Initialize analyzer
    analyzer = FinalValidationAnalyzer()
    
    # Find all Python files
    python_files = list(streamlit_dir.rglob("*.py"))
    print(f"📁 Analyzing {len(python_files)} Python files...")
    
    # Analyze each file
    successful_files = 0
    for file_path in python_files:
        if analyze_file(file_path, analyzer):
            successful_files += 1
    
    print(f"✅ Successfully analyzed {successful_files}/{len(python_files)} files")
    print()
    
    # === VALIDATION 1: Function Duplications ===
    print("🔍 VALIDATION 1: Function Duplications")
    print("-" * 40)
    
    duplicated_functions = {
        name: locations for name, locations in analyzer.functions.items()
        if len(locations) > 1
    }
    
    if duplicated_functions:
        print(f"❌ Found {len(duplicated_functions)} duplicated functions:")
        for func_name, locations in duplicated_functions.items():
            print(f"   - {func_name}:")
            for loc in locations:
                print(f"     * {loc['file']}:{loc['line']} ({loc.get('args', 0)} args)")
    else:
        print("✅ No function duplications found!")
    
    print()
    
    # === VALIDATION 2: Session State Violations ===
    print("🔍 VALIDATION 2: Session State Violations")
    print("-" * 40)
    
    if analyzer.session_violations:
        print(f"❌ Found {len(analyzer.session_violations)} session state violations:")
        for violation in analyzer.session_violations:
            print(f"   - {violation['file']}:{violation['line']} - {violation['context']}")
    else:
        print("✅ No session state violations found!")
    
    print()
    
    # === VALIDATION 3: File Size Compliance ===
    print("🔍 VALIDATION 3: File Size Compliance")
    print("-" * 40)
    
    large_files = []
    for file_path in python_files:
        metrics = get_file_metrics(file_path)
        if 'error' not in metrics and metrics['total_lines'] > 400:
            large_files.append({
                'file': str(file_path),
                'lines': metrics['total_lines']
            })
    
    if large_files:
        print(f"⚠️ Found {len(large_files)} files over 400 lines:")
        for file_info in large_files:
            print(f"   - {file_info['file']}: {file_info['lines']} lines")
    else:
        print("✅ All files are under 400 lines!")
    
    print()
    
    # === VALIDATION 4: Import Integrity Check ===
    print("🔍 VALIDATION 4: Import Integrity Check")
    print("-" * 40)
    
    # Check for circular imports and missing modules
    modules_imported = Counter()
    for imp in analyzer.imports:
        modules_imported[imp['module']] += 1
    
    print(f"📦 Found {len(modules_imported)} unique modules imported")
    
    # Check specific refactored modules
    critical_imports = [
        'streamlit_extension.utils.ui_operations',
        'streamlit_extension.utils.cache_utils', 
        'streamlit_extension.utils.data_utils',
        'streamlit_extension.utils.path_utils'
    ]
    
    missing_imports = []
    for critical in critical_imports:
        if critical not in modules_imported:
            missing_imports.append(critical)
    
    if missing_imports:
        print(f"⚠️ Critical imports not found: {missing_imports}")
    else:
        print("✅ All critical imports are present!")
    
    print()
    
    # === VALIDATION 5: Specific File Analysis ===
    print("🔍 VALIDATION 5: Key File Analysis")
    print("-" * 40)
    
    key_files = {
        'streamlit_extension/streamlit_app.py': 'Main app file',
        'streamlit_extension/utils/streamlit_helpers.py': 'Refactored facade',
        'streamlit_extension/utils/ui_operations.py': 'UI operations module',
        'streamlit_extension/utils/cache_utils.py': 'Cache utilities',
        'streamlit_extension/utils/data_utils.py': 'Data normalization',
        'streamlit_extension/utils/path_utils.py': 'Path utilities',
        'streamlit_extension/utils/session_manager.py': 'Session management',
    }
    
    for file_path, description in key_files.items():
        full_path = Path(file_path)
        if full_path.exists():
            metrics = get_file_metrics(full_path)
            if 'error' not in metrics:
                print(f"   ✅ {description}: {metrics['total_lines']} lines")
            else:
                print(f"   ❌ {description}: Error - {metrics['error']}")
        else:
            print(f"   ⚠️ {description}: File not found")
    
    print()
    
    # === FINAL SCORE ===
    print("🏆 FINAL VALIDATION SCORE")
    print("=" * 40)
    
    score = 0
    max_score = 4
    
    # Duplication check (25 points)
    if not duplicated_functions:
        score += 1
        print("✅ Function Duplications: PASS (25%)")
    else:
        print(f"❌ Function Duplications: FAIL - {len(duplicated_functions)} duplicates")
    
    # Session state check (25 points)  
    if not analyzer.session_violations:
        score += 1
        print("✅ Session State Violations: PASS (25%)")
    else:
        print(f"❌ Session State Violations: FAIL - {len(analyzer.session_violations)} violations")
    
    # File size check (25 points)
    if not large_files:
        score += 1
        print("✅ File Size Compliance: PASS (25%)")
    else:
        print(f"❌ File Size Compliance: FAIL - {len(large_files)} oversized files")
    
    # Import integrity check (25 points)
    if not missing_imports:
        score += 1
        print("✅ Import Integrity: PASS (25%)")
    else:
        print(f"❌ Import Integrity: FAIL - {len(missing_imports)} missing imports")
    
    print()
    final_percentage = (score / max_score) * 100
    print(f"📊 FINAL SCORE: {score}/{max_score} ({final_percentage:.1f}%)")
    
    if final_percentage >= 90:
        print("🎉 EXCELLENT! Refactoring completed successfully!")
    elif final_percentage >= 75:
        print("✅ GOOD! Minor issues remain to be addressed.")
    elif final_percentage >= 50:
        print("⚠️ NEEDS WORK! Several issues need attention.")
    else:
        print("❌ CRITICAL! Major issues need to be resolved.")
    
    return final_percentage >= 75


if __name__ == "__main__":
    success = run_final_validation()
    sys.exit(0 if success else 1)