#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛒 SETUP DUMMY E-COMMERCE PROJECT

Limpa banco de dados e popula com projeto e épicos dummy coerentes
para testar o algoritmo de ordenação topológica com dados realistas.

Projeto: "Sistema E-commerce Completo"
Épicos: 7 épicos com dependências lógicas e dados realistas
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

def get_connection():
    db_path = Path("framework.db")
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def clean_existing_data():
    """Limpar dados existentes de épicos e dependências."""
    print("🧹 Cleaning existing data...")
    
    with get_connection() as conn:
        # Verificar se há dados existentes
        cursor = conn.execute("SELECT COUNT(*) FROM framework_epic_dependencies")
        existing_deps = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(*) FROM framework_epics")
        existing_epics = cursor.fetchone()[0]
        
        print(f"  Found {existing_epics} existing epics and {existing_deps} dependencies")
        
        if existing_deps > 0 or existing_epics > 0:
            # Desabilitar foreign keys temporariamente para limpeza
            conn.execute("PRAGMA foreign_keys=OFF")
            
            # Limpar dependências primeiro
            cursor = conn.execute("DELETE FROM framework_epic_dependencies")
            deps_deleted = cursor.rowcount
            
            # Limpar épicos
            cursor = conn.execute("DELETE FROM framework_epics")
            epics_deleted = cursor.rowcount
            
            # Resetar sequences (SQLite)
            conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('framework_epics', 'framework_epic_dependencies')")
            
            # Reabilitar foreign keys
            conn.execute("PRAGMA foreign_keys=ON")
            
            conn.commit()
            print(f"  ✅ Deleted {epics_deleted} epics")
            print(f"  ✅ Deleted {deps_deleted} dependencies")
        else:
            print(f"  ✅ No existing data to clean")

def create_dummy_project() -> int:
    """Criar projeto dummy coerente."""
    print("🏗️ Creating dummy e-commerce project...")
    
    project_data = {
        "project_key": "ECOMMERCE_DEMO",
        "name": "Sistema E-commerce Completo",
        "description": "Sistema completo de e-commerce com carrinho, pagamentos e dashboard administrativo",
        "project_type": "development",
        "methodology": "agile",
        "status": "active",
        "priority": 1,
        "estimated_hours": 320.0,  # Total estimado
        "budget_amount": 50000.0,
        "budget_currency": "BRL",
        "objectives": json.dumps([
            "Desenvolver plataforma e-commerce escalável",
            "Implementar sistema de pagamentos seguro", 
            "Criar dashboard administrativo completo",
            "Garantir performance e usabilidade"
        ]),
        "success_criteria": json.dumps([
            "Sistema suporta 1000+ produtos",
            "Tempo de resposta < 2 segundos",
            "99.9% uptime",
            "Integração completa com gateways de pagamento"
        ]),
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    with get_connection() as conn:
        # Verificar se projeto já existe
        cursor = conn.execute("SELECT id FROM framework_projects WHERE project_key = ?", (project_data["project_key"],))
        existing = cursor.fetchone()
        
        if existing:
            project_id = existing[0]
            print(f"  ✅ Using existing project: {project_id}")
        else:
            # Criar novo projeto
            fields = ", ".join(project_data.keys())
            placeholders = ", ".join(["?" for _ in project_data])
            
            cursor = conn.execute(
                f"INSERT INTO framework_projects ({fields}) VALUES ({placeholders})",
                list(project_data.values())
            )
            project_id = cursor.lastrowid
            conn.commit()
            print(f"  ✅ Created project: {project_id}")
    
    return project_id

def create_dummy_epics(project_id: int) -> List[Dict]:
    """Criar épicos dummy realistas com dependências lógicas."""
    print("📋 Creating realistic dummy epics...")
    
    base_time = datetime.now()
    
    # Épicos estruturados com dependências lógicas claras
    epics_data = [
        {
            # Epic 1: Foundation - sem dependências
            "epic_key": "ECOM_001_DATABASE_SETUP",
            "name": "Setup Database Schema & Infrastructure",
            "description": "Configurar banco de dados, tabelas principais, índices e infraestrutura básica do sistema",
            "status": "todo",
            "priority": 1,  # Critical
            "duration_days": 3,
            "effort_estimate": 3,
            "complexity_score": 2.5,
            "tdd_phase": "analysis",
            "tdd_order": None,
            "estimated_hours": 24.0,
            "goals": json.dumps([
                "Estrutura de banco normalizada",
                "Índices de performance",
                "Migrations automatizadas"
            ]),
            "definition_of_done": json.dumps([
                "Todas as tabelas criadas",
                "Índices implementados",
                "Scripts de migração testados",
                "Documentação técnica completa"
            ]),
            "labels": json.dumps(["foundation", "database", "infrastructure"]),
            "created_at": base_time,
        },
        {
            # Epic 2: Authentication - depende do database
            "epic_key": "ECOM_002_USER_AUTHENTICATION", 
            "name": "User Authentication & Authorization System",
            "description": "Sistema completo de autenticação com JWT, roles, permissions e segurança",
            "status": "todo",
            "priority": 1,  # Critical
            "duration_days": 5,
            "effort_estimate": 5,
            "complexity_score": 4.0,
            "tdd_phase": "red",
            "tdd_order": 1,
            "estimated_hours": 40.0,
            "goals": json.dumps([
                "JWT authentication",
                "Role-based access control",
                "Password security"
            ]),
            "definition_of_done": json.dumps([
                "Login/logout funcionando",
                "JWT tokens seguros",
                "Roles e permissions implementadas",
                "Testes de segurança aprovados"
            ]),
            "labels": json.dumps(["security", "authentication", "users"]),
            "created_at": base_time + timedelta(hours=1),
        },
        {
            # Epic 3: Product Catalog - depende do database (paralelo ao auth)
            "epic_key": "ECOM_003_PRODUCT_CATALOG",
            "name": "Product Catalog & Inventory Management", 
            "description": "Catálogo de produtos com categorias, busca, filtros e gestão de estoque",
            "status": "todo", 
            "priority": 2,  # High
            "duration_days": 7,
            "effort_estimate": 7,
            "complexity_score": 3.5,
            "tdd_phase": "green",
            "tdd_order": 2,
            "estimated_hours": 56.0,
            "goals": json.dumps([
                "Catálogo completo de produtos",
                "Sistema de categorias",
                "Busca e filtros avançados"
            ]),
            "definition_of_done": json.dumps([
                "CRUD de produtos completo",
                "Categorias hierárquicas",
                "Busca funcionando",
                "Gestão de estoque básica"
            ]),
            "labels": json.dumps(["catalog", "products", "inventory"]),
            "created_at": base_time + timedelta(hours=2),
        },
        {
            # Epic 4: Shopping Cart - depende de auth + catalog
            "epic_key": "ECOM_004_SHOPPING_CART",
            "name": "Shopping Cart & Session Management",
            "description": "Carrinho de compras com persistência, cálculo de totais e gestão de sessão",
            "status": "todo",
            "priority": 2,  # High
            "duration_days": 4,
            "effort_estimate": 4,
            "complexity_score": 3.0,
            "tdd_phase": "red",
            "tdd_order": 1,
            "estimated_hours": 32.0,
            "goals": json.dumps([
                "Carrinho persistente",
                "Cálculo automático de totais",
                "Gestão de sessão"
            ]),
            "definition_of_done": json.dumps([
                "Adicionar/remover produtos",
                "Cálculo de impostos e frete",
                "Persistência entre sessões",
                "Interface responsiva"
            ]),
            "labels": json.dumps(["cart", "session", "calculations"]),
            "created_at": base_time + timedelta(hours=3),
        },
        {
            # Epic 5: Payment System - depende do cart
            "epic_key": "ECOM_005_PAYMENT_SYSTEM",
            "name": "Payment Processing & Gateway Integration",
            "description": "Sistema de pagamentos com múltiplos gateways, segurança PCI e processamento de transações",
            "status": "todo",
            "priority": 1,  # Critical
            "duration_days": 8,
            "effort_estimate": 8,
            "complexity_score": 5.0,
            "tdd_phase": "green", 
            "tdd_order": 2,
            "estimated_hours": 64.0,
            "goals": json.dumps([
                "Múltiplos gateways de pagamento",
                "Segurança PCI compliance",
                "Processamento de transações"
            ]),
            "definition_of_done": json.dumps([
                "Integração com Stripe/PayPal",
                "Processamento seguro",
                "Webhooks funcionando",
                "Certificação de segurança"
            ]),
            "labels": json.dumps(["payments", "security", "integration"]),
            "created_at": base_time + timedelta(hours=4),
        },
        {
            # Epic 6: Admin Dashboard - depende de tudo
            "epic_key": "ECOM_006_ADMIN_DASHBOARD",
            "name": "Administrative Dashboard & Analytics",
            "description": "Dashboard administrativo com relatórios, analytics e gestão completa do sistema",
            "status": "todo",
            "priority": 3,  # Medium
            "duration_days": 6,
            "effort_estimate": 6,
            "complexity_score": 4.5,
            "tdd_phase": "refactor",
            "tdd_order": 3,
            "estimated_hours": 48.0,
            "goals": json.dumps([
                "Dashboard administrativo completo",
                "Relatórios e analytics",
                "Gestão de usuários e produtos"
            ]),
            "definition_of_done": json.dumps([
                "Dashboard responsivo",
                "Relatórios em tempo real",
                "Exportação de dados",
                "Controles administrativos"
            ]),
            "labels": json.dumps(["admin", "dashboard", "analytics"]),
            "created_at": base_time + timedelta(hours=5),
        },
        {
            # Epic 7: API Documentation - pode ser paralelo
            "epic_key": "ECOM_007_API_DOCUMENTATION",
            "name": "API Documentation & Developer Tools",
            "description": "Documentação completa da API, ferramentas para desenvolvedores e SDK básico",
            "status": "todo",
            "priority": 4,  # Low
            "duration_days": 3,
            "effort_estimate": 3,
            "complexity_score": 2.0,
            "tdd_phase": "review",
            "tdd_order": None,
            "estimated_hours": 24.0,
            "goals": json.dumps([
                "Documentação API completa",
                "Ferramentas para desenvolvedores",
                "Exemplos de integração"
            ]),
            "definition_of_done": json.dumps([
                "OpenAPI/Swagger completo",
                "Exemplos funcionando",
                "SDK básico disponível",
                "Guias de integração"
            ]),
            "labels": json.dumps(["documentation", "api", "sdk"]),
            "created_at": base_time + timedelta(hours=6),
        }
    ]
    
    # Inserir épicos no banco
    with get_connection() as conn:
        epic_ids = []
        
        for epic_data in epics_data:
            epic_data["project_id"] = project_id
            epic_data["updated_at"] = epic_data["created_at"]
            
            # Preparar campos para inserção
            fields = ", ".join(epic_data.keys())
            placeholders = ", ".join(["?" for _ in epic_data])
            
            cursor = conn.execute(
                f"INSERT INTO framework_epics ({fields}) VALUES ({placeholders})",
                list(epic_data.values())
            )
            
            epic_id = cursor.lastrowid
            epic_ids.append(epic_id)
            
            print(f"  ✅ Created epic {epic_id}: {epic_data['name']}")
        
        conn.commit()
    
    return epic_ids, epics_data

def create_epic_dependencies(epic_ids: List[int], epics_data: List[Dict]) -> List[Tuple[str, str]]:
    """Criar dependências lógicas entre épicos."""
    print("🔗 Creating logical epic dependencies...")
    
    # Mapear epic_keys para IDs
    key_to_id = {}
    for i, epic in enumerate(epics_data):
        key_to_id[epic["epic_key"]] = epic_ids[i]
    
    # Dependências lógicas:
    # 1. DATABASE_SETUP (foundation) - sem dependências
    # 2. USER_AUTHENTICATION depende de DATABASE_SETUP
    # 3. PRODUCT_CATALOG depende de DATABASE_SETUP  
    # 4. SHOPPING_CART depende de USER_AUTHENTICATION + PRODUCT_CATALOG
    # 5. PAYMENT_SYSTEM depende de SHOPPING_CART
    # 6. ADMIN_DASHBOARD depende de todos os anteriores
    # 7. API_DOCUMENTATION pode ser independente
    
    dependencies_data = [
        {
            "project_id": epics_data[0]["project_id"],
            "epic_id": key_to_id["ECOM_002_USER_AUTHENTICATION"],
            "depends_on_epic_id": key_to_id["ECOM_001_DATABASE_SETUP"],
            "dep_type": "blocks",
            "rationale": "Authentication requires database tables and user schema",
            "created_at": datetime.now()
        },
        {
            "project_id": epics_data[0]["project_id"], 
            "epic_id": key_to_id["ECOM_003_PRODUCT_CATALOG"],
            "depends_on_epic_id": key_to_id["ECOM_001_DATABASE_SETUP"],
            "dep_type": "blocks",
            "rationale": "Product catalog requires database schema for products and categories",
            "created_at": datetime.now()
        },
        {
            "project_id": epics_data[0]["project_id"],
            "epic_id": key_to_id["ECOM_004_SHOPPING_CART"],
            "depends_on_epic_id": key_to_id["ECOM_002_USER_AUTHENTICATION"],
            "dep_type": "blocks", 
            "rationale": "Shopping cart requires user authentication for session management",
            "created_at": datetime.now()
        },
        {
            "project_id": epics_data[0]["project_id"],
            "epic_id": key_to_id["ECOM_004_SHOPPING_CART"],
            "depends_on_epic_id": key_to_id["ECOM_003_PRODUCT_CATALOG"],
            "dep_type": "blocks",
            "rationale": "Shopping cart needs products from catalog to function",
            "created_at": datetime.now()
        },
        {
            "project_id": epics_data[0]["project_id"],
            "epic_id": key_to_id["ECOM_005_PAYMENT_SYSTEM"],
            "depends_on_epic_id": key_to_id["ECOM_004_SHOPPING_CART"],
            "dep_type": "blocks",
            "rationale": "Payment processing requires complete cart functionality",
            "created_at": datetime.now()
        },
        {
            "project_id": epics_data[0]["project_id"],
            "epic_id": key_to_id["ECOM_006_ADMIN_DASHBOARD"],
            "depends_on_epic_id": key_to_id["ECOM_002_USER_AUTHENTICATION"],
            "dep_type": "blocks",
            "rationale": "Admin dashboard requires authentication system",
            "created_at": datetime.now()
        },
        {
            "project_id": epics_data[0]["project_id"],
            "epic_id": key_to_id["ECOM_006_ADMIN_DASHBOARD"], 
            "depends_on_epic_id": key_to_id["ECOM_003_PRODUCT_CATALOG"],
            "dep_type": "blocks",
            "rationale": "Admin dashboard manages products from catalog",
            "created_at": datetime.now()
        },
        {
            "project_id": epics_data[0]["project_id"],
            "epic_id": key_to_id["ECOM_006_ADMIN_DASHBOARD"],
            "depends_on_epic_id": key_to_id["ECOM_005_PAYMENT_SYSTEM"],
            "dep_type": "blocks", 
            "rationale": "Admin dashboard shows payment analytics and transactions",
            "created_at": datetime.now()
        }
        # API_DOCUMENTATION fica independente - pode ser feita em paralelo
    ]
    
    # Inserir dependências no banco
    with get_connection() as conn:
        for dep_data in dependencies_data:
            fields = ", ".join(dep_data.keys())
            placeholders = ", ".join(["?" for _ in dep_data])
            
            cursor = conn.execute(
                f"INSERT INTO framework_epic_dependencies ({fields}) VALUES ({placeholders})",
                list(dep_data.values())
            )
            
            # Get epic names for logging
            epic_cursor = conn.execute("SELECT name FROM framework_epics WHERE id = ?", (dep_data["epic_id"],))
            epic_name = epic_cursor.fetchone()[0]
            
            depends_cursor = conn.execute("SELECT name FROM framework_epics WHERE id = ?", (dep_data["depends_on_epic_id"],))
            depends_name = depends_cursor.fetchone()[0]
            
            print(f"  ✅ {epic_name} → depends on → {depends_name}")
        
        conn.commit()
    
    # Return dependency tuples for algorithm testing
    dependency_tuples = []
    for dep in dependencies_data:
        # Get epic_keys for the tuples
        epic_key = None
        depends_key = None
        
        for epic in epics_data:
            if key_to_id[epic["epic_key"]] == dep["epic_id"]:
                epic_key = epic["epic_key"]
            if key_to_id[epic["epic_key"]] == dep["depends_on_epic_id"]:
                depends_key = epic["epic_key"]
        
        if epic_key and depends_key:
            dependency_tuples.append((epic_key, depends_key))
    
    return dependency_tuples

def validate_data_integrity():
    """Validar integridade dos dados criados."""
    print("🔍 Validating data integrity...")
    
    with get_connection() as conn:
        # Check epics
        cursor = conn.execute("SELECT COUNT(*) FROM framework_epics")
        epic_count = cursor.fetchone()[0]
        
        # Check dependencies
        cursor = conn.execute("SELECT COUNT(*) FROM framework_epic_dependencies") 
        dep_count = cursor.fetchone()[0]
        
        # Check all required fields are filled
        cursor = conn.execute("""
            SELECT COUNT(*) FROM framework_epics 
            WHERE effort_estimate IS NULL OR complexity_score IS NULL
        """)
        incomplete_count = cursor.fetchone()[0]
        
        # Check foreign key integrity
        cursor = conn.execute("""
            SELECT COUNT(*) FROM framework_epic_dependencies dep
            LEFT JOIN framework_epics e1 ON dep.epic_id = e1.id
            LEFT JOIN framework_epics e2 ON dep.depends_on_epic_id = e2.id
            WHERE e1.id IS NULL OR e2.id IS NULL
        """)
        fk_violations = cursor.fetchone()[0]
        
        print(f"  ✅ Created {epic_count} epics")
        print(f"  ✅ Created {dep_count} dependencies")
        print(f"  ✅ Incomplete epics: {incomplete_count}")
        print(f"  ✅ FK violations: {fk_violations}")
        
        if incomplete_count > 0 or fk_violations > 0:
            print("  ❌ Data integrity issues detected!")
            return False
        else:
            print("  ✅ All data integrity checks passed!")
            return True

def print_summary():
    """Print summary of created data."""
    print("\n" + "="*80)
    print("📊 DUMMY E-COMMERCE PROJECT SETUP SUMMARY")
    print("="*80)
    
    with get_connection() as conn:
        # Project info
        cursor = conn.execute("""
            SELECT project_key, name, estimated_hours, budget_amount 
            FROM framework_projects 
            ORDER BY id DESC LIMIT 1
        """)
        project = cursor.fetchone()
        
        print(f"🏗️ PROJECT:")
        print(f"  Key: {project[0]}")
        print(f"  Name: {project[1]}")
        print(f"  Estimated Hours: {project[2]}")
        print(f"  Budget: R$ {project[3]:,.2f}")
        
        # Epics info
        cursor = conn.execute("""
            SELECT epic_key, name, priority, effort_estimate, complexity_score, tdd_phase
            FROM framework_epics 
            ORDER BY created_at
        """)
        epics = cursor.fetchall()
        
        print(f"\n📋 EPICS ({len(epics)}):")
        for epic in epics:
            tdd_info = f"TDD:{epic[5]}" if epic[5] else "No TDD"
            print(f"  • {epic[0]} - {epic[1]}")
            print(f"    Priority: {epic[2]} | Effort: {epic[3]} days | Complexity: {epic[4]} | {tdd_info}")
        
        # Dependencies info  
        cursor = conn.execute("""
            SELECT 
                e1.epic_key as dependent,
                e2.epic_key as prerequisite,
                dep.dep_type,
                dep.rationale
            FROM framework_epic_dependencies dep
            JOIN framework_epics e1 ON dep.epic_id = e1.id
            JOIN framework_epics e2 ON dep.depends_on_epic_id = e2.id
            ORDER BY e1.epic_key
        """)
        dependencies = cursor.fetchall()
        
        print(f"\n🔗 DEPENDENCIES ({len(dependencies)}):")
        for dep in dependencies:
            print(f"  • {dep[0]} → depends on → {dep[1]} ({dep[2]})")
        
        print(f"\n🎯 EXPECTED TOPOLOGICAL ORDER:")
        print(f"  1. DATABASE_SETUP (foundation)")
        print(f"  2. USER_AUTHENTICATION (after database)")  
        print(f"  3. PRODUCT_CATALOG (after database)")
        print(f"  4. SHOPPING_CART (after auth + catalog)")
        print(f"  5. PAYMENT_SYSTEM (after cart)")
        print(f"  6. API_DOCUMENTATION (independent - can be parallel)")
        print(f"  7. ADMIN_DASHBOARD (after everything)")
        
        print("="*80)

def main():
    """Main execution function."""
    print("🚀 SETTING UP DUMMY E-COMMERCE PROJECT")
    print("="*50)
    
    try:
        # Step 1: Clean existing data
        clean_existing_data()
        
        # Step 2: Create dummy project
        project_id = create_dummy_project()
        
        # Step 3: Create dummy epics
        epic_ids, epics_data = create_dummy_epics(project_id)
        
        # Step 4: Create dependencies
        dependency_tuples = create_epic_dependencies(epic_ids, epics_data)
        
        # Step 5: Validate integrity
        integrity_ok = validate_data_integrity()
        
        if integrity_ok:
            print_summary()
            print(f"\n🎉 SUCCESS: Dummy e-commerce project setup completed!")
            print(f"✅ Ready for topological algorithm testing")
            return True
        else:
            print(f"\n❌ FAILURE: Data integrity issues detected")
            return False
            
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)