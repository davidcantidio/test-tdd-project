"""
📄 Pages Package - Streamlit Extension (Optimized)

Sistema de navegação multi-páginas do TDD Framework:
- Analytics, Kanban, Gantt, Timer, Settings, Clients, Projects, Health, Projeto Wizard
- Página de login isolada (oculta na navegação principal)
- Registro tipado com validações leves e proteção de execução

Notas:
- Mantém compatibilidade de nomes exportados.
- Usa tipagem forte e dataclass para reduzir erros sutis.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Callable, Dict, Iterable, List, Optional, Tuple

from streamlit_extension.utils.exception_handler import (
    streamlit_error_boundary,
    safe_streamlit_operation,
)

RenderFunc = Callable[[], Optional[object]]  # páginas podem retornar dict/None


# =============================================================================
# Helpers de import dinâmico (com proteção)
# =============================================================================

def _import_page(module_name: str, func_name: str) -> Tuple[Optional[RenderFunc], bool]:
    """Importa módulo/func dinamicamente com proteção e retorna (callable, disponível)."""
    module = safe_streamlit_operation(
        import_module,
        f"{__name__}.{module_name}",
        default_return=None,
        operation_name=f"import_{module_name}",
    )
    if module and hasattr(module, func_name):
        return getattr(module, func_name), True
    return None, False


# =============================================================================
# Import das páginas (lazy-friendly via safe_streamlit_operation)
# =============================================================================

render_analytics_page, ANALYTICS_AVAILABLE = _import_page("analytics", "render_analytics_page")
render_kanban_page, KANBAN_AVAILABLE = _import_page("kanban", "render_kanban_page")
render_gantt_page, GANTT_AVAILABLE = _import_page("gantt", "render_gantt_page")
render_timer_page, TIMER_AVAILABLE = _import_page("timer", "render_timer_page")
render_settings_page, SETTINGS_AVAILABLE = _import_page("settings", "render_settings_page")
render_clients_page, CLIENTS_AVAILABLE = _import_page("clients", "render_clients_page")
render_projects_page, PROJECTS_AVAILABLE = _import_page("projects", "render_projects_page")
render_health_dashboard, HEALTH_AVAILABLE = _import_page("health", "render_health_dashboard")
render_projeto_wizard_page, PROJETO_WIZARD_AVAILABLE = _import_page("projeto_wizard", "render_projeto_wizard_page")


def _import_auth_page() -> Tuple[Optional[RenderFunc], bool]:
    try:
        from streamlit_extension.auth.login_page import render_login_page  # type: ignore
        return render_login_page, True
    except Exception:
        return None, False


render_login_page, LOGIN_AVAILABLE = _import_auth_page()


# =============================================================================
# Definição tipada do registro de páginas
# =============================================================================

@dataclass(frozen=True)
class PageSpec:
    id: str
    title: str
    icon: str
    description: str
    render_func: Optional[RenderFunc]
    available: bool
    show_in_nav: bool = True  # login fica False

    def is_navigable(self) -> bool:
        return self.available and self.show_in_nav


def _noop_render() -> dict:
    """Placeholder para páginas que não têm função de render específica (ex.: dashboard)."""
    return {"status": "ok", "message": "Dashboard renderizado pelo app principal."}


# Registro canônico (ordem de declaração = ordem de navegação)
PAGE_REGISTRY: Dict[str, PageSpec] = {
    "login": PageSpec(
        id="login",
        title="🔐 Login",
        icon="🔐",
        description="Authentication and user login",
        render_func=render_login_page,
        available=LOGIN_AVAILABLE,
        show_in_nav=False,  # nunca em navegação principal
    ),
    "dashboard": PageSpec(
        id="dashboard",
        title="🏠 Dashboard",
        icon="🏠",
        description="Main overview with key metrics",
        render_func=_noop_render,   # evita erro e mantém contrato
        available=True,
        show_in_nav=True,
    ),
    "analytics": PageSpec(
        id="analytics",
        title="📈 Analytics",
        icon="📈",
        description="Productivity analytics and insights",
        render_func=render_analytics_page,
        available=ANALYTICS_AVAILABLE,
    ),
    "kanban": PageSpec(
        id="kanban",
        title="📋 Kanban Board",
        icon="📋",
        description="Interactive task management",
        render_func=render_kanban_page,
        available=KANBAN_AVAILABLE,
    ),
    "gantt": PageSpec(
        id="gantt",
        title="📊 Gantt Chart",
        icon="📊",
        description="Project timeline visualization",
        render_func=render_gantt_page,
        available=GANTT_AVAILABLE,
    ),
    "timer": PageSpec(
        id="timer",
        title="⏱️ Focus Timer",
        icon="⏱️",
        description="TDAH-optimized focus sessions",
        render_func=render_timer_page,
        available=TIMER_AVAILABLE,
    ),
    "settings": PageSpec(
        id="settings",
        title="⚙️ Settings",
        icon="⚙️",
        description="Configuration and preferences",
        render_func=render_settings_page,
        available=SETTINGS_AVAILABLE,
    ),
    "clients": PageSpec(
        id="clients",
        title="👥 Clients",
        icon="👥",
        description="Client management and contacts",
        render_func=render_clients_page,
        available=CLIENTS_AVAILABLE,
    ),
    "projects": PageSpec(
        id="projects",
        title="📁 Projects",
        icon="📁",
        description="Project management and tracking",
        render_func=render_projects_page,
        available=PROJECTS_AVAILABLE,
    ),
    "projeto_wizard": PageSpec(
        id="projeto_wizard",
        title="🚀 Criar Projeto",
        icon="🚀",
        description="Wizard completo com IA: Visão → Épicos → Stories → Tasks",
        render_func=render_projeto_wizard_page,
        available=PROJETO_WIZARD_AVAILABLE,
    ),
    "health": PageSpec(
        id="health",
        title="🏥 Health",
        icon="🏥",
        description="System health monitoring and diagnostics",
        render_func=render_health_dashboard,
        available=HEALTH_AVAILABLE,
    ),
}


# =============================================================================
# API pública utilitária
# =============================================================================

def get_page_specs() -> Dict[str, PageSpec]:
    """Retorna o registry completo (imutável por contrato)."""
    return PAGE_REGISTRY


def get_available_pages(show_all: bool = False) -> Dict[str, PageSpec]:
    """
    Páginas disponíveis para navegação, preservando a ordem do registro.

    - show_all=False: retorna apenas páginas `is_navigable()`.
    - show_all=True: retorna todas as páginas `available=True` (login continua oculto por padrão).
    """
    out: Dict[str, PageSpec] = {}
    for pid, spec in PAGE_REGISTRY.items():
        if show_all:
            if spec.available:
                out[pid] = spec
        else:
            if spec.is_navigable():
                out[pid] = spec
    return out


def list_pages_for_nav() -> List[Tuple[str, str]]:
    """
    Lista amigável para sidebar/menu:
    [(page_id, "icon title"), ...] somente para páginas navegáveis.
    """
    pages = []
    for pid, spec in get_available_pages(show_all=False).items():
        pages.append((pid, f"{spec.icon} {spec.title}"))
    return pages


def resolve_page_id(raw: str) -> Optional[str]:
    """
    Resolve um identificador de página de forma case-insensitive e tolerante a variações:
    - id exato (ex.: 'analytics')
    - título (sem emoji), ex.: 'Analytics'
    - ícone + título, ex.: '📈 Analytics'
    - apelido com caixa variada, ex.: 'KANBAN'
    """
    if not raw:
        return None
    key = raw.strip().lower()

    if key in PAGE_REGISTRY:
        return key

    for pid, spec in PAGE_REGISTRY.items():
        title_clean = spec.title
        # remove emoji inicial (se houver) para comparação
        if title_clean and len(title_clean) > 1 and title_clean[0] in spec.icon:
            title_clean = title_clean[2:].strip()  # "📈 Analytics" -> "Analytics"
        candidates = {
            spec.title.lower(),
            title_clean.lower(),
            f"{spec.icon} {title_clean}".lower(),
            pid.lower(),
        }
        if key in candidates:
            return pid
    return None


def render_page(page_id: str):
    """
    Renderiza uma página por ID com proteção de erro amigável.
    Retorna o resultado do renderizador, quando houver.
    """
    resolved = resolve_page_id(page_id) or page_id
    spec = PAGE_REGISTRY.get(resolved)
    if spec is None:
        return {"error": f"Unknown page: {page_id}"}

    if not spec.available:
        return {"error": f"Page '{resolved}' is not available"}

    if spec.render_func is None:
        # Por contrato, sempre teremos algo — dashboard usa _noop_render
        return {"error": f"No render function for page: {resolved}"}

    # Protege UX: se a página quebrar, o app segue vivo
    with streamlit_error_boundary(f"Error rendering page '{resolved}'"):
        return spec.render_func()


# =============================================================================
# Back-compat: exporta símbolos esperados pelo restante do projeto
# =============================================================================

__all__ = [
    # render functions
    "render_analytics_page",
    "render_kanban_page",
    "render_gantt_page",
    "render_timer_page",
    "render_settings_page",
    "render_clients_page",
    "render_projects_page",
    "render_health_dashboard",
    "render_projeto_wizard_page",
    "render_login_page",

    # registry & flags
    "PAGE_REGISTRY",
    "get_available_pages",
    "render_page",
    "ANALYTICS_AVAILABLE",
    "KANBAN_AVAILABLE",
    "GANTT_AVAILABLE",
    "TIMER_AVAILABLE",
    "SETTINGS_AVAILABLE",
    "CLIENTS_AVAILABLE",
    "PROJECTS_AVAILABLE",
    "HEALTH_AVAILABLE",
    "PROJETO_WIZARD_AVAILABLE",
    "LOGIN_AVAILABLE",

    # utilitários extras
    "list_pages_for_nav",
    "get_page_specs",
    "resolve_page_id",
]
