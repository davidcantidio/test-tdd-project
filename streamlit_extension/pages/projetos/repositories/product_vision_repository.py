# streamlit_extension/pages/projetos/repositories/product_vision_repository.py
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import json

# -------------------- Domain Entity --------------------

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
            "constraints": list(self.constraints or []),
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
        if not isinstance(constraints, list):
            constraints = []
        # normaliza p/ strings não vazias
        constraints = [str(x).strip() for x in constraints if isinstance(x, str) and x.strip()]

        return cls(
            id=data.get("id"),
            project_id=data.get("project_id"),
            vision_statement=data.get("vision_statement", ""),
            problem_statement=data.get("problem_statement", ""),
            target_audience=data.get("target_audience", ""),
            value_proposition=data.get("value_proposition", ""),
            constraints=constraints,
        )

# -------------------- Abstract Port --------------------

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

# -------------------- In-Memory Impl (Entity API + Facade save/load) --------------------

class InMemoryProductVisionRepository(ProductVisionRepository):
    """
    In-memory implementation for testing and development.

    Mantém a API rica baseada em Entity (save_draft/get_by_project_id/etc) e
    expõe também um FAÇADE simples compatível com os testes do controller:
        - save(project_id: str, data: Dict[str, Any]) -> None
        - load(project_id: str) -> Dict[str, Any]
    """

    def __init__(self):
        # armazenamento por ID (Entity API)
        self._storage: Dict[int, ProductVisionEntity] = {}
        self._next_id: int = 1
        self._project_index: Dict[int, int] = {}  # project_id (int) -> pv_id

        # armazenamento chave-valor por project_id (string) para testes
        self._kv_store: Dict[str, Dict[str, Any]] = {}

    # ---------- Entity API ----------
    def save_draft(self, product_vision: ProductVisionEntity) -> ProductVisionEntity:
        """Save product vision draft, returns entity with ID"""
        if product_vision.id is None:
            product_vision.id = self._next_id
            self._next_id += 1

        self._storage[product_vision.id] = product_vision

        if product_vision.project_id is not None:
            self._project_index[int(product_vision.project_id)] = product_vision.id

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
            if pv_id in self._storage:
                del self._storage[pv_id]
            del self._project_index[project_id]
            return True
        return False

    # ---------- Facade p/ testes (chave = project_id str) ----------
    def save(self, project_id: str, data: Dict[str, Any]) -> None:
        """
        Facade simples usado pelos testes de controller.
        Salva um payload bruto por project_id (string) no armazenamento KV.
        """
        # normaliza constraints
        constraints = data.get("constraints", [])
        if isinstance(constraints, str):
            try:
                constraints = json.loads(constraints)
            except json.JSONDecodeError:
                constraints = []
        if not isinstance(constraints, list):
            constraints = []
        constraints = [str(x).strip() for x in constraints if isinstance(x, str) and x.strip()]

        normalized = {
            "vision_statement": str(data.get("vision_statement", "")).strip(),
            "problem_statement": str(data.get("problem_statement", "")).strip(),
            "target_audience": str(data.get("target_audience", "")).strip(),
            "value_proposition": str(data.get("value_proposition", "")).strip(),
            "constraints": constraints,
        }
        self._kv_store[str(project_id)] = normalized

    def load(self, project_id: str) -> Dict[str, Any]:
        """
        Facade simples usado pelos testes de controller.
        Retorna uma cópia do payload salvo (ou {} se inexistente).
        """
        stored = self._kv_store.get(str(project_id), {})
        return dict(stored)

# -------------------- Database Impl (Entity API) --------------------

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
