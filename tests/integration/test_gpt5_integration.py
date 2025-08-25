#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test GPT-5 Integration
---------------------
Teste simples da integração GPT-5 com os agentes.
"""

import os
import logging
from pathlib import Path

# Load .env file if it exists
env_path = Path('.env')
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

# Setup environment
os.environ["REAL_LLM_ENABLED"] = "1"
os.environ["OPENAI_MODEL"] = "gpt-5"

# Setup logging
logging.basicConfig(level=logging.INFO)

def test_gpt5_backend():
    """Test OpenAI GPT-5 backend directly."""
    print("🔍 Testing GPT-5 Backend Direct Integration...")
    
    try:
        from audit_system.core.openai_backend import OpenAIBackend
        
        # Test backend creation
        backend = OpenAIBackend(model="gpt-5")
        print("✅ GPT-5 Backend created successfully")
        
        # Test simple analysis
        sample_code = '''
def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)
'''
        
        overview = backend.file_overview(
            content=sample_code,
            file_path="fibonacci.py", 
            ast_tree=None
        )
        
        print(f"✅ GPT-5 Analysis Complete:")
        print(f"   Purpose: {overview.overall_purpose}")
        print(f"   Role: {overview.architectural_role}")
        print(f"   Confidence: {overview.confidence_score}")
        
        return True
        
    except Exception as e:
        print(f"❌ GPT-5 Backend Test Failed: {e}")
        return False

def test_agent_integration():
    """Test GPT-5 integration with IntelligentCodeAgent."""
    print("\n🤖 Testing Agent Integration with GPT-5...")
    
    try:
        from audit_system.agents.intelligent_code_agent import IntelligentCodeAgent
        
        # Create agent with GPT-5 enabled
        agent = IntelligentCodeAgent(
            project_root=Path("."),
            enable_real_llm=True  # Should automatically use GPT-5
        )
        
        print("✅ IntelligentCodeAgent created with GPT-5 backend")
        
        # Test analysis on a real file
        test_file = Path("audit_system/core/openai_backend.py")
        if test_file.exists():
            print(f"📁 Analyzing file: {test_file}")
            
            analysis = agent.analyze_file_intelligently(str(test_file))
            
            print(f"✅ Analysis Complete:")
            print(f"   Quality Score: {analysis.semantic_quality_score}")
            print(f"   Security Issues: {len(analysis.security_vulnerabilities)}")
            print(f"   Performance Issues: {len(analysis.performance_bottlenecks)}")
            print(f"   Refactorings: {len(analysis.recommended_refactorings)}")
            print(f"   Lines Analyzed: {len(analysis.lines_analyzed)}")
            print(f"   Tokens Used: {analysis.tokens_used}")
            
            return True
        else:
            print("⚠️ Test file not found, skipping file analysis")
            return True
            
    except Exception as e:
        print(f"❌ Agent Integration Test Failed: {e}")
        return False

def main():
    """Run all GPT-5 integration tests."""
    print("🚀 GPT-5 Integration Test Suite")
    print("="*50)
    
    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not found in environment")
        print("Please set: export OPENAI_API_KEY='sk-proj-YOUR_KEY_HERE'")
        return False
    
    tests_passed = 0
    total_tests = 2
    
    # Test 1: Backend
    if test_gpt5_backend():
        tests_passed += 1
    
    # Test 2: Agent Integration  
    if test_agent_integration():
        tests_passed += 1
    
    print(f"\n📊 Test Results: {tests_passed}/{total_tests} passed")
    
    if tests_passed == total_tests:
        print("🎉 All GPT-5 integration tests passed!")
        return True
    else:
        print("❌ Some tests failed. Check configuration.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)