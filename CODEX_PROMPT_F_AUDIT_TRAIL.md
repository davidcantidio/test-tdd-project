# 📋 CODEX PROMPT F: Audit Trail System

## 🎯 **OBJETIVO**
Implementar sistema completo de audit trail para rastreamento de todas as operações do sistema, incluindo soft deletes e trilha de auditoria completa, conforme requisitos do report.md.

## 📁 **ARQUIVOS ALVO (ISOLADOS)**
```
streamlit_extension/utils/audit_trail.py               # Core audit trail system
streamlit_extension/utils/audit_logger.py              # Audit logging engine
streamlit_extension/utils/audit_storage.py             # Storage backend para audits
streamlit_extension/utils/audit_analyzer.py            # Análise de audit logs
migrations/004_audit_tables.sql                        # Schema para audit tables
migrations/005_audit_triggers.sql                      # Database triggers para audit
streamlit_extension/config/audit_config.py             # Configurações de auditoria
tests/test_audit_trail_system.py                       # Testes do sistema
```

## 🚨 **PROBLEMA IDENTIFICADO**
- Report.md: "Data loss on cascaded delete - Require soft delete + audit trail"
- Necessário rastreamento completo de todas as operações
- Audit trail para compliance e debugging
- Soft delete tracking para recovery

## 📋 **ESPECIFICAÇÕES TÉCNICAS**

### **1. audit_trail.py**
```python
# Sistema central de auditoria:
# - Tracking automático de CRUD operations
# - User action logging
# - Data change tracking (before/after)
# - Cascade operation tracking
# - Performance impact monitoring
```

### **2. audit_logger.py**
```python
# Engine de logging especializado:
# - Structured audit logging
# - Async logging para performance
# - Batch processing de audit events
# - Filtering e classification
# - Integration com correlation IDs
```

### **3. audit_storage.py**
```python
# Storage otimizado para audit:
# - Efficient audit record storage
# - Partitioning por data/tipo
# - Compression para long-term storage
# - Query optimization para audit searches
# - Retention policy management
```

### **4. audit_analyzer.py**
```python
# Análise de audit logs:
# - Pattern detection em operações
# - Anomaly detection
# - Compliance reporting
# - Forensic analysis tools
# - Data recovery assistance
```

## 🔧 **AUDIT TRAIL CATEGORIES**

### **1. Data Operations (CRUD):**
- **CREATE**: Novos registros criados
- **READ**: Acessos a dados sensíveis
- **UPDATE**: Modificações com before/after
- **DELETE**: Soft deletes com recovery info
- **RESTORE**: Recuperação de dados deleted

### **2. User Actions:**
- **AUTHENTICATION**: Login/logout events
- **AUTHORIZATION**: Permission checks
- **NAVIGATION**: Page access tracking
- **FORM_SUBMISSION**: Form data submissions
- **BULK_OPERATIONS**: Operações em massa

### **3. System Events:**
- **SYSTEM_STARTUP**: Inicialização do sistema
- **CONFIGURATION_CHANGE**: Mudanças de config
- **ERROR_EVENTS**: Erros e exceptions
- **PERFORMANCE_ALERTS**: Alertas de performance
- **SECURITY_EVENTS**: Eventos de segurança

### **4. Business Operations:**
- **CLIENT_LIFECYCLE**: Criação, update, delete de clientes
- **PROJECT_LIFECYCLE**: Operações em projetos
- **EPIC_LIFECYCLE**: Mudanças em epics
- **TASK_LIFECYCLE**: TDD phase transitions

## 🧪 **CASOS DE TESTE OBRIGATÓRIOS**

### **Basic Audit Trail Tests:**
```python
def test_crud_operation_tracking():
    # Tracking de operações CRUD
    
def test_soft_delete_audit():
    # Audit de soft deletes
    
def test_cascade_operation_tracking():
    # Tracking de operações em cascata
    
def test_data_change_logging():
    # Logging de mudanças before/after
    
def test_user_action_correlation():
    # Correlação com ações do usuário
```

### **Soft Delete Tests:**
```python
def test_soft_delete_implementation():
    # Implementação de soft delete
    
def test_soft_delete_cascade():
    # Soft delete em cascata
    
def test_data_recovery_from_audit():
    # Recovery de dados via audit
    
def test_permanent_delete_audit():
    # Audit de deletes permanentes
    
def test_soft_delete_listing():
    # Listagem de itens soft deleted
```

### **Compliance Tests:**
```python
def test_audit_log_immutability():
    # Imutabilidade dos audit logs
    
def test_audit_log_integrity():
    # Integridade dos logs
    
def test_gdpr_compliance_tracking():
    # Tracking para compliance GDPR
    
def test_retention_policy_enforcement():
    # Enforcement de políticas de retenção
    
def test_audit_trail_completeness():
    # Completude da trilha de auditoria
```

### **Performance Tests:**
```python
def test_audit_performance_impact():
    # Impacto de performance do audit
    
def test_async_audit_logging():
    # Performance do logging assíncrono
    
def test_audit_storage_efficiency():
    # Eficiência do storage
    
def test_bulk_audit_processing():
    # Processing de audit em massa
```

## 📊 **AUDIT LOG SCHEMA**

### **Core Audit Table:**
```sql
CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    correlation_id UUID NOT NULL,
    operation_type VARCHAR(50) NOT NULL,
    table_name VARCHAR(100),
    record_id INTEGER,
    user_id INTEGER,
    user_session_id VARCHAR(255),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT,
    before_data JSONB,
    after_data JSONB,
    operation_metadata JSONB,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    performance_metrics JSONB
);
```

### **Audit Indexes:**
```sql
-- Performance indexes
CREATE INDEX idx_audit_timestamp ON audit_log(timestamp);
CREATE INDEX idx_audit_user ON audit_log(user_id);
CREATE INDEX idx_audit_table_record ON audit_log(table_name, record_id);
CREATE INDEX idx_audit_correlation ON audit_log(correlation_id);
CREATE INDEX idx_audit_operation ON audit_log(operation_type);

-- Composite indexes para queries comuns
CREATE INDEX idx_audit_user_timestamp ON audit_log(user_id, timestamp);
CREATE INDEX idx_audit_table_timestamp ON audit_log(table_name, timestamp);
```

### **Soft Delete Enhancement:**
```sql
-- Adicionar campos de soft delete a todas as tabelas
ALTER TABLE framework_clients ADD COLUMN deleted_at TIMESTAMP;
ALTER TABLE framework_projects ADD COLUMN deleted_at TIMESTAMP;
ALTER TABLE framework_epics ADD COLUMN deleted_at TIMESTAMP;
ALTER TABLE framework_tasks ADD COLUMN deleted_at TIMESTAMP;

-- Triggers para audit automático
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    -- Insert audit record
    INSERT INTO audit_log (
        operation_type, table_name, record_id, 
        before_data, after_data, user_id, timestamp
    ) VALUES (
        TG_OP, TG_TABLE_NAME, 
        CASE WHEN TG_OP = 'DELETE' THEN OLD.id ELSE NEW.id END,
        CASE WHEN TG_OP = 'DELETE' THEN row_to_json(OLD) ELSE NULL END,
        CASE WHEN TG_OP = 'INSERT' THEN row_to_json(NEW) ELSE row_to_json(NEW) END,
        current_setting('app.current_user_id', true)::INTEGER,
        NOW()
    );
    
    RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END;
$$ LANGUAGE plpgsql;
```

## 🔗 **INTEGRAÇÃO COM SISTEMA EXISTENTE**

### **DatabaseManager Integration:**
```python
# Instrumentar DatabaseManager:
# - Audit decorators em todos os métodos CRUD
# - Automatic soft delete implementation
# - Before/after data capture
# - User context injection
```

### **Authentication Integration:**
```python
# Integração com sistema de auth:
# - User ID capture automático
# - Session tracking
# - Permission change logging
# - Login/logout audit
```

### **Correlation Integration:**
```python
# Integração com correlation IDs:
# - Audit logs com correlation IDs
# - Cross-operation tracking
# - Request-response correlation
# - End-to-end traceability
```

## 🚀 **CONFIGURAÇÃO DO AUDIT SYSTEM**

```python
AUDIT_CONFIG = {
    "enabled": True,
    "storage": {
        "backend": "database",  # database, file, elasticsearch
        "async_logging": True,
        "batch_size": 100,
        "flush_interval": 30  # seconds
    },
    "tracking": {
        "crud_operations": True,
        "user_actions": True,
        "system_events": True,
        "performance_metrics": True,
        "data_changes": True
    },
    "soft_delete": {
        "enabled": True,
        "cascade_mode": "soft",  # soft, hard, mixed
        "retention_period": 365,  # days
        "permanent_delete_audit": True
    },
    "compliance": {
        "gdpr_mode": True,
        "data_retention": 2555,  # days (7 years)
        "audit_immutability": True,
        "encryption_at_rest": True
    },
    "performance": {
        "max_impact_threshold": 0.05,  # 5% max overhead
        "async_processing": True,
        "compression": True,
        "partitioning": "monthly"
    }
}
```

## 📈 **AUDIT ANALYTICS**

### **Operational Analytics:**
```python
# Analytics de operações:
# - Most frequent operations
# - Peak usage times
# - User activity patterns
# - Error frequency analysis
```

### **Security Analytics:**
```python
# Analytics de segurança:
# - Suspicious activity detection
# - Access pattern analysis
# - Privilege escalation attempts
# - Data access anomalies
```

### **Compliance Analytics:**
```python
# Analytics para compliance:
# - Data access tracking
# - Retention policy compliance
# - GDPR right to be forgotten
# - Audit completeness reports
```

## ✅ **CRITÉRIOS DE SUCESSO**

1. **Complete Tracking**: 100% das operações CRUD auditadas
2. **Soft Delete Implementation**: Soft deletes em todas as entidades
3. **Data Recovery**: Recovery completo via audit trail
4. **Performance Impact**: <5% overhead em operações normais
5. **Compliance Ready**: GDPR e SOX compliance
6. **Forensic Capability**: Investigação completa de incidents

## 🔧 **IMPLEMENTAÇÃO TÉCNICA**

### **Async Audit Logging:**
```python
# Logging assíncrono para performance:
# - Queue-based processing
# - Batch inserts para efficiency
# - Background thread processing
# - Graceful degradation em falhas
```

### **Data Change Tracking:**
```python
# Tracking detalhado de mudanças:
# - JSON diff para before/after
# - Field-level change tracking
# - Nested object change detection
# - Efficient storage de deltas
```

### **Storage Optimization:**
```python
# Otimizações de storage:
# - Table partitioning por data
# - Compression para dados antigos
# - Index optimization para queries
# - Archival para long-term storage
```

## 🎯 **CENÁRIOS ESPECÍFICOS TDD FRAMEWORK**

### **Client/Project Audit:**
- Criação, modificação, delete de clientes
- Mudanças em projetos e relacionamentos
- Cascade operations tracking
- Business rule violation logging

### **Epic/Task Audit:**
- TDD phase transitions
- Status changes e workflow
- Task dependency modifications
- Bulk operations tracking

### **User Activity Audit:**
- Login/logout tracking
- Page navigation patterns
- Form submission attempts
- Permission usage tracking

### **System Operations Audit:**
- Configuration changes
- Database maintenance operations
- Performance tuning changes
- Security policy modifications

---

**🎯 RESULTADO ESPERADO:** Sistema completo de audit trail que fornece rastreabilidade total, implementa soft deletes seguros, permite data recovery e satisfaz requisitos de compliance, resolvendo gaps críticos do report.md.