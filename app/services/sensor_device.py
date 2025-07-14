from typing import List
import uuid
from sqlalchemy import desc, func
from sqlalchemy.orm import Session
from app.db.models import Sensor, Device, SensorData
from app.schemas.sensor import SensorCreate, SensorUpdate, SensorWithRecentData
from app.repositories.sensor import SensorRepository
from app.repositories.device import DeviceRepository
from fastapi import HTTPException, status

from app.schemas.sensor_data import SensorDailyAverage, SensorDataOut, SensorMonthlyAverage, SensorWeeklyAverage

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

    def get_recent_sensor_data_for_device(self, device_id: uuid.UUID, current_user_id: uuid.UUID, limit: int = 1) -> List[SensorWithRecentData]:
        """
        Retorna os N dados mais recentes de todos os sensores de um dispositivo específico.
        """
        device = self.device_repo.get_by_id(device_id)
        if not device or device.project.user_id != current_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Device not found or not authorized to access its sensor data.")
        
        sensors_with_data = []
        sensors = self.sensor_repo.get_sensors_by_device(device_id)
        
        for sensor in sensors:
            # Query para os N dados mais recentes
            recent_data = self.sensor_repo.db.query(SensorData) \
                .filter(SensorData.sensor_id == sensor.id) \
                .order_by(desc(SensorData.timestamp)) \
                .limit(limit) \
                .all()
            
            # Mapear para SensorDataOut
            recent_data_out = [SensorDataOut.model_validate(data) for data in recent_data]
            
            sensors_with_data.append(
                SensorWithRecentData(
                    sensor_id=sensor.id,
                    sensor_name=sensor.name,
                    unit_of_measurement=sensor.unit_of_measurement,
                    recent_data=recent_data_out
                )
            )
        
        return sensors_with_data

    # --- NOVOS MÉTODOS DE SERVIÇO PARA MÉDIAS (Parte 2) ---

    def get_daily_averages_for_device(self, device_id: uuid.UUID, current_user_id: uuid.UUID) -> List[SensorDailyAverage]:
        device = self.device_repo.get_by_id(device_id)
        if not device or device.project.user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Device not found or not authorized to access its sensor data."
            )

        results = self.sensor_repo.db.query(
            Sensor.id.label("sensor_id"),
            Sensor.name.label("sensor_name"),
            Sensor.unit_of_measurement.label("unit_of_measurement"),
            func.to_char(SensorData.timestamp, 'YYYY-MM-DD').label("date"),
            func.avg(SensorData.value).label("average_value")
        ).join(SensorData, Sensor.id == SensorData.sensor_id) \
        .filter(Sensor.device_id == device_id) \
        .group_by(
            Sensor.id,
            Sensor.name,
            Sensor.unit_of_measurement,
            func.to_char(SensorData.timestamp, 'YYYY-MM-DD')
        ) \
        .order_by(Sensor.id, func.to_char(SensorData.timestamp, 'YYYY-MM-DD')) \
        .all()

        return [SensorDailyAverage.model_validate(r) for r in results]

    def get_weekly_averages_for_device(self, device_id: uuid.UUID, current_user_id: uuid.UUID) -> List[SensorWeeklyAverage]:
        device = self.device_repo.get_by_id(device_id)
        if not device or device.project.user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Device not found or not authorized to access its sensor data."
            )

        results = self.sensor_repo.db.query(
            Sensor.id.label("sensor_id"),
            Sensor.name.label("sensor_name"),
            Sensor.unit_of_measurement.label("unit_of_measurement"),
            func.to_char(func.date_trunc('week', SensorData.timestamp), 'YYYY-MM-DD').label("week_start_date"),
            func.avg(SensorData.value).label("average_value")
        ).join(SensorData, Sensor.id == SensorData.sensor_id) \
        .filter(Sensor.device_id == device_id) \
        .group_by(
            Sensor.id,
            Sensor.name,
            Sensor.unit_of_measurement,
            func.date_trunc('week', SensorData.timestamp)
        ) \
        .order_by(Sensor.id, func.date_trunc('week', SensorData.timestamp)) \
        .all()

        return [SensorWeeklyAverage.model_validate(r) for r in results]

    def get_monthly_averages_for_device(self, device_id: uuid.UUID, current_user_id: uuid.UUID) -> List[SensorMonthlyAverage]:
        device = self.device_repo.get_by_id(device_id)
        if not device or device.project.user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Device not found or not authorized to access its sensor data."
            )

        results = self.sensor_repo.db.query(
            Sensor.id.label("sensor_id"),
            Sensor.name.label("sensor_name"),
            Sensor.unit_of_measurement.label("unit_of_measurement"),
            func.to_char(SensorData.timestamp, 'YYYY-MM').label("month"),
            func.avg(SensorData.value).label("average_value")
        ).join(SensorData, Sensor.id == SensorData.sensor_id) \
        .filter(Sensor.device_id == device_id) \
        .group_by(
            Sensor.id,
            Sensor.name,
            Sensor.unit_of_measurement,
            func.to_char(SensorData.timestamp, 'YYYY-MM')
        ) \
        .order_by(Sensor.id, func.to_char(SensorData.timestamp, 'YYYY-MM')) \
        .all()

        return [SensorMonthlyAverage.model_validate(r) for r in results]
        
