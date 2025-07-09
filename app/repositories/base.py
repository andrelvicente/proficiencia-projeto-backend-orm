from typing import Generic, TypeVar, Type, List, Optional
import uuid
from app.db.base import Base
from sqlalchemy.orm import Session
from sqlalchemy import func

# Define um tipo genérico para o modelo SQLAlchemy
ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get_by_id(self, item_id: uuid.UUID) -> Optional[ModelType]:
        return self.db.query(self.model).filter(self.model.id == item_id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def create(self, obj_in: dict) -> ModelType:
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, db_obj: ModelType, obj_in: dict) -> ModelType:
        for key, value in obj_in.items():
            setattr(db_obj, key, value)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, db_obj: ModelType) -> None:
        self.db.delete(db_obj)
        self.db.commit()

    def search_by_text(self, query: str, fields: List[str], skip: int = 0, limit: int = 100) -> List[ModelType]:
        filters = []
        for field in fields:
            if hasattr(self.model, field):
                filters.append(func.lower(getattr(self.model, field)).like(f"%{query.lower()}%"))
        
        if not filters:
            return [] 

        return self.db.query(self.model).filter(func.or_(*filters)).offset(skip).limit(limit).all()