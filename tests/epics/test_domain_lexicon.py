"""
Tests for domain lexicon configuration and loading.
Following TDD methodology - RED phase.
"""

import pytest
import yaml
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, patch, mock_open


class TestDomainLexiconLoader:
    """Test suite for DomainLexiconLoader following TDD RED-GREEN-REFACTOR."""

    def test_should_load_lexicon_from_yaml_file(self):
        """Test: deve carregar léxico YAML."""
        # Given
        from streamlit_extension.services.domain_lexicon_loader import DomainLexiconLoader
        loader = DomainLexiconLoader()
        lexicon_path = "configs/domain_lexicon.yaml"
        yaml_content = """
        domain:
          name: "TDD Framework"
          version: "1.0"
        
        terminology:
          epic: "capítulo"
          task: "tarefa"
          sprint: "iteração"
        
        priorities:
          high: "alta"
          medium: "média"
          low: "baixa"
        
        keywords:
          - test-driven
          - agile
          - continuous integration
        """
        expected_lexicon = yaml.safe_load(yaml_content)
        
        # When
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            result = loader.load_lexicon(lexicon_path)
        
        # Then
        assert result == expected_lexicon
        assert result["domain"]["name"] == "TDD Framework"
        assert result["terminology"]["epic"] == "capítulo"
        assert "test-driven" in result["keywords"]

    def test_should_merge_default_and_custom_lexicons(self):
        """Test: deve mesclar léxico padrão com específico do projeto."""
        # Given
        from streamlit_extension.services.domain_lexicon_loader import DomainLexiconLoader
        loader = DomainLexiconLoader()
        
        default_lexicon = {
            "domain": {"name": "Default", "version": "0.1"},
            "terminology": {
                "epic": "epic",
                "task": "task",
                "sprint": "sprint"
            },
            "priorities": {
                "high": "high",
                "medium": "medium",
                "low": "low"
            }
        }
        
        custom_lexicon = {
            "domain": {"name": "Custom Project"},  # Override name, keep version from default
            "terminology": {
                "epic": "capítulo",  # Override epic
                "story": "história"  # Add new term
            },
            "custom_field": "custom_value"  # Add new field
        }
        
        # When
        merged = loader.merge_lexicons(default_lexicon, custom_lexicon)
        
        # Then
        assert merged["domain"]["name"] == "Custom Project"  # Custom overrides
        assert merged["domain"]["version"] == "0.1"  # Default preserved
        assert merged["terminology"]["epic"] == "capítulo"  # Custom overrides
        assert merged["terminology"]["task"] == "task"  # Default preserved
        assert merged["terminology"]["story"] == "história"  # New field added
        assert merged["custom_field"] == "custom_value"  # New field added
        assert merged["priorities"]["high"] == "high"  # Default preserved

    def test_should_validate_lexicon_structure(self):
        """Test: deve validar estrutura do léxico."""
        # Given
        from streamlit_extension.services.domain_lexicon_loader import DomainLexiconLoader
        loader = DomainLexiconLoader()
        
        # Valid lexicon
        valid_lexicon = {
            "domain": {"name": "Project", "version": "1.0"},
            "terminology": {"epic": "capítulo"},
            "keywords": ["keyword1", "keyword2"]
        }
        
        # When/Then
        assert loader.validate_lexicon_structure(valid_lexicon) is True

    def test_should_fail_validation_for_invalid_structure(self):
        """Test: deve falhar validação para estrutura inválida."""
        # Given
        from streamlit_extension.services.domain_lexicon_loader import DomainLexiconLoader
        loader = DomainLexiconLoader()
        
        # Invalid: missing required 'domain' field
        invalid_lexicon = {
            "terminology": {"epic": "capítulo"}
        }
        
        # When/Then
        assert loader.validate_lexicon_structure(invalid_lexicon) is False

    def test_should_use_default_lexicon_if_file_not_found(self):
        """Test: deve usar valores padrão se arquivo não existir."""
        # Given
        from streamlit_extension.services.domain_lexicon_loader import DomainLexiconLoader
        default_lexicon = {
            "domain": {"name": "Default Framework", "version": "1.0"},
            "terminology": {"epic": "epic", "task": "task"}
        }
        loader = DomainLexiconLoader(default_lexicon=default_lexicon)
        
        # When
        with patch("builtins.open", side_effect=FileNotFoundError):
            result = loader.load_lexicon("non_existent.yaml", use_default=True)
        
        # Then
        assert result == default_lexicon

    def test_should_handle_empty_yaml_file(self):
        """Test: deve lidar com arquivo YAML vazio."""
        # Given
        from streamlit_extension.services.domain_lexicon_loader import DomainLexiconLoader
        loader = DomainLexiconLoader()
        
        # When
        with patch("builtins.open", mock_open(read_data="")):
            result = loader.load_lexicon("empty.yaml")
        
        # Then
        assert result == {} or result is None

    def test_should_handle_malformed_yaml(self):
        """Test: deve lidar com YAML mal formatado."""
        # Given
        from streamlit_extension.services.domain_lexicon_loader import DomainLexiconLoader
        loader = DomainLexiconLoader()
        malformed_yaml = """
        domain:
          name: "Test
          version: 1.0
        terminology
          epic: capítulo
        """
        
        # When/Then
        with patch("builtins.open", mock_open(read_data=malformed_yaml)):
            with pytest.raises(yaml.YAMLError):
                loader.load_lexicon("malformed.yaml")

    def test_should_deep_merge_nested_dictionaries(self):
        """Test: deve fazer merge profundo de dicionários aninhados."""
        # Given
        from streamlit_extension.services.domain_lexicon_loader import DomainLexiconLoader
        loader = DomainLexiconLoader()
        
        default = {
            "level1": {
                "level2": {
                    "key1": "default1",
                    "key2": "default2"
                },
                "other": "value"
            }
        }
        
        custom = {
            "level1": {
                "level2": {
                    "key1": "custom1",  # Override
                    "key3": "custom3"   # Add new
                }
            }
        }
        
        # When
        merged = loader.merge_lexicons(default, custom)
        
        # Then
        assert merged["level1"]["level2"]["key1"] == "custom1"  # Overridden
        assert merged["level1"]["level2"]["key2"] == "default2"  # Preserved
        assert merged["level1"]["level2"]["key3"] == "custom3"  # Added
        assert merged["level1"]["other"] == "value"  # Preserved

    def test_should_apply_lexicon_to_text(self):
        """Test: deve aplicar léxico para substituir termos em texto."""
        # Given
        from streamlit_extension.services.domain_lexicon_loader import DomainLexiconLoader
        loader = DomainLexiconLoader()
        
        lexicon = {
            "terminology": {
                "epic": "capítulo",
                "task": "tarefa",
                "sprint": "iteração"
            }
        }
        
        text = "Create an epic with multiple tasks for this sprint"
        
        # When
        translated = loader.apply_lexicon(text, lexicon)
        
        # Then
        assert translated == "Create an capítulo with multiple tarefas for this iteração"

    def test_should_cache_loaded_lexicons(self):
        """Test: deve fazer cache de léxicos carregados."""
        # Given
        from streamlit_extension.services.domain_lexicon_loader import DomainLexiconLoader
        loader = DomainLexiconLoader(enable_cache=True)
        yaml_content = """
        domain:
          name: "Cached Lexicon"
        """
        
        # When
        with patch("builtins.open", mock_open(read_data=yaml_content)) as mock_file:
            # First load
            result1 = loader.load_lexicon("test.yaml")
            # Second load (should use cache)
            result2 = loader.load_lexicon("test.yaml")
        
        # Then
        assert result1 == result2
        assert result1["domain"]["name"] == "Cached Lexicon"
        # File should be opened only once due to caching
        mock_file.assert_called_once()

    def test_should_support_environment_specific_lexicons(self):
        """Test: deve suportar léxicos específicos por ambiente."""
        # Given
        from streamlit_extension.services.domain_lexicon_loader import DomainLexiconLoader
        loader = DomainLexiconLoader()
        
        dev_lexicon = {
            "environment": "development",
            "terminology": {"epic": "dev-epic"}
        }
        
        prod_lexicon = {
            "environment": "production",
            "terminology": {"epic": "capítulo"}
        }
        
        # When
        with patch.dict("os.environ", {"TDD_ENVIRONMENT": "development"}):
            result = loader.load_environment_lexicon(dev_lexicon, prod_lexicon)
        
        # Then
        assert result["terminology"]["epic"] == "dev-epic"
        
        # When production
        with patch.dict("os.environ", {"TDD_ENVIRONMENT": "production"}):
            result = loader.load_environment_lexicon(dev_lexicon, prod_lexicon)
        
        # Then
        assert result["terminology"]["epic"] == "capítulo"

    def test_should_export_lexicon_to_json(self):
        """Test: deve exportar léxico para JSON."""
        # Given
        from streamlit_extension.services.domain_lexicon_loader import DomainLexiconLoader
        import json
        loader = DomainLexiconLoader()
        
        lexicon = {
            "domain": {"name": "Test"},
            "terminology": {"epic": "capítulo"}
        }
        
        # When
        json_output = loader.export_to_json(lexicon)
        
        # Then
        parsed = json.loads(json_output)
        assert parsed == lexicon