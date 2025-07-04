from pydantic import BaseModel
from datetime import datetime
import uuid

# Base para criação/leitura
class DeviceBase(BaseModel):
    name: str
    description: str | None = None
    serial_number: str
    device_type: str
    status: str = 'offline'

# Schema para criação de dispositivo
class DeviceCreate(DeviceBase):
    project_id: uuid.UUID

# Schema para atualização de dispositivo
class DeviceUpdate(DeviceBase):
    name: str | None = None
    description: str | None = None
    serial_number: str | None = None
    device_type: str | None = None
    status: str | None = None

# Schema para retorno de dispositivo
class DeviceOut(DeviceBase):
    id: uuid.UUID
    project_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    # sensors: list["SensorOut"] = [] # Comentado para evitar dependência circular imediata
    # tags: list["TagOut"] = [] # Comentado para evitar dependência circular imediata

    class Config:
        from_attributes = True

# Forward Reference
from app.schemas.sensor import SensorOut
from app.schemas.tag import TagOut
DeviceOut.model_rebuild()