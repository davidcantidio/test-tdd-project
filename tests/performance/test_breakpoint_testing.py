#!/usr/bin/env python3
"""
Breakpoint Testing - Find System Breaking Points
Gradually increase load until system fails to find limits.
"""

import pytest
from typing import Dict, Any
from test_stress_suite import DatabaseStressTester, StressTestResult


class BreakpointTester:
    """Find system breaking points."""
    
    def find_max_concurrent_connections(self) -> Dict[str, Any]:
        """Find maximum concurrent connections before failure."""
        tester = DatabaseStressTester()
        
        max_successful = 0
        breaking_point = None
        
        for connections in [5, 10, 20, 50, 100, 200]:
            result = tester.test_connection_pool_stress(
                num_connections=connections, 
                operations_per_connection=10
            )
            
            if result.success and result.error_rate < 0.05:
                max_successful = connections
            else:
                breaking_point = connections
                break
                
        return {
            'max_successful_connections': max_successful,
            'breaking_point': breaking_point,
            'safe_limit': int(max_successful * 0.8)  # 80% of max
        }