"""
Comprehensive unit tests for ProductVision entity (História 1.2 - TASK-1.2.1)

This test suite validates all aspects of the ProductVision domain entity:
- Creation with required fields
- Field validation
- Type checking
- Timestamp initialization
- Error reporting
"""

import pytest
from datetime import datetime
from typing import Any, Dict
from tdd_core.domain.entities.product_vision import ProductVision


class TestProductVisionCreation:
    """Test ProductVision entity creation and initialization."""

    def test_create_valid_product_vision(self):
        """Test creating a ProductVision with all required fields."""
        # Arrange: prepare valid data
        valid_data = {
            "name": "TDD Framework",
            "vision_statement": "Revolucionar desenvolvimento com TDD",
            "target_user": "Desenvolvedores Python",
            "user_problem": "Complexidade em implementar testes efetivos",
            "expected_benefits": "Qualidade de código e produtividade aumentadas",
            "product_description": "Framework completo para TDD com gamificação",
            "success_metrics": "98% cobertura, zero bugs críticos, 50% redução tempo",
            "tech_requirements": "Python 3.11+, SQLite, Streamlit",
            "non_functional_requirements": "Performance <1ms, disponibilidade 99.9%",
            "compliance_requirements": "GDPR, SOC2, ISO 27001",
            "risks": "Curva de aprendizado inicial, resistência à mudança",
            "assumptions": "Equipe experiente em Python, ambiente CI/CD",
            "must_have": "Persistência explícita, validação completa, auditoria",
            "cannot_have": "Campos genéricos sem semântica, acoplamento forte",
            "deliverables": "API REST, CLI, Interface Web, Documentação",
            "market_opportunity": "10M desenvolvedores Python globalmente"
        }

        # Act: create entity
        pv = ProductVision(**valid_data)

        # Assert: verify all fields
        assert pv.name == "TDD Framework"
        assert pv.vision_statement == "Revolucionar desenvolvimento com TDD"
        assert pv.target_user == "Desenvolvedores Python"
        assert pv.user_problem == "Complexidade em implementar testes efetivos"
        assert pv.expected_benefits == "Qualidade de código e produtividade aumentadas"
        assert pv.product_description == "Framework completo para TDD com gamificação"
        assert pv.success_metrics == "98% cobertura, zero bugs críticos, 50% redução tempo"
        assert pv.tech_requirements == "Python 3.11+, SQLite, Streamlit"
        assert pv.non_functional_requirements == "Performance <1ms, disponibilidade 99.9%"
        assert pv.compliance_requirements == "GDPR, SOC2, ISO 27001"
        assert pv.risks == "Curva de aprendizado inicial, resistência à mudança"
        assert pv.assumptions == "Equipe experiente em Python, ambiente CI/CD"
        assert pv.must_have == "Persistência explícita, validação completa, auditoria"
        assert pv.cannot_have == "Campos genéricos sem semântica, acoplamento forte"
        assert pv.deliverables == "API REST, CLI, Interface Web, Documentação"
        assert pv.market_opportunity == "10M desenvolvedores Python globalmente"

    def test_timestamps_auto_initialized(self):
        """Test that timestamps are automatically initialized."""
        # Arrange
        data = self._get_minimal_valid_data()

        # Act
        pv = ProductVision(**data)

        # Assert
        assert pv.created_at is not None
        assert isinstance(pv.created_at, datetime)
        assert pv.updated_at is not None
        assert isinstance(pv.updated_at, datetime)
        assert pv.created_at == pv.updated_at  # Should be equal on creation

    def test_id_optional_on_creation(self):
        """Test that id is optional when creating entity."""
        # Arrange
        data = self._get_minimal_valid_data()

        # Act
        pv = ProductVision(**data)

        # Assert
        assert pv.id is None  # Should be None before persistence

    def test_create_with_explicit_timestamps(self):
        """Test creating entity with explicit timestamps."""
        # Arrange
        data = self._get_minimal_valid_data()
        custom_time = datetime(2025, 1, 1, 12, 0, 0)
        data["created_at"] = custom_time
        data["updated_at"] = custom_time

        # Act
        pv = ProductVision(**data)

        # Assert
        assert pv.created_at == custom_time
        assert pv.updated_at == custom_time


class TestProductVisionValidation:
    """Test ProductVision validation methods."""

    def test_valid_entity_passes_validation(self):
        """Test that a valid entity passes validation."""
        # Arrange
        data = self._get_minimal_valid_data()
        pv = ProductVision(**data)

        # Act
        errors = pv.validate()
        is_valid = pv.is_valid()

        # Assert
        assert len(errors) == 0
        assert is_valid is True

    def test_empty_string_fields_fail_validation(self):
        """Test that empty string fields fail validation."""
        # Arrange
        data = self._get_minimal_valid_data()
        data["name"] = ""  # Empty string
        data["vision_statement"] = "   "  # Whitespace only
        pv = ProductVision(**data)

        # Act
        errors = pv.validate()
        is_valid = pv.is_valid()

        # Assert
        assert len(errors) == 2
        assert "name is required and cannot be empty" in errors
        assert "vision_statement is required and cannot be empty" in errors
        assert is_valid is False

    def test_all_required_fields_validated(self):
        """Test that all 16 required fields are validated."""
        # Arrange - create entity with all empty strings
        data = {field: "" for field in self._get_required_fields()}
        pv = ProductVision(**data)

        # Act
        errors = pv.validate()

        # Assert
        assert len(errors) == 16
        for field in self._get_required_fields():
            assert f"{field} is required and cannot be empty" in errors

    def test_invalid_type_fields_fail_validation(self):
        """Test that non-string types in required fields fail validation."""
        # Arrange
        data = self._get_minimal_valid_data()
        data["name"] = 123  # Integer instead of string
        data["vision_statement"] = ["list", "value"]  # List instead of string
        pv = ProductVision(**data)

        # Act
        errors = pv.validate()

        # Assert
        assert any("name has invalid type: int" in e for e in errors)
        assert any("vision_statement has invalid type: list" in e for e in errors)

    def test_none_values_fail_validation(self):
        """Test that None values in required fields fail validation."""
        # Arrange
        data = self._get_minimal_valid_data()
        data["name"] = None
        data["target_user"] = None
        pv = ProductVision(**data)

        # Act
        errors = pv.validate()

        # Assert
        assert "name is required and cannot be empty" in errors
        assert "target_user is required and cannot be empty" in errors


class TestProductVisionEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_long_strings_accepted(self):
        """Test that very long strings are accepted."""
        # Arrange
        data = self._get_minimal_valid_data()
        long_text = "A" * 10000  # 10k characters
        data["vision_statement"] = long_text

        # Act
        pv = ProductVision(**data)

        # Assert
        assert pv.vision_statement == long_text
        assert pv.is_valid() is True

    def test_unicode_characters_accepted(self):
        """Test that unicode characters are properly handled."""
        # Arrange
        data = self._get_minimal_valid_data()
        data["name"] = "Projeto 日本語 🚀"
        data["target_user"] = "Développeurs français"

        # Act
        pv = ProductVision(**data)

        # Assert
        assert pv.name == "Projeto 日本語 🚀"
        assert pv.target_user == "Développeurs français"
        assert pv.is_valid() is True

    def test_multiline_strings_accepted(self):
        """Test that multiline strings are accepted."""
        # Arrange
        data = self._get_minimal_valid_data()
        multiline = """Line 1
        Line 2
        Line 3"""
        data["product_description"] = multiline

        # Act
        pv = ProductVision(**data)

        # Assert
        assert pv.product_description == multiline
        assert pv.is_valid() is True

    def test_special_characters_in_strings(self):
        """Test that special characters are handled correctly."""
        # Arrange
        data = self._get_minimal_valid_data()
        special = "Test with 'quotes' and \"double quotes\" & <tags>"
        data["risks"] = special

        # Act
        pv = ProductVision(**data)

        # Assert
        assert pv.risks == special
        assert pv.is_valid() is True


class TestProductVisionMethods:
    """Test ProductVision methods behavior."""

    def test_validate_returns_list_of_strings(self):
        """Test that validate() returns a list of error strings."""
        # Arrange
        data = self._get_minimal_valid_data()
        data["name"] = ""
        pv = ProductVision(**data)

        # Act
        errors = pv.validate()

        # Assert
        assert isinstance(errors, list)
        assert all(isinstance(e, str) for e in errors)
        assert len(errors) > 0

    def test_is_valid_returns_boolean(self):
        """Test that is_valid() returns a boolean."""
        # Arrange
        data = self._get_minimal_valid_data()
        pv_valid = ProductVision(**data)

        data["name"] = ""
        pv_invalid = ProductVision(**data)

        # Act & Assert
        assert pv_valid.is_valid() is True
        assert pv_invalid.is_valid() is False
        assert isinstance(pv_valid.is_valid(), bool)
        assert isinstance(pv_invalid.is_valid(), bool)

    def test_validate_empty_list_when_valid(self):
        """Test that validate() returns empty list when entity is valid."""
        # Arrange
        data = self._get_minimal_valid_data()
        pv = ProductVision(**data)

        # Act
        errors = pv.validate()

        # Assert
        assert errors == []
        assert len(errors) == 0


class TestProductVisionDataclass:
    """Test dataclass-specific behavior."""

    def test_equality_comparison(self):
        """Test that two entities with same data are equal."""
        # Arrange
        data = self._get_minimal_valid_data()
        pv1 = ProductVision(**data)
        pv2 = ProductVision(**data)

        # Act & Assert
        # Note: They won't be equal because timestamps are different
        assert pv1 != pv2  # Different timestamps

        # But if we set same timestamps, they should be equal
        pv2.created_at = pv1.created_at
        pv2.updated_at = pv1.updated_at
        assert pv1 == pv2

    def test_field_modification(self):
        """Test that fields can be modified after creation."""
        # Arrange
        data = self._get_minimal_valid_data()
        pv = ProductVision(**data)

        # Act
        pv.name = "Modified Name"
        pv.vision_statement = "Modified Vision"

        # Assert
        assert pv.name == "Modified Name"
        assert pv.vision_statement == "Modified Vision"
        assert pv.is_valid() is True

    def test_repr_contains_key_info(self):
        """Test that repr contains key information."""
        # Arrange
        data = self._get_minimal_valid_data()
        pv = ProductVision(**data)

        # Act
        repr_str = repr(pv)

        # Assert
        assert "ProductVision" in repr_str
        assert "name='Test Product'" in repr_str


# Helper methods for test classes
def _get_minimal_valid_data(self) -> Dict[str, Any]:
    """Get minimal valid data for creating a ProductVision."""
    return {
        "name": "Test Product",
        "vision_statement": "Test vision",
        "target_user": "Test users",
        "user_problem": "Test problem",
        "expected_benefits": "Test benefits",
        "product_description": "Test description",
        "success_metrics": "Test metrics",
        "tech_requirements": "Test tech",
        "non_functional_requirements": "Test NFR",
        "compliance_requirements": "Test compliance",
        "risks": "Test risks",
        "assumptions": "Test assumptions",
        "must_have": "Test must have",
        "cannot_have": "Test cannot have",
        "deliverables": "Test deliverables",
        "market_opportunity": "Test opportunity"
    }

def _get_required_fields(self) -> list:
    """Get list of required field names."""
    return [
        "name", "vision_statement", "target_user", "user_problem",
        "expected_benefits", "product_description", "success_metrics",
        "tech_requirements", "non_functional_requirements",
        "compliance_requirements", "risks", "assumptions",
        "must_have", "cannot_have", "deliverables", "market_opportunity"
    ]


# Add helper methods to all test classes
for cls in [TestProductVisionCreation, TestProductVisionValidation,
            TestProductVisionEdgeCases, TestProductVisionMethods,
            TestProductVisionDataclass]:
    cls._get_minimal_valid_data = _get_minimal_valid_data
    cls._get_required_fields = _get_required_fields


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])