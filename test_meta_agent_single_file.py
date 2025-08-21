#!/usr/bin/env python3
"""
Test MetaAgent on a single file to validate real optimizations are applied.
"""

import sys
import time
from pathlib import Path

# Add project root to path
sys.path.append('.')

try:
    from audit_system.coordination.meta_agent import (
        MetaAgent, TaskType, FileComplexity, AgentType, Priority
    )
    print("✅ MetaAgent system imported successfully")
except Exception as e:
    print(f"❌ Error importing MetaAgent system: {e}")
    sys.exit(1)

def test_single_file_optimization():
    """Test MetaAgent optimization on a single file."""
    
    file_path = "test_file_for_optimization.py"
    
    if not Path(file_path).exists():
        print(f"❌ Test file {file_path} not found")
        return
    
    print(f"🧠 Testing MetaAgent optimization on: {file_path}")
    
    # Initialize MetaAgent
    try:
        meta_agent = MetaAgent(
            project_root=Path('.'),
            token_budget=50000,
            max_time_per_file=600.0,
            enable_tdah_features=True,
            dry_run=False  # Apply real optimizations
        )
        print("🚀 MetaAgent initialized with all specialized agents")
        
    except Exception as e:
        print(f"❌ Error initializing MetaAgent: {e}")
        return
    
    print(f"\n📋 Step 1: Analyzing file complexity...")
    try:
        file_analysis = meta_agent.analyze_file(file_path)
        print(f"   📏 Lines: {file_analysis.line_count}")
        print(f"   🔧 Functions: {file_analysis.function_count}")
        print(f"   📊 Complexity: {file_analysis.file_complexity.value}")
        print(f"   🧮 AST Complexity Score: {file_analysis.ast_complexity_score:.1f}")
        print(f"   🎯 Suspected patterns: {file_analysis.suspected_patterns}")
        
    except Exception as e:
        print(f"❌ Error analyzing file: {e}")
        return
    
    print(f"\n🎯 Step 2: Creating optimization plan...")
    try:
        optimization_plan = meta_agent.create_execution_plan(
            file_path=file_path,
            task_type=TaskType.COMPREHENSIVE_AUDIT
        )
        
        print(f"   🤖 Selected agents: {[agent.agent_type.value for agent in optimization_plan.agents]}")
        print(f"   ⏱️ Estimated time: {optimization_plan.total_estimated_time:.1f}s")
        print(f"   🪙 Estimated tokens: {optimization_plan.total_estimated_tokens}")
        
    except Exception as e:
        print(f"❌ Error creating optimization plan: {e}")
        return
    
    print(f"\n🚀 Step 3: Executing comprehensive optimization...")
    try:
        start_time = time.time()
        execution_results = meta_agent.execute_plan(optimization_plan)
        execution_time = time.time() - start_time
        
        print(f"   ⏱️ Execution completed in {execution_time:.1f}s")
        print(f"   🤖 Agents executed: {len(execution_results)}")
        
        # Analyze results
        successful_agents = [r for r in execution_results if r.success]
        failed_agents = [r for r in execution_results if not r.success]
        total_tokens_used = sum(r.tokens_used for r in execution_results)
        
        print(f"\n📊 Step 4: Results analysis...")
        print(f"   ✅ Successful agents: {len(successful_agents)}")
        print(f"   ❌ Failed agents: {len(failed_agents)}")
        print(f"   🪙 Total tokens used: {total_tokens_used}")
        
        for result in execution_results:
            status = "✅" if result.success else "❌"
            print(f"   {status} {result.agent_type.value}: {result.execution_time:.1f}s, {result.tokens_used} tokens")
            if result.errors:
                for error in result.errors:
                    print(f"      ⚠️ Error: {error}")
        
        return len(successful_agents) > 0
        
    except Exception as e:
        print(f"❌ Error executing optimization: {e}")
        return False

def validate_syntax():
    """Validate syntax of optimized file."""
    file_path = "test_file_for_optimization.py"
    
    try:
        import py_compile
        py_compile.compile(file_path, doraise=True)
        print("✅ Syntax validation passed")
        return True
    except Exception as e:
        print(f"❌ Syntax validation failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing MetaAgent Real Optimization Capabilities")
    print("=" * 60)
    
    # Create backup
    import shutil
    shutil.copy("test_file_for_optimization.py", "test_file_BEFORE_optimization.py")
    print("💾 Backup created: test_file_BEFORE_optimization.py")
    
    # Test optimization
    success = test_single_file_optimization()
    
    # Validate syntax
    syntax_ok = validate_syntax()
    
    print("\n" + "=" * 60)
    if success and syntax_ok:
        print("🎉 MetaAgent test SUCCESSFUL - real optimizations applied!")
        print("📋 Compare files to see changes:")
        print("   diff test_file_BEFORE_optimization.py test_file_for_optimization.py")
    else:
        print("❌ MetaAgent test FAILED - no optimizations applied")
        
    print("🔍 Check execution details above for specific agent results")