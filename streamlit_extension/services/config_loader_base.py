"""
Base configuration loader for the epic suggestion system.
Provides common functionality for loading and managing configuration files.
Following TDD methodology - REFACTOR phase.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, TypeVar, Generic, Union
from dataclasses import dataclass
from functools import lru_cache


T = TypeVar('T')


@dataclass
class ConfigResult(Generic[T]):
    """Result wrapper for configuration operations."""
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    
    @classmethod
    def ok(cls, data: T) -> 'ConfigResult[T]':
        """Create a successful result."""
        return cls(success=True, data=data, error=None)
    
    @classmethod
    def fail(cls, error: str) -> 'ConfigResult[T]':
        """Create a failed result."""
        return cls(success=False, data=None, error=error)


class ConfigLoaderBase(ABC):
    """
    Abstract base class for configuration loaders.
    
    Provides common functionality:
    - File loading with error handling
    - Caching support
    - Result pattern for error management
    - Default fallback mechanism
    """
    
    def __init__(
        self,
        enable_cache: bool = False,
        cache_size: int = 128
    ):
        """
        Initialize the configuration loader.
        
        Args:
            enable_cache: Whether to enable caching
            cache_size: Maximum number of cached items
        """
        self.enable_cache = enable_cache
        self.cache_size = cache_size
        self._cache: Dict[str, Any] = {}
        
        # Setup LRU cache if enabled
        if enable_cache:
            self._cached_load = lru_cache(maxsize=cache_size)(self._load_file)
        else:
            self._cached_load = self._load_file
    
    @abstractmethod
    def parse_content(self, content: str) -> Any:
        """
        Parse the loaded content into the appropriate format.
        
        Args:
            content: Raw file content
            
        Returns:
            Parsed content
        """
        pass
    
    @abstractmethod
    def validate_content(self, content: Any) -> bool:
        """
        Validate the parsed content.
        
        Args:
            content: Parsed content to validate
            
        Returns:
            True if valid, False otherwise
        """
        pass
    
    def load_from_file(
        self,
        path: Union[str, Path],
        use_default: bool = False,
        default_value: Optional[Any] = None
    ) -> ConfigResult[Any]:
        """
        Load configuration from a file with error handling.
        
        Args:
            path: Path to the configuration file
            use_default: Whether to use default value on error
            default_value: Default value to use if file not found
            
        Returns:
            ConfigResult with loaded data or error
        """
        try:
            # Load content directly - this allows mocking in tests
            content = self._cached_load(str(path))
            
            # Parse content
            parsed = self.parse_content(content)
            
            # Validate
            if not self.validate_content(parsed):
                return ConfigResult.fail(f"Invalid content in file: {path}")
            
            return ConfigResult.ok(parsed)
            
        except FileNotFoundError:
            if use_default and default_value is not None:
                return ConfigResult.ok(default_value)
            return ConfigResult.fail(f"File not found: {path}")
        except Exception as e:
            if use_default and default_value is not None:
                return ConfigResult.ok(default_value)
            return ConfigResult.fail(f"Error loading file: {str(e)}")
    
    def _load_file(self, path: str) -> str:
        """
        Load raw content from a file.
        
        Args:
            path: File path
            
        Returns:
            File content as string
        """
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def clear_cache(self):
        """Clear the cache if caching is enabled."""
        if self.enable_cache:
            self._cache.clear()
            if hasattr(self._cached_load, 'cache_clear'):
                self._cached_load.cache_clear()
    
    def get_cache_info(self) -> Optional[Dict[str, Any]]:
        """
        Get cache statistics if caching is enabled.
        
        Returns:
            Cache information or None if caching disabled
        """
        if self.enable_cache and hasattr(self._cached_load, 'cache_info'):
            info = self._cached_load.cache_info()
            return {
                'hits': info.hits,
                'misses': info.misses,
                'maxsize': info.maxsize,
                'currsize': info.currsize
            }
        return None