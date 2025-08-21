#!/usr/bin/env python3
"""
🧪 Test single file optimization application

Simple test to validate that optimization application works.
"""

import sys
import json
from pathlib import Path

# Add audit_system to Python path
sys.path.append('.')

try:
    from audit_system.agents.intelligent_code_agent import IntelligentCodeAgent, AnalysisDepth, SemanticMode
    
    # Load audit results
    audit_file = Path('.audit_intelligent/intelligent_analysis.json')
    with open(audit_file) as f:
        audit_data = json.load(f)
    
    # Find a file with recommendations (any size)
    results = audit_data.get('results', [])
    files_with_optimizations = [r for r in results if r.get('recommended_refactorings_count', 0) > 0]
    
    # Sort by fewest optimizations first (easier to test)
    files_with_optimizations.sort(key=lambda x: x.get('recommended_refactorings_count', 0))
    
    if not files_with_optimizations:
        print("❌ No files with optimizations found")
        sys.exit(1)
    
    # Take the first file with fewest optimizations
    test_file = files_with_optimizations[0]
    file_path = test_file['file_path']
    refactoring_count = test_file['recommended_refactorings_count']
    
    print(f"🧪 Testing optimization on: {file_path}")
    print(f"   🔧 {refactoring_count} optimizations available")
    print(f"   📊 Lines: {test_file.get('lines_analyzed', 'unknown')}")
    
    # Initialize agent for REAL application testing
    agent = IntelligentCodeAgent(
        project_root=Path('.'),
        enable_real_llm=True,
        analysis_depth=AnalysisDepth.DEEP,
        semantic_mode=SemanticMode.AGGRESSIVE,
        dry_run=False  # Enable REAL application mode
    )
    
    # Re-analyze to get current recommendations
    print("🔍 Re-analyzing file...")
    analysis = agent.analyze_file_intelligently(file_path)
    
    print(f"✅ Analysis complete:")
    print(f"   🔧 {len(analysis.recommended_refactorings)} refactorings found")
    print(f"   📊 Quality score: {analysis.semantic_quality_score:.1f}")
    
    if analysis.recommended_refactorings:
        print(f"\n📋 Recommended refactorings:")
        for i, refactoring in enumerate(analysis.recommended_refactorings[:3], 1):
            print(f"   {i}. {refactoring.refactoring_type}: {refactoring.description}")
            print(f"      Confidence: {refactoring.confidence_score:.0%}")
        
        # Test the apply function (REAL mode set in constructor)
        print(f"\n🧪 Testing REAL apply function...")
        result = agent.apply_intelligent_refactorings(analysis)
        print(f"✅ Apply function result: {result}")
        print(f"   📊 Result type: {type(result)}")
        if isinstance(result, dict):
            for key, value in result.items():
                print(f"   📋 {key}: {value}")
        elif hasattr(result, '__dict__'):
            print(f"   📋 Result attributes: {result.__dict__}")
    else:
        print("ℹ️ No refactorings available for this file")

except Exception as e:
    print(f"❌ Error during test: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("🎉 Single optimization test completed successfully!")