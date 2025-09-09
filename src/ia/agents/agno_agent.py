# src/ia/agents/agno_agent.py
from pydantic import BaseModel, Field
import json
import logging
from typing import List, Dict, Any
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
        """Executa o agente e garante retorno ProductVisionDTO.

        Observação: dependendo da versão da lib, Agent.run pode retornar
        diretamente o modelo tipado, um wrapper com `.content` (string/dict)
        ou outro objeto. Fazemos coercion robusta aqui para evitar retornos
        vazios na camada superior. Não há fallback de negócio — apenas parsing.
        """
        # Validação de entrada
        for f in self.REQUIRED_FIELDS:
            val = raw.get(f)
            if val is None or (isinstance(val, str) and not val.strip()):
                raise ValueError(f"Campo obrigatório '{f}' não preenchido")

        prompt = PROMPT_REFINE.format(raw_json=raw)
        out = self.agent.run(prompt)

        logger = logging.getLogger(__name__)
        try:
            logger.info(
                "VisionRefinerAgent.run | out_type=%s | has_content=%s",
                type(out).__name__, hasattr(out, "content"),
            )
        except Exception:
            pass

        # 1) Já veio no tipo correto
        if isinstance(out, ProductVisionDTO):
            return out

        # 2) Alguns wrappers expõem `.content`
        content = getattr(out, "content", None)
        if isinstance(content, ProductVisionDTO):
            return content
        if isinstance(content, dict):
            return ProductVisionDTO(**content)
        if isinstance(content, str):
            # Tentar JSON → DTO
            data = json.loads(content)
            return ProductVisionDTO(**data)
        # Alguns modelos retornam objeto com atributo `.text`
        if hasattr(content, "text") and isinstance(content.text, str):  # type: ignore[attr-defined]
            data = json.loads(content.text)
            return ProductVisionDTO(**data)

        # 3) Talvez seja um dict direto
        if isinstance(out, dict):
            return ProductVisionDTO(**out)

        # 4) Último recurso: tentar extrair atributos
        try:
            data = {
                "vision_statement": getattr(out, "vision_statement"),
                "problem_statement": getattr(out, "problem_statement"),
                "target_audience": getattr(out, "target_audience"),
                "value_proposition": getattr(out, "value_proposition"),
                "constraints": getattr(out, "constraints", []) or [],
            }
            return ProductVisionDTO(**data)
        except Exception as e:
            raise RuntimeError(f"VisionRefinerAgent: resposta inesperada do agente: {type(out).__name__}: {e}")


@dataclass
class SingleFieldAgent:
    """
    Agente Agno para refinar campos individuais sem estrutura forçada.
    Retorna apenas texto puro (string) ao invés de ProductVisionDTO completo.
    """
    model_id: str = "gpt-5-nano"

    def __post_init__(self):
        self.agent = Agent(
            model=OpenAIChat(id=self.model_id),
            instructions="Refine campos individuais de produto mantendo o significado original.",
            # SEM response_model - retorna string pura
            use_json_mode=False,  # Não força JSON
            markdown=False,
        )

    def refine_field(self, prompt: str) -> str:
        """
        Refina um campo específico usando o prompt fornecido.
        Retorna apenas o texto refinado como string.
        """
        try:
            result = self.agent.run(prompt)
            # Extrair conteúdo da resposta
            if hasattr(result, 'content'):
                return str(result.content).strip()
            elif isinstance(result, str):
                return result.strip()
            else:
                return str(result).strip()
        except Exception as e:
            raise RuntimeError(f"Erro ao refinar campo: {e}")
