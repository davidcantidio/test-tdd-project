#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 API Equivalence Validation Suite (Improved)

Valida a equivalência funcional entre a API legada (DatabaseManager)
e a nova API modular, com foco em:
- Equivalência funcional (com normalização robusta de dados)
- Comparação de performance
- Detecção de breaking changes
- Relatórios para humanos (stdout) e para CI (JSON/JUnit)

Principais melhorias:
- Injeção de dependência da origem do banco de testes (sem monkey-patch frágil)
- Adaptadores (LegacyAdapter / ModularAdapter) com fallback e mensagens claras
- Normalização de resultados (tipos, ordenação, floats, chaves ausentes)
- Opções de CLI mais completas
- Modo “leniente” para pequenas diferenças de formato
- Relatórios JSON e JUnit opcionais

Uso:
    # Validação completa (DB temporário)
    python scripts/testing/api_equivalence_validation.py

    # Modo rápido (testes essenciais)
    python scripts/testing/api_equivalence_validation.py --quick

    # Apenas performance
    python scripts/testing/api_equivalence_validation.py --performance-only

    # Relatório detalhado e salvar JSON
    python scripts/testing/api_equivalence_validation.py --detailed-report --save-report report.json

    # Exportar JUnit para CI
    python scripts/testing/api_equivalence_validation.py --junit-out junit.xml

    # Manter o DB para inspeção e informar caminho
    python scripts/testing/api_equivalence_validation.py --keep-db --print-db-path

    # Usar um DB específico
    python scripts/testing/api_equivalence_validation.py --db /caminho/meu.db
"""

from __future__ import annotations

import sys
import os
import tempfile
import time
import logging
import argparse
import json
import sqlite3
import math
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional, Callable, Union
from dataclasses import dataclass, asdict, field
from contextlib import contextmanager
from xml.etree.ElementTree import Element, SubElement, ElementTree

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("api_equivalence")

# -----------------------------------------------------------------------------
# Caminho do projeto para imports
# -----------------------------------------------------------------------------
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

# -----------------------------------------------------------------------------
# Imports do projeto (protegidos)
# -----------------------------------------------------------------------------
try:
    # Legado
    from streamlit_extension.utils.database import DatabaseManager
except Exception as e:
    DatabaseManager = None
    logger.warning(f"Não foi possível importar DatabaseManager legado: {e}")

try:
    # Novo (modular)
    from streamlit_extension.database import (
        get_connection, transaction, check_health,
        optimize, create_schema_if_needed, seed_initial_data
    )
    from streamlit_extension.database.queries import (
        list_epics, list_all_epics, list_tasks, list_all_tasks,
        list_timer_sessions, get_user_stats, get_achievements
    )
    HAS_MODULAR = True
except Exception as e:
    HAS_MODULAR = False
    logger.warning(f"Não foi possível importar API modular: {e}")

# -----------------------------------------------------------------------------
# Data classes
# -----------------------------------------------------------------------------
@dataclass
class ValidationResult:
    test_name: str
    legacy_result: Any
    modular_result: Any
    equivalent: bool
    legacy_time_ms: float
    modular_time_ms: float
    performance_ratio: float
    error_message: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class ValidationReport:
    timestamp: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    equivalence_percentage: float
    average_performance_ratio: float
    breaking_changes: List[str]
    performance_improvements: List[str]
    test_results: List[ValidationResult] = field(default_factory=list)

# -----------------------------------------------------------------------------
# Utilidades de normalização/comparação
# -----------------------------------------------------------------------------

def _is_number(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)

def _to_number(x: Any) -> Any:
    # Converte strings numéricas e Decimals (se existirem) para float
    try:
        from decimal import Decimal
        if isinstance(x, Decimal):
            return float(x)
    except Exception:
        pass
    if isinstance(x, str):
        try:
            if "." in x or "e" in x.lower():
                return float(x)
            return int(x)
        except Exception:
            return x
    return x

def normalize_value(v: Any, float_tol: float = 1e-6) -> Any:
    """Normaliza valores para comparação robusta."""
    if v is None:
        return None

    if isinstance(v, (list, tuple)):
        return [normalize_value(x, float_tol=float_tol) for x in v]

    if isinstance(v, dict):
        # Normaliza recursivamente e ordena chaves ao final
        return {str(k): normalize_value(v[k], float_tol=float_tol) for k in sorted(v.keys(), key=str)}

    # normaliza números representados como string/Decimal
    v2 = _to_number(v)
    if _is_number(v2):
        # Arredonda para reduzir ruído de float
        return float(round(float(v2), 8))

    return v2

def sort_list_of_dicts(lst: List[Dict[str, Any]], preferred_keys: Tuple[str, ...] = ("id", "pk", "key")) -> List[Dict[str, Any]]:
    """Ordena lista de dicts por chave preferencial existente, fallback por tupla de (k,v)."""
    if not lst:
        return lst

    key_to_use = None
    for k in preferred_keys:
        if isinstance(lst[0], dict) and k in lst[0]:
            key_to_use = k
            break

    if key_to_use:
        return sorted(lst, key=lambda d: (d.get(key_to_use) is None, d.get(key_to_use)))

    # Fallback: ordena pelo repr normalizado de cada item
    return sorted(lst, key=lambda d: json.dumps(normalize_value(d), sort_keys=True))

def results_equivalent(a: Any, b: Any, lenient: bool = True) -> bool:
    """Compara resultados com normalização robusta."""
    a_norm = normalize_value(a)
    b_norm = normalize_value(b)

    if isinstance(a_norm, list) and isinstance(b_norm, list):
        # se for lista de dicts, tenta ordenar
        if a_norm and isinstance(a_norm[0], dict) and b_norm and isinstance(b_norm[0], dict):
            a_norm = sort_list_of_dicts(a_norm)
            b_norm = sort_list_of_dicts(b_norm)

    if a_norm == b_norm:
        return True

    if not lenient:
        return False

    # Modo leniente: tenta comparar estruturas parecidas ainda que haja chaves extras com None
    try:
        if isinstance(a_norm, list) and isinstance(b_norm, list) and len(a_norm) == len(b_norm):
            for x, y in zip(a_norm, b_norm):
                if isinstance(x, dict) and isinstance(y, dict):
                    keys = set(x.keys()) | set(y.keys())
                    for k in keys:
                        xv = x.get(k)
                        yv = y.get(k)
                        if normalize_value(xv) != normalize_value(yv):
                            return False
                else:
                    if normalize_value(x) != normalize_value(y):
                        return False
            return True
    except Exception:
        return False

    return False

# -----------------------------------------------------------------------------
# Adaptadores (injeção de dependência e isolamento)
# -----------------------------------------------------------------------------

class LegacyAdapter:
    def __init__(self, db_path: str):
        if DatabaseManager is None:
            raise RuntimeError("DatabaseManager legado não disponível.")
        self.db = DatabaseManager(framework_db_path=db_path)

    def get_epics(self) -> Any:
        return self.db.get_epics()

    def get_tasks(self, epic_id: int) -> Any:
        return self.db.get_tasks(epic_id)

    def check_health(self) -> Any:
        return self.db.check_database_health()

    def count_epics(self) -> int:
        conn = self.db.get_connection()
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM framework_epics")
            return int(cur.fetchone()[0])


class ModularAdapter:
    """
    Permite configurar a origem do DB durante os testes sem monkey-patch frágil.
    Estratégias:
      1) Se o módulo aceitar variável de ambiente (ex.: FRAMEWORK_DB_PATH), usá-la.
      2) Se `get_connection` aceitar sobrecarga via closure/env, usamos `env_override`.
      3) Fallback: abrir sqlite3 direto para check básicos (apenas testes que não exigem o módulo).
    """
    def __init__(self, db_path: str, env_var: str = "FRAMEWORK_DB_PATH"):
        self.db_path = db_path
        self.env_var = env_var
        self.prev_env = os.environ.get(env_var)
        os.environ[env_var] = db_path  # estratégia #1

        if not HAS_MODULAR:
            raise RuntimeError("API modular não disponível.")

    def __enter__(self) -> "ModularAdapter":
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.prev_env is None:
            os.environ.pop(self.env_var, None)
        else:
            os.environ[self.env_var] = self.prev_env

    # Métodos mapeados
    def list_epics(self) -> Any:
        return list_epics()

    def list_tasks(self, epic_id: int) -> Any:
        return list_tasks(epic_id)

    def health(self) -> Any:
        return check_health()

    def count_epics(self) -> int:
        conn = get_connection()
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM framework_epics")
            return int(cur.fetchone()[0])

# -----------------------------------------------------------------------------
# Setup do ambiente de teste
# -----------------------------------------------------------------------------

def create_schema_and_seed(db_path: str, use_modular_helpers_first: bool = True) -> None:
    """
    Cria schema mínimo e semeia dados. Tenta usar os helpers da API modular (se existirem),
    caindo para SQL direto se indisponíveis.
    """
    # Tenta helpers do módulo
    if use_modular_helpers_first and HAS_MODULAR:
        try:
            # Usa env para direcionar o get_connection da modular
            prev = os.environ.get("FRAMEWORK_DB_PATH")
            os.environ["FRAMEWORK_DB_PATH"] = db_path
            try:
                create_schema_if_needed()
                # Opcional: seed_initial_data() poderia semear “real”, mas queremos dataset controlado.
                # Então, vamos inserir nossos dados controlados após garantir o schema.
            finally:
                if prev is None:
                    os.environ.pop("FRAMEWORK_DB_PATH", None)
                else:
                    os.environ["FRAMEWORK_DB_PATH"] = prev
        except Exception as e:
            logger.warning(f"Falha ao usar helpers do módulo para criar schema: {e}. Usando SQL direto.")

    # Garante schema mínimo (idempotente) — SQL direto
    conn = sqlite3.connect(db_path)
    with conn:
        cur = conn.cursor()
        cur.execute("PRAGMA foreign_keys = ON;")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS framework_epics (
                id INTEGER PRIMARY KEY,
                epic_key TEXT UNIQUE,
                name TEXT,
                status TEXT DEFAULT 'todo',
                progress REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS framework_tasks (
                id INTEGER PRIMARY KEY,
                epic_id INTEGER,
                title TEXT,
                description TEXT,
                status TEXT DEFAULT 'todo',
                estimate_minutes INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (epic_id) REFERENCES framework_epics(id)
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS work_sessions (
                id INTEGER PRIMARY KEY,
                task_id INTEGER,
                duration_minutes INTEGER,
                focus_rating INTEGER DEFAULT 5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES framework_tasks(id)
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_achievements (
                id INTEGER PRIMARY KEY,
                user_id INTEGER DEFAULT 1,
                achievement_type TEXT,
                earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
    conn.close()

def seed_controlled_data(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    with conn:
        cur = conn.cursor()
        # Limpa
        cur.execute("DELETE FROM user_achievements;")
        cur.execute("DELETE FROM work_sessions;")
        cur.execute("DELETE FROM framework_tasks;")
        cur.execute("DELETE FROM framework_epics;")

        epics_data = [
            (1, 'TEST_EPIC_1', 'Test Epic 1', 'active', 25.5),
            (2, 'TEST_EPIC_2', 'Test Epic 2', 'done', 100.0),
            (3, 'TEST_EPIC_3', 'Test Epic 3', 'todo', 0.0),
        ]
        cur.executemany(
            "INSERT INTO framework_epics (id, epic_key, name, status, progress) VALUES (?, ?, ?, ?, ?);",
            epics_data
        )

        tasks_data = [
            (1, 1, 'Test Task 1', 'Description 1', 'done', 30),
            (2, 1, 'Test Task 2', 'Description 2', 'active', 45),
            (3, 2, 'Test Task 3', 'Description 3', 'done', 60),
            (4, 3, 'Test Task 4', 'Description 4', 'todo', 90),
        ]
        cur.executemany(
            "INSERT INTO framework_tasks (id, epic_id, title, description, status, estimate_minutes) VALUES (?, ?, ?, ?, ?, ?);",
            tasks_data
        )

        sessions_data = [
            (1, 1, 30, 8),
            (2, 1, 45, 7),
            (3, 2, 25, 6),
            (4, 3, 60, 9),
        ]
        cur.executemany(
            "INSERT INTO work_sessions (id, task_id, duration_minutes, focus_rating) VALUES (?, ?, ?, ?);",
            sessions_data
        )

        achievements_data = [
            (1, 1, 'TDD_MASTER'),
            (2, 1, 'FOCUS_WARRIOR'),
            (3, 1, 'EARLY_BIRD'),
        ]
        cur.executemany(
            "INSERT INTO user_achievements (id, user_id, achievement_type) VALUES (?, ?, ?);",
            achievements_data
        )

# -----------------------------------------------------------------------------
# Núcleo do validador
# -----------------------------------------------------------------------------

def measure_ms(fn: Callable, *args, **kwargs) -> Tuple[Any, float, Optional[str]]:
    t0 = time.perf_counter()
    try:
        out = fn(*args, **kwargs)
        dt = (time.perf_counter() - t0) * 1000.0
        return out, dt, None
    except Exception as e:
        dt = (time.perf_counter() - t0) * 1000.0
        return None, dt, f"{type(e).__name__}: {e}"

class APIEquivalenceValidator:
    def __init__(self, db_path: str, quick_mode: bool = False, lenient: bool = True, performance_only: bool = False):
        self.db_path = db_path
        self.quick_mode = quick_mode
        self.lenient = lenient
        self.performance_only = performance_only
        self.results: List[ValidationResult] = []

        # Instâncias/adapters criadas durante run()
        self.legacy: Optional[LegacyAdapter] = None
        self.modular_cm: Optional[ModularAdapter] = None

    # --- testes individuais ---------------------------------------------------

    def test_epic_listing(self) -> ValidationResult:
        legacy_out, legacy_ms, legacy_err = measure_ms(self.legacy.get_epics)
        with self.modular_cm:
            modular_out, modular_ms, modular_err = measure_ms(lambda: self.modular_cm.list_epics())

        equivalent = False
        notes = None
        if not self.performance_only and legacy_err is None and modular_err is None:
            equivalent = results_equivalent(legacy_out, modular_out, lenient=self.lenient)
            if not equivalent:
                notes = "Diferenças após normalização; verifique campos extras/formatos."

        return ValidationResult(
            test_name="Epic Listing",
            legacy_result=legacy_out,
            modular_result=modular_out,
            equivalent=equivalent if legacy_err is None and modular_err is None else False,
            legacy_time_ms=legacy_ms,
            modular_time_ms=modular_ms,
            performance_ratio=(modular_ms / legacy_ms) if legacy_ms > 0 else float("inf"),
            error_message=legacy_err or modular_err,
            notes=notes
        )

    def test_task_listing(self) -> ValidationResult:
        legacy_out, legacy_ms, legacy_err = measure_ms(self.legacy.get_tasks, 1)
        with self.modular_cm:
            modular_out, modular_ms, modular_err = measure_ms(lambda: self.modular_cm.list_tasks(1))

        equivalent = False
        notes = None
        if not self.performance_only and legacy_err is None and modular_err is None:
            equivalent = results_equivalent(legacy_out, modular_out, lenient=self.lenient)
            if not equivalent:
                notes = "Diferenças após normalização (id, ordem, tipos)."

        return ValidationResult(
            test_name="Task Listing (epic_id=1)",
            legacy_result=legacy_out,
            modular_result=modular_out,
            equivalent=equivalent if legacy_err is None and modular_err is None else False,
            legacy_time_ms=legacy_ms,
            modular_time_ms=modular_ms,
            performance_ratio=(modular_ms / legacy_ms) if legacy_ms > 0 else float("inf"),
            error_message=legacy_err or modular_err,
            notes=notes
        )

    def test_health_check(self) -> ValidationResult:
        legacy_out, legacy_ms, legacy_err = measure_ms(self.legacy.check_health)
        with self.modular_cm:
            modular_out, modular_ms, modular_err = measure_ms(lambda: self.modular_cm.health())

        equivalent = False
        notes = "Comparação estrutural por 'status' apenas."
        if not self.performance_only and legacy_err is None and modular_err is None:
            equivalent = (
                isinstance(legacy_out, dict) and isinstance(modular_out, dict)
                and "status" in legacy_out and "status" in modular_out
            )

        return ValidationResult(
            test_name="Health Check",
            legacy_result=legacy_out,
            modular_result=modular_out,
            equivalent=equivalent if legacy_err is None and modular_err is None else False,
            legacy_time_ms=legacy_ms,
            modular_time_ms=modular_ms,
            performance_ratio=(modular_ms / legacy_ms) if legacy_ms > 0 else float("inf"),
            error_message=legacy_err or modular_err,
            notes=notes
        )

    def test_connection_count(self) -> ValidationResult:
        legacy_out, legacy_ms, legacy_err = measure_ms(self.legacy.count_epics)
        with self.modular_cm:
            modular_out, modular_ms, modular_err = measure_ms(lambda: self.modular_cm.count_epics())

        equivalent = False
        if not self.performance_only and legacy_err is None and modular_err is None:
            equivalent = int(legacy_out) == int(modular_out)

        return ValidationResult(
            test_name="Connection Handling (COUNT epics)",
            legacy_result=legacy_out,
            modular_result=modular_out,
            equivalent=equivalent if legacy_err is None and modular_err is None else False,
            legacy_time_ms=legacy_ms,
            modular_time_ms=modular_ms,
            performance_ratio=(modular_ms / legacy_ms) if legacy_ms > 0 else float("inf"),
            error_message=legacy_err or modular_err
        )

    # --- execução e relatório -------------------------------------------------

    def run(self) -> List[ValidationResult]:
        if DatabaseManager is None:
            raise RuntimeError("API legada indisponível; não é possível validar.")
        if not HAS_MODULAR:
            raise RuntimeError("API modular indisponível; não é possível validar.")

        self.legacy = LegacyAdapter(self.db_path)
        self.modular_cm = ModularAdapter(self.db_path)

        tests: List[Callable[[], ValidationResult]] = [
            self.test_epic_listing,
            self.test_task_listing,
            self.test_health_check,
            self.test_connection_count,
        ]

        if self.quick_mode:
            tests = [self.test_epic_listing, self.test_task_listing]

        self.results = []
        for test_fn in tests:
            try:
                r = test_fn()
                self.results.append(r)
                status = "✅ PASS" if (r.equivalent and r.error_message is None) or self.performance_only else ("✅ PASS" if r.equivalent else "❌ FAIL")
                perf = "⚡" if r.performance_ratio < 1.0 else ("🐌" if r.performance_ratio > 2.0 else "➡️")
                logger.info(f"{status} {r.test_name} {perf} ({r.performance_ratio:.2f}x)")
                if r.error_message:
                    logger.debug(f"   -> erro: {r.error_message}")
                if r.notes:
                    logger.debug(f"   -> notas: {r.notes}")
            except Exception as e:
                self.results.append(ValidationResult(
                    test_name=test_fn.__name__,
                    legacy_result=None,
                    modular_result=None,
                    equivalent=False,
                    legacy_time_ms=0.0,
                    modular_time_ms=0.0,
                    performance_ratio=0.0,
                    error_message=f"{type(e).__name__}: {e}"
                ))
                logger.exception(f"Teste {test_fn.__name__} falhou com exceção.")
        return self.results

    def build_report(self, detailed: bool = False) -> ValidationReport:
        if not self.results:
            raise ValueError("Sem resultados — execute run() antes.")

        total = len(self.results)
        passed = sum(1 for r in self.results if r.equivalent and (r.error_message is None))
        failed = total - passed

        eq_pct = (passed / total * 100.0) if total else 0.0

        perf_ratios = [r.performance_ratio for r in self.results if r.performance_ratio and math.isfinite(r.performance_ratio) and r.performance_ratio > 0]
        avg_perf = (sum(perf_ratios) / len(perf_ratios)) if perf_ratios else 1.0

        breaking = [r.test_name for r in self.results if not r.equivalent and r.error_message is None]
        perf_improv = [f"{r.test_name}: {r.performance_ratio:.2f}x mais rápido" for r in self.results if r.performance_ratio and r.performance_ratio < 1.0]

        return ValidationReport(
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            total_tests=total,
            passed_tests=passed,
            failed_tests=failed,
            equivalence_percentage=eq_pct,
            average_performance_ratio=avg_perf,
            breaking_changes=breaking,
            performance_improvements=perf_improv,
            test_results=self.results if detailed else []
        )

# -----------------------------------------------------------------------------
# Impressão e exportação de relatórios
# -----------------------------------------------------------------------------

def print_report(report: ValidationReport, detailed: bool = False) -> None:
    print("🔍 **API EQUIVALENCE VALIDATION REPORT**")
    print("=" * 50)
    print(f"📅 **Timestamp:** {report.timestamp}")
    print(f"📊 **Tests:** {report.total_tests} total, {report.passed_tests} passed, {report.failed_tests} failed")
    print(f"✅ **Equivalence:** {report.equivalence_percentage:.1f}%")
    print(f"⚡ **Performance:** {report.average_performance_ratio:.2f}x average ratio\n")

    if report.equivalence_percentage == 100.0 and report.total_tests > 0:
        print("🎉 **RESULT: FULL API EQUIVALENCE ACHIEVED** ✅")
        print("   Zero breaking changes detectados!")
    else:
        print("⚠️  **RESULT: BREAKING CHANGES DETECTED** ❌")
        print(f"   {len(report.breaking_changes)} teste(s) falharam na equivalência")

    if report.breaking_changes:
        print("\n🚨 **Breaking Changes:**")
        for name in report.breaking_changes:
            print(f"   - {name}")

    if report.performance_improvements:
        print("\n⚡ **Performance Improvements:**")
        for imp in report.performance_improvements:
            print(f"   - {imp}")

    if detailed and report.test_results:
        print("\n📋 **Detailed Test Results:**")
        for r in report.test_results:
            status = "✅" if r.equivalent and (r.error_message is None) else "❌"
            print(f"   {status} {r.test_name}")
            print(f"      Legacy:  {r.legacy_time_ms:.2f}ms")
            print(f"      Modular: {r.modular_time_ms:.2f}ms")
            print(f"      Ratio:   {r.performance_ratio:.2f}x")
            if r.error_message:
                print(f"      Error:   {r.error_message}")
            if r.notes:
                print(f"      Notes:   {r.notes}")
            print()

def save_json(report: ValidationReport, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(asdict(report), f, indent=2, ensure_ascii=False, default=str)

def save_junit(report: ValidationReport, path: str) -> None:
    testsuite = Element("testsuite", {
        "name": "APIEquivalence",
        "tests": str(report.total_tests),
        "failures": str(report.failed_tests),
        "timestamp": report.timestamp
    })
    for r in report.test_results if report.test_results else []:
        tc = SubElement(testsuite, "testcase", {
            "classname": "api_equivalence",
            "name": r.test_name,
            "time": f"{(r.modular_time_ms + r.legacy_time_ms)/1000.0:.6f}"
        })
        if not r.equivalent or r.error_message:
            failure = SubElement(tc, "failure", {"message": r.error_message or "Not equivalent"})
            detail = {
                "legacy_time_ms": r.legacy_time_ms,
                "modular_time_ms": r.modular_time_ms,
                "performance_ratio": r.performance_ratio,
                "notes": r.notes,
            }
            failure.text = json.dumps(detail, ensure_ascii=False)

    tree = ElementTree(testsuite)
    tree.write(path, encoding="utf-8", xml_declaration=True)

# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="API Equivalence Validation Suite (Improved)")
    parser.add_argument("--quick", action="store_true", help="Executa validação rápida (testes essenciais)")
    parser.add_argument("--performance-only", action="store_true", help="Compara apenas performance (ignora equivalência)")
    parser.add_argument("--detailed-report", action="store_true", help="Exibe relatório detalhado por teste")
    parser.add_argument("--save-report", metavar="FILE", help="Salva relatório JSON")
    parser.add_argument("--junit-out", metavar="FILE", help="Exporta JUnit XML para CI")
    parser.add_argument("--db", metavar="PATH", help="Usa banco de dados específico")
    parser.add_argument("--keep-db", action="store_true", help="Não apaga o DB temporário ao final")
    parser.add_argument("--print-db-path", action="store_true", help="Imprime o caminho do DB usado")
    parser.add_argument("--no-lenient", action="store_true", help="Desativa comparação leniente (mais estrita)")
    parser.add_argument("--verbose", action="store_true", help="Saída detalhada (DEBUG)")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Determina DB a usar
    temp_file = None
    db_path = args.db
    if not db_path:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        temp_file = tmp.name
        db_path = temp_file

    if args.print-db-path:
        print(f"🗄️  Database path: {db_path}")

    try:
        # Prepara schema e dados
        create_schema_and_seed(db_path, use_modular_helpers_first=True)
        seed_controlled_data(db_path)

        validator = APIEquivalenceValidator(
            db_path=db_path,
            quick_mode=args.quick,
            lenient=not args.no_lenient,
            performance_only=args.performance_only
        )

        results = validator.run()
        # Para permitir relatório detalhado e JUnit, sempre guarde os resultados completos
        report = validator.build_report(detailed=True if (args.detailed_report or args.junit_out) else False)

        print_report(report, detailed=args.detailed_report)

        if args.save_report:
            save_json(report, args.save_report)
            print(f"\n📝 Report JSON salvo em: {args.save_report}")

        if args.junit_out:
            if not report.test_results:
                # Garante ter os detalhes para JUnit
                report = validator.build_report(detailed=True)
            save_junit(report, args.junit_out)
            print(f"🧪 JUnit XML salvo em: {args.junit_out}")

        # Código de saída para CI
        exit_code = 0 if (report.equivalence_percentage == 100.0 or args.performance_only) else 1
        sys.exit(exit_code)

    except Exception as e:
        logger.error(f"Falha na validação: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # Limpeza
        if temp_file and not args.keep_db:
            try:
                Path(temp_file).unlink(missing_ok=True)
                logger.info("DB temporário removido.")
            except Exception as e:
                logger.warning(f"Falha ao remover DB temporário: {e}")

if __name__ == "__main__":
    main()
