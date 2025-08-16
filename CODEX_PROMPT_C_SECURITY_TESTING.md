# 🔒 CODEX PROMPT C: Security Testing XSS/CSRF Suite

## 🎯 **OBJETIVO**
Implementar suite completa de testes de segurança para validar proteções contra XSS, CSRF, SQL injection e outras vulnerabilidades, conforme gap crítico identificado no report.md.

## 📁 **ARQUIVOS ALVO (ISOLADOS)**
```
tests/security_testing/                         # Diretório exclusivo para security tests
├── test_xss_protection.py                     # Testes de XSS prevention
├── test_csrf_protection.py                    # Testes de CSRF tokens
├── test_sql_injection.py                      # Testes de SQL injection
├── test_input_validation.py                   # Validação de inputs
├── test_auth_security.py                      # Testes de autenticação
├── test_session_security.py                   # Security de sessões
└── conftest.py                                # Fixtures de security testing

streamlit_extension/utils/security_test_runner.py  # Engine de security testing
streamlit_extension/utils/attack_simulator.py      # Simulador de ataques
streamlit_extension/utils/vulnerability_scanner.py # Scanner de vulnerabilidades
```

## 🚨 **PROBLEMA IDENTIFICADO**
- Report.md: "Security testing lacks XSS/CSRF scenarios"
- Gap crítico em validação de proteções implementadas
- Necessário verificar eficácia das defesas
- Automatizar detecção de vulnerabilidades

## 📋 **ESPECIFICAÇÕES TÉCNICAS**

### **1. security_test_runner.py**
```python
# Engine principal que coordena:
# - Execução automática de security tests
# - Simulação de ataques controlados
# - Coleta de evidências de proteção
# - Relatórios de vulnerabilidades
# - Integration com CI/CD pipeline
```

### **2. attack_simulator.py**
```python
# Simulador de ataques reais:
# - Payloads XSS (reflected, stored, DOM-based)
# - CSRF attacks (GET/POST/PUT/DELETE)
# - SQL injection (union, blind, boolean)
# - Path traversal attempts
# - Command injection vectors
```

### **3. vulnerability_scanner.py**
```python
# Scanner automatizado:
# - Static analysis de código
# - Dynamic testing de endpoints
# - Dependency vulnerability scan
# - Configuration security check
# - OWASP Top 10 validation
```

## 🔧 **CATEGORIAS DE SECURITY TESTING**

### **1. XSS Protection Testing:**
- **Reflected XSS**: Inputs em formulários
- **Stored XSS**: Dados persistidos no DB
- **DOM-based XSS**: Manipulação client-side
- **Filter Bypass**: Tentativas de bypass
- **Context-aware Encoding**: Validação por contexto

### **2. CSRF Protection Testing:**
- **Token Validation**: Presença e validação de tokens
- **Double Submit**: Cookie vs header validation
- **Origin/Referer Check**: Header validation
- **State Changing Operations**: POST/PUT/DELETE protection
- **Ajax Request Protection**: API endpoint security

### **3. SQL Injection Testing:**
- **Union-based**: Extração de dados
- **Blind Boolean**: Inferência de dados
- **Time-based Blind**: Delays para confirmação
- **Error-based**: Informação via erros
- **Prepared Statements**: Validação de proteção

### **4. Input Validation Testing:**
- **Length Limits**: Buffer overflow prevention
- **Special Characters**: Encoding e sanitização
- **File Upload**: Tipo e tamanho de arquivos
- **Format Validation**: Email, phone, date formats
- **Business Logic**: Regras de negócio

## 🧪 **CASOS DE TESTE OBRIGATÓRIOS**

### **XSS Tests (test_xss_protection.py):**
```python
def test_client_name_xss_protection():
    # Testa XSS em nome do cliente
    payload = "<script>alert('xss')</script>"
    # Deve ser sanitizado/encoded
    
def test_project_description_stored_xss():
    # XSS persistido em descrição
    
def test_search_form_reflected_xss():
    # XSS refletido em busca
    
def test_url_parameter_xss():
    # XSS via parâmetros URL
    
def test_filter_bypass_attempts():
    # Tentativas de bypass dos filtros
```

### **CSRF Tests (test_csrf_protection.py):**
```python
def test_client_creation_csrf_token():
    # Token CSRF em criação de cliente
    
def test_project_update_csrf_protection():
    # Proteção CSRF em updates
    
def test_delete_operation_csrf():
    # CSRF em operações DELETE
    
def test_ajax_request_csrf():
    # Proteção em requests AJAX
    
def test_csrf_token_refresh():
    # Renovação de tokens
```

### **SQL Injection Tests (test_sql_injection.py):**
```python
def test_client_search_sql_injection():
    # SQL injection em busca de clientes
    payload = "'; DROP TABLE clients; --"
    
def test_project_filter_sql_injection():
    # Injection em filtros de projeto
    
def test_blind_sql_injection():
    # Blind SQL injection
    
def test_union_based_injection():
    # Union-based injection
    
def test_parametrized_query_protection():
    # Validação de queries parametrizadas
```

### **Input Validation Tests (test_input_validation.py):**
```python
def test_email_format_validation():
    # Validação de formato de email
    
def test_phone_number_validation():
    # Validação de telefone
    
def test_field_length_limits():
    # Limites de comprimento
    
def test_special_character_handling():
    # Caracteres especiais
    
def test_file_upload_validation():
    # Validação de uploads
```

## 🔍 **PAYLOADS DE TESTE**

### **XSS Payloads:**
```python
XSS_PAYLOADS = [
    "<script>alert('xss')</script>",
    "<img src=x onerror=alert('xss')>",
    "javascript:alert('xss')",
    "<svg onload=alert('xss')>",
    "'><script>alert('xss')</script>",
    "\"><script>alert('xss')</script>",
    "<iframe src=javascript:alert('xss')>",
    "<%73%63%72%69%70%74>alert('xss')<%2f%73%63%72%69%70%74>",
    "<scr<script>ipt>alert('xss')</scr</script>ipt>",
    "<SCRIPT SRC=http://xss.rocks/xss.js></SCRIPT>"
]
```

### **SQL Injection Payloads:**
```python
SQL_INJECTION_PAYLOADS = [
    "' OR '1'='1",
    "'; DROP TABLE users; --",
    "' UNION SELECT username, password FROM users --",
    "' AND (SELECT COUNT(*) FROM users) > 0 --",
    "' OR 1=1 --",
    "'; WAITFOR DELAY '00:00:05' --",
    "' OR pg_sleep(5) --",
    "' UNION SELECT 1,2,3,4,5 --",
    "' AND substring(version(),1,1) = '5",
    "'; INSERT INTO users VALUES('hacker','password'); --"
]
```

### **CSRF Attack Vectors:**
```python
CSRF_VECTORS = [
    "missing_csrf_token",
    "invalid_csrf_token", 
    "expired_csrf_token",
    "csrf_token_reuse",
    "cross_origin_request",
    "referer_header_missing",
    "content_type_bypass",
    "method_override_attack"
]
```

## 📊 **SECURITY METRICS**

### **Vulnerability Metrics:**
- **XSS Protection Rate**: % de inputs protegidos
- **CSRF Coverage**: % de endpoints protegidos
- **SQL Injection Resistance**: % de queries seguras
- **Input Validation**: % de campos validados
- **Authentication Bypass**: Tentativas de bypass

### **Attack Simulation Results:**
- **Successful Attacks**: Ataques que passaram
- **Blocked Attacks**: Ataques bloqueados
- **False Positives**: Falsos positivos detectados
- **Response Time**: Tempo de detecção/bloqueio
- **Evidence Collection**: Logs de ataques

## 🔗 **INTEGRAÇÃO COM SISTEMA EXISTENTE**

### **Security Stack Integration:**
```python
# Testar integração com:
# - CSRF middleware implementado
# - XSS protection filters
# - Input validation system
# - Authentication system
```

### **Monitoring Integration:**
```python
# Integrar com sistema de monitoring:
# - Security alerts em tempo real
# - Attack attempt logging
# - Threat intelligence feeds
# - Incident response automation
```

## 🚀 **CONFIGURAÇÃO DE SECURITY TESTS**

```python
SECURITY_TEST_CONFIG = {
    "xss_testing": {
        "payload_sets": ["basic", "advanced", "evasion"],
        "contexts": ["html", "javascript", "css", "url"],
        "encoding_tests": True,
        "filter_bypass": True
    },
    "csrf_testing": {
        "token_validation": True,
        "origin_check": True,
        "referer_check": True,
        "double_submit": True
    },
    "sql_injection": {
        "payload_types": ["union", "blind", "error", "time"],
        "database_types": ["sqlite", "postgresql", "mysql"],
        "parameter_types": ["get", "post", "cookie", "header"]
    },
    "reporting": {
        "detailed_logs": True,
        "evidence_collection": True,
        "false_positive_analysis": True,
        "remediation_suggestions": True
    }
}
```

## 📈 **AUTOMATED SECURITY SCANNING**

### **Static Analysis:**
```python
# Análise estática do código:
# - Bandit security linting
# - SAST (Static Application Security Testing)
# - Dependency vulnerability scanning
# - Configuration security review
```

### **Dynamic Analysis:**
```python
# Análise dinâmica durante execução:
# - DAST (Dynamic Application Security Testing)
# - Interactive testing (IAST)
# - Runtime protection validation
# - Behavior-based detection
```

## ✅ **CRITÉRIOS DE SUCESSO**

1. **Complete Coverage**: Todos os endpoints testados para XSS/CSRF
2. **Attack Simulation**: Ataques reais simulados e bloqueados
3. **Zero False Negatives**: Vulnerabilidades reais detectadas
4. **Automated Execution**: Testes executam automaticamente no CI/CD
5. **Clear Reporting**: Relatórios detalhados com evidências
6. **Remediation Guidance**: Sugestões claras de correção

## 🔧 **IMPLEMENTAÇÃO TÉCNICA**

### **Test Framework:**
```python
# Usar pytest com plugins de security:
# - pytest-security
# - pytest-bandit
# - pytest-html para relatórios
```

### **Request Manipulation:**
```python
# Manipulação de requests para testes:
# - Modificação de headers
# - Payload injection
# - Cookie manipulation
# - Session hijacking simulation
```

### **Evidence Collection:**
```python
# Coleta de evidências:
# - Request/response logging
# - Screenshot capture
# - Error message analysis
# - Time-based correlation
```

## 🎯 **CENÁRIOS ESPECÍFICOS TDD FRAMEWORK**

### **Client/Project Security:**
- XSS em campos de nome/descrição
- CSRF em CRUD operations
- SQL injection em filtros/busca
- Authorization bypass testing

### **Epic/Task Security:**
- Stored XSS em conteúdo de tasks
- CSRF em mudanças de status
- Privilege escalation testing
- Data access control validation

---

**🎯 RESULTADO ESPERADO:** Suite completa de security testing que valida eficácia das proteções implementadas, identifica vulnerabilidades residuais e automatiza security validation, resolvendo gap crítico do report.md.