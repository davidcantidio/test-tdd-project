Você está colaborando no projeto Streamlit localizado em /workspace/test-tdd-project. A arquitetura relevante segue o padrão abaixo:

Modelos SQLAlchemy centralizados em streamlit_extension/database/models.py, definidos após o bloco if SQLALCHEMY_AVAILABLE: e seguindo a convenção de docstrings com emojis e fallback de importações

Operações de banco via DatabaseManager em streamlit_extension/utils/database.py, onde já existem métodos como get_clients, get_projects e create_client/create_project, com uso de cache_database_query e invalidate_cache_on_change

Registro de páginas na UI em streamlit_extension/pages/__init__.py, utilizando o dicionário PAGE_REGISTRY para navegação

A página principal streamlit_extension/streamlit_app.py contém botões de navegação rápida através de QuickActionButton.render

Objetivo
Adicionar CRUD completo de clientes e projetos, com relacionamento projetos.cliente_id -> clientes.id, validações básicas e interface Streamlit integrada ao estilo existente.

Instruções detalhadas
Modelos SQLAlchemy

Arquivo: streamlit_extension/database/models.py

Dentro do bloco if SQLALCHEMY_AVAILABLE:, criar classes Client (framework_clients) e Project (framework_projects) com:

Campos principais utilizados hoje (client_key, name, primary_contact_email, status, created_at, updated_at, deleted_at etc.)

Project deve ter client_id como ForeignKey("framework_clients.id")

Relationships: Client.projects = relationship("Project", back_populates="client") e Project.client = relationship("Client", back_populates="projects")

Docstrings explicativas com emojis seguindo o padrão do arquivo

Validações

Arquivo: streamlit_extension/utils/validators.py

Criar funções validate_client_data(client: Dict[str, Any]) e validate_project_data(project: Dict[str, Any])

validate_client_data: obrigar client_key, name, primary_contact_email; validar formato de e‑mail via regex; checar unicidade do e‑mail consultando DatabaseManager.get_clients

validate_project_data: exigir client_id, project_key, name, status, planned_start_date, planned_end_date; restringir status a ["planning","in_progress","completed","on_hold","cancelled"]; garantir planned_end_date >= planned_start_date

Retornar (is_valid, errors) como nas funções existentes

Operações CRUD no DatabaseManager

Arquivo: streamlit_extension/utils/database.py

Complementar get_clients e get_projects com parâmetros page: int = 1, page_size: int = 20 e filtros por name/status (clientes) e status/client_id (projetos). Implementar LIMIT/OFFSET.

Adicionar métodos:

update_client(client_id, **fields) e delete_client(client_id, soft_delete=True)

update_project(project_id, **fields) e delete_project(project_id, soft_delete=True)

Todos devem chamar os validadores antes de executar, usar invalidate_cache_on_change para invalidar caches relevantes e seguir o padrão de fallback SQLAlchemy/sqlite já existente (commit e tratamento de exceções com st.error)

Páginas Streamlit

Criar streamlit_extension/pages/clients.py e streamlit_extension/pages/projects.py

Cada página deve:

Ter função render_clients_page() ou render_projects_page() com docstring no estilo atual

Exibir listagem paginada (st.table ou st.dataframe), filtros básicos (nome/status, cliente/status), botões de paginação

Formulário para criar/editar registros usando st.form

Botões de editar/excluir por linha; mensagens claras via st.success, st.error, st.warning

Utilizar os métodos do DatabaseManager e os validadores antes de qualquer operação

Registro de páginas

Arquivo: streamlit_extension/pages/__init__.py

Adicionar entradas em PAGE_REGISTRY para "clients" e "projects" com títulos/ícones (por exemplo, "👥 Clients" e "📁 Projects") e render_func apontando para as funções criadas

Exportar as novas funções em __all__ se apropriado

Navegação na app principal

Arquivo: streamlit_extension/streamlit_app.py

Na seção de Quick Actions (linhas ~493-541), incluir botões adicionais:

"Clients" que define st.session_state.current_page = "Clients"

"Projects" que define st.session_state.current_page = "Projects"

Garantir que current_page seja tratado no fluxo principal para carregar as novas páginas (usar pages.PAGE_REGISTRY ou lógica existente)

Geral

Nenhuma dependência nova além do que já existe

Seguir convenções de nomenclatura, importações condicionais e docstrings com emojis

CRUD completo: criar, listar (com paginação/filtros), editar e excluir

Mensagens de UI usando st.success, st.error, st.warning

Manter integridade do banco (FK project.client_id → client.id)

Responda com o código completo para cada arquivo modificado/criado, pronto para uso imediato.

