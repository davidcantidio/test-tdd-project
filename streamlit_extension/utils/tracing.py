#!/usr/bin/env python3
"""
Simplified Correlation IDs Tracing System
Basic request tracing for debugging.
"""

import uuid
import time
import logging
import json
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass, field
from datetime import datetime
from functools import wraps
from contextlib import contextmanager

import streamlit as st

logger = logging.getLogger(__name__)


@dataclass
class TraceContext:
    """Simplified context for a traced request."""
    correlation_id: str
    operation: Optional[str] = None
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    status: str = "pending"
    error: Optional[str] = None

    def complete(self, error: Optional[str] = None):
        """Mark trace as complete."""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.status = "error" if error else "success"
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            'correlation_id': self.correlation_id,
            'operation': self.operation,
            'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
            'end_time': datetime.fromtimestamp(self.end_time).isoformat() if self.end_time else None,
            'duration_ms': self.duration_ms,
            'status': self.status,
            'error': self.error
        }


class CorrelationIDGenerator:
    """Generate and manage correlation IDs."""

    @staticmethod
    def generate() -> str:
        """Generate a new correlation ID."""
        timestamp = int(time.time() * 1000)
        random_part = str(uuid.uuid4())[:8]
        return f"{timestamp}-{random_part}"

    @staticmethod
    def extract_timestamp(correlation_id: str) -> Optional[datetime]:
        """Extract timestamp from correlation ID."""
        try:
            parts = correlation_id.split('-')
            if len(parts) >= 2:
                timestamp = int(parts[0]) / 1000
                return datetime.fromtimestamp(timestamp)
        except Exception:
            pass
        return None


def traced(operation: str = None):
    """Simplified decorator to add tracing to functions."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            correlation_id = get_correlation_id()
            if not correlation_id:
                correlation_id = CorrelationIDGenerator.generate()
                set_correlation_id(correlation_id)

            operation_name = operation or f"{func.__module__}.{func.__name__}"
            trace = TraceContext(
                correlation_id=correlation_id,
                operation=operation_name
            )

            logger.info(f"[TRACE_START] {operation_name}", extra={
                'correlation_id': correlation_id
            })

            try:
                result = func(*args, **kwargs)
                trace.complete()
                logger.info(
                    f"[TRACE_END] {operation_name} - {trace.duration_ms:.2f}ms",
                    extra={
                        'correlation_id': correlation_id,
                        'duration_ms': trace.duration_ms,
                    }
                )
                return result
            except Exception as e:
                trace.complete(error=str(e))
                logger.error(
                    f"[TRACE_ERROR] {operation_name} - {e}",
                    extra={
                        'correlation_id': correlation_id,
                        'duration_ms': trace.duration_ms,
                        'error': str(e),
                    }
                )
                raise
            finally:
                TraceCollector.instance().add_trace(trace)

        return wrapper

    return decorator


@contextmanager
def trace_context(operation: str, **metadata):
    """Simplified context manager for tracing blocks of code."""
    correlation_id = get_correlation_id() or CorrelationIDGenerator.generate()
    trace = TraceContext(
        correlation_id=correlation_id,
        operation=operation
    )

    logger.info(f"[TRACE_START] {operation}", extra={
        'correlation_id': correlation_id,
        'metadata': metadata,
    })

    try:
        yield trace
        trace.complete()
    except Exception as e:
        trace.complete(error=str(e))
        logger.error(f"[TRACE_ERROR] {operation} - {e}", extra={
            'correlation_id': correlation_id,
            'error': str(e),
        })
        raise
    finally:
        logger.info(
            f"[TRACE_END] {operation} - {trace.duration_ms:.2f}ms",
            extra={
                'correlation_id': correlation_id,
                'duration_ms': trace.duration_ms,
            }
        )
        TraceCollector.instance().add_trace(trace)


class TraceCollector:
    """Simplified trace collector."""

    _instance = None

    def __init__(self):
        self.traces: List[TraceContext] = []
        self.max_traces = 1000

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def add_trace(self, trace: TraceContext):
        self.traces.append(trace)
        if len(self.traces) > self.max_traces:
            self.traces = self.traces[-500:]  # Keep last 500

    def get_trace_chain(self, correlation_id: str) -> List[TraceContext]:
        return [t for t in self.traces if t.correlation_id == correlation_id]

    def get_statistics(self) -> Dict[str, Any]:
        if not self.traces:
            return {}

        successful = sum(1 for t in self.traces if t.status == 'success')
        failed = sum(1 for t in self.traces if t.status == 'error')
        durations = [t.duration_ms for t in self.traces if t.duration_ms]

        return {
            'total_traces': len(self.traces),
            'successful': successful,
            'failed': failed,
            'success_rate': (successful / len(self.traces) * 100) if self.traces else 0,
            'avg_duration_ms': sum(durations) / len(durations) if durations else 0,
        }


def init_request_tracing():
    """Initialize tracing for Streamlit request."""
    if 'correlation_id' not in st.session_state:
        st.session_state.correlation_id = CorrelationIDGenerator.generate()
    set_correlation_id(st.session_state.correlation_id)
    return st.session_state.correlation_id


def trace_streamlit_operation(operation: str):
    """Decorator for tracing Streamlit operations."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            init_request_tracing()
            return traced(operation)(func)(*args, **kwargs)

        return wrapper

    return decorator


def render_trace_viewer():
    """Render simplified trace viewer in Streamlit."""
    st.title("🔍 Request Tracing")
    
    correlation_id = st.session_state.get('correlation_id')
    if correlation_id:
        st.info(f"Current Correlation ID: `{correlation_id}`")
        
    st.subheader("📊 Trace Statistics")
    stats = TraceCollector.instance().get_statistics()
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Traces", stats.get('total_traces', 0))
    with col2:
        st.metric("Success Rate", f"{stats.get('success_rate', 0):.1f}%")
    with col3:
        st.metric("Avg Duration", f"{stats.get('avg_duration_ms', 0):.2f}ms")


# Session state management for correlation ID
_current_correlation_id = None


def get_correlation_id() -> Optional[str]:
    """Get current correlation ID."""
    return _current_correlation_id
