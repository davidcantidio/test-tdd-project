Summary
Refactored epic insertion to run within a single connection, increasing busy-timeout to 60 s and committing once after inserting tasks to eliminate nested transaction deadlocks

Introduced batch task insertion that reuses the outer connection, improving performance and preventing connection contention during multi-table operations

Testing
❌ pytest *(Cache performance test failed: SET operations too slow)*

Notes
tests/test_integration_performance.py::TestIntegrationPerformance::test_cache_performance_under_load exceeded the expected SET operation threshold; further performance tuning may be required.


Arquivo (1)

migration/bidirectional_sync.py
+65
-44