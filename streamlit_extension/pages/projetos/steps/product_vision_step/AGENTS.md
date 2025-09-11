# ⚠️ PRD Alignment — Overrides (2025‑09‑09)

- IA (sem perguntas): PO refina campos (individual/global) sem inventar fatos; gera 3–7 épicos com temp_key, name, description, dependencies[temp_key], complexity_score, effort_estimate.
- Ordenação: autoridade do DETERMINISTIC_TOPOLOGICAL_ORDERING_DEMO.py; inconsistências (ciclos/deps) geram warnings e bloqueiam persistência.
- Schema enxuto: sem epic_key persistente; auditoria IA em framework_epic_ai_audit.
- UX TDAH: “Resumo” colapsado por padrão; Next/Back sticky.

# 📘 AGENTS.md — Product Vision Step (estado atual)

Módulo: `streamlit_extension/pages/projetos/steps/product_vision_step`

Objetivo: coleta e refinamento por IA dos 5 campos da visão de produto, com dois fluxos de UI: Steps (campo a campo) e Revisão final (formulário completo). Este arquivo descreve como o código está hoje, sem promessas de camadas que não existem no repo.

Status: ✅ Produção — UI estável, logs adicionados, refino global em modo estrito (sem fallback).
Última atualização: 2025‑09‑08

---

## Visão Geral

- Fluxos suportados:
  - Steps (campo por campo) com botão “✨ Refinar este campo”.
  - Revisão final (formulário completo) com botão “✨ Refinar Tudo”.
- Campos (contrato atual): strings para todos, incluindo `constraints` (texto multilinha permitido). 
- Chaves únicas de widgets e refresh determinístico com versionamento de keys.

---

## Estrutura real dos arquivos

```
product_vision_step/
├── AGENTS.md          # Este documento (fonte da verdade)
├── CLAUDE.md          # Espelho exato de AGENTS.md
└── product_vision.py  # Implementação consolidada (UI + handlers + IA, sem perguntas)
```

Dependências diretas do passo (fora da pasta):
- `steps/_pv_state.py` (compat shim) → reexporta de `steps/pv_state/*`:
  - `DEFAULT_PV` (todas strings; `constraints` é string)
  - `PV_FIELDS` (ordem canônica dos 5 campos)
  - `init_pv_state`, `total_steps`, `is_review_step`, navegação
- `streamlit_extension/services/vision_service.py` → fábrica `create_vision_service(strict=True)`
- `src/ia/agents/agno_agent.py` → `VisionRefinerAgent` (ajustado para normalizar formatos de retorno do Agno) e `SingleFieldAgent`
- `src/ia/product_vision_refiner.py` → `RealGPTRefiner` / `FakeClaudeRefiner` (mock de desenvolvimento)

Não existem arquivos `form_mode.py`, `steps_mode.py`, `summary.py`, etc. Toda a lógica está em `main.py` para reduzir acoplamento e circularidades.

---

## Principais componentes (product_vision.py)

- `_wiz_key(name, step)` — gera prefixos estáveis por sessão para evitar colisões no wizard macro.
- `_widget_key(field)` e `_form_widget_key(field)` — versionam as keys dos widgets:
  - Steps: `roteiro_{field}_v{N}`
  - Formulário final: `form_{field}_v{N}`
  - Ao refinar, o código incrementa `pv_widget_ver_{field}` (steps) ou `pv_form_widget_ver_{field}` (form) e chama `st.rerun()`.
- `_ensure_ai_env_loaded()` — carrega `.env` (se existir) quando `OPENAI_API_KEY` não está no ambiente (evita falhas nos primeiros cliques em ambiente Streamlit).
- `render_product_vision_with_toggle()` — cabeçalho da macro‑fase, determina Steps vs Form (decisão atual: força Steps e usa Form na revisão final).
- `_render_steps_mode()` — 1 campo por vez; botão “✨ Refinar este campo” chama `_handle_refine_field(field_key)`.
- `_render_form_mode()` — todos os campos; botão “✨ Refinar Tudo” chama `_handle_refine_all()`.
- `_render_summary()` — mostra o conteúdo completo de cada campo; para `constraints`, separe em bullets por linha.

### IA — individual (campo por campo)

- `SingleFieldRefiner` usa `SingleFieldAgent(model_id="gpt-5-nano")` (Agno) para devolver string pura.
- Permite refinar um campo se e somente se o campo atual estiver preenchido (não exige os demais).
- Prompt especializado por campo; aplica o valor retornado em `st.session_state.pv[field]` e incrementa a versão do widget de steps.

### IA — global (formulário completo)

- `VisionRefineService` via `create_vision_service(strict=True)` (sem fallback quando estrito):
  - Se `OPENAI_API_KEY` não estiver presente, a criação levanta erro explicita.
  - Com key presente, usa `RealGPTRefiner` (Agno) e retorna um dict coerente com os 5 campos.
- Tratamento do retorno:
  - Todos os campos são strings; `constraints` permanece string.
  - O handler compara valores, aplica quando não-vazio, incrementa as versões de widgets (form e steps) e faz `st.rerun()`.
- Logs (INFO) adicionados:
  - `PV refine_all | payload: {...}` (pré‑chamada)
  - `PV refine_all | result_type=... | result_keys=[...]`
  - Por campo: `old_len`, `new_len`, `changed`, previews `prev/next`
  - Resumo final com `fields_updated`, versões de widgets e snapshot de `pv`

---

## Contratos e decisões

- `constraints` é tratada como string em toda a camada de UI e estado.
- Refino global trabalha em modo estrito: se a IA não retornar conteúdo válido, não atualiza; erros do agente são propagados (sem “consertar” silenciosamente). 
- O wrapper do agente (`VisionRefinerAgent.refine`) normaliza formatos de retorno do Agno (DTO direto, `.content` JSON, dict), mas não inventa conteúdo.
- Widget keys com versionamento evitam problemas de cache visual do Streamlit após atualização do estado.

---

## Troubleshooting rápido

- “OPENAI_API_KEY required …”: verifique `.env` na raiz do projeto ou exporte no shell. `_ensure_ai_env_loaded()` tenta carregar `.env` (`.env`, `streamlit_extension/.env`, `config/.env`).
- “fields_updated=0” nos logs do refino global: a IA retornou strings vazias/iguais; com modo estrito, nada é aplicado — investigue o parsing do agente (normalizado em `src/ia/agents/agno_agent.py`).
- Widget não muda depois do refino: confirme que a versão de key do campo foi incrementada nos logs (`versions_form`/`versions_steps`).

---

## Boas práticas para evoluções

- Se modularizar a UI (form/steps/summary) for necessário, manter o mesmo contrato de keys e os bumps de versão.
- Testes de integração devem simular ambos os fluxos (Steps e Revisão final) verificando `fields_updated` e reruns.
- Para depurar IA: logar o prompt final e o fragmento de resposta (já há previews controlados nos logs).

---

## Exemplos de uso

- Steps (campo a campo):
  1) Preencha o campo atual. 2) Clique “✨ Refinar este campo”. 3) O texto é atualizado e o passo avança manualmente.

- Formulário final:
  1) Preencha todos os campos. 2) Clique “✨ Refinar Tudo”. 3) Após a execução, os text_area exibem os valores refinados (via bump de key + rerun).

---

## Referências

- `streamlit_extension/pages/projetos/steps/_pv_state.py`
- `streamlit_extension/services/vision_service.py`
- `src/ia/agents/agno_agent.py`
- `src/ia/product_vision_refiner.py`
