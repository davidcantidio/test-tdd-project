#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 Scan Issues - Python Script for Code Quality Analysis

Simple Python interface for intelligent code analysis using the existing
audit system infrastructure. Scans directories for code quality issues,
complexity problems, and refactoring opportunities.

Usage:
    python scan_issues.py [directory]                    # Scan directory
    python scan_issues.py --file path/to/file.py        # Scan single file
    python scan_issues.py --format json                 # JSON output
    python scan_issues.py --verbose                     # Detailed output
    python scan_issues.py --complexity-threshold 50     # Filter by complexity
    python scan_issues.py --issues-only                 # Show only files with issues

Examples:
    python scan_issues.py streamlit_extension/          # Scan Streamlit module
    python scan_issues.py --file database.py --verbose  # Analyze single file
    python scan_issues.py --format json > analysis.json # Save to JSON
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import time

# Setup project path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )

class CodeScanner:
    """Main scanner class that interfaces with the Agno-native audit system."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)
        
        # Initialize with Claude subagents and Agno tools (no OpenAI required)
        from audit_system.tools.complexity_analyzer_tool import ComplexityAnalyzerTool
        from audit_system.tools.extract_method_tool import ExtractMethodTool
        
        # Initialize Agno tools for analysis
        self.complexity_tool = ComplexityAnalyzerTool()
        self.extract_method_tool = ExtractMethodTool()
        
        self.logger.info("✅ Agno-native tools initialized (Claude subagents compatible)")
    
    def scan_file(self, file_path: str) -> Dict[str, Any]:
        """
        Scan a single Python file for issues.
        
        Args:
            file_path: Path to the Python file to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        start_time = time.time()
        
        try:
            # Use Agno tools with Claude subagents
            result = self._analyze_file_with_agno_tools(file_path)
            
            # Add metadata
            result.update({
                "analysis_type": "agno_tools_claude_subagents",
                "analysis_duration": time.time() - start_time,
                "timestamp": datetime.now().isoformat()
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing {file_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path,
                "analysis_duration": time.time() - start_time
            }
    
    def _analyze_file_with_agno_tools(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze file using Agno tools directly (no external API required).
        
        Args:
            file_path: Path to Python file
            
        Returns:
            Analysis results dictionary
        """
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            # Run complexity analysis
            complexity_result = self.complexity_tool.analyze_code(file_content, file_path)
            
            # Run extract method analysis 
            extract_result = self.extract_method_tool.analyze_code(file_content, file_path)
            
            # Combine results into standard format
            total_issues = 0
            recommendations = 0
            complexity_score = 0
            
            # Initialize variables
            complexity_targets = []
            extract_targets = []
            high_complexity_targets = []
            high_confidence_targets = []
            
            # Extract complexity metrics
            if complexity_result.get("success"):
                # Get targets from the result format
                complexity_result_targets = complexity_result.get("targets", [])
                complexity_targets = complexity_result_targets
                
                # Count targets with high confidence as issues
                high_conf_complexity = complexity_result.get("high_confidence_targets", 0)
                if high_conf_complexity > 0:
                    total_issues += high_conf_complexity
                
                # Calculate maximum complexity score for display
                if complexity_result_targets:
                    complexity_scores = [t.get("complexity_score", 0) for t in complexity_result_targets]
                    complexity_score = max(complexity_scores) if complexity_scores else 0
            
            # Extract method extraction opportunities  
            if extract_result.get("success"):
                # Get targets from the result format
                extract_result_targets = extract_result.get("targets", [])
                extract_targets = extract_result_targets
                
                # Count high confidence extraction targets as recommendations
                high_conf_extract = extract_result.get("high_confidence_targets", 0)
                if high_conf_extract > 0:
                    recommendations += high_conf_extract
            
            # Generate summary
            analysis_summary = f"""📊 AGNO TOOLS ANALYSIS RESULTS:

📁 File: {file_path}
🔧 Analysis Method: Agno native tools (Claude subagents compatible)

🚨 COMPLEXITY ANALYSIS:
- Total complexity targets: {len(complexity_targets)}
- High confidence issues: {complexity_result.get("high_confidence_targets", 0)}
- Maximum complexity score: {complexity_score:.1f}

🔧 REFACTORING OPPORTUNITIES:
- Total extraction targets: {len(extract_targets)}
- High confidence recommendations: {extract_result.get("high_confidence_targets", 0)}

📋 SUMMARY:
- Total issues found: {total_issues}
- Optimization recommendations: {recommendations}

{'🔥 HIGH PRIORITY FILES - Action needed!' if total_issues > 0 or recommendations > 0 else '✅ Good code quality - minimal issues detected'}"""
            
            return {
                "success": True,
                "file_path": file_path,
                "analysis": analysis_summary,
                "complexity_score": complexity_score,
                "issues_found": total_issues,
                "recommendations": recommendations,
                "tool_results": {
                    "complexity_analysis": complexity_result,
                    "extract_method_analysis": extract_result
                },
                "tokens_used": 0  # No external API calls
            }
            
        except FileNotFoundError:
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "file_path": file_path
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path
            }
    
    def scan_directory(self, directory: str, file_pattern: str = "*.py") -> Dict[str, Any]:
        """
        Scan all Python files in a directory.
        
        Args:
            directory: Directory path to scan
            file_pattern: File pattern to match (default: "*.py")
            
        Returns:
            Dictionary containing consolidated scan results
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            return {
                "success": False,
                "error": f"Directory not found: {directory}"
            }
        
        # Find Python files
        py_files = []
        for py_file in dir_path.rglob(file_pattern):
            if any(skip in str(py_file) for skip in ['__pycache__', '.git', '.pytest_cache', 'venv', '.venv']):
                continue
            py_files.append(str(py_file))
        
        if not py_files:
            return {
                "success": False,
                "error": f"No Python files found in {directory}"
            }
        
        self.logger.info(f"🔍 Scanning {len(py_files)} Python files in {directory}")
        
        # Analyze files
        file_results = []
        total_issues = 0
        total_recommendations = 0
        failed_files = []
        
        for i, file_path in enumerate(py_files, 1):
            self.logger.info(f"  [{i}/{len(py_files)}] {file_path}")
            
            result = self.scan_file(file_path)
            if result["success"]:
                file_results.append(result)
                total_issues += result.get("issues_found", 0)
                total_recommendations += result.get("recommendations", 0)
            else:
                failed_files.append(result)
        
        # Create summary
        return {
            "success": True,
            "directory": directory,
            "files_scanned": len(py_files),
            "files_analyzed": len(file_results),
            "files_failed": len(failed_files),
            "total_issues": total_issues,
            "total_recommendations": total_recommendations,
            "file_results": file_results,
            "failed_files": failed_files,
            "scan_timestamp": datetime.now().isoformat()
        }
    
    def get_summary(self, scan_result: Dict[str, Any], complexity_threshold: float = 50.0, issues_only: bool = False) -> Dict[str, Any]:
        """
        Generate a summary of scan results.
        
        Args:
            scan_result: Result from scan_file or scan_directory
            complexity_threshold: Minimum complexity to highlight
            issues_only: Only show files with issues
            
        Returns:
            Summary dictionary
        """
        if not scan_result["success"]:
            return scan_result
        
        # Handle single file vs directory scan
        if "file_results" in scan_result:
            files = scan_result["file_results"]
        else:
            files = [scan_result]
        
        # Filter and categorize files
        high_complexity_files = []
        files_with_issues = []
        files_with_recommendations = []
        
        for file_result in files:
            complexity = file_result.get("complexity_score", 0)
            issues = file_result.get("issues_found", 0)
            recommendations = file_result.get("recommendations", 0)
            
            if complexity >= complexity_threshold:
                high_complexity_files.append({
                    "file": file_result["file_path"],
                    "complexity": complexity,
                    "issues": issues,
                    "recommendations": recommendations
                })
            
            if issues > 0:
                files_with_issues.append({
                    "file": file_result["file_path"],
                    "issues": issues,
                    "complexity": complexity,
                    "recommendations": recommendations
                })
            
            if recommendations > 0:
                files_with_recommendations.append({
                    "file": file_result["file_path"],
                    "recommendations": recommendations,
                    "complexity": complexity,
                    "issues": issues
                })
        
        # Apply issues_only filter
        if issues_only:
            relevant_files = files_with_issues
        else:
            relevant_files = files
        
        return {
            "summary": {
                "total_files": len(files),
                "files_shown": len(relevant_files),
                "high_complexity_files": len(high_complexity_files),
                "files_with_issues": len(files_with_issues),
                "files_with_recommendations": len(files_with_recommendations),
                "complexity_threshold": complexity_threshold,
                "issues_only_filter": issues_only
            },
            "high_complexity": sorted(high_complexity_files, key=lambda x: x["complexity"], reverse=True),
            "files_with_issues": sorted(files_with_issues, key=lambda x: x["issues"], reverse=True),
            "optimization_opportunities": sorted(files_with_recommendations, key=lambda x: x["recommendations"], reverse=True)
        }

def format_text_output(scan_result: Dict[str, Any], summary: Dict[str, Any], verbose: bool = False) -> str:
    """Format results as human-readable text."""
    output = []
    
    # Header
    output.append("🔍 CODE QUALITY SCAN RESULTS")
    output.append("=" * 50)
    
    if not scan_result["success"]:
        output.append(f"❌ Error: {scan_result.get('error', 'Unknown error')}")
        return "\n".join(output)
    
    # Summary statistics
    stats = summary["summary"]
    output.append(f"📊 SCAN SUMMARY:")
    output.append(f"   Files analyzed: {stats['total_files']}")
    output.append(f"   High complexity: {stats['high_complexity_files']} (threshold: {stats['complexity_threshold']})")
    output.append(f"   Files with issues: {stats['files_with_issues']}")
    output.append(f"   Optimization opportunities: {len(summary['optimization_opportunities'])}")
    output.append("")
    
    # High complexity files
    if summary["high_complexity"]:
        output.append("🚨 HIGH COMPLEXITY FILES:")
        for file_info in summary["high_complexity"][:10]:  # Top 10
            output.append(f"   {file_info['file']}")
            output.append(f"      Complexity: {file_info['complexity']:.1f}, Issues: {file_info['issues']}, Recommendations: {file_info['recommendations']}")
        output.append("")
    
    # Files with issues
    if summary["files_with_issues"]:
        output.append("⚠️ FILES WITH ISSUES:")
        for file_info in summary["files_with_issues"][:10]:  # Top 10
            output.append(f"   {file_info['file']}")
            output.append(f"      Issues: {file_info['issues']}, Complexity: {file_info['complexity']:.1f}")
        output.append("")
    
    # Optimization opportunities
    if summary["optimization_opportunities"]:
        output.append("🔧 OPTIMIZATION OPPORTUNITIES:")
        for file_info in summary["optimization_opportunities"][:10]:  # Top 10
            output.append(f"   {file_info['file']}")
            output.append(f"      Recommendations: {file_info['recommendations']}, Complexity: {file_info['complexity']:.1f}")
        output.append("")
    
    # Verbose details
    if verbose and "file_results" in scan_result:
        output.append("📋 DETAILED ANALYSIS:")
        for file_result in scan_result["file_results"][:5]:  # Top 5 files
            output.append(f"   📁 {file_result['file_path']}")
            if "analysis" in file_result:
                analysis_text = file_result["analysis"]
                if len(analysis_text) > 200:
                    analysis_text = analysis_text[:200] + "..."
                output.append(f"      {analysis_text}")
            output.append("")
    
    # Next steps
    output.append("🚀 NEXT STEPS:")
    output.append("   1. Review high complexity files for refactoring opportunities")
    output.append("   2. Address files with the most issues first")
    output.append("   3. Run: python apply_fixes.py [file] to apply automated fixes")
    output.append("   4. Use --verbose for detailed analysis output")
    
    return "\n".join(output)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Scan Python code for quality issues and refactoring opportunities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Input options
    parser.add_argument("target", nargs="?", default=".", 
                       help="Directory or file to scan (default: current directory)")
    parser.add_argument("--file", dest="single_file", 
                       help="Scan a single file instead of directory")
    
    # Output options
    parser.add_argument("--format", choices=["text", "json"], default="text",
                       help="Output format (default: text)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Show detailed analysis output")
    
    # Filtering options
    parser.add_argument("--complexity-threshold", type=float, default=50.0,
                       help="Complexity threshold for highlighting (default: 50.0)")
    parser.add_argument("--issues-only", action="store_true",
                       help="Show only files with detected issues")
    
    # System options
    parser.add_argument("--debug", action="store_true",
                       help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(verbose=args.verbose or args.debug)
    
    try:
        # Initialize scanner
        scanner = CodeScanner(verbose=args.verbose)
        
        # Perform scan
        if args.single_file:
            scan_result = scanner.scan_file(args.single_file)
        else:
            scan_result = scanner.scan_directory(args.target)
        
        # Generate summary
        summary = scanner.get_summary(
            scan_result, 
            complexity_threshold=args.complexity_threshold,
            issues_only=args.issues_only
        )
        
        # Output results
        if args.format == "json":
            output_data = {
                "scan_result": scan_result,
                "summary": summary,
                "scan_parameters": {
                    "target": args.single_file or args.target,
                    "complexity_threshold": args.complexity_threshold,
                    "issues_only": args.issues_only,
                    "verbose": args.verbose
                }
            }
            print(json.dumps(output_data, indent=2, ensure_ascii=False))
        else:
            print(format_text_output(scan_result, summary, verbose=args.verbose))
        
        # Exit with appropriate code
        if not scan_result["success"]:
            sys.exit(1)
        elif scan_result.get("total_issues", 0) > 0:
            sys.exit(2)  # Issues found
        else:
            sys.exit(0)  # No issues
            
    except KeyboardInterrupt:
        print("\n❌ Scan interrupted by user")
        sys.exit(130)
    except Exception as e:
        logging.error(f"❌ Scan failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()