#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo: Refino de Product Vision com Agno + OpenAI Responses (Structured Output)

Requisitos:
  pip install -U agno openai python-dotenv

Ambiente:
  Crie um .env na raiz com:
    OPENAI_API_KEY=seu_token_aqui

Execução:
  python scripts/vision_agent_demo.py
"""

from __future__ import annotations

import json
import os
from textwrap import dedent

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List

from agno.agent import Agent, RunResponse
from agno.models.openai import OpenAIResponses

# ---------------------------------------------------------------------
# 1) Carregar variáveis de ambiente (.env) e validar a API key
# ---------------------------------------------------------------------
load_dotenv()
if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError(
        "OPENAI_API_KEY não encontrado. Crie um arquivo .env na raiz com OPENAI_API_KEY=seu_token"
    )

# ---------------------------------------------------------------------
# 2) Definir o schema de saída estruturada (Pydantic)
#    -> o modelo define exatamente o JSON que queremos de volta
# ---------------------------------------------------------------------
class ProductVisionDTO(BaseModel):
    product_name: str = Field(..., description="Nome claro e memorável do produto.")
    target_user: str = Field(..., description="Público‑alvo primário (personas).")
    problem: str = Field(..., description="Problema/necessidade central resolvida.")
    outcome: str = Field(..., description="Resultado/benefício desejado pelo usuário.")
    constraints: List[str] = Field(default_factory=list, description="Restrições e limites (escopo, compliance, etc.).")


# ---------------------------------------------------------------------
# 3) Montar o Agente do Agno com OpenAI *Responses* (suporta structured outputs)
#    -> use_json_mode=True força JSON compatível
# ---------------------------------------------------------------------
# Obs: você pode trocar o id do modelo por outro suportado na sua conta:
# ex: "gpt-4o-mini", "gpt-5" etc.
MODEL_ID = os.getenv("OPENAI_MODEL_ID", "gpt-5-nano")

agent = Agent(
    name="ProductVisionRefiner",
    description="Refina visões de produto e retorna um JSON tipado.",
    model=OpenAIResponses(id=MODEL_ID),
    response_model=ProductVisionDTO,
    use_json_mode=True,
    markdown=False,
)

# ---------------------------------------------------------------------
# 4) Exemplo de visão bruta (simulando o que vem do formulário)
#    -> você pode alterar livremente para testar o comportamento
# ---------------------------------------------------------------------
raw_vision = {
    "product_name": "CursoExpress",
    "target_user": "professores e criadores independentes",
    "problem": "dificuldade para vender cursos online sem dor de cabeça com checkout e integrações",
    "outcome": "lançar e vender cursos rapidamente, com checkout simples e métricas claras",
    "constraints": ["LGPD", "MVP em 8 semanas", "Pagamento via Pix e cartão"],
}

# ---------------------------------------------------------------------
# 5) Prompt desenhado para structured output (curto e objetivo)
# ---------------------------------------------------------------------
def build_prompt(raw: dict) -> str:
    return dedent(f"""
    Você é um especialista em Product Management.
    Refine a visão de produto fornecida e **preencha todos os campos** do schema.

    Regras:
    - Seja específico e conciso.
    - Não invente features: apenas esclareça e organize.
    - Caso algum item esteja vago, torne-o explícito com suposições realistas.

    Campos de saída (JSON tipado):
    - product_name (string)
    - target_user (string)
    - problem (string)
    - outcome (string)
    - constraints (array de strings, pode manter as existentes e completar)

    Visão bruta:
    {json.dumps(raw, ensure_ascii=False, indent=2)}
    """).strip()


def main() -> None:
    prompt = build_prompt(raw_vision)

    # -----------------------------------------------------------------
    # 6) Executar o agente e capturar a resposta
    #     - Agent.run(...) → RunResponse
    #     - run.content     → instancia de ProductVisionDTO (Pydantic)
    # -----------------------------------------------------------------
    run: RunResponse = agent.run(prompt)

    # Checar se veio conteúdo
    if run is None or run.content is None:
        raise RuntimeError("O agente não retornou conteúdo.")

    # Se o modelo estruturado estiver correto, run.content é ProductVisionDTO
    content = run.content
    if isinstance(content, ProductVisionDTO):
        data_dict = content.model_dump()  # depois serializamos com json.dumps para ensure_ascii=False
    elif isinstance(content, dict):
        # fallback (algumas versões/modelos podem retornar dict puro)
        data_dict = content
    else:
        # último recurso: tentar interpretar texto como JSON
        try:
            data_dict = json.loads(str(content))
        except Exception:
            raise RuntimeError(f"Conteúdo inesperado do agente: {type(content)!r}")

    print("\n=== RESULTADO (JSON) ===")
    print(json.dumps(data_dict, indent=2, ensure_ascii=False))

    # Também exibimos o texto bruto (útil para debug)
    if hasattr(run, "content"):
        print("\n=== BRUTO (debug) ===")
        print(run.content)


if __name__ == "__main__":
    main()
