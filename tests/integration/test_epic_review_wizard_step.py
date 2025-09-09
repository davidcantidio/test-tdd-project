"""
🧪 TDD Tests para Integração EpicReview Wizard - História 4.1 FASE 1.4

Testes end-to-end para integração com wizard existente:
- Step visibility gating (visível apenas quando há capítulos)
- Fluxo completo de salvamento com confirmação
- Cancel preserva mudanças em session state
- Integração real com sistema PriorityScorer da História 3.2
- Navegação entre etapas do wizard
- Persistência de dados entre sessões

Implementação TDD seguindo metodologia Red-Green-Refactor.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class MockSessionState:
    """Mock do session state do Streamlit"""
    def __init__(self):
        self._data = {}
        self.wizard_current_step = 1
        self.cap = {"lista": []}
        self.epic_review_state = {}
    
    def __getattr__(self, name):
        return self._data.get(name, None)
    
    def __setattr__(self, name, value):
        if name.startswith('_'):
            super().__setattr__(name, value)
        else:
            if not hasattr(self, '_data'):
                super().__setattr__('_data', {})
            self._data[name] = value


@dataclass
class MockCapitulo:
    """Mock de capítulo para testes"""
    id: int
    epic_key: str
    nome: str
    descricao: str = ""
    prioridade: int = 3
    duracao_dias: int = 5
    status: str = "pending"
    sort_order: int = 0


class TestEpicReviewWizardStep:
    """TDD Tests para Integração Wizard - História 4.1"""

    @pytest.fixture
    def mock_session_state(self):
        """Mock do session state com dados de teste"""
        session = MockSessionState()
        session.wizard_current_step = 2  # Na etapa de Capítulos
        session.cap = {
            "lista": [
                MockCapitulo(1, "EPIC_001", "Backend API", "Sistema de autenticação", 5, 10),
                MockCapitulo(2, "EPIC_002", "Frontend UI", "Interface do usuário", 4, 8),
                MockCapitulo(3, "EPIC_003", "Database", "Estrutura de dados", 3, 6),
            ]
        }
        return session

    @pytest.fixture
    def mock_streamlit(self):
        """Mock do Streamlit"""
        with patch('streamlit_extension.pages.projetos.steps.capitulos_step.epic_review.st') as st_mock:
            st_mock.session_state = MockSessionState()
            st_mock.button = Mock(return_value=False)
            st_mock.markdown = Mock()
            st_mock.columns = Mock(return_value=[Mock(), Mock(), Mock()])
            st_mock.expander = Mock()
            st_mock.success = Mock()
            st_mock.error = Mock()
            st_mock.warning = Mock()
            st_mock.rerun = Mock()
            yield st_mock

    @pytest.fixture
    def mock_priority_scorer(self):
        """Mock do PriorityScorer da História 3.2"""
        scorer = Mock()
        scorer.calculate_epic_scores.return_value = {
            "EPIC_001": Mock(total_score=0.95, valor_score=0.9, risco_score=0.8),
            "EPIC_002": Mock(total_score=0.85, valor_score=0.8, risco_score=0.9),
            "EPIC_003": Mock(total_score=0.75, valor_score=0.7, risco_score=0.8),
        }
        return scorer

    def test_step_visibility_gating(self, mock_session_state, mock_streamlit):
        """
        História 4.1: Step visível apenas quando há capítulos criados
        """
        # Esta import vai falhar - RED phase
        from streamlit_extension.pages.projetos.steps.capitulos_step.epic_review import render_epic_review_step
        from streamlit_extension.pages.projetos.steps.cap_state.init_nav import should_show_epic_review_step
        
        # Cenário 1: Com capítulos - deve mostrar step
        session_with_capitulos = mock_session_state
        should_show = should_show_epic_review_step(session_with_capitulos)
        assert should_show == True
        
        # Cenário 2: Sem capítulos - não deve mostrar step  
        session_without_capitulos = MockSessionState()
        session_without_capitulos.cap = {"lista": []}
        should_show = should_show_epic_review_step(session_without_capitulos)
        assert should_show == False
        
        # Cenário 3: Com capítulos já finalizados - não deve mostrar step
        session_finalized = MockSessionState()
        session_finalized.cap = {
            "lista": [MockCapitulo(1, "EPIC_001", "Test")],
            "finalized": True
        }
        should_show = should_show_epic_review_step(session_finalized)
        assert should_show == False
        
        # Verificar que render só funciona se gating passou
        if should_show_epic_review_step(session_with_capitulos):
            render_epic_review_step(session_with_capitulos)
            # Se chegou aqui sem erro, gating funcionou

    def test_save_flow_success(self, mock_session_state, mock_streamlit):
        """
        História 4.1: Fluxo completo de salvamento com confirmação
        """
        from streamlit_extension.pages.projetos.steps.capitulos_step.epic_review import EpicReviewPage
        
        # Mock dos serviços
        with patch('streamlit_extension.services.ServiceContainer') as mock_container:
            epic_service = Mock()
            epic_service.update_epic_order.return_value = Mock(success=True, data=True)
            mock_container.return_value.get_epic_service.return_value = epic_service
            
            # Criar página de review
            review_page = EpicReviewPage(mock_session_state)
            
            # Simular mudanças nos épicos
            review_page.move_epic_up(epic_id=2)  # Epic 2 sobe na ordem
            review_page.edit_epic(epic_id=1, title="New Backend Title")
            review_page.approve_epic(epic_id=3)
            
            # Verificar que há mudanças pendentes
            assert review_page.has_unsaved_changes() == True
            changes = review_page.get_changes_for_persistence()
            assert len(changes) == 3  # 3 épicos modificados
            
            # Simular confirmação do usuário
            with patch('streamlit_extension.components.form_components.st.button') as mock_button:
                mock_button.return_value = True  # Usuário clicou "Confirmar"
                
                # Executar save
                result = review_page.save_changes()
                
                # Verificar sucesso
                assert result.success == True
                
                # Verificar que service foi chamado
                epic_service.update_epic_order.assert_called_once()
                
                # Verificar que mudanças foram limpas
                assert review_page.has_unsaved_changes() == False

    def test_cancel_preserves_session(self, mock_session_state, mock_streamlit):
        """
        História 4.1: Cancel mantém mudanças apenas em session state
        """
        from streamlit_extension.pages.projetos.steps.capitulos_step.epic_review import EpicReviewPage
        
        # Criar página de review
        review_page = EpicReviewPage(mock_session_state)
        
        # Estado inicial
        initial_state = review_page.get_current_state()
        
        # Fazer mudanças
        review_page.move_epic_down(epic_id=1)
        review_page.edit_epic(epic_id=2, description="Changed description")
        
        # Verificar que mudanças estão em session
        assert review_page.has_unsaved_changes() == True
        
        # Cancel (não salvar)
        result = review_page.cancel_changes()
        
        # Verificar que cancel foi bem-sucedido
        assert result.success == True
        
        # Verificar que mudanças ainda estão em session state
        assert review_page.has_unsaved_changes() == True
        
        # Verificar que nenhuma persistência foi chamada
        with patch('streamlit_extension.services.ServiceContainer') as mock_container:
            epic_service = Mock()
            mock_container.return_value.get_epic_service.return_value = epic_service
            
            review_page.cancel_changes()
            
            # Service NÃO deve ter sido chamado
            epic_service.update_epic_order.assert_not_called()
        
        # Verificar que usuário pode continuar editando
        review_page.edit_epic(epic_id=3, status="approved")
        assert review_page.get_dirty_count() >= 3  # Mudanças acumuladas

    def test_integration_with_priority_weights(self, mock_session_state, mock_priority_scorer):
        """
        História 4.1: Integração real com sistema PriorityScorer da História 3.2
        """
        from streamlit_extension.pages.projetos.steps.capitulos_step.epic_review import EpicReviewPage
        from streamlit_extension.services.ServiceContainer import ServiceContainer
        
        project_id = 1
        
        # Mock do ServiceContainer para injetar PriorityScorer
        with patch('streamlit_extension.services.ServiceContainer') as mock_container:
            # Mock do repository de settings
            priority_repo = Mock()
            priority_repo.get_by_project_id.return_value = Mock(
                success=True,
                data=Mock(
                    valor_weight=0.5,
                    risco_weight=0.2,
                    esforco_weight=0.2,
                    alinhamento_weight=0.1
                )
            )
            
            # Mock do scorer com pesos específicos do projeto
            scorer = Mock()
            scorer.calculate_epic_scores.return_value = {
                "EPIC_001": Mock(total_score=0.95),
                "EPIC_002": Mock(total_score=0.85),
                "EPIC_003": Mock(total_score=0.75),
            }
            
            # Container retorna serviços mockados
            container = Mock()
            container.get_priority_settings_repository.return_value = priority_repo
            container.get_priority_scorer.return_value = scorer
            mock_container.return_value = container
            
            # Criar página com integração de prioridade
            review_page = EpicReviewPage(mock_session_state, project_id=project_id)
            
            # Verificar que ordem inicial usa PriorityScorer
            initial_order = review_page.get_ordered_epics()
            epic_keys = [e.epic_key for e in initial_order]
            assert epic_keys == ["EPIC_001", "EPIC_002", "EPIC_003"]  # Ordem por score
            
            # Verificar que scorer foi chamado com pesos do projeto
            scorer.calculate_epic_scores.assert_called_once()
            
            # Verificar que após modificações, não reordena automaticamente
            review_page.move_epic_down(epic_id=1)  # Usuário modifica ordem
            
            # Nova instância não deve mais usar scorer automaticamente
            review_page2 = EpicReviewPage(mock_session_state, project_id=project_id)
            assert review_page2.has_user_modifications() == True

    def test_wizard_navigation_integration(self, mock_session_state, mock_streamlit):
        """
        História 4.1: Integração com navegação do wizard
        """
        from streamlit_extension.pages.projetos.projeto_wizard import render_current_step
        from streamlit_extension.pages.projetos.steps.cap_state.init_nav import get_available_steps
        
        # Mock session state na etapa de capítulos
        session = mock_session_state
        session.wizard_current_step = 2
        
        # Verificar steps disponíveis
        available_steps = get_available_steps(session)
        
        # Epic Review deve estar disponível se há capítulos
        if len(session.cap["lista"]) > 0:
            assert "epic_review" in available_steps
        
        # Simular navegação para epic review
        session.wizard_current_step = 2.5  # Sub-step epic review
        
        # Render deve funcionar sem erro
        try:
            render_current_step(session)
            navigation_works = True
        except Exception as e:
            navigation_works = False
            
        assert navigation_works == True
        
        # Verificar que pode voltar para capítulos
        session.wizard_current_step = 2
        render_current_step(session)
        
        # Verificar que pode avançar para histórias se review completa
        with patch('streamlit_extension.pages.projetos.steps.capitulos_step.epic_review.is_review_complete') as mock_complete:
            mock_complete.return_value = True
            session.wizard_current_step = 3  # Histórias
            render_current_step(session)

    def test_error_handling_in_integration(self, mock_session_state, mock_streamlit):
        """
        História 4.1: Handling robusto de erros na integração
        """
        from streamlit_extension.pages.projetos.steps.capitulos_step.epic_review import EpicReviewPage
        
        # Mock service que falha
        with patch('streamlit_extension.services.ServiceContainer') as mock_container:
            epic_service = Mock()
            epic_service.update_epic_order.side_effect = Exception("Database connection failed")
            mock_container.return_value.get_epic_service.return_value = epic_service
            
            review_page = EpicReviewPage(mock_session_state)
            
            # Fazer mudanças
            review_page.edit_epic(epic_id=1, title="Test Change")
            
            # Tentar salvar (deve falhar graciosamente)
            result = review_page.save_changes()
            
            # Verificar que erro foi tratado
            assert result.success == False
            assert "database connection failed" in result.error.lower()
            
            # Verificar que mudanças ainda estão preservadas
            assert review_page.has_unsaved_changes() == True
            
            # Verificar que usuário pode tentar novamente
            changes = review_page.get_changes_for_persistence()
            assert len(changes) == 1

    def test_session_state_persistence(self, mock_session_state):
        """
        História 4.1: Persistência correta no session state
        """
        from streamlit_extension.pages.projetos.steps.capitulos_step.epic_review import EpicReviewPage
        
        # Página inicial
        review_page1 = EpicReviewPage(mock_session_state)
        
        # Fazer mudanças
        review_page1.move_epic_up(epic_id=3)
        review_page1.edit_epic(epic_id=2, title="Modified Title")
        
        # Simular nova instância (como seria no Streamlit)
        review_page2 = EpicReviewPage(mock_session_state)
        
        # Verificar que estado foi preservado
        assert review_page2.has_unsaved_changes() == True
        
        # Verificar que mudanças específicas foram mantidas
        changes = review_page2.get_changes_for_persistence()
        title_changes = [c for c in changes if 'title' in c]
        assert len(title_changes) >= 1
        
        # Verificar ordem modificada
        ordered_epics = review_page2.get_ordered_epics()
        epic3_position = next((i for i, e in enumerate(ordered_epics) if e.id == 3), -1)
        assert epic3_position < 2  # Epic 3 subiu na ordem

    def test_performance_with_large_dataset(self, mock_streamlit):
        """
        História 4.1: Performance com muitos capítulos
        """
        # Session com muitos capítulos
        large_session = MockSessionState()
        large_session.cap = {"lista": []}
        
        # Criar 100 capítulos
        for i in range(100):
            large_session.cap["lista"].append(
                MockCapitulo(
                    id=i+1,
                    epic_key=f"EPIC_{i+1:03d}",
                    nome=f"Epic {i+1}",
                    descricao=f"Description for epic {i+1}",
                    prioridade=((i % 5) + 1),
                    duracao_dias=((i % 20) + 1)
                )
            )
        
        from streamlit_extension.pages.projetos.steps.capitulos_step.epic_review import EpicReviewPage
        
        # Medir tempo de criação
        import time
        start_time = time.time()
        
        review_page = EpicReviewPage(large_session)
        
        creation_time = time.time() - start_time
        
        # Deve ser eficiente (< 1 segundo para 100 épicos)
        assert creation_time < 1.0, f"Creation took {creation_time:.3f}s, expected < 1.0s"
        
        # Verificar que todos os épicos foram carregados
        epics = review_page.get_ordered_epics()
        assert len(epics) == 100
        
        # Medir tempo de operação
        start_time = time.time()
        review_page.move_epic_up(epic_id=50)
        operation_time = time.time() - start_time
        
        # Operação deve ser rápida (< 100ms)
        assert operation_time < 0.1, f"Move operation took {operation_time:.3f}s, expected < 0.1s"