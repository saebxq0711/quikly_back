from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.restaurante import Restaurante
from app.models.usuario import Usuario
from app.models.usuarios_rol import UsuarioRol
from app.models.pedido import Pedido
from app.models.pedido_producto import PedidoProducto
from datetime import datetime
from app.core.security import hash_password


# =====================================================
# LISTADO + BÚSQUEDA RESTAURANTES
# =====================================================
async def get_all_restaurants(
    db: AsyncSession,
    search: str | None = None,
    estado: int | None = None,
    page: int = 1,
    limit: int = 12
):
    stmt = select(Restaurante)

    if search:
        stmt = stmt.where(
            or_(
                Restaurante.nombre.ilike(f"%{search}%"),
                func.cast(Restaurante.id_restaurante, str).ilike(f"%{search}%"),
            )
        )

    if estado is not None:
        stmt = stmt.where(Restaurante.estado_id == estado)

    stmt = stmt.order_by(Restaurante.fecha_creacion.desc())
    result = await db.execute(stmt)
    all_restaurants = result.scalars().all()

    # Paginación
    total = len(all_restaurants)
    total_pages = (total + limit - 1) // limit
    start = (page - 1) * limit
    end = start + limit

    # ✅ Convertir a dicts
    items_dicts = [
        {
            "id_restaurante": r.id_restaurante,
            "nombre": r.nombre,
            "logo": r.logo,
            "estado_id": r.estado_id,
            "fecha_creacion": r.fecha_creacion.isoformat(),
        }
        for r in all_restaurants[start:end]
    ]

    return {"items": items_dicts, "total_pages": total_pages}



# =====================================================
# STATS GLOBALES (DASHBOARD PRINCIPAL)
# =====================================================
async def get_restaurant_stats(db: AsyncSession):
    stmt = (
        select(
            Restaurante.estado_id,
            func.count(Restaurante.id_restaurante)
        )
        .group_by(Restaurante.estado_id)
    )

    result = await db.execute(stmt)

    stats = {1: 0, 2: 0, 3: 0}  # activo / inactivo / eliminado
    for estado_id, count in result.all():
        stats[estado_id] = count

    return {
        "Activos": stats[1],
        "Inactivos": stats[2],
        "Eliminados": stats[3],
    }


# =====================================================
# ADMINS POR RESTAURANTE
# =====================================================
async def get_admins_by_restaurant(db: AsyncSession, restaurante_id: int):
    stmt = (
        select(Usuario)
        .join(UsuarioRol, Usuario.id_usuario == UsuarioRol.user_id)
        .where(UsuarioRol.restaurante_id == restaurante_id)
        .where(UsuarioRol.rol_id == 2)
    )

    result = await db.execute(stmt)
    return result.scalars().all()


# =====================================================
# DETALLE RESTAURANTE (INFO BÁSICA)
# =====================================================
async def get_restaurant_by_id(db: AsyncSession, restaurante_id: int):
    stmt = select(Restaurante).where(
        Restaurante.id_restaurante == restaurante_id
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


# =====================================================
# STATS DEL RESTAURANTE (SUPERADMIN)
# =====================================================
async def get_restaurant_detail_stats(db: AsyncSession, restaurante_id: int):
    # -------------------------------
    # Totales pedidos + ventas
    # -------------------------------
    pedidos_stmt = (
        select(
            func.count(Pedido.id_pedido),
            func.coalesce(func.sum(Pedido.total), 0)
        )
        .where(Pedido.restaurante_id == restaurante_id)
    )

    pedidos_result = await db.execute(pedidos_stmt)
    total_pedidos, total_vendido = pedidos_result.one()

    # -------------------------------
    # Ticket promedio
    # -------------------------------
    ticket_promedio = total_vendido / total_pedidos if total_pedidos > 0 else 0.0

    # -------------------------------
    # Estados pedidos
    # -------------------------------
    estados_stmt = (
        select(
            Pedido.estado_id,
            func.count(Pedido.id_pedido)
        )
        .where(Pedido.restaurante_id == restaurante_id)
        .group_by(Pedido.estado_id)
    )

    estados_result = await db.execute(estados_stmt)

    estados = {
        "aprobado": 0,
        "pendiente": 0,
        "rechazado": 0,
    }

    # estados reales: 4 = aprobado, 5 = pendiente, 6 = rechazado
    for estado_id, count in estados_result.all():
        if estado_id == 4:
            estados["aprobado"] = count
        elif estado_id == 5:
            estados["pendiente"] = count
        elif estado_id == 6:
            estados["rechazado"] = count

    # -------------------------------
    # Top productos vendidos
    # -------------------------------
    productos_stmt = (
        select(
            PedidoProducto.nombre_producto.label("producto"),
            func.sum(PedidoProducto.cantidad).label("cantidad"),
            func.sum(PedidoProducto.subtotal).label("total_vendido"),
        )
        .join(Pedido, Pedido.id_pedido == PedidoProducto.pedido_id)
        .where(Pedido.restaurante_id == restaurante_id)
        .group_by(PedidoProducto.nombre_producto)
        .order_by(func.sum(PedidoProducto.cantidad).desc())
        .limit(10)
    )

    productos_result = await db.execute(productos_stmt)
    top_productos = productos_result.mappings().all()

    # -------------------------------
    # Productos totales (cantidad de productos diferentes)
    # -------------------------------
    productos_totales_stmt = (
        select(func.count(PedidoProducto.id_pedido_producto))
        .join(Pedido, Pedido.id_pedido == PedidoProducto.pedido_id)
        .where(Pedido.restaurante_id == restaurante_id)
    )
    productos_totales_result = await db.execute(productos_totales_stmt)
    productos_totales = productos_totales_result.scalar_one() or 0

    # -------------------------------
    # Retornar todos los datos
    # -------------------------------
    return {
        "total_pedidos": total_pedidos,
        "total_vendido": total_vendido,
        "ticket_promedio": ticket_promedio,       # ✅ agregado
        "estados": estados,
        "top_productos": top_productos,
        "productos_totales": productos_totales,   # ✅ agregado
    }


async def get_restaurant_sales(db: AsyncSession, limit: int = 5):
    stmt = (
        select(
            Restaurante.nombre.label("name"),
            func.coalesce(func.sum(Pedido.total), 0).label("ventas"),
        )
        .join(Pedido, Pedido.restaurante_id == Restaurante.id_restaurante)
        .where(Pedido.estado_id == 4)  # aprobado
        .group_by(Restaurante.nombre)
        .order_by(func.sum(Pedido.total).desc())
        .limit(limit)
    )

    result = await db.execute(stmt)
    return [
        {
            "name": r.name,
            "ventas": float(r.ventas),
        }
        for r in result.all()
    ]
    
async def create_restaurante_with_admin(
    db: AsyncSession,
    data: dict,
):
    restaurante = Restaurante(
        nit=int(data["nit"]),
        nombre=data["nombre"],
        logo=data.get("logo"),
        color_primario=data.get("color_primario"),
        color_secundario=data.get("color_secundario"),
        estado_id=1,
        fecha_creacion=datetime.utcnow(),
    )

    db.add(restaurante)
    await db.flush()  # 👈 obtenemos id_restaurante

    usuario = Usuario(
        tipo_documento_id=int(data["admin_tipo_documento_id"]),
        documento=data["admin_documento"],  # ahora string
        nombres=data["admin_nombres"],
        apellidos=data["admin_apellidos"],
        telefono=data["admin_telefono"],    # ahora string
        correo=data["admin_correo"],
        contrasena=hash_password(data["admin_contrasena"]),
        estado_id=1,
        fecha_creacion=datetime.utcnow(),
    )

    db.add(usuario)
    await db.flush()

    usuario_rol = UsuarioRol(
        restaurante_id=restaurante.id_restaurante,
        user_id=usuario.id_usuario,
        rol_id=2,  # admin
        fecha_creacion=datetime.utcnow(),
    )

    db.add(usuario_rol)

    await db.commit()
    return restaurante