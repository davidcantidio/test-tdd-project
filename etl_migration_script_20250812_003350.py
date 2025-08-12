#!/usr/bin/env python3
"""
ETL Script para migração de dados JSON para SQLite
Gerado automaticamente pela auditoria de estrutura
"""

import json
import sqlite3
import os
from datetime import datetime
from typing import Dict, Any, List

class EpicMigrator:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.migration_log = []
    
    def connect(self):
        """Conecta ao banco de dados SQLite"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
    
    def create_tables(self):
        """Cria tabelas necessárias"""
        ddl_statements = [
            """
            CREATE TABLE IF NOT EXISTS framework_epics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                epic_key VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                status VARCHAR(50) DEFAULT 'pending',
                priority INTEGER DEFAULT 1,
                duration_days INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS framework_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_key VARCHAR(50) NOT NULL,
                epic_id INTEGER NOT NULL,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                tdd_phase VARCHAR(20) CHECK(tdd_phase IN ('red', 'green', 'refactor', 'analysis')),
                status VARCHAR(50) DEFAULT 'pending',
                estimate_minutes INTEGER NOT NULL DEFAULT 60,
                story_points INTEGER,
                position INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (epic_id) REFERENCES framework_epics(id),
                UNIQUE(epic_id, task_key)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS task_dependencies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                depends_on_task_key VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES framework_tasks(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS task_deliverables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                deliverable TEXT NOT NULL,
                completed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES framework_tasks(id)
            )
            """
        ]
        
        for ddl in ddl_statements:
            self.conn.execute(ddl)
        
        self.conn.commit()
    
    def migrate_epic(self, epic_data: Dict[str, Any]) -> int:
        """Migra um épico e retorna o ID"""
        epic = epic_data['epic']
        
        cursor = self.conn.execute("""
            INSERT INTO framework_epics 
            (epic_key, name, description, status, priority, duration_days)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            str(epic['id']),
            epic['name'],
            epic.get('description', ''),
            epic.get('status', 'pending'),
            epic.get('priority', 1),
            epic.get('duration', None)
        ))
        
        epic_id = cursor.lastrowid
        self.migration_log.append(f"Epic migrated: {epic['id']} -> DB ID {epic_id}")
        
        # Migra tasks
        for task in epic.get('tasks', []):
            self.migrate_task(task, epic_id)
        
        return epic_id
    
    def migrate_task(self, task_data: Dict[str, Any], epic_id: int):
        """Migra uma task"""
        cursor = self.conn.execute("""
            INSERT INTO framework_tasks 
            (task_key, epic_id, title, description, tdd_phase, status, 
             estimate_minutes, story_points, position)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(task_data['id']),
            epic_id,
            task_data['title'],
            task_data.get('description', ''),
            task_data.get('tdd_phase', 'analysis'),
            task_data.get('status', 'pending'),
            task_data.get('estimate_minutes', 60),
            task_data.get('story_points'),
            task_data.get('position', 0)
        ))
        
        task_id = cursor.lastrowid
        
        # Migra deliverables
        for deliverable in task_data.get('deliverables', []):
            if deliverable:
                self.conn.execute("""
                    INSERT INTO task_deliverables (task_id, deliverable)
                    VALUES (?, ?)
                """, (task_id, str(deliverable)))
        
        # Migra dependências (como chaves, serão resolvidas depois)
        for dep in task_data.get('dependencies', []):
            if dep:
                self.conn.execute("""
                    INSERT INTO task_dependencies (task_id, depends_on_task_key)
                    VALUES (?, ?)
                """, (task_id, str(dep)))
        
        self.migration_log.append(f"Task migrated: {task_data['id']} -> DB ID {task_id}")
    
    def run_migration(self, json_files: List[str]):
        """Executa migração completa"""
        self.connect()
        self.create_tables()
        
        for file_path in json_files:
            print(f"Migrando {file_path}...")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Normaliza dados antes da migração
            normalized = normalize_epic_data(data, os.path.basename(file_path))
            
            # Migra para o banco
            self.migrate_epic(normalized)
        
        self.conn.commit()
        self.conn.close()
        
        print(f"Migração completa! {len(self.migration_log)} operações realizadas.")

def normalize_epic_data(data: Dict[str, Any], filename: str) -> Dict[str, Any]:
    """Normaliza dados do épico (função placeholder)"""
    # Esta função seria importada do script de normalização
    return data

if __name__ == "__main__":
    # Lista de arquivos para migrar
    epic_files = [
        'epics/epic_template.json',
        'epics/example_epic_0.json',
        'epics/template_epic.json',
        'tdd-project-template/epics/epic_1.json',
        'tdd-project-template/epics/template_epic.json'
    ]
    
    # Executa migração
    migrator = EpicMigrator('framework.db')
    migrator.run_migration(epic_files)
