#!/usr/bin/env python3
"""
🧬 Focused Ultra-Deep Audit - Critical Issues Only

Optimized version focusing on the most critical architectural diseases.
"""

import ast
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set

class FocusedUltraAudit:
    def __init__(self):
        self.catastrophic_issues = []
        self.critical_patterns = []
        self.race_conditions = []
        self.data_leaks = []
        
    def quick_scan(self):
        """Quick scan for most critical issues."""
        print("🧬 ULTRA-DEEP AUDIT - FOCUSED SCAN")
        print("="*60)
        
        streamlit_dir = Path("streamlit_extension")
        if not streamlit_dir.exists():
            return
        
        # Focus on key problematic files
        key_files = [
            "utils/database.py",
            "utils/auth_manager.py", 
            "utils/session_manager.py",
            "utils/cache.py",
            "components/form_components.py",
            "auth/middleware.py"
        ]
        
        total_issues = 0
        
        print("\n🔬 SCANNING FOR CATASTROPHIC ISSUES...")
        print("-"*40)
        
        for file_name in key_files:
            file_path = streamlit_dir / file_name
            if not file_path.exists():
                continue
                
            with open(file_path, 'r') as f:
                content = f.read()
            
            print(f"\n📁 {file_name}")
            
            # 1. RACE CONDITIONS - Check for global state modifications
            global_mods = re.findall(r'global\s+(\w+).*\n.*\1\s*=', content, re.MULTILINE)
            if global_mods:
                print(f"  🔴 RACE CONDITION: {len(global_mods)} global state modifications")
                self.race_conditions.extend(global_mods)
                total_issues += len(global_mods)
            
            # 2. CONCURRENT SESSION STATE - Most dangerous in Streamlit
            session_races = re.findall(r'st\.session_state\[.*?\]\s*=.*\n.*st\.session_state\[.*?\]\s*=', content, re.DOTALL)
            if session_races:
                print(f"  🔴 CONCURRENT STATE: {len(session_races)} session state race conditions")
                total_issues += len(session_races)
            
            # 3. DATA LEAKS - Passwords/tokens in logs or prints
            log_leaks = re.findall(r'(log|print).*\(.*?(password|token|secret|api_key).*?\)', content, re.IGNORECASE)
            if log_leaks:
                print(f"  🔴 DATA LEAK: {len(log_leaks)} sensitive data in logs/prints")
                self.data_leaks.extend(log_leaks)
                total_issues += len(log_leaks)
            
            # 4. NON-ATOMIC FINANCIAL OPS - Most catastrophic
            financial_races = re.findall(r'(balance|amount|price).*?[-+].*?\n.*?execute', content, re.IGNORECASE | re.DOTALL)
            if financial_races:
                print(f"  💀 CATASTROPHIC: {len(financial_races)} non-atomic financial operations")
                self.catastrophic_issues.extend(financial_races)
                total_issues += len(financial_races) * 10  # Weight these heavily
            
            # 5. UNVALIDATED EXTERNAL INPUT
            unvalidated = re.findall(r'request\.(get|json|form).*?\[.*?\](?!.*validate)', content)
            if unvalidated:
                print(f"  🔴 INJECTION RISK: {len(unvalidated)} unvalidated external inputs")
                total_issues += len(unvalidated)
            
            # 6. EXCEPTION SWALLOWING
            swallowed = re.findall(r'except.*?:\s*\n\s*pass', content, re.MULTILINE)
            if swallowed:
                print(f"  ⚠️ ERROR CASCADE: {len(swallowed)} swallowed exceptions")
                total_issues += len(swallowed)
        
        # Check for thread safety issues
        print("\n🔬 THREAD SAFETY ANALYSIS...")
        print("-"*40)
        
        # Look for threading without locks
        for file_path in streamlit_dir.rglob("*.py"):
            if '__pycache__' in str(file_path):
                continue
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                if 'threading.Thread' in content:
                    has_lock = 'Lock' in content or 'RLock' in content
                    if not has_lock:
                        print(f"  🔴 THREAD UNSAFE: {file_path.name} uses threading without locks")
                        total_issues += 5
            except:
                pass
        
        # Memory leak detection
        print("\n🔬 MEMORY LEAK DETECTION...")
        print("-"*40)
        
        leak_count = 0
        for file_path in streamlit_dir.rglob("*.py"):
            if '__pycache__' in str(file_path):
                continue
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Unclosed file handles
                opens = len(re.findall(r'\bopen\s*\(', content))
                closes = len(re.findall(r'\.close\s*\(\)', content))
                with_statements = len(re.findall(r'with\s+open', content))
                
                unclosed = opens - closes - with_statements
                if unclosed > 0:
                    print(f"  ⚠️ RESOURCE LEAK: {file_path.name} has {unclosed} unclosed file handles")
                    leak_count += unclosed
                    total_issues += unclosed
            except:
                pass
        
        # Calculate risk score
        print("\n" + "="*60)
        print("🧬 ULTRA-DEEP RISK ASSESSMENT")
        print("="*60)
        
        catastrophic_weight = len(self.catastrophic_issues) * 100
        race_condition_weight = len(self.race_conditions) * 50
        data_leak_weight = len(self.data_leaks) * 30
        other_issues = total_issues - len(self.catastrophic_issues) - len(self.race_conditions) - len(self.data_leaks)
        
        ultra_risk_score = catastrophic_weight + race_condition_weight + data_leak_weight + (other_issues * 10)
        
        print(f"\n📊 ISSUE BREAKDOWN:")
        print(f"  Catastrophic Issues: {len(self.catastrophic_issues)}")
        print(f"  Race Conditions: {len(self.race_conditions)}")
        print(f"  Data Leaks: {len(self.data_leaks)}")
        print(f"  Other Critical Issues: {other_issues}")
        print(f"  Total Issues: {total_issues}")
        
        print(f"\n🎯 ULTRA RISK SCORE: {ultra_risk_score}")
        
        if ultra_risk_score == 0:
            print("✅ PERFECT: No critical architectural diseases found!")
        elif ultra_risk_score < 100:
            print("✅ GOOD: Minor issues only")
        elif ultra_risk_score < 500:
            print("⚠️ WARNING: Significant architectural problems")
        elif ultra_risk_score < 1000:
            print("🔴 DANGEROUS: Serious architectural diseases")
        else:
            print("💀 CATASTROPHIC: System architecture is critically compromised")
        
        # Specific recommendations
        print("\n💡 CRITICAL RECOMMENDATIONS:")
        print("-"*40)
        
        if self.catastrophic_issues:
            print("1. 💀 IMMEDIATE: Fix non-atomic financial operations")
        if self.race_conditions:
            print("2. 🔴 URGENT: Implement thread-safe global state management")
        if self.data_leaks:
            print("3. 🔴 URGENT: Remove sensitive data from logs")
        if leak_count > 0:
            print("4. ⚠️ IMPORTANT: Fix resource leaks with context managers")
        
        return ultra_risk_score

def main():
    auditor = FocusedUltraAudit()
    score = auditor.quick_scan()
    return score < 500  # Return True if acceptable risk

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)