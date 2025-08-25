"""
Test suite for JSON Fields Handler (FASE 3.1)

Comprehensive test coverage for JSON field serialization, deserialization,
validation, and query optimization functionality.

Target: ≥95% code coverage
"""

import pytest
import json
from duration_system.json_handler import (
    JsonFieldHandler,
    JsonFieldType,
    JsonValidationError,
    serialize_goals,
    deserialize_goals,
    serialize_definition_of_done,
    deserialize_definition_of_done,
    serialize_labels,
    deserialize_labels,
    validate_epic_data,
    EpicJsonHandler
)


class TestJsonFieldHandler:
    """Test suite for JsonFieldHandler class"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.handler = JsonFieldHandler()
        self.lenient_handler = JsonFieldHandler(strict_validation=False)
        self.small_handler = JsonFieldHandler(max_field_size=100)
    
    # ==================================================================================
    # SERIALIZATION TESTS
    # ==================================================================================
    
    def test_serialize_goals_valid_list(self):
        """Test serializing valid goals list"""
        goals = [
            "Implementar captura de warnings em tempo real",
            "Criar interface interativa para decisões",
            "Persistir decisões em SQLite"
        ]
        
        result = self.handler.serialize_field(goals, JsonFieldType.GOALS)
        
        assert isinstance(result, str)
        # Should be valid JSON
        parsed = json.loads(result)
        assert parsed == goals
    
    def test_serialize_definition_of_done_valid_list(self):
        """Test serializing valid definition of done list"""
        dod = [
            "Todos os testes escritos antes da implementação e cobertura ≥ 90%",
            "As fases red-green-refactor são seguidas para cada funcionalidade",
            "Sistema captura, persiste e aplica decisões sem exceder 2 chamadas de API"
        ]
        
        result = self.handler.serialize_field(dod, JsonFieldType.DEFINITION_OF_DONE)
        
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed == dod
    
    def test_serialize_labels_valid_list(self):
        """Test serializing valid labels list"""
        labels = ["tdd", "interactive-system", "warnings", "database"]
        
        result = self.handler.serialize_field(labels, JsonFieldType.LABELS)
        
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed == labels
    
    def test_serialize_metadata_valid_object(self):
        """Test serializing valid metadata object"""
        metadata = {
            "created_by": "user1",
            "priority_level": 3,
            "tags": {"urgency": "high", "complexity": "medium"}
        }
        
        result = self.handler.serialize_field(metadata, JsonFieldType.METADATA)
        
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed == metadata
    
    def test_serialize_none_value(self):
        """Test serializing None value"""
        result = self.handler.serialize_field(None, JsonFieldType.GOALS)
        assert result == "{}"
    
    def test_serialize_field_too_large(self):
        """Test error when field exceeds size limit"""
        large_data = ["very long string" * 100] * 10
        
        with pytest.raises(JsonValidationError) as exc_info:
            self.small_handler.serialize_field(large_data, JsonFieldType.GOALS)
        # Could fail due to size limit or validation rules
        assert "too large" in str(exc_info.value) or "cannot exceed" in str(exc_info.value)
    
    def test_serialize_invalid_json_data(self):
        """Test error with non-serializable data"""
        invalid_data = {"key": set([1, 2, 3])}  # sets are not JSON serializable
        
        with pytest.raises(JsonValidationError) as exc_info:
            self.handler.serialize_field(invalid_data, JsonFieldType.METADATA)
        assert "serialize JSON" in str(exc_info.value)
    
    # ==================================================================================
    # DESERIALIZATION TESTS
    # ==================================================================================
    
    def test_deserialize_valid_json_string(self):
        """Test deserializing valid JSON string"""
        goals = ["Goal 1", "Goal 2", "Goal 3"]
        json_str = json.dumps(goals)
        
        result = self.handler.deserialize_field(json_str, JsonFieldType.GOALS)
        assert result == goals
    
    def test_deserialize_empty_string(self):
        """Test deserializing empty string returns default"""
        result = self.handler.deserialize_field("", JsonFieldType.GOALS)
        assert result == []
    
    def test_deserialize_null_values(self):
        """Test deserializing null/empty values"""
        test_cases = ["", "{}", "[]", "null", "   "]
        
        for empty_value in test_cases:
            result = self.handler.deserialize_field(empty_value, JsonFieldType.GOALS)
            assert result == []
    
    def test_deserialize_with_custom_default(self):
        """Test deserializing with custom default value"""
        result = self.handler.deserialize_field("", JsonFieldType.GOALS, default=["default"])
        assert result == ["default"]
    
    def test_deserialize_invalid_json_strict(self):
        """Test deserializing invalid JSON with strict validation"""
        invalid_json = '{"incomplete": json'
        
        with pytest.raises(JsonValidationError) as exc_info:
            self.handler.deserialize_field(invalid_json, JsonFieldType.METADATA)
        assert "Invalid JSON format" in str(exc_info.value)
    
    def test_deserialize_invalid_json_lenient(self):
        """Test deserializing invalid JSON with lenient validation"""
        invalid_json = '{"incomplete": json'
        
        result = self.lenient_handler.deserialize_field(invalid_json, JsonFieldType.METADATA)
        assert result == {}  # Should return default
    
    # ==================================================================================
    # VALIDATION TESTS
    # ==================================================================================
    
    def test_validate_goals_structure_valid(self):
        """Test validating valid goals structure"""
        valid_goals = [
            "Implementar funcionalidade X",
            "Garantir performance adequada",
            "Manter cobertura de testes"
        ]
        
        # Should not raise exception
        self.handler._validate_structure(valid_goals, JsonFieldType.GOALS)
    
    def test_validate_goals_structure_too_short(self):
        """Test validating goals with strings too short"""
        invalid_goals = ["abc"]  # Too short (min 5 chars)
        
        with pytest.raises(JsonValidationError) as exc_info:
            self.handler._validate_structure(invalid_goals, JsonFieldType.GOALS)
        assert "at least 5 characters" in str(exc_info.value)
    
    def test_validate_goals_structure_not_list(self):
        """Test validating goals that is not a list"""
        invalid_goals = "not a list"
        
        with pytest.raises(JsonValidationError) as exc_info:
            self.handler._validate_structure(invalid_goals, JsonFieldType.GOALS)
        assert "Expected list" in str(exc_info.value)
    
    def test_validate_labels_pattern(self):
        """Test validating labels with pattern requirements"""
        valid_labels = ["tdd", "performance", "test-driven", "api_integration"]
        invalid_labels = ["TDD", "test space", "test@invalid"]
        
        # Valid labels should pass
        self.handler._validate_structure(valid_labels, JsonFieldType.LABELS)
        
        # Invalid labels should fail
        with pytest.raises(JsonValidationError):
            self.handler._validate_structure(invalid_labels, JsonFieldType.LABELS)
    
    def test_validate_definition_of_done_min_length(self):
        """Test validating definition of done with minimum length requirement"""
        valid_dod = ["Testes implementados e cobertura ≥ 90% em todos os módulos"]
        invalid_dod = ["Short"]  # Too short (min 10 chars)
        
        # Valid should pass
        self.handler._validate_structure(valid_dod, JsonFieldType.DEFINITION_OF_DONE)
        
        # Invalid should fail
        with pytest.raises(JsonValidationError) as exc_info:
            self.handler._validate_structure(invalid_dod, JsonFieldType.DEFINITION_OF_DONE)
        assert "at least 10 characters" in str(exc_info.value)
    
    def test_validate_metadata_object(self):
        """Test validating metadata object structure"""
        valid_metadata = {
            "created_by": "user123",
            "priority_level": 3
        }
        invalid_metadata = {
            "priority_level": "not_integer"  # Should be integer
        }
        
        # Valid should pass
        self.handler._validate_structure(valid_metadata, JsonFieldType.METADATA)
        
        # Invalid should fail
        with pytest.raises(JsonValidationError):
            self.handler._validate_structure(invalid_metadata, JsonFieldType.METADATA)
    
    # ==================================================================================
    # EPIC VALIDATION TESTS
    # ==================================================================================
    
    def test_validate_epic_json_fields_complete_valid(self):
        """Test validating complete valid epic structure"""
        epic_data = {
            "epic": {
                "id": "3",
                "name": "Test Epic",
                "goals": [
                    "Implementar funcionalidade principal",
                    "Garantir performance adequada"
                ],
                "definition_of_done": [
                    "Todos os testes implementados com cobertura ≥ 90%",
                    "Performance otimizada e documentada"
                ],
                "labels": ["tdd", "performance", "testing"]
            },
            "tasks": [
                {
                    "id": "3.1",
                    "title": "Task 1",
                    "test_specs": {
                        "red_phase": "Write failing test for main functionality",
                        "green_phase": "Implement minimum code to pass test", 
                        "refactor_phase": "Clean up and optimize implementation"
                    }
                }
            ]
        }
        
        result = self.handler.validate_epic_json_fields(epic_data)
        
        assert result["is_valid"] is True
        assert len(result["errors"]) == 0
        assert result["validated_fields"]["goals"] == 2
        assert result["validated_fields"]["definition_of_done"] == 2
        assert result["validated_fields"]["labels"] == 3
        assert result["validated_fields"]["tasks"] == 1
    
    def test_validate_epic_json_fields_invalid_goals(self):
        """Test validating epic with invalid goals"""
        epic_data = {
            "epic": {
                "goals": "not a list"  # Should be list
            }
        }
        
        result = self.handler.validate_epic_json_fields(epic_data)
        
        assert result["is_valid"] is False
        assert any("Goals field is not a list" in error for error in result["errors"])
    
    def test_validate_epic_json_fields_warnings(self):
        """Test validating epic that produces warnings but is still valid"""
        epic_data = {
            "epic": {
                "goals": ["abc"],  # Too short, will produce warning
                "labels": ["tdd", "INVALID_LABEL"]  # Second label invalid
            }
        }
        
        result = self.handler.validate_epic_json_fields(epic_data)
        
        assert result["is_valid"] is True  # Still valid overall
        assert len(result["warnings"]) > 0
    
    def test_validate_epic_json_fields_missing_epic_section(self):
        """Test validating data without epic section"""
        epic_data = {"tasks": []}
        
        result = self.handler.validate_epic_json_fields(epic_data)
        
        assert result["is_valid"] is True  # No epic section to validate
        assert result["validated_fields"]["tasks"] == 0
    
    # ==================================================================================
    # UTILITY FUNCTION TESTS
    # ==================================================================================
    
    def test_extract_searchable_text(self):
        """Test extracting searchable text from JSON data"""
        json_data = {
            "goals": ["Implement feature X", "Optimize performance"],
            "metadata": {
                "author": "developer1",
                "tags": {"priority": "high"}
            }
        }
        
        searchable_text = self.handler.extract_searchable_text(json_data)
        
        assert len(searchable_text) > 0
        assert any("Implement feature X" in text for text in searchable_text)
        assert any("developer1" in text for text in searchable_text)
        assert any("high" in text for text in searchable_text)
    
    def test_merge_json_fields_goals(self):
        """Test merging two goals JSON fields"""
        goals1_json = '["Goal A", "Goal B"]'
        goals2_json = '["Goal B", "Goal C"]'  # Goal B is duplicate
        
        merged = self.handler.merge_json_fields(goals1_json, goals2_json, JsonFieldType.GOALS)
        merged_data = json.loads(merged)
        
        assert len(merged_data) == 3  # No duplicates
        assert "Goal A" in merged_data
        assert "Goal B" in merged_data
        assert "Goal C" in merged_data
    
    def test_merge_json_fields_metadata(self):
        """Test merging two metadata JSON fields"""
        meta1_json = '{"created_by": "user1", "priority": 1}'
        meta2_json = '{"priority": 2, "tags": ["important"]}'  # priority will be overridden
        
        merged = self.handler.merge_json_fields(meta1_json, meta2_json, JsonFieldType.METADATA)
        merged_data = json.loads(merged)
        
        assert merged_data["created_by"] == "user1"
        assert merged_data["priority"] == 2  # Second value wins
        assert merged_data["tags"] == ["important"]
    
    def test_merge_json_fields_empty_fields(self):
        """Test merging with empty fields"""
        goals_json = '["Goal A"]'
        empty_json = ""
        
        merged = self.handler.merge_json_fields(goals_json, empty_json, JsonFieldType.GOALS)
        assert merged == goals_json  # Should return non-empty field
    
    def test_create_database_json_query_contains(self):
        """Test creating database query for contains search"""
        query, params = self.handler.create_database_json_query(
            "goals", "performance", "contains"
        )
        
        assert "JSON_EXTRACT(goals" in query
        assert "LIKE ?" in query
        assert params == ["%performance%"]
    
    def test_create_database_json_query_exact(self):
        """Test creating database query for exact search"""
        query, params = self.handler.create_database_json_query(
            "labels", "tdd", "exact"
        )
        
        assert "JSON_EXTRACT(labels" in query
        assert "= ?" in query
        assert params == ["tdd"]
    
    def test_create_database_json_query_invalid_type(self):
        """Test error with invalid query type"""
        with pytest.raises(ValueError) as exc_info:
            self.handler.create_database_json_query("field", "term", "invalid_type")
        assert "Unsupported query type" in str(exc_info.value)


# ==================================================================================
# CONVENIENCE FUNCTION TESTS
# ==================================================================================

class TestConvenienceFunctions:
    """Test suite for convenience functions"""
    
    def test_serialize_goals_convenience(self):
        """Test goals serialization convenience function"""
        goals = ["Goal 1", "Goal 2"]
        result = serialize_goals(goals)
        
        assert isinstance(result, str)
        assert json.loads(result) == goals
    
    def test_deserialize_goals_convenience(self):
        """Test goals deserialization convenience function"""
        goals_json = '["Goal 1", "Goal 2"]'
        result = deserialize_goals(goals_json)
        
        assert result == ["Goal 1", "Goal 2"]
    
    def test_serialize_definition_of_done_convenience(self):
        """Test definition of done serialization convenience function"""
        dod = ["Criterion 1 with sufficient length", "Criterion 2 with sufficient length"]
        result = serialize_definition_of_done(dod)
        
        assert isinstance(result, str)
        assert json.loads(result) == dod
    
    def test_deserialize_definition_of_done_convenience(self):
        """Test definition of done deserialization convenience function"""
        dod_json = '["Criterion 1", "Criterion 2"]'
        result = deserialize_definition_of_done(dod_json)
        
        assert result == ["Criterion 1", "Criterion 2"]
    
    def test_serialize_labels_convenience(self):
        """Test labels serialization convenience function"""
        labels = ["tdd", "performance"]
        result = serialize_labels(labels)
        
        assert isinstance(result, str)
        assert json.loads(result) == labels
    
    def test_deserialize_labels_convenience(self):
        """Test labels deserialization convenience function"""
        labels_json = '["tdd", "performance"]'
        result = deserialize_labels(labels_json)
        
        assert result == ["tdd", "performance"]
    
    def test_validate_epic_data_convenience(self):
        """Test epic data validation convenience function"""
        epic_data = {
            "epic": {
                "goals": ["Valid goal with sufficient length"]
            }
        }
        
        result = validate_epic_data(epic_data)
        
        assert result["is_valid"] is True
        assert "goals" in result["validated_fields"]


# ==================================================================================
# PRESET HANDLER TESTS
# ==================================================================================

class TestEpicJsonHandlerPresets:
    """Test suite for preset handler configurations"""
    
    def test_strict_preset(self):
        """Test strict validation preset"""
        handler = EpicJsonHandler.strict()
        
        assert handler.strict_validation is True
        assert handler.max_field_size == 8000
    
    def test_lenient_preset(self):
        """Test lenient validation preset"""
        handler = EpicJsonHandler.lenient()
        
        assert handler.strict_validation is False
        assert handler.max_field_size == 15000
    
    def test_migration_preset(self):
        """Test migration preset"""
        handler = EpicJsonHandler.migration()
        
        assert handler.strict_validation is False
        assert handler.max_field_size == 20000


# ==================================================================================
# REAL EPIC DATA INTEGRATION TESTS
# ==================================================================================

class TestRealEpicDataIntegration:
    """Integration tests with real epic data patterns"""
    
    def setup_method(self):
        self.handler = JsonFieldHandler()
    
    def test_real_epic_goals_pattern(self):
        """Test with goals from real epic data"""
        # From epico_3.json
        real_goals = [
            "Implementar captura de warnings em tempo real sem afetar a performance do pipeline em mais de 5% do tempo base de execução",
            "Criar interface interativa que solicite decisão do usuário apenas para warnings desconhecidos",
            "Persistir decisões em SQLite garantindo propriedades ACID e recuperá-las para aplicação automática"
        ]
        
        # Should serialize and deserialize correctly
        serialized = self.handler.serialize_field(real_goals, JsonFieldType.GOALS)
        deserialized = self.handler.deserialize_field(serialized, JsonFieldType.GOALS)
        
        assert deserialized == real_goals
    
    def test_real_epic_definition_of_done_pattern(self):
        """Test with definition_of_done from real epic data"""
        # From epico_5.json
        real_dod = [
            "Funções clear_cache() e invalidate() implementadas e testadas em módulos BIParamLookup e SheetsFetcher",
            "Coordenação entre caches configurável sem aumentar chamadas de API",
            "Chain invalidation test passa em menos de 50 ms por cache",
            "Estatísticas de uso e invalidação disponíveis via função pública",
            "Cobertura de testes ≥ 90% nos novos módulos"
        ]
        
        # Should serialize and validate correctly
        serialized = self.handler.serialize_field(real_dod, JsonFieldType.DEFINITION_OF_DONE)
        deserialized = self.handler.deserialize_field(serialized, JsonFieldType.DEFINITION_OF_DONE)
        
        assert deserialized == real_dod
    
    def test_real_epic_labels_pattern(self):
        """Test with labels from real epic data"""
        # From epico_3.json and epico_5.json
        real_labels = ["tdd", "interactive-system", "warnings", "database", "caching", "performance"]
        
        # Should validate label patterns
        self.handler._validate_structure(real_labels, JsonFieldType.LABELS)
        
        # Should serialize correctly
        serialized = self.handler.serialize_field(real_labels, JsonFieldType.LABELS)
        deserialized = self.handler.deserialize_field(serialized, JsonFieldType.LABELS)
        
        assert deserialized == real_labels
    
    def test_complete_real_epic_validation(self):
        """Test validation of complete real epic structure"""
        # Simplified version of real epic structure
        real_epic = {
            "epic": {
                "id": "5",
                "name": "Cache Management Specifics",
                "goals": [
                    "Permitir invalidação manual e programática do cache de BIParamLookup e SheetsFetcher",
                    "Garantir coordenação entre caches para evitar dados inconsistentes"
                ],
                "definition_of_done": [
                    "Funções clear_cache() e invalidate() implementadas e testadas em módulos BIParamLookup e SheetsFetcher",
                    "Coordenação entre caches configurável sem aumentar chamadas de API"
                ],
                "labels": ["tdd", "caching", "performance", "refactor"]
            }
        }
        
        result = self.handler.validate_epic_json_fields(real_epic)
        
        assert result["is_valid"] is True
        assert len(result["errors"]) == 0
        assert result["validated_fields"]["goals"] == 2
        assert result["validated_fields"]["definition_of_done"] == 2
        assert result["validated_fields"]["labels"] == 4


# ==================================================================================
# ERROR HANDLING AND EDGE CASES
# ==================================================================================

class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge cases"""
    
    def setup_method(self):
        self.handler = JsonFieldHandler()
        self.lenient_handler = JsonFieldHandler(strict_validation=False)
    
    def test_large_field_handling(self):
        """Test handling of very large JSON fields"""
        large_goals = ["Goal " + "x" * 1000 for _ in range(100)]
        
        with pytest.raises(JsonValidationError) as exc_info:
            self.handler.serialize_field(large_goals, JsonFieldType.GOALS)
        # Could fail due to too many items or field size
        assert "too large" in str(exc_info.value) or "cannot have more than" in str(exc_info.value)
    
    def test_deeply_nested_structure(self):
        """Test handling of deeply nested JSON structures"""
        nested_metadata = {
            "level1": {
                "level2": {
                    "level3": {
                        "value": "deep value"
                    }
                }
            }
        }
        
        searchable = self.handler.extract_searchable_text(nested_metadata)
        assert any("deep value" in text for text in searchable)
    
    def test_unicode_handling(self):
        """Test proper Unicode handling in JSON fields"""
        unicode_goals = ["Implementar função com acentuação", "测试中文支持", "🚀 Rocket feature"]
        
        serialized = self.handler.serialize_field(unicode_goals, JsonFieldType.GOALS)
        deserialized = self.handler.deserialize_field(serialized, JsonFieldType.GOALS)
        
        assert deserialized == unicode_goals
    
    def test_edge_case_empty_structures(self):
        """Test handling of edge case empty structures"""
        edge_cases = [
            ([], JsonFieldType.GOALS),
            ({}, JsonFieldType.METADATA),
            (None, JsonFieldType.LABELS)
        ]
        
        for data, field_type in edge_cases:
            # Should handle gracefully without errors
            if data is not None:
                # Use lenient handler for empty structures
                serialized = self.lenient_handler.serialize_field(data, field_type)
                assert isinstance(serialized, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])