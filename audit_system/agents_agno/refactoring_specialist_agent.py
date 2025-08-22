#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Refactoring Specialist Agent - Agno-native semantic-aware refactoring.

This agent applies intelligent refactorings using LLM guidance and specialized tools.
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

# Import our refactoring tools
try:
    from ..tools.extract_method_tool import ExtractMethodTool
    EXTRACT_METHOD_AVAILABLE = True
except ImportError:
    EXTRACT_METHOD_AVAILABLE = False
    ExtractMethodTool = None

try:
    from ..tools.complexity_analyzer_tool import ComplexityAnalyzerTool
    COMPLEXITY_TOOL_AVAILABLE = True
except ImportError:
    COMPLEXITY_TOOL_AVAILABLE = False
    ComplexityAnalyzerTool = None

class RefactoringSpecialistAgent:
    """
    Agno-native agent for applying intelligent refactorings.
    
    This agent specializes in:
    - Method extraction with semantic understanding
    - Complexity reduction strategies
    - Code smell elimination
    - Safe transformation application
    - Refactoring validation and rollback
    """
    
    def __init__(
        self, 
        model_id: str = "gpt-4o",
        temperature: float = 0.1,
        max_tokens: int = 4000
    ):
        self.logger = logging.getLogger(f"{__name__}.RefactoringSpecialistAgent")
        
        if not AGNO_AVAILABLE:
            raise ImportError("Agno is required for RefactoringSpecialistAgent. Install with: pip install agno")
        
        # Initialize tools
        self.tools = []
        
        if EXTRACT_METHOD_AVAILABLE:
            self.tools.append(ExtractMethodTool())
        if COMPLEXITY_TOOL_AVAILABLE:
            self.tools.append(ComplexityAnalyzerTool())
        
        # Create Agno agent
        self.agent = Agent(
            name="Refactoring Specialist",
            role="Semantic-aware code refactoring expert",
            model=OpenAIChat(id=model_id, temperature=temperature, max_tokens=max_tokens),
            tools=self.tools,
            instructions=dedent("""\
                You are an expert refactoring specialist with deep understanding of code quality,
                design patterns, and safe transformation techniques. Your role is to apply
                intelligent refactorings that improve code quality while preserving functionality.
                
                REFACTORING PRINCIPLES:
                1. SAFETY FIRST:
                   - Always preserve functionality
                   - Maintain existing interfaces when possible
                   - Ensure test compatibility
                   - Create incremental, reversible changes
                
                2. SEMANTIC UNDERSTANDING:
                   - Understand the code's intent and purpose
                   - Respect existing architectural patterns
                   - Maintain code cohesion and coupling balance
                   - Consider performance implications
                
                3. QUALITY IMPROVEMENT:
                   - Reduce complexity while maintaining readability
                   - Extract logical cohesive blocks into methods
                   - Follow Single Responsibility Principle
                   - Improve naming and documentation
                
                4. PRIORITIZATION STRATEGY:
                   - Address high-complexity issues first
                   - Focus on frequently modified code
                   - Consider maintenance burden vs. improvement benefit
                   - Prefer simple, obvious improvements over complex ones
                
                REFACTORING TECHNIQUES:
                1. METHOD EXTRACTION:
                   - Extract logical blocks that have clear purpose
                   - Minimize parameter passing
                   - Choose descriptive method names
                   - Maintain proper abstraction levels
                
                2. COMPLEXITY REDUCTION:
                   - Break down complex conditional logic
                   - Reduce nesting through early returns
                   - Simplify boolean expressions
                   - Extract guard clauses
                
                3. VARIABLE MANAGEMENT:
                   - Extract magic numbers to named constants
                   - Improve variable naming
                   - Reduce variable scope when possible
                   - Eliminate dead code and unused variables
                
                4. STRUCTURE IMPROVEMENT:
                   - Group related functionality
                   - Separate concerns appropriately
                   - Improve error handling patterns
                   - Optimize imports and dependencies
                
                REFACTORING WORKFLOW:
                1. ANALYSIS: Use available tools to identify refactoring opportunities
                2. PLANNING: Prioritize refactorings by impact and safety
                3. APPLICATION: Apply refactorings incrementally with validation
                4. VERIFICATION: Ensure changes preserve functionality and improve quality
                
                OUTPUT FORMAT:
                For each refactoring provide:
                - Rationale: Why this refactoring improves the code
                - Approach: How the refactoring will be applied
                - Benefits: Expected improvements in quality metrics
                - Risks: Potential issues and mitigation strategies
                - Validation: How to verify the refactoring succeeded
                
                TONE: Professional, methodical, and safety-focused. Always explain
                the reasoning behind refactoring decisions and provide clear steps.
            """),
            show_tool_calls=True,
            markdown=True,
            add_datetime_to_instructions=True
        )
        
        self.logger.info(f"RefactoringSpecialistAgent initialized with {len(self.tools)} tools")
    
    def refactor_file(
        self, 
        file_path: str, 
        file_content: Optional[str] = None,
        target_refactorings: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Apply intelligent refactorings to a Python file.
        
        Args:
            file_path: Path to the Python file
            file_content: Optional file content (if not provided, will read from file_path)
            target_refactorings: Optional list of specific refactoring types to apply
            
        Returns:
            Dictionary containing refactoring results
        """
        try:
            # Read file content if not provided
            if file_content is None:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
            
            # Build refactoring constraints
            constraints = ""
            if target_refactorings:
                constraints = f"\nFOCUS ON: {', '.join(target_refactorings)} refactorings only."
            
            # Prepare refactoring prompt
            refactoring_prompt = f"""
            Apply intelligent refactorings to improve the quality of this Python file.
            Use all available tools to analyze the code and identify improvement opportunities.
            
            FILE: {file_path}
            {constraints}
            
            CODE TO REFACTOR:
            ```python
            {file_content}
            ```
            
            REQUIREMENTS:
            1. Analyze the code using available tools to identify specific issues
            2. Prioritize refactorings by impact and safety
            3. Apply the most beneficial refactorings first
            4. Provide detailed explanations for each refactoring
            5. Show before/after code examples
            6. Ensure all changes preserve functionality
            
            DELIVERABLES:
            1. Analysis summary of identified issues
            2. Prioritized refactoring plan
            3. Applied refactorings with explanations
            4. Validation checklist for each change
            5. Overall improvement metrics
            
            Focus on practical, safe improvements that will make the code
            more maintainable and easier to understand.
            """
            
            # Get refactoring from agent
            response = self.agent.run(refactoring_prompt)
            
            # Parse and structure the response
            return {
                "success": True,
                "file_path": file_path,
                "original_content": file_content,
                "refactoring_analysis": response.content,
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
            self.logger.error(f"Refactoring failed for {file_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path
            }
    
    def apply_specific_refactoring(
        self, 
        file_content: str,
        refactoring_type: str,
        target_lines: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Apply a specific type of refactoring to code content.
        
        Args:
            file_content: Python code content to refactor
            refactoring_type: Specific refactoring to apply (e.g., "extract_method")
            target_lines: Optional specific lines to target
            
        Returns:
            Dictionary containing refactoring results
        """
        try:
            # Build targeting information
            target_info = ""
            if target_lines:
                target_info = f"\nTARGET LINES: {target_lines}"
            
            # Prepare specific refactoring prompt
            refactoring_prompt = f"""
            Apply a specific {refactoring_type} refactoring to this code.
            Use the appropriate tool to analyze and apply this refactoring safely.
            {target_info}
            
            CODE:
            ```python
            {file_content}
            ```
            
            INSTRUCTIONS:
            1. Use the {refactoring_type} tool to analyze the code
            2. Identify the best opportunities for this refactoring
            3. Apply the refactoring with proper explanation
            4. Provide before/after comparison
            5. Validate that functionality is preserved
            
            Show the specific improvements made and why they benefit code quality.
            """
            
            # Get refactoring from agent
            response = self.agent.run(refactoring_prompt)
            
            return {
                "success": True,
                "refactoring_type": refactoring_type,
                "original_content": file_content,
                "refactoring_result": response.content,
                "tool_calls": getattr(response, 'tool_calls', []),
                "tokens_used": getattr(response, 'tokens', {}).get('total', 0)
            }
            
        except Exception as e:
            self.logger.error(f"Specific refactoring failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "refactoring_type": refactoring_type
            }
    
    def get_refactoring_recommendations(
        self, 
        file_content: str,
        max_recommendations: int = 5
    ) -> Dict[str, Any]:
        """
        Get prioritized refactoring recommendations without applying them.
        
        Args:
            file_content: Python code content to analyze
            max_recommendations: Maximum number of recommendations to return
            
        Returns:
            Dictionary containing prioritized refactoring recommendations
        """
        try:
            recommendation_prompt = f"""
            Analyze this code and provide prioritized refactoring recommendations.
            Use available tools to identify issues and rank them by impact and feasibility.
            
            CODE:
            ```python
            {file_content}
            ```
            
            ANALYSIS REQUIREMENTS:
            1. Use all available tools to analyze the code thoroughly
            2. Identify specific issues with line numbers
            3. Rank recommendations by priority (Critical, High, Medium, Low)
            4. Consider effort vs. benefit for each recommendation
            5. Provide clear descriptions of what needs to be refactored
            
            DELIVERABLES:
            Top {max_recommendations} recommendations in this format:
            1. [PRIORITY] Refactoring Type: Description
               - Lines affected: X-Y
               - Benefit: What this improves
               - Effort: Low/Medium/High
               - Risk: Low/Medium/High
            
            Focus on actionable, specific recommendations that will have
            measurable impact on code quality.
            """
            
            # Get recommendations from agent
            response = self.agent.run(recommendation_prompt)
            
            return {
                "success": True,
                "recommendations": response.content,
                "tool_calls": getattr(response, 'tool_calls', []),
                "tokens_used": getattr(response, 'tokens', {}).get('total', 0),
                "max_requested": max_recommendations
            }
            
        except Exception as e:
            self.logger.error(f"Recommendation generation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def validate_refactoring(
        self, 
        original_code: str, 
        refactored_code: str
    ) -> Dict[str, Any]:
        """
        Validate that a refactoring preserves functionality and improves quality.
        
        Args:
            original_code: Original code before refactoring
            refactored_code: Code after refactoring
            
        Returns:
            Dictionary containing validation results
        """
        try:
            validation_prompt = f"""
            Validate that this refactoring preserves functionality and improves code quality.
            Compare the original and refactored code to ensure correctness.
            
            ORIGINAL CODE:
            ```python
            {original_code}
            ```
            
            REFACTORED CODE:
            ```python
            {refactored_code}
            ```
            
            VALIDATION CHECKLIST:
            1. FUNCTIONALITY PRESERVATION:
               - Same input/output behavior
               - No changes to public interfaces
               - Equivalent logic flow
               - No semantic changes
            
            2. QUALITY IMPROVEMENTS:
               - Reduced complexity
               - Better readability
               - Improved maintainability
               - Follows best practices
            
            3. POTENTIAL ISSUES:
               - Performance impacts
               - Breaking changes
               - Test compatibility
               - Documentation needs
            
            VERDICT: Provide APPROVED/REJECTED with detailed reasoning.
            If approved, list the specific improvements made.
            If rejected, explain what needs to be fixed.
            """
            
            # Get validation from agent
            response = self.agent.run(validation_prompt)
            
            # Parse verdict from response
            response_text = response.content.lower()
            approved = "approved" in response_text and "rejected" not in response_text
            
            return {
                "success": True,
                "approved": approved,
                "validation_analysis": response.content,
                "tokens_used": getattr(response, 'tokens', {}).get('total', 0)
            }
            
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Fallback class for when Agno is not available
class MockRefactoringSpecialistAgent:
    """Mock agent for when Agno is not available."""
    
    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(f"{__name__}.MockRefactoringSpecialistAgent")
        self.logger.warning("Using mock agent - Agno not available")
    
    def refactor_file(self, file_path: str, file_content: Optional[str] = None, target_refactorings: Optional[List[str]] = None) -> Dict[str, Any]:
        return {
            "success": False,
            "error": "Agno not available - using mock agent",
            "file_path": file_path
        }
    
    def apply_specific_refactoring(self, file_content: str, refactoring_type: str, target_lines: Optional[List[int]] = None) -> Dict[str, Any]:
        return {
            "success": False,
            "error": "Agno not available - using mock agent",
            "refactoring_type": refactoring_type
        }
    
    def get_refactoring_recommendations(self, file_content: str, max_recommendations: int = 5) -> Dict[str, Any]:
        return {
            "success": False,
            "error": "Agno not available - using mock agent"
        }
    
    def validate_refactoring(self, original_code: str, refactored_code: str) -> Dict[str, Any]:
        return {
            "success": False,
            "error": "Agno not available - using mock agent"
        }

# Export the appropriate class based on Agno availability
if AGNO_AVAILABLE:
    __all__ = ["RefactoringSpecialistAgent"]
else:
    RefactoringSpecialistAgent = MockRefactoringSpecialistAgent
    __all__ = ["RefactoringSpecialistAgent"]