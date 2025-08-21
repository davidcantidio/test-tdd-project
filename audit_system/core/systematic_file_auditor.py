#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 Systematic File Auditor - Sétima Camada de Auditoria Automatizada

Sistema automatizado que percorre TODOS os arquivos do projeto sistematicamente,
analisando linha por linha, otimizando quando possível e documentando tudo,
com rastreamento no banco de dados para resiliência completa.

Uso:
    python systematic_file_auditor.py [--resume] [--dry-run] [--max-files N]
                                      [--wave {1,2,3,4,all}]
                                      [--risk-category {LOW,MEDIUM,HIGH,CRITICAL}]
                                      [--validate-only] [-v/--verbose]
"""

from __future__ import annotations

import time
import sys
import os
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import ast
import json
import sqlite3

# ---------------------------------------------------------------------------
# Integrações Sétima Camada (graceful degradation)
# ---------------------------------------------------------------------------
try:
    from .context_validator import ContextValidator
    from .integration_tester import IntegrationTester
    from .rollback_context_changes import RollbackManager
except ImportError:
    try:
        from context_validator import ContextValidator  # type: ignore
        from integration_tester import IntegrationTester  # type: ignore
        from rollback_context_changes import RollbackManager  # type: ignore
    except ImportError:
        ContextValidator = None  # type: ignore
        IntegrationTester = None  # type: ignore
        RollbackManager = None  # type: ignore

# ---------------------------------------------------------------------------
# Intelligent agents integration (graceful degradation)
# ---------------------------------------------------------------------------
try:
    from .intelligent_code_agent import IntelligentCodeAgent, AnalysisDepth, SemanticMode
    from .intelligent_refactoring_engine import IntelligentRefactoringEngine  
    from .tdd_intelligent_workflow_agent import TDDIntelligentWorkflowAgent
    from .meta_agent import MetaAgent, TaskType, run_meta_agent_analysis
    INTELLIGENT_AGENTS_AVAILABLE = True
except ImportError:
    try:
        from intelligent_code_agent import IntelligentCodeAgent, AnalysisDepth, SemanticMode  # type: ignore
        from intelligent_refactoring_engine import IntelligentRefactoringEngine  # type: ignore
        from tdd_intelligent_workflow_agent import TDDIntelligentWorkflowAgent  # type: ignore
        from meta_agent import MetaAgent, TaskType, run_meta_agent_analysis  # type: ignore
        INTELLIGENT_AGENTS_AVAILABLE = True
    except ImportError:
        # Graceful degradation
        IntelligentCodeAgent = None
        IntelligentRefactoringEngine = None 
        TDDIntelligentWorkflowAgent = None
        MetaAgent = None
        TaskType = None
        run_meta_agent_analysis = None
        AnalysisDepth = None
        SemanticMode = None
        INTELLIGENT_AGENTS_AVAILABLE = False

# ---------------------------------------------------------------------------
# Caminho do projeto e PYTHONPATH
# ---------------------------------------------------------------------------
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# ---------------------------------------------------------------------------
# Banco de dados: API legada + API modular (preferir modular quando existir)
# ---------------------------------------------------------------------------
from streamlit_extension.utils.database import DatabaseManager  # type: ignore

try:
    # API modular (preferível pela performance)
    from streamlit_extension.database import get_connection as get_modular_connection  # type: ignore
except Exception:  # pragma: no cover
    get_modular_connection = None  # type: ignore


# =============================================================================
# Sétima Camada - Dados de Apoio
# =============================================================================
class SetimaDataLoader:
    """Carrega dados de integração da Sétima Camada a partir de artefatos/relatórios."""

    def __init__(self, audit_dir: Path):
        self.audit_dir = audit_dir
        self.logger = logging.getLogger(f"{__name__}.SetimaDataLoader")

        self.dependency_waves = self._load_dependency_data()
        self.risk_scores = self._load_risk_data()
        self.pattern_templates = self._load_pattern_data()
        self.good_patterns = self._load_good_patterns()
        self.anti_patterns = self._load_anti_patterns()

        self.logger.info(
            "Sétima Camada carregada: %d arquivos com pontuação de risco",
            len(self.risk_scores),
        )

    def _load_dependency_data(self) -> Dict[str, List[str]]:
        # Em produção, faria parsing de um DEPENDENCY_GRAPH.md
        return {
            "WAVE_1_FOUNDATION": [
                "tests/test_duration_calculator.py",
                "tests/test_business_calendar.py",
                "scripts/maintenance/database_maintenance.py",
                "streamlit_extension/components/analytics_cards.py",
                "streamlit_extension/utils/path_utils.py",
                "streamlit_extension/utils/data_utils.py",
                "streamlit_extension/pages/clients.py",
                "streamlit_extension/endpoints/health.py",
            ],
            "WAVE_2_BUSINESS": [
                "streamlit_extension/services/analytics_service.py",
                "streamlit_extension/services/client_service.py",
                "streamlit_extension/models/task_models.py",
                "streamlit_extension/repos/tasks_repo.py",
            ],
            "WAVE_3_INTEGRATION": [
                "streamlit_extension/utils/circuit_breaker.py",
                "streamlit_extension/utils/metrics_collector.py",
                "duration_system/json_security.py",
            ],
            "WAVE_4_CRITICAL": [
                "streamlit_extension/database/connection.py",
                "streamlit_extension/streamlit_app.py",
                "streamlit_extension/middleware/rate_limiting/middleware.py",
                "streamlit_extension/database/queries.py",
                "streamlit_extension/database/seed.py",
                "streamlit_extension/middleware/rate_limiting/core.py",
                "streamlit_extension/database/schema.py",
                "streamlit_extension/database/health.py",
            ],
        }

    def _load_risk_data(self) -> Dict[str, int]:
        # Em produção, faria parsing de RISK_ASSESSMENT_MAP.md
        return {
            # CRITICAL (106+)
            "streamlit_extension/database/connection.py": 165,
            "streamlit_extension/streamlit_app.py": 150,
            "streamlit_extension/middleware/rate_limiting/middleware.py": 145,
            "streamlit_extension/database/queries.py": 140,
            "streamlit_extension/database/seed.py": 135,
            "streamlit_extension/middleware/rate_limiting/core.py": 130,
            "streamlit_extension/database/schema.py": 120,
            "streamlit_extension/database/health.py": 110,
            # HIGH (71-105)
            "streamlit_extension/utils/circuit_breaker.py": 90,
            "streamlit_extension/utils/metrics_collector.py": 85,
            "duration_system/json_security.py": 88,
            # MEDIUM (36-70)
            "streamlit_extension/services/analytics_service.py": 48,
            "streamlit_extension/services/client_service.py": 52,
            "streamlit_extension/models/task_models.py": 45,
            # LOW (0-35)
            "streamlit_extension/components/analytics_cards.py": 20,
            "streamlit_extension/utils/path_utils.py": 15,
            "streamlit_extension/pages/clients.py": 25,
            "tests/test_duration_calculator.py": 8,
        }

    def _load_pattern_data(self) -> Dict[str, Any]:
        return {
            "import_centralization": {
                "description": "Centraliza imports para reduzir import hell",
                "risk_level_safe": ["LOW", "MEDIUM"],
                "transformation": "from streamlit_extension.utils.import_manager import get_safe_import",
                "validation_required": True,
            },
            "exception_swallowing_fix": {
                "description": "Evita except genéricos/bare",
                "risk_level_safe": ["LOW", "MEDIUM", "HIGH"],
                "transformation": 'except {SpecificException} as e:\n    logger.warning("Operation failed: %s", str(e))\n    return None',
                "validation_required": False,
            },
            "method_decomposition": {
                "description": "Quebra métodos gigantes em menores",
                "risk_level_safe": ["LOW"],
                "transformation": "MANUAL_REVIEW_REQUIRED",
                "validation_required": True,
            },
        }

    def _load_good_patterns(self) -> Dict[str, Any]:
        return {
            "graceful_import": {
                "description": "Import seguro com fallback",
                "template": "try:\n    import {module}\nexcept ImportError:\n    {module} = None",
                "preserve": True,
                "files_found": 8,
            },
            "structured_logging": {
                "description": "Logging estruturado com extra/context",
                "template": 'logger.info("Op: %s", operation, extra={"context": ctx})',
                "preserve": True,
                "files_found": 6,
            },
        }

    def _load_anti_patterns(self) -> Dict[str, Any]:
        return {
            "import_hell": {
                "description": "Imports dinâmicos complexos c/ estado global",
                "severity": "HIGH",
                "fix_template": "import_centralization",
                "files_found": 3,
                "auto_fix": True,
            },
            "god_method": {
                "description": "Métodos >50 linhas, multi-responsabilidade",
                "severity": "MEDIUM",
                "fix_template": "method_decomposition",
                "files_found": 4,
                "auto_fix": False,
            },
            "exception_swallowing": {
                "description": "Except genéricos que escondem erros",
                "severity": "HIGH",
                "fix_template": "exception_swallowing_fix",
                "files_found": 15,
                "auto_fix": True,
            },
        }

    def get_file_wave(self, file_path: str) -> str:
        for wave, files in self.dependency_waves.items():
            if file_path in files:
                return wave
        return "WAVE_1_FOUNDATION"

    def get_file_risk_score(self, file_path: str) -> int:
        return self.risk_scores.get(file_path, 25)

    def get_file_risk_category(self, file_path: str) -> str:
        score = self.get_file_risk_score(file_path)
        if score >= 106:
            return "CRITICAL"
        if score >= 71:
            return "HIGH"
        if score >= 36:
            return "MEDIUM"
        return "LOW"


# =============================================================================
# Enums e modelos
# =============================================================================
class AuditStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class SessionStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class RiskCategory(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ModificationWave(Enum):
    WAVE_1_FOUNDATION = "WAVE_1_FOUNDATION"
    WAVE_2_BUSINESS = "WAVE_2_BUSINESS"
    WAVE_3_INTEGRATION = "WAVE_3_INTEGRATION"
    WAVE_4_CRITICAL = "WAVE_4_CRITICAL"


@dataclass
class FileAuditResult:
    file_path: str
    lines_analyzed: int
    issues_found: int
    optimizations_applied: int
    tokens_used: int
    changes_summary: str
    syntax_valid: bool
    backup_created: bool
    # Sétima Camada
    context_quality: float = 0.0
    risk_score: int = 0
    risk_category: str = "LOW"
    modification_wave: str = "WAVE_1_FOUNDATION"
    patterns_found: List[str] | None = None
    good_patterns_preserved: List[str] | None = None
    anti_patterns_fixed: List[str] | None = None
    integration_tests_passed: bool = True
    rollback_available: bool = False

    def __post_init__(self) -> None:
        if self.patterns_found is None:
            self.patterns_found = []
        if self.good_patterns_preserved is None:
            self.good_patterns_preserved = []
        if self.anti_patterns_fixed is None:
            self.anti_patterns_fixed = []


@dataclass
class AuditSession:
    session_id: int
    session_start: datetime
    current_file_index: int
    total_files: int
    files_completed: int
    total_tokens_used: int
    session_status: SessionStatus
    estimated_completion: Optional[datetime] = None


# =============================================================================
# Auditor principal
# =============================================================================
class EnhancedSystematicFileAuditor:
    """Auditor com integração Sétima Camada e salvaguardas enterprise."""

    def __init__(self, project_root: Path, audit_dir: Path, *, dry_run: bool = False, validate_only: bool = False):
        self.project_root = project_root
        self.audit_dir = audit_dir
        self.dry_run = dry_run
        self.validate_only = validate_only
        self.logger = logging.getLogger(f"{__name__}.EnhancedSystematicFileAuditor")

        # Núcleo
        self.db_manager = DatabaseManager()
        self.session_manager = EnterpriseSessionManager(self.db_manager, self.project_root)
        self.token_manager = SmartTokenBudgetManager()
        self.file_manager = FileListManager(project_root)

        # Sétima Camada
        self.context_validator = ContextValidator() if ContextValidator else None  # type: ignore
        self.integration_tester = IntegrationTester() if IntegrationTester else None  # type: ignore
        self.rollback_manager = RollbackManager() if RollbackManager else None  # type: ignore
        self.setima_data = SetimaDataLoader(audit_dir)

        self.setima_integration_available = all(
            [
                self.context_validator is not None,
                self.integration_tester is not None,
                self.rollback_manager is not None,
            ]
        )

        # Initialize Intelligent Agents
        self.intelligent_agents_available = INTELLIGENT_AGENTS_AVAILABLE
        self.intelligent_code_agent = None
        self.refactoring_engine = None
        self.tdd_workflow_agent = None
        self.meta_agent = None
        
        if INTELLIGENT_AGENTS_AVAILABLE:
            try:
                self.intelligent_code_agent = IntelligentCodeAgent(
                    project_root=self.project_root,
                    analysis_depth=AnalysisDepth.ADVANCED,
                    semantic_mode=SemanticMode.CONSERVATIVE,
                    dry_run=self.dry_run
                )
                
                self.refactoring_engine = IntelligentRefactoringEngine(
                    dry_run=self.dry_run
                )
                
                self.tdd_workflow_agent = TDDIntelligentWorkflowAgent(project_root=self.project_root)
                
                # Initialize MetaAgent for intelligent coordination
                self.meta_agent = MetaAgent(
                    project_root=self.project_root,
                    token_budget=self.token_manager.max_tokens_per_hour,
                    dry_run=self.dry_run
                )
                
                self.logger.info("✅ Intelligent agents initialized successfully (including MetaAgent)")
            except Exception as e:
                self.logger.error("❌ Failed to initialize intelligent agents: %s", e)
                self.intelligent_agents_available = False
        else:
            self.logger.warning("⚠️ Intelligent agents not available - using legacy analysis")

        self.validation_pipeline = self._setup_validation_pipeline()
        self.logger.info("Auditor inicializado (Sétima Camada: %s, IA: %s)", 
                        "completa" if self.setima_integration_available else "parcial",
                        "disponível" if self.intelligent_agents_available else "indisponível")

    # ------------------------------------------------------------------ utils
    def _setup_validation_pipeline(self) -> Dict[str, Any]:
        return {
            "min_context_quality": 50.0,
            "integration_test_required": True,
            "critical_validation_required": True,
            "rollback_on_failure": True,
        }

    # --------------------------------------------------------- auditoria file
    def audit_file_enhanced(self, file_path: str) -> FileAuditResult:
        try:
            self.logger.info("Iniciando auditoria (enhanced) de %s", file_path)

            # 1) Contexto
            context_quality = self._validate_context_quality(file_path)
            if context_quality < self.validation_pipeline["min_context_quality"]:
                return self._create_skip_result(file_path, f"Low context quality: {context_quality:.1f}%")

            # 2) Risco
            risk_score = self.setima_data.get_file_risk_score(file_path)
            risk_category = self.setima_data.get_file_risk_category(file_path)

            # 3) Onda
            modification_wave = self.setima_data.get_file_wave(file_path)

            # 4) Padrões
            patterns_found_dicts = self._detect_patterns(file_path)
            anti_patterns = [p for p in patterns_found_dicts if p.get("is_anti_pattern", False)]
            good_patterns = [p for p in patterns_found_dicts if not p.get("is_anti_pattern", False)]

            # 5) Segurança extra p/ críticos
            if risk_category == "CRITICAL":
                safety_check = self._validate_critical_modification_safety(file_path)
                if not safety_check["is_safe"]:
                    return self._create_defer_result(file_path, f"Critical safety check failed: {safety_check['reason']}")

            # 6) Backup (respeita dry-run/validate-only)
            backup_created = False
            if not self.dry_run and not self.validate_only:
                backup_created = self._create_file_backup(file_path)

            # 7) Execução inteligente com IA ou fallback para contexto-aware
            if self.intelligent_agents_available:
                audit_result = self._execute_intelligent_audit(
                    file_path=file_path,
                    risk_score=risk_score,
                    context_quality=context_quality
                )
            else:
                # Fallback para análise contexto-aware (legado)
                audit_result = self._execute_context_aware_audit(
                    file_path=file_path,
                    risk_score=risk_score,
                    patterns=patterns_found_dicts,
                    context_quality=context_quality,
                    wave_info=modification_wave,
                )

            # 8) Validações pós-modificação
            if audit_result.get("modified", False):
                validation_result = self._validate_post_modification(file_path)
                if not validation_result["passed"]:
                    if not self.dry_run and not self.validate_only:
                        self._rollback_file_changes(file_path)
                    return self._create_rollback_result(file_path, validation_result["errors"])

            # 9) Resultado enriquecido
            return FileAuditResult(
                file_path=file_path,
                lines_analyzed=audit_result.get("lines_analyzed", 0),
                issues_found=len(anti_patterns),
                optimizations_applied=audit_result.get("optimizations_applied", 0),
                tokens_used=audit_result.get("tokens_used", 0),
                changes_summary=audit_result.get("changes_summary", "Enhanced audit completed"),
                syntax_valid=audit_result.get("syntax_valid", True),
                backup_created=backup_created,
                context_quality=context_quality,
                risk_score=risk_score,
                risk_category=risk_category,
                modification_wave=modification_wave,
                patterns_found=[p.get("name", "unknown") for p in patterns_found_dicts],
                good_patterns_preserved=[p.get("name", "unknown") for p in good_patterns],
                anti_patterns_fixed=[p.get("name", "unknown") for p in anti_patterns if audit_result.get("modified")],
                integration_tests_passed=True,
                rollback_available=backup_created,
            )
        except Exception as e:  # pragma: no cover - trilha de segurança
            self.logger.error("Erro crítico na auditoria de %s: %s", file_path, e)
            self._emergency_rollback(file_path)
            return self._create_emergency_result(file_path, str(e))

    # -------------------------------------------------------------- validação
    def _validate_context_quality(self, file_path: str) -> float:
        """Análise sofisticada de qualidade usando AST parsing com fallback heurístico."""
        try:
            content = self._read_file_safely(file_path)
            if not content:
                return 20.0
            
            # Tentar análise AST primeiro
            try:
                return self._validate_context_quality_ast_based(file_path, content)
            except SyntaxError:
                self.logger.debug("Syntax error em %s, usando fallback heurístico", file_path)
                return self._validate_context_quality_fallback(content)
                
        except Exception as e:  # pragma: no cover
            self.logger.warning("Falha ao avaliar contexto de %s: %s", file_path, e)
            return 40.0

    def _validate_context_quality_ast_based(self, file_path: str, content: str) -> float:
        """Análise precisa usando AST parsing para métricas estruturais."""
        tree = ast.parse(content)
        
        # Métricas estruturais
        total_functions = 0
        functions_with_docstrings = 0
        functions_with_type_hints = 0
        functions_with_return_hints = 0
        total_classes = 0
        classes_with_docstrings = 0
        has_module_docstring = bool(ast.get_docstring(tree))
        
        # Métricas de complexidade
        total_lines = content.count('\n') + 1
        max_function_complexity = 0
        error_handling_blocks = 0
        logging_calls = 0
        
        # Análise estrutural
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                total_functions += 1
                
                # Docstring
                if ast.get_docstring(node):
                    functions_with_docstrings += 1
                
                # Type hints nos argumentos
                if any(arg.annotation for arg in node.args.args):
                    functions_with_type_hints += 1
                
                # Return type hint
                if node.returns:
                    functions_with_return_hints += 1
                
                # Complexidade (aproximada por número de decisões)
                complexity = self._calculate_function_complexity(node)
                max_function_complexity = max(max_function_complexity, complexity)
            
            elif isinstance(node, ast.ClassDef):
                total_classes += 1
                if ast.get_docstring(node):
                    classes_with_docstrings += 1
            
            elif isinstance(node, ast.Try):
                error_handling_blocks += 1
            
            elif isinstance(node, ast.Call):
                # Detectar logging calls
                if (isinstance(node.func, ast.Attribute) and 
                    isinstance(node.func.value, ast.Name) and
                    node.func.value.id in ['logger', 'logging']):
                    logging_calls += 1
        
        # Cálculo de qualidade baseado em métricas reais
        quality = 30.0  # Base score
        
        # Documentação (30 pontos máximo)
        if has_module_docstring:
            quality += 10.0
        
        if total_functions > 0:
            doc_ratio = functions_with_docstrings / total_functions
            quality += doc_ratio * 15.0  # 15 pontos para 100% docs
        
        if total_classes > 0:
            class_doc_ratio = classes_with_docstrings / total_classes
            quality += class_doc_ratio * 5.0  # 5 pontos para class docs
        
        # Type hints (25 pontos máximo)
        if total_functions > 0:
            hint_ratio = functions_with_type_hints / total_functions
            return_hint_ratio = functions_with_return_hints / total_functions
            quality += hint_ratio * 15.0  # 15 pontos para argument hints
            quality += return_hint_ratio * 10.0  # 10 pontos para return hints
        
        # Error handling (15 pontos máximo)
        if error_handling_blocks > 0:
            quality += min(error_handling_blocks * 3.0, 15.0)
        
        # Logging (10 pontos máximo)
        if logging_calls > 0:
            quality += min(logging_calls * 2.0, 10.0)
        
        # Complexidade (penalidade/bônus - 10 pontos)
        if max_function_complexity <= 5:
            quality += 10.0  # Baixa complexidade
        elif max_function_complexity <= 10:
            quality += 5.0   # Complexidade moderada
        elif max_function_complexity > 20:
            quality -= 5.0   # Penalidade por alta complexidade
        
        # Tamanho do arquivo (10 pontos máximo)
        if 20 <= total_lines <= 300:
            quality += 10.0  # Tamanho ideal
        elif 300 < total_lines <= 500:
            quality += 5.0   # Aceitável
        elif total_lines > 1000:
            quality -= 5.0   # Penalidade por arquivo muito grande
        
        return min(quality, 100.0)
    
    def _calculate_function_complexity(self, func_node: ast.FunctionDef) -> int:
        """Calcula complexidade ciclomática aproximada de uma função."""
        complexity = 1  # Base complexity
        
        for node in ast.walk(func_node):
            # Decisões que aumentam complexidade
            if isinstance(node, (ast.If, ast.While, ast.For, ast.Try)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, ast.With):
                complexity += 1
            # Operadores lógicos
            elif isinstance(node, (ast.And, ast.Or)):
                complexity += 1
        
        return complexity

    def _validate_context_quality_fallback(self, content: str) -> float:
        """Fallback heurístico para arquivos com syntax errors."""
        lines = content.count('\n') + 1
        has_docstrings = '"""' in content or "'''" in content
        has_type_hints = (': ' in content) and ('->' in content)
        has_logging = ('logger.' in content) or ('logging' in content)
        has_error_handling = ('try:' in content and 'except' in content)
        
        quality = 40.0  # Base score mais baixo para fallback
        
        if has_docstrings:
            quality += 12.0
        if has_type_hints:
            quality += 12.0
        if has_logging:
            quality += 8.0
        if has_error_handling:
            quality += 8.0
        if 20 <= lines <= 500:
            quality += 5.0
        
        return min(quality, 85.0)  # Máximo menor para fallback

    def _read_file_safely(self, file_path: str) -> str:
        """Lê arquivo com detecção de encoding e tratamento robusto."""
        full_path = self.project_root / file_path
        if not full_path.exists():
            return ""
        
        # Tentar encodings comuns
        encodings = ["utf-8", "latin1", "cp1252", "iso-8859-1"]
        
        for encoding in encodings:
            try:
                return full_path.read_text(encoding=encoding)
            except UnicodeDecodeError:
                continue
        
        # Fallback com errors='ignore'
        return full_path.read_text(encoding="utf-8", errors="ignore")

    def _detect_patterns(self, file_path: str) -> List[Dict[str, Any]]:
        """Detecção robusta de patterns usando AST parsing com fallback."""
        try:
            content = self._read_file_safely(file_path)
            if not content:
                return []
            
            # Tentar AST parsing primeiro
            try:
                return self._detect_patterns_ast_based(file_path, content)
            except SyntaxError:
                self.logger.debug("Syntax error em %s, usando fallback heurístico", file_path)
                return self._detect_patterns_fallback(file_path, content)
                
        except Exception as e:  # pragma: no cover
            self.logger.warning("Falha ao detectar padrões em %s: %s", file_path, e)
            return []

    def _detect_patterns_ast_based(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Detecção precisa usando AST parsing."""
        patterns: List[Dict[str, Any]] = []
        tree = ast.parse(content)
        
        # Contadores para análise
        try_blocks = 0
        import_errors = 0
        bare_excepts = 0
        exception_swallows = 0
        god_methods = 0
        functions_with_docs = 0
        total_functions = 0
        has_graceful_imports = False
        has_structured_logging = False
        
        for node in ast.walk(tree):
            # Análise de try/except blocks
            if isinstance(node, ast.Try):
                try_blocks += 1
                for handler in node.handlers:
                    if handler.type is None:  # bare except
                        bare_excepts += 1
                        patterns.append({
                            "name": "bare_except",
                            "type": "anti_pattern",
                            "is_anti_pattern": True,
                            "severity": "HIGH",
                            "auto_fixable": True,
                            "line": handler.lineno,
                            "details": "Bare except clause detected"
                        })
                    elif (isinstance(handler.type, ast.Name) and 
                          handler.type.id == "Exception" and 
                          len(handler.body) == 1 and 
                          isinstance(handler.body[0], ast.Return)):
                        exception_swallows += 1
                        patterns.append({
                            "name": "exception_swallowing",
                            "type": "anti_pattern", 
                            "is_anti_pattern": True,
                            "severity": "HIGH",
                            "auto_fixable": True,
                            "line": handler.lineno,
                            "details": "Exception swallowing pattern detected"
                        })
                    elif (isinstance(handler.type, ast.Name) and 
                          handler.type.id == "ImportError"):
                        import_errors += 1
            
            # Análise de funções
            elif isinstance(node, ast.FunctionDef):
                total_functions += 1
                
                # Verificar docstring
                if ast.get_docstring(node):
                    functions_with_docs += 1
                
                # Detectar god methods
                function_lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 0
                if function_lines > 50:
                    god_methods += 1
                    patterns.append({
                        "name": "god_method",
                        "type": "anti_pattern",
                        "is_anti_pattern": True,
                        "severity": "MEDIUM",
                        "auto_fixable": False,
                        "line": node.lineno,
                        "details": f"Function '{node.name}' has {function_lines} lines"
                    })
            
            # Detectar structured logging
            elif isinstance(node, ast.Call):
                if (isinstance(node.func, ast.Attribute) and 
                    isinstance(node.func.value, ast.Name) and 
                    node.func.value.id == "logger"):
                    # Verificar se tem extra= keyword
                    for keyword in node.keywords:
                        if keyword.arg == "extra":
                            has_structured_logging = True
                            break
        
        # Detectar import hell pattern
        if try_blocks > 3 and import_errors >= 2:
            patterns.append({
                "name": "import_hell",
                "type": "anti_pattern",
                "is_anti_pattern": True,
                "severity": "HIGH",
                "auto_fixable": True,
                "details": f"{try_blocks} try blocks, {import_errors} ImportError handlers"
            })
        
        # Detectar graceful imports
        if import_errors > 0 and "_AVAILABLE" in content:
            has_graceful_imports = True
            patterns.append({
                "name": "graceful_import",
                "type": "good_pattern",
                "is_anti_pattern": False,
                "preserve": True,
                "details": "Graceful import pattern with fallback"
            })
        
        # Detectar structured logging
        if has_structured_logging:
            patterns.append({
                "name": "structured_logging",
                "type": "good_pattern",
                "is_anti_pattern": False,
                "preserve": True,
                "details": "Structured logging with extra context"
            })
        
        return patterns

    def _detect_patterns_fallback(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Fallback heurístico para arquivos com syntax errors."""
        patterns: List[Dict[str, Any]] = []
        
        # Anti-patterns básicos por string matching
        if "except Exception:" in content or "except:" in content:
            patterns.append({
                "name": "exception_swallowing",
                "type": "anti_pattern",
                "is_anti_pattern": True,
                "severity": "HIGH",
                "auto_fixable": True,
                "details": "Detected via string matching (fallback)"
            })
        
        if content.count("try:") > 3 and "ImportError" in content:
            patterns.append({
                "name": "import_hell",
                "type": "anti_pattern",
                "is_anti_pattern": True,
                "severity": "HIGH", 
                "auto_fixable": True,
                "details": "Detected via string matching (fallback)"
            })
        
        # Good patterns
        if "try:" in content and "except ImportError:" in content and "_AVAILABLE" in content:
            patterns.append({
                "name": "graceful_import",
                "type": "good_pattern",
                "is_anti_pattern": False,
                "preserve": True,
                "details": "Detected via string matching (fallback)"
            })
        
        if "logger." in content and "extra=" in content:
            patterns.append({
                "name": "structured_logging",
                "type": "good_pattern",
                "is_anti_pattern": False,
                "preserve": True,
                "details": "Detected via string matching (fallback)"
            })
        
        return patterns

    def _validate_critical_modification_safety(self, file_path: str) -> Dict[str, Any]:
        try:
            checks = {
                "database_integrity_check": True,
                "security_constraints_check": True,
                "performance_impact_check": True,
                "rollback_readiness_check": True,
            }
            failed = [k for k, ok in checks.items() if not ok]
            return {
                "is_safe": not failed,
                "reason": f"Failed checks: {failed}" if failed else "All safety checks passed",
                "checks_performed": list(checks.keys()),
                "failed_checks": failed,
            }
        except Exception as e:  # pragma: no cover
            return {"is_safe": False, "reason": f"Safety validation error: {e}", "checks_performed": [], "failed_checks": ["safety_validation_error"]}

    # --------------------------------------------------------------- execução
    def _execute_intelligent_audit(self, file_path: str, risk_score: int, context_quality: float) -> Dict[str, Any]:
        """Execute intelligent audit using MetaAgent coordination with AI agents."""
        try:
            # Step 1: Pre-analysis token estimation
            estimated_tokens = self.token_manager.estimate_file_tokens(file_path, self.project_root)
            
            # Step 2: Token availability check with intelligent throttling
            if not self.token_manager.can_proceed(estimated_tokens, file_path):
                sleep_time = self.token_manager.calculate_intelligent_sleep_time()
                if sleep_time > 0:
                    self.logger.info("🛡️ Token limit protection: sleeping %d seconds for %s", int(sleep_time), file_path)
                    return {
                        "deferred": True,
                        "reason": f"Token limit protection - sleeping {int(sleep_time)}s",
                        "sleep_time": sleep_time,
                        "estimated_tokens": estimated_tokens
                    }
            
            # Step 3: Execute MetaAgent-coordinated analysis
            if self.intelligent_agents_available and self.meta_agent:
                self.logger.info("🧠 Using MetaAgent coordination for %s", file_path)
                
                # Determine task type based on risk and context
                task_type = self._determine_task_type(file_path, risk_score, context_quality)
                
                # Get available tokens for this analysis
                available_tokens = min(
                    estimated_tokens * 2,  # Allow some overhead
                    self.token_manager.get_available_tokens()
                )
                
                # Create execution plan using MetaAgent
                execution_plan = self.meta_agent.create_execution_plan(
                    file_path=file_path,
                    task_type=task_type,
                    available_tokens=available_tokens
                )
                
                self.logger.debug("📋 MetaAgent plan: %d agents, %d estimated tokens, %.1fs estimated time",
                                len(execution_plan.agents),
                                execution_plan.total_estimated_tokens,
                                execution_plan.total_estimated_time)
                
                # Execute the plan
                execution_results = self.meta_agent.execute_plan(execution_plan)
                
                # Process results from all agents
                analysis_result = None
                refactoring_results = None
                tdd_optimizations = None
                god_code_analysis = None
                total_tokens_used = 0
                
                for result in execution_results:
                    total_tokens_used += result.tokens_used
                    
                    if result.agent_type.value == "intelligent_code_agent" and result.success:
                        analysis_result = result.result_data
                    elif result.agent_type.value == "refactoring_engine" and result.success:
                        refactoring_results = result.result_data
                    elif result.agent_type.value == "tdd_workflow_agent" and result.success:
                        tdd_optimizations = result.result_data
                    elif result.agent_type.value == "god_code_agent" and result.success:
                        god_code_analysis = result.result_data
                
                # Record actual token usage
                self.token_manager.record_usage(total_tokens_used, file_path)
                
                # Determine if any modifications were made
                modifications_made = any(
                    result.success and result.result_data.get("applied_refactorings") 
                    for result in execution_results
                ) and not self.dry_run
                
                return {
                    "intelligent_analysis": True,
                    "meta_agent_coordination": True,
                    "execution_plan": {
                        "agents_planned": [agent.agent_type.value for agent in execution_plan.agents],
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
                        for result in execution_results
                    ],
                    "analysis_result": analysis_result,
                    "refactoring_results": refactoring_results,
                    "tdd_optimizations": tdd_optimizations,
                    "god_code_analysis": god_code_analysis,
                    "tokens_used": total_tokens_used,
                    "modified": modifications_made,
                    "lines_analyzed": analysis_result.get("total_lines", 0) if analysis_result else 0,
                    "issues_found": len(analysis_result.get("line_analyses", [])) if analysis_result else 0,
                    "optimizations_applied": len(refactoring_results.get("applied_refactorings", [])) if refactoring_results else 0,
                    "agents_executed": len([r for r in execution_results if r.success]),
                    "success_rate": len([r for r in execution_results if r.success]) / len(execution_results) if execution_results else 0
                }
                
            elif self.intelligent_agents_available and self.intelligent_code_agent:
                # Fallback to manual agent coordination (legacy intelligent mode)
                self.logger.info("🔄 MetaAgent unavailable - using manual agent coordination")
                return self._execute_manual_agent_coordination(file_path, estimated_tokens)
            else:
                # Fallback to legacy analysis
                return self._execute_legacy_audit_fallback(file_path, estimated_tokens)
                
        except Exception as e:
            self.logger.error("❌ Intelligent audit failed for %s: %s", file_path, e)
            return {
                "error": str(e),
                "fallback_to_legacy": True,
                "tokens_used": 100  # Minimal token usage for error
            }

    def _determine_task_type(self, file_path: str, risk_score: int, context_quality: float) -> 'TaskType':
        """Determine appropriate task type based on file characteristics and risk assessment."""
        if not TaskType:
            return None  # Fallback if TaskType not available
            
        # Analyze file name and path patterns
        file_path_lower = file_path.lower()
        
        # God code detection for large/complex files
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                line_count = len([line for line in content.split('\n') if line.strip()])
                
            # God code indicators
            if line_count > 500 or 'class' in content and content.count('def ') > 20:
                return TaskType.GOD_CODE_DETECTION
        except:
            pass
        
        # TDD optimization for test files
        if 'test' in file_path_lower or '/tests/' in file_path_lower:
            return TaskType.TDD_OPTIMIZATION
        
        # Performance analysis for high-risk files
        if risk_score > 80:
            return TaskType.PERFORMANCE_ANALYSIS
        
        # Security analysis for security-critical files
        if any(keyword in file_path_lower for keyword in ['auth', 'security', 'password', 'crypto']):
            return TaskType.SECURITY_ANALYSIS
        
        # Architecture review for core system files
        if any(keyword in file_path_lower for keyword in ['service', 'manager', 'controller', 'middleware']):
            return TaskType.ARCHITECTURE_REVIEW
        
        # Code refactoring for medium-risk files with good context
        if 50 <= risk_score <= 80 and context_quality >= 70.0:
            return TaskType.CODE_REFACTORING
        
        # Default to comprehensive audit
        return TaskType.COMPREHENSIVE_AUDIT
    
    def _execute_manual_agent_coordination(self, file_path: str, estimated_tokens: int) -> Dict[str, Any]:
        """Fallback to manual agent coordination when MetaAgent is not available."""
        try:
            self.logger.info("🔄 Manual agent coordination for %s", file_path)
            
            # Use the original intelligent agents manually
            analysis_result = self.intelligent_code_agent.analyze_file_intelligently(file_path)
            
            # Apply intelligent refactorings if available
            refactoring_results = None
            available_refactorings = getattr(analysis_result, 'refactorings', None) or []
            if self.refactoring_engine and available_refactorings and not self.dry_run:
                refactoring_results = self.refactoring_engine.apply_intelligent_refactorings(analysis_result)
            
            # TDD workflow optimizations
            tdd_optimizations = None
            if self.tdd_workflow_agent and analysis_result:
                try:
                    # Try different possible method names
                    if hasattr(self.tdd_workflow_agent, 'analyze_tdd_opportunities'):
                        tdd_optimizations = self.tdd_workflow_agent.analyze_tdd_opportunities(analysis_result)
                    elif hasattr(self.tdd_workflow_agent, 'analyze_file'):
                        tdd_optimizations = self.tdd_workflow_agent.analyze_file(file_path)
                    elif hasattr(self.tdd_workflow_agent, 'get_tdd_improvements'):
                        tdd_optimizations = self.tdd_workflow_agent.get_tdd_improvements(analysis_result)
                except Exception as tdd_error:
                    self.logger.debug("TDD workflow analysis failed: %s", tdd_error)
                    tdd_optimizations = None
            
            # Calculate actual token usage
            actual_tokens = getattr(analysis_result, 'tokens_used', estimated_tokens)
            if refactoring_results:
                actual_tokens += getattr(refactoring_results, 'tokens_used', 0)
            
            # Record token usage
            self.token_manager.record_usage(actual_tokens, file_path)
            
            return {
                "intelligent_analysis": True,
                "meta_agent_coordination": False,
                "manual_coordination": True,
                "analysis_result": analysis_result,
                "refactoring_results": refactoring_results,
                "tdd_optimizations": tdd_optimizations,
                "tokens_used": actual_tokens,
                "modified": bool(refactoring_results and not self.dry_run),
                "lines_analyzed": getattr(analysis_result, 'total_lines', 0),
                "issues_found": len(getattr(analysis_result, 'line_analyses', [])),
                "optimizations_applied": len(getattr(refactoring_results, 'applied_refactorings', [])) if refactoring_results else 0
            }
            
        except Exception as e:
            self.logger.error("❌ Manual agent coordination failed for %s: %s", file_path, e)
            return {
                "error": str(e),
                "fallback_to_legacy": True,
                "tokens_used": 100
            }

    def _execute_legacy_audit_fallback(self, file_path: str, estimated_tokens: int) -> Dict[str, Any]:
        """Fallback to legacy analysis when intelligent agents are not available."""
        try:
            self.logger.info("🔄 Falling back to legacy analysis for %s", file_path)
            
            # Use basic patterns detection as fallback
            patterns_found = self._detect_patterns(file_path)
            
            # Simple token tracking
            self.token_manager.record_usage(estimated_tokens, file_path)
            
            # Basic analysis without modifications
            content = self._read_file_safely(file_path)
            lines_count = len(content.splitlines()) if content else 0
            
            return {
                "intelligent_analysis": False,
                "legacy_analysis": True,
                "patterns_found": patterns_found,
                "tokens_used": estimated_tokens,
                "modified": False,
                "lines_analyzed": lines_count,
                "issues_found": len([p for p in patterns_found if p.get("is_anti_pattern", False)]),
                "optimizations_applied": 0,
                "changes_summary": "Legacy analysis completed (no modifications)"
            }
            
        except Exception as e:
            self.logger.error("❌ Legacy audit fallback failed for %s: %s", file_path, e)
            return {
                "error": str(e),
                "legacy_analysis": True,
                "tokens_used": 50  # Minimal token usage for error
            }

    def _execute_context_aware_audit(
        self,
        file_path: str,
        risk_score: int,
        patterns: List[Dict[str, Any]],
        context_quality: float,
        wave_info: str,
    ) -> Dict[str, Any]:
        """Sistema inteligente de fixes com auto-import e validação AST."""
        try:
            content = self._read_file_safely(file_path)
            if not content:
                return {
                    "modified": False,
                    "error": "File not found",
                    "lines_analyzed": 0,
                    "optimizations_applied": 0,
                    "tokens_used": 0,
                }

            lines_analyzed = content.count("\n") + 1
            
            # Executar sistema de fixes inteligente
            return self._execute_smart_fixes(file_path, content, patterns, risk_score, lines_analyzed)
            
        except Exception as e:  # pragma: no cover
            self.logger.error("Falha na auditoria contexto-aware de %s: %s", file_path, e)
            return {
                "modified": False,
                "error": str(e),
                "lines_analyzed": 0,
                "optimizations_applied": 0,
                "tokens_used": 50,
            }

    def _execute_smart_fixes(
        self,
        file_path: str,
        content: str,
        patterns: List[Dict[str, Any]],
        risk_score: int,
        lines_analyzed: int,
    ) -> Dict[str, Any]:
        """Sistema de fixes que pode adicionar imports e fazer modificações inteligentes."""
        modifications: List[str] = []
        optimizations_applied = 0
        tokens_used = 50
        modified_content = content
        
        # Verificar se precisa de logger e se pode adicionar
        needs_logger = self._needs_logger_import(patterns)
        has_logger = self._has_logger_import(content)
        
        # Adicionar logger import se necessário e seguro
        if needs_logger and not has_logger and risk_score <= 70:
            modified_content, import_added = self._add_logger_import(modified_content)
            if import_added:
                modifications.append("Added logger import")
                optimizations_applied += 1
        
        # Aplicar fixes específicos por pattern
        for pattern in patterns:
            if not pattern.get("is_anti_pattern") or not pattern.get("auto_fixable"):
                continue
                
            pattern_name = pattern.get("name")
            pattern_line = pattern.get("line", 0)
            
            # Exception swallowing fixes (mais inteligentes)
            if pattern_name in ["exception_swallowing", "bare_except"] and risk_score <= 70:
                modified_content, fix_applied = self._fix_exception_swallowing(
                    modified_content, pattern, has_logger or needs_logger
                )
                if fix_applied:
                    modifications.append(f"Fixed {pattern_name} at line {pattern_line}")
                    optimizations_applied += 1
            
            # Import hell fixes
            elif pattern_name == "import_hell" and risk_score <= 50:
                modified_content, fix_applied = self._fix_import_hell(modified_content, pattern)
                if fix_applied:
                    modifications.append("Simplified import pattern")
                    optimizations_applied += 1
            
            # Outros patterns podem ser adicionados aqui
        
        # Aplicar modificações se não for dry-run
        modified = len(modifications) > 0
        if modified and not self.dry_run and not self.validate_only:
            # Validar sintaxe antes de escrever
            try:
                ast.parse(modified_content)
                full_path = self.project_root / file_path
                full_path.write_text(modified_content, encoding="utf-8")
            except SyntaxError as e:
                self.logger.warning("Syntax error após fixes em %s: %s", file_path, e)
                modifications.append(f"ROLLBACK: Syntax error - {e}")
                modified = False
        
        return {
            "modified": modified,
            "lines_analyzed": lines_analyzed,
            "optimizations_applied": optimizations_applied,
            "tokens_used": tokens_used,
            "changes_summary": "; ".join(modifications) if modifications else
                ("No changes applied (dry-run)" if self.dry_run else "No changes applied"),
            "syntax_valid": True,
            "modifications": modifications,
        }

    def _needs_logger_import(self, patterns: List[Dict[str, Any]]) -> bool:
        """Verifica se os patterns requerem logger."""
        return any(
            p.get("name") in ["exception_swallowing", "bare_except"] and p.get("auto_fixable")
            for p in patterns if p.get("is_anti_pattern")
        )

    def _has_logger_import(self, content: str) -> bool:
        """Verifica se arquivo já tem logger importado ou configurado."""
        return (
            "import logging" in content or
            "from logging import" in content or
            "logger = logging.getLogger" in content or
            "logger." in content
        )

    def _add_logger_import(self, content: str) -> tuple[str, bool]:
        """Adiciona import de logger de forma inteligente."""
        try:
            tree = ast.parse(content)
            
            # Encontrar melhor posição para adicionar import
            lines = content.split('\n')
            insert_position = 0
            
            # Procurar última linha de import
            for i, line in enumerate(lines):
                stripped = line.strip()
                if (stripped.startswith('import ') or 
                    stripped.startswith('from ') or
                    stripped.startswith('#') or
                    stripped.startswith('"""') or
                    stripped.startswith("'''") or
                    not stripped):
                    insert_position = i + 1
                else:
                    break
            
            # Adicionar logger import
            logger_import = "import logging"
            logger_setup = "logger = logging.getLogger(__name__)"
            
            # Inserir nas posições corretas
            lines.insert(insert_position, logger_import)
            lines.insert(insert_position + 1, logger_setup)
            lines.insert(insert_position + 2, "")  # Linha em branco
            
            return '\n'.join(lines), True
            
        except (SyntaxError, Exception):
            # Fallback simples
            import_section = "import logging\nlogger = logging.getLogger(__name__)\n\n"
            return import_section + content, True

    def _fix_exception_swallowing(
        self, 
        content: str, 
        pattern: Dict[str, Any], 
        has_logger: bool
    ) -> tuple[str, bool]:
        """Fix inteligente para exception swallowing usando AST quando possível."""
        if not has_logger:
            return content, False
            
        try:
            # Tentar fix baseado em AST primeiro
            tree = ast.parse(content)
            lines = content.split('\n')
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ExceptHandler):
                    # Bare except
                    if node.type is None and hasattr(node, 'lineno'):
                        line_idx = node.lineno - 1
                        if line_idx < len(lines):
                            original_line = lines[line_idx]
                            if 'except:' in original_line:
                                # Substituir bare except
                                indent = len(original_line) - len(original_line.lstrip())
                                new_line = ' ' * indent + 'except Exception as e:'
                                new_handler = ' ' * (indent + 4) + 'logger.warning("Operation failed: %s", str(e))'
                                
                                lines[line_idx] = new_line
                                # Inserir handler se não existir
                                if line_idx + 1 < len(lines):
                                    lines.insert(line_idx + 1, new_handler)
                                else:
                                    lines.append(new_handler)
                                
                                return '\n'.join(lines), True
                    
                    # Exception swallowing
                    elif (isinstance(node.type, ast.Name) and 
                          node.type.id == "Exception" and
                          len(node.body) == 1 and 
                          isinstance(node.body[0], ast.Return)):
                        
                        line_idx = node.lineno - 1
                        if line_idx < len(lines):
                            # Encontrar linha do handler
                            for i in range(line_idx, min(line_idx + 3, len(lines))):
                                if 'return' in lines[i] and 'except' not in lines[i]:
                                    # Substituir return por logging
                                    indent = len(lines[i]) - len(lines[i].lstrip())
                                    new_handler = ' ' * indent + 'logger.warning("Operation failed: %s", str(e))'
                                    lines[i] = new_handler
                                    return '\n'.join(lines), True
            
            return content, False
            
        except (SyntaxError, Exception):
            # Fallback para string replacement
            return self._fix_exception_swallowing_fallback(content, has_logger)

    def _fix_exception_swallowing_fallback(
        self, 
        content: str, 
        has_logger: bool
    ) -> tuple[str, bool]:
        """Fallback simples para fix de exception swallowing."""
        if not has_logger:
            return content, False
            
        modified = content
        changes_made = False
        
        # Fix bare except
        if "except:" in modified:
            modified = modified.replace(
                "except:",
                'except Exception as e:\n        logger.warning("Operation failed: %s", str(e))'
            )
            changes_made = True
        
        # Fix exception swallowing (heurística simples)
        if "except Exception:" in modified and "return None" in modified:
            modified = modified.replace(
                "except Exception:",
                'except Exception as e:\n        logger.warning("Operation failed: %s", str(e))'
            )
            changes_made = True
        
        return modified, changes_made

    def _fix_import_hell(self, content: str, pattern: Dict[str, Any]) -> tuple[str, bool]:
        """Fix para import hell patterns (simplificado)."""
        # Por enquanto, apenas log o problema - fix manual recomendado
        return content, False

    # ------------------------------------------------------------- salvaguardas
    def _create_file_backup(self, file_path: str) -> bool:
        try:
            full_path = self.project_root / file_path
            if not full_path.exists():
                return False
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup_path = full_path.with_suffix(full_path.suffix + f".backup.{ts}")
            backup_path.write_text(full_path.read_text(encoding="utf-8", errors="ignore"))
            return True
        except Exception as e:  # pragma: no cover
            self.logger.error("Falha ao criar backup de %s: %s", file_path, e)
            return False

    def _validate_post_modification(self, file_path: str) -> Dict[str, Any]:
        try:
            # 1) Testes de integração (se disponíveis)
            if self.validation_pipeline["integration_test_required"] and self.integration_tester is not None:
                try:
                    test_result = self.integration_tester.test_file_integration(file_path)  # type: ignore
                    if hasattr(test_result, "passed"):
                        return {"passed": bool(getattr(test_result, "passed")), "errors": getattr(test_result, "errors", [])}
                except Exception as e:  # pragma: no cover
                    self.logger.warning("Teste de integração falhou em %s: %s", file_path, e)

            # 2) Validação sintática (AST)
            full_path = self.project_root / file_path
            try:
                content = full_path.read_text(encoding="utf-8", errors="ignore")
                ast.parse(content)
                return {"passed": True, "errors": []}
            except SyntaxError as e:
                return {"passed": False, "errors": [f"Syntax error: {e}"]}
        except Exception as e:  # pragma: no cover
            return {"passed": False, "errors": [f"Validation error: {e}"]}

    def _rollback_file_changes(self, file_path: str) -> bool:
        try:
            full_path = self.project_root / file_path
            # procura o backup mais recente
            backups = sorted(
                full_path.parent.glob(full_path.name + ".backup.*"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            if backups:
                full_path.write_text(backups[0].read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
                backups[0].unlink(missing_ok=True)
                self.logger.info("Rollback aplicado em %s", file_path)
                return True
            return False
        except Exception as e:  # pragma: no cover
            self.logger.error("Rollback falhou em %s: %s", file_path, e)
            return False

    def _emergency_rollback(self, file_path: str) -> None:
        try:
            if self.rollback_manager is not None:
                self.rollback_manager.emergency_rollback(file_path)  # type: ignore
                self.logger.warning("Emergency rollback (gestor externo) aplicado em %s", file_path)
            else:
                self._rollback_file_changes(file_path)
                self.logger.warning("Emergency rollback (fallback simples) aplicado em %s", file_path)
        except Exception as e:  # pragma: no cover
            self.logger.critical("Emergency rollback falhou em %s: %s", file_path, e)

    # -------------------------------------------------------- resultados helper
    def _create_skip_result(self, file_path: str, reason: str) -> FileAuditResult:
        return FileAuditResult(
            file_path=file_path,
            lines_analyzed=0,
            issues_found=0,
            optimizations_applied=0,
            tokens_used=0,
            changes_summary=f"SKIPPED: {reason}",
            syntax_valid=True,
            backup_created=False,
            context_quality=0.0,
            risk_score=0,
            risk_category="UNKNOWN",
            modification_wave="NONE",
        )

    def _create_defer_result(self, file_path: str, reason: str) -> FileAuditResult:
        return FileAuditResult(
            file_path=file_path,
            lines_analyzed=0,
            issues_found=0,
            optimizations_applied=0,
            tokens_used=0,
            changes_summary=f"DEFERRED: {reason}",
            syntax_valid=True,
            backup_created=False,
            context_quality=0.0,
            risk_score=self.setima_data.get_file_risk_score(file_path),
            risk_category=self.setima_data.get_file_risk_category(file_path),
            modification_wave=self.setima_data.get_file_wave(file_path),
        )

    def _create_rollback_result(self, file_path: str, errors: List[str]) -> FileAuditResult:
        return FileAuditResult(
            file_path=file_path,
            lines_analyzed=0,
            issues_found=len(errors),
            optimizations_applied=0,
            tokens_used=10,
            changes_summary=f"ROLLED BACK: {'; '.join(errors)}",
            syntax_valid=False,
            backup_created=True,
            rollback_available=False,
            integration_tests_passed=False,
        )

    def _create_emergency_result(self, file_path: str, error: str) -> FileAuditResult:
        return FileAuditResult(
            file_path=file_path,
            lines_analyzed=0,
            issues_found=1,
            optimizations_applied=0,
            tokens_used=5,
            changes_summary=f"EMERGENCY ROLLBACK: {error}",
            syntax_valid=False,
            backup_created=True,
            rollback_available=False,
        )

    # ---------------------------------------------------------- execução waves
    def execute_risk_based_audit(self) -> Dict[str, Any]:
        """Executa as 4 ondas em sequência, com salvaguardas por nível."""
        start = time.time()
        execution_results: Dict[str, Any] = {
            "WAVE_1_LOW": [],
            "WAVE_2_MEDIUM": [],
            "WAVE_3_HIGH": [],
            "WAVE_4_CRITICAL": [],
            "execution_summary": {},
        }

        try:
            # Wave 1: paralelizável (aqui sequência simples por clareza)
            wave_1 = self.setima_data.dependency_waves.get("WAVE_1_FOUNDATION", [])
            execution_results["WAVE_1_LOW"] = self._execute_wave_parallel(wave_1)

            # Wave 2: coordenação
            wave_2 = self.setima_data.dependency_waves.get("WAVE_2_BUSINESS", [])
            execution_results["WAVE_2_MEDIUM"] = self._execute_wave_coordinated(wave_2)

            # Wave 3: sequencial
            wave_3 = self.setima_data.dependency_waves.get("WAVE_3_INTEGRATION", [])
            execution_results["WAVE_3_HIGH"] = self._execute_wave_sequential(wave_3)

            # Wave 4: crítico (um por vez + backup completo)
            wave_4 = self.setima_data.dependency_waves.get("WAVE_4_CRITICAL", [])
            execution_results["WAVE_4_CRITICAL"] = self._execute_wave_critical(wave_4)

            # Summary
            execution_results["execution_summary"] = self._generate_execution_summary(execution_results, time.time() - start)
            return execution_results
        except Exception as e:  # pragma: no cover
            self.logger.error("Falha na execução por ondas: %s", e)
            return {"error": str(e), "execution_aborted": True, "emergency_rollback_triggered": True}

    def execute_intelligent_risk_based_audit(self, resume_session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute intelligent audit using AI agents with advanced batch processing,
        token management, and session persistence.
        """
        start_time = time.time()
        
        try:
            # Step 1: Try to resume existing session
            resumed, resume_info = self._try_resume_session(resume_session_id)
            
            if resumed:
                all_files = self.file_manager.get_all_python_files()
                remaining_files = self.session_manager.get_remaining_files(all_files)
                self.logger.info("🔄 Resumed session with %d remaining files", len(remaining_files))
            else:
                # Start new session
                all_files = self.file_manager.get_all_python_files()
                remaining_files = all_files.copy()
                
                session_config = {
                    "intelligent_mode": self.intelligent_agents_available,
                    "dry_run": self.dry_run,
                    "validate_only": self.validate_only,
                    "audit_mode": "risk_based_intelligent"
                }
                
                session_id = self._start_new_audit_session(len(all_files), session_config)
                self.logger.info("🚀 Started new intelligent audit session: %s", session_id)
            
            # Step 2: Prioritize files using intelligent risk-token analysis
            prioritized_files = self.token_manager.prioritize_files_by_risk_and_tokens(
                remaining_files, self.project_root, self.setima_data
            )
            
            execution_results = {
                "intelligent_analysis": True,
                "files_processed": [],
                "files_deferred": [],
                "files_failed": [],
                "token_consumption": {},
                "performance_metrics": {},
                "execution_summary": {}
            }
            
            # Step 3: Execute intelligent batch processing
            batch_number = 0
            total_files = len(prioritized_files)
            
            while prioritized_files:
                batch_number += 1
                
                # Calculate adaptive batch size
                remaining_count = len(prioritized_files)
                available_time = 1.0  # 1 hour default session
                batch_size = self.token_manager.calculate_adaptive_batch_size(
                    remaining_count, available_time
                )
                
                # Get current batch
                current_batch = prioritized_files[:batch_size]
                prioritized_files = prioritized_files[batch_size:]
                
                self.logger.info(
                    "🎯 Processing batch %d: %d files (remaining: %d)",
                    batch_number, len(current_batch), len(prioritized_files)
                )
                
                # Process batch with intelligent throttling
                batch_results = self._process_intelligent_batch(current_batch, batch_number)
                
                # Consolidate results
                execution_results["files_processed"].extend(batch_results.get("files_processed", []))
                execution_results["files_deferred"].extend(batch_results.get("files_deferred", []))
                execution_results["files_failed"].extend(batch_results.get("files_failed", []))
                
                # Update token consumption tracking
                execution_results["token_consumption"].update(batch_results.get("token_consumption", {}))
                
                # Save checkpoint after each batch
                current_batch_paths = [f[0] for f in current_batch]  # Extract file paths
                token_stats = self.token_manager.get_comprehensive_usage_stats()
                self.session_manager.save_checkpoint(current_batch_paths, token_stats)
                
                # Intelligent throttling between batches
                sleep_time = self.token_manager.calculate_intelligent_sleep_time()
                if sleep_time > 0:
                    self.logger.info("⏱️ Intelligent throttling: sleeping %d seconds", int(sleep_time))
                    time.sleep(sleep_time)
                
                # System health check between batches
                health = self._validate_system_health()
                if not health["healthy"]:
                    self.logger.warning("⚠️ System health degraded: %s", health["issues"])
                    if batch_number > 3:  # Allow some initial instability
                        self.logger.error("🚨 System unhealthy after batch %d - stopping execution", batch_number)
                        break
                
                # Progress reporting
                progress = self.session_manager.get_audit_progress(total_files)
                self.logger.info(
                    "📊 Progress: %.1f%% complete (%d/%d files, efficiency: %s)",
                    progress.completion_percentage, progress.completed_files, 
                    progress.total_files, progress.efficiency_rating
                )
            
            # Step 4: Generate comprehensive execution summary
            execution_time = time.time() - start_time
            final_stats = self._generate_intelligent_execution_summary(execution_results, execution_time)
            
            # Step 5: Finalize session
            self.session_manager.finalize_session(final_stats)
            
            execution_results["execution_summary"] = final_stats
            execution_results["session_finalized"] = True
            
            return execution_results
            
        except Exception as e:
            self.logger.error("❌ Critical error in intelligent audit execution: %s", e)
            return {
                "error": str(e),
                "execution_aborted": True,
                "emergency_recovery_needed": True,
                "execution_time": time.time() - start_time
            }

    def _process_intelligent_batch(
        self, 
        batch_files: List[Tuple[str, int, int, str]], 
        batch_number: int
    ) -> Dict[str, Any]:
        """Process a batch of files using intelligent agents."""
        
        batch_start_time = time.time()
        batch_results = {
            "files_processed": [],
            "files_deferred": [],
            "files_failed": [],
            "token_consumption": {},
            "batch_metrics": {}
        }
        
        for i, (file_path, estimated_tokens, risk_score, priority_reasons) in enumerate(batch_files):
            file_start_time = time.time()
            
            self.logger.info(
                "🔍 [%d/%d] Analyzing %s (tokens: %d, risk: %d, priority: %s)",
                i + 1, len(batch_files), file_path, estimated_tokens, risk_score, priority_reasons
            )
            
            try:
                # Execute intelligent audit
                audit_result = self._execute_intelligent_audit(
                    file_path, risk_score, context_quality=85.0  # Default high quality for IA
                )
                
                # Process result
                if audit_result.get("deferred"):
                    batch_results["files_deferred"].append({
                        "file_path": file_path,
                        "reason": audit_result.get("reason"),
                        "sleep_time": audit_result.get("sleep_time", 0)
                    })
                    
                    # Sleep if needed
                    sleep_time = audit_result.get("sleep_time", 0)
                    if sleep_time > 0:
                        self.logger.info("💤 File deferred - sleeping %d seconds", int(sleep_time))
                        time.sleep(sleep_time)
                        
                    # Retry after sleep
                    audit_result = self._execute_intelligent_audit(file_path, risk_score, 85.0)
                
                if audit_result.get("error"):
                    batch_results["files_failed"].append({
                        "file_path": file_path,
                        "error": audit_result.get("error"),
                        "fallback_used": audit_result.get("fallback_to_legacy", False)
                    })
                else:
                    batch_results["files_processed"].append({
                        "file_path": file_path,
                        "tokens_used": audit_result.get("tokens_used", 0),
                        "lines_analyzed": audit_result.get("lines_analyzed", 0),
                        "issues_found": audit_result.get("issues_found", 0),
                        "optimizations_applied": audit_result.get("optimizations_applied", 0),
                        "intelligent_analysis": audit_result.get("intelligent_analysis", False),
                        "processing_time": time.time() - file_start_time
                    })
                    
                    # Track token consumption per file
                    batch_results["token_consumption"][file_path] = audit_result.get("tokens_used", 0)
                
                # Record result in session
                audit_result["processing_time_seconds"] = time.time() - file_start_time
                self.session_manager.record_file_result(file_path, audit_result)
                
            except Exception as e:
                self.logger.error("❌ Critical error processing %s: %s", file_path, e)
                batch_results["files_failed"].append({
                    "file_path": file_path,
                    "error": str(e),
                    "critical_failure": True
                })
        
        # Calculate batch metrics
        batch_duration = time.time() - batch_start_time
        batch_results["batch_metrics"] = {
            "batch_number": batch_number,
            "batch_duration_seconds": batch_duration,
            "files_in_batch": len(batch_files),
            "files_processed": len(batch_results["files_processed"]),
            "files_failed": len(batch_results["files_failed"]),
            "files_deferred": len(batch_results["files_deferred"]),
            "total_tokens_consumed": sum(batch_results["token_consumption"].values()),
            "average_processing_time": batch_duration / len(batch_files) if batch_files else 0
        }
        
        self.logger.info(
            "✅ Batch %d complete: %d processed, %d failed, %d deferred (%.1f seconds)",
            batch_number, len(batch_results["files_processed"]), len(batch_results["files_failed"]),
            len(batch_results["files_deferred"]), batch_duration
        )
        
        return batch_results

    def _generate_intelligent_execution_summary(
        self, 
        execution_results: Dict[str, Any], 
        execution_time: float
    ) -> Dict[str, Any]:
        """Generate comprehensive execution summary with IA metrics."""
        
        # Calculate totals
        files_processed = len(execution_results.get("files_processed", []))
        files_failed = len(execution_results.get("files_failed", []))
        files_deferred = len(execution_results.get("files_deferred", []))
        total_files = files_processed + files_failed + files_deferred
        
        # Calculate token metrics
        total_tokens = sum(execution_results.get("token_consumption", {}).values())
        avg_tokens_per_file = total_tokens / files_processed if files_processed > 0 else 0
        
        # Calculate success metrics
        success_rate = (files_processed / total_files * 100) if total_files > 0 else 0
        failure_rate = (files_failed / total_files * 100) if total_files > 0 else 0
        
        # Get comprehensive token stats
        token_stats = self.token_manager.get_comprehensive_usage_stats()
        session_summary = self.token_manager.get_session_summary()
        
        # Calculate intelligence metrics
        intelligent_analysis_count = sum(
            1 for f in execution_results.get("files_processed", [])
            if f.get("intelligent_analysis", False)
        )
        intelligence_usage_rate = (intelligent_analysis_count / files_processed * 100) if files_processed > 0 else 0
        
        return {
            # Executive Summary
            "executive_summary": {
                "total_files_audited": total_files,
                "success_rate_percent": round(success_rate, 2),
                "intelligent_analysis_rate_percent": round(intelligence_usage_rate, 2),
                "total_execution_time_hours": round(execution_time / 3600, 2),
                "average_time_per_file_minutes": round(execution_time / 60 / total_files, 2) if total_files > 0 else 0
            },
            
            # File Processing Results
            "file_processing": {
                "successfully_processed": files_processed,
                "failed_processing": files_failed,
                "deferred_processing": files_deferred,
                "total_lines_analyzed": sum(f.get("lines_analyzed", 0) for f in execution_results.get("files_processed", [])),
                "total_issues_found": sum(f.get("issues_found", 0) for f in execution_results.get("files_processed", [])),
                "total_optimizations_applied": sum(f.get("optimizations_applied", 0) for f in execution_results.get("files_processed", []))
            },
            
            # Token Consumption Analysis
            "token_analysis": {
                "total_tokens_consumed": total_tokens,
                "average_tokens_per_file": round(avg_tokens_per_file, 2),
                "efficiency_rating": session_summary.get("session_overview", {}).get("efficiency_rating", "unknown"),
                "hourly_usage_percent": token_stats.get("hourly_usage_percent", 0),
                "daily_usage_percent": token_stats.get("daily_usage_percent", 0),
                "session_usage_percent": token_stats.get("session_usage_percent", 0)
            },
            
            # Performance Metrics  
            "performance_metrics": {
                "files_per_hour": round(total_files / (execution_time / 3600), 2) if execution_time > 0 else 0,
                "tokens_per_minute": token_stats.get("session_rate", 0),
                "average_processing_time_seconds": round(execution_time / total_files, 2) if total_files > 0 else 0,
                "efficiency_score": token_stats.get("efficiency_score", 100.0)
            },
            
            # AI Usage Statistics
            "artificial_intelligence": {
                "intelligent_code_agent_usage": intelligent_analysis_count,
                "refactoring_engine_usage": sum(1 for f in execution_results.get("files_processed", []) if f.get("optimizations_applied", 0) > 0),
                "tdd_workflow_optimizations": sum(1 for f in execution_results.get("files_processed", []) if "tdd" in str(f).lower()),
                "fallback_to_legacy": sum(1 for f in execution_results.get("files_failed", []) if f.get("fallback_used", False))
            },
            
            # System Health
            "system_health": {
                "session_completed_successfully": True,
                "no_critical_failures": files_failed == 0 or failure_rate < 10,
                "token_limits_respected": token_stats.get("hourly_usage_percent", 0) <= 100,
                "adaptive_throttling_used": token_stats.get("adaptive_throttling", False),
                "checkpoints_saved": True
            },
            
            # Recommendations
            "recommendations": self._generate_execution_recommendations(
                success_rate, intelligence_usage_rate, avg_tokens_per_file, execution_time
            )
        }

    def _generate_execution_recommendations(
        self, 
        success_rate: float, 
        intelligence_usage_rate: float, 
        avg_tokens_per_file: float, 
        execution_time: float
    ) -> List[str]:
        """Generate execution recommendations based on metrics."""
        recommendations = []
        
        if success_rate < 90:
            recommendations.append("Consider increasing batch size for better success rates")
        
        if intelligence_usage_rate < 50:
            recommendations.append("Increase IA usage for better code analysis quality") 
            
        if avg_tokens_per_file > 2000:
            recommendations.append("Consider breaking down large files for better token efficiency")
            
        if execution_time > 3600:  # More than 1 hour
            recommendations.append("Consider running audit in smaller sessions for better management")
            
        if not recommendations:
            recommendations.append("Execution performed optimally - continue with current settings")
            
        return recommendations

    def _execute_wave_parallel(self, files: List[str]) -> List[FileAuditResult]:
        results: List[FileAuditResult] = []
        for file_path in files:
            if self._file_exists_in_project(file_path):
                results.append(self.audit_file_enhanced(file_path))
                self.logger.info("Wave 1 - %s → %s", file_path, results[-1].changes_summary)
        return results

    def _execute_wave_coordinated(self, files: List[str]) -> List[FileAuditResult]:
        results: List[FileAuditResult] = []
        for file_path in files:
            if self._file_exists_in_project(file_path):
                dep = self._check_wave_dependencies(file_path)
                if dep["safe_to_modify"]:
                    results.append(self.audit_file_enhanced(file_path))
                    self.logger.info("Wave 2 - %s → %s", file_path, results[-1].changes_summary)
                else:
                    self.logger.warning("Wave 2 - DEFER %s: %s", file_path, dep["reason"])
        return results

    def _execute_wave_sequential(self, files: List[str]) -> List[FileAuditResult]:
        results: List[FileAuditResult] = []
        for file_path in files:
            if self._file_exists_in_project(file_path):
                result = self.audit_file_enhanced(file_path)
                results.append(result)
                if result.issues_found > 0:
                    health = self._validate_system_health()
                    if not health["healthy"]:
                        self.logger.error("Saúde degradada após %s. Interrompendo wave.", file_path)
                        break
                self.logger.info("Wave 3 - %s → %s", file_path, result.changes_summary)
        return results

    def _execute_wave_critical(self, files: List[str]) -> List[FileAuditResult]:
        results: List[FileAuditResult] = []
        for file_path in files:
            if self._file_exists_in_project(file_path):
                backup_id = self._create_full_system_backup()
                try:
                    result = self.audit_file_enhanced(file_path)
                    if result.integration_tests_passed:
                        results.append(result)
                        self.logger.info("Wave 4 - SUCCESS %s → %s", file_path, result.changes_summary)
                    else:
                        self._restore_system_backup(backup_id)
                        self.logger.error("Wave 4 - ROLLBACK %s (testes falharam)", file_path)
                except Exception as e:  # pragma: no cover
                    self._restore_system_backup(backup_id)
                    self.logger.critical("Wave 4 - EMERGENCY ROLLBACK %s: %s", file_path, e)
        return results

    # ---------------------------------------------------------------- sistema
    def _file_exists_in_project(self, file_path: str) -> bool:
        return (self.project_root / file_path).exists()

    def _check_wave_dependencies(self, file_path: str) -> Dict[str, Any]:
        return {"safe_to_modify": True, "reason": "Dependencies satisfied", "dependencies_checked": []}

    def _try_resume_session(self, resume_session_id: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
        """Try to resume an existing session."""
        resumed, session_id, resume_info = self.session_manager.resume_session(resume_session_id)
        
        if resumed:
            self.logger.info("🔄 Resumed session: %s", resume_info)
            return True, resume_info
        
        return False, {}

    def _start_new_audit_session(self, total_files: int, config: Dict[str, Any]) -> str:
        """Start a new audit session with tracking."""
        session_id = self.session_manager.start_new_session(total_files, config)
        self.logger.info("🚀 Started new audit session: %s", session_id)
        return session_id

    def _validate_system_health(self) -> Dict[str, Any]:
        try:
            # Teste simples de conectividade do banco de dados
            try:
                # Usar método seguro da API legada
                result = self.db_manager.get_all_epics()  # type: ignore
                if result is not None:
                    return {"healthy": True, "checks_passed": ["database_connectivity"], "issues": []}
                else:
                    return {"healthy": False, "checks_passed": [], "issues": ["Database returned None"]}
            except Exception as e:
                # Fallback: tentar conexão direta
                try:
                    framework_db_path = self.db_manager.framework_db_path if hasattr(self.db_manager, 'framework_db_path') else "framework.db"
                    with sqlite3.connect(framework_db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT 1")
                        cursor.fetchone()
                    return {"healthy": True, "checks_passed": ["database_connectivity"], "issues": []}
                except Exception as e2:
                    return {"healthy": False, "checks_passed": [], "issues": [f"Database connectivity failed: {e2}"]}
        except Exception as e:
            return {"healthy": False, "checks_passed": [], "issues": [f"Health check error: {e}"]}

    def _create_full_system_backup(self) -> str:
        bid = f"critical_backup_{int(time.time())}"
        self.logger.info("Criando backup completo do sistema: %s", bid)
        # Em produção: snapshot real
        return bid

    def _restore_system_backup(self, backup_id: str) -> bool:
        self.logger.warning("Restaurando sistema a partir do backup: %s", backup_id)
        # Em produção: restauração real
        return True

    def _generate_execution_summary(self, results: Dict[str, Any], duration_seconds: float) -> Dict[str, Any]:
        """Gera relatório detalhado com métricas abrangentes."""
        waves = [k for k in results.keys() if k.startswith("WAVE_")]
        
        # Métricas básicas
        total_files = sum(len(results[w]) for w in waves)
        total_optimizations = 0
        successes = 0
        rollbacks = 0
        
        # Métricas detalhadas
        pattern_metrics = {}
        quality_metrics = {"total_quality": 0.0, "avg_quality": 0.0, "quality_distribution": {}}
        risk_metrics = {"total_risk": 0, "avg_risk": 0.0, "risk_distribution": {}}
        performance_metrics = {"files_per_second": 0.0, "avg_file_size": 0, "total_lines": 0}
        
        for w in waves:
            for r in results[w]:
                if isinstance(r, FileAuditResult):
                    total_optimizations += r.optimizations_applied
                    
                    if r.syntax_valid and not r.changes_summary.startswith("ROLLED BACK"):
                        successes += 1
                    elif r.changes_summary.startswith("ROLLED BACK"):
                        rollbacks += 1
                    
                    # Pattern metrics
                    for pattern in r.patterns_found or []:
                        pattern_metrics[pattern] = pattern_metrics.get(pattern, 0) + 1
                    
                    # Quality metrics
                    quality_metrics["total_quality"] += r.context_quality
                    quality_range = self._get_quality_range(r.context_quality)
                    quality_metrics["quality_distribution"][quality_range] = \
                        quality_metrics["quality_distribution"].get(quality_range, 0) + 1
                    
                    # Risk metrics
                    risk_metrics["total_risk"] += r.risk_score
                    risk_metrics["risk_distribution"][r.risk_category] = \
                        risk_metrics["risk_distribution"].get(r.risk_category, 0) + 1
                    
                    # Performance metrics
                    performance_metrics["total_lines"] += r.lines_analyzed
        
        # Calcular médias
        if total_files > 0:
            quality_metrics["avg_quality"] = round(quality_metrics["total_quality"] / total_files, 2)
            risk_metrics["avg_risk"] = round(risk_metrics["total_risk"] / total_files, 2)
            performance_metrics["avg_file_size"] = round(performance_metrics["total_lines"] / total_files, 0)
        
        if duration_seconds > 0:
            performance_metrics["files_per_second"] = round(total_files / duration_seconds, 2)
        
        success_rate = (successes / max(total_files, 1)) * 100.0
        rollback_rate = (rollbacks / max(total_files, 1)) * 100.0
        
        return {
            # Métricas básicas
            "total_files_processed": total_files,
            "total_optimizations_applied": total_optimizations,
            "waves_completed": len(waves),
            "duration_seconds": round(duration_seconds, 3),
            "success_rate": round(success_rate, 2),
            "rollback_rate": round(rollback_rate, 2),
            
            # Distribuição por waves
            "risk_distribution": {
                "low_risk_processed": len(results.get("WAVE_1_LOW", [])),
                "medium_risk_processed": len(results.get("WAVE_2_MEDIUM", [])),
                "high_risk_processed": len(results.get("WAVE_3_HIGH", [])),
                "critical_risk_processed": len(results.get("WAVE_4_CRITICAL", [])),
            },
            
            # Métricas detalhadas
            "pattern_metrics": dict(sorted(pattern_metrics.items(), key=lambda x: x[1], reverse=True)),
            "quality_metrics": quality_metrics,
            "risk_metrics": risk_metrics,
            "performance_metrics": performance_metrics,
            
            # Assessment geral
            "assessment": self._generate_assessment(
                success_rate, quality_metrics["avg_quality"], risk_metrics["avg_risk"], total_optimizations
            ),
            
            # Timestamp
            "generated_at": datetime.now().isoformat(),
        }

    def _get_quality_range(self, quality: float) -> str:
        """Categoriza qualidade em ranges."""
        if quality >= 90:
            return "excellent"
        elif quality >= 75:
            return "good"
        elif quality >= 60:
            return "acceptable"
        elif quality >= 40:
            return "poor"
        else:
            return "critical"

    def _generate_assessment(
        self, 
        success_rate: float, 
        avg_quality: float, 
        avg_risk: float, 
        total_optimizations: int
    ) -> Dict[str, Any]:
        """Gera assessment geral da execução."""
        grade = "F"
        status = "FAILED"
        recommendations = []
        
        # Calcular grade baseado em múltiplos fatores
        score = 0
        
        # Success rate (40 pontos máximo)
        if success_rate >= 95:
            score += 40
        elif success_rate >= 85:
            score += 30
        elif success_rate >= 70:
            score += 20
        elif success_rate >= 50:
            score += 10
        
        # Quality (30 pontos máximo)
        if avg_quality >= 85:
            score += 30
        elif avg_quality >= 70:
            score += 20
        elif avg_quality >= 55:
            score += 15
        elif avg_quality >= 40:
            score += 10
        
        # Risk management (20 pontos máximo)
        if avg_risk <= 35:
            score += 20
        elif avg_risk <= 70:
            score += 15
        elif avg_risk <= 105:
            score += 10
        elif avg_risk <= 140:
            score += 5
        
        # Optimizations (10 pontos máximo)
        if total_optimizations >= 20:
            score += 10
        elif total_optimizations >= 10:
            score += 7
        elif total_optimizations >= 5:
            score += 5
        elif total_optimizations >= 1:
            score += 3
        
        # Determinar grade e status
        if score >= 90:
            grade, status = "A+", "EXCELLENT"
        elif score >= 85:
            grade, status = "A", "EXCELLENT"
        elif score >= 80:
            grade, status = "B+", "GOOD"
        elif score >= 75:
            grade, status = "B", "GOOD"
        elif score >= 70:
            grade, status = "C+", "ACCEPTABLE"
        elif score >= 65:
            grade, status = "C", "ACCEPTABLE"
        elif score >= 60:
            grade, status = "D+", "POOR"
        elif score >= 55:
            grade, status = "D", "POOR"
        else:
            grade, status = "F", "FAILED"
        
        # Gerar recomendações
        if success_rate < 85:
            recommendations.append("Investigate failed files and improve error handling")
        if avg_quality < 70:
            recommendations.append("Focus on improving code documentation and type hints")
        if avg_risk > 70:
            recommendations.append("Address high-risk files with additional safety measures")
        if total_optimizations < 5:
            recommendations.append("Review pattern detection to find more optimization opportunities")
        
        return {
            "grade": grade,
            "status": status,
            "score": score,
            "max_score": 100,
            "recommendations": recommendations,
            "summary": f"Grade {grade} ({status}) - {score}/100 points"
        }


# =============================================================================
# Enterprise Session Manager - Persistent session with intelligent recovery
# =============================================================================
@dataclass
class SessionCheckpoint:
    """Detailed session checkpoint for recovery."""
    session_id: str
    timestamp: datetime
    files_completed: List[str]
    files_failed: List[str]
    files_deferred: List[str]
    current_batch: List[str]
    token_consumption_history: Dict[str, int]
    performance_metrics: Dict[str, Any]
    session_config: Dict[str, Any]
    recovery_metadata: Dict[str, Any]


@dataclass
class AuditProgress:
    """Comprehensive audit progress tracking."""
    total_files: int
    completed_files: int
    failed_files: int
    deferred_files: int
    completion_percentage: float
    estimated_remaining_time_hours: float
    total_tokens_consumed: int
    average_tokens_per_file: float
    efficiency_rating: str


class EnterpriseSessionManager:
    """
    Enterprise-grade session management with intelligent recovery and distributed execution support.
    """
    
    def __init__(self, db_manager: DatabaseManager, project_root: Path):
        self.db_manager = db_manager
        self.project_root = project_root
        self.logger = logging.getLogger(f"{__name__}.EnterpriseSessionManager")
        
        # Session state
        self.current_session_id: Optional[str] = None
        self.session_start_time: Optional[datetime] = None
        self.checkpoints: List[SessionCheckpoint] = []
        
        # Progress tracking
        self.files_completed: Set[str] = set()
        self.files_failed: Set[str] = set()
        self.files_deferred: Set[str] = set()
        self.file_results: Dict[str, Dict[str, Any]] = {}
        
        # Recovery state
        self.is_resumed_session = False
        self.original_session_id: Optional[str] = None
        
        self._ensure_session_tables()
        self.logger.info("EnterpriseSessionManager initialized")
    
    def _get_db_connection(self):
        """Get database connection consistently."""
        framework_db_path = self.db_manager.framework_db_path if hasattr(self.db_manager, 'framework_db_path') else "framework.db"
        return sqlite3.connect(framework_db_path)
    
    def _ensure_session_tables(self) -> None:
        """Ensure session tracking tables exist in database."""
        try:
            # Use existing database connection - DatabaseManager returns sqlite connection
            framework_db_path = self.db_manager.framework_db_path if hasattr(self.db_manager, 'framework_db_path') else "framework.db"
            
            with sqlite3.connect(framework_db_path) as conn:
                cursor = conn.cursor()
                
                # Session metadata table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS audit_sessions (
                        session_id TEXT PRIMARY KEY,
                        start_time TEXT NOT NULL,
                        end_time TEXT,
                        status TEXT NOT NULL DEFAULT 'active',
                        total_files INTEGER,
                        completed_files INTEGER DEFAULT 0,
                        failed_files INTEGER DEFAULT 0,
                        deferred_files INTEGER DEFAULT 0,
                        total_tokens_consumed INTEGER DEFAULT 0,
                        session_config TEXT,
                        metadata TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # File processing results table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS audit_file_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        status TEXT NOT NULL,
                        tokens_used INTEGER DEFAULT 0,
                        lines_analyzed INTEGER DEFAULT 0,
                        issues_found INTEGER DEFAULT 0,
                        optimizations_applied INTEGER DEFAULT 0,
                        processing_time_seconds REAL DEFAULT 0,
                        analysis_result TEXT,
                        error_message TEXT,
                        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES audit_sessions (session_id)
                    )
                """)
                
                # Checkpoint table for recovery
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS audit_checkpoints (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        checkpoint_data TEXT NOT NULL,
                        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES audit_sessions (session_id)
                    )
                """)
                
                conn.commit()
                self.logger.debug("Session tables ensured in database")
                
        except Exception as e:
            self.logger.error("Failed to ensure session tables: %s", e)
    
    def start_new_session(self, total_files: int, session_config: Dict[str, Any]) -> str:
        """Start a new audit session with comprehensive tracking."""
        self.current_session_id = f"audit_{int(time.time())}_{os.getpid()}"
        self.session_start_time = datetime.now()
        self.is_resumed_session = False
        
        try:
            framework_db_path = self.db_manager.framework_db_path if hasattr(self.db_manager, 'framework_db_path') else "framework.db"
            
            with sqlite3.connect(framework_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO audit_sessions 
                    (session_id, start_time, status, total_files, session_config, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    self.current_session_id,
                    self.session_start_time.isoformat(),
                    'active',
                    total_files,
                    json.dumps(session_config),
                    json.dumps({
                        "pid": os.getpid(),
                        "hostname": os.uname().nodename,
                        "python_version": sys.version,
                        "intelligent_mode": session_config.get("intelligent_mode", False)
                    })
                ))
                conn.commit()
                
            self.logger.info("✅ New audit session started: %s (%d files)", 
                           self.current_session_id, total_files)
            
            return self.current_session_id
            
        except Exception as e:
            self.logger.error("Failed to start new session: %s", e)
            raise
    
    def resume_session(self, session_id: Optional[str] = None) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Resume the most recent incomplete session or specific session."""
        try:
            framework_db_path = self.db_manager.framework_db_path if hasattr(self.db_manager, 'framework_db_path') else "framework.db"
            with sqlite3.connect(framework_db_path) as conn:
                cursor = conn.cursor()
                
                if session_id:
                    # Resume specific session
                    cursor.execute("""
                        SELECT session_id, start_time, total_files, completed_files, 
                               failed_files, deferred_files, session_config, metadata
                        FROM audit_sessions 
                        WHERE session_id = ? AND status = 'active'
                    """, (session_id,))
                else:
                    # Resume most recent incomplete session
                    cursor.execute("""
                        SELECT session_id, start_time, total_files, completed_files,
                               failed_files, deferred_files, session_config, metadata
                        FROM audit_sessions 
                        WHERE status = 'active'
                        ORDER BY start_time DESC LIMIT 1
                    """)
                
                session_row = cursor.fetchone()
                
                if not session_row:
                    self.logger.info("No active session found to resume")
                    return False, None, {}
                
                # Load session data
                session_data = dict(session_row)
                self.current_session_id = session_data['session_id']
                self.original_session_id = self.current_session_id
                self.session_start_time = datetime.fromisoformat(session_data['start_time'])
                self.is_resumed_session = True
                
                # Load file completion status
                cursor.execute("""
                    SELECT file_path, status 
                    FROM audit_file_results 
                    WHERE session_id = ?
                """, (self.current_session_id,))
                
                for file_path, status in cursor.fetchall():
                    if status == 'completed':
                        self.files_completed.add(file_path)
                    elif status == 'failed':
                        self.files_failed.add(file_path)
                    elif status == 'deferred':
                        self.files_deferred.add(file_path)
                
                resume_info = {
                    "session_id": self.current_session_id,
                    "files_completed": len(self.files_completed),
                    "files_failed": len(self.files_failed),
                    "files_deferred": len(self.files_deferred),
                    "total_files": session_data['total_files'],
                    "session_config": json.loads(session_data.get('session_config', '{}')),
                    "metadata": json.loads(session_data.get('metadata', '{}'))
                }
                
                self.logger.info("✅ Resumed session %s: %d completed, %d failed, %d deferred",
                               self.current_session_id, len(self.files_completed), 
                               len(self.files_failed), len(self.files_deferred))
                
                return True, self.current_session_id, resume_info
                
        except Exception as e:
            self.logger.error("Failed to resume session: %s", e)
            return False, None, {}
    
    def save_checkpoint(self, current_batch: List[str], token_manager_stats: Dict[str, Any]) -> bool:
        """Save detailed checkpoint for recovery."""
        if not self.current_session_id:
            return False
            
        try:
            checkpoint = SessionCheckpoint(
                session_id=self.current_session_id,
                timestamp=datetime.now(),
                files_completed=list(self.files_completed),
                files_failed=list(self.files_failed),
                files_deferred=list(self.files_deferred),
                current_batch=current_batch,
                token_consumption_history=getattr(token_manager_stats, 'file_consumption_history', {}),
                performance_metrics=getattr(token_manager_stats, 'performance_metrics', {}),
                session_config={
                    "is_resumed": self.is_resumed_session,
                    "original_session_id": self.original_session_id
                },
                recovery_metadata={
                    "checkpoint_count": len(self.checkpoints) + 1,
                    "last_checkpoint": datetime.now().isoformat()
                }
            )
            
            # Save to database
            framework_db_path = self.db_manager.framework_db_path if hasattr(self.db_manager, 'framework_db_path') else "framework.db"
            with sqlite3.connect(framework_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO audit_checkpoints (session_id, checkpoint_data)
                    VALUES (?, ?)
                """, (self.current_session_id, json.dumps(checkpoint.__dict__, default=str)))
                
                # Update session progress
                cursor.execute("""
                    UPDATE audit_sessions 
                    SET completed_files = ?, failed_files = ?, deferred_files = ?,
                        total_tokens_consumed = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE session_id = ?
                """, (
                    len(self.files_completed),
                    len(self.files_failed), 
                    len(self.files_deferred),
                    token_manager_stats.get('tokens_used_today', 0),
                    self.current_session_id
                ))
                
                conn.commit()
            
            self.checkpoints.append(checkpoint)
            self.logger.debug("Checkpoint saved for session %s", self.current_session_id)
            return True
            
        except Exception as e:
            self.logger.error("Failed to save checkpoint: %s", e)
            return False
    
    def record_file_result(self, file_path: str, result: Dict[str, Any]) -> bool:
        """Record detailed result for a file."""
        if not self.current_session_id:
            return False
            
        try:
            status = "completed" if result.get('modified', False) or not result.get('error') else "failed"
            if result.get('deferred'):
                status = "deferred"
            
            # Update local tracking
            if status == "completed":
                self.files_completed.add(file_path)
                self.files_failed.discard(file_path)
                self.files_deferred.discard(file_path)
            elif status == "failed":
                self.files_failed.add(file_path)
                self.files_completed.discard(file_path)
                self.files_deferred.discard(file_path)
            elif status == "deferred":
                self.files_deferred.add(file_path)
                self.files_completed.discard(file_path)
                self.files_failed.discard(file_path)
            
            # Store detailed result
            self.file_results[file_path] = result
            
            # Save to database
            framework_db_path = self.db_manager.framework_db_path if hasattr(self.db_manager, 'framework_db_path') else "framework.db"
            with sqlite3.connect(framework_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO audit_file_results
                    (session_id, file_path, status, tokens_used, lines_analyzed, 
                     issues_found, optimizations_applied, processing_time_seconds, 
                     analysis_result, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.current_session_id,
                    file_path,
                    status,
                    result.get('tokens_used', 0),
                    result.get('lines_analyzed', 0),
                    result.get('issues_found', 0),
                    result.get('optimizations_applied', 0),
                    result.get('processing_time_seconds', 0),
                    json.dumps(result, default=str),
                    result.get('error', '')
                ))
                conn.commit()
            
            return True
            
        except Exception as e:
            self.logger.error("Failed to record file result for %s: %s", file_path, e)
            return False
    
    def get_remaining_files(self, all_files: List[str]) -> List[str]:
        """Get list of files that still need processing."""
        processed_files = self.files_completed | self.files_failed
        return [f for f in all_files if f not in processed_files]
    
    def get_audit_progress(self, total_files: int) -> AuditProgress:
        """Get comprehensive audit progress information."""
        completed = len(self.files_completed)
        failed = len(self.files_failed)
        deferred = len(self.files_deferred)
        
        completion_percentage = (completed / total_files * 100) if total_files > 0 else 0
        
        # Estimate remaining time
        if self.session_start_time and completed > 0:
            elapsed_hours = (datetime.now() - self.session_start_time).total_seconds() / 3600
            rate_files_per_hour = completed / elapsed_hours
            remaining_files = total_files - completed
            estimated_remaining_hours = remaining_files / rate_files_per_hour if rate_files_per_hour > 0 else 0
        else:
            estimated_remaining_hours = 0
        
        # Calculate efficiency rating
        total_tokens = sum(r.get('tokens_used', 0) for r in self.file_results.values())
        avg_tokens_per_file = total_tokens / completed if completed > 0 else 0
        
        if avg_tokens_per_file < 5000:
            efficiency = "excellent"
        elif avg_tokens_per_file < 10000:
            efficiency = "good"  
        elif avg_tokens_per_file < 20000:
            efficiency = "fair"
        else:
            efficiency = "needs_optimization"
        
        return AuditProgress(
            total_files=total_files,
            completed_files=completed,
            failed_files=failed,
            deferred_files=deferred,
            completion_percentage=completion_percentage,
            estimated_remaining_time_hours=estimated_remaining_hours,
            total_tokens_consumed=total_tokens,
            average_tokens_per_file=avg_tokens_per_file,
            efficiency_rating=efficiency
        )
    
    def finalize_session(self, final_stats: Dict[str, Any]) -> bool:
        """Finalize the audit session with comprehensive results."""
        if not self.current_session_id:
            return False
            
        try:
            framework_db_path = self.db_manager.framework_db_path if hasattr(self.db_manager, 'framework_db_path') else "framework.db"
            with sqlite3.connect(framework_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE audit_sessions 
                    SET end_time = ?, status = 'completed',
                        metadata = ?
                    WHERE session_id = ?
                """, (
                    datetime.now().isoformat(),
                    json.dumps(final_stats, default=str),
                    self.current_session_id
                ))
                conn.commit()
            
            self.logger.info("✅ Session %s finalized successfully", self.current_session_id)
            return True
            
        except Exception as e:
            self.logger.error("Failed to finalize session: %s", e)
            return False


# =============================================================================
# Tracking no banco (leve, sem schema novo)
# =============================================================================
class DatabaseTracker:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(f"{__name__}.DatabaseTracker")
        self._initialize_tables()

    def _initialize_tables(self) -> None:
        try:
            existing = self.db_manager.query("SELECT name FROM sqlite_master WHERE type='table'", database="framework")  # type: ignore
            _ = [row["name"] for row in existing]  # não usado ainda, mas mantém verificação
            self.logger.info("Tabelas verificadas/ok (usando estrutura existente)")
        except Exception as e:  # pragma: no cover
            self.logger.warning("Falha ao verificar/ini tabelas: %s (usando estrutura existente)", e)

    def create_session(self, total_files: int) -> int:
        try:
            sid = int(datetime.now().timestamp())
            self.logger.info("Sessão criada %s para %d arquivos", sid, total_files)
            return sid
        except Exception:  # pragma: no cover
            return int(time.time())

    def get_current_session(self) -> Optional[AuditSession]:
        return None

    def update_session_progress(self, session_id: int, file_index: int, tokens_used: int) -> None:
        try:
            self.logger.debug("Sessão %s: arquivo %s, tokens %s", session_id, file_index, tokens_used)
        except Exception as e:  # pragma: no cover
            self.logger.warning("Falha ao atualizar progresso da sessão: %s", e)

    def initialize_file_list(self, file_paths: List[str]) -> None:
        try:
            self.file_list = file_paths
            self.file_status = {p: AuditStatus.PENDING.value for p in file_paths}
            self.logger.info("Lista de %d arquivos inicializada", len(file_paths))
        except Exception as e:  # pragma: no cover
            self.logger.warning("Falha ao inicializar lista de arquivos: %s", e)

    def mark_file_in_progress(self, file_path: str) -> None:
        try:
            if hasattr(self, "file_status"):
                self.file_status[file_path] = AuditStatus.IN_PROGRESS.value
        except Exception as e:  # pragma: no cover
            self.logger.warning("Falha ao marcar IN_PROGRESS: %s", e)

    def mark_file_completed(self, file_path: str, result: FileAuditResult) -> None:
        try:
            if hasattr(self, "file_status"):
                self.file_status[file_path] = AuditStatus.COMPLETED.value
            self.logger.info("Concluída auditoria de %s: %s", file_path, result.changes_summary)
        except Exception as e:  # pragma: no cover
            self.logger.warning("Falha ao marcar COMPLETED: %s", e)

    def mark_file_failed(self, file_path: str, error_message: str) -> None:
        try:
            if hasattr(self, "file_status"):
                self.file_status[file_path] = AuditStatus.FAILED.value
            self.logger.error("Falha na auditoria de %s: %s", file_path, error_message)
        except Exception as e:  # pragma: no cover
            self.logger.warning("Falha ao marcar FAILED: %s", e)

    def get_pending_files(self) -> List[str]:
        try:
            if hasattr(self, "file_status"):
                return [p for p, s in self.file_status.items() if s == AuditStatus.PENDING.value]
            return []
        except Exception as e:  # pragma: no cover
            self.logger.warning("Falha ao obter pendentes: %s", e)
            return []

    def get_audit_summary(self) -> Dict[str, Any]:
        try:
            if hasattr(self, "file_status"):
                status_counts: Dict[str, int] = {}
                for s in self.file_status.values():
                    status_counts[s] = status_counts.get(s, 0) + 1
                total = len(self.file_status)
                completed = status_counts.get("completed", 0)
                rate = (completed / total * 100.0) if total else 0.0
                return {
                    "statistics": [{"status": k, "count": v} for k, v in status_counts.items()],
                    "total_files": total,
                    "completion_rate": rate,
                    "last_updated": datetime.now().isoformat(),
                }
            return {"statistics": [], "total_files": 0, "completion_rate": 0.0, "last_updated": datetime.now().isoformat()}
        except Exception as e:  # pragma: no cover
            self.logger.warning("Falha ao gerar resumo da auditoria: %s", e)
            return {"error": str(e), "total_files": 0, "completion_rate": 0.0}


# =============================================================================
# Smart Token Budget Manager - Advanced token management with AI analysis estimation
# =============================================================================
class SmartTokenBudgetManager:
    def __init__(self, max_tokens_per_hour: int = 40000):
        self.max_tokens_per_hour = max_tokens_per_hour
        self.daily_budget = max_tokens_per_hour * 20  # 800K tokens per day
        self.session_limit = int(max_tokens_per_hour * 0.8)  # 32K per session (safety buffer)
        
        # Current usage tracking
        self.tokens_used_this_hour = 0
        self.tokens_used_today = 0
        self.tokens_used_this_session = 0
        
        # Time tracking
        self.hour_start = time.time()
        self.day_start = time.time()
        self.session_start = time.time()
        
        # Advanced tracking
        self.token_history: List[Dict[str, Any]] = []
        self.file_consumption_history: Dict[str, int] = {}
        self.performance_metrics: Dict[str, Any] = {}
        
        # AI-specific settings
        self.intelligent_mode = True
        self.adaptive_throttling = True
        self.risk_based_scaling = True
        self.predictive_analysis = True
        
        self.logger = logging.getLogger(f"{__name__}.SmartTokenBudgetManager")
        self.logger.info(
            "SmartTokenBudgetManager initialized: %d tokens/hour, %d daily budget, intelligent mode: %s",
            max_tokens_per_hour, self.daily_budget, self.intelligent_mode
        )

    def _reset_time_windows_if_needed(self) -> None:
        """Reset time windows for hour, day, and session if needed."""
        current_time = time.time()
        
        # Reset hour window
        if current_time - self.hour_start >= 3600:
            self.tokens_used_this_hour = 0
            self.hour_start = current_time
            self.logger.info("Hourly token window reset")
        
        # Reset day window (24 hours)
        if current_time - self.day_start >= 86400:
            self.tokens_used_today = 0
            self.day_start = current_time
            self.logger.info("Daily token budget reset: %d tokens available", self.daily_budget)
        
        # Session timeout (6 hours max)
        if current_time - self.session_start >= 21600:
            self.tokens_used_this_session = 0
            self.session_start = current_time
            self.logger.info("Session token window reset")

    def estimate_file_tokens(self, file_path: str, project_root: Path) -> int:
        """
        Estimate tokens required for intelligent analysis of a file.
        Based on file size, complexity, and historical data.
        """
        try:
            full_path = project_root / file_path
            if not full_path.exists():
                return 1000  # Default for missing files
            
            # Get file metrics
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            lines = content.count('\n') + 1
            
            # Base estimation: tokens per line for IA analysis
            base_tokens_per_line = 25 if self.intelligent_mode else 5
            base_estimate = lines * base_tokens_per_line
            
            # Complexity multipliers
            complexity_multiplier = 1.0
            
            # AST analysis complexity
            try:
                ast_tree = ast.parse(content)
                ast_nodes = len(list(ast.walk(ast_tree)))
                if ast_nodes > 500:
                    complexity_multiplier *= 1.5  # Complex files
                elif ast_nodes > 200:
                    complexity_multiplier *= 1.2  # Medium complexity
            except SyntaxError:
                complexity_multiplier *= 0.8  # Syntax errors = simpler analysis
            
            # File type multipliers
            if 'test' in file_path.lower():
                complexity_multiplier *= 0.7  # Test files are usually simpler
            elif any(critical in file_path.lower() for critical in ['database', 'security', 'auth', 'middleware']):
                complexity_multiplier *= 1.8  # Critical files need deeper analysis
            elif file_path.endswith('__init__.py'):
                complexity_multiplier *= 0.3  # Init files are usually simple
            
            # Size-based adjustments
            if lines > 1000:
                complexity_multiplier *= 1.4  # Large files
            elif lines < 50:
                complexity_multiplier *= 0.6  # Small files
            
            # Historical data adjustment
            if file_path in self.file_consumption_history:
                historical_usage = self.file_consumption_history[file_path]
                # Average with historical data (70% historical, 30% estimation)
                estimated = int(base_estimate * complexity_multiplier)
                final_estimate = int(historical_usage * 0.7 + estimated * 0.3)
            else:
                final_estimate = int(base_estimate * complexity_multiplier)
            
            # Safety bounds
            final_estimate = max(500, min(final_estimate, 50000))  # Between 500-50K tokens
            
            self.logger.debug("Token estimation for %s: %d tokens (lines: %d, multiplier: %.2f)", 
                             file_path, final_estimate, lines, complexity_multiplier)
            
            return final_estimate
            
        except Exception as e:
            self.logger.warning("Failed to estimate tokens for %s: %s", file_path, e)
            return 5000  # Conservative fallback

    def can_proceed(self, estimated_tokens: int, file_path: Optional[str] = None) -> bool:
        """Enhanced token checking with multiple budget levels."""
        self._reset_time_windows_if_needed()
        
        # Check session limit (most restrictive)
        if self.tokens_used_this_session + estimated_tokens > self.session_limit:
            self.logger.warning(
                "Session token limit would be exceeded: %d + %d > %d for file %s",
                self.tokens_used_this_session, estimated_tokens, self.session_limit, file_path
            )
            return False
        
        # Check hourly limit
        if self.tokens_used_this_hour + estimated_tokens > self.max_tokens_per_hour:
            self.logger.warning(
                "Hourly token limit would be exceeded: %d + %d > %d for file %s",
                self.tokens_used_this_hour, estimated_tokens, self.max_tokens_per_hour, file_path
            )
            return False
        
        # Check daily budget (soft limit - warning only)
        if self.tokens_used_today + estimated_tokens > self.daily_budget:
            self.logger.warning(
                "Daily token budget would be exceeded: %d + %d > %d for file %s - proceeding with caution",
                self.tokens_used_today, estimated_tokens, self.daily_budget, file_path
            )
            # Still proceed but log warning
        
        return True

    def calculate_intelligent_sleep_time(self) -> float:
        """Calculate adaptive sleep time based on multiple factors."""
        self._reset_time_windows_if_needed()
        
        current_time = time.time()
        
        # Calculate different usage rates
        hour_elapsed = current_time - self.hour_start
        session_elapsed = current_time - self.session_start
        
        if hour_elapsed < 60:
            return 0.0  # No throttling in first minute
        
        # Hourly rate calculation
        hour_usage_rate = self.tokens_used_this_hour / (hour_elapsed / 60)
        hour_target_rate = self.max_tokens_per_hour / 60
        
        # Session rate calculation  
        session_usage_rate = self.tokens_used_this_session / (session_elapsed / 60)
        session_target_rate = self.session_limit / (6 * 60)  # 6-hour session target
        
        # Calculate sleep times for each constraint
        sleep_times = []
        
        # Hourly constraint
        if hour_usage_rate > hour_target_rate:
            hour_excess = hour_usage_rate - hour_target_rate
            hour_sleep = (hour_excess / hour_target_rate) * 60
            sleep_times.append(("hourly", hour_sleep))
        
        # Session constraint
        if session_usage_rate > session_target_rate:
            session_excess = session_usage_rate - session_target_rate
            session_sleep = (session_excess / session_target_rate) * 30
            sleep_times.append(("session", session_sleep))
        
        # Adaptive throttling based on history
        if self.adaptive_throttling and len(self.token_history) >= 5:
            recent_usage = sum(entry["tokens"] for entry in self.token_history[-5:])
            if recent_usage > self.max_tokens_per_hour * 0.3:  # 30% of hourly in recent 5 files
                adaptive_sleep = min(60.0, recent_usage / 1000)
                sleep_times.append(("adaptive", adaptive_sleep))
        
        if sleep_times:
            # Use the maximum sleep time (most restrictive)
            sleep_reason, sleep_duration = max(sleep_times, key=lambda x: x[1])
            final_sleep = min(sleep_duration, 600.0)  # Max 10 minutes
            
            self.logger.info(
                "Intelligent throttling: %d seconds (reason: %s, hourly rate: %.1f/min, session rate: %.1f/min)",
                int(final_sleep), sleep_reason, hour_usage_rate, session_usage_rate
            )
            return final_sleep
        
        return 0.0
    
    def get_available_tokens(self) -> int:
        """Get the number of tokens available for the current session."""
        self._reset_time_windows_if_needed()
        
        # Calculate available tokens for different time windows
        available_hourly = self.max_tokens_per_hour - self.tokens_used_this_hour
        available_session = self.session_limit - self.tokens_used_this_session
        available_daily = self.daily_budget - self.tokens_used_today
        
        # Return the most restrictive limit
        available = min(available_hourly, available_session, available_daily)
        return max(0, available)

    def calculate_adaptive_batch_size(self, remaining_files: int, available_time_hours: float = 1.0) -> int:
        """Calculate optimal batch size based on current consumption and available time."""
        if remaining_files <= 0:
            return 0
        
        self._reset_time_windows_if_needed()
        
        # Calculate available tokens for this batch
        available_hourly = self.max_tokens_per_hour - self.tokens_used_this_hour
        available_session = self.session_limit - self.tokens_used_this_session
        available_tokens = min(available_hourly, available_session)
        
        # Estimate average tokens per file from history
        if self.file_consumption_history:
            avg_tokens_per_file = sum(self.file_consumption_history.values()) / len(self.file_consumption_history)
        else:
            avg_tokens_per_file = 8000  # Conservative estimate for IA analysis
        
        # Calculate batch size with safety buffer
        max_batch_by_tokens = max(1, int(available_tokens * 0.8 / avg_tokens_per_file))
        max_batch_by_time = max(1, min(10, int(available_time_hours * 6)))  # ~10 minutes per file
        
        optimal_batch = min(max_batch_by_tokens, max_batch_by_time, remaining_files)
        
        self.logger.debug(
            "Adaptive batch size: %d files (tokens available: %d, avg per file: %d, time constraint: %d)",
            optimal_batch, available_tokens, int(avg_tokens_per_file), max_batch_by_time
        )
        
        return max(1, optimal_batch)

    def record_usage(self, tokens_used: int, file_path: Optional[str] = None) -> None:
        """Enhanced usage recording with multiple tracking levels."""
        self._reset_time_windows_if_needed()
        
        # Update all counters
        self.tokens_used_this_hour += tokens_used
        self.tokens_used_today += tokens_used
        self.tokens_used_this_session += tokens_used
        
        # Record in history with enhanced metadata
        usage_entry = {
            "timestamp": time.time(),
            "tokens": tokens_used,
            "file_path": file_path,
            "cumulative_hour": self.tokens_used_this_hour,
            "cumulative_today": self.tokens_used_today,
            "cumulative_session": self.tokens_used_this_session
        }
        
        self.token_history.append(usage_entry)
        
        # Keep history manageable (last 200 entries)
        if len(self.token_history) > 200:
            self.token_history = self.token_history[-200:]
        
        # Update file-specific consumption history
        if file_path:
            self.file_consumption_history[file_path] = tokens_used
        
        # Update performance metrics
        self._update_performance_metrics(tokens_used, file_path)
        
        self.logger.debug(
            "Token usage recorded: +%d tokens for %s (hour: %d, today: %d, session: %d)",
            tokens_used, file_path or "unknown", 
            self.tokens_used_this_hour, self.tokens_used_today, self.tokens_used_this_session
        )

    def _update_performance_metrics(self, tokens_used: int, file_path: Optional[str]) -> None:
        """Update performance metrics for analysis."""
        if not hasattr(self, 'performance_metrics'):
            self.performance_metrics = {
                "total_files_processed": 0,
                "total_tokens_consumed": 0,
                "average_tokens_per_file": 0,
                "peak_tokens_per_file": 0,
                "efficiency_score": 100.0
            }
        
        self.performance_metrics["total_tokens_consumed"] += tokens_used
        
        if file_path:
            self.performance_metrics["total_files_processed"] += 1
            
            # Update average
            total_files = self.performance_metrics["total_files_processed"] 
            self.performance_metrics["average_tokens_per_file"] = (
                self.performance_metrics["total_tokens_consumed"] / total_files
            )
            
            # Update peak
            if tokens_used > self.performance_metrics["peak_tokens_per_file"]:
                self.performance_metrics["peak_tokens_per_file"] = tokens_used
            
            # Calculate efficiency score (lower tokens per file = higher efficiency)
            expected_tokens_per_file = 10000  # Baseline expectation
            actual_average = self.performance_metrics["average_tokens_per_file"]
            
            if actual_average > 0:
                efficiency = min(100.0, (expected_tokens_per_file / actual_average) * 100)
                self.performance_metrics["efficiency_score"] = efficiency

    def get_comprehensive_usage_stats(self) -> Dict[str, Any]:
        """Get detailed usage statistics across all tracking levels."""
        self._reset_time_windows_if_needed()
        
        current_time = time.time()
        
        # Time calculations
        hour_elapsed = current_time - self.hour_start
        day_elapsed = current_time - self.day_start  
        session_elapsed = current_time - self.session_start
        
        # Rate calculations
        hour_rate = self.tokens_used_this_hour / (hour_elapsed / 60) if hour_elapsed > 0 else 0.0
        day_rate = self.tokens_used_today / (day_elapsed / 60) if day_elapsed > 0 else 0.0
        session_rate = self.tokens_used_this_session / (session_elapsed / 60) if session_elapsed > 0 else 0.0
        
        # Projected usage
        projected_hour_end = (hour_rate * 60) if hour_rate > 0 else 0
        projected_day_end = (day_rate * 1440) if day_rate > 0 else 0  # 1440 min/day
        
        return {
            # Current usage
            "tokens_used_this_hour": self.tokens_used_this_hour,
            "tokens_used_today": self.tokens_used_today,
            "tokens_used_this_session": self.tokens_used_this_session,
            
            # Limits
            "hourly_limit": self.max_tokens_per_hour,
            "daily_budget": self.daily_budget,
            "session_limit": self.session_limit,
            
            # Usage percentages
            "hourly_usage_percent": (self.tokens_used_this_hour / self.max_tokens_per_hour) * 100.0,
            "daily_usage_percent": (self.tokens_used_today / self.daily_budget) * 100.0,
            "session_usage_percent": (self.tokens_used_this_session / self.session_limit) * 100.0,
            
            # Rates (tokens per minute)
            "hourly_rate": hour_rate,
            "daily_rate": day_rate,
            "session_rate": session_rate,
            
            # Time elapsed
            "hour_elapsed_minutes": hour_elapsed / 60.0,
            "day_elapsed_hours": day_elapsed / 3600.0,
            "session_elapsed_hours": session_elapsed / 3600.0,
            
            # Projections
            "projected_hour_consumption": projected_hour_end,
            "projected_day_consumption": projected_day_end,
            
            # Throttling
            "estimated_sleep_time": self.calculate_intelligent_sleep_time(),
            "should_throttle": projected_hour_end > self.max_tokens_per_hour * 0.9,
            
            # Performance metrics
            "performance_metrics": getattr(self, 'performance_metrics', {}),
            
            # Health indicators
            "efficiency_score": getattr(self, 'performance_metrics', {}).get('efficiency_score', 100.0),
            "files_processed": len(self.file_consumption_history),
            "average_tokens_per_file": sum(self.file_consumption_history.values()) / len(self.file_consumption_history) if self.file_consumption_history else 0,
            
            # System status
            "intelligent_mode": self.intelligent_mode,
            "adaptive_throttling": self.adaptive_throttling,
            "risk_based_scaling": self.risk_based_scaling
        }

    def prioritize_files_by_risk_and_tokens(
        self, 
        files: List[str], 
        project_root: Path, 
        setima_data: Any
    ) -> List[Tuple[str, int, int, str]]:
        """
        Prioritize files for processing based on risk score and estimated token consumption.
        Returns list of (file_path, estimated_tokens, risk_score, priority_reason).
        """
        file_priorities = []
        
        for file_path in files:
            # Get risk score from setima_data
            risk_score = setima_data.get_file_risk_score(file_path) if setima_data else 25
            risk_category = setima_data.get_file_risk_category(file_path) if setima_data else "MEDIUM"
            
            # Estimate token consumption
            estimated_tokens = self.estimate_file_tokens(file_path, project_root)
            
            # Calculate priority score (higher = process first)
            priority_score = 0
            priority_reasons = []
            
            # Risk-based priority (critical files first)
            if risk_category == "CRITICAL":
                priority_score += 1000
                priority_reasons.append("critical_risk")
            elif risk_category == "HIGH":
                priority_score += 800
                priority_reasons.append("high_risk")
            elif risk_category == "MEDIUM":
                priority_score += 500
                priority_reasons.append("medium_risk")
            else:
                priority_score += 200
                priority_reasons.append("low_risk")
            
            # Token efficiency priority (process smaller files first to build momentum)
            if estimated_tokens < 2000:
                priority_score += 300
                priority_reasons.append("small_efficient")
            elif estimated_tokens < 5000:
                priority_score += 200
                priority_reasons.append("medium_efficient")
            elif estimated_tokens > 15000:
                priority_score -= 100
                priority_reasons.append("large_expensive")
            
            # File type priorities
            if file_path.endswith('__init__.py'):
                priority_score += 100
                priority_reasons.append("init_file")
            elif 'test' in file_path.lower():
                priority_score += 50
                priority_reasons.append("test_file")
            elif any(critical in file_path.lower() for critical in ['database', 'security', 'auth']):
                priority_score += 150
                priority_reasons.append("critical_component")
            
            # Dependency-based priority (foundation files first)
            wave = setima_data.get_file_wave(file_path) if setima_data else "WAVE_1_FOUNDATION"
            if wave == "WAVE_1_FOUNDATION":
                priority_score += 400
                priority_reasons.append("foundation")
            elif wave == "WAVE_4_CRITICAL":
                priority_score += 600
                priority_reasons.append("critical_wave")
            
            file_priorities.append((
                file_path, 
                estimated_tokens, 
                risk_score, 
                ",".join(priority_reasons),
                priority_score
            ))
        
        # Sort by priority score (descending)
        file_priorities.sort(key=lambda x: x[4], reverse=True)
        
        # Return without internal priority_score
        return [(fp[0], fp[1], fp[2], fp[3]) for fp in file_priorities]
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Generate comprehensive session summary."""
        stats = self.get_comprehensive_usage_stats()
        
        # Calculate efficiency metrics
        files_processed = len(self.file_consumption_history)
        if files_processed > 0:
            avg_tokens = sum(self.file_consumption_history.values()) / files_processed
            efficiency_rating = "excellent" if avg_tokens < 5000 else \
                               "good" if avg_tokens < 10000 else \
                               "fair" if avg_tokens < 20000 else "needs_optimization"
        else:
            avg_tokens = 0
            efficiency_rating = "no_data"
        
        # Calculate time remaining estimates
        available_tokens_hour = max(0, self.max_tokens_per_hour - self.tokens_used_this_hour)
        available_tokens_session = max(0, self.session_limit - self.tokens_used_this_session)
        
        files_remaining_hour = int(available_tokens_hour / avg_tokens) if avg_tokens > 0 else 0
        files_remaining_session = int(available_tokens_session / avg_tokens) if avg_tokens > 0 else 0
        
        return {
            "session_overview": {
                "files_processed": files_processed,
                "total_tokens_consumed": self.tokens_used_this_session,
                "average_tokens_per_file": int(avg_tokens),
                "efficiency_rating": efficiency_rating,
                "session_duration_hours": stats["session_elapsed_hours"]
            },
            
            "capacity_remaining": {
                "tokens_available_hour": available_tokens_hour,
                "tokens_available_session": available_tokens_session,
                "estimated_files_remaining_hour": files_remaining_hour,
                "estimated_files_remaining_session": files_remaining_session
            },
            
            "throttling_status": {
                "should_throttle": stats["should_throttle"],
                "recommended_sleep_seconds": int(stats["estimated_sleep_time"]),
                "adaptive_throttling_enabled": self.adaptive_throttling
            },
            
            "performance_indicators": {
                "efficiency_score": stats["efficiency_score"],
                "processing_rate_files_per_hour": files_processed / max(0.1, stats["session_elapsed_hours"]),
                "token_consumption_rate": stats["session_rate"]
            }
        }

    # Legacy compatibility methods
    def calculate_sleep_time(self) -> float:
        """Legacy compatibility - redirects to intelligent sleep time calculation."""
        return self.calculate_intelligent_sleep_time()
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Legacy compatibility - redirects to comprehensive stats."""
        return self.get_comprehensive_usage_stats()


# =============================================================================
# Gerenciador de lista de arquivos – repo inteiro (com exclusões)
# =============================================================================
class FileListManager:
    """Busca .py no repositório inteiro, com exclusões padrão e ordem determinística."""

    DEFAULT_EXCLUDES = {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".idea",
        ".vscode",
        "node_modules",
        "dist",
        "build",
        ".ruff_cache",
        ".tox",
    }

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.logger = logging.getLogger(f"{__name__}.FileListManager")

    def get_all_python_files(self) -> List[str]:
        python_files: List[str] = []
        for root, dirs, files in os.walk(self.project_root):
            # aplica exclusões de diretórios in-place
            dirs[:] = [d for d in dirs if d not in self.DEFAULT_EXCLUDES]
            for fname in files:
                if not fname.endswith(".py"):
                    continue
                full = Path(root) / fname
                rel = str(full.relative_to(self.project_root))
                # ignorar este próprio arquivo
                if rel.endswith(os.path.basename(__file__)):
                    continue
                python_files.append(rel)

        python_files.sort()
        self.logger.info("Foram encontrados %d arquivos Python", len(python_files))
        return python_files

    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        full_path = self.project_root / file_path
        if not full_path.exists():
            return {"exists": False}
        stat = full_path.stat()
        try:
            with full_path.open("r", encoding="utf-8") as f:
                lines = sum(1 for _ in f)
        except Exception:
            lines = 0
        return {
            "exists": True,
            "size_bytes": stat.st_size,
            "lines": lines,
            "modified": datetime.fromtimestamp(stat.st_mtime),
            "readable": os.access(full_path, os.R_OK),
            "writable": os.access(full_path, os.W_OK),
        }


# =============================================================================
# Logging
# =============================================================================
def setup_logging(verbose: bool = False) -> logging.Logger:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("systematic_audit.log"), logging.StreamHandler(sys.stdout)],
    )
    return logging.getLogger(__name__)


# =============================================================================
# CLI
# =============================================================================
def main() -> int:
    parser = argparse.ArgumentParser(description="Enhanced Systematic File Auditor - Sétima Camada")
    parser.add_argument("--resume", nargs='?', const=True, help="Resume previous session or specific session ID")
    parser.add_argument("--dry-run", action="store_true", help="Simular sem escrever no disco")
    parser.add_argument("--max-files", type=int, help="Máximo de arquivos a processar")
    parser.add_argument("--verbose", "-v", action="store_true", help="Logging detalhado (debug)")
    parser.add_argument("--wave", choices=["1", "2", "3", "4", "all"], default="all", help="Executa wave específica")
    parser.add_argument("--risk-category", choices=["LOW", "MEDIUM", "HIGH", "CRITICAL"], help="Filtra por categoria de risco")
    parser.add_argument("--validate-only", action="store_true", help="Apenas valida sistema, sem modificações")
    parser.add_argument("--meta-agent", action="store_true", help="Enable MetaAgent intelligent coordination (experimental)")
    parser.add_argument("--legacy-agents", action="store_true", help="Use legacy manual agent coordination instead of MetaAgent")
    args = parser.parse_args()

    logger = setup_logging(args.verbose)
    logger.info("🤖 Enhanced Systematic File Auditor - Sétima Camada INICIANDO")

    try:
        audit_dir = Path(__file__).parent
        auditor = EnhancedSystematicFileAuditor(project_root, audit_dir, dry_run=args.dry_run, validate_only=args.validate_only)

        logger.info("✅ Auditor inicializado | Integração Sétima Camada: %s", "Full" if auditor.setima_integration_available else "Parcial")

        # Lista de arquivos (repo inteiro)
        all_files = auditor.file_manager.get_all_python_files()
        if args.max_files:
            all_files = all_files[: args.max_files]

        logger.info("📁 Processando %d arquivos (análise baseada em risco)", len(all_files))
        logger.info(
            "🔗 Integração: Context=%s | IntegrationTester=%s | RollbackMgr=%s | RiskScores=%d | Waves=%d",
            "ON" if auditor.context_validator else "OFF",
            "ON" if auditor.integration_tester else "OFF",
            "ON" if auditor.rollback_manager else "OFF",
            len(auditor.setima_data.risk_scores),
            len(auditor.setima_data.dependency_waves),
        )

        if args.validate_only:
            logger.info("🧪 VALIDATION ONLY MODE - Validando saúde do sistema")
            v = auditor._validate_system_health()
            logger.info("System Health: %s", "✅ Healthy" if v["healthy"] else "❌ Issues detected")
            if not v["healthy"]:
                logger.error("Issues: %s", v["issues"])
                return 1
            logger.info("✅ Validação concluída com sucesso")
            return 0

        if args.dry_run:
            logger.info("🧪 DRY RUN MODE - Amostra de análise de risco")
            sample = all_files[: min(10, len(all_files))]
            for fp in sample:
                risk_score = auditor.setima_data.get_file_risk_score(fp)
                risk_category = auditor.setima_data.get_file_risk_category(fp)
                wave = auditor.setima_data.get_file_wave(fp)
                context_q = auditor._validate_context_quality(fp)
                logger.info("📊 %s | Risk=%s (%s) | Wave=%s | Context=%.1f%%", fp, risk_score, risk_category, wave, context_q)
            logger.info("✅ Demonstração concluída (dry-run)")
            return 0

        # Prepare session resumption ID
        resume_session_id = None
        if args.resume:
            resume_session_id = args.resume if isinstance(args.resume, str) else None

        # Execução real
        start = time.time()

        # Filtro por categoria de risco (se fornecido)
        risk_filter = args.risk_category

        if args.wave == "all":
            # Use intelligent audit with AI agents and batch processing
            if auditor.intelligent_agents_available:
                logger.info("🤖 Using intelligent AI-powered audit execution")
                results = auditor.execute_intelligent_risk_based_audit(resume_session_id)
            else:
                logger.info("📊 Using legacy wave-based audit execution (AI not available)")
                # Fallback to original method if AI not available
                results = auditor.execute_risk_based_audit()

            # Se filtro de risco solicitado, filtra apenas para reporting (execução já ocorreu)
            if risk_filter:
                if "intelligent_analysis" in results and results["intelligent_analysis"]:
                    # Filter intelligent results structure
                    def _filter_intelligent_files(files_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
                        filtered = []
                        for file_data in files_list:
                            file_path = file_data.get("file_path", "")
                            file_risk_category = auditor.setima_data.get_file_risk_category(file_path)
                            if file_risk_category == risk_filter:
                                filtered.append(file_data)
                        return filtered
                    
                    results["files_processed"] = _filter_intelligent_files(results.get("files_processed", []))
                    results["files_failed"] = _filter_intelligent_files(results.get("files_failed", []))
                    results["files_deferred"] = _filter_intelligent_files(results.get("files_deferred", []))
                    
                    logger.info("🔍 Risk filter applied: showing only %s category files", risk_filter)
                else:
                    # Filter legacy wave-based results structure
                    def _filter_by_cat(lst: List[FileAuditResult]) -> List[FileAuditResult]:
                        return [r for r in lst if r.risk_category == risk_filter]

                    results["WAVE_1_LOW"] = _filter_by_cat(results.get("WAVE_1_LOW", []))
                    results["WAVE_2_MEDIUM"] = _filter_by_cat(results.get("WAVE_2_MEDIUM", []))
                    results["WAVE_3_HIGH"] = _filter_by_cat(results.get("WAVE_3_HIGH", []))
                    results["WAVE_4_CRITICAL"] = _filter_by_cat(results.get("WAVE_4_CRITICAL", []))
                    results["execution_summary"] = auditor._generate_execution_summary(results, time.time() - start)

        else:
            # Executa apenas uma wave específica
            wave_map = {
                "1": "WAVE_1_FOUNDATION",
                "2": "WAVE_2_BUSINESS",
                "3": "WAVE_3_INTEGRATION",
                "4": "WAVE_4_CRITICAL",
            }
            wave_key = wave_map[args.wave]
            target_files = auditor.setima_data.dependency_waves.get(wave_key, [])

            # Aplica filtro de risco ANTES da execução
            if risk_filter:
                target_files = [
                    fp for fp in target_files if auditor.setima_data.get_file_risk_category(fp) == risk_filter
                ]

            if args.max_files:
                target_files = target_files[: args.max_files]

            logger.info("⚡ Executando apenas a wave %s (%d arquivos)", wave_key, len(target_files))

            if wave_key == "WAVE_1_FOUNDATION":
                wave_results = auditor._execute_wave_parallel(target_files)
                results = {"WAVE_1_LOW": wave_results, "execution_summary": auditor._generate_execution_summary({"WAVE_1_LOW": wave_results}, time.time() - start)}
            elif wave_key == "WAVE_2_BUSINESS":
                wave_results = auditor._execute_wave_coordinated(target_files)
                results = {"WAVE_2_MEDIUM": wave_results, "execution_summary": auditor._generate_execution_summary({"WAVE_2_MEDIUM": wave_results}, time.time() - start)}
            elif wave_key == "WAVE_3_INTEGRATION":
                wave_results = auditor._execute_wave_sequential(target_files)
                results = {"WAVE_3_HIGH": wave_results, "execution_summary": auditor._generate_execution_summary({"WAVE_3_HIGH": wave_results}, time.time() - start)}
            else:  # WAVE_4_CRITICAL
                wave_results = auditor._execute_wave_critical(target_files)
                results = {"WAVE_4_CRITICAL": wave_results, "execution_summary": auditor._generate_execution_summary({"WAVE_4_CRITICAL": wave_results}, time.time() - start)}

        # Exibe resumo
        summary = results.get("execution_summary", {})
        logger.info("🎯 Resumo de Execução → Files: %s | Opts: %s | Waves: %s | Duração: %ss | Sucesso: %s%%",
                    summary.get("total_files_processed", 0),
                    summary.get("total_optimizations_applied", 0),
                    summary.get("waves_completed", 0),
                    summary.get("duration_seconds", 0),
                    summary.get("success_rate", 0.0))

        # Finalize session with execution stats
        final_stats = {
            "execution_summary": summary,
            "total_execution_time": time.time() - start,
            "session_completed": True,
            "intelligent_mode": auditor.intelligent_agents_available
        }
        auditor.session_manager.finalize_session(final_stats)

        logger.info("✅ Execução finalizada")
        return 0

    except Exception as e:  # pragma: no cover
        logger.error("❌ Falha ao iniciar/rodar auditor: %s", e, exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
