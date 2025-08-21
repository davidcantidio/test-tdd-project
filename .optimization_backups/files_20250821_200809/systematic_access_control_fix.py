#!/usr/bin/env python3
"""
🛡️ SYSTEMATIC ACCESS CONTROL FIXES - Security First Approach

Addresses the 43 critical access control gaps identified in the semantic audit.
This script systematically adds authentication protection to sensitive functions.

CRITICAL SECURITY FIXES:
- Database configuration functions
- CRUD operations (Create, Update, Delete)
- Administrative functions
- Configuration management
- Session management
"""

import ast
import re
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
import time

@dataclass
class AccessControlFix:
    """Represents an access control fix to be applied."""
    file_path: str
    function_name: str
    line_number: int
    current_protection: str
    required_protection: str
    fix_type: str  # DECORATOR, MIDDLEWARE, INLINE_CHECK
    risk_level: str  # CRITICAL, HIGH, MEDIUM
    fix_code: str

class SystematicAccessControlFixer:
    """Systematic fixer for access control vulnerabilities."""
    
    def __init__(self):
        self.fixes_needed: List[AccessControlFix] = []
        self.fixes_applied: List[AccessControlFix] = []
        self.sensitive_patterns = {
            'create': ['create_', '_create', 'add_', '_add', 'insert_', '_insert'],
            'update': ['update_', '_update', 'edit_', '_edit', 'modify_', '_modify'],
            'delete': ['delete_', '_delete', 'remove_', '_remove', 'drop_', '_drop'],
            'admin': ['admin_', '_admin', 'config_', '_config', 'setup_', '_setup'],
            'database': ['configure_', '_configure', 'connect_', '_connect', 'init_db', '_init_db']
        }
        
    # TODO: Consider extracting this block into a separate method
    # TODO: Consider extracting this block into a separate method
    def scan_access_control_gaps(self):
        """Scan the entire codebase for access control gaps."""
        print("🔍 SCANNING FOR ACCESS CONTROL GAPS...")
        print("=" * 60)
        
        streamlit_dir = Path("streamlit_extension")
        if not streamlit_dir.exists():
            print("❌ streamlit_extension directory not found")
            return
        
        # Scan all Python files
        for py_file in streamlit_dir.rglob("*.py"):
            if '__pycache__' in str(py_file):
                continue
                
            self._analyze_file_for_gaps(py_file)
        
        # Sort by risk level
        self.fixes_needed.sort(key=lambda x: {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2}[x.risk_level])
        
        print(f"\n📊 ACCESS CONTROL SCAN RESULTS:")
        print(f"  Total gaps found: {len(self.fixes_needed)}")
        
        risk_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0}
        for fix in self.fixes_needed:
            risk_counts[fix.risk_level] += 1
            
        for risk, count in risk_counts.items():
            print(f"  {risk}: {count} issues")
    
    def _analyze_file_for_gaps(self, file_path: Path):
        """Analyze a single file for access control gaps."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(file_path))
            
            class AccessControlAnalyzer(ast.NodeVisitor):
                def __init__(self, fixer, file_path, content):
                    self.fixer = fixer
                    self.file_path = str(file_path)
                    self.content = content
                    self.content_lines = content.split('\n')
                    
                def visit_FunctionDef(self, node):
                    self._check_function_protection(node)
                    self.generic_visit(node)
                    
                def _check_function_protection(self, node):
                    func_name = node.name
                    line_number = node.lineno
                    
                    # Check if function is sensitive
                    if self._is_sensitive_function(func_name):
                        # Check current protection level
                        protection_level = self._get_current_protection(node, func_name)
                        
                        if protection_level == 'NONE':
                            # Determine required protection and risk level
                            required_protection, risk_level = self._determine_required_protection(func_name)
                            
                            # Generate fix code
                            fix_code = self._generate_fix_code(func_name, required_protection)
                            
                            fix = AccessControlFix(
                                file_path=self.file_path,
                                function_name=func_name,
                                line_number=line_number,
                                current_protection='NONE',
                                required_protection=required_protection,
                                fix_type='DECORATOR',
                                risk_level=risk_level,
                                fix_code=fix_code
                            )
                            
                            self.fixer.fixes_needed.append(fix)
                
                def _is_sensitive_function(self, func_name):
                    """Check if function is sensitive based on naming patterns."""
                    func_lower = func_name.lower()
                    
                    for category, patterns in self.fixer.sensitive_patterns.items():
                        for pattern in patterns:
                            if pattern in func_lower:
                                return True
                    
                    return False
                
                def _get_current_protection(self, node, func_name):
                    """Check what protection is already in place."""
                    # Check for decorators
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Name):
                            if 'auth' in decorator.id.lower() or 'require' in decorator.id.lower():
                                return 'DECORATOR'
                        elif isinstance(decorator, ast.Call):
                            if hasattr(decorator.func, 'id'):
                                if 'auth' in decorator.func.id.lower() or 'require' in decorator.func.id.lower():
                                    return 'DECORATOR'
                    
                    # Check for inline authentication checks in function body
                    func_start_line = node.lineno - 1
                    func_lines = []
                    
                    for i, line in enumerate(self.content_lines[func_start_line:func_start_line + 20]):
                        if line.strip():
                            func_lines.append(line.lower())
                    
                    auth_patterns = ['get_current_user', 'check_auth', 'require_auth', 'authenticate', 'is_authenticated']
                    for line in func_lines:
                        if any(pattern in line for pattern in auth_patterns):
                            return 'INLINE'
                    
                    return 'NONE'
                
                def _determine_required_protection(self, func_name):
                    """Determine the required protection level and risk."""
                    func_lower = func_name.lower()
                    
                    # Critical functions (database config, admin operations)
                    if any(pattern in func_lower for pattern in ['configure', 'admin', 'setup', 'init_db', 'connect']):
                        return '@require_admin', 'CRITICAL'
                    
                    # High risk functions (delete operations)
                    elif any(pattern in func_lower for pattern in ['delete', 'remove', 'drop']):
                        return '@require_auth([UserRole.ADMIN, UserRole.MANAGER])', 'HIGH'
                    
                    # Medium risk functions (create, update)
                    elif any(pattern in func_lower for pattern in ['create', 'update', 'edit', 'modify', 'add', 'insert']):
                        return '@require_auth()', 'MEDIUM'
                    
                    return '@require_auth()', 'MEDIUM'
                
                def _generate_fix_code(self, func_name, required_protection):
                    """Generate the fix code to add protection."""
                    return f"""
# ACCESS CONTROL FIX: Add authentication protection
{required_protection}
def {func_name}("""
            
            analyzer = AccessControlAnalyzer(self, file_path, content)
            analyzer.visit(tree)
            
        except Exception as e:
            print(f"⚠️ Error analyzing {file_path}: {e}")
    
# TODO: Consider extracting this block into a separate method
    
# TODO: Consider extracting this block into a separate method
    
    def apply_systematic_fixes(self):
        """Apply access control fixes systematically."""
        print(f"\n🛡️ APPLYING ACCESS CONTROL FIXES...")
        print("=" * 60)
        
        # Group fixes by file for efficient processing
        fixes_by_file = {}
        for fix in self.fixes_needed:
            if fix.file_path not in fixes_by_file:
                fixes_by_file[fix.file_path] = []
            fixes_by_file[fix.file_path].append(fix)
        
        # Apply fixes file by file
        for file_path, fixes in fixes_by_file.items():
            print(f"\n📄 Processing: {file_path}")
            print(f"   Fixes needed: {len(fixes)}")
            
            success_count = self._apply_fixes_to_file(file_path, fixes)
            print(f"   Fixes applied: {success_count}/{len(fixes)}")
        
        print(f"\n✅ ACCESS CONTROL FIXES SUMMARY:")
        print(f"   Total fixes applied: {len(self.fixes_applied)}")
        # TODO: Consider extracting this block into a separate method
        # TODO: Consider extracting this block into a separate method
        print(f"   Total fixes needed: {len(self.fixes_needed)}")
        print(f"   Success rate: {len(self.fixes_applied)/len(self.fixes_needed)*100:.1f}%")
    
    def _apply_fixes_to_file(self, file_path: str, fixes: List[AccessControlFix]) -> int:
        """Apply fixes to a single file."""
        try:
            # Read current file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            # Check if auth imports are present
            self._ensure_auth_imports(lines, file_path)
            
            # Apply fixes from bottom to top (to preserve line numbers)
            fixes_sorted = sorted(fixes, key=lambda x: x.line_number, reverse=True)
            applied_count = 0
            
            for fix in fixes_sorted:
                if self._apply_single_fix(lines, fix):
                    self.fixes_applied.append(fix)
                    applied_count += 1
                    print(f"     ✅ Applied: {fix.function_name} ({fix.risk_level})")
                else:
                    print(f"     ❌ Failed: {fix.function_name}")
            
            # Write modified content back
            if applied_count > 0:
                modified_content = '\n'.join(lines)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
            
            return applied_count
            
        # TODO: Consider extracting this block into a separate method
        # TODO: Consider extracting this block into a separate method
        except Exception as e:
            print(f"     ❌ Error processing file: {e}")
            return 0
    
    def _ensure_auth_imports(self, lines: List[str], file_path: str):
        """Ensure necessary auth imports are present."""
        # Check if auth imports already exist
        has_require_auth = any('require_auth' in line for line in lines[:50])
        has_user_role = any('UserRole' in line for line in lines[:50])
        
        if has_require_auth and has_user_role:
            return
        
        # Find import section
        import_line_idx = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('from ') or line.strip().startswith('import '):
                import_line_idx = i
        
        # Add auth imports if needed
        new_imports = []
        if not has_require_auth:
            new_imports.append("from streamlit_extension.auth.middleware import require_auth, require_admin")
        if not has_user_role:
            new_imports.append("from streamlit_extension.auth.user_model import UserRole")
        
# TODO: Consider extracting this block into a separate method
        
# TODO: Consider extracting this block into a separate method
        
        # Insert imports
        for i, import_line in enumerate(reversed(new_imports)):
            lines.insert(import_line_idx + 1, import_line)
    
    def _apply_single_fix(self, lines: List[str], fix: AccessControlFix) -> bool:
        """Apply a single access control fix."""
        try:
            # Find the function definition line
            func_line_idx = fix.line_number - 1
            
            if func_line_idx >= len(lines):
                return False
            
            # Extract the decorator from required protection
            decorator = fix.required_protection
            
            # Find the correct indentation
            func_line = lines[func_line_idx]
            indent = len(func_line) - len(func_line.lstrip())
            decorator_indent = ' ' * indent
            
            # Insert decorator before function
            lines.insert(func_line_idx, decorator_indent + decorator)
            
# TODO: Consider extracting this block into a separate method
            
# TODO: Consider extracting this block into a separate method
            
            return True
            
        except Exception as e:
            print(f"       Error applying fix: {e}")
            return False
    
    def validate_fixes(self):
        """Validate that the fixes were applied correctly."""
        print(f"\n🔍 VALIDATING ACCESS CONTROL FIXES...")
        print("=" * 60)
        
        validation_errors = []
        
        for fix in self.fixes_applied:
            try:
                with open(fix.file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check if decorator was added
                if '@require_auth' not in content and '@require_admin' not in content:
                    validation_errors.append(f"Missing decorator in {fix.file_path}:{fix.function_name}")
                
                # Check syntax
                try:
                    ast.parse(content)
                except SyntaxError as e:
                    validation_errors.append(f"Syntax error in {fix.file_path}: {e}")
                    
            except Exception as e:
                validation_errors.append(f"Validation error for {fix.file_path}: {e}")
        
        # TODO: Consider extracting this block into a separate method
        # TODO: Consider extracting this block into a separate method
        if validation_errors:
            print(f"❌ VALIDATION ERRORS ({len(validation_errors)}):")
            for error in validation_errors[:10]:  # Show first 10 errors
                print(f"   • {error}")
        else:
            print("✅ ALL FIXES VALIDATED SUCCESSFULLY")
        
        return len(validation_errors) == 0
    
    def generate_fix_report(self):
        """Generate comprehensive fix report."""
        print(f"\n📊 ACCESS CONTROL FIX REPORT")
        print("=" * 60)
        
        # Summary by risk level
        risk_summary = {'CRITICAL': [], 'HIGH': [], 'MEDIUM': []}
        for fix in self.fixes_applied:
            risk_summary[fix.risk_level].append(fix)
        
        print(f"\n🎯 FIXES BY RISK LEVEL:")
        for risk, fixes in risk_summary.items():
            print(f"  {risk}: {len(fixes)} fixes applied")
            for fix in fixes[:3]:  # Show first 3 for each risk level
                print(f"    • {fix.function_name} ({fix.file_path})")
        
        # Files modified
        modified_files = set(fix.file_path for fix in self.fixes_applied)
        print(f"\n📁 FILES MODIFIED ({len(modified_files)}):")
        for file_path in sorted(modified_files):
            file_fixes = [f for f in self.fixes_applied if f.file_path == file_path]
            print(f"  • {file_path} ({len(file_fixes)} fixes)")
        
        # Remaining vulnerabilities
        remaining = len(self.fixes_needed) - len(self.fixes_applied)
        if remaining > 0:
            print(f"\n⚠️ REMAINING VULNERABILITIES: {remaining}")
            print("   These require manual review:")
            for fix in self.fixes_needed:
                if fix not in self.fixes_applied:
                    print(f"     • {fix.function_name} ({fix.file_path})")
        else:
            print(f"\n✅ ALL ACCESS CONTROL GAPS ADDRESSED")
        
        return {
            'total_fixes_applied': len(self.fixes_applied),
            'total_fixes_needed': len(self.fixes_needed),
            'success_rate': len(self.fixes_applied)/len(self.fixes_needed)*100 if self.fixes_needed else 100,
            'files_modified': len(modified_files),
            'remaining_vulnerabilities': remaining,
            'risk_breakdown': {risk: len(fixes) for risk, fixes in risk_summary.items()}
        }

# TODO: Consider extracting this block into a separate method
# TODO: Consider extracting this block into a separate method
def main():
    print("🛡️ SYSTEMATIC ACCESS CONTROL SECURITY FIXES")
    print("=" * 70)
    print("Addressing 43 critical access control gaps from semantic audit\n")
    
    fixer = SystematicAccessControlFixer()
    
    # Step 1: Scan for gaps
    fixer.scan_access_control_gaps()
    
    if not fixer.fixes_needed:
        print("✅ No access control gaps found!")
        return True
    
    # Step 2: Apply fixes
    fixer.apply_systematic_fixes()
    
    # Step 3: Validate fixes
    validation_success = fixer.validate_fixes()
    
    # Step 4: Generate report
    report = fixer.generate_fix_report()
    
    # Determine overall success
    success_rate = report['success_rate']
    remaining = report['remaining_vulnerabilities']
    
    print(f"\n🎯 OVERALL RESULT:")
    if success_rate >= 90 and remaining <= 5:
        print("✅ ACCESS CONTROL FIXES SUCCESSFUL")
        print(f"   Success rate: {success_rate:.1f}%")
        print(f"   Remaining issues: {remaining}")
        return True
    else:
        print("⚠️ ACCESS CONTROL FIXES PARTIAL")
        print(f"   Success rate: {success_rate:.1f}%")
        print(f"   Remaining issues: {remaining}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)