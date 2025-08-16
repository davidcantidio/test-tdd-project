# 🚦 CODEX PROMPT E: Rate Limiting System

## 🎯 **OBJETIVO**
Implementar sistema completo de rate limiting enterprise para prevenir DoS attacks, brute-force attempts e garantir fair usage, resolvendo o gap crítico "Lack of rate limiting (CVSS 5.5)" do report.md com proteção multi-camada.

## 📁 **ARQUIVOS ALVO (ISOLADOS)**
```
streamlit_extension/middleware/rate_limiting/     # Rate limiting middleware
streamlit_extension/middleware/rate_limiting/core.py # Core rate limiter
streamlit_extension/middleware/rate_limiting/algorithms.py # Rate limiting algorithms
streamlit_extension/middleware/rate_limiting/storage.py # Storage backends
streamlit_extension/middleware/rate_limiting/policies.py # Rate limiting policies
streamlit_extension/utils/rate_limiter.py         # Rate limiter utilities
streamlit_extension/utils/fair_usage.py           # Fair usage enforcement
streamlit_extension/utils/dos_protection.py       # DoS protection system
tests/test_rate_limiting_comprehensive.py         # Comprehensive tests
tests/test_dos_protection.py                      # DoS protection tests
```

## 🚨 **PROBLEMA IDENTIFICADO**
- Report.md: "Lack of rate limiting (CVSS 5.5)"
- Report.md: "Streamlit endpoints unprotected from brute-force"
- Severity: CRITICAL (P0)
- Attack Vector: DoS, Brute-force, Resource exhaustion
- Impact: Service unavailability, legitimate user denial

## 📋 **ESPECIFICAÇÕES TÉCNICAS**

### **1. core.py**
```python
# Core rate limiting engine:
# - Multiple algorithm support (Token Bucket, Sliding Window, Fixed Window)
# - Multi-tier rate limiting (IP, User, API Key)
# - Distributed rate limiting support
# - Redis/Memory backend
# - Custom rate limit policies
# - Real-time enforcement
```

### **2. algorithms.py**
```python
# Rate limiting algorithms:
# - Token Bucket Algorithm
# - Sliding Window Algorithm  
# - Fixed Window Algorithm
# - Sliding Window Counter
# - Exponential Backoff
# - Adaptive Rate Limiting
```

### **3. policies.py**
```python
# Rate limiting policies:
# - User tier-based limits
# - Endpoint-specific limits
# - Geographic rate limits
# - Time-based rate limits
# - Burst handling policies
# - Whitelist/blacklist support
```

## 🔧 **RATE LIMITING ALGORITHMS**

### **Token Bucket Algorithm:**
```python
class TokenBucketRateLimiter:
    def __init__(self, capacity: int, refill_rate: float, refill_period: float = 1.0):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.refill_period = refill_period
        self.tokens = capacity
        self.last_refill = time.time()
        
    def is_allowed(self, tokens_requested: int = 1) -> bool:
        """Check if request is allowed"""
        self._refill_tokens()
        
        if self.tokens >= tokens_requested:
            self.tokens -= tokens_requested
            return True
        return False
        
    def _refill_tokens(self):
        """Refill tokens based on time elapsed"""
        now = time.time()
        elapsed = now - self.last_refill
        tokens_to_add = (elapsed / self.refill_period) * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now
```

### **Sliding Window Algorithm:**
```python
class SlidingWindowRateLimiter:
    def __init__(self, window_size: int, max_requests: int):
        self.window_size = window_size
        self.max_requests = max_requests
        self.requests = deque()
        
    def is_allowed(self, timestamp: float = None) -> bool:
        """Check if request is allowed in sliding window"""
        if timestamp is None:
            timestamp = time.time()
            
        # Remove old requests outside window
        cutoff_time = timestamp - self.window_size
        while self.requests and self.requests[0] <= cutoff_time:
            self.requests.popleft()
            
        # Check if under limit
        if len(self.requests) < self.max_requests:
            self.requests.append(timestamp)
            return True
        return False
```

### **Adaptive Rate Limiting:**
```python
class AdaptiveRateLimiter:
    def __init__(self, base_limit: int, adaptation_factor: float = 0.1):
        self.base_limit = base_limit
        self.current_limit = base_limit
        self.adaptation_factor = adaptation_factor
        self.success_rate = 1.0
        
    def adapt_limits(self, success_rate: float):
        """Adapt limits based on system performance"""
        if success_rate < 0.95:  # System under stress
            self.current_limit = max(1, int(self.current_limit * (1 - self.adaptation_factor)))
        elif success_rate > 0.99:  # System healthy
            self.current_limit = min(self.base_limit, int(self.current_limit * (1 + self.adaptation_factor)))
```

## 🔧 **MULTI-TIER RATE LIMITING**

### **User Tier Configuration:**
```python
USER_TIER_LIMITS = {
    "free": {
        "requests_per_minute": 60,
        "requests_per_hour": 1000,
        "requests_per_day": 10000,
        "burst_capacity": 10,
        "concurrent_connections": 5
    },
    "premium": {
        "requests_per_minute": 300,
        "requests_per_hour": 10000,
        "requests_per_day": 100000,
        "burst_capacity": 50,
        "concurrent_connections": 20
    },
    "enterprise": {
        "requests_per_minute": 1000,
        "requests_per_hour": 50000,
        "requests_per_day": 1000000,
        "burst_capacity": 200,
        "concurrent_connections": 100
    },
    "admin": {
        "requests_per_minute": -1,  # Unlimited
        "requests_per_hour": -1,
        "requests_per_day": -1,
        "burst_capacity": 1000,
        "concurrent_connections": 500
    }
}
```

### **Endpoint-Specific Limits:**
```python
ENDPOINT_LIMITS = {
    "/api/auth/login": {
        "rate_limit": "5 per 5 minutes",
        "algorithm": "sliding_window",
        "block_duration": 900,  # 15 minutes
        "progressive_delay": True
    },
    "/api/client/create": {
        "rate_limit": "10 per minute",
        "algorithm": "token_bucket",
        "burst_capacity": 3
    },
    "/api/search": {
        "rate_limit": "100 per minute",
        "algorithm": "sliding_window",
        "adaptive": True
    },
    "/api/bulk/*": {
        "rate_limit": "1 per 10 seconds",
        "algorithm": "fixed_window",
        "queue_enabled": True
    }
}
```

## 🔧 **DOS PROTECTION SYSTEM**

### **Attack Detection:**
```python
class DoSProtectionSystem:
    def __init__(self):
        self.attack_patterns = AttackPatternDetector()
        self.ip_reputation = IPReputationService()
        self.behavior_analyzer = BehaviorAnalyzer()
        
    def detect_attack(self, request_info: RequestInfo) -> AttackAssessment:
        """Detect potential DoS attack"""
        
        # Pattern-based detection
        pattern_score = self.attack_patterns.analyze(request_info)
        
        # IP reputation check
        reputation_score = self.ip_reputation.check(request_info.ip)
        
        # Behavioral analysis
        behavior_score = self.behavior_analyzer.analyze(request_info)
        
        # Combine scores
        attack_probability = self.calculate_attack_probability(
            pattern_score, reputation_score, behavior_score
        )
        
        return AttackAssessment(
            probability=attack_probability,
            threat_level=self.classify_threat_level(attack_probability),
            recommended_action=self.get_recommended_action(attack_probability)
        )
```

### **Progressive Rate Limiting:**
```python
class ProgressiveRateLimiter:
    def __init__(self):
        self.violation_counts = {}
        self.progressive_delays = [1, 5, 15, 60, 300, 900]  # seconds
        
    def get_delay_for_violations(self, identifier: str, violations: int) -> int:
        """Calculate progressive delay based on violations"""
        if violations == 0:
            return 0
            
        delay_index = min(violations - 1, len(self.progressive_delays) - 1)
        return self.progressive_delays[delay_index]
        
    def record_violation(self, identifier: str):
        """Record rate limit violation"""
        self.violation_counts[identifier] = self.violation_counts.get(identifier, 0) + 1
        
    def reset_violations(self, identifier: str):
        """Reset violation count after good behavior"""
        if identifier in self.violation_counts:
            del self.violation_counts[identifier]
```

## 🔧 **STORAGE BACKENDS**

### **Redis Backend:**
```python
class RedisRateLimitStorage:
    def __init__(self, redis_client):
        self.redis = redis_client
        
    def get_request_count(self, key: str, window_start: int, window_size: int) -> int:
        """Get request count for time window"""
        window_end = window_start + window_size
        return self.redis.zcount(key, window_start, window_end)
        
    def add_request(self, key: str, timestamp: float, ttl: int):
        """Add request to sliding window"""
        pipe = self.redis.pipeline()
        pipe.zadd(key, {str(uuid.uuid4()): timestamp})
        pipe.expire(key, ttl)
        pipe.execute()
        
    def cleanup_old_requests(self, key: str, cutoff_timestamp: float):
        """Remove old requests outside window"""
        self.redis.zremrangebyscore(key, 0, cutoff_timestamp)
```

### **Memory Backend:**
```python
class MemoryRateLimitStorage:
    def __init__(self):
        self.data = {}
        self.lock = threading.RLock()
        
    def get_bucket_state(self, key: str) -> Dict[str, Any]:
        """Get token bucket state"""
        with self.lock:
            return self.data.get(key, {
                "tokens": 0,
                "last_refill": time.time()
            })
            
    def update_bucket_state(self, key: str, tokens: float, last_refill: float):
        """Update token bucket state"""
        with self.lock:
            self.data[key] = {
                "tokens": tokens,
                "last_refill": last_refill
            }
```

## 🔧 **FAIR USAGE ENFORCEMENT**

### **Usage Monitoring:**
```python
class FairUsageMonitor:
    def __init__(self):
        self.usage_tracker = UsageTracker()
        self.quota_manager = QuotaManager()
        
    def check_fair_usage(self, user_id: str, resource: str) -> UsageAssessment:
        """Check if user is within fair usage limits"""
        
        current_usage = self.usage_tracker.get_usage(user_id, resource)
        quota = self.quota_manager.get_quota(user_id, resource)
        
        usage_percentage = (current_usage / quota) * 100
        
        return UsageAssessment(
            current_usage=current_usage,
            quota=quota,
            percentage=usage_percentage,
            is_fair=usage_percentage <= 100,
            warning_threshold=usage_percentage > 80,
            action_required=usage_percentage > 95
        )
```

### **Resource Throttling:**
```python
class ResourceThrottler:
    def __init__(self):
        self.throttle_policies = {}
        
    def apply_throttling(self, user_id: str, resource: str, usage_percentage: float):
        """Apply progressive throttling based on usage"""
        
        if usage_percentage > 95:
            return ThrottleAction.BLOCK
        elif usage_percentage > 90:
            return ThrottleAction.SEVERE_LIMIT
        elif usage_percentage > 80:
            return ThrottleAction.MODERATE_LIMIT
        elif usage_percentage > 70:
            return ThrottleAction.GENTLE_LIMIT
        else:
            return ThrottleAction.NONE
```

## 📊 **MIDDLEWARE INTEGRATION**

### **Rate Limiting Middleware:**
```python
class RateLimitingMiddleware:
    def __init__(self, rate_limiter_config):
        self.rate_limiters = {}
        self.dos_protection = DoSProtectionSystem()
        self.initialize_limiters(rate_limiter_config)
        
    def process_request(self, request) -> MiddlewareResponse:
        """Process incoming request through rate limiting"""
        
        # Extract request info
        request_info = self.extract_request_info(request)
        
        # DoS protection check
        attack_assessment = self.dos_protection.detect_attack(request_info)
        if attack_assessment.threat_level == ThreatLevel.HIGH:
            return self.create_block_response("DoS attack detected")
            
        # Apply rate limiting
        rate_limit_result = self.apply_rate_limits(request_info)
        
        if not rate_limit_result.allowed:
            return self.create_rate_limit_response(rate_limit_result)
            
        # Request allowed
        return MiddlewareResponse(allowed=True)
        
    def apply_rate_limits(self, request_info: RequestInfo) -> RateLimitResult:
        """Apply all applicable rate limits"""
        
        results = []
        
        # IP-based rate limiting
        ip_result = self.check_ip_rate_limit(request_info.ip)
        results.append(ip_result)
        
        # User-based rate limiting
        if request_info.user_id:
            user_result = self.check_user_rate_limit(request_info.user_id)
            results.append(user_result)
            
        # Endpoint-specific rate limiting
        endpoint_result = self.check_endpoint_rate_limit(request_info.endpoint)
        results.append(endpoint_result)
        
        # Return most restrictive result
        return self.get_most_restrictive_result(results)
```

## 🧪 **COMPREHENSIVE TESTING**

### **Rate Limiting Tests:**
```python
class RateLimitingTest:
    def test_token_bucket_algorithm(self):
        """Test token bucket rate limiting"""
        
    def test_sliding_window_algorithm(self):
        """Test sliding window rate limiting"""
        
    def test_user_tier_enforcement(self):
        """Test different limits per user tier"""
        
    def test_endpoint_specific_limits(self):
        """Test endpoint-specific rate limits"""
        
    def test_burst_handling(self):
        """Test burst capacity handling"""
        
    def test_progressive_penalties(self):
        """Test progressive delay penalties"""
```

### **DoS Protection Tests:**
```python
class DoSProtectionTest:
    def test_attack_pattern_detection(self):
        """Test detection of attack patterns"""
        
    def test_ip_reputation_blocking(self):
        """Test IP reputation-based blocking"""
        
    def test_behavioral_analysis(self):
        """Test behavioral anomaly detection"""
        
    def test_distributed_attack_simulation(self):
        """Test handling of distributed attacks"""
```

## 📈 **MONITORING & ANALYTICS**

### **Rate Limiting Metrics:**
```python
RATE_LIMITING_METRICS = {
    "requests_allowed": Counter(),
    "requests_blocked": Counter(),
    "rate_limit_violations": Counter(),
    "dos_attacks_detected": Counter(),
    "progressive_delays_applied": Counter(),
    "algorithm_performance": Histogram(),
    "block_duration_distribution": Histogram()
}
```

### **Real-time Dashboard:**
```python
class RateLimitingDashboard:
    def show_rate_limiting_overview(self):
        """Show rate limiting overview"""
        # Current request rates
        # Active blocks
        # Top violators
        # Algorithm performance
        
    def show_dos_protection_status(self):
        """Show DoS protection status"""
        # Attack detection summary
        # Blocked IPs
        # Threat level distribution
        # Response actions taken
```

## ✅ **CRITÉRIOS DE SUCESSO**

1. **DoS Protection:** 99.9% attack detection rate
2. **Fair Usage:** 100% quota enforcement
3. **Performance Impact:** < 5ms latency per request
4. **False Positives:** < 0.1% legitimate requests blocked
5. **Scalability:** Handle 10,000+ concurrent rate checks
6. **Recovery Time:** Automatic unblock within defined timeframes

## 🔧 **CONFIGURATION MANAGEMENT**

```python
RATE_LIMITING_CONFIG = {
    "global": {
        "enabled": True,
        "default_algorithm": "sliding_window",
        "storage_backend": "redis",
        "monitoring_enabled": True
    },
    "dos_protection": {
        "enabled": True,
        "attack_threshold": 0.8,
        "block_duration": 3600,
        "progressive_penalties": True
    },
    "fair_usage": {
        "enabled": True,
        "quota_enforcement": True,
        "warning_threshold": 80,
        "throttling_enabled": True
    },
    "performance": {
        "cache_ttl": 300,
        "cleanup_interval": 600,
        "max_memory_usage": "500MB"
    }
}
```

## 🎯 **RESULTADO ESPERADO**

Sistema completo de rate limiting que:
- Previne ataques DoS e brute-force (99.9% detecção)
- Implementa fair usage com quotas por user tier
- Suporta múltiplos algoritmos de rate limiting
- Fornece proteção progressiva com penalties
- Monitora e bloqueia automaticamente atacantes
- Mantém alta performance (< 5ms overhead)
- Gera alertas e métricas em tempo real
- Integra seamlessly com middleware existente

---

**🎯 RESULTADO FINAL:** Sistema enterprise de rate limiting com algoritmos avançados, proteção DoS multi-camada, fair usage enforcement e monitoramento em tempo real, resolvendo completamente a vulnerabilidade CVSS 5.5 de falta de rate limiting com proteção robusta contra ataques.