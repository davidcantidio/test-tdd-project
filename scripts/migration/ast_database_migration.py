#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔄 AST Database Migration - DatabaseManager → Modular API

Melhorias:
- Usa ast.unparse (fallback para astor)
- Remoção cirúrgica de imports legados
- Suporte a 'import ... as ...' e múltiplos padrões
- De-duplicação de imports novos
- Regras de migração realmente utilizadas
- Validação mais rígida
- Flags de CLI úteis: --include/--exclude/--backup
"""

import ast
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
import difflib
import fnmatch
from dataclasses import dataclass

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ---------- Utils: unparse ----------
def _to_source(tree: ast.AST) -> str:
    """Return source code from AST using stdlib ast.unparse or astor as fallback."""
    try:
        return ast.unparse(tree)  # Python 3.9+
    except Exception:
        try:
            import astor  # type: ignore
            return astor.to_source(tree)
        except Exception as e:
            raise RuntimeError(
                "Não foi possível converter AST para código. "
                "Instale 'astor' ou use Python 3.9+ com ast.unparse."
            ) from e


# ---------- Data classes ----------
@dataclass
class MigrationRule:
    legacy_import: str
    new_imports: List[str]
    method_mapping: Dict[str, str]
    description: str


@dataclass
class MigrationResult:
    file_path: Path
    original_content: str
    migrated_content: str
    changes_count: int
    migration_rules_applied: List[str]
    success: bool
    error_message: Optional[str] = None


# ---------- Transformer ----------
class DatabaseMigrationTransformer(ast.NodeTransformer):
    """
    Transforma:
      - Imports: remove DatabaseManager (mantendo outros nomes) e injeta novos imports
      - Calls: mapeia métodos legados para as novas funções modulares
      - Instanciações: DatabaseManager() → get_connection()
    """

    LEGACY_MODULE = "streamlit_extension.utils.database"
    LEGACY_CLASS = "DatabaseManager"

    def __init__(self, migration_rules: List[MigrationRule]) -> None:
        self.migration_rules = migration_rules

        # Construir mapping consolidado a partir das regras
        self.method_mappings: Dict[str, str] = {}
        self.new_imports_from_rules: Set[str] = set()
        for rule in migration_rules:
            self.method_mappings.update(rule.method_mapping)
            self.new_imports_from_rules.update(rule.new_imports)

        self.changes_count = 0
        self.applied_rules: List[str] = []
        self.imports_to_add: Set[str] = set()
        self.existing_imports_text: Set[str] = set()

        # Heurística: nomes de variáveis comuns para instâncias/aliases de DB
        self.db_aliases: Set[str] = {"db", "database", "db_manager"}

    # ---------- Helpers ----------
    def _record_existing_import_text(self, node: ast.AST) -> None:
        # Guarda a string de import para evitar duplicatas ao final
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            try:
                txt = _to_source(node).strip()
                self.existing_imports_text.add(txt)
            except Exception:
                pass

    def _queue_new_imports(self, imports: Set[str]) -> None:
        for imp in imports:
            if imp not in self.existing_imports_text:
                self.imports_to_add.add(imp)

    # ---------- Visits ----------
    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.AST:
        self._record_existing_import_text(node)
        if not node.module:
            return node

        # Remoção cirúrgica de DatabaseManager a partir do módulo legado
        if node.module == self.LEGACY_MODULE:
            kept_aliases = [alias for alias in node.names if alias.name != self.LEGACY_CLASS]
            if len(kept_aliases) != len(node.names):
                # Algum DatabaseManager foi removido
                self.changes_count += 1
                self.applied_rules.append("Import legado → removido DatabaseManager")
                # Injetar novos imports derivados das regras
                self._queue_new_imports(set(self.new_imports_from_rules))

            if kept_aliases:
                node.names = kept_aliases
                return node
            else:
                # Sem nomes restantes → apaga import
                return None

        return node

    def visit_Import(self, node: ast.Import) -> ast.AST:
        self._record_existing_import_text(node)
        # Cobre 'import streamlit_extension.utils.database as db'
        new_names = []
        removed = False
        for alias in node.names:
            if alias.name == self.LEGACY_MODULE:
                # Remove este alias por completo; heurística: substituições ocorrerão em Calls
                removed = True
            else:
                new_names.append(alias)

        if removed:
            self.changes_count += 1
            self.applied_rules.append("Import legado (module) → removido")
            self._queue_new_imports(set(self.new_imports_from_rules))

        if new_names:
            node.names = new_names
            return node
        else:
            return None

    def visit_Call(self, node: ast.Call) -> ast.AST:
        # DatabaseManager() → get_connection()
        if isinstance(node.func, ast.Name) and node.func.id == self.LEGACY_CLASS:
            new_call = ast.parse("get_connection()").body[0].value  # type: ignore[attr-defined]
            self.changes_count += 1
            self.applied_rules.append("DatabaseManager() → get_connection()")
            return new_call

        # Mapeamento de métodos: db.get_epics(...) → list_epics(...)
        if isinstance(node.func, ast.Attribute):
            # Caso 1: db.get_epics(...)
            if isinstance(node.func.value, ast.Name) and node.func.value.id in self.db_aliases:
                old = node.func.attr
                if old in self.method_mappings:
                    new_name = self.method_mappings[old]
                    self.changes_count += 1
                    self.applied_rules.append(f"{old}() → {new_name}()")
                    return ast.Call(
                        func=ast.Name(id=new_name, ctx=ast.Load()),
                        args=node.args,
                        keywords=node.keywords,
                    )

            # Caso 2: DatabaseManager().get_epics(...)
            if (
                isinstance(node.func.value, ast.Call)
                and isinstance(node.func.value.func, ast.Name)
                and node.func.value.func.id == self.LEGACY_CLASS
            ):
                old = node.func.attr
                if old in self.method_mappings:
                    new_name = self.method_mappings[old]
                    self.changes_count += 1
                    self.applied_rules.append(f"{old}() → {new_name}()")
                    return ast.Call(
                        func=ast.Name(id=new_name, ctx=ast.Load()),
                        args=node.args,
                        keywords=node.keywords,
                    )

        return self.generic_visit(node)

    def visit_Module(self, node: ast.Module) -> ast.AST:
        # Primeiro, varrer para registrar imports existentes
        for stmt in node.body:
            if isinstance(stmt, (ast.Import, ast.ImportFrom)):
                self._record_existing_import_text(stmt)

        # Executa transformações padrão
        node = self.generic_visit(node)

        # Se houve mudanças, injeta novos imports no topo (sem duplicar)
        if self.changes_count > 0 and self.imports_to_add:
            new_import_nodes: List[ast.stmt] = []
            for imp in sorted(self.imports_to_add):
                # Parse seguro: pode ser "from pkg import x" ou múltiplos em uma linha
                parsed = ast.parse(imp).body
                for stmt in parsed:
                    # Evita duplicar se já existe texto idêntico
                    txt = _to_source(stmt).strip()
                    if txt not in self.existing_imports_text:
                        new_import_nodes.append(stmt)
                        self.existing_imports_text.add(txt)

            # Inserir após docstring se houver
            insert_pos = 1 if (node.body and isinstance(node.body[0], ast.Expr) and isinstance(getattr(node.body[0], "value", None), ast.Str)) else 0
            node.body[insert_pos:insert_pos] = new_import_nodes

        return node


# ---------- Migrator ----------
class ASTDatabaseMigrator:
    def __init__(self) -> None:
        self.migration_rules = self._create_migration_rules()

    def _create_migration_rules(self) -> List[MigrationRule]:
        return [
            MigrationRule(
                legacy_import="from streamlit_extension.utils.database import DatabaseManager",
                new_imports=[
                    "from streamlit_extension.database.connection import get_connection, transaction",
                    "from streamlit_extension.database.queries import list_epics, list_tasks, get_user_stats, list_all_epics, list_all_tasks, list_timer_sessions, get_achievements",
                    "from streamlit_extension.database.health import check_health, optimize",
                    "from streamlit_extension.database.schema import create_schema_if_needed",
                    "from streamlit_extension.database.seed import seed_initial_data",
                ],
                method_mapping={
                    "get_epics": "list_epics",
                    "get_all_epics": "list_all_epics",
                    "get_tasks": "list_tasks",
                    "get_all_tasks": "list_all_tasks",
                    "get_timer_sessions": "list_timer_sessions",
                    "get_user_stats": "get_user_stats",
                    "get_achievements": "get_achievements",
                    "check_database_health": "check_health",
                    "optimize_database": "optimize",
                    "create_schema_if_needed": "create_schema_if_needed",
                    "seed_initial_data": "seed_initial_data",
                },
                description="Migração principal de operações de banco",
            )
        ]

    # ---------- FS helpers ----------
    def find_python_files(self, directory: Path, include: List[str], exclude: List[str]) -> List[Path]:
        files: List[Path] = []
        skip_dirs = {".git", "__pycache__", ".pytest_cache", "node_modules"}

        for p in directory.rglob("*.py"):
            if any(sd in p.parts for sd in skip_dirs):
                continue

            rel = str(p)
            if include and not any(fnmatch.fnmatch(rel, pat) for pat in include):
                continue
            if exclude and any(fnmatch.fnmatch(rel, pat) for pat in exclude):
                continue

            files.append(p)
        return files

    # ---------- Analysis ----------
    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)

            has_legacy = False
            import_lines: List[int] = []
            call_lines: List[int] = []

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module == DatabaseMigrationTransformer.LEGACY_MODULE:
                    if any(alias.name == DatabaseMigrationTransformer.LEGACY_CLASS for alias in node.names):
                        has_legacy = True
                        import_lines.append(node.lineno)
                elif isinstance(node, ast.Import):
                    if any(alias.name == DatabaseMigrationTransformer.LEGACY_MODULE for alias in node.names):
                        has_legacy = True
                        import_lines.append(node.lineno)
                elif isinstance(node, ast.Call):
                    # Instanciação
                    if isinstance(node.func, ast.Name) and node.func.id == DatabaseMigrationTransformer.LEGACY_CLASS:
                        has_legacy = True
                        call_lines.append(node.lineno)
                    # db.get_epics(...)
                    if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                        if node.func.value.id in {"db", "database", "db_manager"}:
                            if node.func.attr in self.migration_rules[0].method_mapping:
                                has_legacy = True
                                call_lines.append(node.lineno)

            return {
                "file_path": file_path,
                "migration_needed": has_legacy,
                "database_imports": import_lines,
                "database_calls": call_lines,
            }
        except Exception as e:
            logger.exception("Erro ao analisar %s", file_path)
            return {"file_path": file_path, "migration_needed": False, "error": str(e)}

    # ---------- Migration ----------
    def migrate_file(self, file_path: Path, dry_run: bool = True, backup: bool = False) -> MigrationResult:
        try:
            original_content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(original_content)
            transformer = DatabaseMigrationTransformer(self.migration_rules)
            new_tree = transformer.visit(tree)
            ast.fix_missing_locations(new_tree)

            migrated_content = _to_source(new_tree)

            if not dry_run and transformer.changes_count > 0:
                if backup:
                    bak = file_path.with_suffix(file_path.suffix + ".bak")
                    bak.write_text(original_content, encoding="utf-8")
                file_path.write_text(migrated_content, encoding="utf-8")

            return MigrationResult(
                file_path=file_path,
                original_content=original_content,
                migrated_content=migrated_content,
                changes_count=transformer.changes_count,
                migration_rules_applied=transformer.applied_rules,
                success=True,
            )
        except Exception as e:
            logger.exception("Erro ao migrar %s", file_path)
            return MigrationResult(
                file_path=file_path,
                original_content="",
                migrated_content="",
                changes_count=0,
                migration_rules_applied=[],
                success=False,
                error_message=str(e),
            )

    # ---------- Report ----------
    def generate_migration_report(self, results: List[MigrationResult], preview_lines: int = 12) -> str:
        total_files = len(results)
        success_files = sum(1 for r in results if r.success and r.changes_count > 0)
        failed = [r for r in results if not r.success]
        total_changes = sum(r.changes_count for r in results)

        report = [
            "🔄 **DATABASE MIGRATION REPORT**",
            "=====================================",
            "",
            "📊 **Summary:**",
            f"- Total files analyzed: {total_files}",
            f"- Files successfully migrated: {success_files}",
            f"- Total changes applied: {total_changes}",
            f"- Failed migrations: {len(failed)}",
            "",
            "📋 **Migration Details:**",
        ]

        for r in results:
            if r.changes_count == 0 and r.success:
                # Sem mudanças — opcional listar
                continue
            report.append(f"\n📁 **{r.file_path}**")
            if r.success:
                report.append(f"   Changes: {r.changes_count}")
                if r.migration_rules_applied:
                    report.append(f"   Rules applied: {', '.join(r.migration_rules_applied)}")

                diff = list(
                    difflib.unified_diff(
                        r.original_content.splitlines(keepends=True),
                        r.migrated_content.splitlines(keepends=True),
                        fromfile=f"a/{r.file_path}",
                        tofile=f"b/{r.file_path}",
                        n=3,
                    )
                )
                if diff:
                    report.append("   Preview:")
                    for line in diff[:preview_lines]:
                        report.append(f"   {line.rstrip()}")
                    if len(diff) > preview_lines:
                        report.append(f"   ... ({len(diff) - preview_lines} more lines)")
            else:
                report.append(f"   ❌ Error: {r.error_message}")

        return "\n".join(report)

    # ---------- Validation ----------
    def validate_migration(self, file_path: Path) -> Dict[str, Any]:
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)

            has_legacy_import = False
            has_legacy_name = False

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module == DatabaseMigrationTransformer.LEGACY_MODULE:
                    if any(alias.name == DatabaseMigrationTransformer.LEGACY_CLASS for alias in node.names):
                        has_legacy_import = True
                elif isinstance(node, ast.Import):
                    if any(alias.name == DatabaseMigrationTransformer.LEGACY_MODULE for alias in node.names):
                        has_legacy_import = True
                elif isinstance(node, ast.Name):
                    if node.id == DatabaseMigrationTransformer.LEGACY_CLASS:
                        has_legacy_name = True
                elif isinstance(node, ast.Attribute):
                    if node.attr == DatabaseMigrationTransformer.LEGACY_CLASS:
                        has_legacy_name = True

            has_modular_imports = "streamlit_extension.database" in content
            syntax_valid = True

            return {
                "file_path": file_path,
                "syntax_valid": syntax_valid,
                "has_legacy_usage": has_legacy_import or has_legacy_name,
                "has_modular_imports": has_modular_imports,
                "migration_complete": (not has_legacy_import and not has_legacy_name) and has_modular_imports,
            }
        except SyntaxError as e:
            return {
                "file_path": file_path,
                "syntax_valid": False,
                "syntax_error": str(e),
                "migration_complete": False,
            }
        except Exception as e:
            return {
                "file_path": file_path,
                "syntax_valid": False,
                "error": str(e),
                "migration_complete": False,
            }


# ---------- CLI ----------
def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate DatabaseManager to Modular API")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without applying them")
    parser.add_argument("--execute", action="store_true", help="Execute the migration")
    parser.add_argument("--files", nargs="+", help="Specific files or directories to migrate")
    parser.add_argument("--validate", action="store_true", help="Validate migration results")
    parser.add_argument("--report", action="store_true", help="Generate detailed migration report")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--include", nargs="*", default=[], help="Glob patterns to include (relative paths)")
    parser.add_argument("--exclude", nargs="*", default=[], help="Glob patterns to exclude (relative paths)")
    parser.add_argument("--backup", action="store_true", help="Write .bak files before changing originals")

    args = parser.parse_args()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    migrator = ASTDatabaseMigrator()

    # Descoberta de arquivos alvo
    target_files: List[Path] = []
    if args.files:
        for spec in args.files:
            p = Path(spec)
            if p.is_file() and p.suffix == ".py":
                target_files.append(p)
            elif p.is_dir():
                target_files.extend(migrator.find_python_files(p, args.include, args.exclude))
    else:
        project_root = Path(__file__).resolve().parents[2]
        base = project_root / "streamlit_extension"
        target_files = migrator.find_python_files(base, args.include, args.exclude)

    logger.info("Found %d Python files to analyze", len(target_files))

    # Validação isolada
    if args.validate:
        print("🔍 **VALIDATION RESULTS:**")
        print("=" * 50)
        for f in target_files:
            res = migrator.validate_migration(f)
            status = "✅" if res.get("migration_complete") else "❌"
            print(f"{status} {f}")
            if not res.get("syntax_valid"):
                print(f"   Syntax Error: {res.get('syntax_error', 'Unknown')}")
            elif res.get("has_legacy_usage"):
                print(f"   Warning: Still has legacy DatabaseManager usage")
        return

    # Análise
    analysis = [migrator.analyze_file(f) for f in target_files]
    to_migrate = [a["file_path"] for a in analysis if a.get("migration_needed")]
    logger.info("Found %d files needing migration", len(to_migrate))

    dry_run = args.dry_run or not args.execute
    print("🔍 **DRY RUN MODE - Preview Only**" if dry_run else "🔄 **EXECUTING MIGRATION**")
    print("=" * 50)

    results: List[MigrationResult] = []
    for f in to_migrate:
        logger.info("Migrating %s", f)
        results.append(migrator.migrate_file(f, dry_run=dry_run, backup=args.backup))

    report = migrator.generate_migration_report(results)
    print(report)

    if args.report:
        report_path = Path("database_migration_report.md")
        report_path.write_text(report, encoding="utf-8")
        print(f"\n📝 Detailed report saved to: {report_path}")

    successful = sum(1 for r in results if r.success and r.changes_count > 0)
    total_changes = sum(r.changes_count for r in results)

    if dry_run:
        print("\n🎯 **PREVIEW COMPLETE**")
        print(f"   {successful} files would be migrated")
        print(f"   {total_changes} changes would be applied")
        print("\n   Run with --execute to apply changes")
    else:
        print("\n✅ **MIGRATION COMPLETE**")
        print(f"   {successful} files migrated successfully")
        print(f"   {total_changes} changes applied")


if __name__ == "__main__":
    main()
