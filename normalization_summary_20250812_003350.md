# 🔄 PLANO DE NORMALIZAÇÃO E EXEMPLOS REPRESENTATIVOS

**Data de Geração:** 2025-08-12 00:33:50
**Objetivo:** Normalizar dados JSON para migração consistente

## 📋 Resumo do Plano

### Estratégia de Normalização
1. **Unificação estrutural:** Converter todas as estruturas para formato nested
2. **Padronização de IDs:** Gerar IDs únicos para placeholders
3. **Mapeamento de campos:** Criar correspondência consistente entre variações
4. **Validação de tipos:** Garantir tipos de dados apropriados
5. **Limpeza de dados:** Remover valores vazios e inconsistentes

### Transformações Principais
1. **ID Generation:** Gerar IDs únicos para placeholders
2. **Structure Unification:** Converter flat para nested
3. **Field Mapping:** Padronizar nomes de campos
4. **Data Type Standardization:** Padronizar tipos de dados

### Casos Extremos Identificados
- **Task sem ID:** Gerar ID baseado em epic_id + posição
- **Dependências quebradas:** Manter lista vazia até resolução manual
- **TDD phase inválida:** Usar 'analysis' como padrão
- **Estimate negativo:** Usar 60 minutos como padrão
- **Deliverables vazios:** Remover da lista

## 🎯 Exemplos de Transformação

### Exemplo 1: Template com placeholders

**Antes:**
```json
{
  "epic": {
    "id": "[EPIC-ID]",
    "name": "[Epic Name]",
    "tasks": [
      {
        "id": "[TASK-1-ID]",
        "title": "Write failing test",
        "tdd_phase": "red",
        "estimate_minutes": 30
      }
    ]
  }
}
```

**Transformações aplicadas:**
- ID placeholder '[EPIC-ID]' → 'template_epic_template'
- Nome placeholder '[Epic Name]' → 'Epic from epic_template.json'
- Task ID '[TASK-1-ID]' → 'template_epic_template.1'
- Adicionado metadata com timestamps
- Adicionado campos obrigatórios com valores padrão

### Exemplo 2: Estrutura flat para nested

**Antes:**
```json
{
  "id": 1,
  "title": "User Authentication",
  "estimated_hours": 40,
  "tasks": [
    {
      "task_id": "1.1",
      "name": "Setup auth middleware",
      "phase": "green",
      "estimated_time_minutes": 120
    }
  ]
}
```

**Transformações aplicadas:**
- Estrutura flat → nested com wrapper 'epic'
- Campo 'title' → 'name'
- Campo 'task_id' → 'id'
- Campo 'name' → 'title'
- Campo 'phase' → 'tdd_phase'
- Campo 'estimated_time_minutes' → 'estimate_minutes'


## 🛠️ Implementação

### Scripts Gerados
1. **ETL Script:** `etl_migration_script_*.py`
   - Conecta ao SQLite
   - Cria tabelas necessárias
   - Normaliza e migra dados
   - Registra log de operações

2. **Validation Script:** `validation_script_*.py`
   - Valida contagem de registros
   - Verifica integridade referencial
   - Testa campos obrigatórios
   - Confirma tipos de dados

3. **Examples File:** `normalization_examples_*.json`
   - Comparações antes/depois
   - Catálogo de transformações
   - Documentação de casos extremos

### Próximos Passos
1. Revisar exemplos de normalização
2. Executar ETL script em ambiente de teste
3. Rodar validação pós-migração
4. Corrigir problemas identificados
5. Executar migração final