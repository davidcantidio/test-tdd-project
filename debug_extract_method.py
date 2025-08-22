#!/usr/bin/env python3
"""Debug script for ExtractMethodTool."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from audit_system.tools.extract_method_tool import ExtractMethodTool

def main():
    """Debug ExtractMethodTool analysis."""
    tool = ExtractMethodTool()
    
    # Test code from the test file
    code = '''
def long_complex_method(data):
    """A long method that should be extracted."""
    # Data validation block
    if not data:
        raise ValueError("Data cannot be empty")
    if not isinstance(data, dict):
        raise TypeError("Data must be a dictionary")
    if "id" not in data:
        raise KeyError("Data must have an id field")
    
    # Processing block
    processed_data = {}
    for key, value in data.items():
        if isinstance(value, str):
            processed_data[key] = value.strip().lower()
        elif isinstance(value, int):
            processed_data[key] = value * 2
        elif isinstance(value, list):
            processed_data[key] = [item for item in value if item is not None]
    
    # Result formatting block
    result = {
        "id": processed_data.get("id"),
        "data": processed_data,
        "timestamp": "2024-01-01",
        "status": "processed"
    }
    
    # Logging block
    print(f"Processed data for ID: {result['id']}")
    print(f"Result status: {result['status']}")
    
    return result
'''
    
    print("🔍 Analyzing code...")
    print(f"Code length: {len(code.splitlines())} lines")
    print(f"Tool min_method_lines: {tool.min_method_lines}")
    
    import ast
    tree = ast.parse(code)
    
    # Find the function
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            print(f"Function found: {node.name}")
            print(f"Start line: {node.lineno}")
            print(f"End line: {getattr(node, 'end_lineno', 'unknown')}")
            
            # Check method analysis
            source_lines = code.splitlines()
            method_analysis = tool._analyze_method(node, source_lines)
            print(f"Method analysis:")
            print(f"  Line count: {method_analysis.line_count}")
            print(f"  Complexity: {method_analysis.complexity}")
            print(f"  Variables used: {method_analysis.variables_used}")
            print(f"  Variables defined: {method_analysis.variables_defined}")
            
            # Check if meets criteria
            meets_criteria = method_analysis.line_count >= tool.min_method_lines
            print(f"  Meets line criteria: {meets_criteria}")
            
            if meets_criteria:
                print("  Finding extractable blocks...")
                extractable_blocks = tool._find_extractable_blocks(method_analysis, source_lines)
                print(f"  Found {len(extractable_blocks)} extractable blocks")
                
                for i, block in enumerate(extractable_blocks):
                    print(f"    Block {i+1}:")
                    print(f"      Lines: {block.start_line}-{block.end_line}")
                    print(f"      Confidence: {block.confidence}")
                    print(f"      Description: {block.description}")
    
    # Run the full analysis
    print("\n🎯 Running full analysis...")
    result = tool.analyze_code(code)
    print(f"Analysis result:")
    print(f"  Success: {result.get('success', 'unknown')}")
    print(f"  Targets found: {result.get('targets_found', 0)}")
    print(f"  High confidence targets: {result.get('high_confidence_targets', 0)}")
    
    if 'error' in result:
        print(f"  Error: {result['error']}")
    
    targets = result.get('targets', [])
    for i, target in enumerate(targets):
        print(f"  Target {i+1}:")
        print(f"    Type: {target.get('target_type')}")
        print(f"    Lines: {target.get('start_line')}-{target.get('end_line')}")
        print(f"    Confidence: {target.get('confidence')}")
        print(f"    Description: {target.get('description')}")

if __name__ == "__main__":
    main()