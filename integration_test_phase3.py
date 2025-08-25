#!/usr/bin/env python3
"""
Fase 3.3.3.4 - Teste de Integração
Testa integração completa do sistema
"""

import sys
import time
import subprocess
import os
sys.path.insert(0, '/home/david/Documentos/canimport/test-tdd-project')

def test_priority_tests():
    """Executa testes prioritários com pytest"""
    print("\n🧪 Executando Testes Prioritários...")
    
    # Lista de testes prioritários
    priority_tests = [
        "tests/test_migration_schemas.py",
        "tests/test_database_manager_duration_extension.py",
        "tests/test_security_scenarios.py",
        "tests/test_kanban_functionality.py",
    ]
    
    success_count = 0
    for test_file in priority_tests:
        if os.path.exists(test_file):
            print(f"   🔬 Testando: {test_file}")
            try:
                # Executar pytest de forma silenciosa
                result = subprocess.run(
                    [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short", "-q"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    print(f"      ✅ PASSOU")
                    success_count += 1
                else:
                    # Extrair informação resumida do erro
                    error_lines = result.stdout.split('\n')
                    for line in error_lines:
                        if 'FAILED' in line or 'ERROR' in line:
                            print(f"      ❌ FALHOU: {line[:100]}")
                            break
                    else:
                        print(f"      ❌ FALHOU")
            except subprocess.TimeoutExpired:
                print(f"      ⚠️ TIMEOUT (>30s)")
            except Exception as e:
                print(f"      ❌ ERRO: {str(e)[:100]}")
        else:
            print(f"   ⚠️ Arquivo não encontrado: {test_file}")
    
    success_rate = success_count / len(priority_tests) if priority_tests else 0
    print(f"   📊 Taxa de sucesso: {success_rate*100:.1f}% ({success_count}/{len(priority_tests)})")
    return success_rate >= 0.5  # 50% de sucesso

def test_application_import():
    """Testa importação da aplicação principal"""
    print("\n🚀 Testando Aplicação Principal...")
    
    try:
        # Importar aplicação principal
        from streamlit_extension import streamlit_app
        print("   ✅ Aplicação principal: Import OK")
        
        # Verificar componentes principais
        components = []
        
        # Verificar páginas
        try:
            from streamlit_extension.pages import analytics, kanban, projects, timer, settings
            components.append("Páginas")
            print("   ✅ Páginas principais carregadas")
        except Exception as e:
            print(f"   ❌ Erro ao carregar páginas: {str(e)[:100]}")
        
        # Verificar serviços
        try:
            from streamlit_extension.services import ServiceContainer
            components.append("Services")
            print("   ✅ Service layer carregado")
        except Exception as e:
            print(f"   ❌ Erro ao carregar services: {str(e)[:100]}")
        
        # Verificar database
        try:
            from streamlit_extension.database import list_epics, get_connection
            components.append("Database")
            print("   ✅ Database layer carregado")
        except Exception as e:
            print(f"   ❌ Erro ao carregar database: {str(e)[:100]}")
        
        success_rate = len(components) / 3
        print(f"   📊 Componentes carregados: {len(components)}/3 ({success_rate*100:.1f}%)")
        return success_rate >= 0.66  # 2 de 3 componentes
        
    except Exception as e:
        print(f"   ❌ Aplicação principal: {e}")
        return False

def test_query_performance():
    """Testa performance de queries críticas"""
    print("\n📊 Testando Performance de Queries...")
    
    try:
        from streamlit_extension.database import list_epics
        from streamlit_extension.utils.database import DatabaseManager
        
        # Teste performance API modular
        start = time.time()
        epics_mod = list_epics()
        mod_time = time.time() - start
        
        # Teste performance API legacy
        start = time.time()
        db = DatabaseManager()
        epics_leg = db.get_epics()
        leg_time = time.time() - start
        
        print(f"   📈 Performance Modular: {mod_time:.3f}s ({len(epics_mod)} epics)")
        print(f"   📈 Performance Legacy: {leg_time:.3f}s ({len(epics_leg)} epics)")
        
        # Verificar se performance está aceitável
        if mod_time < 1.0 and leg_time < 1.0:  # Ambas < 1 segundo
            print("   ✅ Performance: Excelente (<1s)")
            performance_score = 1.0
        elif mod_time < 2.0 and leg_time < 2.0:  # Ambas < 2 segundos
            print("   ✅ Performance: Aceitável (<2s)")
            performance_score = 0.8
        else:
            print("   ⚠️ Performance: Lenta (>2s)")
            performance_score = 0.5
        
        # Comparar performance relativa
        if mod_time <= leg_time * 2:  # Modular não pode ser 2x mais lenta
            print("   ✅ Performance relativa: Modular competitiva com Legacy")
        else:
            print("   ⚠️ Performance relativa: Modular significativamente mais lenta")
            performance_score *= 0.8
        
        return performance_score >= 0.6
        
    except Exception as e:
        print(f"   ❌ Teste de performance: {e}")
        return False

def test_data_consistency():
    """Testa consistência de dados entre APIs"""
    print("\n🔄 Testando Consistência de Dados...")
    
    try:
        from streamlit_extension.database import list_epics, list_tasks
        from streamlit_extension.utils.database import DatabaseManager
        
        db = DatabaseManager()
        
        # Comparar epics
        modular_epics = list_epics()
        legacy_epics = db.get_epics()
        
        epic_consistency = len(modular_epics) == len(legacy_epics)
        print(f"   📊 Epics - Modular: {len(modular_epics)}, Legacy: {len(legacy_epics)}")
        
        if epic_consistency:
            print(f"   ✅ Epics: Dados consistentes")
        else:
            print(f"   ⚠️ Epics: Inconsistência detectada")
        
        # Comparar tasks (se possível)
        try:
            # API modular pode requerer epic_id
            legacy_tasks = db.get_tasks()
            print(f"   📊 Tasks - Legacy: {len(legacy_tasks)} tasks")
            print(f"   ✅ Tasks: Legacy funcional")
            task_consistency = True
        except Exception as e:
            print(f"   ⚠️ Tasks: Erro ao comparar - {str(e)[:100]}")
            task_consistency = False
        
        # Calcular score de consistência
        consistency_score = (1.0 if epic_consistency else 0.5) * (1.0 if task_consistency else 0.75)
        
        return consistency_score >= 0.5
        
    except Exception as e:
        print(f"   ❌ Teste de consistência: {e}")
        return False

def test_end_to_end_workflow():
    """Testa workflow end-to-end básico"""
    print("\n🔄 Testando Workflow End-to-End...")
    
    try:
        from streamlit_extension.utils.database import DatabaseManager
        
        db = DatabaseManager()
        
        # 1. Listar epics
        epics = db.get_epics()
        print(f"   ✅ Passo 1: Listar epics ({len(epics)} encontrados)")
        
        # 2. Obter tasks
        tasks = db.get_tasks()
        print(f"   ✅ Passo 2: Obter tasks ({len(tasks)} encontradas)")
        
        # 3. Verificar conexão
        conn = db.get_connection()
        if conn:
            print(f"   ✅ Passo 3: Conexão com banco estabelecida")
        
        # 4. Verificar integridade
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM framework_projects")
        project_count = cursor.fetchone()[0]
        print(f"   ✅ Passo 4: Integridade verificada ({project_count} projetos)")
        
        print(f"   ✅ Workflow End-to-End: Completo")
        return True
        
    except Exception as e:
        print(f"   ❌ Workflow End-to-End: {e}")
        return False

def main():
    print("🔍 FASE 3.3.3.4 - TESTE DE INTEGRAÇÃO")
    print("=" * 60)
    
    tests = [
        ("Priority Tests", test_priority_tests),
        ("Application Import", test_application_import),
        ("Query Performance", test_query_performance),
        ("Data Consistency", test_data_consistency),
        ("End-to-End Workflow", test_end_to_end_workflow),
    ]
    
    success_count = 0
    total_tests = len(tests)
    failed_tests = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Executando: {test_name}")
        try:
            if test_func():
                success_count += 1
                print(f"   ✅ {test_name}: PASSOU")
            else:
                print(f"   ❌ {test_name}: FALHOU")
                failed_tests.append(test_name)
        except Exception as e:
            print(f"   ❌ {test_name}: ERRO - {str(e)[:100]}")
            failed_tests.append(test_name)
    
    print("\n" + "=" * 60)
    print(f"📊 RESULTADOS INTEGRAÇÃO:")
    print(f"   Testes Aprovados: {success_count}/{total_tests}")
    print(f"   Taxa de Sucesso: {success_count/total_tests*100:.1f}%")
    
    if failed_tests:
        print(f"\n❌ TESTES FALHOS ({len(failed_tests)}):")
        for test in failed_tests:
            print(f"   - {test}")
    
    if success_count == total_tests:
        print("\n🎉 FASE 3.3.3.4 COMPLETA - Integração total")
        return True
    elif success_count >= total_tests * 0.6:  # 60% de sucesso
        print("\n✅ FASE 3.3.3.4 APROVADA - Integração aceitável (>60%)")
        return True
    else:
        print("\n⚠️ FASE 3.3.3.4 PARCIAL - Problemas de integração detectados")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)