"""
Domain lexicon loader for epic suggestion system.
Loads and manages domain-specific terminology from YAML files.
Following TDD methodology - REFACTORED implementation.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from .config_loader_base import ConfigLoaderBase, ConfigResult


class DomainLexiconLoader(ConfigLoaderBase):
    """
    Loads and manages domain-specific lexicons for epic suggestion generation.
    
    Features:
    - Load lexicons from YAML files
    - Merge default and custom lexicons
    - Validate lexicon structure
    - Apply lexicon to text
    - Optional caching for performance
    - Environment-specific lexicon support
    """
    
    def __init__(
        self,
        default_lexicon: Optional[Dict[str, Any]] = None,
        enable_cache: bool = False
    ):
        """
        Initialize the domain lexicon loader.
        
        Args:
            default_lexicon: Optional default lexicon to use as fallback
            enable_cache: Whether to enable lexicon caching
        """
        super().__init__(enable_cache=enable_cache)
        self.default_lexicon = default_lexicon or {}
    
    def parse_content(self, content: str) -> Dict[str, Any]:
        """
        Parse YAML content into dictionary.
        
        Args:
            content: Raw YAML content
            
        Returns:
            Parsed lexicon dictionary
        """
        # Handle empty content
        if not content.strip():
            return {}
        
        try:
            lexicon = yaml.safe_load(content)
            return lexicon or {}
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Failed to parse YAML: {e}")
    
    def validate_content(self, content: Any) -> bool:
        """
        Validate lexicon structure.
        
        Args:
            content: Parsed lexicon to validate
            
        Returns:
            True if valid lexicon structure
        """
        if not isinstance(content, dict):
            return False
        
        # Empty dictionary is valid (empty YAML file)
        if not content:
            return True
            
        return self.validate_lexicon_structure(content)
    
    def load_lexicon(
        self,
        path: str,
        use_default: bool = False
    ) -> Dict[str, Any]:
        """
        Load a lexicon from a YAML file.
        
        Args:
            path: Path to the YAML file
            use_default: Whether to use default lexicon if file not found
            
        Returns:
            Lexicon dictionary
            
        Raises:
            FileNotFoundError: If lexicon file not found and no default available
            yaml.YAMLError: If YAML parsing fails
        """
        # Use the base class method with Result pattern
        result = self.load_from_file(
            path=path,
            use_default=use_default,
            default_value=self.default_lexicon
        )
        
        if result.success:
            return result.data
        else:
            # Maintain backward compatibility with exception raising
            if "not found" in result.error.lower():
                raise FileNotFoundError(result.error)
            elif "YAML" in result.error:
                raise yaml.YAMLError(result.error)
            raise ValueError(result.error)
    
    def merge_lexicons(
        self,
        default: Dict[str, Any],
        custom: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge default and custom lexicons with deep merge support.
        
        Args:
            default: Default lexicon dictionary
            custom: Custom lexicon dictionary to override defaults
            
        Returns:
            Merged lexicon dictionary
        """
        return self._deep_merge(default.copy(), custom)
    
    def _deep_merge(
        self,
        base: Dict[str, Any],
        override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform deep merge of two dictionaries.
        
        Args:
            base: Base dictionary
            override: Dictionary with overrides
            
        Returns:
            Merged dictionary
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                # Recursive merge for nested dictionaries
                base[key] = self._deep_merge(base[key], value)
            else:
                # Override value
                base[key] = value
        return base
    
    def validate_lexicon_structure(
        self,
        lexicon: Dict[str, Any]
    ) -> bool:
        """
        Validate that lexicon has required structure.
        
        Args:
            lexicon: Lexicon dictionary to validate
            
        Returns:
            True if structure is valid, False otherwise
        """
        # Check for required 'domain' field
        if 'domain' not in lexicon:
            return False
        
        # Check that domain has required fields
        domain = lexicon.get('domain', {})
        if not isinstance(domain, dict):
            return False
        
        # Domain should have at least 'name' field
        if 'name' not in domain:
            return False
        
        # If keywords exist, they should be a list
        if 'keywords' in lexicon:
            if not isinstance(lexicon['keywords'], list):
                return False
        
        # If terminology exists, it should be a dictionary
        if 'terminology' in lexicon:
            if not isinstance(lexicon['terminology'], dict):
                return False
        
        return True
    
    def apply_lexicon(
        self,
        text: str,
        lexicon: Dict[str, Any]
    ) -> str:
        """
        Apply lexicon terminology to text.
        
        Args:
            text: Text to transform
            lexicon: Lexicon with terminology mappings
            
        Returns:
            Transformed text with lexicon terms applied
        """
        if 'terminology' not in lexicon:
            return text
        
        result = text
        terminology = lexicon['terminology']
        
        # Replace terms in text
        for original, replacement in terminology.items():
            # Case-insensitive replacement preserving word boundaries
            import re
            pattern = r'\b' + re.escape(original) + r'\b'
            
            # Find all matches to preserve case
            matches = re.finditer(pattern, result, re.IGNORECASE)
            
            # Replace from end to beginning to maintain positions
            replacements = []
            for match in matches:
                start, end = match.span()
                matched_text = match.group()
                
                # Preserve case of original text
                if matched_text.isupper():
                    new_text = replacement.upper()
                elif matched_text[0].isupper():
                    new_text = replacement.capitalize()
                else:
                    new_text = replacement
                    
                replacements.append((start, end, new_text))
            
            # Apply replacements in reverse order
            for start, end, new_text in reversed(replacements):
                result = result[:start] + new_text + result[end:]
        
        # Fix plural forms (simple heuristic)
        for original, replacement in terminology.items():
            # Handle simple English plurals
            if original + 's' in result:
                result = result.replace(original + 's', replacement + 's')
        
        return result
    
    def load_environment_lexicon(
        self,
        dev_lexicon: Dict[str, Any],
        prod_lexicon: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Load environment-specific lexicon based on TDD_ENVIRONMENT.
        
        Args:
            dev_lexicon: Development environment lexicon
            prod_lexicon: Production environment lexicon
            
        Returns:
            Appropriate lexicon for current environment
        """
        environment = os.getenv('TDD_ENVIRONMENT', 'development')
        
        if environment == 'development':
            return dev_lexicon
        elif environment == 'production':
            return prod_lexicon
        else:
            # Default to development if unknown environment
            return dev_lexicon
    
    def export_to_json(
        self,
        lexicon: Dict[str, Any]
    ) -> str:
        """
        Export lexicon to JSON format.
        
        Args:
            lexicon: Lexicon dictionary
            
        Returns:
            JSON string representation
        """
        return json.dumps(lexicon, indent=2, ensure_ascii=False)