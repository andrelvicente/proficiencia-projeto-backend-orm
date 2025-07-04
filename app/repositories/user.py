from sqlalchemy.orm import Session
from app.db.models import User
from app.repositories.base import BaseRepository

class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_username(self, username: str) -> User | None:
        return self.db.query(self.model).filter(self.model.username == username).first()

    def get_by_email(self, email: str) -> User | None:
        return self.db.query(self.model).filter(self.model.email == email).first()