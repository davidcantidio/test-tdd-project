"""
🎯 Epic Review Integration Page - História 4.1 FASE 2.4

Integração completa do sistema de revisão de épicos com:
- EpicReviewViewModel para gerenciamento de estado
- Adaptadores para conversão entre camadas
- PriorityScorer 3.2 para ordenação inicial
- Session state persistence
- Wizard navigation integration
- Error handling robusto

Implementação TDD seguindo metodologia Green-phase.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import streamlit as st
from streamlit_extension.components.epic_review import EpicReviewViewModel
from streamlit_extension.components.epic_review_adapters import (
    EpicToViewModelAdapter,
    ViewModelToPatchAdapter,
    DragDropStateManager,
    ConversionResult
)
from streamlit_extension.services.base import ServiceResult


@dataclass
class EpicReviewResult:
    """Result wrapper para operações da página de review"""
    success: bool
    error: str = ""
    data: Any = None


class EpicReviewPage:
    """
    Página principal de integração para revisão e reordenação de épicos.
    
    Integra ViewModel, Adaptadores, PriorityScorer e Session State
    para fornecer interface completa de revisão de épicos.
    """
    
    def __init__(self, session_state, project_id: Optional[int] = None):
        """Inicializa página com session state e project_id opcional"""
        self.session_state = session_state
        self.project_id = project_id or getattr(session_state, 'current_project_id', 1)
        
        # Inicializar adaptadores
        self.dto_adapter = EpicToViewModelAdapter()
        self.patch_adapter = ViewModelToPatchAdapter()
        self.drag_manager = DragDropStateManager()
        
        # Carregar ou inicializar ViewModel
        self.viewmodel = self._initialize_viewmodel()
    
    def _initialize_viewmodel(self) -> EpicReviewViewModel:
        """Inicializa ViewModel com dados do session state ou PriorityScorer"""
        # Verificar se já existe estado no session state
        if hasattr(self.session_state, 'epic_review_state') and self.session_state.epic_review_state:
            # Restaurar do session state
            return self._restore_from_session_state()
        else:
            # Primeira inicialização - usar dados dos capítulos
            return self._create_from_capitulos()
    
    def _restore_from_session_state(self) -> EpicReviewViewModel:
        """Restaura ViewModel do session state"""
        state_data = self.session_state.epic_review_state
        
        # Converter dados salvos de volta para ViewModel
        epics_data = state_data.get('epics', [])
        converted_epics = []
        
        for epic_data in epics_data:
            # Criar ViewModel epic diretamente dos dados salvos
            from streamlit_extension.components.epic_review import ViewModelEpic
            vm_epic = ViewModelEpic(
                id=epic_data['id'],
                epic_key=epic_data['epic_key'],
                title=epic_data['title'],
                description=epic_data.get('description', ''),
                tags=epic_data.get('tags', []),
                status=epic_data.get('status', 'pending'),
                sort_order=epic_data.get('sort_order', 0),
                is_dirty=epic_data.get('is_dirty', False),
                original_values=epic_data.get('original_values', {})
            )
            converted_epics.append(vm_epic)
        
        # Inicializar ViewModel com épicos restaurados
        viewmodel = EpicReviewViewModel(converted_epics)
        
        # Restaurar undo stack se existe
        if 'undo_stack' in state_data:
            viewmodel._undo_stack = state_data['undo_stack']
        
        return viewmodel
    
    def _create_from_capitulos(self) -> EpicReviewViewModel:
        """Cria ViewModel inicial dos dados de capítulos"""
        # Estado padrão dos capítulos fica em session_state.capitulos
        if not hasattr(self.session_state, 'capitulos') or not self.session_state.capitulos.get('lista'):
            return EpicReviewViewModel([])
        
        capitulos = self.session_state.capitulos['lista']
        
        # Converter capítulos para épicos DTO
        epic_dtos = []
        for i, capitulo in enumerate(capitulos):
            # capitulo é um dict conforme state_core
            epic_dto = {
                'id': capitulo.get('id', i + 1),
                'epic_key': capitulo.get('epic_key', f"EPIC_{i+1:03d}"),
                'name': capitulo.get('nome', f'Epic {i+1}'),
                'title': capitulo.get('nome', f'Epic {i+1}'),
                'description': capitulo.get('descricao', ''),
                'tags': capitulo.get('tags', []),
                'status': capitulo.get('status', 'pending'),
                'sort_order': capitulo.get('sort_order', i),
                'priority': capitulo.get('prioridade', 3),
                'effort_estimate': capitulo.get('duracao_dias', 5)
            }
            epic_dtos.append(epic_dto)
        
        # Converter para ViewModel epics usando adapter
        vm_epics = []
        for dto in epic_dtos:
            vm_epic = self.dto_adapter.convert(dto)
            vm_epics.append(vm_epic)
        
        # Verificar se deve usar PriorityScorer para ordem inicial
        priority_scorer = self._get_priority_scorer()
        if priority_scorer and not self.has_user_modifications():
            viewmodel = EpicReviewViewModel(vm_epics, priority_scorer=priority_scorer)
        else:
            viewmodel = EpicReviewViewModel(vm_epics)
        
        return viewmodel
    
    def _get_priority_scorer(self):
        """Obtém PriorityScorer com pesos do projeto via PrioritySettingsRepository DI"""
        try:
            from streamlit_extension.services.priority_scorer import PriorityScorer
            from streamlit_extension.services.service_container import get_priority_settings_repository
            settings_repo = get_priority_settings_repository()
            return PriorityScorer(project_id=self.project_id, settings_repo=settings_repo, total_scale=12.0)
        except Exception:
            # Se falhar, retornar None para usar ordem padrão
            return None
    
    def _save_to_session_state(self):
        """Salva estado atual no session state"""
        epics_data = []
        for epic in self.viewmodel.get_ordered_epics():
            epic_data = {
                'id': epic.id,
                'epic_key': epic.epic_key,
                'title': epic.title,
                'description': epic.description,
                'tags': epic.tags,
                'status': epic.status,
                'sort_order': epic.sort_order,
                'is_dirty': epic.is_dirty,
                'original_values': epic.original_values
            }
            epics_data.append(epic_data)
        
        # Salvar no session state
        if not hasattr(self.session_state, 'epic_review_state'):
            self.session_state.epic_review_state = {}
        
        self.session_state.epic_review_state = {
            'epics': epics_data,
            'undo_stack': getattr(self.viewmodel, '_undo_stack', []),
            'has_user_modifications': self.viewmodel.has_user_modifications()
        }
    
    # Interface pública da página
    
    def move_epic_up(self, epic_id: int) -> EpicReviewResult:
        """Move épico para cima na ordenação"""
        result = self.viewmodel.move_epic_up(epic_id)
        if result.success:
            self._save_to_session_state()
            return EpicReviewResult(success=True, data=result.data)
        else:
            first_error = result.get_first_error()
            error_msg = str(first_error) if first_error else "Move up failed"
            return EpicReviewResult(success=False, error=error_msg)
    
    def move_epic_down(self, epic_id: int) -> EpicReviewResult:
        """Move épico para baixo na ordenação"""
        result = self.viewmodel.move_epic_down(epic_id)
        if result.success:
            self._save_to_session_state()
            return EpicReviewResult(success=True, data=result.data)
        else:
            first_error = result.get_first_error()
            error_msg = str(first_error) if first_error else "Move down failed"
            return EpicReviewResult(success=False, error=error_msg)
    
    def edit_epic(self, epic_id: int, **kwargs) -> EpicReviewResult:
        """Edita épico com validação"""
        # Extrair campos suportados
        supported_fields = ['title', 'description', 'tags', 'status']
        epic_updates = {k: v for k, v in kwargs.items() if k in supported_fields}
        
        if not epic_updates:
            return EpicReviewResult(success=False, error="No valid fields to update")
        
        # Aplicar updates um por vez
        success_count = 0
        last_error = ""
        
        for field, value in epic_updates.items():
            if field == 'title':
                result = self.viewmodel.edit_epic(epic_id, title=value)
            elif field == 'description':
                result = self.viewmodel.edit_epic(epic_id, description=value)
            elif field == 'tags':
                result = self.viewmodel.edit_epic(epic_id, tags=value)
            elif field == 'status':
                if value == 'approved':
                    result = self.viewmodel.approve_epic(epic_id)
                elif value == 'rejected':
                    result = self.viewmodel.reject_epic(epic_id)
                else:
                    # Status personalizado
                    result = self.viewmodel.edit_epic(epic_id, status=value)
            
            if result.success:
                success_count += 1
            else:
                first_error = result.get_first_error()
                last_error = str(first_error) if first_error else f"Failed to update {field}"
        
        if success_count > 0:
            self._save_to_session_state()
            return EpicReviewResult(success=True, data=f"Updated {success_count} fields")
        else:
            return EpicReviewResult(success=False, error=last_error)
    
    def approve_epic(self, epic_id: int) -> EpicReviewResult:
        """Aprova épico"""
        result = self.viewmodel.approve_epic(epic_id)
        if result.success:
            self._save_to_session_state()
            return EpicReviewResult(success=True, data=result.data)
        else:
            first_error = result.get_first_error()
            error_msg = str(first_error) if first_error else "Approval failed"
            return EpicReviewResult(success=False, error=error_msg)
    
    def reject_epic(self, epic_id: int) -> EpicReviewResult:
        """Rejeita épico"""
        result = self.viewmodel.reject_epic(epic_id)
        if result.success:
            self._save_to_session_state()
            return EpicReviewResult(success=True, data=result.data)
        else:
            first_error = result.get_first_error()
            error_msg = str(first_error) if first_error else "Rejection failed"
            return EpicReviewResult(success=False, error=error_msg)
    
    def has_unsaved_changes(self) -> bool:
        """Verifica se há mudanças não salvas"""
        return self.viewmodel.has_unsaved_changes()
    
    def get_dirty_count(self) -> int:
        """Retorna número de mudanças pendentes"""
        return self.viewmodel.get_dirty_count()
    
    def get_changes_for_persistence(self) -> List[Dict[str, Any]]:
        """Retorna mudanças em formato para persistência"""
        # Obter épicos alterados
        changed_epics = [epic for epic in self.viewmodel.get_ordered_epics() if epic.is_dirty]
        
        changes = []
        for epic in changed_epics:
            # Usar adapter para gerar patch
            patch = self.patch_adapter.generate_patch(epic)
            changes.append(patch)
        
        return changes
    
    def get_ordered_epics(self) -> List[Any]:
        """Retorna épicos em ordem atual"""
        return self.viewmodel.get_ordered_epics()
    
    def get_current_state(self) -> Dict[str, Any]:
        """Retorna estado atual completo"""
        return {
            'epics': self.get_ordered_epics(),
            'has_changes': self.has_unsaved_changes(),
            'dirty_count': self.get_dirty_count(),
            'user_modifications': self.has_user_modifications()
        }
    
    def has_user_modifications(self) -> bool:
        """Verifica se usuário fez modificações"""
        return self.viewmodel.has_user_modifications()
    
    def save_changes(self) -> EpicReviewResult:
        """Salva mudanças usando EpicService"""
        try:
            if not self.has_unsaved_changes():
                return EpicReviewResult(success=True, data="No changes to save")
            
            # Obter EpicService via container
            from streamlit_extension.services import get_epic_service
            epic_service = get_epic_service()
            
            # Obter mudanças para persistir
            changes = self.get_changes_for_persistence()
            if not changes:
                return EpicReviewResult(success=True, data="No changes to save")
            
            # Chamar service para salvar
            result = epic_service.update_epic_order(self.project_id, changes)
            
            if result.success:
                # Marcar como salvo
                self.viewmodel.mark_as_saved()
                self._save_to_session_state()
                return EpicReviewResult(success=True, data="Changes saved successfully")
            else:
                # Extrair erro do ServiceResult
                first_error = result.get_first_error()
                error_msg = str(first_error) if first_error else "Save failed"
                return EpicReviewResult(success=False, error=error_msg)
                
        except Exception as e:
            return EpicReviewResult(success=False, error=f"Database connection failed: {str(e)}")

    def reorder_epics_from_layout(self, updated_layout: List[Dict[str, Any]]) -> EpicReviewResult:
        """Apply reorder based on streamlit-elements layout payload."""
        try:
            from streamlit_extension.components.epic_drag_drop import layout_to_order
            ordered_ids = layout_to_order(updated_layout)
            if not ordered_ids:
                return EpicReviewResult(success=False, error="Invalid layout payload")
            result = self.viewmodel.apply_order_by_ids(ordered_ids)
            if result.success:
                self._save_to_session_state()
                return EpicReviewResult(success=True)
            return EpicReviewResult(success=False, error=result.error or "Reorder failed")
        except Exception as e:
            return EpicReviewResult(success=False, error=str(e))
    
    def cancel_changes(self) -> EpicReviewResult:
        """Cancela mudanças (preserva em session state mas não persiste)"""
        # Cancel apenas retorna sucesso - mudanças ficam em session
        # mas não são persistidas no banco
        return EpicReviewResult(success=True, data="Changes cancelled (preserved in session)")
    
    def undo(self) -> EpicReviewResult:
        """Desfaz última ação"""
        result = self.viewmodel.undo()
        if result.success:
            self._save_to_session_state()
            return EpicReviewResult(success=True, data=result.data)
        else:
            first_error = result.get_first_error()
            error_msg = str(first_error) if first_error else "Undo failed"
            return EpicReviewResult(success=False, error=error_msg)


# Funções de navegação e visibility gating

def should_show_epic_review_step(session_state) -> bool:
    """Determina se step de epic review deve ser mostrado"""
    # Verificar se há capítulos
    if not hasattr(session_state, 'capitulos') or not session_state.capitulos.get('lista'):
        return False
    
    # Se lista está vazia, não mostrar
    if len(session_state.capitulos['lista']) == 0:
        return False
    
    # Se capítulos já foram finalizados, não mostrar
    if session_state.capitulos.get('finalized', False):
        return False
    
    return True


def render_epic_review_step(session_state, project_id: Optional[int] = None):
    """Renderiza step completo de epic review com UI enterprise"""
    if not should_show_epic_review_step(session_state):
        st.warning("📋 Epic Review não disponível. Crie capítulos primeiro.")
        return
    
    try:
        # Importar UI components
        from streamlit_extension.components.epic_review_ui import render_epic_review_ui
        
        # Renderizar interface completa
        ui_result = render_epic_review_ui(session_state, project_id)
        
        if not ui_result['success']:
            st.error(f"❌ Erro ao carregar Epic Review: {ui_result.get('error', 'Unknown error')}")
            return
        
        # Mostrar estatísticas de resultado
        results = ui_result['results']
        if results.get('actions_performed'):
            with st.sidebar:
                st.markdown("#### 📊 Session Actions")
                for action in results['actions_performed'][-5:]:  # Últimas 5 ações
                    if action.get('action'):
                        st.markdown(f"• {action['action']}")
        
        return ui_result
        
    except Exception as e:
        st.error(f"❌ Falha crítica no Epic Review: {str(e)}")
        # Fallback para interface básica
        st.markdown("### 🔄 Epic Review - Basic Mode")
        st.warning("Interface avançada indisponível. Usando modo básico.")
        
        # Interface básica de fallback
        _render_basic_epic_review(session_state)
        
        return {'success': False, 'error': str(e), 'fallback_used': True}


def _render_basic_epic_review(session_state):
    """Renderiza interface básica com explainers para epic review - História 4.2"""
    try:
        review_page = EpicReviewPage(session_state)
        epics = review_page.get_ordered_epics()
        
        st.markdown(f"**Total de Épicos:** {len(epics)}")
        st.markdown(f"**Mudanças Pendentes:** {review_page.get_dirty_count()}")
        
        # Obter PriorityScorer para explainers
        project_id = getattr(session_state, 'current_project_id', 1)
        scorer = _get_priority_scorer_for_explainers(project_id)
        
        # Lista de épicos com explainers
        for i, epic in enumerate(epics):
            _render_epic_card_with_explainer(epic, i, session_state, scorer)
        
        # Ações básicas
        if review_page.has_unsaved_changes():
            if st.button("💾 Salvar Mudanças", type="primary", key="epic_review_save_changes"):
                result = review_page.save_changes()
                if result.success:
                    st.success("✅ Mudanças salvas!")
                else:
                    st.error(f"❌ Erro: {result.error}")
    
    except Exception as e:
        st.error(f"❌ Erro na interface básica: {str(e)}")


def _get_priority_scorer_for_explainers(project_id: int):
    """Obtém PriorityScorer para explainers via DI"""
    try:
        from streamlit_extension.services.priority_scorer import PriorityScorer
        from streamlit_extension.services.service_container import get_priority_settings_repository
        settings_repo = get_priority_settings_repository()
        return PriorityScorer(project_id=project_id, settings_repo=settings_repo, total_scale=12.0)
    except Exception:
        return None  # Fallback gracioso


def _render_epic_card_with_explainer(epic, position: int, session_state, scorer):
    """Renderiza card de épico com botão explainer - História 4.2"""
    try:
        # Container principal do épico
        with st.container():
            # Layout com colunas: título + status + botão explainer
            col1, col2, col3 = st.columns([3, 1, 0.3])
            
            with col1:
                st.markdown(f"### #{position+1} - {epic.title}")
                if hasattr(epic, 'epic_key'):
                    st.caption(f"**Key:** {epic.epic_key}")
            
            with col2:
                # Status e confiança resumidos
                if hasattr(epic, 'confidence'):
                    confidence_data = _format_confidence_quick(epic.confidence)
                    if confidence_data:
                        st.markdown(f"**Confiança:** {confidence_data['label']} ({confidence_data['value']:.2f})")
                
                st.markdown(f"**Status:** {epic.status}")
                if epic.is_dirty:
                    st.warning("⚠️ Não salvo")
            
            with col3:
                # Botão explainer
                explainer_key = f"explainer_{epic.id}_{position}"
                if st.button("ℹ️", key=explainer_key, help="Explicar prioridade e rationale"):
                    session_state_key = f"show_explainer_{epic.id}"
                    current_state = getattr(session_state, session_state_key, False)
                    setattr(session_state, session_state_key, not current_state)
            
            # Conteúdo básico do épico
            if hasattr(epic, 'description') and epic.description:
                st.markdown(f"**Descrição:** {epic.description}")
            
            # Explainer expandido quando ativado
            explainer_state_key = f"show_explainer_{epic.id}"
            if getattr(session_state, explainer_state_key, False):
                _render_epic_explainer_expanded(epic, scorer)
            
            st.divider()  # Separador visual
                
    except Exception as e:
        st.error(f"❌ Erro ao renderizar épico {position+1}: {str(e)}")


def _render_epic_explainer_expanded(epic, scorer):
    """Renderiza explainer expandido com rationale + score breakdown + confidence"""
    try:
        from streamlit_extension.components.epic_explainers import EpicExplainerService
        from streamlit_extension.core.dto.epic_suggestion_dto import EpicSuggestionDTO
        
        explainer = EpicExplainerService(cache_enabled=True)
        
        # Converter epic para EpicSuggestionDTO
        epic_dto = _convert_epic_to_dto(epic)
        
        if epic_dto is None:
            st.warning("⚠️ Não foi possível converter épico para análise")
            return
        
        with st.expander("🔍 **Análise Detalhada**", expanded=True):
            # Tabs para organizar informações
            tab1, tab2, tab3 = st.tabs(["📝 Rationale", "⚖️ Score", "🤖 Confiança"])
            
            with tab1:
                st.markdown("**Justificativa do Épico:**")
                rationale = explainer.format_rationale(epic_dto.rationale)
                st.write(rationale)
            
            with tab2:
                st.markdown("**Breakdown do Score de Prioridade:**")
                if scorer:
                    score_breakdown = explainer.compute_score_breakdown(epic_dto, scorer)
                    # Mostrar por peso e por contribuição quando disponível
                    if 'contributions' in score_breakdown:
                        tab_w, tab_c = st.tabs(["⚖️ Por Peso", "🎯 Por Contribuição"])
                        with tab_w:
                            st.info("ℹ️ **Por Peso:** Importância dos critérios no algoritmo (configuração de pesos).")
                            _render_score_breakdown_simple({
                                'percentages': score_breakdown.get('percentages', {}),
                                'total_score': score_breakdown.get('total_score')
                            })
                        with tab_c:
                            st.info("ℹ️ **Por Contribuição:** Impacto real de cada critério no score final deste épico.")
                            _render_score_breakdown_simple({
                                'percentages': score_breakdown.get('contributions', {}),
                                'total_score': score_breakdown.get('total_score')
                            })
                    else:
                        _render_score_breakdown_simple(score_breakdown)
                else:
                    st.warning("⚠️ PriorityScorer não disponível")
            
            with tab3:
                st.markdown("**Confiança da IA:**")
                confidence_data = explainer.format_confidence(epic_dto.confidence)
                _render_confidence_indicator_simple(confidence_data)
    
    except Exception as e:
        st.error(f"❌ Erro ao renderizar explainer: {str(e)}")


def _convert_epic_to_dto(epic) -> Optional[EpicSuggestionDTO]:
    """
    Converte épico para EpicSuggestionDTO para análise.
    
    Mapeia campos reais do banco quando disponíveis:
    - justification → rationale (se existir)
    - ai_confidence → confidence (se existir)
    - Outros campos específicos do banco
    """
    try:
        from streamlit_extension.core.dto.epic_suggestion_dto import EpicSuggestionDTO
        
        # Mapear rationale: preferir justification do banco, senão usar description
        rationale = getattr(epic, 'justification', None) or getattr(epic, 'description', 'Sem descrição disponível')
        
        # Mapear confidence: preferir ai_confidence do banco, senão usar confidence ou default
        confidence = getattr(epic, 'ai_confidence', None)
        if confidence is None:
            confidence = getattr(epic, 'confidence', 0.8)
        
        # Mapear tags: tentar múltiplas fontes
        tags = getattr(epic, 'tags', None)
        if tags is None:
            tags = getattr(epic, 'labels', [])
        if isinstance(tags, str):
            # Se tags vieram como string JSON, tentar decodificar
            try:
                import json
                tags = json.loads(tags)
            except:
                tags = []
        
        # Mapear source: verificar se foi gerado por IA
        source = "ai" if getattr(epic, 'ai_generated', False) else "heuristic"
        
        # Mapear campos do épico para DTO
        return EpicSuggestionDTO(
            title=getattr(epic, 'title', getattr(epic, 'name', 'Épico sem título')),
            rationale=rationale,
            tags=tags,
            confidence=float(confidence),
            source=source,
            id=str(getattr(epic, 'id', 'unknown')),
            business_priority=getattr(epic, 'priority', getattr(epic, 'business_priority', 3)),
            complexity_score=float(getattr(epic, 'complexity_score', 3.0)),
            effort_estimate=int(getattr(epic, 'effort_estimate', 7)),
            alignment_score=int(getattr(epic, 'alignment_score', 3))
        )
    except Exception as e:
        # Log para debug em desenvolvimento
        import logging
        logging.debug(f"Erro ao converter épico para DTO: {e}")
        return None


def _format_confidence_quick(confidence: float) -> Optional[Dict[str, Any]]:
    """Formata confiança de forma rápida para exibição resumida"""
    try:
        from streamlit_extension.components.epic_explainers import EpicExplainerService
        explainer = EpicExplainerService()
        return explainer.format_confidence(confidence)
    except Exception:
        return None


def _render_score_breakdown_simple(breakdown: Dict[str, Any]):
    """Renderiza breakdown de score de forma simplificada"""
    try:
        if 'error' in breakdown:
            st.warning(f"⚠️ {breakdown['error']}")
            if not breakdown.get('fallback', False):
                return
        
        percentages = breakdown.get('percentages', {})
        
        # Layout em colunas para componentes
        col1, col2 = st.columns(2)
        
        with col1:
            if 'valor' in percentages:
                st.metric("💰 Valor Negócio", f"{percentages['valor']:.1f}%")
            if 'esforco' in percentages:
                st.metric("⚡ Eficiência", f"{percentages['esforco']:.1f}%")
        
        with col2:
            if 'risco' in percentages:
                st.metric("⚠️ Risco", f"{percentages['risco']:.1f}%")
            if 'alinhamento' in percentages:
                st.metric("🎯 Alinhamento", f"{percentages['alinhamento']:.1f}%")
        
        # Confidence se presente
        if 'confidence' in percentages and percentages['confidence'] > 0:
            st.metric("🤖 Confiança IA", f"{percentages['confidence']:.1f}%")
        
        # Score total (pequeno)
        if breakdown.get('total_score'):
            st.caption(f"Score Total: {breakdown['total_score']:.2f}")
            
    except Exception as e:
        st.error(f"❌ Erro no breakdown: {str(e)}")


def _render_confidence_indicator_simple(confidence_data: Dict[str, Any]):
    """Renderiza indicador de confiança simplificado"""
    try:
        label = confidence_data.get('label', 'Desconhecida')
        value = confidence_data.get('value', 0.0)
        range_text = confidence_data.get('range', '')
        color = confidence_data.get('color', '#6c757d')
        
        # Layout com métrica
        st.metric(
            label="Nível de Confiança",
            value=f"{label} ({value:.2f})",
            delta=f"Range: {range_text}"
        )
        
        # Progress bar visual
        st.progress(value, text=f"Confiança: {value:.0%}")
        
        # Interpretação
        if value >= 0.8:
            st.success("✅ Alta confiança - Épico bem definido")
        elif value >= 0.5:
            st.info("ℹ️ Confiança média - Pode precisar de refinamento")
        else:
            st.warning("⚠️ Baixa confiança - Recomenda revisão manual")
            
    except Exception as e:
        st.error(f"❌ Erro no indicador de confiança: {str(e)}")


def is_review_complete(session_state) -> bool:
    """Verifica se review foi completada"""
    if not should_show_epic_review_step(session_state):
        return False
    
    # Verificar se há estado de review e se não há mudanças pendentes
    if hasattr(session_state, 'epic_review_state'):
        review_page = EpicReviewPage(session_state)
        return not review_page.has_unsaved_changes()
    
    return False
