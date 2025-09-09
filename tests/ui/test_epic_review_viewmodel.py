"""
🧪 TDD Tests para EpicReviewViewModel - História 4.1 FASE 1.1

Testes robustos para ViewModel de revisão de épicos com:
- Identidade estável baseada em epic.id (nunca índice)
- Movimentação determinística com bounds
- Undo scope limitado a 20 ações com records imutáveis  
- Dirty flag para controle de estado "Save"
- Validação de invariantes com sanitização
- Integração com PriorityScorer via DI

Implementação TDD seguindo metodologia Red-Green-Refactor.
"""

import pytest
import uuid
from unittest.mock import Mock, MagicMock
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Mock classes para testes (serão implementadas na GREEN phase)
@dataclass
class MockEpic:
    """Mock epic para testes"""
    id: int
    epic_key: str  
    title: str
    description: str = ""
    tags: List[str] = None
    status: str = "pending"
    sort_order: int = 0
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

@dataclass
class MockAction:
    """Mock action record para undo/redo"""
    action_type: str  # 'move', 'edit', 'approve', 'reject'
    epic_id: int
    old_value: Any
    new_value: Any
    timestamp: float


class TestEpicReviewViewModel:
    """TDD Tests para EpicReviewViewModel - História 4.1"""

    @pytest.fixture
    def sample_epics(self):
        """Fixture com épicos de teste"""
        return [
            MockEpic(id=1, epic_key="EPIC_001", title="Epic 1", sort_order=0),
            MockEpic(id=2, epic_key="EPIC_002", title="Epic 2", sort_order=1),
            MockEpic(id=3, epic_key="EPIC_003", title="Epic 3", sort_order=2),
            MockEpic(id=4, epic_key="EPIC_004", title="Epic 4", sort_order=3),
            MockEpic(id=5, epic_key="EPIC_005", title="Epic 5", sort_order=4),
        ]

    @pytest.fixture
    def mock_priority_scorer(self):
        """Mock do PriorityScorer para testes de integração"""
        scorer = Mock()
        scorer.calculate_epic_scores.return_value = {
            "EPIC_001": Mock(total_score=0.95),
            "EPIC_002": Mock(total_score=0.85),
            "EPIC_003": Mock(total_score=0.75),
            "EPIC_004": Mock(total_score=0.65),
            "EPIC_005": Mock(total_score=0.55),
        }
        return scorer

    def test_stable_epic_id_identity(self, sample_epics):
        """
        História 4.1: Operações devem ser baseadas em epic.id, nunca índice
        """
        # Esta import vai falhar - RED phase
        from streamlit_extension.components.epic_review import EpicReviewViewModel
        
        viewmodel = EpicReviewViewModel(sample_epics)
        
        # Deve identificar épicos por ID, não por índice
        epic = viewmodel.get_epic_by_id(3)
        assert epic.id == 3
        assert epic.epic_key == "EPIC_003"
        
        # Move epic por ID (não índice)
        result = viewmodel.move_epic_up(epic_id=3)
        assert result.success == True
        
        # Verifica que o épico mantém identidade
        moved_epic = viewmodel.get_epic_by_id(3)
        assert moved_epic.id == 3  # ID nunca muda
        assert moved_epic.epic_key == "EPIC_003"  # Key nunca muda
        
        # Índice deve ter mudado, mas identidade preservada
        new_position = viewmodel.get_position_by_id(3)
        assert new_position == 1  # Moveu para cima na ordem

    def test_move_bounds_deterministic(self, sample_epics):
        """
        História 4.1: Movimentação com bounds e comportamento determinístico
        """
        from streamlit_extension.components.epic_review import EpicReviewViewModel
        
        viewmodel = EpicReviewViewModel(sample_epics)
        
        # Teste de bounds - primeiro épico não pode subir mais
        result = viewmodel.move_epic_up(epic_id=1)  # Já está no topo
        assert result.success == False
        assert "cannot move up" in result.error.lower()
        
        # Teste de bounds - último épico não pode descer mais  
        result = viewmodel.move_epic_down(epic_id=5)  # Já está no final
        assert result.success == False
        assert "cannot move down" in result.error.lower()
        
        # Movimento válido deve ser determinístico
        initial_order = [e.id for e in viewmodel.get_ordered_epics()]
        
        viewmodel.move_epic_up(epic_id=3)
        after_move = [e.id for e in viewmodel.get_ordered_epics()]
        
        # Epic 3 deve ter trocado de lugar com epic 2
        epic3_pos = after_move.index(3)
        epic2_pos = after_move.index(2)
        assert epic3_pos < epic2_pos

    def test_multiple_moves_result(self, sample_epics):
        """
        História 4.1: Múltiplas movimentações consecutivas devem ser determinísticas
        """
        from streamlit_extension.components.epic_review import EpicReviewViewModel
        
        viewmodel = EpicReviewViewModel(sample_epics)
        
        # Sequência de movimentos
        viewmodel.move_epic_up(epic_id=5)    # 5 vai para posição 3
        viewmodel.move_epic_up(epic_id=5)    # 5 vai para posição 2
        viewmodel.move_epic_up(epic_id=5)    # 5 vai para posição 1
        viewmodel.move_epic_up(epic_id=5)    # 5 vai para posição 0 (topo)
        
        final_order = [e.id for e in viewmodel.get_ordered_epics()]
        assert final_order[0] == 5  # Epic 5 agora está no topo
        assert final_order == [5, 1, 2, 3, 4]  # Ordem determinística

    def test_undo_scope_limit(self, sample_epics):
        """
        História 4.1: Undo limitado a 20 ações com records imutáveis
        """
        from streamlit_extension.components.epic_review import EpicReviewViewModel
        
        viewmodel = EpicReviewViewModel(sample_epics)
        
        # Fazer 25 ações (5 além do limite de 20)
        for i in range(25):
            if i % 2 == 0:
                viewmodel.move_epic_down(epic_id=1)
            else:
                viewmodel.move_epic_up(epic_id=1)
        
        # Deve manter apenas as últimas 20 ações
        undo_stack = viewmodel.get_undo_stack()
        assert len(undo_stack) == 20
        
        # Cada action deve ser um record imutável
        for action in undo_stack:
            assert isinstance(action, MockAction)
            assert action.action_type in ['move', 'edit', 'approve', 'reject']
            assert hasattr(action, 'timestamp')
            assert hasattr(action, 'epic_id')
            
        # Undo deve funcionar
        result = viewmodel.undo()
        assert result.success == True
        assert len(viewmodel.get_undo_stack()) == 19

    def test_dirty_flag_management(self, sample_epics):
        """
        História 4.1: Dirty flag para controle de estado "Save"
        """
        from streamlit_extension.components.epic_review import EpicReviewViewModel
        
        viewmodel = EpicReviewViewModel(sample_epics)
        
        # Inicialmente não tem mudanças
        assert viewmodel.has_unsaved_changes() == False
        assert viewmodel.get_dirty_count() == 0
        
        # Fazer uma mudança
        viewmodel.move_epic_up(epic_id=3)
        assert viewmodel.has_unsaved_changes() == True
        assert viewmodel.get_dirty_count() == 1
        
        # Editar um épico
        viewmodel.edit_epic(epic_id=2, title="New Title")
        assert viewmodel.get_dirty_count() == 2
        
        # Aprovar um épico
        viewmodel.approve_epic(epic_id=1)
        assert viewmodel.get_dirty_count() == 3
        
        # Marcar como salvo deve limpar dirty flag
        viewmodel.mark_as_saved()
        assert viewmodel.has_unsaved_changes() == False
        assert viewmodel.get_dirty_count() == 0

    def test_initial_order_from_scorer(self, sample_epics, mock_priority_scorer):
        """
        História 4.1: Ordem inicial via PriorityScorer mock injetado
        """
        from streamlit_extension.components.epic_review import EpicReviewViewModel
        
        # Criar ViewModel com PriorityScorer injetado
        viewmodel = EpicReviewViewModel(sample_epics, priority_scorer=mock_priority_scorer)
        
        # Deve usar scorer para ordem inicial se não há mudanças do usuário
        initial_order = [e.id for e in viewmodel.get_ordered_epics()]
        
        # Ordem deve seguir scores (maior score primeiro)
        # EPIC_001: 0.95, EPIC_002: 0.85, EPIC_003: 0.75, EPIC_004: 0.65, EPIC_005: 0.55
        expected_order = [1, 2, 3, 4, 5]
        assert initial_order == expected_order
        
        # Deve marcar que não tem mudanças do usuário ainda
        assert viewmodel.has_user_modifications() == False
        
        # Após usuário modificar, não deve mais usar scorer automaticamente
        viewmodel.move_epic_up(epic_id=5)
        assert viewmodel.has_user_modifications() == True
        
        # Nova instância deve manter modificações do usuário
        viewmodel2 = EpicReviewViewModel(viewmodel.get_ordered_epics(), mock_priority_scorer)
        assert viewmodel2.has_user_modifications() == True

    def test_validation_invariants(self, sample_epics):
        """
        História 4.1: Título não-vazio, tags sanitizadas, invariantes
        """
        from streamlit_extension.components.epic_review import EpicReviewViewModel
        
        viewmodel = EpicReviewViewModel(sample_epics)
        
        # Título não pode ser vazio
        result = viewmodel.edit_epic(epic_id=1, title="")
        assert result.success == False
        assert "title cannot be empty" in result.error.lower()
        
        # Título deve ser sanitizado (strip whitespace)
        result = viewmodel.edit_epic(epic_id=1, title="  New Title  ")
        assert result.success == True
        epic = viewmodel.get_epic_by_id(1)
        assert epic.title == "New Title"  # Sem espaços extras
        
        # Tags devem ser sanitizadas
        result = viewmodel.edit_epic(epic_id=1, tags=["  tag1  ", "", "tag2", "tag1"])
        assert result.success == True
        epic = viewmodel.get_epic_by_id(1)
        assert epic.tags == ["tag1", "tag2"]  # Sem duplicatas, sem vazias, trimmed
        
        # Descrição com limite de caracteres
        long_description = "x" * 2000  # 2000 caracteres
        result = viewmodel.edit_epic(epic_id=1, description=long_description)
        assert result.success == False
        assert "description too long" in result.error.lower()

    def test_redo_support_preparation(self, sample_epics):
        """
        História 4.1: Preparação para suporte de redo futuro
        """
        from streamlit_extension.components.epic_review import EpicReviewViewModel
        
        viewmodel = EpicReviewViewModel(sample_epics)
        
        # Fazer algumas ações
        viewmodel.move_epic_up(epic_id=3)
        viewmodel.edit_epic(epic_id=2, title="Changed Title")
        
        # Undo uma ação
        viewmodel.undo()
        
        # Deve ter redo disponível
        assert viewmodel.has_redo_available() == True
        redo_stack = viewmodel.get_redo_stack()
        assert len(redo_stack) == 1
        
        # Action no redo deve ser imutável
        redo_action = redo_stack[0]
        assert isinstance(redo_action, MockAction)
        assert redo_action.action_type == 'edit'
        assert redo_action.epic_id == 2

    def test_approve_reject_mutually_exclusive(self, sample_epics):
        """
        História 4.1: Approve/Reject devem ser mutualmente exclusivos
        """
        from streamlit_extension.components.epic_review import EpicReviewViewModel
        
        viewmodel = EpicReviewViewModel(sample_epics)
        
        # Aprovar um épico
        result = viewmodel.approve_epic(epic_id=1)
        assert result.success == True
        
        epic = viewmodel.get_epic_by_id(1)
        assert epic.status == "approved"
        
        # Rejeitar o mesmo épico deve mudar o status
        result = viewmodel.reject_epic(epic_id=1)
        assert result.success == True
        
        epic = viewmodel.get_epic_by_id(1)
        assert epic.status == "rejected"  # Mudou de approved para rejected
        
        # Aprovar novamente deve mudar de rejected para approved
        result = viewmodel.approve_epic(epic_id=1)
        assert result.success == True
        
        epic = viewmodel.get_epic_by_id(1)
        assert epic.status == "approved"

    def test_filter_by_status(self, sample_epics):
        """
        História 4.1: Filtros All/Approved/Rejected/Edited
        """
        from streamlit_extension.components.epic_review import EpicReviewViewModel
        
        viewmodel = EpicReviewViewModel(sample_epics)
        
        # Modificar status de alguns épicos
        viewmodel.approve_epic(epic_id=1)
        viewmodel.reject_epic(epic_id=2) 
        viewmodel.edit_epic(epic_id=3, title="Edited Title")
        
        # Filtro All deve retornar todos
        all_epics = viewmodel.filter_epics("all")
        assert len(all_epics) == 5
        
        # Filtro Approved
        approved_epics = viewmodel.filter_epics("approved")
        assert len(approved_epics) == 1
        assert approved_epics[0].id == 1
        
        # Filtro Rejected
        rejected_epics = viewmodel.filter_epics("rejected")
        assert len(rejected_epics) == 1
        assert rejected_epics[0].id == 2
        
        # Filtro Edited (épicos com mudanças no conteúdo)
        edited_epics = viewmodel.filter_epics("edited")
        assert len(edited_epics) >= 1  # Pelo menos o épico 3
        edited_ids = [e.id for e in edited_epics]
        assert 3 in edited_ids

    def test_get_changes_for_persistence(self, sample_epics):
        """
        História 4.1: Obter mudanças para persistência (payload mínimo)
        """
        from streamlit_extension.components.epic_review import EpicReviewViewModel
        
        viewmodel = EpicReviewViewModel(sample_epics)
        
        # Fazer mudanças
        viewmodel.move_epic_up(epic_id=3)  # Mudou sort_order
        viewmodel.edit_epic(epic_id=2, title="New Title")  # Mudou title
        viewmodel.approve_epic(epic_id=1)  # Mudou status
        
        # Obter mudanças para persistir
        changes = viewmodel.get_changes_for_persistence()
        
        # Deve retornar apenas campos modificados
        assert len(changes) == 3
        
        # Verificar estrutura de mudanças
        change_by_id = {c['epic_id']: c for c in changes}
        
        # Epic 1: apenas status mudou
        epic1_changes = change_by_id[1]
        assert 'status' in epic1_changes
        assert epic1_changes['status'] == 'approved'
        assert 'title' not in epic1_changes  # Não mudou
        
        # Epic 2: apenas title mudou
        epic2_changes = change_by_id[2]  
        assert 'title' in epic2_changes
        assert epic2_changes['title'] == 'New Title'
        assert 'status' not in epic2_changes  # Não mudou
        
        # Epic 3: apenas sort_order mudou
        epic3_changes = change_by_id[3]
        assert 'sort_order' in epic3_changes
        assert isinstance(epic3_changes['sort_order'], int)