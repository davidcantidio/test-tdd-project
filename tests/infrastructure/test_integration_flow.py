import sys
import types
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))
pkg = types.ModuleType("audit_system")
pkg.__path__ = [str(Path(__file__).resolve().parents[1] / "audit_system")]
sys.modules.setdefault("audit_system", pkg)
sys.modules.setdefault("streamlit", types.ModuleType("streamlit"))

from audit_system.coordination.meta_agent import run_meta_agent_analysis, TaskType
from audit_system.core.systematic_file_auditor import EnhancedSystematicFileAuditor


def test_meta_agent_analysis_completes(tmp_path):
    # Create a simple Python file for analysis
    test_file = tmp_path / "sample.py"
    test_file.write_text("def foo():\n    return 42\n")
    result = run_meta_agent_analysis(
        file_path=str(test_file),
        task_type=TaskType.COMPREHENSIVE_AUDIT,
        project_root=str(tmp_path),
        token_budget=1000,
        dry_run=True,
    )
    assert "execution_plan" in result
    assert isinstance(result["execution_results"], list)


def test_systematic_auditor_flow(tmp_path):
    # Simulated project directory
    project_dir = tmp_path
    file_to_audit = project_dir / "module.py"
    file_to_audit.write_text("x = 1\n")
    auditor = EnhancedSystematicFileAuditor(
        project_root=project_dir,
        audit_dir=project_dir,
        dry_run=True,
    )
    res = auditor.audit_file_enhanced(str(file_to_audit))
    assert hasattr(res, "lines_analyzed")
    assert isinstance(res.lines_analyzed, int)
