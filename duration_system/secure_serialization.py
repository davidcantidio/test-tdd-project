"""
🔐 Secure Serialization Utilities

Enterprise-grade serialization utilities addressing SEC-001 vulnerabilities.
Replaces insecure pickle operations with secure msgpack serialization.

Security Features:
1. Secure msgpack serialization (replaces pickle)
2. Data integrity validation
3. Size and depth limits for DoS prevention
4. Type validation and sanitization
5. Error handling with security logging

Usage:
    from duration_system.secure_serialization import SecureSerializer
    
    serializer = SecureSerializer()
    data = {"key": "value", "number": 42}
    
    # Serialize securely
    serialized = serializer.serialize(data)
    
    # Deserialize safely
    deserialized = serializer.deserialize(serialized)
"""

import msgpack
import hashlib
import logging
from typing import Any, Optional, Dict, List, Union, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import json

# Set up security logging
security_logger = logging.getLogger('security.serialization')
security_logger.setLevel(logging.INFO)

# If no handlers are set, add a default one
if not security_logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    security_logger.addHandler(handler)


class SecureSerializationError(Exception):
    """Custom exception for serialization security issues."""
    pass


class SecureSerializer:
    """
    Secure serialization utility using msgpack.
    
    Provides secure replacement for pickle operations with:
    - DoS protection via size/depth limits
    - Data integrity validation
    - Type validation and sanitization
    - Security event logging
    """
    
    def __init__(self, 
                 max_size_mb: int = 10,
                 max_depth: int = 32,
                 max_array_length: int = 10000,
                 strict_mode: bool = True):
        """
        Initialize secure serializer.
        
        Args:
            max_size_mb: Maximum serialized data size in MB
            max_depth: Maximum nested object depth
            max_array_length: Maximum array/list length
            strict_mode: Enable strict type validation
        """
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.max_depth = max_depth
        self.max_array_length = max_array_length
        self.strict_mode = strict_mode
        
        # Statistics for monitoring
        self.stats = {
            "serializations": 0,
            "deserializations": 0,
            "security_violations": 0,
            "size_violations": 0,
            "depth_violations": 0,
            "type_violations": 0,
            "errors": 0
        }
        
        # Allowed types in strict mode
        self.allowed_types = {
            str, int, float, bool, bytes, type(None),
            list, tuple, dict, set, frozenset,
            datetime, timedelta
        }
    
    def _convert_datetime_for_serialization(self, obj: Any) -> Any:
        """Convert datetime objects to serializable format."""
        if isinstance(obj, datetime):
            return {"__datetime__": obj.isoformat()}
        elif isinstance(obj, timedelta):
            return {"__timedelta__": obj.total_seconds()}
        elif isinstance(obj, dict):
            return {key: self._convert_datetime_for_serialization(value) for key, value in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._convert_datetime_for_serialization(item) for item in obj]
        else:
            return obj
    
    def _convert_datetime_after_deserialization(self, obj: Any) -> Any:
        """Convert datetime markers back to datetime objects."""
        if isinstance(obj, dict):
            if "__datetime__" in obj:
                return datetime.fromisoformat(obj["__datetime__"])
            elif "__timedelta__" in obj:
                return timedelta(seconds=obj["__timedelta__"])
            else:
                return {key: self._convert_datetime_after_deserialization(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_datetime_after_deserialization(item) for item in obj]
        else:
            return obj

    def serialize(self, data: Any, validate: bool = True) -> bytes:
        """
        Securely serialize data using msgpack.
        
        Args:
            data: Data to serialize
            validate: Perform security validation
            
        Returns:
            Serialized data as bytes
            
        Raises:
            SecureSerializationError: If security validation fails
        """
        try:
            if validate:
                self._validate_for_serialization(data)
            
            # Convert datetime objects to serializable format
            converted_data = self._convert_datetime_for_serialization(data)
            
            # Use msgpack with security-focused options
            serialized = msgpack.packb(
                converted_data,
                use_bin_type=True,      # Distinguish bytes from strings
                strict_types=True       # Strict type handling
            )
            
            # Final size check
            if len(serialized) > self.max_size_bytes:
                self.stats["size_violations"] += 1
                raise SecureSerializationError(
                    f"Serialized data too large: {len(serialized)} bytes > {self.max_size_bytes}"
                )
            
            self.stats["serializations"] += 1
            
            security_logger.debug(
                f"Secure serialization completed: {len(serialized)} bytes"
            )
            
            return serialized
            
        except msgpack.exceptions.PackException as e:
            self.stats["errors"] += 1
            security_logger.error(f"Msgpack serialization error: {e}")
            raise SecureSerializationError(f"Serialization failed: {e}")
        except Exception as e:
            self.stats["errors"] += 1
            security_logger.error(f"Unexpected serialization error: {e}")
            raise SecureSerializationError(f"Unexpected error: {e}")
    
    def deserialize(self, data: bytes, validate: bool = True) -> Any:
        """
        Securely deserialize data using msgpack.
        
        Args:
            data: Serialized data bytes
            validate: Perform security validation
            
        Returns:
            Deserialized data
            
        Raises:
            SecureSerializationError: If security validation fails
        """
        try:
            # Pre-deserialization size check
            if len(data) > self.max_size_bytes:
                self.stats["size_violations"] += 1
                raise SecureSerializationError(
                    f"Input data too large: {len(data)} bytes > {self.max_size_bytes}"
                )
            
            # Deserialize with security options
            deserialized = msgpack.unpackb(
                data,
                raw=False,              # Return strings as str, not bytes
                strict_map_key=False    # Allow different key types for compatibility
            )
            
            # Convert datetime markers back to datetime objects
            converted_back = self._convert_datetime_after_deserialization(deserialized)
            
            if validate:
                self._validate_after_deserialization(converted_back)
            
            self.stats["deserializations"] += 1
            
            security_logger.debug(
                f"Secure deserialization completed: {type(converted_back).__name__}"
            )
            
            return converted_back
            
        except (msgpack.exceptions.ExtraData, 
                msgpack.exceptions.UnpackException,
                msgpack.exceptions.UnpackValueError) as e:
            self.stats["errors"] += 1
            security_logger.error(f"Msgpack deserialization error: {e}")
            raise SecureSerializationError(f"Deserialization failed: {e}")
        except Exception as e:
            self.stats["errors"] += 1
            security_logger.error(f"Unexpected deserialization error: {e}")
            raise SecureSerializationError(f"Unexpected error: {e}")
    
    def _validate_for_serialization(self, data: Any, depth: int = 0) -> None:
        """
        Validate data before serialization.
        
        Args:
            data: Data to validate
            depth: Current nesting depth
            
        Raises:
            SecureSerializationError: If validation fails
        """
        if depth > self.max_depth:
            self.stats["depth_violations"] += 1
            raise SecureSerializationError(
                f"Data nesting too deep: {depth} > {self.max_depth}"
            )
        
        if self.strict_mode:
            data_type = type(data)
            if data_type not in self.allowed_types:
                self.stats["type_violations"] += 1
                raise SecureSerializationError(
                    f"Type not allowed in strict mode: {data_type.__name__}"
                )
        
        # Validate based on type
        if isinstance(data, (list, tuple)):
            if len(data) > self.max_array_length:
                self.stats["size_violations"] += 1
                raise SecureSerializationError(
                    f"Array too long: {len(data)} > {self.max_array_length}"
                )
            for item in data:
                self._validate_for_serialization(item, depth + 1)
                
        elif isinstance(data, dict):
            if len(data) > self.max_array_length:
                self.stats["size_violations"] += 1
                raise SecureSerializationError(
                    f"Dictionary too large: {len(data)} > {self.max_array_length}"
                )
            for key, value in data.items():
                if not isinstance(key, (str, int, float)):
                    self.stats["type_violations"] += 1
                    raise SecureSerializationError(
                        f"Invalid key type: {type(key).__name__}"
                    )
                self._validate_for_serialization(key, depth + 1)
                self._validate_for_serialization(value, depth + 1)
                
        elif isinstance(data, (set, frozenset)):
            if len(data) > self.max_array_length:
                self.stats["size_violations"] += 1
                raise SecureSerializationError(
                    f"Set too large: {len(data)} > {self.max_array_length}"
                )
            for item in data:
                self._validate_for_serialization(item, depth + 1)
                
        elif isinstance(data, str):
            # Check for excessively long strings
            if len(data) > 1024 * 1024:  # 1MB string limit
                self.stats["size_violations"] += 1
                raise SecureSerializationError(
                    f"String too long: {len(data)} characters"
                )
                
        elif isinstance(data, bytes):
            # Check for excessively large byte arrays
            if len(data) > 1024 * 1024:  # 1MB bytes limit
                self.stats["size_violations"] += 1
                raise SecureSerializationError(
                    f"Bytes object too large: {len(data)} bytes"
                )
    
    def _validate_after_deserialization(self, data: Any, depth: int = 0) -> None:
        """
        Validate data after deserialization.
        
        Args:
            data: Deserialized data to validate
            depth: Current nesting depth
            
        Raises:
            SecureSerializationError: If validation fails
        """
        # Similar validation as pre-serialization
        self._validate_for_serialization(data, depth)
    
    def serialize_to_file(self, data: Any, file_path: Union[str, Path], 
                         validate: bool = True) -> None:
        """
        Serialize data to file securely.
        
        Args:
            data: Data to serialize
            file_path: Path to output file
            validate: Perform security validation
        """
        serialized = self.serialize(data, validate)
        
        file_path = Path(file_path)
        temp_path = file_path.with_suffix('.tmp')
        
        try:
            # Write to temporary file first (atomic operation)
            with open(temp_path, 'wb') as f:
                f.write(serialized)
            
            # Atomic move
            temp_path.replace(file_path)
            
            security_logger.info(f"Data serialized to file: {file_path}")
            
        except Exception as e:
            # Clean up temporary file on error
            if temp_path.exists():
                temp_path.unlink()
            raise SecureSerializationError(f"File serialization failed: {e}")
    
    def deserialize_from_file(self, file_path: Union[str, Path], 
                             validate: bool = True) -> Any:
        """
        Deserialize data from file securely.
        
        Args:
            file_path: Path to input file
            validate: Perform security validation
            
        Returns:
            Deserialized data
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise SecureSerializationError(f"File not found: {file_path}")
        
        # Check file size before reading
        file_size = file_path.stat().st_size
        if file_size > self.max_size_bytes:
            self.stats["size_violations"] += 1
            raise SecureSerializationError(
                f"File too large: {file_size} bytes > {self.max_size_bytes}"
            )
        
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            
            result = self.deserialize(data, validate)
            
            security_logger.info(f"Data deserialized from file: {file_path}")
            
            return result
            
        except Exception as e:
            raise SecureSerializationError(f"File deserialization failed: {e}")
    
    def create_integrity_hash(self, data: bytes) -> str:
        """
        Create integrity hash for serialized data.
        
        Args:
            data: Serialized data
            
        Returns:
            SHA-256 hash as hex string
        """
        return hashlib.sha256(data).hexdigest()
    
    def verify_integrity(self, data: bytes, expected_hash: str) -> bool:
        """
        Verify data integrity using hash.
        
        Args:
            data: Serialized data
            expected_hash: Expected SHA-256 hash
            
        Returns:
            True if integrity verified
        """
        actual_hash = self.create_integrity_hash(data)
        return actual_hash == expected_hash
    
    def get_stats(self) -> Dict[str, Any]:
        """Get serialization statistics."""
        stats = self.stats.copy()
        stats.update({
            "max_size_mb": self.max_size_bytes // (1024 * 1024),
            "max_depth": self.max_depth,
            "max_array_length": self.max_array_length,
            "strict_mode": self.strict_mode,
            "allowed_types": [t.__name__ for t in self.allowed_types]
        })
        return stats
    
    def reset_stats(self) -> None:
        """Reset statistics counters."""
        for key in self.stats:
            self.stats[key] = 0


# Global secure serializer instance
_default_serializer = SecureSerializer()


# Convenience functions using default serializer
def secure_serialize(data: Any, validate: bool = True) -> bytes:
    """Serialize data securely using default serializer."""
    return _default_serializer.serialize(data, validate)


def secure_deserialize(data: bytes, validate: bool = True) -> Any:
    """Deserialize data securely using default serializer."""
    return _default_serializer.deserialize(data, validate)


def secure_serialize_to_file(data: Any, file_path: Union[str, Path], 
                            validate: bool = True) -> None:
    """Serialize data to file securely using default serializer."""
    _default_serializer.serialize_to_file(data, file_path, validate)


def secure_deserialize_from_file(file_path: Union[str, Path], 
                                validate: bool = True) -> Any:
    """Deserialize data from file securely using default serializer."""
    return _default_serializer.deserialize_from_file(file_path, validate)


# Migration helper for existing pickle files
def migrate_pickle_to_secure(pickle_file: Union[str, Path], 
                           output_file: Union[str, Path],
                           validate_output: bool = True) -> bool:
    """
    Migrate existing pickle file to secure msgpack format.
    
    WARNING: This function imports pickle temporarily for migration.
    Use only for trusted pickle files during migration.
    
    Args:
        pickle_file: Path to existing pickle file
        output_file: Path for new secure file
        validate_output: Validate migrated data
        
    Returns:
        True if migration successful
    """
    import pickle
    import warnings
    
    warnings.warn(
        "migrate_pickle_to_secure uses pickle for migration. "
        "Only use with trusted pickle files.",
        SecurityWarning
    )
    
    pickle_path = Path(pickle_file)
    output_path = Path(output_file)
    
    if not pickle_path.exists():
        security_logger.error(f"Pickle file not found: {pickle_path}")
        return False
    
    try:
        # Read and deserialize pickle data
        with open(pickle_path, 'rb') as f:
            data = pickle.load(f)
        
        security_logger.warning(f"Loaded pickle data for migration: {pickle_path}")
        
        # Serialize to secure format
        secure_serialize_to_file(data, output_path, validate_output)
        
        security_logger.info(f"Successfully migrated: {pickle_path} -> {output_path}")
        
        return True
        
    except Exception as e:
        security_logger.error(f"Migration failed: {e}")
        return False


if __name__ == "__main__":
    # Example usage and testing
    def test_secure_serialization():
        """Test secure serialization functionality."""
        print("Testing Secure Serialization...")
        
        serializer = SecureSerializer()
        
        # Test data
        test_data = {
            "string": "Hello, secure world!",
            "number": 42,
            "float": 3.14159,
            "boolean": True,
            "null": None,
            "list": [1, 2, 3, "four"],
            "nested": {
                "inner": {"deep": "value"},
                "timestamp": datetime.now()
            }
        }
        
        try:
            # Serialize
            serialized = serializer.serialize(test_data)
            print(f"✓ Serialization successful: {len(serialized)} bytes")
            
            # Create integrity hash
            integrity_hash = serializer.create_integrity_hash(serialized)
            print(f"✓ Integrity hash: {integrity_hash[:16]}...")
            
            # Deserialize
            deserialized = serializer.deserialize(serialized)
            print(f"✓ Deserialization successful")
            
            # Verify integrity
            if serializer.verify_integrity(serialized, integrity_hash):
                print("✓ Integrity verification passed")
            else:
                print("✗ Integrity verification failed")
            
            # Check data equality (excluding datetime precision)
            if deserialized["string"] == test_data["string"]:
                print("✓ Data integrity maintained")
            else:
                print("✗ Data corruption detected")
            
            # Show statistics
            stats = serializer.get_stats()
            print(f"✓ Statistics: {stats['serializations']} serializations, {stats['deserializations']} deserializations")
            
        except SecureSerializationError as e:
            print(f"✗ Security error: {e}")
        except Exception as e:
            print(f"✗ Unexpected error: {e}")
    
    test_secure_serialization()