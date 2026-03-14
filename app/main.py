from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings

# ---------- Auth / Usuarios ----------
from app.api import auth, usuarios

# ---------- SuperAdmin ----------
from app.api.superadmin import (
    restaurantes,
    pedidos as superadmin_pedidos,
    administradores,
    profile as superadmin_profile,
    dashboard as superadmin_dashboard,
    bancolombia_logs as superadmin_bancolombia_logs,
)

# ---------- Admin Restaurante ----------
from app.api.admin import (
    dashboard as admin_dashboard,
    pedidos as admin_pedidos,
    menu as admin_menu,
    kiosco as admin_kiosco,
    reportes as admin_reportes,
    perfil as admin_perfil,
    promocion as admin_promocion,
)

# ---------- Kiosco ----------

from app.api.kiosco import (
    home as kiosco_home,
    categorias as kiosco_categorias,
    productos as kiosco_productos,
    codigo_qr as kiosco_codigo_qr,
    factura as kiosco_factura,
)

# ---------- Bancolombia ----------
from app.api.bancolombia import (
    qr_webhook as bancolombia_qr_webhook,
)

app = FastAPI(title=settings.project_name)

# ---------- CORS ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# AUTH / USUARIOS
# =====================================================
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(usuarios.router, prefix="/api")

# =====================================================
# SUPERADMIN
# =====================================================
app.include_router(restaurantes.router, prefix="/api")
app.include_router(superadmin_pedidos.router, prefix="/api")
app.include_router(administradores.router, prefix="/api")
app.include_router(superadmin_profile.router, prefix="/api")
app.include_router(superadmin_dashboard.router, prefix="/api")
app.include_router(superadmin_bancolombia_logs.router, prefix="/api")

# =====================================================
# ADMIN RESTAURANTE
# =====================================================
app.include_router(admin_dashboard.router, prefix="/api")
app.include_router(admin_pedidos.router, prefix="/api")
app.include_router(admin_menu.router, prefix="/api")
app.include_router(admin_promocion.router, prefix="/api")
app.include_router(admin_kiosco.router, prefix="/api")
app.include_router(admin_reportes.router, prefix="/api")
app.include_router(admin_perfil.router, prefix="/api")

# =====================================================
# KIOSCO
# =====================================================


app.include_router(kiosco_home.router, prefix="/api", tags=["Kiosco"])
app.include_router(kiosco_categorias.router, prefix="/api", tags=["Kiosco"])
app.include_router(kiosco_productos.router, prefix="/api", tags=["Kiosco"])
app.include_router(kiosco_codigo_qr.router, prefix="/api", tags=["Kiosco"])
app.include_router(kiosco_factura.router, prefix="/api", tags=["Kiosco Factura"])

# =====================================================
# BANCOLOMBIA
# =====================================================
app.include_router(bancolombia_qr_webhook.router, prefix="/api")


# =====================================================
# STATIC FILES
# =====================================================
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# =====================================================
# ROOT
# =====================================================
@app.get("/")
def root():
    return {"status": "ok"}
