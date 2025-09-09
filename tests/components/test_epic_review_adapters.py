"""
🧪 TDD Tests para Adaptadores de EpicReview - História 4.1 FASE 1.2

Testes específicos para adaptadores entre DTO e ViewModel com:
- Conversão completa dto→vm (id, título, descrição, tags, status, sort_order)
- Conversão vm→patch mínima (apenas campos alterados)
- Widget keys únicos com padrão _wiz_key("cap_review", epic.id, field)
- Transições determinísticas de drag state
- Reordering determinístico com tie-breakers
- Proteções contra movimentos out-of-range

Implementação TDD seguindo metodologia Red-Green-Refactor.
"""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class MockEpicDTO:
    """Mock Epic DTO para testes"""
    id: int
    epic_key: str
    name: str
    description: str = ""
    tags: List[str] = None
    status: str = "pending"
    sort_order: int = 0
    priority: int = 3
    complexity_score: float = 3.0
    effort_estimate: int = 5
    ai_confidence: float = 0.8
    created_at: str = "2025-01-01T00:00:00"
    updated_at: str = "2025-01-01T00:00:00"
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass 
class MockViewModelEpic:
    """Mock ViewModel Epic para testes"""
    id: int
    epic_key: str
    title: str
    description: str = ""
    tags: List[str] = None
    status: str = "pending"
    sort_order: int = 0
    is_dirty: bool = False
    original_values: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.original_values is None:
            self.original_values = {}


class TestEpicReviewAdapters:
    """TDD Tests para EpicReviewAdapters - História 4.1"""

    @pytest.fixture
    def sample_epic_dto(self):
        """Fixture com DTO de épico de teste"""
        return MockEpicDTO(
            id=1,
            epic_key="EPIC_001",
            name="Sample Epic",
            description="A sample epic for testing",
            tags=["backend", "api", "auth"],
            status="pending",
            sort_order=2,
            priority=4,
            complexity_score=3.5,
            effort_estimate=8,
            ai_confidence=0.9
        )

    @pytest.fixture
    def sample_vm_epic(self):
        """Fixture com ViewModel Epic de teste"""
        return MockViewModelEpic(
            id=1,
            epic_key="EPIC_001", 
            title="Modified Epic Title",
            description="Modified description",
            tags=["frontend", "ui", "ux"],
            status="approved",
            sort_order=5,
            is_dirty=True,
            original_values={
                "title": "Sample Epic",
                "description": "A sample epic for testing",
                "tags": ["backend", "api", "auth"],
                "status": "pending",
                "sort_order": 2
            }
        )

    def test_dto_to_vm_conversion_complete(self, sample_epic_dto):
        """
        História 4.1: Conversão DTO→VM deve incluir todos os campos específicos
        """
        # Esta import vai falhar - RED phase
        from streamlit_extension.components.epic_review_adapters import EpicToViewModelAdapter
        
        adapter = EpicToViewModelAdapter()
        
        # Conversão completa
        vm_epic = adapter.convert(sample_epic_dto)
        
        # Verificar todos os campos essenciais
        assert vm_epic.id == 1
        assert vm_epic.epic_key == "EPIC_001"
        assert vm_epic.title == "Sample Epic"  # name → title
        assert vm_epic.description == "A sample epic for testing"
        assert vm_epic.tags == ["backend", "api", "auth"]
        assert vm_epic.status == "pending"
        assert vm_epic.sort_order == 2
        
        # Verificar campos de controle
        assert vm_epic.is_dirty == False  # Novo épico não é dirty
        assert vm_epic.original_values == {}  # Sem valores originais ainda
        
        # Verificar campos computados opcionais
        computed_fields = adapter.get_computed_fields(vm_epic)
        assert 'display_priority' in computed_fields
        assert 'complexity_display' in computed_fields
        assert 'effort_display' in computed_fields

    def test_vm_to_patch_minimal(self, sample_vm_epic):
        """
        História 4.1: Conversão VM→patch deve incluir apenas campos alterados
        """
        from streamlit_extension.components.epic_review_adapters import ViewModelToPatchAdapter
        
        adapter = ViewModelToPatchAdapter()
        
        # Gerar patch apenas com mudanças
        patch = adapter.generate_patch(sample_vm_epic)
        
        # Deve incluir apenas campos modificados
        expected_fields = {'title', 'description', 'tags', 'status', 'sort_order'}
        actual_fields = set(patch.keys())
        
        # epic_id sempre presente para identificação
        assert 'epic_id' in patch
        assert patch['epic_id'] == 1
        
        # Apenas campos que mudaram
        assert actual_fields.issuperset(expected_fields)
        
        # Valores corretos
        assert patch['title'] == "Modified Epic Title"
        assert patch['description'] == "Modified description"
        assert patch['tags'] == ["frontend", "ui", "ux"]
        assert patch['status'] == "approved"
        assert patch['sort_order'] == 5
        
        # Não deve incluir campos que não mudaram
        assert 'epic_key' not in patch  # Nunca muda
        assert 'created_at' not in patch  # Não modificável

    def test_widget_key_uniqueness(self):
        """
        História 4.1: Widget keys devem ser únicos usando padrão específico
        """
        from streamlit_extension.components.epic_review_adapters import WidgetKeyBuilder
        
        builder = WidgetKeyBuilder()
        
        # Padrão: _wiz_key("cap_review", epic.id, field)
        key1 = builder.build_key(epic_id=1, field="title")
        key2 = builder.build_key(epic_id=2, field="title") 
        key3 = builder.build_key(epic_id=1, field="description")
        
        # Keys devem ser únicos
        assert key1 != key2  # Diferentes epic_id
        assert key1 != key3  # Diferentes field
        assert key2 != key3  # Diferentes epic_id e field
        
        # Padrão específico
        assert "cap_review" in key1
        assert "1" in key1  # epic_id
        assert "title" in key1  # field
        
        # Mesmo épico e campo deve gerar mesmo key (determinístico)
        key1_repeat = builder.build_key(epic_id=1, field="title")
        assert key1 == key1_repeat
        
        # Session ID deve tornar keys únicos entre sessões
        builder_session2 = WidgetKeyBuilder(session_id="session_2")
        key1_session2 = builder_session2.build_key(epic_id=1, field="title")
        assert key1 != key1_session2

    def test_drag_state_transitions(self):
        """
        História 4.1: Transições de drag state devem ser determinísticas
        """
        from streamlit_extension.components.epic_review_adapters import DragDropStateManager
        
        manager = DragDropStateManager()
        
        # Estado inicial
        assert manager.get_current_state() == "idle"
        assert manager.get_dragged_epic_id() is None
        
        # Iniciar drag
        result = manager.start_drag(epic_id=1, from_position=2)
        assert result.success == True
        assert manager.get_current_state() == "dragging"
        assert manager.get_dragged_epic_id() == 1
        assert manager.get_drag_from_position() == 2
        
        # Hover sobre posição válida
        result = manager.hover_position(to_position=4)
        assert result.success == True
        assert manager.get_hover_position() == 4
        
        # Drop em posição válida
        result = manager.drop(to_position=4)
        assert result.success == True
        assert manager.get_current_state() == "idle"
        assert manager.get_last_drop_result() == {"from": 2, "to": 4, "epic_id": 1}
        
        # Cancel drag
        manager.start_drag(epic_id=2, from_position=1)
        result = manager.cancel_drag()
        assert result.success == True
        assert manager.get_current_state() == "idle"
        assert manager.get_dragged_epic_id() is None

    def test_deterministic_reordering(self):
        """
        História 4.1: Reordering deve ser determinístico com tie-breakers
        """
        from streamlit_extension.components.epic_review_adapters import DragDropStateManager
        
        manager = DragDropStateManager()
        
        # Lista de épicos com mesmos sort_order (tie scenario)
        epics = [
            MockViewModelEpic(id=1, epic_key="EPIC_001", title="Epic 1", sort_order=5),
            MockViewModelEpic(id=2, epic_key="EPIC_002", title="Epic 2", sort_order=5),
            MockViewModelEpic(id=3, epic_key="EPIC_003", title="Epic 3", sort_order=5),
            MockViewModelEpic(id=4, epic_key="EPIC_004", title="Epic 4", sort_order=5),
        ]
        
        # Reordernar determinísticamente
        reordered = manager.reorder_deterministic(epics, move_epic_id=3, to_position=0)
        
        # Epic 3 deve estar na posição 0
        assert reordered[0].id == 3
        
        # Demais épicos mantêm ordem determinística (por ID como tie-breaker)
        remaining_ids = [e.id for e in reordered[1:]]
        assert remaining_ids == [1, 2, 4]  # Ordem crescente por ID
        
        # Sort orders devem ser atualizados sequencialmente
        for i, epic in enumerate(reordered):
            assert epic.sort_order == i

    def test_out_of_range_guards(self):
        """
        História 4.1: Proteção contra movimentos out-of-range
        """
        from streamlit_extension.components.epic_review_adapters import DragDropStateManager
        
        manager = DragDropStateManager()
        
        # Lista com 5 épicos (índices 0-4)
        epic_count = 5
        
        # Tentar mover para posição negativa
        result = manager.validate_move(from_position=2, to_position=-1, epic_count=epic_count)
        assert result.success == False
        assert "out of range" in result.error.lower()
        
        # Tentar mover para posição além do limite
        result = manager.validate_move(from_position=2, to_position=5, epic_count=epic_count)
        assert result.success == False
        assert "out of range" in result.error.lower()
        
        # Movimento no-op (mesma posição)
        result = manager.validate_move(from_position=2, to_position=2, epic_count=epic_count)
        assert result.success == False
        assert "no-op" in result.error.lower()
        
        # Movimento válido
        result = manager.validate_move(from_position=2, to_position=4, epic_count=epic_count)
        assert result.success == True
        
        # From position inválida
        result = manager.validate_move(from_position=5, to_position=2, epic_count=epic_count)
        assert result.success == False
        assert "invalid from position" in result.error.lower()

    def test_batch_conversion_performance(self):
        """
        História 4.1: Conversões em lote devem ser eficientes
        """
        from streamlit_extension.components.epic_review_adapters import EpicToViewModelAdapter
        
        adapter = EpicToViewModelAdapter()
        
        # Lista de 100 épicos para teste de performance
        epic_dtos = []
        for i in range(100):
            epic_dtos.append(MockEpicDTO(
                id=i,
                epic_key=f"EPIC_{i:03d}",
                name=f"Epic {i}",
                description=f"Description {i}",
                tags=[f"tag{i}", f"category{i//10}"],
                sort_order=i
            ))
        
        # Conversão em lote
        import time
        start_time = time.time()
        vm_epics = adapter.convert_batch(epic_dtos)
        conversion_time = time.time() - start_time
        
        # Deve ser eficiente (< 100ms para 100 épicos)
        assert conversion_time < 0.1
        
        # Todos os épicos convertidos
        assert len(vm_epics) == 100
        
        # Verificar alguns épicos convertidos
        assert vm_epics[0].id == 0
        assert vm_epics[50].title == "Epic 50"
        assert vm_epics[99].epic_key == "EPIC_099"

    def test_error_handling_in_conversion(self):
        """
        História 4.1: Conversões devem tratar erros graciosamente
        """
        from streamlit_extension.components.epic_review_adapters import EpicToViewModelAdapter
        
        adapter = EpicToViewModelAdapter()
        
        # DTO com dados inválidos
        invalid_dto = MockEpicDTO(
            id=None,  # ID inválido
            epic_key="",  # Key vazia
            name="",  # Nome vazio
            tags=None  # Tags None
        )
        
        # Conversão deve retornar erro, não exception
        result = adapter.convert_safe(invalid_dto)
        assert result.success == False
        assert "invalid epic data" in result.error.lower()
        
        # Conversão em lote deve pular épicos inválidos
        mixed_dtos = [
            MockEpicDTO(id=1, epic_key="EPIC_001", name="Valid Epic"),
            invalid_dto,
            MockEpicDTO(id=3, epic_key="EPIC_003", name="Another Valid Epic")
        ]
        
        result = adapter.convert_batch_safe(mixed_dtos)
        assert result.success == True
        assert len(result.data) == 2  # Apenas épicos válidos
        assert result.warnings[0] == "Skipped 1 invalid epic"

    def test_widget_key_injection_protection(self):
        """
        História 4.1: Widget keys devem ser protegidos contra injection
        """
        from streamlit_extension.components.epic_review_adapters import WidgetKeyBuilder
        
        builder = WidgetKeyBuilder()
        
        # Tentar injetar caracteres perigosos
        malicious_field = "title'; DROP TABLE epics; --"
        
        key = builder.build_key(epic_id=1, field=malicious_field)
        
        # Key deve ser sanitizada (sem caracteres perigosos)
        assert "DROP" not in key
        assert ";" not in key
        assert "--" not in key
        
        # Deve ser uma key válida
        assert "cap_review" in key
        assert "1" in key  # epic_id preservado
        
        # Field deve ser sanitizado mas reconhecível
        sanitized_field = builder.sanitize_field(malicious_field)
        assert "title" in sanitized_field  # Parte válida preservada
        assert len(sanitized_field) < len(malicious_field)  # Partes perigosas removidas

    def test_conversion_with_null_handling(self, sample_epic_dto):
        """
        História 4.1: Conversões devem tratar valores null/None graciosamente
        """
        from streamlit_extension.components.epic_review_adapters import EpicToViewModelAdapter
        
        adapter = EpicToViewModelAdapter()
        
        # DTO com alguns valores None
        dto_with_nulls = MockEpicDTO(
            id=1,
            epic_key="EPIC_001",
            name="Epic with nulls",
            description=None,  # None
            tags=None,         # None
            status=None        # None
        )
        
        vm_epic = adapter.convert(dto_with_nulls)
        
        # Valores None devem ser convertidos para defaults
        assert vm_epic.description == ""  # None → empty string
        assert vm_epic.tags == []         # None → empty list  
        assert vm_epic.status == "pending"  # None → default status
        
        # Outros campos normais
        assert vm_epic.id == 1
        assert vm_epic.title == "Epic with nulls"