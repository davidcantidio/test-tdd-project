"""
🎯 Product Vision Validator - História 1.1

Funções de validação independentes para Product Vision, extraídas do DTO
para permitir reutilização em diferentes partes do sistema.

Implementa os critérios de aceitação da História 1.1:
- DTO valida campos obrigatórios; rejeita strings vazias  
- constraints sempre lista normalizada (trim, sem duplicatas)
"""

from typing import Dict, Any, List, Tuple, Optional


def normalize_constraint_list(constraints: List[Any]) -> List[str]:
    """
    Normalizar lista de constraints conforme critérios de aceitação.
    
    Normalização aplicada:
    - Remove entradas None ou não-string
    - Remove espaços em branco no início/fim (trim) 
    - Remove entradas vazias após trim
    - Remove duplicatas
    - Mantém ordem original (primeira ocorrência)
    
    Args:
        constraints: Lista de constraints (pode conter tipos diversos)
        
    Returns:
        Lista normalizada de strings únicas
        
    Examples:
        >>> normalize_constraint_list(["  Budget  ", "Time", "Budget"])
        ["Budget", "Time"]
        
        >>> normalize_constraint_list(["", "  ", None, "Valid"])  
        ["Valid"]
    """
    if not constraints:
        return []
    
    normalized = []
    seen = set()
    
    for constraint in constraints:
        # Ignorar entradas None ou não-string
        if constraint is None or not isinstance(constraint, str):
            continue
        
        # Aplicar trim
        trimmed = constraint.strip()
        
        # Ignorar strings vazias após trim
        if not trimmed:
            continue
        
        # Adicionar apenas se ainda não visto (remover duplicatas)
        if trimmed not in seen:
            seen.add(trimmed)
            normalized.append(trimmed)
    
    return normalized


def validate_required_fields(data: Dict[str, Any]) -> List[str]:
    """
    Validar campos obrigatórios do Product Vision.
    
    Args:
        data: Dicionário com dados do product vision
        
    Returns:
        Lista de mensagens de erro (vazia se válido)
    """
    errors = []
    
    # Campos obrigatórios string
    required_string_fields = {
        "vision_statement": "Declaração da Visão",
        "problem_statement": "Declaração do Problema",
        "target_audience": "Público-alvo", 
        "value_proposition": "Proposta de Valor"
    }
    
    for field_name, field_label in required_string_fields.items():
        field_value = data.get(field_name)
        
        # Verificar se campo existe e não é None
        if field_value is None:
            errors.append(f"{field_label} é um campo obrigatório")
            continue
        
        # Verificar se não é string vazia ou apenas espaços
        if not isinstance(field_value, str) or not field_value.strip():
            errors.append(f"{field_label} não pode estar vazio ou em branco")
    
    # Validar constraints (lista pode estar vazia, mas deve existir)
    if "constraints" in data and not isinstance(data["constraints"], list):
        errors.append("Constraints deve ser uma lista")
    
    return errors


def validate_product_vision_dto(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validar dados completos do Product Vision DTO.
    
    Args:
        data: Dicionário com dados do product vision
        
    Returns:
        Tupla (is_valid, errors) onde:
        - is_valid: True se válido, False caso contrário
        - errors: Lista de mensagens de erro
        
    Examples:
        >>> valid_data = {
        ...     "vision_statement": "Create amazing products",
        ...     "problem_statement": "Current solutions are poor", 
        ...     "target_audience": "Developers",
        ...     "value_proposition": "Better development experience",
        ...     "constraints": ["Budget", "Time"]
        ... }
        >>> is_valid, errors = validate_product_vision_dto(valid_data)
        >>> is_valid
        True
        >>> errors
        []
    """
    # Validar campos obrigatórios
    errors = validate_required_fields(data)
    
    # DTO é válido se não há erros
    is_valid = len(errors) == 0
    
    return is_valid, errors


def validate_and_normalize_constraints(constraints: List[Any]) -> Tuple[List[str], List[str]]:
    """
    Validar e normalizar constraints com informações de validação.
    
    Args:
        constraints: Lista de constraints para validar e normalizar
        
    Returns:
        Tupla (normalized_constraints, validation_warnings) onde:
        - normalized_constraints: Lista normalizada
        - validation_warnings: Lista de avisos sobre normalizações feitas
    """
    if not constraints:
        return [], []
    
    warnings = []
    original_count = len(constraints)
    
    # Normalizar
    normalized = normalize_constraint_list(constraints)
    
    # Gerar avisos informativos
    normalized_count = len(normalized)
    removed_count = original_count - normalized_count
    
    if removed_count > 0:
        warnings.append(f"Removidas {removed_count} constraints vazias ou duplicadas")
    
    return normalized, warnings


def create_product_vision_dto_from_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Criar dados normalizados de Product Vision a partir de dicionário.
    
    Esta função aplica todas as normalizações e validações necessárias
    para criar um Product Vision DTO válido.
    
    Args:
        data: Dados brutos do product vision
        
    Returns:
        Dicionário normalizado pronto para uso
        
    Raises:
        ValueError: Se dados são inválidos após normalização
    """
    # Extrair dados com defaults seguros
    normalized_data = {
        "vision_statement": data.get("vision_statement", ""),
        "problem_statement": data.get("problem_statement", ""),
        "target_audience": data.get("target_audience", ""),
        "value_proposition": data.get("value_proposition", ""),
        "constraints": normalize_constraint_list(data.get("constraints", []))
    }
    
    # Validar dados normalizados
    is_valid, errors = validate_product_vision_dto(normalized_data)
    
    if not is_valid:
        error_message = "Dados inválidos: " + "; ".join(errors)
        raise ValueError(error_message)
    
    return normalized_data