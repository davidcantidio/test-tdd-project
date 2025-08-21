# -*- coding: utf-8 -*-
"""
⏱️ Timer Component for TDD Framework (Refactor)

Recursos:
- Sessões Pomodoro (foco, pausa curta, pausa longa)
- Pausa/Retomar corretos com tempo acumulado
- Barra de progresso consistente com o display
- Contagem de ciclos (para acionar long break)
- Registro de interrupções, rating e notas
- Salvamento no DB (flexível a diferentes assinaturas)
"""

from __future__ import annotations

from typing import Optional, Dict, Any, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

# Streamlit (opcional)
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except Exception:
    st = None  # type: ignore
    STREAMLIT_AVAILABLE = False

# DB API (modular) com fallback
DATABASE_AVAILABLE = True
try:
    from ..database import transaction  # type: ignore
    from ..database.queries import create_timer_session, list_timer_sessions  # type: ignore
except Exception:
    DATABASE_AVAILABLE = False
    def transaction():  # type: ignore
        class _Noop:
            def __enter__(self): return self
            def __exit__(self, *exc): return False
        return _Noop()
    def create_timer_session(**kwargs):  # type: ignore
        return False
    def list_timer_sessions(days: int = 30):  # type: ignore
        return []

# Import DRY form components
try:
    from .form_components import render_timer_config
    FORM_COMPONENTS_AVAILABLE = True
except ImportError:
    FORM_COMPONENTS_AVAILABLE = False
    render_timer_config = None

# ---------------------------------------------------------------------------
# Datamodel
# ---------------------------------------------------------------------------
@dataclass
class TimerSession:
    """Representa uma sessão de timer."""
    session_type: str            # 'focus' | 'short_break' | 'long_break'
    started_at: Optional[str]    # ISO8601 quando ativa; None quando pausada/inativa
    planned_sec: int             # duração planejada (segundos)
    accum_sec: int = 0           # acumulado em pausas + blocos anteriores
    is_active: bool = False
    ended_at: Optional[str] = None
    task_id: Optional[int] = None
    focus_rating: Optional[int] = None  # 1..10 (apenas para 'focus')
    interruptions: int = 0
    notes: Optional[str] = None

    def elapsed_sec(self) -> int:
        base = self.accum_sec
        if self.is_active and self.started_at:
            try:
                base += int((now() - datetime.fromisoformat(self.started_at)).total_seconds())
            except Exception:
                pass
        return max(0, base)

    def remaining_sec(self) -> int:
        return max(0, self.planned_sec - self.elapsed_sec())

    def progress(self) -> float:
        if self.planned_sec <= 0:
            return 0.0
        return min(1.0, self.elapsed_sec() / float(self.planned_sec))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def now() -> datetime:
    return datetime.now()

def mmss(sec: int) -> str:
    sec = max(0, int(sec))
    return f"{sec // 60:02d}:{sec % 60:02d}"

def _safe_int(x: Any, default: int = 0) -> int:
    try:
        return int(x)
    except Exception:
        return default

# ---------------------------------------------------------------------------
# Session keys (namespaced)
# ---------------------------------------------------------------------------
SK_CFG      = "timer2.config"
SK_SESSION  = "timer2.session"
SK_CYCLES   = "timer2.cycles_completed"  # número de sessões de foco concluídas

DEFAULT_CFG = {
    "focus_duration_min": 25,
    "short_break_min": 5,
    "long_break_min": 15,
    "sessions_until_long_break": 4,
    "auto_start_breaks": False,
    "auto_start_focus": False,
}

def _init_state():
    if not STREAMLIT_AVAILABLE:
        return
    st.session_state.setdefault(SK_CFG, DEFAULT_CFG.copy())
    st.session_state.setdefault(SK_SESSION, None)
    st.session_state.setdefault(SK_CYCLES, 0)

# ---------------------------------------------------------------------------
# Timer Component
# ---------------------------------------------------------------------------
class TimerComponent:
    # Delegation to TimerComponentUiinteraction
    def __init__(self):
        self._timercomponentuiinteraction = TimerComponentUiinteraction()
    # Delegation to TimerComponentValidation
    def __init__(self):
        self._timercomponentvalidation = TimerComponentValidation()
    # Delegation to TimerComponentNetworking
    def __init__(self):
        self._timercomponentnetworking = TimerComponentNetworking()
    # Delegation to TimerComponentLogging
    def __init__(self):
        self._timercomponentlogging = TimerComponentLogging()
    # Delegation to TimerComponentConfiguration
    def __init__(self):
        self._timercomponentconfiguration = TimerComponentConfiguration()
    # Delegation to TimerComponentCalculation
    def __init__(self):
        self._timercomponentcalculation = TimerComponentCalculation()
    # Delegation to TimerComponentFormatting
    def __init__(self):
        self._timercomponentformatting = TimerComponentFormatting()
    # Delegation to TimerComponentErrorhandling
    def __init__(self):
        self._timercomponenterrorhandling = TimerComponentErrorhandling()
    """
    Timer Pomodoro com suporte a TDAH.
    Integração opcional com tarefa atual via get_current_task_id().
    """

    def __init__(self):
        if STREAMLIT_AVAILABLE:
            _init_state()

    # ---------- API pública ----------
    def render(
        self,
        container=None,
        get_current_task_id: Optional[Callable[[], Optional[int]]] = None
    ) -> Dict[str, Any]:
        """
        Renderiza o timer.

        Args:
            container: container de destino no Streamlit
            get_current_task_id: função para obter task_id atual (inteiro)

        Returns:
            dicionário com estado do timer
        """
        if not STREAMLIT_AVAILABLE:
            return {"error": "Streamlit not available"}

        if container is None:
            container = st.container()

        with container:
            return self._render_ui(get_current_task_id=get_current_task_id)

    def get_session_summary(self) -> Dict[str, Any]:
        """Resumo da sessão atual (sem render)."""
        if not STREAMLIT_AVAILABLE:
            return {}
        ts: Optional[TimerSession] = st.session_state.get(SK_SESSION)
        cfg = st.session_state.get(SK_CFG, DEFAULT_CFG)
        return {
            "has_active_session": bool(ts and ts.is_active),
            "session_type": ts.session_type if ts else None,
            "elapsed_minutes": (ts.elapsed_sec() // 60) if ts else 0,
            "interruptions": ts.interruptions if ts else 0,
            "cycles_completed": _safe_int(st.session_state.get(SK_CYCLES), 0),
            "planned_minutes": (ts.planned_sec // 60) if ts else 0,
        }

    # ---------- UI e ações ----------
    def _render_ui(self, get_current_task_id: Optional[Callable[[], Optional[int]]]) -> Dict[str, Any]:
        ts: Optional[TimerSession] = st.session_state.get(SK_SESSION)
        cfg: Dict[str, Any] = st.session_state.get(SK_CFG, DEFAULT_CFG)

        # Header
        st.markdown("## ⏱️ Focus Timer")
        subtitle = ts.session_type.replace("_", " ").title() if ts else "Focus Session"
        emoji = {"focus": "🎯", "short_break": "☕", "long_break": "🌿"}.get(ts.session_type if ts else "focus", "⏱️")
        st.markdown(f"### {emoji} {subtitle}")

        # Tempo + progresso
        remain = ts.remaining_sec() if ts else 0
        st.markdown(
            f'<div style="text-align:center;font-size:3rem;font-weight:700;'
            f'color:#FF6B6B;margin:1rem 0;">{mmss(remain)}</div>',
            unsafe_allow_html=True,
        )
        if ts:
            st.progress(ts.progress())

        # Controles
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            if not ts or not ts.is_active:
                if st.button("▶️ Start", use_container_width=True):
                    self._action_start(ts, cfg, get_current_task_id)
                    st.rerun()
            else:
                if st.button("⏸️ Pause", use_container_width=True):
                    self._action_pause(ts)
                    st.rerun()

        with c2:
            if st.button("⏹️ Stop", use_container_width=True):
                self._action_stop(ts, cfg, save=True)
                st.rerun()

        with c3:
            if st.button("⏭️ Skip", use_container_width=True):
                self._action_stop(ts, cfg, save=False)  # não grava sessão "pulada"
                st.rerun()

        with c4:
            if ts and st.button("➕ Add 5min", use_container_width=True):
                ts.planned_sec += 5 * 60
                st.session_state[SK_SESSION] = ts
                st.rerun()

        # Interrupções durante foco
        if ts and ts.is_active and ts.session_type == "focus":
            st.markdown("---")
            st.markdown("### 🧠 TDAH Support")
            i1, i2 = st.columns(2)
            with i1:
                if st.button("😵 Distraction", use_container_width=True):
                    ts.interruptions += 1
                    st.session_state[SK_SESSION] = ts
                    st.rerun()
            with i2:
                st.metric("Interruptions", ts.interruptions)

        # Alerta quando tempo acaba (sem loop: exige interação do usuário)
        if ts and ts.remaining_sec() == 0 and ts.is_active:
            st.warning("⏰ Tempo esgotado! Conclua a sessão para continuar.")
            if ts.session_type == "focus":
                with st.expander("✅ Finalizar foco (opcional: avalie sua sessão)"):
                    rating = st.slider("Focus rating", 1, 10, value=7)
                    notes = st.text_input("Notas")
                    if st.button("✅ Concluir e salvar"):
                        ts.focus_rating = rating
                        ts.notes = notes
                        self._action_stop(ts, cfg, save=True)
                        st.success("Sessão de foco registrada.")
                        st.rerun()
            else:
                if st.button("✅ Concluir pausa"):
                    self._action_stop(ts, cfg, save=False)  # não salva pausas
                    st.rerun()

        # Configurações - Using DRY component
        if FORM_COMPONENTS_AVAILABLE and render_timer_config:
            updated_config = render_timer_config(current_config=cfg, form_id="timer_config")
            if updated_config:
                st.session_state[SK_CFG] = updated_config
                st.success("Settings saved.")
                st.rerun()
        else:
            # Fallback: Original inline settings
            with st.expander("⚙️ Timer Settings"):
                fmin = st.slider("Focus (min)", 10, 90, value=_safe_int(cfg.get("focus_duration_min", 25)), step=5)
                smin = st.slider("Short break (min)", 3, 20, value=_safe_int(cfg.get("short_break_min", 5)), step=1)
                lmin = st.slider("Long break (min)", 10, 60, value=_safe_int(cfg.get("long_break_min", 15)), step=5)
                every = st.slider("Long break every N focus", 2, 8,
                                  value=_safe_int(cfg.get("sessions_until_long_break", 4)), step=1)
                auto_b = st.checkbox("Auto-start breaks", value=bool(cfg.get("auto_start_breaks", False)))
                auto_f = st.checkbox("Auto-start next focus", value=bool(cfg.get("auto_start_focus", False)))

                if st.button("💾 Save Settings"):
                    cfg.update({
                        "focus_duration_min": fmin,
                        "short_break_min": smin,
                        "long_break_min": lmin,
                        "sessions_until_long_break": every,
                        "auto_start_breaks": auto_b,
                        "auto_start_focus": auto_f,
                    })
                    st.session_state[SK_CFG] = cfg
                    st.success("Settings saved.")
                    st.rerun()

        # Resumo de hoje (simples; pode ser enriquecido com list_timer_sessions)
        focus_done = _safe_int(st.session_state.get(SK_CYCLES), 0)
        st.markdown("---")
        r1, r2, r3 = st.columns(3)
        with r1:
            st.metric("Focus sessions", focus_done)
        with r2:
            total_focus_min = focus_done * _safe_int(cfg.get("focus_duration_min"), 25)
            st.metric("Planned focus time", f"{total_focus_min} min")
        with r3:
            st.metric("Status", "Running" if ts and ts.is_active else "Paused/Idle")

        return {
            "current_session": asdict(ts) if ts else None,
            "is_active": bool(ts and ts.is_active),
            "session_type": ts.session_type if ts else None,
            "elapsed_seconds": ts.elapsed_sec() if ts else 0,
            "remaining_seconds": ts.remaining_sec() if ts else 0,
            "cycles_completed": _safe_int(st.session_state.get(SK_CYCLES), 0),
        }

    # ---------- Transições ----------
    def _action_start(self, ts: Optional[TimerSession], cfg: Dict[str, Any],
                      get_current_task_id: Optional[Callable[[], Optional[int]]]) -> None:
        # Retomar sessão pausada
        if ts and not ts.is_active:
            ts.is_active = True
            ts.started_at = now().isoformat()
            st.session_state[SK_SESSION] = ts
            return

        # Nova sessão
        if not ts:
            session_type = self._next_session_type(cfg)
        else:
            # Se existe sessão ativa, não cria outra
            if ts.is_active:
                return
            session_type = self._next_session_type(cfg)

        planned_min = self._planned_minutes_for(session_type, cfg)
        task_id = None
        if get_current_task_id:
            try:
                task_id = get_current_task_id()
            except Exception:
                task_id = None

        new_ts = TimerSession(
            session_type=session_type,
            started_at=now().isoformat(),
            planned_sec=int(planned_min * 60),
            accum_sec=0,
            is_active=True,
            task_id=_safe_int(task_id) if task_id is not None else None,
        )
        st.session_state[SK_SESSION] = new_ts

    def _action_pause(self, ts: Optional[TimerSession]) -> None:
        if not ts or not ts.is_active:
            return
        # acumula e desativa
        if ts.started_at:
            ts.accum_sec = ts.elapsed_sec()
        ts.is_active = False
        ts.started_at = None
        st.session_state[SK_SESSION] = ts

    def _action_stop(self, ts: Optional[TimerSession], cfg: Dict[str, Any], save: bool) -> None:
        if not ts:
            return
        # Finaliza
        ts.is_active = False
        ts.ended_at = now().isoformat()
        # normaliza acumulado final
        ts.accum_sec = ts.elapsed_sec()
        st.session_state[SK_SESSION] = ts

        # Atualiza ciclos (apenas foco)
        if ts.session_type == "focus":
            st.session_state[SK_CYCLES] = _safe_int(st.session_state.get(SK_CYCLES), 0) + 1

        # Persiste (apenas foco)
        if save and ts.session_type == "focus":
            self._persist_focus_session(ts)

        # Limpa sessão atual
        st.session_state[SK_SESSION] = None

        # Auto-start próximo estágio se configurado
        nxt = self._next_after(ts, cfg)
        if nxt == "short_break" or nxt == "long_break":
            if cfg.get("auto_start_breaks"):
                self._action_start(None, cfg, get_current_task_id=None)
        elif nxt == "focus":
            if cfg.get("auto_start_focus"):
                self._action_start(None, cfg, get_current_task_id=None)

    # ---------- Lógica Pomodoro ----------
    def _next_session_type(self, cfg: Dict[str, Any]) -> str:
        ts: Optional[TimerSession] = st.session_state.get(SK_SESSION)
        cycles = _safe_int(st.session_state.get(SK_CYCLES), 0)
        # Se ainda não houve foco concluído, começa com foco
        if ts is None:
            return "focus"
        # Caso contrário, alterna baseada no histórico (quando for criar NOVA)
        return self._next_after(ts, cfg)

    def _next_after(self, ts: TimerSession, cfg: Dict[str, Any]) -> str:
        if ts.session_type == "focus":
            # Após foco: pausa curta ou longa
            cycles = _safe_int(st.session_state.get(SK_CYCLES), 0)
            every = _safe_int(cfg.get("sessions_until_long_break"), 4)
            return "long_break" if (cycles % max(1, every)) == 0 else "short_break"
        else:
            # Após pausa: sempre volta para foco
            return "focus"

    def _planned_minutes_for(self, session_type: str, cfg: Dict[str, Any]) -> int:
        if session_type == "focus":
            return _safe_int(cfg.get("focus_duration_min"), 25)
        if session_type == "short_break":
            return _safe_int(cfg.get("short_break_min"), 5)
        if session_type == "long_break":
            return _safe_int(cfg.get("long_break_min"), 15)
        return 25

    # ---------- Persistência ----------
    def _persist_focus_session(self, ts: TimerSession) -> bool:
        if not DATABASE_AVAILABLE:
            if STREAMLIT_AVAILABLE:
                st.info("ℹ️ Banco indisponível — sessão não foi salva.")
            return False

        payload = {
            "task_id": ts.task_id,
            "planned_duration_minutes": int(round(ts.planned_sec / 60)),
            "actual_duration_minutes": int(round(ts.accum_sec / 60)),
            "focus_rating": ts.focus_rating,
            "interruptions": ts.interruptions,
            "started_at": ts.started_at,
            "ended_at": ts.ended_at,
            "notes": ts.notes,
        }

        # Tenta diferentes assinaturas para compatibilidade
        try:
            with transaction():
                return bool(create_timer_session(**payload))
        except TypeError:
            # fallback: versão mais antiga
            minimal = {
                "task_id": ts.task_id,
                "duration_minutes": int(round(ts.planned_sec / 60)),
                "actual_duration_minutes": int(round(ts.accum_sec / 60)),
                "focus_rating": ts.focus_rating,
                "interruptions": ts.interruptions,
                "ended_at": ts.ended_at,
                "notes": ts.notes,
            }
            try:
                with transaction():
                    return bool(create_timer_session(**minimal))
            except Exception as e:
                if STREAMLIT_AVAILABLE:
                    st.warning(f"⚠️ Falha ao salvar sessão (fallback): {e}")
                return False
        except Exception as e:
            if STREAMLIT_AVAILABLE:
                st.warning(f"⚠️ Falha ao salvar sessão: {e}")
            return False