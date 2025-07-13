# app/services/command_service.py
import uuid
from sqlalchemy.orm import Session
from app.db.models import Command, Device
from app.schemas.command import CommandCreate, CommandUpdate
from app.repositories.command import CommandRepository
from app.repositories.device import DeviceRepository
from fastapi import HTTPException, status

class CommandService:
    def __init__(self, db: Session):
        self.command_repo = CommandRepository(db)
        self.device_repo = DeviceRepository(db) # Para verificar permissões do dispositivo

    def get_command(self, command_id: uuid.UUID) -> Command:
        command = self.command_repo.get_by_id(command_id)
        if not command:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Command not found")
        return command

    def get_all_commands(self, skip: int = 0, limit: int = 100) -> list[Command]:
        return self.command_repo.get_all(skip=skip, limit=limit)

    def get_commands_for_device(self, device_id: uuid.UUID, current_user_id: uuid.UUID, skip: int = 0, limit: int = 100) -> list[Command]:
        # Primeiro, verifica se o usuário tem permissão para acessar o dispositivo
        device = self.device_repo.get_by_id(device_id)
        if not device or device.project.user_id != current_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Device not found or not authorized to access its commands")
        
        return self.command_repo.db.query(Command).filter(Command.device_id == device_id).offset(skip).limit(limit).all()


    def create_command(self, command_in: CommandCreate, current_user_id: uuid.UUID) -> Command:
        device = self.device_repo.get_by_id(command_in.device_id)
        if not device or device.project.user_id != current_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Device not found or not authorized to issue commands to it")
        
        with self.command_repo.db.begin_nested(): # Transação ACID
            new_command = self.command_repo.create(command_in.model_dump())
            self.command_repo.db.commit()
            return new_command

    def update_command(self, command_id: uuid.UUID, command_in: CommandUpdate, current_user_id: uuid.UUID) -> Command:
        command = self.get_command(command_id)
        # Verifica se o usuário logado tem permissão para atualizar o comando
        device = self.device_repo.get_by_id(command.device_id)
        if not device or device.project.user_id != current_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this command")

        with self.command_repo.db.begin_nested(): # Transação ACID
            updated_command = self.command_repo.update(command, command_in.model_dump(exclude_unset=True))
            self.command_repo.db.commit()
            return updated_command

    def delete_command(self, command_id: uuid.UUID, current_user_id: uuid.UUID):
        command = self.get_command(command_id)
        device = self.device_repo.get_by_id(command.device_id)
        if not device or device.project.user_id != current_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this command")
        
        with self.command_repo.db.begin_nested(): # Transação ACID
            self.command_repo.delete(command)
            self.command_repo.db.commit()

    # Este método será acessado por um gateway (como a RPi)
    def get_pending_commands_for_device_serial(self, device_serial_number: str) -> list[Command]:
        device = self.device_repo.get_by_serial_number(device_serial_number)
        if not device:
            # Não é um erro 404, apenas significa que não há dispositivo com este serial,
            # ou não há comandos para ele.
            return []
        
        commands = self.command_repo.get_pending_commands_for_device(device.id)
        
        # Opcional: Marcar os comandos como 'sent' aqui para rastreamento
        with self.command_repo.db.begin_nested():
            for cmd in commands:
                if cmd.status == 'pending':
                    cmd.status = 'sent'
                    self.command_repo.db.add(cmd)
            self.command_repo.db.commit()
        
        return commands