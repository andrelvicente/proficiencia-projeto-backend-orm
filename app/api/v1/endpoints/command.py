# app/api/v1/endpoints/commands.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import uuid
import json # Para lidar com parâmetros JSON (se parameters for um JSON string)

from app.schemas.command import CommandCreate, CommandOut, CommandUpdate
from app.core.dependencies import get_db, get_current_user
from app.services.command_service import CommandService
from app.db.models import User as DBUser

router = APIRouter()

# Helper para HATEOAS (simplificado)
def add_command_links(command: CommandOut) -> dict:
    links = {
        "self": {"href": f"/api/v1/commands/{command.id}", "method": "GET"},
        "device": {"href": f"/api/v1/devices/{command.device_id}", "method": "GET"},
        # Ações como update e delete de comandos podem ser limitadas/controladas
    }
    return command.model_dump(by_alias=True, exclude_unset=True) | {"_links": links}


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_command(command_in: CommandCreate, db: Session = Depends(get_db),
                   current_user: DBUser = Depends(get_current_user)):
    """
    Cria um novo comando para um dispositivo atuador.
    O usuário autenticado deve ser o proprietário do projeto do dispositivo.
    """
    command_service = CommandService(db)
    command = command_service.create_command(command_in, current_user.id)
    return add_command_links(CommandOut.model_validate(command))

@router.get("/", response_model=list[dict])
def read_commands(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                  current_user: DBUser = Depends(get_current_user),
                  device_id: uuid.UUID | None = None):
    """
    Lista todos os comandos (filtrando por dispositivo se especificado).
    Acesso restrito aos comandos de dispositivos do usuário logado.
    """
    command_service = CommandService(db)
    if device_id:
        commands = command_service.get_commands_for_device(device_id, current_user.id, skip=skip, limit=limit)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please provide a 'device_id' to filter commands.")
    
    return [add_command_links(CommandOut.model_validate(c)) for c in commands]

@router.get("/{command_id}", response_model=dict)
def read_command(command_id: uuid.UUID, db: Session = Depends(get_db),
                 current_user: DBUser = Depends(get_current_user)):
    """
    Obtém detalhes de um comando específico por ID.
    O usuário deve ser o proprietário do projeto ao qual o comando pertence.
    """
    command_service = CommandService(db)
    command = command_service.get_command(command_id)
    # Verifica a autorização
    device = command_service.device_repo.get_by_id(command.device_id)
    if not device or device.project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this command")
    return add_command_links(CommandOut.model_validate(command))

@router.delete("/{command_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_command(command_id: uuid.UUID, db: Session = Depends(get_db),
                   current_user: DBUser = Depends(get_current_user)):
    """
    Exclui um comando.
    O usuário deve ser o proprietário do projeto ao qual o comando pertence.
    """
    command_service = CommandService(db)
    command_service.delete_command(command_id, current_user.id)
    return {"message": "Command deleted successfully"}

# --- Endpoint para Gateways/Dispositivos puxarem comandos pendentes ---
@router.post("/gateway-pull-commands", response_model=list[dict])
def gateway_pull_commands(device_serial_number: str = Query(..., description="Serial number of the gateway/device pulling commands"),
                          db: Session = Depends(get_db)):
    """
    Endpoint para um gateway ou dispositivo IoT consultar comandos pendentes para ele.
    Este endpoint não requer autenticação de usuário para facilitar a comunicação IoT.
    Em um ambiente de produção, considere proteger com uma chave de API ou token de dispositivo.
    Ao puxar, os comandos são automaticamente marcados como 'sent'.
    """
    command_service = CommandService(db)
    commands = command_service.get_pending_commands_for_device_serial(device_serial_number)
    
    return [add_command_links(CommandOut.model_validate(c)) for c in commands]

# --- Endpoint para Gateways/Dispositivos atualizarem o status do comando ---
@router.put("/gateway-update-command/{command_id}", response_model=dict)
def gateway_update_command_status(command_id: uuid.UUID, command_update: CommandUpdate, db: Session = Depends(get_db)):
    """
    Endpoint para um gateway ou dispositivo IoT atualizar o status de um comando.
    Não requer autenticação de usuário, mas em produção exigiria token de dispositivo.
    """
    command_service = CommandService(db)
    updated_command = command_service.update_command(command_id, command_update, current_user_id=None)
    return add_command_links(CommandOut.model_validate(updated_command))