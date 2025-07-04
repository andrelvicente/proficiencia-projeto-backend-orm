from pydantic import BaseModel
from datetime import datetime
import uuid
from decimal import Decimal

# Base para criação/leitura
class SensorDataBase(BaseModel):
    value: Decimal
    timestamp: datetime | None = None # Será default NOW() no DB, mas opcional na criação

# Schema para criação de dado de sensor
class SensorDataCreate(SensorDataBase):
    sensor_id: uuid.UUID

# Não há um SensorDataUpdate comum, pois dados de sensor geralmente não são atualizados

# Schema para retorno de dado de sensor
class SensorDataOut(SensorDataBase):
    id: uuid.UUID
    sensor_id: uuid.UUID

    class Config:
        from_attributes = True