from pydantic import BaseModel, EmailStr  # <-- IMPORTAR EmailStr

class LoginSchema(BaseModel):
    correo: str
    contrasena: str
    
class ForgotPasswordRequest(BaseModel):
    correo: EmailStr  # ahora sí funciona

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class MessageResponse(BaseModel):
    detail: str


class AdminContext(BaseModel):
    user_id: int
    restaurante_id: int
    rol: str
    
class KioscoContext(BaseModel):
    user_id: int
    restaurante_id: int
    rol: str