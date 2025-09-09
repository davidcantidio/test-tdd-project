"""
🎨 Epic Review UI Components - História 4.1 FASE 3

Componentes UI específicos para sistema de revisão e reordenação de épicos:
- Drag and Drop interface with visual feedback
- Epic cards with inline editing capabilities  
- Validation UI with error display
- Save/Cancel/Undo action buttons
- Responsive layout with accessibility features

Enterprise-grade UI implementation seguindo padrões Streamlit.
"""

from typing import List, Dict, Any, Optional, Tuple
import os
import time
import logging
import streamlit as st
from dataclasses import dataclass
from streamlit_extension.pages.projetos.steps.capitulos_step.epic_review import EpicReviewPage, EpicReviewResult


@dataclass
class UIState:
    """Estado da UI para controle de componentes"""
    editing_epic_id: Optional[int] = None
    drag_mode: bool = False
    show_validation_panel: bool = False
    selected_epic_ids: List[int] = None
    
    def __post_init__(self):
        if self.selected_epic_ids is None:
            self.selected_epic_ids = []


class EpicReviewUI:
    """
    Enterprise-grade UI components para Epic Review System.
    
    Fornece interface visual robusta com:
    - Drag and drop de épicos
    - Inline editing com validação
    - Visual feedback e error handling
    - Accessibility compliance (WCAG 2.1)
    """
    
    def __init__(self, review_page: EpicReviewPage):
        """Inicializa UI com página de review"""
        self.review_page = review_page
        self.ui_state = self._get_ui_state()
        
    def _get_ui_state(self) -> UIState:
        """Obtém ou inicializa estado da UI"""
        if not hasattr(st.session_state, 'epic_review_ui_state'):
            st.session_state.epic_review_ui_state = UIState()
        return st.session_state.epic_review_ui_state
    
    def _save_ui_state(self):
        """Salva estado da UI"""
        st.session_state.epic_review_ui_state = self.ui_state
    
    def render_full_interface(self) -> Dict[str, Any]:
        """
        Renderiza interface completa de Epic Review.
        
        Returns:
            Dict com resultados das ações realizadas
        """
        results = {
            'actions_performed': [],
            'validation_errors': [],
            'ui_state_changed': False
        }
        
        # Header com estatísticas
        self._render_header_stats()
        
        # Action toolbar
        toolbar_result = self._render_action_toolbar()
        if toolbar_result['action_taken']:
            results['actions_performed'].append(toolbar_result)
            results['ui_state_changed'] = True
        
        # Área principal com colunas
        col_main, col_sidebar = st.columns([2, 1])
        
        with col_main:
            # Epic cards com drag-drop
            cards_result = self._render_epic_cards()
            if cards_result['changes_made']:
                results['actions_performed'].extend(cards_result['actions'])
                results['ui_state_changed'] = True
        
        with col_sidebar:
            # Painel de validação e ações
            validation_result = self._render_validation_panel()
            results['validation_errors'].extend(validation_result['errors'])
            
            # Save/cancel buttons
            save_result = self._render_save_cancel_buttons()
            if save_result['action_taken']:
                results['actions_performed'].append(save_result)
        
        # Salvar estado da UI se houve mudanças
        if results['ui_state_changed']:
            self._save_ui_state()
        
        return results
    
    def _render_header_stats(self):
        """Renderiza cabeçalho com estatísticas do review"""
        st.markdown("### 🔄 Epic Review & Reordering")
        
        # Métricas em colunas
        epics = self.review_page.get_ordered_epics()
        total_epics = len(epics)
        dirty_count = self.review_page.get_dirty_count()
        has_changes = self.review_page.has_unsaved_changes()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Epics", total_epics, help="Número total de épicos no projeto")
        
        with col2:
            delta_color = "normal" if dirty_count == 0 else "inverse"
            st.metric("Pending Changes", dirty_count, delta_color=delta_color, 
                     help="Número de épicos com mudanças não salvas")
        
        with col3:
            status_text = "✅ Saved" if not has_changes else "⏳ Unsaved"
            status_color = "normal" if not has_changes else "inverse"  
            st.metric("Status", status_text, help="Status das mudanças")
        
        with col4:
            # Botão de toggle para validation panel
            if st.button("🔍 Validation", help="Toggle validation panel"):
                self.ui_state.show_validation_panel = not self.ui_state.show_validation_panel
    
    def _render_action_toolbar(self) -> Dict[str, Any]:
        """Renderiza toolbar com ações principais"""
        result = {'action_taken': False, 'action': None}
        
        # Ações globais
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if st.button("⬆️ Move Up", disabled=len(self.ui_state.selected_epic_ids) != 1,
                        help="Move selected epic up"):
                epic_id = self.ui_state.selected_epic_ids[0]
                move_result = self.review_page.move_epic_up(epic_id)
                result = {'action_taken': True, 'action': 'move_up', 'result': move_result}
        
        with col2:
            if st.button("⬇️ Move Down", disabled=len(self.ui_state.selected_epic_ids) != 1,
                        help="Move selected epic down"):
                epic_id = self.ui_state.selected_epic_ids[0]
                move_result = self.review_page.move_epic_down(epic_id)
                result = {'action_taken': True, 'action': 'move_down', 'result': move_result}
        
        with col3:
            if st.button("✅ Approve All", disabled=len(self.ui_state.selected_epic_ids) == 0,
                        help="Approve all selected epics"):
                results = []
                for epic_id in self.ui_state.selected_epic_ids:
                    approve_result = self.review_page.approve_epic(epic_id)
                    results.append(approve_result)
                result = {'action_taken': True, 'action': 'approve_all', 'results': results}
        
        with col4:
            if st.button("❌ Reject All", disabled=len(self.ui_state.selected_epic_ids) == 0,
                        help="Reject all selected epics"):
                results = []
                for epic_id in self.ui_state.selected_epic_ids:
                    reject_result = self.review_page.reject_epic(epic_id)
                    results.append(reject_result)
                result = {'action_taken': True, 'action': 'reject_all', 'results': results}
        
        with col5:
            if st.button("↶ Undo Last", disabled=not hasattr(self.review_page.viewmodel, '_undo_stack') or 
                        len(getattr(self.review_page.viewmodel, '_undo_stack', [])) == 0,
                        help="Undo last action"):
                undo_result = self.review_page.undo()
                result = {'action_taken': True, 'action': 'undo', 'result': undo_result}
        
        return result
    
    def _render_epic_cards(self) -> Dict[str, Any]:
        """Renderiza cards de épicos com drag-drop"""
        result = {
            'changes_made': False,
            'actions': []
        }
        
        epics = self.review_page.get_ordered_epics()
        
        if not epics:
            st.info("📝 Nenhum épico encontrado. Crie capítulos primeiro.")
            return result
        
        logger = logging.getLogger(__name__)
        drag_enabled = os.getenv("TDD_ENABLE_DRAGDROP", "true").lower() == "true"
        
        # Try real drag-drop first (guarded by feature flag)
        if drag_enabled:
            try:
                from streamlit_extension.components.epic_drag_drop import render_epic_drag_drop

                st.markdown("#### Epic Cards (Drag & Drop)")

                # Simple throttle to avoid state thrashing
                if not hasattr(self.ui_state, 'last_reorder_ts'):
                    self.ui_state.last_reorder_ts = 0.0

                def handle_reorder(new_layout):
                    now = time.monotonic()
                    # Apply at most ~3 times per second
                    if (now - float(self.ui_state.last_reorder_ts or 0.0)) < 0.3:
                        return
                    self.ui_state.last_reorder_ts = now
                    reorder_result = self.review_page.reorder_epics_from_layout(new_layout)
                    if reorder_result.success:
                        result['changes_made'] = True
                        result['actions'].append({'action': 'drag_reorder'})

                render_epic_drag_drop(epics, handle_reorder)

            except ImportError:
                st.info("💡 streamlit-elements não instalado. Usando fallback ↑/↓ para reordenação.")
                st.markdown("#### Epic Cards (Reorder with ↑/↓)")
                with st.container():
                    for i, epic in enumerate(epics):
                        card_result = self._render_epic_card(epic, i)
                        if card_result['modified']:
                            result['changes_made'] = True
                            result['actions'].append(card_result)
            except Exception as e:
                logger.error(f"Drag-drop failed: {e}")
                st.warning("⚠️ Drag-and-drop temporariamente indisponível. Usando fallback.")
                st.markdown("#### Epic Cards (Reorder with ↑/↓)")
                with st.container():
                    for i, epic in enumerate(epics):
                        card_result = self._render_epic_card(epic, i)
                        if card_result['modified']:
                            result['changes_made'] = True
                            result['actions'].append(card_result)
        else:
            st.markdown("#### Epic Cards (Reorder with ↑/↓)")
            with st.container():
                for i, epic in enumerate(epics):
                    card_result = self._render_epic_card(epic, i)
                    if card_result['modified']:
                        result['changes_made'] = True
                        result['actions'].append(card_result)
        
        return result
    
    def _render_epic_card(self, epic, position: int) -> Dict[str, Any]:
        """
        Renderiza card individual de épico com controles inline.
        
        Args:
            epic: ViewModelEpic object
            position: Posição na lista (0-based)
            
        Returns:
            Dict com resultados da renderização
        """
        result = {
            'modified': False,
            'epic_id': epic.id,
            'changes': {}
        }
        
        # Determinar estilo do card baseado no status
        status_style = self._get_card_style(epic)
        
        with st.expander(
            f"#{position+1:02d} - {epic.title} ({epic.epic_key})",
            expanded=self.ui_state.editing_epic_id == epic.id
        ):
            # Checkbox para seleção
            is_selected = st.checkbox(
                "Select",
                value=epic.id in self.ui_state.selected_epic_ids,
                key=f"select_epic_{epic.id}",
                help="Select epic for bulk actions"
            )
            
            # Atualizar seleção
            if is_selected and epic.id not in self.ui_state.selected_epic_ids:
                self.ui_state.selected_epic_ids.append(epic.id)
            elif not is_selected and epic.id in self.ui_state.selected_epic_ids:
                self.ui_state.selected_epic_ids.remove(epic.id)
            
            # Informações do épico
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Campos editáveis
                if self.ui_state.editing_epic_id == epic.id:
                    # Modo de edição inline
                    edit_result = self._render_inline_edit_form(epic)
                    if edit_result['saved']:
                        result['modified'] = True
                        result['changes'] = edit_result['changes']
                        self.ui_state.editing_epic_id = None
                else:
                    # Modo de visualização
                    st.markdown(f"**Description:** {epic.description or 'No description'}")
                    
                    if epic.tags:
                        tag_display = " ".join([f"`{tag}`" for tag in epic.tags])
                        st.markdown(f"**Tags:** {tag_display}")
                    
                    # Status com cor
                    status_color = self._get_status_color(epic.status)
                    st.markdown(f"**Status:** :{status_color}[{epic.status.upper()}]")
                    
                    # Dirty indicator
                    if epic.is_dirty:
                        st.warning("⚠️ Unsaved changes")
            
            with col2:
                # Botões de ação do card
                if st.button("✏️", key=f"edit_epic_{epic.id}", help="Edit epic"):
                    self.ui_state.editing_epic_id = epic.id
                
                if st.button("✅", key=f"approve_epic_{epic.id}", help="Approve epic"):
                    approve_result = self.review_page.approve_epic(epic.id)
                    if approve_result.success:
                        result['modified'] = True
                        result['changes']['status'] = 'approved'
                
                if st.button("❌", key=f"reject_epic_{epic.id}", help="Reject epic"):
                    reject_result = self.review_page.reject_epic(epic.id)
                    if reject_result.success:
                        result['modified'] = True
                        result['changes']['status'] = 'rejected'
        
        return result
    
    def _render_inline_edit_form(self, epic) -> Dict[str, Any]:
        """Renderiza formulário de edição inline"""
        result = {
            'saved': False,
            'cancelled': False,
            'changes': {}
        }
        
        with st.form(f"edit_epic_form_{epic.id}"):
            # Campos editáveis
            new_title = st.text_input("Title", value=epic.title, key=f"edit_title_{epic.id}")
            new_description = st.text_area("Description", value=epic.description or "", 
                                         key=f"edit_desc_{epic.id}", height=100)
            
            # Tags como string separada por vírgulas
            tags_str = ", ".join(epic.tags) if epic.tags else ""
            new_tags_str = st.text_input("Tags (comma separated)", value=tags_str, 
                                       key=f"edit_tags_{epic.id}")
            
            # Status dropdown
            status_options = ['pending', 'in_progress', 'approved', 'rejected', 'blocked']
            current_status_idx = status_options.index(epic.status) if epic.status in status_options else 0
            new_status = st.selectbox("Status", status_options, index=current_status_idx,
                                    key=f"edit_status_{epic.id}")
            
            # Botões do formulário
            col1, col2 = st.columns(2)
            
            with col1:
                if st.form_submit_button("💾 Save", type="primary"):
                    # Processar tags
                    new_tags = [tag.strip() for tag in new_tags_str.split(",") if tag.strip()]
                    
                    # Aplicar mudanças
                    edit_result = self.review_page.edit_epic(
                        epic.id,
                        title=new_title,
                        description=new_description,
                        tags=new_tags,
                        status=new_status
                    )
                    
                    if edit_result.success:
                        st.success("✅ Epic updated successfully!")
                        result['saved'] = True
                        result['changes'] = {
                            'title': new_title,
                            'description': new_description,
                            'tags': new_tags,
                            'status': new_status
                        }
                    else:
                        st.error(f"❌ Failed to update: {edit_result.error}")
            
            with col2:
                if st.form_submit_button("🚫 Cancel"):
                    result['cancelled'] = True
        
        return result
    
    def _render_validation_panel(self) -> Dict[str, Any]:
        """Renderiza painel de validação lateral"""
        result = {'errors': []}
        
        if not self.ui_state.show_validation_panel:
            return result
        
        st.markdown("#### 🔍 Validation Panel")
        
        # Validações
        epics = self.review_page.get_ordered_epics()
        validation_errors = []
        
        # Validação de títulos vazios
        empty_titles = [epic for epic in epics if not epic.title or not epic.title.strip()]
        if empty_titles:
            validation_errors.append({
                'severity': 'error',
                'message': f"Found {len(empty_titles)} epics with empty titles",
                'epic_ids': [epic.id for epic in empty_titles]
            })
        
        # Validação de descrições vazias
        empty_descriptions = [epic for epic in epics if not epic.description or not epic.description.strip()]
        if empty_descriptions:
            validation_errors.append({
                'severity': 'warning',
                'message': f"Found {len(empty_descriptions)} epics without descriptions",
                'epic_ids': [epic.id for epic in empty_descriptions]
            })
        
        # Validação de status pendente
        pending_epics = [epic for epic in epics if epic.status == 'pending']
        if pending_epics:
            validation_errors.append({
                'severity': 'info',
                'message': f"Found {len(pending_epics)} epics with pending status",
                'epic_ids': [epic.id for epic in pending_epics]
            })
        
        # Exibir resultados da validação
        if validation_errors:
            for error in validation_errors:
                if error['severity'] == 'error':
                    st.error(f"🚨 {error['message']}")
                elif error['severity'] == 'warning':
                    st.warning(f"⚠️ {error['message']}")
                else:
                    st.info(f"ℹ️ {error['message']}")
                
                # Botão para selecionar épicos com problema
                if st.button(f"Select {len(error['epic_ids'])} epics", 
                           key=f"select_validation_{hash(error['message'])}"):
                    self.ui_state.selected_epic_ids = error['epic_ids']
        else:
            st.success("✅ All validations passed!")
        
        result['errors'] = validation_errors
        return result
    
    def _render_save_cancel_buttons(self) -> Dict[str, Any]:
        """Renderiza botões de salvar/cancelar com progress tracking"""
        result = {'action_taken': False}
        
        st.markdown("#### 💾 Actions")
        
        has_changes = self.review_page.has_unsaved_changes()
        dirty_count = self.review_page.get_dirty_count()
        
        if has_changes:
            st.warning(f"⚠️ You have {dirty_count} unsaved changes")
            
            # Botão de salvar com progress tracking
            if st.button("💾 Save All Changes", type="primary", key="save_all_changes",
                        help="Save all pending changes to database with transaction safety"):
                
                # Placeholder para progress
                progress_placeholder = st.empty()
                
                try:
                    # Usar save flow enterprise
                    from streamlit_extension.components.epic_review_save_flow import execute_epic_save_with_progress
                    
                    with progress_placeholder:
                        st.info("🔄 Preparing save operation...")
                    
                    # Executar save com progress tracking
                    save_result = execute_epic_save_with_progress(
                        self.review_page, 
                        progress_placeholder
                    )
                    
                    progress_placeholder.empty()
                    
                    if save_result.success:
                        st.success(f"✅ Successfully saved {save_result.items_processed} changes!")
                        if save_result.processing_time_ms:
                            st.info(f"⚡ Completed in {save_result.processing_time_ms}ms")
                        st.balloons()  # Celebração visual
                        
                        result = {
                            'action_taken': True,
                            'action': 'save_all_enterprise',
                            'result': save_result
                        }
                    else:
                        st.error("❌ Save operation failed")
                        
                        # Mostrar detalhes do erro
                        with st.expander("🔍 Error Details", expanded=True):
                            for error in save_result.error_details:
                                st.error(f"• {error}")
                        
                        if save_result.rollback_performed:
                            st.warning("🔄 Automatic rollback was performed")
                        
                        result = {
                            'action_taken': True,
                            'action': 'save_failed',
                            'result': save_result
                        }
                
                except ImportError:
                    # Fallback para save simples
                    progress_placeholder.empty()
                    st.warning("⚠️ Using basic save (enterprise save flow not available)")
                    
                    with st.spinner("Saving changes..."):
                        save_result = self.review_page.save_changes()
                        
                        if save_result.success:
                            st.success("✅ Changes saved!")
                            result = {
                                'action_taken': True,
                                'action': 'save_basic',
                                'result': save_result
                            }
                        else:
                            st.error(f"❌ Failed to save: {save_result.error}")
                
                except Exception as e:
                    progress_placeholder.empty()
                    st.error(f"❌ Critical save error: {str(e)}")
            
            # Botão de cancelar
            if st.button("🚫 Cancel Changes", type="secondary", key="cancel_all_changes",
                        help="Cancel all pending changes (keeps in session)"):
                cancel_result = self.review_page.cancel_changes()
                st.info("📝 Changes cancelled but preserved in session")
                result = {
                    'action_taken': True,
                    'action': 'cancel_all',
                    'result': cancel_result
                }
        else:
            st.success("✅ All changes saved")
            st.info("No pending changes to save")
        
        return result
    
    # Helper methods
    
    def _get_card_style(self, epic) -> str:
        """Retorna estilo CSS para card baseado no status"""
        if epic.status == 'approved':
            return "success"
        elif epic.status == 'rejected':
            return "error"
        elif epic.status == 'blocked':
            return "warning"
        elif epic.is_dirty:
            return "info"
        else:
            return "default"
    
    def _get_status_color(self, status: str) -> str:
        """Retorna cor Streamlit para status"""
        color_map = {
            'approved': 'green',
            'rejected': 'red',
            'blocked': 'orange',
            'in_progress': 'blue',
            'pending': 'gray'
        }
        return color_map.get(status, 'gray')


# Função principal de renderização

def render_epic_review_ui(session_state, project_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Função principal para renderizar interface completa de Epic Review.
    
    Args:
        session_state: Streamlit session state
        project_id: ID do projeto (opcional)
        
    Returns:
        Dict com resultados das ações realizadas
    """
    try:
        # Criar página de review
        review_page = EpicReviewPage(session_state, project_id)
        
        # Criar e renderizar UI
        ui = EpicReviewUI(review_page)
        results = ui.render_full_interface()
        
        return {
            'success': True,
            'results': results,
            'page_state': review_page.get_current_state()
        }
        
    except Exception as e:
        st.error(f"❌ Failed to render Epic Review UI: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'results': {}
        }
