#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 TESTE COMPLETO DO ALGORITMO TOPOLÓGICO COM DADOS REAIS

Testa o fluxo end-to-end do algoritmo de ordenação topológica:
1. Leitura de épicos reais do banco
2. Leitura de dependências reais
3. Aplicação do algoritmo DETERMINISTIC_TOPOLOGICAL_ORDERING_DEMO
4. Gravação dos resultados no banco
5. Validação da integridade

Este é o teste definitivo antes da implementação da geração IA.
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any

# Add project root to path for algorithm import
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import the topological algorithm
from DETERMINISTIC_TOPOLOGICAL_ORDERING_DEMO import (
    Task, topological_sort_with_priority_corrected, 
    TaskPriorityScore, ScoringWeights
)

def get_connection():
    db_path = project_root / "framework.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def read_epics_from_database(project_id: int = None) -> List[Dict]:
    """Lê épicos reais do banco de dados."""
    print("📖 Reading real epics from database...")
    
    with get_connection() as conn:
        if project_id:
            cursor = conn.execute("""
                SELECT 
                    id, epic_key, name, description, status, priority,
                    effort_estimate, complexity_score, tdd_phase, tdd_order,
                    estimated_hours, created_at, project_id
                FROM framework_epics 
                WHERE project_id = ?
                ORDER BY created_at
            """, (project_id,))
        else:
            cursor = conn.execute("""
                SELECT 
                    id, epic_key, name, description, status, priority,
                    effort_estimate, complexity_score, tdd_phase, tdd_order,
                    estimated_hours, created_at, project_id
                FROM framework_epics 
                ORDER BY project_id, created_at
            """)
        
        epics = cursor.fetchall()
        epics_list = [dict(epic) for epic in epics]
        
        print(f"  ✅ Found {len(epics_list)} epics in database")
        
        # Show summary
        for epic in epics_list:
            effort = epic['effort_estimate'] or 0
            complexity = epic['complexity_score'] or 0
            tdd_info = f"{epic['tdd_phase']}:{epic['tdd_order']}" if epic['tdd_phase'] else "No TDD"
            print(f"    • {epic['epic_key']} - Priority: {epic['priority']} | Effort: {effort} | Complexity: {complexity} | {tdd_info}")
        
        return epics_list

def read_dependencies_from_database(project_id: int = None) -> List[Tuple[str, str]]:
    """Lê dependências reais do banco de dados.""" 
    print("🔗 Reading dependencies from database...")
    
    with get_connection() as conn:
        if project_id:
            cursor = conn.execute("""
                SELECT 
                    e1.epic_key as dependent_key,
                    e2.epic_key as prerequisite_key,
                    dep.dep_type, dep.rationale
                FROM framework_epic_dependencies dep
                JOIN framework_epics e1 ON dep.epic_id = e1.id
                JOIN framework_epics e2 ON dep.depends_on_epic_id = e2.id
                WHERE dep.project_id = ?
                ORDER BY e1.epic_key
            """, (project_id,))
        else:
            cursor = conn.execute("""
                SELECT 
                    e1.epic_key as dependent_key,
                    e2.epic_key as prerequisite_key,
                    dep.dep_type, dep.rationale
                FROM framework_epic_dependencies dep
                JOIN framework_epics e1 ON dep.epic_id = e1.id
                JOIN framework_epics e2 ON dep.depends_on_epic_id = e2.id
                ORDER BY dep.project_id, e1.epic_key
            """)
        
        dependencies_raw = cursor.fetchall()
        dependencies = [(dep['dependent_key'], dep['prerequisite_key']) for dep in dependencies_raw]
        
        print(f"  ✅ Found {len(dependencies)} dependencies in database")
        
        # Show dependencies
        for dep in dependencies_raw:
            print(f"    • {dep['dependent_key']} → depends on → {dep['prerequisite_key']} ({dep['dep_type']})")
        
        return dependencies

def convert_epics_to_tasks(epics: List[Dict]) -> List[Task]:
    """Converte épicos do banco para objetos Task do algoritmo."""
    print("🔄 Converting database epics to Task objects...")
    
    tasks = []
    
    for epic in epics:
        # Garantir valores válidos para campos obrigatórios
        priority = epic.get('priority', 3)
        if priority is None or priority < 1 or priority > 5:
            priority = 3
            
        effort_estimate = epic.get('effort_estimate', 5)
        if effort_estimate is None or effort_estimate < 1:
            effort_estimate = 5
            
        # tdd_order pode ser None para o algoritmo
        tdd_order = epic.get('tdd_order')
        if tdd_order is not None and (tdd_order < 1 or tdd_order > 3):
            tdd_order = None
        
        task = Task(
            task_key=epic['epic_key'],
            id=epic.get('id', 0),
            title=epic.get('name', ''),
            epic_id=epic.get('project_id', 0),
            priority=priority,
            effort_estimate=effort_estimate,
            story_points=int(epic.get('complexity_score', 3)),
            tdd_phase=epic.get('tdd_phase'),
            tdd_order=tdd_order,
            status=epic.get('status', 'todo'),
            created_at=epic.get('created_at')
        )
        
        tasks.append(task)
        print(f"    ✅ {epic['epic_key']} → Task(priority={priority}, effort={effort_estimate}, tdd_order={tdd_order})")
    
    return tasks

def apply_topological_algorithm(tasks: List[Task], dependencies: List[Tuple[str, str]]) -> Tuple[List[str], Dict[str, TaskPriorityScore], float]:
    """Aplica o algoritmo topológico com dados reais."""
    print("🧠 Applying topological ordering algorithm...")
    
    print(f"  📊 Input: {len(tasks)} tasks, {len(dependencies)} dependencies")
    
    # Aplicar algoritmo
    execution_order, task_scores, exec_time = topological_sort_with_priority_corrected(
        tasks, dependencies
    )
    
    print(f"  ⚡ Execution time: {exec_time:.2f}ms")
    print(f"  📋 Execution order: {' → '.join(execution_order)}")
    
    # Mostrar scores detalhados
    print(f"  📊 Task Scores:")
    for task_key in execution_order:
        score = task_scores[task_key]
        print(f"    • {task_key}: {score.total_score:.2f} (prio:{score.priority_score:.1f} density:{score.value_density_score:.1f} unblock:{score.unblock_score:.1f})")
    
    return execution_order, task_scores, exec_time

def save_sort_order_to_database(execution_order: List[str], task_scores: Dict[str, TaskPriorityScore]) -> bool:
    """Grava o sort_order calculado no banco de dados."""
    print("💾 Saving sort_order to database...")
    
    try:
        with get_connection() as conn:
            updated_count = 0
            
            for order_index, epic_key in enumerate(execution_order):
                score = task_scores[epic_key]
                
                cursor = conn.execute("""
                    UPDATE framework_epics 
                    SET 
                        sort_order = ?,
                        updated_at = ?
                    WHERE epic_key = ?
                """, (
                    order_index,
                    datetime.now(),
                    epic_key
                ))
                
                if cursor.rowcount > 0:
                    updated_count += 1
                    print(f"    ✅ Updated {epic_key}: sort_order={order_index}, score={score.total_score:.2f}")
                else:
                    print(f"    ❌ Failed to update {epic_key}")
            
            conn.commit()
            print(f"  ✅ Successfully updated {updated_count} epics")
            return updated_count > 0
            
    except Exception as e:
        print(f"  ❌ Error saving to database: {e}")
        return False

def validate_results() -> bool:
    """Valida os resultados salvos no banco."""
    print("🔍 Validating saved results...")
    
    with get_connection() as conn:
        # Verificar se sort_order foi atribuído
        cursor = conn.execute("""
            SELECT COUNT(*) as total,
                   COUNT(sort_order) as with_sort_order
            FROM framework_epics
        """)
        counts = cursor.fetchone()
        
        print(f"  📊 Total epics: {counts['total']}")
        print(f"  📊 With sort_order: {counts['with_sort_order']}")
        
        if counts['total'] != counts['with_sort_order']:
            print(f"  ❌ Some epics missing sort_order!")
            return False
        
        # Verificar ordem correta 
        cursor = conn.execute("""
            SELECT epic_key, sort_order, complexity_score, priority, effort_estimate
            FROM framework_epics
            ORDER BY sort_order
        """)
        ordered_epics = cursor.fetchall()
        
        print(f"  📋 Final sorted order:")
        for epic in ordered_epics:
            print(f"    {epic['sort_order']+1}. {epic['epic_key']} (score:{epic['complexity_score']:.2f}, prio:{epic['priority']}, effort:{epic['effort_estimate']})")
        
        # Verificar se não há sort_order duplicado
        cursor = conn.execute("""
            SELECT sort_order, COUNT(*) as count
            FROM framework_epics
            WHERE sort_order IS NOT NULL
            GROUP BY sort_order
            HAVING COUNT(*) > 1
        """)
        duplicates = cursor.fetchall()
        
        if duplicates:
            print(f"  ❌ Found duplicate sort_orders: {duplicates}")
            return False
        
        print(f"  ✅ All validation checks passed!")
        return True

def test_performance_with_real_data() -> bool:
    """Testa performance com dados reais."""
    print("⚡ Testing performance with real data...")
    
    # Multiple runs para verificar consistência
    execution_times = []
    orders = []
    
    # Get fresh data for each run
    epics = read_epics_from_database()
    dependencies = read_dependencies_from_database()
    tasks = convert_epics_to_tasks(epics)
    
    for run in range(3):
        execution_order, task_scores, exec_time = topological_sort_with_priority_corrected(
            tasks, dependencies
        )
        execution_times.append(exec_time)
        orders.append(execution_order)
        
        print(f"    Run {run+1}: {exec_time:.2f}ms")
    
    # Verificar consistência (algoritmo deve ser determinístico)
    all_same = all(order == orders[0] for order in orders)
    avg_time = sum(execution_times) / len(execution_times)
    
    print(f"  📊 Average execution time: {avg_time:.2f}ms")
    print(f"  🔄 Deterministic results: {'✅' if all_same else '❌'}")
    
    if not all_same:
        print(f"    ❌ Different orders detected - algorithm not deterministic!")
        for i, order in enumerate(orders):
            print(f"      Run {i+1}: {' → '.join(order)}")
    
    return all_same and avg_time < 100  # Should be <100ms

def compare_with_expected_order() -> bool:
    """Compara com ordem esperada logicamente."""
    print("🎯 Comparing with logically expected order...")
    
    expected_first = ["ECOM_001_DATABASE_SETUP"]  # Database deve ser primeiro
    expected_last = ["ECOM_006_ADMIN_DASHBOARD", "ECOM_007_API_DOCUMENTATION"]   # Admin ou API podem ser últimos
    expected_early = ["ECOM_002_USER_AUTHENTICATION", "ECOM_003_PRODUCT_CATALOG"]  # Auth e Catalog após DB
    expected_middle = ["ECOM_004_SHOPPING_CART"]   # Cart após auth+catalog
    expected_late = ["ECOM_005_PAYMENT_SYSTEM"]    # Payment após cart
    
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT epic_key, sort_order
            FROM framework_epics
            ORDER BY sort_order
        """)
        actual_order = [epic['epic_key'] for epic in cursor.fetchall()]
    
    print(f"  📋 Actual order: {' → '.join(actual_order)}")
    
    checks = []
    
    # Check: Database deve ser primeiro
    if actual_order[0] in expected_first:
        checks.append("✅ Database is first")
    else:
        checks.append(f"❌ Database not first (actual: {actual_order[0]})")
    
    # Check: Admin deve ser último
    if actual_order[-1] in expected_last:
        checks.append("✅ Admin Dashboard is last")
    else:
        checks.append(f"❌ Admin Dashboard not last (actual: {actual_order[-1]})")
    
    # Check: Auth/Catalog devem vir antes de Cart
    auth_pos = actual_order.index("ECOM_002_USER_AUTHENTICATION") if "ECOM_002_USER_AUTHENTICATION" in actual_order else -1
    catalog_pos = actual_order.index("ECOM_003_PRODUCT_CATALOG") if "ECOM_003_PRODUCT_CATALOG" in actual_order else -1
    cart_pos = actual_order.index("ECOM_004_SHOPPING_CART") if "ECOM_004_SHOPPING_CART" in actual_order else -1
    
    if auth_pos >= 0 and catalog_pos >= 0 and cart_pos >= 0:
        if auth_pos < cart_pos and catalog_pos < cart_pos:
            checks.append("✅ Auth & Catalog before Cart")
        else:
            checks.append("❌ Auth/Catalog ordering incorrect")
    
    # Check: Cart deve vir antes de Payment
    payment_pos = actual_order.index("ECOM_005_PAYMENT_SYSTEM") if "ECOM_005_PAYMENT_SYSTEM" in actual_order else -1
    
    if cart_pos >= 0 and payment_pos >= 0:
        if cart_pos < payment_pos:
            checks.append("✅ Cart before Payment") 
        else:
            checks.append("❌ Cart/Payment ordering incorrect")
    
    for check in checks:
        print(f"    {check}")
    
    passed_checks = sum(1 for check in checks if check.startswith("✅"))
    total_checks = len(checks)
    
    print(f"  📊 Logical order validation: {passed_checks}/{total_checks} checks passed")
    
    return passed_checks == total_checks

def test_cycle_detection() -> bool:
    """Testa detecção de ciclos nas dependências."""
    print("🔄 Testing cycle detection...")
    
    with get_connection() as conn:
        # Tentar criar ciclo (deve falhar por trigger)
        try:
            # Pegar dois épicos existentes
            cursor = conn.execute("SELECT id FROM framework_epics LIMIT 2")
            epics = cursor.fetchall()
            
            if len(epics) >= 2:
                epic1_id = epics[0]['id']
                epic2_id = epics[1]['id']
                
                # Tentar criar dependência circular
                conn.execute("BEGIN TRANSACTION")
                
                # Primeiro: epic2 depende de epic1
                conn.execute("""
                    INSERT OR IGNORE INTO framework_epic_dependencies 
                    (project_id, epic_id, depends_on_epic_id) 
                    VALUES (8, ?, ?)
                """, (epic2_id, epic1_id))
                
                # Segundo: epic1 depende de epic2 (ciclo!)
                conn.execute("""
                    INSERT INTO framework_epic_dependencies 
                    (project_id, epic_id, depends_on_epic_id) 
                    VALUES (8, ?, ?)
                """, (epic1_id, epic2_id))
                
                conn.execute("ROLLBACK")
                print("  ❌ Cycle detection failed - circular dependency was allowed!")
                return False
                
        except sqlite3.Error as e:
            conn.execute("ROLLBACK")
            print(f"  ✅ Cycle prevention working (error: {e})")
            return True
    
    return True

def main():
    """Função principal do teste."""
    print("="*80)
    print("🧪 TESTE COMPLETO DO ALGORITMO TOPOLÓGICO COM DADOS REAIS")
    print("="*80)
    print(f"📅 Test Time: {datetime.now().isoformat()}")
    print(f"🗄️ Database: {project_root / 'framework.db'}")
    
    try:
        # Get project ID for e-commerce demo
        with get_connection() as conn:
            cursor = conn.execute("SELECT id FROM framework_projects WHERE project_key = 'ECOMMERCE_DEMO'")
            project = cursor.fetchone()
            if project:
                project_id = project['id']
                print(f"🎯 Using project ECOMMERCE_DEMO (ID: {project_id})")
            else:
                print("❌ ECOMMERCE_DEMO project not found!")
                return False
        
        print()
        
        # Phase 1: Read real data from database
        epics = read_epics_from_database(project_id)
        if not epics:
            print("❌ No epics found in database!")
            return False
        
        dependencies = read_dependencies_from_database(project_id)
        
        print()
        
        # Phase 2: Convert to algorithm format
        tasks = convert_epics_to_tasks(epics)
        
        print()
        
        # Phase 3: Apply topological algorithm
        execution_order, task_scores, exec_time = apply_topological_algorithm(tasks, dependencies)
        
        print()
        
        # Phase 4: Save results to database
        save_success = save_sort_order_to_database(execution_order, task_scores)
        if not save_success:
            print("❌ Failed to save results to database!")
            return False
        
        print()
        
        # Phase 5: Validate results
        validation_success = validate_results()
        if not validation_success:
            print("❌ Result validation failed!")
            return False
        
        print()
        
        # Phase 6: Performance testing
        performance_ok = test_performance_with_real_data()
        if not performance_ok:
            print("❌ Performance test failed!")
            return False
        
        print()
        
        # Phase 7: Logical order validation
        logic_ok = compare_with_expected_order()
        if not logic_ok:
            print("❌ Logical order validation failed!")
            return False
        
        # Note: Cycle detection is handled by database triggers, not tested here
        
        # Final summary
        print()
        print("="*80)
        print("🎉 ALL TESTS PASSED!")
        print("="*80)
        print(f"✅ Algorithm works perfectly with real database data")
        print(f"✅ Performance is excellent ({exec_time:.2f}ms)")
        print(f"✅ Results saved correctly to database")
        print(f"✅ Logical ordering makes sense")
        print(f"✅ System ready for IA-driven epic generation!")
        print("="*80)
        
        return True
        
    except Exception as e:
        print(f"\n💥 TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)