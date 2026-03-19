from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.categoria import Categoria
from app.models.producto import Producto


async def get_restaurant_menu(
    db: AsyncSession,
    restaurante_id: int,
    only_active: bool = False  # 🔥 clave
):
    # ======================
    # Categorías
    # ======================
    categorias_stmt = select(Categoria).where(
        Categoria.restaurante_id == restaurante_id
    )

    if only_active:
        categorias_stmt = categorias_stmt.where(Categoria.estado_id == 1)

    categorias_stmt = categorias_stmt.order_by(Categoria.orden)

    categorias = (await db.execute(categorias_stmt)).scalars().all()

    resultado = []

    # ======================
    # Productos
    # ======================
    for cat in categorias:
        productos_stmt = select(Producto).where(
            Producto.restaurante_id == restaurante_id,
            Producto.categoria_id == cat.id_categoria
        )

        if only_active:
            productos_stmt = productos_stmt.where(Producto.estado_id == 1)

        productos_stmt = productos_stmt.order_by(Producto.nombre)

        productos = (await db.execute(productos_stmt)).scalars().all()

        resultado.append({
            "id_categoria": cat.id_categoria,
            "nombre": cat.nombre,
            "img_categoria": cat.img_categoria,
            "orden": cat.orden,
            "estado_id": cat.estado_id,
            "productos": [
                {
                    "id_producto": p.id_producto,
                    "nombre": p.nombre,
                    "descripcion": p.descripcion,
                    "precio_base": float(p.precio_base),
                    "img_producto": p.img_producto,
                    "estado_id": p.estado_id,
                }
                for p in productos
            ],
        })

    return resultado