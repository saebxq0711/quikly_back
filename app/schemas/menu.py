from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal

class ProductoOut(BaseModel):
    id_producto: int
    nombre: str
    descripcion: Optional[str] = None
    precio_base: Decimal
    img_producto: Optional[str] = None
    estado_id: int

class CategoriaOrdenIn(BaseModel):
    id_categoria: int
    orden: int

class CategoriaOut(BaseModel):
    id_categoria: int
    nombre: str
    img_categoria: Optional[str] = None
    orden: int
    estado_id: int
    productos: List[ProductoOut] = []

class MenuRestauranteOut(BaseModel):
    categorias: List[CategoriaOut]
