from typing import List
import uuid
from sqlalchemy.orm import Session
from app.db.models import Project
from app.repositories.base import BaseRepository

class ProjectRepository(BaseRepository[Project]):
    def __init__(self, db: Session):
        super().__init__(Project, db)

    def get_projects_by_user(self, user_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Project]:
        return self.db.query(self.model).filter(self.model.user_id == user_id).offset(skip).limit(limit).all()