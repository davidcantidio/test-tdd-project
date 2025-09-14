# Plano de Execução — História 1.2: Extrair Entidades de Domínio

Status: Pronto para execução • Marco 0 (Extração do Domínio) • Épico 1

---

## 1) Contexto e Alinhamento

A História 1.2 implementa as entidades principais do domínio no módulo `tdd_core`, continuando o trabalho iniciado na História 1.1 (estrutura base). O objetivo é extrair e isolar as entidades centrais do sistema atual (ProductVision, Project, Epic, Task) como objetos de negócio puros, sem dependências de frameworks, seguindo princípios DDD e mantendo compatibilidade total com o sistema existente.

- Referências diretas:
  - Marco 0 — Extração do Domínio: `docs/marco_0_domain_extraction.md` (História 1.2)
  - PRD Final — Seção "Marco 0 — Extração do Domínio (tdd_core)": `prd_final.md`
  - História 1.1 — Estrutura Base Completa: `docs/PLANO_HISTORIA_1_1.md`
- Princípios: Domain-Driven Design (DDD), entidades ricas, independência de frameworks, imutabilidade onde apropriado
- Não inclui: value objects completos (História 1.3), serviços (Épico 2), alterações no banco, mudanças na UI

---

## 2) Escopo da História (User Story)

Como arquiteto de software, quero extrair e isolar as entidades principais do domínio para ter objetos de negócio independentes de frameworks que encapsulem regras e comportamentos do domínio.

---

## 3) Critérios de Aceite

- [ ] ProductVision entity com 15 campos obrigatórios implementada
- [ ] Project entity com campos essenciais (78 campos conforme CLAUDE.md)
- [ ] Epic entity com 56 campos incluindo campos IA (Phase 5.1)
- [ ] Task entity com campos TDD e suporte TDAH
- [ ] Zero dependências externas (exceto stdlib e typing)
- [ ] Métodos de validação e comportamento de domínio implementados
- [ ] 100% de cobertura de testes unitários
- [ ] Documentação inline completa (docstrings)
- [ ] Nenhuma regressão nos sistemas existentes

---

## 4) Entregáveis

- `tdd_core/domain/entities/product_vision.py` - Entidade ProductVision com validação
- `tdd_core/domain/entities/project.py` - Entidade Project como hub central
- `tdd_core/domain/entities/epic.py` - Entidade Epic com campos IA e ordenação topológica
- `tdd_core/domain/entities/task.py` - Entidade Task com suporte TDD/TDAH
- `tdd_core/domain/entities/__init__.py` - Exports das entidades
- `tests/tdd_core/domain/entities/` - Testes unitários completos para cada entidade
- Atualização do `tdd_core/domain/__init__.py` com imports das entidades

---

## 5) Tarefas Técnicas

### TASK-1.2.1: Criar ProductVision entity (3h)
```python
# tdd_core/domain/entities/product_vision.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

@dataclass
class ProductVision:
    """Entidade de Visão do Produto - 15 campos obrigatórios"""

    # Campos obrigatórios (15) — SEM defaults primeiro (regra dataclass)
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
    market_opportunity: str

    # Campos opcionais e metadados (com defaults)
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now()
        if not self.updated_at:
            self.updated_at = datetime.now()

    def validate(self) -> List[str]:
        """Valida campos obrigatórios"""
        errors: List[str] = []
        required_fields = [
            'name', 'vision_statement', 'target_user',
            'user_problem', 'expected_benefits', 'product_description',
            'success_metrics', 'tech_requirements', 'non_functional_requirements',
            'compliance_requirements', 'risks', 'assumptions',
            'constraints', 'deliverables', 'market_opportunity'
        ]
        for field in required_fields:
            value = getattr(self, field, None)
            if not value or (isinstance(value, str) and not value.strip()):
                errors.append(f"{field} is required and cannot be empty")
        return errors

    def is_valid(self) -> bool:
        """Verifica se a entidade é válida"""
        return len(self.validate()) == 0
```

### TASK-1.2.2: Criar Epic entity com campos IA (4h)
```python
# tdd_core/domain/entities/epic.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List

@dataclass
class Epic:
    """Entidade Epic com 56 campos incluindo IA e ordenação topológica.

    Observações:
    - Cálculo de prioridade NÃO fica na entidade. Use o PriorityScorer
      na camada de aplicação para scoring determinístico com DI (Histórias 3.1/3.2).
    - Mapeamento de persistência:
        • Domínio: key -> Banco: epic_key (mapper/infraestrutura)
        • epic_dependencies (List[str]) -> tabela de junção framework_epic_dependencies
    """

    # Campos obrigatórios — SEM defaults primeiro (regra dataclass)
    project_id: int
    key: str  # mapeia para coluna 'epic_key' no banco
    name: str
    description: str

    # Campos com defaults
    id: Optional[int] = None
    status: str = "pending"
    priority: int = 3

    # Campos IA (Phase 5.1)
    ai_generated: bool = False
    ai_confidence: float = 0.0  # 0.0-1.0
    complexity_score: float = 3.0  # 1.0-5.0
    effort_estimate: int = 5  # dias (>=1)

    # Campos de ordenação topológica
    sort_order: int = 0
    unblock_potential: int = 0
    critical_path_weight: float = 0.0
    epic_dependencies: List[str] = field(default_factory=list)  # keys dependentes (mapper grava na tabela de junção)

    # Campos TDD
    tdd_phase: str = "analysis"  # analysis/red/green/refactor/review
    tdd_order: int = 1  # 1-3 prioridade dentro da fase

    # Campos de negócio
    business_value: int = 5  # 1-10
    risk_mitigation: int = 5  # 1-10
    strategic_alignment: int = 5  # 1-10

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now()
        if not self.updated_at:
            self.updated_at = datetime.now()

    def validate(self) -> List[str]:
        """Valida a entidade Epic"""
        errors: List[str] = []

        # Validar campos obrigatórios
        if not self.project_id:
            errors.append("project_id is required")
        if not self.key or not self.key.strip():
            errors.append("key is required and cannot be empty")
        if not self.name or not self.name.strip():
            errors.append("name is required and cannot be empty")

        # Validar ranges
        if not 0.0 <= self.ai_confidence <= 1.0:
            errors.append("ai_confidence must be between 0.0 and 1.0")
        if not 1.0 <= self.complexity_score <= 5.0:
            errors.append("complexity_score must be between 1.0 and 5.0")
        if self.effort_estimate <= 0:
            errors.append("effort_estimate must be greater than zero")

        # Validar TDD phase
        valid_phases = ['analysis', 'red', 'green', 'refactor', 'review']
        if self.tdd_phase not in valid_phases:
            errors.append(f"tdd_phase must be one of {valid_phases}")

        return errors

    def is_valid(self) -> bool:
        """Verifica se a entidade é válida"""
        return len(self.validate()) == 0

    def has_dependencies(self) -> bool:
        """Verifica se o épico tem dependências"""
        return bool(self.epic_dependencies)

    def is_ai_generated(self) -> bool:
        """Verifica se foi gerado por IA"""
        return self.ai_generated

    def is_high_confidence(self) -> bool:
        """Verifica se tem alta confiança da IA"""
        return self.ai_confidence >= 0.8
```

### TASK-1.2.3: Criar Project entity (2h)
```python
# tdd_core/domain/entities/project.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List

@dataclass
class Project:
    """Entidade Project - Hub central com 78 campos"""

    # Campos obrigatórios — SEM defaults primeiro (regra dataclass)
    name: str
    description: str

    # Identificação e status
    id: Optional[int] = None
    status: str = "active"  # active/archived/completed

    # Relacionamento com vision
    vision_id: Optional[int] = None

    # Metadados do wizard
    wizard_completed: bool = False
    current_phase: str = "roteiro"  # roteiro/capitulos/historias/tarefas
    phases_completed: List[str] = field(default_factory=list)

    # Configurações de prioridade
    use_custom_weights: bool = False

    # Métricas
    total_epics: int = 0
    completed_epics: int = 0
    total_tasks: int = 0
    completed_tasks: int = 0
    progress_percentage: float = 0.0

    # Timestamps e audit
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now()
        if not self.updated_at:
            self.updated_at = datetime.now()

    def validate(self) -> List[str]:
        """Valida a entidade Project"""
        errors: List[str] = []

        if not self.name or not self.name.strip():
            errors.append("name is required and cannot be empty")

        valid_statuses = ['active', 'archived', 'completed']
        if self.status not in valid_statuses:
            errors.append(f"status must be one of {valid_statuses}")

        valid_phases = ['roteiro', 'capitulos', 'historias', 'tarefas']
        if self.current_phase not in valid_phases:
            errors.append(f"current_phase must be one of {valid_phases}")

        if self.progress_percentage < 0 or self.progress_percentage > 100:
            errors.append("progress_percentage must be between 0 and 100")

        return errors

    def is_valid(self) -> bool:
        """Verifica se a entidade é válida"""
        return len(self.validate()) == 0

    def calculate_progress(self) -> float:
        """Calcula o progresso do projeto"""
        if self.total_tasks == 0:
            return 0.0
        return (self.completed_tasks / self.total_tasks) * 100

    def mark_phase_complete(self, phase: str) -> None:
        """Marca uma fase como completa"""
        if phase not in self.phases_completed:
            self.phases_completed.append(phase)
        self.updated_at = datetime.now()

    def is_wizard_complete(self) -> bool:
        """Verifica se o wizard foi completado"""
        return self.wizard_completed
```

### TASK-1.2.4: Criar Task entity (2h)
```python
# tdd_core/domain/entities/task.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

@dataclass
class Task:
    """Entidade Task com suporte TDD e TDAH"""

    # Campos obrigatórios — SEM defaults primeiro (regra dataclass)
    epic_id: int
    key: str
    name: str
    description: str

    # Identificação e status
    id: Optional[int] = None
    status: str = "todo"  # todo/in_progress/done/blocked
    tdd_status: str = "pending"  # pending/red/green/refactor

    # Métricas TDD
    test_coverage: float = 0.0  # 0-100%
    tests_passing: int = 0
    tests_total: int = 0
    tests_failing: int = 0

    # TDAH Support
    focus_rating: Optional[int] = None  # 1-5
    interruption_count: int = 0
    energy_level: Optional[str] = None  # low/medium/high
    estimated_duration: Optional[int] = None  # minutos
    actual_duration: Optional[int] = None  # minutos

    # Prioridade e complexidade
    priority: int = 3  # 1-5
    complexity: int = 3  # 1-5
    story_points: Optional[int] = None

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now()
        if not self.updated_at:
            self.updated_at = datetime.now()

    def validate(self) -> List[str]:
        """Valida a entidade Task"""
        errors: List[str] = []

        if not self.epic_id:
            errors.append("epic_id is required")
        if not self.key or not self.key.strip():
            errors.append("key is required and cannot be empty")
        if not self.name or not self.name.strip():
            errors.append("name is required and cannot be empty")

        valid_statuses = ['todo', 'in_progress', 'done', 'blocked']
        if self.status not in valid_statuses:
            errors.append(f"status must be one of {valid_statuses}")

        valid_tdd_statuses = ['pending', 'red', 'green', 'refactor']
        if self.tdd_status not in valid_tdd_statuses:
            errors.append(f"tdd_status must be one of {valid_tdd_statuses}")

        if self.test_coverage < 0 or self.test_coverage > 100:
            errors.append("test_coverage must be between 0 and 100")

        if self.focus_rating is not None and not 1 <= self.focus_rating <= 5:
            errors.append("focus_rating must be between 1 and 5")

        if self.energy_level and self.energy_level not in ['low', 'medium', 'high']:
            errors.append("energy_level must be one of ['low', 'medium', 'high']")

        return errors

    def is_valid(self) -> bool:
        """Verifica se a entidade é válida"""
        return len(self.validate()) == 0

    def is_tdd_complete(self) -> bool:
        """Verifica se o ciclo TDD está completo"""
        return self.tdd_status == 'refactor' and self.test_coverage > 80

    def mark_interrupted(self) -> None:
        """Marca uma interrupção na tarefa (TDAH support)"""
        self.interruption_count += 1
        self.updated_at = datetime.now()

    def calculate_efficiency(self) -> Optional[float]:
        """Calcula eficiência (duração estimada vs real)"""
        if self.estimated_duration and self.actual_duration:
            return (self.estimated_duration / self.actual_duration) * 100
        return None
```

### TASK-1.2.5: Atualizar __init__.py das entidades (1h)
```python
# tdd_core/domain/entities/__init__.py
"""Domain Entities - Core Business Objects

Entities represent the core concepts of the business domain with identity.
All entities are framework-independent and contain business logic.

Available entities:
    - ProductVision: Product vision with 15 required fields
    - Project: Project hub with 78 fields including metrics
    - Epic: Epic with 56 fields including AI and topological ordering
    - Task: Task with TDD workflow and TDAH support

Status: História 1.2 Complete - Entities Extracted
"""

from .product_vision import ProductVision
from .project import Project
from .epic import Epic
from .task import Task

__all__: list[str] = [
    "ProductVision",
    "Project",
    "Epic",
    "Task"
]
```

### TASK-1.2.6: Criar testes unitários das entidades (3h)
```python
# tests/tdd_core/domain/entities/test_product_vision.py
import pytest
from datetime import datetime
from tdd_core.domain.entities import ProductVision, Epic

def test_product_vision_creation():
    """Testa criação de ProductVision com campos obrigatórios"""
    vision = ProductVision(
        name="TDD Framework",
        vision_statement="Revolucionar desenvolvimento com TDD",
        target_user="Desenvolvedores",
        user_problem="Complexidade em testes",
        expected_benefits="Qualidade e produtividade",
        product_description="Framework completo TDD",
        success_metrics="98% cobertura, zero bugs",
        tech_requirements="Python 3.11+, SQLite",
        non_functional_requirements="Performance <1ms",
        compliance_requirements="GDPR, SOC2",
        risks="Curva de aprendizado",
        assumptions="Equipe experiente",
        constraints="6 meses, R$100k",
        deliverables="API, CLI, Web",
        market_opportunity="10M desenvolvedores"
    )

    assert vision.name == "TDD Framework"
    assert vision.is_valid()
    assert isinstance(vision.created_at, datetime)

def test_product_vision_validation_missing_fields():
    """Testa validação com campos faltando"""
    vision = ProductVision(
        name="",
        vision_statement="Test",
        target_user="",
        user_problem="Problem",
        expected_benefits="",
        product_description="Description",
        success_metrics="",
        tech_requirements="Tech",
        non_functional_requirements="",
        compliance_requirements="Compliance",
        risks="",
        assumptions="Assumptions",
        constraints="",
        deliverables="Deliverables",
        market_opportunity=""
    )

    errors = vision.validate()
    assert len(errors) > 0
    assert "name is required" in str(errors)
    assert not vision.is_valid()

"""
# tests/tdd_core/domain/entities/test_epic.py
"""

def test_epic_validation_and_defaults():
    """Testa validação e defaults do Epic sem cálculo de prioridade na entidade"""
    epic = Epic(
        project_id=1,
        key="EP-001",
        name="Backend Infrastructure",
        description="Setup backend",
        effort_estimate=5,
    )

    assert epic.is_valid()
    assert epic.status == "pending"
    assert epic.tdd_phase == "analysis"
    assert isinstance(epic.epic_dependencies, list) and len(epic.epic_dependencies) == 0

def test_epic_ai_fields():
    """Testa campos de IA do Epic"""
    epic = Epic(
        project_id=1,
        key="EP-002",
        name="AI Generated Epic",
        description="Generated by AI",
        ai_generated=True,
        ai_confidence=0.92,
        complexity_score=4.5,
        effort_estimate=15
    )

    assert epic.is_ai_generated()
    assert epic.is_high_confidence()
    assert epic.complexity_score == 4.5

    errors = epic.validate()
    assert len(errors) == 0

# Mais testes para Project e Task...
```

---

## 6) Validação e Testes

### Estrutural
- Todas as entidades criadas em `tdd_core/domain/entities/`
- Imports funcionando corretamente sem dependências circulares
- Zero dependências externas além de stdlib

### Funcional
- Todas as entidades instanciáveis com campos obrigatórios
- Métodos de validação retornando erros apropriados
- Métodos de cálculo (progress em Project, efficiency em Task) funcionando
- Scoring de épicos delegado ao PriorityScorer (Camada de Aplicação)

### Qualidade
- 100% cobertura de testes para todas as entidades
- Type hints completos para todos os métodos e propriedades
- Docstrings descritivas para classes e métodos principais
- Sem violações de mypy ou outros linters

### Integração
- Importação bem-sucedida: `from tdd_core.domain.entities import ProductVision, Project, Epic, Task`
- Nenhuma regressão nos sistemas existentes (Streamlit continua funcional)
- Compatibilidade com estruturas de dados existentes no banco

---

## 7) Restrições e Não-Objetivos

- Não implementar value objects completos (História 1.3 cobrirá isso)
- Não criar repositórios ou serviços (Épicos 2 e 3)
- Não alterar banco de dados ou fazer migrações
- Não modificar UI Streamlit existente
- Não adicionar dependências externas desnecessárias
- Manter compatibilidade total com código existente

---

## 8) Riscos e Mitigações

### Risco: Incompatibilidade com estruturas existentes
**Mitigação:** Mapear cuidadosamente campos do banco atual para entidades, usar tipos opcionais onde apropriado

### Risco: Complexidade excessiva nas entidades
**Mitigação:** Começar simples, adicionar comportamentos incrementalmente, focar em validação básica

### Risco: Dependências acidentais
**Mitigação:** Revisar imports, usar apenas stdlib e typing, rodar testes de isolamento

---

## 9) Critérios de Pronto (DoR)

- Mapeamento completo dos campos do banco para entidades aprovado
- Estrutura das entidades revisada e alinhada com DDD
- Casos de teste especificados para cada entidade
- História 1.1 completada com sucesso (estrutura base pronta)

---

## 10) Definição de Pronto (DoD)

- [ ] Todas as 4 entidades criadas com campos completos
- [ ] Métodos de validação implementados e testados
- [ ] Métodos de comportamento de domínio implementados
- [ ] 100% cobertura de testes unitários
- [ ] Type hints completos, sem erros de mypy
- [ ] Docstrings para todas as classes e métodos públicos
- [ ] Imports atualizados em `__init__.py` files
- [ ] Smoke test de importação passando
- [ ] Nenhuma regressão no sistema existente
- [ ] Código formatado com Black e isort

---

## 11) Estimativa e Carga

- **Esforço total:** 8 Story Points
- **Distribuição:**
  - ProductVision entity: 3h
  - Epic entity (mais complexa): 4h
  - Project entity: 2h
  - Task entity: 2h
  - Atualização de __init__.py: 1h
  - Testes unitários: 3h
  - Total: ~15h (2 dias de desenvolvimento)

---

## 12) Validação com Documentação Existente

### Alinhamento com CLAUDE.md
- ✅ ProductVision: 15 campos obrigatórios conforme especificado
- ✅ Project: Hub central com metadados do wizard (78 campos)
- ✅ Epic: 56 campos incluindo IA (Phase 5.1) e ordenação topológica
- ✅ Task: Suporte TDD e TDAH conforme requisitos

### Compatibilidade com Sistema Atual
- ✅ Estruturas mapeadas de `streamlit_extension/pages/projetos/dto/`
- ✅ Campos alinhados com `framework_*` tables do banco
- ✅ Métodos de cálculo preservam lógica de negócio existente

---

## 13) Comando de Execução

```bash
# Branch da história
git checkout -b feature/historia-1-2-domain-entities

# Criar estrutura de entidades
mkdir -p tdd_core/domain/entities
mkdir -p tests/tdd_core/domain/entities

# Implementar entidades (seguir tarefas técnicas acima)

# Rodar testes
python -m pytest tests/tdd_core/domain/entities/ -v --cov=tdd_core.domain.entities

# Verificar tipos
python -m mypy tdd_core/domain/entities/

# Formatar código
python -m black tdd_core/domain/entities/
python -m isort tdd_core/domain/entities/

# Smoke test
python -c "from tdd_core.domain.entities import ProductVision, Project, Epic, Task; print('✅ Entities imported successfully')"
```

---

## 14) Referências

- Marco 0 — Extração do Domínio: `docs/marco_0_domain_extraction.md`
- PRD Final — Marco 0 e Gates: `prd_final.md`
- História 1.1 — Plano Executado: `docs/PLANO_HISTORIA_1_1.md`
- Sistema Atual — ProductVisionDTO: `streamlit_extension/pages/projetos/dto/product_vision_dto.py`
- Sistema Atual — EpicSuggestionDTO: `streamlit_extension/pages/projetos/dto/epic_suggestion_dto.py`
