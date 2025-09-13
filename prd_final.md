# PRD Final — TDD‑Project: Migração para Arquitetura API‑First (Web + CLI)

## Visão do Produto

- O que é: Evolução do TDD‑Project (monolito Streamlit) para uma plataforma API‑First que serve múltiplos clientes (Web Nuxt 3, CLI e futuros mobile), mantendo lógica de negócio, desempenho (<10ms consultas) e postura de segurança A+.
- Problema: UI acoplada e com reload completo; pouca reutilização programática; integração externa limitada.
- Objetivo: API estável e versionada que habilita experiências modernas de Web/CLI, preservando o fluxo TDD e a inteligência de geração/ordenação de épicos.
- Premissas: manter serviços (Vision/Epic/AI), repositórios, esquema e migrações (Phase 5.1), pesos por projeto (História 3.2) e navegação em 4 macrofases (Roteiro→Capítulos→Histórias→Tarefas).

## Público‑Alvo e Personas

- Criador(a) de Projetos (PM/Founder): Cria projetos e aprova épicos rapidamente, com transparência.
- Power User (CLI): Automatiza wizard e rotinas; integra em pipelines.
- Analista/PO: Acompanha prioridades, pesos e progresso/topologia.
- Usuário(a) com TDAH: Fluxo previsível, feedback claro, continuidade e foco.

## Metas e KPIs

- Adoção: ≥70% dos fluxos via API (Web/CLI) nas 4 semanas pós‑MVP; ≥30% usam Web+CLI; ≥50% do time usa CLI semanalmente.
- Experiência: Tempo Roteiro→Capítulos ≤ 3–5 min (p95); CSAT wizard ≥ 4.5/5.
- Desempenho e Confiabilidade: p95 API < 200ms; consultas <10ms; ordenação topo ≤ 1ms (meta 0.19ms validada); 5xx < 0.3%/semana; disponibilidade ≥ 99.9%.
- Qualidade: Cobertura ≥ 95% no core e endpoints críticos; 0 vulnerabilidades críticas.
- Migração: Paridade funcional faseada; zero perda de dados; rollback testado e documentado.

## Escopo por Marcos (MVP e além)

### Marco 0 — Extração do Domínio (tdd_core)

- Entregáveis:
  - Módulo `tdd_core/` criado com camadas de domínio e aplicação: `domain/entities` (product_vision, project, epic), `value_objects` (priority, tdd_phase), `exceptions`, `application/services` (vision, epic, ai), `application/dto` e `validators` preservados.
  - Adapters/Interfaces: manter Streamlit funcional via adapter enquanto API/Web/CLI passam a consumir o núcleo.
  - Mapeadores explícitos entre DTOs do domínio e schemas de borda (request/response) para a API.
- Critérios de aceite:
  - Streamlit continua operando (somente leitura se necessário) usando o adapter do `tdd_core`.
  - Serviços isolados de frameworks; testes do domínio continuam passando.
  - Nenhuma regressão funcional nos fluxos Roteiro→Capítulos via núcleo.

### Marco 1 — Backend API v1 + CLI MVP

- API v1: Health/Status; Readiness; Métricas (`/healthz`, `/readyz`, `/metrics`). Projetos (CRUD essencial). Wizard (salvar visão; refino campo‑a‑campo sob comando do usuário com progresso via SSE; geração de épicos com ordenação topológica determinística). Prioridade por projeto (pesos normalizados, efeito no ordering).
- Acesso e segurança (nível produto): autenticação obrigatória para operações de escrita; política de versão (`/api/v1`) publicamente documentada; limites de uso e mensagens de erro consistentes.
- CLI: iniciar wizard; refinar campos; gerar/listar épicos; ajustar pesos; exportar resultados (JSON/YAML). Suporte a modos Online (API) e Offline (uso direto do `tdd_core` para produtividade local).
- Documentação: guia “comece aqui” (CLI e API) com exemplos de entrada/saída e termos do domínio.

Critérios de aceite
- Concluir Roteiro→Capítulos via CLI com resultados determinísticos; ajuste de pesos reflete imediatamente no ordering; OpenAPI válido com testes de contrato básicos; endpoints `/healthz`, `/readyz` e `/metrics` respondendo; documentação publicada.

### Marco 2 — Web v1 (Nuxt)

- Wizard Web: Roteiro→Capítulos com formulários verticais, salvamento de rascunho, revisão/aceite de épicos sugeridos por IA, feedback claro (“refinando…/pronto”) e progresso em tempo real via SSE quando aplicável. Interação focada: uma pergunta por vez na tela, sem distrações (TDAH).
- Projetos/Épicos: listas e detalhes; ordenação por prioridade; ajuste de pesos por projeto.
- UX: conteúdo completo sem truncamento; estados visuais por macrofase; acessibilidade básica; suporte a foco (TDAH).

Critérios de aceite
- Saídas Web equivalentes às da CLI para cenários equivalentes; rascunhos persistem; SSE de refinamento visível quando aplicável; CSAT ≥ 4.5 em teste interno (3–5 usuários).

### Marco 3 — Fluxos Completos e Consolidação

- Histórias→Tarefas com IA assistida e aprovação; persistência completa do progresso do wizard no banco; painel de métricas essenciais (tempo por fase, foco/interrupções básicas, progresso).
- Polimento UX: empty states, mensagens de erro amigáveis, ajuda contextual.

Critérios de aceite
- Cenário ponta‑a‑ponta (Roteiro→Tarefas) revisado; métricas básicas visíveis.

## Requisitos Funcionais

- Projetos: criar/editar/arquivar; visualizar status e metadados essenciais.
- Wizard (Roteiro→Capítulos): capturar visão; salvar rascunho; refinar campos com IA sob solicitação e com confirmação do usuário; gerar 3–7 épicos com dependências e ordenação determinística; aprovar/modificar sugestões.
  - Referências existentes (Streamlit):
    - Orquestração: `streamlit_extension/pages/projetos/projeto_wizard.py` (função `render_projeto_wizard_page`).
    - Estado global: `streamlit_extension/pages/projetos/project_wizard_state.py`.
    - Estado da visão: `streamlit_extension/pages/projetos/steps/_pv_state.py`.
    - UI do passo Visão: `streamlit_extension/pages/projetos/steps/product_vision_step/product_vision.py`.
    - Serviço de IA (refino de campo/visão): `streamlit_extension/services/vision_service.py` via `ServiceContainer.get_vision_refine_service()` (UnifiedVisionService).
- Épicos: exibir/ordenar; campos IA (complexidade, esforço, confiança, unblock) preservados; priorização por pesos por projeto (padrão 5:3:2:2; customizável).
  - Referências existentes:
    - Consultas/ordenação: `streamlit_extension/database/queries.py` e `utils/query_builder.py` (builders com estatísticas de épicos).
    - Serviço: `streamlit_extension/services/epic_service.py` (priorização e integração com pesos por projeto).
    - Pesos por projeto (História 3.2): `framework_priority_settings` (migração 011) e repositório em `services/priority_settings_repository.py`.
- Prioridade por Projeto: criar/atualizar pesos normalizados (≈1.0) com validação e efeito imediato no ordering.
- CLI: fluxo guiado; confirmações antes de ações destrutivas; exportação JSON/YAML; leitura/ajuste de pesos; modos Online (API) e Offline (núcleo `tdd_core`).
- Documentação: exemplos de payloads e respostas; glossário de termos (Roteiro, Capítulos, Histórias, Tarefas).

## Requisitos Não Funcionais

- Desempenho: p95 API < 200ms; consultas <10ms; algoritmo de ordenação O(V+E) ≤ 1ms.
- Confiabilidade: disponibilidade 99.9%; persistência confiável do wizard; sem perda de estado entre passos.
- Segurança (A+): entradas validadas/sanitizadas; proteção contra XSS/CSRF (quando aplicável); proibição de práticas inseguras (SQL sem bind, pickle, MD5, YAML inseguro); logs sem dados sensíveis.
- Determinismo: resultados reprodutíveis para mesma entrada/pesos; auditoria básica para conteúdo IA (ai_generated/ai_confidence).
- Observabilidade (produto): healthchecks públicos; readiness de dependências; métricas Prometheus expostas em `/metrics` (contadores e latências essenciais); trilhas do wizard (tempo por fase, passos concluídos); indicadores básicos de integridade.
- Terminologia: manter PT‑BR e consistência textual do framework universal.

## Experiência do Usuário

- Template Web: usaremos o template Nuxt “nuxt-shadcn-dashboard” (https://github.com/dianprata/nuxt-shadcn-dashboard). Componentes previstos: Cards (lista de projetos), DataTable/Tables (épicos), Forms/Inputs e Textarea do kit, Modal/Dialog (refino IA), Toast/Alerts, Breadcrumbs e Tabs para navegação em detalhes.
- Web: wizard em passos, apenas uma pergunta por vez na tela (clean e sem distrações), indicadores de progresso, estados salvos, feedback explícito em ações de IA (incluindo SSE quando aplicável); layouts limpos, ícone ET, textos claros; visibilidade total de conteúdo.
- CLI: prompts simples, confirmações claras, saída legível e exportável; poucos comandos para concluir; ajuda (`--help`) consistente.
- TDAH: minimizar bloqueios; permitir pausa/retomar; mensagens curtas e objetivas; previsibilidade nas transições.

### Mapa de Páginas (Web)

- Menu “Projetos” (rota `/projects`):
  - Lista em Cards com informações resumidas (nome, status, contagem de épicos, última atualização).
  - Ação “Novo Projeto” (ícone/botão) inicia o wizard (rota `/projects/new` ou `/wizard`).
- Página “Projeto” (rota `/projects/:id`):
  - Cabeçalho com título, badges de status e ações rápidas.
  - Seções/Tabs: “Capítulos (Épicos)”, “Prioridade (Pesos)”, “Configurações”.
  - Listas e detalhes usando componentes do template (Cards, Tables, Tabs, Breadcrumbs).
- Wizard (rota `/wizard` ou aninhado sob `/projects/new`):
  - Passos focados (uma pergunta por vez), barra de progresso, rascunho salvo, revisão/aceite de épicos.

## Autenticação e Acesso (escopo de produto)

- Web: autenticação do usuário (OAuth 2.0/OIDC com Google) para criação/edição; sessão segura; consentimento explícito para uso de IA quando aplicável (via fluxo de consentimento na UI). Usar bibliotecas do ecossistema Nuxt/Nitro adequadas ao template.
- CLI: mecanismo de autenticação para operações que alteram dados; Device Code Flow como padrão; armazenamento seguro de tokens no keyring do SO; uso permitido de modo leitura sem credenciais para listagens públicas (quando definido) e modo Offline para desenvolvimento.
- Integração: política de chaves/tokens para acesso programático; escopos mínimos necessários por caso de uso.

## Governança de API e Comunicação

- Versionamento: `/api/v1` com estabilidade contratual; ciclo de mudanças comunicado; notas de versão por marco; detecção de breaking changes (diff de OpenAPI) no pipeline.
- Contratos e clientes: geração automática de tipos/clients a partir do OpenAPI (TypeScript no build do frontend; Python client para CLI no CI), evitando drift entre clientes e servidor.
- Convivência e rollback: manter um branch de segurança do monolito; migração agressiva priorizando backend (código e API). O front antigo não permanece ativo em produção; rollback rápido para o branch salvo em caso de necessidade.
- Materiais: guia de migração, FAQ, sessões de demonstração; canal de suporte nas 2 semanas após Web v1.

## Dados, Migração e Continuidade

- Preservar o esquema e migrações da Phase 5.1 (56 colunas em `framework_epics`, dependências, triggers, índices) e História 3.2 (pesos por projeto com soma ≈1.0, unicidade por projeto, cascatas).
- Garantir: zero perda de dados; backups antes de marcos; verificação de migração (scripts já existentes) executada; rollback documentado.

## Riscos e Mitigações (Produto)

- Adoção abaixo do esperado: tutoriais curtos, exemplos prontos, onboarding “comece aqui”.
- Expectativa de paridade imediata: comunicar escopo por marcos e datas; priorizar Roteiro→Capítulos.
- Carga cognitiva do wizard: simplificar etapas; sugestões de IA com confirmação; feedback de qualidade/confiança.
- Terminologia e consistência: manter glossário PT‑BR; evitar renomeações desnecessárias.

## Roadmap e Cronograma (referência)

## Gates de Go/No‑Go

- Gate 1 (após Marco 0 — Domínio): `tdd_core` extraído sem breaking changes; Streamlit funcional via adapter; serviços isolados de framework; suíte do domínio passando.
- Gate 2 (após Marco 1 — API/CLI): API funcional com SQLite WAL; autenticação mínima ativa; OpenAPI válido e versionado; endpoints de saúde e métricas respondendo; testes de contrato básicos aprovados.
- Gate 3 (após Marco 2 — Web v1): Web e CLI consomem a API; SSE de refinamento funcionando; tipos gerados sem drift; equivalência Web↔CLI para cenários de referência.

- Semanas 1–2: Marco 1 (API v1 + CLI MVP; docs e exemplos).
- Semanas 3–4: Marco 2 (Web v1: Roteiro→Capítulos; pesos; listagens).
- Semanas 5–6: Marco 3 (Histórias→Tarefas; métricas básicas; polimento UX).

## Critérios de Encerramento da Migração

- Fluxo completo (Roteiro→Tarefas) disponível em Web e CLI com resultados determinísticos equivalentes.
- KPIs de adoção/experiência atingidos por 2 semanas consecutivas.
- Documentação atualizada; suporte estabilizado; plano de desligamento do monolito aprovado.

## Anexos e Referências

- CLAUDE.md (root): histórico de fases, requisitos de segurança e desempenho, migrações 2025‑09‑01→05, métricas de 0.19ms na ordenação, História 3.2 (pesos por projeto).
- streamlit_extension/CLAUDE.md: padrões de navegação, multi‑step wizard, serviços e práticas de segurança.
- tests/CLAUDE.md, migration/CLAUDE.md, scripts/CLAUDE.md: padrões de testes, verificação de migração e manutenção.

—

Nota: Este PRD consolida pontos do PRD Codex (objetivos, KPIs e marcos por fases) com itens enfatizados no PRD Claude (jornadas de uso, acesso/autenticação, excelência de experiência e governança de contratos), além de esclarecimentos dos arquivos de documentação do projeto (migrações, campos IA, pesos por projeto e padrões de segurança).
