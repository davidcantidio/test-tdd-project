"""
ProductVision Entity (História 1.2)

Clean, framework-independent domain entity representing the product vision.
Implements basic validation and timestamp initialization.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class ProductVision:
    """Entidade de Visão do Produto - 16 campos obrigatórios.

    Campos obrigatórios:
        - name, vision_statement, target_user, user_problem, expected_benefits
        - product_description, success_metrics, tech_requirements
        - non_functional_requirements, compliance_requirements, risks
        - assumptions, must_have, cannot_have, deliverables, market_opportunity

    Observações:
        - Entidade pura do domínio; sem dependências de frameworks
        - Validação básica via método validate()
        - Timestamps são inicializados no __post_init__ se ausentes
    """

    # Campos obrigatórios (sem defaults, regra do dataclass)
    name: str
    vision_statement: str
    target_user: str
    user_problem: str
    expected_benefits: str
    product_description: str
    success_metrics: str
    tech_requirements: str
    non_functional_requirements: str
    compliance_requirements: str
    risks: str
    assumptions: str
    must_have: str
    cannot_have: str
    deliverables: str
    market_opportunity: str

    # Campos opcionais e metadados
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now()
        if not self.updated_at:
            self.updated_at = datetime.now()

    def validate(self) -> List[str]:
        """Valida campos obrigatórios e retorna lista de erros (se houver)."""
        errors: List[str] = []
        required_fields = [
            "name",
            "vision_statement",
            "target_user",
            "user_problem",
            "expected_benefits",
            "product_description",
            "success_metrics",
            "tech_requirements",
            "non_functional_requirements",
            "compliance_requirements",
            "risks",
            "assumptions",
            "must_have",
            "cannot_have",
            "deliverables",
            "market_opportunity",
        ]
        for field_name in required_fields:
            value = getattr(self, field_name, None)
            # Listas vazias ou strings em branco são inválidas
            if value is None:
                errors.append(f"{field_name} is required and cannot be empty")
                continue
            if isinstance(value, str):
                if not value.strip():
                    errors.append(f"{field_name} is required and cannot be empty")
            else:
                # Outros tipos não são aceitos para campos obrigatórios
                errors.append(f"{field_name} has invalid type: {type(value).__name__}")

        return errors

    def is_valid(self) -> bool:
        """Retorna True se a entidade não possuir erros de validação."""
        return len(self.validate()) == 0
