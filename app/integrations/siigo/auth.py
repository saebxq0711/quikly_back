import httpx
from app.core.config import settings

_token_cache = None


async def get_siigo_token():

    global _token_cache

    if _token_cache:
        return _token_cache

    url = f"{settings.siigo_base_url}/auth"

    headers = {
        "Content-Type": "application/json",
        "Partner-Id": "SandboxSiigoAPI"
    }

    payload = {
        "username": settings.siigo_user,
        "access_key": settings.siigo_key
    }

    async with httpx.AsyncClient(timeout=20) as client:

        response = await client.post(
            url,
            json=payload,
            headers=headers
        )

    if response.status_code >= 400:
        print("SIIGO ERROR:")
        print(response.text)
        raise Exception(response.text)

    data = response.json()

    token = data["access_token"]

    _token_cache = token

    return token