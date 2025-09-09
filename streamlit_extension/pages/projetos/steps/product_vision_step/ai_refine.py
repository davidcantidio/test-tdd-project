"""Refino por IA — Camada de Acesso (Product Vision).

Este módulo fornece um ponto único para obter o serviço de refino por IA
usado no passo Product Vision. Diferente de versões anteriores, não há
fallback para mocks: se a IA real não estiver disponível, o código deve
falhar explicitamente (falha visível é preferível a um resultado enganoso).

Responsabilidades:
- Obter o serviço via Service Container (DI).
- Expor um adaptador fino de compatibilidade.
- Registrar logs úteis sem poluir a saída padrão.
"""

from typing import Dict, Any
import logging

# Import explícito (absoluto) para evitar ambiguidade de pacotes
from streamlit_extension.services import get_service_container

logger = logging.getLogger(__name__)


def get_vision_service():
    """Retorna o serviço unificado de refino por IA.

    - Usa o Service Container para criar/recuperar a instância.
    - Sem fallback para mocks: em caso de falha, levanta RuntimeError
      com mensagem clara (ex.: variável OPENAI_API_KEY ausente).
    """
    try:
        container = get_service_container()
        service = container.get_vision_refine_service()
        # Log reduzido (apenas metadados de diagnóstico)
        stype = getattr(service, "service_type", type(service).__name__)
        is_real = getattr(service, "is_using_real_ai", False)
        logger.info("Vision service carregado | type=%s | real_ai=%s", stype, is_real)
        return service
    except Exception as e:  # pragma: no cover - comportamento explícito em prod
        logger.error("Falha ao obter Vision service: %s", e)
        raise RuntimeError(
            "Vision service indisponível. Verifique suas credenciais e a variável "
            "OPENAI_API_KEY, ou o provisionamento do serviço no container."
        ) from e


# Alias mantido por compatibilidade: callable que retorna o serviço
VisionRefineService = get_vision_service


class UnifiedVisionRefineAdapter:
    """Adaptador fino para compatibilidade.

    Mantém a mesma interface utilizada historicamente pelo wizard, porém
    delega ao serviço real obtido via container. Não existe fallback para
    mocks neste adaptador — qualquer falha deve ser tratada pelo chamador.
    """
    
    def __init__(self):
        self._service = get_vision_service()
    
    def refine(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Refina os dados da Product Vision usando o serviço unificado."""
        return self._service.refine(payload)
    
    @property
    def is_using_real_ai(self) -> bool:
        """Indica se o serviço atual está usando IA real."""
        return getattr(self._service, 'is_using_real_ai', False)
    
    @property
    def service_type(self) -> str:
        """Nome do tipo de serviço em uso (diagnóstico)."""
        return getattr(self._service, 'service_type', type(self._service).__name__)


# API pública explícita
__all__ = [
    'VisionRefineService',
    'UnifiedVisionRefineAdapter',
    'get_vision_service',
]
