from __future__ import annotations

from pathlib import Path

from audit_system.core.container import build_default_auditor


def test_integration_basic_flow(tmp_path: Path):
    root = tmp_path / "proj"
    pkg = root / "pkg"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("")
    (pkg / "mod.py").write_text("# TODO: fix\nx=1\n", encoding="utf-8")

    auditor = build_default_auditor(root)
    findings = auditor.run()
    # Deve achar pelo menos o TODO
    assert any(f.rule == "TODO_PRESENT" for f in findings)
