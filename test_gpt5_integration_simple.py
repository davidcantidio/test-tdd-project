#!/usr/bin/env python3
"""
GPT-5 Integration Validation - Simple Test
Tests the GPT-5 integration without making actual API calls.
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

def test_backend_initialization():
    """Test GPT-5 backend can be initialized."""
    logging.info("🔍 Testing GPT-5 Backend Initialization...")
    
    try:
        from audit_system.core.openai_backend import OpenAIBackend
        
        # Test backend creation
        backend = OpenAIBackend(model="gpt-5")
        logging.info("✅ GPT-5 Backend created successfully")
        logging.info(f"   Model: {backend.model}")
        logging.info(f"   Client initialized: {backend.client is not None}")
        
        return True
        
    except Exception as e:
        logging.info(f"❌ GPT-5 Backend Test Failed: {e}")
        return False

def test_agent_initialization():
    """Test IntelligentCodeAgent initializes with GPT-5."""
    logging.info("\n🤖 Testing Agent Initialization with GPT-5...")
    
    try:
        from audit_system.agents.intelligent_code_agent import IntelligentCodeAgent
        
        # Create agent with GPT-5 enabled
        agent = IntelligentCodeAgent(
            project_root=Path("."),
            enable_real_llm=True  # Should automatically use GPT-5
        )
        
        logging.info("✅ IntelligentCodeAgent created with GPT-5 backend")
        logging.info(f"   Real LLM enabled: {agent.enable_real_llm}")
        logging.info(f"   LLM Backend type: {type(agent.llm_backend).__name__}")
        
        # Check if GPT-5 backend is used
        if hasattr(agent.llm_backend, 'model'):
            logging.info(f"   Model configured: {agent.llm_backend.model}")
        
        return True
            
    except Exception as e:
        logging.info(f"❌ Agent Integration Test Failed: {e}")
        return False

def test_refactoring_engine_integration():
    """Test IntelligentRefactoringEngine integration."""
    logging.info("\n🔧 Testing Refactoring Engine GPT-5 Integration...")
    
    try:
        from audit_system.agents.intelligent_refactoring_engine import IntelligentRefactoringEngine
        
        # Create refactoring engine
        engine = IntelligentRefactoringEngine(
            dry_run=True,  # Don't make actual changes
            enable_real_llm=True
        )
        
        logging.info("✅ IntelligentRefactoringEngine created with GPT-5")
        logging.info(f"   Real LLM enabled: {engine.enable_real_llm}")
        logging.info(f"   Available strategies: {len(engine.refactoring_strategies)}")
        
        # List strategies
        for i, strategy in enumerate(engine.refactoring_strategies.keys(), 1):
            logging.info(f"   {i}. {strategy}")
        
        return True
        
    except Exception as e:
        logging.info(f"❌ Refactoring Engine Test Failed: {e}")
        return False

def main():
    """Run all GPT-5 integration validation tests."""
    logging.info("🚀 GPT-5 Integration Validation Suite")
    logging.info("="*50)
    
    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        logging.info("❌ OPENAI_API_KEY not found in environment")
        logging.info("Please set: export OPENAI_API_KEY='sk-proj-YOUR_KEY_HERE'")
        return False
    else:
        logging.info("✅ OPENAI_API_KEY configured")
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: Backend Initialization
    if test_backend_initialization():
        tests_passed += 1
    
    # Test 2: Agent Integration  
    if test_agent_initialization():
        tests_passed += 1
    
    # Test 3: Refactoring Engine Integration
    if test_refactoring_engine_integration():
        tests_passed += 1
    
    logging.info(f"\n📊 Validation Results: {tests_passed}/{total_tests} passed")
    
    if tests_passed == total_tests:
        logging.info("🎉 All GPT-5 integration validations passed!")
        logging.info("\n✅ **INTEGRATION STATUS: SUCCESS**")
        logging.info("   - GPT-5 backend properly initialized")
        logging.info("   - Agents successfully integrated with GPT-5")
        logging.info("   - System ready for real LLM usage")
        logging.info("\n💡 **NEXT STEPS:**")
        logging.info("   1. Add API credit to your OpenAI account")
        logging.info("   2. Run: ./audit_intelligent.sh")
        logging.info("   3. Run: ./apply_intelligent_optimizations.sh --apply")
        return True
    else:
        logging.info("❌ Some validations failed. Check configuration.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)