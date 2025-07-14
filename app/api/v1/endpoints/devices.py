from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import uuid

from app.schemas.device import DeviceCreate, DeviceOut, DeviceUpdate
from app.schemas.sensor import SensorWithRecentData
from app.schemas.sensor_data import SensorDailyAverage, SensorMonthlyAverage, SensorWeeklyAverage
from app.schemas.tag import TagOut
from app.core.dependencies import get_db, get_current_user
from app.services.device_service import DeviceService
from app.db.models import User as DBUser
from app.services.sensor_device import SensorService

router = APIRouter()

def add_device_links(device: DeviceOut) -> dict:
    links = {
        "self": {"href": f"/api/v1/devices/{device.id}", "method": "GET"},
        "update": {"href": f"/api/v1/devices/{device.id}", "method": "PUT"},
        "delete": {"href": f"/api/v1/devices/{device.id}", "method": "DELETE"},
        "project": {"href": f"/api/v1/projects/{device.project_id}", "method": "GET"},
        "sensors": {"href": f"/api/v1/devices/{device.id}/sensors", "method": "GET"},
        "tags": {"href": f"/api/v1/devices/{device.id}/tags", "method": "GET"},
        "add_tags": {"href": f"/api/v1/devices/{device.id}/tags", "method": "POST"},
    }
    return device.model_dump(by_alias=True, exclude_unset=True) | {"_links": links}


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_device(device_in: DeviceCreate,
                  tag_ids: list[uuid.UUID] = Query([]),
                  db: Session = Depends(get_db),
                  current_user: DBUser = Depends(get_current_user)):
    """
    Cria um novo dispositivo associado a um projeto.
    O usuário deve ser o proprietário do projeto.
    """
    device_service = DeviceService(db)
    device = device_service.create_device(device_in, current_user.id, tag_ids=tag_ids)
    return add_device_links(DeviceOut.model_validate(device))

@router.get("/", response_model=list[dict])
def read_devices(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                 current_user: DBUser = Depends(get_current_user),
                 project_id: uuid.UUID | None = None,
                 query: str | None = None):
    """
    Lista todos os dispositivos (filtrando por projeto se especificado) ou pesquisa por texto.
    Acesso restrito aos dispositivos de projetos do usuário logado.
    """
    device_service = DeviceService(db)
    if project_id:
        devices = device_service.get_devices_by_project(project_id, current_user.id, skip=skip, limit=limit)
    elif query:
        devices = device_service.search_devices(query, skip=skip, limit=limit)
    else:
        # Para listar todos os dispositivos do usuário, precisaria de uma query mais complexa ou outro endpoint
        # Por simplicidade, se não houver project_id ou query, retorna uma lista vazia ou força um erro
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please provide a 'project_id' or 'query' parameter.")
    
    return [add_device_links(DeviceOut.model_validate(d)) for d in devices]


@router.get("/{device_id}", response_model=dict)
def read_device(device_id: uuid.UUID, db: Session = Depends(get_db),
                current_user: DBUser = Depends(get_current_user)):
    """
    Obtém detalhes de um dispositivo específico por ID.
    O usuário deve ser o proprietário do projeto ao qual o dispositivo pertence.
    """
    device_service = DeviceService(db)
    device = device_service.get_device(device_id)
    if device.project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this device")
    return add_device_links(DeviceOut.model_validate(device))

@router.put("/{device_id}", response_model=dict)
def update_device(device_id: uuid.UUID, device_in: DeviceUpdate, db: Session = Depends(get_db),
                  current_user: DBUser = Depends(get_current_user)):
    """
    Atualiza um dispositivo existente.
    O usuário deve ser o proprietário do projeto ao qual o dispositivo pertence.
    """
    device_service = DeviceService(db)
    updated_device = device_service.update_device(device_id, device_in, current_user.id)
    return add_device_links(DeviceOut.model_validate(updated_device))

@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(device_id: uuid.UUID, db: Session = Depends(get_db),
                  current_user: DBUser = Depends(get_current_user)):
    """
    Exclui um dispositivo.
    O usuário deve ser o proprietário do projeto ao qual o dispositivo pertence.
    """
    device_service = DeviceService(db)
    device_service.delete_device(device_id, current_user.id)
    return {"message": "Device deleted successfully"}


# Endpoints para gerenciamento de Tags em Dispositivos
@router.post("/{device_id}/tags", response_model=dict)
def add_tags_to_device(device_id: uuid.UUID, tag_ids: list[uuid.UUID], db: Session = Depends(get_db),
                       current_user: DBUser = Depends(get_current_user)):
    """
    Adiciona tags a um dispositivo existente.
    """
    device_service = DeviceService(db)
    device = device_service.add_tags_to_device(device_id, tag_ids, current_user.id)
    return add_device_links(DeviceOut.model_validate(device))

@router.delete("/{device_id}/tags", response_model=dict)
def remove_tags_from_device(device_id: uuid.UUID, tag_ids: list[uuid.UUID], db: Session = Depends(get_db),
                            current_user: DBUser = Depends(get_current_user)):
    """
    Remove tags de um dispositivo existente.
    """
    device_service = DeviceService(db)
    device = device_service.remove_tags_from_device(device_id, tag_ids, current_user.id)
    return add_device_links(DeviceOut.model_validate(device))

@router.get("/{device_id}/tags", response_model=list[TagOut])
def get_device_tags(device_id: uuid.UUID, db: Session = Depends(get_db),
                    current_user: DBUser = Depends(get_current_user)):
    """
    Lista as tags associadas a um dispositivo.
    """
    device_service = DeviceService(db)
    device = device_service.get_device(device_id)
    if device.project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this device's tags")
    return device.tags

@router.get("/{device_id}/recent-sensor-data", response_model=list[SensorWithRecentData])
def get_recent_sensor_data_for_device_endpoint(
    device_id: uuid.UUID,
    limit: int = Query(1, ge=1, description="Número de registros mais recentes por sensor."), # Parâmetro limit
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user)
):
    """
    Retorna os N dados mais recentes de todos os sensores associados a um determinado dispositivo.
    O usuário deve ser o proprietário do projeto ao qual o dispositivo pertence.
    """
    sensor_service = SensorService(db)
    recent_readings = sensor_service.get_recent_sensor_data_for_device(device_id, current_user.id, limit)
    
    if not recent_readings:
        # Se não houver dados ou sensores, retorna 200 OK com lista vazia.
        pass 
        
    return recent_readings

# --- NOVOS ENDPOINTS PARA MÉDIAS ---

@router.get("/{device_id}/sensor-data/averages/daily", response_model=list[SensorDailyAverage])
def get_device_sensor_daily_averages(
    device_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user)
):
    """
    Retorna a média aritmética dos dados de cada sensor de um dispositivo, agrupada por dia.
    """
    sensor_service = SensorService(db)
    return sensor_service.get_daily_averages_for_device(device_id, current_user.id)

@router.get("/{device_id}/sensor-data/averages/weekly", response_model=list[SensorWeeklyAverage])
def get_device_sensor_weekly_averages(
    device_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user)
):
    """
    Retorna a média aritmética dos dados de cada sensor de um dispositivo, agrupada por semana.
    """
    sensor_service = SensorService(db)
    return sensor_service.get_weekly_averages_for_device(device_id, current_user.id)

@router.get("/{device_id}/sensor-data/averages/monthly", response_model=list[SensorMonthlyAverage])
def get_device_sensor_monthly_averages(
    device_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user)
):
    """
    Retorna a média aritmética dos dados de cada sensor de um dispositivo, agrupada por mês.
    """
    sensor_service = SensorService(db)
    return sensor_service.get_monthly_averages_for_device(device_id, current_user.id)