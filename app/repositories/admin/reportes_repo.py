from sqlalchemy import text, select, func, literal
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.pedido import Pedido

from datetime import date

async def ventas(
    session: AsyncSession,
    restaurante_id: int,
    desde: date | None,
    hasta: date | None,
):
    where = ["p.restaurante_id = :restaurante_id"]
    params = {"restaurante_id": restaurante_id}

    if desde:
        where.append("p.fecha_creacion >= :desde")
        params["desde"] = desde

    if hasta:
        where.append("p.fecha_creacion <= :hasta")
        params["hasta"] = hasta

    query = text(f"""
        SELECT
            DATE(p.fecha_creacion) AS fecha,
            COUNT(*) AS pedidos,
            SUM(p.total) AS total
        FROM pedido p
        WHERE {" AND ".join(where)}
        GROUP BY DATE(p.fecha_creacion)
        ORDER BY fecha
    """)

    result = await session.execute(query, params)
    detalle = result.fetchall()

    resumen = await session.execute(
        text(f"""
            SELECT
                COUNT(*) AS pedidos,
                COALESCE(SUM(total),0) AS total
            FROM pedido p
            WHERE {" AND ".join(where)}
        """),
        params,
    )

    row = resumen.first()

    return row.pedidos, row.total, detalle


async def productos_mas_vendidos(session: AsyncSession, restaurante_id: int):
    result = await session.execute(text("""
        SELECT
            pp.producto_id,
            pp.nombre_producto,
            SUM(pp.cantidad) AS cantidad,
            SUM(pp.subtotal) AS total
        FROM pedido_producto pp
        JOIN pedido p ON p.id_pedido = pp.pedido_id
        WHERE p.restaurante_id = :restaurante_id
        GROUP BY pp.producto_id, pp.nombre_producto
        ORDER BY cantidad DESC
        LIMIT 10
    """), {"restaurante_id": restaurante_id})

    return result.fetchall()


async def opciones_mas_usadas(session: AsyncSession, restaurante_id: int):
    result = await session.execute(text("""
        SELECT
            ppo.tipo_opcion,
            ppo.nombre_opcion,
            COUNT(*) AS cantidad,
            SUM(ppo.precio_adicional) AS total
        FROM pedido_producto_opcion ppo
        JOIN pedido_producto pp ON pp.id_pedido_producto = ppo.pedido_producto_id
        JOIN pedido p ON p.id_pedido = pp.pedido_id
        WHERE p.restaurante_id = :restaurante_id
        GROUP BY ppo.tipo_opcion, ppo.nombre_opcion
        ORDER BY cantidad DESC
    """), {"restaurante_id": restaurante_id})

    return result.fetchall()


async def ventas_por_categoria(session: AsyncSession, restaurante_id: int):
    result = await session.execute(text("""
        SELECT
            c.id_categoria,
            c.nombre,
            COUNT(DISTINCT p.id_pedido) AS pedidos,
            SUM(pp.subtotal) AS total
        FROM categoria c
        JOIN producto pr ON pr.categoria_id = c.id_categoria
        JOIN pedido_producto pp ON pp.producto_id = pr.id_producto
        JOIN pedido p ON p.id_pedido = pp.pedido_id
        WHERE p.restaurante_id = :restaurante_id
        GROUP BY c.id_categoria, c.nombre
        ORDER BY total DESC
    """), {"restaurante_id": restaurante_id})

    return result.fetchall()


async def horas_pico(session: AsyncSession, restaurante_id: int):
    result = await session.execute(text("""
        SELECT
            EXTRACT(HOUR FROM p.fecha_creacion) AS hora,
            COUNT(*) AS pedidos,
            SUM(p.total) AS total
        FROM pedido p
        WHERE p.restaurante_id = :restaurante_id
        GROUP BY hora
        ORDER BY hora
    """), {"restaurante_id": restaurante_id})

    return result.fetchall()



async def estado_pedidos(session: AsyncSession, restaurante_id: int):
    result = await session.execute(text("""
        SELECT
            e.nombre,
            COUNT(*) AS cantidad
        FROM pedido p
        JOIN estado e ON e.id_estado = p.estado_id
        WHERE p.restaurante_id = :restaurante_id
        GROUP BY e.nombre
    """), {"restaurante_id": restaurante_id})

    return result.fetchall()


async def clientes(
    session: AsyncSession,
    restaurante_id: int,
):
    stmt = (
        select(
            Pedido.cliente_identificacion,
            Pedido.cliente_nombres,
            Pedido.cliente_correo,
            Pedido.cliente_telefono,
            func.count(Pedido.id_pedido).label("pedidos"),
            func.coalesce(func.sum(Pedido.total), 0).label("total"),
        )
        .where(Pedido.restaurante_id == restaurante_id)
        .group_by(
            Pedido.cliente_identificacion,
            Pedido.cliente_nombres,
            Pedido.cliente_correo,
            Pedido.cliente_telefono,
        )
        .order_by(func.sum(Pedido.total).desc())
    )

    result = await session.execute(stmt)
    return result.all()


async def pedidos(
    session: AsyncSession,
    restaurante_id: int,
    desde=None,
    hasta=None,
    page: int = 1,
    limit: int = 20,
):
    where = ["p.restaurante_id = :restaurante_id"]
    params = {"restaurante_id": restaurante_id}
    offset = (page - 1) * limit

    params["limit"] = limit
    params["offset"] = offset

    if desde:
        where.append("p.fecha_creacion >= :desde")
        params["desde"] = desde

    if hasta:
        where.append("p.fecha_creacion <= :hasta")
        params["hasta"] = hasta

    # ======================
    # RESUMEN
    # ======================
    resumen = await session.execute(
        text(f"""
            SELECT
                COUNT(*) AS total_pedidos,
                COALESCE(SUM(p.total), 0) AS total_ingresos
            FROM pedido p
            WHERE {" AND ".join(where)}
        """),
        params,
    )

    resumen_row = resumen.first()

    # ======================
    # POR ESTADO
    # ======================
    estados = await session.execute(
        text(f"""
            SELECT
                e.nombre AS estado,
                COUNT(*) AS cantidad
            FROM pedido p
            JOIN estado e ON e.id_estado = p.estado_id
            WHERE {" AND ".join(where)}
            GROUP BY e.nombre
        """),
        params,
    )

    # ======================
    # DETALLE
    # ======================
    detalle = await session.execute(
        text(f"""
            SELECT
                p.id_pedido,
                p.fecha_creacion,
                e.nombre AS estado,
                COALESCE(p.cliente_nombres, 'Consumidor final') AS cliente,
                p.total
            FROM pedido p
            JOIN estado e ON e.id_estado = p.estado_id
            WHERE {" AND ".join(where)}
            ORDER BY p.fecha_creacion DESC
            LIMIT :limit OFFSET :offset
        """),
        params,
    )

    total_query = await session.execute(
        text(f"""
            SELECT COUNT(*) as total
            FROM pedido p
            WHERE {" AND ".join(where)}
        """),
        params,
    )

    total_registros = total_query.first().total

    return (
        resumen_row,
        estados.fetchall(),
        detalle.fetchall(),
        total_registros
    )