# streamlit_extension/pages/projeto_wizard/projeto_wizard.py
from __future__ import annotations

import logging
from datetime import date
from typing import Any, Dict, List, Optional

import streamlit as st

logger = logging.getLogger(__name__)

# --- Autenticação -------------------------------------------------------------
# Import absoluto; em dev caímos num fallback simples
try:
    from streamlit_extension.auth.middleware import init_protected_page, require_auth
except ImportError:
    def init_protected_page(title: str, *, layout: str = "wide") -> None:
        st.set_page_config(page_title=title, layout=layout)

    def require_auth(role: Optional[str] = None):
        def _decorator(fn):
            def _inner(*args, **kwargs):
                return fn(*args, **kwargs)
            return _inner
        return _decorator

# --- Camada de banco (padrão híbrido com fallback) ---------------------------
_DBM = None
_queries = None
_transaction_ctx = None
_db_initialized = False

def _init_db_layer() -> None:
    """Inicializa camada de banco com fallbacks robustos."""
    global _DBM, _queries, _transaction_ctx, _db_initialized

    if _db_initialized:
        return

    # Tenta API modular primeiro
    try:
        from streamlit_extension.database import queries
        from streamlit_extension.database.connection import transaction

        _queries = queries
        _transaction_ctx = transaction
        _db_initialized = True
        return
    except Exception:
        pass

    # Fallback para DatabaseManager
    try:
        from streamlit_extension.utils.database import DatabaseManager
        _DBM = DatabaseManager()
        _db_initialized = True
    except Exception as e:
        st.error(f"❌ Sistema de banco indisponível: {e}")
        _db_initialized = False

def _create_project_safely(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Cria projeto usando API modular com fallback para DatabaseManager.
    """
    _init_db_layer()

    if not _db_initialized:
        return {"ok": False, "error": "Sistema de banco de dados indisponível"}

    try:
        if _queries is not None and _transaction_ctx is not None:
            return _create_project_with_modular_api(payload)

        if _DBM is not None:
            return _create_project_with_manager(payload)

        return {"ok": False, "error": "Nenhuma API de banco disponível"}
    except Exception as e:
        return {"ok": False, "error": f"Falha ao criar projeto: {e}"}

def _create_project_with_modular_api(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Cria projeto usando a API modular (com transação)."""
    with _transaction_ctx() as conn:
        cursor = conn.execute(
            """
            INSERT INTO framework_projects (project_key, name, description, status)
            VALUES (?, ?, ?, 'active')
            """,
            (payload.get("project_key"), payload.get("name"), payload.get("description", "")),
        )
        project_id = cursor.lastrowid
        created = {
            "id": project_id,
            "project_key": payload.get("project_key"),
            "name": payload.get("name"),
            "description": payload.get("description", ""),
            "status": "active",
        }
        return {"ok": True, "data": created}

def _create_project_with_manager(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Cria projeto usando DatabaseManager (fallback)."""
    data = {
        "project_key": payload.get("project_key"),
        "name": payload.get("name"),
        "description": payload.get("description", ""),
        "status": "active",
    }
    result = _DBM.create_project(data)  # type: ignore[attr-defined]
    if result and result.get("id"):
        return {"ok": True, "data": result}
    return {"ok": False, "error": "Falha ao criar projeto via DatabaseManager"}

# --- UI helpers ---------------------------------------------------------------
def _form_validation(project_name: str, start: date, end: date, budget: float) -> List[str]:
    errors: List[str] = []
    if not project_name or len(project_name.strip()) < 3:
        errors.append("Informe um nome de projeto com pelo menos 3 caracteres.")
    if end < start:
        errors.append("A data de término não pode ser anterior à data de início.")
    if budget < 0:
        errors.append("O orçamento não pode ser negativo.")
    return errors

@require_auth()
def _render() -> None:
    st.set_page_config(page_title="Projeto Wizard", layout="wide")
    init_protected_page("Projeto Wizard")
    st.title("🧙‍♂️ Projeto Wizard")

    _init_db_layer()

    col_left, col_right = st.columns([2, 1], vertical_alignment="top")

    with col_left:
        st.subheader("1) Informações do Projeto")
        with st.form("project_wizard_form", clear_on_submit=False):
            project_name = st.text_input("Nome do Projeto", placeholder="Ex.: Plataforma X")
            description = st.text_area("Descrição (opcional)", placeholder="Contexto, objetivos e escopo…")
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Início", value=date.today())
            with col2:
                end_date = st.date_input("Término", value=date.today())
            col3, col4 = st.columns(2)
            with col3:
                budget = st.number_input("Orçamento (R$)", min_value=0.0, step=1000.0, value=0.0)
            with col4:
                status = st.selectbox("Status", ["Planned", "In Progress", "On Hold", "Completed"], index=0)

            submitted = st.form_submit_button("Criar Projeto", use_container_width=True)

        if submitted:
            errors = _form_validation(project_name, start_date, end_date, budget)
            if errors:
                for e in errors:
                    st.error(e)
                st.stop()

            # Gera project_key simples e estável
            import re
            project_key = re.sub(r"[^\w]", "", project_name.strip().lower().replace(" ", "_").replace("-", "_"))[:50]

            payload: Dict[str, Any] = {
                "project_key": project_key,
                "name": project_name.strip(),
                "description": (description or "").strip(),
                "start_date": str(start_date),
                "end_date": str(end_date),
                "budget": float(budget),
                "status": status.lower().replace(" ", "_"),
            }

            result = _create_project_safely(payload)
            if result.get("ok"):
                st.success("✅ Projeto criado com sucesso!")
                st.json(result.get("data", {}))
                st.toast("Projeto criado", icon="✅")
            else:
                st.error(result.get("error", "Falha desconhecida ao criar projeto."))

    with col_right:
        st.subheader("2) Resumo")
        st.caption("Revise as informações antes de criar o projeto.")
        st.info(
            "• Este assistente usa o **padrão híbrido de banco** automaticamente.\n"
            "• Em **desenvolvimento**, a página permite acesso mesmo sem login.\n"
            "• Em **produção**, o middleware real de autenticação deve estar ativo.",
            icon="ℹ️",
        )
        st.write("### Dicas")
        st.write(
            "- Use nomes claros e padronizados para facilitar analytics.\n"
            "- Defina datas realistas; você pode ajustar depois.\n"
            "- Orçamento pode ser zero se o projeto não tiver CAPEX/OPEX definido."
        )

def render_projeto_wizard_page() -> Dict[str, Any]:
    """Interface pública para a página do wizard (usada pelo roteador de páginas)."""
    logger.info("🚀 Project wizard page requested - rendering…")
    try:
        _render()
        return {"status": "success", "page": "projeto_wizard"}
    except Exception as e:
        logger.error(f"❌ Error rendering project wizard page: {e}")
        st.error("⚠️ Erro ao carregar página do wizard")
        return {"status": "error", "error": str(e), "page": "projeto_wizard"}

# Importar este módulo não deve renderizar nada automaticamente.
if __name__ == "__main__":
    _render()
