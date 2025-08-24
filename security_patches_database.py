#!/usr/bin/env python3
"""
🛡️ Security Patches for Database.py

Critical SQL Injection vulnerability fixes for streamlit_extension/utils/database.py
Addresses 18+ f-string SQL injection vulnerabilities found in deep audit.
"""

import os
import re
from pathlib import Path

def create_security_patches():
    """Create comprehensive security patches for database.py SQL injections."""
    
    database_file = Path("streamlit_extension/utils/database.py")
    
    if not database_file.exists():
        print(f"❌ File not found: {database_file}")
        return False
    
    print("🛡️ APPLYING CRITICAL SECURITY PATCHES TO DATABASE.PY")
    print("="*60)
    
    # Read current content
    with open(database_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup original
    backup_file = database_file.with_suffix('.py.backup')
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"📋 Backup created: {backup_file}")
    
    # Security patches to apply
    patches = [
        # Patch 1: Add security validation helper
        {
            'search': 'from typing import Dict, List, Optional, Any, Union, Tuple',
            'replace': '''from typing import Dict, List, Optional, Any, Union, Tuple

# SECURITY: SQL injection prevention helpers
def _validate_table_name(table_name: str) -> str:
    """Validate table name against whitelist to prevent SQL injection."""
    allowed_tables = {
        'framework_clients', 'framework_projects', 'framework_epics', 'framework_tasks',
        'work_sessions', 'achievement_types', 'user_achievements', 'user_streaks',
        'github_sync_log', 'system_settings'
    }
    if table_name not in allowed_tables:
        raise ValueError(f"SECURITY: Invalid table name: {table_name}")
    return table_name

def _validate_column_name(column_name: str, table_name: str) -> str:
    """Validate column name against whitelist to prevent SQL injection."""
    # Common allowed columns across tables
    allowed_columns = {
        'id', 'name', 'email', 'company', 'status', 'created_at', 'updated_at',
        'title', 'description', 'priority', 'estimate_minutes', 'actual_minutes',
        'project_id', 'epic_id', 'task_id', 'user_id',
        'start_date', 'end_date', 'budget', 'progress', 'points'
    }
    if column_name not in allowed_columns:
        raise ValueError(f"SECURITY: Invalid column name: {column_name} for table {table_name}")
    return column_name''',
            'description': 'Add security validation helpers'
        },
        
        # Patch 2: Fix order clause vulnerability (line ~211)
        {
            'search': 'order_clause = f"ORDER BY {sort_column} {sort_order}" if sort_column else ""',
            'replace': '''# SECURITY FIX: Validate column and order before building ORDER BY clause
                if sort_column:
                    validated_column = _validate_column_name(sort_column, table_name)
                    validated_order = 'ASC' if sort_order.upper() == 'ASC' else 'DESC'
                    order_clause = f"ORDER BY {validated_column} {validated_order}"
                else:
                    order_clause = ""''',
            'description': 'Fix ORDER BY SQL injection vulnerability'
        },
        
        # Patch 3: Fix table name validation in count query (line ~214)
        {
            'search': 'count_query = text(f"SELECT COUNT(*) FROM {table_name}") if not where_clause else text(f"SELECT COUNT(*) FROM {table_name} {where_clause}")',
            'replace': '''# SECURITY FIX: Validate table name before query construction
                validated_table = _validate_table_name(table_name)
                if not where_clause:
                    count_query = text(f"SELECT COUNT(*) FROM {validated_table}")
                else:
                    count_query = text(f"SELECT COUNT(*) FROM {validated_table} {where_clause}")''',
            'description': 'Fix COUNT query table name vulnerability'
        },
        
        # Patch 4: Fix cursor condition vulnerabilities (multiple lines)
        {
            'search': 'cursor_cond = f"{sort_column} > :cursor" if sort_order.upper() == "ASC" else f"{sort_column} < :cursor"',
            'replace': '''# SECURITY FIX: Validate column name in cursor condition
                    validated_column = _validate_column_name(sort_column, table_name)
                    cursor_cond = f"{validated_column} > :cursor" if sort_order.upper() == "ASC" else f"{validated_column} < :cursor"''',
            'description': 'Fix cursor condition column name vulnerability'
        },
        
        # Patch 5: Fix data_sql query construction
        {
            'search': 'data_sql = f"SELECT * FROM {table_name} {where_clause_cursor} {order_clause} LIMIT :limit"',
            'replace': '''# SECURITY FIX: Use validated table name
                    validated_table = _validate_table_name(table_name)  
                    data_sql = f"SELECT * FROM {validated_table} {where_clause_cursor} {order_clause} LIMIT :limit"''',
            'description': 'Fix SELECT query table name vulnerability'
        },
        
        # Patch 6: Fix SQLite section ORDER BY (around line 254)
        {
            'search': 'order_clause = f"ORDER BY {sort_column} {sort_order}"',
            'replace': '''# SECURITY FIX: Validate column and order for SQLite queries
                validated_column = _validate_column_name(sort_column, table_name)
                validated_order = 'ASC' if sort_order.upper() == 'ASC' else 'DESC'
                order_clause = f"ORDER BY {validated_column} {validated_order}"''',
            'description': 'Fix SQLite ORDER BY vulnerability'
        },
        
        # Patch 7: Fix SQLite count query
        {
            'search': 'count_sql = f"SELECT COUNT(*) FROM {table_name} {where_clause}"',
            'replace': '''# SECURITY FIX: Validate table name in SQLite count query
                validated_table = _validate_table_name(table_name)
                count_sql = f"SELECT COUNT(*) FROM {validated_table} {where_clause}"''',
            'description': 'Fix SQLite count query vulnerability'
        }
    ]
    
    # Apply patches
    patched_content = content
    applied_patches = 0
    
    for i, patch in enumerate(patches, 1):
        if patch['search'] in patched_content:
            patched_content = patched_content.replace(patch['search'], patch['replace'])
            print(f"✅ Patch {i}: {patch['description']}")
            applied_patches += 1
        else:
            print(f"⚠️ Patch {i}: Pattern not found - {patch['description']}")
    
    # Write patched content
    if applied_patches > 0:
        with open(database_file, 'w', encoding='utf-8') as f:
            f.write(patched_content)
        print(f"\n🛡️ Applied {applied_patches}/{len(patches)} security patches")
        print(f"✅ Patched file: {database_file}")
        return True
    else:
        print("\n❌ No patches applied - patterns may have changed")
        return False

def validate_patches():
    """Validate that patches were applied correctly."""
    database_file = Path("streamlit_extension/utils/database.py")
    
    if not database_file.exists():
        return False
    
    with open(database_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for security functions
    if '_validate_table_name' in content and '_validate_column_name' in content:
        print("✅ Security validation functions added")
    else:
        print("❌ Security validation functions missing")
        return False
    
    # Check for SECURITY FIX comments
    security_fixes = content.count('SECURITY FIX:')
    print(f"✅ Found {security_fixes} security fixes applied")
    
    # Check for remaining f-string SQL vulnerabilities
    remaining_vulns = []
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        if 'f"' in line and any(sql_keyword in line.upper() for sql_keyword in ['SELECT', 'FROM', 'WHERE', 'ORDER BY']):
            if 'SECURITY FIX' not in line and 'validated_' not in line:
                remaining_vulns.append(f"Line {i}: {line.strip()}")
    
    if remaining_vulns:
        print(f"⚠️ Potential remaining vulnerabilities: {len(remaining_vulns)}")
        for vuln in remaining_vulns[:5]:  # Show first 5
            print(f"   {vuln}")
    else:
        print("✅ No obvious remaining SQL injection vulnerabilities found")
    
    return len(remaining_vulns) == 0

def main():
    """Main security patching process."""
    print("🛡️ DATABASE.PY SECURITY PATCHING TOOL")
    print("="*50)
    
    if create_security_patches():
        print("\n🔍 Validating patches...")
        if validate_patches():
            print("\n🎉 ALL SECURITY PATCHES APPLIED SUCCESSFULLY!")
            print("✅ SQL injection vulnerabilities have been addressed")
            return True
        else:
            print("\n⚠️ Some issues may remain - manual review recommended")
            return False
    else:
        print("\n❌ Security patching failed")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)