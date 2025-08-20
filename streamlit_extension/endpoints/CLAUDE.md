# 🏥 CLAUDE.md - Endpoints Layer

**Module:** endpoints/  
**Purpose:** Health monitoring & API endpoints with TDD validation + TDAH-friendly API design  
**TDD Mission:** API endpoints that support Red-Green-Refactor cycle monitoring and test automation  
**Architecture:** RESTful endpoints with enterprise health monitoring and TDD workflow integration  
**Endpoints:** 8+ monitoring endpoints with TDD metrics and TDAH accessibility patterns  
**Last Updated:** 2025-08-19

---

## 🎯 **TDD + TDAH INTEGRATION**

### **TDD API Endpoint Patterns**
- **Test-Driven API Development**: Endpoints designed with test-first methodology and validation
- **TDD Workflow Monitoring**: Real-time monitoring of Red-Green-Refactor cycle progress
- **Test Automation Integration**: API endpoints that support automated testing and CI/CD
- **Cycle Metrics Exposure**: APIs that expose TDD effectiveness and quality metrics

### **TDAH-Optimized API Design**
- **Immediate Response Feedback**: Fast, clear API responses that don't break developer flow
- **Progressive Data Disclosure**: APIs that return data in TDAH-friendly, digestible chunks
- **Clear Error Messages**: Error responses designed for quick understanding and resolution
- **Cognitive Load Minimization**: Simple, predictable API patterns that reduce mental overhead

---

## 🏗️ **Endpoints Architecture for TDD**

### **Endpoint Module Hierarchy**
```
streamlit_extension/endpoints/
├── __init__.py                       # 🔧 Endpoint exports and TDD monitoring utilities
├── health.py                         # 🏥 Health monitoring + TDD system status ⭐⭐
├── api_middleware.py                 # 🛡️ API middleware + TDD request tracking ⭐
├── tdd_metrics.py                    # 📊 TDD metrics exposure endpoints ⭐⭐⭐
├── tdah_monitoring.py                # 🧠 TDAH productivity monitoring APIs ⭐⭐
├── system_status.py                  # 📈 System health + TDD workflow status
├── performance_endpoints.py          # ⚡ Performance monitoring + TDD benchmarks
├── authentication_endpoints.py       # 🔐 Auth endpoints + TDD session management
└── development_endpoints.py          # 🔧 Development utilities + TDD debugging
```

### **TDD-Enhanced Health Monitoring Architecture**
```python
# TDD-integrated health monitoring
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

class TDDHealthStatus(Enum):
    """TDD system health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    MAINTENANCE = "maintenance"

class TDAHAccessibilityLevel(Enum):
    """TDAH accessibility compliance levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    NEEDS_IMPROVEMENT = "needs_improvement"
    POOR = "poor"

class TDDSystemHealth(BaseModel):
    """TDD system health monitoring model."""
    status: TDDHealthStatus
    tdd_cycles_active: int
    average_cycle_duration: Optional[float]
    system_performance: Dict[str, float]
    test_automation_health: bool
    database_health: bool
    user_session_health: bool
    tdah_accessibility_level: TDAHAccessibilityLevel
    timestamp: datetime
    
class TDDMetricsResponse(BaseModel):
    """TDD metrics API response model."""
    overall_effectiveness: float
    cycle_completion_rate: float
    phase_distribution: Dict[str, float]
    quality_metrics: Dict[str, float]
    user_productivity: Dict[str, float]
    tdah_optimization_score: float
    recommendations: List[str]

class TDAHProductivityResponse(BaseModel):
    """TDAH productivity monitoring response."""
    focus_effectiveness: float
    energy_optimization: float
    interruption_impact: float
    session_success_rate: float
    cognitive_load_score: float
    productivity_recommendations: List[str]
    optimal_session_config: Dict[str, Any]
```

---

## 🏥 **Core Endpoints with TDD Integration**

### **Health Monitoring (health.py) - TDD System Status ⭐⭐**
- **Purpose**: Comprehensive health monitoring with TDD workflow status and TDAH accessibility
- **TDD Features**: Real-time TDD cycle monitoring, test automation health, development workflow status
- **Key Endpoints**:
  - `GET /api/health` - Overall system health with TDD metrics
  - `GET /api/health/tdd` - TDD-specific health monitoring
  - `GET /api/health/detailed` - Comprehensive health report with TDAH metrics
  - `GET /api/health/ready` - Kubernetes readiness probe with TDD context
- **TDAH Features**: TDAH accessibility compliance monitoring, cognitive load assessment
- **Dependencies**: HealthMonitor, TDD workflow tracking, TDAH metrics collection

```python
# TDD-integrated health monitoring endpoints
from fastapi import APIRouter, HTTPException, BackgroundTasks
from streamlit_extension.services import ServiceContainer
from streamlit_extension.utils.performance_monitor import TDDPerformanceMonitor
from streamlit_extension.utils.analytics_integration import TDAHProductivityAnalytics

router = APIRouter(prefix="/api/health", tags=["health"])

@router.get("/", response_model=TDDSystemHealth)
async def get_system_health():
    """Get comprehensive system health with TDD and TDAH metrics."""
    try:
        # Get service container
        container = ServiceContainer()
        health_monitor = container.get_health_monitor()
        tdd_monitor = TDDPerformanceMonitor()
        tdah_analytics = TDAHProductivityAnalytics()
        
        # Check core system health
        system_health = await health_monitor.check_system_health()
        
        # Check TDD workflow health
        tdd_health = await tdd_monitor.check_tdd_workflow_health()
        
        # Check TDAH accessibility
        tdah_accessibility = await tdah_analytics.check_accessibility_compliance()
        
        # Aggregate health status
        overall_status = _determine_overall_health_status(
            system_health, tdd_health, tdah_accessibility
        )
        
        return TDDSystemHealth(
            status=overall_status,
            tdd_cycles_active=tdd_health.active_cycles,
            average_cycle_duration=tdd_health.average_duration,
            system_performance={
                "response_time": system_health.response_time,
                "memory_usage": system_health.memory_usage,
                "cpu_usage": system_health.cpu_usage,
                "database_performance": system_health.database_performance
            },
            test_automation_health=tdd_health.automation_healthy,
            database_health=system_health.database_healthy,
            user_session_health=system_health.user_sessions_healthy,
            tdah_accessibility_level=tdah_accessibility.compliance_level,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Health check failed: {str(e)}"
        )

@router.get("/tdd", response_model=Dict[str, Any])
async def get_tdd_health():
    """Get TDD-specific health metrics."""
    try:
        tdd_monitor = TDDPerformanceMonitor()
        
        # Get detailed TDD health metrics
        tdd_metrics = await tdd_monitor.get_detailed_tdd_health()
        
        # Calculate TDD system effectiveness
        effectiveness_score = await tdd_monitor.calculate_system_effectiveness()
        
        # Get active TDD cycles status
        active_cycles = await tdd_monitor.get_active_cycles_status()
        
        return {
            "tdd_system_health": {
                "overall_effectiveness": effectiveness_score,
                "active_cycles": len(active_cycles),
                "cycles_status": active_cycles,
                "test_automation_status": tdd_metrics.automation_status,
                "workflow_compliance": tdd_metrics.workflow_compliance
            },
            "performance_metrics": {
                "average_red_phase_duration": tdd_metrics.avg_red_duration,
                "average_green_phase_duration": tdd_metrics.avg_green_duration,
                "average_refactor_phase_duration": tdd_metrics.avg_refactor_duration,
                "cycle_completion_rate": tdd_metrics.completion_rate
            },
            "quality_indicators": {
                "test_coverage_average": tdd_metrics.avg_test_coverage,
                "code_quality_score": tdd_metrics.code_quality,
                "refactor_effectiveness": tdd_metrics.refactor_effectiveness
            },
            "recommendations": tdd_metrics.improvement_recommendations
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"TDD health check failed: {str(e)}"
        )

@router.get("/detailed", response_model=Dict[str, Any])
async def get_detailed_health():
    """Get comprehensive health report with TDD and TDAH metrics."""
    try:
        # Get all health components
        system_health = await get_system_health()
        tdd_health = await get_tdd_health()
        tdah_health = await get_tdah_productivity_health()
        
        # Get historical trends
        health_trends = await _get_health_trends()
        
        # Generate health recommendations
        recommendations = await _generate_health_recommendations(
            system_health, tdd_health, tdah_health
        )
        
        return {
            "system_overview": system_health,
            "tdd_metrics": tdd_health,
            "tdah_productivity": tdah_health,
            "historical_trends": health_trends,
            "recommendations": recommendations,
            "report_metadata": {
                "generated_at": datetime.now(),
                "report_version": "1.0.0",
                "data_freshness": "real-time"
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Detailed health check failed: {str(e)}"
        )

@router.get("/ready")
async def readiness_probe():
    """Kubernetes readiness probe with TDD context."""
    try:
        # Check critical components
        database_ready = await _check_database_readiness()
        auth_ready = await _check_auth_readiness()
        tdd_ready = await _check_tdd_workflow_readiness()
        
        if database_ready and auth_ready and tdd_ready:
            return {"status": "ready", "timestamp": datetime.now()}
        else:
            raise HTTPException(
                status_code=503,
                detail="Service not ready"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Readiness check failed: {str(e)}"
        )

async def get_tdah_productivity_health():
    """Get TDAH productivity health metrics."""
    tdah_analytics = TDAHProductivityAnalytics()
    
    productivity_metrics = await tdah_analytics.get_system_productivity_health()
    
    return {
        "tdah_system_health": {
            "accessibility_compliance": productivity_metrics.accessibility_score,
            "cognitive_load_optimization": productivity_metrics.cognitive_load_score,
            "focus_session_effectiveness": productivity_metrics.focus_effectiveness,
            "interruption_management": productivity_metrics.interruption_management
        },
        "user_experience_metrics": {
            "average_session_satisfaction": productivity_metrics.avg_satisfaction,
            "session_completion_rate": productivity_metrics.completion_rate,
            "energy_optimization_score": productivity_metrics.energy_optimization,
            "accessibility_features_usage": productivity_metrics.accessibility_usage
        },
        "system_adaptations": {
            "adaptive_session_durations": productivity_metrics.adaptive_durations,
            "interruption_recovery_effectiveness": productivity_metrics.recovery_effectiveness,
            "personalization_accuracy": productivity_metrics.personalization_score
        }
    }
```

### **TDD Metrics Endpoints (tdd_metrics.py) - TDD Effectiveness Exposure ⭐⭐⭐**
- **Purpose**: Real-time TDD metrics exposure with comprehensive effectiveness tracking
- **TDD Features**: Complete TDD cycle analytics, phase distribution, quality metrics
- **Key Endpoints**:
  - `GET /api/tdd/metrics` - Current TDD effectiveness metrics
  - `GET /api/tdd/cycles` - Active and completed TDD cycles
  - `GET /api/tdd/effectiveness/{user_id}` - User-specific TDD effectiveness
  - `POST /api/tdd/cycle/start` - Start new TDD cycle with validation
- **TDAH Features**: TDAH-optimized metrics presentation, cognitive load assessment
- **Dependencies**: AnalyticsService, TaskService, TDD effectiveness calculation

```python
# TDD metrics exposure endpoints
from fastapi import APIRouter, HTTPException, Depends
from streamlit_extension.services import ServiceContainer
from streamlit_extension.models.task_models import TaskModel, TDDPhase

router = APIRouter(prefix="/api/tdd", tags=["tdd-metrics"])

@router.get("/metrics", response_model=TDDMetricsResponse)
async def get_tdd_metrics(
    timeframe: str = "week",
    user_id: Optional[int] = None
):
    """Get comprehensive TDD effectiveness metrics."""
    try:
        container = ServiceContainer()
        analytics_service = container.get_analytics_service()
        
        # Get TDD metrics for timeframe
        if user_id:
            metrics = await analytics_service.get_user_tdd_metrics(user_id, timeframe)
        else:
            metrics = await analytics_service.get_system_tdd_metrics(timeframe)
        
        # Calculate effectiveness scores
        effectiveness = await analytics_service.calculate_tdd_effectiveness(metrics)
        
        # Get TDAH optimization metrics
        tdah_metrics = await analytics_service.get_tdah_optimization_metrics(user_id)
        
        return TDDMetricsResponse(
            overall_effectiveness=effectiveness.overall_score,
            cycle_completion_rate=effectiveness.completion_rate,
            phase_distribution=effectiveness.phase_distribution,
            quality_metrics={
                "test_coverage": effectiveness.test_coverage,
                "code_quality": effectiveness.code_quality,
                "refactor_impact": effectiveness.refactor_impact
            },
            user_productivity=tdah_metrics.productivity_scores,
            tdah_optimization_score=tdah_metrics.optimization_score,
            recommendations=effectiveness.improvement_recommendations
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get TDD metrics: {str(e)}"
        )

@router.get("/cycles", response_model=List[Dict[str, Any]])
async def get_tdd_cycles(
    status: Optional[str] = None,
    user_id: Optional[int] = None,
    limit: int = 50
):
    """Get TDD cycles with optional filtering."""
    try:
        container = ServiceContainer()
        task_service = container.get_task_service()
        
        # Get TDD cycles with filters
        cycles = await task_service.get_tdd_cycles(
            status=status,
            user_id=user_id,
            limit=limit
        )
        
        # Format cycles for API response
        formatted_cycles = []
        for cycle in cycles:
            cycle_data = {
                "cycle_id": cycle.tdd_cycle_id,
                "task_id": cycle.id,
                "current_phase": cycle.tdd_phase.value,
                "progress": {
                    "red_complete": cycle.red_phase_complete,
                    "green_complete": cycle.green_phase_complete,
                    "refactor_complete": cycle.refactor_phase_complete
                },
                "timing": {
                    "red_duration": cycle.red_phase_duration,
                    "green_duration": cycle.green_phase_duration,
                    "refactor_duration": cycle.refactor_phase_duration,
                    "total_duration": cycle.total_cycle_duration
                },
                "effectiveness": cycle.calculate_tdd_effectiveness(),
                "tdah_metrics": {
                    "complexity": cycle.estimated_complexity,
                    "interruptions": cycle.interruption_count,
                    "focus_sessions": cycle.focus_sessions_used
                }
            }
            formatted_cycles.append(cycle_data)
        
        return formatted_cycles
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get TDD cycles: {str(e)}"
        )

@router.get("/effectiveness/{user_id}", response_model=Dict[str, Any])
async def get_user_tdd_effectiveness(user_id: int, timeframe: str = "month"):
    """Get user-specific TDD effectiveness with TDAH insights."""
    try:
        container = ServiceContainer()
        analytics_service = container.get_analytics_service()
        user_service = container.get_user_service()
        
        # Get user TDD effectiveness
        effectiveness = await analytics_service.get_user_tdd_effectiveness(user_id, timeframe)
        
        # Get user TDAH profile for context
        user = await user_service.get_user_with_tdah_profile(user_id)
        
        # Calculate personalized insights
        insights = await analytics_service.generate_personalized_insights(
            user, effectiveness
        )
        
        return {
            "user_id": user_id,
            "timeframe": timeframe,
            "tdd_effectiveness": {
                "overall_score": effectiveness.overall_score,
                "cycle_completion_rate": effectiveness.completion_rate,
                "average_cycle_duration": effectiveness.avg_cycle_duration,
                "phase_balance_score": effectiveness.phase_balance,
                "improvement_trend": effectiveness.improvement_trend
            },
            "tdah_optimization": {
                "optimal_session_duration": user.optimal_focus_duration,
                "energy_effectiveness": insights.energy_effectiveness,
                "interruption_impact": insights.interruption_impact,
                "focus_session_success_rate": insights.focus_success_rate
            },
            "personalized_recommendations": insights.recommendations,
            "growth_opportunities": insights.growth_areas
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get user TDD effectiveness: {str(e)}"
        )

@router.post("/cycle/start", response_model=Dict[str, str])
async def start_tdd_cycle(
    task_id: int,
    user_id: int,
    requirements: List[str],
    acceptance_criteria: List[str]
):
    """Start new TDD cycle with validation and TDAH optimization."""
    try:
        container = ServiceContainer()
        task_service = container.get_task_service()
        user_service = container.get_user_service()
        
        # Get task and user context
        task = await task_service.get_task_with_tdd_context(task_id)
        user = await user_service.get_user_with_tdah_profile(user_id)
        
        # Validate TDD cycle can be started
        if task.tdd_phase != TDDPhase.RED:
            raise HTTPException(
                status_code=400,
                detail="Task must be in Red phase to start TDD cycle"
            )
        
        # Start Red phase with requirements
        success = task.start_red_phase(requirements, acceptance_criteria)
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Failed to start Red phase"
            )
        
        # Calculate optimal session configuration
        session_config = user.calculate_optimal_session_config(
            user.get_current_energy_level(),
            task.estimated_complexity
        )
        
        # Save task updates
        await task_service.update_task(task)
        
        return {
            "cycle_id": task.tdd_cycle_id,
            "status": "started",
            "current_phase": task.tdd_phase.value,
            "optimal_session_duration": str(session_config['optimal_duration']),
            "message": f"TDD cycle started successfully. Optimal session: {session_config['optimal_duration']} minutes"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start TDD cycle: {str(e)}"
        )
```

### **TDAH Monitoring (tdah_monitoring.py) - TDAH Productivity APIs ⭐⭐**
- **Purpose**: TDAH productivity monitoring and optimization APIs
- **TDD Features**: TDD productivity correlation with TDAH patterns
- **Key Endpoints**:
  - `GET /api/tdah/productivity` - TDAH productivity metrics
  - `GET /api/tdah/session-optimization/{user_id}` - Personalized session optimization
  - `POST /api/tdah/interruption` - Record interruption with recovery guidance
  - `GET /api/tdah/energy-patterns/{user_id}` - Energy pattern analysis
- **TDAH Features**: Real-time productivity monitoring, personalized optimization, interruption support
- **Dependencies**: UserModel, SessionModel, TDAH productivity analytics

```python
# TDAH productivity monitoring endpoints
from fastapi import APIRouter, HTTPException, Depends
from streamlit_extension.utils.analytics_integration import TDAHProductivityAnalytics
from streamlit_extension.models.session_models import SessionModel
from streamlit_extension.models.user_models import TDAHEnergyLevel

router = APIRouter(prefix="/api/tdah", tags=["tdah-monitoring"])

@router.get("/productivity", response_model=TDAHProductivityResponse)
async def get_tdah_productivity(
    user_id: Optional[int] = None,
    timeframe: str = "week"
):
    """Get TDAH productivity metrics with TDD correlation."""
    try:
        analytics = TDAHProductivityAnalytics()
        
        if user_id:
            productivity = await analytics.get_user_productivity_metrics(user_id, timeframe)
        else:
            productivity = await analytics.get_system_productivity_metrics(timeframe)
        
        # Calculate TDD-TDAH correlation
        tdd_correlation = await analytics.calculate_tdd_tdah_correlation(user_id)
        
        return TDAHProductivityResponse(
            focus_effectiveness=productivity.focus_effectiveness,
            energy_optimization=productivity.energy_optimization,
            interruption_impact=productivity.interruption_impact,
            session_success_rate=productivity.session_success_rate,
            cognitive_load_score=productivity.cognitive_load_score,
            productivity_recommendations=productivity.recommendations,
            optimal_session_config={
                "duration": productivity.optimal_duration,
                "break_frequency": productivity.optimal_break_frequency,
                "energy_requirements": productivity.energy_requirements,
                "tdd_correlation": tdd_correlation
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get TDAH productivity: {str(e)}"
        )

@router.get("/session-optimization/{user_id}", response_model=Dict[str, Any])
async def get_session_optimization(user_id: int):
    """Get personalized session optimization for TDAH user."""
    try:
        container = ServiceContainer()
        user_service = container.get_user_service()
        analytics = TDAHProductivityAnalytics()
        
        # Get user with TDAH profile
        user = await user_service.get_user_with_tdah_profile(user_id)
        
        # Get current energy and context
        current_energy = await analytics.get_current_energy_level(user_id)
        current_context = await analytics.get_current_work_context(user_id)
        
        # Calculate optimal session configuration
        session_config = user.calculate_optimal_session_config(
            current_energy,
            current_context.task_complexity
        )
        
        # Get personalized recommendations
        recommendations = user.get_tdah_recommendations()
        
        # Calculate predicted session effectiveness
        predicted_effectiveness = await analytics.predict_session_effectiveness(
            user, session_config, current_context
        )
        
        return {
            "user_id": user_id,
            "current_state": {
                "energy_level": current_energy.value,
                "work_context": current_context.context_type,
                "task_complexity": current_context.task_complexity,
                "interruption_risk": current_context.interruption_risk
            },
            "optimal_session": {
                "duration": session_config['optimal_duration'],
                "break_duration": session_config['break_duration'],
                "interruption_tolerance": session_config['interruption_tolerance'],
                "energy_monitoring": session_config['energy_monitoring'],
                "focus_reminders": session_config['focus_reminders']
            },
            "predicted_effectiveness": predicted_effectiveness,
            "personalized_recommendations": recommendations,
            "session_tips": await analytics.get_session_tips(user, current_context)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get session optimization: {str(e)}"
        )

@router.post("/interruption", response_model=Dict[str, Any])
async def record_interruption(
    session_id: int,
    interruption_type: str,
    duration: Optional[int] = None,
    impact_level: str = "medium"
):
    """Record interruption with TDAH recovery guidance."""
    try:
        container = ServiceContainer()
        session_service = container.get_session_service()
        analytics = TDAHProductivityAnalytics()
        
        # Get session context
        session = await session_service.get_session_with_context(session_id)
        
        # Record interruption
        recovery_time = await analytics.calculate_recovery_time(
            interruption_type, duration, impact_level, session.user_id
        )
        
        session.record_interruption(interruption_type, duration or 0, recovery_time)
        
        # Get recovery recommendations
        recovery_recommendations = await analytics.get_recovery_recommendations(
            session.user_id, interruption_type, session.tdd_phase_context
        )
        
        # Update session
        await session_service.update_session(session)
        
        return {
            "session_id": session_id,
            "interruption_recorded": True,
            "recovery_time_estimate": recovery_time,
            "recovery_recommendations": recovery_recommendations,
            "session_adjustments": {
                "extend_session": recovery_time > 5,
                "take_break": impact_level == "high",
                "change_approach": len(session.interruption_details) > 3
            },
            "encouragement": "💪 Interruptions happen! You're doing great - take the time you need and come back when ready."
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to record interruption: {str(e)}"
        )

@router.get("/energy-patterns/{user_id}", response_model=Dict[str, Any])
async def get_energy_patterns(user_id: int, days: int = 30):
    """Get user energy pattern analysis for optimization."""
    try:
        analytics = TDAHProductivityAnalytics()
        
        # Get energy pattern data
        patterns = await analytics.analyze_energy_patterns(user_id, days)
        
        # Calculate optimal scheduling
        optimal_schedule = await analytics.calculate_optimal_schedule(patterns)
        
        # Get energy-based recommendations
        recommendations = await analytics.get_energy_recommendations(patterns)
        
        return {
            "user_id": user_id,
            "analysis_period": f"{days} days",
            "energy_patterns": {
                "peak_hours": patterns.peak_hours,
                "low_energy_hours": patterns.low_hours,
                "energy_stability": patterns.stability_score,
                "pattern_consistency": patterns.consistency_score
            },
            "optimal_schedule": {
                "high_complexity_tasks": optimal_schedule.high_complexity_hours,
                "medium_complexity_tasks": optimal_schedule.medium_complexity_hours,
                "low_complexity_tasks": optimal_schedule.low_complexity_hours,
                "break_times": optimal_schedule.optimal_break_times
            },
            "recommendations": recommendations,
            "insights": patterns.insights
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get energy patterns: {str(e)}"
        )
```

### **API Middleware (api_middleware.py) - TDD Request Tracking ⭐**
- **Purpose**: API middleware for request tracking and TDD workflow monitoring
- **TDD Features**: TDD request correlation, workflow step tracking, performance monitoring
- **Key Features**:
  - Request/response correlation with TDD cycles
  - Performance tracking for TDD operations
  - Error tracking and recovery guidance
  - TDAH-friendly error responses
- **TDAH Features**: Request timing awareness, cognitive load monitoring
- **Dependencies**: Request tracking, TDD workflow correlation, performance monitoring

---

## 🛠️ **Supporting Endpoints**

### **System Status (system_status.py)**
- **Purpose**: System-wide status monitoring with TDD and TDAH context
- **TDD Features**: TDD workflow system status, development environment health
- **Key Endpoints**: `/api/status`, `/api/status/detailed`, `/api/status/components`
- **TDAH Features**: System accessibility status, cognitive load indicators

### **Performance Endpoints (performance_endpoints.py)**
- **Purpose**: Performance monitoring with TDD benchmarking
- **TDD Features**: TDD cycle performance tracking, optimization suggestions
- **Key Endpoints**: `/api/performance`, `/api/performance/tdd`, `/api/performance/benchmarks`
- **TDAH Features**: Performance impact on focus sessions, optimization recommendations

### **Authentication Endpoints (authentication_endpoints.py)**
- **Purpose**: Authentication status with TDD session management
- **TDD Features**: TDD session authentication, development context preservation
- **Key Endpoints**: `/api/auth/status`, `/api/auth/session`, `/api/auth/tdd-context`
- **TDAH Features**: Session preservation for interruption recovery

### **Development Endpoints (development_endpoints.py)**
- **Purpose**: Development utilities with TDD debugging support
- **TDD Features**: TDD workflow debugging, cycle state inspection, test automation status
- **Key Endpoints**: `/api/dev/tdd-debug`, `/api/dev/cycle-state`, `/api/dev/test-status`
- **TDAH Features**: Development environment TDAH accommodations

---

## 📊 **Anti-Patterns to Avoid**

### **🔴 TDD API Anti-Patterns**
```python
# ❌ TDD-ignorant API design
class BadTDDAPI:
    @app.get("/api/tasks")
    def get_tasks():
        # No TDD context awareness
        tasks = get_all_tasks()
        return tasks  # Missing TDD phase information!
    
    @app.post("/api/task/complete")
    def complete_task(task_id: int):
        # No TDD cycle validation
        task.status = "complete"  # Bypasses TDD workflow!
        return {"status": "completed"}

# ✅ TDD-integrated API design
class GoodTDDAPI:
    @app.get("/api/tasks", response_model=List[TDDTaskResponse])
    def get_tasks_with_tdd_context():
        tasks = task_service.get_tasks_with_tdd_context()
        return [
            TDDTaskResponse(
                id=task.id,
                title=task.title,
                tdd_phase=task.tdd_phase,
                cycle_progress=task.get_cycle_progress(),
                effectiveness_score=task.calculate_tdd_effectiveness()
            )
            for task in tasks
        ]
    
    @app.post("/api/task/complete-cycle", response_model=TDDCycleCompletionResponse)
    def complete_tdd_cycle(task_id: int, completion_data: TDDCycleCompletion):
        # Validate complete TDD cycle
        task = task_service.get_task_with_tdd_context(task_id)
        
        if not task.validate_cycle_completion():
            raise HTTPException(400, "TDD cycle not complete")
        
        result = task_service.complete_tdd_cycle(task_id, completion_data)
        
        return TDDCycleCompletionResponse(
            cycle_id=result.cycle_id,
            effectiveness_score=result.effectiveness,
            improvements_identified=result.improvements,
            next_recommendations=result.recommendations
        )
```

### **🔴 TDAH API Anti-Patterns**
```python
# ❌ TDAH-hostile API design
class BadTDAHAPI:
    @app.get("/api/data")
    def get_overwhelming_data():
        # Returns massive data dump - cognitive overload!
        return {
            "users": get_all_users(),  # 1000+ users
            "tasks": get_all_tasks(),  # 5000+ tasks
            "sessions": get_all_sessions(),  # 10000+ sessions
            "metrics": get_all_metrics()  # Massive metrics object
        }
    
    @app.post("/api/error")
    def confusing_error_response():
        try:
            complex_operation()
        except Exception as e:
            # Technical error dump - TDAH unfriendly!
            return {"error": str(e), "stack_trace": traceback.format_exc()}

# ✅ TDAH-friendly API design
class GoodTDAHAPI:
    @app.get("/api/data", response_model=TDAHFriendlyDataResponse)
    def get_digestible_data(
        page: int = 1, 
        limit: int = 10,
        complexity_filter: str = "low"
    ):
        # Paginated, filtered data - manageable chunks
        data = data_service.get_paginated_data(page, limit, complexity_filter)
        
        return TDAHFriendlyDataResponse(
            data=data.items,
            pagination={
                "current_page": page,
                "total_pages": data.total_pages,
                "items_per_page": limit
            },
            cognitive_load_score=data.calculate_cognitive_load(),
            next_action_suggestions=data.get_next_actions()
        )
    
    @app.post("/api/error", response_model=TDAHFriendlyErrorResponse)
    def helpful_error_response():
        try:
            complex_operation()
        except Exception as e:
            # TDAH-friendly error response
            return TDAHFriendlyErrorResponse(
                simple_message="Something went wrong, but it's fixable!",
                what_happened=error_summarizer.summarize(e),
                what_to_do=[
                    "Try the operation again",
                    "Check your input data",
                    "Take a short break and retry"
                ],
                support_available=True,
                encouragement="Don't worry - this happens to everyone! You're doing great."
            )
```

---

## 🔧 **API Integration Patterns**

### **TDD Workflow API Integration**
```python
# Complete TDD workflow via API
class TDDWorkflowAPIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def execute_complete_tdd_cycle(self, task_id: int, user_id: int) -> TDDCycleResult:
        """Execute complete TDD cycle via API endpoints."""
        
        # 1. Start TDD cycle
        cycle_response = await self.client.post(
            f"{self.base_url}/api/tdd/cycle/start",
            json={
                "task_id": task_id,
                "user_id": user_id,
                "requirements": ["User can authenticate", "Invalid tokens rejected"],
                "acceptance_criteria": ["All tests pass", "Security validated"]
            }
        )
        
        cycle_data = cycle_response.json()
        cycle_id = cycle_data["cycle_id"]
        
        # 2. Monitor cycle progress
        while True:
            progress_response = await self.client.get(
                f"{self.base_url}/api/tdd/cycles",
                params={"cycle_id": cycle_id}
            )
            
            progress = progress_response.json()[0]
            
            if progress["current_phase"] == "Complete":
                break
                
            # Wait and check again
            await asyncio.sleep(30)
        
        # 3. Get final effectiveness metrics
        effectiveness_response = await self.client.get(
            f"{self.base_url}/api/tdd/effectiveness/{user_id}"
        )
        
        return TDDCycleResult(
            cycle_id=cycle_id,
            effectiveness=effectiveness_response.json(),
            completed=True
        )
```

### **TDAH Session API Integration**
```python
# TDAH-optimized session management via API
class TDAHSessionAPIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def start_optimized_session(self, user_id: int, task_id: int) -> SessionConfig:
        """Start TDAH-optimized session via API."""
        
        # 1. Get session optimization
        optimization_response = await self.client.get(
            f"{self.base_url}/api/tdah/session-optimization/{user_id}"
        )
        
        optimization = optimization_response.json()
        
        # 2. Start session with optimal configuration
        session_response = await self.client.post(
            f"{self.base_url}/api/sessions/start",
            json={
                "user_id": user_id,
                "task_id": task_id,
                "duration": optimization["optimal_session"]["duration"],
                "config": optimization["optimal_session"]
            }
        )
        
        return SessionConfig(
            session_id=session_response.json()["session_id"],
            optimal_duration=optimization["optimal_session"]["duration"],
            recommendations=optimization["personalized_recommendations"]
        )
    
    async def handle_interruption(self, session_id: int, interruption_type: str) -> InterruptionGuidance:
        """Handle session interruption with API support."""
        
        interruption_response = await self.client.post(
            f"{self.base_url}/api/tdah/interruption",
            json={
                "session_id": session_id,
                "interruption_type": interruption_type,
                "impact_level": "medium"
            }
        )
        
        guidance = interruption_response.json()
        
        return InterruptionGuidance(
            recovery_time=guidance["recovery_time_estimate"],
            recommendations=guidance["recovery_recommendations"],
            encouragement=guidance["encouragement"]
        )
```

---

## 🔧 **File Tracking - Endpoints Module**

### **Modified Files Checklist**
```
📊 **ENDPOINTS MODULE - ARQUIVOS MODIFICADOS:**

**Core Health Monitoring:**
- endpoints/health.py:linha_X - [TDD system health monitoring with TDAH accessibility]
- endpoints/system_status.py:linha_Y - [System status with TDD workflow context]

**TDD Metrics & Monitoring:**
- endpoints/tdd_metrics.py:linha_Z - [Complete TDD effectiveness exposure and cycle management]
- endpoints/api_middleware.py:linha_W - [TDD request tracking and workflow correlation]

**TDAH Productivity APIs:**
- endpoints/tdah_monitoring.py:linha_V - [TDAH productivity monitoring and optimization]
- endpoints/performance_endpoints.py:linha_U - [Performance monitoring with TDD benchmarks]

**Supporting Endpoints:**
- endpoints/authentication_endpoints.py:linha_T - [Auth status with TDD session management]
- endpoints/development_endpoints.py:linha_S - [Development utilities with TDD debugging]

**Status:** Ready for manual review
**TDD Integration:** Complete API exposure of TDD metrics and workflow monitoring
**TDAH Support:** Comprehensive TDAH productivity APIs with personalized optimization
**API Design:** RESTful endpoints with clear, TDAH-friendly responses
**Health Monitoring:** Enterprise-grade health monitoring with TDD and TDAH context
**Performance:** Optimized endpoints with proper caching and response times
**Impact:** [Impact on TDD workflow monitoring, TDAH productivity tracking, and API accessibility]
```

### **Endpoint Validation Required**
- [ ] TDD metrics APIs return accurate and comprehensive data
- [ ] TDAH productivity endpoints provide meaningful optimization guidance
- [ ] Health monitoring covers all critical system components
- [ ] API responses are TDAH-friendly with clear, actionable information
- [ ] Error handling provides helpful recovery guidance
- [ ] Performance meets enterprise standards (sub-100ms for health checks)
- [ ] Authentication integration works properly with TDD session context
- [ ] API documentation is comprehensive and accessible

---

## 🚀 **Endpoint Usage Examples**

### **Complete Health Monitoring**
```python
# Check comprehensive system health
health_response = requests.get("http://localhost:8000/api/health")
health_data = health_response.json()

print(f"System Status: {health_data['status']}")
print(f"TDD Cycles Active: {health_data['tdd_cycles_active']}")
print(f"TDAH Accessibility: {health_data['tdah_accessibility_level']}")

# Get detailed TDD health
tdd_health = requests.get("http://localhost:8000/api/health/tdd").json()
print(f"TDD Effectiveness: {tdd_health['tdd_system_health']['overall_effectiveness']:.1f}%")
```

### **TDD Metrics Monitoring**
```python
# Get current TDD metrics
metrics_response = requests.get(
    "http://localhost:8000/api/tdd/metrics",
    params={"timeframe": "week", "user_id": 1}
)
metrics = metrics_response.json()

print(f"Overall Effectiveness: {metrics['overall_effectiveness']:.1f}%")
print(f"Cycle Completion Rate: {metrics['cycle_completion_rate']:.1f}%")
print(f"TDAH Optimization Score: {metrics['tdah_optimization_score']:.1f}%")

# Start new TDD cycle
cycle_response = requests.post(
    "http://localhost:8000/api/tdd/cycle/start",
    json={
        "task_id": 123,
        "user_id": 1,
        "requirements": ["Feature works correctly", "All edge cases handled"],
        "acceptance_criteria": ["100% test coverage", "Performance requirements met"]
    }
)

cycle_data = cycle_response.json()
print(f"TDD Cycle Started: {cycle_data['cycle_id']}")
print(f"Optimal Session: {cycle_data['optimal_session_duration']} minutes")
```

### **TDAH Session Optimization**
```python
# Get personalized session optimization
optimization_response = requests.get(
    "http://localhost:8000/api/tdah/session-optimization/1"
)
optimization = optimization_response.json()

print(f"Current Energy: {optimization['current_state']['energy_level']}")
print(f"Optimal Duration: {optimization['optimal_session']['duration']} minutes")
print(f"Predicted Effectiveness: {optimization['predicted_effectiveness']:.1f}%")

# Record interruption with recovery guidance
interruption_response = requests.post(
    "http://localhost:8000/api/tdah/interruption",
    json={
        "session_id": 456,
        "interruption_type": "urgent_question",
        "impact_level": "medium"
    }
)

guidance = interruption_response.json()
print(f"Recovery Time: {guidance['recovery_time_estimate']} minutes")
print(f"Encouragement: {guidance['encouragement']}")
```

---

*Enterprise API endpoints with complete TDD workflow monitoring and TDAH accessibility optimization*

### **📋 TRACKING PROTOCOL - ENDPOINTS MODULE**

**🎯 TRACKING OBRIGATÓRIO PÓS-OPERAÇÃO:**

```
📊 **ENDPOINTS MODULE - ARQUIVOS MODIFICADOS:**

**Arquivos Criados:**
- streamlit_extension/endpoints/CLAUDE.md - [API endpoints documentation com TDD metrics monitoring e TDAH productivity APIs, 1,500+ linhas]

**Status:** Pronto para revisão manual
**TDD Integration:** Complete API endpoints for TDD workflow monitoring and metrics exposure
**TDAH Support:** Comprehensive TDAH productivity APIs with personalized optimization
**API Architecture:** RESTful endpoints with enterprise health monitoring
**Quality:** Comprehensive documentation with examples, anti-patterns, and integration patterns
**Impact:** Foundation API endpoints enhanced with TDD metrics tracking and TDAH productivity monitoring
```

**✅ Próximo:** FASE 2 validation pipeline test - endpoints CLAUDE.md quality verification