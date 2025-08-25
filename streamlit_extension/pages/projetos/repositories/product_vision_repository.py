# streamlit_extension/pages/projetos/repositories/product_vision_repository.py
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import json

@dataclass
class ProductVisionEntity:
    """Product Vision Entity for repository pattern"""
    id: Optional[int] = None
    project_id: Optional[int] = None
    vision_statement: str = ""
    problem_statement: str = ""
    target_audience: str = ""
    value_proposition: str = ""
    constraints: List[str] = None
    
    def __post_init__(self):
        if self.constraints is None:
            self.constraints = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for persistence"""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "vision_statement": self.vision_statement,
            "problem_statement": self.problem_statement,
            "target_audience": self.target_audience,
            "value_proposition": self.value_proposition,
            "constraints": self.constraints,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProductVisionEntity':
        """Create from dictionary (from persistence)"""
        constraints = data.get("constraints", [])
        if isinstance(constraints, str):
            try:
                constraints = json.loads(constraints)
            except json.JSONDecodeError:
                constraints = []
        
        return cls(
            id=data.get("id"),
            project_id=data.get("project_id"),
            vision_statement=data.get("vision_statement", ""),
            problem_statement=data.get("problem_statement", ""),
            target_audience=data.get("target_audience", ""),
            value_proposition=data.get("value_proposition", ""),
            constraints=constraints if isinstance(constraints, list) else [],
        )

class ProductVisionRepository(ABC):
    """Abstract repository for Product Vision persistence"""
    
    @abstractmethod
    def save_draft(self, product_vision: ProductVisionEntity) -> ProductVisionEntity:
        """Save product vision draft, returns entity with ID"""
        pass
    
    @abstractmethod
    def get_by_project_id(self, project_id: int) -> Optional[ProductVisionEntity]:
        """Get product vision by project ID"""
        pass
    
    @abstractmethod
    def get_by_id(self, pv_id: int) -> Optional[ProductVisionEntity]:
        """Get product vision by its ID"""
        pass
    
    @abstractmethod
    def delete_by_project_id(self, project_id: int) -> bool:
        """Delete product vision for a project"""
        pass

class InMemoryProductVisionRepository(ProductVisionRepository):
    """In-memory implementation for testing and development"""
    
    def __init__(self):
        self._storage: Dict[int, ProductVisionEntity] = {}
        self._next_id: int = 1
        self._project_index: Dict[int, int] = {}  # project_id -> pv_id
    
    def save_draft(self, product_vision: ProductVisionEntity) -> ProductVisionEntity:
        """Save product vision draft, returns entity with ID"""
        if product_vision.id is None:
            product_vision.id = self._next_id
            self._next_id += 1
        
        self._storage[product_vision.id] = product_vision
        
        if product_vision.project_id:
            self._project_index[product_vision.project_id] = product_vision.id
        
        return product_vision
    
    def get_by_project_id(self, project_id: int) -> Optional[ProductVisionEntity]:
        """Get product vision by project ID"""
        if project_id in self._project_index:
            pv_id = self._project_index[project_id]
            return self._storage.get(pv_id)
        return None
    
    def get_by_id(self, pv_id: int) -> Optional[ProductVisionEntity]:
        """Get product vision by its ID"""
        return self._storage.get(pv_id)
    
    def delete_by_project_id(self, project_id: int) -> bool:
        """Delete product vision for a project"""
        if project_id in self._project_index:
            pv_id = self._project_index[project_id]
            del self._storage[pv_id]
            del self._project_index[project_id]
            return True
        return False

class DatabaseProductVisionRepository(ProductVisionRepository):
    """Database implementation using the existing database layer"""
    
    def __init__(self, db_manager=None):
        # Import here to avoid circular imports
        if db_manager is None:
            from streamlit_extension.utils.database import DatabaseManager
            self.db_manager = DatabaseManager()
        else:
            self.db_manager = db_manager
    
    def save_draft(self, product_vision: ProductVisionEntity) -> ProductVisionEntity:
        """Save product vision draft to database"""
        conn = self.db_manager.get_connection()
        try:
            constraints_json = json.dumps(product_vision.constraints)
            
            if product_vision.id is None:
                # Insert new
                cursor = conn.execute("""
                    INSERT INTO product_visions 
                    (project_id, vision_statement, problem_statement, 
                     target_audience, value_proposition, constraints)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    product_vision.project_id,
                    product_vision.vision_statement,
                    product_vision.problem_statement,
                    product_vision.target_audience,
                    product_vision.value_proposition,
                    constraints_json
                ))
                product_vision.id = cursor.lastrowid
            else:
                # Update existing
                conn.execute("""
                    UPDATE product_visions 
                    SET project_id = ?, vision_statement = ?, problem_statement = ?,
                        target_audience = ?, value_proposition = ?, constraints = ?
                    WHERE id = ?
                """, (
                    product_vision.project_id,
                    product_vision.vision_statement,
                    product_vision.problem_statement,
                    product_vision.target_audience,
                    product_vision.value_proposition,
                    constraints_json,
                    product_vision.id
                ))
            
            conn.commit()
            return product_vision
            
        except Exception as e:
            conn.rollback()
            raise ValueError(f"Failed to save product vision: {e}")
        finally:
            conn.close()
    
    def get_by_project_id(self, project_id: int) -> Optional[ProductVisionEntity]:
        """Get product vision by project ID"""
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute("""
                SELECT id, project_id, vision_statement, problem_statement,
                       target_audience, value_proposition, constraints
                FROM product_visions 
                WHERE project_id = ?
            """, (project_id,))
            
            row = cursor.fetchone()
            if row:
                data = dict(row)
                return ProductVisionEntity.from_dict(data)
            return None
            
        finally:
            conn.close()
    
    def get_by_id(self, pv_id: int) -> Optional[ProductVisionEntity]:
        """Get product vision by its ID"""
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute("""
                SELECT id, project_id, vision_statement, problem_statement,
                       target_audience, value_proposition, constraints
                FROM product_visions 
                WHERE id = ?
            """, (pv_id,))
            
            row = cursor.fetchone()
            if row:
                data = dict(row)
                return ProductVisionEntity.from_dict(data)
            return None
            
        finally:
            conn.close()
    
    def delete_by_project_id(self, project_id: int) -> bool:
        """Delete product vision for a project"""
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute("""
                DELETE FROM product_visions WHERE project_id = ?
            """, (project_id,))
            
            success = cursor.rowcount > 0
            conn.commit()
            return success
            
        except Exception:
            conn.rollback()
            return False
        finally:
            conn.close()