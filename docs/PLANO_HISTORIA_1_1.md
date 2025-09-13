# Plano de Execução — História 1.1: Estrutura Base do `tdd_core`

Status: Pronto para execução • Marco 0 (Extração do Domínio)

---

## 1) Contexto e Alinhamento

A História 1.1 implementa a fundação do módulo `tdd_core`, conforme o Marco 0 (extração do domínio) e em conformidade com o PRD Final. O objetivo é isolar a base arquitetural (Clean Architecture + DDD) sem alterar comportamento funcional existente na UI Streamlit, garantindo caminho para API/CLI sem regressões.

- Referências diretas:
  - Marco 0 — Extração do Domínio: `docs/marco_0_domain_extraction.md` (História 1.1)
  - PRD Final — Seção “Marco 0 — Extração do Domínio (tdd_core)”: `prd_final.md`
- Princípios: Clean Architecture, DDD, separação de camadas, desacoplamento de frameworks, testabilidade.
- Não inclui: implementação de entidades/VOs completos (Histórias 1.2 e 1.3), alterações de banco, mudanças na lógica de negócio.

---

## 2) Escopo da História (User Story)

Como desenvolvedor, quero criar a estrutura de diretórios e a configuração inicial do módulo `tdd_core` para estabelecer a fundação da arquitetura limpa.

---

## 3) Critérios de Aceite

- Estrutura de pastas criada conforme diagrama arquitetural do Marco 0.
- Todos os `__init__.py` mínimos criados com exports previstos (placeholders) sem dependências cruzadas indevidas.
- `pyproject.toml` atualizado para incluir o pacote `tdd_core` (sem alterar dependências globais críticas).
- README do `tdd_core` com visão arquitetural, princípios e camadas.
- Testes de smoke de importação passando: `import tdd_core` e checagem de `__version__`.
- Nenhuma regressão funcional na UI existente (Streamlit permanece operacional).
- Sem implementação de entidades/VOs além de stubs; nada de regras de negócio nesta história.

---

## 4) Entregáveis

- Diretório `tdd_core/` com camadas: `domain/`, `application/`, `infrastructure/` e subestruturas vazias (stubs) alinhadas ao Marco 0.
- `tdd_core/__init__.py` com metadados e exports mínimos; `__version__` definido.
- `tdd_core/README.md` com visão arquitetural.
- Ajustes no `pyproject.toml` para empacotar `tdd_core` (sem quebrar toolings existentes).
- Teste(s) de smoke em `tests/tdd_core/` validando importação e versão.

---

## 5) Tarefas Técnicas

1. Criar estrutura de diretórios base
   ```bash
   mkdir -p tdd_core/{domain,application,infrastructure}
   mkdir -p tdd_core/domain/{entities,value_objects,exceptions,repositories}
   mkdir -p tdd_core/application/{services,dto,validators,use_cases}
   mkdir -p tdd_core/infrastructure/{adapters,mappers,repositories,ai}
   ```

2. Criar `__init__.py` mínimos (stubs) em cada pasta para habilitar imports relativos e exports planejados
   - `tdd_core/__init__.py`: define `__version__ = "1.0.0"` e exports vazios previstos
   - `domain/__init__.py`, `application/__init__.py`, `infrastructure/__init__.py`: metadados de camada e `__all__` vazio

3. Documentação arquitetural do núcleo
   - `tdd_core/README.md`: visão geral (camadas, princípios, limites, não‑objetivos), referência ao Marco 0 e PRD

4. Atualizar empacotamento
   - Incluir `tdd_core` no `pyproject.toml` (se necessário via `packages`/`tool.poetry.packages`), sem alterar versões de Python/deps

5. Teste(s) de smoke de importação
   ```python
   # tests/tdd_core/test_smoke_import.py
   def test_module_imports():
       import tdd_core
       assert hasattr(tdd_core, "__version__")
       assert isinstance(tdd_core.__version__, str)
   ```

6. Verificações locais
   ```bash
   python -c "import tdd_core; print(tdd_core.__version__)"
   python -m pytest -k tdd_core -q
   ```

---

## 6) Validação e Testes

- Estrutural
  - Diretórios e `__init__.py` presentes e sem ciclos de importação.
- Configuração
  - `pyproject.toml` reconhece `tdd_core` como pacote; ambiente continua instalável.
- Funcional (smoke)
  - `import tdd_core` com sucesso; `__version__ == "1.0.0"`.
- Qualidade
  - Linters/formatters não reportam erros novos; testes existentes continuam passando.
- PRD/Marco 0
  - Streamlit permanece funcional (sem alterações na UI); núcleo pronto para ser consumido por adapters em histórias futuras.

---

## 7) Restrições e Não‑Objetivos

- Não implementar entidades, VOs e regras de negócio (Histórias 1.2 e 1.3 cobrem isso).
- Não tocar no banco de dados, migrações ou repositórios de infra (apenas estrutura vazia).
- Não introduzir dependências novas desnecessárias.

---

## 8) Riscos e Mitigações

- Empacotamento incorreto (não inclusão de `tdd_core`): revisar `pyproject.toml` e executar testes de import.
- Imports prematuros entre camadas: manter stubs sem dependências cruzadas (apenas metadados/exports vazios).
- Regressões na UI: não alterar `streamlit_extension/` nesta história; apenas preparar adapters (pasta) no núcleo.

---

## 9) Critérios de Pronto (DoR)

- Diretório e arquivos alvo mapeados; caminhos e nomes aprovados.
- Checklist de impacto no `pyproject.toml` definido.
- Teste de smoke especificado e caminho de execução acordado.

---

## 10) Definição de Pronto (DoD)

- [ ] Estrutura `tdd_core/` criada com subpastas conforme Marco 0.
- [ ] `__init__.py` mínimos em todas as pastas; `__version__` definido.
- [ ] `tdd_core/README.md` com visão arquitetural e referências.
- [ ] `pyproject.toml` atualizado para empacotar `tdd_core`.
- [ ] Teste de smoke passando localmente e na suíte.
- [ ] Nenhuma regressão nos testes existentes.

---

## 11) Estimativa e Carga

- Esforço sugerido (do Marco 0): ~5 SP
  - Estrutura e inits: 2h
  - README arquitetural: 1–2h
  - Ajustes `pyproject.toml` + smoke: 1h

---

## 12) Avaliação do Plano Original (Resumo)

Análise do arquivo `plano_historia1.1.md` (versão atual):

- Pontos fortes
  - Abrange critérios de aceite completos (estrutura, pyproject, README, smoke tests).
  - Propõe stubs para camadas com metadados e exports planejados.
  - Considera qualidade (type hints, mypy) como plus de engenharia.
- Ajustes propostos nesta consolidação
  - Remoção de artefatos visuais (bordas/colunas) e padronização Markdown.
  - Delimitação explícita de escopo: sem entidades/VOs/outros (deixar para 1.2/1.3).
  - Reforço de alinhamento com PRD: garantir zero regressão na UI e foco em empacotamento.

---

## 13) Referências

- Marco 0 — Extração do Domínio: `docs/marco_0_domain_extraction.md`
- PRD Final — Marco 0 e Gates: `prd_final.md`
- Histórico e padrões (segurança/qualidade): `CLAUDE.md`, `AGENTS.md`

