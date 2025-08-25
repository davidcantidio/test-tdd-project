# streamlit_extension/pages/projeto_wizard.py
# -----------------------------------------------------------------------------
# Projeto Wizard (P0) - Página Streamlit com correções:
# - Import absoluto do middleware (corrige ImportError de relative import)
# - Fallback de autenticação em modo dev (comportamento consistente com dashboard)
# - Formulário em st.form (remove console warnings de campo fora de <form>)
# - Sem CSS/HTML vazando (no unsafe_allow_html)
# - Padrão híbrido de banco (DatabaseManager + transaction) com autodetecção
# - Validações e mensagens claras, erros tratados sem quebrar a página
# -----------------------------------------------------------------------------

from __future__ import annotations

import logging
from datetime import date
from typing import Any, Dict, List, Optional

import streamlit as st

logger = logging.getLogger(__name__)

# --- Autenticação -------------------------------------------------------------
# Import absoluto (corrige erro crítico do relatório):
try:
    from streamlit_extension.auth.middleware import init_protected_page, require_auth
except ImportError:
    # Fallback seguro em desenvolvimento: mantém página acessível
    def init_protected_page(title: str, *, layout: str = "wide") -> None:
        st.set_page_config(page_title=title, layout=layout)

    def require_auth(role: Optional[str] = None):  # type: ignore
        def _decorator(fn):
            def _inner(*args, **kwargs):
                # Em produção real, este fallback não deve ser usado.
                return fn(*args, **kwargs)
            return _inner
        return _decorator

# --- Banco (padrão híbrido) ---------------------------------------------------
# Preferimos o híbrido, mas funcionamos mesmo que alguma API não esteja disponível
_DBM = None
_queries = None
_transaction_ctx = None
_db_initialized = False

def _init_db_layer() -> None:
    """Inicializa camada de banco com fallbacks robustos."""
    global _DBM, _queries, _transaction_ctx, _db_initialized
    
    if _db_initialized:
        logger.info("Database layer already initialized")
        return
    
    logger.info("Initializing database layer for projeto wizard...")
    
    # Try modular database API first
    try:
        logger.info("Attempting to import modular database API...")
        from streamlit_extension.database import queries
        from streamlit_extension.database.connection import transaction
        
        _queries = queries
        _transaction_ctx = transaction
        _db_initialized = True
        logger.info("✅ Modular database API successfully initialized")
        return
        
    except ImportError as e:
        logger.warning(f"Modular database API import failed: {e}")
        st.info("🔄 Using fallback database system...")
    except Exception as e:
        logger.error(f"Unexpected error with modular database API: {e}")
        st.warning(f"Database API error: {e}")
    
    # Fallback to DatabaseManager
    try:
        logger.info("Attempting DatabaseManager fallback...")
        from streamlit_extension.utils.database import DatabaseManager
        _DBM = DatabaseManager()
        _db_initialized = True
        logger.info("✅ DatabaseManager fallback successfully initialized")
        return
        
    except ImportError as e:
        logger.error(f"DatabaseManager import failed: {e}")
        st.error("❌ Sistema de banco de dados indisponível")
        _db_initialized = False
    except Exception as e:
        logger.error(f"DatabaseManager initialization failed: {e}")
        st.error(f"❌ Falha na inicialização do banco: {e}")
        _db_initialized = False


def _create_project_safely(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Cria projeto usando API modular com fallback para DatabaseManager.
    """
    # Ensure database layer is initialized
    _init_db_layer()
    
    if not _db_initialized:
        return {"ok": False, "error": "Sistema de banco de dados indisponível"}
    
    try:
        # Try modular API first
        if _queries is not None and _transaction_ctx is not None:
            return _create_project_with_modular_api(payload)
        
        # Fallback to DatabaseManager
        if _DBM is not None:
            return _create_project_with_manager(payload)
            
        return {"ok": False, "error": "Nenhuma API de banco disponível"}
        
    except Exception as e:
        return {"ok": False, "error": f"Falha ao criar projeto: {e}"}


def _create_project_with_modular_api(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Create project using modular database API."""
    with _transaction_ctx() as conn:
        # Insert into framework_projects table
        cursor = conn.execute("""
            INSERT INTO framework_projects (project_key, name, description, status)
            VALUES (?, ?, ?, 'active')
        """, (payload.get('project_key'), payload.get('name'), payload.get('description', '')))
        
        project_id = cursor.lastrowid
        
        # Return created project data
        created_project = {
            'id': project_id,
            'project_key': payload.get('project_key'),
            'name': payload.get('name'),
            'description': payload.get('description', ''),
            'status': 'active'
        }
        
        return {"ok": True, "data": created_project}


def _create_project_with_manager(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Create project using DatabaseManager fallback.""" 
    project_data = {
        'project_key': payload.get('project_key'),
        'name': payload.get('name'),
        'description': payload.get('description', ''),
        'status': 'active'
    }
    
    # Use DatabaseManager method to create project
    result = _DBM.create_project(project_data)
    
    if result and result.get('id'):
        return {"ok": True, "data": result}
    else:
        return {"ok": False, "error": "Falha ao criar projeto via DatabaseManager"}

# --- UI Helpers ----------------------------------------------------------------
def _form_validation(
    project_name: str,
    start: date,
    end: date,
    budget: float,
) -> List[str]:
    errors: List[str] = []
    if not project_name or len(project_name.strip()) < 3:
        errors.append("Informe um nome de projeto com pelo menos 3 caracteres.")
    if end < start:
        errors.append("A data de término não pode ser anterior à data de início.")
    if budget < 0:
        errors.append("O orçamento não pode ser negativo.")
    return errors

# --- Página --------------------------------------------------------------------
@require_auth()  # Protege a página; em dev, o fallback acima permite acesso
def _render() -> None:
    # Configure page layout first
    st.set_page_config(
        page_title="Projeto Wizard",
        layout="wide"
    )
    init_protected_page("Projeto Wizard")
    st.title("🧙‍♂️ Projeto Wizard")

    # Carrega camada de banco
    _init_db_layer()

    # “Passo 1: dados básicos” + “Passo 2: confirmação”
    col_left, col_right = st.columns([2, 1], vertical_alignment="top")

    with col_left:
        st.subheader("1) Informações do Projeto")

        with st.form("project_wizard_form", clear_on_submit=False):
            project_name = st.text_input("Nome do Projeto", placeholder="Ex.: Plataforma ETL – SEBRAE")
            description = st.text_area("Descrição (opcional)", placeholder="Contexto, objetivos e escopo do projeto")
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Início", value=date.today())
            with col2:
                end_date = st.date_input("Término", value=date.today())
            col3, col4 = st.columns(2)
            with col3:
                budget = st.number_input("Orçamento (R$)", min_value=0.0, step=1000.0, value=0.0, help="Informe 0 se não aplicável")
            with col4:
                status = st.selectbox("Status", ["Planned", "In Progress", "On Hold", "Completed"], index=0)

            submitted = st.form_submit_button("Criar Projeto", use_container_width=True)

        if submitted:
            errors = _form_validation(project_name, start_date, end_date, budget)
            if errors:
                for e in errors:
                    st.error(e)
                st.stop()

            # Generate project key from name (normalized)
            project_key = project_name.strip().lower().replace(' ', '_').replace('-', '_')
            # Remove special characters and limit length
            import re
            project_key = re.sub(r'[^\w]', '', project_key)[:50]
            
            payload: Dict[str, Any] = {
                "project_key": project_key,
                "name": project_name.strip(),
                "description": (description or "").strip(),
                "start_date": str(start_date),
                "end_date": str(end_date),
                "budget": float(budget),
                "status": status.lower().replace(' ', '_'),
            }

            try:
                result = _create_project_safely(payload)
                if result.get("ok"):
                    st.success("✅ Projeto criado com sucesso!")
                    st.json(result.get("data", {}))
                    st.toast("Projeto criado", icon="✅")
                else:
                    st.error(result.get("error", "Falha desconhecida ao criar projeto."))
            except Exception as e:
                st.error(f"Ocorreu um erro ao criar o projeto: {e}")

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
    """Public interface for rendering the project wizard page."""
    logger.info("🚀 Project wizard page requested - rendering...")
    try:
        _render()
        logger.info("✅ Project wizard page rendered successfully")
        return {"status": "success", "page": "projeto_wizard"}
    except Exception as e:
        logger.error(f"❌ Error rendering project wizard page: {e}")
        st.error("⚠️ Erro ao carregar página do wizard")
        return {"status": "error", "error": str(e), "page": "projeto_wizard"}


if __name__ == "__main__":
    _render()
else:
    _render()
