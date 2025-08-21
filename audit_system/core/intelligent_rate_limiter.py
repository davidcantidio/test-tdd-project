#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 Intelligent Rate Limiter - Smart Token Pacing System

PURPOSE: Avoid API rate limits through intelligent throttling, not budget limiting.

Key insight from user: Token estimation should determine DELAY between operations,
not whether to allow operations. Be generous with tokens, smart with timing.

STRATEGY:
1. Track real token usage from previous operations
2. Calculate required delays based on API rate limits  
3. Adaptive throttling based on recent consumption patterns
4. Predictive pacing to maintain steady operation flow
"""

import time
import logging
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from collections import deque
import statistics


@dataclass
class TokenUsageRecord:
    """Record of actual token usage from an operation."""
    timestamp: float
    operation_type: str  # "intelligent_analysis", "refactoring", "tdd_analysis", etc.
    file_path: str
    tokens_consumed: int
    duration: float
    api_provider: str = "claude"  # "claude", "openai", "etc"


@dataclass
class RateLimitConfig:
    """Rate limit configuration for different API providers."""
    provider: str
    tokens_per_minute: int
    requests_per_minute: int
    tokens_per_hour: int = None
    burst_allowance: int = None  # Tokens that can be used in burst
    
    def __post_init__(self):
        if self.tokens_per_hour is None:
            self.tokens_per_hour = self.tokens_per_minute * 60
        if self.burst_allowance is None:
            self.burst_allowance = int(self.tokens_per_minute * 0.3)  # 30% burst


class IntelligentRateLimiter:
    """
    Intelligent rate limiter that uses real token consumption to calculate
    optimal delays between operations, preventing API rate limit violations.
    """
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.logger = logging.getLogger(__name__)
        
        # Historical usage tracking
        self.usage_history = deque(maxlen=100)  # Last 100 operations
        self.recent_usage = deque(maxlen=10)    # Last 10 operations for quick estimates
        self.usage_file = project_root / ".audit_reports" / "token_usage_history.json"
        
        # Rate limit configurations for different providers
        self.rate_limits = {
            "claude": RateLimitConfig(
                provider="claude",
                tokens_per_minute=40000,  # Anthropic's rate limit
                requests_per_minute=50,
                burst_allowance=12000
            ),
            "openai": RateLimitConfig(
                provider="openai", 
                tokens_per_minute=90000,  # OpenAI GPT-4 limit
                requests_per_minute=500,
                burst_allowance=27000
            ),
            "local": RateLimitConfig(
                provider="local",
                tokens_per_minute=999999,  # No limit for local models
                requests_per_minute=999999,
                burst_allowance=999999
            )
        }
        
        # Current session tracking
        self.session_start = time.time()
        self.session_tokens = 0
        self.session_requests = 0
        self.last_operation_time = 0
        
        # Load historical data
        self._load_usage_history()
        
        self.logger.info("Intelligent Rate Limiter initialized: generous tokens, smart pacing")
    
    def estimate_tokens_needed(
        self, 
        operation_type: str, 
        file_path: str,
        file_size_lines: int = None
    ) -> int:
        """
        Estimate tokens needed based on REAL historical usage, not theoretical limits.
        
        Args:
            operation_type: Type of operation ("intelligent_analysis", etc.)
            file_path: Path to file being analyzed
            file_size_lines: Number of lines in file (for scaling)
            
        Returns:
            Estimated tokens based on historical data
        """
        
        # Get historical data for this operation type
        similar_operations = [
            record for record in self.usage_history 
            if record.operation_type == operation_type
        ]
        
        if not similar_operations:
            # No historical data - use generous default based on operation type
            defaults = {
                "intelligent_analysis": 15000,
                "refactoring": 12000,
                "tdd_analysis": 10000,
                "god_code_detection": 8000,
                "security_analysis": 20000,
                "comprehensive_audit": 30000
            }
            estimated = defaults.get(operation_type, 15000)
        else:
            # Use median of recent similar operations (more robust than average)
            recent_similar = similar_operations[-20:]  # Last 20 similar operations
            tokens_used = [record.tokens_consumed for record in recent_similar]
            estimated = int(statistics.median(tokens_used))
            
            # Scale based on file size if provided
            if file_size_lines and len(recent_similar) > 3:
                # Calculate scaling factor based on line count
                avg_scaling = []
                for record in recent_similar:
                    if hasattr(record, 'file_size_lines') and record.file_size_lines:
                        scaling = record.tokens_consumed / record.file_size_lines
                        avg_scaling.append(scaling)
                
                if avg_scaling:
                    tokens_per_line = statistics.median(avg_scaling)
                    size_estimate = int(file_size_lines * tokens_per_line)
                    # Blend historical median with size-based estimate
                    estimated = int(estimated * 0.7 + size_estimate * 0.3)
        
        self.logger.debug(
            "Token estimation for %s (%s): %d tokens (based on %d historical records)",
            operation_type, file_path, estimated, len(similar_operations)
        )
        
        return estimated
    
    def calculate_required_delay(
        self, 
        estimated_tokens: int, 
        operation_type: str,
        api_provider: str = "claude"
    ) -> float:
        """
        Calculate how long to wait before next operation to avoid rate limits.
        
        This is the CORE function - smart pacing based on consumption patterns.
        
        Args:
            estimated_tokens: Expected token consumption
            operation_type: Type of operation
            api_provider: API provider ("claude", "openai", etc.)
            
        Returns:
            Delay in seconds (0 if no delay needed)
        """
        
        rate_config = self.rate_limits.get(api_provider, self.rate_limits["claude"])
        current_time = time.time()
        
        # Calculate current usage rates
        minute_ago = current_time - 60
        hour_ago = current_time - 3600
        
        # Recent usage in last minute
        recent_minute_usage = sum(
            record.tokens_consumed for record in self.usage_history
            if record.timestamp > minute_ago
        )
        
        # Recent usage in last hour
        recent_hour_usage = sum(
            record.tokens_consumed for record in self.usage_history
            if record.timestamp > hour_ago
        )
        
        # Check if adding estimated tokens would exceed limits
        projected_minute_usage = recent_minute_usage + estimated_tokens
        projected_hour_usage = recent_hour_usage + estimated_tokens
        
        # Calculate delays needed
        minute_delay = 0
        hour_delay = 0
        
        # Per-minute rate limit check
        if projected_minute_usage > rate_config.tokens_per_minute:
            excess_tokens = projected_minute_usage - rate_config.tokens_per_minute
            # Time to wait for oldest tokens in minute window to expire
            minute_delay = 60 - (current_time - self._get_oldest_token_time_in_window(minute_ago))
            minute_delay = max(0, minute_delay)
        
        # Per-hour rate limit check (usually less restrictive)
        if projected_hour_usage > rate_config.tokens_per_hour:
            excess_tokens = projected_hour_usage - rate_config.tokens_per_hour
            # Time to wait for oldest tokens in hour window to expire
            hour_delay = 3600 - (current_time - self._get_oldest_token_time_in_window(hour_ago))
            hour_delay = max(0, hour_delay)
        
        # Use the longer delay
        required_delay = max(minute_delay, hour_delay)
        
        # Add adaptive buffer based on recent consumption volatility
        if len(self.recent_usage) > 3:
            recent_tokens = [record.tokens_consumed for record in self.recent_usage]
            volatility = statistics.stdev(recent_tokens) / statistics.mean(recent_tokens)
            adaptive_buffer = required_delay * min(volatility, 0.5)  # Max 50% buffer
            required_delay += adaptive_buffer
        
        # Minimum spacing between operations (prevent too rapid firing)
        time_since_last = current_time - self.last_operation_time
        min_spacing = 2.0  # Minimum 2 seconds between operations
        spacing_delay = max(0, min_spacing - time_since_last)
        
        final_delay = max(required_delay, spacing_delay)
        
        if final_delay > 0:
            self.logger.info(
                "Rate limiting: waiting %.1fs before %s (estimated %d tokens, recent usage: %d/min, %d/hour)",
                final_delay, operation_type, estimated_tokens, recent_minute_usage, recent_hour_usage
            )
        
        return final_delay
    
    def should_proceed_with_operation(
        self, 
        operation_type: str, 
        file_path: str,
        file_size_lines: int = None,
        api_provider: str = "claude"
    ) -> Tuple[bool, float, int]:
        """
        Determine if operation should proceed and how long to wait.
        
        PHILOSOPHY: Always allow operations, just pace them intelligently.
        
        Returns:
            (should_proceed, delay_seconds, estimated_tokens)
        """
        
        # Always estimate generously - we want comprehensive analysis
        estimated_tokens = self.estimate_tokens_needed(operation_type, file_path, file_size_lines)
        
        # Calculate intelligent delay
        delay = self.calculate_required_delay(estimated_tokens, operation_type, api_provider)
        
        # ALWAYS proceed, just with appropriate timing
        return True, delay, estimated_tokens
    
    def record_actual_usage(
        self, 
        operation_type: str, 
        file_path: str,
        tokens_consumed: int, 
        duration: float,
        api_provider: str = "claude"
    ) -> None:
        """
        Record actual token usage to improve future estimates.
        
        This is crucial for the learning aspect of the rate limiter.
        """
        
        record = TokenUsageRecord(
            timestamp=time.time(),
            operation_type=operation_type,
            file_path=file_path,
            tokens_consumed=tokens_consumed,
            duration=duration,
            api_provider=api_provider
        )
        
        # Add to tracking
        self.usage_history.append(record)
        self.recent_usage.append(record)
        
        # Update session counters
        self.session_tokens += tokens_consumed
        self.session_requests += 1
        self.last_operation_time = time.time()
        
        # Save to persistent storage
        self._save_usage_history()
        
        # Log for monitoring
        self.logger.info(
            "Usage recorded: %s consumed %d tokens in %.2fs (session total: %d tokens, %d requests)",
            operation_type, tokens_consumed, duration, self.session_tokens, self.session_requests
        )
        
        # Calculate estimate accuracy for learning
        recent_estimates = getattr(self, '_recent_estimates', {})
        if operation_type in recent_estimates:
            estimated = recent_estimates[operation_type]
            accuracy = abs(estimated - tokens_consumed) / estimated if estimated > 0 else 0
            self.logger.debug(
                "Estimate accuracy for %s: estimated %d, actual %d (%.1f%% error)",
                operation_type, estimated, tokens_consumed, accuracy * 100
            )
    
    def wait_if_needed(
        self, 
        operation_type: str, 
        file_path: str,
        file_size_lines: int = None,
        api_provider: str = "claude"
    ) -> int:
        """
        Wait if needed to avoid rate limits, then return estimated tokens.
        
        This is the main entry point for the rate limiting system.
        """
        
        should_proceed, delay, estimated_tokens = self.should_proceed_with_operation(
            operation_type, file_path, file_size_lines, api_provider
        )
        
        # Store estimate for accuracy tracking
        if not hasattr(self, '_recent_estimates'):
            self._recent_estimates = {}
        self._recent_estimates[operation_type] = estimated_tokens
        
        # Wait if needed
        if delay > 0:
            self.logger.info(f"⏱️ Rate limiting: waiting {delay:.1f}s before {operation_type}")
            time.sleep(delay)
        
        return estimated_tokens
    
    def _get_oldest_token_time_in_window(self, window_start: float) -> float:
        """Get timestamp of oldest token usage in the time window."""
        tokens_in_window = [
            record.timestamp for record in self.usage_history
            if record.timestamp > window_start
        ]
        return min(tokens_in_window) if tokens_in_window else window_start
    
    def _load_usage_history(self) -> None:
        """Load historical usage data from disk."""
        if self.usage_file.exists():
            try:
                with open(self.usage_file, 'r') as f:
                    data = json.load(f)
                
                for record_data in data.get('usage_history', []):
                    record = TokenUsageRecord(**record_data)
                    self.usage_history.append(record)
                    if len(self.recent_usage) < 10:
                        self.recent_usage.append(record)
                
                self.logger.info(f"Loaded {len(self.usage_history)} historical usage records")
                
            except Exception as e:
                self.logger.warning(f"Failed to load usage history: {e}")
    
    def _save_usage_history(self) -> None:
        """Save usage history to disk for persistence."""
        try:
            self.usage_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert to serializable format
            data = {
                'usage_history': [
                    {
                        'timestamp': record.timestamp,
                        'operation_type': record.operation_type,
                        'file_path': record.file_path,
                        'tokens_consumed': record.tokens_consumed,
                        'duration': record.duration,
                        'api_provider': record.api_provider
                    }
                    for record in list(self.usage_history)
                ],
                'session_stats': {
                    'session_start': self.session_start,
                    'session_tokens': self.session_tokens,
                    'session_requests': self.session_requests
                }
            }
            
            with open(self.usage_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.warning(f"Failed to save usage history: {e}")
    
    def get_usage_stats(self) -> Dict:
        """Get comprehensive usage statistics."""
        current_time = time.time()
        hour_ago = current_time - 3600
        minute_ago = current_time - 60
        
        # Recent usage
        last_hour_records = [r for r in self.usage_history if r.timestamp > hour_ago]
        last_minute_records = [r for r in self.usage_history if r.timestamp > minute_ago]
        
        hour_tokens = sum(r.tokens_consumed for r in last_hour_records)
        minute_tokens = sum(r.tokens_consumed for r in last_minute_records)
        
        # Operation type breakdown
        operation_stats = {}
        for record in list(self.usage_history):
            op_type = record.operation_type
            if op_type not in operation_stats:
                operation_stats[op_type] = {
                    'total_operations': 0,
                    'total_tokens': 0,
                    'avg_tokens': 0,
                    'avg_duration': 0
                }
            
            stats = operation_stats[op_type]
            stats['total_operations'] += 1
            stats['total_tokens'] += record.tokens_consumed
            stats['avg_tokens'] = stats['total_tokens'] / stats['total_operations']
            
        return {
            'session_stats': {
                'session_duration': current_time - self.session_start,
                'session_tokens': self.session_tokens,
                'session_requests': self.session_requests,
                'tokens_per_minute': self.session_tokens / ((current_time - self.session_start) / 60) if current_time > self.session_start else 0
            },
            'recent_usage': {
                'last_hour_tokens': hour_tokens,
                'last_minute_tokens': minute_tokens,
                'last_hour_requests': len(last_hour_records),
                'last_minute_requests': len(last_minute_records)
            },
            'historical_stats': {
                'total_records': len(self.usage_history),
                'operation_breakdown': operation_stats
            },
            'rate_limit_status': {
                provider: {
                    'minute_usage_percent': (minute_tokens / config.tokens_per_minute) * 100,
                    'hour_usage_percent': (hour_tokens / config.tokens_per_hour) * 100,
                    'approaching_limit': minute_tokens > config.tokens_per_minute * 0.8
                }
                for provider, config in self.rate_limits.items()
            }
        }


def demonstrate_intelligent_rate_limiting():
    """Demonstrate the intelligent rate limiting system."""
    
    print("🎯 INTELLIGENT RATE LIMITER DEMONSTRATION")
    print("=" * 60)
    
    # Initialize rate limiter
    project_root = Path("/home/david/Documentos/canimport/test-tdd-project")
    rate_limiter = IntelligentRateLimiter(project_root)
    
    # Simulate different operations
    operations = [
        ("intelligent_analysis", "large_file.py", 1500),
        ("refactoring", "medium_file.py", 800),
        ("tdd_analysis", "small_file.py", 200),
        ("security_analysis", "critical_file.py", 2000),
    ]
    
    print("\n🧠 SMART PACING SIMULATION:")
    
    for i, (op_type, file_path, file_lines) in enumerate(operations, 1):
        print(f"\n[{i}] Operation: {op_type} on {file_path} ({file_lines} lines)")
        
        # Get pacing recommendation
        should_proceed, delay, estimated_tokens = rate_limiter.should_proceed_with_operation(
            op_type, file_path, file_lines
        )
        
        print(f"   🎯 Should proceed: {'✅ Yes' if should_proceed else '❌ No'}")
        print(f"   ⏱️ Recommended delay: {delay:.1f}s")
        print(f"   🔥 Estimated tokens: {estimated_tokens:,}")
        
        # Simulate waiting and operation
        if delay > 0:
            print(f"   ⏱️ Waiting {delay:.1f}s for rate limiting...")
            # In real implementation: time.sleep(delay)
        
        # Simulate actual token consumption (with some variance)
        import random
        actual_tokens = int(estimated_tokens * random.uniform(0.7, 1.3))
        duration = random.uniform(1.0, 5.0)
        
        # Record actual usage
        rate_limiter.record_actual_usage(op_type, file_path, actual_tokens, duration)
        
        print(f"   📊 Actual consumption: {actual_tokens:,} tokens in {duration:.1f}s")
    
    # Show final statistics
    print("\n📈 FINAL USAGE STATISTICS:")
    stats = rate_limiter.get_usage_stats()
    
    session = stats['session_stats']
    print(f"   🎯 Session duration: {session['session_duration']:.1f}s")
    print(f"   🔥 Total tokens: {session['session_tokens']:,}")
    print(f"   📊 Tokens per minute: {session['tokens_per_minute']:.0f}")
    
    recent = stats['recent_usage']
    print(f"   ⏱️ Last minute: {recent['last_minute_tokens']:,} tokens")
    print(f"   🕐 Last hour: {recent['last_hour_tokens']:,} tokens")
    
    print(f"\n💡 RATE LIMITING STATUS:")
    for provider, status in stats['rate_limit_status'].items():
        if provider != "local":  # Skip local for demo
            print(f"   📡 {provider.upper()}:")
            print(f"      Minute usage: {status['minute_usage_percent']:.1f}%")
            print(f"      Hour usage: {status['hour_usage_percent']:.1f}%")
            print(f"      Status: {'⚠️ Approaching limit' if status['approaching_limit'] else '✅ Safe'}")


if __name__ == "__main__":
    demonstrate_intelligent_rate_limiting()