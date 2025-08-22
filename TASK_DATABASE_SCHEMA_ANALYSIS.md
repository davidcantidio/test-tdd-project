# 📊 ESQUEMA ATUAL DO BANCO DE DADOS - TAREFAS (TASKS)

## 🎯 **OBJETIVO**
Este documento apresenta o esquema atual da tabela `framework_tasks` e estruturas relacionadas para análise e possível otimização. O objetivo é gerar um novo esquema mais adequado ao projeto TDD Framework com foco em TDAH e produtividade.

---

## 🗄️ **ESQUEMA ATUAL DA TABELA TASKS**

### **📋 Tabela Principal: `framework_tasks`**
```sql
CREATE TABLE IF NOT EXISTS framework_tasks (
    -- Identificação
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_key VARCHAR(50) NOT NULL,
    epic_id INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- TDD (Test-Driven Development)
    tdd_phase VARCHAR(20) CHECK(tdd_phase IN ('analysis', 'red', 'green', 'refactor', 'review')),
    tdd_order INTEGER,
    
    -- Status e Workflow
    status VARCHAR(50) DEFAULT 'pending',
    task_type TEXT DEFAULT 'implementation',
    
    -- Estimativas e Tracking
    estimate_minutes INTEGER NOT NULL DEFAULT 60,
    actual_minutes INTEGER DEFAULT 0,
    story_points INTEGER DEFAULT 1,
    position INTEGER,
    
    -- Priorização
    priority INTEGER DEFAULT 3,  -- 1=crítico, 5=backlog
    
    -- Gamificação
    points_earned INTEGER DEFAULT 0,
    difficulty_modifier DECIMAL(3,2) DEFAULT 1.0,
    streak_bonus INTEGER DEFAULT 0,
    perfectionist_bonus INTEGER DEFAULT 0,
    
    -- GitHub Integration
    github_issue_number INTEGER,
    github_branch VARCHAR(255),
    github_pr_number INTEGER,
    
    -- Multi-user
    assigned_to INTEGER,
    reviewer_id INTEGER,
    
    -- Auditoria
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    reviewed_at TIMESTAMP NULL,
    deleted_at TIMESTAMP NULL,
    due_date TIMESTAMP NULL,
    
    FOREIGN KEY (epic_id) REFERENCES framework_epics(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_to) REFERENCES framework_users(id),
    FOREIGN KEY (reviewer_id) REFERENCES framework_users(id)
);
```

### **🔗 Tabelas Relacionadas**

#### **1. Épicos (framework_epics)**
```sql
CREATE TABLE IF NOT EXISTS framework_epics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    epic_key VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 1,
    
    -- Outras colunas relacionadas a épicos...
    FOREIGN KEY (project_id) REFERENCES framework_projects(id) ON DELETE CASCADE
);
```

#### **2. Sessões de Trabalho (work_sessions)**
```sql
CREATE TABLE IF NOT EXISTS work_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    task_id INTEGER,
    epic_id INTEGER,
    
    -- Session data
    session_type VARCHAR(50) DEFAULT 'work',
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_minutes INTEGER,
    
    -- Productivity metrics
    focus_score DECIMAL(3,2),
    interruptions_count INTEGER DEFAULT 0,
    
    -- TDAH support
    energy_level INTEGER CHECK(energy_level BETWEEN 1 AND 10),
    mood_rating INTEGER CHECK(mood_rating BETWEEN 1 AND 10),
    notes TEXT,
    
    FOREIGN KEY (user_id) REFERENCES framework_users(id),
    FOREIGN KEY (task_id) REFERENCES framework_tasks(id),
    FOREIGN KEY (epic_id) REFERENCES framework_epics(id)
);
```

---

## 📊 **ESTRUTURA ATUAL DOS DADOS JSON (ÉPICOS)**

### **Estrutura de Tarefas nos Arquivos JSON**
Baseado na análise dos arquivos de épicos, as tarefas possuem a seguinte estrutura:

```json
{
  "id": "0.1",
  "title": "Mapear comportamento atual do warning_suppressor",
  "description": "Executar o pipeline...",
  
  // Estimativas
  "story_points": 15,
  "estimate_minutes": 45,
  
  // TDD
  "tdd_phase": "red",  // red, green, refactor, analysis
  "tdd_order": 1,
  "tdd_skip_reason": "Analysis/documentation task",
  
  // Detalhamento
  "acceptance_criteria": [
    "Lista de padrões suprimidos com exemplos reais de logs",
    "Diferenças de saída documentadas (antes/depois)"
  ],
  "deliverables": [
    "docs/compat/warning_suppressor_report.md",
    "artefato de logs (logs/warning_suppressor_sample.log)"
  ],
  "test_specs": [
    "test_module_0_3_should_arquivo_envexample_criado"
  ],
  "test_plan": [
    "Rodar pipeline em modo DEV com e sem supressor e comparar logs"
  ],
  
  // Organização
  "dependencies": [],
  "branch": "refactor",
  "files_touched": [],
  "parent_task_key": "0.3",
  "task_group": "0.3",
  "task_sequence": 1,
  
  // Risco
  "risk": "Padrões implícitos não documentados mascararem problemas",
  "mitigation": "Ampliar amostra e ativar logging detalhado temporário",
  
  // Classificação
  "task_type": "analysis",
  "priority": 3,
  "task_labels": ["analysis", "documentation"],
  "priority_tags": ["compatibility"]
}
```

---

## 🎯 **CAMPOS IDENTIFICADOS NO MODELO ATUAL**

### **✅ Campos Básicos (Já Implementados)**
- `id`, `task_key`, `epic_id`, `title`, `description`
- `tdd_phase`, `status`, `estimate_minutes`, `actual_minutes`
- `story_points`, `priority`, `created_at`, `updated_at`
- `assigned_to`, `reviewer_id`

### **❓ Campos Parcialmente Implementados**
- `tdd_order` (presente no modelo Python, questionável no banco)
- `task_type` (presente no JSON e modelo Python)
- `position` (presente no banco, mas pouco usado)

### **❌ Campos Ausentes (Presentes no JSON/Modelo)**
1. **Detalhamento de Tarefas:**
   - `acceptance_criteria` (JSON array)
   - `deliverables` (JSON array)
   - `test_specs` (JSON array)
   - `test_plan` (JSON array)
   - `files_touched` (JSON array)

2. **Dependências e Organização:**
   - `dependencies` (JSON array)
   - `parent_task_key` (STRING)
   - `task_group` (STRING)
   - `task_sequence` (INTEGER)

3. **Classificação e Metadados:**
   - `task_labels` (JSON array)
   - `priority_tags` (JSON array)
   - `branch` (STRING)

4. **Gestão de Riscos:**
   - `risk` (TEXT)
   - `mitigation` (TEXT)
   - `tdd_skip_reason` (TEXT)

5. **Flexibilidade e Contexto:**
   - `context_data` (JSON)
   - `custom_fields` (JSON)
   - `metadata` (JSON)

---

## 🚀 **PROBLEMAS IDENTIFICADOS NO ESQUEMA ATUAL**

### **🔴 Limitações Críticas**

1. **Falta de Detalhamento:**
   - Não há campos para acceptance criteria detalhados
   - Ausência de deliverables específicos
   - Test specs não são rastreados no banco

2. **Dependências Inadequadas:**
   - Sistema de dependências não modelado adequadamente
   - Hierarquia de tarefas (parent/child) não suportada
   - Agrupamento lógico limitado

3. **Flexibilidade Limitada:**
   - Campos JSON ausentes para dados dinâmicos
   - Classificação/tagging inadequada
   - Contexto de negócio limitado

4. **TDD Integration Incompleta:**
   - Apenas `tdd_phase` básico, sem detalhamento
   - Sem rastreamento de test requirements
   - Ausência de métricas de qualidade TDD

### **🟡 Limitações de Usabilidade**

1. **TDAH Support Limitado:**
   - Sem campos para complexidade cognitiva
   - Ausência de tempo estimado de foco
   - Sem classificação de energia necessária

2. **Gamificação Básica:**
   - Campos de pontuação presentes mas limitados
   - Sem sistema de achievement tracking
   - Ausência de métricas de progresso detalhadas

3. **Reporting e Analytics Limitados:**
   - Poucos campos para métricas detalhadas
   - Ausência de contexto de negócio
   - Campos de auditoria básicos

---

## 📈 **MÉTRICAS E ESTATÍSTICAS ATUAIS**

### **📊 Dados do Projeto Atual**
- **Total de Épicos:** 12
- **Total de Tarefas:** 206
- **Hierarquia:** Client → Project → Epic → Task
- **TDD Phases:** 5 (analysis, red, green, refactor, review)
- **Status Types:** ~8 diferentes (pending, in_progress, completed, etc.)
- **Priority Levels:** 1-5 (1=crítico, 5=backlog)

### **🎯 Campos Mais Utilizados**
1. `title`, `description` (100% das tarefas)
2. `tdd_phase` (80%+ das tarefas)
3. `estimate_minutes`, `story_points` (95%+ das tarefas)
4. `acceptance_criteria` (90%+ via JSON)
5. `test_specs` (60%+ das tarefas TDD)

### **❌ Campos Subutilizados**
1. `actual_minutes` (preenchido em <30% das tarefas)
2. `reviewer_id` (usado em <20% das tarefas)
3. `github_*` fields (projeto ainda não integrado)
4. Campos de gamificação (pouco utilizados)

---

## 🎮 **CONTEXTO DO PROJETO TDD FRAMEWORK**

### **🎯 Missão Principal**
Framework enterprise para metodologia TDD com suporte a TDAH e gamificação de produtividade.

### **👥 Usuários Alvo**
- Desenvolvedores com TDAH
- Equipes praticando TDD
- Gerentes de projeto
- Profissionais buscando produtividade

### **🔧 Requisitos Especiais**
1. **TDAH Support:**
   - Quebra de tarefas complexas
   - Estimativa de tempo de foco
   - Gestão de interrupções
   - Feedback imediato

2. **TDD Integration:**
   - Rastreamento completo de ciclos Red-Green-Refactor
   - Métricas de qualidade de testes
   - Progressão de fases
   - Validação de completude

3. **Gamificação:**
   - Sistema de pontos e achievements
   - Progress tracking visual
   - Streaks e bonificações
   - Motivação contínua

4. **Enterprise Features:**
   - Multi-user support
   - Hierarquia client/project/epic/task
   - Auditoria completa
   - Reporting detalhado

---

## 🔍 **ANÁLISE DE CASOS DE USO**

### **📋 Casos de Uso Principais**

1. **Criação de Tarefa TDD:**
   - Definir requirements e acceptance criteria
   - Especificar test specs e deliverables
   - Estimar complexidade e tempo de foco
   - Classificar com labels e prioridade

2. **Execução de Ciclo TDD:**
   - Rastrear progressão Red → Green → Refactor
   - Validar completion criteria de cada fase
   - Medir effectiveness e quality metrics
   - Registrar learnings e improvements

3. **Gestão de Dependências:**
   - Mapear dependências entre tarefas
   - Gerenciar hierarquia parent/child
   - Agrupar tarefas logicamente
   - Ordenar execução otimizada

4. **TDAH Productivity Support:**
   - Estimar cognitive load
   - Quebrar tarefas complexas
   - Sugerir timing ótimo
   - Rastrear interruptions

5. **Reporting e Analytics:**
   - Métricas de TDD effectiveness
   - Produtividade individual/equipe
   - Progress tracking visual
   - Identificação de bottlenecks

### **🎯 Requisitos de Performance**
- Queries < 10ms (atualmente atingido)
- Support para 1000+ tarefas simultâneas
- Real-time updates
- Offline capability

---

## 📊 **SUGESTÕES PARA NOVO ESQUEMA**

### **🎯 Objetivos da Reformulação**
1. **Flexibilidade:** Suporte a dados dinâmicos via JSON
2. **Detalhamento:** Campos específicos para TDD e TDAH
3. **Escalabilidade:** Estrutura que cresce com o projeto
4. **Performance:** Índices otimizados para queries comuns
5. **Usabilidade:** Campos intuitivos e bem documentados

### **🔧 Áreas de Melhoria Prioritárias**
1. **JSON Fields:** Para dados flexíveis e evolutivos
2. **Dependency System:** Sistema robusto de dependências
3. **TDD Enhancement:** Campos específicos para metodologia TDD
4. **TDAH Support:** Campos para cognitive load e focus management
5. **Advanced Analytics:** Campos para métricas detalhadas

---

## ✅ **CONCLUSÃO**

O esquema atual da tabela `framework_tasks` fornece uma base sólida, mas possui limitações significativas para um framework TDD enterprise com suporte TDAH. 

**Pontos Fortes:**
- Estrutura básica bem definida
- Relacionamentos corretos
- Auditoria básica implementada
- Performance adequada

**Principais Gaps:**
- Falta de campos JSON para flexibilidade
- Sistema de dependências inadequado
- TDD support limitado
- TDAH features ausentes
- Detalhamento insuficiente

**Recomendação:** Evolução incremental do esquema mantendo compatibilidade, com adição de campos JSON para flexibilidade e campos específicos para TDD/TDAH optimization.

---

## 📋 **PRÓXIMOS PASSOS SUGERIDOS**

1. **Análise com ChatGPT** para gerar novo esquema otimizado
2. **Migração incremental** mantendo compatibilidade
3. **Testes de performance** com novo esquema
4. **Validação com usuários** reais do framework
5. **Documentação** completa do novo modelo

---

*Documento gerado para análise e otimização do esquema de banco de dados do TDD Framework*
*Data: 2025-08-22 | Versão: 1.0*