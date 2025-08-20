#!/bin/bash
# 🚨 EMERGENCY RESTORE SCRIPT - CONTEXT EXTRACTION BACKUP
# Created: 2025-08-19 21:29:49
# Purpose: Restore system to golden state before context extraction modifications

echo "🚨 EMERGENCY RESTORE - CONTEXT EXTRACTION BACKUP"
echo "================================================"

BACKUP_DIR="context_extraction_20250819_212949"
RESTORE_TIMESTAMP=$(date '+%Y%m%d_%H%M%S')

echo "📅 Restore initiated at: $RESTORE_TIMESTAMP"
echo "🗂️ Using backup: $BACKUP_DIR"

# Verify backup exists
if [ ! -d "backups/$BACKUP_DIR" ]; then
    echo "❌ ERROR: Backup directory not found!"
    echo "   Expected: backups/$BACKUP_DIR"
    exit 1
fi

# Create restore log
echo "📝 Creating restore log..."
mkdir -p "backups/restore_logs"
RESTORE_LOG="backups/restore_logs/restore_$RESTORE_TIMESTAMP.log"

# Function to restore file with logging
restore_file() {
    local backup_file="$1"
    local target_file="$2"
    
    if [ -f "backups/$BACKUP_DIR/$backup_file" ]; then
        echo "🔄 Restoring: $target_file"
        cp "backups/$BACKUP_DIR/$backup_file" "$target_file"
        echo "✅ Restored: $target_file" >> "$RESTORE_LOG"
    else
        echo "⚠️ Warning: Backup file not found: $backup_file"
        echo "⚠️ Warning: Backup file not found: $backup_file" >> "$RESTORE_LOG"
    fi
}

echo "🔄 Starting restore process..."

# Restore root critical files
echo "📁 Restoring root critical files..."
restore_file "CLAUDE.md" "CLAUDE.md"
restore_file "INDEX.md" "INDEX.md" 
restore_file "NAVIGATION.md" "NAVIGATION.md"

# Restore module CLAUDE.md files
echo "📁 Restoring module CLAUDE.md files..."
restore_file "CLAUDE_migration.md" "migration/CLAUDE.md"
restore_file "CLAUDE_monitoring.md" "monitoring/CLAUDE.md"
restore_file "CLAUDE_scripts.md" "scripts/CLAUDE.md"
restore_file "CLAUDE_config.md" "config/CLAUDE.md"
restore_file "CLAUDE_tests.md" "tests/CLAUDE.md"

# Restore streamlit_extension CLAUDE.md files
echo "📁 Restoring streamlit_extension CLAUDE.md files..."
restore_file "CLAUDE_streamlit_database.md" "streamlit_extension/database/CLAUDE.md"
restore_file "CLAUDE_streamlit_services.md" "streamlit_extension/services/CLAUDE.md"
restore_file "CLAUDE_streamlit_components.md" "streamlit_extension/components/CLAUDE.md"
restore_file "CLAUDE_streamlit_main.md" "streamlit_extension/CLAUDE.md"
restore_file "CLAUDE_streamlit_auth.md" "streamlit_extension/auth/CLAUDE.md"

# Restore critical scripts
echo "📁 Restoring critical scripts..."
restore_file "systematic_file_auditor.py" "scripts/automated_audit/systematic_file_auditor.py"

# Restore consultation docs
echo "📁 Restoring consultation docs..."
restore_file "PROJECT_MISSION.md" "scripts/automated_audit/PROJECT_MISSION.md"
restore_file "TDD_WORKFLOW_PATTERNS.md" "scripts/automated_audit/TDD_WORKFLOW_PATTERNS.md"
restore_file "TDAH_OPTIMIZATION_GUIDE.md" "scripts/automated_audit/TDAH_OPTIMIZATION_GUIDE.md"

echo ""
echo "✅ RESTORE PROCESS COMPLETED"
echo "================================================"
echo "📊 Restore Summary:"
echo "   - Timestamp: $RESTORE_TIMESTAMP"
echo "   - Backup Used: $BACKUP_DIR"
echo "   - Log File: $RESTORE_LOG"
echo ""
echo "🎯 Next Steps:"
echo "   1. Verify system functionality"
echo "   2. Run: python scripts/testing/comprehensive_integrity_test.py"
echo "   3. Check: all critical files restored correctly"
echo ""
echo "⚠️ NOTE: This restore overwrites current files with backup versions."
echo "   Any changes made after backup creation will be lost."
echo ""
echo "🔄 System restored to golden state: 2025-08-19 21:29:49"