"""
🎯 Epic Suggestion Validator - História 1.2

Funções de validação independentes para Epic Suggestion, extraídas do DTO
para permitir reutilização em diferentes partes do sistema.

Implementa os critérios de aceitação da História 1.2:
- Estrutura: EpicSuggestionDTO(title, rationale, tags[], confidence:0..1, source="ai|heuristic")
- Serializa/deserializa (dict) sem perda
"""

from typing import Dict, Any, List, Tuple, Optional, Union


def normalize_tag_list(tags: List[Any]) -> List[str]:
    """
    Normalizar lista de tags conforme critérios de aceitação.
    
    Normalização aplicada:
    - Remove entradas None ou não-string
    - Remove espaços em branco no início/fim (trim) 
    - Remove entradas vazias após trim
    - Remove duplicatas
    - Mantém ordem original (primeira ocorrência)
    
    Args:
        tags: Lista de tags (pode conter tipos diversos)
        
    Returns:
        Lista normalizada de strings únicas
        
    Examples:
        >>> normalize_tag_list(["  Backend  ", "Frontend", "Backend"])
        ["Backend", "Frontend"]
        
        >>> normalize_tag_list(["", "  ", None, "Valid"])  
        ["Valid"]
    """
    if not tags:
        return []
    
    normalized = []
    seen = set()
    
    for tag in tags:
        # Ignorar entradas None ou não-string
        if tag is None or not isinstance(tag, str):
            continue
        
        # Aplicar trim
        trimmed = tag.strip()
        
        # Ignorar strings vazias após trim
        if not trimmed:
            continue
        
        # Adicionar apenas se ainda não visto (remover duplicatas)
        if trimmed not in seen:
            seen.add(trimmed)
            normalized.append(trimmed)
    
    return normalized


def validate_confidence_range(confidence: Union[int, float]) -> Tuple[bool, Optional[str]]:
    """
    Validar se confidence está no range 0.0-1.0.
    
    Args:
        confidence: Valor de confidence para validar
        
    Returns:
        Tupla (is_valid, error_message) onde:
        - is_valid: True se válido, False caso contrário
        - error_message: Mensagem de erro ou None se válido
        
    Examples:
        >>> validate_confidence_range(0.5)
        (True, None)
        
        >>> validate_confidence_range(1.5)
        (False, "Confidence deve estar entre 0.0 e 1.0")
    """
    if not isinstance(confidence, (int, float)):
        return False, "Confidence deve ser um número"
    
    if confidence < 0.0 or confidence > 1.0:
        return False, "Confidence deve estar entre 0.0 e 1.0"
    
    return True, None


def validate_source_type(source: str) -> Tuple[bool, Optional[str]]:
    """
    Validar se source é "ai" ou "heuristic".
    
    Args:
        source: Valor de source para validar
        
    Returns:
        Tupla (is_valid, error_message) onde:
        - is_valid: True se válido, False caso contrário
        - error_message: Mensagem de erro ou None se válido
        
    Examples:
        >>> validate_source_type("ai")
        (True, None)
        
        >>> validate_source_type("manual")
        (False, "Source deve ser 'ai' ou 'heuristic', recebido: 'manual'")
    """
    valid_sources = ["ai", "heuristic"]
    
    if not isinstance(source, str):
        return False, "Source deve ser uma string"
    
    if source not in valid_sources:
        return False, f"Source deve ser 'ai' ou 'heuristic', recebido: '{source}'"
    
    return True, None


def validate_required_epic_suggestion_fields(data: Dict[str, Any]) -> List[str]:
    """
    Validar campos obrigatórios do Epic Suggestion.
    
    Args:
        data: Dicionário com dados do epic suggestion
        
    Returns:
        Lista de mensagens de erro (vazia se válido)
    """
    errors = []
    
    # Campos obrigatórios string
    required_string_fields = {
        "title": "Título",
        "rationale": "Justificativa"
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
    
    return errors


def validate_epic_suggestion_dto(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validar dados completos do Epic Suggestion DTO.
    
    Args:
        data: Dicionário com dados do epic suggestion
        
    Returns:
        Tupla (is_valid, errors) onde:
        - is_valid: True se válido, False caso contrário
        - errors: Lista de mensagens de erro
        
    Examples:
        >>> valid_data = {
        ...     "title": "Autenticação de Usuários",
        ...     "rationale": "Sistema precisa de login seguro", 
        ...     "tags": ["segurança", "login"],
        ...     "confidence": 0.85,
        ...     "source": "ai"
        ... }
        >>> is_valid, errors = validate_epic_suggestion_dto(valid_data)
        >>> is_valid
        True
        >>> errors
        []
    """
    errors = []
    
    # Validar campos obrigatórios
    errors.extend(validate_required_epic_suggestion_fields(data))
    
    # Validar confidence
    confidence = data.get("confidence", 0.0)
    confidence_valid, confidence_error = validate_confidence_range(confidence)
    if not confidence_valid:
        errors.append(confidence_error)
    
    # Validar source
    source = data.get("source", "")
    source_valid, source_error = validate_source_type(source)
    if not source_valid:
        errors.append(source_error)
    
    # Validar tags (opcional - apenas normalização, sem erro se vazia)
    tags = data.get("tags", [])
    if not isinstance(tags, list):
        errors.append("Tags deve ser uma lista")
    
    # DTO é válido se não há erros
    is_valid = len(errors) == 0
    
    return is_valid, errors


def validate_and_normalize_tags(tags: List[Any]) -> Tuple[List[str], List[str]]:
    """
    Validar e normalizar tags com informações de validação.
    
    Args:
        tags: Lista de tags para validar e normalizar
        
    Returns:
        Tupla (normalized_tags, validation_warnings) onde:
        - normalized_tags: Lista normalizada
        - validation_warnings: Lista de avisos sobre normalizações feitas
    """
    if not tags:
        return [], []
    
    warnings = []
    original_count = len(tags)
    
    # Normalizar
    normalized = normalize_tag_list(tags)
    
    # Gerar avisos informativos
    normalized_count = len(normalized)
    removed_count = original_count - normalized_count
    
    if removed_count > 0:
        warnings.append(f"Removidas {removed_count} tags vazias ou duplicadas")
    
    return normalized, warnings


def create_epic_suggestion_dto_from_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Criar dados normalizados de Epic Suggestion a partir de dicionário.
    
    Esta função aplica todas as normalizações e validações necessárias
    para criar um Epic Suggestion DTO válido.
    
    Args:
        data: Dados brutos do epic suggestion
        
    Returns:
        Dicionário normalizado pronto para uso
        
    Raises:
        ValueError: Se dados são inválidos após normalização
    """
    # Extrair dados com defaults seguros
    normalized_data = {
        "title": data.get("title"),
        "rationale": data.get("rationale"),
        "tags": normalize_tag_list(data.get("tags", [])),
        "confidence": data.get("confidence", 0.0),
        "source": data.get("source", "")
    }
    
    # Validar dados normalizados
    is_valid, errors = validate_epic_suggestion_dto(normalized_data)
    
    if not is_valid:
        error_message = "Dados inválidos: " + "; ".join(errors)
        raise ValueError(error_message)
    
    return normalized_data


def get_epic_suggestion_validation_summary(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Obter resumo completo de validação para Epic Suggestion.
    
    Args:
        data: Dados para validar
        
    Returns:
        Dicionário com resumo completo da validação
    """
    is_valid, errors = validate_epic_suggestion_dto(data)
    tags_normalized, tag_warnings = validate_and_normalize_tags(data.get("tags", []))
    
    summary = {
        "is_valid": is_valid,
        "errors": errors,
        "warnings": tag_warnings,
        "normalized_tags": tags_normalized,
        "validation_details": {
            "title_valid": not any("título" in error.lower() for error in errors),
            "rationale_valid": not any("justificativa" in error.lower() for error in errors),
            "confidence_valid": not any("confidence" in error.lower() for error in errors),
            "source_valid": not any("source" in error.lower() for error in errors),
            "tags_count": len(tags_normalized)
        }
    }
    
    return summary