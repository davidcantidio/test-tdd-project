#!/usr/bin/env python3
"""
🤖 Systematic File Auditor - Sétima Camada de Auditoria Automatizada

Sistema automatizado que percorre TODOS os arquivos do projeto sistematicamente,
analisando linha por linha, otimizando quando possível, e documentando tudo
com tracking no banco de dados para resiliência completa.

Usage:
    python systematic_file_auditor.py [--resume] [--dry-run] [--max-files=N]
"""

import asyncio
import time
import sys
import os
import sqlite3
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import subprocess
import ast

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from streamlit_extension.utils.database import DatabaseManager


class AuditStatus(Enum):
    """Status of file audit."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class SessionStatus(Enum):
    """Status of audit session."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class FileAuditResult:
    """Result of file audit."""
    file_path: str
    lines_analyzed: int
    issues_found: int
    optimizations_applied: int
    tokens_used: int
    changes_summary: str
    syntax_valid: bool
    backup_created: bool


@dataclass
class AuditSession:
    """Audit session information."""
    session_id: int
    session_start: datetime
    current_file_index: int
    total_files: int
    files_completed: int
    total_tokens_used: int
    session_status: SessionStatus
    estimated_completion: Optional[datetime] = None


class DatabaseTracker:
    """Database tracking system for audit progress."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(f"{__name__}.DatabaseTracker")
        self._initialize_tables()
    
    def _initialize_tables(self) -> None:
        """Initialize audit tracking tables."""
        
        # File audit log table
        create_file_audit_table = """
        CREATE TABLE IF NOT EXISTS file_audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            lines_analyzed INTEGER DEFAULT 0,
            issues_found INTEGER DEFAULT 0,
            optimizations_applied INTEGER DEFAULT 0,
            tokens_used INTEGER DEFAULT 0,
            changes_summary TEXT,
            commit_hash TEXT,
            syntax_valid BOOLEAN DEFAULT TRUE,
            backup_created BOOLEAN DEFAULT FALSE,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # Audit session table
        create_session_table = """
        CREATE TABLE IF NOT EXISTS audit_session (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_start TIMESTAMP NOT NULL,
            session_end TIMESTAMP,
            current_file_index INTEGER DEFAULT 0,
            total_files INTEGER NOT NULL,
            files_completed INTEGER DEFAULT 0,
            total_tokens_used INTEGER DEFAULT 0,
            session_status TEXT DEFAULT 'active',
            estimated_completion TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # Execute table creation
        with self.db_manager.get_connection("framework") as conn:
            conn.execute(create_file_audit_table)
            conn.execute(create_session_table)
            conn.commit()
            
        self.logger.info("Database tracking tables initialized successfully")
    
    def create_session(self, total_files: int) -> int:
        """Create new audit session."""
        session_start = datetime.now()
        
        with self.db_manager.get_connection("framework") as conn:
            cursor = conn.execute("""
                INSERT INTO audit_session (session_start, total_files, session_status)
                VALUES (?, ?, ?)
            """, (session_start, total_files, SessionStatus.ACTIVE.value))
            session_id = cursor.lastrowid
            conn.commit()
            
        self.logger.info(f"Created audit session {session_id} for {total_files} files")
        return session_id
    
    def get_current_session(self) -> Optional[AuditSession]:
        """Get current active session."""
        with self.db_manager.get_connection("framework") as conn:
            cursor = conn.execute("""
                SELECT * FROM audit_session 
                WHERE session_status = 'active'
                ORDER BY session_start DESC LIMIT 1
            """)
            row = cursor.fetchone()
            
        if row:
            return AuditSession(
                session_id=row['id'],
                session_start=datetime.fromisoformat(row['session_start']),
                current_file_index=row['current_file_index'],
                total_files=row['total_files'],
                files_completed=row['files_completed'],
                total_tokens_used=row['total_tokens_used'],
                session_status=SessionStatus(row['session_status']),
                estimated_completion=datetime.fromisoformat(row['estimated_completion']) if row['estimated_completion'] else None
            )
        return None
    
    def update_session_progress(self, session_id: int, file_index: int, tokens_used: int) -> None:
        """Update session progress."""
        with self.db_manager.get_connection("framework") as conn:
            conn.execute("""
                UPDATE audit_session 
                SET current_file_index = ?, 
                    total_tokens_used = total_tokens_used + ?,
                    files_completed = files_completed + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (file_index, tokens_used, session_id))
            conn.commit()
    
    def initialize_file_list(self, file_paths: List[str]) -> None:
        """Initialize file list for audit."""
        with self.db_manager.get_connection("framework") as conn:
            for file_path in file_paths:
                conn.execute("""
                    INSERT OR IGNORE INTO file_audit_log (file_path, status)
                    VALUES (?, ?)
                """, (file_path, AuditStatus.PENDING.value))
            conn.commit()
            
        self.logger.info(f"Initialized {len(file_paths)} files for audit")
    
    def mark_file_in_progress(self, file_path: str) -> None:
        """Mark file as in progress."""
        with self.db_manager.get_connection("framework") as conn:
            conn.execute("""
                UPDATE file_audit_log 
                SET status = ?, started_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE file_path = ?
            """, (AuditStatus.IN_PROGRESS.value, file_path))
            conn.commit()
    
    def mark_file_completed(self, file_path: str, result: FileAuditResult) -> None:
        """Mark file as completed with results."""
        with self.db_manager.get_connection("framework") as conn:
            conn.execute("""
                UPDATE file_audit_log 
                SET status = ?, 
                    completed_at = CURRENT_TIMESTAMP,
                    lines_analyzed = ?,
                    issues_found = ?,
                    optimizations_applied = ?,
                    tokens_used = ?,
                    changes_summary = ?,
                    syntax_valid = ?,
                    backup_created = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE file_path = ?
            """, (
                AuditStatus.COMPLETED.value,
                result.lines_analyzed,
                result.issues_found,
                result.optimizations_applied,
                result.tokens_used,
                result.changes_summary,
                result.syntax_valid,
                result.backup_created,
                file_path
            ))
            conn.commit()
    
    def mark_file_failed(self, file_path: str, error_message: str) -> None:
        """Mark file as failed with error."""
        with self.db_manager.get_connection("framework") as conn:
            conn.execute("""
                UPDATE file_audit_log 
                SET status = ?, 
                    error_message = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE file_path = ?
            """, (AuditStatus.FAILED.value, error_message, file_path))
            conn.commit()
    
    def get_pending_files(self) -> List[str]:
        """Get list of pending files."""
        with self.db_manager.get_connection("framework") as conn:
            cursor = conn.execute("""
                SELECT file_path FROM file_audit_log 
                WHERE status = ? 
                ORDER BY file_path
            """, (AuditStatus.PENDING.value,))
            return [row['file_path'] for row in cursor.fetchall()]
    
    def get_audit_summary(self) -> Dict[str, Any]:
        """Get comprehensive audit summary."""
        with self.db_manager.get_connection("framework") as conn:
            # Overall statistics
            cursor = conn.execute("""
                SELECT 
                    status,
                    COUNT(*) as count,
                    SUM(lines_analyzed) as total_lines,
                    SUM(issues_found) as total_issues,
                    SUM(optimizations_applied) as total_optimizations,
                    SUM(tokens_used) as total_tokens
                FROM file_audit_log 
                GROUP BY status
            """)
            stats = cursor.fetchall()
            
        summary = {
            "statistics": [dict(row) for row in stats],
            "total_files": sum(row['count'] for row in stats),
            "completion_rate": 0.0,
            "last_updated": datetime.now().isoformat()
        }
        
        completed = next((row['count'] for row in stats if row['status'] == 'completed'), 0)
        total = summary["total_files"]
        if total > 0:
            summary["completion_rate"] = (completed / total) * 100
            
        return summary


class TokenManager:
    """Intelligent token usage management with rate limiting."""
    
    def __init__(self, max_tokens_per_hour: int = 40000):
        self.max_tokens_per_hour = max_tokens_per_hour
        self.tokens_used_this_hour = 0
        self.hour_start = time.time()
        self.token_history = []
        self.logger = logging.getLogger(f"{__name__}.TokenManager")
        
        self.logger.info(f"TokenManager initialized with {max_tokens_per_hour} tokens/hour limit")
    
    def _reset_hour_if_needed(self) -> None:
        """Reset hour counter if an hour has passed."""
        if time.time() - self.hour_start >= 3600:  # 1 hour
            self.tokens_used_this_hour = 0
            self.hour_start = time.time()
            self.logger.info("Token counter reset for new hour")
    
    def can_proceed(self, estimated_tokens: int) -> bool:
        """Check if we can proceed with the estimated token usage."""
        self._reset_hour_if_needed()
        
        would_exceed = (self.tokens_used_this_hour + estimated_tokens) > self.max_tokens_per_hour
        
        if would_exceed:
            self.logger.warning(f"Would exceed token limit: {self.tokens_used_this_hour} + {estimated_tokens} > {self.max_tokens_per_hour}")
            
        return not would_exceed
    
    def calculate_sleep_time(self) -> float:
        """Calculate optimal sleep time based on current usage rate."""
        self._reset_hour_if_needed()
        
        time_elapsed = time.time() - self.hour_start
        if time_elapsed < 60:  # Less than 1 minute
            return 0.0
            
        usage_rate = self.tokens_used_this_hour / (time_elapsed / 60)  # tokens per minute
        target_rate = self.max_tokens_per_hour / 60  # target tokens per minute
        
        if usage_rate > target_rate:
            # Calculate sleep time to get back on track
            excess_rate = usage_rate - target_rate
            sleep_time = (excess_rate / target_rate) * 60  # seconds
            return min(sleep_time, 300)  # max 5 minutes
            
        return 0.0
    
    def record_usage(self, tokens_used: int) -> None:
        """Record token usage."""
        self._reset_hour_if_needed()
        
        self.tokens_used_this_hour += tokens_used
        self.token_history.append({
            "timestamp": time.time(),
            "tokens": tokens_used,
            "cumulative": self.tokens_used_this_hour
        })
        
        # Keep only last 100 records
        if len(self.token_history) > 100:
            self.token_history = self.token_history[-100:]
            
        self.logger.debug(f"Recorded {tokens_used} tokens. Hour total: {self.tokens_used_this_hour}")
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics."""
        self._reset_hour_if_needed()
        
        time_elapsed = time.time() - self.hour_start
        usage_rate = self.tokens_used_this_hour / (time_elapsed / 60) if time_elapsed > 0 else 0
        
        return {
            "tokens_used_this_hour": self.tokens_used_this_hour,
            "max_tokens_per_hour": self.max_tokens_per_hour,
            "usage_percentage": (self.tokens_used_this_hour / self.max_tokens_per_hour) * 100,
            "current_rate_per_minute": usage_rate,
            "time_elapsed_minutes": time_elapsed / 60,
            "estimated_sleep_time": self.calculate_sleep_time()
        }


class FileListManager:
    """Manages the list of files to audit."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.streamlit_extension_path = project_root / "streamlit_extension"
        self.logger = logging.getLogger(f"{__name__}.FileListManager")
    
    def get_all_python_files(self) -> List[str]:
        """Get all Python files in streamlit_extension directory."""
        python_files = []
        
        for file_path in self.streamlit_extension_path.rglob("*.py"):
            # Convert to relative path from project root
            relative_path = str(file_path.relative_to(self.project_root))
            python_files.append(relative_path)
            
        python_files.sort()  # Deterministic order
        
        self.logger.info(f"Found {len(python_files)} Python files")
        return python_files
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get information about a file."""
        full_path = self.project_root / file_path
        
        if not full_path.exists():
            return {"exists": False}
            
        stat = full_path.stat()
        
        # Count lines
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = len(f.readlines())
        except Exception:
            lines = 0
            
        return {
            "exists": True,
            "size_bytes": stat.st_size,
            "lines": lines,
            "modified": datetime.fromtimestamp(stat.st_mtime),
            "readable": os.access(full_path, os.R_OK),
            "writable": os.access(full_path, os.W_OK)
        }


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('systematic_audit.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)


def main():
    """Main entry point for systematic file auditor."""
    parser = argparse.ArgumentParser(description="Systematic File Auditor - Sétima Camada")
    parser.add_argument("--resume", action="store_true", help="Resume from previous session")
    parser.add_argument("--dry-run", action="store_true", help="Dry run without making changes")
    parser.add_argument("--max-files", type=int, help="Maximum number of files to process")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(args.verbose)
    logger.info("🤖 Systematic File Auditor - Sétima Camada INICIANDO")
    
    # Initialize components
    try:
        db_manager = DatabaseManager()
        tracker = DatabaseTracker(db_manager)
        token_manager = TokenManager()
        file_manager = FileListManager(project_root)
        
        logger.info("✅ All components initialized successfully")
        
        # Get file list
        all_files = file_manager.get_all_python_files()
        if args.max_files:
            all_files = all_files[:args.max_files]
            
        logger.info(f"📁 Processing {len(all_files)} files")
        
        # Initialize or resume session
        if args.resume:
            session = tracker.get_current_session()
            if session:
                logger.info(f"📋 Resuming session {session.session_id} from file {session.current_file_index}")
            else:
                logger.warning("No active session found to resume")
                session = None
        else:
            session = None
            
        if not session:
            # Create new session
            tracker.initialize_file_list(all_files)
            session_id = tracker.create_session(len(all_files))
            logger.info(f"🚀 Created new session {session_id}")
        
        # Show summary
        summary = tracker.get_audit_summary()
        logger.info(f"📊 Audit Summary: {summary}")
        
        # Show token manager status
        token_stats = token_manager.get_usage_stats()
        logger.info(f"🎫 Token Stats: {token_stats}")
        
        if args.dry_run:
            logger.info("🧪 DRY RUN MODE - No changes will be made")
            logger.info("✅ FASE 1 Infrastructure setup completed successfully")
        else:
            logger.info("⚠️  REAL MODE - Changes will be made (not implemented yet)")
            logger.info("✅ FASE 1 Infrastructure setup completed - Ready for FASE 2")
            
    except Exception as e:
        logger.error(f"❌ Failed to initialize: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())