Objetivo do Incremento

Implementar o fluxo “IA sugere Capítulos a partir do Roteiro”, com revisão/reordenação no Streamlit e persistência auditada.

Definições Globais

Definition of Ready (DoR) das histórias

Critérios de aceitação claros

Dados mínimos do Roteiro disponíveis (product_name, target_user, problem, outcome, constraints[])

Cenários de teste definidos antes do código

Definition of Done (DoD) de todo item

Testes unitários ≥ 85% do novo código (pytest + coverage)

Nomes de testes seguindo tests/**/test_*.py

Tipagem mypy sem erros nos módulos tocados

Log estruturado (nível INFO para sucesso, WARNING/ERROR para falhas)

Persistência e/ou side effects cobertos por testes (com mocks/fakes)

Docs curtas em docstring + CHANGELOG.md atualizado

CAPÍTULO 1 — Contratos de dados do Roteiro (Visão) e da Sugestão de Capítulos

Assegura que a IA receba dados padronizados e devolva sugestões em DTOs estáveis.

História 1.1 — Como sistema, eu quero padronizar o Roteiro em DTO

Aceitação

DTO valida campos obrigatórios; rejeita strings vazias

constraints sempre lista normalizada (trim, sem duplicatas)

Tarefas (TDD-first)

Escrever testes de DTO/validação

tests/product_vision/test_product_vision_dto.py

casos: completo, campo faltando, constraints duplicadas/em branco

Implementar DTO/validador

product_vision_state.py e/ou schema.py (DTO)

funções de normalização

História 1.2 — Como sistema, eu quero um DTO para Sugestão de Capítulos

Aceitação

Estrutura: EpicSuggestionDTO(title, rationale, tags[], confidence:0..1, source="ai|heuristic")

Serializa/deserializa (dict) sem perda

Tarefas

Testes do EpicSuggestionDTO

tests/epics/test_epic_suggestion_dto.py

Implementação DTO

schema.py (ou novo epic_schemas.py)

CAPÍTULO 2 — Motor de Sugestão (IA + heurísticas)

Gera lista de capítulos a partir do Roteiro.

História 2.1 — Como usuário, quero que a IA sugira capítulos coerentes com o Roteiro

Aceitação

Dada uma visão válida, retorna 3–8 capítulos com título + rationale

Execução determinística com seed quando em modo teste

Tarefas

Testes de caracterização do motor (mock LLM)

tests/epics/test_epic_suggester_core.py

cenários: visão mínima; visão rica com várias constraints

Implementar interface de provedor LLM desacoplada

epic_service.py: EpicSuggester( llm: EpicLLMProvider )

fakes.py: FakeEpicLLMProvider para testes (sem rede)

Implementar heurística de fallback (sem LLM)

palavras-chave extraídas de problem, outcome, constraints

História 2.2 — Como PO, quero configurar prompt templates e léxico de domínio

Aceitação

Template em arquivo (prompts/epic_suggestion.md)

Léxico carregado de YAML (configs/domain_lexicon.yaml)

Tarefas

Testes: carga de template/lexicon + merges e variáveis obrigatórias

tests/epics/test_prompt_config.py

Implementação de carregadores

product_vision_repository.py (ou novo config_loader.py)

CAPÍTULO 3 — Priorização e Ordenação

Converte sugestões em lista ordenada (valor/risco/esforço, pesos ajustáveis).

História 3.1 — Como usuário, quero ver os capítulos em ordem de prioridade

Aceitação

Score = função ponderada (valor, risco, esforço, alinhamento)

Ordenação estável; empates preservam ordem de entrada

Tarefas

Testes do PriorityScorer

tests/epics/test_priority_scorer.py

casos: pesos diferentes; empates

Implementação do PriorityScorer

epic_service.py (ou services/priority.py)

História 3.2 — Como PO, quero ajustar pesos de priorização

Aceitação

Persistir pesos por projeto em repositório

Valor padrão (ex.: valor=0.5, risco=0.2, esforço=0.2, alinhamento=0.1)

Tarefas

Testes de persistência e defaults

tests/repositories/test_priority_settings_repo.py

Implementação repo/config

product_vision_repository.py (ou epic_service.py + repo dedicado)

CAPÍTULO 4 — UI de Revisão e Reordenação no Streamlit

Exibe sugestões, permite editar, aprovar/rejeitar e arrastar para reordenar.

História 4.1 — Como usuário, quero revisar, editar e reordenar capítulos no UI

Aceitação

Lista com drag-and-drop (ou botões ↑/↓ fallback)

Edit inline (título/descrição/tags)

Marcar Aprovar/Rejeitar por item

Tarefas

Testes de lógica de UI desacoplada (sem Streamlit)

tests/ui/test_epic_review_viewmodel.py

cobre: mover item, editar, aprovar/rejeitar, undo simples

Implementar ViewModel e adaptadores

form_components.py (ou streamlit_extension/components/epic_review.py)

observação: manter regras fora do callback do Streamlit

Implementar página no Streamlit

projeto_wizard.py / init_nav.py → adicionar etapa “Revisão de Capítulos”

Uso de sessão segura; persistência ao confirmar

História 4.2 — Como usuário, quero visualizar o racional/score de cada capítulo

Aceitação

Tooltip/expansão com rationale e breakdown do score

Indicador de confiança da IA

Tarefas

Testes do formatter do rationale/score

tests/ui/test_epic_explainers.py

Implementação dos explainers

form_components.py (formatters)

integração na página

CAPÍTULO 5 — Persistência, Versão e Auditoria

Salva a ordem aprovada e mantém trilha de mudanças.

História 5.1 — Como usuário, quero salvar a ordem aprovada com versionamento

Aceitação

epic_plan.json por projeto (vX semântica)

diff armazenado a cada confirmação (quem, quando, o quê)

Tarefas

Testes de repo/versões/diff

tests/repositories/test_epic_plan_repository.py

Implementar repositório e diff

product_vision_repository.py (ou epic_plan_repository.py)

state_core.py para utilidades

História 5.2 — Como auditor, quero logs estruturados e erros tratáveis

Aceitação

Logs com project_id, user_id, action

Erros de IA/IO convertem para mensagens UX claras + códigos internos

Tarefas

Testes de mapeamento de exceções → mensagens

tests/infra/test_error_mapping.py

Implementação middleware de erros/log

base.py (ou constants.py + logging setup)

Plano de Sprints (sugestão enxuta)

Sprint 1 (Infra + Motor)

Histórias 1.1, 1.2, 2.1, 2.2

Sprint 2 (Priorizar + UI Básica)

Histórias 3.1, 3.2, 4.1

Sprint 3 (Explainability + Persistência + Auditoria)

Histórias 4.2, 5.1, 5.2

Modelo de Tarefa (TDD-first) — usar este checklist em todas

 Especificar testes (cenários, fixtures, given-when-then)

 Escrever testes que falham (Red)

 Implementar mínimo para passar (Green)

 Refactor com segurança (Refactor)

 Cobertura atualizada (≥85%)

 Tipagem/mypy OK

 Log/erros padronizados

 Docs/changelog atualizados