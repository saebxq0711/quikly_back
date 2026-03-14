from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta

from app.models.usuario import Usuario
from app.models.usuarios_rol import UsuarioRol
from app.models.restaurante import Restaurante
from app.models.pedido import Pedido
from app.models.pedido_producto import PedidoProducto


# =====================================================
# KPIs USUARIOS
# =====================================================
async def get_user_kpis(db: AsyncSession):
    total = (await db.execute(select(func.count(Usuario.id_usuario)))).scalar() or 0
    activos = (await db.execute(select(func.count(Usuario.id_usuario)).where(Usuario.estado_id == 1))).scalar() or 0
    inactivos = (await db.execute(select(func.count(Usuario.id_usuario)).where(Usuario.estado_id != 1))).scalar() or 0

    roles_stmt = select(UsuarioRol.rol_id, func.count(UsuarioRol.user_id)).group_by(UsuarioRol.rol_id)
    roles_result = await db.execute(roles_stmt)
    rol_map = {1: "SuperAdmin", 2: "Admin Restaurante", 3: "Cliente"}
    por_rol = [{"rol": rol_map.get(rol_id, f"Rol {rol_id}"), "total": count} for rol_id, count in roles_result.all()]

    return {
        "total": total,
        "activos": activos,
        "inactivos": inactivos,
        "por_rol": por_rol,
    }


# =====================================================
# KPIs RESTAURANTES
# =====================================================
async def get_restaurant_kpis(db: AsyncSession):
    total = (await db.execute(select(func.count(Restaurante.id_restaurante)))).scalar() or 0
    activos = (await db.execute(select(func.count(Restaurante.id_restaurante)).where(Restaurante.estado_id == 1))).scalar() or 0
    inactivos = (await db.execute(select(func.count(Restaurante.id_restaurante)).where(Restaurante.estado_id != 1))).scalar() or 0

    ranking_stmt = (
        select(
            Restaurante.nombre,
            func.count(Pedido.id_pedido).label("total_pedidos"),
            func.sum(case((Pedido.estado_id==5,1), else_=0)).label("pendientes"),
            func.sum(case((Pedido.estado_id==6,1), else_=0)).label("rechazados"),
            func.coalesce(func.sum(Pedido.total), 0).label("ingresos"),
            (func.coalesce(func.sum(Pedido.total),0) / func.nullif(func.count(Pedido.id_pedido),0)).label("ticket_promedio")
        )
        .outerjoin(Pedido, Pedido.restaurante_id == Restaurante.id_restaurante)
        .group_by(Restaurante.nombre)
        .order_by(func.count(Pedido.id_pedido).desc())
        .limit(5)
    )
    
    ranking_result = await db.execute(ranking_stmt)
    por_restaurante = [
        {
            "nombre": r.nombre,
            "total_pedidos": r.total_pedidos or 0,
            "pedidos_pendientes": r.pendientes or 0,
            "pedidos_rechazados": r.rechazados or 0,
            "ingresos": float(r.ingresos or 0),
            "ticket_promedio": float(r.ticket_promedio or 0)
        }
        for r in ranking_result.mappings().all()
    ]

    return {
        "total": total,
        "activos": activos,
        "inactivos": inactivos,
        "por_restaurante": por_restaurante,
    }


# =====================================================
# KPIs PEDIDOS
# =====================================================
async def get_order_kpis(db: AsyncSession):
    today = date.today()
    week_start = today - timedelta(days=7)
    month_start = today.replace(day=1)

    total = (await db.execute(select(func.count(Pedido.id_pedido)))).scalar() or 0
    hoy = (await db.execute(select(func.count(Pedido.id_pedido)).where(func.date(Pedido.fecha_creacion) == today))).scalar() or 0
    semana = (await db.execute(select(func.count(Pedido.id_pedido)).where(Pedido.fecha_creacion >= week_start))).scalar() or 0
    mes = (await db.execute(select(func.count(Pedido.id_pedido)).where(Pedido.fecha_creacion >= month_start))).scalar() or 0

    estados_map = {4: "Aprobado", 5: "Pendiente", 6: "Rechazado", 7: "Entregado"}
    estados_stmt = select(Pedido.estado_id, func.count(Pedido.id_pedido)).group_by(Pedido.estado_id)
    result = await db.execute(estados_stmt)
    por_estado = [{"estado": estados_map.get(eid, "Otro"), "total": t} for eid, t in result.all()]

    ingresos = float((await db.execute(select(func.coalesce(func.sum(Pedido.total), 0)))).scalar() or 0)
    ticket_promedio = ingresos / total if total > 0 else 0

    return {
        "total": total,
        "hoy": hoy,
        "semana": semana,
        "mes": mes,
        "ingresos": ingresos,
        "ticket_promedio": ticket_promedio,
        "por_estado": por_estado,
    }


# =====================================================
# TOP PRODUCTOS GLOBALES
# =====================================================
async def get_top_products(db: AsyncSession, limit: int = 10):
    stmt = (
        select(
            PedidoProducto.nombre_producto.label("producto"),
            func.sum(PedidoProducto.cantidad).label("cantidad"),
            func.sum(PedidoProducto.subtotal).label("total_vendido"),
        )
        .group_by(PedidoProducto.nombre_producto)
        .order_by(func.sum(PedidoProducto.cantidad).desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.mappings().all()


# =====================================================
# DATOS RECIENTES
# =====================================================
async def get_recent_data(db: AsyncSession):
    pedidos_stmt = select(Pedido).order_by(Pedido.fecha_creacion.desc()).limit(10)
    restaurantes_stmt = select(Restaurante).order_by(Restaurante.fecha_creacion.desc()).limit(5)
    usuarios_stmt = select(Usuario).order_by(Usuario.fecha_creacion.desc()).limit(5)

    pedidos = (await db.execute(pedidos_stmt)).scalars().all()
    restaurantes = (await db.execute(restaurantes_stmt)).scalars().all()
    usuarios = (await db.execute(usuarios_stmt)).scalars().all()

    return {
        "pedidos": pedidos,
        "restaurantes": restaurantes,
        "usuarios": usuarios,
    }
