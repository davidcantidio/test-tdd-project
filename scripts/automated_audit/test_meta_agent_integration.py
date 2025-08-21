#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 Test MetaAgent Integration

Tests the MetaAgent integration with the systematic file auditor
to ensure intelligent agent coordination is working correctly.
"""

import sys
import logging
import time
from pathlib import Path

# Setup project path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Test imports
try:
    from audit_system.coordination.meta_agent import (
        MetaAgent, 
        TaskType,
        run_meta_agent_analysis
    )
    from audit_system.core.systematic_file_auditor import EnhancedSystematicFileAuditor
    
    META_AGENT_AVAILABLE = True
except ImportError as e:
    print(f"❌ MetaAgent not available: {e}")
    META_AGENT_AVAILABLE = False


def test_meta_agent_initialization():
    """Test MetaAgent can be initialized correctly."""
    
    print("\n🔍 Testing MetaAgent Initialization...")
    
    try:
        meta_agent = MetaAgent(
            project_root=project_root,
            token_budget=10000,
            dry_run=True
        )
        
        print("✅ MetaAgent initialized successfully")
        
        # Test performance summary
        summary = meta_agent.get_performance_summary()
        print(f"📊 Initial performance summary: {summary['total_executions']} executions")
        
        return True
        
    except Exception as e:
        print(f"❌ MetaAgent initialization failed: {e}")
        return False


def test_meta_agent_file_analysis():
    """Test MetaAgent file analysis on a sample file."""
    
    print("\n🔍 Testing MetaAgent File Analysis...")
    
    # Find a sample Python file to analyze
    sample_files = list(project_root.glob("streamlit_extension/**/*.py"))
    if not sample_files:
        sample_files = list(project_root.glob("**/*.py"))
    
    if not sample_files:
        print("❌ No Python files found for testing")
        return False
    
    sample_file = sample_files[0]
    print(f"📄 Testing with file: {sample_file}")
    
    try:
        results = run_meta_agent_analysis(
            file_path=str(sample_file),
            task_type=TaskType.COMPREHENSIVE_AUDIT,
            token_budget=5000,
            dry_run=True
        )
        
        if results.get("error"):
            print(f"❌ Analysis failed: {results['error']}")
            return False
        
        print("✅ MetaAgent analysis completed successfully")
        
        # Show execution plan
        plan = results.get("execution_plan", {})
        agents = plan.get("agents", [])
        
        print(f"🤖 Agents selected: {', '.join(agents)}")
        print(f"🔥 Estimated tokens: {plan.get('estimated_tokens', 0)}")
        print(f"⏱️  Estimated time: {plan.get('estimated_time', 0):.1f}s")
        
        # Show execution results
        exec_results = results.get("execution_results", [])
        success_count = len([r for r in exec_results if r["success"]])
        
        print(f"📈 Execution results: {success_count}/{len(exec_results)} agents successful")
        
        return True
        
    except Exception as e:
        print(f"❌ MetaAgent file analysis failed: {e}")
        return False


def test_systematic_auditor_integration():
    """Test MetaAgent integration with systematic auditor."""
    
    print("\n🔍 Testing Systematic Auditor Integration...")
    
    try:
        audit_dir = Path(__file__).parent
        auditor = EnhancedSystematicFileAuditor(
            project_root=project_root, 
            audit_dir=audit_dir, 
            dry_run=True
        )
        
        print(f"✅ Auditor initialized - MetaAgent available: {auditor.meta_agent is not None}")
        
        if not auditor.meta_agent:
            print("⚠️  MetaAgent not available in auditor - check initialization")
            return False
        
        # Test with a small file
        sample_files = list(project_root.glob("config/*.py"))
        if not sample_files:
            sample_files = list(project_root.glob("**/*.py"))[:1]
        
        if not sample_files:
            print("❌ No files found for testing")
            return False
        
        sample_file = str(sample_files[0])
        print(f"📄 Testing integration with: {sample_file}")
        
        # Test the enhanced audit method
        result = auditor.audit_file_enhanced(sample_file)
        
        print(f"✅ Integration test completed")
        print(f"📊 Result: {result.lines_analyzed} lines analyzed, {result.issues_found} issues found")
        print(f"🔥 Tokens used: {result.tokens_used}")
        
        return True
        
    except Exception as e:
        print(f"❌ Systematic auditor integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_agent_selection_logic():
    """Test MetaAgent's intelligent agent selection logic."""
    
    print("\n🔍 Testing Agent Selection Logic...")
    
    try:
        meta_agent = MetaAgent(
            project_root=project_root,
            token_budget=10000,
            dry_run=True
        )
        
        # Test different file types
        test_cases = [
            ("streamlit_extension/services/client_service.py", "Service file - should select multiple agents"),
            ("tests/test_duration_calculator.py", "Test file - should select TDD agent"),
            ("config/environment.py", "Config file - should select basic analysis"),
        ]
        
        for file_path, description in test_cases:
            full_path = project_root / file_path
            if not full_path.exists():
                print(f"⚠️  Skipping {file_path} - file not found")
                continue
            
            print(f"\n📄 {description}")
            print(f"   File: {file_path}")
            
            # Analyze file characteristics
            file_analysis = meta_agent.analyze_file(str(full_path))
            
            print(f"   📏 Lines: {file_analysis.line_count}")
            print(f"   🏗️  Functions: {file_analysis.function_count}")
            print(f"   📦 Classes: {file_analysis.class_count}")
            print(f"   🔍 Complexity: {file_analysis.file_complexity.value}")
            print(f"   🎯 Type: {file_analysis.file_type}")
            
            # Get agent recommendations
            recommendations = meta_agent.recommend_agents(file_analysis)
            
            print(f"   🤖 Recommended agents ({len(recommendations)}):")
            for rec in recommendations:
                agent_name = rec.agent_type.value.replace('_', ' ').title()
                print(f"      - {agent_name} (Priority: {rec.priority.value}, Confidence: {rec.confidence:.2f})")
                print(f"        Reason: {rec.reasoning}")
        
        print("\n✅ Agent selection logic test completed")
        return True
        
    except Exception as e:
        print(f"❌ Agent selection logic test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all MetaAgent integration tests."""
    
    print("🧠 MetaAgent Integration Test Suite")
    print("=" * 50)
    
    # Setup logging
    logging.basicConfig(level=logging.WARNING)  # Reduce noise during testing
    
    if not META_AGENT_AVAILABLE:
        print("❌ MetaAgent not available - cannot run tests")
        return 1
    
    tests = [
        ("MetaAgent Initialization", test_meta_agent_initialization),
        ("MetaAgent File Analysis", test_meta_agent_file_analysis),
        ("Systematic Auditor Integration", test_systematic_auditor_integration),
        ("Agent Selection Logic", test_agent_selection_logic),
    ]
    
    results = []
    total_time = 0
    
    for test_name, test_func in tests:
        print(f"\n{'=' * 60}")
        print(f"🧪 Running: {test_name}")
        print("-" * 60)
        
        start_time = time.time()
        try:
            success = test_func()
            elapsed = time.time() - start_time
            total_time += elapsed
            
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"\n{status} {test_name} ({elapsed:.2f}s)")
            
            results.append((test_name, success, elapsed))
            
        except Exception as e:
            elapsed = time.time() - start_time
            total_time += elapsed
            
            print(f"\n❌ FAIL {test_name} ({elapsed:.2f}s)")
            print(f"   Error: {e}")
            
            results.append((test_name, False, elapsed))
    
    # Summary
    print(f"\n{'=' * 60}")
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = len([r for r in results if r[1]])
    total = len(results)
    
    print(f"Total tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Total time: {total_time:.2f}s")
    print()
    
    for test_name, success, elapsed in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name} ({elapsed:.2f}s)")
    
    if passed == total:
        print(f"\n🎉 All tests passed! MetaAgent integration is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())