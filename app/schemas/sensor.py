from pydantic import BaseModel
from datetime import datetime
import uuid
from decimal import Decimal

# Base para criação/leitura
class SensorBase(BaseModel):
    name: str
    unit_of_measurement: str | None = None
    min_value: Decimal | None = None
    max_value: Decimal | None = None

# Schema para criação de sensor
class SensorCreate(SensorBase):
    device_id: uuid.UUID

# Schema para atualização de sensor
class SensorUpdate(SensorBase):
    name: str | None = None
    unit_of_measurement: str | None = None
    min_value: Decimal | None = None
    max_value: Decimal | None = None

# Schema para retorno de sensor
class SensorOut(SensorBase):
    id: uuid.UUID
    device_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    # sensor_data: list["SensorDataOut"] = [] # Comentado para evitar dependência circular imediata

    class Config:
        from_attributes = True

# Forward Reference
from app.schemas.sensor_data import SensorDataOut
SensorOut.model_rebuild()