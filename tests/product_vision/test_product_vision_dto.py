"""
🧪 Testes RED para ProductVisionDTO - História 1.1

Este arquivo implementa testes TDD para validação do DTO do Product Vision
seguindo os critérios de aceitação da História 1.1:

Aceitação:
- DTO valida campos obrigatórios; rejeita strings vazias
- constraints sempre lista normalizada (trim, sem duplicatas)

Casos de teste:
- DTO completo e válido → sucesso
- Campo obrigatório faltando → falha com mensagem clara
- String vazia em campo obrigatório → falha
- Constraints duplicadas → normalização automática
- Constraints com espaços → trim automático
- Constraints vazias → remoção automática
"""

import pytest
from typing import Dict, Any, List
from unittest.mock import Mock

# TODO: Importar ProductVisionDTO quando implementado
# from streamlit_extension.pages.projetos.dto.product_vision_dto import ProductVisionDTO
# from streamlit_extension.pages.projetos.validators.product_vision_validator import (
#     validate_product_vision_dto, 
#     normalize_constraint_list
# )


class TestProductVisionDTO:
    """Testes RED para ProductVisionDTO - TDD História 1.1"""
    
    def test_valid_complete_dto_should_pass_validation(self):
        """
        RED: DTO completo e válido deve passar na validação
        
        Given: Dados completos e válidos do product vision
        When: Criar ProductVisionDTO
        Then: Validação deve ser bem-sucedida
        """
        # Arrange
        valid_data = {
            "vision_statement": "Transformar desenvolvimento de software com TDD",
            "problem_statement": "Equipes lutam para adotar TDD eficazmente",
            "target_audience": "Times de desenvolvimento de software",
            "value_proposition": "Framework simplificado para adoção de TDD",
            "constraints": ["Prazo de 90 dias", "Orçamento limitado", "Equipe pequena"]
        }
        
        # Act & Assert
        from streamlit_extension.pages.projetos.dto.product_vision_dto import ProductVisionDTO
        dto = ProductVisionDTO.from_dict(valid_data)
        assert dto.is_valid() is True
        assert dto.get_errors() == []
    
    def test_missing_required_field_should_fail_validation(self):
        """
        RED: Campo obrigatório faltando deve falhar na validação
        
        Given: Dados sem campo obrigatório (vision_statement)
        When: Criar ProductVisionDTO
        Then: Validação deve falhar com mensagem clara
        """
        # Arrange
        incomplete_data = {
            # "vision_statement": missing!
            "problem_statement": "Problema identificado",
            "target_audience": "Audiência definida",
            "value_proposition": "Valor claro",
            "constraints": ["Restrição 1"]
        }
        
        # Act & Assert
        from streamlit_extension.pages.projetos.dto.product_vision_dto import ProductVisionDTO
        dto = ProductVisionDTO.from_dict(incomplete_data)
        assert dto.is_valid() is False
        errors = dto.get_errors()
        assert any("visão" in error.lower() for error in errors)
        assert any("vazio" in error.lower() or "em branco" in error.lower() for error in errors)
    
    def test_empty_string_field_should_fail_validation(self):
        """
        RED: String vazia em campo obrigatório deve falhar na validação
        
        Given: Campo obrigatório com string vazia
        When: Criar ProductVisionDTO
        Then: Validação deve falhar
        """
        # Arrange
        data_with_empty_field = {
            "vision_statement": "",  # String vazia
            "problem_statement": "Problema válido",
            "target_audience": "Audiência válida",
            "value_proposition": "Valor válido",
            "constraints": ["Restrição válida"]
        }
        
        # Act & Assert
        from streamlit_extension.pages.projetos.dto.product_vision_dto import ProductVisionDTO
        dto = ProductVisionDTO.from_dict(data_with_empty_field)
        assert dto.is_valid() is False
        errors = dto.get_errors()
        assert any("visão" in error.lower() for error in errors)
    
    def test_whitespace_only_field_should_fail_validation(self):
        """
        RED: Campo com apenas espaços em branco deve falhar na validação
        
        Given: Campo obrigatório com apenas whitespace
        When: Criar ProductVisionDTO
        Then: Validação deve falhar
        """
        # Arrange
        data_with_whitespace_field = {
            "vision_statement": "   ",  # Apenas espaços
            "problem_statement": "Problema válido",
            "target_audience": "Audiência válida", 
            "value_proposition": "Valor válido",
            "constraints": ["Restrição válida"]
        }
        
        # Act & Assert
        from streamlit_extension.pages.projetos.dto.product_vision_dto import ProductVisionDTO
        dto = ProductVisionDTO.from_dict(data_with_whitespace_field)
        assert dto.is_valid() is False


class TestConstraintsNormalization:
    """Testes RED para normalização de constraints - História 1.1"""
    
    def test_duplicate_constraints_should_be_normalized(self):
        """
        RED: Constraints duplicadas devem ser removidas automaticamente
        
        Given: Lista de constraints com duplicatas
        When: Normalizar constraints
        Then: Duplicatas devem ser removidas
        """
        # Arrange
        data_with_duplicates = {
            "vision_statement": "Visão válida",
            "problem_statement": "Problema válido",
            "target_audience": "Audiência válida",
            "value_proposition": "Valor válido",
            "constraints": ["Orçamento limitado", "Prazo curto", "Orçamento limitado", "Prazo curto"]
        }
        
        # Act & Assert
        from streamlit_extension.pages.projetos.dto.product_vision_dto import ProductVisionDTO
        dto = ProductVisionDTO.from_dict(data_with_duplicates)
        assert dto.is_valid() is True
        assert len(dto.constraints) == 2
        assert "Orçamento limitado" in dto.constraints
        assert "Prazo curto" in dto.constraints
    
    def test_constraints_with_whitespace_should_be_trimmed(self):
        """
        RED: Constraints com espaços devem ser limpas (trim)
        
        Given: Constraints com espaços no início/fim
        When: Normalizar constraints
        Then: Espaços devem ser removidos
        """
        # Arrange
        constraints_with_whitespace = ["  Orçamento limitado  ", " Prazo curto", "Equipe pequena "]
        
        # Act & Assert  
        from streamlit_extension.pages.projetos.dto.product_vision_dto import ProductVisionDTO
        # Simular dados completos com constraints problemáticas
        data = {
            "vision_statement": "Visão válida",
            "problem_statement": "Problema válido",
            "target_audience": "Audiência válida",
            "value_proposition": "Valor válido",
            "constraints": constraints_with_whitespace
        }
        dto = ProductVisionDTO.from_dict(data)
        assert "Orçamento limitado" in dto.constraints
        assert "Prazo curto" in dto.constraints
        assert "Equipe pequena" in dto.constraints
        # Verificar que não há espaços extras
        for constraint in dto.constraints:
            assert constraint == constraint.strip()
    
    def test_empty_constraints_should_be_removed(self):
        """
        RED: Constraints vazias devem ser removidas automaticamente
        
        Given: Lista com constraints vazias
        When: Normalizar constraints
        Then: Entradas vazias devem ser removidas
        """
        # Arrange
        constraints_with_empty = ["Válida", "", "  ", "Outra válida", None]
        
        # Act & Assert
        from streamlit_extension.pages.projetos.dto.product_vision_dto import ProductVisionDTO
        # Simular dados completos com constraints problemáticas
        data = {
            "vision_statement": "Visão válida",
            "problem_statement": "Problema válido",
            "target_audience": "Audiência válida",
            "value_proposition": "Valor válido",
            "constraints": constraints_with_empty
        }
        dto = ProductVisionDTO.from_dict(data)
        assert len(dto.constraints) == 2
        assert "Válida" in dto.constraints
        assert "Outra válida" in dto.constraints
        assert "" not in dto.constraints
        # None values are filtered out during normalization
    
    def test_constraints_normalization_comprehensive(self):
        """
        RED: Normalização completa - duplicatas, espaços e vazias
        
        Given: Lista com todos os problemas (duplicatas, espaços, vazias)
        When: Normalizar constraints
        Then: Lista limpa e única
        """
        # Arrange
        messy_constraints = [
            "  Orçamento limitado  ",
            "Prazo curto",
            "",
            "  Orçamento limitado",  # Duplicata com espaço
            "   ",  # Apenas espaços
            "Equipe pequena",
            "Prazo curto ",  # Duplicata com espaço final
            None
        ]
        
        # Act & Assert
        from streamlit_extension.pages.projetos.dto.product_vision_dto import ProductVisionDTO
        # Simular dados completos com constraints problemáticas
        data = {
            "vision_statement": "Visão válida",
            "problem_statement": "Problema válido",
            "target_audience": "Audiência válida",
            "value_proposition": "Valor válido",
            "constraints": messy_constraints
        }
        dto = ProductVisionDTO.from_dict(data)
        assert len(dto.constraints) == 3  # Apenas as 3 únicas
        assert "Orçamento limitado" in dto.constraints
        assert "Prazo curto" in dto.constraints
        assert "Equipe pequena" in dto.constraints


class TestProductVisionDTOIntegration:
    """Testes RED para integração completa do DTO - História 1.1"""
    
    def test_dto_serialization_roundtrip(self):
        """
        RED: DTO deve serializar/deserializar sem perda de dados
        
        Given: DTO válido
        When: Serializar e deserializar
        Then: Dados devem permanecer íntegros
        """
        # Arrange
        original_data = {
            "vision_statement": "Visão original",
            "problem_statement": "Problema original",
            "target_audience": "Audiência original",
            "value_proposition": "Valor original",
            "constraints": ["Restrição 1", "Restrição 2"]
        }
        
        # Act & Assert
        from streamlit_extension.pages.projetos.dto.product_vision_dto import ProductVisionDTO
        original_dto = ProductVisionDTO.from_dict(original_data)
        serialized = original_dto.to_dict()
        deserialized_dto = ProductVisionDTO.from_dict(serialized)
        
        assert deserialized_dto.vision_statement == original_dto.vision_statement
        assert deserialized_dto.constraints == original_dto.constraints
    
    def test_dto_with_existing_product_vision_state_compatibility(self):
        """
        RED: DTO deve ser compatível com product_vision_state existente
        
        Given: Dados do sistema existente
        When: Criar DTO
        Then: Deve funcionar com funções existentes
        """
        # Arrange
        from streamlit_extension.pages.projetos.domain.product_vision_state import (
            DEFAULT_PV, REQUIRED_FIELDS
        )
        
        # Act & Assert
        from streamlit_extension.pages.projetos.dto.product_vision_dto import ProductVisionDTO
        dto = ProductVisionDTO.from_dict(DEFAULT_PV)
        
        # Deve reconhecer os campos obrigatórios do sistema existente
        for field in REQUIRED_FIELDS:
            assert hasattr(dto, field)


class TestValidationMessages:
    """Testes RED para mensagens de validação - História 1.1"""
    
    def test_validation_messages_should_be_user_friendly(self):
        """
        RED: Mensagens de erro devem ser amigáveis ao usuário
        
        Given: Dados inválidos
        When: Validar
        Then: Mensagens devem ser claras e úteis
        """
        # Arrange
        invalid_data = {
            "vision_statement": "",
            "problem_statement": None,
            # target_audience missing
            "value_proposition": "   ",
            "constraints": []
        }
        
        # Act & Assert
        from streamlit_extension.pages.projetos.dto.product_vision_dto import ProductVisionDTO
        dto = ProductVisionDTO.from_dict(invalid_data)
        errors = dto.get_errors()
        
        # Verificar mensagens em português
        error_text = " ".join(errors)
        assert "obrigatório" in error_text.lower()
        assert "vazio" in error_text.lower() or "em branco" in error_text.lower()


# Fixtures para testes
@pytest.fixture
def valid_product_vision_data() -> Dict[str, Any]:
    """Fixture com dados válidos para testes"""
    return {
        "vision_statement": "Transformar desenvolvimento com TDD",
        "problem_statement": "Dificuldade na adoção de TDD",
        "target_audience": "Desenvolvedores de software",
        "value_proposition": "Framework TDD simplificado",
        "constraints": ["90 dias", "Orçamento R$50k", "Equipe de 3 pessoas"]
    }


@pytest.fixture
def invalid_product_vision_data() -> Dict[str, Any]:
    """Fixture com dados inválidos para testes"""
    return {
        "vision_statement": "",  # Inválido: vazio
        # problem_statement missing - Inválido: faltando
        "target_audience": "   ",  # Inválido: apenas espaços
        "value_proposition": None,  # Inválido: None
        "constraints": ["", "  ", "Válida", "Válida"]  # Problemas: vazias e duplicatas
    }


# Testes TDD para História 1.1 - ProductVisionDTO