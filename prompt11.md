# PROMPT 11: Function Complexity Reduction

## 🎯 OBJETIVO
Refatorar funções complexas para resolver item do report.md: "Functions exceed 100 lines (e.g., render_clients_page) leading to high cyclomatic complexity."

## 📁 ARQUIVOS ALVO (ESPECÍFICOS - SEM INTERSEÇÃO)
- `streamlit_extension/pages/clients.py` (REFATORAÇÃO ESPECÍFICA)
- `streamlit_extension/pages/projects.py` (REFATORAÇÃO ESPECÍFICA)

## 🚀 DELIVERABLES

### 1. Client Page Refactoring (`streamlit_extension/pages/clients.py`)

#### Análise Atual:
- `render_clients_page()`: >150 linhas
- `render_create_client_form()`: >100 linhas
- Alta complexidade ciclomática
- Lógica misturada: UI + business + data

#### Refatoração Target:

```python
"""
👥 Client Management Page - Refactored Architecture

Reduced from >150 lines to <50 lines per function:
- Separation of concerns
- Reusable components
- Reduced cyclomatic complexity
- Clear single responsibility
"""

# MAIN PAGE FUNCTION (TARGET: <50 lines)
def render_clients_page():
    """Render main clients management page - SIMPLIFIED."""
    if not STREAMLIT_AVAILABLE:
        return {"error": "Streamlit not available"}
    
    # Setup and authentication
    setup_result = _setup_page_infrastructure()
    if setup_result.get("error"):
        return setup_result
    
    db_manager = setup_result["db_manager"]
    
    # Render page sections
    _render_page_header()
    _render_search_and_filters()
    _render_create_client_section(db_manager)
    _render_clients_list(db_manager)
    
    return {"status": "success"}

# COMPONENT FUNCTIONS (TARGET: <30 lines each)
def _setup_page_infrastructure():
    """Setup page infrastructure and authentication."""
    
def _render_page_header():
    """Render page title and description."""
    
def _render_search_and_filters():
    """Render search and filter controls."""
    
def _render_create_client_section(db_manager):
    """Render client creation form section."""
    
def _render_clients_list(db_manager):
    """Render paginated clients list."""
    
def _render_client_card(client, db_manager):
    """Render individual client card."""
    
def _render_client_actions(client, db_manager):
    """Render client action buttons."""
    
def _handle_client_creation(db_manager, form_data):
    """Handle client creation logic."""
    
def _handle_client_update(db_manager, client_id, form_data):
    """Handle client update logic."""
    
def _handle_client_deletion(db_manager, client_id):
    """Handle client deletion logic."""

# FORM COMPONENTS (TARGET: <40 lines each)
def _render_client_form_fields(client_data=None):
    """Render client form fields with validation."""
    
def _validate_client_form_data(form_data):
    """Validate client form data."""
    
def _render_client_filters():
    """Render client filtering controls."""
```

### 2. Project Page Refactoring (`streamlit_extension/pages/projects.py`)

#### Análise Atual:
- `render_projects_page()`: >140 linhas
- `render_create_project_form()`: >90 linhas
- Lógica duplicada com clients.py
- Business logic misturada com UI

#### Refatoração Target:

```python
"""
📁 Project Management Page - Refactored Architecture

Reduced from >140 lines to <50 lines per function:
- DRY principle applied
- Shared components extracted
- Business logic separated
- Clear component hierarchy
"""

# MAIN PAGE FUNCTION (TARGET: <50 lines)
def render_projects_page():
    """Render main projects management page - SIMPLIFIED."""
    if not STREAMLIT_AVAILABLE:
        return {"error": "Streamlit not available"}
    
    # Setup and authentication
    setup_result = _setup_page_infrastructure()
    if setup_result.get("error"):
        return setup_result
    
    db_manager = setup_result["db_manager"]
    
    # Render page sections
    _render_page_header()
    _render_search_and_filters()
    _render_create_project_section(db_manager)
    _render_projects_list(db_manager)
    
    return {"status": "success"}

# COMPONENT FUNCTIONS (TARGET: <30 lines each)
def _setup_page_infrastructure():
    """Setup page infrastructure and authentication."""
    
def _render_page_header():
    """Render page title and description."""
    
def _render_search_and_filters():
    """Render search and filter controls."""
    
def _render_create_project_section(db_manager):
    """Render project creation form section."""
    
def _render_projects_list(db_manager):
    """Render paginated projects list."""
    
def _render_project_card(project, db_manager):
    """Render individual project card."""
    
def _render_project_actions(project, db_manager):
    """Render project action buttons."""
    
def _render_project_metrics(project):
    """Render project metrics and progress."""
    
def _handle_project_creation(db_manager, form_data):
    """Handle project creation logic."""
    
def _handle_project_update(db_manager, project_id, form_data):
    """Handle project update logic."""
    
def _handle_project_deletion(db_manager, project_id):
    """Handle project deletion logic."""

# FORM COMPONENTS (TARGET: <40 lines each)
def _render_project_form_fields(project_data=None, clients=None):
    """Render project form fields with validation."""
    
def _validate_project_form_data(form_data):
    """Validate project form data."""
    
def _render_project_filters():
    """Render project filtering controls."""
    
def _load_client_options(db_manager):
    """Load client options for project form."""
```

### 3. Shared Components Module

#### `streamlit_extension/components/crud_components.py` (NOVO)
```python
"""
🔧 Shared CRUD Components

Extracts common patterns from clients.py and projects.py:
- Reusable form components
- Common validation logic
- Shared UI patterns
- Standard error handling
"""

class CRUDPageRenderer:
    """Base class for CRUD page rendering."""
    
    def __init__(self, entity_type, db_manager):
        self.entity_type = entity_type
        self.db_manager = db_manager
    
    def render_standard_page_layout(self):
        """Render standard CRUD page layout."""
        
    def render_search_section(self, search_config):
        """Render configurable search section."""
        
    def render_filter_section(self, filter_config):
        """Render configurable filter section."""
        
    def render_entity_list(self, entities, render_card_func):
        """Render paginated entity list."""
        
    def render_pagination_controls(self, pagination_info):
        """Render pagination controls."""

class FormRenderer:
    """Reusable form rendering components."""
    
    @staticmethod
    def render_text_field(label, key, value=None, **kwargs):
        """Render standardized text field."""
        
    @staticmethod
    def render_select_field(label, key, options, value=None, **kwargs):
        """Render standardized select field."""
        
    @staticmethod
    def render_form_actions(submit_label="Save", cancel_label="Cancel"):
        """Render standardized form action buttons."""
        
    @staticmethod
    def render_validation_errors(errors):
        """Render validation error messages."""

class ActionHandler:
    """Handles common CRUD actions."""
    
    def __init__(self, db_manager, entity_type):
        self.db_manager = db_manager
        self.entity_type = entity_type
    
    def handle_create_action(self, form_data, validation_func):
        """Handle entity creation with validation."""
        
    def handle_update_action(self, entity_id, form_data, validation_func):
        """Handle entity update with validation."""
        
    def handle_delete_action(self, entity_id, confirmation_required=True):
        """Handle entity deletion with confirmation."""
```

## 🔧 REFACTORING STRATEGY

### Function Size Targets:
- **Main page functions**: <50 lines
- **Component functions**: <30 lines  
- **Form functions**: <40 lines
- **Handler functions**: <25 lines

### Complexity Reduction:
- **Cyclomatic complexity**: <10 per function
- **Nesting levels**: <4 levels deep
- **Single responsibility**: 1 clear purpose per function
- **DRY principle**: Extract common patterns

### Quality Metrics:
- **Reusability**: 80%+ code reuse between pages
- **Testability**: Each function independently testable
- **Maintainability**: Clear separation of concerns
- **Readability**: Self-documenting function names

## 📊 SUCCESS CRITERIA

- [ ] `render_clients_page()` reduzida para <50 linhas
- [ ] `render_projects_page()` reduzida para <50 linhas
- [ ] Componentes reutilizáveis extraídos
- [ ] Complexidade ciclomática <10 por função
- [ ] 80%+ código compartilhado entre páginas
- [ ] Business logic separada da UI
- [ ] Funções independently testáveis
- [ ] Documentação clara de responsabilidades