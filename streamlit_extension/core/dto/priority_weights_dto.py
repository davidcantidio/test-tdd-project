"""
🎯 PriorityWeightsDTO - História 3.2
Data Transfer Object for project-specific priority weight configuration.

Maintains normalized weights [0,1] that sum to ~1.0 for epic prioritization.
Default values preserve the 5:3:2:2 proportion from História 3.1.
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class PriorityWeightsDTO:
    """
    Priority weights configuration DTO for project-specific epic scoring.
    
    All weights are normalized [0,1] and should sum to ~1.0 (tolerance 0.0001).
    Default values maintain the 5:3:2:2 proportion from História 3.1:
    - valor: 5/12 ≈ 0.4167
    - risco: 3/12 = 0.25
    - esforco: 2/12 ≈ 0.1667
    - alinhamento: 2/12 ≈ 0.1667
    - confidence: 0 (feature flag OFF)
    """
    
    # Primary fields
    id: Optional[int] = None
    project_id: Optional[int] = None
    
    # Normalized weights [0,1] - sum must equal ~1.0
    valor_weight: float = 0.4167        # Business value weight (5/12)
    risco_weight: float = 0.25          # Risk mitigation weight (3/12)
    esforco_weight: float = 0.1667      # Effort efficiency weight (2/12)
    alinhamento_weight: float = 0.1667  # Strategic alignment weight (2/12)
    confidence_weight: float = 0.0      # AI confidence weight (feature OFF)
    
    # Audit fields
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate and normalize weights after initialization"""
        # Clamp all weights to [0,1] range
        self.valor_weight = max(0.0, min(1.0, self.valor_weight))
        self.risco_weight = max(0.0, min(1.0, self.risco_weight))
        self.esforco_weight = max(0.0, min(1.0, self.esforco_weight))
        self.alinhamento_weight = max(0.0, min(1.0, self.alinhamento_weight))
        self.confidence_weight = max(0.0, min(1.0, self.confidence_weight))
        
        # Validate sum with tolerance
        self._validate_sum()
    
    def _validate_sum(self, tolerance: float = 0.0001):
        """
        Validate that weights sum to ~1.0 within tolerance.
        
        Args:
            tolerance: Maximum allowed deviation from 1.0
            
        Raises:
            ValueError: If weights don't sum to ~1.0
        """
        total = (self.valor_weight + self.risco_weight + 
                self.esforco_weight + self.alinhamento_weight + 
                self.confidence_weight)
        
        if abs(total - 1.0) > tolerance:
            raise ValueError(
                f"Priority weights must sum to 1.0 (±{tolerance}). "
                f"Current sum: {total:.4f}"
            )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for persistence"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'valor_weight': self.valor_weight,
            'risco_weight': self.risco_weight,
            'esforco_weight': self.esforco_weight,
            'alinhamento_weight': self.alinhamento_weight,
            'confidence_weight': self.confidence_weight,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PriorityWeightsDTO':
        """
        Create from dictionary (from persistence).
        
        Args:
            data: Dictionary with weight configuration
            
        Returns:
            PriorityWeightsDTO instance
        """
        # Parse datetime fields if present
        created_at = data.get('created_at')
        updated_at = data.get('updated_at')
        
        if created_at and isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except (ValueError, TypeError):
                created_at = None
        
        if updated_at and isinstance(updated_at, str):
            try:
                updated_at = datetime.fromisoformat(updated_at)
            except (ValueError, TypeError):
                updated_at = None
        
        return cls(
            id=data.get('id'),
            project_id=data.get('project_id'),
            valor_weight=float(data.get('valor_weight', 0.4167)),
            risco_weight=float(data.get('risco_weight', 0.25)),
            esforco_weight=float(data.get('esforco_weight', 0.1667)),
            alinhamento_weight=float(data.get('alinhamento_weight', 0.1667)),
            confidence_weight=float(data.get('confidence_weight', 0.0)),
            created_at=created_at,
            updated_at=updated_at
        )
    
    @classmethod
    def get_defaults(cls) -> 'PriorityWeightsDTO':
        """
        Get default weight configuration.
        
        Returns default weights that preserve the 5:3:2:2 proportion
        from História 3.1 in normalized form.
        
        Returns:
            PriorityWeightsDTO with default values
        """
        return cls(
            valor_weight=0.4167,      # 5/12
            risco_weight=0.25,        # 3/12
            esforco_weight=0.1667,    # 2/12
            alinhamento_weight=0.1667,# 2/12
            confidence_weight=0.0     # Feature flag OFF
        )
    
    def normalize(self) -> 'PriorityWeightsDTO':
        """
        Normalize weights to sum exactly to 1.0.
        
        Proportionally adjusts all weights to ensure exact sum of 1.0.
        
        Returns:
            New PriorityWeightsDTO instance with normalized weights
        """
        total = (self.valor_weight + self.risco_weight + 
                self.esforco_weight + self.alinhamento_weight + 
                self.confidence_weight)
        
        if total == 0:
            # If all weights are 0, return defaults
            return self.get_defaults()
        
        # Normalize proportionally
        return PriorityWeightsDTO(
            id=self.id,
            project_id=self.project_id,
            valor_weight=self.valor_weight / total,
            risco_weight=self.risco_weight / total,
            esforco_weight=self.esforco_weight / total,
            alinhamento_weight=self.alinhamento_weight / total,
            confidence_weight=self.confidence_weight / total,
            created_at=self.created_at,
            updated_at=self.updated_at
        )
    
    def __str__(self) -> str:
        """String representation for debugging"""
        return (f"PriorityWeights(project={self.project_id}, "
                f"valor={self.valor_weight:.3f}, "
                f"risco={self.risco_weight:.3f}, "
                f"esforco={self.esforco_weight:.3f}, "
                f"alinhamento={self.alinhamento_weight:.3f}, "
                f"confidence={self.confidence_weight:.3f})")
    
    def __repr__(self) -> str:
        """Developer-friendly representation"""
        return (f"PriorityWeightsDTO(id={self.id}, project_id={self.project_id}, "
                f"weights=[{self.valor_weight:.4f}, {self.risco_weight:.4f}, "
                f"{self.esforco_weight:.4f}, {self.alinhamento_weight:.4f}, "
                f"{self.confidence_weight:.4f}])")