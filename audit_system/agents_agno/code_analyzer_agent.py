#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Code Analyzer Agent - Agno-native intelligent code analysis.

This agent provides deep code analysis capabilities using Agno's LLM integration
for semantic understanding of code structure, patterns, and quality.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from textwrap import dedent

try:
    from agno.agent import Agent
    from agno.models.openai import OpenAIChat
    AGNO_AVAILABLE = True
except ImportError:
    AGNO_AVAILABLE = False
    Agent = None
    OpenAIChat = None

# Import our analysis tools
try:
    from ..tools.complexity_analyzer_tool import ComplexityAnalyzerTool
    COMPLEXITY_TOOL_AVAILABLE = True
except ImportError:
    COMPLEXITY_TOOL_AVAILABLE = False
    ComplexityAnalyzerTool = None

try:
    from ..tools.pattern_detector_tool import PatternDetectorTool
    PATTERN_TOOL_AVAILABLE = True
except ImportError:
    PATTERN_TOOL_AVAILABLE = False
    PatternDetectorTool = None

try:
    from ..tools.dependency_analyzer_tool import DependencyAnalyzerTool
    DEPENDENCY_TOOL_AVAILABLE = True
except ImportError:
    DEPENDENCY_TOOL_AVAILABLE = False
    DependencyAnalyzerTool = None

try:
    from ..tools.method_analyzer_tool import MethodAnalyzerTool
    METHOD_TOOL_AVAILABLE = True
except ImportError:
    METHOD_TOOL_AVAILABLE = False
    MethodAnalyzerTool = None

class CodeAnalyzerAgent:
    """
    Agno-native agent for deep code analysis.
    
    This agent specializes in:
    - Complexity analysis and hotspot detection
    - Code smell and anti-pattern identification
    - Architectural analysis and recommendations
    - Performance bottleneck identification
    - Security vulnerability detection
    """
    
    def __init__(
        self, 
        model_id: str = "gpt-4o",
        temperature: float = 0.1,
        max_tokens: int = 4000
    ):
        self.logger = logging.getLogger(f"{__name__}.CodeAnalyzerAgent")
        
        if not AGNO_AVAILABLE:
            raise ImportError("Agno is required for CodeAnalyzerAgent. Install with: pip install agno")
        
        # Initialize tools
        self.tools = []
        
        if COMPLEXITY_TOOL_AVAILABLE:
            self.tools.append(ComplexityAnalyzerTool())
        if PATTERN_TOOL_AVAILABLE:
            self.tools.append(PatternDetectorTool())
        if DEPENDENCY_TOOL_AVAILABLE:
            self.tools.append(DependencyAnalyzerTool())
        if METHOD_TOOL_AVAILABLE:
            self.tools.append(MethodAnalyzerTool())
        
        # Create Agno agent
        self.agent = Agent(
            name="Code Analyzer",
            role="Deep code analysis specialist",
            model=OpenAIChat(id=model_id, temperature=temperature, max_tokens=max_tokens),
            tools=self.tools,
            instructions=dedent("""\
                You are an expert code analyst with deep understanding of software architecture,
                design patterns, and code quality principles. Your role is to provide comprehensive
                analysis of Python code with actionable insights.
                
                ANALYSIS FOCUS AREAS:
                1. COMPLEXITY ANALYSIS:
                   - Identify methods/functions with high cyclomatic complexity
                   - Detect cognitive complexity hotspots
                   - Flag deeply nested code structures
                   - Measure maintainability index
                
                2. CODE SMELLS & ANTI-PATTERNS:
                   - God classes and god methods
                   - Code duplication and repetition
                   - Long parameter lists
                   - Feature envy and inappropriate intimacy
                   - Dead code and unused variables
                   - Magic numbers and strings
                
                3. ARCHITECTURAL ANALYSIS:
                   - Single Responsibility Principle violations
                   - Tight coupling indicators
                   - Missing abstraction opportunities
                   - Layer violations and circular dependencies
                   - Interface segregation issues
                
                4. PERFORMANCE CONCERNS:
                   - Inefficient algorithms and data structures
                   - N+1 query patterns
                   - Memory usage inefficiencies
                   - String concatenation in loops
                   - Unnecessary object creation
                
                5. SECURITY VULNERABILITIES:
                   - SQL injection opportunities
                   - Input validation issues
                   - Hardcoded secrets
                   - Unsafe serialization patterns
                   - Path traversal vulnerabilities
                
                ANALYSIS METHODOLOGY:
                1. Use available tools to gather quantitative metrics
                2. Perform semantic analysis of code intent and structure
                3. Identify patterns both positive and negative
                4. Prioritize issues by severity and impact
                5. Provide specific, actionable recommendations
                
                OUTPUT FORMAT:
                Provide analysis in this structure:
                - Executive Summary (2-3 sentences)
                - Critical Issues (high priority items)
                - Code Quality Metrics (quantitative measures)
                - Refactoring Opportunities (specific suggestions)
                - Security Concerns (if any)
                - Performance Optimizations (if applicable)
                - Architectural Recommendations (strategic improvements)
                
                TONE: Professional, constructive, and actionable. Focus on improvements
                rather than criticism. Provide specific examples and clear next steps.
            """),
            show_tool_calls=True,
            markdown=True,
            add_datetime_to_instructions=True
        )
        
        self.logger.info(f"CodeAnalyzerAgent initialized with {len(self.tools)} tools")
    
    def analyze_file(self, file_path: str, file_content: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze a single Python file for code quality and refactoring opportunities.
        
        Args:
            file_path: Path to the Python file
            file_content: Optional file content (if not provided, will read from file_path)
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            # Read file content if not provided
            if file_content is None:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
            
            # Prepare analysis prompt
            analysis_prompt = f"""
            Analyze the following Python file for code quality, refactoring opportunities,
            and potential improvements. Use all available tools to provide comprehensive analysis.
            
            FILE: {file_path}
            
            CODE:
            ```python
            {file_content}
            ```
            
            Please provide a detailed analysis covering:
            1. Code complexity and quality metrics
            2. Specific refactoring opportunities with line numbers
            3. Security and performance concerns
            4. Architectural recommendations
            5. Priority ranking of identified issues
            
            Focus on actionable insights that will improve code maintainability,
            readability, and performance.
            """
            
            # Get analysis from agent
            response = self.agent.run(analysis_prompt)
            
            # Parse and structure the response
            return {
                "success": True,
                "file_path": file_path,
                "analysis": response.content,
                "tool_calls": getattr(response, 'tool_calls', []),
                "tokens_used": getattr(response, 'tokens', {}).get('total', 0),
                "model_used": self.agent.model.id
            }
            
        except FileNotFoundError:
            self.logger.error(f"File not found: {file_path}")
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "file_path": file_path
            }
        except Exception as e:
            self.logger.error(f"Analysis failed for {file_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path
            }
    
    def analyze_multiple_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Analyze multiple Python files and provide consolidated insights.
        
        Args:
            file_paths: List of Python file paths to analyze
            
        Returns:
            Dictionary containing consolidated analysis results
        """
        individual_analyses = []
        failed_analyses = []
        
        # Analyze each file
        for file_path in file_paths:
            result = self.analyze_file(file_path)
            if result["success"]:
                individual_analyses.append(result)
            else:
                failed_analyses.append(result)
        
        if not individual_analyses:
            return {
                "success": False,
                "error": "No files could be analyzed successfully",
                "failed_files": failed_analyses
            }
        
        # Create consolidated analysis prompt
        files_summary = "\n".join([
            f"- {analysis['file_path']}: Analysis completed"
            for analysis in individual_analyses
        ])
        
        consolidation_prompt = f"""
        I have analyzed {len(individual_analyses)} Python files individually. 
        Now please provide a consolidated analysis that identifies:
        
        FILES ANALYZED:
        {files_summary}
        
        CONSOLIDATION REQUIREMENTS:
        1. CROSS-FILE PATTERNS: Identify patterns that appear across multiple files
        2. ARCHITECTURAL INSIGHTS: Overall system architecture observations
        3. PRIORITY MATRIX: Rank issues by impact and effort required
        4. REFACTORING STRATEGY: Suggest order of refactoring activities
        5. SYSTEM-WIDE RECOMMENDATIONS: Improvements that affect multiple files
        
        Please synthesize the individual file analyses into strategic recommendations
        for improving the overall codebase quality.
        """
        
        try:
            consolidated_response = self.agent.run(consolidation_prompt)
            
            return {
                "success": True,
                "files_analyzed": len(individual_analyses),
                "individual_analyses": individual_analyses,
                "failed_analyses": failed_analyses,
                "consolidated_analysis": consolidated_response.content,
                "total_tokens_used": sum(
                    analysis.get("tokens_used", 0) 
                    for analysis in individual_analyses
                ) + getattr(consolidated_response, 'tokens', {}).get('total', 0)
            }
            
        except Exception as e:
            self.logger.error(f"Consolidation failed: {e}")
            return {
                "success": False,
                "error": f"Consolidation failed: {e}",
                "individual_analyses": individual_analyses,
                "failed_analyses": failed_analyses
            }
    
    def analyze_project_directory(self, project_path: str, max_files: int = 20) -> Dict[str, Any]:
        """
        Analyze all Python files in a project directory.
        
        Args:
            project_path: Path to the project root directory
            max_files: Maximum number of files to analyze (to avoid overwhelming the LLM)
            
        Returns:
            Dictionary containing project-wide analysis results
        """
        try:
            project_dir = Path(project_path)
            if not project_dir.exists():
                return {
                    "success": False,
                    "error": f"Project directory not found: {project_path}"
                }
            
            # Find Python files
            python_files = list(project_dir.rglob("*.py"))
            
            # Filter out common directories to ignore
            ignored_patterns = {
                "__pycache__", ".git", ".pytest_cache", ".mypy_cache",
                "venv", "env", ".venv", ".env", "node_modules"
            }
            
            filtered_files = []
            for file_path in python_files:
                # Check if any parent directory should be ignored
                if not any(pattern in file_path.parts for pattern in ignored_patterns):
                    filtered_files.append(str(file_path))
            
            # Limit number of files
            if len(filtered_files) > max_files:
                self.logger.warning(
                    f"Found {len(filtered_files)} Python files, analyzing first {max_files}"
                )
                filtered_files = filtered_files[:max_files]
            
            self.logger.info(f"Analyzing {len(filtered_files)} Python files in {project_path}")
            
            # Analyze multiple files
            return self.analyze_multiple_files(filtered_files)
            
        except Exception as e:
            self.logger.error(f"Project analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "project_path": project_path
            }
    
    def get_refactoring_recommendations(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract specific refactoring recommendations from analysis results.
        
        Args:
            analysis_result: Result from analyze_file or analyze_multiple_files
            
        Returns:
            Dictionary containing structured refactoring recommendations
        """
        if not analysis_result.get("success"):
            return {
                "success": False,
                "error": "Cannot extract recommendations from failed analysis"
            }
        
        extraction_prompt = """
        Based on the code analysis provided, extract specific, actionable refactoring
        recommendations in a structured format. For each recommendation, provide:
        
        1. PRIORITY (Critical, High, Medium, Low)
        2. TYPE (extract_method, improve_exceptions, optimize_strings, etc.)
        3. LOCATION (file path and line numbers if available)
        4. DESCRIPTION (what needs to be refactored)
        5. BENEFIT (why this refactoring is valuable)
        6. EFFORT (estimated complexity: Simple, Moderate, Complex)
        
        Format as a numbered list of recommendations, prioritized by impact and feasibility.
        Focus on refactorings that can be automated or semi-automated.
        """
        
        try:
            response = self.agent.run(extraction_prompt)
            
            return {
                "success": True,
                "recommendations": response.content,
                "source_analysis": analysis_result,
                "tokens_used": getattr(response, 'tokens', {}).get('total', 0)
            }
            
        except Exception as e:
            self.logger.error(f"Recommendation extraction failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "source_analysis": analysis_result
            }

# Fallback class for when Agno is not available
class MockCodeAnalyzerAgent:
    """Mock agent for when Agno is not available."""
    
    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(f"{__name__}.MockCodeAnalyzerAgent")
        self.logger.warning("Using mock agent - Agno not available")
    
    def analyze_file(self, file_path: str, file_content: Optional[str] = None) -> Dict[str, Any]:
        return {
            "success": False,
            "error": "Agno not available - using mock agent",
            "file_path": file_path
        }
    
    def analyze_multiple_files(self, file_paths: List[str]) -> Dict[str, Any]:
        return {
            "success": False,
            "error": "Agno not available - using mock agent",
            "files": file_paths
        }
    
    def analyze_project_directory(self, project_path: str, max_files: int = 20) -> Dict[str, Any]:
        return {
            "success": False,
            "error": "Agno not available - using mock agent",
            "project_path": project_path
        }
    
    def get_refactoring_recommendations(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "success": False,
            "error": "Agno not available - using mock agent"
        }

# Export the appropriate class based on Agno availability
if AGNO_AVAILABLE:
    __all__ = ["CodeAnalyzerAgent"]
else:
    CodeAnalyzerAgent = MockCodeAnalyzerAgent
    __all__ = ["CodeAnalyzerAgent"]