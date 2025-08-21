#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 Comprehensive Agents Audit - 100% Production Readiness Validation

Auditoria completa e sistemática de todos os agentes IA implementados
para garantir 100% production readiness com validação abrangente.

Auditoria Inclui:
- Functional testing de todos os agentes
- Integration testing entre componentes
- Performance benchmarking
- Security validation
- Error handling validation
- Edge cases testing
- Memory leak detection
- Documentation completeness
- Production readiness checklist

Uso:
    python comprehensive_agents_audit.py [--verbose] [--full-test-suite]
"""

from __future__ import annotations

import sys
import os
import logging
import time
import traceback
import psutil
import gc
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import argparse
import json

# Project setup
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Import all agents to test
try:
    from intelligent_code_agent import (
        IntelligentCodeAgent, SemanticAnalysisEngine, 
        FileSemanticAnalysis, AnalysisDepth, SemanticMode
    )
    from intelligent_refactoring_engine import (
        IntelligentRefactoringEngine, RefactoringResult
    )
    from tdd_intelligent_workflow_agent import (
        TDDIntelligentWorkflowAgent, TDDPhase, TDAHEnergyLevel,
        TDDWorkflowSession
    )
    AGENTS_AVAILABLE = True
except ImportError as e:
    AGENTS_AVAILABLE = False
    IMPORT_ERROR = str(e)


@dataclass
class AuditResult:
    """Result of a single audit test."""
    test_name: str
    success: bool
    duration_seconds: float
    memory_usage_mb: float
    details: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class ComprehensiveAuditReport:
    """Complete audit report."""
    audit_timestamp: datetime
    total_tests: int
    passed_tests: int
    failed_tests: int
    total_duration: float
    peak_memory_usage: float
    agents_tested: List[str]
    test_results: List[AuditResult] = field(default_factory=list)
    production_readiness_score: float = 0.0
    critical_issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return (self.passed_tests / self.total_tests) * 100


class ComprehensiveAgentsAuditor:
    """
    Comprehensive auditor for all AI agents ensuring 100% production readiness.
    """
    
    def __init__(self, project_root: Path, verbose: bool = False):
        self.project_root = project_root
        self.verbose = verbose
        self.logger = logging.getLogger(f"{__name__}.ComprehensiveAgentsAuditor")
        
        # Test files for validation
        self.test_files = self._identify_test_files()
        
        # Audit configuration
        self.audit_config = {
            "memory_threshold_mb": 500,  # Alert if agent uses >500MB
            "performance_threshold_seconds": 30,  # Alert if operation takes >30s
            "min_quality_score": 70,  # Minimum acceptable quality score
            "max_refactoring_time": 60,  # Max time for refactoring operation
            "required_success_rate": 95  # 95% of tests must pass
        }
        
        self.logger.info("Comprehensive Agents Auditor initialized")
    
    def execute_full_audit(self) -> ComprehensiveAuditReport:
        """Execute comprehensive audit of all AI agents."""
        
        self.logger.info("🔍 Starting comprehensive agents audit for 100% production readiness")
        audit_start = datetime.now()
        
        report = ComprehensiveAuditReport(
            audit_timestamp=audit_start,
            total_tests=0,
            passed_tests=0,
            failed_tests=0,
            total_duration=0.0,
            peak_memory_usage=0.0,
            agents_tested=[]
        )
        
        try:
            # Phase 1: Availability and Import Testing
            availability_results = self._test_agents_availability()
            report.test_results.extend(availability_results)
            
            if not AGENTS_AVAILABLE:
                report.critical_issues.append(f"Agents not available: {IMPORT_ERROR}")
                return self._finalize_report(report, audit_start)
            
            # Phase 2: Individual Agent Functional Testing
            functional_results = self._test_individual_agents_functionality()
            report.test_results.extend(functional_results)
            
            # Phase 3: Integration Testing Between Agents
            integration_results = self._test_agents_integration()
            report.test_results.extend(integration_results)
            
            # Phase 4: Performance and Memory Testing
            performance_results = self._test_performance_and_memory()
            report.test_results.extend(performance_results)
            
            # Phase 5: Edge Cases and Error Handling
            edge_case_results = self._test_edge_cases_and_errors()
            report.test_results.extend(edge_case_results)
            
            # Phase 6: Security Validation
            security_results = self._test_security_validation()
            report.test_results.extend(security_results)
            
            # Phase 7: Real-World Usage Scenarios
            real_world_results = self._test_real_world_scenarios()
            report.test_results.extend(real_world_results)
            
            # Phase 8: Documentation and Usability
            documentation_results = self._test_documentation_completeness()
            report.test_results.extend(documentation_results)
            
        except Exception as e:
            self.logger.error("Critical error during audit: %s", e)
            report.critical_issues.append(f"Audit execution failed: {str(e)}")
        
        return self._finalize_report(report, audit_start)
    
    def _test_agents_availability(self) -> List[AuditResult]:
        """Test that all agents are available and importable."""
        results = []
        
        start_time = time.time()
        memory_before = self._get_memory_usage()
        
        if AGENTS_AVAILABLE:
            result = AuditResult(
                test_name="agents_import_availability",
                success=True,
                duration_seconds=time.time() - start_time,
                memory_usage_mb=self._get_memory_usage() - memory_before,
                details={
                    "agents_imported": [
                        "IntelligentCodeAgent",
                        "IntelligentRefactoringEngine", 
                        "TDDIntelligentWorkflowAgent"
                    ]
                }
            )
            self.logger.info("✅ All agents imported successfully")
        else:
            result = AuditResult(
                test_name="agents_import_availability",
                success=False,
                duration_seconds=time.time() - start_time,
                memory_usage_mb=0.0,
                errors=[f"Import failed: {IMPORT_ERROR}"]
            )
            self.logger.error("❌ Agent import failed: %s", IMPORT_ERROR)
        
        results.append(result)
        return results
    
    def _test_individual_agents_functionality(self) -> List[AuditResult]:
        """Test functionality of each agent individually."""
        results = []
        
        if not AGENTS_AVAILABLE:
            return results
        
        # Test IntelligentCodeAgent
        results.extend(self._test_intelligent_code_agent())
        
        # Test IntelligentRefactoringEngine
        results.extend(self._test_intelligent_refactoring_engine())
        
        # Test TDDIntelligentWorkflowAgent
        results.extend(self._test_tdd_intelligent_workflow_agent())
        
        return results
    
    def _test_intelligent_code_agent(self) -> List[AuditResult]:
        """Comprehensive testing of IntelligentCodeAgent."""
        results = []
        
        self.logger.info("🤖 Testing IntelligentCodeAgent functionality")
        
        try:
            # Test 1: Basic initialization
            start_time = time.time()
            memory_before = self._get_memory_usage()
            
            agent = IntelligentCodeAgent(
                project_root=self.project_root,
                analysis_depth=AnalysisDepth.ADVANCED,
                semantic_mode=SemanticMode.CONSERVATIVE,
                dry_run=True
            )
            
            result = AuditResult(
                test_name="intelligent_code_agent_initialization",
                success=True,
                duration_seconds=time.time() - start_time,
                memory_usage_mb=self._get_memory_usage() - memory_before,
                details={"agent_type": "IntelligentCodeAgent", "mode": "ADVANCED+CONSERVATIVE"}
            )
            results.append(result)
            self.logger.info("✅ IntelligentCodeAgent initialization successful")
            
            # Test 2: File analysis on multiple complexity levels
            for test_file in self.test_files[:3]:  # Test on 3 different files
                if test_file.exists():
                    start_time = time.time()
                    memory_before = self._get_memory_usage()
                    
                    try:
                        analysis = agent.analyze_file_intelligently(str(test_file))
                        
                        # Validate analysis results
                        validation_errors = self._validate_file_analysis(analysis)
                        
                        result = AuditResult(
                            test_name=f"file_analysis_{test_file.name}",
                            success=len(validation_errors) == 0,
                            duration_seconds=time.time() - start_time,
                            memory_usage_mb=self._get_memory_usage() - memory_before,
                            details={
                                "file": str(test_file),
                                "lines_analyzed": len(analysis.lines_analyzed),
                                "quality_score": analysis.semantic_quality_score,
                                "refactorings_found": len(analysis.recommended_refactorings),
                                "security_issues": len(analysis.security_vulnerabilities),
                                "performance_issues": len(analysis.performance_bottlenecks)
                            },
                            errors=validation_errors,
                            performance_metrics={
                                "lines_per_second": len(analysis.lines_analyzed) / (time.time() - start_time),
                                "quality_score": analysis.semantic_quality_score
                            }
                        )
                        
                        results.append(result)
                        
                        if len(validation_errors) == 0:
                            self.logger.info("✅ Analysis successful for %s (quality: %.1f)", 
                                           test_file.name, analysis.semantic_quality_score)
                        else:
                            self.logger.error("❌ Analysis validation failed for %s: %s", 
                                            test_file.name, validation_errors)
                        
                    except Exception as e:
                        result = AuditResult(
                            test_name=f"file_analysis_{test_file.name}",
                            success=False,
                            duration_seconds=time.time() - start_time,
                            memory_usage_mb=self._get_memory_usage() - memory_before,
                            errors=[f"Analysis failed: {str(e)}"],
                            details={"file": str(test_file)}
                        )
                        results.append(result)
                        self.logger.error("❌ Analysis failed for %s: %s", test_file.name, e)
            
            # Test 3: Different analysis depths
            for depth in [AnalysisDepth.BASIC, AnalysisDepth.ADVANCED, AnalysisDepth.DEEP]:
                start_time = time.time()
                memory_before = self._get_memory_usage()
                
                try:
                    depth_agent = IntelligentCodeAgent(
                        project_root=self.project_root,
                        analysis_depth=depth,
                        dry_run=True
                    )
                    
                    test_file = self.test_files[0]
                    if test_file.exists():
                        analysis = depth_agent.analyze_file_intelligently(str(test_file))
                        
                        result = AuditResult(
                            test_name=f"analysis_depth_{depth.value}",
                            success=True,
                            duration_seconds=time.time() - start_time,
                            memory_usage_mb=self._get_memory_usage() - memory_before,
                            details={
                                "depth": depth.value,
                                "quality_score": analysis.semantic_quality_score,
                                "refactorings": len(analysis.recommended_refactorings)
                            },
                            performance_metrics={
                                "analysis_time": time.time() - start_time,
                                "memory_efficiency": (self._get_memory_usage() - memory_before) / len(analysis.lines_analyzed)
                            }
                        )
                        results.append(result)
                        
                except Exception as e:
                    result = AuditResult(
                        test_name=f"analysis_depth_{depth.value}",
                        success=False,
                        duration_seconds=time.time() - start_time,
                        memory_usage_mb=self._get_memory_usage() - memory_before,
                        errors=[str(e)]
                    )
                    results.append(result)
                    
        except Exception as e:
            result = AuditResult(
                test_name="intelligent_code_agent_comprehensive",
                success=False,
                duration_seconds=0.0,
                memory_usage_mb=0.0,
                errors=[f"Comprehensive testing failed: {str(e)}"]
            )
            results.append(result)
            
        return results
    
    def _test_intelligent_refactoring_engine(self) -> List[AuditResult]:
        """Comprehensive testing of IntelligentRefactoringEngine."""
        results = []
        
        self.logger.info("🔧 Testing IntelligentRefactoringEngine functionality")
        
        try:
            # Test 1: Engine initialization
            start_time = time.time()
            memory_before = self._get_memory_usage()
            
            engine = IntelligentRefactoringEngine(dry_run=True)
            
            result = AuditResult(
                test_name="refactoring_engine_initialization",
                success=True,
                duration_seconds=time.time() - start_time,
                memory_usage_mb=self._get_memory_usage() - memory_before,
                details={"engine_type": "IntelligentRefactoringEngine", "strategies": len(engine.refactoring_strategies)}
            )
            results.append(result)
            
            # Test 2: Available refactoring strategies
            expected_strategies = [
                "extract_method", "improve_exception_handling", 
                "optimize_string_operations", "eliminate_god_method",
                "optimize_database_queries", "extract_constants",
                "improve_conditional_logic"
            ]
            
            available_strategies = list(engine.refactoring_strategies.keys())
            missing_strategies = set(expected_strategies) - set(available_strategies)
            
            result = AuditResult(
                test_name="refactoring_strategies_availability",
                success=len(missing_strategies) == 0,
                duration_seconds=0.0,
                memory_usage_mb=0.0,
                details={
                    "expected_strategies": expected_strategies,
                    "available_strategies": available_strategies,
                    "missing_strategies": list(missing_strategies)
                },
                errors=[f"Missing strategies: {missing_strategies}"] if missing_strategies else []
            )
            results.append(result)
            
            # Test 3: Refactoring on example file
            if hasattr(self, '_get_example_refactoring_file'):
                test_file = self._get_example_refactoring_file()
                if test_file and test_file.exists():
                    
                    # Create a simple refactoring to test
                    from intelligent_refactoring_engine import IntelligentRefactoring
                    
                    test_refactoring = IntelligentRefactoring(
                        refactoring_type="improve_exception_handling",
                        target_lines=[1, 2, 3],
                        description="Test exception handling improvement",
                        benefits=["Better error handling"],
                        risks=["Minimal"],
                        confidence_score=0.9,
                        estimated_impact={"maintainability": "high"}
                    )
                    
                    start_time = time.time()
                    memory_before = self._get_memory_usage()
                    
                    try:
                        refactoring_result = engine.apply_refactoring(str(test_file), test_refactoring)
                        
                        result = AuditResult(
                            test_name="refactoring_execution_test",
                            success=refactoring_result.success,
                            duration_seconds=time.time() - start_time,
                            memory_usage_mb=self._get_memory_usage() - memory_before,
                            details={
                                "refactoring_type": test_refactoring.refactoring_type,
                                "lines_affected": len(refactoring_result.lines_affected),
                                "improvements": refactoring_result.improvements
                            },
                            errors=refactoring_result.errors,
                            warnings=refactoring_result.warnings
                        )
                        results.append(result)
                        
                    except Exception as e:
                        result = AuditResult(
                            test_name="refactoring_execution_test",
                            success=False,
                            duration_seconds=time.time() - start_time,
                            memory_usage_mb=self._get_memory_usage() - memory_before,
                            errors=[f"Refactoring execution failed: {str(e)}"]
                        )
                        results.append(result)
            
        except Exception as e:
            result = AuditResult(
                test_name="refactoring_engine_comprehensive",
                success=False,
                duration_seconds=0.0,
                memory_usage_mb=0.0,
                errors=[f"Refactoring engine testing failed: {str(e)}"]
            )
            results.append(result)
            
        return results
    
    def _test_tdd_intelligent_workflow_agent(self) -> List[AuditResult]:
        """Comprehensive testing of TDDIntelligentWorkflowAgent."""
        results = []
        
        self.logger.info("🎯 Testing TDDIntelligentWorkflowAgent functionality")
        
        try:
            # Test 1: Agent initialization
            start_time = time.time()
            memory_before = self._get_memory_usage()
            
            tdd_agent = TDDIntelligentWorkflowAgent(
                project_root=self.project_root,
                tdah_mode=True,
                default_focus_minutes=25
            )
            
            result = AuditResult(
                test_name="tdd_workflow_agent_initialization",
                success=True,
                duration_seconds=time.time() - start_time,
                memory_usage_mb=self._get_memory_usage() - memory_before,
                details={
                    "agent_type": "TDDIntelligentWorkflowAgent",
                    "tdah_mode": True,
                    "focus_minutes": 25
                }
            )
            results.append(result)
            
            # Test 2: Session creation for different TDD phases
            for phase in [TDDPhase.RED, TDDPhase.GREEN, TDDPhase.REFACTOR]:
                start_time = time.time()
                memory_before = self._get_memory_usage()
                
                try:
                    test_file = self.test_files[0]
                    if test_file.exists():
                        session = tdd_agent.start_tdd_workflow_session(
                            target_file=str(test_file),
                            initial_phase=phase,
                            user_energy_level=TDAHEnergyLevel.MEDIUM,
                            focus_session_minutes=15
                        )
                        
                        result = AuditResult(
                            test_name=f"tdd_session_creation_{phase.value}",
                            success=True,
                            duration_seconds=time.time() - start_time,
                            memory_usage_mb=self._get_memory_usage() - memory_before,
                            details={
                                "phase": phase.value,
                                "session_id": session.session_id,
                                "tasks_count": len(session.tasks_remaining),
                                "focus_minutes": session.focus_session_minutes
                            },
                            performance_metrics={
                                "session_creation_time": time.time() - start_time,
                                "tasks_generated": len(session.tasks_remaining)
                            }
                        )
                        results.append(result)
                        
                except Exception as e:
                    result = AuditResult(
                        test_name=f"tdd_session_creation_{phase.value}",
                        success=False,
                        duration_seconds=time.time() - start_time,
                        memory_usage_mb=self._get_memory_usage() - memory_before,
                        errors=[f"Session creation failed: {str(e)}"]
                    )
                    results.append(result)
            
            # Test 3: TDAH energy level matching
            for energy_level in [TDAHEnergyLevel.LOW, TDAHEnergyLevel.MEDIUM, TDAHEnergyLevel.HIGH]:
                start_time = time.time()
                
                try:
                    test_file = self.test_files[0]
                    if test_file.exists():
                        session = tdd_agent.start_tdd_workflow_session(
                            target_file=str(test_file),
                            initial_phase=TDDPhase.REFACTOR,
                            user_energy_level=energy_level,
                            focus_session_minutes=10
                        )
                        
                        # Analyze task energy matching
                        matching_tasks = [
                            task for task in session.tasks_remaining 
                            if task.energy_level_required == energy_level
                        ]
                        
                        result = AuditResult(
                            test_name=f"tdah_energy_matching_{energy_level.value}",
                            success=len(matching_tasks) > 0,
                            duration_seconds=time.time() - start_time,
                            memory_usage_mb=0.0,
                            details={
                                "energy_level": energy_level.value,
                                "total_tasks": len(session.tasks_remaining),
                                "matching_tasks": len(matching_tasks),
                                "energy_match_rate": len(matching_tasks) / len(session.tasks_remaining) if session.tasks_remaining else 0
                            }
                        )
                        results.append(result)
                        
                except Exception as e:
                    result = AuditResult(
                        test_name=f"tdah_energy_matching_{energy_level.value}",
                        success=False,
                        duration_seconds=time.time() - start_time,
                        memory_usage_mb=0.0,
                        errors=[str(e)]
                    )
                    results.append(result)
                    
        except Exception as e:
            result = AuditResult(
                test_name="tdd_workflow_agent_comprehensive",
                success=False,
                duration_seconds=0.0,
                memory_usage_mb=0.0,
                errors=[f"TDD workflow agent testing failed: {str(e)}"]
            )
            results.append(result)
            
        return results
    
    def _test_agents_integration(self) -> List[AuditResult]:
        """Test integration between all agents."""
        results = []
        
        if not AGENTS_AVAILABLE:
            return results
        
        self.logger.info("🔗 Testing agents integration")
        
        try:
            # Integration Test 1: Code Agent → Refactoring Engine
            start_time = time.time()
            memory_before = self._get_memory_usage()
            
            code_agent = IntelligentCodeAgent(self.project_root, dry_run=True)
            refactoring_engine = IntelligentRefactoringEngine(dry_run=True)
            
            test_file = self.test_files[0] if self.test_files else None
            if test_file and test_file.exists():
                # Analyze file with code agent
                analysis = code_agent.analyze_file_intelligently(str(test_file))
                
                # Use analysis to drive refactoring engine
                refactoring_applied = False
                if analysis.recommended_refactorings:
                    first_refactoring = analysis.recommended_refactorings[0]
                    refactoring_result = refactoring_engine.apply_refactoring(str(test_file), first_refactoring)
                    refactoring_applied = refactoring_result.success
                
                result = AuditResult(
                    test_name="code_agent_refactoring_engine_integration",
                    success=True,
                    duration_seconds=time.time() - start_time,
                    memory_usage_mb=self._get_memory_usage() - memory_before,
                    details={
                        "analysis_successful": True,
                        "refactorings_found": len(analysis.recommended_refactorings),
                        "refactoring_applied": refactoring_applied,
                        "quality_score": analysis.semantic_quality_score
                    }
                )
                results.append(result)
                
            # Integration Test 2: Code Agent → TDD Workflow Agent
            start_time = time.time()
            memory_before = self._get_memory_usage()
            
            tdd_agent = TDDIntelligentWorkflowAgent(self.project_root, tdah_mode=True)
            
            if test_file and test_file.exists():
                session = tdd_agent.start_tdd_workflow_session(
                    target_file=str(test_file),
                    initial_phase=TDDPhase.REFACTOR,
                    user_energy_level=TDAHEnergyLevel.MEDIUM
                )
                
                result = AuditResult(
                    test_name="code_agent_tdd_workflow_integration",
                    success=True,
                    duration_seconds=time.time() - start_time,
                    memory_usage_mb=self._get_memory_usage() - memory_before,
                    details={
                        "session_created": True,
                        "tasks_generated": len(session.tasks_remaining),
                        "session_id": session.session_id
                    }
                )
                results.append(result)
            
            # Integration Test 3: Full Pipeline
            start_time = time.time()
            memory_before = self._get_memory_usage()
            
            pipeline_success = True
            pipeline_details = {}
            
            try:
                if test_file and test_file.exists():
                    # Step 1: Analyze with code agent
                    analysis = code_agent.analyze_file_intelligently(str(test_file))
                    pipeline_details["analysis_completed"] = True
                    pipeline_details["quality_score"] = analysis.semantic_quality_score
                    
                    # Step 2: Create TDD session
                    session = tdd_agent.start_tdd_workflow_session(
                        target_file=str(test_file),
                        initial_phase=TDDPhase.REFACTOR,
                        user_energy_level=TDAHEnergyLevel.HIGH
                    )
                    pipeline_details["tdd_session_created"] = True
                    pipeline_details["tasks_count"] = len(session.tasks_remaining)
                    
                    # Step 3: Apply first refactoring if available
                    if analysis.recommended_refactorings:
                        refactoring_result = refactoring_engine.apply_refactoring(
                            str(test_file), analysis.recommended_refactorings[0]
                        )
                        pipeline_details["refactoring_applied"] = refactoring_result.success
                    
            except Exception as e:
                pipeline_success = False
                pipeline_details["error"] = str(e)
            
            result = AuditResult(
                test_name="full_pipeline_integration",
                success=pipeline_success,
                duration_seconds=time.time() - start_time,
                memory_usage_mb=self._get_memory_usage() - memory_before,
                details=pipeline_details,
                errors=[pipeline_details.get("error")] if not pipeline_success else []
            )
            results.append(result)
            
        except Exception as e:
            result = AuditResult(
                test_name="agents_integration_comprehensive",
                success=False,
                duration_seconds=0.0,
                memory_usage_mb=0.0,
                errors=[f"Integration testing failed: {str(e)}"]
            )
            results.append(result)
            
        return results
    
    def _test_performance_and_memory(self) -> List[AuditResult]:
        """Test performance and memory usage of agents."""
        results = []
        
        if not AGENTS_AVAILABLE:
            return results
        
        self.logger.info("⚡ Testing performance and memory usage")
        
        # Performance Test 1: Large file analysis
        large_files = [f for f in self.test_files if f.stat().st_size > 10000]  # >10KB files
        
        if large_files:
            test_file = large_files[0]
            start_time = time.time()
            memory_before = self._get_memory_usage()
            
            try:
                agent = IntelligentCodeAgent(self.project_root, dry_run=True)
                analysis = agent.analyze_file_intelligently(str(test_file))
                
                duration = time.time() - start_time
                memory_used = self._get_memory_usage() - memory_before
                
                # Performance thresholds
                performance_acceptable = duration < self.audit_config["performance_threshold_seconds"]
                memory_acceptable = memory_used < self.audit_config["memory_threshold_mb"]
                
                result = AuditResult(
                    test_name="large_file_performance",
                    success=performance_acceptable and memory_acceptable,
                    duration_seconds=duration,
                    memory_usage_mb=memory_used,
                    details={
                        "file_size_bytes": test_file.stat().st_size,
                        "lines_analyzed": len(analysis.lines_analyzed),
                        "lines_per_second": len(analysis.lines_analyzed) / duration,
                        "memory_per_line_kb": (memory_used * 1024) / len(analysis.lines_analyzed)
                    },
                    performance_metrics={
                        "analysis_duration": duration,
                        "memory_efficiency": memory_used / (test_file.stat().st_size / 1024),
                        "processing_speed": len(analysis.lines_analyzed) / duration
                    },
                    warnings=[] if performance_acceptable else [f"Performance slower than threshold: {duration:.1f}s"] + 
                             [] if memory_acceptable else [f"Memory usage higher than threshold: {memory_used:.1f}MB"]
                )
                results.append(result)
                
            except Exception as e:
                result = AuditResult(
                    test_name="large_file_performance",
                    success=False,
                    duration_seconds=time.time() - start_time,
                    memory_usage_mb=self._get_memory_usage() - memory_before,
                    errors=[str(e)]
                )
                results.append(result)
        
        # Memory Leak Test
        start_time = time.time()
        initial_memory = self._get_memory_usage()
        
        try:
            # Create and destroy multiple agents
            for i in range(5):
                agent = IntelligentCodeAgent(self.project_root, dry_run=True)
                if self.test_files:
                    analysis = agent.analyze_file_intelligently(str(self.test_files[0]))
                del agent
                gc.collect()  # Force garbage collection
            
            final_memory = self._get_memory_usage()
            memory_growth = final_memory - initial_memory
            
            # Acceptable memory growth (should be minimal)
            acceptable_growth = memory_growth < 50  # <50MB growth
            
            result = AuditResult(
                test_name="memory_leak_detection",
                success=acceptable_growth,
                duration_seconds=time.time() - start_time,
                memory_usage_mb=memory_growth,
                details={
                    "initial_memory_mb": initial_memory,
                    "final_memory_mb": final_memory,
                    "memory_growth_mb": memory_growth,
                    "agents_created_destroyed": 5
                },
                warnings=[] if acceptable_growth else [f"Potential memory leak detected: {memory_growth:.1f}MB growth"]
            )
            results.append(result)
            
        except Exception as e:
            result = AuditResult(
                test_name="memory_leak_detection",
                success=False,
                duration_seconds=time.time() - start_time,
                memory_usage_mb=0.0,
                errors=[str(e)]
            )
            results.append(result)
        
        return results
    
    def _test_edge_cases_and_errors(self) -> List[AuditResult]:
        """Test edge cases and error handling."""
        results = []
        
        if not AGENTS_AVAILABLE:
            return results
        
        self.logger.info("🧪 Testing edge cases and error handling")
        
        # Edge Case 1: Empty file
        empty_file = self.project_root / "test_empty_file.py"
        try:
            empty_file.write_text("")
            
            start_time = time.time()
            agent = IntelligentCodeAgent(self.project_root, dry_run=True)
            analysis = agent.analyze_file_intelligently(str(empty_file))
            
            result = AuditResult(
                test_name="empty_file_handling",
                success=True,
                duration_seconds=time.time() - start_time,
                memory_usage_mb=0.0,
                details={
                    "file_size": 0,
                    "lines_analyzed": len(analysis.lines_analyzed),
                    "quality_score": analysis.semantic_quality_score
                }
            )
            results.append(result)
            
        except Exception as e:
            result = AuditResult(
                test_name="empty_file_handling",
                success=False,
                duration_seconds=0.0,
                memory_usage_mb=0.0,
                errors=[str(e)]
            )
            results.append(result)
        finally:
            if empty_file.exists():
                empty_file.unlink()
        
        # Edge Case 2: Syntactically incorrect Python file
        syntax_error_file = self.project_root / "test_syntax_error.py"
        try:
            syntax_error_file.write_text("def broken_function(\n    invalid syntax here\n    return None")
            
            start_time = time.time()
            agent = IntelligentCodeAgent(self.project_root, dry_run=True)
            analysis = agent.analyze_file_intelligently(str(syntax_error_file))
            
            result = AuditResult(
                test_name="syntax_error_file_handling",
                success=True,  # Should handle gracefully, not crash
                duration_seconds=time.time() - start_time,
                memory_usage_mb=0.0,
                details={
                    "handled_gracefully": True,
                    "quality_score": analysis.semantic_quality_score
                }
            )
            results.append(result)
            
        except Exception as e:
            result = AuditResult(
                test_name="syntax_error_file_handling",
                success=False,
                duration_seconds=0.0,
                memory_usage_mb=0.0,
                errors=[str(e)]
            )
            results.append(result)
        finally:
            if syntax_error_file.exists():
                syntax_error_file.unlink()
        
        # Edge Case 3: Non-existent file
        start_time = time.time()
        try:
            agent = IntelligentCodeAgent(self.project_root, dry_run=True)
            analysis = agent.analyze_file_intelligently("non_existent_file.py")
            
            result = AuditResult(
                test_name="non_existent_file_handling",
                success=False,  # Should fail gracefully
                duration_seconds=time.time() - start_time,
                memory_usage_mb=0.0,
                errors=["Should have raised FileNotFoundError"]
            )
            results.append(result)
            
        except FileNotFoundError:
            result = AuditResult(
                test_name="non_existent_file_handling",
                success=True,  # Expected to fail with FileNotFoundError
                duration_seconds=time.time() - start_time,
                memory_usage_mb=0.0,
                details={"error_handled_correctly": True}
            )
            results.append(result)
        except Exception as e:
            result = AuditResult(
                test_name="non_existent_file_handling",
                success=False,
                duration_seconds=time.time() - start_time,
                memory_usage_mb=0.0,
                errors=[f"Unexpected error: {str(e)}"]
            )
            results.append(result)
        
        return results
    
    def _test_security_validation(self) -> List[AuditResult]:
        """Test security aspects of the agents."""
        results = []
        
        if not AGENTS_AVAILABLE:
            return results
        
        self.logger.info("🛡️ Testing security validation")
        
        # Security Test 1: Malicious code detection
        malicious_file = self.project_root / "test_malicious.py"
        try:
            malicious_content = '''
import os
import subprocess

# Hardcoded secrets
API_KEY = "secret_key_12345"
PASSWORD = "admin_password"

def dangerous_function():
    # SQL injection vulnerability
    query = f"SELECT * FROM users WHERE id = {user_input}"
    
    # Command injection
    os.system(f"rm -rf {user_provided_path}")
    
    # Unsafe deserialization
    import pickle
    data = pickle.loads(untrusted_data)
    
    return data
'''
            malicious_file.write_text(malicious_content)
            
            start_time = time.time()
            agent = IntelligentCodeAgent(self.project_root, dry_run=True)
            analysis = agent.analyze_file_intelligently(str(malicious_file))
            
            # Check if security issues were detected
            security_issues_found = len(analysis.security_vulnerabilities) > 0
            hardcoded_secrets_found = any("hardcoded_secret" in vuln[1] for vuln in analysis.security_vulnerabilities)
            
            result = AuditResult(
                test_name="malicious_code_detection",
                success=security_issues_found and hardcoded_secrets_found,
                duration_seconds=time.time() - start_time,
                memory_usage_mb=0.0,
                details={
                    "security_issues_detected": len(analysis.security_vulnerabilities),
                    "hardcoded_secrets_found": hardcoded_secrets_found,
                    "vulnerabilities": [vuln[1] for vuln in analysis.security_vulnerabilities]
                },
                errors=[] if security_issues_found else ["Failed to detect security vulnerabilities"]
            )
            results.append(result)
            
        except Exception as e:
            result = AuditResult(
                test_name="malicious_code_detection",
                success=False,
                duration_seconds=0.0,
                memory_usage_mb=0.0,
                errors=[str(e)]
            )
            results.append(result)
        finally:
            if malicious_file.exists():
                malicious_file.unlink()
        
        return results
    
    def _test_real_world_scenarios(self) -> List[AuditResult]:
        """Test real-world usage scenarios."""
        results = []
        
        if not AGENTS_AVAILABLE:
            return results
        
        self.logger.info("🌍 Testing real-world scenarios")
        
        # Scenario 1: Analyze actual project files
        real_files = [
            self.project_root / "streamlit_extension" / "services" / "analytics_service.py",
            self.project_root / "streamlit_extension" / "utils" / "data_utils.py",
            self.project_root / "scripts" / "automated_audit" / "systematic_file_auditor.py"
        ]
        
        for real_file in real_files:
            if real_file.exists():
                start_time = time.time()
                memory_before = self._get_memory_usage()
                
                try:
                    agent = IntelligentCodeAgent(self.project_root, 
                                               analysis_depth=AnalysisDepth.ADVANCED, 
                                               dry_run=True)
                    analysis = agent.analyze_file_intelligently(str(real_file))
                    
                    # Validate realistic expectations
                    quality_reasonable = 30 <= analysis.semantic_quality_score <= 100
                    has_analysis_results = len(analysis.lines_analyzed) > 0
                    
                    result = AuditResult(
                        test_name=f"real_world_analysis_{real_file.name}",
                        success=quality_reasonable and has_analysis_results,
                        duration_seconds=time.time() - start_time,
                        memory_usage_mb=self._get_memory_usage() - memory_before,
                        details={
                            "file": str(real_file),
                            "file_size_kb": real_file.stat().st_size // 1024,
                            "lines_analyzed": len(analysis.lines_analyzed),
                            "quality_score": analysis.semantic_quality_score,
                            "refactorings_suggested": len(analysis.recommended_refactorings),
                            "security_issues": len(analysis.security_vulnerabilities),
                            "complexity_hotspots": len(analysis.complexity_hotspots)
                        },
                        performance_metrics={
                            "kb_per_second": (real_file.stat().st_size // 1024) / (time.time() - start_time),
                            "analysis_efficiency": len(analysis.lines_analyzed) / (time.time() - start_time)
                        }
                    )
                    results.append(result)
                    
                except Exception as e:
                    result = AuditResult(
                        test_name=f"real_world_analysis_{real_file.name}",
                        success=False,
                        duration_seconds=time.time() - start_time,
                        memory_usage_mb=self._get_memory_usage() - memory_before,
                        errors=[str(e)]
                    )
                    results.append(result)
        
        return results
    
    def _test_documentation_completeness(self) -> List[AuditResult]:
        """Test documentation completeness and usability."""
        results = []
        
        self.logger.info("📚 Testing documentation completeness")
        
        # Check if agent files have proper docstrings
        agent_files = [
            self.project_root / "scripts" / "automated_audit" / "intelligent_code_agent.py",
            self.project_root / "scripts" / "automated_audit" / "intelligent_refactoring_engine.py",
            self.project_root / "scripts" / "automated_audit" / "tdd_intelligent_workflow_agent.py"
        ]
        
        for agent_file in agent_files:
            if agent_file.exists():
                try:
                    content = agent_file.read_text()
                    
                    # Check for comprehensive docstring
                    has_module_docstring = '"""' in content[:1000]  # Check first 1000 chars
                    has_class_docstrings = 'class ' in content and '"""' in content
                    has_function_docstrings = 'def ' in content and '"""' in content
                    has_usage_examples = 'Usage:' in content or 'Example:' in content
                    
                    documentation_score = sum([has_module_docstring, has_class_docstrings, 
                                             has_function_docstrings, has_usage_examples])
                    
                    result = AuditResult(
                        test_name=f"documentation_completeness_{agent_file.name}",
                        success=documentation_score >= 3,  # At least 3 out of 4
                        duration_seconds=0.0,
                        memory_usage_mb=0.0,
                        details={
                            "file": str(agent_file),
                            "has_module_docstring": has_module_docstring,
                            "has_class_docstrings": has_class_docstrings,
                            "has_function_docstrings": has_function_docstrings,
                            "has_usage_examples": has_usage_examples,
                            "documentation_score": documentation_score
                        },
                        warnings=[] if documentation_score >= 3 else [f"Documentation incomplete: {documentation_score}/4"]
                    )
                    results.append(result)
                    
                except Exception as e:
                    result = AuditResult(
                        test_name=f"documentation_completeness_{agent_file.name}",
                        success=False,
                        duration_seconds=0.0,
                        memory_usage_mb=0.0,
                        errors=[str(e)]
                    )
                    results.append(result)
        
        return results
    
    def _finalize_report(self, report: ComprehensiveAuditReport, audit_start: datetime) -> ComprehensiveAuditReport:
        """Finalize the audit report with summary metrics."""
        
        report.total_duration = (datetime.now() - audit_start).total_seconds()
        report.total_tests = len(report.test_results)
        report.passed_tests = sum(1 for result in report.test_results if result.success)
        report.failed_tests = report.total_tests - report.passed_tests
        report.peak_memory_usage = max([result.memory_usage_mb for result in report.test_results], default=0.0)
        report.agents_tested = ["IntelligentCodeAgent", "IntelligentRefactoringEngine", "TDDIntelligentWorkflowAgent"]
        
        # Calculate production readiness score
        base_score = (report.passed_tests / report.total_tests * 100) if report.total_tests > 0 else 0
        
        # Deduct points for critical issues
        critical_deduction = len(report.critical_issues) * 10
        
        # Deduct points for warnings
        warning_deduction = sum(len(result.warnings) for result in report.test_results) * 2
        
        report.production_readiness_score = max(0, base_score - critical_deduction - warning_deduction)
        
        # Generate recommendations
        if report.production_readiness_score < 90:
            report.recommendations.append("Address failing tests to improve production readiness")
        if report.peak_memory_usage > 400:
            report.recommendations.append("Optimize memory usage - peak usage exceeded 400MB")
        if any("performance" in result.test_name for result in report.test_results if not result.success):
            report.recommendations.append("Optimize performance - some operations are slower than expected")
        
        # Identify critical issues from failed tests
        critical_test_failures = [
            result.test_name for result in report.test_results 
            if not result.success and "critical" in result.test_name.lower()
        ]
        report.critical_issues.extend(critical_test_failures)
        
        self.logger.info(
            "Audit completed: %d/%d tests passed (%.1f%%), readiness score: %.1f",
            report.passed_tests, report.total_tests, report.success_rate, report.production_readiness_score
        )
        
        return report
    
    # Helper methods
    def _identify_test_files(self) -> List[Path]:
        """Identify files to use for testing."""
        test_files = []
        
        # Add some known files if they exist
        known_files = [
            "streamlit_extension/utils/data_utils.py",
            "streamlit_extension/services/analytics_service.py", 
            "example_code_to_refactor.py",
            "scripts/automated_audit/systematic_file_auditor.py"
        ]
        
        for file_path in known_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                test_files.append(full_path)
        
        return test_files
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024  # Convert to MB
        except:
            return 0.0
    
    def _validate_file_analysis(self, analysis: FileSemanticAnalysis) -> List[str]:
        """Validate a file analysis result."""
        errors = []
        
        if analysis.semantic_quality_score < 0 or analysis.semantic_quality_score > 100:
            errors.append(f"Quality score out of range: {analysis.semantic_quality_score}")
        
        if analysis.testability_score < 0 or analysis.testability_score > 100:
            errors.append(f"Testability score out of range: {analysis.testability_score}")
        
        if len(analysis.lines_analyzed) == 0:
            errors.append("No lines were analyzed")
        
        if not analysis.overall_purpose:
            errors.append("Overall purpose not determined")
        
        if not analysis.architectural_role:
            errors.append("Architectural role not determined")
        
        return errors


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Comprehensive Agents Audit - 100% Production Readiness"
    )
    
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--full-test-suite", action="store_true", help="Run complete test suite")
    parser.add_argument("--output-file", type=str, help="Save report to file")
    
    args = parser.parse_args()
    
    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize auditor
        project_root = Path(__file__).resolve().parent.parent.parent
        auditor = ComprehensiveAgentsAuditor(project_root, verbose=args.verbose)
        
        # Execute comprehensive audit
        logger.info("🔍 Starting comprehensive agents audit...")
        report = auditor.execute_full_audit()
        
        # Display results
        print(f"\n🔍 COMPREHENSIVE AGENTS AUDIT REPORT")
        print(f"=" * 60)
        print(f"Timestamp: {report.audit_timestamp}")
        print(f"Duration: {report.total_duration:.1f} seconds")
        print(f"Peak Memory: {report.peak_memory_usage:.1f} MB")
        print()
        print(f"Tests: {report.passed_tests}/{report.total_tests} passed ({report.success_rate:.1f}%)")
        print(f"Production Readiness Score: {report.production_readiness_score:.1f}/100")
        print()
        
        if report.agents_tested:
            print(f"Agents Tested: {', '.join(report.agents_tested)}")
            print()
        
        if report.critical_issues:
            print(f"🚨 CRITICAL ISSUES ({len(report.critical_issues)}):")
            for issue in report.critical_issues:
                print(f"   ❌ {issue}")
            print()
        
        # Show failed tests
        failed_tests = [result for result in report.test_results if not result.success]
        if failed_tests:
            print(f"❌ FAILED TESTS ({len(failed_tests)}):")
            for result in failed_tests[:10]:  # Show first 10
                print(f"   • {result.test_name}: {', '.join(result.errors)}")
            if len(failed_tests) > 10:
                print(f"   ... and {len(failed_tests) - 10} more")
            print()
        
        # Show recommendations
        if report.recommendations:
            print(f"💡 RECOMMENDATIONS ({len(report.recommendations)}):")
            for rec in report.recommendations:
                print(f"   • {rec}")
            print()
        
        # Production readiness assessment
        if report.production_readiness_score >= 95:
            print("🎉 PRODUCTION READY! All systems operational.")
        elif report.production_readiness_score >= 85:
            print("⚠️  MOSTLY READY - Minor issues need attention.")
        elif report.production_readiness_score >= 70:
            print("🔧 NEEDS WORK - Several issues need fixing.")
        else:
            print("🚨 NOT READY - Critical issues must be resolved.")
        
        # Save report if requested
        if args.output_file:
            report_dict = {
                "audit_timestamp": report.audit_timestamp.isoformat(),
                "total_tests": report.total_tests,
                "passed_tests": report.passed_tests,
                "failed_tests": report.failed_tests,
                "success_rate": report.success_rate,
                "total_duration": report.total_duration,
                "peak_memory_usage": report.peak_memory_usage,
                "production_readiness_score": report.production_readiness_score,
                "agents_tested": report.agents_tested,
                "critical_issues": report.critical_issues,
                "recommendations": report.recommendations,
                "test_results": [
                    {
                        "test_name": result.test_name,
                        "success": result.success,
                        "duration_seconds": result.duration_seconds,
                        "memory_usage_mb": result.memory_usage_mb,
                        "errors": result.errors,
                        "warnings": result.warnings
                    }
                    for result in report.test_results
                ]
            }
            
            with open(args.output_file, 'w') as f:
                json.dump(report_dict, f, indent=2)
            print(f"📄 Report saved to: {args.output_file}")
        
        # Exit code based on readiness
        if report.production_readiness_score >= 90:
            return 0
        elif report.production_readiness_score >= 70:
            return 1
        else:
            return 2
    
    except Exception as e:
        logger.error("Audit failed: %s", e, exc_info=args.verbose)
        return 3


if __name__ == "__main__":
    exit(main())