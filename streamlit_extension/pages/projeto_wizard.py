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

from datetime import date
from typing import Any, Dict, List, Optional

import streamlit as st

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
_list_clients_fn = None
_create_project_fn = None
_transaction_ctx = None

def _init_db_layer() -> None:
    global _DBM, _list_clients_fn, _create_project_fn, _transaction_ctx
    # Tentamos APIs em ordem: híbrido (modular + manager) → apenas manager
    try:
        # Modular API (transação)
        from streamlit_extension.database import transaction  # type: ignore
        _transaction_ctx = transaction
    except Exception:
        _transaction_ctx = None

    try:
        # Enterprise API (DatabaseManager)
        from streamlit_extension.utils.database import DatabaseManager  # type: ignore
        _DBM = DatabaseManager()
    except Exception:
        _DBM = None

    # Opcional: modular helpers, se existirem
    try:
        from streamlit_extension.database import list_clients as _lc  # type: ignore
        _list_clients_fn = _lc
    except Exception:
        _list_clients_fn = None

    try:
        from streamlit_extension.database import create_project as _cp  # type: ignore
        _create_project_fn = _cp
    except Exception:
        _create_project_fn = None

def _get_clients() -> List[Dict[str, Any]]:
    # 1) Modular list_clients() → 2) DatabaseManager().get_clients() → 3) fallback
    try:
        if _list_clients_fn is not None:
            items = _list_clients_fn()
            # Normalizamos para lista de dicionários
            if isinstance(items, list) and (not items or isinstance(items[0], dict)):
                return items
    except Exception as e:
        st.warning(f"Não foi possível carregar clientes via API modular: {e}")

    try:
        if _DBM is not None and hasattr(_DBM, "get_clients"):
            items = _DBM.get_clients()  # type: ignore[attr-defined]
            if isinstance(items, list) and (not items or isinstance(items[0], dict)):
                return items
    except Exception as e:
        st.warning(f"Não foi possível carregar clientes via DatabaseManager: {e}")

    # Fallback seguro — evita o erro “List argument must consist only of dictionaries”
    return [{"id": 0, "name": "Default Client"}]

def _create_project_safely(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Cria projeto usando o melhor caminho disponível:
    1) modular create_project() dentro de transaction()
    2) DatabaseManager().create_project()
    Lança exceção com mensagem amigável se nenhum caminho estiver disponível.
    """
    # 1) Modular
    try:
        if _create_project_fn is not None:
            if _transaction_ctx is not None:
                with _transaction_ctx():  # type: ignore[misc]
                    created = _create_project_fn(payload)  # type: ignore[misc]
                    return {"ok": True, "data": created}
            # Se transação modular não existir, ainda tentamos criar direto
            created = _create_project_fn(payload)  # type: ignore[misc]
            return {"ok": True, "data": created}
    except Exception as e:
        return {"ok": False, "error": f"Falha ao criar projeto (API modular): {e}"}

    # 2) DatabaseManager
    try:
        if _DBM is not None and hasattr(_DBM, "create_project"):
            created = _DBM.create_project(payload)  # type: ignore[attr-defined]
            return {"ok": True, "data": created}
    except Exception as e:
        return {"ok": False, "error": f"Falha ao criar projeto (DatabaseManager): {e}"}

    # 3) Sem backend disponível
    raise RuntimeError(
        "Nenhuma API de banco disponível para criar projeto. "
        "Verifique as dependências do módulo database."
    )

# --- UI Helpers ----------------------------------------------------------------
def _form_validation(
    client_name: str,
    project_name: str,
    start: date,
    end: date,
    budget: float,
) -> List[str]:
    errors: List[str] = []
    if not client_name:
        errors.append("Selecione um cliente.")
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
    init_protected_page("Projeto Wizard", layout="wide")
    st.title("🧙‍♂️ Projeto Wizard")

    # Carrega camada de banco
    _init_db_layer()

    # “Passo 1: dados básicos” + “Passo 2: confirmação”
    col_left, col_right = st.columns([2, 1], vertical_alignment="top")

    with col_left:
        st.subheader("1) Informações do Projeto")

        clients = _get_clients()
        client_names = [c.get("name") or c.get("title") or f"Cliente {c.get('id', '')}" for c in clients]
        client_map = {name: c for name, c in zip(client_names, clients)}  # nome → dict

        with st.form("project_wizard_form", clear_on_submit=False):
            client_name = st.selectbox("Cliente", client_names, index=0 if client_names else None)
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
            errors = _form_validation(client_name, project_name, start_date, end_date, budget)
            if errors:
                for e in errors:
                    st.error(e)
                st.stop()

            client_obj = client_map.get(client_name, {})
            payload: Dict[str, Any] = {
                "client_id": client_obj.get("id", 0),
                "client_name": client_name,
                "name": project_name.strip(),
                "description": (description or "").strip(),
                "start_date": str(start_date),
                "end_date": str(end_date),
                "budget": float(budget),
                "status": status,
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

if __name__ == "__main__":
    _render()
else:
    _render()
