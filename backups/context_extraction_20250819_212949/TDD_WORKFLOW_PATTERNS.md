# 🔄 TDD Workflow Patterns - Red-Green-Refactor Automation

**Purpose:** TDD-specific patterns for intelligent optimization  
**Scope:** Red-Green-Refactor cycles, Epic-Task mapping, TDD effectiveness  
**Integration:** Timer service, analytics engine, progress tracking  
**Last Updated:** 2025-08-19

---

## 🔴 **RED PHASE PATTERNS**

### **Failing Test Creation**
```python
# TDD Red phase pattern
def create_failing_test(epic_id: int, task_data: dict) -> TaskModel:
    # 1. Create task in RED phase
    task = TaskModel(
        title=task_data['title'],
        epic_id=epic_id,
        tdd_phase='Red',
        test_written=True,
        test_passing=False,
        created_at=datetime.now()
    )
    
    # 2. Track TDD phase transition
    tdd_tracker.start_red_phase(task.id)
    
    # 3. Start focus session for test writing
    timer_service.start_focus_session(
        task_id=task.id,
        session_type='test_writing',
        estimated_duration=25,  # Pomodoro default
        interruption_sensitivity='low'  # Minimize interruptions during test design
    )
    
    # 4. Analytics tracking
    analytics_service.track_tdd_phase_start('Red', task.id)
    
    return task
```

### **Red Phase Validation**
- **Test Required**: Every Red phase must have at least one failing test
- **Clear Requirements**: Task must have clear acceptance criteria
- **Time Boxing**: Red phase should be time-boxed (recommended: 25-50 minutes)
- **Focus Session**: Automated focus session tracking for Red phase
- **Test Quality**: Tests should be meaningful and comprehensive

### **Red Phase Anti-Patterns**
```python
# 🚨 RED PHASE ANTI-PATTERNS
def bad_red_phase():
    # ❌ No test written
    task.tdd_phase = 'Red'
    # No failing test created!
    
    # ❌ Vague requirements
    task.description = "Make it work"  # Too vague!
    
    # ❌ No time tracking
    # No focus session or time estimation
    
    # ❌ Skipping to implementation
    task.tdd_phase = 'Green'  # Skipped Red phase!
```

### **Red Phase Optimization**
```python
# ✅ OPTIMIZED RED PHASE
def optimized_red_phase(task_data: dict) -> TaskModel:
    # Clear, specific requirements
    task = TaskModel(
        title=task_data['title'],
        description=task_data['detailed_description'],
        acceptance_criteria=task_data['acceptance_criteria'],
        tdd_phase='Red'
    )
    
    # Multiple test scenarios
    for scenario in task_data['test_scenarios']:
        create_test_case(task.id, scenario, should_pass=False)
    
    # TDAH-friendly time boxing
    estimated_time = estimate_red_phase_duration(task.complexity)
    timer_service.start_adaptive_session(task.id, estimated_time)
    
    return task
```

---

## 🟢 **GREEN PHASE PATTERNS**

### **Implementation Focus**
```python
# TDD Green phase pattern
def transition_to_green(task_id: int) -> bool:
    task = task_service.get_task(task_id)
    
    # Validate Red phase completion
    if not task.has_failing_test():
        raise TDDWorkflowError("Cannot transition to Green without failing test")
    
    if not task.has_clear_acceptance_criteria():
        raise TDDWorkflowError("Cannot implement without clear requirements")
    
    # Update task phase
    task.tdd_phase = 'Green'
    task.implementation_started = datetime.now()
    
    # Start implementation focus session
    timer_service.start_focus_session(
        task_id=task_id,
        session_type='implementation',
        interruption_sensitivity='medium',  # Allow some interruptions
        energy_requirement='medium'  # Implementation requires sustained focus
    )
    
    # Track transition analytics
    red_duration = task.get_red_phase_duration()
    analytics_service.track_phase_transition('Red', 'Green', red_duration)
    
    return True
```

### **Green Phase Guidelines**
- **Minimal Implementation**: Write just enough code to make tests pass
- **No Over-Engineering**: Resist the urge to add extra features
- **Test Feedback**: Continuous test execution for immediate feedback
- **Progress Tracking**: Track implementation time vs estimates
- **Single Responsibility**: Focus on one failing test at a time

### **Green Phase Optimization for TDAH**
```python
# TDAH-optimized Green phase
class TDAHGreenPhase:
    def __init__(self, task_id: int):
        self.task_id = task_id
        self.micro_goals = self.break_into_micro_goals()
        self.dopamine_checkpoints = self.setup_reward_system()
    
    def break_into_micro_goals(self) -> List[str]:
        # Break implementation into 5-10 minute chunks
        task = task_service.get_task(self.task_id)
        return task.get_micro_implementation_steps()
    
    def complete_micro_goal(self, goal_index: int):
        # Immediate positive feedback for TDAH brains
        st.success(f"✅ Micro-goal {goal_index + 1} completed!")
        self.update_progress_bar()
        self.trigger_dopamine_reward()
    
    def trigger_dopamine_reward(self):
        # Visual and auditory feedback for completion
        st.balloons()  # Visual celebration
        analytics_service.record_micro_achievement(self.task_id)
```

### **Green Phase Anti-Patterns**
```python
# 🚨 GREEN PHASE ANTI-PATTERNS
def bad_green_phase():
    # ❌ Over-engineering
    def simple_addition(a, b):
        # Creating complex framework for simple addition
        return MathFramework().create_calculator().add(a, b)
    
    # ❌ Adding untested features
    if feature_flag_not_in_requirements:
        implement_extra_feature()  # Scope creep!
    
    # ❌ No progress tracking
    # Long implementation without micro-goals or feedback
    
    # ❌ Ignoring failing tests
    # Continuing implementation while tests still fail
```

---

## 🔵 **REFACTOR PHASE PATTERNS**

### **Code Improvement**
```python
# TDD Refactor phase pattern
def transition_to_refactor(task_id: int) -> bool:
    task = task_service.get_task(task_id)
    
    # Validate Green phase completion
    if not task.all_tests_passing():
        raise TDDWorkflowError("Cannot refactor with failing tests")
    
    if not task.requirements_satisfied():
        raise TDDWorkflowError("Requirements not met, cannot refactor")
    
    # Update task phase
    task.tdd_phase = 'Refactor'
    task.refactor_started = datetime.now()
    
    # Start refactor focus session
    timer_service.start_focus_session(
        task_id=task_id,
        session_type='refactoring',
        interruption_sensitivity='low',  # Minimize interruptions
        energy_requirement='high'  # Refactoring requires deep focus
    )
    
    # Identify refactoring opportunities
    refactor_suggestions = code_analyzer.suggest_refactorings(task.get_code())
    task.refactor_opportunities = refactor_suggestions
    
    return True
```

### **Refactor Phase Guidelines**
- **Test Safety Net**: Never refactor without comprehensive test coverage
- **Small Steps**: Make incremental improvements, test frequently
- **Code Clarity**: Focus on readability and maintainability
- **Performance**: Optimize hot paths and bottlenecks
- **Design Patterns**: Apply appropriate design patterns

### **Refactor Phase for TDAH**
```python
# TDAH-friendly refactoring
class TDAHRefactorSession:
    def __init__(self, task_id: int):
        self.task_id = task_id
        self.refactor_chunks = self.create_refactor_chunks()
        self.safety_checkpoints = self.setup_safety_net()
    
    def create_refactor_chunks(self) -> List[RefactorStep]:
        # Break refactoring into small, manageable steps
        return [
            RefactorStep("Extract method", estimated_minutes=10),
            RefactorStep("Rename variables", estimated_minutes=5),
            RefactorStep("Remove duplication", estimated_minutes=15),
            RefactorStep("Optimize imports", estimated_minutes=5)
        ]
    
    def execute_refactor_step(self, step: RefactorStep):
        # Execute with automatic test validation
        pre_tests = self.run_all_tests()
        if not pre_tests.all_passing():
            raise RefactorError("Tests failing before refactor")
        
        # Apply refactoring
        step.execute()
        
        # Validate tests still pass
        post_tests = self.run_all_tests()
        if not post_tests.all_passing():
            step.rollback()
            raise RefactorError("Refactoring broke tests")
        
        # Celebrate micro-achievement
        st.success(f"✅ {step.name} completed successfully!")
```

---

## 🔄 **COMPLETE CYCLE PATTERNS**

### **Full TDD Cycle Automation**
```python
# Complete TDD cycle management
class TDDCycleManager:
    def __init__(self, epic_id: int):
        self.epic_id = epic_id
        self.current_task = None
        self.cycle_analytics = TDDCycleAnalytics()
    
    def start_new_cycle(self, task_data: dict) -> TaskModel:
        # 1. Create task in Red phase
        self.current_task = self.create_red_phase_task(task_data)
        
        # 2. Set up analytics tracking
        self.cycle_analytics.start_cycle(self.current_task.id)
        
        # 3. Begin Red phase focus session
        self.start_red_phase_session()
        
        return self.current_task
    
    def advance_to_next_phase(self) -> bool:
        current_phase = self.current_task.tdd_phase
        
        if current_phase == 'Red':
            return self.transition_to_green()
        elif current_phase == 'Green':
            return self.transition_to_refactor()
        elif current_phase == 'Refactor':
            return self.complete_cycle()
        
        return False
    
    def complete_cycle(self) -> bool:
        # Mark task as complete
        self.current_task.tdd_phase = 'Complete'
        self.current_task.completed_at = datetime.now()
        
        # Calculate cycle metrics
        cycle_metrics = self.cycle_analytics.calculate_cycle_metrics()
        
        # Update epic progress
        epic_service.update_epic_progress(self.epic_id)
        
        # TDAH reward system
        self.trigger_completion_rewards(cycle_metrics)
        
        return True
    
    def trigger_completion_rewards(self, metrics: dict):
        # Visual celebration
        st.balloons()
        st.success(f"🎉 TDD Cycle Complete!")
        
        # Show metrics
        st.metric("Cycle Duration", f"{metrics['total_duration']} minutes")
        st.metric("Phase Balance", f"{metrics['balance_score']}/10")
        st.metric("Test Coverage", f"{metrics['coverage_improvement']}%")
        
        # Award achievements
        achievement_service.check_and_award_achievements(
            self.current_task.id, metrics
        )
```

---

## 📊 **TDD EFFECTIVENESS METRICS**

### **Cycle Quality Indicators**
```python
# TDD cycle quality measurement
class TDDQualityMetrics:
    def calculate_cycle_effectiveness(self, task_id: int) -> dict:
        task = task_service.get_task(task_id)
        
        return {
            # Phase balance (ideal: 30% Red, 50% Green, 20% Refactor)
            'phase_balance_score': self.calculate_phase_balance(task),
            
            # Test quality metrics
            'test_coverage_improvement': self.calculate_coverage_improvement(task),
            'test_quality_score': self.assess_test_quality(task),
            
            # Code quality improvements
            'code_complexity_reduction': self.measure_complexity_improvement(task),
            'maintainability_score': self.assess_maintainability(task),
            
            # Productivity metrics
            'velocity_score': self.calculate_development_velocity(task),
            'focus_effectiveness': self.measure_focus_quality(task),
            
            # TDAH-specific metrics
            'interruption_recovery_rate': self.calculate_recovery_rate(task),
            'energy_efficiency': self.assess_energy_usage(task)
        }
    
    def generate_improvement_recommendations(self, metrics: dict) -> List[str]:
        recommendations = []
        
        if metrics['phase_balance_score'] < 7:
            recommendations.append("Consider spending more time in Red phase for better test design")
        
        if metrics['focus_effectiveness'] < 6:
            recommendations.append("Try shorter focus sessions or adjust interruption settings")
        
        if metrics['energy_efficiency'] < 5:
            recommendations.append("Schedule complex tasks during high-energy periods")
        
        return recommendations
```

### **Epic-Level TDD Analytics**
```python
# Epic TDD performance tracking
class EpicTDDAnalytics:
    def analyze_epic_tdd_performance(self, epic_id: int) -> dict:
        epic = epic_service.get_epic(epic_id)
        tasks = task_service.get_tasks_by_epic(epic_id)
        
        return {
            'overall_tdd_adoption': self.calculate_tdd_adoption_rate(tasks),
            'average_cycle_quality': self.calculate_average_cycle_quality(tasks),
            'velocity_trends': self.analyze_velocity_trends(tasks),
            'quality_improvements': self.measure_quality_improvements(tasks),
            'team_effectiveness': self.assess_team_tdd_effectiveness(tasks),
            'tdah_optimization_impact': self.measure_tdah_benefits(tasks)
        }
```

---

## 🧠 **TDAH-OPTIMIZED TDD PATTERNS**

### **Hyperfocus Session Management**
```python
# Hyperfocus-aware TDD cycling
class HyperfocusTDDManager:
    def detect_hyperfocus_state(self, user_id: int) -> bool:
        recent_sessions = timer_service.get_recent_sessions(user_id, hours=2)
        
        # Indicators of hyperfocus
        return (
            len(recent_sessions) > 3 and  # Multiple consecutive sessions
            all(s.duration > 45 for s in recent_sessions) and  # Long sessions
            all(s.interruption_count < 2 for s in recent_sessions)  # Few interruptions
        )
    
    def manage_hyperfocus_tdd_cycle(self, task_id: int):
        if self.detect_hyperfocus_state(task.user_id):
            # Extend session times for hyperfocus
            timer_service.extend_session_duration(task_id, multiplier=2.0)
            
            # Reduce interruption notifications
            notification_service.set_do_not_disturb(task.user_id, duration=120)
            
            # Prepare for energy crash recovery
            self.schedule_recovery_reminders(task.user_id)
```

### **Energy-Aware Phase Scheduling**
```python
# Energy-based TDD phase optimization
class EnergyAwareTDD:
    def suggest_optimal_phase(self, user_id: int) -> str:
        energy_level = user_profile_service.get_current_energy(user_id)
        time_of_day = datetime.now().hour
        
        if energy_level >= 8:  # High energy
            return 'Red'  # Complex thinking for test design
        elif energy_level >= 6:  # Medium energy
            return 'Green'  # Implementation work
        else:  # Low energy
            return 'Refactor'  # Mechanical improvements
    
    def adapt_session_to_energy(self, task_id: int, energy_level: int):
        if energy_level < 5:  # Low energy
            # Shorter sessions, more breaks
            timer_service.use_micro_sessions(task_id, duration=15)
            
        elif energy_level > 8:  # High energy
            # Longer sessions, complex work
            timer_service.use_extended_sessions(task_id, duration=45)
```

---

*TDD Workflow Patterns: Optimizing Red-Green-Refactor cycles for enterprise productivity and TDAH accessibility*