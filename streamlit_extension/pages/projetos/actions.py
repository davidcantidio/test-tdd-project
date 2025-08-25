from typing import Dict, Tuple

MIN_NAME_LEN = 3

def validate_project_name(name: str) -> bool:
    if not isinstance(name, str):
        return False
    name = name.strip()
    return len(name) >= MIN_NAME_LEN

def _empty_product_vision() -> Dict:
    return {
        "vision_statement": "",
        "problem_statement": "",
        "target_audience": "",
        "value_proposition": "",
        "constraints": [],
    }

def create_new_project_draft(name: str) -> Tuple[Dict, str]:
    """
    Retorna (draft, route). Route esperado: 'projeto_wizard'.
    Lança ValueError se o nome for inválido.
    """
    if not validate_project_name(name):
        raise ValueError("Nome do projeto inválido (mínimo 3 caracteres).")

    draft: Dict = {
        "id": None,                # ainda não persistido
        "name": name.strip(),
        "current_phase": "product_vision",
        "product_vision": _empty_product_vision(),
    }
    return draft, "projeto_wizard"
