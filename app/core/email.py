import aiosmtplib
from email.message import EmailMessage
from app.core.config import settings

async def send_email(to: str, subject: str, body: str):
    message = EmailMessage()
    message["From"] = settings.from_email
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    await aiosmtplib.send(
        message,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_user,
        password=settings.smtp_password,
        start_tls=True  # importante para Mailtrap
    )
    print(f"Correo enviado a {to}")
