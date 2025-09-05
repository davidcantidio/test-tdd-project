"""
🎯 EpicSuggestionDTO - História 1.2

Data Transfer Object padronizado para Sugestão de Épicos seguindo os critérios
de aceitação da História 1.2:

Aceitação:
- Estrutura: EpicSuggestionDTO(title, rationale, tags[], confidence:0..1, source="ai|heuristic")
- Serializa/deserializa (dict) sem perda

Implementação TDD seguindo metodologia Red-Green-Refactor.
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field


@dataclass
class EpicSuggestionDTO:
    """
    DTO padronizado para Sugestão de Épicos com validação automática.
    
    Critérios de Aceitação (História 1.2):
    - Estrutura: EpicSuggestionDTO(title, rationale, tags[], confidence:0..1, source="ai|heuristic")
    - Serializa/deserializa (dict) sem perda
    
    Campos obrigatórios:
    - title: Título do epic/capítulo
    - rationale: Justificativa/racionalização do epic
    - tags: Lista de tags categóricas (normalizada automaticamente)
    - confidence: Nível de confiança entre 0.0 e 1.0
    - source: Fonte da sugestão ("ai" ou "heuristic")
    """
    
    title: Optional[str] = None
    rationale: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    confidence: float = 0.0
    source: str = ""
    
    # Campos de controle interno
    _errors: List[str] = field(default_factory=list, init=False)
    _is_valid: Optional[bool] = field(default=None, init=False)
    
    def __post_init__(self):
        """Inicialização após criação do DTO com normalização e validação."""
        # Normalizar tags automaticamente
        self.tags = self._normalize_tags(self.tags)
        
        # Executar validação
        self._validate()
    
    def _normalize_tags(self, tags: List[Any]) -> List[str]:
        """
        Normalizar lista de tags seguindo o padrão das constraints.
        
        Normalização aplicada:
        - Remove entradas None ou não-string
        - Remove espaços em branco no início/fim (trim)
        - Remove entradas vazias após trim
        - Remove duplicatas
        - Mantém ordem original (primeira ocorrência)
        """
        if not tags:
            return []
        
        normalized = []
        seen = set()
        
        for tag in tags:
            # Ignorar entradas None ou não-string
            if tag is None or not isinstance(tag, str):
                continue
            
            # Aplicar trim
            trimmed = tag.strip()
            
            # Ignorar strings vazias após trim
            if not trimmed:
                continue
            
            # Adicionar apenas se ainda não visto (remover duplicatas)
            if trimmed not in seen:
                seen.add(trimmed)
                normalized.append(trimmed)
        
        return normalized
    
    def _validate(self):
        """Executar validação completa do DTO."""
        self._errors = []
        self._is_valid = None
        
        # Validar campos obrigatórios string
        self._validate_required_string_fields()
        
        # Validar confidence
        self._validate_confidence()
        
        # Validar source
        self._validate_source()
        
        # Determinar validade final
        self._is_valid = len(self._errors) == 0
    
    def _validate_required_string_fields(self):
        """Validar campos obrigatórios string."""
        required_fields = {
            "title": "Título",
            "rationale": "Justificativa"
        }
        
        for field_name, field_label in required_fields.items():
            field_value = getattr(self, field_name)
            
            # Verificar se campo existe e não é None
            if field_value is None:
                self._errors.append(f"{field_label} é um campo obrigatório")
                continue
            
            # Verificar se não é string vazia ou apenas espaços
            if not isinstance(field_value, str) or not field_value.strip():
                self._errors.append(f"{field_label} não pode estar vazio ou em branco")
    
    def _validate_confidence(self):
        """Validar campo confidence."""
        if not isinstance(self.confidence, (int, float)):
            self._errors.append("Confidence deve ser um número")
            return
        
        if self.confidence < 0.0 or self.confidence > 1.0:
            self._errors.append("Confidence deve estar entre 0.0 e 1.0")
    
    def _validate_source(self):
        """Validar campo source."""
        valid_sources = ["ai", "heuristic"]
        
        if not isinstance(self.source, str):
            self._errors.append("Source deve ser uma string")
            return
        
        if self.source not in valid_sources:
            self._errors.append(f"Source deve ser 'ai' ou 'heuristic', recebido: '{self.source}'")
    
    def is_valid(self) -> bool:
        """
        Verificar se o DTO é válido.
        
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
        if self._is_valid is None:
            self._validate()
        return self._errors.copy()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serializar DTO para dicionário.
        
        Returns:
            Dicionário com dados do DTO
        """
        return {
            "title": self.title,
            "rationale": self.rationale,
            "tags": self.tags.copy(),
            "confidence": self.confidence,
            "source": self.source
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EpicSuggestionDTO':
        """
        Criar DTO a partir de dicionário.
        
        Args:
            data: Dicionário com dados do epic suggestion
            
        Returns:
            Instância de EpicSuggestionDTO
        """
        # Extrair dados - None para campos obrigatórios ausentes
        return cls(
            title=data.get("title", None),
            rationale=data.get("rationale", None),
            tags=data.get("tags", []),
            confidence=data.get("confidence", 0.0),
            source=data.get("source", "")
        )
    
    def __str__(self) -> str:
        """Representação string do DTO."""
        return f"EpicSuggestionDTO(title='{self.title}', source='{self.source}', confidence={self.confidence})"
    
    def __repr__(self) -> str:
        """Representação técnica do DTO."""
        return (f"EpicSuggestionDTO(title='{self.title}', rationale='{self.rationale[:50]}...', "
                f"tags={self.tags}, confidence={self.confidence}, source='{self.source}')")