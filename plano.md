# 📋 Duration System Implementation Plan
**Projeto:** Test-TDD-Project - Epic Migration System  
**Foco:** Sistema de Duração com Dados Calculados  
**Data:** 2025-08-13

---

## 🎯 Objetivo Principal

Implementar sistema de duração baseado em datas calculadas que mantém descrições amigáveis e suporta a estrutura rica dos épicos reais, com foco específico no **primeiro item** da migração.

---

## 📊 Análise da Situação Atual

### ✅ Estado do Banco de Dados
- **Schema Atual:** framework_v3.sql com estrutura básica
- **Campos Existentes:** duration_days (INTEGER), campos básicos de auditoria
- **Limitações Identificadas:** 
  - Sem campos de data início/fim
  - Sem suporte para goals/definition_of_done
  - Sem sistema de dependências
  - Sem suporte para labels/prioridades

### 📈 Épicos Reais Analisados
- **Total:** 9 épicos em `/epics/user_epics/`
- **Formatos de Duração:** "1.5 dias", "2 dias", "1 semana" 
- **Incompatibilidade:** ~75% com schema atual
- **Dados Ricos:** goals[], definition_of_done[], labels[], dependencies[]

---

## 🚀 Plano de Implementação - Duration System

### **FASE 1: Análise e Design da Extensão do Schema**
**Duração:** 2-3 horas | **Prioridade:** ALTA

#### 1.1 Análise Detalhada de Incompatibilidades
- **Tarefa:** Mapear todos os campos faltantes nos épicos reais
- **Entregáveis:** 
  - `reports/schema_gap_analysis.md`
  - Lista de campos prioritários vs opcionais
- **Critérios:** 100% dos campos mapeados com classificação de prioridade

#### 1.2 Design da Extensão do Schema
- **Tarefa:** Projetar campos de data e duração calculada
- **Campos Novos:**
  ```sql
  -- Campos de data
  planned_start_date DATE,
  planned_end_date DATE,
  actual_start_date DATE,
  actual_end_date DATE,
  
  -- Duração calculada e amigável
  calculated_duration_days INTEGER,
  duration_description VARCHAR(50), -- "1.5 dias", "2 semanas"
  
  -- Metadados ricos
  goals JSON,
  definition_of_done JSON,
  labels JSON,
  priority_tags JSON
  ```
- **Entregáveis:** `schema_extensions_v4.sql`

#### 1.3 Design do Sistema de Dependências
- **Tarefa:** Criar tabela de dependências entre tarefas
- **Schema:**
  ```sql
  CREATE TABLE task_dependencies (
    id INTEGER PRIMARY KEY,
    task_id INTEGER REFERENCES framework_tasks(id),
    depends_on_task_id INTEGER REFERENCES framework_tasks(id),
    dependency_type VARCHAR(20), -- 'blocking', 'related', 'optional'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );
  ```
- **Entregáveis:** Definição completa do sistema de dependências

---

### **FASE 2: Implementação do Core Duration System**
**Duração:** 4-5 horas | **Prioridade:** ALTA

#### 2.1 DurationCalculator Engine
- **Tarefa:** Implementar classe para cálculo automático de duração
- **Funcionalidades:**
  - Calcular duration_days a partir de start_date/end_date
  - Considerar dias úteis vs calendário
  - Validar consistência de datas
- **Arquivo:** `duration_system/duration_calculator.py`
- **Testes:** Cobertura ≥ 95%

#### 2.2 DurationFormatter Engine  
- **Tarefa:** Criar formatador para descrições amigáveis
- **Funcionalidades:**
  - Converter dias para "X dias", "Y semanas"
  - Suporte para frações: "1.5 dias"
  - Manter compatibilidade com épicos existentes
- **Arquivo:** `duration_system/duration_formatter.py`
- **Exemplos:**
  ```python
  DurationFormatter.format(1) → "1 dia"
  DurationFormatter.format(7) → "1 semana" 
  DurationFormatter.format(10) → "1.5 semanas"
  ```

#### 2.3 Extensão do DatabaseManager
- **Tarefa:** Adicionar métodos para duration system
- **Métodos Novos:**
  ```python
  def calculate_epic_duration(epic_id: int) -> int
  def update_duration_description(epic_id: int, description: str)
  def get_epic_timeline(epic_id: int) -> Dict
  def validate_date_consistency(epic_id: int) -> bool
  ```
- **Arquivo:** `streamlit_extension/utils/database.py`

---

### **FASE 3: Suporte para Dados Ricos e Prioridades**
**Duração:** 3-4 horas | **Prioridade:** MÉDIA

#### 3.1 JSON Fields Handler
- **Tarefa:** Implementar manipulação de campos JSON
- **Funcionalidades:**
  - Serialização/deserialização de goals, definition_of_done
  - Validação de estrutura JSON
  - Queries eficientes em campos JSON
- **Arquivo:** `duration_system/json_handler.py`

#### 3.2 Priority System
- **Tarefa:** Sistema de prioridades e tags especiais
- **Tags Especiais:** 
  - `"emergency"` - prioridade máxima
  - `"skip_queue"` - pular fila normal
  - `"background"` - baixa prioridade
- **Arquivo:** `duration_system/priority_manager.py`

#### 3.3 Dependency Resolver
- **Tarefa:** Implementar resolvedor de dependências
- **Funcionalidades:**
  ```python
  class DependencyResolver:
    def validate_no_cycles(self, task_key, dependencies)
    def get_executable_tasks(self) 
    def get_dependency_chain(self, task_key)
    def get_blocking_tasks(self, task_key)
  ```
- **Arquivo:** `duration_system/dependency_resolver.py`

---

### **FASE 4: Migration Engine para Épicos Reais**
**Duração:** 2-3 horas | **Prioridade:** ALTA

#### 4.1 Epic Data Analyzer
- **Tarefa:** Analisar e validar épicos reais
- **Funcionalidades:**
  - Parse de duration strings ("1.5 dias" → 1.5)
  - Validação de estrutura JSON
  - Relatório de compatibilidade
- **Arquivo:** `migration/epic_analyzer.py`

#### 4.2 Migration Script
- **Tarefa:** Script principal de migração
- **Funcionalidades:**
  - Migrar 9 épicos de `/epics/user_epics/`
  - Calcular datas baseado em duração
  - Preservar dados ricos em JSON
  - Rollback automático em caso de erro
- **Arquivo:** `migration/migrate_real_epics.py`
- **Validação:** 100% dos épicos migrados com sucesso

#### 4.3 Data Integrity Validator
- **Tarefa:** Validador de integridade pós-migração
- **Verificações:**
  - Consistência de datas calculadas
  - Integridade referencial de dependências
  - Validação de JSON fields
- **Arquivo:** `migration/integrity_validator.py`

---

## 🔧 Scripts e Utilitários

### Scripts Principais
```bash
# Executar migração completa
python migration/migrate_real_epics.py

# Validar integridade dos dados
python migration/integrity_validator.py

# Recalcular durações
python duration_system/recalculate_durations.py

# Análise de épicos
python migration/epic_analyzer.py --source epics/user_epics/
```

### Testes de Integração
```bash
# Testar duration system completo
pytest tests/test_duration_system_integration.py -v

# Testar migração
pytest tests/test_epic_migration.py -v

# Validar performance
pytest tests/test_duration_performance.py -v
```

---

## 📈 Métricas de Sucesso

### Performance
- **Cálculo de duração:** < 10ms por épico
- **Migração completa:** < 5 minutos para 9 épicos
- **Queries JSON:** < 50ms para campos complexos

### Qualidade
- **Cobertura de testes:** ≥ 90% em todos os módulos
- **Integridade referencial:** 100% das dependências válidas
- **Compatibilidade:** 100% dos épicos migrados com sucesso

### Funcionalidade
- **Cálculo automático:** Duração calculada a partir de datas
- **Descrições amigáveis:** Mantidas e validadas
- **Dependências:** Sistema funcional com validação de ciclos
- **Dados ricos:** Goals, definition_of_done, labels preservados

---

## ⚠️ Riscos e Mitigações

### Riscos Técnicos
1. **Performance de JSON queries**
   - **Mitigação:** Indexes específicos, caching de queries frequentes

2. **Complexidade de dependências**
   - **Mitigação:** Validação incremental, testes de ciclos

3. **Migração de dados inconsistentes**
   - **Mitigação:** Validação prévia, rollback automático

### Riscos de Negócio
1. **Perda de dados durante migração**
   - **Mitigação:** Backup automático, validação completa

2. **Incompatibilidade com sistema existente**
   - **Mitigação:** Testes de regressão, migração gradual

---

## 📅 Cronograma Detalhado

| Fase | Tarefas | Tempo Estimado | Dependências |
|------|---------|----------------|--------------|
| **1** | Análise e Design | 3h | - |
| **2** | Duration System Core | 5h | Fase 1 |
| **3** | Dados Ricos | 4h | Fase 2 |
| **4** | Migration Engine | 3h | Fases 1-3 |
| **Total** | **15 horas** | **~2 dias** | - |

---

## 🚀 Próximos Passos Imediatos

1. **Iniciar Fase 1:** Análise detalhada do schema gap
2. **Criar branch:** `feature/duration-system`
3. **Setup inicial:** Estrutura de diretórios para duration_system/
4. **Primeira implementação:** DurationCalculator básico
5. **Testes:** Cobertura desde o início

---

*Plano criado: 2025-08-13*  
*Foco: Duration System - Primeiro Item da Migração*  
*Status: Pronto para Execução*