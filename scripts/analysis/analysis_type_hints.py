#!/usr/bin/env python3
"""
🔍 Type Hints Analysis for DatabaseManager

Analyzes the DatabaseManager class to identify methods that need
type hints improvement for report.md requirement:
"Add type hints to DatabaseManager methods"

This script:
- Analyzes existing type hints
- Identifies missing return type annotations
- Suggests improvements for complex types
- Provides comprehensive typing coverage
"""

import ast
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

def analyze_function_signatures(file_path: str) -> Dict[str, Any]:
    """Analyze Python file for function signatures and type hints."""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"❌ Syntax error in {file_path}: {e}")
        return {}
    
    analysis = {
        "classes": [],
        "functions": [],
        "methods": [],
        "type_hint_coverage": {
            "total_functions": 0,
            "with_return_hints": 0,
            "with_param_hints": 0,
            "fully_typed": 0
        }
    }
    
    class TypeHintAnalyzer(ast.NodeVisitor):
        def __init__(self):
            self.current_class = None
        
        def visit_ClassDef(self, node):
            self.current_class = node.name
            class_info = {
                "name": node.name,
                "methods": []
            }
            analysis["classes"].append(class_info)
            self.generic_visit(node)
            self.current_class = None
        
        def visit_FunctionDef(self, node):
            func_info = self.analyze_function(node)
            
            if self.current_class:
                # It's a method
                analysis["methods"].append(func_info)
                # Add to current class methods
                for cls in analysis["classes"]:
                    if cls["name"] == self.current_class:
                        cls["methods"].append(func_info)
                        break
            else:
                # It's a standalone function
                analysis["functions"].append(func_info)
            
            # Update coverage stats
            stats = analysis["type_hint_coverage"]
            stats["total_functions"] += 1
            
            if func_info["has_return_hint"]:
                stats["with_return_hints"] += 1
            
            if func_info["param_hints_count"] > 0:
                stats["with_param_hints"] += 1
            
            if func_info["is_fully_typed"]:
                stats["fully_typed"] += 1
        
        def analyze_function(self, node):
            """Analyze a function for type hints."""
            param_hints = []
            param_hints_count = 0
            
            # Analyze parameters
            for arg in node.args.args:
                has_hint = arg.annotation is not None
                param_info = {
                    "name": arg.arg,
                    "has_hint": has_hint,
                    "hint": ast.unparse(arg.annotation) if has_hint else None
                }
                param_hints.append(param_info)
                if has_hint:
                    param_hints_count += 1
            
            # Analyze return type
            has_return_hint = node.returns is not None
            return_hint = ast.unparse(node.returns) if has_return_hint else None
            
            # Determine if fully typed
            total_params = len(node.args.args)
            # Exclude 'self' parameter for methods
            if total_params > 0 and node.args.args[0].arg == 'self':
                total_params -= 1
                # Only subtract from param_hints_count if self actually had a hint (which it normally doesn't)
                if param_hints and param_hints[0].get("name") == "self" and param_hints[0].get("has_hint"):
                    param_hints_count = max(0, param_hints_count - 1)
            
            is_fully_typed = has_return_hint and (total_params == 0 or param_hints_count == total_params)
            
            return {
                "name": node.name,
                "line": node.lineno,
                "is_method": self.current_class is not None,
                "class_name": self.current_class,
                "parameters": param_hints,
                "param_hints_count": param_hints_count,
                "total_params": total_params,
                "has_return_hint": has_return_hint,
                "return_hint": return_hint,
                "is_fully_typed": is_fully_typed,
                "needs_improvement": not is_fully_typed and node.name not in ['__init__', '__str__', '__repr__']
            }
    
    analyzer = TypeHintAnalyzer()
    analyzer.visit(tree)
    
    return analysis

def print_analysis_report(analysis: Dict[str, Any], file_name: str):
    """Print detailed analysis report."""
    
    print(f"\n🔍 TYPE HINTS ANALYSIS: {file_name}")
    print("=" * 80)
    
    # Overall statistics
    stats = analysis["type_hint_coverage"]
    total = stats["total_functions"]
    
    if total == 0:
        print("❌ No functions found")
        return
    
    print(f"📊 OVERALL STATISTICS")
    print(f"   Total functions/methods: {total}")
    print(f"   With return type hints: {stats['with_return_hints']} ({stats['with_return_hints']/total*100:.1f}%)")
    print(f"   With parameter hints: {stats['with_param_hints']} ({stats['with_param_hints']/total*100:.1f}%)")
    print(f"   Fully typed: {stats['fully_typed']} ({stats['fully_typed']/total*100:.1f}%)")
    
    # Class analysis
    print(f"\n📋 CLASSES FOUND: {len(analysis['classes'])}")
    for cls in analysis["classes"]:
        print(f"\n   📁 Class: {cls['name']}")
        print(f"      Methods: {len(cls['methods'])}")
        
        # Method analysis
        needs_improvement = [m for m in cls["methods"] if m["needs_improvement"]]
        if needs_improvement:
            print(f"      🔧 Methods needing type hints: {len(needs_improvement)}")
            for method in needs_improvement[:5]:  # Show first 5
                missing = []
                if not method["has_return_hint"]:
                    missing.append("return type")
                if method["param_hints_count"] < method["total_params"]:
                    missing.append("parameter types")
                print(f"         ⚠️  {method['name']}() - missing: {', '.join(missing)}")
            
            if len(needs_improvement) > 5:
                print(f"         ... and {len(needs_improvement) - 5} more")
    
    # Functions that need improvement
    all_methods = analysis["methods"]
    needs_improvement = [m for m in all_methods if m["needs_improvement"]]
    
    if needs_improvement:
        print(f"\n🔧 METHODS NEEDING TYPE HINTS: {len(needs_improvement)}")
        print("   Priority fixes:")
        
        # Prioritize by method name patterns
        high_priority = [m for m in needs_improvement if any(pattern in m["name"] for pattern in [
            "get_", "create_", "update_", "delete_", "load_", "save_"
        ])]
        
        for method in high_priority[:10]:  # Show top 10 priority
            missing = []
            if not method["has_return_hint"]:
                missing.append("return type")
            if method["param_hints_count"] < method["total_params"]:
                missing.append(f"{method['total_params'] - method['param_hints_count']} parameters")
            
            print(f"      🎯 {method['name']}() (line {method['line']}) - missing: {', '.join(missing)}")
    
    # Type hint suggestions
    print(f"\n💡 SUGGESTED IMPROVEMENTS")
    
    common_return_types = {
        "get_": "Union[Dict[str, Any], List[Dict[str, Any]], None]",
        "create_": "Optional[int]",
        "update_": "bool", 
        "delete_": "bool",
        "load_": "Dict[str, Any]",
        "save_": "bool",
        "execute_": "Any",
        "fetch_": "List[Dict[str, Any]]",
        "find_": "Optional[Dict[str, Any]]",
        "search_": "List[Dict[str, Any]]"
    }
    
    suggestions_made = 0
    for method in needs_improvement[:8]:  # Limit suggestions
        if not method["has_return_hint"]:
            suggestion = None
            for pattern, return_type in common_return_types.items():
                if method["name"].startswith(pattern):
                    suggestion = return_type
                    break
            
            if suggestion:
                print(f"   🔄 {method['name']}() -> {suggestion}")
                suggestions_made += 1
    
    if suggestions_made == 0:
        print("   ✅ Most methods already have appropriate type hints")
    
    # Coverage grade
    coverage_percent = stats['fully_typed'] / total * 100
    if coverage_percent >= 90:
        grade = "A+ (Excellent)"
    elif coverage_percent >= 80:
        grade = "A (Very Good)"
    elif coverage_percent >= 70:
        grade = "B (Good)"
    elif coverage_percent >= 60:
        grade = "C (Needs Improvement)"
    else:
        grade = "D (Significant Improvement Needed)"
    
    print(f"\n📈 TYPE HINT COVERAGE GRADE: {grade}")
    print(f"   Coverage: {coverage_percent:.1f}%")

def main():
    """Main analysis execution."""
    database_file = Path(__file__).parent / "streamlit_extension" / "utils" / "database.py"
    
    if not database_file.exists():
        print(f"❌ Database file not found: {database_file}")
        return False
    
    print("🔍 ANALYZING DATABASEMANAGER TYPE HINTS")
    print("Addresses report.md requirement: Add type hints to DatabaseManager methods")
    
    analysis = analyze_function_signatures(str(database_file))
    
    if not analysis:
        print("❌ Failed to analyze file")
        return False
    
    print_analysis_report(analysis, "database.py")
    
    # Summary recommendations
    total_methods = analysis["type_hint_coverage"]["total_functions"]
    fully_typed = analysis["type_hint_coverage"]["fully_typed"]
    
    if total_methods > 0:
        coverage = fully_typed / total_methods * 100
        
        print(f"\n🎯 RECOMMENDATIONS")
        print("-" * 40)
        
        if coverage >= 90:
            print("✅ Excellent type hint coverage!")
            print("✅ Focus on complex return types and edge cases")
        elif coverage >= 70:
            print("🔧 Good foundation, needs refinement")
            print("🎯 Priority: Add return type hints to CRUD methods")
            print("🎯 Priority: Add parameter types to complex methods")
        else:
            print("🚨 Significant type hint improvements needed")
            print("🎯 High Priority: Add return types to all public methods")
            print("🎯 High Priority: Add parameter types to all methods")
            print("🎯 Focus on CRUD operations first")
        
        print(f"\n📊 Current Progress: {fully_typed}/{total_methods} methods fully typed ({coverage:.1f}%)")
        
        return coverage >= 70  # Consider success if 70%+ coverage
    
    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)