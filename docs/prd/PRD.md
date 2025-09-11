# Product Requirements Document (PRD)

Título: Framework Streamlit para Produtividade TDAH (Template GitHub Base)
Versão: 1.0 (framework pessoal)
Data: 2025‑09‑09
Status: Em vigor (template reutilizável para novos projetos)

Resumo executivo
- **Objetivo:** Framework pessoal Streamlit otimizado para pessoas com TDAH, servindo como template base para todos os projetos futuros. Oferece wizard estruturado em 4 macro fases (Roteiro → Capítulos → Histórias → Tarefas) com IA para geração/refino e interface TDAH-friendly.
- **Benefício:** Reduz sobrecarga cognitiva através de estrutura previsível, progresso visual claro e gestão de foco. Padroniza captura de visão, priorização baseada em valor e execução com rastreabilidade adaptada para características de TDAH.
- **Pilares Técnicos:** Clean Architecture + Repository Pattern, TDD 98%+ cobertura, SQLite definitivo, IU otimizada para foco e produtividade, performance <1–10ms por consulta.
- **Uso como Template:** Clone este repositório como base para novos projetos Streamlit, aproveitando toda arquitetura e padrões já implementados.

1. Contexto e Motivação

### Problema Central: Desafios de TDAH na Gestão de Projetos
- **Sobrecarga Cognitiva:** Pessoas com TDAH enfrentam dificuldade em organizar projetos complexos sem estrutura clara, resultando em procrastinação e projetos abandonados
- **Falta de Progresso Visual:** Ferramentas existentes não oferecem feedback visual adequado sobre o progresso, essencial para manter motivação em cérebros com TDAH
- **Decisões de Priorização:** Dificuldade em determinar "por onde começar" devido à paralisia da escolha e falta de critérios objetivos de priorização
- **Perda de Contexto:** Interrupções frequentes (característica do TDAH) resultam em perda de contexto do projeto, exigindo reprocessamento mental custoso
- **Ferramentas Inadequadas:** Soluções existentes são ou muito complexas (causam overwhelm) ou muito simples (não estruturam adequadamente)

### Oportunidade: Framework TDAH-Optimized
- **Estrutura Previsível:** Wizard em 4 macro fases que sempre seguem a mesma sequência (Roteiro → Capítulos → Histórias → Tarefas), reduzindo carga cognitiva de decisão
- **IA como Assistente Cognitivo:** Refinamento automático de ideias e geração de estrutura, reduzindo o esforço mental de "começar do zero"
- **Priorização Automatizada:** Algoritmo determinístico de ordenação topológica que remove a paralisia da escolha
- **Template Reutilizável:** Base para todos os projetos futuros, criando consistência e familiaridade (essencial para TDAH)
- **Gamificação Integrada:** Sistema de achievements e tracking de foco para manter engajamento

### Estado Atual do Framework
- **Técnico:** Clean Architecture implementada, TDD 98%+ cobertura, IA pipeline funcional
- **Funcional:** Roteiro + Capítulos operacionais, Histórias + Tarefas em desenvolvimento
- **Banco de Dados:** Migrações 2025‑09‑01..05 aplicadas, schema otimizado para performance
- **Referências:** CLAUDE.md (documentação técnica), DTOs implementados (ProductVisionDTO/EpicSuggestionDTO)

2. Objetivos (SMART) - Foco em Produtividade TDAH

### Objetivos de Produtividade Pessoal
- **O1 — Redução de Procrastinação:** 90% dos projetos criados com o framework completam pelo menos a fase Roteiro (vs. histórico de 30% de projetos iniciados abandonados sem estrutura)
- **O2 — Velocidade de Estruturação:** Completar Roteiro → Capítulos em <20 minutos com IA, reduzindo em 75% o tempo típico de planejamento inicial de projetos
- **O3 — Consistência de Uso:** Usar o framework como template base em 100% dos novos projetos Streamlit, criando padrão pessoal de desenvolvimento
- **O4 — Gestão de Foco:** Sistema de tracking de interruções e foco registra dados objetivos para melhoria contínua da produtividade pessoal

### Objetivos Técnicos (Manutenção do Framework)
- **O5 — Performance:** Consultas principais <10ms para manter fluidez da interface (crítico para TDAH - latência alta quebra fluxo mental)
- **O6 — Confiabilidade:** 98%+ cobertura de testes para garantir framework sempre funcional (falhas técnicas são disruptivas para pessoas com TDAH)
- **O7 — Qualidade de IA:** 95%+ dos epics gerados passam validação de dependências, com zero ciclos detectados automaticamente

3. Não‑Objetivos (Out‑of‑Scope)

### Funcionalidades Explicitamente Excluídas
- **Gestão Financeira:** Controle de orçamento, custos, ROI financeiro (foco é produtividade, não finanças)
- **Gestão de Equipe:** Alocação de recursos humanos, calendários compartilhados, aprovações (framework pessoal)
- **Project Management Avançado:** Gráficos de Gantt, critical path detalhado, gestão de riscos corporativa
- **Integrações Corporativas:** SSO empresarial, LDAP, políticas de compliance enterprise (mantém OAuth Google para autenticação pessoal)
- **Multi-Portfólio:** Gestão de múltiplos projetos simultâneos (foco é "um projeto por vez")
- **Colaboração Avançada:** Chat, comentários, notificações push, workflow de aprovação
- **Relatórios Executivos:** Dashboards gerenciais, métricas de produtividade de equipe

### Mantém Simples e Focado
- **Escopo:** Um usuário, um projeto ativo, estrutura clara
- **Complexidade:** Interface direta sem configurações excessivas
- **Manutenção:** SQLite definitivo (sem migração PostgreSQL planejada)

4. Persona Principal - Desenvolvedor com TDAH

### Usuário Primário: Desenvolvedor com TDAH (Você)
**Perfil:**
- Desenvolvedor experiente com TDAH que inicia múltiplos projetos Streamlit
- Enfrenta desafios típicos: procrastinação inicial, perda de contexto, paralisia da escolha
- Precisa de estrutura previsível para reduzir sobrecarga cognitiva
- Valoriza automação e IA para reduzir esforço mental de "começar do zero"

**Necessidades Específicas:**
- **Estrutura Sempre Igual:** Mesmo fluxo (Roteiro → Capítulos → Histórias → Tarefas) em todos os projetos
- **Progresso Visual:** Feedback imediato sobre o que foi feito e o que falta fazer
- **Decisões Automatizadas:** IA que prioriza e ordena para evitar paralisia da escolha
- **Interrupção-Friendly:** Sistema que preserva contexto quando você volta após interrupções
- **Template Ready:** Base técnica sólida para começar qualquer novo projeto rapidamente

**Padrões de Uso:**
- Clona este repositório como base para cada novo projeto
- Usa o wizard para estruturar a visão inicial do projeto
- Confia na IA para gerar estrutura inicial de capítulos/epics
- Retorna periodicamente para acompanhar progresso e ajustar prioridades
- Aproveita sistema de gamificação para manter motivação

### Usuários Secundários (Futuros)
- **Colaboradores:** Outros desenvolvedores que trabalham em projetos iniciados com este framework
- **Clientes/Stakeholders:** Visualizam estrutura e progresso através da interface readonly

5. Benefícios Específicos para TDAH

### Como o Framework Otimiza Produtividade para TDAH

#### 🧠 **Redução de Sobrecarga Cognitiva**
- **Estrutura Previsível:** Sempre mesma sequência (Roteiro → Capítulos → Histórias → Tarefas) reduz decisões desnecessárias
- **Template Pronto:** Base técnica completa elimina "paralisia da página em branco"
- **IA como Assistente:** Refinamento automático reduz esforço mental de estruturação inicial

#### ⚡ **Gestão de Hiperatividade e Impulsividade**
- **Progresso Visual:** Interface mostra claramente o que foi feito e o que falta, satisfazendo necessidade de feedback imediato
- **Gamificação Integrada:** Sistema de achievements canaliza hiperatividade para produtividade
- **Passos Pequenos:** Wizard quebra projeto grande em etapas gerenciáveis

#### 🎯 **Combate à Procrastinação**
- **Início Automático:** IA gera estrutura inicial, eliminando "não sei por onde começar"
- **Priorização Algorítmica:** Remove paralisia da escolha através de ordenação determinística
- **Contexto Preservado:** Interface salva progresso automaticamente, facilitando retomada após interrupções

#### 🔄 **Gestão de Interrupções**
- **Estado Persistente:** Session state mantém contexto completo do projeto
- **Resumo Visual:** Sidebar sempre mostra onde você parou
- **Retomada Fácil:** Interface clara permite voltar ao trabalho rapidamente após pausas

#### 📊 **Tracking de Produtividade**
- **Métricas Objetivas:** Dados sobre foco, interrupções, tempo de conclusão de fases
- **Padrões Pessoais:** Identifica horários e condições de maior produtividade
- **Melhoria Contínua:** Dados embasam ajustes no ambiente e processo de trabalho

6. Escopo Funcional (alto nível)
5.1 Wizard Universal (4 fases)
- Roteiro: coleta visão do produto (5 perguntas) com refino por IA (campo e global), chave para gerar epics.
- Capítulos: epics gerados/ajustados; dependências; ordenação topológica determinística; priorização com pesos por projeto.
- Histórias: detalhamento em histórias de usuário (planejado 5.2) com assistência de IA e ligação com epics.
- Tarefas: granularização em tarefas executáveis (planejado 5.2) e estado básico (pendente/em progresso/concluída).

5.2 IA e Algoritmos
- IA de Refino (Roteiro):
  - Individual: refina um campo com contexto disponível; valida entradas; reescreve sem adicionar fatos.
  - Global: refina todos os campos; requer todos preenchidos; aplica versão de widget para forçar refresh de UI.
- IA Geração de Epics (Capítulos):
  - A partir da visão, gera 3–7 epics com campos: complexidade (1–5), esforço (dias), dependências, unblock_potential, critical_path_weight, flags AI, confiança.
  - Ordenação Topológica Determinística: algoritmo tipo Kahn com heap de prioridade e 4 níveis de desempate (score → prioridade → esforço → chave), O(V+E).
- Pesos de Prioridade por Projeto: normalizados [0..1] somando ≈1; default 5:3:2:2; persistidos e validados.

5.3 Integrações
- **Repositório/BD:** SQLite definitivo (escolha arquitetural para simplicidade do framework pessoal), com suporte a JSON nativo
- **GitHub Projects V2:** Integração bidirecional planejada para sincronização de progresso
- **OAuth 2:** Autenticação Google para ambiente de produção via variáveis de ambiente

6. Requisitos Funcionais (detalhado)
RF‑01 — Roteiro: Coleta de 5 campos
- Campos: visão do produto, problema a resolver, público‑alvo, proposta de valor, restrições (texto multilinha).
- Aceite: cada campo não pode ser string vazia; restrições permitem linhas múltiplas.
- UI: text_area (80–200px) com ajuda contextual (LGPD, prazos, orçamento).

RF‑02 — IA de Refino de Campo (Roteiro)
- Ação: botão “Refinar este campo” disponível quando o campo não está vazio.
- Comportamento: chama SingleFieldAgent; reescreve mantendo sentido; versão do widget incrementada e UI atualiza.
- Aceite: resultado string; se vazio ou erro, mantém anterior e informa status.

RF‑03 — IA de Refino Global (Roteiro)
- Pré‑requisito: todos os 5 campos preenchidos.
- Ação: botão “Refinar Tudo” em formulário completo.
- Aceite: retorna dict com chaves dos 5 campos; aplica apenas strings não vazias; incrementa versões (steps e form); rerun controlado.

RF‑04 — Geração de Epics com IA (Capítulos)
- Dado: visão aprovada (Roteiro completo e validado pelo usuário).
- Ação: o sistema gera automaticamente 3–7 epics a partir da visão usando IA, calculando dependências e posição na execução (topologia). O usuário pode:
  - Editar nome/descrição e metadados do epic
  - Ajustar/confirmar dependências sugeridas
  - Reordenar quando permitido (drag‑drop) respeitando bloqueios/topologia
  - Aprovar/descartar epics antes de persistir
- Campos mínimos por epic (gerados/validados):
  - temp_key (efêmero, apenas na geração), name, description, project_id
  - Topologia: dependências (lista de temp_key) e sort_order calculado pelo algoritmo
  - Estimativas IA: complexity_score [1.0–5.0], effort_estimate [1–30 dias]
  - Priorização: priority (1–5) (derivada/ajustada via PriorityScorer por projeto)
  - Auditoria: model/version/explainer registrados em tabela de auditoria (não no registro do épico)
- Regras de geração/validação:
  - 3 ≤ epics ≤ 7, salvo override explícito do usuário
  - Sem dependências cíclicas (validação em banco + algoritmo)
  - sort_order sequencial por project_id, consistente com dependências e locks
  - Faixas e tipos válidos para campos IA; estimativas coerentes (ex.: esforço > 0)
  - Se a IA falhar (timeout/erro), feedback claro e fallback para modo manual
- Persistência e auditoria:
  - Criação em transação única; em caso de erro, rollback completo
  - Dependências: mapeamento de temp_key → IDs persistidos e gravação em framework_epic_dependencies (prevenção de ciclos)
  - Auditoria: registro de model/version/explainer em framework_epic_ai_audit (histórico consultável), em vez de colunas no épico
- Critérios de Aceitação:
  - A1: Dado um Roteiro válido, ao acionar “Gerar Capítulos”, são sugeridos 3–7 epics com todos os campos mínimos preenchidos
  - A2: Nenhum epic aparece antes de seus pré‑requisitos (validação automática de topologia) e não existem ciclos
  - A3: Após aprovar, os epics são persistidos com sort_order sequencial por projeto e dependências registradas em N:N
  - A4: Logs de IA registram versão do algoritmo e explicação de ordenação; o usuário consegue revisar/ajustar manualmente
  - A5: Em ambiente de desenvolvimento, a geração responde <300ms com mock; em produção, UI apresenta estado e tempo limite adequado

RF‑05 — Ordenação Topológica Determinística
- Comportamento: respeita dependências; resolve empates; calcula critical path.
- Aceite: validar com projeto dummy E‑commerce (7 epics, 8 deps), resultado estável entre execuções.

RF‑06 — Prioridade por Projeto (pesos)
- Persistência: tabela framework_priority_settings com UNIQUE(project_id) e CHECK de soma≈1.
- Backward compat: default 5:3:2:2 quando não houver configuração.
- Aceite: EpicService aplica DI de pesos; ordenação de prioridade refletida na listagem.

RF‑07 — Navegação e Estado
- Steps com Next/Back e “revisão final”; alternância entre passo‑a‑passo e formulário sem perda de dados.
- Aceite: session_state consistente; chaves únicas; nenhum widget com chave duplicada; recuperação de estado em rerun.

RF‑08 — Resumo Completo
- Sidebar com resumo completo (sem truncar); restrições mostradas como bullets (por linha).
- Aceite: textos exibidos integralmente; acessibilidade mínima (leitura por screen readers).

RF‑09 — Gamificação e TDAH
- Acompanhar foco, interrupções, humor, energia; conquistas (10 tipos) e streaks; UI não intrusiva.
- Aceite: eventos armazenados, consultas rápidas, nenhum impacto negativo na latência do wizard.

RF‑10 — Integração de Serviços (DI)
- Container de serviços thread‑safe; registro de PrioritySettingsRepository; VisionRefineService com fallback.
- Aceite: testes integram mocks; troca entre real/mock via env; logs informativos.

7. Requisitos Não‑Funcionais
RNF‑01 — Segurança
- Sem SQL injection (bind), sem pickle, sem MD5, YAML safe_load; inputs validados; proteção CSRF/XSS.
- Conformidade: GDPR pronto; logs sem PII sensível; segredos em env.

RNF‑02 — Performance
- p95 <10ms consultas de epics/prioridade; <1ms para rotas de cache quente; algoritmo topológico O(V+E) com 0.19ms em dataset de referência.

RNF‑03 — Confiabilidade
- Testes 98%+ cobertura; sem deadlocks; 100% integridade referencial; locks controlados.

RNF‑04 — Observabilidade
- Logs com níveis (INFO/DEBUG) para IA e ordenação; métricas de contagem de refinamentos; healthcheck do container de serviços.

RNF‑05 — Usabilidade/Acessibilidade
- IU com áreas verticais; estados de botões claros; mensagens amigáveis em PT‑BR; contraste adequado; teclas de navegação básicas.

RNF‑06 — Portabilidade
- Dev: roda com SQLite e mock IA sem segredos; Prod: OAuth e IA real; conteinerização futura (planejada) sem dependências nativas pesadas.

RNF‑07 — Manutenibilidade (DRY) dos Steps
- Filosofia DRY: nenhuma lógica duplicada entre passos; utilidades comuns residem em módulos compartilhados (ex.: `steps/_pv_state.py`, `pv_state/`, `cap_state/`).
- Padrão de Estrutura (obrigatório):
  - Diretório base: `streamlit_extension/pages/projetos/steps/`
  - Para cada fase, um pacote e um arquivo principal descritivo:
    - Roteiro: `product_vision_step/product_vision.py`
    - Capítulos: `capitulos_step/capitulos.py`
    - Histórias: `historias_step/historias.py`
    - Tarefas: `tarefas_step/tarefas.py`
  - `__init__.py` reexporta API estável do passo (ex.: `render_step`, `validate`, `get_summary` ou função `render_...` principal do passo).
  - Documentação local por passo: `AGENTS.md` e `CLAUDE.md` (quando aplicável) — sem divergências entre elas.
  - Proibido múltiplos `main.py` em subpacotes; nomes devem refletir o domínio do passo (ex.: `product_vision.py`, não `main.py`).
- Convenções de UI/Estado (consistentes entre passos):
  - Geração de chaves de widgets (`_wiz_key`, `_widget_key`, `_form_widget_key`) com version bump para forçar refresh visual após ações de IA.
  - Alturas de `text_area` padronizadas por tipo de campo (80/100/120/150/200px) e ajuda contextual.
  - Navegação com Next/Back padronizada (sticky quando possível) e persistência de estado por sessão (`session_state`).
- Critérios de Aceitação (DRY/Arquitetura):
  - CA‑DRY1: Cada passo possui exatamente um módulo principal com nome descritivo (sem `main.py`) e `__init__.py` reexportando a API pública.
  - CA‑DRY2: Código compartilhado não se repete entre passos; utilidades residem em módulos comuns (ex.: `steps/_pv_state.py`).
  - CA‑DRY3: As funções públicas por passo seguem assinatura e comportamento consistentes (render, validate, get_summary) quando aplicável.
  - CA‑DRY4: Documentação local do passo (AGENTS.md/CLAUDE.md) está alinhada com o PRD e não contém referências a arquivos inexistentes.

8. Dados e Modelo Relacional

### Arquitetura de Banco de Dados
- **Bancos:** framework.db (principal) + task_timer.db (cronômetro) usando SQLite como solução definitiva
- **Justificativa SQLite:** Simplicidade de manutenção, portabilidade, zero configuração, adequado para uso pessoal
- **Performance:** Otimizado para consultas <10ms através de índices estratégicos e triggers

### Schema Principal
- **Tabelas Core:** framework_projects, framework_epics (schema enxuto), framework_tasks, framework_priority_settings
- **Tabelas de Produtividade:** work_sessions, achievement_types, user_achievements, user_streaks
- **Tabelas de Sistema:** github_sync_log, system_settings, framework_epic_dependencies (junção N:N)

### Otimizações Técnicas
- **Índices:** Compostos para project_id+sort_order, específicos para ordenação topológica
- **JSON:** Suporte nativo SQLite JSON1 para campos flexíveis
- **Triggers:** Auto-incremento de sort_order, prevenção de dependências cíclicas, locks automáticos
- **Integridade:** 100% referencial com foreign keys e constraints

### Simplificações Implementadas
- **Removido:** framework_clients (eliminação da camada de cliente)
- **Slim dos Épicos (Migração 012):** remoção de campos legacy (summary, goals, definition_of_done, quality_gates, automation_hooks, checklist_epic_level, epic_key, epic_template_version)
- **Auditoria IA (Migração 013):** criação da tabela framework_epic_ai_audit para registrar model/version/explainer por operação (histórico consultável)

9. Especificação de IA
9.1 Ambiente e Alternância
- Env: TDD_ENVIRONMENT (development/production), OPENAI_API_KEY, TDD_REQUIRE_REAL_AI (on/off).
- Fábrica: create_vision_service(strict) seleciona Mock/Real; fallback controlado.

9.2 Refino Individual (Roteiro)
- Agente: SingleFieldAgent(model_id="gpt‑5‑nano"); prompts por campo; validações; não adiciona fatos; idioma: PT‑BR.
- Retorno: string; UI atualiza via bump de key.

9.3 Refino Global (Roteiro)
- Serviço: UnifiedVisionService (Mock/Real); retorna dict; validações de tipo; erros no modo estrito propagam.

9.4 Geração de Epics (Capítulos)
- Pipeline: Vision → EpicSuggestionDTO → framework_epics; dependências resolvidas; topologia determinística; auditoria de IA registrada em framework_epic_ai_audit.
- Autoridade de Ordenação: a sequência final é SEMPRE calculada pelo DETERMINISTIC_TOPOLOGICAL_ORDERING_DEMO.py. A IA apenas sugere; inconsistências (ciclos, dependências inválidas, cardinalidade) geram warnings e bloqueiam persistência até correção manual.

 9.5 Campos Gerados pela IA (para Ordenação Topológica)
- Por épico (requeridos):
  - temp_key: identificador efêmero e estável durante a geração (ex.: E1, E2, …). Não é persistido.
  - name: título do épico (1–255 chars).
  - description: descrição clara e objetiva do escopo.
  - dependencies: lista de temp_key que este épico depende (vazio quando raiz).
  - complexity_score: número decimal [1.0–5.0] (dificuldade relativa).
  - effort_estimate: inteiro [1–30] (dias estimados).
- Por épico (opcionais/derivados):
  - ai_score: score agregado para heurísticas (0.0–1.0) — opcional.
  - tie_breaker_info: dados de desempate (ex.: prioridade relativa, esforço) — derivados do PriorityScorer.
- Saídas do algoritmo (conjunto):
  - execution_order: lista de temp_key em ordem de execução topológica (determinística).
  - sort_order: atribuição sequencial por projeto após persistência.
  - critical_path (opcional): identificação de possíveis gargalos (em memória).
  - auditoria: model/version/explainer gravados em framework_epic_ai_audit.

9.6 Agno: Papéis e Orquestração (sem perguntas ao usuário)
- Princípio operacional
  - Os agentes NÃO fazem perguntas de volta ao usuário. Em caso de falta de dados ou ambiguidade, devem:
    - Manter o conteúdo original (sem inventar fatos),
    - Refatorar somente o que estiver claro,
    - Retornar avisos estruturados (ex.: warnings) para a UI sinalizar campos pendentes,
    - Delegar ao Scrum Master a decisão de reprocesso (ex.: bloquear botão “Refinar Tudo” até completar campos obrigatórios).
- Papéis
  - Scrum Master (Orquestrador): decide qual agente invocar, controla timeboxes, valida saídas contra o PRD, aplica ordenação e registra auditoria (framework_epic_ai_audit).
  - Product Owner (PO):
    - Roteiro: refina campos individuais e o conjunto, sem adicionar fatos; retorna apenas texto final.
    - Capítulos: gera 3–7 épicos com campos requeridos (temp_key, name, description, dependencies[temp_key], complexity_score, effort_estimate). Não pergunta — se faltar base, retorna warnings conservadores.
  - Dev Team (Líder/Time):
    - Histórias: colabora com o PO para transformar “o quê/por quê” em histórias testáveis (INVEST), sem pedir esclarecimentos via IA — se faltar dado, devolve estrutura parcial com warnings.
    - Tarefas (sempre TDD): detalha as histórias em tarefas técnicas seguindo o paradigma TDD (RED→GREEN→REFACTOR) — sem perguntas interativas; cada tarefa vem acompanhada de um plano de testes a priori.
- Entradas/Saídas (contratos)
  - PO.refine_field(field_key, value, context) → str (sem comentários, sem perguntas)
  - PO.refine_all(pv_dict) → dict[str, str]
  - PO.generate_epics(vision_dto) → list[{temp_key, name, description, dependencies, complexity_score, effort_estimate}]
  - DevTeam.generate_user_stories(epics, po_input) → list[UserStoryDTO]
  - DevTeam.generate_tasks(user_story) → list[TaskDTO] (cada TaskDTO inclui plano de testes TDD)
- Política de prompts
  - PT‑BR, voz ativa, concisa; “NÃO faça perguntas”; “NÃO invente fatos”.
  - Se faltar dado, mantenha o texto original e inclua apenas melhorias seguras (ex.: clareza/gramática); sinalize warnings (metadado estruturado, não no texto).
- Ordenação e Auditoria
  - Scrum Master aplica topologia: calcula execution_order, mapeia temp_key→IDs, grava dependências N:N e sort_order sequencial.
  - Auditoria em framework_epic_ai_audit: model/version/explainer por operação.

### Tarefas — Paradigma TDD (obrigatório)
- Princípios por tarefa
  - RED: definir os testes antes da implementação (falhando inicialmente) mapeando critérios de aceitação da história.
  - GREEN: implementar o mínimo necessário para passar os testes definidos.
  - REFACTOR: melhorar design/nomeação/duplicação mantendo todos os testes verdes.
- Entregáveis por TaskDTO (além de descrição técnica)
  - test_plan: lista de casos de teste (nomes/escopo) em PT‑BR, com arranjo/ação/asserções (AAA) e estratégia de mocks/stubs.
  - commands_hint: comandos para executar localmente (ex.: `pytest -k nome_do_teste`), quando aplicável.
  - coverage_hint (opcional): alvos mínimos de cobertura para componentes críticos.
  - security_checks (quando aplicável): binds SQL, hash seguro, safe_load YAML, validação/sanitização.
- Regras operacionais
  - O agente Dev Team não faz perguntas: se faltar informação da história, registra warnings e gera um test_plan conservador; implementação fica pendente até validação humana.
  - O CI deve falhar quando uma tarefa não incluir test_plan coerente com a história (regra a ser implementada no pipeline quando disponível).

#### Critérios de Aceitação (Tarefas/TDD)
- CA‑TDD1: Cada tarefa proposta vem com test_plan claro (AAA) e mapeado aos critérios de aceitação da história.
- CA‑TDD2: Implementações passam de RED→GREEN com evidência (logs/execução de testes); refactors não quebram testes.
- CA‑TDD3: Para componentes sensíveis, o test_plan inclui checks de segurança (serialização segura, hashing, binds SQL) quando aplicável.

10. UX/UI — Requisitos Detalhados
- Identidade: ícone ET monocromático; botões com estados (ativo, completo, desabilitado); texto amigável em PT‑BR.
- Widgets: text_area com alturas (80/100/120/150/200px); ajuda contextual; barra de progresso (steps); status com st.status (fallback para _NoStatus).
- Feedback: mensagens de sucesso, aviso e erro claras; pré‑visualização de sugestões de IA opcional.

### Roteiro — Resumo e Menu (colapsáveis por padrão) + Navegação Sticky
- Coluna “Resumo” (Roteiro)
  - Deve ser colapsável/expandível (expander), iniciando colapsada por padrão para reduzir carga cognitiva.
  - Exibe um indicador de status compacto quando colapsada (ex.: ✅ Completo / ⏳ Em progresso) sem mostrar o conteúdo integral.
  - A expansão deve preservar a rolagem e não causar salto de layout abrupto; preferir expander nativo com animação suave.
  - Estado de colapso/expansão deve persistir durante a sessão (session_state) para evitar distrações em reruns.

- Barra de Menu (navegação principal)
  - Deve ser colapsável/expandível, iniciando colapsada por padrão (ex.: ícone “hambúrguer”), priorizando conteúdo na tela.
  - Na expansão, exibe seções/fases com realce do passo atual; ao colapsar, mostra apenas ícones/atalhos essenciais.
  - Estado de colapso/expansão deve persistir na sessão.

- Botões “Recuar” e “Avançar” (sticky)
  - Devem permanecer “sticky” no rodapé da página (sempre visíveis), reduzindo esforço de rolagem.
  - Considerar “safe area” em mobile e evitar sobrepor conteúdo; reservar padding inferior quando necessário.
  - Acessibilidade por teclado (TAB/ENTER) e rótulos claros; tamanho mínimo de toque em mobile.

#### Critérios de Aceitação (Roteiro/Menu/Navegação)
- CA‑UX1: A coluna “Resumo” inicia colapsada e pode ser expandida sem perda de contexto; o estado persiste na sessão.
- CA‑UX2: A barra de menu inicia colapsada e pode ser expandida para navegação; o estado persiste na sessão.
- CA‑UX3: Os botões “Recuar” e “Avançar” permanecem visíveis (sticky) e não sobrepõem o conteúdo de forma bloqueadora.
- CA‑UX4: Todos os controles são acessíveis por teclado e têm feedback visual adequado.

### Navegação — Menu “Projetos” e Página de Projeto
- Item de Menu: “Projetos”
  - Lista todos os projetos em um layout de cards elegantes (grid responsivo).
  - Cada card exibe, no mínimo: nome do projeto, breve descrição (primeiras linhas), status, data de criação/última atualização, contadores básicos (ex.: épicos, tarefas) e um indicador simples de progresso (ex.: % concluído se disponível).
  - Ações por card:
    - Abrir (clique no próprio card) → navega para a Página de Projeto.
    - Editar → aciona o wizard na fase relevante (por padrão, Roteiro/Capítulos conforme estado do projeto).
    - Excluir → requer confirmação explícita; remover projeto e relações (épicos/tarefas) com segurança transacional.
  - Comportamentos desejáveis (opcional): busca por nome, filtro por status, ordenação por data/atividade.

- Página de Projeto (detalhe)
  - Cabeçalho: nome, descrição completa, status, datas, ações rápidas (Editar, Excluir com confirmação).
  - Conteúdo organizado (sugestão via abas/seções):
    - Visão (Roteiro): resumo dos 5 campos refinados; link para refinar novamente.
    - Capítulos: lista dos épicos na ordem topológica (sort_order), com dependências visíveis e ações de revisão.
    - Histórias: painel das histórias associadas (quando implementadas), com critérios de aceitação sintetizados.
    - Tarefas: lista/board (quando aplicável) com estado e estimativas.
    - Analytics: gráficos (ex.: distribuição por status, evolução de conclusão), métricas de produtividade e foco.
    - Gamificação: achievements, streaks, métricas gamificadas relevantes ao projeto.
  - Requisitos de UI: carregar rapidamente (<1s dados cacheados), manter navegação clara e permitir retorno à lista de projetos.
  - Segurança: confirmações explícitas para exclusão; entradas validadas; sem exposição de PII sensível.

#### Critérios de Aceitação (Menu/Detalhe)
- CA‑P1: A lista de “Projetos” exibe cards com nome, status e resumo, permitindo editar/excluir cada projeto de forma independente.
- CA‑P2: Ao clicar no card, o usuário é levado à página de detalhes do projeto com visão, capítulos e analytics (quando disponíveis) sem perda de contexto.
- CA‑P3: Operações de exclusão pedem confirmação e executam remoção transacional do projeto e entidades relacionadas.

11. Métricas e Analytics
- Funil do Wizard: taxa de conclusão por fase; tempo médio; passos com maior desistência.
- IA: taxa de uso do refino por campo e global; variação de tamanho de textos; confiança AI média.
- Prioridade: distribuição de pesos por projeto; correlação com velocidade.
- SLOs: p95 latência; integridade referencial; falhas de IA; erros por 1k execuções.

12. Operações e Suporte
- Ambientes: development (mock IA, SQLite), production (OAuth + IA real), possível staging.
- Segredos: via env; sem commit de credenciais; validação em startup.
- Rotinas: manutenção de banco, limpeza de cache, testes de integridade.

13. Riscos, Dependências e Mitigações
- Dependência de provedor IA: custos/limites → mock development, fallback, cache, timeouts.
- Conformidade: GDPR → minimização de dados; restrições registradas sem PII.
- Crescimento de escopo: foco em macro‑fases; feature flags; roadmap iterativo.
- **Escalabilidade:** SQLite adequado para uso pessoal; sem necessidade de migração de banco de dados.

14. Decisões Arquiteturais - SQLite como Solução Definitiva

### Justificativa para SQLite
- **Framework Pessoal:** Uso individual não requer recursos de banco multiusuário
- **Simplicidade:** Zero configuração, backup simples (cópia de arquivo), portabilidade total
- **Performance:** Adequada para volume de dados pessoais (<1000 projetos, <10000 epics)
- **Manutenção:** Sem dependências externas, sem necessidade de DBA ou administração

### Benefícios Específicos para TDAH
- **Menos Complexidade:** Uma preocupação a menos (configuração/manutenção de banco)
- **Portabilidade:** Framework pode ser movido entre máquinas facilmente
- **Backup Simples:** Arquivo único para backup/restore completo
- **Confiabilidade:** Menos pontos de falha técnica (crítico para manter produtividade)

### Funcionalidades SQLite Utilizadas
- **JSON1:** Suporte nativo para campos flexíveis (epic dependencies, configurações)
- **Triggers:** Automação de sort_order e validações de integridade
- **Transactions:** ACID completo para operações críticas
- **Full-Text Search:** Capacidade de busca futura em projetos/epics

15. Lançamento e Rollout
- Fases concluídas: 4.5 (wizard multi‑step), 4.6 (polimento), 5.1 (IA epics + migrações), 3.2 (pesos por projeto).
- Próximas (5.2): persistência completa do wizard em DB; Histórias/Tarefas com IA; dashboard; GitHub V2; mobile; REST API.
- Feature flags: `TDD_REQUIRE_REAL_AI`, modos do wizard; chaves do serviço de visão.

16. Testes e Qualidade
- Estratégia: TDD (Red/Green/Refactor), unit/integration/e2e, mocks para IA em dev; validações de migrações; cobertura 98%+.
- Exemplos de verificação:
  - IA refino (campo/global) — testes em `tests/product_vision/`.
  - Ordenação topológica — scripts de validação e dataset E‑commerce.
  - Repositório de pesos — testes CRUD/validação (25 casos) e integração com EpicService.
  - Segurança — testes de cenários (serialização segura, hashing SHA‑256, binds SQL).

17. Critérios de Aceitação (resumo)
- Completar Roteiro e gerar Capítulos com IA, sem erros e com ordenação estável.
- Atualizar prioridade por projeto e refletir no ordering de epics.
- Refino de campo/global com feedback claro e sem perda de dados.
- Logs de IA e estado suficientes para auditoria básica.
- Testes 98%+ passando; zero vulnerabilidades críticas conhecidas.

18. Roadmap (alto nível)
- 5.2: Histórias/Tarefas + persistência total + dashboard + GitHub V2 + REST API + mobile.
- **5.3+:** Internacionalização, acessibilidade ampliada, API pública com OAuth scopes, busca full-text SQLite.

19. Governança e Decisões
- Clean Architecture e Repository Pattern mandatórios.
- AGENTS.md por diretório define convenções locais; PRD define o “o quê/por quê”.
- Decisões técnicas maiores via ADRs (a adicionar na pasta docs/adr/).

20. Guia de Uso como Template GitHub

### Como Usar Este Framework como Base para Novos Projetos

#### 1. **Clonando o Template**
```bash
# Clone este repositório para um novo projeto
git clone https://github.com/seu-usuario/test-tdd-project.git meu-novo-projeto
cd meu-novo-projeto

# Remover histórico git existente e inicializar novo
rm -rf .git
git init
git add .
git commit -m "feat: Initial project setup from TDAH productivity framework"
```

#### 2. **Configuração Inicial**
```bash
# Instalar dependências
pip install -r requirements.txt
# ou se usando poetry:
poetry install

# Configurar ambiente de desenvolvimento
export TDD_ENVIRONMENT=development
export TDD_REQUIRE_REAL_AI=off  # Usa mock IA para desenvolvimento inicial
```

#### 3. **Personalização do Projeto**
- **Adaptar `CLAUDE.md`:** Atualizar com contexto específico do novo projeto
- **Configurar `.env`:** Adicionar variáveis específicas se necessário
- **Customizar Interface:** Ajustar títulos, descrições e labels no wizard
- **Banco de Dados:** Os arquivos `.db` serão criados automaticamente na primeira execução

#### 4. **Estrutura de Desenvolvimento Recomendada**
```bash
meu-novo-projeto/
├── 📱 streamlit_extension/     # Sua aplicação principal aqui
│   ├── streamlit_app.py       # Entry point customizável
│   └── pages/                 # Suas páginas específicas
├── ⚙️ config/                 # Configurações do projeto
├── 🗄️ *.db                   # Bancos SQLite (criados automaticamente)
├── 📋 CLAUDE.md              # Documentação específica do projeto
└── 🧪 tests/                 # Seus testes específicos
```

#### 5. **Workflow de Desenvolvimento**
1. **Planejamento:** Use o wizard Roteiro → Capítulos para estruturar seu projeto
2. **Desenvolvimento:** Implemente seguindo a Clean Architecture já configurada
3. **Testes:** Aproveite a infraestrutura TDD já implementada
4. **Deploy:** Configure suas próprias variáveis de produção

#### 6. **Vantagens Imediatas**
- ✅ **Arquitetura Pronta:** Clean Architecture + Repository Pattern implementados
- ✅ **Testes Configurados:** Suite de testes TDD completa como base
- ✅ **IA Integrada:** Pipeline de IA pronto para usar (mock + real)
- ✅ **Banco de Dados:** Schema SQLite otimizado e migrations funcionais
- ✅ **Interface TDAH-Friendly:** UI otimizada para produtividade e foco
- ✅ **Gamificação:** Sistema de tracking de progresso já implementado

21. Anexos e Glossário
- **Termos:** Roteiro (visão), Capítulos (epics), Histórias (user stories), Tarefas (tasks), DTO (objeto de transferência), DI (injeção de dependência), RTM (matriz de rastreio), Topologia (ordenação com dependências), IA (inteligência artificial).
- **Links úteis:** documentação de módulos (CLAUDE.md), migrações, serviços de IA, testes.

— Fim —
