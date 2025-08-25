from dataclasses import dataclass
from typing import Dict, List
from agno.agent import Agent
from agno.models.openai import OpenAIChat  # use o provider que você já configurou

@dataclass
class ProductVisionDTO:
    product_name: str
    target_user: str
    problem: str
    outcome: str
    constraints: List[str]

class VisionRefineService:
    """
    Serviço fino: recebe o dict cru do form, chama o agente e retorna DTO.
    """

    def __init__(self, model: str = "gpt-5-nano"):
        self.agent = Agent(
            model=OpenAIChat(id=model),
            instructions=(
                "Você é um assistente de produto. Refine a visão recebida e devolva "
                "apenas um JSON válido com: product_name, target_user, problem, outcome, constraints (lista)."
            ),
            structured_outputs=False,  # vamos parsear do texto
        )

    def refine(self, raw: Dict) -> ProductVisionDTO:
        prompt = (
            "Refine esta visão de produto e devolva SOMENTE JSON válido, sem comentários.\n"
            "Campos: product_name, target_user, problem, outcome, constraints (lista de strings).\n"
            f"Visão bruta: {raw}"
        )
        run = self.agent.run(prompt)  # Agno retorna um objeto com .output_text
        text = run.output_text or "{}"

        # parsing defensivo
        import json
        data = json.loads(text)

        return ProductVisionDTO(
            product_name=data["product_name"].strip(),
            target_user=data["target_user"].strip(),
            problem=data["problem"].strip(),
            outcome=data["outcome"].strip(),
            constraints=[c.strip() for c in data.get("constraints", []) if c and str(c).strip()],
        )
