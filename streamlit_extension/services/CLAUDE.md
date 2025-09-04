# 🏢 CLAUDE.md - Service Layer

**Module:** services/  
**Purpose:** Business logic layer with clean architecture + TDD business logic patterns  
**TDD Mission:** Orchestrate Red-Green-Refactor cycles with enterprise business rules  
**Architecture:** BaseService + ServiceResult pattern + DI container  
**Services:** 7 business services (5,800+ lines) with TDD integration + IA-driven epic generation (Phase 5.1)  
**Last Updated:** 2025-09-04 - IA-Driven Epic Generation & Topological Ordering

---

## 🎯 **TDD + TDAH INTEGRATION**

### **TDD Business Logic Patterns**
- **TDD Cycle Orchestration**: Business rules for Red-Green-Refactor transitions
- **Phase Validation**: Ensure proper TDD workflow compliance
- **Test-Code Integration**: Business logic connecting tests to implementation
- **Cycle Analytics**: Business intelligence for TDD effectiveness

### **TDAH-Optimized Service Operations**
- **Micro-Service Patterns**: Break complex operations into TDAH-friendly chunks
- **Immediate Feedback**: ServiceResult pattern provides instant success/failure feedback
- **Focus Session Integration**: Services aware of TDAH focus states
- **Energy-Based Scheduling**: Service operations adapted to user energy levels

---

## 🔧 **Service Architecture for TDD**

### **Service Hierarchy with TDD Integration + IA**
```
BaseService (Abstract)
├── ProjectService (612 lines) + TDD epic organization
├── EpicService (847 lines) + TDD workflow orchestration ⭐
├── EpicGenerationService (480 lines) + IA-driven epic creation ⭐⭐⭐ [NEW]
├── TopologicalOrderingService (320 lines) + Deterministic epic ordering ⭐⭐ [NEW]
├── TaskService (923 lines) + TDD cycle management ⭐⭐
├── AnalyticsService (856 lines) + TDD effectiveness metrics ⭐
└── TimerService (734 lines) + TDAH focus session management ⭐⭐
```

### **TDD-Enhanced ServiceResult Pattern**
```python
# Type-safe TDD error handling without exceptions
from streamlit_extension.services.base import ServiceResult, TDDServiceResult

def start_red_phase(task_data: dict) -> TDDServiceResult[TaskModel]:
    # TDD-specific validation
    if not task_data.get('test_requirements'):
        return TDDServiceResult.tdd_failure("Red phase requires test requirements")
    
    if not task_data.get('acceptance_criteria'):
        return TDDServiceResult.tdd_failure("Red phase requires clear acceptance criteria")
    
    # Create task in Red phase
    task = TaskModel(**task_data, tdd_phase='Red')
    
    # Start focus session for test writing
    focus_result = timer_service.start_test_writing_session(task.id)
    if not focus_result.is_success():
        return TDDServiceResult.tdd_failure(f"Failed to start focus session: {focus_result.get_error()}")
    
    return TDDServiceResult.tdd_success(task, phase='Red', next_action='Write failing tests')

# Usage pattern with TDAH-friendly feedback
result = task_service.start_red_phase(task_data)
if result.is_success():
    task = result.get_value()
    st.success(f"🔴 Red Phase Started! Next: {result.get_next_action()}")
    show_tdd_guidance(result.get_phase_guidance())
else:
    st.error(f"❌ {result.get_error()}")
    show_helpful_tdd_tips(result.get_tdd_suggestions())
```

### **TDAH-Aware ServiceContainer Pattern**
```python
# Dependency injection with TDAH considerations
from streamlit_extension.services import ServiceContainer

class TDAHServiceContainer(ServiceContainer):
    def __init__(self, user_profile: UserProfile):
        super().__init__()
        self.user_profile = user_profile
        self.adapt_services_to_tdah()
    
    def adapt_services_to_tdah(self):
        # Configure services for TDAH users
        if self.user_profile.has_attention_challenges:
            self.configure_micro_operations()
            self.enable_immediate_feedback()
        
        if self.user_profile.has_hyperfocus_tendencies:
            self.configure_hyperfocus_protection()
            self.enable_gentle_interruptions()
    
    def get_task_service(self) -> 'TDAHTaskService':
        # Return TDAH-optimized task service
        service = super().get_task_service()
        service.configure_for_tdah(self.user_profile)
        return service
```

---

## 🎯 **Business Services with TDD Integration**

### **EpicService (847 lines) - TDD Workflow Orchestration ⭐**
- **Purpose**: Epic management with TDD workflow integration and gamification
- **TDD Features**: Epic progress based on TDD cycle completions
- **Key Methods**: 
  - `create_epic_with_tdd_plan()` - Create epic with TDD structure
  - `calculate_tdd_progress()` - Progress based on Red-Green-Refactor cycles
  - `update_epic_from_tdd_cycles()` - Auto-update epic progress from TDD completions
- **TDAH Features**: Chunked epic breakdown, visual progress tracking
- **Dependencies**: ProjectService, TaskService, TDDWorkflowEngine

```python
# TDD-integrated epic management
class EpicService(BaseService):
    def create_epic_with_tdd_structure(self, epic_data: dict) -> ServiceResult[EpicModel]:
        # Validate epic can support TDD workflow
        if not self._validate_tdd_epic_requirements(epic_data):
            return ServiceResult.failure("Epic must have clear TDD structure")
        
        # Create epic with TDD phases planned
        epic = EpicModel(**epic_data)
        epic.tdd_structure = self._generate_tdd_structure(epic_data)
        
        # Create initial Red-phase tasks
        initial_tasks = self._create_initial_red_phase_tasks(epic.id)
        
        # Set up TDD progress tracking
        self._initialize_tdd_progress_tracking(epic.id)
        
        return ServiceResult.success(epic)
    
    def calculate_tdd_effectiveness(self, epic_id: int) -> dict:
        # Calculate TDD cycle effectiveness for epic
        tasks = self.task_service.get_tasks_by_epic(epic_id)
        tdd_cycles = [task for task in tasks if task.has_complete_tdd_cycle()]
        
        return {
            'total_cycles': len(tdd_cycles),
            'average_cycle_time': self._calculate_average_cycle_time(tdd_cycles),
            'red_green_refactor_balance': self._calculate_phase_balance(tdd_cycles),
            'test_coverage_improvement': self._calculate_coverage_improvement(tdd_cycles),
            'effectiveness_score': self._calculate_tdd_effectiveness_score(tdd_cycles)
        }
```

### **EpicGenerationService (480 lines) - IA-Driven Epic Creation ⭐⭐⭐ [NEW]**
- **Purpose**: AI-driven epic generation from product vision analysis with confidence scoring
- **IA Features**: GPT-4 integration, structured epic extraction, dependency detection
- **Key Methods**:
  - `analyze_product_vision()` - Deep analysis of product vision for epic generation
  - `generate_epics_from_vision()` - Create 3-7 optimized epics with AI
  - `extract_epic_dependencies()` - Automatic dependency detection between epics
  - `calculate_confidence_scores()` - Transparent AI confidence metrics
- **Integration**: Works with TopologicalOrderingService for epic sequencing
- **Dependencies**: ProductVisionService, AIAnalysisEngine, ConfidenceCalculator

```python
# AI-driven epic generation from product vision
class EpicGenerationService(BaseService):
    def analyze_product_vision(self, vision_data: dict) -> ServiceResult[VisionAnalysis]:
        # Comprehensive product vision analysis
        analysis = VisionAnalysis()
        
        # Extract key components for epic generation
        analysis.core_features = self._extract_core_features(vision_data)
        analysis.technical_requirements = self._identify_technical_requirements(vision_data)
        analysis.user_personas = self._extract_user_personas(vision_data)
        analysis.constraints = self._analyze_constraints(vision_data)
        
        # AI-powered insight generation
        ai_insights = self.ai_engine.analyze_vision_for_epics(vision_data)
        analysis.suggested_architecture = ai_insights.get('architecture_recommendations')
        analysis.complexity_factors = ai_insights.get('complexity_analysis')
        
        return ServiceResult.success(analysis)
    
    def generate_epics_from_vision(self, vision_analysis: VisionAnalysis) -> ServiceResult[List[GeneratedEpic]]:
        # AI prompt engineering for epic generation
        prompt_context = self._build_epic_generation_prompt(vision_analysis)
        
        # Call AI service with structured prompt
        ai_response = self.ai_engine.generate_structured_epics(prompt_context)
        
        # Parse and validate AI response
        raw_epics = self._parse_ai_epic_response(ai_response)
        validated_epics = []
        
        for epic_data in raw_epics:
            # Validate epic structure and content
            validation_result = self._validate_generated_epic(epic_data)
            if validation_result.is_valid:
                # Enhance with calculated fields
                epic = GeneratedEpic(
                    name=epic_data['name'],
                    description=epic_data['description'],
                    complexity_score=self._calculate_complexity_score(epic_data),
                    effort_estimate=self._estimate_effort_days(epic_data),
                    epic_dependencies=self._extract_dependencies(epic_data),
                    unblock_potential=self._calculate_unblock_potential(epic_data),
                    ai_confidence=validation_result.confidence_score
                )
                validated_epics.append(epic)
        
        if len(validated_epics) < 3:
            return ServiceResult.failure("AI generated insufficient valid epics")
        
        return ServiceResult.success(validated_epics)
    
    def _build_epic_generation_prompt(self, analysis: VisionAnalysis) -> str:
        # Structured prompt for consistent epic generation
        return f"""
        Baseado na seguinte análise de product vision, gere 3-7 épicos otimizados:
        
        **Visão do Produto:**
        - Problema: {analysis.problem_statement}
        - Solução: {analysis.solution_overview}
        - Público-alvo: {analysis.target_audience}
        - Restrições: {analysis.constraints}
        
        **Requisitos Técnicos:**
        {analysis.technical_requirements}
        
        **Para cada épico, forneça:**
        1. Nome conciso e descritivo
        2. Descrição detalhada do escopo
        3. Nível de complexidade (1-5)
        4. Estimativa de esforço em dias
        5. Dependências de outros épicos
        6. Potencial de desbloqueio de épicos futuros
        
        **Formato de resposta:** JSON estruturado com array de épicos.
        """

    def calculate_confidence_scores(self, generated_epics: List[GeneratedEpic]) -> dict:
        # Calculate confidence metrics for transparency
        total_confidence = sum(epic.ai_confidence for epic in generated_epics)
        average_confidence = total_confidence / len(generated_epics)
        
        confidence_distribution = {
            'high_confidence': len([e for e in generated_epics if e.ai_confidence >= 0.8]),
            'medium_confidence': len([e for e in generated_epics if 0.6 <= e.ai_confidence < 0.8]),
            'low_confidence': len([e for e in generated_epics if e.ai_confidence < 0.6])
        }
        
        return {
            'average_confidence': average_confidence,
            'confidence_distribution': confidence_distribution,
            'recommendation': self._get_confidence_recommendation(average_confidence),
            'suggested_actions': self._get_confidence_improvement_suggestions(generated_epics)
        }
```

### **TopologicalOrderingService (320 lines) - Deterministic Epic Ordering ⭐⭐ [NEW]**
- **Purpose**: Apply DETERMINISTIC_TOPOLOGICAL_ORDERING_DEMO algorithm to epic dependencies
- **Algorithm Features**: Kahn's algorithm, priority heap, 4-level tie-breaking
- **Key Methods**:
  - `order_epics_by_dependencies()` - Main ordering algorithm application
  - `convert_epics_to_tasks()` - Adapter for Task-compatible algorithm
  - `validate_epic_dependencies()` - Dependency cycle detection
  - `assign_sort_order()` - Deterministic ordering assignment
- **Performance**: O(V+E) complexity for any project size
- **Dependencies**: EpicGenerationService, DETERMINISTIC_TOPOLOGICAL_ORDERING_DEMO

```python
# Deterministic topological ordering for epics
class TopologicalOrderingService(BaseService):
    def order_epics_by_dependencies(self, generated_epics: List[GeneratedEpic]) -> ServiceResult[List[OrderedEpic]]:
        # Convert epics to Task-compatible format for algorithm
        epic_tasks = self._convert_epics_to_tasks(generated_epics)
        epic_dependencies = self._extract_epic_dependencies(generated_epics)
        
        # Validate dependencies for cycles
        dependency_validation = self._validate_dependencies(epic_dependencies)
        if not dependency_validation.is_valid:
            return ServiceResult.failure(f"Dependency cycle detected: {dependency_validation.cycle_info}")
        
        # Apply DETERMINISTIC_TOPOLOGICAL_ORDERING_DEMO algorithm
        try:
            execution_order, task_scores, exec_time = topological_sort_with_priority_corrected(
                epic_tasks, epic_dependencies
            )
            
            # Convert back to ordered epics with sort_order
            ordered_epics = []
            for i, epic_key in enumerate(execution_order):
                epic = self._find_epic_by_key(generated_epics, epic_key)
                ordered_epic = OrderedEpic.from_generated_epic(epic)
                ordered_epic.sort_order = i
                ordered_epic.priority_score = task_scores[epic_key].total_score
                ordered_epic.critical_path_weight = task_scores[epic_key].critical_path_score
                ordered_epics.append(ordered_epic)
            
            # Performance metrics
            ordering_metrics = {
                'execution_time_ms': exec_time,
                'epics_ordered': len(ordered_epics),
                'dependency_complexity': len(epic_dependencies),
                'algorithm_performance': 'O(V+E)' 
            }
            
            return ServiceResult.success(ordered_epics, metadata=ordering_metrics)
            
        except Exception as e:
            return ServiceResult.failure(f"Topological ordering failed: {str(e)}")
    
    def _convert_epics_to_tasks(self, epics: List[GeneratedEpic]) -> List[Task]:
        # Adapter pattern: Convert epics to Task objects for algorithm compatibility
        tasks = []
        for epic in epics:
            task = Task(
                task_key=epic.epic_key,
                title=epic.name,
                priority=self._map_complexity_to_priority(epic.complexity_score),
                effort_estimate=epic.effort_estimate,
                story_points=int(epic.complexity_score),
                created_at=datetime.now()
            )
            tasks.append(task)
        return tasks
    
    def _validate_dependencies(self, dependencies: List[Tuple[str, str]]) -> DependencyValidation:
        # Cycle detection using DFS
        graph = defaultdict(list)
        for dependent, prerequisite in dependencies:
            graph[prerequisite].append(dependent)
        
        visited = set()
        rec_stack = set()
        
        def has_cycle(node):
            if node in rec_stack:
                return True
            if node in visited:
                return False
                
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph[node]:
                if has_cycle(neighbor):
                    return True
                    
            rec_stack.remove(node)
            return False
        
        # Check all nodes for cycles
        all_nodes = set()
        for dep, prereq in dependencies:
            all_nodes.update([dep, prereq])
        
        for node in all_nodes:
            if node not in visited:
                if has_cycle(node):
                    return DependencyValidation(is_valid=False, cycle_info=f"Cycle detected involving {node}")
        
        return DependencyValidation(is_valid=True, cycle_info=None)
    
    def assign_sort_order_to_database(self, ordered_epics: List[OrderedEpic], project_id: int) -> ServiceResult[bool]:
        # Persist sort_order to database for UI display
        try:
            with self.db_manager.get_connection() as conn:
                for epic in ordered_epics:
                    conn.execute("""
                        UPDATE framework_epics 
                        SET sort_order = ?, 
                            critical_path_weight = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE epic_key = ? AND project_id = ?
                    """, (epic.sort_order, epic.critical_path_weight, epic.epic_key, project_id))
                
                conn.commit()
            
            return ServiceResult.success(True)
            
        except Exception as e:
            return ServiceResult.failure(f"Failed to persist sort order: {str(e)}")
```

### **TaskService (923 lines) - TDD Cycle Management ⭐⭐**
- **Purpose**: Task CRUD with complete Red→Green→Refactor workflow management
- **TDD Features**: Full TDD cycle automation, phase validation, test integration
- **Key Methods**:
  - `start_red_phase()` - Initialize Red phase with test requirements
  - `transition_to_green()` - Validate Red completion, start implementation
  - `transition_to_refactor()` - Validate Green completion, start improvements
  - `complete_tdd_cycle()` - Finalize cycle with metrics and analytics
- **TDAH Features**: Micro-task breakdown, immediate feedback, interruption recovery
- **Dependencies**: EpicService, TimerService, TDDWorkflowEngine, TestExecutionService

```python
# Complete TDD cycle management
class TaskService(BaseService):
    def transition_tdd_phase(self, task_id: int, from_phase: str, to_phase: str) -> TDDServiceResult[TaskModel]:
        task = self.get_task(task_id)
        
        # Validate transition is allowed
        if not self._validate_tdd_transition(task, from_phase, to_phase):
            return TDDServiceResult.tdd_failure(f"Invalid transition from {from_phase} to {to_phase}")
        
        # Phase-specific validation
        if to_phase == 'Green':
            return self._validate_and_transition_to_green(task)
        elif to_phase == 'Refactor':
            return self._validate_and_transition_to_refactor(task)
        elif to_phase == 'Complete':
            return self._validate_and_complete_cycle(task)
        
        return TDDServiceResult.tdd_failure(f"Unknown phase: {to_phase}")
    
    def _validate_and_transition_to_green(self, task: TaskModel) -> TDDServiceResult[TaskModel]:
        # Red phase completion validation
        if not task.has_failing_tests():
            return TDDServiceResult.tdd_failure("Cannot transition to Green without failing tests")
        
        if not task.has_clear_requirements():
            return TDDServiceResult.tdd_failure("Cannot implement without clear requirements")
        
        # Update task to Green phase
        task.tdd_phase = 'Green'
        task.green_phase_started = datetime.now()
        
        # Start implementation focus session
        focus_result = self.timer_service.start_implementation_session(task.id)
        
        # Analytics tracking
        self.analytics_service.track_tdd_transition('Red', 'Green', task.id)
        
        return TDDServiceResult.tdd_success(
            task, 
            phase='Green', 
            next_action='Write minimal implementation to make tests pass'
        )
```

### **TimerService (734 lines) - TDAH Focus Session Management ⭐⭐**
- **Purpose**: TDAH-optimized focus sessions with TDD integration
- **TDD Features**: Phase-specific timer sessions, TDD-aware break timing
- **Key Methods**:
  - `start_tdd_phase_session()` - Phase-specific focus sessions
  - `handle_tdd_interruption()` - TDD-aware interruption management
  - `track_tdd_focus_effectiveness()` - TDD productivity analytics
- **TDAH Features**: Adaptive timing, hyperfocus protection, energy tracking
- **Dependencies**: TaskService, AnalyticsService, TDAHProfileService

```python
# TDAH-optimized focus sessions for TDD
class TimerService(BaseService):
    def start_tdd_phase_session(self, task_id: int, phase: str) -> ServiceResult[FocusSession]:
        task = self.task_service.get_task(task_id)
        user_profile = self.get_user_profile(task.user_id)
        
        # Phase-specific session configuration
        session_config = self._get_tdd_phase_session_config(phase, user_profile)
        
        # Adapt for TDAH profile
        if user_profile.has_tdah_traits:
            session_config = self._adapt_session_for_tdah(session_config, user_profile)
        
        # Create focus session
        session = FocusSession(
            task_id=task_id,
            session_type=f'tdd_{phase.lower()}',
            duration=session_config['duration'],
            interruption_tolerance=session_config['interruption_tolerance'],
            break_reminders=session_config['break_reminders']
        )
        
        # Start session with TDD context
        return self._start_session_with_tdd_context(session, task)
    
    def _get_tdd_phase_session_config(self, phase: str, profile: UserProfile) -> dict:
        # Phase-specific timing for TDD + TDAH
        configs = {
            'Red': {  # Test design requires deep thinking
                'duration': 45 if profile.can_sustain_long_focus else 25,
                'interruption_tolerance': 'low',  # Minimize interruptions during design
                'break_reminders': ['hydration', 'eye_rest'],
                'energy_requirement': 'high'
            },
            'Green': {  # Implementation can handle some interruptions
                'duration': 50 if profile.can_sustain_long_focus else 30,
                'interruption_tolerance': 'medium',
                'break_reminders': ['movement', 'hydration'],
                'energy_requirement': 'medium'
            },
            'Refactor': {  # Refactoring requires sustained attention
                'duration': 35 if profile.can_sustain_long_focus else 20,
                'interruption_tolerance': 'low',
                'break_reminders': ['eye_rest', 'posture'],
                'energy_requirement': 'high'
            }
        }
        
        return configs.get(phase, configs['Green'])
```

### **AnalyticsService (856 lines) - TDD Effectiveness Metrics ⭐**
- **Purpose**: Comprehensive analytics with TDD effectiveness and TDAH productivity patterns
- **TDD Features**: Cycle effectiveness, phase balance analysis, test quality metrics
- **Key Methods**:
  - `get_tdd_effectiveness_metrics()` - Complete TDD performance analysis
  - `calculate_phase_balance_score()` - Red-Green-Refactor time distribution
  - `analyze_tdd_velocity_trends()` - TDD development speed analysis
- **TDAH Features**: Focus pattern analysis, energy optimization, interruption impact
- **Dependencies**: All other services, TDDAnalyticsEngine, TDAHProductivityEngine

```python
# TDD effectiveness analytics
class AnalyticsService(BaseService):
    def get_comprehensive_tdd_metrics(self, user_id: int, timeframe: str = 'week') -> dict:
        # Collect TDD performance data
        tdd_cycles = self._get_tdd_cycles_for_timeframe(user_id, timeframe)
        focus_sessions = self._get_focus_sessions_for_timeframe(user_id, timeframe)
        
        # Calculate TDD effectiveness
        tdd_metrics = {
            'cycle_completion_rate': self._calculate_cycle_completion_rate(tdd_cycles),
            'average_cycle_duration': self._calculate_average_cycle_duration(tdd_cycles),
            'phase_balance_score': self._calculate_phase_balance(tdd_cycles),
            'test_quality_improvement': self._calculate_test_quality_trends(tdd_cycles),
            'refactor_effectiveness': self._calculate_refactor_impact(tdd_cycles)
        }
        
        # TDAH-specific productivity metrics
        tdah_metrics = {
            'focus_session_effectiveness': self._analyze_focus_effectiveness(focus_sessions),
            'interruption_recovery_rate': self._calculate_interruption_recovery(focus_sessions),
            'energy_optimization_score': self._analyze_energy_patterns(user_id),
            'hyperfocus_utilization': self._analyze_hyperfocus_patterns(focus_sessions)
        }
        
        # Combined insights
        insights = self._generate_tdd_tdah_insights(tdd_metrics, tdah_metrics)
        
        return {
            'tdd_effectiveness': tdd_metrics,
            'tdah_productivity': tdah_metrics,
            'insights': insights,
            'recommendations': self._generate_optimization_recommendations(tdd_metrics, tdah_metrics)
        }
```

---

## 📊 **Anti-Patterns to Avoid**

### **🔴 TDD Service Anti-Patterns**
```python
# ❌ TDD-ignorant service methods
def bad_tdd_service():
    # No TDD phase awareness
    def create_task(task_data):
        task = Task(**task_data)
        # No TDD structure or phase information!
        return task
    
    # No test integration
    def complete_task(task_id):
        task.status = 'complete'
        # No validation of test status or TDD cycle completion!
    
    # Missing TDD validation
    def update_task(task_id, updates):
        # Direct updates without TDD workflow validation
        apply_updates(task_id, updates)

# ✅ TDD-integrated service methods
def good_tdd_service():
    def create_task_in_red_phase(epic_id, requirements):
        # Clear TDD phase initialization
        task = TaskModel(
            epic_id=epic_id,
            tdd_phase='Red',
            test_requirements=requirements.test_requirements,
            acceptance_criteria=requirements.acceptance_criteria
        )
        
        # Initialize TDD tracking
        tdd_tracker.start_red_phase(task.id)
        return task
    
    def transition_task_to_green_phase(task_id):
        # Validate Red phase completion
        task = self.get_task(task_id)
        if not task.has_failing_tests():
            raise TDDWorkflowError("Cannot transition without failing tests")
        
        # Safe transition with validation
        task.tdd_phase = 'Green'
        tdd_tracker.track_phase_transition(task_id, 'Red', 'Green')
        return task
```

### **🔴 TDAH Service Anti-Patterns**
```python
# ❌ TDAH-hostile service patterns
def bad_tdah_service():
    # Long, complex operations without feedback
    def complex_operation(data):
        # 50+ steps without any progress feedback
        for i in range(50):
            complex_step(i)  # No progress indication for TDAH users
        return result
    
    # No interruption tolerance
    def rigid_workflow(task_id):
        start_workflow()
        # If user gets distracted, entire workflow fails
        if not continuous_attention():
            reset_everything()  # Lost all progress!
    
    # Missing energy awareness
    def schedule_task(task_id):
        # Ignores user's current energy level
        schedule_at_next_available_slot()  # May schedule complex task during low energy

# ✅ TDAH-friendly service patterns
def good_tdah_service():
    def chunked_operation_with_feedback(data):
        total_steps = len(data)
        for i, item in enumerate(data):
            # Process in small chunks
            process_item(item)
            
            # Immediate feedback for dopamine
            progress = (i + 1) / total_steps
            yield ProgressUpdate(progress=progress, message=f"Processed {i+1}/{total_steps}")
    
    def interruption_tolerant_workflow(task_id):
        # Save state at each step
        workflow_state = load_workflow_state(task_id)
        
        try:
            continue_from_step(workflow_state.current_step)
        except InterruptionException:
            # Graceful interruption handling
            save_workflow_state(task_id, workflow_state)
            return InterruptionResponse("Work saved! You can resume anytime.")
    
    def energy_aware_scheduling(task_id, user_id):
        # Consider user's current energy and optimal times
        energy_level = get_current_energy(user_id)
        optimal_times = get_user_optimal_times(user_id)
        
        if energy_level >= 7 and current_time in optimal_times:
            return schedule_immediately(task_id)
        else:
            return suggest_optimal_scheduling(task_id, energy_level, optimal_times)
```

---

## 🔧 **File Tracking - Services Module**

### **Modified Files Checklist**
```
📊 **SERVICES MODULE - ARQUIVOS MODIFICADOS:**

**TDD Core Services:**
- services/task_service.py:linha_X - [Complete TDD cycle management]
- services/epic_service.py:linha_Y - [TDD workflow orchestration]

**TDAH Support Services:**
- services/timer_service.py:linha_Z - [TDAH-optimized focus sessions]
- services/analytics_service.py:seção_W - [TDD + TDAH effectiveness metrics]

**Business Services:**
- services/project_service.py:linha_U - [TDD epic organization]

**Infrastructure:**
- services/base.py:linha_T - [TDD ServiceResult pattern]
- services/service_container.py:linha_S - [TDAH-aware DI container]

**Status:** Ready for manual review
**TDD Integration:** Complete Red-Green-Refactor workflow operational
**TDAH Support:** Focus sessions and interruption handling implemented
**Business Logic:** All validation rules verified
**Architecture:** Clean architecture patterns maintained
**Impact:** [Impact on TDD workflows, TDAH productivity, and business operations]
```

### **Service Validation Required**
- [ ] TDD ServiceResult pattern used consistently
- [ ] All TDD business rules validated
- [ ] TDAH focus session integration functional
- [ ] No direct database calls from UI
- [ ] Transaction management proper for TDD cycles
- [ ] Error handling comprehensive with encouraging feedback
- [ ] Energy-aware operations implemented

---

*Business logic layer with complete TDD workflow integration and TDAH accessibility optimization*