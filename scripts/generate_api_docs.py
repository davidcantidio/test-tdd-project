"""
Script para gerar documentação de API automaticamente.

Extrai docstrings de classes e métodos e gera markdown.
"""

from __future__ import annotations

import importlib.util
import inspect
from pathlib import Path
from typing import Dict


class APIDocGenerator:
    def extract_docstrings(self, module_path: str) -> Dict[str, str]:
        """Extract docstrings from Python modules."""
        spec = importlib.util.spec_from_file_location("_mod", module_path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)  # type: ignore[assignment]

        docs: Dict[str, str] = {}
        for name, obj in inspect.getmembers(module, inspect.isclass):
            docs[name] = inspect.getdoc(obj) or ""
        return docs

    def generate_markdown(self, docstrings: Dict[str, str]) -> str:
        """Generate markdown documentation from docstrings."""
        lines = []
        for name, doc in docstrings.items():
            lines.append(f"# {name}\n\n{doc}\n")
        return "\n".join(lines)

    def save_documentation(self, content: str, output_path: str) -> None:
        """Save generated documentation to file."""
        Path(output_path).write_text(content, encoding="utf-8")


if __name__ == "__main__":
    generator = APIDocGenerator()
    docs = generator.extract_docstrings("streamlit_extension/utils/database.py")
    markdown = generator.generate_markdown(docs)
    generator.save_documentation(markdown, "docs/api/generated_database.md")
