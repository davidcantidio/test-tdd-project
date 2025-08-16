#!/usr/bin/env python3
"""
🔧 DATABASE MAINTENANCE - Framework SQLite

Sistema completo de manutenção automática para framework.db e task_timer.db
com cleanup, backup, otimização e health checks.
"""

import sqlite3
import os
import shutil
import json
import gzip
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('database_maintenance.log'),
        logging.StreamHandler()
    ]
)

class DatabaseMaintenance:
    def __init__(self, framework_db="framework.db", timer_db="task_timer.db"):
        self.framework_db = framework_db
        self.timer_db = timer_db
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
        
        self.stats = {
            'cleaned_records': 0,
            'backed_up_files': 0,
            'optimizations_run': 0,
            'health_checks_passed': 0,
            'errors': []
        }
    
    def run_full_maintenance(self):
        """Executa manutenção completa em ambos os bancos."""
        print("🔧 DATABASE MAINTENANCE - FULL CYCLE")
        print("=" * 60)
        
        start_time = datetime.now()
        
        try:
            # 1. Health checks pré-manutenção
            print("\n🏥 Running pre-maintenance health checks...")
            self.run_health_checks()
            
            # 2. Backup automático
            print("\n💾 Creating automated backups...")
            self.create_backups()
            
            # 3. Limpeza de dados
            print("\n🧹 Running data cleanup procedures...")
            self.run_cleanup_procedures()
            
            # 4. Otimização de performance
            print("\n⚡ Running performance optimization...")
            self.run_performance_optimization()
            
            # 5. Aplicar políticas de retenção
            print("\n📅 Applying data retention policies...")
            self.apply_retention_policies()
            
            # 6. Health checks pós-manutenção
            print("\n🏥 Running post-maintenance health checks...")
            self.run_health_checks()
            
            # 7. Limpar backups antigos
            print("\n🗑️ Cleaning old backups...")
            self.cleanup_old_backups()
            
            # 8. Gerar relatório
            duration = datetime.now() - start_time
            self.generate_maintenance_report(duration)
            
            print(f"\n✅ Maintenance completed successfully in {duration}")
            return True
            
        except Exception as e:
            logging.error(f"Maintenance failed: {e}")
            self.stats['errors'].append(str(e))
            print(f"\n❌ Maintenance failed: {e}")
            return False
    
    def run_health_checks(self):
        """Executa verificações de saúde dos bancos."""
        databases = [
            (self.framework_db, "Framework DB"),
            (self.timer_db, "Timer DB") if Path(self.timer_db).exists() else None
        ]
        
        for db_info in filter(None, databases):
            db_path, db_name = db_info
            print(f"  📊 Checking {db_name}...")
            
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Verifica integridade
                cursor.execute("PRAGMA integrity_check")
                integrity_result = cursor.fetchone()[0]
                
                if integrity_result == "ok":
                    print(f"    ✅ {db_name} integrity: OK")
                    self.stats['health_checks_passed'] += 1
                else:
                    print(f"    ❌ {db_name} integrity: {integrity_result}")
                    self.stats['errors'].append(f"{db_name} integrity check failed: {integrity_result}")
                
                # Verifica tamanho do banco
                db_size = Path(db_path).stat().st_size / (1024 * 1024)  # MB
                print(f"    📏 {db_name} size: {db_size:.2f} MB")
                
                # Verifica foreign keys
                cursor.execute("PRAGMA foreign_key_check")
                fk_violations = cursor.fetchall()
                
                if not fk_violations:
                    print(f"    ✅ {db_name} foreign keys: OK")
                    self.stats['health_checks_passed'] += 1
                else:
                    print(f"    ❌ {db_name} foreign key violations: {len(fk_violations)}")
                    self.stats['errors'].append(f"{db_name} has {len(fk_violations)} FK violations")
                
                # Estatísticas de tabelas
                if db_path == self.framework_db:
                    self._check_framework_stats(cursor)
                else:
                    self._check_timer_stats(cursor)
                
                conn.close()
                
            except Exception as e:
                logging.error(f"Health check failed for {db_name}: {e}")
                self.stats['errors'].append(f"{db_name} health check: {e}")
    
    def _check_framework_stats(self, cursor):
        """Verifica estatísticas específicas do framework.db."""
        cursor.execute("SELECT COUNT(*) FROM framework_epics")
        epic_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM framework_tasks")
        task_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM framework_users WHERE is_active = TRUE")
        user_count = cursor.fetchone()[0]
        
        print(f"    📊 Records: {epic_count} epics, {task_count} tasks, {user_count} active users")
    
    def _check_timer_stats(self, cursor):
        """Verifica estatísticas específicas do task_timer.db."""
        cursor.execute("SELECT COUNT(*) FROM timer_sessions")
        session_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT user_identifier) FROM timer_sessions")
        user_count = cursor.fetchone()[0]
        
        print(f"    📊 Records: {session_count} sessions, {user_count} users")
    
    def create_backups(self):
        """Cria backups automáticos com compressão."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        databases = [
            (self.framework_db, "framework"),
            (self.timer_db, "timer") if Path(self.timer_db).exists() else None
        ]
        
        for db_info in filter(None, databases):
            db_path, db_name = db_info
            
            try:
                # Backup comprimido
                backup_filename = f"{db_name}_{timestamp}.db.gz"
                backup_path = self.backup_dir / backup_filename
                
                with open(db_path, 'rb') as f_in:
                    with gzip.open(backup_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                backup_size = backup_path.stat().st_size / (1024 * 1024)
                print(f"  💾 {db_name}.db backed up ({backup_size:.2f} MB compressed)")
                
                self.stats['backed_up_files'] += 1
                
                # Backup JSON de metadata (para framework.db)
                if db_name == "framework":
                    self._backup_metadata(timestamp)
                
            except Exception as e:
                logging.error(f"Backup failed for {db_name}: {e}")
                self.stats['errors'].append(f"Backup {db_name}: {e}")
    
    def _backup_metadata(self, timestamp):
        """Cria backup JSON das configurações e metadata."""
        try:
            conn = sqlite3.connect(self.framework_db)
            cursor = conn.cursor()
            
            metadata = {
                'timestamp': timestamp,
                'system_settings': [],
                'achievement_types': [],
                'epic_metadata': []
            }
            
            # System settings
            cursor.execute("SELECT * FROM system_settings")
            for row in cursor.fetchall():
                metadata['system_settings'].append({
                    'category': row[1],
                    'setting_key': row[2],
                    'setting_value': row[3],
                    'setting_type': row[4],
                    'description': row[5]
                })
            
            # Achievement types
            cursor.execute("SELECT * FROM achievement_types")
            for row in cursor.fetchall():
                metadata['achievement_types'].append({
                    'code': row[1],
                    'name': row[2],
                    'description': row[3],
                    'category': row[4],
                    'points_reward': row[5],
                    'rarity': row[7]
                })
            
            # Epic metadata
            cursor.execute("""
                SELECT e.epic_key, e.name, s.setting_value 
                FROM framework_epics e
                LEFT JOIN system_settings s ON s.setting_key = 'epic_' || e.id
                WHERE s.category = 'epic_metadata'
            """)
            for row in cursor.fetchall():
                metadata['epic_metadata'].append({
                    'epic_key': row[0],
                    'name': row[1],
                    'metadata': json.loads(row[2]) if row[2] else None
                })
            
            conn.close()
            
            # Salva metadata
            metadata_path = self.backup_dir / f"metadata_{timestamp}.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            print(f"  💾 Metadata backed up ({len(metadata['system_settings'])} settings)")
            
        except Exception as e:
            logging.error(f"Metadata backup failed: {e}")
            self.stats['errors'].append(f"Metadata backup: {e}")
    
    def run_cleanup_procedures(self):
        """Executa procedimentos de limpeza de dados."""
        self._cleanup_framework_db()
        
        if Path(self.timer_db).exists():
            self._cleanup_timer_db()
    
    def _cleanup_framework_db(self):
        """Limpeza específica do framework.db."""
        conn = sqlite3.connect(self.framework_db)
        cursor = conn.cursor()
        
        try:
            # Remove sessões de trabalho órfãs
            cursor.execute("""
                DELETE FROM work_sessions 
                WHERE task_id NOT IN (SELECT id FROM framework_tasks)
            """)
            orphan_sessions = cursor.rowcount
            if orphan_sessions > 0:
                print(f"    🧹 Removed {orphan_sessions} orphan work sessions")
                self.stats['cleaned_records'] += orphan_sessions
            
            # Remove achievements de usuários inativos
            cursor.execute("""
                DELETE FROM user_achievements 
                WHERE user_id IN (
                    SELECT id FROM framework_users WHERE is_active = FALSE
                )
            """)
            inactive_achievements = cursor.rowcount
            if inactive_achievements > 0:
                print(f"    🧹 Removed {inactive_achievements} achievements from inactive users")
                self.stats['cleaned_records'] += inactive_achievements
            
            # Remove streaks antigos (mais de 90 dias sem atividade)
            cursor.execute("""
                DELETE FROM user_streaks 
                WHERE last_activity_date < DATE('now', '-90 days')
                AND current_count = 0
            """)
            old_streaks = cursor.rowcount
            if old_streaks > 0:
                print(f"    🧹 Removed {old_streaks} old inactive streaks")
                self.stats['cleaned_records'] += old_streaks
            
            # Limpa logs de sync antigos
            cursor.execute("""
                DELETE FROM github_sync_log 
                WHERE started_at < DATE('now', '-30 days')
            """)
            old_sync_logs = cursor.rowcount
            if old_sync_logs > 0:
                print(f"    🧹 Removed {old_sync_logs} old sync logs")
                self.stats['cleaned_records'] += old_sync_logs
            
            conn.commit()
            
        except Exception as e:
            logging.error(f"Framework cleanup failed: {e}")
            conn.rollback()
            self.stats['errors'].append(f"Framework cleanup: {e}")
        
        finally:
            conn.close()
    
    def _cleanup_timer_db(self):
        """Limpeza específica do task_timer.db."""
        conn = sqlite3.connect(self.timer_db)
        cursor = conn.cursor()
        
        try:
            # Remove sessões órfãs (sem referência válida)
            cursor.execute("""
                DELETE FROM timer_sessions 
                WHERE started_at < DATE('now', '-180 days')
                AND actual_duration_minutes < 5
            """)
            short_old_sessions = cursor.rowcount
            if short_old_sessions > 0:
                print(f"    🧹 Removed {short_old_sessions} short old timer sessions")
                self.stats['cleaned_records'] += short_old_sessions
            
            # Remove goals muito antigos
            cursor.execute("""
                DELETE FROM daily_goals 
                WHERE goal_date < DATE('now', '-365 days')
            """)
            old_goals = cursor.rowcount
            if old_goals > 0:
                print(f"    🧹 Removed {old_goals} old daily goals")
                self.stats['cleaned_records'] += old_goals
            
            conn.commit()
            
        except Exception as e:
            logging.error(f"Timer cleanup failed: {e}")
            conn.rollback()
            self.stats['errors'].append(f"Timer cleanup: {e}")
        
        finally:
            conn.close()
    
    def run_performance_optimization(self):
        """Executa otimizações de performance."""
        databases = [
            (self.framework_db, "Framework DB"),
            (self.timer_db, "Timer DB") if Path(self.timer_db).exists() else None
        ]
        
        for db_info in filter(None, databases):
            db_path, db_name = db_info
            
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                print(f"  ⚡ Optimizing {db_name}...")
                
                # VACUUM - compacta e desfragmenta
                cursor.execute("VACUUM")
                print(f"    📦 {db_name} vacuumed")
                
                # ANALYZE - atualiza estatísticas do query planner
                cursor.execute("ANALYZE")
                print(f"    📈 {db_name} analyzed")
                
                # Rebuild indexes se necessário
                cursor.execute("REINDEX")
                print(f"    🔍 {db_name} indexes rebuilt")
                
                self.stats['optimizations_run'] += 1
                
                conn.close()
                
            except Exception as e:
                logging.error(f"Optimization failed for {db_name}: {e}")
                self.stats['errors'].append(f"Optimization {db_name}: {e}")
    
    def apply_retention_policies(self):
        """Aplica políticas de retenção de dados."""
        print("  📅 Applying retention policies...")
        
        conn = sqlite3.connect(self.framework_db)
        cursor = conn.cursor()
        
        try:
            # Soft delete para épicos antigos sem atividade
            cursor.execute("""
                UPDATE framework_epics 
                SET deleted_at = CURRENT_TIMESTAMP
                WHERE status = 'completed' 
                AND completed_at < DATE('now', '-1 year')
                AND deleted_at IS NULL
            """)
            soft_deleted = cursor.rowcount
            if soft_deleted > 0:
                print(f"    📅 Soft deleted {soft_deleted} old completed epics")
                self.stats['cleaned_records'] += soft_deleted
            
            # Archive old work sessions
            if Path(self.timer_db).exists():
                timer_conn = sqlite3.connect(self.timer_db)
                timer_cursor = timer_conn.cursor()
                
                # Move sessões antigas para arquivo
                archive_path = self.backup_dir / f"archived_sessions_{datetime.now().strftime('%Y%m')}.json"
                
                timer_cursor.execute("""
                    SELECT * FROM timer_sessions 
                    WHERE started_at < DATE('now', '-2 years')
                """)
                old_sessions = timer_cursor.fetchall()
                
                if old_sessions and not archive_path.exists():
                    archived_data = []
                    for session in old_sessions:
                        archived_data.append({
                            'task_reference': session[1],
                            'user_identifier': session[2],
                            'started_at': session[3],
                            'ended_at': session[4],
                            'duration_minutes': session[6],
                            'focus_rating': session[7],
                            'productivity_rating': session[18]
                        })
                    
                    with open(archive_path, 'w') as f:
                        json.dump(archived_data, f, indent=2)
                    
                    # Remove da tabela principal
                    timer_cursor.execute("""
                        DELETE FROM timer_sessions 
                        WHERE started_at < DATE('now', '-2 years')
                    """)
                    
                    print(f"    📦 Archived {len(old_sessions)} old timer sessions")
                    self.stats['cleaned_records'] += len(old_sessions)
                
                timer_conn.commit()
                timer_conn.close()
            
            conn.commit()
            
        except Exception as e:
            logging.error(f"Retention policy failed: {e}")
            conn.rollback()
            self.stats['errors'].append(f"Retention policy: {e}")
        
        finally:
            conn.close()
    
    def cleanup_old_backups(self):
        """Remove backups antigos (mais de 30 dias)."""
        try:
            cutoff_date = datetime.now() - timedelta(days=30)
            removed_count = 0
            
            for backup_file in self.backup_dir.glob("*"):
                if backup_file.is_file():
                    file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                    if file_time < cutoff_date:
                        backup_file.unlink()
                        removed_count += 1
            
            if removed_count > 0:
                print(f"  🗑️ Removed {removed_count} old backup files")
            else:
                print(f"  ✅ No old backups to remove")
                
        except Exception as e:
            logging.error(f"Backup cleanup failed: {e}")
            self.stats['errors'].append(f"Backup cleanup: {e}")
    
    def generate_maintenance_report(self, duration):
        """Gera relatório final da manutenção."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': duration.total_seconds(),
            'statistics': self.stats.copy(),
            'summary': {
                'total_records_cleaned': self.stats['cleaned_records'],
                'files_backed_up': self.stats['backed_up_files'],
                'optimizations_completed': self.stats['optimizations_run'],
                'health_checks_passed': self.stats['health_checks_passed'],
                'errors_encountered': len(self.stats['errors'])
            },
            'recommendations': self._generate_recommendations()
        }
        
        # Salva relatório
        report_path = f"maintenance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📋 Maintenance Report:")
        print(f"  🕐 Duration: {duration}")
        print(f"  🧹 Records cleaned: {self.stats['cleaned_records']}")
        print(f"  💾 Files backed up: {self.stats['backed_up_files']}")
        print(f"  ⚡ Optimizations: {self.stats['optimizations_run']}")
        print(f"  ✅ Health checks: {self.stats['health_checks_passed']}")
        print(f"  ❌ Errors: {len(self.stats['errors'])}")
        
        if self.stats['errors']:
            print(f"\n⚠️ Errors encountered:")
            for error in self.stats['errors']:
                print(f"    • {error}")
        
        print(f"\n📄 Full report saved: {report_path}")
    
    def _generate_recommendations(self):
        """Gera recomendações baseadas na manutenção."""
        recommendations = []
        
        if self.stats['cleaned_records'] > 100:
            recommendations.append("Consider reviewing data retention policies - high cleanup volume")
        
        if len(self.stats['errors']) > 2:
            recommendations.append("Multiple errors detected - investigate database consistency")
        
        if self.stats['health_checks_passed'] < 4:
            recommendations.append("Health checks failed - database integrity may be compromised")
        
        # Verifica tamanhos dos bancos
        framework_size = Path(self.framework_db).stat().st_size / (1024 * 1024)
        if framework_size > 100:  # 100MB
            recommendations.append("Framework database is large - consider archiving old data")
        
        if not recommendations:
            recommendations.append("Database is healthy - no immediate actions required")
        
        return recommendations

def main():
    """Executa manutenção principal."""
    maintenance = DatabaseMaintenance()
    success = maintenance.run_full_maintenance()
    return success

def quick_backup():
    """Executa apenas backup rápido."""
    print("💾 Quick Backup Mode")
    maintenance = DatabaseMaintenance()
    maintenance.create_backups()
    print("✅ Quick backup completed")

def health_check_only():
    """Executa apenas health checks."""
    print("🏥 Health Check Mode")
    maintenance = DatabaseMaintenance()
    maintenance.run_health_checks()
    print("✅ Health check completed")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode == "backup":
            quick_backup()
        elif mode == "health":
            health_check_only()
        else:
            print("Usage: python database_maintenance.py [backup|health]")
    else:
        success = main()
        sys.exit(0 if success else 1)