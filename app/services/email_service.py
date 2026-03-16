# app/services/email_service.py
from app.core.config import settings
import resend  # SDK de Resend

# Configura API Key de Resend
resend.api_key = settings.resend_api_key

async def send_reset_password_email(to_email: str, token: str):
    """
    Envía un correo de restablecimiento con diseño moderno, logo arriba
    y botón intuitivo, usando la URL pública del logo.
    """
    reset_link = f"{settings.frontend_url}/reset-password?token={token}"

    html_content = f"""
    <div style="
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        max-width: 600px; 
        margin: auto; 
        padding: 30px; 
        border: 1px solid var(--border, #e5e5e5); 
        border-radius: 12px; 
        background-color: var(--secondary, #f5f5f5);
    ">
        <!-- Logo arriba centrado -->
        <div style="text-align:center; margin-bottom: 30px;">
            <img src="https://quikly-front-pa66.vercel.app/images/logo.png" 
                 alt="QuiklyGo" 
                 style="width:180px; max-width:100%; height:auto;">
        </div>

        <!-- Título -->
        <h2 style="
            color: var(--primary, #5CCFE6);
            text-align: center; 
            font-weight: 700; 
            margin-bottom: 25px;
            font-size: 24px;
        ">
            Restablece tu contraseña
        </h2>

        <!-- Mensaje -->
        <p style="font-size:16px; color: var(--foreground, #0a0a0a);">
            Hola,
        </p>
        <p style="font-size:16px; color: var(--foreground, #0a0a0a);">
            Recibimos una solicitud para restablecer tu contraseña en <strong>QuiklyGo</strong>.
        </p>

        <!-- Botón -->
        <p style="text-align:center; margin:40px 0;">
            <a href="{reset_link}" style="
                display:inline-block; 
                padding:16px 32px; 
                background-color: var(--primary, #5CCFE6); 
                color: var(--primary-foreground, #000); 
                text-decoration:none; 
                border-radius:8px; 
                font-weight:600; 
                font-size:16px;
                transition: background-color 0.3s ease;
            " onmouseover="this.style.backgroundColor='#4bb8d6';" onmouseout="this.style.backgroundColor='var(--primary, #5CCFE6)';">
                Restablecer contraseña
            </a>
        </p>

        <!-- Mensaje de seguridad -->
        <p style="font-size:14px; color: var(--muted-foreground, #525252);">
            Si no solicitaste esto, puedes ignorar este correo.
        </p>

        <!-- Pie de página -->
        <div style="
            font-size:12px; 
            color: var(--muted-foreground, #525252); 
            text-align:center; 
            margin-top:35px;
        ">
            Este link expira en {settings.reset_token_expire_minutes} minutos.<br>
            © 2026 QuiklyGo. Todos los derechos reservados.
        </div>
    </div>
    """

    # Configuración del correo
    params = {
        "from": settings.from_email,
        "to": [to_email],
        "subject": "Restablece tu contraseña",
        "html": html_content,
    }

    # Envía el correo
    resend.Emails.send(params)