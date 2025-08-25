# src/ai/product_vision_refiner.py
from typing import Dict
from dataclasses import dataclass
from src.ia.agents.agno_agent import VisionRefinerAgent, ProductVisionDTO

@dataclass
class RealGPTRefiner:
    model_id: str = "gpt-5-nano"

    def __post_init__(self):
        self.agent = VisionRefinerAgent(model_id=self.model_id)

    def refine(self, raw: Dict) -> ProductVisionDTO:
        return self.agent.refine(raw)
