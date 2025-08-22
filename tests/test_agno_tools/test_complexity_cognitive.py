#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast
import textwrap
import sys
from pathlib import Path

# Ensure project root is on sys.path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from audit_system.tools.complexity_analyzer_tool import ComplexityAnalyzerTool

def test_cognitive_complexity_counts_top_level_branches_independently():
    code = textwrap.dedent(
        '''
        def sample(x):
            if x > 0:
                pass
            if x < 0:
                pass
            return x
        '''
    )
    tree = ast.parse(code)
    func = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
    tool = ComplexityAnalyzerTool()
    assert tool._calculate_cognitive_complexity(func) == 2
