#!/usr/bin/env python3
"""
Fase 3.3.3.2 - Validação de Imports
Testa se todos os imports híbridos funcionam corretamente
"""

import sys
import importlib
import traceback
from pathlib import Path

# Adicionar projeto ao path
sys.path.insert(0, '/home/david/Documentos/canimport/test-tdd-project')

CRITICAL_MODULES = [
    # UI Pages
    ('streamlit_extension.pages.projects', 'UI/Projects'),
    ('streamlit_extension.pages.gantt', 'UI/Gantt'),
    ('streamlit_extension.pages.analytics', 'UI/Analytics'),
    ('streamlit_extension.pages.projeto_wizard', 'UI/Wizard'),
    ('streamlit_extension.pages.timer', 'UI/Timer'),
    ('streamlit_extension.pages.settings', 'UI/Settings'),
    ('streamlit_extension.pages.kanban', 'UI/Kanban'),
    
    # Database Layer
    ('streamlit_extension.database.seed', 'DB/Seed'),
    ('streamlit_extension.database.connection', 'DB/Connection'),
    ('streamlit_extension.models.base', 'Models/Base'),
    ('streamlit_extension.models.database', 'Models/Database'),
    ('streamlit_extension.database.schema', 'DB/Schema'),
    ('streamlit_extension.database.queries', 'DB/Queries'),
    ('streamlit_extension.database.health', 'DB/Health'),
    
    # Tests
    ('tests.test_migration_schemas', 'Test/Migration'),
    ('tests.test_database_manager_duration_extension', 'Test/Duration'),
    ('tests.test_security_scenarios', 'Test/Security'),
    ('tests.test_type_hints_database_manager', 'Test/TypeHints'),
    ('tests.test_kanban_functionality', 'Test/Kanban'),
    ('tests.test_epic_progress_defaults', 'Test/EpicProgress'),
    ('tests.test_dashboard_headless', 'Test/Dashboard'),
    
    # Utils
    ('streamlit_extension.utils.cached_database', 'Utils/CachedDB'),
    ('streamlit_extension.utils.performance_tester', 'Utils/Performance'),
]

def test_module_import(module_name, display_name):
    """Testa import de um módulo específico"""
    try:
        module = importlib.import_module(module_name)
        
        # Verificar se tem DatabaseManager import
        has_legacy = False
        has_modular = False
        
        if hasattr(module, '__file__'):
            try:
                with open(module.__file__, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'from streamlit_extension.utils.database import' in content:
                        has_legacy = True
                    if 'from streamlit_extension.database import' in content:
                        has_modular = True
            except:
                pass
        
        status = "✅"
        if has_legacy and has_modular:
            status = "✅ (Híbrido)"
        elif has_legacy:
            status = "✅ (Legacy)"
        elif has_modular:
            status = "✅ (Modular)"
            
        return True, f"{status} {display_name}: Import OK"
    except ImportError as e:
        return False, f"❌ {display_name}: ImportError - {str(e)[:100]}"
    except Exception as e:
        return False, f"❌ {display_name}: {type(e).__name__} - {str(e)[:100]}"

def main():
    print("🔍 FASE 3.3.3.2 - VALIDAÇÃO DE IMPORTS")
    print("=" * 60)
    
    success_count = 0
    total_modules = len(CRITICAL_MODULES)
    failed_modules = []
    hybrid_count = 0
    legacy_count = 0
    modular_count = 0
    
    # Agrupar por categoria
    categories = {
        'UI Pages': [],
        'Database Layer': [],
        'Tests': [],
        'Utils': []
    }
    
    for module_name, display_name in CRITICAL_MODULES:
        success, message = test_module_import(module_name, display_name)
        
        # Determinar categoria
        if 'UI/' in display_name:
            category = 'UI Pages'
        elif 'DB/' in display_name or 'Models/' in display_name:
            category = 'Database Layer'
        elif 'Test/' in display_name:
            category = 'Tests'
        else:
            category = 'Utils'
        
        categories[category].append((success, message))
        
        if success:
            success_count += 1
            if 'Híbrido' in message:
                hybrid_count += 1
            elif 'Legacy' in message:
                legacy_count += 1
            elif 'Modular' in message:
                modular_count += 1
        else:
            failed_modules.append(module_name)
    
    # Exibir resultados por categoria
    for category, results in categories.items():
        print(f"\n📁 {category}:")
        for success, message in results:
            print(f"   {message}")
    
    print("\n" + "=" * 60)
    print(f"📊 RESULTADOS IMPORTS:")
    print(f"   Sucessos: {success_count}/{total_modules}")
    print(f"   Taxa de Sucesso: {success_count/total_modules*100:.1f}%")
    
    if success_count > 0:
        print(f"\n📈 DISTRIBUIÇÃO DOS IMPORTS:")
        print(f"   Híbridos: {hybrid_count}")
        print(f"   Legacy apenas: {legacy_count}")
        print(f"   Modular apenas: {modular_count}")
        print(f"   Sem DB imports: {success_count - hybrid_count - legacy_count - modular_count}")
    
    if failed_modules:
        print(f"\n❌ MÓDULOS FALHOS ({len(failed_modules)}):")
        for module in failed_modules:
            print(f"   - {module}")
    
    if success_count == total_modules:
        print("\n🎉 FASE 3.3.3.2 COMPLETA - Todos imports funcionais")
        return True
    elif success_count >= total_modules * 0.95:  # 95% de sucesso
        print("\n✅ FASE 3.3.3.2 APROVADA - Taxa de sucesso aceitável (>95%)")
        return True
    else:
        print("\n⚠️ FASE 3.3.3.2 PARCIAL - Taxa de sucesso abaixo do esperado")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)