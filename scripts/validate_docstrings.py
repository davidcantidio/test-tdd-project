"""
Script para validar que todos os métodos públicos têm docstrings.
"""

from __future__ import annotations

import importlib.util
import inspect
from typing import List, Dict


class DocstringValidator:
    def check_missing_docstrings(self, module_path: str) -> List[str]:
        """Check for missing docstrings in public methods.

        Args:
            module_path: File path to module or dotted module path.
        """
        if module_path.endswith(".py"):
            spec = importlib.util.spec_from_file_location("_mod", module_path)
            module = importlib.util.module_from_spec(spec)
            assert spec.loader is not None
            spec.loader.exec_module(module)  # type: ignore[assignment]
        else:
            module = importlib.import_module(module_path)

        missing: List[str] = []
        for name, obj in inspect.getmembers(module, inspect.isclass):
            for meth_name, meth in inspect.getmembers(obj, inspect.isfunction):
                if not meth_name.startswith("_") and not inspect.getdoc(meth):
                    missing.append(f"{name}.{meth_name}")
        return missing

    def validate_docstring_format(self, docstring: str) -> bool:
        """Validate docstring follows Google style guide."""
        if not docstring:
            return False
        return "Args:" in docstring and "Returns:" in docstring

    def generate_report(self, results: Dict[str, object]) -> str:
        """Generate validation report."""
        lines = []
        for name, status in results.items():
            lines.append(f"{name}: {status}")
        return "\n".join(lines)


if __name__ == "__main__":
    validator = DocstringValidator()
    missing = validator.check_missing_docstrings("streamlit_extension/utils/database.py")
    report = validator.generate_report({"missing": missing})
    print(report)
