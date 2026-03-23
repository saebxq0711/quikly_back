# app/services/storage_service.py

from app.services.supabase_client import supabase

BUCKET = "images"


def upload_file(path: str, file_bytes: bytes, content_type: str):
    """
    Sube o reemplaza un archivo en Supabase Storage
    """
    return supabase.storage.from_(BUCKET).upload(
        path,
        file_bytes,
        {
            "content-type": content_type,
            "upsert": "true"
        }
    )


def delete_file(path: str):
    """
    Elimina un archivo del bucket
    """
    return supabase.storage.from_(BUCKET).remove([path])


def get_public_url(path: str) -> str:
    """
    Obtiene la URL pública del archivo
    """
    response = supabase.storage.from_(BUCKET).get_public_url(path)
    return response