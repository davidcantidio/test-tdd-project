 Introdução – Escopo Geral do Projeto (Framework Reutilizável)
Claude, este repositório test‑tdd-project deixa de ser apenas um template e passa a ser um framework base reutilizável sempre que eu for criar projetos Streamlit.
Ele já traz embutidos:

Metodologia TDD com fases red/green/refactor, esquema de épicos em JSON e integração opcional com GitHub Projects V2.

Banco de dados SQLite (task_timer.db) para sessões de tempo, estatísticas e, a partir desta extensão, armazenamento de épicos, tarefas, decisões e logs de sincronização.

Dashboards interativos com Plotly e diagramas Mermaid, usados atualmente na página gerada via GitHub Pages.

CLI robusta com Typer e Rich para timers, analytics e geração de diagramas.

Gamificação e suporte a TDAH para manter o foco: timers com alertas sonoros/visuais, análise de padrões de atenção e recomendações de pausas.

Reuso em Novos Projetos
Quando iniciar um novo projeto, poderei:

Conectar meu próprio banco de dados relacional (MySQL, Postgres, etc.) às tabelas do framework por meio de chaves estrangeiras, aproveitando o esquema de sessões de tempo e épicos.

Continuar usando a análise de produtividade (analytics_engine) em cima dos meus dados.

Reaproveitar o gerador de Gantt e o interceptor de warnings, adaptando‑os aos módulos do novo projeto.

Ter a opção de integrar tarefas de Node.js ou projetos mistos: o framework detecta o tipo de projeto (Python/Node.js/Mixed) via wizard e configura os arquivos necessários
GitHub
. A UI Streamlit continuará disponível para qualquer linguagem, pois o tracking e a sincronização funcionam em Python.

Objetivo da Extensão Streamlit
A evolução agora é adicionar uma camada Streamlit, mantendo compatibilidade, que:

Ofereça uma interface local, interativa e gamificada, substituindo o dashboard do GitHub Pages.

Não altere o funcionamento atual: todos os scripts existentes continuam funcionais (inclusive o wizard de setup e validação de ambiente).

Permita adicionar bancos próprios nos projetos derivados, relacionando com as tabelas do framework.

Inclua sincronização opcional com GitHub Projects V2, respeitando rate limits.

Seja clonável: cada projeto pode incluir essa extensão e adaptar a pasta app/ para sua lógica específica.

Instruções para Atualizar os claude.md
Atualize os seguintes arquivos de documentação do Claude com base neste novo escopo:

claude.md na raiz: visão geral do framework reutilizável, requisitos de sistema (Python 3.11+, Git, 4 GB RAM
GitHub
) e como iniciar a extensão Streamlit.

streamlit_extension/claude.md (novo): detalhes técnicos da UI, esquema de banco, sincronia GitHub, gamificação e instruções para futuros projetos.

claude.md em módulos existentes (tdah_tools/, setup/, docs/): explicar onde ocorrem integrações (ex.: o wizard deve perguntar se o usuário quer habilitar a UI Streamlit; o validate_environment.py deve checar dependências de Streamlit).

Esclarecer que todas as futuras contribuições devem manter compatibilidade e modularidade para preservar a possibilidade de reuso.

🛠️ Plano de Implementação Revisado
A seguir, o plano revisado para criar a extensão Streamlit, incorporando pontos antes omitidos.

1. Atualizar dependências e ambiente
Versão do Python: atualizar pyproject.toml para python = "^3.11,<4.0" e garantir compatibilidade com Node.js quando necessário. O setup atual exige Python ≥ 3.8
GitHub
; a nova versão preserva isso.

Adicionar dependências: streamlit >= 1.30, sqlalchemy ou pydantic_sqlalchemy para ORM, python-dotenv para gestão de tokens, gql para GraphQL e pyjwt se for necessário assinar payloads. Incluir asyncio ou fastapi se a UI precisar de chamadas assíncronas para warnings.

Dependências de Front‑end: manter plotly (já presente
GitHub
), adicionar recharts ou similar se for usar React; podem ser instaladas via NPM no template de front‑end se necessário.

Scripts de verificação: atualizar setup/validate_environment.py para verificar se Streamlit, SQLite, GraphQL libs e as novas dependências estão instaladas e, em caso negativo, instruir o usuário a rodar poetry install ou pip install -r requirements.txt.

2. Unificar banco de dados com migrações
Tabela centralizada: manter o uso de task_timer.db para sessões de tempo e incluir as tabelas framework_epicos, framework_tasks, github_project_fields, github_sync_log, user_decisions e warning_rules. Isso simplifica queries e evita múltiplos arquivos.

Migrations: criar pasta streamlit_extension/database/migrations/ com scripts versionados (por exemplo, 001_initial.sql, 002_add_rules_engine.sql). Estes scripts devem ser idempotentes (não rodarem duas vezes).

Relacionamentos: adicionar FOREIGN KEY em framework_tasks ligando epic_id a framework_epicos(id) e task_sessions.task_id a framework_tasks(id) para que o time tracking associe sessões a tasks.

Persistência de warnings: as tabelas user_decisions e warning_rules devem armazenar decisões do usuário (com colunas warning_hash, decision, timestamp) e regras derivadas (pattern, action). Indexar warning_hash para lookup rápido (≤ 5 ms).

Campos de auditoria: adicionar colunas created_at, updated_at e deleted_at em todas as novas tabelas para versionamento e possivelmente auditorias futuras.

3. Estrutura do diretório e integração
Manter a estrutura original (docs, epics, scripts, tdah_tools). Acrescentar:

arduino
Copiar
Editar
test-tdd-project/
├── streamlit_extension/
│   ├── streamlit_app.py
│   ├── config/
│   │   └── streamlit_config.py
│   ├── components/
│   │   ├── time_tracker.py
│   │   ├── scrum_dashboard.py
│   │   ├── github_sync.py
│   │   └── warnings_module/
│   │       ├── warning_interceptor.py
│   │       ├── interactive_handler.py
│   │       ├── decision_database.py
│   │       └── rules_engine.py
│   ├── database/
│   │   ├── models.py
│   │   └── migrations/
│   └── integration/
│       └── existing_system.py
└── ...
Detecção de projeto: o wizard setup/init_tdd_project.py deve perguntar se o usuário quer habilitar a extensão Streamlit. Se sim, copiar a pasta streamlit_extension e ajustar pyproject.toml.

Bridge com sistema atual: existing_system.py deve detectar automaticamente se o projeto usa Python, Node ou Mixed, e mapear tasks/épicos independentemente da linguagem. No caso de Node, tasks serão identificadas pelo JSON; o front‑end em Streamlit continuará funcional pois roda em Python.

Configuração: streamlit_config.py deve ler .env para carregar tokens, definir intervalos de sync e armazenar configuração da UI (por exemplo, tema light/dark).

4. Interface Streamlit gamificada
Sidebar persistente: inclui seleção do épico ativo, controles de tempo (start/pause/resume/stop) e tempo decorrido. Persistir estado com st.session_state e gravar no banco para que, mesmo recarregando a página, o timer continue.

Navegação: páginas “Minha Aplicação”, “Scrum Dashboard”, “Time Analytics”, “Task Board” (Kanban com drag‑and‑drop), “Gantt Chart” e “Configurações”.

Gamificação: mostrar badges, contadores e barras de progresso. Por exemplo, badge ao completar um épico dentro do tempo estimado, ou pontos por seguir o ciclo red‑green‑refactor. Incluir animações de transição (Framer Motion) e cores variáveis para fases (red, green, blue).

Ajuste de time zone: todas as datas exibidas na UI devem seguir o fuso do usuário (America/Fortaleza). Se usar datetime.now(), converter para a timezone via pytz ou zoneinfo.

Acessibilidade: suporte a temas (dark/light), contraste elevado e fontes maiores.

Gantt chart regenerado: em scrum_dashboard.py, use os dados do banco para gerar um Gantt via plotly. O código atual em gantt_tracker.py já carrega épicos da pasta epics
GitHub
; adapte a lógica para ler do banco, calcular percentuais (por exemplo, tasks em fase green e refactor) e desenhar o gráfico.

Kanban: implementar drag‑and‑drop com streamlit-dnd ou biblioteca similar. Cada task terá campos de status local (To Do, In Progress, Done) além de tdd_phase.

Analytics: reutilizar TDDAHAnalytics
GitHub
 para mostrar gráficos (linha, barra, heatmap) com tempo estimado vs real, overrun, foco (accuracy_ratio). Adaptar queries para filtrar por épico ou período (últimos 7 dias, mês, etc.).

5. Lógica de warnings interativos (TDD)
Interceptor: warning_interceptor.py deve ser injetável no pipeline (transform/warnings). Ele captura warnings de forma síncrona ou assíncrona e gera um hash único para lookup. Deve garantir latência ≤ 10 ms por warning, não adicionando chamadas de API (ver performance constraints do JSON).

Handler interativo: interactive_handler.py exibe prompts ao usuário apenas para warnings desconhecidos. Se a UI não estiver aberta (por exemplo, rodando testes via CLI), deve cair em modo CLI e pedir input no terminal.

Banco de decisões: decision_database.py implementa persistência ACID. Use SQLite com transações; se um erro ocorrer, faça rollback. Todos os métodos devem retornar em ≤ 50 ms para escrita e ≤ 10 ms para leitura, conforme constraints no epic.

Engine de regras: rules_engine.py aplica decisões salvas sem prompt. Separar lógica de matching e aplicação, permitindo suportar novas ações (por exemplo, auto‑silenciar warnings ou abrir issues).

Concorrência: use asyncio ou threading.Lock para processar múltiplos warnings simultaneamente. Escreva testes para garantir ausência de race conditions e deadlocks.

6. Sincronização com GitHub Projects V2
Campos locais vs opcionais:

Armazenar sempre no banco: estimate_minutes, story_points, tdd_phase, deliverables, performance_constraints.

Sincronizar somente se existirem no Project: Status, Estimate, Story Points, Epic ID.

Criação de campos: devido às limitações da API, novos campos não podem ser criados via GraphQL. Instruir o usuário a criar os campos manualmente na interface do Project.

API token: usar token classic para GraphQL, carregado a partir de .env. Salvar apenas o hash no banco (coluna github_token_hash). Nunca gravar o token completo em logs.

Smart polling: agendar sincronizações a cada 5 minutos ou sob demanda (botão “Sync GitHub” na UI). Bater no GraphQL apenas se houver mudanças locais ou se o usuário clicar. Use caching TTL e arredondamento de consultas para agrupar atualizações e preservar o limite de 5 000 pontos/hora.

Gestão de conflitos: se o GitHub indicar que um issue foi fechado/reaberto, atualize o status local. Se os campos opcionais divergirem, registre conflito no github_sync_log e mostre alerta. O usuário decide se quer sobrescrever.

Branch/PR automation: opcionalmente, o módulo pode abrir PRs ou criar rótulos com base no epic, mas deve respeitar a regra de não criar campos.

7. CLI e automação
Comandos atualizados:

manage.py sync-github → Sincroniza issues, épicos e campos opcionais.

manage.py migrate-db → Roda migrations da extensão.

manage.py streamlit-run → Inicia a UI (poetry run streamlit run streamlit_extension/streamlit_app.py).

manage.py export-gantt → Exporta Gantt para HTML ou PDF (caso ainda deseje publicar).

manage.py validate-epics → Valida JSONs em epics/ (continua usando scripts/validate_epic.py).

Integração com Typer: Aproveitar typer já presente na dependency list
GitHub
. Cada comando deve ser assíncrono quando envolver sincronização.

Wizard: adaptar setup/init_tdd_project.py para que, ao criar novo projeto, pergunte se o usuário quer instalar a extensão Streamlit e, em caso afirmativo, execute manage.py migrate-db e adicione as dependências.

8. Atualização de documentação e remoção do GitHub Pages
README.md: retirar a referência ao “GitHub Pages Dashboard”
GitHub
 e aos links de live dashboard
GitHub
. Substituir por instruções de como iniciar a UI local (streamlit run ...) e explicar que o GitHub Pages se torna opcional.

SETUP_GUIDE.md: alterar a seção “GitHub Pages Dashboard” para “Streamlit Dashboard” e atualizar o passo a passo.

CUSTOMIZATION_GUIDE.md: incluir instruções sobre como personalizar o tema da UI, configurar a sincronização e adicionar bancos de dados adicionais.

TROUBLESHOOTING.md: adicionar seções de depuração para problemas comuns de Streamlit (porta ocupada, dependências faltando) e de GitHub API (rate limit, campos inexistentes).

Docs técnicas: incluir diagramas Mermaid para a arquitetura da extensão e o fluxo de dados (epic JSON → banco → UI).

9. Testes, segurança e multi‑usuário
Testes de aceitação: criar suite tests_streamlit/ que valida:

Renderização das páginas e widgets via streamlit.testing.

Persistência de sessões e recarga da UI.

Lógica de warnings (red/green/refactor).

Sincronização com GitHub (mock).

Cobertura ≥ 90 %: rodar pytest-cov e incluir a extensão na métrica.

Gerenciamento de usuários: embora o projeto atual seja mono‑usuário (apenas eu), estruturar tabelas com um campo opcional user_id para facilitar a expansão no futuro. Se mais devs forem adicionados, o time tracker e a UI precisam isolar sessões por usuário.

Notificações: exibir alertas toast na UI quando um épico ultrapassar a estimativa ou quando houver conflitos de sincronização. Deixar ganchos para integração com Slack ou email (via Webhooks) em versões futuras.

Segurança de tokens: usar .env ou secret manager para armazenar GH_TOKEN. Nunca exibir o token em logs. Adicionar documentação sobre como gerar um token classic com permissões necessárias.

✔️ Checklist de Validação Final
Sistema e scripts atuais continuam funcionando.

Extensão Streamlit instala e roda sem erros, independente de haver integração com GitHub.

Banco de dados unificado com migrações automáticas.

Gantt e dashboards regenerados via UI com Plotly.

Warnings interativos implementados, com armazenamento e regras.

Sincronização GitHub respeita limites e lida com conflitos.

Documentação e claude.md atualizados para refletir o novo escopo.

Interface gamificada e preparada para reuso em novos projetos.

Conclusão
Este prompt fornece a visão geral (framework reutilizável), instruções para os claude.md e um plano de implementação completo, incluindo detalhes antes omitidos (como detecção de ambiente, segurança de tokens, multi‑usuário, time zone, suporte a Node/mixed e ajustes na CLI).

Claude deve agora:

Atualizar seus claude.md conforme descrito.

Seguir o plano para criar a extensão Streamlit sem impactar o funcionamento atual.

Garantir que o framework continue reutilizável em novos projetos, permitindo a criação de bancos de dados e lógicas específicas que aproveitem a base.