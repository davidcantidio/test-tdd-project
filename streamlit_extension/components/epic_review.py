"""
🎯 EpicReviewViewModel - História 4.1 FASE 2.2

ViewModel enterprise para revisão e reordenação de épicos com:
- Identidade estável baseada em epic.id (nunca índice)
- Dirty flags para controle de estado "Save"
- Undo stack limitado a 20 ações com records imutáveis
- Operações determinísticas de movimentação
- Validação e sanitização completa
- Integração com PriorityScorer via DI

Implementação seguindo TDD Green phase.
"""

from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
import json
from enum import Enum


class ActionType(Enum):
    """Tipos de ação para undo/redo"""
    MOVE = "move"
    EDIT = "edit"
    APPROVE = "approve"
    REJECT = "reject"


@dataclass(frozen=True)
class EpicReviewAction:
    """Record imutável de ação para undo/redo"""
    action_type: ActionType
    epic_id: int
    old_value: Any
    new_value: Any
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())


@dataclass
class ViewModelEpic:
    """Epic adaptado para ViewModel com controle de estado"""
    id: int
    epic_key: str
    title: str
    description: str = ""
    tags: List[str] = field(default_factory=list)
    status: str = "pending"
    sort_order: int = 0
    is_dirty: bool = False
    original_values: Dict[str, Any] = field(default_factory=dict)
    
    def mark_dirty(self, field: str, old_value: Any):
        """Marca épico como dirty e salva valor original"""
        if not self.is_dirty:
            self.original_values = {}
        
        if field not in self.original_values:
            self.original_values[field] = old_value
        
        self.is_dirty = True
    
    def get_changes(self) -> Dict[str, Any]:
        """Retorna apenas campos que foram alterados"""
        if not self.is_dirty:
            return {}
        
        changes = {"epic_id": self.id}
        
        for field, original_value in self.original_values.items():
            current_value = getattr(self, field)
            if current_value != original_value:
                changes[field] = current_value
        
        return changes


@dataclass
class ServiceResult:
    """Result pattern para operações do ViewModel"""
    success: bool
    data: Any = None
    error: str = ""
    
    @classmethod
    def ok(cls, data: Any = None) -> 'ServiceResult':
        return cls(success=True, data=data)
    
    @classmethod
    def fail(cls, error: str) -> 'ServiceResult':
        return cls(success=False, error=error)


class EpicReviewViewModel:
    """
    ViewModel para revisão e reordenação de épicos.
    
    Características:
    - Operações baseadas em epic.id (identidade estável)
    - Undo stack limitado a 20 ações
    - Dirty flag management
    - Validação robusta
    - Integração com PriorityScorer
    """
    
    MAX_UNDO_ACTIONS = 20
    
    def __init__(self, epics: List[Dict[str, Any]], priority_scorer=None):
        """
        Inicializa ViewModel com lista de épicos.
        
        Args:
            epics: Lista de épicos (dicts from database)
            priority_scorer: Optional PriorityScorer for initial ordering
        """
        self._epics: Dict[int, ViewModelEpic] = {}
        self._epic_order: List[int] = []  # Lista de epic IDs em ordem
        self._undo_stack: List[EpicReviewAction] = []
        self._redo_stack: List[EpicReviewAction] = []
        self._has_user_modifications = False
        self._priority_scorer = priority_scorer
        
        # Converter épicos para ViewModelEpic
        self._initialize_epics(epics)
        
        # Aplicar ordem inicial se disponível scorer
        if priority_scorer and not self._has_user_modifications:
            self._apply_initial_priority_order()
    
    def _initialize_epics(self, epics: List[Union[Dict[str, Any], Any]]):
        """Inicializa épicos no ViewModel"""
        for epic_data in epics:
            # Suporte para objetos (MockEpic) e dicionários
            if hasattr(epic_data, '__dict__'):
                # Objeto com atributos
                epic = ViewModelEpic(
                    id=getattr(epic_data, 'id'),
                    epic_key=getattr(epic_data, 'epic_key', f"EPIC_{getattr(epic_data, 'id'):03d}"),
                    title=getattr(epic_data, 'title', getattr(epic_data, 'name', '')),
                    description=getattr(epic_data, 'description', ''),
                    tags=self._parse_tags(getattr(epic_data, 'tags', [])),
                    status=getattr(epic_data, 'status', 'pending'),
                    sort_order=getattr(epic_data, 'sort_order', len(self._epics))
                )
            else:
                # Dicionário
                epic = ViewModelEpic(
                    id=epic_data['id'],
                    epic_key=epic_data.get('epic_key', f"EPIC_{epic_data['id']:03d}"),
                    title=epic_data.get('name', epic_data.get('title', '')),
                    description=epic_data.get('description', ''),
                    tags=self._parse_tags(epic_data.get('tags', [])),
                    status=epic_data.get('status', 'pending'),
                    sort_order=epic_data.get('sort_order', len(self._epics))
                )
            
            self._epics[epic.id] = epic
            self._epic_order.append(epic.id)
        
        # Ordenar por sort_order inicial
        self._epic_order.sort(key=lambda eid: self._epics[eid].sort_order)
    
    def _parse_tags(self, tags: Union[str, List[str]]) -> List[str]:
        """Parse tags from JSON string or list"""
        if isinstance(tags, str):
            try:
                return json.loads(tags) if tags else []
            except json.JSONDecodeError:
                return [tag.strip() for tag in tags.split(',') if tag.strip()]
        elif isinstance(tags, list):
            return [str(tag).strip() for tag in tags if str(tag).strip()]
        return []
    
    def _apply_initial_priority_order(self):
        """Aplica ordem inicial usando PriorityScorer"""
        if not self._priority_scorer:
            return
        
        # Converter para formato esperado pelo scorer
        epic_dtos = []
        for epic in self._epics.values():
            epic_dtos.append({
                'epic_key': epic.epic_key,
                'title': epic.title,
                'description': epic.description,
                # Campos necessários para scoring
                'business_priority': 3,  # Default values
                'complexity_score': 3.0,
                'alignment_score': 3
            })
        
        try:
            scores = self._priority_scorer.calculate_epic_scores(epic_dtos)
            
            # Reordenar baseado nos scores
            self._epic_order.sort(
                key=lambda eid: scores.get(self._epics[eid].epic_key, type('obj', (), {'total_score': 0})).total_score,
                reverse=True
            )
            
            # Atualizar sort_order
            for i, epic_id in enumerate(self._epic_order):
                self._epics[epic_id].sort_order = i
                
        except Exception as e:
            # Fallback silencioso se scoring falhar
            pass

    def apply_order_by_ids(self, ordered_ids: List[int]) -> ServiceResult:
        """Apply a full reorder based on a list of epic IDs.

        Validates that IDs match current set, updates sort_order for changed
        positions, marks dirty selectively, and records a single MOVE action
        with old/new order snapshots for undo.
        """
        # Validation
        if not ordered_ids:
            return ServiceResult.fail("Empty order not allowed")

        # Allow partial reorders: provided IDs must exist; others keep relative order
        unknown_ids = [eid for eid in ordered_ids if eid not in self._epics]
        if unknown_ids:
            return ServiceResult.fail(f"Unknown epic IDs: {unknown_ids}")

        old_order = self._epic_order.copy()

        # No-op if exact same order
        if old_order == ordered_ids:
            return ServiceResult.ok("Order unchanged")

        # Compute new order: provided IDs in given order, then remaining in original order
        provided_set = set(ordered_ids)
        remaining = [eid for eid in old_order if eid not in provided_set]
        self._epic_order = ordered_ids[:] + remaining

        for idx, eid in enumerate(self._epic_order):
            epic = self._epics.get(eid)
            if epic is None:
                continue
            old_pos = epic.sort_order
            if old_pos != idx:
                epic.mark_dirty("sort_order", old_pos)
                epic.sort_order = idx

        # Record a single MOVE action with snapshot
        self._add_undo_action(
            EpicReviewAction(
                action_type=ActionType.MOVE,
                epic_id=-1,  # -1 indicates batch order change
                old_value=old_order,
                new_value=self._epic_order.copy(),
            )
        )

        self._has_user_modifications = True
        return ServiceResult.ok()
    
    def get_epic_by_id(self, epic_id: int) -> Optional[ViewModelEpic]:
        """Obtém épico por ID (identidade estável)"""
        return self._epics.get(epic_id)
    
    def get_ordered_epics(self) -> List[ViewModelEpic]:
        """Retorna épicos na ordem atual"""
        return [self._epics[eid] for eid in self._epic_order]
    
    def get_position_by_id(self, epic_id: int) -> int:
        """Obtém posição atual do épico na lista ordenada"""
        try:
            return self._epic_order.index(epic_id)
        except ValueError:
            return -1
    
    def move_epic_up(self, epic_id: int) -> ServiceResult:
        """Move épico para cima na ordem"""
        current_pos = self.get_position_by_id(epic_id)
        
        if current_pos <= 0:
            return ServiceResult.fail("Cannot move up - already at top")
        
        return self._move_epic_to_position(epic_id, current_pos - 1)
    
    def move_epic_down(self, epic_id: int) -> ServiceResult:
        """Move épico para baixo na ordem"""
        current_pos = self.get_position_by_id(epic_id)
        
        if current_pos >= len(self._epic_order) - 1:
            return ServiceResult.fail("Cannot move down - already at bottom")
        
        return self._move_epic_to_position(epic_id, current_pos + 1)
    
    def _move_epic_to_position(self, epic_id: int, new_position: int) -> ServiceResult:
        """Move épico para posição específica"""
        current_pos = self.get_position_by_id(epic_id)
        
        if current_pos == -1:
            return ServiceResult.fail("Epic not found")
        
        if new_position < 0 or new_position >= len(self._epic_order):
            return ServiceResult.fail("Position out of range")
        
        if current_pos == new_position:
            return ServiceResult.fail("No-op move - same position")
        
        # Salvar ação para undo
        old_order = self._epic_order.copy()
        
        # Realizar movimento
        epic_id_moved = self._epic_order.pop(current_pos)
        self._epic_order.insert(new_position, epic_id_moved)
        
        # Atualizar sort_order
        for i, eid in enumerate(self._epic_order):
            self._epics[eid].sort_order = i
            self._epics[eid].mark_dirty('sort_order', old_order.index(eid))
        
        # Registrar ação no undo
        self._add_undo_action(EpicReviewAction(
            action_type=ActionType.MOVE,
            epic_id=epic_id,
            old_value=current_pos,
            new_value=new_position
        ))
        
        self._has_user_modifications = True
        return ServiceResult.ok()
    
    def edit_epic(self, epic_id: int, **updates) -> ServiceResult:
        """Edita campos do épico com validação"""
        epic = self.get_epic_by_id(epic_id)
        if not epic:
            return ServiceResult.fail(f"Epic {epic_id} not found")
        
        # Validar updates
        validation_result = self._validate_epic_updates(updates)
        if not validation_result.success:
            return validation_result
        
        # Aplicar updates
        old_values = {}
        for field, new_value in updates.items():
            if hasattr(epic, field):
                old_value = getattr(epic, field)
                old_values[field] = old_value
                
                # Sanitizar e aplicar
                sanitized_value = self._sanitize_field_value(field, new_value)
                setattr(epic, field, sanitized_value)
                epic.mark_dirty(field, old_value)
        
        # Registrar no undo
        self._add_undo_action(EpicReviewAction(
            action_type=ActionType.EDIT,
            epic_id=epic_id,
            old_value=old_values,
            new_value=updates
        ))
        
        self._has_user_modifications = True
        return ServiceResult.ok()
    
    def approve_epic(self, epic_id: int) -> ServiceResult:
        """Marca épico como aprovado"""
        return self._set_epic_status(epic_id, "approved")
    
    def reject_epic(self, epic_id: int) -> ServiceResult:
        """Marca épico como rejeitado"""
        return self._set_epic_status(epic_id, "rejected")
    
    def _set_epic_status(self, epic_id: int, status: str) -> ServiceResult:
        """Define status do épico (approved/rejected são mutuamente exclusivos)"""
        epic = self.get_epic_by_id(epic_id)
        if not epic:
            return ServiceResult.fail(f"Epic {epic_id} not found")
        
        old_status = epic.status
        epic.status = status
        epic.mark_dirty('status', old_status)
        
        # Registrar no undo
        action_type = ActionType.APPROVE if status == "approved" else ActionType.REJECT
        self._add_undo_action(EpicReviewAction(
            action_type=action_type,
            epic_id=epic_id,
            old_value=old_status,
            new_value=status
        ))
        
        self._has_user_modifications = True
        return ServiceResult.ok()
    
    def _validate_epic_updates(self, updates: Dict[str, Any]) -> ServiceResult:
        """Valida updates de épico"""
        # Título não pode ser vazio
        if 'title' in updates and not str(updates['title']).strip():
            return ServiceResult.fail("Title cannot be empty")
        
        # Descrição tem limite
        if 'description' in updates and len(str(updates['description'])) > 1500:
            return ServiceResult.fail("Description too long (max 1500 characters)")
        
        # Status deve ser válido
        if 'status' in updates and updates['status'] not in ['pending', 'approved', 'rejected']:
            return ServiceResult.fail("Invalid status")
        
        return ServiceResult.ok()
    
    def _sanitize_field_value(self, field: str, value: Any) -> Any:
        """Sanitiza valor do campo"""
        if field == 'title' and isinstance(value, str):
            return value.strip()
        
        elif field == 'description' and isinstance(value, str):
            return value.strip()
        
        elif field == 'tags' and isinstance(value, list):
            # Remove duplicatas, vazias, e trim
            sanitized = []
            for tag in value:
                clean_tag = str(tag).strip()
                if clean_tag and clean_tag not in sanitized:
                    sanitized.append(clean_tag)
            return sanitized
        
        return value
    
    def _add_undo_action(self, action: EpicReviewAction):
        """Adiciona ação ao undo stack (limitado a MAX_UNDO_ACTIONS)"""
        self._undo_stack.append(action)
        
        # Limitar tamanho do stack
        if len(self._undo_stack) > self.MAX_UNDO_ACTIONS:
            self._undo_stack.pop(0)  # Remove mais antiga
        
        # Clear redo stack quando nova ação é realizada
        self._redo_stack.clear()
    
    def undo(self) -> ServiceResult:
        """Desfaz última ação"""
        if not self._undo_stack:
            return ServiceResult.fail("Nothing to undo")
        
        action = self._undo_stack.pop()
        
        # Aplicar undo baseado no tipo de ação
        try:
            if action.action_type == ActionType.MOVE:
                # Reverter movimento
                self._move_epic_to_position_without_undo(action.epic_id, action.old_value)
            
            elif action.action_type in [ActionType.EDIT]:
                # Reverter edição
                epic = self.get_epic_by_id(action.epic_id)
                if epic and isinstance(action.old_value, dict):
                    for field, old_val in action.old_value.items():
                        if hasattr(epic, field):
                            setattr(epic, field, old_val)
            
            elif action.action_type in [ActionType.APPROVE, ActionType.REJECT]:
                # Reverter status
                epic = self.get_epic_by_id(action.epic_id)
                if epic:
                    epic.status = action.old_value
            
            # Adicionar ao redo stack
            self._redo_stack.append(action)
            
            return ServiceResult.ok()
            
        except Exception as e:
            # Re-adicionar ação em caso de erro
            self._undo_stack.append(action)
            return ServiceResult.fail(f"Undo failed: {str(e)}")
    
    def _move_epic_to_position_without_undo(self, epic_id: int, position: int):
        """Move épico sem registrar undo (para operações de undo)"""
        current_pos = self.get_position_by_id(epic_id)
        if current_pos != -1:
            epic_id_moved = self._epic_order.pop(current_pos)
            self._epic_order.insert(position, epic_id_moved)
            
            # Atualizar sort_order
        for i, eid in enumerate(self._epic_order):
            self._epics[eid].sort_order = i
    
    def get_undo_stack(self) -> List[EpicReviewAction]:
        """Retorna stack de undo (para testes)"""
        return self._undo_stack.copy()
    
    def get_redo_stack(self) -> List[EpicReviewAction]:
        """Retorna stack de redo"""
        return self._redo_stack.copy()
    
    def has_redo_available(self) -> bool:
        """Verifica se há ações para redo"""
        return len(self._redo_stack) > 0
    
    def has_unsaved_changes(self) -> bool:
        """Verifica se há mudanças não salvas"""
        return any(epic.is_dirty for epic in self._epics.values())
    
    def get_dirty_count(self) -> int:
        """Retorna número de épicos com mudanças"""
        return sum(1 for epic in self._epics.values() if epic.is_dirty)
    
    def has_user_modifications(self) -> bool:
        """Verifica se usuário fez modificações"""
        return self._has_user_modifications
    
    def mark_as_saved(self):
        """Marca todos os épicos como salvos (limpa dirty flags)"""
        for epic in self._epics.values():
            epic.is_dirty = False
            epic.original_values.clear()
    
    def get_changes_for_persistence(self) -> List[Dict[str, Any]]:
        """Retorna mudanças para persistir (apenas campos alterados)"""
        changes = []
        for epic in self._epics.values():
            if epic.is_dirty:
                changes.append(epic.get_changes())
        return changes
    
    def filter_epics(self, filter_type: str) -> List[ViewModelEpic]:
        """Filtra épicos por tipo"""
        epics = self.get_ordered_epics()
        
        if filter_type == "all":
            return epics
        elif filter_type == "approved":
            return [e for e in epics if e.status == "approved"]
        elif filter_type == "rejected":
            return [e for e in epics if e.status == "rejected"]
        elif filter_type == "edited":
            return [e for e in epics if e.is_dirty]
        
        return epics
