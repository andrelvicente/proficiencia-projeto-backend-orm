from typing import List, Optional
import uuid
from sqlalchemy.orm import Session
from app.db.models import Sensor
from app.repositories.base import BaseRepository

class SensorRepository(BaseRepository[Sensor]):
    def __init__(self, db: Session):
        super().__init__(Sensor, db)

    def get_sensors_by_device(self, device_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Sensor]:
        return self.db.query(self.model).filter(self.model.device_id == device_id).offset(skip).limit(limit).all()

    def get_by_name_and_device(self, name: str, device_id: uuid.UUID) -> Optional[Sensor]:
        """
        Busca um sensor pelo seu nome e o ID do dispositivo ao qual ele pertence.
        Útil para identificar sensores específicos em um dispositivo.
        """
        return self.db.query(self.model).filter(
            self.model.name == name,
            self.model.device_id == device_id
        ).first()
