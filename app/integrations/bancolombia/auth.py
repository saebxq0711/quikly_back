import httpx
from datetime import datetime, timedelta
from app.core.config import settings

_token_cache = {
    "access_token": None,
    "expires_at": None
}


async def get_bancolombia_token() -> str:
    """
    Obtiene token OAuth2 de Bancolombia usando client_credentials.
    Usa cache en memoria para evitar pedir token en cada request.
    """

    now = datetime.utcnow()

    # Si el token sigue vigente lo reutilizamos
    if (
        _token_cache["access_token"]
        and _token_cache["expires_at"]
        and now < _token_cache["expires_at"]
    ):
        return _token_cache["access_token"]

    auth = httpx.BasicAuth(
        settings.bancolombia_client_id,
        settings.bancolombia_client_secret
    )

    data = {
        "grant_type": "client_credentials",
        "scope": "qr-codes:write:app"
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            settings.bancolombia_auth_url,
            auth=auth,
            data=data,
            headers=headers
        )

    response.raise_for_status()

    token_data = response.json()

    access_token = token_data["access_token"]
    expires_in = int(token_data["expires_in"])

    # Guardamos en cache
    _token_cache["access_token"] = access_token
    _token_cache["expires_at"] = now + timedelta(seconds=expires_in - 60)

    return access_token