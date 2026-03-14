from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.schemas.reportes import (
    ReporteVentas,
    ProductoVendido,
    OpcionReporte,
    CategoriaVenta,
    HoraPico,
    EstadoPedidoReporte,
)
from app.repositories.admin import reportes_repo
from app.db.database import get_db
from app.core.security import get_admin_user
from app.schemas.auth import AdminContext
from app.schemas.reportes import ReportePedidos

from datetime import date, datetime

router = APIRouter(
    prefix="/admin/reportes",
    tags=["Admin - Reportes"],
)

# =====================================================
# 1️⃣ REPORTE DE VENTAS
# =====================================================
@router.get("/ventas", response_model=ReporteVentas)
async def reporte_ventas(
    desde: str | None = None,
    hasta: str | None = None,
    session: AsyncSession = Depends(get_db),
    admin: AdminContext = Depends(get_admin_user),
):
    desde_dt: date | None = None
    hasta_dt: date | None = None

    if desde:
        desde_dt = datetime.strptime(desde, "%Y-%m-%d").date()

    if hasta:
        hasta_dt = datetime.strptime(hasta, "%Y-%m-%d").date()

    pedidos, total, detalle = await reportes_repo.ventas(
        session,
        admin.restaurante_id,
        desde_dt,
        hasta_dt,
    )

    return {
        "total_ingresos": float(total),
        "total_pedidos": pedidos,
        "ticket_promedio": float(total / pedidos) if pedidos else 0,
        "detalle": [
            {
                "fecha": d.fecha,
                "pedidos": d.pedidos,
                "total": float(d.total),
            }
            for d in detalle
        ],
    }


# =====================================================
# 2️⃣ PRODUCTOS MÁS VENDIDOS
# =====================================================
@router.get(
    "/productos",
    response_model=List[ProductoVendido],
)
async def reporte_productos(
    session: AsyncSession = Depends(get_db),
    admin: AdminContext = Depends(get_admin_user),
):
    rows = await reportes_repo.productos_mas_vendidos(
        session,
        admin.restaurante_id,
    )

    return [
        ProductoVendido(
            producto_id=r.producto_id,
            nombre=r.nombre_producto,
            cantidad=r.cantidad,
            total=float(r.total),
        )
        for r in rows
    ]


# =====================================================
# 3️⃣ OPCIONES / TOPPINGS
# =====================================================
@router.get(
    "/opciones",
    response_model=List[OpcionReporte],
)
async def reporte_opciones(
    session: AsyncSession = Depends(get_db),
    admin: AdminContext = Depends(get_admin_user),
):
    rows = await reportes_repo.opciones_mas_usadas(
        session,
        admin.restaurante_id,
    )

    return [
        OpcionReporte(
            tipo_opcion=r.tipo_opcion,
            nombre_opcion=r.nombre_opcion,
            cantidad=r.cantidad,
            total_adicional=float(r.total),
        )
        for r in rows
    ]


# =====================================================
# 4️⃣ VENTAS POR CATEGORÍA
# =====================================================
@router.get(
    "/categorias",
    response_model=List[CategoriaVenta],
)
async def reporte_categorias(
    session: AsyncSession = Depends(get_db),
    admin: AdminContext = Depends(get_admin_user),
):
    rows = await reportes_repo.ventas_por_categoria(
        session,
        admin.restaurante_id,
    )

    return [
        CategoriaVenta(
            categoria_id=r.id_categoria,
            nombre=r.nombre,
            pedidos=r.pedidos,
            total=float(r.total),
        )
        for r in rows
    ]


# =====================================================
# 5️⃣ HORAS PICO
# =====================================================
@router.get(
    "/horas-pico",
    response_model=List[HoraPico],
)
async def reporte_horas_pico(
    session: AsyncSession = Depends(get_db),
    admin: AdminContext = Depends(get_admin_user),
):
    rows = await reportes_repo.horas_pico(
        session,
        admin.restaurante_id,
    )

    return [
        HoraPico(
            hora=int(r.hora),
            pedidos=r.pedidos,
            total=float(r.total),
        )
        for r in rows
    ]


# =====================================================
# 6️⃣ ESTADO DE PEDIDOS
# =====================================================
@router.get(
    "/estado-pedidos",
    response_model=List[EstadoPedidoReporte],
)
async def reporte_estado_pedidos(
    session: AsyncSession = Depends(get_db),
    admin: AdminContext = Depends(get_admin_user),
):
    rows = await reportes_repo.estado_pedidos(
        session,
        admin.restaurante_id,
    )

    return [
        EstadoPedidoReporte(
            estado=r.nombre,
            cantidad=r.cantidad,
        )
        for r in rows
    ]

# =====================================================
# 7️⃣ REPORTE DE CLIENTES
# =====================================================
@router.get(
    "/clientes",
    response_model=List[dict],
)
async def reporte_clientes(
    session: AsyncSession = Depends(get_db),
    admin: AdminContext = Depends(get_admin_user),
):
    rows = await reportes_repo.clientes(
        session,
        admin.restaurante_id,
    )

    return [
        {
            "cliente": r.cliente,
            "pedidos": r.pedidos,
            "total": float(r.total),
        }
        for r in rows
    ]

@router.get(
    "/pedidos",
    response_model=ReportePedidos,
)
async def reporte_pedidos(
    desde: str | None = None,
    hasta: str | None = None,
    session: AsyncSession = Depends(get_db),
    admin: AdminContext = Depends(get_admin_user),
):
    desde_dt = datetime.strptime(desde, "%Y-%m-%d") if desde else None
    hasta_dt = datetime.strptime(hasta, "%Y-%m-%d") if hasta else None

    resumen, estados, detalle = await reportes_repo.pedidos(
        session,
        admin.restaurante_id,
        desde_dt,
        hasta_dt,
    )

    return {
        "total_pedidos": resumen.total_pedidos,
        "total_ingresos": float(resumen.total_ingresos),
        "por_estado": [
            {
                "estado": e.estado,
                "cantidad": e.cantidad,
            }
            for e in estados
        ],
        "detalle": [
            {
                "id_pedido": d.id_pedido,
                "fecha": d.fecha_creacion.strftime("%Y-%m-%d %H:%M"),
                "estado": d.estado,
                "cliente": d.cliente,
                "total": float(d.total),
            }
            for d in detalle
        ],
    }