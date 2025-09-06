"""
Prompt template loader for epic suggestion system.
Loads and manages prompt templates from markdown files.
Following TDD methodology - REFACTORED implementation.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from .config_loader_base import ConfigLoaderBase, ConfigResult


class PromptTemplateLoader(ConfigLoaderBase):
    """
    Loads and manages prompt templates for epic suggestion generation.
    
    Features:
    - Load templates from markdown files
    - Validate required variables
    - Render templates with variable substitution
    - Optional caching for performance
    - Default template fallback
    """
    
    def __init__(
        self,
        default_template: Optional[str] = None,
        enable_cache: bool = False
    ):
        """
        Initialize the prompt template loader.
        
        Args:
            default_template: Optional default template to use as fallback
            enable_cache: Whether to enable template caching
        """
        super().__init__(enable_cache=enable_cache)
        self.default_template = default_template
    
    def parse_content(self, content: str) -> str:
        """
        Parse template content (for templates, just return as-is).
        
        Args:
            content: Raw template content
            
        Returns:
            Template string
        """
        return content
    
    def validate_content(self, content: Any) -> bool:
        """
        Validate template content.
        
        Args:
            content: Template string to validate
            
        Returns:
            True if valid template syntax
        """
        if not isinstance(content, str):
            return False
        return self.validate_syntax(content)
    
    def load_template(
        self,
        path: str,
        use_default: bool = False
    ) -> str:
        """
        Load a template from a markdown file.
        
        Args:
            path: Path to the template file
            use_default: Whether to use default template if file not found
            
        Returns:
            Template content as string
            
        Raises:
            FileNotFoundError: If template file not found and no default available
        """
        # Use the base class method with Result pattern
        result = self.load_from_file(
            path=path,
            use_default=use_default,
            default_value=self.default_template
        )
        
        if result.success:
            return result.data
        else:
            # Maintain backward compatibility with exception raising
            if "not found" in result.error.lower():
                raise FileNotFoundError(f"Template file not found: {path}")
            raise ValueError(result.error)
    
    def validate_variables(
        self,
        template: str,
        required: List[str]
    ) -> bool:
        """
        Validate that all required variables are present in the template.
        
        Args:
            template: Template string to validate
            required: List of required variable names
            
        Returns:
            True if all required variables are present, False otherwise
        """
        # Extract all variables from template
        pattern = r'\{(\w+)\}'
        found_variables = set(re.findall(pattern, template))
        
        # Check if all required variables are present
        required_set = set(required)
        return required_set.issubset(found_variables)
    
    def render_template(
        self,
        template: str,
        variables: Dict[str, Any],
        nested: bool = False
    ) -> str:
        """
        Render a template by substituting variables.
        
        Args:
            template: Template string with placeholders
            variables: Dictionary of variable values
            nested: Whether to handle nested variable structures
            
        Returns:
            Rendered template with variables substituted
            
        Raises:
            KeyError: If a required variable is missing
        """
        if nested:
            # Handle nested variables like {product.name}
            return self._render_nested(template, variables)
        else:
            # Simple string format
            try:
                return template.format(**variables)
            except KeyError as e:
                raise KeyError(f"Missing required variable: {e}")
    
    def _render_nested(
        self,
        template: str,
        variables: Dict[str, Any]
    ) -> str:
        """
        Render template with nested variable support.
        
        Args:
            template: Template string
            variables: Nested dictionary of variables
            
        Returns:
            Rendered template
        """
        # Flatten nested dictionary
        flat_vars = self._flatten_dict(variables)
        
        # Replace nested placeholders
        result = template
        for key, value in flat_vars.items():
            placeholder = "{" + key + "}"
            result = result.replace(placeholder, str(value))
        
        return result
    
    def _flatten_dict(
        self,
        d: Dict[str, Any],
        parent_key: str = '',
        sep: str = '.'
    ) -> Dict[str, Any]:
        """
        Flatten a nested dictionary.
        
        Args:
            d: Dictionary to flatten
            parent_key: Parent key for recursion
            sep: Separator for nested keys
            
        Returns:
            Flattened dictionary
        """
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    def validate_syntax(self, template: str) -> bool:
        """
        Validate template syntax.
        
        Args:
            template: Template string to validate
            
        Returns:
            True if syntax is valid, False otherwise
        """
        # Check for unclosed brackets
        if template.count('{') != template.count('}'):
            return False
        
        # Check for empty variables
        if '{}' in template:
            return False
        
        # Check for properly formed variables
        pattern = r'\{[^}]*\}'
        matches = re.findall(pattern, template)
        for match in matches:
            # Variable name should not be empty and should be valid identifier
            var_name = match[1:-1]  # Remove { and }
            if not var_name or not re.match(r'^[\w.]+$', var_name):
                return False
        
        return True