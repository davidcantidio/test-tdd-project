#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔄 STATE MANAGER - Projeto Wizard (versão otimizada)

Compatível com a API original:
- initialize_wizard_state, get_wizard_state, update_wizard_state
- mark_step_dirty, is_step_valid, validate_all_wizard_data
- save_wizard_draft, load_wizard_draft, auto_save_wizard
- add_validation_error, clear_validation_errors, get_validation_errors, has_validation_errors
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import IntEnum
from typing import Dict, List, Optional, Any, Callable
from typing import Set


import streamlit as st

# -----------------------------------------------------------------------------
# Logging (silencioso por padrão; configurável via root logger do app)  
# -----------------------------------------------------------------------------
logger = logging.getLogger(__name__)
if not logger.handlers:
    logger.addHandler(logging.NullHandler())

# -----------------------------------------------------------------------------
# Imports condicionais (graceful degradation)
# -----------------------------------------------------------------------------
try:
    from streamlit_extension.models.ai_generation import (
        AiGenerationORM, GenerationType, ContextType, ContentType
    )
    from streamlit_extension.database.connection import get_connection
    from streamlit_extension.utils.exception_handler import safe_streamlit_operation
    AI_MODELS_AVAILABLE = True
except ImportError:
    AI_MODELS_AVAILABLE = False
    logger.debug("AI generation models not available, using session-only persistence")

# -----------------------------------------------------------------------------
# Constantes & Tipos
# -----------------------------------------------------------------------------
AUTO_SAVE_MIN_INTERVAL = timedelta(seconds=5)  # evita salvamentos em excesso
SESSION_KEY_STATE = "projeto_wizard_state"
SESSION_KEY_STEP = "current_step"
SESSION_KEY_VIEW = "current_view"
SESSION_KEY_LAST_AUTOSAVE = "projeto_wizard_last_autosave"

class WizardView(str):
    WIZARD = "wizard"
    PROJECT_LIST = "project_list"

class Step(IntEnum):
    VISION = 1
    EPICS = 2
    STORIES = 3
    TASKS = 4
    PREVIEW = 5

JsonDict = Dict[str, Any]

# -----------------------------------------------------------------------------
# Estado
# -----------------------------------------------------------------------------
@dataclass
class WizardState:
    """
    Estado centralizado do wizard de projeto.
    """
    # Navegação
    current_step: int = Step.VISION
    current_view: str = WizardView.WIZARD

    # Identificação
    project_id: Optional[int] = None

    # Step 1: Vision
    vision_title: str = ""
    vision_description: str = ""
    vision_objectives: List[str] = field(default_factory=list)

    # Step 2: Epics
    epics: List[JsonDict] = field(default_factory=list)

    # Step 3: Stories
    stories: List[JsonDict] = field(default_factory=list)

    # Step 4: Tasks
    tasks: List[JsonDict] = field(default_factory=list)

    # Step 5: Preview/Planning
    velocity: int = 10
    sprint_length: int = 14
    planning_result: Optional[JsonDict] = None

    # Integração IA
    ai_suggestions: JsonDict = field(default_factory=dict)
    ai_session_id: Optional[str] = None

    # Controle de estado
    dirty_flags: Dict[str, bool] = field(default_factory=dict)
    last_saved: Optional[datetime] = None
    validation_errors: Dict[str, List[str]] = field(default_factory=dict)

    # Metadados
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

     # 🔎 Rastreamento claro (não substitui dirty_flags; é complementar)
    changed_fields: Set[str] = field(default_factory=set)
    needs_persistence: Set[str] = field(default_factory=set)

    # ------------------------- utilitários -------------------------
    def mark_dirty(self, *keys: str) -> None:
        """Marca campos como modificados com tracking completo."""
        for k in keys:
            self.dirty_flags[k] = True                  # legacy compatibility
            self.changed_fields.add(k)                  # analytics tracking
            self.needs_persistence.add(k)              # persistence queue
        self.updated_at = datetime.now()

    def clear_dirty(self) -> None:
        """Limpa flags após persistência bem-sucedida."""
        self.dirty_flags.clear()                        # legacy compatibility
        self.needs_persistence.clear()                  # persistence cleared
        # Note: changed_fields kept for analytics history

    def to_json(self) -> JsonDict:
        """
        Serializa somente dados necessários para persistência (JSON-safe).
        Datas em ISO 8601.
        """
        d = asdict(self)
        # Normaliza datetimes → isoformat
        for k in ("last_saved", "created_at", "updated_at"):
            v = d.get(k)
            d[k] = v.isoformat() if isinstance(v, datetime) else None
        # sets não são JSON‑safe: serializa como lista
        d["changed_fields"] = sorted(list(self.changed_fields))
        d["needs_persistence"] = sorted(list(self.needs_persistence))
        return d

# -----------------------------------------------------------------------------
# Inicialização & Acesso
# -----------------------------------------------------------------------------
def initialize_wizard_state() -> WizardState:
    """
    Inicializa session_state com chaves padrão e retorna WizardState.
    """
    if SESSION_KEY_STEP not in st.session_state:
        st.session_state[SESSION_KEY_STEP] = int(Step.VISION)

    if SESSION_KEY_VIEW not in st.session_state:
        st.session_state[SESSION_KEY_VIEW] = WizardView.WIZARD

    if SESSION_KEY_STATE not in st.session_state:
        st.session_state[SESSION_KEY_STATE] = WizardState(
            current_step=st.session_state[SESSION_KEY_STEP],
            current_view=st.session_state[SESSION_KEY_VIEW],
        )

    return st.session_state[SESSION_KEY_STATE]


def get_wizard_state() -> WizardState:
    """
    Obtém o estado atual do wizard da session state.
    """
    return initialize_wizard_state()

# -----------------------------------------------------------------------------
# Mutação de Estado
# -----------------------------------------------------------------------------
def _apply_updates(state: WizardState, updates: Dict[str, Any]) -> None:
    changed_any = False
    for key, value in updates.items():
        if hasattr(state, key):
            if getattr(state, key) != value:
                setattr(state, key, value)
                # legado + novo rastreamento
                state.dirty_flags[key] = True
                state.changed_fields.add(key)
                state.needs_persistence.add(key)
                changed_any = True
        else:
            logger.warning("Tentativa de atualizar campo inexistente: %s", key)
    if changed_any:
        state.updated_at = datetime.now()

def update_wizard_state(**kwargs: Any) -> None:
    """
    Atualiza campos específicos do estado do wizard e persiste no session_state.
    """
    state = get_wizard_state()
    _apply_updates(state, kwargs)
    st.session_state[SESSION_KEY_STATE] = state


def mark_step_dirty(step: int) -> None:
    """
    Marca um step como modificado (precisa ser salvo).
    """
    state = get_wizard_state()
    state.dirty_flags[f"step_{int(step)}"] = True
    state.updated_at = datetime.now()
    st.session_state[SESSION_KEY_STATE] = state

# -----------------------------------------------------------------------------
# Validação
# -----------------------------------------------------------------------------
def _validate_vision(state: WizardState) -> bool:
    ok = bool(state.vision_title.strip() and state.vision_description.strip())
    return ok

def _validate_epics(state: WizardState) -> bool:
    if not state.epics:
        return False
    for epic in state.epics:
        if not str(epic.get("title", "")).strip():
            return False
        if not str(epic.get("description", "")).strip():
            return False
    return True

def _validate_stories(state: WizardState) -> bool:
    return bool(state.stories) and all(str(s.get("title", "")).strip() for s in state.stories)

def _validate_tasks(state: WizardState) -> bool:
    return bool(state.tasks) and all(str(t.get("title", "")).strip() for t in state.tasks)

_VALIDATORS: Dict[int, Callable[[WizardState], bool]] = {
    Step.VISION: _validate_vision,
    Step.EPICS: _validate_epics,
    Step.STORIES: _validate_stories,
    Step.TASKS: _validate_tasks,
    Step.PREVIEW: lambda _s: True,  # preview sempre válido
}

def is_step_valid(step: int) -> bool:
    """
    Valida se um step possui dados válidos.
    """
    state = get_wizard_state()
    validator = _VALIDATORS.get(int(step))
    if validator is None:
        return False
    return validator(state)

def validate_all_wizard_data() -> bool:
    """
    Valida se todos os steps obrigatórios (1-4) estão preenchidos.
    """
    return all(is_step_valid(s) for s in (Step.VISION, Step.EPICS, Step.STORIES, Step.TASKS))

def add_validation_error(field: str, error: str) -> None:
    """
    Adiciona erro de validação para um campo.
    """
    state = get_wizard_state()
    errs = state.validation_errors.setdefault(field, [])
    if error not in errs:
        errs.append(error)
        state.updated_at = datetime.now()
    st.session_state[SESSION_KEY_STATE] = state

def clear_validation_errors(field: Optional[str] = None) -> None:
    """
    Limpa erros de validação. Se field for None, limpa todos.
    """
    state = get_wizard_state()
    if field is None:
        state.validation_errors.clear()
    else:
        state.validation_errors.pop(field, None)
    state.updated_at = datetime.now()
    st.session_state[SESSION_KEY_STATE] = state

def get_validation_errors(field: Optional[str] = None) -> Dict[str, List[str]]:
    """
    Obtém erros de validação. Se field especificado, retorna apenas desse campo.
    """
    state = get_wizard_state()
    if field is None:
        return state.validation_errors
    return {field: state.validation_errors.get(field, [])}

def has_validation_errors() -> bool:
    """
    Verifica se há erros de validação pendentes.
    """
    state = get_wizard_state()
    return any(state.validation_errors.values())

# -----------------------------------------------------------------------------
# Persistência (Auto-save em ai_generations) - Simulado
# -----------------------------------------------------------------------------
def _build_draft_payload(state: WizardState) -> JsonDict:
    """
    Prepara payload compacto para auto-save (somente campos relevantes).
    """
    payload: JsonDict = {
        "current_step": st.session_state.get(SESSION_KEY_STEP, int(Step.VISION)),
        "current_view": st.session_state.get(SESSION_KEY_VIEW, WizardView.WIZARD),
        "project_id": state.project_id,
        "vision_title": state.vision_title,
        "vision_description": state.vision_description,
        "vision_objectives": list(state.vision_objectives),
        "epics": list(state.epics),
        "stories": list(state.stories),
        "tasks": list(state.tasks),
        "velocity": state.velocity,
        "sprint_length": state.sprint_length,
        "ai_suggestions": dict(state.ai_suggestions),
        "planning_result": state.planning_result,
        "metadata": {
            "created_at": state.created_at.isoformat(),
            "updated_at": state.updated_at.isoformat(),
            "last_saved": datetime.now().isoformat(),
        },
    }
    return payload

def save_wizard_draft() -> bool:
    """
    Salva rascunho do wizard em ai_generations.
    Retorna True se salvou com sucesso.
    """
    try:
        state = get_wizard_state()
        draft_data = _build_draft_payload(state)

        # 🔐 Serialização segura (JSON)
        draft_json = json.dumps(draft_data, ensure_ascii=False)
        
        # Persist to ai_generations table
        if AI_MODELS_AVAILABLE:
            result = safe_streamlit_operation(
                _save_to_ai_generations,
                draft_json=draft_json,
                state=state,
                default_return=False,
                operation_name="save_wizard_draft"
            )
            if not result:
                logger.warning("Database save failed, falling back to session-only save")
        else:
            logger.info("AI Generation model not available, using session-only save")

        # Always update session state (fallback)
        now = datetime.now()
        state.last_saved = now
        state.clear_dirty()  # Single call to clear both legacy and new flags
        st.session_state[SESSION_KEY_STATE] = state
        st.session_state[SESSION_KEY_LAST_AUTOSAVE] = now
        
        logger.info("Wizard draft auto-saved successfully")
        return True
        
    except Exception as e:  # noqa: BLE001 - loga e retorna False
        logger.error("Erro ao salvar rascunho do wizard: %s", e, exc_info=True)
        return False

def load_wizard_draft(draft_id: Optional[str] = None, user_id: Optional[int] = None) -> bool:
    """
    Carrega rascunho do wizard de ai_generations.
    Retorna True se carregou com sucesso.
    """
    try:
        if not AI_MODELS_AVAILABLE:
            logger.info("AI Generation model not available, using fresh state")
            initialize_wizard_state()
            return True
            
        # Load from database if available
        loaded_data = safe_streamlit_operation(
            _load_from_ai_generations,
            draft_id=draft_id,
            user_id=user_id,
            default_return=None,
            operation_name="load_wizard_draft"
        )
        
        if loaded_data:
            # Restore state from loaded data
            _restore_wizard_state_from_data(loaded_data)
            logger.info("Wizard draft loaded from database successfully%s", 
                       f" (id={draft_id})" if draft_id else "")
        else:
            # Fallback to fresh state
            logger.info("No saved draft found, initializing fresh wizard state")
            initialize_wizard_state()
            
        return True
        
    except Exception as e:  # noqa: BLE001
        logger.error("Erro ao carregar rascunho do wizard: %s", e, exc_info=True)
        initialize_wizard_state()  # Safe fallback
        return False

def _should_throttle_autosave() -> bool:
    """
    Evita auto-saves excessivos respeitando AUTO_SAVE_MIN_INTERVAL.
    """
    last: Optional[datetime] = st.session_state.get(SESSION_KEY_LAST_AUTOSAVE)
    if last is None:
        return False
    return datetime.now() - last < AUTO_SAVE_MIN_INTERVAL

def auto_save_wizard() -> None:
    """
    Auto-save do wizard quando há mudanças.
    Chamado automaticamente durante a navegação.
    """
    state = get_wizard_state()

    # Single check using new semantics
    has_changes = bool(state.needs_persistence or any(state.dirty_flags.values()))
    if not has_changes or _should_throttle_autosave():
        return

    ok = save_wizard_draft()
    now = datetime.now()
    last_toast_at: Optional[datetime] = st.session_state.get(_LAST_TOAST_AT_KEY)

    # Avoid multiple toasts in short interval
    if not last_toast_at or (now - last_toast_at) >= timedelta(seconds=3):
        if ok:
            st.toast("✅ Rascunho salvo automaticamente", icon="💾")
        else:
            st.toast("⚠️ Erro ao salvar rascunho", icon="🚨")
        st.session_state[_LAST_TOAST_AT_KEY] = now


def _save_to_ai_generations(draft_json: str, state: WizardState) -> bool:
    """
    Salva o draft na tabela ai_generations.
    Retorna True se salvou com sucesso.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if user has existing wizard draft
            user_id = _get_current_user_id()
            if user_id:
                cursor.execute(
                    "SELECT id FROM ai_generations WHERE generation_type = ? AND context_type = ? AND user_id = ? AND (expires_at IS NULL OR expires_at > ?)",
                    (GenerationType.PLANNING_ASSISTANCE.value, ContextType.PROJECT.value, user_id, datetime.now())
                )
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing draft
                    cursor.execute(
                        "UPDATE ai_generations SET ai_response = ?, generation_metadata = ?, updated_at = ? WHERE id = ?",
                        (draft_json, json.dumps({"last_step": state.current_step}), datetime.now(), existing[0])
                    )
                    logger.debug("Updated existing wizard draft (id=%s)", existing[0])
                else:
                    # Create new draft
                    cursor.execute(
                        "INSERT INTO ai_generations (generation_type, context_type, user_prompt, ai_response, user_id, content_type, generation_metadata, generated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            GenerationType.PLANNING_ASSISTANCE.value,
                            ContextType.PROJECT.value,
                            f"Wizard Draft - {state.vision_title or 'Untitled Project'}",
                            draft_json,
                            user_id,
                            ContentType.JSON.value,
                            json.dumps({"last_step": state.current_step, "total_steps": 5}),
                            datetime.now()
                        )
                    )
                    logger.debug("Created new wizard draft")
            else:
                # No user context, save as anonymous draft
                cursor.execute(
                    "INSERT INTO ai_generations (generation_type, context_type, user_prompt, ai_response, content_type, generation_metadata, generated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        GenerationType.PLANNING_ASSISTANCE.value,
                        ContextType.GENERAL.value,
                        "Anonymous Wizard Draft",
                        draft_json,
                        ContentType.JSON.value,
                        json.dumps({"anonymous": True, "last_step": state.current_step}),
                        datetime.now()
                    )
                )
                logger.debug("Created anonymous wizard draft")
            
            conn.commit()
            return True
            
    except Exception as e:
        logger.error("Failed to save wizard draft to database: %s", e, exc_info=True)
        return False


def _load_from_ai_generations(draft_id: Optional[str] = None, user_id: Optional[int] = None) -> Optional[JsonDict]:
    """
    Carrega draft da tabela ai_generations.
    Retorna dados do draft ou None se não encontrado.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            if draft_id:
                # Load specific draft by ID
                cursor.execute(
                    "SELECT ai_response FROM ai_generations WHERE id = ? AND generation_type = ?",
                    (draft_id, GenerationType.PLANNING_ASSISTANCE.value)
                )
            elif user_id:
                # Load most recent draft for user
                cursor.execute(
                    "SELECT ai_response FROM ai_generations WHERE user_id = ? AND generation_type = ? AND context_type = ? ORDER BY generated_at DESC LIMIT 1",
                    (user_id, GenerationType.PLANNING_ASSISTANCE.value, ContextType.PROJECT.value)
                )
            else:
                # Try to load anonymous draft from session context
                cursor.execute(
                    "SELECT ai_response FROM ai_generations WHERE generation_type = ? AND context_type = ? AND user_id IS NULL ORDER BY generated_at DESC LIMIT 1",
                    (GenerationType.PLANNING_ASSISTANCE.value, ContextType.GENERAL.value)
                )
            
            result = cursor.fetchone()
            if result:
                return json.loads(result[0])
            
            return None
            
    except Exception as e:
        logger.error("Failed to load wizard draft from database: %s", e, exc_info=True)
        return None


def _restore_wizard_state_from_data(data: JsonDict) -> None:
    """
    Restaura o estado do wizard a partir dos dados carregados.
    """
    try:
        # Update session state keys
        if "current_step" in data:
            st.session_state[SESSION_KEY_STEP] = data["current_step"]
        if "current_view" in data:
            st.session_state[SESSION_KEY_VIEW] = data["current_view"]
        
        # Create wizard state from loaded data
        metadata = data.get("metadata", {})
        
        state = WizardState(
            current_step=data.get("current_step", Step.VISION),
            current_view=data.get("current_view", WizardView.WIZARD),
            project_id=data.get("project_id"),
            vision_title=data.get("vision_title", ""),
            vision_description=data.get("vision_description", ""),
            vision_objectives=data.get("vision_objectives", []),
            epics=data.get("epics", []),
            stories=data.get("stories", []),
            tasks=data.get("tasks", []),
            velocity=data.get("velocity", 10),
            sprint_length=data.get("sprint_length", 14),
            ai_suggestions=data.get("ai_suggestions", {}),
            planning_result=data.get("planning_result"),
            last_saved=datetime.fromisoformat(metadata.get("last_saved")) if metadata.get("last_saved") else None,
            created_at=datetime.fromisoformat(metadata.get("created_at")) if metadata.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(metadata.get("updated_at")) if metadata.get("updated_at") else datetime.now()
        )
        
        # Update session state with restored state
        st.session_state[SESSION_KEY_STATE] = state
        
        logger.debug("Wizard state restored successfully")
        
    except Exception as e:
        logger.error("Failed to restore wizard state from data: %s", e, exc_info=True)
        # Fallback to initialize fresh state
        initialize_wizard_state()


def _get_current_user_id() -> Optional[int]:
    """
    Obtém o ID do usuário atual da sessão.
    Retorna None se não autenticado.
    """
    try:
        # Try to get user from session state (standard auth pattern)
        current_user = st.session_state.get("authenticated_user")
        if current_user and isinstance(current_user, dict):
            return current_user.get("id")
        
        # Fallback - try alternative auth patterns
        user_id = st.session_state.get("user_id")
        if user_id:
            return int(user_id)
            
        return None
        
    except Exception as e:
        logger.debug("Could not determine current user ID: %s", e)
        return None

# --- Navegação consistente entre state <-> session ---
from typing import Union

def set_current_step(step: Union[int, Step]) -> None:
    """Atualiza passo atual no WizardState e nas chaves de sessão."""
    state = get_wizard_state()
    step_int = int(step)
    if state.current_step != step_int:
        state.current_step = step_int
        state.dirty_flags["current_step"] = True
        state.updated_at = datetime.now()
        st.session_state[SESSION_KEY_STEP] = step_int
        st.session_state[SESSION_KEY_STATE] = state
        logger.info("Wizard step -> %s", step_int)

def set_current_view(view: Union[str, WizardView]) -> None:
    """Atualiza view atual no WizardState e nas chaves de sessão."""
    state = get_wizard_state()
    view_str = str(view)
    if state.current_view != view_str:
        state.current_view = view_str
        state.dirty_flags["current_view"] = True
        state.updated_at = datetime.now()
        st.session_state[SESSION_KEY_VIEW] = view_str
        st.session_state[SESSION_KEY_STATE] = state
        logger.info("Wizard view -> %s", view_str)

def sync_nav_from_session() -> None:
    """Sincroniza navegação priorizando WizardState como fonte primária."""
    state = get_wizard_state()
    step_sess = int(st.session_state.get(SESSION_KEY_STEP, int(Step.VISION)))
    view_sess = st.session_state.get(SESSION_KEY_VIEW, WizardView.WIZARD)

    # preferimos o que já está no state; só usamos sessão como bootstrap
    changed = False
    if SESSION_KEY_STATE not in st.session_state:
        state.current_step = step_sess
        state.current_view = view_sess
        changed = True

    # refletimos sempre o valor do state para as chaves derivadas
    if st.session_state.get(SESSION_KEY_STEP) != state.current_step:
        st.session_state[SESSION_KEY_STEP] = int(state.current_step)
    if st.session_state.get(SESSION_KEY_VIEW) != state.current_view:
        st.session_state[SESSION_KEY_VIEW] = str(state.current_view)

    if changed:
        state.updated_at = datetime.now()
        st.session_state[SESSION_KEY_STATE] = state

# --- Autosave: seguro e silencioso quando não precisa salvar ---
_LAST_TOAST_AT_KEY = "projeto_wizard_last_toast_at"

# --- Restauração com normalização e limpeza ---
def _normalize_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return list(value) if hasattr(value, "__iter__") and not isinstance(value, (str, bytes, dict)) else [value]

def _normalize_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}

def _restore_wizard_state_from_data(data: JsonDict) -> None:
    try:
        # session keys
        if "current_step" in data:
            st.session_state[SESSION_KEY_STEP] = int(data["current_step"])
        if "current_view" in data:
            st.session_state[SESSION_KEY_VIEW] = str(data["current_view"])

        meta = _normalize_dict(data.get("metadata", {}))
        def _dt(key: str, default: Optional[datetime] = None) -> Optional[datetime]:
            v = meta.get(key)
            try:
                return datetime.fromisoformat(v) if v else default
            except Exception:
                return default

        state = WizardState(
            current_step=int(data.get("current_step", int(Step.VISION))),
            current_view=str(data.get("current_view", WizardView.WIZARD)),
            project_id=data.get("project_id"),
            vision_title=data.get("vision_title", ""),
            vision_description=data.get("vision_description", ""),
            vision_objectives=_normalize_list(data.get("vision_objectives")),
            epics=_normalize_list(data.get("epics")),
            stories=_normalize_list(data.get("stories")),
            tasks=_normalize_list(data.get("tasks")),
            velocity=int(data.get("velocity", 10)),
            sprint_length=int(data.get("sprint_length", 14)),
            ai_suggestions=_normalize_dict(data.get("ai_suggestions")),
            planning_result=data.get("planning_result"),
            last_saved=_dt("last_saved"),
            created_at=_dt("created_at", datetime.now()) or datetime.now(),
            updated_at=_dt("updated_at", datetime.now()) or datetime.now(),
        )

        # restaura e limpa flags (estado carregado não é “sujo”)
        state.clear_dirty()
        st.session_state[SESSION_KEY_STATE] = state
        st.session_state[SESSION_KEY_LAST_AUTOSAVE] = datetime.now()
        logger.info("Wizard state restored (step=%s, view=%s)", state.current_step, state.current_view)
    except Exception as e:
        logger.error("Failed to restore wizard state from data: %s", e, exc_info=True)
        initialize_wizard_state()

# state_manager.py (ao final do arquivo)
class WizardStateManager:
    """
    Fachada simples: navegação, atualização e persistência.
    Single source of truth para operações do wizard.
    """
    
    @staticmethod
    def current_step() -> int:
        """Get current wizard step."""
        return int(get_wizard_state().current_step)
    
    @staticmethod
    def current_view() -> str:
        """Get current wizard view."""
        return str(get_wizard_state().current_view)

    @staticmethod
    def navigate_to(step: int) -> bool:
        """
        Navigate to specific step with validation.
        Returns True if navigation successful.
        """
        cur = WizardStateManager.current_step()
        if step == cur:
            return True
        if step > cur and not is_step_valid(cur):
            return False
        set_current_step(step)
        auto_save_wizard()
        return True

    @staticmethod
    def update(field: str, value: Any) -> None:
        """Update single field with auto-save."""
        update_wizard_state(**{field: value})
        auto_save_wizard()
    
    @staticmethod
    def update_multiple(**fields: Any) -> None:
        """Update multiple fields at once with single auto-save."""
        update_wizard_state(**fields)
        auto_save_wizard()

    @staticmethod
    def save() -> bool:
        """Manually save wizard draft."""
        return save_wizard_draft()

    @staticmethod
    def load(user_id: Optional[int] = None) -> bool:
        """Load wizard draft for user."""
        return load_wizard_draft(user_id=user_id)
    
    @staticmethod
    def has_changes() -> bool:
        """Check if there are unsaved changes."""
        state = get_wizard_state()
        return bool(state.needs_persistence)
    
    @staticmethod
    def get_validation_status() -> Dict[str, bool]:
        """Get validation status for all steps."""
        return {
            'vision': is_step_valid(int(Step.VISION)),
            'epics': is_step_valid(int(Step.EPICS)),
            'stories': is_step_valid(int(Step.STORIES)),
            'tasks': is_step_valid(int(Step.TASKS)),
            'preview': is_step_valid(int(Step.PREVIEW)),
        }
    
    @staticmethod
    def reset_wizard() -> None:
        """Reset wizard to initial state."""
        # Clear session state keys
        keys_to_clear = [
            SESSION_KEY_STATE,
            SESSION_KEY_STEP, 
            SESSION_KEY_VIEW,
            SESSION_KEY_LAST_AUTOSAVE,
            _LAST_TOAST_AT_KEY,
            "wizard_draft_loaded"
        ]
        for key in keys_to_clear:
            st.session_state.pop(key, None)
        # Reinitialize
        initialize_wizard_state()
