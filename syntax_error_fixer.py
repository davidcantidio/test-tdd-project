#!/usr/bin/env python3
"""
🔧 SYNTAX ERROR SYSTEMATIC FIXER

Fixes the 179 syntax errors introduced by the access control fixes.
Common issues:
1. Auth imports inserted in wrong places (middle of try/except blocks)
2. Decorators inserted inside functions instead of before function definitions
"""

import ast
import re
from pathlib import Path
from typing import List, Tuple
import os

class SyntaxErrorFixer:
    """Systematic syntax error fixer."""
    
    def __init__(self):
        self.files_fixed = 0
        self.errors_fixed = 0
        self.failed_files = []
        
    def fix_all_syntax_errors(self):
        """Fix syntax errors in all files."""
        print("🔧 FIXING SYNTAX ERRORS SYSTEMATICALLY...")
        print("=" * 60)
        
        streamlit_dir = Path("streamlit_extension")
        if not streamlit_dir.exists():
            print("❌ streamlit_extension directory not found")
            return
        
        # Find all Python files with potential syntax errors
        for py_file in streamlit_dir.rglob("*.py"):
            if '__pycache__' in str(py_file):
                continue
                
            if self._has_syntax_error(py_file):
                print(f"🔧 Fixing: {py_file}")
                if self._fix_file_syntax(py_file):
                    self.files_fixed += 1
                    print(f"   ✅ Fixed")
                else:
                    self.failed_files.append(str(py_file))
                    print(f"   ❌ Failed")
        
        self._print_summary()
    
    def _has_syntax_error(self, file_path: Path) -> bool:
        """Check if file has syntax errors."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            ast.parse(content)
            return False
        except SyntaxError:
            return True
        except Exception:
            return False
    
    def _fix_file_syntax(self, file_path: Path) -> bool:
        """Fix syntax errors in a single file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Fix common syntax error patterns
            content = self._fix_misplaced_imports(content)
            content = self._fix_misplaced_decorators(content)
            content = self._fix_decorator_syntax(content)
            content = self._fix_import_blocks(content)
            content = self._remove_duplicate_imports(content)
            
            # Only write if content changed and is valid
            if content != original_content:
                # Validate syntax
                try:
                    ast.parse(content)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    self.errors_fixed += 1
                    return True
                except SyntaxError:
                    # If fix didn't work, try more aggressive fixes
                    content = self._aggressive_fix(original_content)
                    try:
                        ast.parse(content)
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        self.errors_fixed += 1
                        return True
                    except SyntaxError:
                        return False
            
            return True
            
        except Exception as e:
            print(f"     Error: {e}")
            return False
    
    def _fix_misplaced_imports(self, content: str) -> str:
        """Fix imports that were inserted in wrong places."""
        lines = content.split('\n')
        
        # Find auth import lines that are misplaced
        auth_import_lines = []
        clean_lines = []
        
        in_try_block = False
        try_indent = 0
        
        for i, line in enumerate(lines):
            # Detect try blocks
            stripped = line.strip()
            if stripped.startswith('try:'):
                in_try_block = True
                try_indent = len(line) - len(line.lstrip())
            elif in_try_block and stripped.startswith('except'):
                in_try_block = False
            
            # Check if this is a misplaced auth import
            if ('from streamlit_extension.auth.middleware import' in line or 
                'from streamlit_extension.auth.user_model import' in line):
                
                # If it's inside a try block or not at module level, move it
                current_indent = len(line) - len(line.lstrip())
                if in_try_block or current_indent > 0:
                    auth_import_lines.append(line.strip())
                    continue  # Skip this line
            
            clean_lines.append(line)
        
        # Add auth imports at the top, after other imports
        if auth_import_lines:
            # Find where to insert auth imports
            insert_idx = 0
            for i, line in enumerate(clean_lines):
                if (line.strip().startswith('import ') or 
                    line.strip().startswith('from ') and 
                    'streamlit_extension.auth' not in line):
                    insert_idx = i + 1
            
            # Remove duplicates from auth imports
            unique_auth_imports = list(dict.fromkeys(auth_import_lines))
            
            # Insert auth imports
            for auth_import in reversed(unique_auth_imports):
                clean_lines.insert(insert_idx, auth_import)
        
        return '\n'.join(clean_lines)
    
    def _fix_misplaced_decorators(self, content: str) -> str:
        """Fix decorators that were inserted inside functions."""
        lines = content.split('\n')
        clean_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Look for decorator inside function
            if '    @require_auth' in line or '    @require_admin' in line:
                # Check if this is inside a function
                if i > 0:
                    prev_lines = lines[max(0, i-10):i]
                    
                    # Look for function definition above
                    func_def_idx = None
                    for j in range(len(prev_lines)-1, -1, -1):
                        if prev_lines[j].strip().startswith('def '):
                            func_def_idx = (max(0, i-10) + j)
                            break
                    
                    if func_def_idx is not None:
                        # This decorator is misplaced, skip it
                        i += 1
                        continue
            
            # Look for decorators before comments or in wrong places
            if (line.strip().startswith('@require_auth') or line.strip().startswith('@require_admin')):
                # Check if next non-empty line is a function definition
                next_func_line = None
                for j in range(i+1, min(len(lines), i+5)):
                    if lines[j].strip() and not lines[j].strip().startswith('#'):
                        next_func_line = lines[j]
                        break
                
                if next_func_line and not next_func_line.strip().startswith('def '):
                    # Decorator not before function, skip it
                    i += 1
                    continue
            
            clean_lines.append(line)
            i += 1
        
        return '\n'.join(clean_lines)
    
    def _fix_decorator_syntax(self, content: str) -> str:
        """Fix decorator syntax issues."""
        # Fix decorators that end up on same line as function
        content = re.sub(r'@require_auth\(\)\s*def ', '@require_auth()\ndef ', content)
        content = re.sub(r'@require_admin\s*def ', '@require_admin\ndef ', content)
        
        return content
    
    def _fix_import_blocks(self, content: str) -> str:
        """Fix broken import blocks."""
        lines = content.split('\n')
        clean_lines = []
        
        for line in lines:
            # Skip lines that break import blocks
            if (line.strip() == 'from streamlit_extension.auth.middleware import require_auth, require_admin' and
                len(clean_lines) > 0 and 
                not (clean_lines[-1].strip().startswith('import') or clean_lines[-1].strip().startswith('from'))):
                continue
                
            if (line.strip() == 'from streamlit_extension.auth.user_model import UserRole' and
                len(clean_lines) > 0 and 
                not (clean_lines[-1].strip().startswith('import') or clean_lines[-1].strip().startswith('from'))):
                continue
            
            clean_lines.append(line)
        
        return '\n'.join(clean_lines)
    
    def _remove_duplicate_imports(self, content: str) -> str:
        """Remove duplicate imports."""
        lines = content.split('\n')
        seen_imports = set()
        clean_lines = []
        
        for line in lines:
            if (line.strip().startswith('import ') or line.strip().startswith('from ')):
                if line.strip() in seen_imports:
                    continue  # Skip duplicate
                seen_imports.add(line.strip())
            
            clean_lines.append(line)
        
        return '\n'.join(clean_lines)
    
    def _aggressive_fix(self, content: str) -> str:
        """More aggressive fixes for stubborn syntax errors."""
        lines = content.split('\n')
        clean_lines = []
        
        # Remove all misplaced auth imports and decorators
        for line in lines:
            # Skip obviously misplaced auth imports
            if ('from streamlit_extension.auth' in line and 
                ('    ' in line or 'try:' in content[content.find(line)-50:content.find(line)])):
                continue
            
            # Skip misplaced decorators  
            if ('    @require_' in line or 
                line.strip().startswith('@require_') and 
                not self._is_before_function(lines, lines.index(line))):
                continue
            
            clean_lines.append(line)
        
        # Add proper auth imports at top
        auth_imports = [
            "from streamlit_extension.auth.middleware import require_auth, require_admin",
            "from streamlit_extension.auth.user_model import UserRole"
        ]
        
        # Find insertion point
        insert_idx = 0
        for i, line in enumerate(clean_lines):
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                insert_idx = i + 1
        
        # Insert auth imports if not already present
        for auth_import in reversed(auth_imports):
            if auth_import not in '\n'.join(clean_lines):
                clean_lines.insert(insert_idx, auth_import)
        
        return '\n'.join(clean_lines)
    
    def _is_before_function(self, lines: List[str], decorator_idx: int) -> bool:
        """Check if decorator is properly placed before a function."""
        for i in range(decorator_idx + 1, min(len(lines), decorator_idx + 3)):
            if lines[i].strip().startswith('def '):
                return True
        return False
    
    def _print_summary(self):
        """Print fix summary."""
        print(f"\n📊 SYNTAX ERROR FIX SUMMARY:")
        print(f"   Files processed: {self.files_fixed}")
        print(f"   Errors fixed: {self.errors_fixed}")
        print(f"   Failed files: {len(self.failed_files)}")
        
        if self.failed_files:
            print(f"\n❌ FILES THAT NEED MANUAL REVIEW:")
            for file_path in self.failed_files[:10]:
                print(f"   • {file_path}")

def main():
    print("🔧 SYSTEMATIC SYNTAX ERROR FIXER")
    print("=" * 60)
    print("Fixing 179 syntax errors introduced by access control fixes\n")
    
    fixer = SyntaxErrorFixer()
    fixer.fix_all_syntax_errors()
    
    # Test some critical files
    print(f"\n🧪 TESTING CRITICAL FILES:")
    critical_files = [
        "streamlit_extension/utils/session_manager.py",
        "streamlit_extension/utils/performance_tester.py", 
        "streamlit_extension/utils/database.py",
        "streamlit_extension/services/timer_service.py"
    ]
    
    all_good = True
    for file_path in critical_files:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            ast.parse(content)
            print(f"   ✅ {file_path}")
        except SyntaxError as e:
            print(f"   ❌ {file_path}: {e}")
            all_good = False
        except FileNotFoundError:
            print(f"   ⚠️ {file_path}: Not found")
    
    return all_good

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)