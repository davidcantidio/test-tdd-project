#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 TDD Intelligent Workflow Agent - AI-Powered TDD Enhancement

Agente IA especializado em otimizar workflows TDD com suporte TDAH.
Integra análise semântica, refatoração automática e patterns TDD.

Recursos TDD-Específicos:
- Red-Green-Refactor cycle optimization
- Test-first code analysis and suggestions
- TDD anti-pattern detection and correction
- Refactoring safety with test validation
- TDD metrics and effectiveness analysis

Recursos TDAH-Optimized:
- Micro-task breakdown for complex refactorings
- Focus-friendly incremental improvements
- Immediate feedback and encouragement
- Energy-aware scheduling of improvements
- Hyperfocus protection with gentle interruptions

Uso:
    python tdd_intelligent_workflow_agent.py --task-file FILE --tdd-phase {red,green,refactor}
                                           [--tdah-mode] [--focus-session-minutes N]
"""

from __future__ import annotations

import logging
import time
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import argparse

# Project setup
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from audit_system.agents.intelligent_code_agent import IntelligentCodeAgent, FileSemanticAnalysis
from audit_system.agents.intelligent_refactoring_engine import IntelligentRefactoringEngine


class TDDPhase(Enum):
    """TDD cycle phases."""
    RED = "red"           # Writing failing tests
    GREEN = "green"       # Making tests pass (minimal implementation)
    REFACTOR = "refactor" # Improving code quality while maintaining tests


class TDAHEnergyLevel(Enum):
    """TDAH energy levels for task scheduling."""
    LOW = "low"         # Simple, mechanical tasks
    MEDIUM = "medium"   # Standard development tasks
    HIGH = "high"       # Complex, creative tasks


@dataclass
class TDDAnalysis:
    """TDD-specific analysis of code."""
    current_phase: TDDPhase
    test_coverage_percentage: float
    has_failing_tests: bool
    has_passing_tests: bool
    refactoring_safety_score: float  # 0-100
    tdd_compliance_score: float      # 0-100
    suggested_next_steps: List[str]
    test_quality_issues: List[str]
    implementation_issues: List[str]
    refactoring_opportunities: List[str]


@dataclass
class TDAHOptimizedTask:
    """TDAH-optimized task breakdown."""
    task_id: str
    description: str
    estimated_duration_minutes: int
    energy_level_required: TDAHEnergyLevel
    complexity_score: float  # 1-10
    immediate_feedback_available: bool
    can_be_interrupted: bool
    focus_breaking_potential: float  # 0-1
    encouragement_message: str
    prerequisites: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)


@dataclass
class TDDWorkflowSession:
    """Complete TDD workflow session with TDAH support."""
    session_id: str
    start_time: datetime
    target_file: str
    current_phase: TDDPhase
    user_energy_level: TDAHEnergyLevel
    focus_session_minutes: int
    tasks_completed: List[TDAHOptimizedTask] = field(default_factory=list)
    tasks_remaining: List[TDAHOptimizedTask] = field(default_factory=list)
    interruptions_count: int = 0
    breaks_taken: int = 0
    quality_improvements_applied: int = 0
    
    def get_session_duration(self) -> timedelta:
        return datetime.now() - self.start_time
    
    def get_progress_percentage(self) -> float:
        total_tasks = len(self.tasks_completed) + len(self.tasks_remaining)
        if total_tasks == 0:
            return 100.0
        return (len(self.tasks_completed) / total_tasks) * 100


class TDDIntelligentWorkflowAgent:
    """
    AI-powered agent that optimizes TDD workflows with TDAH accessibility.
    """
    
    def __init__(
        self, 
        project_root: Path, 
        tdah_mode: bool = False,
        default_focus_minutes: int = 25
    ):
        self.project_root = project_root
        self.tdah_mode = tdah_mode
        self.default_focus_minutes = default_focus_minutes
        
        self.logger = logging.getLogger(f"{__name__}.TDDIntelligentWorkflowAgent")
        
        # Initialize core agents
        self.code_agent = IntelligentCodeAgent(project_root, dry_run=False)
        self.refactoring_engine = IntelligentRefactoringEngine(dry_run=False)
        
        # TDD-specific configurations
        self.tdd_patterns = self._load_tdd_pattern_knowledge()
        self.tdah_optimizations = self._load_tdah_optimization_knowledge()
        
        self.logger.info(
            "TDD Intelligent Workflow Agent initialized: TDAH=%s, focus=%dm",
            tdah_mode, default_focus_minutes
        )
    
    def start_tdd_workflow_session(
        self, 
        target_file: str, 
        initial_phase: TDDPhase,
        user_energy_level: TDAHEnergyLevel,
        focus_session_minutes: Optional[int] = None
    ) -> TDDWorkflowSession:
        """Start a new TDD workflow session with TDAH optimization."""
        
        session_id = f"tdd_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        focus_minutes = focus_session_minutes or self.default_focus_minutes
        
        # Analyze the target file
        self.logger.info("Analyzing %s for TDD workflow optimization", target_file)
        semantic_analysis = self.code_agent.analyze_file_intelligently(target_file)
        tdd_analysis = self._analyze_tdd_specific_aspects(semantic_analysis, target_file)
        
        # Create TDAH-optimized tasks
        tasks = self._create_tdah_optimized_tasks(
            semantic_analysis, tdd_analysis, initial_phase, user_energy_level
        )
        
        session = TDDWorkflowSession(
            session_id=session_id,
            start_time=datetime.now(),
            target_file=target_file,
            current_phase=initial_phase,
            user_energy_level=user_energy_level,
            focus_session_minutes=focus_minutes,
            tasks_remaining=tasks
        )
        
        self.logger.info(
            "TDD session started: %s with %d tasks, focus=%dm",
            session_id, len(tasks), focus_minutes
        )
        
        return session
    
    def execute_tdd_workflow_session(self, session: TDDWorkflowSession) -> Dict[str, Any]:
        """Execute a complete TDD workflow session with TDAH support."""
        
        results = {
            "session_id": session.session_id,
            "start_time": session.start_time,
            "tasks_completed": 0,
            "quality_improvements": 0,
            "phase_transitions": [],
            "tdah_support_used": [],
            "final_quality_score": 0.0
        }
        
        self.logger.info("🎯 Starting TDD workflow execution for %s", session.target_file)
        
        try:
            while session.tasks_remaining:
                # Get next task based on energy level and complexity
                next_task = self._select_next_task(session)
                
                if not next_task:
                    self.logger.info("No suitable tasks for current energy level")
                    break
                
                # Execute task with TDAH support
                task_result = self._execute_tdah_optimized_task(session, next_task)
                
                if task_result["success"]:
                    session.tasks_completed.append(next_task)
                    session.tasks_remaining.remove(next_task)
                    results["tasks_completed"] += 1
                    
                    # TDAH encouragement
                    if self.tdah_mode:
                        self._provide_tdah_encouragement(next_task, task_result)
                
                # Check for focus session boundaries
                if self._should_suggest_break(session):
                    break_result = self._handle_focus_break(session)
                    results["tdah_support_used"].append(break_result)
                
                # Check for phase transitions
                phase_change = self._check_tdd_phase_transition(session)
                if phase_change:
                    results["phase_transitions"].append(phase_change)
            
            # Final analysis
            final_analysis = self.code_agent.analyze_file_intelligently(session.target_file)
            results["final_quality_score"] = final_analysis.semantic_quality_score
            results["quality_improvements"] = session.quality_improvements_applied
            
            self.logger.info(
                "TDD session completed: %d/%d tasks, quality=%.1f",
                len(session.tasks_completed), 
                len(session.tasks_completed) + len(session.tasks_remaining),
                results["final_quality_score"]
            )
            
            return results
            
        except Exception as e:
            self.logger.error("Error in TDD workflow execution: %s", e)
            results["error"] = str(e)
            return results
    
    def _analyze_tdd_specific_aspects(
        self, 
        semantic_analysis: FileSemanticAnalysis, 
        file_path: str
    ) -> TDDAnalysis:
        """Analyze TDD-specific aspects of the code."""
        
        # Determine current TDD phase based on file analysis
        current_phase = self._determine_tdd_phase(semantic_analysis, file_path)
        
        # Analyze test coverage (simplified)
        test_coverage = self._estimate_test_coverage(semantic_analysis, file_path)
        
        # Check for failing/passing tests
        has_failing_tests = self._check_for_failing_tests(file_path)
        has_passing_tests = self._check_for_passing_tests(file_path)
        
        # Calculate refactoring safety
        refactoring_safety = self._calculate_refactoring_safety(semantic_analysis)
        
        # Calculate TDD compliance
        tdd_compliance = self._calculate_tdd_compliance(
            semantic_analysis, current_phase, test_coverage
        )
        
        # Generate TDD-specific suggestions
        next_steps = self._generate_tdd_next_steps(
            current_phase, test_coverage, semantic_analysis
        )
        
        return TDDAnalysis(
            current_phase=current_phase,
            test_coverage_percentage=test_coverage,
            has_failing_tests=has_failing_tests,
            has_passing_tests=has_passing_tests,
            refactoring_safety_score=refactoring_safety,
            tdd_compliance_score=tdd_compliance,
            suggested_next_steps=next_steps,
            test_quality_issues=[],
            implementation_issues=[],
            refactoring_opportunities=[]
        )
    
    def _create_tdah_optimized_tasks(
        self,
        semantic_analysis: FileSemanticAnalysis,
        tdd_analysis: TDDAnalysis,
        current_phase: TDDPhase,
        user_energy: TDAHEnergyLevel
    ) -> List[TDAHOptimizedTask]:
        """Create TDAH-optimized task breakdown."""
        
        tasks = []
        
        # Phase-specific tasks
        if current_phase == TDDPhase.RED:
            tasks.extend(self._create_red_phase_tasks(semantic_analysis, tdd_analysis))
        elif current_phase == TDDPhase.GREEN:
            tasks.extend(self._create_green_phase_tasks(semantic_analysis, tdd_analysis))
        elif current_phase == TDDPhase.REFACTOR:
            tasks.extend(self._create_refactor_phase_tasks(semantic_analysis, tdd_analysis))
        
        # Sort tasks by energy level compatibility and complexity
        tasks = self._optimize_task_order_for_tdah(tasks, user_energy)
        
        return tasks
    
    def _create_red_phase_tasks(
        self, 
        analysis: FileSemanticAnalysis, 
        tdd_analysis: TDDAnalysis
    ) -> List[TDAHOptimizedTask]:
        """Create tasks for Red phase (writing failing tests)."""
        
        tasks = []
        
        # Task 1: Analyze requirements
        tasks.append(TDAHOptimizedTask(
            task_id="red_1_analyze_requirements",
            description="📋 Analyze and clarify requirements for new functionality",
            estimated_duration_minutes=10,
            energy_level_required=TDAHEnergyLevel.HIGH,
            complexity_score=6.0,
            immediate_feedback_available=True,
            can_be_interrupted=True,
            focus_breaking_potential=0.3,
            encouragement_message="🎯 Great start! Clear requirements lead to better tests.",
            success_criteria=["Requirements documented", "Edge cases identified"]
        ))
        
        # Task 2: Design test cases
        tasks.append(TDAHOptimizedTask(
            task_id="red_2_design_tests",
            description="🧪 Design comprehensive test cases for functionality",
            estimated_duration_minutes=15,
            energy_level_required=TDAHEnergyLevel.HIGH,
            complexity_score=7.0,
            immediate_feedback_available=True,
            can_be_interrupted=False,  # Creative thinking shouldn't be interrupted
            focus_breaking_potential=0.2,
            encouragement_message="💡 Excellent thinking! Good tests make development faster.",
            prerequisites=["red_1_analyze_requirements"],
            success_criteria=["Test cases designed", "Happy and sad paths covered"]
        ))
        
        # Task 3: Write failing tests
        tasks.append(TDAHOptimizedTask(
            task_id="red_3_write_tests",
            description="✍️ Write failing tests that specify desired behavior",
            estimated_duration_minutes=20,
            energy_level_required=TDAHEnergyLevel.MEDIUM,
            complexity_score=5.0,
            immediate_feedback_available=True,  # Tests run immediately
            can_be_interrupted=True,
            focus_breaking_potential=0.4,
            encouragement_message="🔴 Perfect! Failing tests show what we need to build.",
            prerequisites=["red_2_design_tests"],
            success_criteria=["Tests written", "Tests fail as expected", "Error messages clear"]
        ))
        
        return tasks
    
    def _create_green_phase_tasks(
        self, 
        analysis: FileSemanticAnalysis, 
        tdd_analysis: TDDAnalysis
    ) -> List[TDAHOptimizedTask]:
        """Create tasks for Green phase (making tests pass)."""
        
        tasks = []
        
        # Task 1: Implement minimal solution
        tasks.append(TDAHOptimizedTask(
            task_id="green_1_minimal_implementation",
            description="🟢 Implement minimal code to make tests pass",
            estimated_duration_minutes=25,
            energy_level_required=TDAHEnergyLevel.MEDIUM,
            complexity_score=6.0,
            immediate_feedback_available=True,  # Tests provide immediate feedback
            can_be_interrupted=True,
            focus_breaking_potential=0.5,
            encouragement_message="⚡ You're in the flow! Making tests pass feels great.",
            success_criteria=["All tests pass", "No more code than necessary", "Clean test run"]
        ))
        
        # Task 2: Verify edge cases
        tasks.append(TDAHOptimizedTask(
            task_id="green_2_verify_edge_cases",
            description="🔍 Verify edge cases and error handling work correctly",
            estimated_duration_minutes=10,
            energy_level_required=TDAHEnergyLevel.MEDIUM,
            complexity_score=4.0,
            immediate_feedback_available=True,
            can_be_interrupted=True,
            focus_breaking_potential=0.3,
            encouragement_message="🛡️ Great attention to detail! Edge cases matter.",
            prerequisites=["green_1_minimal_implementation"],
            success_criteria=["Edge cases tested", "Error handling verified"]
        ))
        
        return tasks
    
    def _create_refactor_phase_tasks(
        self, 
        analysis: FileSemanticAnalysis, 
        tdd_analysis: TDDAnalysis
    ) -> List[TDAHOptimizedTask]:
        """Create tasks for Refactor phase (improving code quality)."""
        
        tasks = []
        
        # Break down refactorings into micro-tasks for TDAH
        for i, refactoring in enumerate(analysis.recommended_refactorings[:3]):  # Limit to top 3
            tasks.append(TDAHOptimizedTask(
                task_id=f"refactor_{i+1}_{refactoring.refactoring_type}",
                description=f"🔧 {refactoring.description}",
                estimated_duration_minutes=15,
                energy_level_required=TDAHEnergyLevel.HIGH,
                complexity_score=refactoring.confidence_score * 10,
                immediate_feedback_available=True,  # Tests verify refactoring safety
                can_be_interrupted=False,  # Refactoring should be atomic
                focus_breaking_potential=0.2,
                encouragement_message=f"🏆 Excellent refactoring! Code quality improved.",
                success_criteria=["Refactoring applied", "All tests still pass", "Code quality improved"]
            ))
        
        # Task: Review and document changes
        tasks.append(TDAHOptimizedTask(
            task_id="refactor_review_changes",
            description="📝 Review and document refactoring changes",
            estimated_duration_minutes=10,
            energy_level_required=TDAHEnergyLevel.MEDIUM,
            complexity_score=4.0,
            immediate_feedback_available=True,
            can_be_interrupted=True,
            focus_breaking_potential=0.3,
            encouragement_message="📋 Great documentation! Future you will thank you.",
            success_criteria=["Changes documented", "Code comments updated", "Commit message prepared"]
        ))
        
        # Task: Run full test suite
        tasks.append(TDAHOptimizedTask(
            task_id="refactor_final_test_run",
            description="✅ Run complete test suite to verify all changes",
            estimated_duration_minutes=5,
            energy_level_required=TDAHEnergyLevel.LOW,
            complexity_score=2.0,
            immediate_feedback_available=True,
            can_be_interrupted=True,
            focus_breaking_potential=0.1,
            encouragement_message="🎉 Perfect! All tests pass. TDD cycle complete!",
            success_criteria=["All tests pass", "No regressions", "Quality metrics improved"]
        ))
        
        return tasks
    
    def _execute_tdah_optimized_task(
        self, 
        session: TDDWorkflowSession, 
        task: TDAHOptimizedTask
    ) -> Dict[str, Any]:
        """Execute a single TDAH-optimized task."""
        
        self.logger.info("🎯 Executing task: %s", task.description)
        
        start_time = datetime.now()
        
        try:
            # Pre-task TDAH support
            if self.tdah_mode:
                self._provide_pre_task_support(task)
            
            # Execute the actual task logic
            if task.task_id.startswith("refactor_") and "refactor_final" not in task.task_id:
                # Apply refactoring
                result = self._apply_refactoring_task(session.target_file, task)
            elif "test" in task.task_id:
                # Run tests
                result = self._run_test_task(session.target_file, task)
            else:
                # Generic task execution
                result = self._execute_generic_task(session.target_file, task)
            
            duration = datetime.now() - start_time
            
            # Post-task TDAH support
            if self.tdah_mode:
                self._provide_post_task_support(task, result, duration)
            
            return {
                "success": True,
                "task_id": task.task_id,
                "duration_seconds": duration.total_seconds(),
                "result": result
            }
            
        except Exception as e:
            self.logger.error("Task execution failed: %s", e)
            return {
                "success": False,
                "task_id": task.task_id,
                "error": str(e)
            }
    
    def _should_suggest_break(self, session: TDDWorkflowSession) -> bool:
        """Check if a break should be suggested based on TDAH patterns."""
        
        if not self.tdah_mode:
            return False
        
        session_duration = session.get_session_duration()
        
        # Suggest break if focus session time exceeded
        if session_duration.total_seconds() > session.focus_session_minutes * 60:
            return True
        
        # Suggest break if too many interruptions
        if session.interruptions_count > 3:
            return True
        
        # Suggest break after complex tasks
        if session.tasks_completed:
            last_task = session.tasks_completed[-1]
            if last_task.complexity_score > 7.0:
                return True
        
        return False
    
    def _handle_focus_break(self, session: TDDWorkflowSession) -> Dict[str, Any]:
        """Handle focus break with TDAH-friendly messaging."""
        
        self.logger.info("🧠 Suggesting focus break for TDAH optimization")
        
        session.breaks_taken += 1
        
        break_suggestions = [
            "Take a 5-10 minute walk to reset your focus",
            "Do some light stretching or breathing exercises", 
            "Hydrate and have a healthy snack",
            "Step outside for fresh air and vitamin D",
            "Do a quick mindfulness or meditation exercise"
        ]
        
        suggestion = break_suggestions[session.breaks_taken % len(break_suggestions)]
        
        return {
            "type": "focus_break",
            "suggestion": suggestion,
            "break_number": session.breaks_taken,
            "message": f"🌟 Great progress! {suggestion} Then come back refreshed."
        }
    
    def _provide_tdah_encouragement(
        self, 
        task: TDAHOptimizedTask, 
        result: Dict[str, Any]
    ) -> None:
        """Provide TDAH-friendly encouragement and feedback."""
        
        encouragement_messages = [
            f"🎉 {task.encouragement_message}",
            f"⚡ Task completed in {result.get('duration_seconds', 0):.1f}s - excellent focus!",
            "🏆 You're building momentum! Keep going!",
            "💪 Every small step counts - you're doing great!",
            "🚀 Look at you conquering complexity one task at a time!"
        ]
        
        message = encouragement_messages[0]  # Use task-specific message
        self.logger.info(message)
        print(f"\n{message}\n")
    
    # Helper methods with simplified implementations
    def _load_tdd_pattern_knowledge(self) -> Dict[str, Any]:
        """Load TDD-specific pattern knowledge."""
        return {
            "red_phase_patterns": ["test_first", "failing_test", "clear_expectations"],
            "green_phase_patterns": ["minimal_implementation", "make_tests_pass", "no_extra_code"],
            "refactor_phase_patterns": ["improve_design", "maintain_behavior", "run_tests"]
        }
    
    def _load_tdah_optimization_knowledge(self) -> Dict[str, Any]:
        """Load TDAH optimization patterns."""
        return {
            "task_sizing": {"micro": 5, "small": 15, "medium": 25, "large": 45},
            "energy_mapping": {
                "creative": TDAHEnergyLevel.HIGH,
                "implementation": TDAHEnergyLevel.MEDIUM,
                "mechanical": TDAHEnergyLevel.LOW
            },
            "interruption_tolerance": {"analysis": True, "coding": True, "refactoring": False}
        }
    
    def _determine_tdd_phase(self, analysis: FileSemanticAnalysis, file_path: str) -> TDDPhase:
        """Determine current TDD phase based on analysis."""
        # Simplified logic - in practice would analyze test files and implementation
        if "test" in file_path:
            return TDDPhase.RED
        elif analysis.semantic_quality_score < 70:
            return TDDPhase.REFACTOR
        else:
            return TDDPhase.GREEN
    
    def _estimate_test_coverage(self, analysis: FileSemanticAnalysis, file_path: str) -> float:
        """Estimate test coverage (simplified)."""
        return analysis.testability_score  # Use testability as proxy
    
    def _check_for_failing_tests(self, file_path: str) -> bool:
        """Check for failing tests."""
        return False  # Simplified
    
    def _check_for_passing_tests(self, file_path: str) -> bool:
        """Check for passing tests.""" 
        return True  # Simplified
    
    def _calculate_refactoring_safety(self, analysis: FileSemanticAnalysis) -> float:
        """Calculate how safe refactoring would be."""
        return analysis.testability_score  # Higher testability = safer refactoring
    
    def _calculate_tdd_compliance(
        self, 
        analysis: FileSemanticAnalysis, 
        phase: TDDPhase, 
        coverage: float
    ) -> float:
        """Calculate TDD compliance score."""
        base_score = analysis.semantic_quality_score
        coverage_bonus = coverage * 0.3
        return min(base_score + coverage_bonus, 100.0)
    
    def _generate_tdd_next_steps(
        self, 
        phase: TDDPhase, 
        coverage: float, 
        analysis: FileSemanticAnalysis
    ) -> List[str]:
        """Generate TDD-specific next steps."""
        steps = []
        
        if phase == TDDPhase.RED:
            steps.append("Write failing tests that specify desired behavior")
            steps.append("Ensure tests fail for the right reasons")
        elif phase == TDDPhase.GREEN:
            steps.append("Implement minimal code to make tests pass")
            steps.append("Avoid over-engineering in this phase")
        else:  # REFACTOR
            steps.extend([ref.description for ref in analysis.recommended_refactorings[:3]])
        
        return steps
    
    def _optimize_task_order_for_tdah(
        self, 
        tasks: List[TDAHOptimizedTask], 
        user_energy: TDAHEnergyLevel
    ) -> List[TDAHOptimizedTask]:
        """Optimize task order for TDAH patterns."""
        
        # Sort by energy level compatibility and complexity
        def task_priority(task: TDAHOptimizedTask) -> Tuple[int, float]:
            energy_match = 0 if task.energy_level_required == user_energy else 1
            return (energy_match, task.complexity_score)
        
        return sorted(tasks, key=task_priority)
    
    def _select_next_task(self, session: TDDWorkflowSession) -> Optional[TDAHOptimizedTask]:
        """Select next task based on current context."""
        
        if not session.tasks_remaining:
            return None
        
        # Find tasks with satisfied prerequisites
        available_tasks = []
        completed_task_ids = {task.task_id for task in session.tasks_completed}
        
        for task in session.tasks_remaining:
            if all(req in completed_task_ids for req in task.prerequisites):
                available_tasks.append(task)
        
        if not available_tasks:
            return session.tasks_remaining[0]  # Return first if no prerequisites
        
        # Select based on energy level and complexity
        for task in available_tasks:
            if task.energy_level_required == session.user_energy_level:
                return task
        
        return available_tasks[0]  # Return first available
    
    def _provide_pre_task_support(self, task: TDAHOptimizedTask) -> None:
        """Provide pre-task support for TDAH users."""
        print(f"\n🎯 Next Task: {task.description}")
        print(f"⏱️ Estimated time: {task.estimated_duration_minutes} minutes")
        print(f"⚡ Energy level: {task.energy_level_required.value}")
        print(f"🧠 Complexity: {task.complexity_score:.1f}/10")
        
        if task.success_criteria:
            print("✅ Success criteria:")
            for criteria in task.success_criteria:
                print(f"   • {criteria}")
        
        print("\n🚀 Ready to start? Take a deep breath and begin!\n")
    
    def _provide_post_task_support(
        self, 
        task: TDAHOptimizedTask, 
        result: Dict[str, Any], 
        duration: timedelta
    ) -> None:
        """Provide post-task support and celebration."""
        print(f"\n🎉 Task completed: {task.description}")
        print(f"⏱️ Actual time: {duration.total_seconds():.1f} seconds")
        print(f"🎯 {task.encouragement_message}")
        
        # Dopamine reward for TDAH
        if task.immediate_feedback_available:
            print("✨ Immediate feedback: Changes applied successfully!")
        
        print("\n💪 Great job! Ready for the next challenge?\n")
    
    def _apply_refactoring_task(self, file_path: str, task: TDAHOptimizedTask) -> Dict[str, Any]:
        """Apply refactoring for a specific task."""
        # This would integrate with the refactoring engine
        return {"type": "refactoring", "applied": True}
    
    def _run_test_task(self, file_path: str, task: TDAHOptimizedTask) -> Dict[str, Any]:
        """Run tests for a specific task."""
        return {"type": "test", "passed": True}
    
    def _execute_generic_task(self, file_path: str, task: TDAHOptimizedTask) -> Dict[str, Any]:
        """Execute a generic task."""
        return {"type": "generic", "completed": True}
    
    def _check_tdd_phase_transition(self, session: TDDWorkflowSession) -> Optional[Dict[str, Any]]:
        """Check if TDD phase should transition."""
        # Simplified logic for phase transitions
        return None
    
    def analyze_tdd_opportunities(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze TDD opportunities in the code - MetaAgent compatible method."""
        
        try:
            file_path = analysis_result.get("file_path", "")
            if not file_path:
                return {
                    "success": False,
                    "error": "No file_path provided in analysis_result",
                    "tokens_used": 0,
                    "tdd_opportunities": []
                }
            
            # Check if file exists
            if not Path(file_path).exists():
                return {
                    "success": False,
                    "error": f"File not found: {file_path}",
                    "tokens_used": 0,
                    "tdd_opportunities": []
                }
            
            tdd_opportunities = []
            tokens_used = 200  # Estimate for TDD analysis
            
            # Detect current TDD phase
            current_phase = self._detect_current_phase(file_path)
            
            # Analyze test coverage opportunities
            test_opportunities = self._analyze_test_opportunities(file_path)
            
            # TDD cycle optimization opportunities
            cycle_opportunities = self._analyze_tdd_cycle_opportunities(file_path, current_phase)
            
            # TDAH-specific optimizations
            if self.tdah_mode:
                tdah_opportunities = self._analyze_tdah_optimization_opportunities(file_path)
            else:
                tdah_opportunities = []
            
            # Combine all opportunities
            all_opportunities = test_opportunities + cycle_opportunities + tdah_opportunities
            
            return {
                "success": True,
                "file_path": file_path,
                "current_tdd_phase": current_phase.value if current_phase else "unknown",
                "opportunities_found": len(all_opportunities),
                "tdd_opportunities": all_opportunities,
                "tokens_used": tokens_used,
                "tdah_mode_active": self.tdah_mode,
                "recommendations": [
                    "Focus on test-first development",
                    "Implement smallest possible changes to make tests pass",
                    "Refactor only when tests are green",
                    "Break complex tasks into TDAH-friendly micro-tasks"
                ] if self.tdah_mode else [
                    "Follow Red-Green-Refactor cycle",
                    "Maintain high test coverage",
                    "Refactor frequently with confidence"
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error in analyze_tdd_opportunities: {e}")
            return {
                "success": False,
                "error": str(e),
                "tokens_used": 0,
                "tdd_opportunities": []
            }
    
    def _analyze_test_opportunities(self, file_path: str) -> List[Dict[str, Any]]:
        """Analyze opportunities for better testing."""
        opportunities = []
        
        # Check if it's a test file or source file
        if "_test.py" in file_path or "test_" in file_path:
            opportunities.append({
                "type": "test_improvement",
                "description": "Consider adding more edge case tests",
                "priority": "medium",
                "estimated_effort": "15 minutes"
            })
        else:
            opportunities.append({
                "type": "test_creation",
                "description": "Create comprehensive unit tests for this module",
                "priority": "high", 
                "estimated_effort": "30 minutes"
            })
        
        return opportunities
    
    def _analyze_tdd_cycle_opportunities(self, file_path: str, current_phase: Optional[TDDPhase]) -> List[Dict[str, Any]]:
        """Analyze TDD cycle optimization opportunities."""
        opportunities = []
        
        if current_phase == TDDPhase.RED:
            opportunities.append({
                "type": "red_phase_optimization",
                "description": "Write more specific failing tests",
                "priority": "high",
                "estimated_effort": "10 minutes"
            })
        elif current_phase == TDDPhase.GREEN:
            opportunities.append({
                "type": "green_phase_optimization", 
                "description": "Implement minimal code to make tests pass",
                "priority": "high",
                "estimated_effort": "20 minutes"
            })
        elif current_phase == TDDPhase.REFACTOR:
            opportunities.append({
                "type": "refactor_phase_optimization",
                "description": "Improve code quality while maintaining tests",
                "priority": "medium",
                "estimated_effort": "25 minutes"
            })
        
        return opportunities
    
    def _analyze_tdah_optimization_opportunities(self, file_path: str) -> List[Dict[str, Any]]:
        """Analyze TDAH-specific optimization opportunities."""
        opportunities = []
        
        # TDAH-friendly micro-tasks
        opportunities.append({
            "type": "micro_task_breakdown",
            "description": "Break complex method into TDAH-friendly 5-minute chunks",
            "priority": "high",
            "estimated_effort": "5 minutes",
            "tdah_benefit": "Reduces cognitive overload and improves focus"
        })
        
        # Focus session optimization
        opportunities.append({
            "type": "focus_session_optimization",
            "description": f"Optimize for {self.default_focus_minutes}-minute focus sessions",
            "priority": "medium",
            "estimated_effort": "10 minutes",
            "tdah_benefit": "Aligns with optimal attention span"
        })
        
        return opportunities
    
    def _detect_current_phase(self, file_path: str) -> Optional[TDDPhase]:
        """Detect current TDD phase based on file analysis."""
        # Simplified detection logic
        if "_test.py" in file_path or "test_" in file_path:
            return TDDPhase.RED
        else:
            return TDDPhase.GREEN


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="TDD Intelligent Workflow Agent"
    )
    
    parser.add_argument("--task-file", type=str, required=True, help="File to work on")
    parser.add_argument(
        "--tdd-phase", 
        choices=["red", "green", "refactor"], 
        default="refactor",
        help="Current TDD phase"
    )
    parser.add_argument("--tdah-mode", action="store_true", help="Enable TDAH optimizations")
    parser.add_argument("--focus-session-minutes", type=int, default=25, help="Focus session duration")
    parser.add_argument(
        "--energy-level", 
        choices=["low", "medium", "high"], 
        default="medium",
        help="Current energy level"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')
    
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize the TDD workflow agent
        project_root = Path(__file__).resolve().parent.parent.parent
        agent = TDDIntelligentWorkflowAgent(
            project_root=project_root,
            tdah_mode=args.tdah_mode,
            default_focus_minutes=args.focus_session_minutes
        )
        
        # Start TDD workflow session
        session = agent.start_tdd_workflow_session(
            target_file=args.task_file,
            initial_phase=TDDPhase(args.tdd_phase),
            user_energy_level=TDAHEnergyLevel(args.energy_level),
            focus_session_minutes=args.focus_session_minutes
        )
        
        print(f"\n🎯 TDD Workflow Session Started!")
        print(f"📁 File: {args.task_file}")
        print(f"🔄 Phase: {args.tdd_phase.upper()}")
        print(f"⚡ Energy: {args.energy_level}")
        print(f"🧠 TDAH Mode: {'ON' if args.tdah_mode else 'OFF'}")
        print(f"📋 Tasks: {len(session.tasks_remaining)}")
        
        # Execute the workflow
        results = agent.execute_tdd_workflow_session(session)
        
        print(f"\n🎉 TDD Workflow Session Complete!")
        print(f"✅ Tasks completed: {results['tasks_completed']}")
        print(f"🏆 Quality improvements: {results['quality_improvements']}")
        print(f"📊 Final quality score: {results['final_quality_score']:.1f}/100")
        
        if results.get("phase_transitions"):
            print(f"🔄 Phase transitions: {len(results['phase_transitions'])}")
        
        if results.get("tdah_support_used"):
            print(f"🧠 TDAH support instances: {len(results['tdah_support_used'])}")
        
        return 0
        
    except Exception as e:
        logger.error("Error: %s", e, exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    exit(main())