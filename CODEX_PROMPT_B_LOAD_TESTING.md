# ⚡ CODEX PROMPT B: Load Testing Suite Completa

## 🎯 **OBJETIVO**
Implementar sistema completo de load testing e stress testing para identificar bottlenecks de performance e validar limites do sistema, conforme gap identificado no report.md.

## 📁 **ARQUIVOS ALVO (ISOLADOS)**
```
tests/load_testing/                              # Diretório exclusivo
├── test_load_basic.py                          # Testes básicos de carga
├── test_load_stress.py                         # Testes de stress
├── test_load_concurrent.py                     # Testes de concorrência
├── test_load_database.py                       # Load testing específico DB
└── conftest.py                                 # Fixtures para load testing

streamlit_extension/utils/load_tester_advanced.py # Engine de load testing
streamlit_extension/utils/stress_simulator.py     # Simulador de stress
streamlit_extension/utils/performance_profiler.py # Profiler avançado
```

## 🚨 **PROBLEMA IDENTIFICADO**
- Report.md: "Load/performance testing absent; stress scenarios not simulated"
- Necessário validar comportamento sob carga
- Identificar limites de concorrência
- Teste de degradação gradual

## 📋 **ESPECIFICAÇÕES TÉCNICAS**

### **1. load_tester_advanced.py**
```python
# Engine principal que inclui:
# - Geração de carga configurável (1-1000 usuários)
# - Métricas de latência (p50, p95, p99)
# - Throughput measurement (req/s)
# - Resource utilization tracking
# - Automated bottleneck detection
```

### **2. stress_simulator.py**
```python
# Simulador de cenários extremos:
# - Spike testing (carga súbita)
# - Soak testing (carga prolongada)
# - Volume testing (grandes datasets)
# - Memory leak detection
# - Connection exhaustion scenarios
```

### **3. performance_profiler.py**
```python
# Profiler detalhado:
# - CPU profiling durante load tests
# - Memory usage tracking
# - Database query analysis
# - I/O bottleneck identification
# - Cache hit/miss ratios
```

## 🔧 **REQUISITOS FUNCIONAIS**

### **Load Testing Scenarios:**
1. **Basic Load**: 10-50 usuários simultâneos
2. **Peak Load**: 100-200 usuários simultâneos  
3. **Stress Load**: 500-1000 usuários simultâneos
4. **Spike Load**: 0→500→0 usuários em 30s
5. **Soak Load**: 100 usuários por 30 minutos

### **Database Load Testing:**
1. **CRUD Operations**: Create, Read, Update, Delete sob carga
2. **Complex Queries**: Joins e agregações pesadas
3. **Concurrent Access**: Múltiplas threads no mesmo registro
4. **Transaction Load**: Commit/rollback sob stress
5. **Connection Pool**: Esgotamento e recuperação

### **Streamlit UI Load Testing:**
1. **Page Rendering**: Tempo de carregamento das páginas
2. **Form Submissions**: Envio simultâneo de formulários
3. **Real-time Updates**: Atualizações em tempo real
4. **Session Management**: Múltiplas sessões ativas
5. **Cache Performance**: Eficiência do cache Streamlit

## 🧪 **CASOS DE TESTE OBRIGATÓRIOS**

### **Basic Load Tests (test_load_basic.py):**
```python
def test_concurrent_client_creation():
    # 50 clientes criados simultaneamente
    
def test_concurrent_project_queries():
    # 100 consultas simultâneas
    
def test_pagination_under_load():
    # Paginação com múltiplos usuários
    
def test_cache_performance_load():
    # Performance do cache sob carga
```

### **Stress Tests (test_load_stress.py):**
```python
def test_database_connection_exhaustion():
    # Esgotamento do pool de conexões
    
def test_memory_usage_under_stress():
    # Uso de memória em stress
    
def test_response_time_degradation():
    # Degradação dos tempos de resposta
    
def test_recovery_after_stress():
    # Recuperação após stress
```

### **Concurrency Tests (test_load_concurrent.py):**
```python
def test_concurrent_form_submissions():
    # Envios simultâneos de formulários
    
def test_race_condition_detection():
    # Detecção de race conditions
    
def test_deadlock_prevention():
    # Prevenção de deadlocks
    
def test_data_consistency_concurrent():
    # Consistência sob concorrência
```

### **Database Load Tests (test_load_database.py):**
```python
def test_heavy_query_performance():
    # Queries pesadas sob carga
    
def test_bulk_insert_performance():
    # Inserções em massa
    
def test_cascade_delete_load():
    # Deletes em cascata
    
def test_transaction_rollback_load():
    # Rollbacks sob carga
```

## 📊 **MÉTRICAS E BENCHMARKS**

### **Performance Targets:**
- **Response Time**: p95 < 2s, p99 < 5s
- **Throughput**: >100 req/s para operações CRUD
- **Concurrency**: 200 usuários simultâneos sem degradação
- **Memory**: <500MB por 100 usuários
- **CPU**: <80% utilização em peak load

### **Database Targets:**
- **Query Time**: Queries complexas <1s
- **Connection Pool**: 20 conexões máximas
- **Transaction Rate**: >50 tx/s
- **Lock Wait Time**: <100ms média

### **Streamlit Targets:**
- **Page Load**: <3s primeira carga
- **Cache Hit**: >80% para dados frequentes
- **Session Size**: <50MB por sessão
- **Real-time Updates**: <500ms latência

## 🔗 **INTEGRAÇÃO COM SISTEMA EXISTENTE**

### **DatabaseManager Integration:**
```python
# Instrumentar DatabaseManager para:
# - Coletar métricas durante load tests
# - Monitorar pool de conexões
# - Tracking de query performance
```

### **Cache Integration:**
```python
# Testar cache Redis:
# - Hit/miss ratios sob carga
# - Eviction policies
# - Memory usage patterns
```

### **Monitoring Integration:**
```python
# Integrar com sistema de monitoring:
# - Prometheus metrics durante tests
# - Grafana dashboards para visualização
# - Alertas para thresholds
```

## 🚀 **CONFIGURAÇÃO DE LOAD TESTS**

```python
LOAD_TEST_CONFIG = {
    "basic_load": {
        "users": 50,
        "ramp_up": 30,  # seconds
        "duration": 300,  # seconds
        "operations": ["create_client", "list_projects", "view_epic"]
    },
    "stress_load": {
        "users": 1000,
        "ramp_up": 60,
        "duration": 600,
        "operations": ["all_crud_operations"]
    },
    "spike_load": {
        "spike_users": 500,
        "spike_duration": 30,
        "base_users": 10
    },
    "soak_load": {
        "users": 100,
        "duration": 1800  # 30 minutes
    }
}
```

## 📈 **REPORTING E ANÁLISE**

### **Report Generation:**
```python
# Gerar relatórios automaticamente:
# - Performance summary
# - Bottleneck identification  
# - Resource utilization charts
# - Recommendations for optimization
```

### **Automated Analysis:**
```python
# Análise automática para detectar:
# - Memory leaks
# - Performance regressions
# - Concurrency issues
# - Resource bottlenecks
```

## ✅ **CRITÉRIOS DE SUCESSO**

1. **Comprehensive Coverage**: Todos os cenários de load testados
2. **Performance Baselines**: Métricas de baseline estabelecidas
3. **Bottleneck Identification**: Gargalos identificados e documentados
4. **Automated Execution**: Testes executam automaticamente
5. **Clear Reporting**: Relatórios claros com recomendações
6. **Integration**: Funciona com monitoring existente

## 🔧 **IMPLEMENTAÇÃO TÉCNICA**

### **Load Generation:**
```python
# Usar asyncio para concorrência eficiente
# - aiohttp para requests HTTP
# - asyncpg para conexões DB assíncronas
# - Controle preciso de timing
```

### **Metrics Collection:**
```python
# Coletar métricas detalhadas:
# - Latência por operação
# - Throughput por endpoint
# - Resource utilization
# - Error rates
```

### **Test Data Management:**
```python
# Gestão de dados de teste:
# - Cleanup automático após testes
# - Dados realistas para cenários
# - Isolation entre test runs
```

### **Parallel Execution:**
```python
# Execução paralela eficiente:
# - Thread pools para I/O
# - Process pools para CPU-intensive
# - Resource management
```

## 🎯 **CENÁRIOS ESPECÍFICOS DO TDD FRAMEWORK**

### **Epic/Task Load:**
- Criação de 1000 epics simultaneamente
- Atualização de status de 500 tasks
- Consultas complexas de analytics
- Geração de relatórios pesados

### **Client/Project Load:**
- 100 clientes com 10 projetos cada
- Consultas hierárquicas complexas
- Filtros e ordenação sob carga
- Export de dados em massa

---

**🎯 RESULTADO ESPERADO:** Sistema completo de load testing que identifica limites, valida performance targets e fornece insights para otimização, resolvendo gap crítico do report.md.