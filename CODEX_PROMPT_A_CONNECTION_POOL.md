# 🔧 CODEX PROMPT A: Connection Pool Fix + DB Resilience

## 🎯 **OBJETIVO**
Resolver o teste que trava (`test_connection_pool_limit`) e implementar sistema de resiliência para o banco de dados com circuit breakers e retry logic, conforme requisitos do report.md.

## 📁 **ARQUIVOS ALVO (ISOLADOS)**
```
tests/test_connection_pool_fix.py          # Novo teste para connection pool
streamlit_extension/utils/db_resilience.py # Sistema de resiliência DB
streamlit_extension/utils/circuit_breaker.py # Circuit breaker pattern
```

## 🚨 **PROBLEMA IDENTIFICADO**
- Teste `test_connection_pool_limit` trava durante execução (hanging)
- Indica possível deadlock ou vazamento de conexões
- Necessário implementar circuit breakers e retry logic

## 📋 **ESPECIFICAÇÕES TÉCNICAS**

### **1. test_connection_pool_fix.py**
```python
# Criar teste robusto que:
# - Testa limites de pool de conexões sem travar
# - Verifica liberação adequada de conexões
# - Testa cenários de timeout
# - Valida comportamento sob carga
# - Inclui testes de deadlock prevention
```

### **2. db_resilience.py**
```python
# Sistema de resiliência que inclui:
# - Connection retry logic (exponential backoff)
# - Connection timeout management
# - Pool monitoring e health checks
# - Graceful degradation
# - Connection leak detection
```

### **3. circuit_breaker.py**
```python
# Circuit breaker pattern para DB:
# - Estados: CLOSED, OPEN, HALF_OPEN
# - Threshold de falhas configurável
# - Timeout de recuperação
# - Métricas de falhas/sucessos
# - Integration com DatabaseManager
```

## 🔧 **REQUISITOS FUNCIONAIS**

### **Connection Pool Management:**
1. **Timeout Control**: Conexões com timeout configurável (5-30s)
2. **Pool Size Limits**: Máximo 20 conexões simultâneas
3. **Leak Detection**: Identificar conexões não liberadas
4. **Health Monitoring**: Status do pool em tempo real

### **Circuit Breaker Logic:**
1. **Failure Threshold**: 5 falhas consecutivas → OPEN
2. **Recovery Timeout**: 60s em estado OPEN → HALF_OPEN
3. **Success Recovery**: 3 sucessos consecutivos → CLOSED
4. **Metrics Collection**: Falhas, sucessos, estado atual

### **Retry Logic:**
1. **Exponential Backoff**: 1s, 2s, 4s, 8s, 16s
2. **Max Retries**: 5 tentativas
3. **Jitter**: ±25% para evitar thundering herd
4. **Conditional Retry**: Apenas para erros recuperáveis

## 🧪 **CASOS DE TESTE OBRIGATÓRIOS**

### **Connection Pool Tests:**
```python
def test_connection_pool_limit_no_hang():
    # Testa limite sem travar
    
def test_connection_leak_detection():
    # Detecta vazamentos
    
def test_connection_timeout_handling():
    # Testa timeouts
    
def test_pool_exhaustion_recovery():
    # Recuperação após esgotamento
```

### **Circuit Breaker Tests:**
```python
def test_circuit_breaker_open_on_failures():
    # Abre após falhas
    
def test_circuit_breaker_half_open_recovery():
    # Transição para half-open
    
def test_circuit_breaker_closed_on_success():
    # Fecha após sucessos
```

### **Retry Logic Tests:**
```python
def test_retry_exponential_backoff():
    # Testa backoff exponencial
    
def test_retry_max_attempts():
    # Respeita limite de tentativas
    
def test_retry_conditional_logic():
    # Retry apenas em erros recuperáveis
```

## 📊 **MÉTRICAS E MONITORING**

### **Pool Metrics:**
- Conexões ativas/inativas
- Tempo médio de uso
- Taxa de timeout
- Vazamentos detectados

### **Circuit Breaker Metrics:**
- Estado atual (OPEN/CLOSED/HALF_OPEN)
- Taxa de falhas
- Tempo em cada estado
- Última falha/recuperação

### **Retry Metrics:**
- Tentativas por operação
- Taxa de sucesso após retry
- Tempo total de retry
- Tipos de erro mais comuns

## 🔗 **INTEGRAÇÃO COM SISTEMA EXISTENTE**

### **DatabaseManager Integration:**
```python
# Modificar DatabaseManager para usar:
# - db_resilience.ConnectionPool
# - circuit_breaker.DatabaseCircuitBreaker
# - Retry decorators automáticos
```

### **Health Check Integration:**
```python
# Adicionar ao health check:
# - Status do circuit breaker
# - Métricas do pool
# - Últimas falhas de conexão
```

## 🚀 **CONFIGURAÇÃO PADRÃO**

```python
DB_RESILIENCE_CONFIG = {
    "pool": {
        "max_connections": 20,
        "timeout": 30,
        "leak_detection": True
    },
    "circuit_breaker": {
        "failure_threshold": 5,
        "recovery_timeout": 60,
        "success_threshold": 3
    },
    "retry": {
        "max_attempts": 5,
        "base_delay": 1.0,
        "max_delay": 16.0,
        "jitter": 0.25
    }
}
```

## ✅ **CRITÉRIOS DE SUCESSO**

1. **Teste não trava**: `test_connection_pool_fix.py` executa em <30s
2. **Circuit breaker funcional**: Abre/fecha conforme configuração
3. **Retry logic efetiva**: Recupera de falhas temporárias
4. **Pool management**: Não há vazamentos de conexão
5. **Integration**: Funciona com DatabaseManager existente
6. **Performance**: Overhead <5% nas operações normais

## 🔧 **IMPLEMENTAÇÃO TÉCNICA**

### **Error Categories:**
```python
# Recoverable errors (retry allowed):
# - Connection timeout
# - Temporary connection failure
# - Pool exhaustion

# Non-recoverable errors (fail fast):
# - Authentication failure
# - Database not found
# - SQL syntax errors
```

### **Thread Safety:**
- Todos os componentes thread-safe
- Locks minimizados para performance
- Atomic operations para contadores

### **Logging Integration:**
- Structured logging para todas as operações
- Correlation IDs para rastreamento
- Debug logs para troubleshooting

---

**🎯 RESULTADO ESPERADO:** Sistema robusto que resolve o hanging test e adiciona resiliência enterprise ao banco de dados, eliminando um dos principais gaps do report.md.