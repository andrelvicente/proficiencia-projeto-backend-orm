from sqlalchemy.orm import Session
from app.db.models import Tag
from app.repositories.base import BaseRepository

class TagRepository(BaseRepository[Tag]):
    def __init__(self, db: Session):
        super().__init__(Tag, db)

    def get_by_name(self, name: str) -> Tag | None:
        return self.db.query(self.model).filter(self.model.name == name).first()