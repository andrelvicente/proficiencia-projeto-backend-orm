from app.services.sensor_device import SensorService
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid

from app.schemas.sensor import SensorCreate, SensorOut, SensorUpdate
from app.core.dependencies import get_db, get_current_user
from app.db.models import User as DBUser

router = APIRouter()

# Helper para HATEOAS (simplificado)
def add_sensor_links(sensor: SensorOut) -> dict:
    links = {
        "self": {"href": f"/api/v1/sensors/{sensor.id}", "method": "GET"},
        "update": {"href": f"/api/v1/sensors/{sensor.id}", "method": "PUT"},
        "delete": {"href": f"/api/v1/sensors/{sensor.id}", "method": "DELETE"},
        "device": {"href": f"/api/v1/devices/{sensor.device_id}", "method": "GET"},
        "sensor_data": {"href": f"/api/v1/sensors/{sensor.id}/data", "method": "GET"},
        "add_data": {"href": f"/api/v1/sensor-data/", "method": "POST", "body_params": {"sensor_id": str(sensor.id), "value": "..."}},
    }
    return sensor.model_dump(by_alias=True, exclude_unset=True) | {"_links": links}

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_sensor(sensor_in: SensorCreate, db: Session = Depends(get_db),
                  current_user: DBUser = Depends(get_current_user)):
    """
    Cria um novo sensor associado a um dispositivo.
    O usuário deve ser o proprietário do projeto do dispositivo.
    """
    sensor_service = SensorService(db)
    sensor = sensor_service.create_sensor(sensor_in, current_user.id)
    return add_sensor_links(SensorOut.model_validate(sensor))

@router.get("/", response_model=list[dict])
def read_sensors(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                 current_user: DBUser = Depends(get_current_user),
                 device_id: uuid.UUID | None = None):
    """
    Lista todos os sensores (filtrando por dispositivo se especificado).
    Acesso restrito aos sensores de dispositivos do usuário logado.
    """
    sensor_service = SensorService(db)
    if device_id:
        sensors = sensor_service.get_sensors_by_device(device_id, current_user.id, skip=skip, limit=limit)
    else:
        # Lista todos os sensores que o usuário tem acesso (mais complexo sem filtro)
        # Por simplicidade, pode-se exigir device_id ou implementar um filtro mais amplo aqui
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please provide a 'device_id' parameter.")
    
    return [add_sensor_links(SensorOut.model_validate(s)) for s in sensors]

@router.get("/{sensor_id}", response_model=dict)
def read_sensor(sensor_id: uuid.UUID, db: Session = Depends(get_db),
                current_user: DBUser = Depends(get_current_user)):
    """
    Obtém detalhes de um sensor específico por ID.
    O usuário deve ser o proprietário do projeto ao qual o sensor pertence.
    """
    sensor_service = SensorService(db)
    sensor = sensor_service.get_sensor(sensor_id)
    if sensor.device.project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this sensor")
    return add_sensor_links(SensorOut.model_validate(sensor))

@router.put("/{sensor_id}", response_model=dict)
def update_sensor(sensor_id: uuid.UUID, sensor_in: SensorUpdate, db: Session = Depends(get_db),
                  current_user: DBUser = Depends(get_current_user)):
    """
    Atualiza um sensor existente.
    O usuário deve ser o proprietário do projeto ao qual o sensor pertence.
    """
    sensor_service = SensorService(db)
    updated_sensor = sensor_service.update_sensor(sensor_id, sensor_in, current_user.id)
    return add_sensor_links(SensorOut.model_validate(updated_sensor))

@router.delete("/{sensor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sensor(sensor_id: uuid.UUID, db: Session = Depends(get_db),
                  current_user: DBUser = Depends(get_current_user)):
    """
    Exclui um sensor.
    O usuário deve ser o proprietário do projeto ao qual o sensor pertence.
    """
    sensor_service = SensorService(db)
    sensor_service.delete_sensor(sensor_id, current_user.id)
    return {"message": "Sensor deleted successfully"}