# ⚡ CODEX PROMPT B: Load Testing Suite Completa

## 🎯 **OBJETIVO**
Implementar suite completa de load testing e performance testing para identificar bottlenecks, estabelecer baselines e simular cenários de stress, resolvendo o gap crítico "Load/performance testing absent" do report.md.

## 📁 **ARQUIVOS ALVO (ISOLADOS)**
```
tests/load_testing/                              # Diretório principal de load tests
tests/load_testing/test_load_crud.py            # Load test para operações CRUD
tests/load_testing/test_load_concurrent.py      # Testes de concorrência
tests/load_testing/test_load_stress.py          # Stress testing extremo
tests/load_testing/test_load_endurance.py       # Endurance/soak testing
streamlit_extension/utils/load_tester.py        # Engine de load testing
streamlit_extension/utils/performance_monitor.py # Monitor de performance
streamlit_extension/utils/metrics_collector.py   # Coletor de métricas
tests/load_testing/scenarios/                    # Cenários de teste
tests/load_testing/reports/                      # Relatórios de performance
```

## 🚨 **PROBLEMA IDENTIFICADO**
- Report.md: "Load/performance testing absent; stress scenarios not simulated"
- Severity: HIGH
- Impact: Performance desconhecida, bottlenecks não identificados
- Risk: Sistema pode falhar sob carga em produção

## 📋 **ESPECIFICAÇÕES TÉCNICAS**

### **1. load_tester.py**
```python
# Engine principal de load testing:
# - Geração de carga configurável
# - Simulação de usuários virtuais
# - Ramp-up/ramp-down patterns
# - Request distribution
# - Response time tracking
# - Error rate monitoring
```

### **2. performance_monitor.py**
```python
# Monitor de performance em tempo real:
# - CPU usage tracking
# - Memory consumption
# - Database query performance
# - Network latency
# - Thread/process monitoring
# - Resource bottleneck detection
```

### **3. metrics_collector.py**
```python
# Coletor e agregador de métricas:
# - Response time percentiles (P50, P95, P99)
# - Throughput (req/s)
# - Error rates
# - Resource utilization
# - Concurrent users
# - Transaction success rate
```

## 🔧 **TIPOS DE TESTES IMPLEMENTADOS**

### **1. Load Testing (Normal Load)**
```python
# Simula carga normal esperada:
# - 50-100 usuários concorrentes
# - Operações típicas do dia-a-dia
# - Duração: 15-30 minutos
# - Objetivo: Validar performance normal
```

### **2. Stress Testing (Peak Load)**
```python
# Simula picos de carga:
# - 200-500 usuários concorrentes
# - Burst de requisições
# - Duração: 5-10 minutos
# - Objetivo: Encontrar ponto de quebra
```

### **3. Spike Testing (Sudden Load)**
```python
# Simula picos súbitos:
# - 0 → 1000 usuários em 1 minuto
# - Load instantâneo
# - Duração: 2-5 minutos
# - Objetivo: Testar elasticidade
```

### **4. Endurance Testing (Soak Test)**
```python
# Simula carga prolongada:
# - 100 usuários constantes
# - Duração: 2-8 horas
# - Objetivo: Detectar memory leaks
```

### **5. Volume Testing (Data Load)**
```python
# Testa com grandes volumes:
# - 1M+ registros no database
# - Queries complexas
# - Bulk operations
# - Objetivo: Performance com big data
```

## 🧪 **CENÁRIOS DE TESTE ESPECÍFICOS**

### **CRUD Operations Load Test:**
```python
class CRUDLoadTest:
    def test_create_client_load(self):
        """100 criações simultâneas de clientes"""
        
    def test_read_pagination_load(self):
        """1000 leituras com paginação"""
        
    def test_update_concurrent_load(self):
        """50 updates simultâneos"""
        
    def test_delete_cascade_load(self):
        """Delete em cascata sob carga"""
```

### **Concurrent User Scenarios:**
```python
class ConcurrentUserTest:
    def test_multi_user_workflow(self):
        """50 usuários executando workflow completo"""
        
    def test_concurrent_form_submission(self):
        """100 submissões simultâneas"""
        
    def test_session_management_load(self):
        """200 sessões ativas"""
        
    def test_authentication_spike(self):
        """500 logins simultâneos"""
```

### **Database Performance Tests:**
```python
class DatabaseLoadTest:
    def test_connection_pool_saturation(self):
        """Saturação do pool de conexões"""
        
    def test_complex_query_load(self):
        """Queries complexas sob carga"""
        
    def test_transaction_deadlock_scenario(self):
        """Cenário de deadlock simulado"""
        
    def test_bulk_insert_performance(self):
        """Insert de 10k registros"""
```

## 📊 **MÉTRICAS COLETADAS**

### **Performance Metrics:**
```python
METRICS = {
    "response_time": {
        "min": 0,
        "max": 0,
        "mean": 0,
        "median": 0,
        "p95": 0,
        "p99": 0
    },
    "throughput": {
        "requests_per_second": 0,
        "transactions_per_second": 0,
        "bytes_per_second": 0
    },
    "errors": {
        "total_errors": 0,
        "error_rate": 0,
        "error_types": {}
    },
    "resources": {
        "cpu_usage": 0,
        "memory_usage": 0,
        "disk_io": 0,
        "network_io": 0
    }
}
```

### **SLA Targets:**
```python
SLA_TARGETS = {
    "response_time_p95": 2000,  # ms
    "response_time_p99": 5000,  # ms
    "error_rate": 0.01,          # 1%
    "availability": 0.999,       # 99.9%
    "throughput_min": 100,       # req/s
    "concurrent_users": 200      # users
}
```

## 🚀 **LOAD TESTING FRAMEWORK**

### **Load Generator Configuration:**
```python
class LoadGenerator:
    def __init__(self, config):
        self.users = config['users']
        self.ramp_up = config['ramp_up']
        self.duration = config['duration']
        self.scenario = config['scenario']
        
    def generate_load(self):
        # Thread pool para usuários virtuais
        # Rate limiting configurável
        # Request patterns realistas
        # Session management
```

### **Scenario Definition:**
```python
SCENARIOS = {
    "normal_day": {
        "users": 100,
        "ramp_up": 60,
        "duration": 1800,
        "think_time": 5,
        "actions": ["login", "browse", "create", "update", "logout"]
    },
    "black_friday": {
        "users": 1000,
        "ramp_up": 10,
        "duration": 3600,
        "think_time": 1,
        "actions": ["login", "search", "filter", "paginate"]
    },
    "maintenance_window": {
        "users": 10,
        "ramp_up": 5,
        "duration": 300,
        "think_time": 10,
        "actions": ["health_check", "status"]
    }
}
```

## 📈 **RELATÓRIOS E VISUALIZAÇÃO**

### **Report Generation:**
```python
class PerformanceReporter:
    def generate_html_report(self, metrics):
        # Gráficos de response time
        # Throughput over time
        # Error rate visualization
        # Resource utilization charts
        # Comparative analysis
        
    def generate_csv_export(self, metrics):
        # Raw data export
        # Time series data
        # Detailed metrics
```

### **Real-time Dashboard:**
```python
class LoadTestDashboard:
    def show_realtime_metrics(self):
        # Live response times
        # Current throughput
        # Active users
        # Error rate
        # System resources
```

## 🔧 **INTEGRAÇÃO COM CI/CD**

```yaml
# GitHub Actions Integration:
name: Performance Testing
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  pull_request:
    types: [opened, synchronize]

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - name: Run Load Tests
        run: python -m pytest tests/load_testing/ --benchmark
      
      - name: Check Performance Regression
        run: python check_performance_regression.py
      
      - name: Upload Results
        uses: actions/upload-artifact@v2
        with:
          name: performance-report
          path: tests/load_testing/reports/
```

## 🎯 **BOTTLENECKS ESPERADOS**

### **Identificação de Bottlenecks:**
1. **Database queries sem índices**
   - Solução: Adicionar índices apropriados
   
2. **N+1 query problems**
   - Solução: Eager loading, query optimization
   
3. **Session management overhead**
   - Solução: Session caching, Redis integration
   
4. **Serialization/deserialization**
   - Solução: Optimized serializers, caching

5. **Connection pool exhaustion**
   - Solução: Pool tuning, connection reuse

## ✅ **CRITÉRIOS DE SUCESSO**

1. **Coverage:** 100% dos endpoints testados
2. **Performance Baseline:** Estabelecido para todas as operações
3. **Bottlenecks:** Todos identificados e documentados
4. **SLA Compliance:** 95%+ das métricas dentro do target
5. **Regression Detection:** Sistema automático funcionando
6. **Documentation:** Relatórios completos gerados

## 🔧 **FERRAMENTAS E BIBLIOTECAS**

```python
DEPENDENCIES = {
    "locust": "2.17.0",      # Load testing framework
    "pytest-benchmark": "4.0.0",  # Benchmarking
    "memory-profiler": "0.61.0",  # Memory profiling
    "py-spy": "0.3.14",      # CPU profiling
    "psutil": "5.9.6",       # System monitoring
    "matplotlib": "3.7.3",    # Visualization
    "pandas": "2.1.3",       # Data analysis
}
```

## 📊 **EXEMPLO DE OUTPUT**

```
====== LOAD TEST RESULTS ======
Test: CRUD Operations
Duration: 1800 seconds
Virtual Users: 100

RESPONSE TIMES:
  Min: 12ms
  Max: 4521ms
  Mean: 187ms
  Median: 142ms
  P95: 412ms
  P99: 892ms

THROUGHPUT:
  Requests/sec: 245.3
  Success Rate: 99.7%
  
ERRORS:
  Total: 14
  Rate: 0.3%
  Types:
    - Timeout: 8
    - Connection: 6

RESOURCES:
  CPU Peak: 67%
  Memory Peak: 1.2GB
  DB Connections: 8/10

BOTTLENECKS IDENTIFIED:
1. Slow query in get_client_projects() - 800ms avg
2. Memory spike during bulk delete - 400MB
3. Connection pool near limit at peak

RECOMMENDATIONS:
1. Add index on projects.client_id
2. Implement pagination for large deletes
3. Increase connection pool to 15
================================
```

## 🎯 **RESULTADO ESPERADO**

Suite completa de load testing que:
- Identifica todos os bottlenecks de performance
- Estabelece baselines confiáveis
- Simula cenários realistas de produção
- Detecta regressões automaticamente
- Gera relatórios acionáveis
- Integra com CI/CD pipeline

---

**🎯 RESULTADO FINAL:** Sistema completo de load testing com múltiplos cenários, métricas detalhadas, identificação automática de bottlenecks e relatórios acionáveis, resolvendo completamente o gap de performance testing do report.md.