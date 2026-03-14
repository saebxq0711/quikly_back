from fastapi import APIRouter
from .routes import auth

api_router = APIRouter()

# Prefijo: /api/v1/auth
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
