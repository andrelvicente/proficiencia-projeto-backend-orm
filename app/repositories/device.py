from typing import List
import uuid
from sqlalchemy.orm import Session
from app.db.models import Device
from app.repositories.base import BaseRepository

class DeviceRepository(BaseRepository[Device]):
    def __init__(self, db: Session):
        super().__init__(Device, db)

    def get_devices_by_project(self, project_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Device]:
        return self.db.query(self.model).filter(self.model.project_id == project_id).offset(skip).limit(limit).all()

    def get_by_serial_number(self, serial_number: str) -> Device | None:
        return self.db.query(self.model).filter(self.model.serial_number == serial_number).first()