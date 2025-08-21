#!/bin/bash
# -*- coding: utf-8 -*-
#
# 🚀 Apply Intelligent Optimizations - Smart Code Optimization Application
#
# PURPOSE: Apply the 386+ refactoring recommendations detected by audit_intelligent.sh
# PHILOSOPHY: Safety first - backup, validate, rollback capability
#
# WORKFLOW:
# 1. Read audit results from .audit_intelligent/
# 2. Present optimization opportunities 
# 3. Apply selected optimizations with backup
# 4. Validate syntax and functionality
# 5. Provide rollback if needed
#
# SAFETY FEATURES:
# - Automatic backup before any changes
# - Dry-run mode by default
# - Selective application with user confirmation
# - Syntax validation after each change
# - Complete rollback capability

set -euo pipefail

# Color codes for better UX
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
AUDIT_DIR="${AUDIT_DIR:-.audit_intelligent}"
BACKUP_DIR="${BACKUP_DIR:-.optimization_backups}"
PROJECT_ROOT="${PROJECT_ROOT:-.}"
DRY_RUN=${DRY_RUN:-1}  # Default to dry-run for safety
VERBOSE=${VERBOSE:-0}
SELECTIVE=${SELECTIVE:-0}
FORCE_APPLY=${FORCE_APPLY:-0}

# Script metadata
SCRIPT_START_TIME=$(date +%Y%m%d_%H%M%S)
OPTIMIZATION_LOG="$BACKUP_DIR/optimization_log_$SCRIPT_START_TIME.txt"

# Ensure backup directory exists early
mkdir -p "$BACKUP_DIR"

# Usage information
usage() {
    cat << EOF
🚀 Apply Intelligent Optimizations - Smart Code Refactoring

USAGE: $0 [OPTIONS]

OPTIONS:
    --input DIR         Input directory with audit results (default: .audit_intelligent)
    --dry-run          Show what would be changed without applying (DEFAULT)
    --apply            Actually apply optimizations (overrides dry-run)
    --selective        Ask before applying each optimization
    --backup DIR       Backup directory (default: .optimization_backups)
    --force            Apply all optimizations without confirmation (DANGEROUS)
    --rollback ID      Rollback to specific backup ID
    --list-backups     List available backups
    --verbose          Enable verbose output
    -h, --help         Show this help

EXAMPLES:
    $0                                    # Dry-run mode (safe preview)
    $0 --dry-run                         # Explicit dry-run
    $0 --apply --selective               # Apply with confirmation
    $0 --apply --backup /safe/location   # Apply with custom backup location
    $0 --rollback 20250821_132845        # Rollback to specific backup

SAFETY FEATURES:
    • Automatic backup before any changes
    • Syntax validation after each optimization
    • Complete rollback capability
    • Dry-run by default for safety
    • Selective application with user control

EOF
}

# Logging functions
log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1" | tee -a "$OPTIMIZATION_LOG"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] WARNING:${NC} $1" | tee -a "$OPTIMIZATION_LOG"
}

log_error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] ERROR:${NC} $1" | tee -a "$OPTIMIZATION_LOG"
}

log_info() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')] INFO:${NC} $1" | tee -a "$OPTIMIZATION_LOG"
}

log_success() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] SUCCESS:${NC} $1" | tee -a "$OPTIMIZATION_LOG"
}

# Utility functions
check_dependencies() {
    log_info "🔍 Checking dependencies..."
    
    # Check if Python is available
    if ! command -v python3 >/dev/null 2>&1; then
        log_error "Python 3 is required but not installed"
        exit 1
    fi
    
    # Check if audit results exist
    if [[ ! -d "$AUDIT_DIR" ]]; then
        log_error "Audit directory '$AUDIT_DIR' not found"
        log_info "Please run ./audit_intelligent.sh first"
        exit 1
    fi
    
    # Check if audit results contain optimization data
    if [[ ! -f "$AUDIT_DIR/intelligent_analysis.json" ]]; then
        log_error "No audit results found in '$AUDIT_DIR'"
        log_info "Please run ./audit_intelligent.sh to generate optimization recommendations"
        exit 1
    fi
    
    log_success "✅ All dependencies satisfied"
}

create_backup_structure() {
    log_info "📁 Creating backup structure..."
    
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$BACKUP_DIR/files_$SCRIPT_START_TIME"
    mkdir -p "$BACKUP_DIR/metadata"
    
    # Create backup metadata
    cat > "$BACKUP_DIR/metadata/backup_$SCRIPT_START_TIME.json" << EOF
{
    "backup_id": "$SCRIPT_START_TIME",
    "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "audit_input": "$AUDIT_DIR",
    "project_root": "$PROJECT_ROOT",
    "script_version": "1.0.0",
    "files_backed_up": [],
    "optimizations_applied": []
}
EOF
    
    log_success "✅ Backup structure created: $BACKUP_DIR/files_$SCRIPT_START_TIME"
}

backup_file() {
    local file_path="$1"
    local backup_file_path="$BACKUP_DIR/files_$SCRIPT_START_TIME/$file_path"
    
    # Create directory structure in backup
    mkdir -p "$(dirname "$backup_file_path")"
    
    # Copy original file to backup
    cp "$file_path" "$backup_file_path"
    
    log_info "💾 Backed up: $file_path"
}

validate_syntax() {
    local file_path="$1"
    
    # Check Python syntax
    if [[ "$file_path" == *.py ]]; then
        if ! python3 -m py_compile "$file_path" 2>/dev/null; then
            log_error "❌ Syntax error in $file_path after optimization"
            return 1
        fi
    fi
    
    # Could add other file type validations here
    return 0
}

# Parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --input)
                AUDIT_DIR="$2"
                shift 2
                ;;
            --dry-run)
                DRY_RUN=1
                shift
                ;;
            --apply)
                DRY_RUN=0
                shift
                ;;
            --selective)
                SELECTIVE=1
                shift
                ;;
            --backup)
                BACKUP_DIR="$2"
                shift 2
                ;;
            --force)
                FORCE_APPLY=1
                SELECTIVE=0
                shift
                ;;
            --rollback)
                rollback_to_backup "$2"
                exit $?
                ;;
            --list-backups)
                list_backups
                exit 0
                ;;
            --verbose)
                VERBOSE=1
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done
}

# Backup and rollback functions
list_backups() {
    log_info "📋 Available backups:"
    
    if [[ ! -d "$BACKUP_DIR/metadata" ]]; then
        log_warning "No backups found in $BACKUP_DIR"
        return
    fi
    
    for backup_file in "$BACKUP_DIR"/metadata/backup_*.json; do
        if [[ -f "$backup_file" ]]; then
            local backup_id=$(basename "$backup_file" .json | sed 's/backup_//')
            local created_at=$(python3 -c "import json; print(json.load(open('$backup_file'))['created_at'])" 2>/dev/null || echo "unknown")
            echo "  📦 $backup_id (created: $created_at)"
        fi
    done
}

rollback_to_backup() {
    local backup_id="$1"
    local backup_metadata="$BACKUP_DIR/metadata/backup_$backup_id.json"
    
    if [[ ! -f "$backup_metadata" ]]; then
        log_error "Backup $backup_id not found"
        exit 1
    fi
    
    log_info "🔄 Rolling back to backup $backup_id..."
    
    # Read files that were backed up
    python3 - << EOF
import json
import shutil
import os

with open('$backup_metadata') as f:
    metadata = json.load(f)

backup_dir = '$BACKUP_DIR/files_$backup_id'
files_backed_up = metadata.get('files_backed_up', [])

for file_path in files_backed_up:
    backup_file_path = os.path.join(backup_dir, file_path)
    if os.path.exists(backup_file_path):
        # Create directory if needed (only if file is not in root)
        dirname = os.path.dirname(file_path)
        if dirname:  # Only create directory if dirname is not empty
            os.makedirs(dirname, exist_ok=True)
        # Restore file
        shutil.copy2(backup_file_path, file_path)
        print(f"✅ Restored: {file_path}")
    else:
        print(f"⚠️ Backup not found for: {file_path}")
EOF
    
    log_success "🔄 Rollback completed"
}

# Main optimization application logic
load_audit_results() {
    log_info "📊 Loading audit results from $AUDIT_DIR..."
    
    # Use Python to parse and summarize audit results
    python3 - << EOF
import json
import sys
from pathlib import Path

try:
    audit_file = Path('$AUDIT_DIR/intelligent_analysis.json')
    if not audit_file.exists():
        print("❌ No audit results found")
        sys.exit(1)
    
    with open(audit_file) as f:
        data = json.load(f)
    
    files_analyzed = data.get('files_analyzed', 0)
    successful_analyses = data.get('successful_analyses', 0)
    total_issues = data.get('total_issues_found', 0)
    total_recommendations = data.get('total_recommendations', 0)
    
    print(f"📊 Audit Summary:")
    print(f"   📁 Files analyzed: {files_analyzed}")
    print(f"   ✅ Successful analyses: {successful_analyses}")
    print(f"   🚨 Total issues found: {total_issues}")
    print(f"   🔧 Total recommendations: {total_recommendations}")
    print()
    
    if total_recommendations == 0:
        print("ℹ️ No optimization recommendations found")
        sys.exit(0)
    
    # Show top files with most recommendations
    results = data.get('results', [])
    top_files = sorted(results, key=lambda x: x.get('recommended_refactorings_count', 0), reverse=True)[:10]
    
    print("🎯 Top files for optimization:")
    for i, file_result in enumerate(top_files[:5], 1):
        file_path = file_result.get('file_path', 'unknown')
        refactorings = file_result.get('recommended_refactorings_count', 0)
        quality_score = file_result.get('semantic_quality_score', 0)
        print(f"   {i}. {file_path}: {refactorings} optimizations (quality: {quality_score:.1f})")
    
    print()

except Exception as e:
    print(f"❌ Error loading audit results: {e}")
    sys.exit(1)
EOF
}

apply_optimizations() {
    if [[ $DRY_RUN -eq 1 ]]; then
        log_info "🔍 DRY-RUN MODE: Showing what would be optimized..."
        show_optimization_preview
        return
    fi
    
    if [[ $FORCE_APPLY -eq 0 && $SELECTIVE -eq 0 ]]; then
        log_warning "⚠️ This will apply optimizations to your code files"
        echo -n "Are you sure you want to continue? (y/N): "
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            log_info "Operation cancelled by user"
            exit 0
        fi
    fi
    
    log_info "🚀 Applying intelligent optimizations..."
    
    # Set environment variables for Python script
    export SCRIPT_START_TIME
    export BACKUP_DIR
    
    # Apply optimizations using enhanced Python integration
    python3 - << 'EOF'
import json, sys, os, shutil
from pathlib import Path

# ---------- Helpers ----------
def load_json(p: Path):
    with p.open('r', encoding='utf-8') as f:
        return json.load(f)

def save_json(p: Path, data: dict):
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix('.tmp')
    with tmp.open('w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(p)

def ensure_backup(file_path: str, backup_root: Path, backup_id: str, metadata_path: Path):
    """Copia o arquivo para BACKUP_DIR/files_<ID>/<path_relativo> e
    atualiza o array files_backed_up no metadata."""
    src = Path(file_path)
    # Guard: só faz backup de arquivos que existem
    if not src.exists():
        return False

    rel = src.as_posix()
    # destino
    dest = backup_root / f"files_{backup_id}" / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)

    # atualizar metadata
    if not metadata_path.exists():
        save_json(metadata_path, {"files_backed_up": [], "created_at": backup_id})
    
    meta = load_json(metadata_path)
    files = set(meta.get("files_backed_up", []))
    if rel not in files:
        files.add(rel)
        meta["files_backed_up"] = sorted(files)
        save_json(metadata_path, meta)
    return True

def validate_python_syntax(file_path: str) -> bool:
    if not file_path.endswith(".py"):
        return True
    import py_compile
    try:
        py_compile.compile(file_path, doraise=True)
        return True
    except Exception:
        return False

# ---------- Config/env ----------
audit_dir = Path(os.environ.get('AUDIT_DIR', '.audit_intelligent'))
selective = int(os.environ.get('SELECTIVE', '0'))

backup_dir = Path(os.environ.get('BACKUP_DIR', '.optimization_backups'))
backup_id  = os.environ.get('SCRIPT_START_TIME')  # passada do Bash via env
metadata_path = backup_dir / "metadata" / f"backup_{backup_id}.json"

# ---------- Imports do agente ----------
sys.path.append('.')
try:
    from audit_system.agents.intelligent_code_agent import IntelligentCodeAgent, AnalysisDepth, SemanticMode
except Exception as e:
    print(f"❌ Error importing optimization agents: {e}")
    print("📋 Make sure the audit system is properly installed (PYTHONPATH).")
    sys.exit(1)

# ---------- Carrega resultados ----------
try:
    data = load_json(audit_dir / 'intelligent_analysis.json')
except Exception as e:
    print(f"❌ Error loading audit results: {e}")
    sys.exit(1)

results = data.get('results', [])
targets = [r for r in results if r.get('recommended_refactorings_count', 0) > 0]
if not targets:
    print("ℹ️ No files with optimization recommendations found")
    sys.exit(0)

print(f"🔧 Found {len(targets)} files with optimization opportunities")

# Single agent instance (optimization)
code_agent = IntelligentCodeAgent(
    project_root=Path('.'),
    enable_real_llm=True,
    analysis_depth=AnalysisDepth.DEEP,
    semantic_mode=SemanticMode.AGGRESSIVE,
    dry_run=False
)

total_applied = 0
total_files_modified = 0
failed_files = []

for fr in targets:
    file_path = fr['file_path']
    count = fr['recommended_refactorings_count']
    qscore = fr.get('semantic_quality_score', 0)
    print(f"\n📝 Processing: {file_path}")
    print(f"   🔧 {count} optimizations available")
    print(f"   📊 Current quality score: {qscore:.1f}")

    if selective:
        try:
            resp = input(f"   Apply optimizations to {file_path}? (y/N/q): ").strip().lower()
        except EOFError:
            resp = 'n'
        if resp == 'q':
            print("🛑 Optimization process stopped by user")
            break
        if resp != 'y':
            print("   ⏭️ Skipped")
            continue

    try:
        analysis = code_agent.analyze_file_intelligently(file_path)

        if not getattr(analysis, "recommended_refactorings", None):
            print("   ℹ️ No current optimization recommendations")
            continue

        # 1) BACKUP antes de mexer
        backed_up = ensure_backup(file_path, backup_dir, backup_id, metadata_path)
        if not backed_up:
            print("   ⚠️ File not found for backup; skipping.")
            continue

        # 2) Aplica refatorações
        result = code_agent.apply_intelligent_refactorings(
            analysis=analysis,
            selected_refactorings=None
        )
        applied = int(result.get('applied', 0))
        failed  = int(result.get('failed', 0))

        # 3) Valida sintaxe (.py) — rollback se falhar
        if not validate_python_syntax(file_path):
            # rollback do arquivo
            src_backup = backup_dir / f"files_{backup_id}" / Path(file_path).as_posix()
            if src_backup.exists():
                shutil.copy2(src_backup, file_path)
            print(f"   ❌ Syntax error after changes — rolled back {file_path}")
            failed_files.append(file_path)
            continue

        if applied > 0:
            total_applied += applied
            total_files_modified += 1
            msg = f"   ✅ Applied {applied} optimizations successfully"
            if failed > 0:
                msg += f" (⚠️ {failed} failed)"
            print(msg)
        else:
            status = result.get('status', 'unknown')
            if status == 'completed':
                print("   ℹ️ No optimizations to apply (already optimized)")
            else:
                print(f"   ℹ️ No optimizations applied (status: {status})")

    except Exception as e:
        failed_files.append(file_path)
        print(f"   ❌ Error optimizing {file_path}: {e}")

print(f"\n🎉 Optimization Summary:")
print(f"   📁 Files modified: {total_files_modified}")
print(f"   🔧 Total optimizations applied: {total_applied}")
if failed_files:
    print(f"   ❗ Files with errors (kept/rolled back): {len(failed_files)}")
EOF
}

show_optimization_preview() {
    log_info "🔍 Optimization Preview (Dry-Run Mode):"
    
    python3 - << 'EOF'
import json
import sys
import os
from pathlib import Path

try:
    audit_dir = Path(os.environ.get('AUDIT_DIR', '.audit_intelligent'))
    
    # Load audit results
    with open(audit_dir / 'intelligent_analysis.json') as f:
        audit_data = json.load(f)
    
    results = audit_data.get('results', [])
    files_with_optimizations = [r for r in results if r.get('recommended_refactorings_count', 0) > 0]
    
    if not files_with_optimizations:
        print("ℹ️ No optimization opportunities found")
        sys.exit(0)
    
    print(f"\n📊 Preview of {len(files_with_optimizations)} files with optimization opportunities:")
    print("=" * 80)
    
    total_optimizations = 0
    for i, file_result in enumerate(files_with_optimizations, 1):
        file_path = file_result['file_path']
        refactoring_count = file_result['recommended_refactorings_count']
        quality_score = file_result.get('semantic_quality_score', 0)
        security_issues = file_result.get('security_vulnerabilities_count', 0)
        performance_issues = file_result.get('performance_bottlenecks_count', 0)
        
        total_optimizations += refactoring_count
        
        print(f"\n{i:2d}. 📁 {file_path}")
        print(f"    🔧 {refactoring_count} refactoring recommendations")
        print(f"    📊 Quality score: {quality_score:.1f}/100")
        if security_issues > 0:
            print(f"    🚨 Security issues: {security_issues}")
        if performance_issues > 0:
            print(f"    ⚡ Performance bottlenecks: {performance_issues}")
    
    print("=" * 80)
    print(f"📈 TOTAL OPTIMIZATIONS AVAILABLE: {total_optimizations}")
    print()
    print("🚀 To apply these optimizations:")
    print("   ./apply_intelligent_optimizations.sh --apply --selective")
    print("   ./apply_intelligent_optimizations.sh --apply --backup /safe/location")
    print()

except Exception as e:
    print(f"❌ Error generating preview: {e}")
    sys.exit(1)
EOF
}

# Main execution
main() {
    echo "🚀 Apply Intelligent Optimizations - Smart Code Refactoring"
    echo "📅 Started at: $(date)"
    echo "🔧 Script version: 1.0.0"
    echo

    # Parse command line arguments
    parse_arguments "$@"
    
    # Check system requirements
    check_dependencies
    
    # Create backup structure (even for dry-run to log operations)
    create_backup_structure
    
    # Load and summarize audit results
    load_audit_results
    
    # Apply optimizations (or show preview)
    apply_optimizations
    
    if [[ $DRY_RUN -eq 0 ]]; then
        log_success "🎉 Optimization process completed!"
        log_info "📋 Log file: $OPTIMIZATION_LOG"
        log_info "💾 Backup location: $BACKUP_DIR/files_$SCRIPT_START_TIME"
        echo
        echo "🔄 If you need to rollback:"
        echo "   ./apply_intelligent_optimizations.sh --rollback $SCRIPT_START_TIME"
    else
        log_info "🔍 Dry-run completed - no files were modified"
        echo
        echo "🚀 To apply optimizations:"
        echo "   ./apply_intelligent_optimizations.sh --apply"
    fi
}

# Execute main function with all arguments
main "$@"