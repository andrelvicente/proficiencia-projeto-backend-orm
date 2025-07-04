from pydantic import BaseModel
import uuid

# Base para criação/leitura
class TagBase(BaseModel):
    name: str

# Schema para criação de tag
class TagCreate(TagBase):
    pass

# Schema para atualização de tag
class TagUpdate(TagBase):
    name: str | None = None

# Schema para retorno de tag
class TagOut(TagBase):
    id: uuid.UUID

    class Config:
        from_attributes = True