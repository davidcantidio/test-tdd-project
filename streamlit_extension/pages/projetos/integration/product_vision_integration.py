"""
🔗 Product Vision Integration - História 1.1

Funções de integração que conectam o ProductVisionDTO com o sistema existente,
mantendo compatibilidade com product_vision_state.py e outros componentes.

Este módulo demonstra como usar o novo DTO padronizado em conjunto com
a arquitetura Clean Architecture existente.
"""

from typing import Dict, Any, Tuple
from ..dto.product_vision_dto import ProductVisionDTO
from ..domain.product_vision_state import (
    DEFAULT_PV, REQUIRED_FIELDS, 
    all_fields_filled, validate_product_vision,
    normalize_constraints as existing_normalize_constraints
)


def convert_existing_to_dto(existing_data: Dict[str, Any]) -> ProductVisionDTO:
    """
    Converter dados do sistema existente para ProductVisionDTO.
    
    Esta função facilita a migração de dados existentes para o novo DTO,
    mantendo compatibilidade com o formato atual do sistema.
    
    Args:
        existing_data: Dados no formato do sistema existente
        
    Returns:
        ProductVisionDTO validado e normalizado
        
    Examples:
        >>> from streamlit_extension.pages.projetos.domain.product_vision_state import DEFAULT_PV
        >>> dto = convert_existing_to_dto(DEFAULT_PV)
        >>> isinstance(dto, ProductVisionDTO)
        True
    """
    return ProductVisionDTO.from_dict(existing_data)


def convert_dto_to_existing(dto: ProductVisionDTO) -> Dict[str, Any]:
    """
    Converter ProductVisionDTO para formato do sistema existente.
    
    Esta função permite usar o DTO normalizado com funções legadas
    que esperam o formato tradicional de dicionário.
    
    Args:
        dto: ProductVisionDTO validado
        
    Returns:
        Dicionário no formato esperado pelo sistema existente
    """
    return dto.to_dict()


def validate_with_both_systems(data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    Validar dados usando tanto o sistema novo (DTO) quanto o existente.
    
    Esta função demonstra compatibilidade entre os dois sistemas de validação
    e pode ser usada durante a migração para verificar consistência.
    
    Args:
        data: Dados para validar
        
    Returns:
        Tupla (is_consistent, comparison_results) onde:
        - is_consistent: True se ambos sistemas concordam
        - comparison_results: Detalhes da comparação
    """
    # Validação com novo sistema (DTO)
    dto = ProductVisionDTO.from_dict(data)
    dto_valid = dto.is_valid()
    dto_errors = dto.get_errors()
    
    # Validação com sistema existente
    existing_valid = all_fields_filled(data)
    existing_validation = validate_product_vision(data)
    existing_errors = [] if existing_validation[0] else [existing_validation[1]]
    
    # Comparar resultados
    is_consistent = dto_valid == existing_valid
    
    comparison_results = {
        "dto_validation": {
            "valid": dto_valid,
            "errors": dto_errors
        },
        "existing_validation": {
            "valid": existing_valid, 
            "errors": existing_errors
        },
        "consistent": is_consistent,
        "dto_constraints": dto.constraints,
        "existing_constraints": existing_normalize_constraints(data.get("constraints", []))
    }
    
    return is_consistent, comparison_results


def create_default_dto() -> ProductVisionDTO:
    """
    Criar ProductVisionDTO com dados padrão do sistema existente.
    
    Returns:
        ProductVisionDTO inicializado com DEFAULT_PV
    """
    return ProductVisionDTO.from_dict(DEFAULT_PV)


def is_dto_compatible_with_required_fields() -> bool:
    """
    Verificar se ProductVisionDTO é compatível com REQUIRED_FIELDS existente.
    
    Returns:
        True se todos os campos obrigatórios estão presentes no DTO
    """
    dto = create_default_dto()
    
    for field in REQUIRED_FIELDS:
        if not hasattr(dto, field):
            return False
    
    return True


def migration_helper_validate_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Helper para migração: validar dados e fornecer relatório detalhado.
    
    Esta função pode ser usada durante a migração para identificar
    dados que precisam de atenção especial.
    
    Args:
        data: Dados para analisar
        
    Returns:
        Relatório detalhado da migração
    """
    # Criar DTO e verificar estado
    dto = ProductVisionDTO.from_dict(data)
    
    # Análise detalhada
    migration_report = {
        "original_data": data,
        "dto_valid": dto.is_valid(),
        "dto_errors": dto.get_errors(),
        "normalized_data": dto.to_dict(),
        "constraints_normalized": dto.constraints != data.get("constraints", []),
        "fields_summary": {
            "vision_statement": {
                "original": data.get("vision_statement", ""),
                "normalized": dto.vision_statement,
                "changed": data.get("vision_statement", "") != dto.vision_statement
            },
            "constraints": {
                "original": data.get("constraints", []),
                "normalized": dto.constraints,
                "changed": data.get("constraints", []) != dto.constraints
            }
        },
        "migration_needed": not dto.is_valid(),
        "recommendations": []
    }
    
    # Gerar recomendações
    if not dto.is_valid():
        migration_report["recommendations"].append("Dados requerem correção antes da migração")
        for error in dto.get_errors():
            migration_report["recommendations"].append(f"Corrigir: {error}")
    
    if migration_report["constraints_normalized"]:
        migration_report["recommendations"].append("Constraints foram normalizadas (duplicatas/espaços removidos)")
    
    return migration_report