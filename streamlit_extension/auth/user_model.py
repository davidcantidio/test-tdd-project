"""User model and role definitions."""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class UserRole(Enum):
    """User role enumeration."""
    ADMIN = "admin"
    USER = "user"
    READONLY = "readonly"
    
    def __str__(self) -> str:
        return self.value
    
    @property
    def display_name(self) -> str:
        """Get display name for role."""
        return {
            UserRole.ADMIN: "Administrator",
            UserRole.USER: "User", 
            UserRole.READONLY: "Read Only"
        }[self]
    
    def can_edit(self) -> bool:
        """Check if role can edit data."""
        return self in [UserRole.ADMIN, UserRole.USER]
    
    def can_admin(self) -> bool:
        """Check if role has admin privileges."""
        return self == UserRole.ADMIN


@dataclass
class User:
    """User data model."""
    id: int
    username: str
    email: str
    role: UserRole
    is_active: bool = True
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    def __post_init__(self):
        """Set defaults after initialization."""
        if self.created_at is None:
            self.created_at = datetime.now()
    
    @property
    def display_name(self) -> str:
        """Get display name (username)."""
        return self.username
    
    @property
    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role.can_admin()
    
    @property
    def can_edit(self) -> bool:
        """Check if user can edit data."""
        return self.role.can_edit() and self.is_active
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role.value,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> User:
        """Create from dictionary."""
        return cls(
            id=data["id"],
            username=data["username"],
            email=data["email"],
            role=UserRole(data["role"]),
            is_active=data["is_active"],
            created_at=datetime.fromisoformat(data["created_at"]) if data["created_at"] else None,
            last_login=datetime.fromisoformat(data["last_login"]) if data["last_login"] else None
        )
