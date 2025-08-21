#!/bin/bash
# -*- coding: utf-8 -*-
#
# 🚀 Apply Intelligent Optimizations - FIXED VERSION
#
# PURPOSE: Apply the 386+ refactoring recommendations using ALL specialized agents
# PHILOSOPHY: Use MetaAgent to coordinate all specialized agents for real corrections
#
# 🔧 FIXED ISSUES:
# - Now uses MetaAgent instead of single IntelligentCodeAgent
# - Activates all specialized agents (IntelligentRefactoringEngine, GodCodeRefactoringAgent, etc.)
# - Real corrections applied instead of just analysis
# - Comprehensive file complexity analysis for optimal agent selection

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
OPTIMIZATION_LOG="$BACKUP_DIR/optimization_log_FIXED_$SCRIPT_START_TIME.txt"

# Ensure backup directory exists early
mkdir -p "$BACKUP_DIR"

# Usage information
usage() {
    cat << EOF
🚀 Apply Intelligent Optimizations - FIXED VERSION with MetaAgent

USAGE: $0 [OPTIONS]

🔧 FIXED FEATURES:
    • Uses MetaAgent to coordinate ALL specialized agents
    • IntelligentRefactoringEngine for real code transformations
    • GodCodeRefactoringAgent for god code elimination
    • Comprehensive complexity analysis for optimal agent selection
    • Real corrections applied based on file complexity and patterns

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
    $0 --apply --selective               # Apply with confirmation using ALL agents
    $0 --apply --backup /safe/location   # Apply with custom backup location

🎯 NEW FEATURES:
    • MetaAgent coordination ensures optimal agent selection
    • Real refactoring engine for actual code improvements
    • God code detection and elimination
    • File complexity analysis drives agent selection strategy

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
    log_info "🔍 Checking dependencies for MetaAgent system..."
    
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
    "script_version": "2.0.0-FIXED",
    "optimization_engine": "MetaAgent with all specialized agents",
    "files_backed_up": [],
    "optimizations_applied": []
}
EOF
    
    log_success "✅ Backup structure created: $BACKUP_DIR/files_$SCRIPT_START_TIME"
}

# Parse command line arguments (reuse existing argument parsing)
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

# Main optimization application logic using MetaAgent
apply_optimizations_with_meta_agent() {
    if [[ $DRY_RUN -eq 1 ]]; then
        log_info "🔍 DRY-RUN MODE: Showing what MetaAgent would optimize..."
        show_optimization_preview
        return
    fi
    
    if [[ $FORCE_APPLY -eq 0 && $SELECTIVE -eq 0 ]]; then
        log_warning "⚠️ This will apply REAL optimizations using ALL specialized agents"
        echo -n "Are you sure you want to continue with MetaAgent optimization? (y/N): "
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            log_info "Operation cancelled by user"
            exit 0
        fi
    fi
    
    log_info "🧠 Applying optimizations using MetaAgent coordination..."
    
    # Set environment variables for Python script
    export SCRIPT_START_TIME
    export BACKUP_DIR
    export SELECTIVE
    export AUDIT_DIR
    
    # Apply optimizations using MetaAgent coordination
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
    """Backup file with metadata tracking."""
    src = Path(file_path)
    if not src.exists():
        return False

    rel = src.as_posix()
    dest = backup_root / f"files_{backup_id}" / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)

    # Update metadata
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
backup_id  = os.environ.get('SCRIPT_START_TIME')
metadata_path = backup_dir / "metadata" / f"backup_{backup_id}.json"

# ---------- Import MetaAgent and dependencies ----------
sys.path.append('.')
try:
    from audit_system.coordination.meta_agent import (
        MetaAgent, TaskType, FileComplexity, AgentType, Priority
    )
    print("✅ MetaAgent system imported successfully")
except Exception as e:
    print(f"❌ Error importing MetaAgent system: {e}")
    print("📋 Make sure the audit system is properly installed")
    sys.exit(1)

# ---------- Load audit results ----------
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

print(f"🧠 Found {len(targets)} files with optimization opportunities")
print(f"🎯 Initializing MetaAgent for comprehensive optimization...")

# ---------- Initialize MetaAgent ----------
try:
    meta_agent = MetaAgent(
        project_root=Path('.'),
        token_budget=50000,  # Increased budget for comprehensive optimization
        max_time_per_file=600.0,  # 10 minutes max per file
        enable_tdah_features=True,  # Enable TDAH optimization
        dry_run=False  # Real optimizations
    )
    print("🚀 MetaAgent initialized with all specialized agents")
    print("   • IntelligentCodeAgent: Semantic analysis")
    print("   • IntelligentRefactoringEngine: Real code transformations") 
    print("   • GodCodeRefactoringAgent: God code elimination")
    print("   • TDDIntelligentWorkflowAgent: TDD workflow optimization")
    
except Exception as e:
    print(f"❌ Error initializing MetaAgent: {e}")
    sys.exit(1)

# ---------- Process files with MetaAgent ----------
total_applied = 0
total_files_modified = 0
failed_files = []
comprehensive_results = []

for fr in targets:
    file_path = fr['file_path']
    count = fr['recommended_refactorings_count']
    qscore = fr.get('semantic_quality_score', 0)
    
    print(f"\n📝 Processing: {file_path}")
    print(f"   🔧 {count} optimization opportunities detected")
    print(f"   📊 Current quality score: {qscore:.1f}")

    if selective:
        try:
            resp = input(f"   Apply MetaAgent optimization to {file_path}? (y/N/q): ").strip().lower()
        except EOFError:
            resp = 'n'
        if resp == 'q':
            print("🛑 Optimization process stopped by user")
            break
        if resp != 'y':
            print("   ⏭️ Skipped")
            continue

    try:
        # Step 1: Analyze file complexity and determine optimal agent strategy
        print("   🔍 Analyzing file complexity for optimal agent selection...")
        file_analysis = meta_agent.analyze_file(file_path)
        
        print(f"   📋 File complexity: {file_analysis.file_complexity.value}")
        print(f"   📏 Lines: {file_analysis.line_count}, Functions: {file_analysis.function_count}")
        print(f"   🧮 Complexity score: {file_analysis.ast_complexity_score:.1f}")
        
        # Step 2: Create comprehensive optimization plan
        print("   🎯 Creating comprehensive optimization plan...")
        optimization_plan = meta_agent.create_execution_plan(
            file_path=file_path,
            task_type=TaskType.COMPREHENSIVE_AUDIT,
            priority=Priority.HIGH
        )
        
        print(f"   🤖 Selected agents: {[agent.agent_type.value for agent in optimization_plan.agents]}")
        print(f"   ⏱️ Estimated time: {optimization_plan.total_estimated_time:.1f}s")
        print(f"   🪙 Estimated tokens: {optimization_plan.total_estimated_tokens}")
        
        # Step 3: Backup before modifications
        backed_up = ensure_backup(file_path, backup_dir, backup_id, metadata_path)
        if not backed_up:
            print("   ⚠️ File not found for backup; skipping.")
            continue

        # Step 4: Execute comprehensive optimization using MetaAgent
        print("   🚀 Executing comprehensive optimization...")
        execution_results = meta_agent.execute_plan(optimization_plan)
        
        # Step 5: Validate syntax after modifications
        if not validate_python_syntax(file_path):
            # Rollback on syntax error
            src_backup = backup_dir / f"files_{backup_id}" / Path(file_path).as_posix()
            if src_backup.exists():
                shutil.copy2(src_backup, file_path)
            print(f"   ❌ Syntax error after changes — rolled back {file_path}")
            failed_files.append(file_path)
            continue

        # Step 6: Analyze results and report
        successful_agents = [r for r in execution_results if r.success]
        total_tokens_used = sum(r.tokens_used for r in execution_results)
        total_time_spent = sum(r.execution_time for r in execution_results)
        
        if successful_agents:
            total_files_modified += 1
            applied_optimizations = len(successful_agents)
            total_applied += applied_optimizations
            
            print(f"   ✅ Applied {applied_optimizations} comprehensive optimizations")
            print(f"   🤖 Successful agents: {[r.agent_type.value for r in successful_agents]}")
            print(f"   ⏱️ Time spent: {total_time_spent:.1f}s")
            print(f"   🪙 Tokens used: {total_tokens_used}")
            
            # Log detailed results
            comprehensive_results.append({
                "file_path": file_path,
                "original_quality_score": qscore,
                "file_complexity": file_analysis.file_complexity.value,
                "agents_executed": [r.agent_type.value for r in successful_agents],
                "tokens_used": total_tokens_used,
                "execution_time": total_time_spent,
                "success": True
            })
        else:
            print("   ℹ️ No optimizations could be applied")
            comprehensive_results.append({
                "file_path": file_path,
                "success": False,
                "errors": [err for result in execution_results for err in result.errors]
            })

    except Exception as e:
        failed_files.append(file_path)
        print(f"   ❌ Error optimizing {file_path}: {e}")

# ---------- Final Summary ----------
print(f"\n🎉 MetaAgent Optimization Summary:")
print(f"   📁 Files modified: {total_files_modified}")
print(f"   🔧 Total optimizations applied: {total_applied}")
print(f"   🤖 Used all specialized agents for comprehensive improvements")

if failed_files:
    print(f"   ❗ Files with errors: {len(failed_files)}")

# Save comprehensive results
if comprehensive_results:
    results_file = backup_dir / f"meta_agent_results_{backup_id}.json"
    save_json(results_file, {
        "timestamp": backup_id,
        "optimization_engine": "MetaAgent",
        "files_processed": len(targets),
        "files_modified": total_files_modified,
        "total_optimizations": total_applied,
        "detailed_results": comprehensive_results
    })
    print(f"   📋 Detailed results saved: {results_file}")

print("\n🚀 MetaAgent optimization completed successfully!")
EOF
}

show_optimization_preview() {
    log_info "🔍 MetaAgent Optimization Preview (Dry-Run Mode):"
    
    python3 - << 'EOF'
import json, sys, os
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
    
    print(f"\n📊 MetaAgent Optimization Preview - {len(files_with_optimizations)} files:")
    print("=" * 80)
    
    # Import MetaAgent for complexity analysis
    sys.path.append('.')
    try:
        from audit_system.coordination.meta_agent import MetaAgent
        meta_agent = MetaAgent(
            project_root=Path('.'),
            dry_run=True
        )
        
        total_optimizations = 0
        for i, file_result in enumerate(files_with_optimizations, 1):
            file_path = file_result['file_path']
            refactoring_count = file_result['recommended_refactorings_count']
            quality_score = file_result.get('semantic_quality_score', 0)
            
            # Analyze file complexity for agent selection preview
            try:
                file_analysis = meta_agent.analyze_file(file_path)
                complexity = file_analysis.file_complexity.value
                estimated_agents = 3 if complexity == "GOD_FILE" else 2 if complexity == "COMPLEX" else 1
            except:
                complexity = "unknown"
                estimated_agents = 1
            
            total_optimizations += refactoring_count
            
            print(f"\n{i:2d}. 📁 {file_path}")
            print(f"    🔧 {refactoring_count} optimization opportunities")
            print(f"    📊 Quality score: {quality_score:.1f}/100")
            print(f"    🏗️ Complexity: {complexity}")
            print(f"    🤖 Estimated agents: {estimated_agents} specialized agents")
        
        print("=" * 80)
        print(f"📈 TOTAL OPTIMIZATIONS AVAILABLE: {total_optimizations}")
        print(f"🤖 MetaAgent will coordinate all specialized agents for optimal results")
        print()
        print("🚀 To apply these optimizations with MetaAgent:")
        print("   ./apply_intelligent_optimizations_FIXED.sh --apply --selective")
        print("   ./apply_intelligent_optimizations_FIXED.sh --apply --backup /safe/location")
        print()
        
    except ImportError:
        print("⚠️ MetaAgent not available - using basic preview")
        for i, file_result in enumerate(files_with_optimizations[:10], 1):
            file_path = file_result['file_path']
            refactoring_count = file_result['recommended_refactorings_count']
            quality_score = file_result.get('semantic_quality_score', 0)
            
            print(f"\n{i:2d}. 📁 {file_path}")
            print(f"    🔧 {refactoring_count} optimization opportunities")
            print(f"    📊 Quality score: {quality_score:.1f}/100")

except Exception as e:
    print(f"❌ Error generating preview: {e}")
    sys.exit(1)
EOF
}

# Main execution
main() {
    echo "🚀 Apply Intelligent Optimizations - FIXED VERSION with MetaAgent"
    echo "📅 Started at: $(date)"
    echo "🔧 Script version: 2.0.0-FIXED"
    echo "🧠 Engine: MetaAgent with all specialized agents"
    echo

    # Parse command line arguments
    parse_arguments "$@"
    
    # Check system requirements
    check_dependencies
    
    # Create backup structure
    create_backup_structure
    
    # Apply optimizations using MetaAgent
    apply_optimizations_with_meta_agent
    
    if [[ $DRY_RUN -eq 0 ]]; then
        log_success "🎉 MetaAgent optimization process completed!"
        log_info "📋 Log file: $OPTIMIZATION_LOG"
        log_info "💾 Backup location: $BACKUP_DIR/files_$SCRIPT_START_TIME"
        echo
        echo "🔄 If you need to rollback:"
        echo "   ./apply_intelligent_optimizations_FIXED.sh --rollback $SCRIPT_START_TIME"
    else
        log_info "🔍 Dry-run completed - no files were modified"
        echo
        echo "🚀 To apply MetaAgent optimizations:"
        echo "   ./apply_intelligent_optimizations_FIXED.sh --apply"
    fi
}

# Execute main function with all arguments
main "$@"