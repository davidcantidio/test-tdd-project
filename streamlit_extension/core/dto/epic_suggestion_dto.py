"""
🎯 EpicSuggestionDTO - História 1.2 + 3.1

Data Transfer Object padronizado para Sugestão de Épicos seguindo os critérios
de aceitação da História 1.2 + campos para PriorityScorer (História 3.1).

Aceitação História 1.2:
- Estrutura: EpicSuggestionDTO(title, rationale, tags[], confidence:0..1, source="ai|heuristic")
- Serializa/deserializa (dict) sem perda

Aceitação História 3.1:
- Campos para priority scoring: id, business_priority, complexity_score, effort_estimate, alignment_score
- Validação e normalização robusta com clamps consistentes

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
    
    Critérios de Aceitação (História 3.1):
    - Campos para priorização: id, business_priority, complexity_score, effort_estimate, alignment_score
    - Clamps consistentes em todos os campos numéricos
    - ID UUID obrigatório para chaveamento estável
    
    Campos obrigatórios:
    - title: Título do epic/capítulo
    - rationale: Justificativa/racionalização do epic
    - tags: Lista de tags categóricas (normalizada automaticamente)
    - confidence: Nível de confiança entre 0.0 e 1.0
    - source: Fonte da sugestão ("ai" ou "heuristic")
    - id: Identificador UUID único e estável
    - business_priority: Prioridade de negócio (1-5)
    - complexity_score: Score de complexidade (1-5)
    - effort_estimate: Estimativa de esforço em dias (≥1)
    - alignment_score: Score de alinhamento estratégico (1-5)
    """
    
    # Campos História 1.2
    title: Optional[str] = None
    rationale: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    confidence: float = 0.0
    source: str = ""
    
    # Campos História 3.1 - PriorityScorer
    id: Optional[str] = None                # UUID obrigatório
    business_priority: int = 3              # 1-5 prioridade de negócio (1=crítico, 5=backlog)
    complexity_score: float = 3.0           # 1-5 complexidade (1=simples, 5=complexo)
    effort_estimate: int = 7                # Dias de esforço (≥1)
    alignment_score: int = 3                # 1-5 alinhamento estratégico (1=baixo, 5=alto)
    
    # Campos de controle interno
    _errors: List[str] = field(default_factory=list, init=False)
    _is_valid: Optional[bool] = field(default=None, init=False)
    
    def __post_init__(self):
        """Inicialização após criação do DTO com normalização e validação."""
        # Normalizar tags automaticamente
        self.tags = self._normalize_tags(self.tags)
        
        # Garantir ID obrigatório (micro-checagem 1)
        if not self.id:
            import uuid
            self.id = str(uuid.uuid4())
        
        # Aplicar clamps consistentes (micro-checagem 2)
        self._apply_consistent_clamps()
        
        # Executar validação
        self._validate()
    
    def _apply_consistent_clamps(self):
        """Aplicar clamps consistentes em todos os campos numéricos."""
        self.business_priority = max(1, min(5, self.business_priority))
        self.complexity_score = max(1.0, min(5.0, self.complexity_score))
        self.effort_estimate = max(1, self.effort_estimate)
        self.alignment_score = max(1, min(5, self.alignment_score))
        self.confidence = max(0.0, min(1.0, self.confidence))
    
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
        
        # Validar campos História 1.2
        self._validate_confidence()
        self._validate_source()
        
        # Validar campos História 3.1
        self._validate_id()
        self._validate_effort_estimate()
        
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
    
    def _validate_id(self):
        """Validar campo id (obrigatório para História 3.1)."""
        if not self.id or not self.id.strip():
            self._errors.append("Epic deve ter ID obrigatório")
    
    def _validate_effort_estimate(self):
        """Validar campo effort_estimate."""
        if self.effort_estimate <= 0:
            self._errors.append(f"effort_estimate deve ser > 0, recebido: {self.effort_estimate}")
    
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
            Dicionário com dados do DTO (incluindo campos História 3.1)
        """
        return {
            # Campos História 1.2
            "title": self.title,
            "rationale": self.rationale,
            "tags": self.tags.copy(),
            "confidence": self.confidence,
            "source": self.source,
            
            # Campos História 3.1
            "id": self.id,
            "business_priority": self.business_priority,
            "complexity_score": self.complexity_score,
            "effort_estimate": self.effort_estimate,
            "alignment_score": self.alignment_score
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EpicSuggestionDTO':
        """
        Criar DTO a partir de dicionário.
        
        Args:
            data: Dicionário com dados do epic suggestion
            
        Returns:
            Instância de EpicSuggestionDTO com clamps aplicados
        """
        # Extrair dados com defaults seguros
        return cls(
            # Campos História 1.2
            title=data.get("title", None),
            rationale=data.get("rationale", None),
            tags=data.get("tags", []),
            confidence=data.get("confidence", 0.8),
            source=data.get("source", "ai"),
            
            # Campos História 3.1
            id=data.get("id", None),  # UUID será gerado em __post_init__ se None
            business_priority=data.get("business_priority", 3),
            complexity_score=data.get("complexity_score", 3.0),
            effort_estimate=data.get("effort_estimate", 7),
            alignment_score=data.get("alignment_score", 3)
        )
    
    def __str__(self) -> str:
        """Representação string do DTO."""
        return f"EpicSuggestionDTO(id='{self.id}', title='{self.title}', source='{self.source}', confidence={self.confidence})"
    
    def __repr__(self) -> str:
        """Representação técnica do DTO."""
        return (f"EpicSuggestionDTO(id='{self.id}', title='{self.title}', "
                f"priority={self.business_priority}, effort={self.effort_estimate}, "
                f"confidence={self.confidence}, source='{self.source}')")