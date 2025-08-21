# Refactor Plan: systematic_file_auditor.py (fase 1 – não-invasiva)

## Objetivos (curto prazo)
- Introduzir contratos (interfaces.py) para DI/testabilidade ✅
- Garantir I/O seguro com path validation e atomic write ✅
- Criar testes smoke (auditor/meta-agent) e utilitários ✅

## Próximos passos (médio prazo)
1. Extrair "persistence" (checkpoints/sessions) para `core/persistence.py`
2. Extrair "planning" (seleção de agentes) para `coordination/plan.py`
3. Isolar "file ops" em `core/file_ops.py` usando `path_security.py`
4. Introduzir `Auditor` concreto que injeta dependências via construtor

## Guidelines
- Nenhum método > 60 linhas
- Nenhuma classe > 400 linhas
- Funções puras sempre que possível
- Evitar efeitos colaterais fora de camadas “ops”
