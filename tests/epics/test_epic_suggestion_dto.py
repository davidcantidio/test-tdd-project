"""
🧪 Testes RED para EpicSuggestionDTO - História 1.2

Este arquivo implementa testes TDD para validação do DTO de Sugestão de Épicos
seguindo os critérios de aceitação da História 1.2:

Aceitação:
- Estrutura: EpicSuggestionDTO(title, rationale, tags[], confidence:0..1, source="ai|heuristic")
- Serializa/deserializa (dict) sem perda

Casos de teste:
- DTO completo e válido → sucesso
- Campo obrigatório faltando → falha com mensagem clara
- String vazia em campo obrigatório → falha
- Confidence fora de range (< 0.0 ou > 1.0) → falha  
- Source inválida (não "ai" nem "heuristic") → falha
- Tags duplicadas → normalização automática
- Tags com espaços → trim automático
- Tags vazias → remoção automática
- Serialização roundtrip → sem perda de dados
"""

import pytest
from typing import Dict, Any, List
from unittest.mock import Mock


class TestEpicSuggestionDTO:
    """Testes RED para EpicSuggestionDTO - TDD História 1.2"""
    
    def test_valid_complete_dto_should_pass_validation(self):
        """
        RED: DTO completo e válido deve passar na validação
        
        Given: Dados completos e válidos de epic suggestion
        When: Criar EpicSuggestionDTO
        Then: Validação deve ser bem-sucedida
        """
        # Arrange
        valid_data = {
            "title": "Autenticação de Usuários",
            "rationale": "Sistema precisa de login seguro e confiável para proteger dados dos usuários",
            "tags": ["segurança", "login", "backend", "autenticação"],
            "confidence": 0.85,
            "source": "ai"
        }
        
        # Act & Assert
        from streamlit_extension.pages.projetos.dto.epic_suggestion_dto import EpicSuggestionDTO
        dto = EpicSuggestionDTO.from_dict(valid_data)
        assert dto.is_valid() is True
        assert dto.get_errors() == []
        assert dto.title == "Autenticação de Usuários"
        assert dto.confidence == 0.85
        assert dto.source == "ai"
    
    def test_missing_required_field_should_fail_validation(self):
        """
        RED: Campo obrigatório faltando deve falhar na validação
        
        Given: Dados sem campo obrigatório (title)
        When: Criar EpicSuggestionDTO
        Then: Validação deve falhar com mensagem clara
        """
        # Arrange
        incomplete_data = {
            # "title": missing!
            "rationale": "Justificativa válida",
            "tags": ["tag1", "tag2"],
            "confidence": 0.8,
            "source": "heuristic"
        }
        
        # Act & Assert
        from streamlit_extension.pages.projetos.dto.epic_suggestion_dto import EpicSuggestionDTO
        dto = EpicSuggestionDTO.from_dict(incomplete_data)
        assert dto.is_valid() is False
        errors = dto.get_errors()
        assert any("título" in error.lower() for error in errors)
        assert any("obrigatório" in error.lower() for error in errors)
    
    def test_empty_string_field_should_fail_validation(self):
        """
        RED: String vazia em campo obrigatório deve falhar na validação
        
        Given: Campo obrigatório com string vazia
        When: Criar EpicSuggestionDTO
        Then: Validação deve falhar
        """
        # Arrange
        data_with_empty_field = {
            "title": "",  # String vazia
            "rationale": "Justificativa válida",
            "tags": ["tag1", "tag2"],
            "confidence": 0.7,
            "source": "ai"
        }
        
        # Act & Assert
        from streamlit_extension.pages.projetos.dto.epic_suggestion_dto import EpicSuggestionDTO
        dto = EpicSuggestionDTO.from_dict(data_with_empty_field)
        assert dto.is_valid() is False
        errors = dto.get_errors()
        assert any("título" in error.lower() for error in errors)
        assert any("vazio" in error.lower() or "em branco" in error.lower() for error in errors)
    
    def test_whitespace_only_field_should_fail_validation(self):
        """
        RED: Campo com apenas espaços em branco deve falhar na validação
        
        Given: Campo obrigatório com apenas whitespace
        When: Criar EpicSuggestionDTO
        Then: Validação deve falhar
        """
        # Arrange
        data_with_whitespace_field = {
            "title": "Título válido",
            "rationale": "   ",  # Apenas espaços
            "tags": ["tag1"],
            "confidence": 0.6,
            "source": "heuristic"
        }
        
        # Act & Assert
        from streamlit_extension.pages.projetos.dto.epic_suggestion_dto import EpicSuggestionDTO
        dto = EpicSuggestionDTO.from_dict(data_with_whitespace_field)
        assert dto.is_valid() is False
        errors = dto.get_errors()
        assert any("justificativa" in error.lower() or "rationale" in error.lower() for error in errors)


class TestConfidenceValidation:
    """Testes RED para validação do campo confidence - História 1.2"""
    
    def test_confidence_below_zero_should_fail_validation(self):
        """
        RED: Confidence abaixo de 0.0 deve falhar na validação
        
        Given: Confidence < 0.0
        When: Criar EpicSuggestionDTO
        Then: Validação deve falhar
        """
        # Arrange
        data_with_invalid_confidence = {
            "title": "Título válido",
            "rationale": "Justificativa válida",
            "tags": ["tag1"],
            "confidence": -0.1,  # Inválido: < 0.0
            "source": "ai"
        }
        
        # Act & Assert
        from streamlit_extension.pages.projetos.dto.epic_suggestion_dto import EpicSuggestionDTO
        dto = EpicSuggestionDTO.from_dict(data_with_invalid_confidence)
        assert dto.is_valid() is False
        errors = dto.get_errors()
        assert any("confidence" in error.lower() or "confiança" in error.lower() for error in errors)
        assert any("0.0" in error and "1.0" in error for error in errors)
    
    def test_confidence_above_one_should_fail_validation(self):
        """
        RED: Confidence acima de 1.0 deve falhar na validação
        
        Given: Confidence > 1.0
        When: Criar EpicSuggestionDTO
        Then: Validação deve falhar
        """
        # Arrange
        data_with_invalid_confidence = {
            "title": "Título válido",
            "rationale": "Justificativa válida",
            "tags": ["tag1"],
            "confidence": 1.5,  # Inválido: > 1.0
            "source": "heuristic"
        }
        
        # Act & Assert
        from streamlit_extension.pages.projetos.dto.epic_suggestion_dto import EpicSuggestionDTO
        dto = EpicSuggestionDTO.from_dict(data_with_invalid_confidence)
        assert dto.is_valid() is False
        errors = dto.get_errors()
        assert any("confidence" in error.lower() or "confiança" in error.lower() for error in errors)
        assert any("0.0" in error and "1.0" in error for error in errors)
    
    def test_confidence_boundary_values_should_be_valid(self):
        """
        RED: Valores limítrofes de confidence (0.0 e 1.0) devem ser válidos
        
        Given: Confidence exatamente 0.0 ou 1.0
        When: Criar EpicSuggestionDTO
        Then: Validação deve passar
        """
        # Test confidence = 0.0
        data_confidence_zero = {
            "title": "Título válido",
            "rationale": "Justificativa válida",
            "tags": ["tag1"],
            "confidence": 0.0,  # Válido: limite inferior
            "source": "ai"
        }
        
        # Test confidence = 1.0
        data_confidence_one = {
            "title": "Título válido",
            "rationale": "Justificativa válida",
            "tags": ["tag1"],
            "confidence": 1.0,  # Válido: limite superior
            "source": "heuristic"
        }
        
        # Act & Assert
        from streamlit_extension.pages.projetos.dto.epic_suggestion_dto import EpicSuggestionDTO
        
        dto_zero = EpicSuggestionDTO.from_dict(data_confidence_zero)
        assert dto_zero.is_valid() is True
        assert dto_zero.confidence == 0.0
        
        dto_one = EpicSuggestionDTO.from_dict(data_confidence_one)
        assert dto_one.is_valid() is True
        assert dto_one.confidence == 1.0


class TestSourceValidation:
    """Testes RED para validação do campo source - História 1.2"""
    
    def test_invalid_source_should_fail_validation(self):
        """
        RED: Source inválida (não "ai" nem "heuristic") deve falhar
        
        Given: Source com valor inválido
        When: Criar EpicSuggestionDTO
        Then: Validação deve falhar
        """
        # Arrange
        data_with_invalid_source = {
            "title": "Título válido",
            "rationale": "Justificativa válida",
            "tags": ["tag1"],
            "confidence": 0.8,
            "source": "manual"  # Inválido: deve ser "ai" ou "heuristic"
        }
        
        # Act & Assert
        from streamlit_extension.pages.projetos.dto.epic_suggestion_dto import EpicSuggestionDTO
        dto = EpicSuggestionDTO.from_dict(data_with_invalid_source)
        assert dto.is_valid() is False
        errors = dto.get_errors()
        assert any("source" in error.lower() or "fonte" in error.lower() for error in errors)
        assert any("ai" in error and "heuristic" in error for error in errors)
    
    def test_valid_sources_should_pass_validation(self):
        """
        RED: Sources válidas ("ai" e "heuristic") devem passar
        
        Given: Source com valores válidos
        When: Criar EpicSuggestionDTO
        Then: Validação deve passar
        """
        # Test source = "ai"
        data_ai_source = {
            "title": "Título válido",
            "rationale": "Justificativa válida",
            "tags": ["tag1"],
            "confidence": 0.8,
            "source": "ai"
        }
        
        # Test source = "heuristic"
        data_heuristic_source = {
            "title": "Título válido", 
            "rationale": "Justificativa válida",
            "tags": ["tag1"],
            "confidence": 0.9,
            "source": "heuristic"
        }
        
        # Act & Assert
        from streamlit_extension.pages.projetos.dto.epic_suggestion_dto import EpicSuggestionDTO
        
        dto_ai = EpicSuggestionDTO.from_dict(data_ai_source)
        assert dto_ai.is_valid() is True
        assert dto_ai.source == "ai"
        
        dto_heuristic = EpicSuggestionDTO.from_dict(data_heuristic_source)
        assert dto_heuristic.is_valid() is True
        assert dto_heuristic.source == "heuristic"


class TestTagsNormalization:
    """Testes RED para normalização de tags - História 1.2"""
    
    def test_duplicate_tags_should_be_normalized(self):
        """
        RED: Tags duplicadas devem ser removidas automaticamente
        
        Given: Lista de tags com duplicatas
        When: Normalizar tags
        Then: Duplicatas devem ser removidas
        """
        # Arrange
        data_with_duplicates = {
            "title": "Título válido",
            "rationale": "Justificativa válida",
            "tags": ["backend", "segurança", "backend", "api", "segurança"],
            "confidence": 0.8,
            "source": "ai"
        }
        
        # Act & Assert
        from streamlit_extension.pages.projetos.dto.epic_suggestion_dto import EpicSuggestionDTO
        dto = EpicSuggestionDTO.from_dict(data_with_duplicates)
        assert dto.is_valid() is True
        assert len(dto.tags) == 3  # Apenas tags únicas
        assert "backend" in dto.tags
        assert "segurança" in dto.tags
        assert "api" in dto.tags
    
    def test_tags_with_whitespace_should_be_trimmed(self):
        """
        RED: Tags com espaços devem ser limpas (trim)
        
        Given: Tags com espaços no início/fim
        When: Normalizar tags
        Then: Espaços devem ser removidos
        """
        # Arrange
        tags_with_whitespace = ["  backend  ", " frontend", "database ", "  api  "]
        
        data = {
            "title": "Título válido",
            "rationale": "Justificativa válida",
            "tags": tags_with_whitespace,
            "confidence": 0.7,
            "source": "heuristic"
        }
        
        # Act & Assert
        from streamlit_extension.pages.projetos.dto.epic_suggestion_dto import EpicSuggestionDTO
        dto = EpicSuggestionDTO.from_dict(data)
        assert dto.is_valid() is True
        
        # Verificar que não há espaços extras
        for tag in dto.tags:
            assert tag == tag.strip()
        
        assert "backend" in dto.tags
        assert "frontend" in dto.tags
        assert "database" in dto.tags
        assert "api" in dto.tags
    
    def test_empty_tags_should_be_removed(self):
        """
        RED: Tags vazias devem ser removidas automaticamente
        
        Given: Lista com tags vazias
        When: Normalizar tags
        Then: Entradas vazias devem ser removidas
        """
        # Arrange
        tags_with_empty = ["válida", "", "  ", "outra-válida", None]
        
        data = {
            "title": "Título válido",
            "rationale": "Justificativa válida",
            "tags": tags_with_empty,
            "confidence": 0.6,
            "source": "ai"
        }
        
        # Act & Assert
        from streamlit_extension.pages.projetos.dto.epic_suggestion_dto import EpicSuggestionDTO
        dto = EpicSuggestionDTO.from_dict(data)
        assert dto.is_valid() is True
        assert len(dto.tags) == 2
        assert "válida" in dto.tags
        assert "outra-válida" in dto.tags
        assert "" not in dto.tags
    
    def test_tags_normalization_comprehensive(self):
        """
        RED: Normalização completa - duplicatas, espaços e vazias
        
        Given: Lista com todos os problemas (duplicatas, espaços, vazias)
        When: Normalizar tags
        Then: Lista limpa e única
        """
        # Arrange
        messy_tags = [
            "  backend  ",
            "frontend",
            "",
            "  backend",  # Duplicata com espaço
            "   ",  # Apenas espaços
            "database",
            "frontend ",  # Duplicata com espaço final
            None
        ]
        
        data = {
            "title": "Título válido",
            "rationale": "Justificativa válida",
            "tags": messy_tags,
            "confidence": 0.9,
            "source": "heuristic"
        }
        
        # Act & Assert
        from streamlit_extension.pages.projetos.dto.epic_suggestion_dto import EpicSuggestionDTO
        dto = EpicSuggestionDTO.from_dict(data)
        assert dto.is_valid() is True
        assert len(dto.tags) == 3  # Apenas as 3 únicas
        assert "backend" in dto.tags
        assert "frontend" in dto.tags
        assert "database" in dto.tags


class TestEpicSuggestionDTOIntegration:
    """Testes RED para integração completa do DTO - História 1.2"""
    
    def test_dto_serialization_roundtrip(self):
        """
        RED: DTO deve serializar/deserializar sem perda de dados
        
        Given: DTO válido
        When: Serializar e deserializar
        Then: Dados devem permanecer íntegros
        """
        # Arrange
        original_data = {
            "title": "Sistema de Notificações",
            "rationale": "Usuários precisam ser notificados sobre eventos importantes no sistema",
            "tags": ["notificação", "email", "push", "tempo-real"],
            "confidence": 0.92,
            "source": "ai"
        }
        
        # Act & Assert
        from streamlit_extension.pages.projetos.dto.epic_suggestion_dto import EpicSuggestionDTO
        original_dto = EpicSuggestionDTO.from_dict(original_data)
        serialized = original_dto.to_dict()
        deserialized_dto = EpicSuggestionDTO.from_dict(serialized)
        
        assert deserialized_dto.title == original_dto.title
        assert deserialized_dto.rationale == original_dto.rationale
        assert deserialized_dto.tags == original_dto.tags
        assert deserialized_dto.confidence == original_dto.confidence
        assert deserialized_dto.source == original_dto.source
        assert deserialized_dto.is_valid() is True


class TestValidationMessages:
    """Testes RED para mensagens de validação - História 1.2"""
    
    def test_validation_messages_should_be_user_friendly(self):
        """
        RED: Mensagens de erro devem ser amigáveis ao usuário
        
        Given: Dados inválidos
        When: Validar
        Then: Mensagens devem ser claras e úteis em português
        """
        # Arrange
        invalid_data = {
            "title": "",
            "rationale": None,
            # tags missing
            "confidence": 2.0,  # > 1.0
            "source": "invalid"
        }
        
        # Act & Assert
        from streamlit_extension.pages.projetos.dto.epic_suggestion_dto import EpicSuggestionDTO
        dto = EpicSuggestionDTO.from_dict(invalid_data)
        errors = dto.get_errors()
        
        # Verificar mensagens em português
        error_text = " ".join(errors)
        assert "obrigatório" in error_text.lower() or "título" in error_text.lower()
        assert "confidence" in error_text.lower() or "confiança" in error_text.lower()
        assert "source" in error_text.lower() or "fonte" in error_text.lower()


# Fixtures para testes
@pytest.fixture
def valid_epic_suggestion_data() -> Dict[str, Any]:
    """Fixture com dados válidos para testes"""
    return {
        "title": "Gerenciamento de Usuários",
        "rationale": "Sistema precisa de funcionalidade robusta para criar, editar e gerenciar usuários",
        "tags": ["usuários", "crud", "admin", "permissões"],
        "confidence": 0.88,
        "source": "ai"
    }


@pytest.fixture
def invalid_epic_suggestion_data() -> Dict[str, Any]:
    """Fixture com dados inválidos para testes"""
    return {
        "title": "",  # Inválido: vazio
        # rationale missing - Inválido: faltando
        "tags": ["", "  ", "válida", "válida"],  # Problemas: vazias e duplicatas
        "confidence": 1.5,  # Inválido: > 1.0
        "source": "manual"  # Inválido: não é "ai" nem "heuristic"
    }


# Testes TDD para História 1.2 - EpicSuggestionDTO