#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 God Code Refactoring CLI - Command Line Interface

Easy-to-use command line interface for the God Code Refactoring Agent.
Detects and refactors god methods and god classes following SRP.

Usage:
    python run_god_code_refactoring.py --file path/to/file.py [options]
    python run_god_code_refactoring.py --scan path/to/directory [options]
"""

import sys
import argparse
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

# Setup project path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from audit_system.agents.god_code_refactoring_agent import (
    GodCodeRefactoringAgent, 
    GodCodeType, 
    run_god_code_analysis
)


def scan_directory(directory: Path, extensions: List[str] = None) -> List[Path]:
    """Scan directory for Python files."""
    if extensions is None:
        extensions = ['.py']
    
    python_files = []
    for ext in extensions:
        python_files.extend(directory.rglob(f"*{ext}"))
    
    return [f for f in python_files if f.is_file()]


def analyze_file(file_path: str, args: argparse.Namespace) -> Dict[str, Any]:
    """Analyze a single file for god codes."""
    
    print(f"\n🔍 Analyzing: {file_path}")
    print("-" * 50)
    
    results = run_god_code_analysis(
        file_path=file_path,
        aggressive=args.aggressive,
        dry_run=not args.apply
    )
    
    if results.get('error'):
        print(f"❌ Error: {results['error']}")
        return results
    
    detections_count = results['total_detections']
    
    if detections_count == 0:
        print("✅ No god code patterns detected")
        return results
    
    print(f"🚨 Found {detections_count} god code pattern(s):")
    print()
    
    # Show detections
    for i, detection in enumerate(results['detections'], 1):
        priority_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}
        emoji = priority_emoji.get(detection['priority'], "⚪")
        
        print(f"{emoji} {i}. {detection['type'].upper()}: {detection['name']}")
        print(f"   📏 Lines: {detection['lines']} ({detection['total_lines']} total)")
        print(f"   🎯 Complexity: {detection['complexity_score']:.1f}/100")
        print(f"   📋 Responsibilities: {detection['responsibilities']}")
        print(f"   ⚠️  Priority: {detection['priority']}")
        print()
    
    # Show strategies
    if args.show_strategy:
        print("🚀 Refactoring Strategies:")
        print("-" * 25)
        
        for i, strategy in enumerate(results['strategies'], 1):
            print(f"{i}. {strategy['original_name']}")
            print(f"   🔧 Approach: {strategy['approach']}")
            print(f"   📦 New modules: {len(strategy['new_modules'])}")
            print(f"   ⚠️  Risk: {strategy['risk']}")
            print(f"   📊 Expected improvement: {strategy['improvement']:.1f}%")
            print()
    
    # Show refactoring results if applied
    if args.apply:
        print("⚡ Refactoring Results:")
        print("-" * 20)
        
        for i, result in enumerate(results['refactoring_results'], 1):
            status = "✅" if result['success'] else "❌"
            print(f"{status} {i}. {result['original_name']}")
            
            if result['success']:
                print(f"   📁 Created: {len(result['modules_created'])} modules")
                for module in result['modules_created']:
                    print(f"      - {module}")
            
            if result['warnings']:
                print("   ⚠️  Warnings:")
                for warning in result['warnings']:
                    print(f"      - {warning}")
            print()
    
    return results


def generate_report(all_results: List[Dict[str, Any]], output_file: str = None):
    """Generate summary report of all analyzed files."""
    
    total_files = len(all_results)
    total_detections = sum(r.get('total_detections', 0) for r in all_results)
    files_with_issues = len([r for r in all_results if r.get('total_detections', 0) > 0])
    
    report = {
        "summary": {
            "total_files_analyzed": total_files,
            "files_with_god_codes": files_with_issues,
            "total_god_codes_found": total_detections,
            "clean_files": total_files - files_with_issues
        },
        "files": []
    }
    
    print("\n" + "="*60)
    print("📊 GOD CODE ANALYSIS REPORT")
    print("="*60)
    print()
    
    print("📈 Summary:")
    print(f"   📁 Files analyzed: {total_files}")
    print(f"   🚨 Files with god codes: {files_with_issues}")
    print(f"   ⚡ Total god codes found: {total_detections}")
    print(f"   ✅ Clean files: {total_files - files_with_issues}")
    print()
    
    if files_with_issues > 0:
        print("🔍 Files requiring attention:")
        
        # Sort files by severity (number of detections)
        problem_files = [r for r in all_results if r.get('total_detections', 0) > 0]
        problem_files.sort(key=lambda x: x.get('total_detections', 0), reverse=True)
        
        for result in problem_files:
            file_path = result.get('file_path', 'Unknown')
            detections = result.get('total_detections', 0)
            
            # Count priorities
            high_priority = len([d for d in result.get('detections', []) if d.get('priority') == 'HIGH'])
            medium_priority = len([d for d in result.get('detections', []) if d.get('priority') == 'MEDIUM'])
            low_priority = len([d for d in result.get('detections', []) if d.get('priority') == 'LOW'])
            
            print(f"   📄 {file_path}")
            print(f"      🔴 High: {high_priority} | 🟡 Medium: {medium_priority} | 🟢 Low: {low_priority}")
            
            # Add to report
            report["files"].append({
                "file_path": file_path,
                "total_detections": detections,
                "high_priority": high_priority,
                "medium_priority": medium_priority,
                "low_priority": low_priority,
                "detections": result.get('detections', [])
            })
        
        print()
        
        # Recommendations
        print("💡 Recommendations:")
        if high_priority > 0:
            print("   🔴 HIGH PRIORITY: Start with high-priority god codes for maximum impact")
        if medium_priority > 0:
            print("   🟡 MEDIUM PRIORITY: Refactor medium-priority codes for better maintainability")
        if low_priority > 0:
            print("   🟢 LOW PRIORITY: Consider refactoring for perfect code quality")
        
        print("   📚 Use --apply flag to automatically refactor detected patterns")
        print("   🔧 Use --aggressive for more sensitive detection")
        
    else:
        print("🎉 All files are clean! No god code patterns detected.")
    
    # Save report to file if specified
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n📄 Detailed report saved to: {output_file}")


def main():
    """Main CLI entry point."""
    
    parser = argparse.ArgumentParser(
        description="God Code Refactoring Agent - Detect and refactor god methods/classes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze single file
  python run_god_code_refactoring.py --file my_code.py
  
  # Scan entire directory
  python run_god_code_refactoring.py --scan ./src --aggressive
  
  # Apply refactoring automatically
  python run_god_code_refactoring.py --file my_code.py --apply
  
  # Generate detailed report
  python run_god_code_refactoring.py --scan ./src --report report.json
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--file', '-f', 
                           help='Analyze a single Python file')
    input_group.add_argument('--scan', '-s', 
                           help='Scan directory for Python files')
    
    # Analysis options
    parser.add_argument('--aggressive', '-a', 
                       action='store_true',
                       help='Use aggressive detection (lower thresholds)')
    
    parser.add_argument('--apply', 
                       action='store_true',
                       help='Apply refactoring automatically (not just detect)')
    
    parser.add_argument('--show-strategy', 
                       action='store_true',
                       help='Show refactoring strategies for detected patterns')
    
    # Output options
    parser.add_argument('--report', '-r',
                       help='Generate JSON report file')
    
    parser.add_argument('--verbose', '-v', 
                       action='store_true',
                       help='Enable verbose logging')
    
    parser.add_argument('--quiet', '-q', 
                       action='store_true',
                       help='Minimal output (errors only)')
    
    args = parser.parse_args()
    
    # Setup logging
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    elif args.quiet:
        logging.basicConfig(level=logging.ERROR)
    else:
        logging.basicConfig(level=logging.INFO)
    
    # Print header unless quiet
    if not args.quiet:
        print("🧠 God Code Refactoring Agent")
        print("Detecting and refactoring god methods/classes")
        print("Following Single Responsibility Principle (SRP)")
        print()
    
    # Collect files to analyze
    files_to_analyze = []
    
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"❌ Error: File not found: {args.file}")
            return 1
        files_to_analyze = [file_path]
        
    elif args.scan:
        scan_path = Path(args.scan)
        if not scan_path.exists():
            print(f"❌ Error: Directory not found: {args.scan}")
            return 1
        
        files_to_analyze = scan_directory(scan_path)
        if not files_to_analyze:
            print(f"❌ No Python files found in: {args.scan}")
            return 1
        
        if not args.quiet:
            print(f"📁 Found {len(files_to_analyze)} Python files to analyze")
    
    # Analyze all files
    all_results = []
    
    for file_path in files_to_analyze:
        try:
            result = analyze_file(str(file_path), args)
            all_results.append(result)
        except Exception as e:
            print(f"❌ Error analyzing {file_path}: {e}")
            all_results.append({"file_path": str(file_path), "error": str(e)})
    
    # Generate summary report
    if not args.quiet:
        generate_report(all_results, args.report)
    
    # Exit with error code if god codes found
    total_detections = sum(r.get('total_detections', 0) for r in all_results)
    return 1 if total_detections > 0 else 0


if __name__ == "__main__":
    sys.exit(main())