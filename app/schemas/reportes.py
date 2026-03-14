from pydantic import BaseModel
from typing import List
from datetime import date

# ======================
# VENTAS
# ======================

class VentaDia(BaseModel):
    fecha: date
    pedidos: int
    total: float


class ReporteVentas(BaseModel):
    total_ingresos: float
    total_pedidos: int
    ticket_promedio: float
    detalle: List[VentaDia]


# ======================
# PRODUCTOS MÁS VENDIDOS
# ======================

class ProductoVendido(BaseModel):
    producto_id: int
    nombre: str
    cantidad: int
    total: float


# ======================
# OPCIONES / TOPPINGS
# ======================

class OpcionReporte(BaseModel):
    tipo_opcion: str
    nombre_opcion: str
    cantidad: int
    total_adicional: float


# ======================
# CATEGORÍAS
# ======================

class CategoriaVenta(BaseModel):
    categoria_id: int
    nombre: str
    pedidos: int
    total: float


# ======================
# HORAS PICO
# ======================

class HoraPico(BaseModel):
    hora: int
    pedidos: int
    total: float


# ======================
# ESTADO PEDIDOS
# ======================

class EstadoPedidoReporte(BaseModel):
    estado: str
    cantidad: int


class PedidoDetalle(BaseModel):
    id_pedido: int
    fecha: str
    estado: str
    cliente: str
    total: float


class PedidoEstadoResumen(BaseModel):
    estado: str
    cantidad: int


class ReportePedidos(BaseModel):
    total_pedidos: int
    total_ingresos: float
    por_estado: List[PedidoEstadoResumen]
    detalle: List[PedidoDetalle]