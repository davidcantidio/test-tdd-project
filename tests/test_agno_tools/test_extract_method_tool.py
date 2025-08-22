#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test ExtractMethodTool - Validation of Agno-native method extraction.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from audit_system.tools.extract_method_tool import ExtractMethodTool

class TestExtractMethodTool:
    """Test suite for ExtractMethodTool."""
    
    def setup_method(self):
        """Setup test method."""
        self.tool = ExtractMethodTool()
    
    def test_tool_initialization(self):
        """Test tool initializes correctly."""
        assert self.tool.name == "extract_method"
        assert "extract" in self.tool.description.lower()
        assert self.tool.min_method_lines == 15
    
    def test_analyze_simple_short_method(self):
        """Test analysis of short method (should find no targets)."""
        code = '''
def simple_method():
    """A simple short method."""
    return "hello world"
'''
        result = self.tool.analyze_code(code)
        
        assert isinstance(result, dict)
        assert result.get("tool_name") == "extract_method"
        assert len(result.get("targets", [])) == 0  # Too short for extraction
    
    def test_analyze_long_method(self):
        """Test analysis of long method (should find targets)."""
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
        
        result = self.tool.analyze_code(code)
        
        assert isinstance(result, dict)
        assert result.get("tool_name") == "extract_method"
        assert "targets" in result
        
        # Should find extraction opportunities
        targets = result.get("targets", [])
        assert len(targets) > 0, "Should find extraction targets in long method"
        
        # Check target structure
        for target in targets:
            assert "start_line" in target
            assert "end_line" in target
            assert "target_type" in target
            assert target["target_type"] == "method_extraction"
            assert "confidence" in target
            assert 0 <= target["confidence"] <= 1
    
    def test_apply_refactoring_basic(self):
        """Test basic refactoring application."""
        code = '''
def test_method():
    # Block 1
    x = 1
    y = 2
    z = x + y
    
    # Block 2  
    a = 4
    b = 5
    c = a + b
    
    # Block 3
    result = z + c
    print(f"Result: {result}")
    return result
'''
        
        # First analyze to get targets
        analysis = self.tool.analyze_code(code)
        targets = analysis.get("targets", [])
        
        if targets:
            # Apply refactoring to first target
            refactoring_result = self.tool.apply_refactoring(code, [0])
            
            assert isinstance(refactoring_result, dict)
            assert "success" in refactoring_result
            assert "original_code" in refactoring_result
            assert "refactored_code" in refactoring_result
            
            # If successful, refactored code should be different
            if refactoring_result["success"]:
                assert refactoring_result["refactored_code"] != refactoring_result["original_code"]
    
    def test_complexity_calculation(self):
        """Test complexity calculation methods."""
        code = '''
def complex_method(x):
    if x > 0:
        for i in range(x):
            if i % 2 == 0:
                try:
                    result = i * 2
                    if result > 10:
                        return result
                except ValueError:
                    continue
    return 0
'''
        
        import ast
        tree = ast.parse(code)
        func_node = None
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_node = node
                break
        
        assert func_node is not None
        
        # Test cyclomatic complexity calculation
        complexity = self.tool._calculate_cyclomatic_complexity(func_node)
        assert complexity > 1, "Should detect complexity in nested control structures"
        
        # Test cognitive complexity calculation  
        cognitive = self.tool._calculate_cognitive_complexity(func_node)
        assert cognitive > complexity, "Cognitive complexity should be higher than cyclomatic"
    
    def test_variable_analysis(self):
        """Test variable usage analysis."""
        code = '''
def method_with_variables(param1, param2):
    local_var = param1 + param2
    result = local_var * 2
    return result
'''
        
        import ast
        tree = ast.parse(code)
        func_node = None
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_node = node
                break
        
        assert func_node is not None
        
        variables_used, variables_defined = self.tool._analyze_variables(func_node)
        
        # Should detect local variables
        assert "local_var" in variables_defined
        assert "result" in variables_defined
        
        # Parameters should not be in variables_used (they're defined)
        assert "param1" not in variables_used
        assert "param2" not in variables_used
    
    def test_error_handling(self):
        """Test error handling for invalid code."""
        # Test with syntax error
        invalid_code = '''
def broken_method(
    # Missing closing parenthesis and body
'''
        
        result = self.tool.analyze_code(invalid_code)
        
        assert isinstance(result, dict)
        assert "error" in result
        assert not result.get("success", True)
    
    def test_empty_code(self):
        """Test handling of empty code."""
        result = self.tool.analyze_code("")
        
        assert isinstance(result, dict)
        # Should handle gracefully, either with error or empty targets
        assert "targets" in result or "error" in result

if __name__ == "__main__":
    pytest.main([__file__, "-v"])