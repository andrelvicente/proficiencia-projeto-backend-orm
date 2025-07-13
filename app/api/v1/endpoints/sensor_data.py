from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

from app.schemas.sensor import SensorCreate
from app.schemas.sensor_data import IngestDataPayload, SensorDataCreate, SensorDataOut
from app.core.dependencies import get_db, get_current_user
from app.services.device_service import DeviceService
from app.services.sensor_data_service import SensorDataService
from app.db.models import User as DBUser
from app.services.sensor_device import SensorService

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

@router.post("/ingest", status_code=status.HTTP_207_MULTI_STATUS) # Use 207 para indicar sucesso parcial
def ingest_generic_sensor_data(
    payload: IngestDataPayload,
    db: Session = Depends(get_db)
):
    """
    Endpoint genérico para ingestão de dados de múltiplos sensores de um dispositivo IoT.
    Recebe um número de série do dispositivo e uma lista de leituras.
    Para cada leitura, tenta encontrar o sensor correspondente. Se o sensor não existir
    e a lógica de negócio permitir, ele pode ser criado dinamicamente.
    Retorna 207 Multi-Status se houver sucesso parcial com erros.
    """
    device_service = DeviceService(db)
    sensor_service = SensorService(db)
    sensor_data_service = SensorDataService(db)

    # 1. Encontrar o Dispositivo pelo número de série
    device = device_service.device_repo.get_by_serial_number(payload.device_serial_number)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with serial number '{payload.device_serial_number}' not found."
        )

    # Para criar sensores dinamicamente ou para operações de SensorData,
    # precisamos do user_id do proprietário do projeto ao qual o dispositivo pertence.
    # Em um cenário de produção, um token de dispositivo dedicado seria mais seguro.
    owner_user_id = device.project.user_id

    ingested_count = 0
    errors = []
    processed_data_out = [] # Para retornar os dados que foram ingeridos com sucesso

    # Use uma transação para toda a operação de ingestão do payload
    with db.begin_nested(): # Inicia a transação ACID
        for reading in payload.readings:
            try:
                # Tenta encontrar o sensor usando o nome/ID fornecido e o ID do dispositivo
                sensor = sensor_service.sensor_repo.get_by_name_and_device(
                    name=reading.sensor_name_or_id,
                    device_id=device.id
                )

                if not sensor:
                    # Se o sensor não existir, cria-o dinamicamente
                    new_sensor_schema = SensorCreate(
                        name=reading.sensor_name_or_id,
                        unit_of_measurement=reading.unit_of_measurement,
                        device_id=device.id
                    )
                    sensor = sensor_service.create_sensor(new_sensor_schema, owner_user_id)
                    print(f"DEBUG: Sensor '{reading.sensor_name_or_id}' criado (ID: {sensor.id}) para o dispositivo '{device.name}'.")

                # Criar o SensorData para a leitura
                sensor_data_schema = SensorDataCreate(
                    sensor_id=sensor.id,
                    value=reading.value,
                    timestamp=reading.timestamp if reading.timestamp else datetime.utcnow()
                )
                
                # A camada de serviço já garante a atomicidade interna, mas a transação externa
                # garante que múltiplas inserções/criações para um payload sejam atômicas.
                new_data = sensor_data_service.create_sensor_data(sensor_data_schema, owner_user_id)
                processed_data_out.append(add_sensor_data_links(SensorDataOut.model_validate(new_data)))
                ingested_count += 1

            except HTTPException as e:
                errors.append(f"Leitura '{reading.sensor_name_or_id}' (Disp: {payload.device_serial_number}): {e.detail}")
                print(f"DEBUG: Erro ao processar leitura: {e.detail}")
            except Exception as e:
                errors.append(f"Leitura '{reading.sensor_name_or_id}' (Disp: {payload.device_serial_number}): Erro inesperado - {str(e)}")
                print(f"DEBUG: Erro inesperado: {e}")
        
    response_detail = {
        "message": f"Ingested {ingested_count} readings successfully.",
        "ingested_data": processed_data_out # Dados que foram realmente ingeridos
    }
    if errors:
        response_detail["warning"] = "Some readings encountered errors."
        response_detail["errors"] = errors
        raise HTTPException(status_code=status.HTTP_207_MULTI_STATUS, detail=response_detail)

    return response_detail
