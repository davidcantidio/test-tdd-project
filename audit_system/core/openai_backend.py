# -*- coding: utf-8 -*-
"""
OpenAI Backend Implementation for GPT-5 Integration
--------------------------------------------------
Implementação direta do LLMBackend usando OpenAI GPT-5.
Simples e funcional - sem overengineering.
"""
from __future__ import annotations

import os
import time
import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None

from .llm_backend import LLMBackend, LLMOverview


class OpenAIBackend(LLMBackend):
    """Backend OpenAI simples para GPT-5."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-5"):
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not installed. Run: pip install openai")
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"✅ OpenAI Backend initialized with model: {self.model}")
    
    def file_overview(self, *, content: str, file_path: str, ast_tree: Any | None) -> LLMOverview:
        """Análise geral do arquivo usando GPT-5."""
        
        prompt = f"""Analyze this Python file and provide structured analysis:

FILE: {file_path}

CODE:
{content[:3000]}  # Limit to avoid token overflow

Please analyze:
1. Overall purpose and responsibility
2. Architectural role (service/controller/utility/model/test)
3. Main security risks or vulnerabilities
4. Key notes about code quality

Respond in a structured way focusing on practical insights."""

        try:
            start_time = time.time()
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a senior Python code architect. Provide concise, actionable analysis."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.1  # Low temperature for consistent analysis
            )
            
            elapsed = time.time() - start_time
            content_text = response.choices[0].message.content
            
            # Log real usage
            self.logger.info(f"🧠 GPT-5 file analysis: {file_path} ({elapsed:.2f}s, {response.usage.total_tokens} tokens)")
            
            # Parse response into structured format
            return self._parse_file_overview(content_text, file_path)
            
        except Exception as e:
            self.logger.error(f"❌ OpenAI API error for {file_path}: {e}")
            # Return fallback response
            return LLMOverview(
                overall_purpose=f"API Error: {str(e)}",
                architectural_role="unknown",
                risks=[f"Failed to analyze: {str(e)}"],
                notes=["OpenAI API call failed"],
                confidence_score=0.0,
            )
    
    def line_batch_analysis(
        self, *, content: str, file_path: str, ast_tree: Any | None, line_batch: List[Tuple[int, str]]
    ) -> List[Dict[str, Any]]:
        """Análise de lote de linhas usando GPT-5."""
        
        if not line_batch:
            return []
        
        # Build context for batch analysis
        lines_context = "\n".join([f"{ln}: {text}" for ln, text in line_batch])
        
        prompt = f"""Analyze these specific lines from a Python file:

FILE: {file_path}
LINES TO ANALYZE:
{lines_context}

For each line, provide:
- Purpose: What this line does
- Semantic type: (control_flow/data_manipulation/function_call/etc)
- Any notable issues or improvements

Keep responses concise and practical."""

        try:
            start_time = time.time()
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a code analysis expert. Analyze each line efficiently."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.1
            )
            
            elapsed = time.time() - start_time
            content_text = response.choices[0].message.content
            
            self.logger.info(f"🧠 GPT-5 line batch analysis: {len(line_batch)} lines ({elapsed:.2f}s, {response.usage.total_tokens} tokens)")
            
            # Parse response and return structured analysis
            return self._parse_line_analysis(content_text, line_batch)
            
        except Exception as e:
            self.logger.error(f"❌ OpenAI API error for line analysis in {file_path}: {e}")
            # Return fallback analysis
            return [
                {
                    "line": ln,
                    "purpose": f"API Error: {str(e)}",
                    "semantic_type": "error",
                    "notes": ["OpenAI API call failed"],
                }
                for ln, _ in line_batch
            ]
    
    def _parse_file_overview(self, response_text: str, file_path: str) -> LLMOverview:
        """Parse GPT-5 response into LLMOverview structure."""
        
        # Simple parsing - could be enhanced with structured output
        lines = response_text.strip().split('\n')
        
        purpose = "Unknown"
        role = "unknown" 
        risks = []
        notes = []
        
        # Extract key information from response
        for line in lines:
            line = line.strip()
            if any(word in line.lower() for word in ['purpose', 'responsibility']):
                purpose = line
            elif any(word in line.lower() for word in ['role', 'architectural']):
                role = line
            elif any(word in line.lower() for word in ['risk', 'security', 'vulnerability']):
                risks.append(line)
            elif line:
                notes.append(line)
        
        return LLMOverview(
            overall_purpose=purpose,
            architectural_role=role,
            risks=risks,
            notes=notes[:5],  # Limit notes
            confidence_score=0.8,  # GPT-5 is generally reliable
        )
    
    def _parse_line_analysis(self, response_text: str, line_batch: List[Tuple[int, str]]) -> List[Dict[str, Any]]:
        """Parse GPT-5 line analysis response."""
        
        # Simple fallback parsing - in production could use structured output
        results = []
        
        for ln, text in line_batch:
            results.append({
                "line": ln,
                "purpose": f"GPT-5 analysis available",
                "semantic_type": "analyzed",
                "notes": [response_text[:100]],  # First 100 chars as sample
                "confidence": 0.8,
            })
        
        return results


def create_openai_backend(api_key: Optional[str] = None, model: str = "gpt-5") -> OpenAIBackend:
    """Factory function to create OpenAI backend."""
    return OpenAIBackend(api_key=api_key, model=model)


# Test function
def test_openai_backend():
    """Test OpenAI backend with sample code."""
    if not OPENAI_AVAILABLE:
        print("❌ OpenAI library not available")
        return
    
    try:
        backend = create_openai_backend()
        
        sample_code = '''
def calculate_total(items):
    total = 0
    for item in items:
        total += item.price
    return total
'''
        
        overview = backend.file_overview(
            content=sample_code,
            file_path="test.py",
            ast_tree=None
        )
        
        print(f"✅ GPT-5 Analysis: {overview.overall_purpose}")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    test_openai_backend()