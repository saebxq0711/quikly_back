from pydantic import BaseModel
from typing import List
from datetime import datetime


# -------------------------
# PRODUCTOS DEL PEDIDO
# -------------------------

class PedidoProductoOpcionSchema(BaseModel):
    tipo_opcion: str
    nombre_opcion: str
    precio_adicional: float

    model_config = {
        "from_attributes": True
    }


class PedidoProductoSchema(BaseModel):
    id_pedido_producto: int
    nombre_producto: str
    cantidad: int
    precio_base: float
    subtotal: float
    opciones: List[PedidoProductoOpcionSchema] = []

    model_config = {
        "from_attributes": True
    }


# -------------------------
# PEDIDO COMPLETO
# -------------------------

class PedidoSchema(BaseModel):
    id_pedido: int
    cliente_identificacion: str | None
    cliente_nombres: str | None
    cliente_correo: str | None
    cliente_telefono: str | None
    estado_id: int
    total: float
    fecha_creacion: datetime
    productos: List[PedidoProductoSchema] = []

    model_config = {
        "from_attributes": True
    }


# -------------------------
# CREATE PEDIDO (KIOSCO)
# -------------------------

class PhoneSchema(BaseModel):
    indicative: str
    number: str


class CustomerSchema(BaseModel):
    person_type: str
    id_type: str
    identification: str
    first_name: str
    last_name: str
    email: str
    phone: PhoneSchema


class PedidoCreate(BaseModel):
    customer: CustomerSchema