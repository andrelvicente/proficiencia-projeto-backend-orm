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
        
class SensorReading(BaseModel):
    sensor_name_or_id: str
    value: Decimal
    unit_of_measurement: str | None = None
    timestamp: datetime | None = None

# Schema para o payload completo de ingestão de dados de um dispositivo.
class IngestDataPayload(BaseModel):
    device_serial_number: str
    readings: list[SensorReading]

class SensorDailyAverage(BaseModel):
    sensor_id: uuid.UUID
    sensor_name: str
    date: str # Formato YYYY-MM-DD
    average_value: Decimal
    unit_of_measurement: str | None = None

    class Config:
        from_attributes = True

class SensorWeeklyAverage(BaseModel):
    sensor_id: uuid.UUID
    sensor_name: str
    week_start_date: str # Formato YYYY-MM-DD (início da semana)
    average_value: Decimal
    unit_of_measurement: str | None = None

    class Config:
        from_attributes = True

class SensorMonthlyAverage(BaseModel):
    sensor_id: uuid.UUID
    sensor_name: str
    month: str # Formato YYYY-MM
    average_value: Decimal
    unit_of_measurement: str | None = None

    class Config:
        from_attributes = True
        