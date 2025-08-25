#!/usr/bin/env python3
"""
Fase 3.3.3.1 - Validação Sintática
Valida sintaxe Python de todos os arquivos críticos
"""

import sys
import py_compile
import os
from pathlib import Path

# Adicionar projeto ao path
sys.path.insert(0, '/home/david/Documentos/canimport/test-tdd-project')

# Lista de arquivos críticos para validação
CRITICAL_FILES = [
    # UI Pages
    "streamlit_extension/pages/projects.py",
    "streamlit_extension/pages/gantt.py",
    "streamlit_extension/pages/analytics.py",
    "streamlit_extension/pages/projeto_wizard.py",
    "streamlit_extension/pages/timer.py",
    "streamlit_extension/pages/settings.py",
    "streamlit_extension/pages/kanban.py",
    
    # Database Layer
    "streamlit_extension/database/seed.py",
    "streamlit_extension/database/connection.py",
    "streamlit_extension/models/base.py",
    "streamlit_extension/models/database.py",
    "streamlit_extension/database/schema.py",
    "streamlit_extension/database/queries.py",
    "streamlit_extension/database/health.py",
    
    # Tests
    "tests/test_migration_schemas.py",
    "tests/test_database_manager_duration_extension.py",
    "tests/test_security_scenarios.py",
    "tests/test_type_hints_database_manager.py",
    "tests/test_kanban_functionality.py",
    "tests/test_epic_progress_defaults.py",
    "tests/test_dashboard_headless.py",
    
    # Utils
    "streamlit_extension/utils/cached_database.py",
    "streamlit_extension/utils/performance_tester.py",
    "scripts/migration/add_performance_indexes.py"
]

def validate_syntax(file_path):
    """Valida sintaxe de um arquivo Python"""
    try:
        py_compile.compile(file_path, doraise=True)
        return True, None
    except py_compile.PyCompileError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)

def main():
    print("🔍 FASE 3.3.3.1 - VALIDAÇÃO SINTÁTICA")
    print("=" * 60)
    
    success_count = 0
    total_files = len(CRITICAL_FILES)
    failed_files = []
    
    for file_path in CRITICAL_FILES:
        if os.path.exists(file_path):
            print(f"🧪 Validando: {file_path}")
            success, error = validate_syntax(file_path)
            
            if success:
                print(f"   ✅ Sintaxe OK")
                success_count += 1
            else:
                print(f"   ❌ ERRO DE SINTAXE")
                print(f"      {error[:200]}")  # Primeiros 200 chars do erro
                failed_files.append((file_path, error))
        else:
            print(f"⚠️  Arquivo não encontrado: {file_path}")
            failed_files.append((file_path, "Arquivo não encontrado"))
    
    print("\n" + "=" * 60)
    print("📊 RESULTADOS SINTAXE:")
    print(f"   Sucessos: {success_count}/{total_files}")
    print(f"   Taxa de Sucesso: {success_count * 100 // total_files}%")
    
    if failed_files:
        print(f"\n❌ ARQUIVOS COM PROBLEMAS ({len(failed_files)}):")
        for file_path, error in failed_files:
            print(f"   - {file_path}")
            if "não encontrado" not in error:
                print(f"     Erro: {error[:100]}")
    
    if success_count == total_files:
        print("\n🎉 FASE 3.3.3.1 COMPLETA - Toda sintaxe válida")
        return True
    else:
        print(f"\n⚠️ FASE 3.3.3.1 PARCIAL - {len(failed_files)} arquivos com problemas")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)