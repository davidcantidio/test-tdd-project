#!/usr/bin/env python3
"""
Debug script to see what the agents actually return
so we can fix the extraction methods in MetaAgent.
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from audit_system.agents.intelligent_code_agent import IntelligentCodeAgent, AnalysisDepth, SemanticMode
from audit_system.agents.god_code_refactoring_agent import run_god_code_analysis

def debug_intelligent_code_agent():
    """Debug what IntelligentCodeAgent returns."""
    print("🔍 DEBUGGING INTELLIGENT CODE AGENT")
    logging.info("="*50)
    
    agent = IntelligentCodeAgent(
        project_root=project_root,
        analysis_depth=AnalysisDepth.ADVANCED,
        semantic_mode=SemanticMode.CONSERVATIVE,
        dry_run=False
    )
    
    result = agent.analyze_file_intelligently("test_complex_god_code.py")
    
    logging.info(f"Result type: {type(result)}")
    logging.info(f"Result dir: {[attr for attr in dir(result) if not attr.startswith('_')]}")
    
    if hasattr(result, 'recommended_refactorings'):
        refactorings = result.recommended_refactorings
        logging.info(f"Recommended refactorings count: {len(refactorings)}")
        
        for i, refactoring in enumerate(refactorings):
            logging.info(f"\nRefactoring {i+1}:")
            logging.info(f"  Type: {type(refactoring)}")
            logging.info(f"  Dir: {[attr for attr in dir(refactoring) if not attr.startswith('_')]}")
            
            if hasattr(refactoring, 'refactoring_type'):
                logging.info(f"  Refactoring type: {refactoring.refactoring_type}")
            
            # Check for any code-related attributes
            for attr in dir(refactoring):
                if 'code' in attr.lower() and not attr.startswith('_'):
                    value = getattr(refactoring, attr)
                    logging.info(f"  {attr}: {type(value)} - {str(value)[:100] if value else 'None'}...")
    
    return result

def debug_god_code_agent():
    """Debug what GodCodeAgent returns."""
    print("\n🔍 DEBUGGING GOD CODE AGENT")
    logging.info("="*50)
    
    result = run_god_code_analysis(
        file_path="test_complex_god_code.py",
        aggressive=False,
        dry_run=False
    )
    
    logging.info(f"Result type: {type(result)}")
    
    if isinstance(result, dict):
        logging.info("Result keys:", list(result.keys()))
        
        # Check for refactoring results
        if "refactoring_results" in result:
            refactoring_results = result["refactoring_results"]
            logging.info(f"Refactoring results type: {type(refactoring_results)}")
            logging.info(f"Refactoring results length: {len(refactoring_results) if isinstance(refactoring_results, list) else 'Not a list'}")
            
            if isinstance(refactoring_results, list) and refactoring_results:
                for i, item in enumerate(refactoring_results):
                    logging.info(f"\nRefactoring result {i+1}:")
                    logging.info(f"  Type: {type(item)}")
                    if isinstance(item, dict):
                        logging.info(f"  Keys: {list(item.keys())}")
                        
                        # Look for code
                        for key in item.keys():
                            if 'code' in key.lower():
                                value = item[key]
                                logging.info(f"  {key}: {type(value)} - {str(value)[:100] if value else 'None'}...")
                    else:
                        logging.info(f"  Dir: {[attr for attr in dir(item) if not attr.startswith('_')]}")
                        
                        # Check for code attributes
                        for attr in dir(item):
                            if 'code' in attr.lower() and not attr.startswith('_'):
                                value = getattr(item, attr)
                                logging.info(f"  {attr}: {type(value)} - {str(value)[:100] if value else 'None'}...")
        
        # Check for detections
        if "detections" in result:
            detections = result["detections"]
            logging.info(f"Detections type: {type(detections)}")
            logging.info(f"Detections length: {len(detections) if isinstance(detections, list) else 'Not a list'}")
            
            if isinstance(detections, list) and detections:
                for i, detection in enumerate(detections):
                    logging.info(f"\nDetection {i+1}:")
                    logging.info(f"  Type: {type(detection)}")
                    if isinstance(detection, dict):
                        logging.info(f"  Keys: {list(detection.keys())}")
                        
                        # Check for refactored_modules
                        if "refactored_modules" in detection:
                            modules = detection["refactored_modules"]
                            logging.info(f"  Refactored modules: {type(modules)}")
                            if isinstance(modules, dict):
                                logging.info(f"  Module keys: {list(modules.keys())}")
                                for key, value in modules.items():
                                    logging.info(f"    {key}: {type(value)} - {str(value)[:100] if isinstance(value, str) else 'Non-string'}...")
    
    return result

if __name__ == "__main__":
    print("🧪 DEBUGGING AGENT RESULTS STRUCTURE")
    logging.info("="*60)
    
    # Debug IntelligentCodeAgent
    try:
        intelligent_result = debug_intelligent_code_agent()
    except Exception as e:
        print(f"Error debugging IntelligentCodeAgent: {e}")
    
    # Debug GodCodeAgent  
    try:
        god_code_result = debug_god_code_agent()
    except Exception as e:
        print(f"Error debugging GodCodeAgent: {e}")
    
    print("\n✅ Debug complete!")