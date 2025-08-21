from __future__ import annotations

from pathlib import Path

import pytest
import sys, types, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.modules.setdefault("streamlit", types.ModuleType("streamlit"))

meta_agent_mod = pytest.importorskip("audit_system.coordination.meta_agent")


def test_recommend_agents_returns_list(tmp_path: Path) -> None:
    MetaAgent = getattr(meta_agent_mod, "MetaAgent", None)
    assert MetaAgent is not None, "MetaAgent class is required"
    ma = MetaAgent(project_root=tmp_path)
    f = tmp_path / "sample.py"
    f.write_text("x = 1\n")
    FileAnalysis = getattr(meta_agent_mod, "FileAnalysis")
    FileComplexity = getattr(meta_agent_mod, "FileComplexity")
    analysis = FileAnalysis(file_path=str(f), line_count=1, function_count=0, class_count=0, ast_complexity_score=0.0, file_complexity=FileComplexity.SIMPLE)
    recs = ma.recommend_agents(analysis)
    assert isinstance(recs, (list, tuple))
    for r in recs:
        assert hasattr(r, "name")
