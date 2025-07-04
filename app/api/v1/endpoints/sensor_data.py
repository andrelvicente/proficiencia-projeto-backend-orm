from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

from app.schemas.sensor_data import SensorDataCreate, SensorDataOut
from app.core.dependencies import get_db, get_current_user
from app.services.sensor_data_service import SensorDataService
from app.db.models import User as DBUser

router = APIRouter()

def add_sensor_data_links(data: SensorDataOut) -> dict:
    links = {
        "self": {"href": f"/api/v1/sensor-data/{data.id}", "method": "GET"},
        "sensor": {"href": f"/api/v1/sensors/{data.sensor_id}", "method": "GET"},
    }
    return data.model_dump(by_alias=True, exclude_unset=True) | {"_links": links}

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_sensor_data(data_in: SensorDataCreate, db: Session = Depends(get_db),
                       current_user: DBUser = Depends(get_current_user)):
    """
    Cria um novo registro de dado de sensor.
    O usuário deve ser o proprietário do projeto ao qual o sensor pertence.
    """
    sensor_data_service = SensorDataService(db)
    data = sensor_data_service.create_sensor_data(data_in, current_user.id)
    return add_sensor_data_links(SensorDataOut.model_validate(data))

@router.get("/", response_model=list[dict])
def read_sensor_data(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                     current_user: DBUser = Depends(get_current_user),
                     sensor_id: uuid.UUID | None = None,
                     start_time: datetime | None = Query(None, description="Start timestamp for data filtering"),
                     end_time: datetime | None = Query(None, description="End timestamp for data filtering")):
    """
    Lista todos os dados de sensor (filtrando por sensor e/ou período de tempo).
    Acesso restrito aos dados de sensores de dispositivos do usuário logado.
    """
    sensor_data_service = SensorDataService(db)
    if sensor_id:
        data = sensor_data_service.get_data_by_sensor(sensor_id, current_user.id, start_time=start_time, end_time=end_time, skip=skip, limit=limit)
    else:
        # Não é recomendado listar TODOS os dados de sensor sem filtro em um projeto real devido ao volume
        # Para fins de demonstração, pode-se descomentar, mas avisar sobre o potencial de lentidão
        # data = sensor_data_service.get_all_sensor_data(skip=skip, limit=limit)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please provide a 'sensor_id' to filter sensor data.")
    
    return [add_sensor_data_links(SensorDataOut.model_validate(d)) for d in data]


@router.get("/{data_id}", response_model=dict)
def read_single_sensor_data(data_id: uuid.UUID, db: Session = Depends(get_db),
                             current_user: DBUser = Depends(get_current_user)):
    """
    Obtém um único registro de dado de sensor por ID.
    O usuário deve ser o proprietário do projeto ao qual o dado pertence.
    """
    sensor_data_service = SensorDataService(db)
    data = sensor_data_service.get_sensor_data(data_id)
    if data.sensor.device.project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this sensor data")
    return add_sensor_data_links(SensorDataOut.model_validate(data))

@router.delete("/{data_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sensor_data(data_id: uuid.UUID, db: Session = Depends(get_db),
                       current_user: DBUser = Depends(get_current_user)):
    """
    Exclui um registro de dado de sensor.
    O usuário deve ser o proprietário do projeto ao qual o dado pertence.
    """
    sensor_data_service = SensorDataService(db)
    sensor_data_service.delete_sensor_data(data_id, current_user.id)
    return {"message": "Sensor data deleted successfully"}