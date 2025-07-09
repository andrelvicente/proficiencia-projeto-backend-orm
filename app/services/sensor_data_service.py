import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.models import SensorData, Sensor
from app.schemas.sensor_data import SensorDataCreate
from app.repositories.sensor_data import SensorDataRepository
from app.repositories.sensor import SensorRepository
from fastapi import HTTPException, status

class SensorDataService:
    def __init__(self, db: Session):
        self.sensor_data_repo = SensorDataRepository(db)
        self.sensor_repo = SensorRepository(db)

    def get_sensor_data(self, data_id: uuid.UUID) -> SensorData:
        data = self.sensor_data_repo.get_by_id(data_id)
        if not data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sensor data not found")
        return data

    def get_all_sensor_data(self, skip: int = 0, limit: int = 100) -> list[SensorData]:
        return self.sensor_data_repo.get_all(skip=skip, limit=limit)

    def get_data_by_sensor(self, sensor_id: uuid.UUID, current_user_id: uuid.UUID, start_time: datetime = None, end_time: datetime = None, skip: int = 0, limit: int = 100) -> list[SensorData]:
        sensor = self.sensor_repo.get_by_id(sensor_id)
        if not sensor or sensor.device.project.user_id != current_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sensor not found or not authorized to access its data")
        return self.sensor_data_repo.get_data_by_sensor(sensor_id, start_time, end_time, skip=skip, limit=limit)

    def create_sensor_data(self, data_in: SensorDataCreate, current_user_id: uuid.UUID) -> SensorData:
        sensor = self.sensor_repo.get_by_id(data_in.sensor_id)
        if not sensor or sensor.device.project.user_id != current_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sensor not found or not authorized to add data to it")
        
        new_data = self.sensor_data_repo.create(data_in.model_dump())
        return new_data

    def delete_sensor_data(self, data_id: uuid.UUID, current_user_id: uuid.UUID):
        data = self.get_sensor_data(data_id)
        if data.sensor.device.project.user_id != current_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this sensor data")
        
        self.sensor_data_repo.delete(data)
