🤖 CLAUDE.md - Streamlit Extension Module

Module: streamlit_extension/
Purpose: Enterprise Streamlit Application with Authentication & Security
Architecture: Multi-page application with service layer, authentication, and security stack
Last Updated: 2025-08-18

📱 Module Overview

Enterprise-grade Streamlit application featuring:

Authentication System: Complete user management with session handling

Advanced Security Stack: CSRF protection, XSS sanitization, enterprise rate limiting

Rate Limiting Layer: Multi-backend support (Memory/SQLite/Redis), métricas e proteção DoS

Service Layer: Clean architecture com 6 serviços de negócio

Multi-page Interface: Gestão de Client/Project/Epic/Task

Component System: Componentes de UI reutilizáveis e padrões de formulário

Terminologia: Streamlit não possui HTTP middleware nativo. Nesta documentação, “middleware” refere-se a decorators/camadas de serviço aplicadas ao fluxo da aplicação.

🏗️ Architecture Overview
Directory Structure
streamlit_extension/
├── auth/           # 🔐 Authentication system
├── components/     # 🧩 Reusable UI components
├── config/         # ⚙️ Configuration management
├── database/       # 📊 Modular database layer (6 specialized modules)
├── endpoints/      # 🏥 Health monitoring endpoints
├── middleware/     # 🛡️ Security/rate limiting (decorators/camadas)
├── pages/          # 📄 Streamlit pages
├── services/       # 🏢 Business logic layer
└── utils/          # 🔧 Utilities (database, security, validation)


Opcional (recomendado se o app crescer): adotar uma camada app/ (ex.: boot.py, router.py, layout.py, pages/) para isolar inicialização, roteamento e layout do entrypoint. Atualize exemplos de import conforme a estrutura final do repositório.

Key Patterns

Service Layer: Lógica de negócio separada da UI

Repository: Abstração de acesso a dados

Dependency Injection: ServiceContainer para baixo acoplamento

Result Pattern: Erros tipados sem exceções de controle de fluxo

Decorators/Camadas: Cross-cutting concerns (auth, rate-limiting, segurança)

🔐 Authentication (Google OAuth 2.0)
Core Components

GoogleOAuthManager: Fluxo completo OAuth 2.0 com Google

auth/__init__.py: Camada de compatibilidade (funções legadas)

Session Management: Armazenamento seguro de tokens, refresh automático

(Opcional) Google People API: Perfil e dados organizacionais

Integration Pattern (estilo funcional padronizado)
from streamlit_extension.utils.auth import (
    GoogleOAuthManager,
    render_login_page,
    get_authenticated_user,
    is_user_authenticated,
)
import streamlit as st

# Gate de autenticação
if not is_user_authenticated():
    render_login_page()
    st.stop()

current_user = get_authenticated_user()

# Backward compatibility (código existente continua funcionando)
from streamlit_extension.auth import auth_middleware, is_authenticated, get_current_user
current_user = auth_middleware()  # retorna o usuário autenticado

OAuth Features

Fluxo OAuth 2.0 com validação de CSRF state

People API (opcional) para enriquecer perfil

Sessões seguras e refresh tokens

Ambientes: dev e prod via configuração

Compatibilidade: API legada preservada

🛡️ Security Stack
CSRF Protection (exemplo corrigido)
import streamlit as st

# 1) Formulário com token de CSRF em session_state
with st.form("client_create_form"):
    csrf_form_id = "client_create_form"
    csrf_field = security_manager.get_csrf_form_field(csrf_form_id)

    if csrf_field and "csrf_token" not in st.session_state:
        st.session_state["csrf_token"] = csrf_field["token_value"]

    # Campos do formulário...
    name = st.text_input("Name")
    email = st.text_input("Email")

    submitted = st.form_submit_button("Submit")

# 2) Validação do token no submit
if submitted:
    csrf_valid, csrf_error = security_manager.require_csrf_protection(
        csrf_form_id,
        st.session_state.get("csrf_token", "")
    )
    if not csrf_valid:
        st.error(f"🔒 Security Error: {csrf_error}")
        st.stop()

    # prossiga com a lógica segura...

XSS Protection
safe_description = sanitize_display(user_input)
st.markdown(f"**Description:** {safe_description}")

security_valid, security_errors = validate_form(raw_data)
if not security_valid:
    for error in security_errors:
        st.error(f"🔒 Security: {error}")

SQL Injection (correção conceitual)

Valores → sempre parameter binding (?, %s etc.)

Identificadores (nomes de tabela/coluna) → nunca via binding; usar whitelist controlada.

# ✅ Correto (valores)
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))

# ✅ Correto (identificadores via whitelist)
TABLES = {"users", "projects"}
if table_name not in TABLES:
    raise ValueError("Invalid table name")
cursor.execute(f"DELETE FROM {table_name} WHERE id = ?", (row_id,))

🚦 Rate Limiting (camada de serviço)
Recursos

Backends: Memory (dev), SQLite (single-node), Redis (distribuído)

Algoritmos: fixed_window, sliding_window, token_bucket (com burst)

DoS protection: Sinais de anomalia independentes

TTL Cache: Limiter cache com coleta de idle

from streamlit_extension.middleware.rate_limiting.storage import (
    MemoryRateLimitStorage, SQLiteRateLimitStorage, RedisRateLimitStorage
)
from streamlit_extension.middleware.rate_limiting.middleware import RateLimitingMiddleware

storage = SQLiteRateLimitStorage(path="rate_limit.db")
middleware = RateLimitingMiddleware(config={
    "rate_limit_storage": storage,
    "ttl_seconds": 900,
})

Nota sobre “HTTP Headers”

Em Streamlit, não há resposta HTTP tradicional para páginas. Os “headers” de rate limit neste projeto são metadados internos (ex.: retorno de funções/camada de serviço, logs/telemetria) que você pode:

exibir na UI (st.caption),

enviar em respostas de APIs internas suas,

ou registrar em logs/metrics.

Eles não são injetados automaticamente como cabeçalhos HTTP no navegador pelo Streamlit.

Configuração por endpoint
ENDPOINT_LIMITS = {
    "/api/auth/login":  {"rate_limit": "5 per 5 minutes", "algorithm": "sliding_window"},
    "/api/bulk/upload": {"rate_limit": "10 per minute",    "algorithm": "token_bucket", "burst_capacity": 3},
    "/api/reports":     {"rate_limit": "100 per hour",     "algorithm": "fixed_window"},
}

DoS Protection
from streamlit_extension.utils.dos_protection import DoSProtectionSystem
dos = DoSProtectionSystem(threshold=100, window=60)
if dos.detect_attack(client_ip):
    # tomar ação
    ...

🏢 Service Layer
Service Container
from streamlit_extension.services import ServiceContainer
container = ServiceContainer()
client_service = container.get_client_service()
project_service = container.get_project_service()

ServiceResult (type hints explícitos)
result = client_service.get_all_clients()
if result.success:
    clients: list[ClientDTO] = result.data
else:
    for error in result.errors:
        st.error(f"Error: {error}")

Serviços Disponíveis

ClientService, ProjectService, EpicService, TaskService, AnalyticsService, TimerService

📊 Modular Database
Estrutura (refatoração 2025-08-17)
streamlit_extension/database/
├── __init__.py
├── connection.py   # conexão & transações
├── health.py       # health checks & otimizações
├── queries.py      # operações de alto nível
├── schema.py       # criação/migrações de schema
└── seed.py         # carga inicial

Dual API (sem breaking changes)
# Legado (preservado)
from streamlit_extension.utils.database import DatabaseManager
db = DatabaseManager()
conn = db.get_connection()
epics = db.get_epics()

# Modular (recomendado)
from streamlit_extension.database.connection import get_connection, transaction
from streamlit_extension.database.queries import list_epics, list_tasks

conn = get_connection()
with transaction():
    ...
epics = list_epics()

📄 Page Development Patterns
Estrutura padrão
from streamlit_extension.auth.middleware import init_protected_page
from streamlit_extension.utils.exception_handler import handle_streamlit_exceptions
from streamlit_extension.middleware.rate_limiting.core import check_rate_limit

@handle_streamlit_exceptions(show_error=True, attempt_recovery=True)
def render_page():
    current_user = init_protected_page("📄 Page Title")
    if not current_user:
        return

    ok, msg = check_rate_limit("page_load")
    if not ok:
        st.error(f"🚦 {msg}")
        return

    # conteúdo da página...

Form Standards

CSRF obrigatório

Rate limit em submissões

Sanitização (sanitize_display)

Validação (validate_*)

Mensagens de erro amigáveis

🧩 Components

form_components.py: StandardForm, ClientForm, ProjectForm

dashboard_widgets.py: métricas, charts, progress

pagination.py, sidebar.py

from streamlit_extension.components.form_components import ClientForm

client_form = ClientForm()
result = client_form.render(
    data=existing_data,
    validation_rules=custom_rules,
    security_enabled=True
)
if result.submitted and result.valid:
    safe_data = result.sanitized_data

🔧 Utils

Type Safety: from __future__ import annotations

Performance: regex pré-compilados em validações

Segurança: rotação CSRF e hashing configurável

Exports: __all__ explícitos

Logging: correlação e resiliência

DatabaseManager (exemplo seguro)
from streamlit_extension.utils.database import DatabaseManager

db = DatabaseManager(db_path)
clients = safe_streamlit_operation(
    db.get_clients,
    include_inactive=True,
    default_return=[],
    operation_name="get_clients"
)

🎨 UI/UX Standards

Navegação consistente (sidebar)

Progressive disclosure em formulários complexos

Indicadores de status com ícones/cores

Feedback responsivo (loading/sucesso/erro)

Acessibilidade (rótulos claros, contraste, teclado)

🔍 Development Guidelines
Organização

Single Responsibility por página

Error First nos fluxos

Security First consistente

Performance Aware (cache/memoization)

Testes

Auth (proteção de páginas)

CSRF/XSS

Integração entre services

UI básica (render/fluxos críticos)

Performance (Streamlit)
@st.cache_data
def expensive_calculation(params):
    return complex_calculation(params)

@st.cache_data
def cached_get_clients():
    return db_manager.get_clients()

🚀 Workflow
Novas Páginas

Criar arquivo em pages/

Estrutura padrão + auth

CSRF em todos os formulários

Validação + sanitização

Adicionar na navegação

Escrever testes de integração

Novos Serviços

Herdar de BaseService

Retornos com ServiceResult

Registrar em ServiceContainer

Unit tests isolados

Documentar API & padrões

Security Checklist (ampliado)

 @require_auth() aplicado

 Tokens CSRF em todos os forms

 Sanitização em toda saída de usuário

 Rate limiting por operação e export/bulk

 Mensagens não vazam dados sensíveis

 SQL com binding para valores (identificadores via whitelist)

 Logs sanitizados (sem PII/segredos)

 Limites de payload (tamanho de campos/linhas, uploads)

📊 Module Metrics (informativos)

Organização: 6 serviços • 10+ páginas • 20+ componentes • 30+ utils
Segurança: 100% páginas protegidas • 100% forms com CSRF • 240+ padrões de validação
Performance: pooling/otimização de consultas • caching em operações caras

🔗 See Also

Config: config/CLAUDE.md — Multi-ambiente, feature flags, segredos

Tests: tests/CLAUDE.md — Estratégia e suites

Monitoring: monitoring/CLAUDE.md — Observabilidade & alertas

Scripts: scripts/CLAUDE.md — Manutenção, análise, deploy

Core: duration_system/CLAUDE.md — Cálculo de duração e segurança

Enterprise Streamlit app com segurança, desempenho e mantenibilidade em primeiro lugar.