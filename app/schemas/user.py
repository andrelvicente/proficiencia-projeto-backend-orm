from pydantic import BaseModel, EmailStr
from datetime import datetime
import uuid

# Base para criação/leitura (dados comuns)
class UserBase(BaseModel):
    username: str
    email: EmailStr

# Schema para criação de usuário (inclui senha)
class UserCreate(UserBase):
    password: str

# Schema para atualização de usuário (campos opcionais)
class UserUpdate(UserBase):
    username: str | None = None
    email: EmailStr | None = None
    is_active: bool | None = None

# Schema para retorno de usuário (exclui senha hashed)
class UserOut(UserBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True # ou orm_mode = True para Pydantic < v2