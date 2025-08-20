# 📊 CLAUDE.md - Data Models Layer

**Module:** models/  
**Purpose:** Enterprise data models with TDD integration + TDAH-optimized data structures  
**TDD Mission:** Data models that support Red-Green-Refactor cycle requirements and test data lifecycle  
**Architecture:** Type-safe data models with business logic validation and TDD workflow integration  
**Models:** 8+ core models with TDD test data support and TDAH accessibility patterns  
**Last Updated:** 2025-08-19

---

## 🎯 **TDD + TDAH INTEGRATION**

### **TDD Data Model Patterns**
- **Test Data Lifecycle**: Models designed to support test data creation, validation, and cleanup
- **Phase-Aware Modeling**: Data models that track TDD phase state and transitions
- **Validation-First Design**: Models with built-in validation that supports test-driven development
- **Refactor-Safe Structures**: Data models designed for safe refactoring and schema evolution

### **TDAH-Optimized Data Structures**
- **Cognitive Load Reduction**: Simple, intuitive data structures that reduce mental overhead
- **Clear Relationships**: Explicit relationship modeling that's easy to understand and navigate
- **Progressive Disclosure**: Models that support gradual revelation of complexity
- **Error Prevention**: Data structures designed to prevent common mistakes and confusion

---

## 🏗️ **Models Architecture for TDD**

### **Model Hierarchy with TDD Integration**
```
streamlit_extension/models/
├── __init__.py                       # 🔧 Model exports and TDD utilities
├── base_models.py                    # 🏗️ Base model classes with TDD support ⭐
├── client_models.py                  # 👤 Client data models + TDD project context
├── project_models.py                 # 📋 Project models + TDD epic organization
├── epic_models.py                    # 🎯 Epic models + TDD workflow tracking ⭐⭐
├── task_models.py                    # ✅ Task models + TDD cycle management ⭐⭐⭐
├── user_models.py                    # 👥 User models + TDAH profile integration ⭐
├── session_models.py                 # ⏱️ Session models + TDAH focus tracking ⭐⭐
└── scoring.py                        # 📈 Scoring models + TDD effectiveness metrics
```

### **TDD-Enhanced Base Model Architecture**
```python
# Base model with TDD lifecycle support
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class TDDPhase(Enum):
    """TDD cycle phases with clear progression."""
    RED = "Red"         # Test creation phase
    GREEN = "Green"     # Implementation phase  
    REFACTOR = "Refactor"  # Optimization phase
    COMPLETE = "Complete"  # Cycle complete

class TDAHEnergyLevel(Enum):
    """TDAH energy levels for session optimization."""
    VERY_LOW = 1
    LOW = 2
    MODERATE = 3
    HIGH = 4
    VERY_HIGH = 5

@dataclass
class BaseTDDModel:
    """Base model with TDD and TDAH support."""
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # TDD Integration
    tdd_phase: Optional[TDDPhase] = None
    tdd_cycle_id: Optional[str] = None
    test_data_context: Optional[Dict[str, Any]] = None
    
    # TDAH Support
    cognitive_complexity: Optional[int] = field(default=1)  # 1-10 scale
    estimated_focus_time: Optional[int] = None  # minutes
    interruption_tolerance: Optional[str] = "medium"  # low/medium/high
    
    def __post_init__(self):
        """Post-initialization for TDD and TDAH setup."""
        if self.created_at is None:
            self.created_at = datetime.now()
        
        if self.tdd_cycle_id is None and self.tdd_phase:
            self.tdd_cycle_id = self._generate_tdd_cycle_id()
    
    def _generate_tdd_cycle_id(self) -> str:
        """Generate unique TDD cycle identifier."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"tdd_{self.__class__.__name__.lower()}_{timestamp}"
    
    def transition_tdd_phase(self, new_phase: TDDPhase) -> bool:
        """Safely transition between TDD phases with validation."""
        if not self._validate_tdd_transition(self.tdd_phase, new_phase):
            return False
        
        self.tdd_phase = new_phase
        self.updated_at = datetime.now()
        return True
    
    def _validate_tdd_transition(self, from_phase: Optional[TDDPhase], to_phase: TDDPhase) -> bool:
        """Validate TDD phase transitions follow proper workflow."""
        if from_phase is None:
            return to_phase == TDDPhase.RED
        
        valid_transitions = {
            TDDPhase.RED: [TDDPhase.GREEN],
            TDDPhase.GREEN: [TDDPhase.REFACTOR, TDDPhase.COMPLETE],
            TDDPhase.REFACTOR: [TDDPhase.COMPLETE, TDDPhase.GREEN],  # Can go back to Green
            TDDPhase.COMPLETE: []  # Terminal state
        }
        
        return to_phase in valid_transitions.get(from_phase, [])
    
    def calculate_tdah_suitability(self, user_energy: TDAHEnergyLevel) -> float:
        """Calculate how suitable this task is for current TDAH energy level."""
        energy_requirements = {
            1: TDAHEnergyLevel.VERY_LOW,
            2: TDAHEnergyLevel.LOW,
            3: TDAHEnergyLevel.MODERATE,
            4: TDAHEnergyLevel.HIGH,
            5: TDAHEnergyLevel.VERY_HIGH
        }
        
        required_energy = energy_requirements.get(self.cognitive_complexity, TDAHEnergyLevel.MODERATE)
        
        # Calculate suitability score (0.0 to 1.0)
        if user_energy.value >= required_energy.value:
            return 1.0 - (required_energy.value - user_energy.value) * 0.1
        else:
            return max(0.1, user_energy.value / required_energy.value)
```

---

## 🎯 **Core Models with TDD Integration**

### **TaskModel (task_models.py) - TDD Cycle Management ⭐⭐⭐**
- **Purpose**: Complete task management with full TDD cycle support and TDAH optimization
- **TDD Features**: Phase tracking, test requirement management, implementation validation
- **Key Attributes**:
  - `tdd_phase` - Current TDD phase (Red/Green/Refactor/Complete)
  - `test_requirements` - Acceptance criteria and test specifications
  - `implementation_status` - Implementation progress tracking
  - `refactor_improvements` - Optimization and quality improvements
- **TDAH Features**: Cognitive complexity scoring, focus time estimation, interruption recovery
- **Dependencies**: EpicModel, UserModel, SessionModel

```python
@dataclass
class TaskModel(BaseTDDModel):
    """Complete task model with TDD cycle management."""
    
    # Basic Task Information
    title: str = ""
    description: str = ""
    epic_id: Optional[int] = None
    
    # TDD Cycle Management
    tdd_phase: TDDPhase = TDDPhase.RED
    test_requirements: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)
    implementation_notes: str = ""
    refactor_improvements: List[str] = field(default_factory=list)
    
    # TDD Phase Status
    red_phase_complete: bool = False
    green_phase_complete: bool = False
    refactor_phase_complete: bool = False
    
    # TDD Timing and Metrics
    red_phase_duration: Optional[int] = None  # minutes
    green_phase_duration: Optional[int] = None
    refactor_phase_duration: Optional[int] = None
    total_cycle_duration: Optional[int] = None
    
    # Test Integration
    test_file_path: Optional[str] = None
    test_coverage_percentage: Optional[float] = None
    test_passing_count: int = 0
    test_failing_count: int = 0
    
    # TDAH Optimization
    estimated_complexity: int = 1  # 1-10 scale
    actual_complexity: Optional[int] = None
    interruption_count: int = 0
    focus_sessions_used: int = 0
    energy_level_required: TDAHEnergyLevel = TDAHEnergyLevel.MODERATE
    
    # Progress Tracking
    progress_percentage: float = 0.0
    status: str = "todo"  # todo, in_progress, blocked, completed
    priority: str = "medium"  # low, medium, high, urgent
    
    def start_red_phase(self, requirements: List[str], criteria: List[str]) -> bool:
        """Start Red phase with test requirements and acceptance criteria."""
        if self.tdd_phase != TDDPhase.RED:
            return False
        
        self.test_requirements = requirements
        self.acceptance_criteria = criteria
        self.status = "in_progress"
        self.red_phase_start_time = datetime.now()
        
        return True
    
    def complete_red_phase(self) -> bool:
        """Complete Red phase with validation."""
        if not self._validate_red_phase_completion():
            return False
        
        self.red_phase_complete = True
        self.red_phase_duration = self._calculate_phase_duration("red")
        
        return self.transition_tdd_phase(TDDPhase.GREEN)
    
    def _validate_red_phase_completion(self) -> bool:
        """Validate Red phase completion requirements."""
        return (
            len(self.test_requirements) > 0 and
            len(self.acceptance_criteria) > 0 and
            self.test_failing_count > 0  # Must have failing tests
        )
    
    def complete_green_phase(self) -> bool:
        """Complete Green phase with validation."""
        if not self._validate_green_phase_completion():
            return False
        
        self.green_phase_complete = True
        self.green_phase_duration = self._calculate_phase_duration("green")
        
        return self.transition_tdd_phase(TDDPhase.REFACTOR)
    
    def _validate_green_phase_completion(self) -> bool:
        """Validate Green phase completion requirements."""
        return (
            self.test_passing_count > 0 and
            self.test_failing_count == 0 and  # All tests must pass
            len(self.implementation_notes) > 0
        )
    
    def complete_refactor_phase(self) -> bool:
        """Complete Refactor phase with validation."""
        if not self._validate_refactor_phase_completion():
            return False
        
        self.refactor_phase_complete = True
        self.refactor_phase_duration = self._calculate_phase_duration("refactor")
        self.total_cycle_duration = self._calculate_total_cycle_duration()
        
        return self.transition_tdd_phase(TDDPhase.COMPLETE)
    
    def _validate_refactor_phase_completion(self) -> bool:
        """Validate Refactor phase completion requirements."""
        return (
            len(self.refactor_improvements) > 0 and
            self.test_passing_count > 0 and  # Tests still pass after refactor
            self.test_coverage_percentage and self.test_coverage_percentage >= 80.0
        )
    
    def add_interruption(self, interruption_type: str, recovery_time: int) -> None:
        """Track TDAH interruption for analytics."""
        self.interruption_count += 1
        self.interruption_log.append({
            'type': interruption_type,
            'timestamp': datetime.now(),
            'recovery_time': recovery_time
        })
    
    def calculate_tdd_effectiveness(self) -> Dict[str, float]:
        """Calculate TDD cycle effectiveness metrics."""
        if not self.total_cycle_duration:
            return {'effectiveness': 0.0}
        
        # Time balance between phases (ideal: 30% Red, 50% Green, 20% Refactor)
        red_percentage = (self.red_phase_duration or 0) / self.total_cycle_duration * 100
        green_percentage = (self.green_phase_duration or 0) / self.total_cycle_duration * 100
        refactor_percentage = (self.refactor_phase_duration or 0) / self.total_cycle_duration * 100
        
        # Calculate balance score (how close to ideal distribution)
        ideal_balance = {'red': 30, 'green': 50, 'refactor': 20}
        actual_balance = {'red': red_percentage, 'green': green_percentage, 'refactor': refactor_percentage}
        
        balance_score = 100 - sum(abs(ideal_balance[phase] - actual_balance[phase]) for phase in ideal_balance) / 3
        
        # Test quality score
        test_quality = (self.test_coverage_percentage or 0) + (self.test_passing_count * 10)
        test_quality = min(test_quality, 100)
        
        # Overall effectiveness
        effectiveness = (balance_score * 0.4 + test_quality * 0.4 + self._calculate_completion_score() * 0.2)
        
        return {
            'effectiveness': effectiveness,
            'balance_score': balance_score,
            'test_quality': test_quality,
            'phase_distribution': actual_balance
        }
    
    def get_tdah_recommendations(self) -> List[str]:
        """Get TDAH-specific recommendations for this task."""
        recommendations = []
        
        if self.cognitive_complexity > 7:
            recommendations.append("🧠 High complexity task - consider breaking into smaller pieces")
        
        if self.interruption_count > 3:
            recommendations.append("🔄 Multiple interruptions detected - try enabling focus mode")
        
        if self.estimated_focus_time and self.estimated_focus_time > 45:
            recommendations.append("⏰ Long task - schedule during high-energy periods")
        
        if self.energy_level_required == TDAHEnergyLevel.VERY_HIGH:
            recommendations.append("⚡ High energy required - best tackled when well-rested")
        
        return recommendations
```

### **EpicModel (epic_models.py) - TDD Workflow Tracking ⭐⭐**
- **Purpose**: Epic management with TDD workflow orchestration and gamification
- **TDD Features**: Epic-level TDD progress tracking, task cycle aggregation
- **Key Attributes**:
  - `tdd_completion_rate` - Percentage of tasks with complete TDD cycles
  - `total_tdd_cycles` - Number of completed TDD cycles in epic
  - `average_cycle_effectiveness` - Average effectiveness across all task cycles
- **TDAH Features**: Epic breakdown for cognitive manageability, progress visualization
- **Dependencies**: ProjectModel, TaskModel, TDD workflow engine

```python
@dataclass
class EpicModel(BaseTDDModel):
    """Epic model with TDD workflow tracking and TDAH optimization."""
    
    # Basic Epic Information
    title: str = ""
    description: str = ""
    project_id: Optional[int] = None
    
    # TDD Epic Management
    total_tasks: int = 0
    completed_tasks: int = 0
    tasks_in_red_phase: int = 0
    tasks_in_green_phase: int = 0
    tasks_in_refactor_phase: int = 0
    tasks_completed_cycles: int = 0
    
    # TDD Effectiveness Metrics
    epic_tdd_completion_rate: float = 0.0
    average_cycle_effectiveness: float = 0.0
    total_tdd_cycles_completed: int = 0
    epic_test_coverage: float = 0.0
    
    # Epic Progress and Goals
    progress_percentage: float = 0.0
    definition_of_done: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)
    
    # TDAH Epic Management
    estimated_total_focus_time: Optional[int] = None  # minutes
    actual_total_focus_time: Optional[int] = None
    epic_complexity_score: int = 1  # 1-10 scale
    breakdown_strategy: str = "sequential"  # sequential, parallel, flexible
    
    # Gamification Elements
    points_earned: int = 0
    achievements_unlocked: List[str] = field(default_factory=list)
    milestone_rewards: List[str] = field(default_factory=list)
    
    def calculate_tdd_progress(self) -> Dict[str, Any]:
        """Calculate comprehensive TDD progress for epic."""
        if self.total_tasks == 0:
            return {'overall_progress': 0.0, 'phase_distribution': {}}
        
        # Phase distribution
        phase_distribution = {
            'red': (self.tasks_in_red_phase / self.total_tasks) * 100,
            'green': (self.tasks_in_green_phase / self.total_tasks) * 100,
            'refactor': (self.tasks_in_refactor_phase / self.total_tasks) * 100,
            'complete': (self.tasks_completed_cycles / self.total_tasks) * 100
        }
        
        # Overall TDD progress
        tdd_progress = (self.tasks_completed_cycles / self.total_tasks) * 100
        
        # Epic effectiveness score
        effectiveness_score = self._calculate_epic_effectiveness()
        
        return {
            'overall_progress': tdd_progress,
            'phase_distribution': phase_distribution,
            'effectiveness_score': effectiveness_score,
            'completion_rate': self.epic_tdd_completion_rate,
            'test_coverage': self.epic_test_coverage
        }
    
    def add_task_tdd_completion(self, task_effectiveness: float) -> None:
        """Record completion of a TDD cycle for analytics."""
        self.tasks_completed_cycles += 1
        self.total_tdd_cycles_completed += 1
        
        # Update average effectiveness
        if self.total_tdd_cycles_completed == 1:
            self.average_cycle_effectiveness = task_effectiveness
        else:
            current_total = self.average_cycle_effectiveness * (self.total_tdd_cycles_completed - 1)
            self.average_cycle_effectiveness = (current_total + task_effectiveness) / self.total_tdd_cycles_completed
        
        # Update completion rate
        self.epic_tdd_completion_rate = (self.tasks_completed_cycles / max(self.total_tasks, 1)) * 100
        
        # Check for achievements
        self._check_tdd_achievements()
    
    def _check_tdd_achievements(self) -> None:
        """Check and unlock TDD-related achievements."""
        # TDD Mastery Achievement
        if self.epic_tdd_completion_rate >= 100 and "TDD_EPIC_MASTER" not in self.achievements_unlocked:
            self.achievements_unlocked.append("TDD_EPIC_MASTER")
            self.points_earned += 100
        
        # High Effectiveness Achievement
        if self.average_cycle_effectiveness >= 90 and "HIGH_EFFECTIVENESS" not in self.achievements_unlocked:
            self.achievements_unlocked.append("HIGH_EFFECTIVENESS")
            self.points_earned += 50
        
        # Consistency Achievement
        if self.total_tdd_cycles_completed >= 10 and "CONSISTENT_TDD" not in self.achievements_unlocked:
            self.achievements_unlocked.append("CONSISTENT_TDD")
            self.points_earned += 75
    
    def get_tdah_breakdown_strategy(self) -> Dict[str, Any]:
        """Get TDAH-optimized breakdown strategy for epic."""
        if self.epic_complexity_score <= 3:
            return {
                'strategy': 'simple_linear',
                'recommended_session_length': 25,
                'break_frequency': 'standard',
                'parallelization': False
            }
        elif self.epic_complexity_score <= 6:
            return {
                'strategy': 'structured_chunks',
                'recommended_session_length': 20,
                'break_frequency': 'frequent',
                'parallelization': True,
                'chunk_size': 3
            }
        else:
            return {
                'strategy': 'micro_tasks',
                'recommended_session_length': 15,
                'break_frequency': 'very_frequent',
                'parallelization': True,
                'chunk_size': 2,
                'additional_support': ['visual_progress', 'external_accountability']
            }
```

### **SessionModel (session_models.py) - TDAH Focus Tracking ⭐⭐**
- **Purpose**: Focus session management with TDAH optimization and TDD integration
- **TDD Features**: TDD phase-specific session types, cycle timing tracking
- **Key Attributes**:
  - `session_type` - Type of session (red_phase, green_phase, refactor_phase, general)
  - `tdd_context` - Associated TDD cycle and phase information
  - `effectiveness_score` - Session effectiveness for TDD productivity
- **TDAH Features**: Interruption tracking, energy monitoring, focus pattern analysis
- **Dependencies**: TaskModel, UserModel, TDD workflow tracking

```python
@dataclass
class SessionModel(BaseTDDModel):
    """Focus session model with TDAH optimization and TDD integration."""
    
    # Session Basic Information
    user_id: int = 0
    task_id: Optional[int] = None
    session_name: str = ""
    
    # Session Timing
    planned_duration: int = 25  # minutes
    actual_duration: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    # TDD Integration
    session_type: str = "general"  # red_phase, green_phase, refactor_phase, general
    tdd_phase_context: Optional[TDDPhase] = None
    tdd_cycle_id: Optional[str] = None
    tdd_productivity_score: Optional[float] = None
    
    # TDAH Focus Tracking
    energy_level_start: TDAHEnergyLevel = TDAHEnergyLevel.MODERATE
    energy_level_end: Optional[TDAHEnergyLevel] = None
    focus_rating: Optional[int] = None  # 1-10 scale
    interruption_count: int = 0
    interruption_details: List[Dict[str, Any]] = field(default_factory=list)
    
    # Session Effectiveness
    goals_achieved: int = 0
    goals_planned: int = 1
    effectiveness_score: Optional[float] = None
    satisfaction_rating: Optional[int] = None  # 1-10 scale
    
    # Recovery and Adaptation
    break_time_needed: Optional[int] = None  # minutes
    next_session_recommendations: List[str] = field(default_factory=list)
    session_notes: str = ""
    
    def start_session(self, energy_level: TDAHEnergyLevel, planned_goals: int = 1) -> bool:
        """Start focus session with TDAH and TDD context."""
        self.start_time = datetime.now()
        self.energy_level_start = energy_level
        self.goals_planned = planned_goals
        self.status = "active"
        
        # Adapt session duration based on energy and TDD phase
        self.planned_duration = self._calculate_optimal_duration(energy_level)
        
        return True
    
    def _calculate_optimal_duration(self, energy_level: TDAHEnergyLevel) -> int:
        """Calculate optimal session duration based on energy and TDD phase."""
        base_duration = {
            TDAHEnergyLevel.VERY_LOW: 10,
            TDAHEnergyLevel.LOW: 15,
            TDAHEnergyLevel.MODERATE: 25,
            TDAHEnergyLevel.HIGH: 35,
            TDAHEnergyLevel.VERY_HIGH: 45
        }
        
        duration = base_duration.get(energy_level, 25)
        
        # Adjust for TDD phase requirements
        if self.tdd_phase_context == TDDPhase.RED:
            # Red phase requires deep thinking - prefer longer sessions if energy allows
            duration = min(duration + 10, 50)
        elif self.tdd_phase_context == TDDPhase.GREEN:
            # Green phase can handle interruptions - standard duration
            pass
        elif self.tdd_phase_context == TDDPhase.REFACTOR:
            # Refactor requires sustained attention - slightly longer
            duration = min(duration + 5, 40)
        
        return duration
    
    def record_interruption(self, interruption_type: str, duration: int, recovery_time: int) -> None:
        """Record interruption with TDAH-specific tracking."""
        self.interruption_count += 1
        self.interruption_details.append({
            'type': interruption_type,
            'timestamp': datetime.now(),
            'duration': duration,
            'recovery_time': recovery_time,
            'energy_impact': self._estimate_energy_impact(interruption_type, duration)
        })
    
    def _estimate_energy_impact(self, interruption_type: str, duration: int) -> str:
        """Estimate energy impact of interruption for TDAH users."""
        high_impact_types = ['context_switch', 'urgent_task', 'phone_call']
        medium_impact_types = ['quick_question', 'notification', 'bathroom_break']
        
        if interruption_type in high_impact_types or duration > 10:
            return 'high'
        elif interruption_type in medium_impact_types or duration > 3:
            return 'medium'
        else:
            return 'low'
    
    def complete_session(self, energy_level: TDAHEnergyLevel, focus_rating: int, goals_achieved: int) -> Dict[str, Any]:
        """Complete session with TDAH and TDD effectiveness calculation."""
        self.end_time = datetime.now()
        self.actual_duration = int((self.end_time - self.start_time).total_seconds() / 60)
        self.energy_level_end = energy_level
        self.focus_rating = focus_rating
        self.goals_achieved = goals_achieved
        
        # Calculate session effectiveness
        self.effectiveness_score = self._calculate_session_effectiveness()
        
        # Calculate TDD productivity if applicable
        if self.tdd_phase_context:
            self.tdd_productivity_score = self._calculate_tdd_productivity()
        
        # Generate recommendations for next session
        self.next_session_recommendations = self._generate_session_recommendations()
        
        return {
            'effectiveness_score': self.effectiveness_score,
            'tdd_productivity': self.tdd_productivity_score,
            'energy_change': self.energy_level_end.value - self.energy_level_start.value,
            'recommendations': self.next_session_recommendations
        }
    
    def _calculate_session_effectiveness(self) -> float:
        """Calculate overall session effectiveness score."""
        # Goal achievement score (0-40 points)
        goal_score = (self.goals_achieved / max(self.goals_planned, 1)) * 40
        
        # Focus quality score (0-30 points)
        focus_score = (self.focus_rating / 10) * 30 if self.focus_rating else 0
        
        # Duration efficiency score (0-20 points) 
        duration_efficiency = min((self.actual_duration / self.planned_duration), 1.2) * 20
        
        # Interruption penalty (0-10 points deducted)
        interruption_penalty = min(self.interruption_count * 2, 10)
        
        effectiveness = goal_score + focus_score + duration_efficiency - interruption_penalty
        return max(min(effectiveness, 100), 0)
    
    def _calculate_tdd_productivity(self) -> float:
        """Calculate TDD-specific productivity score."""
        if not self.tdd_phase_context:
            return 0.0
        
        base_score = self.effectiveness_score or 0
        
        # Phase-specific bonuses
        phase_bonuses = {
            TDDPhase.RED: 10 if self.focus_rating and self.focus_rating >= 7 else 0,  # Red phase benefits from high focus
            TDDPhase.GREEN: 10 if self.interruption_count <= 2 else 0,  # Green phase tolerates some interruptions
            TDDPhase.REFACTOR: 10 if self.actual_duration >= self.planned_duration * 0.8 else 0  # Refactor needs time
        }
        
        bonus = phase_bonuses.get(self.tdd_phase_context, 0)
        return min(base_score + bonus, 100)
    
    def _generate_session_recommendations(self) -> List[str]:
        """Generate personalized recommendations for next session."""
        recommendations = []
        
        # Energy-based recommendations
        energy_change = self.energy_level_end.value - self.energy_level_start.value
        if energy_change <= -2:
            recommendations.append("🔋 Energy depleted - take a longer break before next session")
        elif energy_change <= -1:
            recommendations.append("⚡ Take a short energizing break")
        
        # Focus-based recommendations
        if self.focus_rating and self.focus_rating <= 4:
            recommendations.append("🧠 Low focus detected - try shorter sessions or environment changes")
        elif self.focus_rating and self.focus_rating >= 8:
            recommendations.append("🚀 Great focus! Consider slightly longer sessions")
        
        # Interruption-based recommendations
        if self.interruption_count >= 5:
            recommendations.append("🔕 High interruptions - enable focus mode or change environment")
        elif self.interruption_count >= 3:
            recommendations.append("📱 Moderate interruptions - consider silencing notifications")
        
        # TDD-specific recommendations
        if self.tdd_productivity_score and self.tdd_productivity_score < 60:
            recommendations.append(f"📝 TDD productivity low - consider adjusting {self.tdd_phase_context.value} phase approach")
        
        return recommendations
```

### **UserModel (user_models.py) - TDAH Profile Integration ⭐**
- **Purpose**: User management with TDAH profile and TDD preference integration
- **TDD Features**: TDD skill tracking, preferred TDD patterns, effectiveness history
- **Key Attributes**:
  - `tdd_experience_level` - User's TDD skill level (beginner/intermediate/advanced)
  - `preferred_tdd_cycle_length` - Optimal TDD cycle duration for this user
  - `tdd_effectiveness_history` - Historical TDD performance data
- **TDAH Features**: Comprehensive TDAH profile, focus patterns, energy tracking
- **Dependencies**: SessionModel, TaskModel, TDAH productivity analytics

```python
@dataclass
class UserModel(BaseTDDModel):
    """User model with TDAH profile and TDD integration."""
    
    # Basic User Information
    username: str = ""
    email: str = ""
    full_name: str = ""
    
    # TDAH Profile
    has_tdah_diagnosis: bool = False
    tdah_traits: List[str] = field(default_factory=list)  # hyperactivity, inattention, impulsivity
    preferred_work_style: str = "flexible"  # structured, flexible, mixed
    optimal_focus_duration: int = 25  # minutes
    energy_pattern_type: str = "variable"  # morning, afternoon, evening, variable
    
    # Focus and Energy Patterns
    peak_energy_hours: List[int] = field(default_factory=list)  # Hours 0-23
    focus_sustainability: int = 5  # 1-10 scale
    interruption_sensitivity: str = "medium"  # low, medium, high
    hyperfocus_tendency: bool = False
    
    # TDD Integration
    tdd_experience_level: str = "beginner"  # beginner, intermediate, advanced, expert
    preferred_tdd_cycle_length: int = 60  # minutes for complete Red-Green-Refactor cycle
    tdd_tools_proficiency: List[str] = field(default_factory=list)
    tdd_effectiveness_average: float = 0.0
    
    # Productivity Metrics
    total_focus_sessions: int = 0
    successful_sessions_count: int = 0
    total_tdd_cycles_completed: int = 0
    average_session_effectiveness: float = 0.0
    
    # Preferences and Adaptations
    notification_preferences: Dict[str, bool] = field(default_factory=dict)
    accessibility_needs: List[str] = field(default_factory=list)
    productivity_goals: List[str] = field(default_factory=list)
    
    def calculate_optimal_session_config(self, current_energy: TDAHEnergyLevel, task_complexity: int) -> Dict[str, Any]:
        """Calculate optimal session configuration based on TDAH profile."""
        base_duration = self.optimal_focus_duration
        
        # Adjust for current energy
        energy_modifiers = {
            TDAHEnergyLevel.VERY_LOW: 0.5,
            TDAHEnergyLevel.LOW: 0.7,
            TDAHEnergyLevel.MODERATE: 1.0,
            TDAHEnergyLevel.HIGH: 1.3,
            TDAHEnergyLevel.VERY_HIGH: 1.5
        }
        
        duration = int(base_duration * energy_modifiers.get(current_energy, 1.0))
        
        # Adjust for task complexity
        if task_complexity >= 8:
            duration = int(duration * 0.8)  # Shorter sessions for complex tasks
        elif task_complexity <= 3:
            duration = int(duration * 1.2)  # Longer sessions for simple tasks
        
        # Apply TDAH-specific adjustments
        if self.hyperfocus_tendency and current_energy.value >= 4:
            duration = min(duration * 2, 90)  # Allow longer sessions but cap at 90 minutes
        
        if self.interruption_sensitivity == "high":
            duration = min(duration, 20)  # Shorter sessions for high sensitivity
        
        return {
            'optimal_duration': duration,
            'break_duration': max(5, duration // 5),
            'interruption_tolerance': self.interruption_sensitivity,
            'energy_monitoring': True,
            'focus_reminders': duration >= 30
        }
    
    def update_tdd_effectiveness(self, cycle_effectiveness: float) -> None:
        """Update TDD effectiveness metrics."""
        self.total_tdd_cycles_completed += 1
        
        if self.total_tdd_cycles_completed == 1:
            self.tdd_effectiveness_average = cycle_effectiveness
        else:
            current_total = self.tdd_effectiveness_average * (self.total_tdd_cycles_completed - 1)
            self.tdd_effectiveness_average = (current_total + cycle_effectiveness) / self.total_tdd_cycles_completed
    
    def get_tdah_recommendations(self) -> List[str]:
        """Get personalized TDAH productivity recommendations."""
        recommendations = []
        
        # Focus sustainability recommendations
        if self.focus_sustainability <= 3:
            recommendations.append("🧠 Consider micro-sessions (10-15 minutes) with frequent breaks")
        elif self.focus_sustainability <= 6:
            recommendations.append("⏰ Standard Pomodoro (25 minutes) works well for you")
        else:
            recommendations.append("🚀 You can handle longer focus sessions (35-45 minutes)")
        
        # Energy pattern recommendations
        if self.peak_energy_hours:
            peak_times = ", ".join([f"{h}:00" for h in self.peak_energy_hours[:3]])
            recommendations.append(f"⚡ Schedule complex tasks during peak hours: {peak_times}")
        
        # TDD skill development
        if self.tdd_experience_level == "beginner":
            recommendations.append("📚 Focus on mastering Red-Green-Refactor basics")
        elif self.tdd_experience_level == "intermediate":
            recommendations.append("🎯 Practice advanced TDD patterns and refactoring techniques")
        
        # Hyperfocus management
        if self.hyperfocus_tendency:
            recommendations.append("⏰ Set timers to prevent hyperfocus burnout")
            recommendations.append("🔔 Enable break reminders every 45-60 minutes")
        
        return recommendations
```

---

## 📊 **Supporting Models**

### **ScoringModel (scoring.py) - TDD Effectiveness Metrics**
- **Purpose**: Comprehensive scoring system for TDD effectiveness and TDAH productivity
- **TDD Features**: Cycle effectiveness calculation, phase balance scoring, improvement tracking
- **Key Methods**:
  - `calculate_tdd_cycle_score()` - Score individual TDD cycles
  - `calculate_epic_effectiveness()` - Epic-level TDD performance
  - `track_improvement_trends()` - Progress tracking over time
- **TDAH Features**: Productivity scoring, energy efficiency metrics, focus effectiveness
- **Dependencies**: TaskModel, EpicModel, SessionModel, analytics integration

### **ClientModel & ProjectModel - TDD Context**
- **Purpose**: Client and project management with TDD project context
- **TDD Features**: Project-level TDD adoption tracking, client TDD preferences
- **Key Attributes**:
  - `tdd_adoption_level` - How extensively TDD is used in project
  - `tdd_training_completed` - Team TDD training status
  - `preferred_tdd_tools` - Project-specific TDD toolchain
- **TDAH Features**: Project complexity assessment, team TDAH accommodations
- **Dependencies**: EpicModel, TeamModel, TDD workflow tracking

---

## 📊 **Anti-Patterns to Avoid**

### **🔴 TDD Model Anti-Patterns**
```python
# ❌ TDD-ignorant model design
class BadTaskModel:
    def __init__(self):
        self.title = ""
        self.description = ""
        self.status = "todo"
        # No TDD phase awareness!
        # No test integration!
        # No cycle tracking!
    
    def complete_task(self):
        self.status = "done"
        # No validation of TDD cycle completion!
        # No effectiveness tracking!

# ✅ TDD-integrated model design
class GoodTaskModel(BaseTDDModel):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.description = ""
        self.tdd_phase = TDDPhase.RED
        self.test_requirements = []
        self.acceptance_criteria = []
    
    def complete_tdd_cycle(self):
        if not self._validate_cycle_completion():
            raise TDDValidationError("Cannot complete cycle: validation failed")
        
        self.tdd_phase = TDDPhase.COMPLETE
        self.effectiveness_score = self._calculate_effectiveness()
        return self.effectiveness_score
```

### **🔴 TDAH Model Anti-Patterns**
```python
# ❌ TDAH-hostile model design
class BadUserModel:
    def __init__(self):
        self.username = ""
        # No TDAH profile information!
        # No focus pattern tracking!
        # No energy level awareness!
    
    def schedule_task(self, task):
        # Ignores user's energy patterns and focus capabilities
        return "scheduled"

# ✅ TDAH-optimized model design
class GoodUserModel:
    def __init__(self):
        self.username = ""
        self.tdah_profile = TDAHProfile()
        self.energy_patterns = EnergyPatternTracker()
        self.focus_capabilities = FocusCapabilityProfile()
    
    def schedule_task(self, task):
        optimal_time = self.energy_patterns.get_optimal_time_for_task(task)
        session_config = self.calculate_optimal_session_config(task.complexity)
        
        return TaskSchedule(
            optimal_time=optimal_time,
            session_config=session_config,
            tdah_accommodations=self._get_task_accommodations(task)
        )
```

---

## 🔧 **Model Integration Patterns**

### **TDD Workflow Model Integration**
```python
# Complete TDD workflow using integrated models
class TDDWorkflowOrchestrator:
    def execute_task_tdd_cycle(self, task_id: int, user_id: int) -> TDDCycleResult:
        # Get models with full context
        task = TaskModel.get_with_tdd_context(task_id)
        user = UserModel.get_with_tdah_profile(user_id)
        
        # Start Red phase with user-optimized session
        session_config = user.calculate_optimal_session_config(
            user.get_current_energy_level(),
            task.estimated_complexity
        )
        
        red_session = SessionModel(
            user_id=user_id,
            task_id=task_id,
            session_type="red_phase",
            tdd_phase_context=TDDPhase.RED,
            planned_duration=session_config['optimal_duration']
        )
        
        # Execute Red phase
        red_result = self._execute_red_phase(task, red_session)
        if not red_result.success:
            return TDDCycleResult.phase_failure('Red', red_result.error)
        
        # Continue with Green and Refactor phases...
        green_result = self._execute_green_phase(task, user)
        refactor_result = self._execute_refactor_phase(task, user)
        
        # Update epic progress
        epic = EpicModel.get_by_id(task.epic_id)
        epic.add_task_tdd_completion(task.calculate_tdd_effectiveness()['effectiveness'])
        
        # Update user metrics
        user.update_tdd_effectiveness(task.calculate_tdd_effectiveness()['effectiveness'])
        
        return TDDCycleResult.success(
            task=task,
            epic_progress=epic.calculate_tdd_progress(),
            user_improvement=user.get_improvement_metrics()
        )
```

### **TDAH-Optimized Session Management**
```python
# TDAH-optimized session with full model integration
class TDAHSessionManager:
    def start_optimized_session(self, user_id: int, task_id: int) -> SessionModel:
        user = UserModel.get_with_tdah_profile(user_id)
        task = TaskModel.get_with_tdd_context(task_id)
        
        # Calculate optimal session parameters
        current_energy = user.get_current_energy_level()
        session_config = user.calculate_optimal_session_config(
            current_energy, 
            task.estimated_complexity
        )
        
        # Create TDAH-optimized session
        session = SessionModel(
            user_id=user_id,
            task_id=task_id,
            session_type=f"{task.tdd_phase.value.lower()}_phase",
            tdd_phase_context=task.tdd_phase,
            planned_duration=session_config['optimal_duration'],
            energy_level_start=current_energy
        )
        
        # Start session with TDAH accommodations
        session.start_session(current_energy, task.get_session_goals())
        
        return session
    
    def handle_session_interruption(self, session_id: int, interruption_type: str) -> InterruptionResponse:
        session = SessionModel.get_by_id(session_id)
        user = UserModel.get_by_id(session.user_id)
        
        # Record interruption with TDAH context
        recovery_time = user.calculate_interruption_recovery_time(interruption_type)
        session.record_interruption(interruption_type, 0, recovery_time)
        
        # Generate TDAH-friendly response
        return InterruptionResponse(
            message="💾 Context saved! Take the time you need.",
            recovery_suggestions=user.get_interruption_recovery_suggestions(),
            optimal_return_time=datetime.now() + timedelta(minutes=recovery_time)
        )
```

---

## 🔧 **File Tracking - Models Module**

### **Modified Files Checklist**
```
📊 **MODELS MODULE - ARQUIVOS MODIFICADOS:**

**Core Models:**
- models/base_models.py:linha_X - [BaseTDDModel with TDD lifecycle and TDAH support]
- models/task_models.py:linha_Y - [Complete TDD cycle management with TDAH optimization]
- models/epic_models.py:linha_Z - [TDD workflow tracking and gamification]

**User & Session Models:**
- models/user_models.py:linha_W - [TDAH profile integration with TDD preferences]
- models/session_models.py:linha_V - [TDAH focus tracking with TDD productivity]

**Supporting Models:**
- models/client_models.py:linha_U - [Client management with TDD project context]
- models/project_models.py:linha_T - [Project models with TDD adoption tracking]
- models/scoring.py:linha_S - [TDD effectiveness and TDAH productivity metrics]

**Status:** Ready for manual review
**TDD Integration:** Complete Red-Green-Refactor cycle support in data models
**TDAH Support:** Comprehensive TDAH profile and session optimization
**Data Integrity:** Type-safe models with validation and business logic
**Architecture:** Clean model design with proper separation of concerns
**Impact:** [Impact on TDD workflows, TDAH productivity, and data management]
```

### **Model Validation Required**
- [ ] TDD phase transitions work correctly and enforce proper workflow
- [ ] TDAH profile calculations provide meaningful session optimization
- [ ] Model relationships properly enforce data integrity
- [ ] Validation logic prevents invalid state transitions
- [ ] Scoring algorithms provide accurate effectiveness metrics
- [ ] Type hints are comprehensive and accurate
- [ ] Model serialization/deserialization works properly
- [ ] Performance is optimized for frequent model operations

---

## 🚀 **Model Usage Examples**

### **Complete TDD Task Lifecycle**
```python
# Create task in Red phase
task = TaskModel(
    title="Implement user authentication",
    description="Add OAuth 2.0 authentication system",
    epic_id=1,
    tdd_phase=TDDPhase.RED,
    estimated_complexity=7
)

# Start Red phase with requirements
task.start_red_phase(
    requirements=[
        "User can authenticate with Google OAuth",
        "Invalid tokens are rejected",
        "Session persistence works correctly"
    ],
    criteria=[
        "All authentication tests pass",
        "Security validation passes",
        "Performance meets requirements"
    ]
)

# Complete Red phase
task.test_failing_count = 3  # Failing tests written
task.complete_red_phase()  # Transitions to Green

# Complete Green phase
task.test_passing_count = 3
task.test_failing_count = 0
task.implementation_notes = "OAuth integration complete with security validation"
task.complete_green_phase()  # Transitions to Refactor

# Complete Refactor phase
task.refactor_improvements = [
    "Improved error handling",
    "Added comprehensive logging",
    "Optimized token validation"
]
task.test_coverage_percentage = 95.0
task.complete_refactor_phase()  # Transitions to Complete

# Get effectiveness metrics
effectiveness = task.calculate_tdd_effectiveness()
print(f"TDD Effectiveness: {effectiveness['effectiveness']:.1f}%")
```

### **TDAH-Optimized User Session**
```python
# Create user with TDAH profile
user = UserModel(
    username="developer1",
    has_tdah_diagnosis=True,
    tdah_traits=["inattention", "hyperfocus"],
    optimal_focus_duration=20,
    peak_energy_hours=[9, 10, 14, 15],
    tdd_experience_level="intermediate"
)

# Calculate optimal session for current state
current_energy = TDAHEnergyLevel.HIGH
task_complexity = 6

session_config = user.calculate_optimal_session_config(current_energy, task_complexity)
print(f"Optimal duration: {session_config['optimal_duration']} minutes")

# Create and start optimized session
session = SessionModel(
    user_id=user.id,
    task_id=task.id,
    session_type="green_phase",
    tdd_phase_context=TDDPhase.GREEN,
    planned_duration=session_config['optimal_duration']
)

session.start_session(current_energy, planned_goals=2)

# Handle interruption gracefully
session.record_interruption("quick_question", 3, 2)

# Complete session with metrics
completion_result = session.complete_session(
    energy_level=TDAHEnergyLevel.MODERATE,
    focus_rating=8,
    goals_achieved=2
)

print(f"Session effectiveness: {completion_result['effectiveness_score']:.1f}%")
print(f"Recommendations: {completion_result['recommendations']}")
```

---

*Enterprise data models with complete TDD workflow integration and TDAH accessibility optimization*

### **📋 TRACKING PROTOCOL - MODELS MODULE**

**🎯 TRACKING OBRIGATÓRIO PÓS-OPERAÇÃO:**

```
📊 **MODELS MODULE - ARQUIVOS MODIFICADOS:**

**Arquivos Criados:**
- streamlit_extension/models/CLAUDE.md - [Context-aware data models documentation com TDD cycle management e TDAH optimization patterns, 1,600+ linhas]

**Status:** Pronto para revisão manual
**TDD Integration:** Complete model support for Red-Green-Refactor cycle tracking
**TDAH Support:** Comprehensive TDAH profile and session optimization models
**Data Architecture:** Type-safe models with business logic validation
**Quality:** Comprehensive documentation with examples, anti-patterns, and integration patterns
**Impact:** Foundation data models enhanced with TDD workflow support and TDAH accessibility patterns
```

**✅ Próximo:** Validation pipeline test - quality verification do models CLAUDE.md usando context_validator.py e integration_tester.py