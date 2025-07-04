from typing import List, Optional
import uuid
from sqlalchemy.orm import Session
from app.db.models import SensorData
from app.repositories.base import BaseRepository
from datetime import datetime

class SensorDataRepository(BaseRepository[SensorData]):
    def __init__(self, db: Session):
        super().__init__(SensorData, db)

    def get_data_by_sensor(self, sensor_id: uuid.UUID, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None, skip: int = 0, limit: int = 100) -> List[SensorData]:
        query = self.db.query(self.model).filter(self.model.sensor_id == sensor_id)
        if start_time:
            query = query.filter(self.model.timestamp >= start_time)
        if end_time:
            query = query.filter(self.model.timestamp <= end_time)
        return query.order_by(self.model.timestamp.desc()).offset(skip).limit(limit).all()