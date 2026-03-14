from sqlalchemy import select, func, cast, extract, Date
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta

from app.models.pedido import Pedido
from app.models.restaurante import Restaurante
from app.models.usuarios_rol import UsuarioRol

# ==========================================
# DASHBOARD ADMIN RESTAURANTE
# ==========================================
async def get_dashboard_kpis(db, restaurante_id):
    # Pedidos hoy
    stmt_pedidos_hoy = select(func.count(Pedido.id_pedido)).where(
        Pedido.restaurante_id == restaurante_id,
        func.date(Pedido.fecha_creacion) == func.current_date()
    )
    pedidos_hoy = (await db.execute(stmt_pedidos_hoy)).scalar()

    # Ventas hoy
    stmt_ventas_hoy = select(func.coalesce(func.sum(Pedido.total), 0)).where(
        Pedido.restaurante_id == restaurante_id,
        func.date(Pedido.fecha_creacion) == func.current_date()
    )
    ventas_hoy = (await db.execute(stmt_ventas_hoy)).scalar()

    # Pedidos activos (por ejemplo estado pendiente/aprobado)
    stmt_pedidos_activos = select(func.count(Pedido.id_pedido)).where(
        Pedido.restaurante_id == restaurante_id,
        Pedido.estado_id.in_([4, 5])  # 4=Aprobado, 5=Pendiente
    )
    pedidos_activos = (await db.execute(stmt_pedidos_activos)).scalar()

    # Ticket promedio
    ticket_promedio = (ventas_hoy / pedidos_hoy) if pedidos_hoy else 0

    return {
        "pedidos_hoy": pedidos_hoy,
        "ventas_hoy": float(ventas_hoy),
        "ticket_promedio": float(ticket_promedio),
        "pedidos_activos": pedidos_activos,
    }


async def get_restaurante_info(
    db: AsyncSession,
    restaurante_id: int
):
    stmt = (
        select(
            Restaurante.id_restaurante,
            Restaurante.nombre,
            Restaurante.logo
        )
        .where(Restaurante.id_restaurante == restaurante_id)
    )

    return (await db.execute(stmt)).mappings().first()


async def get_admin_restaurante_id(
    db,
    user_id: int,
):
    stmt = (
        select(UsuarioRol.restaurante_id)
        .where(
            UsuarioRol.user_id == user_id,
            UsuarioRol.rol_id == 2,  # o ID numérico
        )
        .limit(1)
    )

    result = await db.execute(stmt)
    return result.scalar()

async def get_pedidos_recientes(db, restaurante_id, limit=5):
    stmt = (
        select(Pedido)
        .where(Pedido.restaurante_id == restaurante_id)
        .order_by(Pedido.fecha_creacion.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_pedidos_por_hora(db: AsyncSession, restaurante_id: int):
    stmt = (
        select(
            extract("hour", Pedido.fecha_creacion).label("hora"),
            func.count(Pedido.id_pedido).label("pedidos")
        )
        .where(
            Pedido.restaurante_id == restaurante_id,
            cast(Pedido.fecha_creacion, Date) == date.today()
        )
        .group_by("hora")
        .order_by("hora")
    )
    result = await db.execute(stmt)
    return [{"hora": int(r.hora), "pedidos": r.pedidos} for r in result.all()]

async def get_ventas_por_hora(db: AsyncSession, restaurante_id: int):
    stmt = (
        select(
            extract("hour", Pedido.fecha_creacion).label("hora"),
            func.coalesce(func.sum(Pedido.total), 0).label("ventas")
        )
        .where(
            Pedido.restaurante_id == restaurante_id,
            cast(Pedido.fecha_creacion, Date) == date.today()
        )
        .group_by("hora")
        .order_by("hora")
    )
    result = await db.execute(stmt)
    return [{"hora": int(r.hora), "ventas": float(r.ventas)} for r in result.all()]