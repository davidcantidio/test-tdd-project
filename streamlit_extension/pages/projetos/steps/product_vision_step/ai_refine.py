"""
Compat layer para testes e código legado do passo Product Vision.

Fornece uma interface estável que alguns testes esperam encontrar
(`get_vision_service`, `VisionRefineService`, `UnifiedVisionRefineAdapter`,
`MockVisionRefineService`, `SingleFieldMockRefiner`).

Internamente, delega para o serviço unificado em
`streamlit_extension.services.vision_service` quando possível.
"""

from __future__ import annotations

from typing import Any, Dict
import logging
import os

import streamlit_extension.services as services
from streamlit_extension.services.vision_service import (
    create_vision_service,
    UnifiedVisionService,
)

logger = logging.getLogger(__name__)


def _validate_payload(payload: Dict[str, Any]) -> None:
    """Validações simples para garantir contrato esperado pelos testes.

    Regras mínimas: payload não pode ser vazio e os campos principais
    não podem ser strings vazias quando presentes.
    """
    if not isinstance(payload, dict) or not payload:
        raise ValueError("payload vazio ou inválido")

    required = [
        "vision_statement",
        "problem_statement",
        "target_audience",
        "value_proposition",
    ]
    for k in required:
        if k in payload and isinstance(payload[k], str) and not payload[k].strip():
            raise ValueError(f"campo obrigatório vazio: {k}")


class MockVisionRefineService:
    """Serviço de refino falso usado em desenvolvimento e fallback.

    Comportamento: retorna um dict com os mesmos campos e adiciona
    o prefixo "[MOCK] " em campos textuais principais.
    """

    is_using_real_ai: bool = False
    service_type: str = "FakeClaudeRefiner"

    def refine(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("MockVisionRefineService.refine chamado")
        _validate_payload(payload)

        def _fmt(v: Any) -> Any:
            if isinstance(v, str) and v.strip():
                return f"[MOCK] {v}"
            return v

        result = {
            "vision_statement": _fmt(payload.get("vision_statement", "")),
            "problem_statement": _fmt(payload.get("problem_statement", "")),
            "target_audience": _fmt(payload.get("target_audience", "")),
            "value_proposition": _fmt(payload.get("value_proposition", "")),
            "constraints": payload.get("constraints", []),
        }
        return result


class SingleFieldMockRefiner:
    """Refinador de campo individual (mock) para testes de UI."""

    def refine_field(self, field_key: str, field_value: Any, _context: Dict[str, Any]) -> Any:
        logger.info("SingleFieldMockRefiner.refine_field chamado: %s", field_key)
        text = str(field_value or "").strip()
        if not text:
            raise ValueError("campo vazio")
        return f"[MOCK] {text}"


class UnifiedVisionRefineAdapter:
    """Adapter fino sobre UnifiedVisionService com validação amigável.

    Exposto para manter compatibilidade de testes que esperam atributos
    `is_using_real_ai` e `service_type` diretamente no objeto de serviço.
    """

    def __init__(self) -> None:
        env = os.getenv("TDD_ENVIRONMENT", "development").lower()
        strict = os.getenv("TDD_REQUIRE_REAL_AI", "false").lower() in ("true", "1", "yes", "on")
        try:
            # Usa a fábrica oficial (prod + credenciais → real; caso contrário mock)
            self._svc: UnifiedVisionService = create_vision_service(strict=strict)
            logger.info("UnifiedVisionRefineAdapter criado: env=%s, type=%s", env, self._svc.service_type)
        except Exception as e:  # fallback robusto
            logger.warning("Falha ao criar UnifiedVisionService (%s). Usando Mock.", e)
            self._svc = MockVisionRefineService()  # type: ignore[assignment]

    @property
    def is_using_real_ai(self) -> bool:
        return bool(getattr(self._svc, "is_using_real_ai", False))

    @property
    def service_type(self) -> str:
        return str(getattr(self._svc, "service_type", type(self._svc).__name__))

    def refine(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("UnifiedVisionRefineAdapter.refine chamado")
        _validate_payload(payload)
        result = self._svc.refine(payload)
        # Normaliza para dict se necessário
        return result.dict() if hasattr(result, "dict") else result


def get_vision_service():
    """Retorna o serviço de refino apropriado, com container se disponível.

    Ordem de decisão:
    1) Tenta via ServiceContainer (permite DI/Mocks nos testes)
    2) Caso falhe, usa UnifiedVisionRefineAdapter (fábrica oficial)
    """
    try:
        container = services.get_service_container()
        svc = container.get_vision_refine_service()
        logger.info("get_vision_service: container OK (%s)", svc.service_type)

        # Se ambiente exigir IA real e o container estiver com mock, resetar
        env = os.getenv("TDD_ENVIRONMENT", "development").lower()
        has_creds = bool(os.getenv("OPENAI_API_KEY"))
        strict = os.getenv("TDD_REQUIRE_REAL_AI", "false").lower() in ("true", "1", "yes", "on")
        needs_real = strict or (env == "production" and has_creds)
        if needs_real and not getattr(svc, "is_using_real_ai", False):
            logger.info("get_vision_service: reconfigurando container para IA real (env=%s)", env)
            services.reset_service_container()
            container = services.get_service_container()
            svc = container.get_vision_refine_service()

        # Adapter para manter atributos esperados nos testes
        adapter = UnifiedVisionRefineAdapter()
        adapter._svc = svc  # type: ignore[attr-defined]
        return adapter
    except Exception as e:
        logger.info("get_vision_service: fallback para adapter (%s)", e)
        return UnifiedVisionRefineAdapter()


def VisionRefineService():  # noqa: N802 (API legada sugere nome de classe)
    """Compat: retorna uma instância de serviço (adapter).

    Embora o nome sugira classe, nos testes ele é chamado como fábrica
    e o objeto retornado deve possuir `.refine(...)`.
    """
    return get_vision_service()
