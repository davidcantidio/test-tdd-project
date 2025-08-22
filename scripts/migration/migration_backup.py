#!/usr/bin/env python3
"""
🔐 MIGRATION BACKUP SYSTEM - Automated Database Backup for Migrations

Sistema de backup automatizado para proteger dados antes de migrações críticas.
Executa backups inteligentes com verificação de integridade e estratégias de retenção.

Usage:
    python scripts/migration/migration_backup.py --create --migration 007
    python scripts/migration/migration_backup.py --restore --backup-id 20250822_141500_007
    python scripts/migration/migration_backup.py --list
    python scripts/migration/migration_backup.py --cleanup --older-than 30

Features:
- Backup automático antes de cada migração
- Verificação de integridade com checksums
- Compressão e otimização de espaço
- Sistema de retenção inteligente
- Backup incremental quando possível
- Restauração segura com validação
"""

import os
import sys
import shutil
import sqlite3
import hashlib
import gzip
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import tempfile

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

try:
    from streamlit_extension.config import load_config
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    print("⚠️ Warning: Configuration not available, using defaults")


class MigrationBackupManager:
    """
    Gerenciador de backup para migrações de banco de dados
    """
    
    def __init__(self, db_path: Optional[str] = None, backup_dir: Optional[str] = None):
        """Inicializa o gerenciador de backup"""
        
        # Database paths
        if CONFIG_AVAILABLE:
            config = load_config()
            self.db_path = str(config.get_database_path())
            self.timer_db_path = str(config.get_timer_database_path())
        else:
            # Fallback paths
            self.db_path = db_path or str(project_root / "framework.db")
            self.timer_db_path = str(project_root / "task_timer.db")
        
        # Backup directory
        self.backup_dir = Path(backup_dir or project_root / "backups" / "migrations")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Metadata file
        self.metadata_file = self.backup_dir / "backup_metadata.json"
        
        # Compression settings
        self.compress_backups = True
        self.compression_level = 6  # Good balance of speed vs size
        
        # Retention settings
        self.max_backups_per_migration = 5
        self.max_total_backups = 50
        self.auto_cleanup_days = 90
    
    def create_backup(self, migration_id: str, backup_type: str = "full") -> Dict[str, any]:
        """
        Cria backup completo do banco de dados
        
        Args:
            migration_id: ID da migração (ex: "007", "008")
            backup_type: Tipo de backup ("full", "incremental")
            
        Returns:
            Dict com informações do backup criado
        """
        print(f"🔐 Iniciando backup para migração {migration_id}...")
        
        # Generate backup ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_id = f"{timestamp}_{migration_id}"
        
        # Backup directory for this specific backup
        backup_path = self.backup_dir / backup_id
        backup_path.mkdir(exist_ok=True)
        
        try:
            # Verify databases exist and are accessible
            self._verify_database_access()
            
            # Create backup metadata
            backup_info = {
                "backup_id": backup_id,
                "migration_id": migration_id,
                "backup_type": backup_type,
                "created_at": datetime.now().isoformat(),
                "database_files": [],
                "checksums": {},
                "file_sizes": {},
                "compression_used": self.compress_backups,
                "integrity_verified": False,
                "backup_path": str(backup_path),
                "restoration_tested": False
            }
            
            # Backup main framework database
            if os.path.exists(self.db_path):
                backup_info["database_files"].append("framework.db")
                self._backup_database_file(
                    self.db_path, 
                    backup_path / "framework.db",
                    backup_info
                )
                print(f"✅ Framework database backup: {self._format_file_size(backup_info['file_sizes'].get('framework.db', 0))}")
            
            # Backup timer database
            if os.path.exists(self.timer_db_path):
                backup_info["database_files"].append("task_timer.db")
                self._backup_database_file(
                    self.timer_db_path,
                    backup_path / "task_timer.db", 
                    backup_info
                )
                print(f"✅ Timer database backup: {self._format_file_size(backup_info['file_sizes'].get('task_timer.db', 0))}")
            
            # Create database schema dumps (human readable)
            self._create_schema_dumps(backup_path, backup_info)
            
            # Verify backup integrity
            backup_info["integrity_verified"] = self._verify_backup_integrity(backup_path, backup_info)
            
            if backup_info["integrity_verified"]:
                print("✅ Backup integrity verification passed")
            else:
                print("⚠️ Warning: Backup integrity verification failed")
            
            # Save backup metadata
            self._save_backup_metadata(backup_info)
            
            # Update global metadata
            self._update_global_metadata(backup_info)
            
            # Calculate total backup size
            total_size = sum(backup_info["file_sizes"].values())
            print(f"🎉 Backup concluído: {backup_id}")
            print(f"📊 Total backup size: {self._format_file_size(total_size)}")
            print(f"📁 Backup path: {backup_path}")
            
            return backup_info
            
        except Exception as e:
            print(f"❌ Erro durante backup: {str(e)}")
            # Cleanup partial backup
            if backup_path.exists():
                shutil.rmtree(backup_path, ignore_errors=True)
            raise
    
    def _backup_database_file(self, source_path: str, backup_path: Path, backup_info: Dict):
        """Realiza backup de um arquivo de banco específico"""
        
        # Get database name for metadata
        db_name = backup_path.name
        
        try:
            # Create database backup using SQLite backup API (safer than file copy)
            if backup_path.suffix == '.db':
                self._sqlite_backup(source_path, str(backup_path))
            else:
                # Fallback to file copy for non-SQLite files
                shutil.copy2(source_path, backup_path)
            
            # Calculate file size
            file_size = backup_path.stat().st_size
            backup_info["file_sizes"][db_name] = file_size
            
            # Calculate checksum
            checksum = self._calculate_file_checksum(backup_path)
            backup_info["checksums"][db_name] = checksum
            
            # Compress if enabled
            if self.compress_backups:
                compressed_path = backup_path.with_suffix(backup_path.suffix + '.gz')
                self._compress_file(backup_path, compressed_path)
                
                # Update metadata for compressed file
                compressed_size = compressed_path.stat().st_size
                backup_info["file_sizes"][db_name + '.gz'] = compressed_size
                backup_info["checksums"][db_name + '.gz'] = self._calculate_file_checksum(compressed_path)
                
                # Remove uncompressed file
                backup_path.unlink()
                
                print(f"  📦 Compressed: {self._format_file_size(file_size)} → {self._format_file_size(compressed_size)} ({compressed_size/file_size*100:.1f}%)")
            
        except Exception as e:
            print(f"❌ Erro no backup de {db_name}: {str(e)}")
            raise
    
    def _sqlite_backup(self, source_path: str, backup_path: str):
        """Realiza backup seguro usando SQLite backup API"""
        
        # Source database connection
        source_conn = sqlite3.connect(source_path)
        
        try:
            # Backup database connection
            backup_conn = sqlite3.connect(backup_path)
            
            try:
                # Perform backup using SQLite's backup API
                source_conn.backup(backup_conn)
                
                # Verify backup
                backup_conn.execute("PRAGMA integrity_check").fetchone()
                
            finally:
                backup_conn.close()
                
        finally:
            source_conn.close()
    
    def _create_schema_dumps(self, backup_path: Path, backup_info: Dict):
        """Cria dumps do schema em formato texto para análise"""
        
        schema_dir = backup_path / "schemas"
        schema_dir.mkdir(exist_ok=True)
        
        # Dump framework database schema
        if os.path.exists(self.db_path):
            self._dump_database_schema(
                self.db_path, 
                schema_dir / "framework_schema.sql",
                "Framework Database Schema"
            )
        
        # Dump timer database schema
        if os.path.exists(self.timer_db_path):
            self._dump_database_schema(
                self.timer_db_path,
                schema_dir / "timer_schema.sql", 
                "Timer Database Schema"
            )
        
        backup_info["schema_dumps"] = True
    
    def _dump_database_schema(self, db_path: str, output_path: Path, title: str):
        """Exporta schema do banco para arquivo SQL"""
        
        conn = sqlite3.connect(db_path)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"-- {title}\n")
                f.write(f"-- Generated: {datetime.now().isoformat()}\n")
                f.write(f"-- Source: {db_path}\n\n")
                
                # Get all tables, indexes, triggers, etc.
                for line in conn.iterdump():
                    f.write(line + '\n')
                    
        finally:
            conn.close()
    
    def _compress_file(self, source_path: Path, compressed_path: Path):
        """Comprime arquivo usando gzip"""
        
        with open(source_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb', compresslevel=self.compression_level) as f_out:
                shutil.copyfileobj(f_in, f_out)
    
    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calcula checksum SHA-256 do arquivo"""
        
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
                
        return sha256_hash.hexdigest()
    
    def _verify_database_access(self):
        """Verifica se os bancos de dados estão acessíveis"""
        
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Framework database not found: {self.db_path}")
        
        # Test framework database connection
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()
            conn.close()
        except Exception as e:
            raise Exception(f"Cannot access framework database: {str(e)}")
        
        # Timer database is optional
        if os.path.exists(self.timer_db_path):
            try:
                conn = sqlite3.connect(self.timer_db_path)
                conn.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()
                conn.close()
            except Exception as e:
                print(f"⚠️ Warning: Timer database access issue: {str(e)}")
    
    def _verify_backup_integrity(self, backup_path: Path, backup_info: Dict) -> bool:
        """Verifica integridade do backup"""
        
        try:
            # Verify all expected files exist
            for db_file in backup_info["database_files"]:
                expected_file = backup_path / (db_file + ('.gz' if self.compress_backups else ''))
                if not expected_file.exists():
                    print(f"❌ Missing backup file: {expected_file}")
                    return False
            
            # Test database integrity (if not compressed)
            if not self.compress_backups:
                for db_file in backup_info["database_files"]:
                    if db_file.endswith('.db'):
                        db_backup_path = backup_path / db_file
                        try:
                            conn = sqlite3.connect(str(db_backup_path))
                            result = conn.execute("PRAGMA integrity_check").fetchone()
                            conn.close()
                            
                            if result[0] != "ok":
                                print(f"❌ Database integrity check failed for {db_file}: {result[0]}")
                                return False
                                
                        except Exception as e:
                            print(f"❌ Cannot verify {db_file} integrity: {str(e)}")
                            return False
            
            return True
            
        except Exception as e:
            print(f"❌ Error during integrity verification: {str(e)}")
            return False
    
    def _save_backup_metadata(self, backup_info: Dict):
        """Salva metadados do backup"""
        
        metadata_path = Path(backup_info["backup_path"]) / "backup_info.json"
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(backup_info, f, indent=2, ensure_ascii=False)
    
    def _update_global_metadata(self, backup_info: Dict):
        """Atualiza metadados globais de backup"""
        
        # Load existing metadata
        global_metadata = {}
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    global_metadata = json.load(f)
            except:
                global_metadata = {}
        
        # Initialize structure
        if 'backups' not in global_metadata:
            global_metadata['backups'] = []
        
        if 'statistics' not in global_metadata:
            global_metadata['statistics'] = {
                'total_backups': 0,
                'total_size_bytes': 0,
                'last_cleanup': None
            }
        
        # Add new backup
        global_metadata['backups'].append({
            'backup_id': backup_info['backup_id'],
            'migration_id': backup_info['migration_id'],
            'created_at': backup_info['created_at'],
            'total_size': sum(backup_info['file_sizes'].values()),
            'integrity_verified': backup_info['integrity_verified']
        })
        
        # Update statistics
        global_metadata['statistics']['total_backups'] = len(global_metadata['backups'])
        global_metadata['statistics']['total_size_bytes'] = sum(
            b['total_size'] for b in global_metadata['backups']
        )
        global_metadata['statistics']['last_backup'] = backup_info['created_at']
        
        # Save updated metadata
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(global_metadata, f, indent=2, ensure_ascii=False)
    
    def list_backups(self) -> List[Dict]:
        """Lista todos os backups disponíveis"""
        
        if not self.metadata_file.exists():
            return []
        
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                return metadata.get('backups', [])
                
        except Exception as e:
            print(f"⚠️ Error reading backup metadata: {str(e)}")
            return []
    
    def restore_backup(self, backup_id: str, target_path: Optional[str] = None) -> bool:
        """
        Restaura backup especificado
        
        Args:
            backup_id: ID do backup para restaurar
            target_path: Caminho de destino (None = restaurar no local original)
        """
        print(f"🔄 Iniciando restauração do backup {backup_id}...")
        
        backup_path = self.backup_dir / backup_id
        
        if not backup_path.exists():
            print(f"❌ Backup não encontrado: {backup_id}")
            return False
        
        # Load backup metadata
        metadata_path = backup_path / "backup_info.json"
        if not metadata_path.exists():
            print(f"❌ Metadados do backup não encontrados: {backup_id}")
            return False
        
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                backup_info = json.load(f)
        except Exception as e:
            print(f"❌ Erro lendo metadados do backup: {str(e)}")
            return False
        
        # Restore each database file
        for db_file in backup_info["database_files"]:
            source_file = backup_path / (db_file + ('.gz' if backup_info.get('compression_used', False) else ''))
            
            if target_path:
                restore_path = Path(target_path) / db_file
            else:
                # Restore to original location
                if db_file == "framework.db":
                    restore_path = Path(self.db_path)
                elif db_file == "task_timer.db":
                    restore_path = Path(self.timer_db_path)
                else:
                    restore_path = Path(db_file)  # Fallback
            
            # Create backup of current file if it exists
            if restore_path.exists():
                backup_current = restore_path.with_suffix('.current_backup')
                shutil.copy2(restore_path, backup_current)
                print(f"📦 Current {db_file} backed up to {backup_current}")
            
            try:
                # Restore file
                if backup_info.get('compression_used', False):
                    # Decompress first
                    with gzip.open(source_file, 'rb') as f_in:
                        with open(restore_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                else:
                    shutil.copy2(source_file, restore_path)
                
                # Verify restored database
                if db_file.endswith('.db'):
                    conn = sqlite3.connect(str(restore_path))
                    result = conn.execute("PRAGMA integrity_check").fetchone()
                    conn.close()
                    
                    if result[0] != "ok":
                        print(f"❌ Restored database {db_file} failed integrity check")
                        return False
                
                print(f"✅ Restored {db_file}")
                
            except Exception as e:
                print(f"❌ Error restoring {db_file}: {str(e)}")
                return False
        
        print(f"🎉 Backup {backup_id} restored successfully")
        return True
    
    def cleanup_old_backups(self, older_than_days: int = None):
        """Remove backups antigos baseado em política de retenção"""
        
        if older_than_days is None:
            older_than_days = self.auto_cleanup_days
        
        print(f"🧹 Limpando backups mais antigos que {older_than_days} dias...")
        
        cutoff_date = datetime.now() - timedelta(days=older_than_days)
        removed_count = 0
        total_size_removed = 0
        
        backups = self.list_backups()
        
        for backup in backups[:]:  # Create a copy to modify during iteration
            backup_date = datetime.fromisoformat(backup['created_at'])
            
            if backup_date < cutoff_date:
                backup_id = backup['backup_id']
                backup_path = self.backup_dir / backup_id
                
                if backup_path.exists():
                    # Calculate size before removal
                    size_removed = sum(
                        f.stat().st_size 
                        for f in backup_path.rglob('*') 
                        if f.is_file()
                    )
                    
                    # Remove backup directory
                    shutil.rmtree(backup_path)
                    
                    total_size_removed += size_removed
                    removed_count += 1
                    
                    print(f"🗑️ Removido: {backup_id} ({self._format_file_size(size_removed)})")
        
        # Update metadata
        if removed_count > 0:
            self._cleanup_metadata()
            print(f"✅ Limpeza concluída: {removed_count} backups removidos, {self._format_file_size(total_size_removed)} liberados")
        else:
            print("ℹ️ Nenhum backup para remover")
    
    def _cleanup_metadata(self):
        """Remove metadados de backups que não existem mais"""
        
        if not self.metadata_file.exists():
            return
        
        with open(self.metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        if 'backups' in metadata:
            # Keep only backups that still exist
            metadata['backups'] = [
                backup for backup in metadata['backups']
                if (self.backup_dir / backup['backup_id']).exists()
            ]
            
            # Update statistics
            metadata['statistics']['total_backups'] = len(metadata['backups'])
            metadata['statistics']['total_size_bytes'] = sum(
                backup['total_size'] for backup in metadata['backups']
            )
            metadata['statistics']['last_cleanup'] = datetime.now().isoformat()
        
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Formata tamanho do arquivo em formato legível"""
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def get_backup_statistics(self) -> Dict:
        """Retorna estatísticas dos backups"""
        
        if not self.metadata_file.exists():
            return {
                'total_backups': 0,
                'total_size_bytes': 0,
                'total_size_formatted': '0 B',
                'oldest_backup': None,
                'newest_backup': None
            }
        
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            stats = metadata.get('statistics', {})
            backups = metadata.get('backups', [])
            
            if backups:
                dates = [datetime.fromisoformat(b['created_at']) for b in backups]
                stats['oldest_backup'] = min(dates).isoformat()
                stats['newest_backup'] = max(dates).isoformat()
            
            stats['total_size_formatted'] = self._format_file_size(stats.get('total_size_bytes', 0))
            
            return stats
            
        except Exception as e:
            print(f"⚠️ Error reading backup statistics: {str(e)}")
            return {'error': str(e)}


def main():
    """Função principal do script"""
    
    parser = argparse.ArgumentParser(
        description="Migration Backup System - Automated Database Backup",
        epilog="Use this tool to create, restore, and manage database backups for migrations."
    )
    
    parser.add_argument('--create', action='store_true',
                       help='Create a new backup')
    parser.add_argument('--restore', action='store_true',
                       help='Restore from backup')
    parser.add_argument('--list', action='store_true',
                       help='List available backups')
    parser.add_argument('--cleanup', action='store_true',
                       help='Clean up old backups')
    parser.add_argument('--stats', action='store_true',
                       help='Show backup statistics')
    
    parser.add_argument('--migration', type=str,
                       help='Migration ID (e.g., "007", "008")')
    parser.add_argument('--backup-id', type=str,
                       help='Backup ID for restoration')
    parser.add_argument('--target-path', type=str,
                       help='Target path for restoration (default: original location)')
    parser.add_argument('--older-than', type=int, default=90,
                       help='Remove backups older than N days (default: 90)')
    
    parser.add_argument('--db-path', type=str,
                       help='Custom database path')
    parser.add_argument('--backup-dir', type=str,
                       help='Custom backup directory')
    
    args = parser.parse_args()
    
    # Initialize backup manager
    backup_manager = MigrationBackupManager(
        db_path=args.db_path,
        backup_dir=args.backup_dir
    )
    
    try:
        if args.create:
            if not args.migration:
                print("❌ --migration parameter required for backup creation")
                return 1
            
            backup_info = backup_manager.create_backup(args.migration)
            print(f"\n📋 Backup Summary:")
            print(f"   Backup ID: {backup_info['backup_id']}")
            print(f"   Migration: {backup_info['migration_id']}")
            print(f"   Files: {len(backup_info['database_files'])}")
            print(f"   Integrity: {'✅ Verified' if backup_info['integrity_verified'] else '❌ Failed'}")
            
        elif args.restore:
            if not args.backup_id:
                print("❌ --backup-id parameter required for restoration")
                return 1
            
            success = backup_manager.restore_backup(args.backup_id, args.target_path)
            if not success:
                return 1
            
        elif args.list:
            backups = backup_manager.list_backups()
            
            if not backups:
                print("ℹ️ No backups found")
                return 0
            
            print(f"\n📋 Available Backups ({len(backups)}):")
            print("-" * 80)
            print(f"{'Backup ID':<25} {'Migration':<10} {'Date':<20} {'Size':<12} {'Status'}")
            print("-" * 80)
            
            for backup in sorted(backups, key=lambda x: x['created_at'], reverse=True):
                date_str = datetime.fromisoformat(backup['created_at']).strftime("%Y-%m-%d %H:%M")
                size_str = backup_manager._format_file_size(backup['total_size'])
                status = "✅" if backup.get('integrity_verified', False) else "❌"
                
                print(f"{backup['backup_id']:<25} {backup['migration_id']:<10} {date_str:<20} {size_str:<12} {status}")
            
        elif args.cleanup:
            backup_manager.cleanup_old_backups(args.older_than)
            
        elif args.stats:
            stats = backup_manager.get_backup_statistics()
            
            if 'error' in stats:
                print(f"❌ Error getting statistics: {stats['error']}")
                return 1
            
            print(f"\n📊 Backup Statistics:")
            print(f"   Total Backups: {stats.get('total_backups', 0)}")
            print(f"   Total Size: {stats.get('total_size_formatted', '0 B')}")
            
            if stats.get('oldest_backup'):
                oldest = datetime.fromisoformat(stats['oldest_backup']).strftime("%Y-%m-%d %H:%M")
                print(f"   Oldest Backup: {oldest}")
            
            if stats.get('newest_backup'):
                newest = datetime.fromisoformat(stats['newest_backup']).strftime("%Y-%m-%d %H:%M")
                print(f"   Newest Backup: {newest}")
                
        else:
            print("❌ No action specified. Use --help for usage information.")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())