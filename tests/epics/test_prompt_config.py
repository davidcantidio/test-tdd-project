"""
Tests for prompt template configuration and loading.
Following TDD methodology - RED phase.
"""

import pytest
from pathlib import Path
from typing import Dict, List
from unittest.mock import Mock, patch, mock_open


class TestPromptTemplateLoader:
    """Test suite for PromptTemplateLoader following TDD RED-GREEN-REFACTOR."""

    def test_should_load_template_from_markdown_file(self):
        """Test: deve carregar template markdown do arquivo."""
        # Given
        from streamlit_extension.services.prompt_template_loader import PromptTemplateLoader
        loader = PromptTemplateLoader()
        template_path = "prompts/epic_suggestion.md"
        expected_content = """# Epic Suggestion Template
        
        Product: {product_name}
        Target User: {target_user}
        
        Generate epic suggestions based on the following context:
        {context}
        """
        
        # When
        with patch("builtins.open", mock_open(read_data=expected_content)):
            result = loader.load_template(template_path)
        
        # Then
        assert result == expected_content
        assert "{product_name}" in result
        assert "{target_user}" in result
        assert "{context}" in result

    def test_should_validate_required_variables_in_template(self):
        """Test: deve validar variáveis obrigatórias no template."""
        # Given
        from streamlit_extension.services.prompt_template_loader import PromptTemplateLoader
        loader = PromptTemplateLoader()
        template = "Product: {product_name}, User: {target_user}, Problem: {problem}"
        required_variables = ["product_name", "target_user", "problem"]
        
        # When
        is_valid = loader.validate_variables(template, required_variables)
        
        # Then
        assert is_valid is True

    def test_should_fail_validation_if_required_variable_missing(self):
        """Test: deve falhar validação se variável obrigatória estiver faltando."""
        # Given
        from streamlit_extension.services.prompt_template_loader import PromptTemplateLoader
        loader = PromptTemplateLoader()
        template = "Product: {product_name}, User: {target_user}"
        required_variables = ["product_name", "target_user", "problem"]  # 'problem' is missing
        
        # When
        is_valid = loader.validate_variables(template, required_variables)
        
        # Then
        assert is_valid is False

    def test_should_substitute_variables_in_template(self):
        """Test: deve substituir variáveis no template."""
        # Given
        from streamlit_extension.services.prompt_template_loader import PromptTemplateLoader
        loader = PromptTemplateLoader()
        template = "Product: {product_name}, User: {target_user}, Problem: {problem}"
        variables = {
            "product_name": "TDD Framework",
            "target_user": "Developers",
            "problem": "Complex testing workflows"
        }
        
        # When
        rendered = loader.render_template(template, variables)
        
        # Then
        assert rendered == "Product: TDD Framework, User: Developers, Problem: Complex testing workflows"
        assert "{product_name}" not in rendered
        assert "{target_user}" not in rendered
        assert "{problem}" not in rendered

    def test_should_raise_error_if_template_file_not_found(self):
        """Test: deve falhar se arquivo não existir."""
        # Given
        from streamlit_extension.services.prompt_template_loader import PromptTemplateLoader
        loader = PromptTemplateLoader()
        non_existent_path = "prompts/non_existent.md"
        
        # When/Then
        with patch("builtins.open", side_effect=FileNotFoundError):
            with pytest.raises(FileNotFoundError) as exc_info:
                loader.load_template(non_existent_path)
            
            assert "Template file not found" in str(exc_info.value)

    def test_should_raise_error_if_variable_missing_during_render(self):
        """Test: deve falhar se variável obrigatória estiver faltando durante renderização."""
        # Given
        from streamlit_extension.services.prompt_template_loader import PromptTemplateLoader
        loader = PromptTemplateLoader()
        template = "Product: {product_name}, User: {target_user}, Problem: {problem}"
        incomplete_variables = {
            "product_name": "TDD Framework",
            "target_user": "Developers"
            # 'problem' is missing
        }
        
        # When/Then
        with pytest.raises(KeyError) as exc_info:
            loader.render_template(template, incomplete_variables)
        
        assert "problem" in str(exc_info.value)

    def test_should_handle_nested_template_variables(self):
        """Test: deve lidar com variáveis aninhadas no template."""
        # Given
        from streamlit_extension.services.prompt_template_loader import PromptTemplateLoader
        loader = PromptTemplateLoader()
        template = """
        Product Vision:
        - Name: {product.name}
        - Version: {product.version}
        - Users: {users.primary}, {users.secondary}
        """
        variables = {
            "product": {"name": "TDD Framework", "version": "1.0"},
            "users": {"primary": "Developers", "secondary": "QA Engineers"}
        }
        
        # When
        rendered = loader.render_template(template, variables, nested=True)
        
        # Then
        assert "TDD Framework" in rendered
        assert "1.0" in rendered
        assert "Developers" in rendered
        assert "QA Engineers" in rendered

    def test_should_cache_loaded_templates(self):
        """Test: deve fazer cache de templates carregados."""
        # Given
        from streamlit_extension.services.prompt_template_loader import PromptTemplateLoader
        loader = PromptTemplateLoader(enable_cache=True)
        template_path = "prompts/epic_suggestion.md"
        template_content = "Cached template content"
        
        # When
        with patch("builtins.open", mock_open(read_data=template_content)) as mock_file:
            # First load
            result1 = loader.load_template(template_path)
            # Second load (should use cache)
            result2 = loader.load_template(template_path)
        
        # Then
        assert result1 == result2 == template_content
        # File should be opened only once due to caching
        mock_file.assert_called_once()

    def test_should_provide_default_template_if_configured(self):
        """Test: deve fornecer template padrão se configurado."""
        # Given
        from streamlit_extension.services.prompt_template_loader import PromptTemplateLoader
        default_template = "Default: {product_name}"
        loader = PromptTemplateLoader(default_template=default_template)
        
        # When
        with patch("builtins.open", side_effect=FileNotFoundError):
            result = loader.load_template("non_existent.md", use_default=True)
        
        # Then
        assert result == default_template

    def test_should_validate_template_syntax(self):
        """Test: deve validar sintaxe do template."""
        # Given
        from streamlit_extension.services.prompt_template_loader import PromptTemplateLoader
        loader = PromptTemplateLoader()
        
        # Valid template
        valid_template = "Product: {product_name}"
        assert loader.validate_syntax(valid_template) is True
        
        # Invalid template with unclosed bracket
        invalid_template = "Product: {product_name"
        assert loader.validate_syntax(invalid_template) is False
        
        # Invalid template with empty variable
        invalid_template2 = "Product: {}"
        assert loader.validate_syntax(invalid_template2) is False