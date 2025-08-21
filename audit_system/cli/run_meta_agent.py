#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 MetaAgent CLI - Command Line Interface for Intelligent Agent Coordination

Easy-to-use command line interface for the MetaAgent system.
Demonstrates intelligent agent selection and coordination for code analysis.

Usage:
    python run_meta_agent.py --file path/to/file.py [options]
    python run_meta_agent.py --scan path/to/directory [options]
"""

import sys
import argparse
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any

# Setup project path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from audit_system.coordination.meta_agent import (
    MetaAgent, 
    TaskType,
    run_meta_agent_analysis
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
    """Analyze a single file using MetaAgent coordination."""
    
    print(f"\n🧠 MetaAgent Analysis: {file_path}")
    print("-" * 60)
    
    # Convert task string to enum
    task_type = TaskType(args.task)
    
    # Run MetaAgent analysis
    results = run_meta_agent_analysis(
        file_path=file_path,
        task_type=task_type,
        project_root=args.project_root,
        token_budget=args.token_budget,
        dry_run=not args.apply
    )
    
    if results.get('error'):
        print(f"❌ Analysis failed: {results['error']}")
        return results
    
    print("🎯 Agent Selection & Planning:")
    plan = results["execution_plan"]
    agents = plan["agents"]
    
    if not agents:
        print("   ℹ️  No agents recommended for this file")
        return results
    
    print(f"   📋 Selected agents: {', '.join(agents)}")
    print(f"   🔥 Estimated tokens: {plan['estimated_tokens']}")
    print(f"   ⏱️  Estimated time: {plan['estimated_time']:.1f}s")
    print()
    
    # Show execution results
    print("🚀 Execution Results:")
    execution_results = results["execution_results"]
    
    success_count = 0
    for result in execution_results:
        status = "✅" if result["success"] else "❌"
        agent_name = result["agent"].replace("_", " ").title()
        
        print(f"   {status} {agent_name}")
        print(f"      ⏱️  Time: {result['execution_time']:.2f}s")
        print(f"      🔥 Tokens: {result['tokens_used']}")
        
        if result["success"]:
            success_count += 1
        
        # Show warnings
        if result["warnings"]:
            for warning in result["warnings"]:
                print(f"      ⚠️  {warning}")
        
        # Show errors  
        if result["errors"]:
            for error in result["errors"]:
                print(f"      ❌ {error}")
        
        print()
    
    # Show summary
    summary = results["summary"]
    print("📊 Analysis Summary:")
    print(f"   🎯 Agents executed: {summary['total_agents']}")
    print(f"   ✅ Successful: {summary['successful_agents']}")
    print(f"   ⏱️  Total time: {summary['total_execution_time']:.2f}s")
    print(f"   🔥 Total tokens: {summary['total_tokens_used']}")
    
    success_rate = summary['successful_agents'] / summary['total_agents'] if summary['total_agents'] > 0 else 0
    print(f"   📈 Success rate: {success_rate:.1%}")
    
    return results


def generate_report(all_results: List[Dict[str, Any]], output_file: str = None):
    """Generate comprehensive report of all analyzed files."""
    
    total_files = len(all_results)
    successful_analyses = len([r for r in all_results if not r.get('error')])
    total_agents_executed = sum(r.get('summary', {}).get('total_agents', 0) for r in all_results)
    total_tokens_used = sum(r.get('summary', {}).get('total_tokens_used', 0) for r in all_results)
    total_time = sum(r.get('summary', {}).get('total_execution_time', 0) for r in all_results)
    
    report = {
        "meta_analysis_summary": {
            "total_files_analyzed": total_files,
            "successful_analyses": successful_analyses,
            "failed_analyses": total_files - successful_analyses,
            "total_agents_executed": total_agents_executed,
            "total_tokens_consumed": total_tokens_used,
            "total_execution_time": total_time
        },
        "files": []
    }
    
    print("\n" + "="*70)
    print("🧠 METAAGENT ANALYSIS REPORT")
    print("="*70)
    print()
    
    print("📈 Overall Summary:")
    print(f"   📁 Files analyzed: {total_files}")
    print(f"   ✅ Successful analyses: {successful_analyses}")
    print(f"   ❌ Failed analyses: {total_files - successful_analyses}")
    print(f"   🤖 Total agents executed: {total_agents_executed}")
    print(f"   🔥 Total tokens consumed: {total_tokens_used}")
    print(f"   ⏱️  Total execution time: {total_time:.1f}s")
    
    if successful_analyses > 0:
        avg_agents = total_agents_executed / successful_analyses
        avg_tokens = total_tokens_used / successful_analyses
        avg_time = total_time / successful_analyses
        
        print(f"   📊 Average agents per file: {avg_agents:.1f}")
        print(f"   📊 Average tokens per file: {avg_tokens:.0f}")
        print(f"   📊 Average time per file: {avg_time:.1f}s")
    
    print()
    
    # Agent usage statistics
    agent_stats = {}
    for result in all_results:
        if result.get('error'):
            continue
        
        for exec_result in result.get('execution_results', []):
            agent_type = exec_result['agent']
            if agent_type not in agent_stats:
                agent_stats[agent_type] = {
                    'executions': 0,
                    'successes': 0,
                    'total_tokens': 0,
                    'total_time': 0
                }
            
            agent_stats[agent_type]['executions'] += 1
            if exec_result['success']:
                agent_stats[agent_type]['successes'] += 1
            agent_stats[agent_type]['total_tokens'] += exec_result['tokens_used']
            agent_stats[agent_type]['total_time'] += exec_result['execution_time']
    
    if agent_stats:
        print("🤖 Agent Performance Statistics:")
        for agent_type, stats in sorted(agent_stats.items()):
            success_rate = stats['successes'] / stats['executions'] if stats['executions'] > 0 else 0
            avg_tokens = stats['total_tokens'] / stats['executions'] if stats['executions'] > 0 else 0
            avg_time = stats['total_time'] / stats['executions'] if stats['executions'] > 0 else 0
            
            agent_name = agent_type.replace('_', ' ').title()
            print(f"   📋 {agent_name}:")
            print(f"      🎯 Executions: {stats['executions']}")
            print(f"      ✅ Success rate: {success_rate:.1%}")
            print(f"      🔥 Avg tokens: {avg_tokens:.0f}")
            print(f"      ⏱️  Avg time: {avg_time:.2f}s")
    
    print()
    
    # File-specific results
    if successful_analyses > 0:
        print("📁 File Analysis Results:")
        
        # Sort files by total agents executed (most complex first)
        sorted_results = sorted(
            [r for r in all_results if not r.get('error')],
            key=lambda r: r.get('summary', {}).get('total_agents', 0),
            reverse=True
        )
        
        for result in sorted_results[:10]:  # Show top 10 most complex
            file_path = result['file_path']
            summary = result['summary']
            
            print(f"   📄 {file_path}")
            print(f"      🤖 Agents: {summary['total_agents']} ({summary['successful_agents']} successful)")
            print(f"      🔥 Tokens: {summary['total_tokens_used']}")
            print(f"      ⏱️  Time: {summary['total_execution_time']:.2f}s")
            
            # Show which agents were used
            agents = [r['agent'] for r in result['execution_results'] if r['success']]
            if agents:
                agent_names = [a.replace('_', ' ').title() for a in agents]
                print(f"      🎯 Used: {', '.join(agent_names)}")
            
            # Add to report
            report["files"].append({
                "file_path": file_path,
                "agents_executed": summary['total_agents'],
                "successful_agents": summary['successful_agents'],
                "tokens_used": summary['total_tokens_used'],
                "execution_time": summary['total_execution_time'],
                "agents_used": agents
            })
        
        if len(sorted_results) > 10:
            print(f"   ... and {len(sorted_results) - 10} more files")
    
    print()
    
    # Recommendations
    print("💡 MetaAgent Recommendations:")
    
    if total_tokens_used > 50000:
        print("   🔥 High token usage detected - consider using more selective analysis")
        
    if total_files - successful_analyses > 0:
        print(f"   ⚠️  {total_files - successful_analyses} files failed analysis - check error logs")
    
    if agent_stats:
        # Find least successful agent
        worst_agent = min(agent_stats.items(), 
                         key=lambda x: x[1]['successes'] / x[1]['executions'] if x[1]['executions'] > 0 else 1)
        if worst_agent[1]['successes'] / worst_agent[1]['executions'] < 0.8:
            print(f"   🔧 Agent '{worst_agent[0]}' has low success rate - check configuration")
    
    if successful_analyses > 0:
        print("   ✅ MetaAgent successfully coordinated intelligent analysis")
        print("   🎯 Agent selection appears to be working effectively")
    
    # Save report to file if specified
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n📄 Detailed report saved to: {output_file}")


def main():
    """Main CLI entry point."""
    
    parser = argparse.ArgumentParser(
        description="MetaAgent CLI - Intelligent Agent Coordination for Code Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze single file with comprehensive audit
  python run_meta_agent.py --file my_code.py
  
  # Analyze with specific task type
  python run_meta_agent.py --file my_code.py --task god_code_detection
  
  # Scan entire directory
  python run_meta_agent.py --scan ./src --token-budget 100000
  
  # Apply agent recommendations (not dry-run)
  python run_meta_agent.py --file my_code.py --apply
  
  # Generate detailed report
  python run_meta_agent.py --scan ./src --report meta_analysis_report.json
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--file', '-f', 
                           help='Analyze a single Python file')
    input_group.add_argument('--scan', '-s', 
                           help='Scan directory for Python files')
    
    # Task options
    parser.add_argument('--task', '-t',
                       choices=[t.value for t in TaskType],
                       default=TaskType.COMPREHENSIVE_AUDIT.value,
                       help='Type of analysis task to perform')
    
    # Configuration options
    parser.add_argument('--project-root',
                       help='Project root directory (auto-detected if not specified)')
    
    parser.add_argument('--token-budget',
                       type=int,
                       default=32000,
                       help='Token budget for analysis (default: 32000)')
    
    parser.add_argument('--apply',
                       action='store_true', 
                       help='Apply agent recommendations (not dry-run mode)')
    
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
        print("🧠 MetaAgent - Intelligent Agent Coordination")
        print("Automated agent selection and task optimization")
        print(f"Task: {args.task.replace('_', ' ').title()}")
        print(f"Token Budget: {args.token_budget:,}")
        print(f"Mode: {'Apply Changes' if args.apply else 'Dry Run'}")
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
    start_time = time.time()
    
    for i, file_path in enumerate(files_to_analyze, 1):
        if not args.quiet and len(files_to_analyze) > 1:
            print(f"\n[{i}/{len(files_to_analyze)}] Processing: {file_path}")
        
        try:
            result = analyze_file(str(file_path), args)
            all_results.append(result)
        except KeyboardInterrupt:
            print("\n⚠️  Analysis interrupted by user")
            break
        except Exception as e:
            print(f"❌ Error analyzing {file_path}: {e}")
            all_results.append({"file_path": str(file_path), "error": str(e)})
    
    total_time = time.time() - start_time
    
    # Generate summary report
    if not args.quiet and all_results:
        print(f"\n⏱️  Total analysis time: {total_time:.1f}s")
        generate_report(all_results, args.report)
    
    # Exit with appropriate code
    failed_analyses = len([r for r in all_results if r.get('error')])
    return 1 if failed_analyses > 0 else 0


if __name__ == "__main__":
    sys.exit(main())