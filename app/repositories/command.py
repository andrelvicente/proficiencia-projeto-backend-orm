# app/repositories/command.py
from sqlalchemy.orm import Session
from app.db.models import Command
from app.repositories.base import BaseRepository
from typing import List, Optional
import uuid

class CommandRepository(BaseRepository[Command]):
    def __init__(self, db: Session):
        super().__init__(Command, db)

    def get_pending_commands_for_device(self, device_id: uuid.UUID, limit: int = 10) -> List[Command]:
        """Obtém comandos pendentes para um dispositivo específico."""
        return self.db.query(self.model).filter(
            self.model.device_id == device_id,
            self.model.status == 'pending'
        ).limit(limit).all()