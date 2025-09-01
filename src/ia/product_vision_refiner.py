# src/ia/product_vision_refiner.py
from typing import Dict
from dataclasses import dataclass
from src.ia.agents.agno_agent import VisionRefinerAgent, ProductVisionDTO

@dataclass
class RealGPTRefiner:
    """Real AI refiner using GPT model."""
    model_id: str = "gpt-5-nano"

    def __post_init__(self):
        self.agent = VisionRefinerAgent(model_id=self.model_id)

    def refine(self, raw: Dict) -> ProductVisionDTO:
        return self.agent.refine(raw)


@dataclass
class FakeClaudeRefiner:
    """Mock refiner for testing, compatible with ProductVisionDTO schema."""
    
    def refine(self, raw: Dict) -> ProductVisionDTO:
        """
        Mock refinement with validation similar to VisionRefinerAgent.
        
        Args:
            raw: Dict with vision fields
            
        Returns:
            ProductVisionDTO with mock-refined content
            
        Raises:
            ValueError: If any required field is empty
        """
        # Same validation as VisionRefinerAgent
        required_fields = ["vision_statement", "problem_statement", "target_audience", "value_proposition"]
        
        for field in required_fields:
            val = raw.get(field)
            if val is None or (isinstance(val, str) and not val.strip()):
                raise ValueError(f"Campo obrigatório '{field}' não preenchido")
        
        # Mock refinement - add [MOCK] prefix to show it's fake
        return ProductVisionDTO(
            vision_statement=f"[MOCK] {raw['vision_statement'].strip()}",
            problem_statement=f"[MOCK] {raw['problem_statement'].strip()}",
            target_audience=f"[MOCK] {raw['target_audience'].strip()}",
            value_proposition=f"[MOCK] {raw['value_proposition'].strip()}",
            constraints=raw.get('constraints', [])
        )
