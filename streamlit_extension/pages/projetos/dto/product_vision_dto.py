"""
🎯 ProductVisionDTO - História 1.1

Data Transfer Object padronizado para Product Vision seguindo os critérios
de aceitação da História 1.1:

Aceitação:
- DTO valida campos obrigatórios; rejeita strings vazias
- constraints sempre lista normalizada (trim, sem duplicatas)

Implementação TDD seguindo metodologia Red-Green-Refactor.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class ProductVisionDTO:
    """
    DTO padronizado para Product Vision com validação automática.
    
    Critérios de Aceitação (História 1.1):
    - Valida campos obrigatórios; rejeita strings vazias
    - constraints sempre lista normalizada (trim, sem duplicatas)
    
    Campos obrigatórios:
    - vision_statement: Declaração da visão do produto
    - problem_statement: Problema que o produto resolve
    - target_audience: Público-alvo do produto
    - value_proposition: Proposta de valor
    - constraints: Lista de restrições (normalizada automaticamente)
    """
    
    vision_statement: str = ""
    problem_statement: str = ""
    target_audience: str = ""
    value_proposition: str = ""
    constraints: List[str] = field(default_factory=list)
    
    # Campos de controle interno
    _errors: List[str] = field(default_factory=list, init=False)
    _is_valid: Optional[bool] = field(default=None, init=False)
    
    def __post_init__(self):
        """Inicialização após criação do DTO com normalização e validação."""
        # Normalizar constraints automaticamente
        self.constraints = self._normalize_constraints(self.constraints)
        
        # Executar validação
        self._validate()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProductVisionDTO':
        """
        Criar ProductVisionDTO a partir de dicionário.
        
        Args:
            data: Dicionário com dados do product vision
            
        Returns:
            ProductVisionDTO validado e normalizado
        """
        return cls(
            vision_statement=data.get("vision_statement", ""),
            problem_statement=data.get("problem_statement", ""),
            target_audience=data.get("target_audience", ""),
            value_proposition=data.get("value_proposition", ""),
            constraints=data.get("constraints", [])
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serializar DTO para dicionário.
        
        Returns:
            Dicionário com dados normalizados
        """
        return {
            "vision_statement": self.vision_statement,
            "problem_statement": self.problem_statement,
            "target_audience": self.target_audience,
            "value_proposition": self.value_proposition,
            "constraints": self.constraints
        }
    
    def is_valid(self) -> bool:
        """
        Verificar se DTO é válido.
        
        Returns:
            True se válido, False caso contrário
        """
        if self._is_valid is None:
            self._validate()
        return self._is_valid
    
    def get_errors(self) -> List[str]:
        """
        Obter lista de erros de validação.
        
        Returns:
            Lista de mensagens de erro em português
        """
        return self._errors.copy()
    
    def _validate(self) -> None:
        """Executar validação completa do DTO."""
        self._errors.clear()
        
        # Validar campos obrigatórios string
        required_string_fields = {
            "vision_statement": "Declaração da Visão",
            "problem_statement": "Declaração do Problema", 
            "target_audience": "Público-alvo",
            "value_proposition": "Proposta de Valor"
        }
        
        for field_name, field_label in required_string_fields.items():
            field_value = getattr(self, field_name, None)
            
            # Verificar se campo existe e não é None
            if field_value is None:
                self._errors.append(f"{field_label} é um campo obrigatório")
                continue
            
            # Verificar se não é string vazia ou apenas espaços
            if not isinstance(field_value, str) or not field_value.strip():
                self._errors.append(f"{field_label} não pode estar vazio ou em branco")
        
        # Validar constraints (lista pode estar vazia, mas deve existir)
        if not isinstance(self.constraints, list):
            self._errors.append("Constraints deve ser uma lista")
        
        # DTO é válido se não há erros
        self._is_valid = len(self._errors) == 0
    
    def _normalize_constraints(self, constraints: List[Any]) -> List[str]:
        """
        Normalizar lista de constraints conforme critérios de aceitação.
        
        Normalização aplicada:
        - Remove entradas None ou não-string
        - Remove espaços em branco no início/fim (trim)
        - Remove entradas vazias após trim
        - Remove duplicatas
        - Mantém ordem original (primeira ocorrência)
        
        Args:
            constraints: Lista de constraints (pode conter tipos diversos)
            
        Returns:
            Lista normalizada de strings únicas
        """
        if not constraints:
            return []
        
        normalized = []
        seen = set()
        
        for constraint in constraints:
            # Ignorar entradas None ou não-string
            if constraint is None or not isinstance(constraint, str):
                continue
            
            # Aplicar trim
            trimmed = constraint.strip()
            
            # Ignorar strings vazias após trim
            if not trimmed:
                continue
            
            # Adicionar apenas se ainda não visto (remover duplicatas)
            if trimmed not in seen:
                seen.add(trimmed)
                normalized.append(trimmed)
        
        return normalized


# ProductVisionDTO implementado como classe dataclass
# Os testes podem usar ProductVisionDTO.from_dict(data) para compatibilidade