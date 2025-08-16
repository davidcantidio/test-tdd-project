# 🔒 CODEX PROMPT G: Security Testing XSS/CSRF Suite

## 🎯 **OBJETIVO**
Implementar suite completa de testes de segurança XSS/CSRF conforme gap identificado no report.md: "Security testing lacks XSS/CSRF scenarios".

## 📁 **ARQUIVOS ALVO (ISOLADOS - SEM INTERSEÇÃO)**
```
tests/test_security_xss_csrf.py                    # Suite principal de testes
streamlit_extension/utils/security_testing.py      # Utilities de teste de segurança  
tests/security_scenarios/                          # Cenários de teste
tests/security_scenarios/__init__.py               # Package init
tests/security_scenarios/xss_payloads.py          # Payloads XSS
tests/security_scenarios/csrf_scenarios.py        # Cenários CSRF
```

## 📋 **ESPECIFICAÇÕES TÉCNICAS**

### **1. tests/test_security_xss_csrf.py**
```python
# Implementar TestSecurityXSS e TestSecurityCSRF classes
# - test_xss_script_injection()
# - test_xss_html_injection() 
# - test_xss_attribute_injection()
# - test_csrf_form_submission()
# - test_csrf_ajax_requests()
# - test_csrf_token_validation()
# - test_input_sanitization()
# - test_output_encoding()
```

### **2. streamlit_extension/utils/security_testing.py**
```python
# XSSTestHelper class:
# - generate_xss_payloads()
# - test_input_sanitization()
# - validate_output_encoding()

# CSRFTestHelper class:
# - generate_csrf_tokens()
# - validate_csrf_protection()
# - simulate_csrf_attacks()

# SecurityTestRunner class:
# - run_security_suite()
# - generate_security_report()
```

### **3. tests/security_scenarios/xss_payloads.py**
```python
# XSS_PAYLOADS dictionary com:
# - Script injection payloads
# - HTML injection payloads  
# - Attribute injection payloads
# - Event handler injections
# - DOM-based XSS vectors
```

### **4. tests/security_scenarios/csrf_scenarios.py**
```python
# CSRF_SCENARIOS dictionary com:
# - Form-based CSRF attacks
# - AJAX CSRF attacks
# - JSON CSRF attacks
# - GET-based CSRF
# - Cross-origin scenarios
```

## 🧪 **CASOS DE TESTE OBRIGATÓRIOS**

### **XSS Testing:**
```python
def test_xss_client_description_field():
    # Teste XSS no campo description de clients
    
def test_xss_project_name_field():
    # Teste XSS no campo name de projects
    
def test_xss_reflected_in_error_messages():
    # Teste XSS refletido em mensagens de erro
    
def test_xss_stored_in_database():
    # Teste XSS armazenado no banco
```

### **CSRF Testing:**
```python
def test_csrf_client_creation():
    # Teste CSRF na criação de clients
    
def test_csrf_project_update():
    # Teste CSRF na atualização de projects
    
def test_csrf_bulk_operations():
    # Teste CSRF em operações em lote
    
def test_csrf_token_rotation():
    # Teste rotação de tokens CSRF
```

## 🎯 **CRITÉRIOS DE SUCESSO**
1. **15+ testes de segurança** implementados
2. **100% cobertura** dos campos de input identificados
3. **Payloads realísticos** baseados em OWASP Top 10
4. **Relatórios detalhados** de vulnerabilidades encontradas
5. **Zero dependências** de arquivos existentes modificados

## 🔗 **INTEGRAÇÃO**
- Executar com: `python -m pytest tests/test_security_xss_csrf.py -v`
- Gerar relatório: `SecurityTestRunner().generate_security_report()`
- Isolado: Não modifica arquivos existentes do projeto

---

**🎯 RESULTADO ESPERADO:** Suite completa de testes de segurança que identifica e documenta vulnerabilidades XSS/CSRF, resolvendo gap crítico do report.md.