#!/usr/bin/env python3
"""
Refactor 'open(' to 'safe_open(BASE_DIR, ...)' inside 'audit_system/' Python files.
- Inserts: from audit_system.utils.path_security import safe_open
- Adds module-level BASE_DIR pointing to repo root (parents) or cwd as fallback
- Skips replacements where 'open(' is already qualified or part of a name (very conservative)

USAGE:
  python scripts/maintenance/refactor_safe_open.py --dry-run
  python scripts/maintenance/refactor_safe_open.py --apply
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET_DIR = ROOT / "audit_system"

OPEN_PATTERN = re.compile(r"(?<![A-Za-z0-9_\.])open\s*\(", re.MULTILINE)

IMPORT_LINE = "from audit_system.utils.path_security import safe_open"
BASE_DIR_LINE = "BASE_DIR = Path(__file__).resolve().parents[2]"


def process_file(path: Path) -> tuple[bool, str]:
    text = path.read_text(encoding="utf-8")
    changed = False
    new_text = text

    if IMPORT_LINE not in new_text:
        lines = new_text.splitlines()
        insert_idx = 0
        for i, ln in enumerate(lines[:50]):
            if ln.startswith("from __future__ import"):
                insert_idx = i + 1
        lines.insert(insert_idx, IMPORT_LINE)
        new_text = "\n".join(lines)
        changed = True

    if "safe_open(" in new_text and "BASE_DIR" not in new_text:
        lines = new_text.splitlines()
        if "from pathlib import Path" not in new_text:
            for i, ln in enumerate(lines[:50]):
                if ln.startswith("import") or ln.startswith("from"):
                    insert_idx = i + 1
            else:
                insert_idx = 0
            lines.insert(insert_idx, "from pathlib import Path")
        insert_at = 0
        for i, ln in enumerate(lines[:100]):
            if ln.strip() == "" or ln.startswith(("import", "from")):
                insert_at = i + 1
            else:
                break
        lines.insert(insert_at, BASE_DIR_LINE)
        new_text = "\n".join(lines)
        changed = True

    def repl(m: re.Match[str]) -> str:
        return "safe_open(BASE_DIR, "

    replaced_text, n = OPEN_PATTERN.subn(repl, new_text)
    if n > 0:
        new_text = replaced_text
        changed = True

    return changed, new_text


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Write changes to files")
    ap.add_argument("--dry-run", action="store_true", help="Show diff-like preview")
    args = ap.parse_args()

    assert TARGET_DIR.exists(), f"{TARGET_DIR} not found"
    py_files = [p for p in TARGET_DIR.rglob("*.py") if p.is_file()]

    changed_any = False
    for f in py_files:
        changed, new_text = process_file(f)
        if not changed:
            continue
        changed_any = True
        if args.dry_run:
            print(f"--- {f}")
            print(f"+++ {f}")
            old_lines = f.read_text(encoding="utf-8").splitlines()
            new_lines = new_text.splitlines()
            for i, (o, n) in enumerate(zip(old_lines, new_lines)):
                if o != n:
                    print(f"@@ line {i+1} @@")
                    print(f"- {o}")
                    print(f"+ {n}")
            if len(new_lines) > len(old_lines):
                for j in range(len(old_lines), len(new_lines)):
                    print(f"+ {new_lines[j]}")
        if args.apply:
            f.write_text(new_text, encoding="utf-8")

    if not changed_any:
        print("No changes needed.")


if __name__ == "__main__":
    main()
