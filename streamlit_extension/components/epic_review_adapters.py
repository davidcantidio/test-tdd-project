"""
🔄 Epic Review Adapters - História 4.1 FASE 2.3

Adaptadores robustos para conversão entre camadas:
- DTO ↔ ViewModel com mapeamento completo de campos
- ViewModel → Patch mínimo (apenas campos alterados)
- Widget keys únicos com padrão _wiz_key("cap_review", epic.id, field)
- Drag & Drop state management determinístico
- Proteções contra injection e out-of-range

Implementação TDD seguindo metodologia Green-phase.
"""

import re
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
import hashlib
import time


@dataclass
class ConversionResult:
    """Result wrapper para conversões de adaptadores"""
    success: bool
    data: Any = None
    error: str = ""
    warnings: List[str] = field(default_factory=list)


@dataclass
class DragDropResult:
    """Result wrapper simples para drag & drop operations"""
    success: bool
    error: str = ""


class EpicToViewModelAdapter:
    """
    Adaptador para conversão DTO → ViewModel com mapeamento completo.
    
    Converte objetos Epic DTO para ViewModelEpic com:
    - Mapeamento completo de campos (name → title)
    - Valores default para campos None
    - Campos computados opcionais
    - Conversões em lote para performance
    """
    
    def convert(self, epic_dto) -> Any:
        """Converte um Epic DTO para ViewModel Epic"""
        # Handle both dict and object inputs
        def get_field(obj, field_name, default=None):
            if hasattr(obj, field_name):
                return getattr(obj, field_name, default)
            elif isinstance(obj, dict):
                return obj.get(field_name, default)
            else:
                return default
        
        # Extract fields with defaults for None values
        epic_id = get_field(epic_dto, 'id')
        epic_key = get_field(epic_dto, 'epic_key', '')
        name = get_field(epic_dto, 'name', '')
        description = get_field(epic_dto, 'description', '')
        tags = get_field(epic_dto, 'tags', [])
        status = get_field(epic_dto, 'status', 'pending')
        sort_order = get_field(epic_dto, 'sort_order', 0)
        
        # Handle None values with appropriate defaults
        if description is None:
            description = ""
        if tags is None:
            tags = []
        if status is None:
            status = "pending"
            
        # Create ViewModel epic - assuming ViewModelEpic class from epic_review.py
        from streamlit_extension.components.epic_review import ViewModelEpic
        
        vm_epic = ViewModelEpic(
            id=epic_id,
            epic_key=epic_key,
            title=name,  # name → title mapping
            description=description,
            tags=tags.copy() if tags else [],
            status=status,
            sort_order=sort_order,
            is_dirty=False,  # New epic is not dirty
            original_values={}  # No original values yet
        )
        
        return vm_epic
    
    def get_computed_fields(self, vm_epic) -> Dict[str, Any]:
        """Retorna campos computados para o ViewModel Epic"""
        # Get priority and complexity from original DTO if available
        priority = getattr(vm_epic, 'priority', 3)
        complexity_score = getattr(vm_epic, 'complexity_score', 3.0)
        effort_estimate = getattr(vm_epic, 'effort_estimate', 5)
        
        return {
            'display_priority': self._format_priority_display(priority),
            'complexity_display': self._format_complexity_display(complexity_score),
            'effort_display': self._format_effort_display(effort_estimate)
        }
    
    def _format_priority_display(self, priority: int) -> str:
        """Formata prioridade para display"""
        priority_map = {1: "🔴 Critical", 2: "🟠 High", 3: "🟡 Medium", 4: "🟢 Low", 5: "⚪ Minimal"}
        return priority_map.get(priority, "🟡 Medium")
    
    def _format_complexity_display(self, complexity: float) -> str:
        """Formata complexidade para display"""
        if complexity >= 4.5:
            return f"🔥 Very High ({complexity:.1f})"
        elif complexity >= 3.5:
            return f"🔶 High ({complexity:.1f})"
        elif complexity >= 2.5:
            return f"🟡 Medium ({complexity:.1f})"
        elif complexity >= 1.5:
            return f"🟢 Low ({complexity:.1f})"
        else:
            return f"⚪ Very Low ({complexity:.1f})"
    
    def _format_effort_display(self, effort: int) -> str:
        """Formata estimativa de esforço para display"""
        if effort >= 20:
            return f"🏔️ Epic ({effort} days)"
        elif effort >= 10:
            return f"⛰️ Large ({effort} days)"
        elif effort >= 5:
            return f"🏕️ Medium ({effort} days)"
        else:
            return f"🚶 Small ({effort} days)"
    
    def convert_batch(self, epic_dtos: List[Any]) -> List[Any]:
        """Converte lista de DTOs em lote para performance"""
        vm_epics = []
        for dto in epic_dtos:
            try:
                vm_epic = self.convert(dto)
                vm_epics.append(vm_epic)
            except Exception:
                # Skip invalid epics in batch conversion
                continue
        return vm_epics
    
    def convert_safe(self, epic_dto) -> ConversionResult:
        """Conversão com tratamento de erro gracioso"""
        try:
            # Validate required fields
            epic_id = getattr(epic_dto, 'id', None) if hasattr(epic_dto, 'id') else epic_dto.get('id', None)
            epic_key = getattr(epic_dto, 'epic_key', None) if hasattr(epic_dto, 'epic_key') else epic_dto.get('epic_key', None)
            name = getattr(epic_dto, 'name', None) if hasattr(epic_dto, 'name') else epic_dto.get('name', None)
            
            if epic_id is None or not epic_key or not name:
                return ConversionResult(
                    success=False,
                    error="Invalid epic data: missing required fields (id, epic_key, name)"
                )
            
            vm_epic = self.convert(epic_dto)
            return ConversionResult(success=True, data=vm_epic)
            
        except Exception as e:
            return ConversionResult(
                success=False,
                error=f"Invalid epic data: {str(e)}"
            )
    
    def convert_batch_safe(self, epic_dtos: List[Any]) -> ConversionResult:
        """Conversão em lote com tratamento de épicos inválidos"""
        valid_epics = []
        invalid_count = 0
        
        for dto in epic_dtos:
            result = self.convert_safe(dto)
            if result.success:
                valid_epics.append(result.data)
            else:
                invalid_count += 1
        
        warnings = []
        if invalid_count > 0:
            warnings.append(f"Skipped {invalid_count} invalid epic")
        
        return ConversionResult(
            success=True,
            data=valid_epics,
            warnings=warnings
        )


class ViewModelToPatchAdapter:
    """
    Adaptador para conversão ViewModel → Patch mínimo.
    
    Gera patch contendo apenas campos que foram modificados,
    comparando com original_values para otimizar persistência.
    """
    
    def generate_patch(self, vm_epic) -> Dict[str, Any]:
        """Gera patch com apenas campos alterados"""
        patch = {}
        
        # epic_id sempre presente para identificação
        patch['epic_id'] = vm_epic.id
        
        # Comparar com valores originais se disponível
        original = vm_epic.original_values or {}
        
        # Verificar cada campo modificável
        current_values = {
            'title': vm_epic.title,
            'description': vm_epic.description,
            'tags': vm_epic.tags,
            'status': vm_epic.status,
            'sort_order': vm_epic.sort_order
        }
        
        for field, current_value in current_values.items():
            # Se não há valor original, assumir que mudou
            if field not in original:
                patch[field] = current_value
            # Se valor mudou do original
            elif original[field] != current_value:
                patch[field] = current_value
        
        # Não incluir campos que nunca mudam
        # epic_key, created_at, etc. não devem estar no patch
        
        return patch


class WidgetKeyBuilder:
    """
    Builder para chaves de widget únicos no Streamlit.
    
    Gera keys usando padrão: _wiz_key("cap_review", epic.id, field)
    com proteção contra injection e suporte a sessões.
    """
    
    def __init__(self, session_id: Optional[str] = None):
        """Inicializa builder com session_id opcional para unicidade"""
        self.session_id = session_id or "default"
        self.base_prefix = "cap_review"
    
    def build_key(self, epic_id: int, field: str) -> str:
        """Constrói chave única para widget"""
        # Sanitizar field para proteção contra injection
        safe_field = self.sanitize_field(field)
        
        # Padrão: _wiz_key("cap_review", epic.id, field)
        components = [self.base_prefix, str(epic_id), safe_field]
        
        # Incluir session_id se não for default
        if self.session_id != "default":
            components.append(str(self.session_id))
        
        # Criar chave determinística
        key_base = "_".join(components)
        
        # Usar hash para garantir caracteres seguros
        key_hash = hashlib.md5(key_base.encode()).hexdigest()[:8]
        
        return f"_wiz_key_{key_hash}_{self.base_prefix}_{epic_id}_{safe_field}"
    
    def sanitize_field(self, field: str) -> str:
        """Sanitiza nome do campo contra injection"""
        if not field:
            return "unknown"
        
        # Remover caracteres perigosos
        dangerous_chars = [';', '--', 'DROP', 'TABLE', 'DELETE', 'INSERT', 'UPDATE', 'SELECT']
        
        sanitized = field
        for danger in dangerous_chars:
            sanitized = sanitized.replace(danger, '')
        
        # Manter apenas caracteres alfanuméricos e underscore
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '', sanitized)
        
        # Se ficou vazio, usar fallback
        if not sanitized:
            sanitized = "field"
        
        # Limitar tamanho
        return sanitized[:50]


class DragDropStateManager:
    """
    Gerenciador de estado para drag & drop determinístico.
    
    Controla transições de estado, validações de movimento
    e reordenação com tie-breakers.
    """
    
    def __init__(self):
        """Inicializa estado idle"""
        self.current_state = "idle"
        self.dragged_epic_id = None
        self.drag_from_position = None
        self.current_hover_position = None
        self.last_drop_result = None
    
    def get_current_state(self) -> str:
        """Retorna estado atual do drag"""
        return self.current_state
    
    def get_dragged_epic_id(self) -> Optional[int]:
        """Retorna ID do épico sendo arrastado"""
        return self.dragged_epic_id
    
    def get_drag_from_position(self) -> Optional[int]:
        """Retorna posição inicial do drag"""
        return self.drag_from_position
    
    def get_hover_position(self) -> Optional[int]:
        """Retorna posição do hover atual"""
        return self.current_hover_position
    
    def get_last_drop_result(self) -> Optional[Dict[str, Any]]:
        """Retorna resultado do último drop"""
        return self.last_drop_result
    
    def start_drag(self, epic_id: int, from_position: int) -> DragDropResult:
        """Inicia operação de drag"""
        if self.current_state != "idle":
            return DragDropResult(success=False, error=f"Cannot start drag in state: {self.current_state}")
        
        self.current_state = "dragging"
        self.dragged_epic_id = epic_id
        self.drag_from_position = from_position
        self.current_hover_position = None
        
        return DragDropResult(success=True)
    
    def hover_position(self, to_position: int) -> DragDropResult:
        """Atualiza posição do hover"""
        if self.current_state != "dragging":
            return DragDropResult(success=False, error=f"Cannot hover in state: {self.current_state}")
        
        self.current_hover_position = to_position
        return DragDropResult(success=True)
    
    def drop(self, to_position: int) -> DragDropResult:
        """Finaliza operação de drag com drop"""
        if self.current_state != "dragging":
            return DragDropResult(success=False, error=f"Cannot drop in state: {self.current_state}")
        
        # Registrar resultado do drop
        self.last_drop_result = {
            "from": self.drag_from_position,
            "to": to_position,
            "epic_id": self.dragged_epic_id
        }
        
        # Resetar estado para idle
        self._reset_to_idle()
        
        return DragDropResult(success=True)
    
    def cancel_drag(self) -> DragDropResult:
        """Cancela operação de drag"""
        if self.current_state != "dragging":
            return DragDropResult(success=False, error=f"Cannot cancel in state: {self.current_state}")
        
        self._reset_to_idle()
        return DragDropResult(success=True)
    
    def _reset_to_idle(self):
        """Reseta estado para idle"""
        self.current_state = "idle"
        self.dragged_epic_id = None
        self.drag_from_position = None
        self.current_hover_position = None
    
    def reorder_deterministic(self, epics: List[Any], move_epic_id: int, to_position: int) -> List[Any]:
        """Reordena lista de épicos determinísticamente"""
        # Encontrar épico a ser movido
        epic_to_move = None
        remaining_epics = []
        
        for epic in epics:
            if epic.id == move_epic_id:
                epic_to_move = epic
            else:
                remaining_epics.append(epic)
        
        if epic_to_move is None:
            return epics  # Epic não encontrado, retorna original
        
        # Ordenar épicos restantes determinísticamente (por ID como tie-breaker)
        remaining_epics.sort(key=lambda e: e.id)
        
        # Inserir épico na posição desejada
        if to_position >= len(remaining_epics):
            remaining_epics.append(epic_to_move)
        else:
            remaining_epics.insert(to_position, epic_to_move)
        
        # Atualizar sort_order sequencialmente
        for i, epic in enumerate(remaining_epics):
            epic.sort_order = i
        
        return remaining_epics
    
    def validate_move(self, from_position: int, to_position: int, epic_count: int) -> DragDropResult:
        """Valida movimento contra out-of-range"""
        # Validar from_position
        if from_position < 0 or from_position >= epic_count:
            return DragDropResult(success=False, error="Invalid from position")
        
        # Validar to_position
        if to_position < 0 or to_position >= epic_count:
            return DragDropResult(success=False, error="Position out of range")
        
        # Movimento no-op (mesma posição)
        if from_position == to_position:
            return DragDropResult(success=False, error="No-op move (same position)")
        
        # Movimento válido
        return DragDropResult(success=True)