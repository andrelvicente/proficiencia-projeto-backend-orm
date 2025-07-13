# app/schemas/command.py
from pydantic import BaseModel
from datetime import datetime
import uuid

# Base para criação/leitura
class CommandBase(BaseModel):
    command_type: str
    parameters: str | None = None # Pode ser um JSON string de parâmetros

# Schema para criação de comando (API envia isso)
class CommandCreate(CommandBase):
    device_id: uuid.UUID

# Schema para atualização de comando (para o dispositivo atualizar o status)
class CommandUpdate(BaseModel):
    status: str | None = None
    response_message: str | None = None
    completed_at: datetime | None = None

# Schema para retorno de comando (saída da API)
class CommandOut(CommandBase):
    id: uuid.UUID
    device_id: uuid.UUID
    status: str
    issued_at: datetime
    completed_at: datetime | None = None
    response_message: str | None = None

    class Config:
        from_attributes = True
