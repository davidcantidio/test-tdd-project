"""Infrastructure Mappers - Data Transformation

Mappers for converting data between different representations.

Future mappers (História 3.2):
    - ProductVisionMapper: Entity ↔ DTO mapping
    - EpicMapper: Epic entity ↔ DTO with AI fields
    - ProjectMapper: Project data mapping
    - DTOEntityMapper: Generic mapping utilities

Status: História 1.1 Complete - Structure Ready
Next: História 3.2 - Mapper Implementation
"""

from .product_vision_mapper import ProductVisionMapper

__all__: list[str] = [
    "ProductVisionMapper",
]
