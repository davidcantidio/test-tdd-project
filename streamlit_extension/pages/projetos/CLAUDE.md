Visão Geral

Este módulo implementa o Wizard de Projetos, com foco na fase Product Vision.
Ele é parte da arquitetura do TDD Framework (Client → Project → Epic → Task).

Objetivos principais:

Permitir preenchimento e refinamento incremental da visão do produto.

Suportar dois modos de interação (Formulário e Passo a passo).

Oferecer integração com IA (Agno Agent ou outro refiner).

Otimizar UX para usuários com TDAH (micro-passos + resumo lateral).

Garantir persistência via repositório (in-memory ou DB).

🏗️ Arquitetura
Estrutura de Pastas
streamlit_extension/pages/
├── projects.py                   # Wrapper para compatibilidade Streamlit
├── projeto_wizard.py             # Wrapper para compatibilidade Streamlit
└── projetos/                     # Implementação real
    ├── controllers/              # ProductVisionController
    ├── domain/                   # Estados e validações (product_vision_state)
    ├── repositories/             # Repo abstrato + InMemory/DB impls
    ├── steps/                    # Etapas do wizard (ex.: product_vision_step)
    ├── projects.py               # Página principal de projetos
    ├── projeto_wizard.py         # Orquestração do wizard
    ├── project_wizard_state.py   # Estado global do wizard (multi-etapas)
    └── actions.py / state.py     # Lógicas auxiliares

Principais Componentes

ProductVisionController

Lida com validação, refinamento (via service) e persistência (repo).

Puro e testável (sem dependência de Streamlit).

Métodos principais:

refine_with_ai(payload)

save_draft(project_id, payload)

build_summary(payload)

can_refine(payload)

can_save(payload)

InMemoryProductVisionRepository

Mock simples para testes/UI.

Métodos: save_draft, get_by_project_id, delete_by_project_id.

product_vision_step.py

Renderiza UI da fase Product Vision.

Gerencia st.session_state["pv"], "pv_mode", "pv_step_idx".

Exibe Resumo lateral sempre atualizado.

projeto_wizard.py

Entry point da página.

Injeta controller + repo no step atual.

Facilita substituição do _NoopRefiner por serviço de IA real.

🎮 UX (Terceira Via)

Formulário completo: todos os campos de uma vez.

Passo a passo: 1 campo por vez, com navegação anterior/próximo.

Resumo lateral: sempre visível, mostra visão atual consolidada.

Botões de IA:

“✨ Refinar tudo” → aplica refinamento completo.

“✨ Refinar este” → aplica no campo atual (mas com merge seguro).

Salvar rascunho: mantém em memória ou envia para repo, somente quando o usuário desejar.

🚦 Checklist de Implementação

 Controller puro com testes unitários (Red → Green → Refactor).

 Repositório in-memory implementado.

 UI híbrida (form/steps) com resumo lateral.

 Botões de refinamento conectados ao controller.

 Persistência no DB real (via DatabaseProductVisionRepository).

 Página projeto.py (detalhes do projeto).

 Integração real com Agno Agent como serviço de IA.

 Testes de integração (UI + controller + repo DB).

🧪 Testes

Unitários:

Controller (test_product_vision_controller_refine.py, test_product_vision_controller_save.py).

Integração futura:

Simular fluxo wizard completo com repo de banco.

Cobertura:

pytest --cov=streamlit_extension/pages/projetos

🐛 Problemas Conhecidos

Erro SQLAlchemy: Attribute name 'metadata' is reserved

Corrigir renomeando a coluna/atributo metadata em ProductVisionORM para extra_metadata.

Bloqueia boot da página de projetos.

📝 Correções Realizadas (2025-08-26)

Navegação Streamlit corrigida
- ✅ Criado wrapper file `/pages/projects.py` para acessar `/projetos/projects.py`
- ✅ Mantido wrapper file `/pages/projeto_wizard.py` existente
- ✅ Navegação funcionando: Streamlit requer arquivos diretamente em `/pages/`

🚀 Próximos Passos

Finalizar UI Product Vision

Habilitar troca persistente entre modos (form <-> steps).

Garantir que campos persistam entre modos.

Persistência Real

Usar DatabaseProductVisionRepository ao invés de InMemory.

IA Real

Substituir _NoopRefiner por refiner integrado ao Agno Agent.

Wizard Completo

Criar subpastas steps/ para Epics, Backlog, etc.

Navegação entre macro-etapas do Scrum.

📊 Tracking desta Etapa (Product Vision)

Arquivos criados/modificados:

Criado: steps/product_vision_step.py

Modificado: projeto_wizard.py (injeção controller)

Modificado: repositories/product_vision_repository.py (repo in-memory atualizado)

Modificado: controllers/product_vision_controller.py (validação/refino)

Status: ✅ Controller e testes verdes, ✅ UI inicial, ⏳ Integração DB/Agno pendente.