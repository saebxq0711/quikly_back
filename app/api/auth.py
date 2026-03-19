from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.schemas.auth import LoginSchema, ForgotPasswordRequest, ResetPasswordRequest, MessageResponse
from app.services.auth_service import authenticate, send_reset_password_email, reset_password
from app.core.security import create_access_token, get_current_user

router = APIRouter()

# --- Login existente ---
@router.post("/login")
async def login(data: LoginSchema, db: AsyncSession = Depends(get_db)):
    user = await authenticate(db, data.correo, data.contrasena)

    if not user:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    token = create_access_token({
        "sub": str(user["id_usuario"]),
        "rol": user["rol"],
        "restaurante_id": user["restaurante_id"]
    })

    return {
        "access_token": token,
        "rol": user["rol"]
    }

@router.post("/refresh")
async def refresh_token(current_user = Depends(get_current_user)):
    new_token = create_access_token({
        "sub": str(current_user.id_usuario),
        "rol": current_user.rol,
        "restaurante_id": current_user.restaurante_id
    })

    return {
        "access_token": new_token,
        "rol": current_user.rol
    }

# --- Olvidé contraseña ---
@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(request: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    await send_reset_password_email(db, request.correo)
    return {"detail": "Si existe la cuenta, se envió un correo."}

# --- Reset password ---
@router.post("/reset-password", response_model=MessageResponse)
async def reset_password_endpoint(request: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    try:
        await reset_password(db, request.token, request.new_password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"detail": "Contraseña actualizada exitosamente"}
