import uuid
from sqlalchemy.orm import Session
from app.db.models import Sensor, Device
from app.schemas.sensor import SensorCreate, SensorUpdate
from app.repositories.sensor import SensorRepository
from app.repositories.device import DeviceRepository
from fastapi import HTTPException, status

class SensorService:
    def __init__(self, db: Session):
        self.sensor_repo = SensorRepository(db)
        self.device_repo = DeviceRepository(db)

    def get_sensor(self, sensor_id: uuid.UUID) -> Sensor:
        sensor = self.sensor_repo.get_by_id(sensor_id)
        if not sensor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sensor not found")
        return sensor

    def get_all_sensors(self, skip: int = 0, limit: int = 100) -> list[Sensor]:
        return self.sensor_repo.get_all(skip=skip, limit=limit)

    def get_sensors_by_device(self, device_id: uuid.UUID, current_user_id: uuid.UUID, skip: int = 0, limit: int = 100) -> list[Sensor]:
        device = self.device_repo.get_by_id(device_id)
        if not device or device.project.user_id != current_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Device not found or not authorized to access its sensors")
        return self.sensor_repo.get_sensors_by_device(device_id, skip=skip, limit=limit)

    def create_sensor(self, sensor_in: SensorCreate, current_user_id: uuid.UUID) -> Sensor:
        device = self.device_repo.get_by_id(sensor_in.device_id)
        if not device or device.project.user_id != current_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Device not found or not authorized to add sensors to it")
        

        new_sensor = self.sensor_repo.create(sensor_in.model_dump())
        return new_sensor

    def update_sensor(self, sensor_id: uuid.UUID, sensor_in: SensorUpdate, current_user_id: uuid.UUID) -> Sensor:
        sensor = self.get_sensor(sensor_id)
        if sensor.device.project.user_id != current_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this sensor")
        
        updated_sensor = self.sensor_repo.update(sensor, sensor_in.model_dump(exclude_unset=True))
        return updated_sensor

    def delete_sensor(self, sensor_id: uuid.UUID, current_user_id: uuid.UUID):
        sensor = self.get_sensor(sensor_id)
        if sensor.device.project.user_id != current_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this sensor")
        
        self.sensor_repo.delete(sensor)
