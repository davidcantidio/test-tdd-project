# 🛡️ CODEX PROMPT D: Exception Enhancement + Correlation IDs

## 🎯 **OBJETIVO**
Melhorar o sistema de exception handling já implementado (Patch 5) adicionando correlation IDs completos, user context preservation, enhanced recovery strategies e integration com todos os sistemas, resolvendo gaps de rastreabilidade e debugging.

## 📁 **ARQUIVOS ALVO (ISOLADOS)**
```
streamlit_extension/middleware/                   # Middleware layer
streamlit_extension/middleware/correlation.py     # Correlation ID management
streamlit_extension/middleware/context_manager.py # User context preservation
streamlit_extension/middleware/error_correlation.py # Error correlation system
streamlit_extension/utils/enhanced_recovery.py    # Enhanced recovery strategies
streamlit_extension/utils/error_analytics.py      # Error analytics & patterns
streamlit_extension/utils/correlation_logger.py   # Correlation-aware logging
tests/test_correlation_system.py                  # Correlation tests
tests/test_enhanced_recovery.py                   # Recovery strategy tests
```

## 🚨 **PROBLEMA IDENTIFICADO**
- Report.md: "No global exception handler"
- Report.md: "Raw error messages to users"
- Gap: Falta correlation IDs para debugging
- Gap: Context preservation across requests
- Enhancement: Recovery strategies limitadas

## 📋 **ESPECIFICAÇÕES TÉCNICAS**

### **1. correlation.py**
```python
# Sistema completo de correlation IDs:
# - UUID generation per request
# - Correlation propagation across calls
# - Thread-local storage
# - Cross-system correlation
# - Distributed tracing support
# - Request lifecycle tracking
```

### **2. context_manager.py**
```python
# Gerenciamento de contexto de usuário:
# - User session context
# - Request context preservation
# - Multi-tenant context
# - Security context
# - Performance context
# - Error context enrichment
```

### **3. enhanced_recovery.py**
```python
# Estratégias avançadas de recovery:
# - Circuit breaker integration
# - Graceful degradation patterns
# - Fallback chain execution
# - Auto-retry with backoff
# - Resource cleanup
# - State recovery mechanisms
```

## 🔧 **CORRELATION ID SYSTEM**

### **Correlation ID Generation:**
```python
class CorrelationManager:
    def __init__(self):
        self.correlation_context = threading.local()
        
    def generate_correlation_id(self) -> str:
        """Generate unique correlation ID"""
        return f"{uuid.uuid4().hex[:8]}-{int(time.time())}"
        
    def set_correlation_id(self, correlation_id: str):
        """Set correlation ID for current thread"""
        self.correlation_context.id = correlation_id
        
    def get_correlation_id(self) -> Optional[str]:
        """Get current correlation ID"""
        return getattr(self.correlation_context, 'id', None)
```

### **Request Lifecycle Tracking:**
```python
class RequestLifecycleTracker:
    def track_request_start(self, correlation_id: str, context: Dict):
        # Log request initiation
        # Set correlation context
        # Initialize metrics
        # Setup error tracking
        
    def track_request_end(self, correlation_id: str, status: str):
        # Log request completion
        # Calculate metrics
        # Cleanup context
        # Generate analytics
```

## 🔧 **USER CONTEXT PRESERVATION**

### **Context Data Structure:**
```python
@dataclass
class UserContext:
    user_id: Optional[str]
    session_id: str
    request_id: str
    correlation_id: str
    ip_address: str
    user_agent: str
    timestamp: datetime
    permissions: List[str]
    preferences: Dict[str, Any]
    performance_budget: Dict[str, float]
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize context for logging"""
        
    def sanitize_for_logging(self) -> Dict[str, Any]:
        """Remove sensitive data for logs"""
```

### **Context Middleware:**
```python
class ContextMiddleware:
    def process_request(self, request):
        # Extract user context
        # Generate correlation ID
        # Set thread-local context
        # Initialize tracking
        
    def process_response(self, response):
        # Add correlation headers
        # Log response metrics
        # Cleanup context
        # Update analytics
```

## 🔧 **ENHANCED RECOVERY STRATEGIES**

### **Recovery Strategy Interface:**
```python
class RecoveryStrategy(ABC):
    @abstractmethod
    def can_recover(self, error: Exception, context: UserContext) -> bool:
        """Check if this strategy can handle the error"""
        
    @abstractmethod
    def attempt_recovery(self, error: Exception, context: UserContext) -> RecoveryResult:
        """Attempt to recover from the error"""
        
    @abstractmethod
    def get_fallback(self, error: Exception, context: UserContext) -> Any:
        """Provide fallback result if recovery fails"""
```

### **Specific Recovery Implementations:**
```python
class DatabaseRecoveryStrategy(RecoveryStrategy):
    def attempt_recovery(self, error, context):
        if isinstance(error, OperationalError):
            # Try different connection
            # Retry with backoff
            # Switch to read-only mode
            # Use cached data
            
class AuthenticationRecoveryStrategy(RecoveryStrategy):
    def attempt_recovery(self, error, context):
        if isinstance(error, AuthenticationError):
            # Clear invalid tokens
            # Redirect to login
            # Provide guest access
            # Log security event
            
class ValidationRecoveryStrategy(RecoveryStrategy):
    def attempt_recovery(self, error, context):
        if isinstance(error, ValidationError):
            # Provide corrected data
            # Suggest valid inputs
            # Use default values
            # Guide user fix
```

## 🔧 **ERROR CORRELATION SYSTEM**

### **Error Pattern Detection:**
```python
class ErrorPatternAnalyzer:
    def analyze_error_patterns(self, correlation_id: str) -> ErrorPattern:
        """Analyze errors within correlation context"""
        related_errors = self.get_correlated_errors(correlation_id)
        
        return ErrorPattern(
            pattern_type=self.detect_pattern_type(related_errors),
            frequency=len(related_errors),
            time_span=self.calculate_time_span(related_errors),
            root_cause=self.identify_root_cause(related_errors),
            impact_scope=self.calculate_impact(related_errors)
        )
```

### **Cross-System Correlation:**
```python
class CrossSystemCorrelator:
    def correlate_distributed_errors(self, correlation_id: str):
        """Correlate errors across different systems"""
        # Database errors
        # Cache errors  
        # External API errors
        # UI errors
        # Background task errors
        
    def build_error_timeline(self, correlation_id: str) -> List[ErrorEvent]:
        """Build chronological error timeline"""
        events = self.collect_all_events(correlation_id)
        return sorted(events, key=lambda x: x.timestamp)
```

## 📊 **CORRELATION-AWARE LOGGING**

### **Enhanced Log Format:**
```python
LOG_FORMAT = {
    "timestamp": "2025-08-16T10:30:45.123Z",
    "level": "ERROR",
    "correlation_id": "a1b2c3d4-1692177045",
    "request_id": "req-uuid-here",
    "user_context": {
        "user_id": "user123",
        "session_id": "sess456", 
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0...",
        "permissions": ["read", "write"]
    },
    "error_context": {
        "exception_type": "DatabaseError",
        "message": "Connection timeout",
        "stack_trace": "...",
        "recovery_attempted": True,
        "recovery_success": False
    },
    "performance_metrics": {
        "response_time": 1200,
        "memory_usage": 245,
        "cpu_usage": 15
    },
    "business_context": {
        "operation": "create_client",
        "entity_id": "client_789",
        "workflow_step": "validation"
    }
}
```

### **Structured Error Logger:**
```python
class CorrelationLogger:
    def log_error_with_correlation(self, 
                                  error: Exception,
                                  context: UserContext,
                                  recovery_result: Optional[RecoveryResult] = None):
        """Log error with full correlation context"""
        
        log_entry = {
            "correlation_id": context.correlation_id,
            "error_chain": self.build_error_chain(error),
            "user_journey": self.trace_user_journey(context),
            "system_state": self.capture_system_state(),
            "recovery_actions": self.log_recovery_actions(recovery_result)
        }
        
        self.structured_logger.error(log_entry)
```

## 🔧 **INTEGRATION WITH EXISTING SYSTEMS**

### **Exception Handler Enhancement:**
```python
# Enhance existing global_exception_handler
class EnhancedGlobalExceptionHandler(GlobalExceptionHandler):
    def __init__(self):
        super().__init__()
        self.correlation_manager = CorrelationManager()
        self.context_manager = ContextManager()
        self.recovery_engine = RecoveryEngine()
        
    def handle_exception_with_correlation(self, 
                                        exception: Exception,
                                        request_context: Optional[Dict] = None):
        # Generate/get correlation ID
        correlation_id = self.correlation_manager.get_or_create()
        
        # Enrich context
        context = self.context_manager.build_context(request_context)
        
        # Attempt enhanced recovery
        recovery_result = self.recovery_engine.attempt_recovery(exception, context)
        
        # Log with correlation
        self.correlation_logger.log_error_with_correlation(exception, context, recovery_result)
        
        # Update error analytics
        self.error_analytics.record_error(exception, context, correlation_id)
        
        return self.create_enhanced_error_response(exception, context, recovery_result)
```

## 📈 **ERROR ANALYTICS & INSIGHTS**

### **Error Analytics Engine:**
```python
class ErrorAnalyticsEngine:
    def generate_error_insights(self, time_window: timedelta) -> ErrorInsights:
        """Generate actionable error insights"""
        
        insights = ErrorInsights(
            error_trends=self.analyze_error_trends(time_window),
            pattern_detection=self.detect_error_patterns(time_window),
            recovery_effectiveness=self.analyze_recovery_success(time_window),
            user_impact=self.calculate_user_impact(time_window),
            system_health=self.assess_system_health(time_window),
            recommendations=self.generate_recommendations()
        )
        
        return insights
```

### **Real-time Error Dashboard:**
```python
class ErrorDashboard:
    def show_correlation_view(self, correlation_id: str):
        """Show all events for a correlation ID"""
        # Error timeline
        # User journey map
        # System interaction trace
        # Recovery attempts
        # Impact assessment
        
    def show_pattern_analysis(self):
        """Show error pattern analysis"""
        # Recurring error patterns
        # Seasonal trends
        # User segment analysis
        # System component reliability
```

## ✅ **CASOS DE TESTE ESPECÍFICOS**

### **Correlation Tests:**
```python
class CorrelationSystemTest:
    def test_correlation_id_propagation(self):
        """Test correlation ID flows through all systems"""
        
    def test_cross_request_correlation(self):
        """Test correlation across multiple requests"""
        
    def test_correlation_in_async_operations(self):
        """Test correlation in background tasks"""
```

### **Enhanced Recovery Tests:**
```python
class EnhancedRecoveryTest:
    def test_multi_strategy_recovery(self):
        """Test recovery strategy chaining"""
        
    def test_context_aware_recovery(self):
        """Test recovery based on user context"""
        
    def test_recovery_performance_impact(self):
        """Test recovery doesn't degrade performance"""
```

## 🎯 **INTEGRATION SCENARIOS**

### **Streamlit Page Integration:**
```python
@handle_streamlit_exceptions(
    show_error=True, 
    attempt_recovery=True,
    correlation_aware=True,
    context_preservation=True
)
def enhanced_client_page():
    """Client page with full correlation support"""
    
    # Context automatically captured
    # Correlation ID in all logs
    # Enhanced recovery for DB errors
    # User journey tracking
```

### **Database Operation Integration:**
```python
@correlate_operation("database")
@with_enhanced_recovery([DatabaseRecoveryStrategy()])
def create_client_with_correlation(client_data: Dict) -> ClientResult:
    """Database operation with full correlation"""
    
    # All queries tagged with correlation ID
    # Enhanced error handling
    # Automatic retry with context
    # Performance tracking
```

## ✅ **CRITÉRIOS DE SUCESSO**

1. **100% Correlation Coverage:** Todos os endpoints têm correlation IDs
2. **Context Preservation:** User context mantido através de toda operação
3. **Enhanced Recovery:** 90%+ de recovery success rate
4. **Cross-System Tracing:** Rastreamento completo de operações distribuídas
5. **Performance Impact:** < 2% overhead com correlation
6. **Error Pattern Detection:** Identificação automática de padrões

## 🔧 **MONITORING & ALERTING**

```python
MONITORING_ALERTS = {
    "correlation_failure": {
        "condition": "correlation_id_missing > 1%",
        "severity": "HIGH",
        "action": "investigate_correlation_system"
    },
    "recovery_failure": {
        "condition": "recovery_success_rate < 85%",
        "severity": "MEDIUM", 
        "action": "review_recovery_strategies"
    },
    "error_pattern_detected": {
        "condition": "same_error_pattern > 10 times/hour",
        "severity": "HIGH",
        "action": "automated_investigation"
    }
}
```

## 🎯 **RESULTADO ESPERADO**

Sistema de exception handling aprimorado que:
- Fornece rastreabilidade completa com correlation IDs
- Preserva contexto do usuário através de todas operações
- Implementa recovery strategies avançadas e context-aware
- Gera insights acionáveis sobre padrões de erro
- Integra seamlessly com sistemas existentes
- Mantém performance com overhead mínimo
- Facilita debugging e troubleshooting

---

**🎯 RESULTADO FINAL:** Exception handling enterprise-grade com correlation IDs completos, context preservation, enhanced recovery strategies e error analytics, fornecendo visibilidade total e recuperação inteligente para debugging e operações de produção.