#!/usr/bin/env bash
# audit.sh — Auditoria completa e otimizações opcionais do TDD Framework

# =======================
# Fail-fast + diagnósticos
# =======================
set -Eeuo pipefail

# Mensagem de erro padronizada com linha/comando
trap 'rc=$?; echo -e "\033[0;31m[erro]\033[0m Falha na linha $LINENO: comando '\''$BASH_COMMAND'\'' (exit $rc)"; exit $rc' ERR

# =======================
# Cores (com fallback se não for TTY)
# =======================
if [[ -t 1 ]]; then
  BOLD='\033[1m'; BLUE='\033[1;34m'; CYAN='\033[0;36m'; YELLOW='\033[0;33m'; GREEN='\033[0;32m'; RED='\033[0;31m'; RESET='\033[0m'
else
  BOLD=''; BLUE=''; CYAN=''; YELLOW=''; GREEN=''; RED=''; RESET=''
fi

# =======================
# Configuração e opções
# =======================
FAST=0
FIX=1

usage() {
  cat <<'EOF'
Uso: ./audit.sh [opções]

  --fast     Executa auditoria mais rápida (pula testes pesados e parte das análises)
  --no-fix   Não executa etapa de otimização/correções (apenas análise/validação)
  --help     Mostra esta ajuda

Pastas auditadas (principais):
  streamlit_extension/  duration_system/  migration/  scripts/
  tests/  monitoring/  docs/  epics/  tdah_tools/

Saídas:
  - Relatórios resumidos em ./.audit_reports/
  - Sumário final no console
EOF
}

die() { echo -e "${RED}Erro:${RESET} $*" >&2; exit 1; }

# -----------------------
# Parse de argumentos
# -----------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --fast)   FAST=1; shift ;;
    --no-fix) FIX=0;  shift ;;
    --help)   usage; exit 0 ;;
    *)        die "opção desconhecida: $1" ;;
  esac
done

# =======================
# Utilitários de saída
# =======================
SECTION() { printf "\n${BLUE}==> %s${RESET}\n" "$*"; }
NOTE()    { printf "${CYAN}[info]${RESET} %s\n" "$*"; }
WARN()    { printf "${YELLOW}[aviso]${RESET} %s\n" "$*"; }
OK()      { printf "${GREEN}[ok]${RESET} %s\n" "$*"; }

RUN() {
  local desc="$1"; shift
  NOTE "$desc"
  if "$@"; then OK "$desc concluído"; else return 1; fi
}

# =======================
# Ambiente / ferramentas
# =======================
mkdir -p .audit_reports

SECTION "Pré‑checagens de ambiente"

# Descobrir Python preferindo python3
PY="$(command -v python3 || true)"
if [[ -z "${PY}" ]]; then
  PY="$(command -v python || true)"
fi
[[ -n "${PY}" ]] || die "Python não encontrado (python3/python)"

command -v bash   >/dev/null 2>&1 || die "Bash não encontrado"

if ! command -v pytest >/dev/null 2>&1; then
  WARN "pytest não encontrado — testes serão limitados"
fi

# PYTHONPATH para imports relativos da app
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)"
OK "PYTHONPATH configurado: $PYTHONPATH"
OK "Usando interpretador: $(${PY} -V 2>&1)"

# =======================
# Diretórios alvo
# =======================
TARGET_DIRS=(
  "streamlit_extension"
  "duration_system"
  "migration"
  "scripts"
  "tests"
  "monitoring"
  "docs"
  "epics"
  "tdah_tools"
)

SECTION "Inventário básico de arquivos"
{
  echo "# Inventário ($(date))"
  for d in "${TARGET_DIRS[@]}"; do
    if [[ -d "$d" ]]; then
      echo "## $d"
      # Lista arquivos relevantes ordenados
      find "$d" -type f \( -name "*.py" -o -name "*.md" -o -name "*.sql" -o -name "*.yml" -o -name "*.yaml" -o -name "*.toml" \) | sort
      echo
    fi
  done
} > .audit_reports/inventario.txt
OK "Inventário salvo em .audit_reports/inventario.txt"

# =======================
# Validação de sintaxe Python
# =======================
SECTION "Validação de sintaxe (python -m py_compile)"
: > .audit_reports/py_compile_errors.log || true
: > .audit_reports/py_compile_failed.txt || true

PY_ERRORS=0
# find + -print0 para lidar com espaços/NUL-safe
while IFS= read -r -d '' f; do
  if ! "${PY}" -m py_compile "$f" 2>> .audit_reports/py_compile_errors.log; then
    echo "$f" >> .audit_reports/py_compile_failed.txt
    ((PY_ERRORS++)) || true
  fi
done < <(find "${TARGET_DIRS[@]}" -type f -name "*.py" -print0)

if (( PY_ERRORS > 0 )); then
  WARN "Arquivos Python com erro de sintaxe: $PY_ERRORS (veja .audit_reports/py_compile_errors.log)"
else
  OK "Sem erros de sintaxe Python"
fi

# =======================
# Análises específicas do projeto (scripts/analysis)
# =======================
SECTION "Análises do projeto (scripts/analysis)"

run_analysis() {
  local script="$1"; shift || true
  if [[ -f "scripts/analysis/$script" ]]; then
    RUN "Executando $script" "${PY}" "scripts/analysis/$script" "$@" \
      > ".audit_reports/${script%.py}.out" 2>&1 || WARN "$script retornou código != 0"
  else
    NOTE "Pulado: scripts/analysis/$script não encontrado"
  fi
}

# Seleção de análises (reduzidas em --fast)
run_analysis "analysis_type_hints.py"
run_analysis "audit_gap_analysis.py"
run_analysis "map_epic_task_hierarchy.py"

if (( FAST == 0 )); then
  run_analysis "identify_invalid_data.py"
  run_analysis "compare_structures.py"
fi

# =======================
# Saúde e manutenção do banco
# =======================
SECTION "Saúde e manutenção do banco"
if [[ -f "scripts/maintenance/database_maintenance.py" ]]; then
  RUN "Health check do banco" "${PY}" scripts/maintenance/database_maintenance.py health \
    > .audit_reports/db_health.out 2>&1 || WARN "health retornou != 0"
  if (( FIX == 1 )); then
    RUN "Backup do banco"       "${PY}" scripts/maintenance/database_maintenance.py backup \
      > .audit_reports/db_backup.out 2>&1 || WARN "backup retornou != 0"
    RUN "Otimização do banco"   "${PY}" scripts/maintenance/database_maintenance.py optimize \
      > .audit_reports/db_optimize.out 2>&1 || WARN "optimize retornou != 0"
  else
    NOTE "Etapa de fix/otimização desabilitada por --no-fix"
  fi
else
  WARN "scripts/maintenance/database_maintenance.py não encontrado; pulando etapa do banco"
fi

# =======================
# Testes
# =======================
SECTION "Execução de testes (pytest)"
if command -v pytest >/dev/null 2>&1 && [[ -d tests ]]; then
  if (( FAST == 1 )); then
    NOTE "Modo --fast: executando smoke tests essenciais"
    RUN "Smoke: duração"    "${PY}" -m pytest tests/test_duration_calculator.py -q \
      > .audit_reports/tests_smoke.out 2>&1 || true
    RUN "Smoke: segurança"  "${PY}" -m pytest 'tests/test_*security*.py' -q \
      >> .audit_reports/tests_smoke.out 2>&1 || true
  else
    RUN "Suite completa" "${PY}" -m pytest tests/ --tb=short \
      > .audit_reports/tests_full.out 2>&1 || true
  fi
else
  WARN "pytest ausente ou diretório tests/ não encontrado — pulando testes"
fi

# =======================
# ANÁLISE INTELIGENTE MULTI-AGENT
# =======================
SECTION "Análise Inteligente com Sistema Multi-Agent"

if [[ -f "audit_system/cli/run_meta_agent.py" ]]; then
  NOTE "Sistema Multi-Agent detectado - iniciando análises avançadas"

  run_agent_analysis() {
    local file="$1"
    local task="$2"
    local output="$3"
    local extra_args="${4:-}"

    if [[ $FIX -eq 1 ]]; then
      extra_args="$extra_args --apply"
    fi

    "${PY}" audit_system/cli/run_meta_agent.py \
      --file "$file" \
      --task "$task" \
      $extra_args \
      > "$output" 2>&1
  }

  # 1. Segurança (apenas no modo completo)
  if (( FAST == 0 )); then
    NOTE "Executando análise de segurança em arquivos críticos"
    CRITICAL_FILES=(
      "streamlit_extension/auth/user_model.py"
      "streamlit_extension/middleware/rate_limiting/core.py"
      "streamlit_extension/database/connection.py"
    )
    for file in "${CRITICAL_FILES[@]}"; do
      if [[ -f "$file" ]]; then
        run_agent_analysis "$file" "security_analysis" \
          ".audit_reports/security_$(basename "$file" .py).out" "" &
      fi
    done
    wait || true
    OK "Análise de segurança concluída"
  fi

  # 2. God codes
  NOTE "Detectando god codes e complexidade excessiva"
  GOD_CODE_TARGETS=(
    "streamlit_extension/utils/database.py"
    "streamlit_extension/services/analytics_service.py"
    "streamlit_extension/streamlit_app.py"
  )
  for file in "${GOD_CODE_TARGETS[@]}"; do
    if [[ -f "$file" ]]; then
      run_agent_analysis "$file" "code_refactoring" \
        ".audit_reports/god_code_$(basename "$file" .py).out" ""
    fi
  done

  # 3. Performance (modo completo)
  if (( FAST == 0 )); then
    NOTE "Analisando performance de serviços críticos"
    PERFORMANCE_TARGETS=(
      "streamlit_extension/services/analytics_service.py"
      "streamlit_extension/services/client_service.py"
      "streamlit_extension/services/timer_service.py"
    )
    for file in "${PERFORMANCE_TARGETS[@]}"; do
      if [[ -f "$file" ]]; then
        run_agent_analysis "$file" "performance_analysis" \
          ".audit_reports/performance_$(basename "$file" .py).out" ""
      fi
    done
  fi

  # 4. Arquitetura
  NOTE "Verificando arquitetura e padrões de design"
  if [[ -f "streamlit_extension/components/form_components.py" ]]; then
    run_agent_analysis "streamlit_extension/components/form_components.py" \
      "architecture_review" \
      ".audit_reports/architecture_review.out" ""
  fi

  # 5. TDD workflow (se há testes)
  if [[ -d "tests" ]] && (( FAST == 0 )); then
    NOTE "Analisando workflow TDD e cobertura"
    if [[ -f "tests/test_timer_service.py" ]]; then
      run_agent_analysis "tests/test_timer_service.py" \
        "tdd_optimization" \
        ".audit_reports/tdd_workflow.out" ""
    fi
  fi

  OK "Análises Multi-Agent concluídas"
else
  WARN "Sistema Multi-Agent não encontrado em audit_system/"
  WARN "Execute primeiro: python audit_system/coordination/meta_agent.py --setup"
fi

# =======================
# Coleta de logs
# =======================
SECTION "Coleta e resumo de logs"
LOG_BUNDLES=( "logs" "demo_logs" )
for L in "${LOG_BUNDLES[@]}"; do
  if [[ -d "$L" ]]; then
    tar -czf ".audit_reports/${L}.tar.gz" "$L" || WARN "Falha ao compactar $L"
  fi
done

# =======================
# Reparos/otimizações opcionais
# =======================
if (( FIX == 1 )); then
  SECTION "Otimizações e limpeza (fix phase)"
  if [[ -f "cleanup_cache.py" ]]; then
    RUN "Cleanup de cache" "${PY}" cleanup_cache.py \
      > .audit_reports/cleanup_cache.out 2>&1 || WARN "cleanup_cache retornou != 0"
  fi
  # Outras otimizações leves e seguras podem ser adicionadas aqui
else
  NOTE "Fix desativado (--no-fix). Somente análise/relatórios."
fi

# =======================
# MÉTRICAS CONSOLIDADAS
# =======================
SECTION "Geração de Métricas de Qualidade Consolidadas"

generate_consolidated_metrics() {
  "${PY}" - <<'PYTHON_METRICS'
import json, re
from pathlib import Path

metrics = {
    "god_codes_found": 0,
    "god_codes_fixed": 0,
    "security_issues": 0,
    "security_fixed": 0,
    "performance_issues": 0,
    "performance_optimized": 0,
    "quality_scores": [],
    "refactorings_applied": 0,
    "files_analyzed": 0,
    "architecture_violations": 0,
    "tdd_coverage": 0.0,
    "agents_executed": 0,
    "total_execution_time": 0.0
}

report_dir = Path(".audit_reports")
if report_dir.exists():
    for report_file in report_dir.glob("*.out"):
        try:
            content = report_file.read_text(encoding="utf-8", errors="ignore")
            lower = content.lower()

            if "god code patterns" in lower:
                m = re.search(r"Found (\d+) god code patterns", content, re.I)
                if m: metrics["god_codes_found"] += int(m.group(1))

            if "security" in lower:
                m = re.search(r"Security Issues?: (\d+)", content, re.I)
                if m: metrics["security_issues"] += int(m.group(1))
                if ("fixed" in lower) or ("applied" in lower):
                    metrics["security_fixed"] += 1

            if "performance" in lower:
                m = re.search(r"Performance Issues?: (\d+)", content, re.I)
                if m: metrics["performance_issues"] += int(m.group(1))
                if "optimized" in lower:
                    metrics["performance_optimized"] += 1

            m = re.search(r"Quality Score:? ([\d.]+)", content, re.I)
            if m: metrics["quality_scores"].append(float(m.group(1)))

            m = re.search(r"(\d+) refactorings? (applied|identified)", content, re.I)
            if m: metrics["refactorings_applied"] += int(m.group(1))

            if "architecture" in lower:
                m = re.search(r"(\d+) violations?", content, re.I)
                if m: metrics["architecture_violations"] += int(m.group(1))

            m = re.search(r"Coverage:? (\d+)%", content, re.I)
            if m: metrics["tdd_coverage"] = max(metrics["tdd_coverage"], int(m.group(1)))

            if "agents executed" in lower:
                m = re.search(r"(\d+) agents? executed", content, re.I)
                if m: metrics["agents_executed"] += int(m.group(1))

            m = re.search(r"Total time:? ([\d.]+)s", content, re.I)
            if m: metrics["total_execution_time"] += float(m.group(1))

            metrics["files_analyzed"] += 1

        except Exception as e:
            print(f"[warn] Erro ao processar {report_file}: {e}")

if metrics["quality_scores"]:
    metrics["average_quality"] = sum(metrics["quality_scores"]) / len(metrics["quality_scores"])
else:
    metrics["average_quality"] = 0.0

metrics["god_code_fix_rate"] = ((metrics["god_codes_fixed"] / metrics["god_codes_found"]) * 100) if metrics["god_codes_found"] else 0.0
metrics["security_fix_rate"] = ((metrics["security_fixed"] / metrics["security_issues"]) * 100) if metrics["security_issues"] else 0.0

metrics_file = Path(".audit_reports/consolidated_metrics.json")
metrics_file.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

final_score = 0.0
score_components = []

if metrics["average_quality"] > 0:
    final_score += metrics["average_quality"] * 10
    score_components.append(f"Qualidade: {metrics['average_quality']:.1f}")

if metrics["god_codes_found"] == 0:
    final_score += 20
    score_components.append("God Codes: ✅")
elif metrics["god_code_fix_rate"] > 50:
    final_score += 10
    score_components.append(f"God Codes: {metrics['god_code_fix_rate']:.0f}% corrigidos")

if metrics["security_issues"] == 0:
    final_score += 20
    score_components.append("Segurança: ✅")
elif metrics["security_fix_rate"] > 50:
    final_score += 10
    score_components.append(f"Segurança: {metrics['security_fix_rate']:.0f}% corrigidos")

if metrics["tdd_coverage"] > 80:
    final_score += 20
    score_components.append(f"TDD Coverage: {metrics['tdd_coverage']:.0f}%")
elif metrics["tdd_coverage"] > 60:
    final_score += 10
    score_components.append(f"TDD Coverage: {metrics['tdd_coverage']:.0f}%")

print("📊 MÉTRICAS CONSOLIDADAS:")
print(f"├── Arquivos Analisados: {metrics['files_analyzed']}")
print(f"├── God Codes Detectados: {metrics['god_codes_found']}")
if metrics["god_codes_found"] > 0:
    print(f"│   └── Taxa de Correção: {metrics['god_code_fix_rate']:.1f}%")
print(f"├── Issues de Segurança: {metrics['security_issues']}")
if metrics["security_issues"] > 0:
    print(f"│   └── Taxa de Correção: {metrics['security_fix_rate']:.1f}%")
print(f"├── Issues de Performance: {metrics['performance_issues']}")
print(f"├── Violações de Arquitetura: {metrics['architecture_violations']}")
print(f"├── Refatorações Aplicadas: {metrics['refactorings_applied']}")
print(f"├── Qualidade Média: {metrics['average_quality']:.1f}/10")
print(f"├── TDD Coverage: {metrics['tdd_coverage']:.0f}%")
print(f"├── Agentes Executados: {metrics['agents_executed']}")
print(f"├── Tempo Total: {metrics['total_execution_time']:.1f}s")
print(f"└── 🏆 Score Final: {final_score:.0f}/100 ({', '.join(score_components)})")

summary_file = Path(".audit_reports/audit_summary.txt")
summary_file.write_text(
    "RESUMO DA AUDITORIA\n" +
    "=" * 50 + "\n\n" +
    f"Score Final: {final_score:.0f}/100\n" +
    f"Arquivos Analisados: {metrics['files_analyzed']}\n" +
    f"God Codes: {metrics['god_codes_found']}\n" +
    f"Security Issues: {metrics['security_issues']}\n" +
    f"Performance Issues: {metrics['performance_issues']}\n" +
    f"Qualidade Média: {metrics['average_quality']:.1f}/10\n" +
    f"Agentes Executados: {metrics['agents_executed']}\n" +
    f"Tempo Total: {metrics['total_execution_time']:.1f}s\n",
    encoding="utf-8"
)

print(f"\n✅ Métricas salvas em: {metrics_file}")
print(f"✅ Resumo salvo em: {summary_file}")
PYTHON_METRICS
}

# Executa geração de métricas
if command -v "${PY}" >/dev/null 2>&1; then
  generate_consolidated_metrics || WARN "Falha ao gerar métricas consolidadas"
else
  WARN "Python não encontrado - pulando geração de métricas"
fi

# =======================
# Resumo final
# =======================
SECTION "Resumo"

FAILED_PY_FILES=$(wc -l < .audit_reports/py_compile_failed.txt 2>/dev/null || echo 0)
echo "• Arquivos Python com erro de sintaxe: ${FAILED_PY_FILES}"

if [[ -f ".audit_reports/consolidated_metrics.json" ]]; then
  echo "• 🤖 Sistema Multi-Agent: EXECUTADO"
  if command -v "${PY}" >/dev/null 2>&1; then
    "${PY}" - <<'PY'
import json
with open('.audit_reports/consolidated_metrics.json') as f:
    m = json.load(f)
print(f'  ├── God Codes: {m.get("god_codes_found", 0)}')
print(f'  ├── Security Issues: {m.get("security_issues", 0)}')
print(f'  ├── Quality Score: {m.get("average_quality", 0):.1f}/10')
print(f'  └── Refactorings: {m.get("refactorings_applied", 0)}')
PY
  fi
else
  echo "• 🤖 Sistema Multi-Agent: NÃO EXECUTADO"
fi

if (( FAST == 1 )); then
  echo "• Modo: FAST (análises e testes reduzidos)"
else
  echo "• Modo: COMPLETO"
fi
if (( FIX == 1 )); then
  echo "• Fix/Otimizações: ATIVADAS"
else
  echo "• Fix/Otimizações: DESATIVADAS (--no-fix)"
fi
# caminho absoluto do diretório de relatórios
if command -v realpath >/dev/null 2>&1; then
  echo "• Relatórios: $(realpath .audit_reports)"
else
  echo "• Relatórios: $(cd .audit_reports && pwd)"
fi

OK "Auditoria concluída."
