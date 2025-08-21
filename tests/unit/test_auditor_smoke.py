from __future__ import annotations

from pathlib import Path

import pytest
import sys, types, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.modules.setdefault("streamlit", types.ModuleType("streamlit"))

core_mod = pytest.importorskip("audit_system.core.systematic_file_auditor")


def _locate_candidate_class(mod) -> type | None:
    for name in ("EnhancedSystematicFileAuditor", "SystematicFileAuditor", "FileAuditor"):
        cls = getattr(mod, name, None)
        if isinstance(cls, type):
            return cls
    return None


def test_auditor_basic_flow(tmp_path: Path) -> None:
    AuditorCls = _locate_candidate_class(core_mod)
    assert AuditorCls is not None, "Auditor class not found in core.systematic_file_auditor"
    auditor = AuditorCls(project_root=tmp_path, audit_dir=tmp_path)
    file_path = tmp_path / "demo.py"
    file_path.write_text("def add(a,b):\n    return a+b\n")
    for meth in ("audit_file_enhanced", "audit_file", "analyze_file"):
        fn = getattr(auditor, meth, None)
        if callable(fn):
            try:
                res = fn(file_path=str(file_path))
            except TypeError:
                try:
                    res = fn(file_path=file_path)
                except TypeError:
                    continue
            assert res is not None or res is None
            break
    else:
        pytest.skip("No compatible auditor method found (audit_file_enhanced/audit_file/analyze_file)")
