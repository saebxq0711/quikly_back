from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from sqlalchemy import text
from typing import List, Dict

router = APIRouter(tags=["Usuarios"])



@router.get("/tipo-documento", response_model=List[Dict])
async def tipos_documento(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT id_tipo_documento, nombre FROM tipo_documento"))
    return result.mappings().all()  # 🔹 lista de dicts listos para JSON

