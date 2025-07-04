from pydantic import BaseModel
from datetime import datetime
import uuid

# Base para criação/leitura
class ProjectBase(BaseModel):
    name: str
    description: str | None = None

# Schema para criação de projeto
class ProjectCreate(ProjectBase):
    user_id: uuid.UUID # Opcional, mas para criação inicial pode ser necessário

# Schema para atualização de projeto
class ProjectUpdate(ProjectBase):
    name: str | None = None
    description: str | None = None

# Schema para retorno de projeto (inclui relacionamentos básicos)
class ProjectOut(ProjectBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    # Adicione estes campos para HATEOAS ou para facilitar visualização
    # devices: list["DeviceOut"] = [] # Comentado para evitar dependência circular imediata
    # tags: list["TagOut"] = [] # Comentado para evitar dependência circular imediata
    
    class Config:
        from_attributes = True

# Forward Reference para evitar circular import se usado em ProjectOut
from app.schemas.device import DeviceOut
from app.schemas.tag import TagOut
ProjectOut.model_rebuild()