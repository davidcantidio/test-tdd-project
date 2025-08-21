#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧠 MetaAgent - Intelligent Agent Coordination System

Advanced agent orchestration that determines which specialized AI agents
should be activated for each task based on file analysis, complexity assessment,
and resource optimization.

This MetaAgent acts as the central coordinator for:
- IntelligentCodeAgent: Semantic code analysis
- IntelligentRefactoringEngine: Code improvement and optimization  
- TDDIntelligentWorkflowAgent: TDD process optimization
- GodCodeRefactoringAgent: God code pattern detection and refactoring

The MetaAgent uses intelligent decision trees, resource optimization,
and contextual analysis to maximize audit efficiency and effectiveness.
"""

import ast
import logging
import json
import time
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

# File coordination for safe modifications
from .file_coordination_manager import (
    FileCoordinationManager, 
    get_coordination_manager,
    safe_file_modification,
    LockType
)

# Agent imports
try:
    from audit_system.agents.intelligent_code_agent import (
        IntelligentCodeAgent, AnalysisDepth, SemanticMode
    )
    from audit_system.agents.intelligent_refactoring_engine import (
        IntelligentRefactoringEngine
    )
    from audit_system.agents.tdd_intelligent_workflow_agent import (
        TDDIntelligentWorkflowAgent, TDDPhase, TDAHEnergyLevel
    )
    from audit_system.agents.god_code_refactoring_agent import (
        GodCodeRefactoringAgent, run_god_code_analysis
    )
    AGENTS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Some agents not available: {e}")
    AGENTS_AVAILABLE = False

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Types of analysis tasks that can be performed."""
    SEMANTIC_ANALYSIS = "semantic_analysis"
    CODE_REFACTORING = "code_refactoring"  
    TDD_OPTIMIZATION = "tdd_optimization"
    GOD_CODE_DETECTION = "god_code_detection"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    SECURITY_ANALYSIS = "security_analysis"
    ARCHITECTURE_REVIEW = "architecture_review"
    COMPREHENSIVE_AUDIT = "comprehensive_audit"


class AgentType(Enum):
    """Available specialized agents."""
    INTELLIGENT_CODE_AGENT = "intelligent_code_agent"
    REFACTORING_ENGINE = "refactoring_engine"
    TDD_WORKFLOW_AGENT = "tdd_workflow_agent"
    GOD_CODE_AGENT = "god_code_agent"


class Priority(Enum):
    """Task priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FileComplexity(Enum):
    """File complexity levels for agent selection."""
    SIMPLE = "simple"      # < 100 lines, basic structure
    MODERATE = "moderate"  # 100-300 lines, some complexity
    COMPLEX = "complex"    # 300-600 lines, high complexity
    GOD_FILE = "god_file"  # > 600 lines, potential god code


@dataclass
class FileAnalysis:
    """Analysis of a file to determine agent selection."""
    file_path: str
    line_count: int
    function_count: int
    class_count: int
    ast_complexity_score: float
    file_complexity: FileComplexity
    suspected_patterns: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    file_type: str = "unknown"
    estimated_tokens: int = 0


@dataclass
class AgentRecommendation:
    """Recommendation for which agents to use."""
    agent_type: AgentType
    priority: Priority
    confidence: float  # 0-1 confidence in recommendation
    reasoning: str
    configuration: Dict[str, Any] = field(default_factory=dict)
    estimated_tokens: int = 0
    estimated_time: float = 0


@dataclass
class TaskExecution:
    """Execution plan for a specific task."""
    task_type: TaskType
    file_path: str
    agents: List[AgentRecommendation]
    execution_order: List[AgentType]
    total_estimated_tokens: int
    total_estimated_time: float
    dependencies: List[str] = field(default_factory=list)


@dataclass
class ExecutionResult:
    """Result of agent execution."""
    agent_type: AgentType
    success: bool
    execution_time: float
    tokens_used: int
    result_data: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class MetaAgent:
    """
    Intelligent agent coordination system that determines optimal
    agent selection and execution strategy for code analysis tasks.
    """
    
    def __init__(
        self,
        project_root: Path,
        token_budget: int = 32000,
        max_time_per_file: float = 300.0,  # 5 minutes max per file
        enable_tdah_features: bool = False,
        dry_run: bool = False
    ):
        """Initialize MetaAgent with configuration and resource limits."""
        self.project_root = Path(project_root)
        self.token_budget = token_budget
        self.max_time_per_file = max_time_per_file
        self.enable_tdah_features = enable_tdah_features
        self.dry_run = dry_run
        
        # Initialize file coordination manager for safe modifications
        self.coordination_manager = get_coordination_manager(str(self.project_root))
        
        # Agent instances
        self._agents = {}
        self._initialize_agents()
        
        # Decision trees and knowledge base
        self._agent_selection_rules = self._build_agent_selection_rules()
        self._file_pattern_knowledge = self._build_file_pattern_knowledge()
        self._token_estimation_models = self._build_token_estimation_models()
        
        # Execution tracking
        self.execution_history = []
        self.token_usage_stats = defaultdict(int)
        self.performance_metrics = defaultdict(list)
        
        logger.info("MetaAgent initialized for %s", self.project_root)
        logger.info("Token budget: %s, TDAH features: %s", self.token_budget, self.enable_tdah_features)
        
    def _initialize_agents(self):
        """Initialize all available specialized agents."""
        if not AGENTS_AVAILABLE:
            logger.warning("Specialized agents not available - MetaAgent running in analysis-only mode")
            return
            
        try:
            # Initialize IntelligentCodeAgent
            self._agents[AgentType.INTELLIGENT_CODE_AGENT] = IntelligentCodeAgent(
                project_root=self.project_root,
                analysis_depth=AnalysisDepth.ADVANCED,
                semantic_mode=SemanticMode.CONSERVATIVE,
                dry_run=self.dry_run
            )
            
            # Initialize IntelligentRefactoringEngine
            self._agents[AgentType.REFACTORING_ENGINE] = IntelligentRefactoringEngine(
                dry_run=self.dry_run
            )
            
            # Initialize TDDIntelligentWorkflowAgent
            self._agents[AgentType.TDD_WORKFLOW_AGENT] = TDDIntelligentWorkflowAgent(
                project_root=self.project_root,
                tdah_mode=self.enable_tdah_features,
                default_focus_minutes=25 if not self.enable_tdah_features else 15
            )
            
            # Initialize GodCodeRefactoringAgent
            self._agents[AgentType.GOD_CODE_AGENT] = GodCodeRefactoringAgent(
                dry_run=self.dry_run,
                aggressive_refactoring=False
            )
            
            logger.info("Initialized %s specialized agents", len(self._agents))
            
        except Exception as e:
            logger.error("Error initializing agents: %s", e)
            self._agents = {}
    
    def _build_agent_selection_rules(self) -> Dict[str, Any]:
        """Build intelligent decision rules for agent selection."""
        return {
            # File complexity → Agent selection
            "complexity_rules": {
                FileComplexity.SIMPLE: [
                    AgentType.INTELLIGENT_CODE_AGENT,
                    AgentType.REFACTORING_ENGINE
                ],
                FileComplexity.MODERATE: [
                    AgentType.INTELLIGENT_CODE_AGENT,
                    AgentType.REFACTORING_ENGINE,
                    AgentType.TDD_WORKFLOW_AGENT
                ],
                FileComplexity.COMPLEX: [
                    AgentType.INTELLIGENT_CODE_AGENT,
                    AgentType.REFACTORING_ENGINE,
                    AgentType.TDD_WORKFLOW_AGENT,
                    AgentType.GOD_CODE_AGENT
                ],
                FileComplexity.GOD_FILE: [
                    AgentType.GOD_CODE_AGENT,  # Primary focus
                    AgentType.INTELLIGENT_CODE_AGENT,
                    AgentType.REFACTORING_ENGINE
                ]
            },
            
            # File patterns → Specific agent preferences
            "pattern_rules": {
                "test_file": [AgentType.TDD_WORKFLOW_AGENT, AgentType.INTELLIGENT_CODE_AGENT],
                "database_file": [AgentType.INTELLIGENT_CODE_AGENT, AgentType.REFACTORING_ENGINE],
                "service_file": [AgentType.INTELLIGENT_CODE_AGENT, AgentType.REFACTORING_ENGINE, AgentType.GOD_CODE_AGENT],
                "util_file": [AgentType.REFACTORING_ENGINE, AgentType.INTELLIGENT_CODE_AGENT],
                "main_file": [AgentType.INTELLIGENT_CODE_AGENT, AgentType.GOD_CODE_AGENT],
                "config_file": [AgentType.INTELLIGENT_CODE_AGENT],
                "streamlit_file": [AgentType.INTELLIGENT_CODE_AGENT, AgentType.REFACTORING_ENGINE]
            },
            
            # Task type → Agent priorities
            "task_rules": {
                TaskType.SEMANTIC_ANALYSIS: [AgentType.INTELLIGENT_CODE_AGENT],
                TaskType.CODE_REFACTORING: [AgentType.REFACTORING_ENGINE, AgentType.INTELLIGENT_CODE_AGENT],
                TaskType.TDD_OPTIMIZATION: [AgentType.TDD_WORKFLOW_AGENT, AgentType.INTELLIGENT_CODE_AGENT],
                TaskType.GOD_CODE_DETECTION: [AgentType.GOD_CODE_AGENT],
                TaskType.PERFORMANCE_ANALYSIS: [AgentType.INTELLIGENT_CODE_AGENT, AgentType.REFACTORING_ENGINE],
                TaskType.SECURITY_ANALYSIS: [AgentType.INTELLIGENT_CODE_AGENT],
                TaskType.ARCHITECTURE_REVIEW: [AgentType.INTELLIGENT_CODE_AGENT, AgentType.GOD_CODE_AGENT],
                TaskType.COMPREHENSIVE_AUDIT: [
                    AgentType.INTELLIGENT_CODE_AGENT,
                    AgentType.REFACTORING_ENGINE,
                    AgentType.TDD_WORKFLOW_AGENT,
                    AgentType.GOD_CODE_AGENT
                ]
            }
        }
    
    def _build_file_pattern_knowledge(self) -> Dict[str, Any]:
        """Build knowledge base for file pattern recognition."""
        return {
            # File name patterns
            "filename_patterns": {
                "test": ["test_", "_test.py", "tests/"],
                "database": ["database", "db_", "_db.py", "models/", "schema"],
                "service": ["service", "_service.py", "services/"],
                "util": ["util", "utils", "helper", "common"],
                "main": ["main.py", "__main__.py", "app.py"],
                "config": ["config", "settings", "constants"],
                "streamlit": ["streamlit", "st_", "_app.py"]
            },
            
            # Import patterns that suggest file type
            "import_patterns": {
                "test_file": ["pytest", "unittest", "mock", "fixtures"],
                "database_file": ["sqlite3", "sqlalchemy", "database", "models"],
                "service_file": ["service", "repository", "dao"],
                "streamlit_file": ["streamlit", "st.", "plotly", "dash"],
                "util_file": ["typing", "collections", "itertools", "functools"]
            },
            
            # Code patterns that indicate complexity
            "complexity_indicators": {
                "god_method": ["def.*{.*\n.*{250,}"],  # Methods with 250+ lines
                "god_class": ["class.*:.*\n.*{30,}.*def"],  # Classes with 30+ methods
                "high_nesting": ["if.*:.*\n.*if.*:.*\n.*if.*:"],  # Deep nesting
                "complex_imports": ["from.*import.*,.*,.*,.*,"]  # Many imports
            }
        }
        
    def _build_token_estimation_models(self) -> Dict[str, Any]:
        """Build models for estimating token usage per agent type.
        
        REAL LLM MODELS based on comprehensive analysis requirements:
        - Small files (2 lines): ~5K-15K tokens for semantic + architectural analysis
        - Large files (1685 lines): ~40K-80K tokens for 6-layer comprehensive analysis
        - Real LLM analysis scales with complexity and analysis depth
        """
        return {
            # REAL LLM: IntelligentCodeAgent does semantic understanding + code quality
            AgentType.INTELLIGENT_CODE_AGENT: {
                "base_tokens": 8000,   # Semantic understanding baseline
                "tokens_per_line": 15,  # Scales with code complexity
                "tokens_per_function": 200,  # Function-level analysis
                "tokens_per_class": 500,  # Class-level architectural analysis
                "complexity_multiplier": 2.0  # High complexity impact for real analysis
            },
            # REAL LLM: RefactoringEngine does architectural + performance analysis
            AgentType.REFACTORING_ENGINE: {
                "base_tokens": 12000,  # Architectural analysis baseline
                "tokens_per_line": 20,  # Pattern detection scaling
                "tokens_per_function": 300,  # Refactoring opportunity analysis
                "complexity_multiplier": 2.5  # High impact for refactoring decisions
            },
            # REAL LLM: TDDWorkflowAgent does test strategy + workflow analysis
            AgentType.TDD_WORKFLOW_AGENT: {
                "base_tokens": 10000,  # TDD strategy analysis
                "tokens_per_line": 12,  # Test coverage analysis
                "tokens_per_function": 150,  # Test case analysis
                "complexity_multiplier": 1.0  # No complexity impact observed
            },
            # REAL LLM: GodCodeAgent does anti-pattern detection + complexity analysis
            AgentType.GOD_CODE_AGENT: {
                "base_tokens": 6000,  # Anti-pattern detection baseline
                "tokens_per_line": 8,  # Complexity analysis scaling
                "tokens_per_function": 100,  # Function complexity analysis
                "god_code_bonus": 5000,  # Significant analysis when god codes found
                "complexity_multiplier": 3.0  # High impact for complex anti-patterns
            }
        }
    
    def analyze_file(self, file_path: str) -> FileAnalysis:
        """
        Analyze file to determine characteristics for agent selection.
        
        Args:
            file_path: Path to file to analyze
            
        Returns:
            FileAnalysis with file characteristics and metrics
        """
        try:
            file_path_obj = Path(file_path)
            
            # Read and parse file
            with open(file_path_obj, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic metrics
            lines = content.split('\n')
            line_count = len([line for line in lines if line.strip()])
            
            # AST analysis
            try:
                tree = ast.parse(content)
                function_count = len([node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)])
                class_count = len([node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)])
                
                # Calculate AST complexity score
                complexity_score = self._calculate_ast_complexity(tree)
                
            except SyntaxError:
                logger.warning("Could not parse AST for %s", file_path)
                function_count = content.count('def ')
                class_count = content.count('class ')
                complexity_score = line_count * 0.1  # Fallback estimate
            
            # Determine file complexity
            file_complexity = self._classify_file_complexity(
                line_count, function_count, class_count, complexity_score
            )
            
            # Detect patterns and imports
            suspected_patterns = self._detect_file_patterns(file_path_obj, content)
            imports = self._extract_imports(content)
            file_type = self._classify_file_type(file_path_obj, imports, content)
            
            # Estimate tokens needed for analysis
            estimated_tokens = self._estimate_file_tokens(
                line_count, function_count, class_count, complexity_score
            )
            
            return FileAnalysis(
                file_path=file_path,
                line_count=line_count,
                function_count=function_count,
                class_count=class_count,
                ast_complexity_score=complexity_score,
                file_complexity=file_complexity,
                suspected_patterns=suspected_patterns,
                imports=imports,
                file_type=file_type,
                estimated_tokens=estimated_tokens
            )
            
        except Exception as e:
            logger.error("Error analyzing file %s: %s", file_path, e)
            return FileAnalysis(
                file_path=file_path,
                line_count=0,
                function_count=0,
                class_count=0,
                ast_complexity_score=0.0,
                file_complexity=FileComplexity.SIMPLE,
                estimated_tokens=100  # Minimal fallback estimate
            )
    
    def _calculate_ast_complexity(self, tree: ast.AST) -> float:
        """Calculate complexity score from AST analysis."""
        complexity = 0.0
        
        for node in ast.walk(tree):
            # Control flow complexity
            if isinstance(node, (ast.If, ast.While, ast.For)):
                complexity += 2.0
            elif isinstance(node, ast.Try):
                complexity += 3.0
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Function complexity based on arguments and decorators
                complexity += 1.0 + len(node.args.args) * 0.2 + len(node.decorator_list) * 0.5
            elif isinstance(node, ast.ClassDef):
                complexity += 2.0 + len(node.bases) * 0.5
            elif isinstance(node, ast.ListComp):
                complexity += 1.5
            elif isinstance(node, ast.Lambda):
                complexity += 1.0
                
        return complexity
    
    def _classify_file_complexity(
        self, line_count: int, function_count: int, class_count: int, ast_complexity: float
    ) -> FileComplexity:
        """Classify file complexity based on metrics."""
        
        # God file indicators
        if (line_count > 600 or 
            function_count > 30 or 
            class_count > 5 or 
            ast_complexity > 100):
            return FileComplexity.GOD_FILE
        
        # Complex file indicators
        elif (line_count > 300 or 
              function_count > 15 or 
              class_count > 2 or 
              ast_complexity > 50):
            return FileComplexity.COMPLEX
        
        # Moderate complexity
        elif (line_count > 100 or 
              function_count > 5 or 
              class_count > 0 or 
              ast_complexity > 20):
            return FileComplexity.MODERATE
        
        # Simple file
        else:
            return FileComplexity.SIMPLE
    
    def _detect_file_patterns(self, file_path: Path, content: str) -> List[str]:
        """Detect code patterns that suggest specific analysis needs."""
        patterns = []
        
        # File name pattern detection
        file_name = file_path.name.lower()
        for pattern_type, pattern_list in self._file_pattern_knowledge["filename_patterns"].items():
            if any(pattern in file_name or pattern in str(file_path) for pattern in pattern_list):
                patterns.append(pattern_type)
        
        # Content pattern detection
        content_lower = content.lower()
        
        # God code patterns
        if len(content.split('\n')) > 500:
            patterns.append("potential_god_file")
        
        # Long methods (rough estimate)
        method_blocks = content.split('def ')
        for block in method_blocks[1:]:  # Skip first empty block
            if len(block.split('\n')) > 50:
                patterns.append("long_method")
                break
        
        # Database patterns
        if any(keyword in content_lower for keyword in ['select ', 'insert ', 'update ', 'delete ', 'cursor']):
            patterns.append("database_operations")
        
        # Performance-critical patterns
        if any(keyword in content_lower for keyword in ['performance', 'benchmark', 'optimization', 'cache']):
            patterns.append("performance_critical")
        
        # Security patterns
        if any(keyword in content_lower for keyword in ['password', 'auth', 'security', 'crypto', 'hash']):
            patterns.append("security_critical")
        
        return patterns
    
    def _extract_imports(self, content: str) -> List[str]:
        """Extract import statements from file content."""
        imports = []
        
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('import ') or line.startswith('from '):
                # Extract module names
                if line.startswith('import '):
                    modules = line[7:].split(',')
                else:  # from ... import ...
                    if ' import ' in line:
                        module = line.split(' import ')[0][5:].strip()
                        imports.append(module)
                        continue
                
                for module in modules:
                    module = module.strip().split('.')[0]  # Get base module
                    if module and not module.startswith('.'):
                        imports.append(module)
        
        return list(set(imports))  # Remove duplicates
    
    def _classify_file_type(self, file_path: Path, imports: List[str], content: str) -> str:
        """Classify file type based on path, imports, and content."""
        
        # Check import patterns first
        for file_type, type_imports in self._file_pattern_knowledge["import_patterns"].items():
            if any(imp in imports for imp in type_imports):
                return file_type
        
        # Check filename patterns
        file_name = file_path.name.lower()
        file_path_str = str(file_path).lower()
        
        for file_type, patterns in self._file_pattern_knowledge["filename_patterns"].items():
            if any(pattern in file_name or pattern in file_path_str for pattern in patterns):
                return f"{file_type}_file"
        
        # Default classification
        if 'test' in file_path_str:
            return "test_file"
        elif file_path.suffix == '.py':
            return "python_file"
        else:
            return "unknown"
    
    def _estimate_file_tokens(
        self, line_count: int, function_count: int, class_count: int, complexity_score: float
    ) -> int:
        """Estimate total tokens needed to analyze this file with all agents."""
        
        total_tokens = 0
        
        for agent_type, model in self._token_estimation_models.items():
            agent_tokens = model["base_tokens"]
            agent_tokens += line_count * model["tokens_per_line"]
            agent_tokens += function_count * model.get("tokens_per_function", 0)
            agent_tokens += class_count * model.get("tokens_per_class", 0)
            
            # Apply complexity multiplier
            agent_tokens *= model.get("complexity_multiplier", 1.0)
            
            # Special bonuses
            if agent_type == AgentType.GOD_CODE_AGENT and (line_count > 500 or function_count > 20):
                agent_tokens += model.get("god_code_bonus", 0)
            
            total_tokens += int(agent_tokens)
        
        return total_tokens
    
    def recommend_agents(
        self, 
        file_analysis: FileAnalysis, 
        task_type: TaskType = TaskType.COMPREHENSIVE_AUDIT,
        available_tokens: Optional[int] = None
    ) -> List[AgentRecommendation]:
        """
        Recommend which agents should be used for the given file and task.
        
        Args:
            file_analysis: Analysis of the file to process
            task_type: Type of task to perform
            available_tokens: Available token budget (uses instance budget if None)
            
        Returns:
            List of agent recommendations in priority order
        """
        
        if available_tokens is None:
            available_tokens = self.token_budget
            
        recommendations = []
        
        # Get base agent list from task type
        if task_type in self._agent_selection_rules["task_rules"]:
            base_agents = self._agent_selection_rules["task_rules"][task_type]
        else:
            base_agents = [AgentType.INTELLIGENT_CODE_AGENT]  # Default fallback
        
        # Adjust based on file complexity
        complexity_agents = self._agent_selection_rules["complexity_rules"].get(
            file_analysis.file_complexity, []
        )
        
        # Adjust based on file patterns
        pattern_agents = []
        for pattern in file_analysis.suspected_patterns:
            if pattern in self._agent_selection_rules["pattern_rules"]:
                pattern_agents.extend(self._agent_selection_rules["pattern_rules"][pattern])
        
        # Combine and prioritize agents
        all_agents = list(set(base_agents + complexity_agents + pattern_agents))
        
        # Create recommendations for each agent
        for agent_type in all_agents:
            if agent_type not in self._agents:
                continue  # Skip unavailable agents
            
            priority, confidence, reasoning = self._calculate_agent_priority(
                agent_type, file_analysis, task_type
            )
            
            # Estimate tokens and time for this agent
            estimated_tokens = self._estimate_agent_tokens(agent_type, file_analysis)
            estimated_time = self._estimate_agent_time(agent_type, file_analysis)
            
            # Skip agent if it would exceed token budget
            if estimated_tokens > available_tokens:
                logger.warning(
                    "Skipping %s - estimated tokens (%s) exceed budget (%s)",
                    agent_type.value,
                    estimated_tokens,
                    available_tokens,
                )
                continue
            
            configuration = self._build_agent_configuration(agent_type, file_analysis)
            
            recommendation = AgentRecommendation(
                agent_type=agent_type,
                priority=priority,
                confidence=confidence,
                reasoning=reasoning,
                configuration=configuration,
                estimated_tokens=estimated_tokens,
                estimated_time=estimated_time
            )
            
            recommendations.append(recommendation)
        
        # Sort by priority and confidence
        recommendations.sort(key=lambda r: (
            r.priority.value,  # Priority first (critical, high, medium, low)
            -r.confidence      # Then by confidence (higher is better)
        ))
        
        return recommendations
    
    def _calculate_agent_priority(
        self, agent_type: AgentType, file_analysis: FileAnalysis, task_type: TaskType
    ) -> Tuple[Priority, float, str]:
        """Calculate priority and confidence for an agent recommendation."""
        
        confidence = 0.5  # Base confidence
        priority = Priority.MEDIUM
        reasons = []
        
        # Task type alignment
        if task_type == TaskType.COMPREHENSIVE_AUDIT:
            confidence += 0.2
            reasons.append("comprehensive audit requires multiple agents")
        elif task_type == TaskType.GOD_CODE_DETECTION and agent_type == AgentType.GOD_CODE_AGENT:
            confidence += 0.4
            priority = Priority.CRITICAL
            reasons.append("god code detection specifically requested")
        elif task_type == TaskType.TDD_OPTIMIZATION and agent_type == AgentType.TDD_WORKFLOW_AGENT:
            confidence += 0.3
            priority = Priority.HIGH
            reasons.append("TDD optimization specifically requested")
        
        # File complexity alignment
        if file_analysis.file_complexity == FileComplexity.GOD_FILE:
            if agent_type == AgentType.GOD_CODE_AGENT:
                confidence += 0.3
                priority = Priority.CRITICAL
                reasons.append("god file detected - god code agent essential")
            elif agent_type == AgentType.INTELLIGENT_CODE_AGENT:
                confidence += 0.2
                priority = Priority.HIGH
                reasons.append("god file requires deep analysis")
        
        # Pattern-based adjustments
        if "potential_god_file" in file_analysis.suspected_patterns:
            if agent_type == AgentType.GOD_CODE_AGENT:
                confidence += 0.2
                priority = Priority.HIGH
                reasons.append("potential god patterns detected")
        
        if "performance_critical" in file_analysis.suspected_patterns:
            if agent_type in [AgentType.INTELLIGENT_CODE_AGENT, AgentType.REFACTORING_ENGINE]:
                confidence += 0.15
                reasons.append("performance-critical code identified")
        
        if "security_critical" in file_analysis.suspected_patterns:
            if agent_type == AgentType.INTELLIGENT_CODE_AGENT:
                confidence += 0.2
                priority = Priority.HIGH
                reasons.append("security-critical code identified")
        
        # Test file handling
        if file_analysis.file_type == "test_file":
            if agent_type == AgentType.TDD_WORKFLOW_AGENT:
                confidence += 0.25
                priority = Priority.HIGH
                reasons.append("test file identified - TDD analysis valuable")
            else:
                confidence -= 0.1  # Lower priority for other agents on test files
                reasons.append("test file - limited benefit from general analysis")
        
        # File size considerations
        if file_analysis.line_count > 1000:
            if agent_type == AgentType.GOD_CODE_AGENT:
                confidence += 0.15
                priority = Priority.HIGH
                reasons.append("very large file - god code analysis recommended")
        
        # Cap confidence at 1.0
        confidence = min(1.0, confidence)
        
        reasoning = "; ".join(reasons) or "standard analysis recommendation"
        
        return priority, confidence, reasoning
    
    def _estimate_agent_tokens(self, agent_type: AgentType, file_analysis: FileAnalysis) -> int:
        """Estimate token usage for a specific agent on a file."""
        
        if agent_type not in self._token_estimation_models:
            return 500  # Fallback estimate
        
        model = self._token_estimation_models[agent_type]
        
        tokens = model["base_tokens"]
        tokens += file_analysis.line_count * model["tokens_per_line"]
        tokens += file_analysis.function_count * model.get("tokens_per_function", 0)
        tokens += file_analysis.class_count * model.get("tokens_per_class", 0)
        
        # Apply complexity multiplier
        tokens *= model.get("complexity_multiplier", 1.0)
        
        # Special bonuses
        if agent_type == AgentType.GOD_CODE_AGENT:
            if file_analysis.file_complexity == FileComplexity.GOD_FILE:
                tokens += model.get("god_code_bonus", 0)
        
        return int(tokens)
    
    def _estimate_agent_time(self, agent_type: AgentType, file_analysis: FileAnalysis) -> float:
        """Estimate execution time for a specific agent on a file."""
        
        # Base time estimates (in seconds)
        base_times = {
            AgentType.INTELLIGENT_CODE_AGENT: 30.0,
            AgentType.REFACTORING_ENGINE: 20.0,
            AgentType.TDD_WORKFLOW_AGENT: 15.0,
            AgentType.GOD_CODE_AGENT: 25.0
        }
        
        base_time = base_times.get(agent_type, 20.0)
        
        # Scale with file size and complexity
        complexity_multiplier = {
            FileComplexity.SIMPLE: 0.5,
            FileComplexity.MODERATE: 1.0,
            FileComplexity.COMPLEX: 2.0,
            FileComplexity.GOD_FILE: 4.0
        }.get(file_analysis.file_complexity, 1.0)
        
        return base_time * complexity_multiplier
    
    def _build_agent_configuration(
        self, agent_type: AgentType, file_analysis: FileAnalysis
    ) -> Dict[str, Any]:
        """Build configuration for specific agent based on file analysis."""
        
        config = {}
        
        if agent_type == AgentType.INTELLIGENT_CODE_AGENT:
            # Adjust analysis depth based on file complexity
            if file_analysis.file_complexity in [FileComplexity.COMPLEX, FileComplexity.GOD_FILE]:
                config["analysis_depth"] = "ADVANCED"
            else:
                config["analysis_depth"] = "BASIC"
            
            # Adjust semantic mode based on file patterns
            if "security_critical" in file_analysis.suspected_patterns:
                config["semantic_mode"] = "CONSERVATIVE"
            else:
                config["semantic_mode"] = "CONSERVATIVE"  # Default to conservative
        
        elif agent_type == AgentType.REFACTORING_ENGINE:
            # Enable specific refactoring strategies based on patterns
            strategies = []
            if "long_method" in file_analysis.suspected_patterns:
                strategies.extend([0, 3])  # Extract method, eliminate god methods
            if "database_operations" in file_analysis.suspected_patterns:
                strategies.append(4)  # Optimize database queries
            if "performance_critical" in file_analysis.suspected_patterns:
                strategies.extend([2, 4])  # Optimize strings, optimize queries
            
            config["selected_strategies"] = strategies or [0, 1, 2]  # Default strategies
        
        elif agent_type == AgentType.TDD_WORKFLOW_AGENT:
            # TDAH-specific configuration
            config["enable_tdah_features"] = self.enable_tdah_features
            config["focus_session_minutes"] = 15 if self.enable_tdah_features else 25
            
            # Phase detection for test files
            if file_analysis.file_type == "test_file":
                config["initial_phase"] = "GREEN"  # Assume existing tests
            else:
                config["initial_phase"] = "RED"  # Need to write tests
        
        elif agent_type == AgentType.GOD_CODE_AGENT:
            # Aggressive mode for confirmed god files
            if file_analysis.file_complexity == FileComplexity.GOD_FILE:
                config["aggressive_refactoring"] = False  # Stay conservative for safety
            else:
                config["aggressive_refactoring"] = False
            
            config["dry_run"] = self.dry_run
        
        return config
    
    def create_execution_plan(
        self, 
        file_path: str, 
        task_type: TaskType = TaskType.COMPREHENSIVE_AUDIT,
        available_tokens: Optional[int] = None
    ) -> TaskExecution:
        """
        Create a complete execution plan for a file analysis task.
        
        Args:
            file_path: Path to file to analyze
            task_type: Type of analysis task to perform
            available_tokens: Available token budget
            
        Returns:
            TaskExecution with complete execution plan
        """
        
        # Analyze file to understand characteristics
        file_analysis = self.analyze_file(file_path)
        
        # Get agent recommendations
        agent_recommendations = self.recommend_agents(
            file_analysis, task_type, available_tokens
        )
        
        # Determine optimal execution order
        execution_order = self._determine_execution_order(agent_recommendations)
        
        # Calculate totals
        total_tokens = sum(rec.estimated_tokens for rec in agent_recommendations)
        total_time = sum(rec.estimated_time for rec in agent_recommendations)
        
        # Identify dependencies (if any)
        dependencies = self._identify_dependencies(file_path)
        
        return TaskExecution(
            task_type=task_type,
            file_path=file_path,
            agents=agent_recommendations,
            execution_order=execution_order,
            total_estimated_tokens=total_tokens,
            total_estimated_time=total_time,
            dependencies=dependencies
        )
    
    def _determine_execution_order(self, recommendations: List[AgentRecommendation]) -> List[AgentType]:
        """Determine optimal execution order for agents."""
        
        # Priority order for agent execution
        priority_order = {
            AgentType.INTELLIGENT_CODE_AGENT: 1,      # Foundational analysis first
            AgentType.GOD_CODE_AGENT: 2,              # God code detection early
            AgentType.REFACTORING_ENGINE: 3,          # Refactoring based on analysis
            AgentType.TDD_WORKFLOW_AGENT: 4           # TDD optimization last
        }
        
        # Sort by priority and then by recommendation priority
        sorted_recs = sorted(
            recommendations,
            key=lambda r: (
                priority_order.get(r.agent_type, 10),
                r.priority.value,
                -r.confidence
            )
        )
        
        return [rec.agent_type for rec in sorted_recs]
    
    def _identify_dependencies(self, file_path: str) -> List[str]:
        """Identify file dependencies that might affect analysis."""
        dependencies = []
        
        # TODO: Implement dependency analysis
        # This could analyze imports to identify related files
        # that should be analyzed together
        
        return dependencies
    
    def execute_plan(self, execution_plan: TaskExecution) -> List[ExecutionResult]:
        """
        Execute the agent plan for a file.
        
        Args:
            execution_plan: Complete execution plan
            
        Returns:
            List of execution results from each agent
        """
        
        if not AGENTS_AVAILABLE:
            logger.error("Cannot execute plan - agents not available")
            return []
        
        results = []
        start_time = time.time()
        
        logger.info("Executing plan for %s", execution_plan.file_path)
        logger.info("Agents: %s", [a.value for a in execution_plan.execution_order])
        logger.info("Estimated tokens: %s", execution_plan.total_estimated_tokens)
        logger.info("Estimated time: %.1fs", execution_plan.total_estimated_time)
        
        # Execute each agent in order
        for agent_type in execution_plan.execution_order:
            if agent_type not in self._agents:
                logger.warning("Agent %s not available - skipping", agent_type.value)
                continue
            
            # Find the recommendation for this agent
            agent_rec = next(
                (rec for rec in execution_plan.agents if rec.agent_type == agent_type),
                None
            )
            
            if not agent_rec:
                logger.warning("No recommendation found for %s", agent_type.value)
                continue
            
            # Execute agent with configuration
            result = self._execute_single_agent(
                agent_type, 
                execution_plan.file_path, 
                agent_rec.configuration
            )
            
            results.append(result)
            
            # Update token usage statistics
            self.token_usage_stats[agent_type] += result.tokens_used
            
            # Check if we should stop due to errors
            if not result.success and agent_rec.priority == Priority.CRITICAL:
                logger.error("Critical agent %s failed - stopping execution", agent_type.value)
                break
        
        total_time = time.time() - start_time
        total_tokens = sum(result.tokens_used for result in results)
        
        # Update performance metrics
        self.performance_metrics["total_execution_time"].append(total_time)
        self.performance_metrics["total_tokens_used"].append(total_tokens)
        self.performance_metrics["agents_executed"].append(len(results))
        
        # Record in execution history
        self.execution_history.append({
            "file_path": execution_plan.file_path,
            "task_type": execution_plan.task_type.value,
            "agents_executed": [r.agent_type.value for r in results],
            "execution_time": total_time,
            "tokens_used": total_tokens,
            "success_rate": len([r for r in results if r.success]) / len(results) if results else 0
        })
        
        logger.info("Plan execution completed: %s agents, %s tokens, %.1fs", len(results), total_tokens, total_time)
        
        return results
    
    def _execute_single_agent(
        self, agent_type: AgentType, file_path: str, configuration: Dict[str, Any]
    ) -> ExecutionResult:
        """Execute a single agent with the given configuration and file coordination."""
        
        start_time = time.time()
        tokens_used = 0
        result_data = {}
        warnings = []
        errors = []
        success = False
        agent_name = agent_type.value
        
        try:
            agent = self._agents[agent_type]
            
            logger.debug(f"Executing {agent_name} on {file_path}")
            logger.debug(f"Configuration: {configuration}")
            
            # Determine if this agent will modify files (not dry_run)
            will_modify_file = not self.dry_run and not configuration.get("dry_run", self.dry_run)
            
            if will_modify_file:
                # Execute with file coordination for safe modifications
                logger.info("🔒 Acquiring file lock for %s -> %s", agent_name, file_path)
                
                with self.coordination_manager.acquire_file_lock(
                    file_path, 
                    agent_name, 
                    LockType.EXCLUSIVE,
                    create_backup=True
                ) as lock_info:
                    
                    # Execute agent within protected context
                    result_data, success, tokens_used = self._execute_agent_safely(
                        agent, agent_type, file_path, configuration
                    )
                    
                    # Record modification
                    self.coordination_manager.record_modification(
                        file_path=file_path,
                        agent_name=agent_name,
                        modification_type=agent_type.value.lower().replace("_", "_"),
                        backup_path=lock_info.backup_path or "",
                        success=success,
                        error_message=None if success else str(result_data.get("error", "Unknown error"))
                    )
                    
                    logger.info("🔓 Released file lock for %s -> %s", agent_name, file_path)
                    
            else:
                # Execute in analysis-only mode (dry_run)
                result_data, success, tokens_used = self._execute_agent_safely(
                    agent, agent_type, file_path, configuration
                )
                
        except Exception as e:
            logger.error("Error executing %s: %s", agent_name, e)
            errors.append(str(e))
            
            # Record failed modification if applicable
            if not self.dry_run:
                try:
                    self.coordination_manager.record_modification(
                        file_path=file_path,
                        agent_name=agent_name,
                        modification_type=agent_type.value.lower().replace("_", "_"),
                        backup_path="",
                        success=False,
                        error_message=str(e)
                    )
                except Exception:
                    pass  # Don't let recording errors block execution
        
        execution_time = time.time() - start_time
        
        return ExecutionResult(
            agent_type=agent_type,
            success=success,
            execution_time=execution_time,
            tokens_used=tokens_used,
            result_data=result_data,
            warnings=warnings,
            errors=errors
        )
                
    def _execute_agent_safely(
        self, agent, agent_type: AgentType, file_path: str, configuration: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], bool, int]:
        """Execute individual agent logic safely with error handling."""
        
        try:
            if agent_type == AgentType.INTELLIGENT_CODE_AGENT:
                # Execute IntelligentCodeAgent
                analysis_result = agent.analyze_file_intelligently(file_path)
                if analysis_result is None:
                    return {"error": "Analysis returned None", "file_path": file_path}, False, 0
                
                # Apply analysis-based improvements if not dry run
                file_modified = False
                if not self.dry_run and not configuration.get("dry_run", self.dry_run):
                    file_modified = self._apply_analysis_improvements(file_path, analysis_result)
                
                # Get tokens_used from dataclass or dict
                tokens_used = getattr(analysis_result, 'tokens_used', 0) if hasattr(analysis_result, 'tokens_used') else analysis_result.get("tokens_used", 0)
                
                # Return result dict with file modification status
                return {
                    "analysis_result": analysis_result,
                    "file_modified": file_modified,
                    "tokens_used": tokens_used
                }, True, tokens_used
                
            elif agent_type == AgentType.REFACTORING_ENGINE:
                # Execute IntelligentRefactoringEngine
                refactoring_results = agent.apply_intelligent_refactorings(
                    {"file_path": file_path},  # Simplified - would use real analysis
                    configuration.get("selected_strategies", [0, 1, 2])
                )
                if refactoring_results is None:
                    return {"error": "Refactoring returned None", "file_path": file_path}, False, 0
                
                # Apply refactoring results if not dry run
                file_modified = False
                if not self.dry_run and not configuration.get("dry_run", self.dry_run):
                    file_modified = self._apply_refactoring_results(file_path, refactoring_results)
                
                # Get tokens_used from result
                tokens_used = refactoring_results.get("tokens_used", 0) if isinstance(refactoring_results, dict) else getattr(refactoring_results, 'tokens_used', 0)
                
                # Return result dict with file modification status
                return {
                    "refactoring_results": refactoring_results,
                    "file_modified": file_modified,
                    "tokens_used": tokens_used
                }, True, tokens_used
                
            elif agent_type == AgentType.TDD_WORKFLOW_AGENT:
                # Execute TDDIntelligentWorkflowAgent
                tdd_analysis = agent.analyze_tdd_opportunities({
                    "file_path": file_path
                })
                if tdd_analysis is None:
                    return {"error": "TDD analysis returned None", "file_path": file_path}, False, 0
                
                # Apply TDD improvements if not dry run
                file_modified = False
                if not self.dry_run and not configuration.get("dry_run", self.dry_run):
                    file_modified = self._apply_tdd_improvements(file_path, tdd_analysis)
                
                # Get tokens_used from result
                tokens_used = tdd_analysis.get("tokens_used", 0) if isinstance(tdd_analysis, dict) else getattr(tdd_analysis, 'tokens_used', 0)
                
                # Return result dict with file modification status
                return {
                    "tdd_analysis": tdd_analysis,
                    "file_modified": file_modified,
                    "tokens_used": tokens_used
                }, True, tokens_used
                
            elif agent_type == AgentType.GOD_CODE_AGENT:
                # Execute GodCodeRefactoringAgent with direct access to refactored code
                god_code_results = self._execute_god_code_agent_with_code_generation(
                    file_path=file_path,
                    aggressive=configuration.get("aggressive_refactoring", False),
                    dry_run=configuration.get("dry_run", self.dry_run)
                )
                if god_code_results is None:
                    return {"error": "God code analysis returned None", "file_path": file_path}, False, 0
                
                # Apply god code refactoring results if not dry run
                file_modified = False
                if not self.dry_run and not configuration.get("dry_run", self.dry_run):
                    file_modified = self._apply_god_code_refactoring(file_path, god_code_results)
                
                # Get tokens_used and error status from result
                tokens_used = god_code_results.get("tokens_used", 0) if isinstance(god_code_results, dict) else getattr(god_code_results, 'tokens_used', 0)
                has_error = god_code_results.get("error") if isinstance(god_code_results, dict) else getattr(god_code_results, 'error', None)
                
                # Return result dict with file modification status
                return {
                    "god_code_results": god_code_results,
                    "file_modified": file_modified,
                    "tokens_used": tokens_used
                }, not has_error, tokens_used
                
            else:
                raise ValueError(f"Unknown agent type: {agent_type}")
                
        except Exception as e:
            logger.error("Error in _execute_agent_safely for %s: %s", agent_type.value, e)
            return {"error": str(e), "file_path": file_path}, False, 0
    
    def _execute_god_code_agent_with_code_generation(
        self, file_path: str, aggressive: bool = False, dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Execute GodCodeRefactoringAgent with direct access to generated refactored code.
        
        This method bypasses the run_god_code_analysis function to get the actual
        RefactoringResult objects with the refactored code content.
        """
        try:
            # Read the file content
            with open(file_path, 'r', encoding='utf-8') as f:
                code_content = f.read()
        except Exception as e:
            return {"error": f"Failed to read file {file_path}: {e}"}
        
        # Initialize the agent
        agent = self._agents.get(AgentType.GOD_CODE_AGENT)
        if not agent:
            return {"error": "GodCodeRefactoringAgent not available"}
        
        try:
            # Analyze god codes
            detections = agent.analyze_god_codes(file_path, code_content)
            
            results = {
                "file_path": file_path,
                "total_detections": len(detections),
                "detections": [],
                "strategies": [],
                "refactoring_results": [],
                "full_refactoring_results": []  # NEW: Store complete RefactoringResult objects
            }
            
            # Generate strategies and apply refactoring for each detection
            for detection in detections:
                detection_dict = {
                    "type": detection.type.value,
                    "name": detection.name,
                    "lines": f"{detection.start_line}-{detection.end_line}",
                    "total_lines": detection.total_lines,
                    "complexity_score": detection.complexity_score,
                    "priority": detection.refactoring_priority,
                    "responsibilities": len(detection.responsibilities),
                    "suggested_modules": detection.suggested_separation
                }
                results["detections"].append(detection_dict)
                
                # Generate strategy
                strategy = agent.generate_refactoring_strategy(detection)
                strategy_dict = {
                    "original_name": strategy.original_name,
                    "approach": strategy.separation_approach,
                    "new_modules": [m.get('name', 'Unknown') for m in strategy.new_modules],
                    "risk": strategy.risk_assessment,
                    "improvement": strategy.estimated_improvement
                }
                results["strategies"].append(strategy_dict)
                
                # Apply refactoring and get the FULL result
                refactoring_result = agent.apply_refactoring(code_content, detection, strategy)
                
                # Store minimal metadata (for compatibility)
                result_dict = {
                    "original_name": detection.name,
                    "success": refactoring_result.validation_passed,
                    "modules_created": list(refactoring_result.refactored_modules.keys()),
                    "warnings": refactoring_result.warnings
                }
                results["refactoring_results"].append(result_dict)
                
                # Store FULL RefactoringResult with actual code (NEW!)
                full_result = {
                    "original_code": refactoring_result.original_code,
                    "refactored_modules": refactoring_result.refactored_modules,  # Dict[str, str] - module_name -> code
                    "updated_original": refactoring_result.updated_original,      # Updated original code
                    "validation_passed": refactoring_result.validation_passed,
                    "improvement_metrics": getattr(refactoring_result, 'improvement_metrics', {}),
                    "warnings": refactoring_result.warnings
                }
                results["full_refactoring_results"].append(full_result)
            
            return results
            
        except Exception as e:
            logger.error("Error in god code agent execution: %s", e)
            return {"error": f"God code agent execution failed: {e}"}
    
    def _apply_analysis_improvements(self, file_path: str, analysis_result: Dict[str, Any]) -> bool:
        """Apply improvements suggested by IntelligentCodeAgent analysis."""
        try:
            # Extract refactored code from analysis result
            refactored_code = self._extract_analysis_code(analysis_result)
            if not refactored_code:
                logger.info("No code improvements found in analysis for %s", file_path)
                return False
            
            # Apply the refactored code
            return self._safe_write_file(file_path, refactored_code, "analysis_improvements")
            
        except Exception as e:
            logger.error("Error applying analysis improvements to %s: %s", file_path, e)
            return False
    
    def _apply_refactoring_results(self, file_path: str, refactoring_results: Dict[str, Any]) -> bool:
        """Apply results from IntelligentRefactoringEngine."""
        try:
            # Extract refactored code from refactoring results
            refactored_code = self._extract_refactoring_code(refactoring_results)
            if not refactored_code:
                logger.info("No refactoring improvements found for %s", file_path)
                return False
            
            # Apply the refactored code
            return self._safe_write_file(file_path, refactored_code, "refactoring_engine")
            
        except Exception as e:
            logger.error("Error applying refactoring results to %s: %s", file_path, e)
            return False
    
    def _apply_tdd_improvements(self, file_path: str, tdd_analysis: Dict[str, Any]) -> bool:
        """Apply improvements suggested by TDDIntelligentWorkflowAgent."""
        try:
            # Extract improved code from TDD analysis
            improved_code = self._extract_tdd_code(tdd_analysis)
            if not improved_code:
                logger.info("No TDD improvements found for %s", file_path)
                return False
            
            # Apply the improved code
            return self._safe_write_file(file_path, improved_code, "tdd_improvements")
            
        except Exception as e:
            logger.error("Error applying TDD improvements to %s: %s", file_path, e)
            return False
    
    def _apply_god_code_refactoring(self, file_path: str, god_code_results: Dict[str, Any]) -> bool:
        """Apply god code refactoring results."""
        try:
            # Extract refactored code from god code analysis
            refactored_code = self._extract_god_code_refactoring(god_code_results)
            if not refactored_code:
                logger.info("No god code refactoring found for %s", file_path)
                return False
            
            # Apply the refactored code
            return self._safe_write_file(file_path, refactored_code, "god_code_refactoring")
            
        except Exception as e:
            logger.error("Error applying god code refactoring to %s: %s", file_path, e)
            return False
    
    def _extract_analysis_code(self, analysis_result: Any) -> Optional[str]:
        """Extract refactored code from IntelligentCodeAgent analysis result."""
        # Handle FileSemanticAnalysis dataclass
        if hasattr(analysis_result, 'recommended_refactorings'):
            # Check if there are recommended refactorings with actual code
            refactorings = getattr(analysis_result, 'recommended_refactorings', [])
            if refactorings:
                # Look for refactorings that have refactored code
                for refactoring in refactorings:
                    if hasattr(refactoring, 'refactored_code') and getattr(refactoring, 'refactored_code'):
                        return getattr(refactoring, 'refactored_code')
                    if hasattr(refactoring, 'improved_code') and getattr(refactoring, 'improved_code'):
                        return getattr(refactoring, 'improved_code')
        
        # Handle dictionary format (fallback)
        if isinstance(analysis_result, dict):
            code_keys = [
                "refactored_code", "improved_code", "optimized_code", 
                "updated_code", "result_code", "output_code"
            ]
            
            for key in code_keys:
                if key in analysis_result and analysis_result[key]:
                    return analysis_result[key]
            
            # Check for nested structures
            if "analysis" in analysis_result and isinstance(analysis_result["analysis"], dict):
                for key in code_keys:
                    if key in analysis_result["analysis"]:
                        return analysis_result["analysis"][key]
        
        # Handle direct dataclass with get method
        if hasattr(analysis_result, 'get'):
            code_keys = [
                "refactored_code", "improved_code", "optimized_code", 
                "updated_code", "result_code", "output_code"
            ]
            for key in code_keys:
                value = analysis_result.get(key)
                if value:
                    return value
        
        return None
    
    def _extract_refactoring_code(self, refactoring_results: Dict[str, Any]) -> Optional[str]:
        """Extract refactored code from IntelligentRefactoringEngine results."""
        # Look for refactored code in common result structures
        code_keys = [
            "refactored_code", "final_code", "improved_code", 
            "output_code", "result", "updated_original"
        ]
        
        for key in code_keys:
            if key in refactoring_results and refactoring_results[key]:
                return refactoring_results[key]
        
        # Check for refactoring list with final result
        if "refactorings" in refactoring_results:
            refactorings = refactoring_results["refactorings"]
            if isinstance(refactorings, list) and refactorings:
                last_refactoring = refactorings[-1]
                if isinstance(last_refactoring, dict):
                    for key in code_keys:
                        if key in last_refactoring:
                            return last_refactoring[key]
        
        return None
    
    def _extract_tdd_code(self, tdd_analysis: Dict[str, Any]) -> Optional[str]:
        """Extract improved code from TDDIntelligentWorkflowAgent analysis."""
        # Look for TDD-improved code
        code_keys = [
            "optimized_code", "tdd_improved_code", "refactored_code",
            "improved_code", "output_code", "result_code"
        ]
        
        for key in code_keys:
            if key in tdd_analysis and tdd_analysis[key]:
                return tdd_analysis[key]
        
        # Check for TDD optimization results
        if "tdd_optimizations" in tdd_analysis:
            optimizations = tdd_analysis["tdd_optimizations"]
            if isinstance(optimizations, dict):
                for key in code_keys:
                    if key in optimizations:
                        return optimizations[key]
        
        return None
    
    def _extract_god_code_refactoring(self, god_code_results: Dict[str, Any]) -> Optional[str]:
        """Extract refactored code from GodCodeRefactoringAgent results."""
        
        # NEW: Check for full_refactoring_results with actual code
        if "full_refactoring_results" in god_code_results:
            full_results = god_code_results["full_refactoring_results"]
            if isinstance(full_results, list) and full_results:
                for full_result in full_results:
                    if isinstance(full_result, dict):
                        # Try updated_original first (complete refactored file)
                        if "updated_original" in full_result and full_result["updated_original"]:
                            logger.info("Found updated_original code (%s chars)", len(full_result['updated_original']))
                            return full_result["updated_original"]
                        
                        # Try combining refactored_modules
                        if "refactored_modules" in full_result and full_result["refactored_modules"]:
                            modules = full_result["refactored_modules"]
                            if isinstance(modules, dict) and modules:
                                logger.info("Found refactored_modules: %s", list(modules.keys()))
                                combined_code = self._combine_refactored_modules(modules)
                                if combined_code:
                                    return combined_code
        
        # FALLBACK: Look for god code refactoring results (old format)
        code_keys = [
            "refactored_code", "updated_original", "final_code",
            "improved_code", "output_code", "result_code"
        ]
        
        for key in code_keys:
            if key in god_code_results and god_code_results[key]:
                return god_code_results[key]
        
        # Check for refactoring results list
        if "refactoring_results" in god_code_results:
            results = god_code_results["refactoring_results"]
            if isinstance(results, list) and results:
                # Use the last/final refactoring result
                final_result = results[-1]
                if isinstance(final_result, dict):
                    for key in code_keys:
                        if key in final_result:
                            return final_result[key]
        
        # Check for detection results with refactored modules
        if "detections" in god_code_results:
            detections = god_code_results["detections"]
            if isinstance(detections, list) and detections:
                for detection in detections:
                    if isinstance(detection, dict) and "refactored_modules" in detection:
                        modules = detection["refactored_modules"]
                        if isinstance(modules, dict):
                            # Combine all refactored modules into final code
                            combined_code = self._combine_refactored_modules(modules)
                            if combined_code:
                                return combined_code
        
        logger.info("No refactored code found in god code results")
        return None
    
    def _combine_refactored_modules(self, refactored_modules: Dict[str, Any]) -> Optional[str]:
        """Combine refactored modules into a single code string."""
        try:
            code_parts = []
            
            # Add imports first
            if "imports" in refactored_modules:
                code_parts.append(refactored_modules["imports"])
            
            # Add classes and functions
            for key, value in refactored_modules.items():
                if key != "imports" and isinstance(value, str) and value.strip():
                    code_parts.append(value)
            
            if code_parts:
                return "\n\n".join(code_parts)
            
        except Exception as e:
            logger.error("Error combining refactored modules: %s", e)
        
        return None
    
    def _safe_write_file(self, file_path: str, new_code: str, operation_type: str) -> bool:
        """
        Safely write refactored code to file with validation and rollback capability.
        
        Args:
            file_path: Path to file to modify
            new_code: New code content to write
            operation_type: Type of operation for logging
            
        Returns:
            True if file was successfully modified, False otherwise
        """
        try:
            # Read original file for backup
            with open(file_path, 'r', encoding='utf-8') as f:
                original_code = f.read()
            
            # Validate that new code is actually different
            if new_code.strip() == original_code.strip():
                logger.info("No changes needed for %s - code is identical", file_path)
                return False
            
            # Validate syntax of new code
            if not self._validate_refactored_code(new_code, file_path):
                logger.error("Validation failed for refactored code in %s", file_path)
                return False
            
            # Create additional backup before modification
            backup_path = f"{file_path}.backup.meta_agent.{int(time.time())}"
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_code)
            
            # Write new code to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_code)
            
            logger.info("✅ Successfully applied %s to %s", operation_type, file_path)
            logger.info("📋 Backup created: %s", backup_path)
            
            # Verify the write was successful by reading back
            with open(file_path, 'r', encoding='utf-8') as f:
                written_code = f.read()
            
            if written_code != new_code:
                logger.error("File write verification failed for %s", file_path)
                # Restore from backup
                with open(backup_path, 'r', encoding='utf-8') as f:
                    with open(file_path, 'w', encoding='utf-8') as f2:
                        f2.write(f.read())
                return False
            
            return True
            
        except Exception as e:
            logger.error("Error in _safe_write_file for %s: %s", file_path, e)
            
            # Attempt to restore from backup if available
            try:
                if 'backup_path' in locals():
                    with open(backup_path, 'r', encoding='utf-8') as f:
                        with open(file_path, 'w', encoding='utf-8') as f2:
                            f2.write(f.read())
                    logger.info("Restored %s from backup after error", file_path)
            except Exception as restore_error:
                logger.error("Failed to restore backup for %s: %s", file_path, restore_error)
            
            return False
    
    def _validate_refactored_code(self, code: str, file_path: str) -> bool:
        """
        Validate that refactored code is syntactically correct and safe to apply.
        
        Args:
            code: Code to validate
            file_path: Original file path for context
            
        Returns:
            True if code is valid, False otherwise
        """
        try:
            # Basic syntax validation using AST
            ast.parse(code)
            
            # Check for minimum code quality indicators
            lines = [line.strip() for line in code.split('\n') if line.strip()]
            
            # Ensure code is not empty or trivial
            if len(lines) < 5:
                logger.warning(
                    "Refactored code for %s seems too short (%s lines)",
                    file_path,
                    len(lines),
                )
                return False
            
            # Check for obvious corruption patterns
            corruption_indicators = [
                "SyntaxError", "IndentationError", "TabError",
                "<<<<<<< HEAD", ">>>>>>> ", "======="
            ]
            
            for indicator in corruption_indicators:
                if indicator in code:
                    logger.error("Code corruption detected in %s: %s", file_path, indicator)
                    return False
            
            # Check for basic Python structure
            has_functions_or_classes = any(
                line.startswith(('def ', 'class ', 'async def ')) 
                for line in lines
            )
            
            # Allow files without functions/classes (e.g., config files, scripts)
            if not has_functions_or_classes and len(lines) > 20:
                logger.warning(
                    "Refactored code for %s has no functions or classes but is %s lines",
                    file_path,
                    len(lines),
                )
            
            logger.debug(f"Code validation passed for {file_path}")
            return True
            
        except SyntaxError as e:
            logger.error("Syntax error in refactored code for %s: %s", file_path, e)
            return False
        except Exception as e:
            logger.error("Error validating refactored code for %s: %s", file_path, e)
            return False
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary and statistics."""
        
        total_executions = len(self.execution_history)
        
        if total_executions == 0:
            return {
                "total_executions": 0,
                "message": "No executions recorded yet"
            }
        
        # Calculate averages
        avg_execution_time = sum(self.performance_metrics["total_execution_time"]) / len(self.performance_metrics["total_execution_time"])
        avg_tokens_used = sum(self.performance_metrics["total_tokens_used"]) / len(self.performance_metrics["total_tokens_used"])
        avg_agents_per_execution = sum(self.performance_metrics["agents_executed"]) / len(self.performance_metrics["agents_executed"])
        
        # Calculate success rates
        total_success_rate = sum(ex["success_rate"] for ex in self.execution_history) / total_executions
        
        # Agent usage statistics
        agent_usage_stats = {}
        for agent_type, token_usage in self.token_usage_stats.items():
            executions = len([ex for ex in self.execution_history if agent_type.value in ex["agents_executed"]])
            agent_usage_stats[agent_type.value] = {
                "executions": executions,
                "total_tokens": token_usage,
                "avg_tokens_per_execution": token_usage / executions if executions > 0 else 0
            }
        
        return {
            "total_executions": total_executions,
            "avg_execution_time": avg_execution_time,
            "avg_tokens_used": avg_tokens_used,
            "avg_agents_per_execution": avg_agents_per_execution,
            "total_success_rate": total_success_rate,
            "agent_usage_stats": agent_usage_stats,
            "total_tokens_consumed": sum(self.token_usage_stats.values())
        }


def run_meta_agent_analysis(
    file_path: str, 
    task_type: TaskType = TaskType.COMPREHENSIVE_AUDIT,
    project_root: Optional[str] = None,
    token_budget: int = 32000,
    dry_run: bool = True
) -> Dict[str, Any]:
    """
    Convenience function to run MetaAgent analysis on a single file.
    
    Args:
        file_path: Path to file to analyze
        task_type: Type of analysis to perform
        project_root: Project root directory (auto-detected if None)
        token_budget: Available token budget
        dry_run: Run in dry-run mode
        
    Returns:
        Dictionary with analysis results
    """
    
    if project_root is None:
        project_root = Path(file_path).parent
        while project_root.parent != project_root:
            if (project_root / "pyproject.toml").exists() or (project_root / ".git").exists():
                break
            project_root = project_root.parent
    
    try:
        # Initialize MetaAgent
        meta_agent = MetaAgent(
            project_root=project_root,
            token_budget=token_budget,
            dry_run=dry_run
        )
        
        # Create execution plan
        execution_plan = meta_agent.create_execution_plan(file_path, task_type)
        
        # Execute plan
        results = meta_agent.execute_plan(execution_plan)
        
        return {
            "file_path": file_path,
            "task_type": task_type.value,
            "execution_plan": {
                "agents": [rec.agent_type.value for rec in execution_plan.agents],
                "estimated_tokens": execution_plan.total_estimated_tokens,
                "estimated_time": execution_plan.total_estimated_time
            },
            "execution_results": [
                {
                    "agent": result.agent_type.value,
                    "success": result.success,
                    "execution_time": result.execution_time,
                    "tokens_used": result.tokens_used,
                    "warnings": result.warnings,
                    "errors": result.errors
                }
                for result in results
            ],
            "summary": {
                "total_agents": len(results),
                "successful_agents": len([r for r in results if r.success]),
                "total_execution_time": sum(r.execution_time for r in results),
                "total_tokens_used": sum(r.tokens_used for r in results)
            }
        }
        
    except Exception as e:
        logger.error("Error in meta agent analysis: %s", e)
        return {
            "file_path": file_path,
            "error": str(e),
            "success": False
        }


if __name__ == "__main__":
    # Simple CLI for testing MetaAgent
    import argparse
    
    parser = argparse.ArgumentParser(description="MetaAgent - Intelligent Agent Coordination")
    parser.add_argument("file_path", help="Path to file to analyze")
    parser.add_argument("--task", choices=[t.value for t in TaskType], 
                       default=TaskType.COMPREHENSIVE_AUDIT.value, help="Analysis task type")
    parser.add_argument("--project-root", help="Project root directory")
    parser.add_argument("--token-budget", type=int, default=32000, help="Token budget")
    parser.add_argument("--dry-run", action="store_true", help="Run in dry-run mode")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Convert task string to enum
    task_type = TaskType(args.task)
    
    print(f"🧠 MetaAgent - Intelligent Agent Coordination")
    print(f"File: {args.file_path}")
    print(f"Task: {task_type.value}")
    print(f"Token Budget: {args.token_budget}")
    print(f"Dry Run: {args.dry_run}")
    print()
    
    # Run analysis
    results = run_meta_agent_analysis(
        file_path=args.file_path,
        task_type=task_type,
        project_root=args.project_root,
        token_budget=args.token_budget,
        dry_run=args.dry_run
    )
    
    # Display results
    if results.get("error"):
        print(f"❌ Error: {results['error']}")
    else:
        print("✅ Analysis completed successfully")
        print()
        print("📊 Execution Plan:")
        plan = results["execution_plan"]
        print(f"   Agents: {', '.join(plan['agents'])}")
        print(f"   Estimated tokens: {plan['estimated_tokens']}")
        print(f"   Estimated time: {plan['estimated_time']:.1f}s")
        print()
        
        print("🚀 Execution Results:")
        for result in results["execution_results"]:
            status = "✅" if result["success"] else "❌"
            print(f"   {status} {result['agent']}: {result['execution_time']:.1f}s, {result['tokens_used']} tokens")
            
            if result["warnings"]:
                for warning in result["warnings"]:
                    print(f"      ⚠️ {warning}")
            
            if result["errors"]:
                for error in result["errors"]:
                    print(f"      ❌ {error}")
        
        print()
        summary = results["summary"]
        print("📈 Summary:")
        print(f"   Total agents: {summary['total_agents']}")
        print(f"   Successful: {summary['successful_agents']}")
        print(f"   Total time: {summary['total_execution_time']:.1f}s")
        print(f"   Total tokens: {summary['total_tokens_used']}")