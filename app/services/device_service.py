import uuid
from sqlalchemy.orm import Session
from app.db.models import Device, Project, Tag
from app.schemas.device import DeviceCreate, DeviceUpdate
from app.repositories.device import DeviceRepository
from app.repositories.project import ProjectRepository
from app.repositories.tag import TagRepository
from fastapi import HTTPException, status

class DeviceService:
    def __init__(self, db: Session):
        self.device_repo = DeviceRepository(db)
        self.project_repo = ProjectRepository(db)
        self.tag_repo = TagRepository(db)

    def get_device(self, device_id: uuid.UUID) -> Device:
        device = self.device_repo.get_by_id(device_id)
        if not device:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
        return device

    def get_all_devices(self, skip: int = 0, limit: int = 100) -> list[Device]:
        return self.device_repo.get_all(skip=skip, limit=limit)

    def get_devices_by_project(self, project_id: uuid.UUID, current_user_id: uuid.UUID, skip: int = 0, limit: int = 100) -> list[Device]:
        project = self.project_repo.get_by_id(project_id)
        if not project or project.user_id != current_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Project not found or not authorized to access it")
        return self.device_repo.get_devices_by_project(project_id, skip=skip, limit=limit)

    def search_devices(self, query: str, skip: int = 0, limit: int = 100) -> list[Device]:
        return self.device_repo.search_by_text(query, ['name', 'description', 'serial_number'], skip=skip, limit=limit)

    def create_device(self, device_in: DeviceCreate, current_user_id: uuid.UUID, tag_ids: list[uuid.UUID] = []) -> Device:
        project = self.project_repo.get_by_id(device_in.project_id)
        if not project or project.user_id != current_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Project not found or not authorized to add devices to it")

        with self.device_repo.db.begin_nested(): # Transação ACID
            if self.device_repo.get_by_serial_number(device_in.serial_number):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Device with this serial number already exists.")

            new_device = self.device_repo.create(device_in.model_dump())

            for tag_id in tag_ids:
                tag = self.tag_repo.get_by_id(tag_id)
                if not tag:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tag with ID {tag_id} not found.")
                new_device.tags.append(tag)

            self.device_repo.db.commit()
            self.device_repo.db.refresh(new_device)
            return new_device

    def update_device(self, device_id: uuid.UUID, device_in: DeviceUpdate, current_user_id: uuid.UUID) -> Device:
        device = self.get_device(device_id)
        if device.project.user_id != current_user_id: # Verifica se o projeto do dispositivo pertence ao usuário
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this device")
        
        with self.device_repo.db.begin_nested(): # Transação ACID
            updated_device = self.device_repo.update(device, device_in.model_dump(exclude_unset=True))
            self.device_repo.db.commit()
            return updated_device

    def delete_device(self, device_id: uuid.UUID, current_user_id: uuid.UUID):
        device = self.get_device(device_id)
        if device.project.user_id != current_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this device")
        
        with self.device_repo.db.begin_nested(): # Transação ACID
            self.device_repo.delete(device)
            self.device_repo.db.commit()

    def add_tags_to_device(self, device_id: uuid.UUID, tag_ids: list[uuid.UUID], current_user_id: uuid.UUID) -> Device:
        device = self.get_device(device_id)
        if device.project.user_id != current_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify this device")

        with self.device_repo.db.begin_nested():
            for tag_id in tag_ids:
                tag = self.tag_repo.get_by_id(tag_id)
                if not tag:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tag with ID {tag_id} not found.")
                if tag not in device.tags:
                    device.tags.append(tag)
            self.device_repo.db.commit()
            self.device_repo.db.refresh(device)
            return device

    def remove_tags_from_device(self, device_id: uuid.UUID, tag_ids: list[uuid.UUID], current_user_id: uuid.UUID) -> Device:
        device = self.get_device(device_id)
        if device.project.user_id != current_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify this device")

        with self.device_repo.db.begin_nested():
            for tag_id in tag_ids:
                tag_to_remove = next((t for t in device.tags if t.id == tag_id), None)
                if tag_to_remove:
                    device.tags.remove(tag_to_remove)
            self.device_repo.db.commit()
            self.device_repo.db.refresh(device)
            return device