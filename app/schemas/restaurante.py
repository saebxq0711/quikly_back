# app/schemas/restaurant.py
from pydantic import BaseModel, EmailStr
from typing import List, Dict
from datetime import datetime

class RestauranteOut(BaseModel):
    id_restaurante: int
    nit: int
    nombre: str
    logo: str | None
    color_primario: str | None
    color_secundario: str | None
    estado_id: int
    fecha_creacion: datetime

    class Config:
        orm_mode = True

class RestauranteStatsOut(BaseModel):
    Activos: int
    Inactivos: int
    Eliminados: int

class UsuarioOut(BaseModel):
    id_usuario: int
    correo: str

    class Config:
        orm_mode = True

class RestauranteDetailOut(RestauranteOut):
    """
    Detalle completo del restaurante
    (puedes extender luego con más campos)
    """
    pass

class TopProductoOut(BaseModel):
    producto: str
    cantidad: int
    total_vendido: float

class RestauranteStatsDetailOut(BaseModel):
    total_pedidos: int
    total_vendido: float
    ticket_promedio: float
    estados: Dict[str, int]
    top_productos: List[TopProductoOut]


class RestauranteCreate(BaseModel):
    nit: int
    nombre: str
    logo: str | None = None
    color_primario: str | None = None
    color_secundario: str | None = None

    admin_nombres: str
    admin_apellidos: str
    admin_documento: str
    admin_telefono: str
    admin_correo: EmailStr
    admin_contrasena: str