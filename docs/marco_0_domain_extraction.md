# 📚 Marco 0: Extração do Domínio (tdd_core) - Documentação Completa

## 📋 Sumário Executivo

### Visão Geral
O Marco 0 representa a primeira fase crítica da migração do TDD-Project de uma arquitetura monolítica Streamlit para uma plataforma API-First. Esta fase foca exclusivamente na extração e isolamento da lógica de negócio em um módulo independente chamado `tdd_core`, estabelecendo a fundação para toda a evolução subsequente do sistema.

### Contexto e Motivação
- **Situação Atual:** Monolito Streamlit com 15+ serviços acoplados, 56 colunas na tabela framework_epics, sistema de priorização com História 3.2 implementada
- **Problema Central:** Acoplamento forte entre UI (Streamlit) e lógica de negócio, dificultando evolução, testes e reutilização
- **Solução Proposta:** Extrair núcleo de domínio seguindo Clean Architecture e Domain-Driven Design (DDD)

### Objetivos Estratégicos
1. **Isolamento do Domínio:** Criar camada de domínio 100% independente de frameworks
2. **Preservação Funcional:** Manter Streamlit operacional durante toda a migração
3. **Preparação API:** Estabelecer base sólida para futura API REST
4. **Qualidade Garantida:** Alcançar ≥95% de cobertura de testes no núcleo

### Benefícios Esperados
- **Testabilidade:** Testes unitários puros sem dependências externas
- **Manutenibilidade:** Código organizado em camadas bem definidas
- **Reutilização:** Núcleo compartilhável entre múltiplos clientes (Web, CLI, Mobile)
- **Performance:** Manutenção da meta de <10ms para consultas e 0.19ms para ordenação topológica

---

## 🏗️ Arquitetura Proposta

### Estrutura de Camadas

```
┌─────────────────────────────────────────────────────────┐
│                    Presentation Layer                    │
│         (Streamlit UI - Temporariamente Mantida)        │
├─────────────────────────────────────────────────────────┤
│                    Infrastructure Layer                  │
│                  (Adapters & Mappers)                   │
├─────────────────────────────────────────────────────────┤
│                    Application Layer                     │
│              (Services, DTOs, Validators)               │
├─────────────────────────────────────────────────────────┤
│                      Domain Layer                        │
│           (Entities, Value Objects, Exceptions)         │
└─────────────────────────────────────────────────────────┘
```

### Estrutura de Diretórios Detalhada

```
test-tdd-project/
├── tdd_core/                           # 🆕 Novo módulo de domínio
│   ├── __init__.py
│   ├── domain/                         # Camada de Domínio (pura)
│   │   ├── __init__.py
│   │   ├── entities/                   # Entidades do domínio
│   │   │   ├── __init__.py
│   │   │   ├── product_vision.py       # Entidade ProductVision
│   │   │   ├── project.py              # Entidade Project
│   │   │   ├── epic.py                 # Entidade Epic com campos IA
│   │   │   └── task.py                 # Entidade Task
│   │   │
│   │   ├── value_objects/              # Objetos de valor imutáveis
│   │   │   ├── __init__.py
│   │   │   ├── priority.py             # VO Priority (valor, risco, esforço, alinhamento)
│   │   │   ├── tdd_phase.py            # VO TddPhase (analysis/red/green/refactor/review)
│   │   │   ├── complexity_score.py     # VO ComplexityScore (1.0-5.0)
│   │   │   ├── confidence_score.py     # VO ConfidenceScore (0.0-1.0)
│   │   │   └── epic_dependency.py      # VO EpicDependency
│   │   │
│   │   ├── exceptions/                  # Exceções do domínio
│   │   │   ├── __init__.py
│   │   │   ├── validation_error.py
│   │   │   ├── business_rule_error.py
│   │   │   └── domain_error.py
│   │   │
│   │   └── repositories/               # Interfaces de repositório
│   │       ├── __init__.py
│   │       ├── project_repository.py   # Interface IProjectRepository
│   │       ├── epic_repository.py      # Interface IEpicRepository
│   │       ├── task_repository.py      # Interface ITaskRepository
│   │       └── priority_settings_repository.py
│   │
│   ├── application/                    # Camada de Aplicação
│   │   ├── __init__.py
│   │   ├── services/                   # Serviços de aplicação
│   │   │   ├── __init__.py
│   │   │   ├── vision_service.py       # Serviço de visão de produto
│   │   │   ├── epic_service.py         # Serviço de épicos com ordenação
│   │   │   ├── ai_service.py           # Serviço de IA para sugestões
│   │   │   ├── priority_scorer.py      # Calculador de prioridades
│   │   │   └── topological_sorter.py   # Ordenação topológica determinística
│   │   │
│   │   ├── dto/                        # Data Transfer Objects
│   │   │   ├── __init__.py
│   │   │   ├── product_vision_dto.py   # DTO com 15 campos
│   │   │   ├── epic_suggestion_dto.py  # DTO com campos IA
│   │   │   ├── priority_weights_dto.py # DTO de pesos normalizados
│   │   │   └── project_dto.py
│   │   │
│   │   ├── validators/                 # Validadores de aplicação
│   │   │   ├── __init__.py
│   │   │   ├── product_vision_validator.py
│   │   │   ├── epic_suggestion_validator.py
│   │   │   └── priority_weights_validator.py
│   │   │
│   │   └── use_cases/                  # Casos de uso específicos
│   │       ├── __init__.py
│   │       ├── create_project_wizard.py
│   │       ├── generate_epics_from_vision.py
│   │       ├── refine_product_vision_field.py
│   │       └── calculate_epic_priorities.py
│   │
│   └── infrastructure/                 # Camada de Infraestrutura
│       ├── __init__.py
│       ├── adapters/                   # Adaptadores para frameworks
│       │   ├── __init__.py
│       │   ├── streamlit_adapter.py    # Adapter para Streamlit
│       │   ├── session_state_adapter.py
│       │   └── service_container_adapter.py
│       │
│       ├── mappers/                    # Mapeadores entre camadas
│       │   ├── __init__.py
│       │   ├── product_vision_mapper.py
│       │   ├── epic_mapper.py
│       │   ├── project_mapper.py
│       │   └── dto_entity_mapper.py
│       │
│       ├── repositories/               # Implementações concretas
│       │   ├── __init__.py
│       │   ├── sqlite_project_repository.py
│       │   ├── sqlite_epic_repository.py
│       │   ├── sqlite_task_repository.py
│       │   └── sqlite_priority_settings_repository.py
│       │
│       └── ai/                         # Implementações de IA
│           ├── __init__.py
│           ├── openai_service.py       # Implementação OpenAI
│           ├── mock_ai_service.py      # Mock para desenvolvimento
│           ├── prompt_template_loader.py
│           └── domain_lexicon_loader.py
│
├── streamlit_extension/                # Aplicação Streamlit existente
│   └── [estrutura atual mantida com adapters]
│
└── tests/
    └── tdd_core/                       # 🆕 Novos testes do núcleo
        ├── domain/
        ├── application/
        └── infrastructure/
```

---

## 📋 Planejamento Scrum Detalhado

## 🎯 ÉPICO 1: Estruturação do Núcleo de Domínio
**Objetivo:** Estabelecer a arquitetura base do módulo tdd_core seguindo princípios de Clean Architecture  
**Estimativa:** 13 Story Points  
**Prioridade:** Crítica  
**Dependências:** Nenhuma  

### 📖 História 1.1: Criar Estrutura Base do tdd_core
**Como** desenvolvedor  
**Quero** criar a estrutura de diretórios e configuração inicial do módulo tdd_core  
**Para** estabelecer a fundação da arquitetura limpa  

**Critérios de Aceite:**
- [ ] Estrutura de pastas criada conforme diagrama arquitetural
- [ ] Todos os `__init__.py` configurados com exports corretos
- [ ] Setup.py ou pyproject.toml configurado para o módulo
- [ ] README.md com visão geral da arquitetura
- [ ] Testes de importação passando

**Tarefas Técnicas:**
```python
# TASK-1.1.1: Criar estrutura de diretórios (1h)
mkdir -p tdd_core/{domain,application,infrastructure}
mkdir -p tdd_core/domain/{entities,value_objects,exceptions,repositories}
mkdir -p tdd_core/application/{services,dto,validators,use_cases}
mkdir -p tdd_core/infrastructure/{adapters,mappers,repositories,ai}

# TASK-1.1.2: Configurar __init__.py files (2h)
# Exemplo tdd_core/__init__.py:
"""TDD Core - Domain Layer for TDD Project
Version: 1.0.0
"""
from .domain import entities, value_objects, exceptions
from .application import services, dto, validators
__version__ = "1.0.0"

# TASK-1.1.3: Criar pyproject.toml (1h)
[project]
name = "tdd-core"
version = "1.0.0"
dependencies = [
    "pydantic>=2.0",
    "typing-extensions>=4.0",
]

# TASK-1.1.4: Criar README.md arquitetural (2h)
# Documentar princípios SOLID, DDD, Clean Architecture

# TASK-1.1.5: Configurar testes de smoke (1h)
def test_module_imports():
    import tdd_core
    assert tdd_core.__version__ == "1.0.0"
```

**Estimativa:** 5 Story Points

---

### 📖 História 1.2: Extrair Entidades de Domínio
**Como** arquiteto de software  
**Quero** extrair e isolar as entidades principais do domínio  
**Para** ter objetos de negócio independentes de frameworks  

**Critérios de Aceite:**
- [ ] ProductVision entity com 15 campos obrigatórios
- [ ] Project entity com campos essenciais
- [ ] Epic entity com 56 campos incluindo IA
- [ ] Task entity com campos TDD
- [ ] Zero dependências externas (exceto stdlib)
- [ ] 100% de cobertura de testes

**Tarefas Técnicas:**

```python
# TASK-1.2.1: Criar ProductVision entity (3h)
# tdd_core/domain/entities/product_vision.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

@dataclass
class ProductVision:
    """Entidade de Visão do Produto - 15 campos obrigatórios"""
    id: Optional[int] = None
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
    constraints: str
    deliverables: str
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now()
        if not self.updated_at:
            self.updated_at = datetime.now()
    
    def validate(self) -> List[str]:
        """Valida campos obrigatórios"""
        errors = []
        required_fields = [
            'name', 'vision_statement', 'target_user', 
            'user_problem', 'expected_benefits'
        ]
        for field in required_fields:
            if not getattr(self, field):
                errors.append(f"{field} is required")
        return errors

# TASK-1.2.2: Criar Epic entity com campos IA (4h)
# tdd_core/domain/entities/epic.py
@dataclass
class Epic:
    """Entidade Epic com 56 campos incluindo IA e ordenação topológica"""
    # Campos básicos
    id: Optional[int] = None
    project_id: int
    key: str
    name: str
    description: str
    status: str = "pending"
    priority: int = 3
    
    # Campos IA (Phase 5.1)
    ai_generated: bool = False
    ai_confidence: float = 0.0  # 0.0-1.0
    complexity_score: float = 3.0  # 1.0-5.0
    effort_estimate: int = 5  # dias
    
    # Campos de ordenação topológica
    sort_order: int = 0
    unblock_potential: int = 0
    critical_path_weight: float = 0.0
    
    # Campos TDD
    tdd_phase: str = "analysis"  # analysis/red/green/refactor/review
    tdd_order: int = 1  # 1-3 prioridade dentro da fase
    
    # Timestamps
    created_at: datetime = None
    updated_at: datetime = None
    
    def calculate_priority_score(self, weights: dict) -> float:
        """Calcula score de prioridade com pesos customizados"""
        return (
            weights.get('valor', 0.4167) * self.business_value +
            weights.get('risco', 0.25) * self.risk_mitigation +
            weights.get('esforco', 0.1667) * (10 - self.effort_estimate) +
            weights.get('alinhamento', 0.1667) * self.strategic_alignment +
            weights.get('confidence', 0.0) * self.ai_confidence
        )

# TASK-1.2.3: Criar Project entity (2h)
@dataclass
class Project:
    """Entidade Project - Hub central com 78 campos"""
    id: Optional[int] = None
    name: str
    description: str
    status: str = "active"
    vision_id: Optional[int] = None
    
    # Metadados do wizard
    wizard_completed: bool = False
    current_phase: str = "roteiro"  # roteiro/capitulos/historias/tarefas
    
    # Configurações de prioridade
    use_custom_weights: bool = False
    
    # Timestamps e audit
    created_at: datetime = None
    updated_at: datetime = None
    created_by: Optional[str] = None

# TASK-1.2.4: Criar Task entity (2h)
@dataclass
class Task:
    """Entidade Task com suporte TDD"""
    id: Optional[int] = None
    epic_id: int
    key: str
    name: str
    description: str
    status: str = "todo"  # todo/in_progress/done
    tdd_status: str = "pending"  # pending/red/green/refactor
    
    # Métricas TDD
    test_coverage: float = 0.0
    tests_passing: int = 0
    tests_total: int = 0
    
    # TDAH Support
    focus_rating: Optional[int] = None  # 1-5
    interruption_count: int = 0
    energy_level: Optional[str] = None  # low/medium/high

# TASK-1.2.5: Criar testes unitários das entidades (3h)
def test_product_vision_validation():
    vision = ProductVision(name="", vision_statement="Test")
    errors = vision.validate()
    assert "name is required" in errors

def test_epic_priority_calculation():
    epic = Epic(project_id=1, key="EP-001", name="Test")
    score = epic.calculate_priority_score({'valor': 0.6})
    assert score >= 0
```

**Estimativa:** 8 Story Points

---

### 📖 História 1.3: Implementar Value Objects
**Como** desenvolvedor  
**Quero** criar value objects imutáveis para conceitos do domínio  
**Para** garantir integridade e semântica dos valores  

**Critérios de Aceite:**
- [ ] Priority VO com validação de pesos normalizados
- [ ] TddPhase VO com estados válidos
- [ ] ComplexityScore VO com range 1.0-5.0
- [ ] ConfidenceScore VO com range 0.0-1.0
- [ ] Todos VOs imutáveis (frozen dataclass ou __slots__)
- [ ] Métodos de comparação implementados

**Tarefas Técnicas:**

```python
# TASK-1.3.1: Criar Priority value object (2h)
# tdd_core/domain/value_objects/priority.py
from dataclasses import dataclass
from typing import ClassVar

@dataclass(frozen=True)
class Priority:
    """Value Object para prioridade com pesos normalizados"""
    valor: float = 0.4167  # 5/12
    risco: float = 0.25    # 3/12
    esforco: float = 0.1667  # 2/12
    alinhamento: float = 0.1667  # 2/12
    confidence: float = 0.0
    
    TOLERANCE: ClassVar[float] = 0.0001
    
    def __post_init__(self):
        # Validar que soma é ~1.0
        total = self.valor + self.risco + self.esforco + self.alinhamento + self.confidence
        if abs(total - 1.0) > self.TOLERANCE:
            raise ValueError(f"Weights must sum to 1.0, got {total}")
        
        # Validar ranges individuais
        for field in ['valor', 'risco', 'esforco', 'alinhamento', 'confidence']:
            value = getattr(self, field)
            if not 0 <= value <= 1:
                raise ValueError(f"{field} must be between 0 and 1")
    
    def to_absolute_scale(self) -> dict:
        """Converte pesos normalizados para escala absoluta (5:3:2:2)"""
        return {
            'valor': self.valor * 12,
            'risco': self.risco * 12,
            'esforco': self.esforco * 12,
            'alinhamento': self.alinhamento * 12,
            'confidence': self.confidence * 12
        }

# TASK-1.3.2: Criar TddPhase value object (1h)
@dataclass(frozen=True)
class TddPhase:
    """Value Object para fases do TDD"""
    phase: str
    
    VALID_PHASES: ClassVar[list] = [
        'analysis', 'red', 'green', 'refactor', 'review'
    ]
    
    def __post_init__(self):
        if self.phase not in self.VALID_PHASES:
            raise ValueError(f"Invalid phase: {self.phase}")
    
    def next_phase(self) -> 'TddPhase':
        """Retorna próxima fase no ciclo TDD"""
        idx = self.VALID_PHASES.index(self.phase)
        next_idx = (idx + 1) % len(self.VALID_PHASES)
        return TddPhase(self.VALID_PHASES[next_idx])
    
    def is_testing_phase(self) -> bool:
        return self.phase in ['red', 'green']

# TASK-1.3.3: Criar ComplexityScore value object (1h)
@dataclass(frozen=True)
class ComplexityScore:
    """Value Object para score de complexidade (1.0-5.0)"""
    value: float
    
    def __post_init__(self):
        if not 1.0 <= self.value <= 5.0:
            raise ValueError(f"Complexity must be between 1.0 and 5.0")
    
    def to_effort_days(self) -> int:
        """Converte complexidade em estimativa de dias"""
        # 1.0 = 1-3 dias, 5.0 = 20-30 dias
        return int(self.value * 6)
    
    def __lt__(self, other):
        return self.value < other.value

# TASK-1.3.4: Criar ConfidenceScore value object (1h)
@dataclass(frozen=True) 
class ConfidenceScore:
    """Value Object para score de confiança IA (0.0-1.0)"""
    value: float
    
    def __post_init__(self):
        if not 0.0 <= self.value <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0")
    
    def to_percentage(self) -> int:
        return int(self.value * 100)
    
    def is_high_confidence(self) -> bool:
        return self.value >= 0.8
    
    def requires_review(self) -> bool:
        return self.value < 0.6
```

**Estimativa:** 3 Story Points

---

## 🔧 ÉPICO 2: Migração dos Serviços de Aplicação
**Objetivo:** Extrair e isolar serviços de negócio, removendo dependências de infraestrutura  
**Estimativa:** 21 Story Points  
**Prioridade:** Crítica  
**Dependências:** Épico 1  

### 📖 História 2.1: Migrar VisionService
**Como** desenvolvedor  
**Quero** extrair o VisionService para a camada de aplicação  
**Para** ter lógica de visão independente do Streamlit  

**Critérios de Aceite:**
- [ ] Interface IVisionService definida
- [ ] Implementação extraída sem dependências Streamlit
- [ ] Refino de campos com IA funcionando
- [ ] Cache LRU preservado
- [ ] Testes de integração passando

**Tarefas Técnicas:**

```python
# TASK-2.1.1: Criar interface IVisionService (2h)
# tdd_core/application/services/vision_service.py
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from ..dto import ProductVisionDTO

class IVisionService(ABC):
    """Interface para serviço de visão de produto"""
    
    @abstractmethod
    def create_vision(self, data: Dict[str, Any]) -> ProductVisionDTO:
        """Cria nova visão de produto"""
        pass
    
    @abstractmethod
    def refine_field(
        self, 
        vision_id: int, 
        field_name: str, 
        current_value: str
    ) -> str:
        """Refina campo específico com IA"""
        pass
    
    @abstractmethod
    def validate_vision(self, vision: ProductVisionDTO) -> List[str]:
        """Valida visão completa"""
        pass
    
    @abstractmethod
    def generate_summary(self, vision: ProductVisionDTO) -> str:
        """Gera resumo executivo da visão"""
        pass

# TASK-2.1.2: Implementar VisionService (4h)
from functools import lru_cache
from typing import Dict, Any, List

class VisionService(IVisionService):
    """Implementação do serviço de visão"""
    
    def __init__(
        self,
        vision_repository: IVisionRepository,
        ai_service: IAIService,
        validator: ProductVisionValidator
    ):
        self.repository = vision_repository
        self.ai_service = ai_service
        self.validator = validator
    
    def create_vision(self, data: Dict[str, Any]) -> ProductVisionDTO:
        # Validar dados
        errors = self.validator.validate(data)
        if errors:
            raise ValidationError(errors)
        
        # Criar DTO
        vision_dto = ProductVisionDTO(**data)
        
        # Persistir
        vision_entity = self._dto_to_entity(vision_dto)
        saved_entity = self.repository.save(vision_entity)
        
        return self._entity_to_dto(saved_entity)
    
    @lru_cache(maxsize=128)
    def refine_field(
        self,
        vision_id: int,
        field_name: str, 
        current_value: str
    ) -> str:
        """Refina campo com IA usando cache LRU"""
        # Buscar visão completa para contexto
        vision = self.repository.find_by_id(vision_id)
        if not vision:
            raise NotFoundError(f"Vision {vision_id} not found")
        
        # Preparar contexto para IA
        context = self._build_context(vision, field_name)
        
        # Chamar serviço de IA
        refined_value = self.ai_service.refine_text(
            current_value,
            context,
            field_type=field_name
        )
        
        return refined_value
    
    def _build_context(self, vision: ProductVision, field_name: str) -> Dict:
        """Constrói contexto para refinamento IA"""
        return {
            'product_name': vision.name,
            'vision_statement': vision.vision_statement,
            'target_user': vision.target_user,
            'field_being_refined': field_name,
            'current_fields': {
                k: v for k, v in vision.__dict__.items()
                if v and k != field_name
            }
        }

# TASK-2.1.3: Migrar lógica de refinamento (3h)
class AIFieldRefiner:
    """Componente para refinamento de campos com IA"""
    
    def __init__(self, template_loader, lexicon_loader):
        self.template_loader = template_loader
        self.lexicon_loader = lexicon_loader
    
    def refine(self, field_data: Dict) -> str:
        # Carregar template apropriado
        template = self.template_loader.load_template(
            f"refine_{field_data['field_name']}.md"
        )
        
        # Aplicar lexicon do domínio
        lexicon = self.lexicon_loader.load_lexicon("domain_lexicon.yaml")
        
        # Renderizar prompt
        prompt = self.template_loader.render_template(template, field_data)
        localized_prompt = self.lexicon_loader.apply_lexicon(prompt, lexicon)
        
        return localized_prompt

# TASK-2.1.4: Criar testes de integração (2h)
def test_vision_service_refine_field():
    # Arrange
    mock_repo = Mock(IVisionRepository)
    mock_ai = Mock(IAIService)
    service = VisionService(mock_repo, mock_ai, ProductVisionValidator())
    
    # Act
    result = service.refine_field(1, "vision_statement", "Initial vision")
    
    # Assert
    assert result is not None
    mock_ai.refine_text.assert_called_once()
```

**Estimativa:** 8 Story Points

---

### 📖 História 2.2: Migrar EpicService com Ordenação Topológica
**Como** desenvolvedor  
**Quero** extrair o EpicService preservando toda lógica de priorização  
**Para** manter algoritmo de ordenação determinística independente  

**Critérios de Aceite:**
- [ ] Interface IEpicService definida
- [ ] Ordenação topológica ≤1ms (meta 0.19ms)
- [ ] Sistema de pesos por projeto funcionando
- [ ] Geração de épicos com IA preservada
- [ ] Dependências entre épicos mantidas

**Tarefas Técnicas:**

```python
# TASK-2.2.1: Criar interface IEpicService (2h)
# tdd_core/application/services/epic_service.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from ..dto import EpicSuggestionDTO, PriorityWeightsDTO

class IEpicService(ABC):
    """Interface para serviço de épicos"""
    
    @abstractmethod
    def generate_epics_from_vision(
        self,
        vision_id: int,
        count: int = 5
    ) -> List[EpicSuggestionDTO]:
        """Gera épicos via IA a partir da visão"""
        pass
    
    @abstractmethod
    def calculate_topological_order(
        self,
        epics: List[Epic],
        dependencies: Dict[int, List[int]]
    ) -> List[Epic]:
        """Ordena épicos topologicamente"""
        pass
    
    @abstractmethod
    def update_priority_weights(
        self,
        project_id: int,
        weights: PriorityWeightsDTO
    ) -> bool:
        """Atualiza pesos de prioridade do projeto"""
        pass
    
    @abstractmethod
    def get_epics_by_priority(
        self,
        project_id: int,
        use_custom_weights: bool = True
    ) -> List[Epic]:
        """Retorna épicos ordenados por prioridade"""
        pass

# TASK-2.2.2: Implementar TopologicalSorter (4h)
# tdd_core/application/services/topological_sorter.py
import heapq
from collections import defaultdict, deque
from typing import List, Dict, Tuple
import time

class DeterministicTopologicalSorter:
    """
    Implementação do algoritmo DETERMINISTIC_TOPOLOGICAL_ORDERING_DEMO
    Performance target: ≤1ms (meta 0.19ms)
    """
    
    def sort(
        self,
        epics: List[Epic],
        dependencies: Dict[int, List[int]]
    ) -> Tuple[List[Epic], float]:
        """
        Ordena épicos usando Kahn's algorithm com heap priority
        Returns: (sorted_epics, execution_time_ms)
        """
        start_time = time.perf_counter()
        
        # Construir grafo de dependências
        graph = defaultdict(list)
        in_degree = defaultdict(int)
        epic_map = {e.id: e for e in epics}
        
        for epic_id, deps in dependencies.items():
            for dep_id in deps:
                graph[dep_id].append(epic_id)
                in_degree[epic_id] += 1
        
        # Inicializar heap com épicos sem dependências
        heap = []
        for epic in epics:
            if in_degree[epic.id] == 0:
                # Priority tuple: (-score, priority, effort, key)
                score = self._calculate_score(epic)
                priority_tuple = (
                    -score,  # Negative for max-heap behavior
                    epic.priority,
                    epic.effort_estimate,
                    epic.key
                )
                heapq.heappush(heap, (priority_tuple, epic))
        
        # Processar ordenação topológica
        sorted_epics = []
        while heap:
            _, epic = heapq.heappop(heap)
            sorted_epics.append(epic)
            
            # Processar dependentes
            for dependent_id in graph[epic.id]:
                in_degree[dependent_id] -= 1
                if in_degree[dependent_id] == 0:
                    dep_epic = epic_map[dependent_id]
                    score = self._calculate_score(dep_epic)
                    priority_tuple = (
                        -score,
                        dep_epic.priority,
                        dep_epic.effort_estimate,
                        dep_epic.key
                    )
                    heapq.heappush(heap, (priority_tuple, dep_epic))
        
        # Validar que todos foram processados
        if len(sorted_epics) != len(epics):
            raise ValueError("Circular dependency detected!")
        
        # Atualizar sort_order
        for i, epic in enumerate(sorted_epics):
            epic.sort_order = i + 1
        
        execution_time = (time.perf_counter() - start_time) * 1000
        return sorted_epics, execution_time
    
    def _calculate_score(self, epic: Epic) -> float:
        """Calcula score composto para ordenação"""
        return (
            epic.priority * 10 +
            epic.unblock_potential * 5 +
            (10 - epic.effort_estimate) +
            epic.ai_confidence * 3
        )

# TASK-2.2.3: Implementar EpicService (4h)
class EpicService(IEpicService):
    """Serviço de épicos com ordenação e priorização"""
    
    def __init__(
        self,
        epic_repository: IEpicRepository,
        priority_repository: IPrioritySettingsRepository,
        ai_service: IAIService,
        sorter: DeterministicTopologicalSorter
    ):
        self.epic_repo = epic_repository
        self.priority_repo = priority_repository
        self.ai_service = ai_service
        self.sorter = sorter
    
    def generate_epics_from_vision(
        self,
        vision_id: int,
        count: int = 5
    ) -> List[EpicSuggestionDTO]:
        """Gera épicos via IA com campos completos"""
        # Buscar visão
        vision = self.vision_repo.find_by_id(vision_id)
        
        # Preparar prompt
        prompt = self._build_epic_generation_prompt(vision, count)
        
        # Chamar IA
        ai_response = self.ai_service.generate_epics(prompt)
        
        # Parsear resposta em DTOs
        epic_suggestions = []
        for epic_data in ai_response['epics']:
            dto = EpicSuggestionDTO(
                name=epic_data['name'],
                description=epic_data['description'],
                complexity_score=epic_data.get('complexity', 3.0),
                effort_estimate=epic_data.get('effort', 5),
                ai_confidence=epic_data.get('confidence', 0.8),
                dependencies=epic_data.get('dependencies', []),
                unblock_potential=epic_data.get('unblock_potential', 0)
            )
            epic_suggestions.append(dto)
        
        # Calcular ordem topológica
        dependencies = self._extract_dependencies(epic_suggestions)
        sorted_epics, exec_time = self.sorter.sort(
            epic_suggestions, 
            dependencies
        )
        
        print(f"Topological sort completed in {exec_time:.2f}ms")
        
        return sorted_epics
    
    def update_priority_weights(
        self,
        project_id: int,
        weights: PriorityWeightsDTO
    ) -> bool:
        """Atualiza pesos com validação História 3.2"""
        # Validar soma ~1.0
        total = sum([
            weights.valor_weight,
            weights.risco_weight,
            weights.esforco_weight,
            weights.alinhamento_weight,
            weights.confidence_weight
        ])
        
        if abs(total - 1.0) > 0.0001:
            raise ValueError(f"Weights must sum to 1.0, got {total}")
        
        # Persistir
        return self.priority_repo.upsert(project_id, weights)

# TASK-2.2.4: Criar testes de performance (2h)
def test_topological_sort_performance():
    """Valida meta de 0.19ms para 7 épicos com 8 dependências"""
    # Setup E-commerce dummy project
    epics = [
        Epic(id=1, key="ECOM_001", name="Database Setup"),
        Epic(id=2, key="ECOM_002", name="User Auth"),
        Epic(id=3, key="ECOM_003", name="Product Catalog"),
        Epic(id=4, key="ECOM_004", name="Shopping Cart"),
        Epic(id=5, key="ECOM_005", name="Payment System"),
        Epic(id=6, key="ECOM_006", name="Admin Dashboard"),
        Epic(id=7, key="ECOM_007", name="API Documentation"),
    ]
    
    dependencies = {
        2: [1],  # Auth depends on DB
        3: [1],  # Catalog depends on DB
        4: [2, 3],  # Cart depends on Auth + Catalog
        5: [4],  # Payment depends on Cart
        6: [1, 2, 3, 4, 5],  # Admin depends on all
        7: []  # API Doc is independent
    }
    
    sorter = DeterministicTopologicalSorter()
    sorted_epics, exec_time = sorter.sort(epics, dependencies)
    
    # Assertions
    assert exec_time <= 1.0  # Must be under 1ms
    assert sorted_epics[0].key == "ECOM_001"  # DB first
    assert sorted_epics[-1].key == "ECOM_006"  # Admin last
    print(f"✅ Performance: {exec_time:.2f}ms (target: 0.19ms)")
```

**Estimativa:** 8 Story Points

---

### 📖 História 2.3: Migrar AIService com Configurações
**Como** desenvolvedor  
**Quero** extrair serviço de IA com templates e lexicons  
**Para** ter geração de conteúdo independente e configurável  

**Critérios de Aceite:**
- [ ] Interface IAIService definida
- [ ] PromptTemplateLoader migrado
- [ ] DomainLexiconLoader migrado
- [ ] MockAIService para desenvolvimento
- [ ] Cache LRU funcionando

**Tarefas Técnicas:**

```python
# TASK-2.3.1: Criar interface IAIService (1h)
# tdd_core/application/services/ai_service.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class IAIService(ABC):
    """Interface para serviço de IA"""
    
    @abstractmethod
    def refine_text(
        self,
        text: str,
        context: Dict[str, Any],
        field_type: str
    ) -> str:
        """Refina texto com IA"""
        pass
    
    @abstractmethod
    def generate_epics(
        self,
        vision_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Gera sugestões de épicos"""
        pass
    
    @abstractmethod
    def analyze_complexity(
        self,
        epic_description: str
    ) -> float:
        """Analisa complexidade (1.0-5.0)"""
        pass

# TASK-2.3.2: Migrar PromptTemplateLoader (2h)
# tdd_core/infrastructure/ai/prompt_template_loader.py
from functools import lru_cache
from string import Formatter
from pathlib import Path

class PromptTemplateLoader:
    """Carregador de templates com cache e validação"""
    
    def __init__(self, templates_dir: Path, enable_cache: bool = True):
        self.templates_dir = templates_dir
        self.enable_cache = enable_cache
        self._formatter = Formatter()
    
    @lru_cache(maxsize=32)
    def load_template(self, template_name: str) -> str:
        """Carrega template do arquivo"""
        template_path = self.templates_dir / template_name
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_name}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Validar sintaxe
        self._validate_syntax(content)
        return content
    
    def _validate_syntax(self, template: str) -> None:
        """Valida sintaxe do template"""
        try:
            # Check for valid placeholders
            placeholders = [
                field_name 
                for _, field_name, _, _ in self._formatter.parse(template)
                if field_name is not None
            ]
        except ValueError as e:
            raise ValueError(f"Invalid template syntax: {e}")
    
    def render_template(
        self,
        template: str,
        variables: Dict[str, Any]
    ) -> str:
        """Renderiza template com variáveis"""
        try:
            return template.format(**variables)
        except KeyError as e:
            raise ValueError(f"Missing template variable: {e}")

# TASK-2.3.3: Migrar DomainLexiconLoader (2h)
# tdd_core/infrastructure/ai/domain_lexicon_loader.py
import yaml
import re
from functools import lru_cache

class DomainLexiconLoader:
    """Carregador de léxico do domínio"""
    
    def __init__(self, config_dir: Path, enable_cache: bool = True):
        self.config_dir = config_dir
        self.enable_cache = enable_cache
    
    @lru_cache(maxsize=16)
    def load_lexicon(self, lexicon_file: str) -> Dict[str, str]:
        """Carrega léxico do arquivo YAML"""
        lexicon_path = self.config_dir / lexicon_file
        
        with open(lexicon_path, 'r', encoding='utf-8') as f:
            lexicon = yaml.safe_load(f)
        
        # Validar estrutura
        self._validate_lexicon_structure(lexicon)
        
        # Mesclar com léxico padrão
        default_lexicon = self._load_default_lexicon()
        return {**default_lexicon, **lexicon}
    
    def apply_lexicon(self, text: str, lexicon: Dict[str, str]) -> str:
        """Aplica traduções do léxico preservando case"""
        result = text
        
        for term, translation in lexicon.items():
            # Criar regex com word boundaries
            pattern = r'\b' + re.escape(term) + r'\b'
            
            # Substituir preservando capitalização
            def replace_func(match):
                original = match.group()
                if original.isupper():
                    return translation.upper()
                elif original[0].isupper():
                    return translation.capitalize()
                else:
                    return translation
            
            result = re.sub(pattern, replace_func, result, flags=re.IGNORECASE)
        
        return result
    
    def _load_default_lexicon(self) -> Dict[str, str]:
        """Carrega léxico padrão PT-BR"""
        return {
            'epic': 'capítulo',
            'task': 'tarefa',
            'story': 'história',
            'sprint': 'ciclo',
            'backlog': 'pendências',
            'workflow': 'fluxo de trabalho'
        }

# TASK-2.3.4: Criar MockAIService (2h)
class MockAIService(IAIService):
    """Mock service para desenvolvimento sem API keys"""
    
    def refine_text(
        self,
        text: str,
        context: Dict[str, Any],
        field_type: str
    ) -> str:
        """Simula refinamento com melhorias pré-definidas"""
        improvements = {
            'vision_statement': ' [Refined: More clear and focused]',
            'target_user': ' [Refined: Better defined personas]',
            'success_metrics': ' [Refined: SMART metrics added]'
        }
        
        improvement = improvements.get(field_type, ' [Refined]')
        return text + improvement
    
    def generate_epics(
        self,
        vision_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Gera épicos mock baseados no contexto"""
        return [
            {
                'name': 'Setup Infrastructure',
                'description': 'Database and core services setup',
                'complexity': 2.0,
                'effort': 3,
                'confidence': 0.9,
                'dependencies': [],
                'unblock_potential': 3
            },
            {
                'name': 'User Authentication',
                'description': 'OAuth and session management',
                'complexity': 3.5,
                'effort': 5,
                'confidence': 0.85,
                'dependencies': [0],
                'unblock_potential': 2
            },
            {
                'name': 'Core Features',
                'description': 'Main product functionality',
                'complexity': 4.0,
                'effort': 8,
                'confidence': 0.75,
                'dependencies': [0, 1],
                'unblock_potential': 1
            }
        ]
```

**Estimativa:** 5 Story Points

---

## 🔌 ÉPICO 3: Criação de Adapters e Integração
**Objetivo:** Criar camada de adaptação para manter Streamlit funcionando com novo núcleo  
**Estimativa:** 13 Story Points  
**Prioridade:** Crítica  
**Dependências:** Épicos 1 e 2  

### 📖 História 3.1: Criar Streamlit Adapter
**Como** desenvolvedor  
**Quero** criar adapter que conecta Streamlit ao tdd_core  
**Para** manter aplicação funcionando sem alterações na UI  

**Critérios de Aceite:**
- [ ] StreamlitAdapter criado e funcional
- [ ] Session state mapeado para domínio
- [ ] ServiceContainer adaptado
- [ ] Zero breaking changes na UI
- [ ] Fluxo wizard completo funcionando

**Tarefas Técnicas:**

```python
# TASK-3.1.1: Criar StreamlitAdapter principal (3h)
# tdd_core/infrastructure/adapters/streamlit_adapter.py
import streamlit as st
from typing import Any, Dict, Optional
from ...application.services import ServiceContainer as CoreContainer

class StreamlitAdapter:
    """Adapter para conectar Streamlit ao tdd_core"""
    
    def __init__(self):
        self.core_container = CoreContainer()
        self._init_session_state()
    
    def _init_session_state(self):
        """Inicializa session state com valores padrão"""
        if 'wizard_state' not in st.session_state:
            st.session_state.wizard_state = {
                'current_phase': 'roteiro',
                'product_vision': {},
                'epics': [],
                'tasks': []
            }
    
    def get_vision_service(self):
        """Retorna VisionService adaptado"""
        return StreamlitVisionServiceAdapter(
            self.core_container.get_vision_service(),
            st.session_state
        )
    
    def get_epic_service(self):
        """Retorna EpicService adaptado"""
        return StreamlitEpicServiceAdapter(
            self.core_container.get_epic_service(),
            st.session_state
        )
    
    def sync_state_to_domain(self):
        """Sincroniza session state com domínio"""
        wizard_state = st.session_state.wizard_state
        
        # Mapear vision
        if wizard_state.get('product_vision'):
            vision_dto = self._map_vision_to_dto(
                wizard_state['product_vision']
            )
            self.core_container.set_current_vision(vision_dto)
        
        # Mapear epics
        if wizard_state.get('epics'):
            epic_dtos = [
                self._map_epic_to_dto(epic)
                for epic in wizard_state['epics']
            ]
            self.core_container.set_current_epics(epic_dtos)
    
    def sync_domain_to_state(self):
        """Sincroniza domínio com session state"""
        # Atualizar vision
        current_vision = self.core_container.get_current_vision()
        if current_vision:
            st.session_state.wizard_state['product_vision'] = (
                self._map_dto_to_vision(current_vision)
            )
        
        # Atualizar epics
        current_epics = self.core_container.get_current_epics()
        if current_epics:
            st.session_state.wizard_state['epics'] = [
                self._map_dto_to_epic(epic)
                for epic in current_epics
            ]

# TASK-3.1.2: Criar adapter para VisionService (2h)
class StreamlitVisionServiceAdapter:
    """Adapter específico para VisionService"""
    
    def __init__(self, core_service, session_state):
        self.core_service = core_service
        self.session_state = session_state
    
    def refine_field(self, field_name: str) -> str:
        """Refina campo usando valores do session state"""
        vision_data = self.session_state.wizard_state['product_vision']
        current_value = vision_data.get(field_name, '')
        
        # Converter para formato do core
        vision_dto = ProductVisionDTO(**vision_data)
        
        # Chamar core service
        refined_value = self.core_service.refine_field(
            vision_dto.id or 0,
            field_name,
            current_value
        )
        
        # Atualizar session state
        vision_data[field_name] = refined_value
        
        return refined_value
    
    def validate_current_vision(self) -> List[str]:
        """Valida visão atual do session state"""
        vision_data = self.session_state.wizard_state['product_vision']
        
        if not vision_data:
            return ["No vision data found"]
        
        vision_dto = ProductVisionDTO(**vision_data)
        return self.core_service.validate_vision(vision_dto)

# TASK-3.1.3: Adaptar ServiceContainer existente (2h)
# streamlit_extension/services/service_container.py
from tdd_core.infrastructure.adapters import StreamlitAdapter

class ServiceContainer:
    """Container adaptado para usar tdd_core"""
    
    _instance = None
    _adapter = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._adapter = StreamlitAdapter()
        return cls._instance
    
    def get_vision_service(self):
        """Retorna VisionService do core via adapter"""
        return self._adapter.get_vision_service()
    
    def get_epic_service(self):
        """Retorna EpicService do core via adapter"""  
        return self._adapter.get_epic_service()
    
    def get_analytics_service(self):
        """Mantém serviço legado por enquanto"""
        # TODO: Migrar em fase posterior
        return self._legacy_analytics_service

# TASK-3.1.4: Testar fluxo completo wizard (2h)
def test_wizard_flow_with_adapter():
    """Testa fluxo Roteiro→Capítulos com adapter"""
    # Setup
    adapter = StreamlitAdapter()
    
    # Simular preenchimento da visão
    st.session_state.wizard_state['product_vision'] = {
        'name': 'Test Product',
        'vision_statement': 'Revolutionary solution',
        'target_user': 'Developers',
        # ... outros campos
    }
    
    # Sincronizar com domínio
    adapter.sync_state_to_domain()
    
    # Gerar épicos
    epic_service = adapter.get_epic_service()
    epics = epic_service.generate_epics_from_vision(1)
    
    # Validar resultado
    assert len(epics) >= 3
    assert all(e.ai_generated for e in epics)
    
    # Sincronizar volta
    adapter.sync_domain_to_state()
    assert len(st.session_state.wizard_state['epics']) >= 3
```

**Estimativa:** 5 Story Points

---

### 📖 História 3.2: Criar Mapeadores DTO ↔ Entity
**Como** desenvolvedor  
**Quero** criar mapeadores bidirecionais entre DTOs e Entities  
**Para** traduzir dados entre camadas mantendo integridade  

**Critérios de Aceite:**
- [ ] Mapeadores para todas entidades principais
- [ ] Validação durante mapeamento
- [ ] Type hints completos
- [ ] Tratamento de campos opcionais
- [ ] Testes de ida e volta (roundtrip)

**Tarefas Técnicas:**

```python
# TASK-3.2.1: Criar base mapper genérico (2h)
# tdd_core/infrastructure/mappers/base_mapper.py
from abc import ABC, abstractmethod
from typing import TypeVar, Generic

TEntity = TypeVar('TEntity')
TDto = TypeVar('TDto')

class BaseMapper(ABC, Generic[TEntity, TDto]):
    """Mapper base para conversão Entity ↔ DTO"""
    
    @abstractmethod
    def to_dto(self, entity: TEntity) -> TDto:
        """Converte Entity para DTO"""
        pass
    
    @abstractmethod
    def to_entity(self, dto: TDto) -> TEntity:
        """Converte DTO para Entity"""
        pass
    
    def to_dto_list(self, entities: List[TEntity]) -> List[TDto]:
        """Converte lista de entities para DTOs"""
        return [self.to_dto(e) for e in entities]
    
    def to_entity_list(self, dtos: List[TDto]) -> List[TEntity]:
        """Converte lista de DTOs para entities"""
        return [self.to_entity(d) for d in dtos]

# TASK-3.2.2: Implementar ProductVisionMapper (2h)
# tdd_core/infrastructure/mappers/product_vision_mapper.py
from datetime import datetime
from ...domain.entities import ProductVision
from ...application.dto import ProductVisionDTO

class ProductVisionMapper(BaseMapper[ProductVision, ProductVisionDTO]):
    """Mapper para ProductVision ↔ ProductVisionDTO"""
    
    def to_dto(self, entity: ProductVision) -> ProductVisionDTO:
        """Entity → DTO com validação"""
        return ProductVisionDTO(
            id=entity.id,
            name=entity.name,
            vision_statement=entity.vision_statement,
            target_user=entity.target_user,
            user_problem=entity.user_problem,
            expected_benefits=entity.expected_benefits,
            product_description=entity.product_description,
            success_metrics=entity.success_metrics,
            tech_requirements=entity.tech_requirements,
            non_functional_requirements=entity.non_functional_requirements,
            compliance_requirements=entity.compliance_requirements,
            risks=entity.risks,
            assumptions=entity.assumptions,
            constraints=entity.constraints,
            deliverables=entity.deliverables,
            created_at=entity.created_at.isoformat() if entity.created_at else None,
            updated_at=entity.updated_at.isoformat() if entity.updated_at else None
        )
    
    def to_entity(self, dto: ProductVisionDTO) -> ProductVision:
        """DTO → Entity com validação"""
        entity = ProductVision(
            id=dto.id,
            name=dto.name,
            vision_statement=dto.vision_statement,
            target_user=dto.target_user,
            user_problem=dto.user_problem,
            expected_benefits=dto.expected_benefits,
            product_description=dto.product_description,
            success_metrics=dto.success_metrics,
            tech_requirements=dto.tech_requirements,
            non_functional_requirements=dto.non_functional_requirements,
            compliance_requirements=dto.compliance_requirements,
            risks=dto.risks,
            assumptions=dto.assumptions,
            constraints=dto.constraints,
            deliverables=dto.deliverables
        )
        
        # Validar entidade
        errors = entity.validate()
        if errors:
            raise ValueError(f"Invalid entity: {errors}")
        
        return entity

# TASK-3.2.3: Implementar EpicMapper com campos IA (3h)
# tdd_core/infrastructure/mappers/epic_mapper.py
from ...domain.entities import Epic
from ...domain.value_objects import ComplexityScore, ConfidenceScore, TddPhase
from ...application.dto import EpicSuggestionDTO

class EpicMapper(BaseMapper[Epic, EpicSuggestionDTO]):
    """Mapper para Epic ↔ EpicSuggestionDTO com campos IA"""
    
    def to_dto(self, entity: Epic) -> EpicSuggestionDTO:
        """Entity → DTO preservando campos IA"""
        return EpicSuggestionDTO(
            id=entity.id,
            project_id=entity.project_id,
            key=entity.key,
            name=entity.name,
            description=entity.description,
            status=entity.status,
            priority=entity.priority,
            
            # Campos IA
            ai_generated=entity.ai_generated,
            ai_confidence=entity.ai_confidence,
            complexity_score=entity.complexity_score,
            effort_estimate=entity.effort_estimate,
            
            # Ordenação topológica
            sort_order=entity.sort_order,
            unblock_potential=entity.unblock_potential,
            critical_path_weight=entity.critical_path_weight,
            dependencies=self._extract_dependencies(entity),
            
            # TDD
            tdd_phase=entity.tdd_phase,
            tdd_order=entity.tdd_order,
            
            # Timestamps
            created_at=entity.created_at.isoformat() if entity.created_at else None,
            updated_at=entity.updated_at.isoformat() if entity.updated_at else None
        )
    
    def to_entity(self, dto: EpicSuggestionDTO) -> Epic:
        """DTO → Entity com value objects"""
        entity = Epic(
            id=dto.id,
            project_id=dto.project_id,
            key=dto.key,
            name=dto.name,
            description=dto.description,
            status=dto.status,
            priority=dto.priority,
            
            # Campos IA com value objects
            ai_generated=dto.ai_generated,
            ai_confidence=ConfidenceScore(dto.ai_confidence).value,
            complexity_score=ComplexityScore(dto.complexity_score).value,
            effort_estimate=dto.effort_estimate,
            
            # Ordenação
            sort_order=dto.sort_order,
            unblock_potential=dto.unblock_potential,
            critical_path_weight=dto.critical_path_weight,
            
            # TDD com value object
            tdd_phase=TddPhase(dto.tdd_phase).phase,
            tdd_order=dto.tdd_order
        )
        
        return entity
    
    def _extract_dependencies(self, entity: Epic) -> List[int]:
        """Extrai IDs de dependências do epic"""
        # TODO: Implementar com repository de dependências
        return []

# TASK-3.2.4: Criar testes de roundtrip (1h)
def test_product_vision_mapper_roundtrip():
    """Testa conversão ida e volta Entity ↔ DTO"""
    # Create entity
    entity = ProductVision(
        name="Test Product",
        vision_statement="Revolutionary solution",
        target_user="Developers",
        user_problem="Complex workflows",
        expected_benefits="10x productivity"
        # ... outros campos
    )
    
    # Map to DTO and back
    mapper = ProductVisionMapper()
    dto = mapper.to_dto(entity)
    entity_back = mapper.to_entity(dto)
    
    # Assert equivalence
    assert entity.name == entity_back.name
    assert entity.vision_statement == entity_back.vision_statement
    assert entity.target_user == entity_back.target_user

def test_epic_mapper_preserves_ai_fields():
    """Testa preservação de campos IA no mapeamento"""
    entity = Epic(
        project_id=1,
        key="EP-001",
        name="Test Epic",
        ai_generated=True,
        ai_confidence=0.85,
        complexity_score=3.5,
        effort_estimate=5
    )
    
    mapper = EpicMapper()
    dto = mapper.to_dto(entity)
    
    assert dto.ai_generated == True
    assert dto.ai_confidence == 0.85
    assert dto.complexity_score == 3.5
    assert dto.effort_estimate == 5
```

**Estimativa:** 4 Story Points

---

### 📖 História 3.3: Implementar Repositórios do Domínio
**Como** desenvolvedor  
**Quero** criar repositórios com interfaces do domínio  
**Para** persistir entidades mantendo separação de concerns  

**Critérios de Aceite:**
- [ ] Interfaces de repositório no domínio
- [ ] Implementações SQLite na infraestrutura
- [ ] Transações ACID garantidas
- [ ] Foreign keys e constraints preservados
- [ ] Performance <10ms mantida

**Tarefas Técnicas:**

```python
# TASK-3.3.1: Definir interfaces de repositório (2h)
# tdd_core/domain/repositories/project_repository.py
from abc import ABC, abstractmethod
from typing import Optional, List
from ..entities import Project

class IProjectRepository(ABC):
    """Interface para repositório de projetos"""
    
    @abstractmethod
    def find_by_id(self, project_id: int) -> Optional[Project]:
        """Busca projeto por ID"""
        pass
    
    @abstractmethod
    def find_all(self, status: Optional[str] = None) -> List[Project]:
        """Lista projetos com filtro opcional"""
        pass
    
    @abstractmethod
    def save(self, project: Project) -> Project:
        """Salva ou atualiza projeto"""
        pass
    
    @abstractmethod
    def delete(self, project_id: int) -> bool:
        """Remove projeto (soft delete)"""
        pass
    
    @abstractmethod
    def find_by_vision_id(self, vision_id: int) -> Optional[Project]:
        """Busca projeto por vision_id"""
        pass

# tdd_core/domain/repositories/epic_repository.py
class IEpicRepository(ABC):
    """Interface para repositório de épicos"""
    
    @abstractmethod
    def find_by_project(
        self,
        project_id: int,
        include_archived: bool = False
    ) -> List[Epic]:
        """Lista épicos do projeto"""
        pass
    
    @abstractmethod
    def save_batch(self, epics: List[Epic]) -> List[Epic]:
        """Salva múltiplos épicos em transação"""
        pass
    
    @abstractmethod
    def update_sort_order(
        self,
        project_id: int,
        epic_orders: Dict[int, int]
    ) -> bool:
        """Atualiza ordem de múltiplos épicos atomicamente"""
        pass
    
    @abstractmethod
    def get_dependencies(self, epic_id: int) -> List[int]:
        """Retorna IDs de épicos dependentes"""
        pass
    
    @abstractmethod
    def save_dependencies(
        self,
        epic_id: int,
        dependency_ids: List[int]
    ) -> bool:
        """Salva dependências do épico"""
        pass

# TASK-3.3.2: Implementar SQLiteProjectRepository (3h)
# tdd_core/infrastructure/repositories/sqlite_project_repository.py
import sqlite3
from contextlib import contextmanager
from typing import Optional, List
from ...domain.entities import Project
from ...domain.repositories import IProjectRepository

class SQLiteProjectRepository(IProjectRepository):
    """Implementação SQLite do repositório de projetos"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Inicializa schema se necessário"""
        with self._get_connection() as conn:
            # Usar schema existente da Phase 5.1
            conn.execute("PRAGMA foreign_keys = ON")
    
    @contextmanager
    def _get_connection(self):
        """Context manager para conexões"""
        conn = sqlite3.connect(
            self.db_path,
            isolation_level='IMMEDIATE'  # Transações ACID
        )
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def find_by_id(self, project_id: int) -> Optional[Project]:
        """Busca com <10ms de latência"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM framework_projects 
                WHERE id = ? AND deleted_at IS NULL
                """,
                (project_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return self._row_to_entity(row)
            return None
    
    def save(self, project: Project) -> Project:
        """Insert ou Update com RETURNING"""
        with self._get_connection() as conn:
            if project.id:
                # Update
                cursor = conn.execute(
                    """
                    UPDATE framework_projects 
                    SET name = ?, description = ?, status = ?,
                        vision_id = ?, wizard_completed = ?,
                        current_phase = ?, use_custom_weights = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    RETURNING *
                    """,
                    (
                        project.name, project.description,
                        project.status, project.vision_id,
                        project.wizard_completed, project.current_phase,
                        project.use_custom_weights, project.id
                    )
                )
            else:
                # Insert
                cursor = conn.execute(
                    """
                    INSERT INTO framework_projects (
                        name, description, status, vision_id,
                        wizard_completed, current_phase,
                        use_custom_weights, created_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    RETURNING *
                    """,
                    (
                        project.name, project.description,
                        project.status, project.vision_id,
                        project.wizard_completed, project.current_phase,
                        project.use_custom_weights, project.created_by
                    )
                )
            
            row = cursor.fetchone()
            return self._row_to_entity(row)
    
    def _row_to_entity(self, row: sqlite3.Row) -> Project:
        """Converte row SQLite para Entity"""
        return Project(
            id=row['id'],
            name=row['name'],
            description=row['description'],
            status=row['status'],
            vision_id=row['vision_id'],
            wizard_completed=bool(row['wizard_completed']),
            current_phase=row['current_phase'],
            use_custom_weights=bool(row['use_custom_weights']),
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            created_by=row['created_by']
        )

# TASK-3.3.3: Implementar SQLiteEpicRepository (3h)
class SQLiteEpicRepository(IEpicRepository):
    """Repositório de épicos com suporte a ordenação topológica"""
    
    def save_batch(self, epics: List[Epic]) -> List[Epic]:
        """Salva múltiplos épicos em transação única"""
        with self._get_connection() as conn:
            saved_epics = []
            
            for epic in epics:
                cursor = conn.execute(
                    """
                    INSERT INTO framework_epics (
                        project_id, key, name, description,
                        status, priority, ai_generated,
                        ai_confidence, complexity_score,
                        effort_estimate, sort_order,
                        unblock_potential, critical_path_weight,
                        tdd_phase, tdd_order
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    RETURNING *
                    """,
                    (
                        epic.project_id, epic.key, epic.name,
                        epic.description, epic.status, epic.priority,
                        epic.ai_generated, epic.ai_confidence,
                        epic.complexity_score, epic.effort_estimate,
                        epic.sort_order, epic.unblock_potential,
                        epic.critical_path_weight, epic.tdd_phase,
                        epic.tdd_order
                    )
                )
                
                row = cursor.fetchone()
                saved_epics.append(self._row_to_entity(row))
            
            return saved_epics
    
    def update_sort_order(
        self,
        project_id: int,
        epic_orders: Dict[int, int]
    ) -> bool:
        """Atualiza ordem atomicamente com lock"""
        with self._get_connection() as conn:
            # Lock project para evitar condições de corrida
            conn.execute(
                "SELECT * FROM framework_projects WHERE id = ? FOR UPDATE",
                (project_id,)
            )
            
            # Atualizar ordens
            for epic_id, order in epic_orders.items():
                conn.execute(
                    """
                    UPDATE framework_epics 
                    SET sort_order = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND project_id = ?
                    """,
                    (order, epic_id, project_id)
                )
            
            return True

# TASK-3.3.4: Criar testes de repositório (2h)
def test_project_repository_crud():
    """Testa operações CRUD do repositório"""
    repo = SQLiteProjectRepository(":memory:")
    
    # Create
    project = Project(
        name="Test Project",
        description="Test Description",
        status="active"
    )
    saved = repo.save(project)
    assert saved.id is not None
    
    # Read
    found = repo.find_by_id(saved.id)
    assert found.name == "Test Project"
    
    # Update
    found.description = "Updated Description"
    updated = repo.save(found)
    assert updated.description == "Updated Description"
    
    # Delete
    deleted = repo.delete(saved.id)
    assert deleted == True
    assert repo.find_by_id(saved.id) is None

def test_epic_repository_batch_save():
    """Testa salvamento em lote com transação"""
    repo = SQLiteEpicRepository(":memory:")
    
    epics = [
        Epic(project_id=1, key=f"EP-{i:03d}", name=f"Epic {i}")
        for i in range(1, 6)
    ]
    
    saved = repo.save_batch(epics)
    assert len(saved) == 5
    assert all(e.id is not None for e in saved)
```

**Estimativa:** 4 Story Points

---

## 🧪 ÉPICO 4: Validação e Migração de DTOs
**Objetivo:** Migrar DTOs existentes preservando validações e compatibilidade  
**Estimativa:** 8 Story Points  
**Prioridade:** Alta  
**Dependências:** Épicos 1, 2 e 3  

### 📖 História 4.1: Migrar ProductVisionDTO
**Como** desenvolvedor  
**Quero** migrar ProductVisionDTO com suas validações  
**Para** manter integridade de dados no novo núcleo  

**Critérios de Aceite:**
- [ ] ProductVisionDTO migrado para application/dto
- [ ] 15 campos obrigatórios validados
- [ ] Validators independentes funcionando
- [ ] Compatibilidade com código existente
- [ ] Testes unitários passando

**Tarefas Técnicas:**

```python
# TASK-4.1.1: Migrar ProductVisionDTO (2h)
# tdd_core/application/dto/product_vision_dto.py
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime

@dataclass
class ProductVisionDTO:
    """
    DTO para Visão do Produto - História 1.1
    15 campos obrigatórios + metadata
    """
    # Campos obrigatórios (15)
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
    constraints: str
    deliverables: str
    
    # Campos opcionais e metadata
    id: Optional[int] = None
    project_id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    # Campos de refinamento IA
    refinement_status: Dict[str, bool] = field(default_factory=dict)
    ai_suggestions: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validação pós-inicialização"""
        self._validate_required_fields()
        self._normalize_timestamps()
    
    def _validate_required_fields(self):
        """Valida que campos obrigatórios não estão vazios"""
        required = [
            'name', 'vision_statement', 'target_user',
            'user_problem', 'expected_benefits', 'product_description',
            'success_metrics', 'tech_requirements',
            'non_functional_requirements', 'compliance_requirements',
            'risks', 'assumptions', 'constraints', 'deliverables'
        ]
        
        empty_fields = [
            field for field in required
            if not getattr(self, field, '').strip()
        ]
        
        if empty_fields:
            raise ValueError(
                f"Required fields cannot be empty: {', '.join(empty_fields)}"
            )
    
    def _normalize_timestamps(self):
        """Normaliza timestamps para ISO format"""
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte DTO para dicionário"""
        return {
            k: v for k, v in self.__dict__.items()
            if not k.startswith('_')
        }
    
    def get_completion_percentage(self) -> float:
        """Calcula percentual de campos refinados"""
        total_fields = 15
        refined_count = sum(
            1 for refined in self.refinement_status.values()
            if refined
        )
        return (refined_count / total_fields) * 100

# TASK-4.1.2: Migrar ProductVisionValidator (2h)
# tdd_core/application/validators/product_vision_validator.py
from typing import Dict, Any, List
import re

class ProductVisionValidator:
    """Validador para ProductVisionDTO"""
    
    MIN_LENGTH = {
        'name': 3,
        'vision_statement': 20,
        'target_user': 10,
        'user_problem': 20,
        'expected_benefits': 20
    }
    
    MAX_LENGTH = {
        'name': 100,
        'vision_statement': 500,
        'target_user': 200,
        'user_problem': 500,
        'expected_benefits': 500
    }
    
    def validate(self, data: Dict[str, Any]) -> List[str]:
        """Valida dados da visão"""
        errors = []
        
        # Validar campos obrigatórios
        errors.extend(self._validate_required_fields(data))
        
        # Validar comprimentos
        errors.extend(self._validate_lengths(data))
        
        # Validar formatos específicos
        errors.extend(self._validate_formats(data))
        
        # Validar conteúdo semântico
        errors.extend(self._validate_semantic_content(data))
        
        return errors
    
    def _validate_required_fields(self, data: Dict[str, Any]) -> List[str]:
        """Valida presença de campos obrigatórios"""
        errors = []
        required_fields = [
            'name', 'vision_statement', 'target_user',
            'user_problem', 'expected_benefits', 'product_description',
            'success_metrics', 'tech_requirements',
            'non_functional_requirements', 'compliance_requirements',
            'risks', 'assumptions', 'constraints', 'deliverables'
        ]
        
        for field in required_fields:
            if field not in data or not str(data.get(field, '')).strip():
                errors.append(f"{field} is required")
        
        return errors
    
    def _validate_lengths(self, data: Dict[str, Any]) -> List[str]:
        """Valida comprimentos min/max"""
        errors = []
        
        for field, min_len in self.MIN_LENGTH.items():
            value = str(data.get(field, ''))
            if len(value) < min_len:
                errors.append(
                    f"{field} must be at least {min_len} characters"
                )
        
        for field, max_len in self.MAX_LENGTH.items():
            value = str(data.get(field, ''))
            if len(value) > max_len:
                errors.append(
                    f"{field} must not exceed {max_len} characters"
                )
        
        return errors
    
    def _validate_formats(self, data: Dict[str, Any]) -> List[str]:
        """Valida formatos específicos (e.g., métricas SMART)"""
        errors = []
        
        # Validar métricas de sucesso (devem ter números)
        metrics = data.get('success_metrics', '')
        if metrics and not re.search(r'\d', metrics):
            errors.append(
                "success_metrics should contain measurable values"
            )
        
        # Validar requisitos técnicos (devem ter termos técnicos)
        tech_req = data.get('tech_requirements', '')
        tech_terms = ['api', 'database', 'server', 'client', 'framework']
        if tech_req and not any(term in tech_req.lower() for term in tech_terms):
            errors.append(
                "tech_requirements should mention technical components"
            )
        
        return errors
    
    def _validate_semantic_content(self, data: Dict[str, Any]) -> List[str]:
        """Valida conteúdo semântico e consistência"""
        errors = []
        
        # Vision não deve ser igual ao problema
        if data.get('vision_statement') == data.get('user_problem'):
            errors.append(
                "vision_statement should be different from user_problem"
            )
        
        # Benefícios devem endereçar o problema
        problem = str(data.get('user_problem', '')).lower()
        benefits = str(data.get('expected_benefits', '')).lower()
        
        # Verificar alguma relação semântica
        problem_keywords = set(problem.split())
        benefits_keywords = set(benefits.split())
        
        if problem_keywords and benefits_keywords:
            overlap = problem_keywords & benefits_keywords
            if len(overlap) < 2:  # Muito pouca relação
                errors.append(
                    "expected_benefits should address the user_problem"
                )
        
        return errors

# TASK-4.1.3: Atualizar imports no adapter (1h)
# tdd_core/infrastructure/adapters/dto_adapter.py
from ...application.dto import ProductVisionDTO as CoreProductVisionDTO
from ...application.validators import ProductVisionValidator as CoreValidator

class DTOAdapter:
    """Adapter para compatibilidade com DTOs legados"""
    
    @staticmethod
    def adapt_legacy_vision_data(legacy_data: Dict) -> CoreProductVisionDTO:
        """Adapta dados legados para novo DTO"""
        # Mapear campos com nomes diferentes
        adapted_data = {
            'name': legacy_data.get('product_name', legacy_data.get('name')),
            'vision_statement': legacy_data.get('vision', 
                                               legacy_data.get('vision_statement')),
            'target_user': legacy_data.get('target_audience',
                                          legacy_data.get('target_user')),
            # ... mapear outros campos
        }
        
        # Preencher campos faltantes com defaults
        for field in CoreProductVisionDTO.__dataclass_fields__:
            if field not in adapted_data:
                adapted_data[field] = legacy_data.get(field, '')
        
        return CoreProductVisionDTO(**adapted_data)

# TASK-4.1.4: Criar testes de compatibilidade (1h)
def test_product_vision_dto_compatibility():
    """Testa compatibilidade com código existente"""
    # Dados no formato antigo
    legacy_data = {
        'product_name': 'Test Product',
        'vision': 'Revolutionary solution',
        'target_audience': 'Developers',
        # ... outros campos no formato antigo
    }
    
    # Adaptar para novo formato
    adapter = DTOAdapter()
    dto = adapter.adapt_legacy_vision_data(legacy_data)
    
    # Validar que funciona
    assert dto.name == 'Test Product'
    assert dto.vision_statement == 'Revolutionary solution'
    assert dto.target_user == 'Developers'
    
    # Validar com validator
    validator = CoreValidator()
    errors = validator.validate(dto.to_dict())
    assert len(errors) == 0  # Sem erros após adaptação
```

**Estimativa:** 4 Story Points

---

### 📖 História 4.2: Migrar EpicSuggestionDTO
**Como** desenvolvedor  
**Quero** migrar EpicSuggestionDTO com campos IA  
**Para** preservar funcionalidade de geração de épicos  

**Critérios de Aceite:**
- [ ] EpicSuggestionDTO com 56 campos
- [ ] Campos IA preservados (complexity, confidence, etc)
- [ ] Validação de dependências funcionando
- [ ] Ordenação topológica mantida
- [ ] Testes de História 1.2 passando

**Tarefas Técnicas:**

```python
# TASK-4.2.1: Migrar EpicSuggestionDTO (2h)
# tdd_core/application/dto/epic_suggestion_dto.py
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

@dataclass
class EpicSuggestionDTO:
    """
    DTO para Sugestão de Épico - História 1.2
    Inclui campos IA da Phase 5.1
    """
    # Campos básicos
    name: str
    description: str
    project_id: int
    
    # Campos de negócio
    key: Optional[str] = None
    status: str = "pending"
    priority: int = 3  # 1-5
    
    # Campos IA (Phase 5.1)
    ai_generated: bool = True
    ai_confidence: float = 0.8  # 0.0-1.0
    complexity_score: float = 3.0  # 1.0-5.0
    effort_estimate: int = 5  # dias
    
    # Ordenação topológica
    sort_order: int = 0
    unblock_potential: int = 0
    critical_path_weight: float = 0.0
    dependencies: List[int] = field(default_factory=list)
    
    # Campos TDD
    tdd_phase: str = "analysis"
    tdd_order: int = 1
    
    # Metadata
    id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    # Campos calculados
    priority_score: Optional[float] = None
    is_blocked: bool = False
    blocking_epics: List[int] = field(default_factory=list)
    
    def __post_init__(self):
        """Validações e inicializações"""
        self._validate_ai_fields()
        self._validate_dependencies()
        self._generate_key_if_missing()
    
    def _validate_ai_fields(self):
        """Valida ranges dos campos IA"""
        if not 0.0 <= self.ai_confidence <= 1.0:
            raise ValueError(
                f"ai_confidence must be between 0.0 and 1.0, got {self.ai_confidence}"
            )
        
        if not 1.0 <= self.complexity_score <= 5.0:
            raise ValueError(
                f"complexity_score must be between 1.0 and 5.0, got {self.complexity_score}"
            )
        
        if not 1 <= self.effort_estimate <= 30:
            raise ValueError(
                f"effort_estimate must be between 1 and 30 days, got {self.effort_estimate}"
            )
    
    def _validate_dependencies(self):
        """Valida que não há auto-dependência"""
        if self.id and self.id in self.dependencies:
            raise ValueError("Epic cannot depend on itself")
        
        # Remover duplicatas
        self.dependencies = list(set(self.dependencies))
    
    def _generate_key_if_missing(self):
        """Gera key automática se não fornecida"""
        if not self.key and self.project_id:
            # Formato: PROJ_{project_id}_EP_{timestamp}
            import time
            timestamp = int(time.time() * 1000) % 100000
            self.key = f"PROJ_{self.project_id}_EP_{timestamp:05d}"
    
    def calculate_priority_score(
        self,
        weights: Dict[str, float]
    ) -> float:
        """Calcula score com pesos customizados"""
        # Valores base (simulados para DTO)
        business_value = self.priority * 2
        risk_mitigation = max(0, 5 - self.complexity_score)
        effort_efficiency = max(0, 10 - self.effort_estimate)
        strategic_alignment = self.unblock_potential
        
        score = (
            weights.get('valor', 0.4167) * business_value +
            weights.get('risco', 0.25) * risk_mitigation +
            weights.get('esforco', 0.1667) * effort_efficiency +
            weights.get('alinhamento', 0.1667) * strategic_alignment +
            weights.get('confidence', 0.0) * self.ai_confidence * 10
        )
        
        self.priority_score = score
        return score
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            k: v for k, v in self.__dict__.items()
            if not k.startswith('_')
        }
    
    def requires_human_review(self) -> bool:
        """Determina se precisa revisão humana"""
        return (
            self.ai_confidence < 0.6 or
            self.complexity_score >= 4.5 or
            self.effort_estimate > 20
        )

# TASK-4.2.2: Migrar EpicSuggestionValidator (2h)
# tdd_core/application/validators/epic_suggestion_validator.py
class EpicSuggestionValidator:
    """Validador para EpicSuggestionDTO"""
    
    def validate(self, epic_dto: EpicSuggestionDTO) -> List[str]:
        """Valida DTO de épico"""
        errors = []
        
        # Validar campos obrigatórios
        if not epic_dto.name or len(epic_dto.name) < 3:
            errors.append("Epic name must be at least 3 characters")
        
        if not epic_dto.description or len(epic_dto.description) < 10:
            errors.append("Epic description must be at least 10 characters")
        
        if not epic_dto.project_id:
            errors.append("project_id is required")
        
        # Validar campos IA
        errors.extend(self._validate_ai_fields(epic_dto))
        
        # Validar dependências
        errors.extend(self._validate_dependencies(epic_dto))
        
        # Validar TDD
        errors.extend(self._validate_tdd_fields(epic_dto))
        
        return errors
    
    def _validate_ai_fields(self, epic_dto: EpicSuggestionDTO) -> List[str]:
        """Valida campos específicos de IA"""
        errors = []
        
        if epic_dto.ai_generated and epic_dto.ai_confidence == 0:
            errors.append(
                "AI-generated epics must have confidence > 0"
            )
        
        if epic_dto.complexity_score > 4.0 and epic_dto.effort_estimate < 10:
            errors.append(
                "High complexity epics should have higher effort estimates"
            )
        
        return errors
    
    def _validate_dependencies(self, epic_dto: EpicSuggestionDTO) -> List[str]:
        """Valida dependências do épico"""
        errors = []
        
        if len(epic_dto.dependencies) > 10:
            errors.append(
                "Epic has too many dependencies (max 10)"
            )
        
        # Verificar dependências circulares seria feito no serviço
        
        return errors
    
    def _validate_tdd_fields(self, epic_dto: EpicSuggestionDTO) -> List[str]:
        """Valida campos TDD"""
        errors = []
        
        valid_phases = ['analysis', 'red', 'green', 'refactor', 'review']
        if epic_dto.tdd_phase not in valid_phases:
            errors.append(
                f"Invalid TDD phase: {epic_dto.tdd_phase}"
            )
        
        if not 1 <= epic_dto.tdd_order <= 3:
            errors.append(
                "TDD order must be between 1 and 3"
            )
        
        return errors
    
    def validate_batch(
        self,
        epics: List[EpicSuggestionDTO]
    ) -> Dict[int, List[str]]:
        """Valida múltiplos épicos"""
        errors_by_index = {}
        
        for i, epic in enumerate(epics):
            errors = self.validate(epic)
            if errors:
                errors_by_index[i] = errors
        
        # Validar unicidade de keys
        keys = [e.key for e in epics if e.key]
        if len(keys) != len(set(keys)):
            errors_by_index[-1] = ["Duplicate epic keys found"]
        
        return errors_by_index

# TASK-4.2.3: Criar testes dos DTOs migrados (1h)
def test_epic_suggestion_dto_ai_fields():
    """Testa campos IA do DTO"""
    epic = EpicSuggestionDTO(
        name="Test Epic",
        description="AI-generated epic for testing",
        project_id=1,
        ai_generated=True,
        ai_confidence=0.85,
        complexity_score=3.5,
        effort_estimate=8
    )
    
    assert epic.ai_generated == True
    assert epic.ai_confidence == 0.85
    assert epic.complexity_score == 3.5
    assert epic.effort_estimate == 8
    assert epic.requires_human_review() == False
    
    # Testar caso que requer revisão
    epic.ai_confidence = 0.5
    assert epic.requires_human_review() == True

def test_epic_priority_calculation():
    """Testa cálculo de prioridade com pesos"""
    epic = EpicSuggestionDTO(
        name="High Priority Epic",
        description="Critical path epic",
        project_id=1,
        priority=5,
        complexity_score=2.0,
        effort_estimate=3,
        unblock_potential=4
    )
    
    # Pesos História 3.2
    weights = {
        'valor': 0.6,
        'risco': 0.2,
        'esforco': 0.1,
        'alinhamento': 0.1,
        'confidence': 0.0
    }
    
    score = epic.calculate_priority_score(weights)
    assert score > 0
    assert epic.priority_score == score
```

**Estimativa:** 4 Story Points

---

## ✅ ÉPICO 5: Testes e Documentação
**Objetivo:** Garantir qualidade e documentação completa do novo núcleo  
**Estimativa:** 8 Story Points  
**Prioridade:** Alta  
**Dependências:** Épicos 1-4  

### 📖 História 5.1: Implementar Suite de Testes Completa
**Como** QA Engineer  
**Quero** uma suite de testes abrangente  
**Para** garantir ≥95% de cobertura e zero regressões  

**Critérios de Aceite:**
- [ ] Testes unitários para todas as entidades
- [ ] Testes de integração para serviços
- [ ] Testes E2E via Streamlit adapter
- [ ] Testes de performance (<10ms, 0.19ms topological)
- [ ] Coverage report ≥95%

**Tarefas Técnicas:**

```python
# TASK-5.1.1: Criar test fixtures compartilhadas (2h)
# tests/tdd_core/conftest.py
import pytest
from pathlib import Path
from tdd_core.domain.entities import *
from tdd_core.application.dto import *
from tdd_core.infrastructure.repositories import *

@pytest.fixture
def sample_product_vision():
    """Fixture para ProductVision válida"""
    return ProductVision(
        name="E-commerce Platform",
        vision_statement="Revolutionize online shopping with AI",
        target_user="Small business owners",
        user_problem="Complex e-commerce setup",
        expected_benefits="10x faster store creation",
        product_description="AI-powered e-commerce builder",
        success_metrics="1000 stores in 6 months",
        tech_requirements="Cloud-native, microservices",
        non_functional_requirements="99.9% uptime, <100ms response",
        compliance_requirements="PCI-DSS, GDPR compliant",
        risks="Market competition, technical complexity",
        assumptions="Users have basic tech knowledge",
        constraints="$500k budget, 6 month timeline",
        deliverables="MVP, documentation, deployment"
    )

@pytest.fixture
def sample_epics():
    """Fixture para lista de épicos"""
    return [
        Epic(
            project_id=1,
            key="ECOM_001",
            name="Database Setup",
            description="Core database and ORM setup",
            complexity_score=2.0,
            effort_estimate=3,
            ai_confidence=0.9
        ),
        Epic(
            project_id=1,
            key="ECOM_002",
            name="User Authentication",
            description="OAuth and session management",
            complexity_score=3.5,
            effort_estimate=5,
            ai_confidence=0.85
        ),
        # ... mais épicos
    ]

@pytest.fixture
def in_memory_db():
    """Fixture para banco in-memory"""
    import sqlite3
    conn = sqlite3.connect(":memory:")
    
    # Criar schema
    with open("migrations/schema.sql") as f:
        conn.executescript(f.read())
    
    yield conn
    conn.close()

# TASK-5.1.2: Testes unitários do domínio (2h)
# tests/tdd_core/domain/test_entities.py
def test_product_vision_validation(sample_product_vision):
    """Testa validação de ProductVision"""
    # Valid vision
    errors = sample_product_vision.validate()
    assert len(errors) == 0
    
    # Invalid vision
    invalid_vision = ProductVision(
        name="",  # Empty required field
        vision_statement="Test"
    )
    errors = invalid_vision.validate()
    assert "name is required" in errors

def test_epic_priority_calculation():
    """Testa cálculo de prioridade do épico"""
    epic = Epic(
        project_id=1,
        key="TEST_001",
        name="Test Epic",
        priority=4,
        complexity_score=2.5,
        effort_estimate=5
    )
    
    weights = {
        'valor': 0.5,
        'risco': 0.2,
        'esforco': 0.2,
        'alinhamento': 0.1
    }
    
    score = epic.calculate_priority_score(weights)
    assert score > 0
    assert isinstance(score, float)

def test_value_objects_immutability():
    """Testa imutabilidade dos value objects"""
    from tdd_core.domain.value_objects import Priority, ComplexityScore
    
    priority = Priority(
        valor=0.5,
        risco=0.2,
        esforco=0.2,
        alinhamento=0.1,
        confidence=0.0
    )
    
    # Deve falhar ao tentar modificar
    with pytest.raises(AttributeError):
        priority.valor = 0.6
    
    complexity = ComplexityScore(3.5)
    with pytest.raises(AttributeError):
        complexity.value = 4.0

# TASK-5.1.3: Testes de integração dos serviços (3h)
# tests/tdd_core/application/test_services.py
from unittest.mock import Mock, MagicMock

def test_vision_service_create_and_refine():
    """Testa criação e refinamento de visão"""
    # Setup
    mock_repo = Mock()
    mock_ai = Mock()
    mock_validator = Mock()
    mock_validator.validate.return_value = []
    
    service = VisionService(mock_repo, mock_ai, mock_validator)
    
    # Test create
    vision_data = {
        'name': 'Test Product',
        'vision_statement': 'Test vision',
        # ... outros campos
    }
    
    mock_repo.save.return_value = ProductVision(**vision_data)
    
    result = service.create_vision(vision_data)
    assert result.name == 'Test Product'
    mock_repo.save.assert_called_once()
    
    # Test refine
    mock_repo.find_by_id.return_value = ProductVision(**vision_data)
    mock_ai.refine_text.return_value = "Refined vision statement"
    
    refined = service.refine_field(1, 'vision_statement', 'Original')
    assert refined == "Refined vision statement"
    mock_ai.refine_text.assert_called_once()

def test_epic_service_topological_sort():
    """Testa ordenação topológica com meta de performance"""
    import time
    
    # Setup
    epics = [
        Epic(id=i, project_id=1, key=f"EP_{i:03d}", name=f"Epic {i}")
        for i in range(1, 8)
    ]
    
    dependencies = {
        2: [1],
        3: [1],
        4: [2, 3],
        5: [4],
        6: [1, 2, 3, 4, 5],
        7: []
    }
    
    sorter = DeterministicTopologicalSorter()
    
    # Measure performance
    start = time.perf_counter()
    sorted_epics, exec_time = sorter.sort(epics, dependencies)
    
    # Assertions
    assert len(sorted_epics) == 7
    assert sorted_epics[0].id == 1  # No dependencies
    assert sorted_epics[-1].id == 6  # Most dependencies
    assert exec_time <= 1.0  # Under 1ms
    
    print(f"Topological sort: {exec_time:.3f}ms (target: 0.19ms)")

def test_ai_service_mock_behavior():
    """Testa comportamento do MockAIService"""
    service = MockAIService()
    
    # Test refine
    refined = service.refine_text(
        "Original text",
        {},
        "vision_statement"
    )
    assert "Refined" in refined
    
    # Test generate epics
    epics = service.generate_epics({})
    assert len(epics) >= 3
    assert all('name' in e for e in epics)
    assert all('complexity' in e for e in epics)

# TASK-5.1.4: Testes E2E com Streamlit (2h)
# tests/tdd_core/e2e/test_streamlit_integration.py
def test_streamlit_adapter_full_flow():
    """Testa fluxo completo via adapter"""
    # Setup Streamlit session state mock
    import streamlit as st
    st.session_state = MagicMock()
    st.session_state.wizard_state = {
        'current_phase': 'roteiro',
        'product_vision': {},
        'epics': []
    }
    
    # Create adapter
    adapter = StreamlitAdapter()
    
    # Fill vision
    st.session_state.wizard_state['product_vision'] = {
        'name': 'Test Product',
        'vision_statement': 'Test Vision',
        # ... all required fields
    }
    
    # Sync to domain
    adapter.sync_state_to_domain()
    
    # Generate epics
    epic_service = adapter.get_epic_service()
    # Mock the AI response
    epic_service.ai_service = MockAIService()
    
    epics = epic_service.generate_epics_from_vision(1)
    
    # Sync back
    adapter.sync_domain_to_state()
    
    # Verify
    assert len(st.session_state.wizard_state['epics']) >= 3
    assert st.session_state.wizard_state['current_phase'] == 'capitulos'

# TASK-5.1.5: Testes de performance (1h)
# tests/tdd_core/performance/test_performance.py
def test_repository_query_performance(in_memory_db):
    """Testa performance <10ms das queries"""
    import time
    
    repo = SQLiteProjectRepository(":memory:")
    
    # Create test data
    for i in range(100):
        project = Project(
            name=f"Project {i}",
            description=f"Description {i}"
        )
        repo.save(project)
    
    # Measure query time
    start = time.perf_counter()
    projects = repo.find_all()
    elapsed = (time.perf_counter() - start) * 1000
    
    assert len(projects) == 100
    assert elapsed < 10  # Under 10ms
    print(f"Query 100 projects: {elapsed:.2f}ms")

def test_cache_effectiveness():
    """Testa efetividade do cache LRU"""
    from functools import lru_cache
    
    call_count = 0
    
    @lru_cache(maxsize=128)
    def expensive_operation(param):
        nonlocal call_count
        call_count += 1
        return f"Result for {param}"
    
    # First calls
    for i in range(10):
        expensive_operation(i)
    assert call_count == 10
    
    # Cached calls
    for i in range(10):
        expensive_operation(i)
    assert call_count == 10  # No new calls
    
    # Cache info
    info = expensive_operation.cache_info()
    assert info.hits == 10
    assert info.misses == 10
```

**Estimativa:** 5 Story Points

---

### 📖 História 5.2: Criar Documentação Completa
**Como** desenvolvedor  
**Quero** documentação técnica completa  
**Para** facilitar manutenção e onboarding  

**Critérios de Aceite:**
- [ ] README.md do tdd_core
- [ ] Diagramas de arquitetura
- [ ] Guia de migração
- [ ] API documentation
- [ ] Exemplos de uso

**Tarefas Técnicas:**

```python
# TASK-5.2.1: Criar README principal (1h)
# tdd_core/README.md
"""
# TDD Core - Domain Layer for TDD Project

## Overview
Clean Architecture implementation of TDD-Project business logic.

## Architecture
```
tdd_core/
├── domain/          # Pure business logic
├── application/     # Use cases and services  
├── infrastructure/  # External interfaces
```

## Quick Start
```python
from tdd_core.infrastructure.adapters import StreamlitAdapter

adapter = StreamlitAdapter()
vision_service = adapter.get_vision_service()
epic_service = adapter.get_epic_service()
```

## Key Features
- ✅ Domain-Driven Design
- ✅ Clean Architecture
- ✅ 95%+ test coverage
- ✅ <10ms query performance
- ✅ 0.19ms topological sorting

## Documentation
- [Architecture Guide](docs/architecture.md)
- [Migration Guide](docs/migration.md)
- [API Reference](docs/api.md)
"""

# TASK-5.2.2: Criar guia de migração (2h)
# docs/migration_guide.md
"""
# Migration Guide: Streamlit → TDD Core

## Phase 1: Install tdd_core
```bash
pip install -e ./tdd_core
```

## Phase 2: Update ServiceContainer
Replace in `streamlit_extension/services/service_container.py`:

```python
from tdd_core.infrastructure.adapters import StreamlitAdapter

class ServiceContainer:
    def __init__(self):
        self._adapter = StreamlitAdapter()
    
    def get_vision_service(self):
        return self._adapter.get_vision_service()
```

## Phase 3: Update imports
Replace direct imports:
```python
# Old
from streamlit_extension.pages.projetos.dto import ProductVisionDTO

# New
from tdd_core.application.dto import ProductVisionDTO
```

## Rollback Plan
1. Keep backup branch: `git branch backup-pre-tddcore`
2. Test in staging first
3. Feature flag for gradual rollout
"""

# TASK-5.2.3: Gerar documentação da API (1h)
# docs/generate_api_docs.py
import inspect
from tdd_core import domain, application

def generate_api_docs():
    """Gera documentação automática da API"""
    docs = []
    
    # Document entities
    for name, obj in inspect.getmembers(domain.entities):
        if inspect.isclass(obj):
            docs.append(f"## {name}")
            docs.append(inspect.getdoc(obj))
            
            # Document methods
            for method_name, method in inspect.getmembers(obj):
                if not method_name.startswith('_'):
                    docs.append(f"### {method_name}")
                    docs.append(inspect.getdoc(method))
    
    # Save to file
    with open('docs/api_reference.md', 'w') as f:
        f.write('\n\n'.join(docs))

if __name__ == '__main__':
    generate_api_docs()
```

**Estimativa:** 3 Story Points

---

## 📊 Métricas e KPIs do Marco 0

### Métricas de Sucesso
| Métrica | Meta | Como Medir |
|---------|------|------------|
| **Cobertura de Testes** | ≥95% | `pytest --cov=tdd_core` |
| **Performance Queries** | <10ms | Benchmark tests |
| **Ordenação Topológica** | ≤1ms (0.19ms target) | Performance tests |
| **Zero Breaking Changes** | 0 | E2E tests passando |
| **Código Duplicado** | <5% | Análise estática |
| **Complexidade Ciclomática** | <10 | radon/pylint |

### Checkpoints de Validação
- [ ] **Checkpoint 1 (Fim Semana 1):** Estrutura criada, entidades extraídas
- [ ] **Checkpoint 2 (Meio Semana 2):** Serviços migrados, adapters funcionando
- [ ] **Checkpoint 3 (Fim Semana 2):** Testes completos, documentação pronta

---

## 🚨 Riscos e Mitigações Detalhadas

### Risco 1: Quebra da Aplicação Streamlit
**Probabilidade:** Alta  
**Impacto:** Crítico  
**Mitigação:**
- Implementação incremental com adapters
- Testes E2E contínuos
- Branch de segurança para rollback
- Feature flags para ativação gradual

### Risco 2: Degradação de Performance
**Probabilidade:** Média  
**Impacto:** Alto  
**Mitigação:**
- Benchmarks antes/depois
- Profiling com cProfile
- Manter cache LRU
- Otimizar queries críticas

### Risco 3: Complexidade do Adapter
**Probabilidade:** Média  
**Impacto:** Médio  
**Mitigação:**
- Implementação incremental
- Pair programming
- Revisão de código rigorosa
- Documentação inline extensa

### Risco 4: Resistência da Equipe
**Probabilidade:** Baixa  
**Impacto:** Médio  
**Mitigação:**
- Workshops de arquitetura
- Documentação clara
- Quick wins demonstráveis
- Suporte durante transição

---

## 🎯 Definition of Done - Marco 0

### Critérios Gerais
- [ ] Código revisado por pelo menos 2 desenvolvedores
- [ ] Todos os testes automatizados passando
- [ ] Documentação atualizada (código + README)
- [ ] Sem regressões no Streamlit
- [ ] Performance mantida ou melhorada
- [ ] Zero vulnerabilidades críticas (security scan)

### Critérios Específicos do Domínio
- [ ] Entidades 100% independentes de frameworks
- [ ] Value Objects imutáveis com validação
- [ ] Interfaces de repositório definidas
- [ ] Serviços sem dependências de infraestrutura

### Critérios de Integração
- [ ] Adapter Streamlit funcionando sem breaking changes
- [ ] Session state sincronizado com domínio
- [ ] Fluxo wizard completo testado E2E
- [ ] Rollback plan documentado e testado

---

## 📅 Cronograma Detalhado (2 Semanas)

### Semana 1: Estrutura e Migração Core

**Segunda (Dia 1)**
- ✅ Manhã: Criar estrutura tdd_core (História 1.1)
- ✅ Tarde: Começar extração de entidades (História 1.2)

**Terça (Dia 2)**
- ✅ Manhã: Finalizar entidades e value objects (História 1.2-1.3)
- ✅ Tarde: Iniciar migração VisionService (História 2.1)

**Quarta (Dia 3)**
- ✅ Manhã: Finalizar VisionService (História 2.1)
- ✅ Tarde: Migrar EpicService com ordenação (História 2.2)

**Quinta (Dia 4)**
- ✅ Manhã: Finalizar EpicService e performance (História 2.2)
- ✅ Tarde: Migrar AIService e configurações (História 2.3)

**Sexta (Dia 5)**
- ✅ Manhã: Revisar e ajustar serviços
- ✅ Tarde: **Checkpoint 1** - Validação com equipe

### Semana 2: Integração e Finalização

**Segunda (Dia 6)**
- ✅ Manhã: Criar StreamlitAdapter (História 3.1)
- ✅ Tarde: Testar integração básica

**Terça (Dia 7)**
- ✅ Manhã: Criar mapeadores DTO↔Entity (História 3.2)
- ✅ Tarde: Implementar repositórios SQLite (História 3.3)

**Quarta (Dia 8)**
- ✅ Manhã: Migrar DTOs e validators (História 4.1-4.2)
- ✅ Tarde: **Checkpoint 2** - Integração completa

**Quinta (Dia 9)**
- ✅ Manhã: Implementar suite de testes (História 5.1)
- ✅ Tarde: Executar testes de performance e E2E

**Sexta (Dia 10)**
- ✅ Manhã: Criar documentação (História 5.2)
- ✅ Tarde: **Gate Final** - Validação e aprovação

---

## 🔄 Processo de Rollback

### Condições para Rollback
1. Breaking changes não resolvidos em 4h
2. Performance degradada >50%
3. Perda de dados detectada
4. Múltiplos bugs críticos

### Procedimento de Rollback
```bash
# 1. Parar deploy
kubectl rollout pause deployment/tdd-app

# 2. Reverter para branch de backup
git checkout backup-pre-tddcore
git push origin main --force-with-lease

# 3. Reverter banco se necessário
psql < backups/pre_tddcore_backup.sql

# 4. Reiniciar aplicação
kubectl rollout restart deployment/tdd-app

# 5. Validar funcionamento
pytest tests/smoke/
```

---

## 📝 Notas de Implementação

### Padrões de Código
- **Docstrings:** Google style para todas as classes/métodos públicos
- **Type hints:** 100% de cobertura com mypy strict
- **Naming:** snake_case para funções, PascalCase para classes
- **Imports:** Absolute imports dentro do tdd_core
- **Testes:** Arrange-Act-Assert pattern

### Ferramentas Recomendadas
- **Linting:** pylint, flake8, black
- **Type checking:** mypy --strict
- **Security:** bandit, safety
- **Performance:** cProfile, memory_profiler
- **Coverage:** pytest-cov com min 95%

### Convenções de Commit
```
feat(core): add ProductVision entity
fix(adapter): resolve session state sync issue
test(epic): add topological sort performance test
docs(api): update service documentation
refactor(mapper): simplify DTO conversion logic
```

---

## 🎉 Conclusão

O Marco 0 estabelece a fundação técnica crítica para a evolução do TDD-Project. Com a extração bem-sucedida do domínio para o módulo `tdd_core`, estaremos prontos para:

1. **Marco 1:** Implementar API REST v1
2. **Marco 2:** Desenvolver interface Web com Nuxt 3
3. **Marco 3:** Criar CLI e ferramentas de automação

A arquitetura limpa garantirá que o sistema seja:
- **Testável:** Lógica de negócio isolada e pura
- **Manutenível:** Camadas bem definidas e desacopladas
- **Extensível:** Fácil adicionar novos clientes (Web, CLI, Mobile)
- **Performático:** Mantendo metas de <10ms e 0.19ms

**Próximos Passos:**
1. Aprovação deste plano pela equipe
2. Alocação de recursos (2-3 desenvolvedores)
3. Kick-off meeting para alinhamento
4. Início da implementação

---

*Documento gerado em: 2025-09-13*  
*Versão: 1.0.0*  
*Autores: Equipe de Arquitetura TDD-Project*