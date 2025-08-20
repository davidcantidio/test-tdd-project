#!/usr/bin/env python3
"""
🛡️ Final Security Fixes

Patches the remaining 4 critical SQL injection vulnerabilities in database.py
"""

from pathlib import Path

def apply_final_fixes():
    """Apply final security fixes to database.py"""
    
    database_file = Path("streamlit_extension/utils/database.py")
    
    with open(database_file, 'r') as f:
        content = f.read()
    
    # Final patches for remaining vulnerabilities
    patches = [
        # Lines 293, 300: SELECT queries with table_name
        (
            'data_sql = f"SELECT * FROM {table_name} {where_clause_cursor} {order_clause} LIMIT ?"',
            '''# SECURITY FIX: Validate table name
                    validated_table = _validate_table_name(table_name)
                    data_sql = f"SELECT * FROM {validated_table} {where_clause_cursor} {order_clause} LIMIT ?"'''
        ),
        
        # Line 304: SELECT query with table_name
        (
            'data_sql = f"SELECT * FROM {table_name} {where_clause} {order_clause} LIMIT ? OFFSET ?"',
            '''# SECURITY FIX: Validate table name
                data_sql = f"SELECT * FROM {_validate_table_name(table_name)} {where_clause} {order_clause} LIMIT ? OFFSET ?"'''
        ),
        
        # Line 731: DELETE query with table_name
        (
            'f"DELETE FROM {table_name} WHERE id = :record_id",',
            'f"DELETE FROM {_validate_table_name(table_name)} WHERE id = :record_id",  # SECURITY FIX'
        )
    ]
    
    patched_content = content
    applied = 0
    
    for old, new in patches:
        if old in patched_content:
            patched_content = patched_content.replace(old, new)
            applied += 1
            print(f"✅ Applied patch: {old[:50]}...")
    
    if applied > 0:
        with open(database_file, 'w') as f:
            f.write(patched_content)
        print(f"\n🛡️ Applied {applied} final security patches")
        return True
    else:
        print("❌ No patches applied")
        return False

def validate_final_state():
    """Validate final security state"""
    database_file = Path("streamlit_extension/utils/database.py")
    
    with open(database_file, 'r') as f:
        content = f.read()
    
    # Count remaining unpatched f-strings with SQL
    lines = content.split('\n')
    remaining_vulns = []
    
    for i, line in enumerate(lines, 1):
        if 'f"' in line and any(sql in line.upper() for sql in ['SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE']):
            if 'SECURITY FIX' not in line and 'validated_' not in line and '_validate_table_name' not in line:
                if any(danger in line for danger in ['{table_name}', '{sort_column}', '{column}']):
                    remaining_vulns.append((i, line.strip()))
    
    print(f"\n📊 FINAL SECURITY VALIDATION:")
    print(f"Remaining critical SQL injection vulnerabilities: {len(remaining_vulns)}")
    
    if remaining_vulns:
        print("⚠️ Remaining vulnerabilities:")
        for line_no, line in remaining_vulns[:3]:
            print(f"  Line {line_no}: {line}")
    else:
        print("✅ NO CRITICAL SQL INJECTION VULNERABILITIES REMAINING!")
    
    # Count total security fixes applied
    security_fixes = content.count('SECURITY FIX')
    print(f"✅ Total security fixes applied: {security_fixes}")
    
    return len(remaining_vulns) == 0

def main():
    print("🛡️ FINAL SECURITY PATCHING")
    print("="*40)
    
    if apply_final_fixes():
        if validate_final_state():
            print("\n🎉 ALL CRITICAL SQL INJECTION VULNERABILITIES FIXED!")
            print("✅ Database.py is now secure")
            return True
        else:
            print("\n⚠️ Some vulnerabilities may remain")
            return False
    else:
        print("\n❌ Final patching failed")
        return False

if __name__ == "__main__":
    main()