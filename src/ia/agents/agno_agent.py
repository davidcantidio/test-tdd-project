# src/ia/agents/agno_agent.py
from pydantic import BaseModel, Field
from typing import List, Dict
from dataclasses import dataclass

from agno.agent import Agent
from agno.models.openai import OpenAIChat  # Model object (não use string)

# ===== Saída estruturada (Pydantic) =====
class ProductVisionDTO(BaseModel):
    product_name: str = Field(..., description="Nome do produto")
    target_user: str = Field(..., description="Público-alvo primário")
    problem: str = Field(..., description="Problema a resolver")
    outcome: str = Field(..., description="Resultado/benefício esperado")
    constraints: List[str] = Field(default_factory=list, description="Restrições/limitações")

# ===== Prompt base =====
PROMPT_REFINE = """Você é um Product Manager Sênior.
Refine a visão de produto recebida, mantendo intenção e escopo, mas:
- Clareie público-alvo, problema e resultado
- Evite jargão e redundâncias
- Liste restrições objetivas (ou vazio, se não existirem)

Retorne SOMENTE nos campos do schema solicitado.
Visão bruta:
{raw_json}
"""

@dataclass
class VisionRefinerAgent:
    """
    Agente Agno para refinar visões de produto com saída estruturada.
    """
    # Use um Model object (requisito do Agno)
    model_id: str = "gpt-5-nano"

    def __post_init__(self):
        self.agent = Agent(
            model=OpenAIChat(id=self.model_id),
            instructions="Refine visões de produto mantendo o escopo original.",
            response_model=ProductVisionDTO,  # structured output
            use_json_mode=True,               # força o JSON do schema
            markdown=False,
        )

    REQUIRED_FIELDS = ["product_name", "target_user", "problem", "outcome", "constraints"]

    def refine(self, raw: Dict) -> ProductVisionDTO:
        # Validação: só roda se TODOS os campos estiverem preenchidos
        for f in self.REQUIRED_FIELDS:
            val = raw.get(f)
            if val is None or (isinstance(val, str) and not val.strip()):
                raise ValueError(f"Campo obrigatório '{f}' não preenchido")

        # Execução do agente com saída tipada (Pydantic)
        prompt = PROMPT_REFINE.format(raw_json=raw)
        result: ProductVisionDTO = self.agent.run(prompt)
        return result
