#!/usr/bin/env python3
"""
Script to assign all epics to client David and project ETL SEBRAE
"""
import sqlite3
from datetime import datetime

def main():
    # Connect to the database
    conn = sqlite3.connect('framework.db')
    cursor = conn.cursor()
    
    try:
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")
        
        # 1. Check if client David exists, if not create it
        cursor.execute("""
            SELECT id FROM framework_clients 
            WHERE client_key = 'david' AND deleted_at IS NULL
        """)
        client_result = cursor.fetchone()
        
        if client_result:
            client_id = client_result[0]
            print(f"✅ Client 'David' already exists with ID: {client_id}")
        else:
            cursor.execute("""
                INSERT INTO framework_clients (
                    client_key, name, description, industry, company_size,
                    primary_contact_name, primary_contact_email,
                    timezone, currency, preferred_language,
                    status, client_tier, priority_level,
                    created_at, updated_at
                ) VALUES (
                    'david', 'David', 'Internal Development Client', 
                    'Software', 'individual',
                    'David', 'david@example.com',
                    'America/Sao_Paulo', 'BRL', 'pt-BR',
                    'active', 'premium', 10,
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
            """)
            client_id = cursor.lastrowid
            print(f"✅ Created client 'David' with ID: {client_id}")
        
        # 2. Check if project ETL SEBRAE exists, if not create it
        cursor.execute("""
            SELECT id FROM framework_projects 
            WHERE client_id = ? AND project_key = 'etl_sebrae' AND deleted_at IS NULL
        """, (client_id,))
        project_result = cursor.fetchone()
        
        if project_result:
            project_id = project_result[0]
            print(f"✅ Project 'ETL SEBRAE' already exists with ID: {project_id}")
        else:
            cursor.execute("""
                INSERT INTO framework_projects (
                    client_id, project_key, name, description, summary,
                    project_type, methodology,
                    status, priority, health_status,
                    estimated_hours, budget_currency,
                    visibility, access_level,
                    created_at, updated_at
                ) VALUES (
                    ?, 'etl_sebrae', 'ETL SEBRAE', 
                    'ETL pipeline development for SEBRAE data integration',
                    'Extract, Transform, and Load pipeline for SEBRAE business data processing and analysis',
                    'development', 'agile',
                    'active', 10, 'green',
                    500.0, 'BRL',
                    'client', 'full',
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
            """, (client_id,))
            project_id = cursor.lastrowid
            print(f"✅ Created project 'ETL SEBRAE' with ID: {project_id}")
        
        # 3. Update all epics to point to this project
        cursor.execute("""
            UPDATE framework_epics 
            SET project_id = ?, 
                updated_at = CURRENT_TIMESTAMP
            WHERE deleted_at IS NULL
        """, (project_id,))
        
        updated_count = cursor.rowcount
        print(f"✅ Updated {updated_count} epics to project 'ETL SEBRAE'")
        
        # 4. Verify the update
        cursor.execute("""
            SELECT COUNT(*) FROM framework_epics 
            WHERE project_id = ? AND deleted_at IS NULL
        """, (project_id,))
        verified_count = cursor.fetchone()[0]
        print(f"✅ Verification: {verified_count} epics now belong to project 'ETL SEBRAE'")
        
        # Show hierarchy summary
        cursor.execute("""
            SELECT 
                c.name as client_name,
                p.name as project_name,
                COUNT(DISTINCT e.id) as epic_count,
                COUNT(DISTINCT t.id) as task_count
            FROM framework_clients c
            JOIN framework_projects p ON c.id = p.client_id
            LEFT JOIN framework_epics e ON p.id = e.project_id AND e.deleted_at IS NULL
            LEFT JOIN framework_tasks t ON e.id = t.epic_id
            WHERE c.id = ? AND p.id = ?
            GROUP BY c.name, p.name
        """, (client_id, project_id))
        
        summary = cursor.fetchone()
        if summary:
            print("\n📊 Hierarchy Summary:")
            print(f"   Client: {summary[0]}")
            print(f"   Project: {summary[1]}")
            print(f"   Epics: {summary[2]}")
            print(f"   Tasks: {summary[3]}")
        
        # Commit transaction
        conn.commit()
        print("\n✅ All changes committed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        return 1
    finally:
        conn.close()
    
    return 0

if __name__ == "__main__":
    exit(main())