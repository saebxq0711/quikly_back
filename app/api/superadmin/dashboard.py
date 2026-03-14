from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.repositories.superadmin.dashboard_repo import (
    get_user_kpis,
    get_restaurant_kpis,
    get_order_kpis,
    get_top_products,
    get_recent_data,
)

router = APIRouter(
    prefix="/superadmin/dashboard",
    tags=["SuperAdmin Dashboard"]
)


# ==========================
# DB DEPENDENCY
# ==========================



# ==========================
# DASHBOARD GLOBAL
# ==========================
@router.get("/")
async def superadmin_dashboard(db: AsyncSession = Depends(get_db)):
    """
    Dashboard global del SuperAdmin.
    Retorna KPIs, rankings y datos recientes del sistema.
    """

    usuarios = await get_user_kpis(db)
    restaurantes = await get_restaurant_kpis(db)
    pedidos = await get_order_kpis(db)
    productos_top = await get_top_products(db)
    recientes = await get_recent_data(db)

    return {
        "usuarios": usuarios,
        "restaurantes": restaurantes,
        "pedidos": pedidos,
        "productos_top": productos_top,
        "recientes": recientes,
    }
