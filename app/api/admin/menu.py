# app/api/admin/menu.py

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.security import get_current_user
from app.db.database import get_db
from app.models.categoria import Categoria
from app.models.producto import Producto
from app.models.grupo_opcion_producto import GrupoOpcionProducto
from app.models.opcion_producto import OpcionProducto
from app.models.usuarios_rol import UsuarioRol
from app.schemas.menu import MenuRestauranteOut, CategoriaOut, ProductoOut, CategoriaOrdenIn
from app.repositories.menu_repo import get_restaurant_menu

router = APIRouter(
    prefix="/admin/restaurante/menu",
    tags=["Admin Restaurante - Menú"]
)

# ======================
# DB dependency
# ======================



# ======================
# Helper: obtener restaurante del admin
# ======================
async def get_admin_restaurante_id(admin, db: AsyncSession) -> int:
    stmt = select(UsuarioRol.restaurante_id).where(
        UsuarioRol.user_id == admin.id_usuario,
        UsuarioRol.rol_id == 2  # admin_restaurante
    ).limit(1)

    restaurante_id = (await db.execute(stmt)).scalar()

    if not restaurante_id:
        raise HTTPException(
            status_code=403,
            detail="Usuario no asociado a ningún restaurante"
        )

    return restaurante_id


# ======================
# GET: Obtener menú
# ======================
@router.get("/", response_model=MenuRestauranteOut)
async def obtener_menu(
    admin=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    restaurante_id = await get_admin_restaurante_id(admin, db)

    categorias_data = await get_restaurant_menu(db, restaurante_id)

    return MenuRestauranteOut(
        categorias=[
            CategoriaOut(
                id_categoria=cat["id_categoria"],
                nombre=cat["nombre"],
                img_categoria=cat["img_categoria"],
                orden=cat["orden"],
                estado_id=cat["estado_id"],
                productos=[ProductoOut(**p) for p in cat["productos"]],
            )
            for cat in categorias_data
        ]
    )


# ======================
# POST: Crear categoría
# ======================
@router.post("/categoria", response_model=CategoriaOut)
async def crear_categoria(
    nombre: str = Body(..., embed=True),
    img_categoria: str | None = Body(None, embed=True),
    admin=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    restaurante_id = await get_admin_restaurante_id(admin, db)

    stmt = select(func.coalesce(func.max(Categoria.orden), 0)).where(
    Categoria.restaurante_id == restaurante_id
)
    ultimo_orden = (await db.execute(stmt)).scalar()

    nueva_cat = Categoria(
        restaurante_id=restaurante_id,
        nombre=nombre,
        img_categoria=img_categoria,
        orden=ultimo_orden + 1,
        estado_id=1
    )

    db.add(nueva_cat)
    await db.commit()
    await db.refresh(nueva_cat)

    return CategoriaOut(
        id_categoria=nueva_cat.id_categoria,
        nombre=nueva_cat.nombre,
        img_categoria=nueva_cat.img_categoria,
        orden=nueva_cat.orden,
        estado_id=nueva_cat.estado_id,
        productos=[]
    )


# ======================
# PUT: Editar categoría
# ======================
@router.put("/categoria/{categoria_id}", response_model=CategoriaOut)
async def editar_categoria(
    categoria_id: int,
    nombre: str = Body(..., embed=True),
    img_categoria: str | None = Body(None, embed=True),
    admin=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    restaurante_id = await get_admin_restaurante_id(admin, db)

    stmt = select(Categoria).where(
        Categoria.id_categoria == categoria_id,
        Categoria.restaurante_id == restaurante_id
    )
    cat = (await db.execute(stmt)).scalar_one_or_none()

    if not cat:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    cat.nombre = nombre
    cat.img_categoria = img_categoria

    await db.commit()
    await db.refresh(cat)

    return CategoriaOut(
        id_categoria=cat.id_categoria,
        nombre=cat.nombre,
        img_categoria=cat.img_categoria,
        orden=cat.orden,
        estado_id=cat.estado_id,
        productos=[]
    )


# ======================
# PATCH: Cambiar estado categoría
# ======================
@router.patch("/categoria/{categoria_id}/estado", response_model=CategoriaOut)
async def cambiar_estado_categoria(
    categoria_id: int,
    estado_id: int = Body(..., embed=True),
    admin=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    restaurante_id = await get_admin_restaurante_id(admin, db)

    stmt = select(Categoria).where(
        Categoria.id_categoria == categoria_id,
        Categoria.restaurante_id == restaurante_id
    )
    cat = (await db.execute(stmt)).scalar_one_or_none()

    if not cat:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    cat.estado_id = estado_id
    await db.commit()
    await db.refresh(cat)

    return CategoriaOut(
        id_categoria=cat.id_categoria,
        nombre=cat.nombre,
        img_categoria=cat.img_categoria,
        orden=cat.orden,
        estado_id=cat.estado_id,
        productos=[]
    )


@router.put("/orden")
async def actualizar_orden(
    ordenes: list[CategoriaOrdenIn],
    admin=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    restaurante_id = await get_admin_restaurante_id(admin, db)

    for item in ordenes:
        stmt = select(Categoria).where(
            Categoria.id_categoria == item.id_categoria,
            Categoria.restaurante_id == restaurante_id
        )
        cat = (await db.execute(stmt)).scalar_one()
        cat.orden = item.orden

    await db.commit()
    return {"ok": True}


# ======================
@router.get("/categoria/{categoria_id}", response_model=CategoriaOut)
async def obtener_categoria_detalle(
    categoria_id: int,
    admin=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    restaurante_id = await get_admin_restaurante_id(admin, db)

    stmt = (
        select(Categoria)
        .where(
            Categoria.id_categoria == categoria_id,
            Categoria.restaurante_id == restaurante_id
        )
    )

    categoria = (await db.execute(stmt)).scalar_one_or_none()

    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    # ⚠️ IMPORTANTE: lazy loading
    productos = [
        ProductoOut(
            id_producto=p.id_producto,
            nombre=p.nombre,
            precio_base=p.precio_base,
            estado_id=p.estado_id,
        )
        for p in categoria.productos
    ]

    return CategoriaOut(
        id_categoria=categoria.id_categoria,
        nombre=categoria.nombre,
        img_categoria=categoria.img_categoria,
        orden=categoria.orden,
        estado_id=categoria.estado_id,
        productos=productos,
    )
    
@router.get("/producto/{producto_id}")
async def obtener_producto_detalle(
    producto_id: int,
    admin=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    restaurante_id = await get_admin_restaurante_id(admin, db)

    stmt = (
        select(Producto)
        .options(
            selectinload(Producto.grupos_opcion)
            .selectinload(GrupoOpcionProducto.opciones)
        )
        .where(
            Producto.id_producto == producto_id,
            Producto.restaurante_id == restaurante_id
        )
    )

    producto = (await db.execute(stmt)).scalar_one_or_none()
    if not producto:
        raise HTTPException(404, "Producto no encontrado")

    return {
        "id_producto": producto.id_producto,
        "nombre": producto.nombre,
        "descripcion": producto.descripcion,
        "precio_base": producto.precio_base,
        "estado_id": producto.estado_id,
        "grupos": [
            {
                "id_grupo_opcion": g.id_grupo_opcion,
                "nombre": g.nombre,
                "tipo": g.tipo,
                "obligatorio": g.obligatorio,
                "min": g.min_selecciones,
                "max": g.max_selecciones,
                "estado_id": g.estado_id,
                "opciones": [
                    {
                        "id_opcion_producto": o.id_opcion_producto,
                        "nombre": o.nombre,
                        "precio_adicional": o.precio_adicional,
                        "estado_id": o.estado_id,
                    }
                    for o in g.opciones
                ],
            }
            for g in producto.grupos_opcion
        ],
    }



@router.post("/producto/{producto_id}/grupo")
async def crear_grupo_opcion(
    producto_id: int,
    nombre: str = Body(...),
    tipo: str = Body(...),  # tamaño | topping
    obligatorio: bool = Body(False),
    min_selecciones: int = Body(0),
    max_selecciones: int = Body(1),
    admin=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    restaurante_id = await get_admin_restaurante_id(admin, db)

    grupo = GrupoOpcionProducto(
        producto_id=producto_id,
        nombre=nombre,
        tipo=tipo,
        obligatorio=obligatorio,
        min_selecciones=min_selecciones,
        max_selecciones=max_selecciones,
        estado_id=1
    )

    db.add(grupo)
    await db.commit()
    await db.refresh(grupo)

    return {"id_grupo_opcion": grupo.id_grupo_opcion}


@router.post("/grupo/{grupo_id}/opcion")
async def crear_opcion(
    grupo_id: int,
    nombre: str = Body(...),
    precio_adicional: float = Body(0),
    admin=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    opcion = OpcionProducto(
        grupo_opcion_id=grupo_id,
        nombre=nombre,
        precio_adicional=precio_adicional,
        estado_id=1
    )

    db.add(opcion)
    await db.commit()
    await db.refresh(opcion)

    return {"id_opcion_producto": opcion.id_opcion_producto}


@router.patch("/opcion/{id_opcion}/estado")
async def toggle_opcion(
    id_opcion: int,
    db: AsyncSession = Depends(get_db),
):
    opcion = await db.get(OpcionProducto, id_opcion)

    if not opcion:
        raise HTTPException(status_code=404, detail="Opción no encontrada")

    opcion.estado_id = 2 if opcion.estado_id == 1 else 1

    await db.commit()
    await db.refresh(opcion)

    return {
        "id_opcion_producto": opcion.id_opcion_producto,
        "estado_id": opcion.estado_id,
    }
