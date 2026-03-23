from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.core.security import get_kiosco_context
from app.schemas.auth import KioscoContext
from app.models.categoria import Categoria
from app.services.storage_service import get_public_url  # 🔥 importar

router = APIRouter(
    prefix="/kiosco",
    tags=["Kiosco"],
)

@router.get("/categorias")
async def get_categorias_kiosco(
    ctx: KioscoContext = Depends(get_kiosco_context),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Categoria)
        .where(
            Categoria.restaurante_id == ctx.restaurante_id,
            Categoria.estado_id == 1,
        )
        .order_by(Categoria.orden.asc(), Categoria.nombre.asc())
    )

    result = await db.execute(stmt)
    categorias = result.scalars().all()

    return [
        {
            "id": c.id_categoria,
            "nombre": c.nombre,
            "img": get_public_url(c.img_categoria) if c.img_categoria else None,  # 🔹 URL pública
        }
        for c in categorias
    ]