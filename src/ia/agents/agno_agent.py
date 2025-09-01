# src/ia/agents/agno_agent.py
from pydantic import BaseModel, Field
from typing import List, Dict
from dataclasses import dataclass

from agno.agent import Agent
from agno.models.openai import OpenAIChat  # Model object (não use string)

# ===== Saída estruturada (Pydantic) - Schema Compatível com Wizard =====
class ProductVisionDTO(BaseModel):
    vision_statement: str = Field(..., description="Visão do produto")
    problem_statement: str = Field(..., description="Problema a resolver")
    target_audience: str = Field(..., description="Público-alvo primário")
    value_proposition: str = Field(..., description="Proposta de valor")
    constraints: List[str] = Field(default_factory=list, description="Restrições/limitações")

# ===== Prompt base - Compatível com Wizard Schema =====
PROMPT_REFINE = """Você é um Product Manager Sênior.
Refine a visão de produto nos seguintes campos específicos:
- vision_statement: Visão clara e inspiradora do produto
- problem_statement: Problema específico a resolver
- target_audience: Público-alvo bem definido
- value_proposition: Valor único oferecido
- constraints: Limitações objetivas (ou vazio, se não existirem)

Mantendo intenção e escopo, mas evitando jargão e redundâncias.
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

    REQUIRED_FIELDS = ["vision_statement", "problem_statement", "target_audience", "value_proposition", "constraints"]

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
