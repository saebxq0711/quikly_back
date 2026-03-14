from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.pedido import Pedido
from app.models.restaurante import Restaurante
from app.models.pedido_producto import PedidoProducto
from datetime import date


# ===============================
# DASHBOARD SUMMARY
# ===============================
async def get_pedidos_summary(db, from_date, to_date):
    query = select(
        func.count(Pedido.id_pedido).label("total_pedidos"),
        func.coalesce(
            func.sum(case((Pedido.estado_id == 7, Pedido.total), else_=0)),
            0
        ).label("total_vendido"),
        func.coalesce(
            func.avg(case((Pedido.estado_id == 7, Pedido.total))),
            0
        ).label("ticket_promedio"),
        func.sum(case((Pedido.estado_id == 4, 1), else_=0)).label("en_preparacion"),
        func.sum(case((Pedido.estado_id == 5, 1), else_=0)).label("pendiente"),
        func.sum(case((Pedido.estado_id == 6, 1), else_=0)).label("rechazado"),
        func.sum(case((Pedido.estado_id == 7, 1), else_=0)).label("entregado"),
    ).where(
        Pedido.fecha_creacion.between(from_date, to_date)
    )

    result = await db.execute(query)
    row = result.one()

    return {
        "total_pedidos": row.total_pedidos,
        "total_vendido": float(row.total_vendido),
        "ticket_promedio": float(row.ticket_promedio),
        "estados": {
            "en_preparacion": row.en_preparacion,
            "pendiente": row.pendiente,
            "rechazado": row.rechazado,
            "entregado": row.entregado,
        }
    }


# ===============================
# TOP RESTAURANTES
# ===============================
async def get_top_restaurants_by_sales(db, from_date, to_date, limit=3):
    query = (
        select(
            Restaurante.id_restaurante,
            Restaurante.nombre,
            func.count(Pedido.id_pedido).label("pedidos"),
            func.sum(Pedido.total).label("total_vendido")
        )
        .join(Restaurante, Restaurante.id_restaurante == Pedido.restaurante_id)
        .where(
            Pedido.estado_id == 7,  # solo pedidos entregados
            Pedido.fecha_creacion.between(from_date, to_date)
        )
        .group_by(Restaurante.id_restaurante, Restaurante.nombre)
        .order_by(func.sum(Pedido.total).desc())
        .limit(limit)
    )

    result = await db.execute(query)
    rows = result.all()

    return [
        {
            "restaurante_id": r.id_restaurante,
            "restaurante": r.nombre,
            "pedidos": r.pedidos,
            "total_vendido": float(r.total_vendido),
        }
        for r in rows
    ]


# ===============================
# TOP PRODUCTOS
# ===============================
async def get_top_products(db, from_date, to_date, limit=5):
    query = (
        select(
            PedidoProducto.nombre_producto,
            func.sum(PedidoProducto.cantidad).label("cantidad"),
            func.sum(PedidoProducto.subtotal).label("total")
        )
        .join(Pedido, Pedido.id_pedido == PedidoProducto.pedido_id)
        .where(
            Pedido.estado_id == 7,  # solo entregados
            Pedido.fecha_creacion.between(from_date, to_date)
        )
        .group_by(PedidoProducto.nombre_producto)
        .order_by(func.sum(PedidoProducto.cantidad).desc())
        .limit(limit)
    )

    result = await db.execute(query)
    rows = result.all()

    return [
        {
            "producto": r.nombre_producto,
            "cantidad": r.cantidad,
            "total_vendido": float(r.total),
        }
        for r in rows
    ]


# ===============================
# LISTADO DE PEDIDOS
# ===============================
async def get_pedidos(
    db: AsyncSession,
    from_date: date,
    to_date: date,
    restaurante_id: int | None = None,
    estado_id: int | None = None,
    page: int = 1,
    limit: int = 20,
):
    offset = (page - 1) * limit

    query = (
        select(
            Pedido.id_pedido,
            Restaurante.nombre.label("restaurante"),
            Pedido.cliente_nombres.label("cliente"),
            Pedido.total,
            Pedido.estado_id.label("estado_id"),  # devolver ID real
            Pedido.fecha_creacion.label("fecha"),
        )
        .join(Restaurante, Restaurante.id_restaurante == Pedido.restaurante_id)
        .where(Pedido.fecha_creacion.between(from_date, to_date))
    )

    if restaurante_id:
        query = query.where(Pedido.restaurante_id == restaurante_id)

    if estado_id:
        query = query.where(Pedido.estado_id == estado_id)  # filtrar por estado real

    query = query.order_by(Pedido.fecha_creacion.desc())

    total_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(total_query)).scalar()

    result = await db.execute(
        query.offset(offset).limit(limit)
    )

    return {
        "items": [dict(row._mapping) for row in result],
        "total": total,
    }


async def get_pedidos_by_restaurante(
    db: AsyncSession,
    restaurante_id: int,
    from_date: date | None = None,
    to_date: date | None = None,
    page: int = 1,
    limit: int = 20,
):
    if not from_date:
        from_date = date(2000, 1, 1)
    if not to_date:
        to_date = date.today()

    return await get_pedidos(
        db=db,
        from_date=from_date,
        to_date=to_date,
        restaurante_id=restaurante_id,
        page=page,
        limit=limit,
    )
