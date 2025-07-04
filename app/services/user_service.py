import uuid
from sqlalchemy.orm import Session
from app.db.models import User
from app.schemas.user import UserCreate, UserUpdate
from app.repositories.user import UserRepository
from app.core.security import get_password_hash, verify_password
from fastapi import HTTPException, status

class UserService:
    def __init__(self, db: Session):
        self.user_repo = UserRepository(db)

    def get_user(self, user_id: uuid.UUID) -> User:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user

    def get_user_by_username(self, username: str) -> User:
        user = self.user_repo.get_by_username(username)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user

    def get_all_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        return self.user_repo.get_all(skip=skip, limit=limit)

    def create_user(self, user_in: UserCreate) -> User:
        if self.user_repo.get_by_username(user_in.username):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
        if self.user_repo.get_by_email(user_in.email):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
        
        hashed_password = get_password_hash(user_in.password)
        user_data = user_in.model_dump()
        user_data["hashed_password"] = hashed_password
        del user_data["password"]

        new_user = self.user_repo.create(user_data)
        return new_user

    def update_user(self, user_id: uuid.UUID, user_in: UserUpdate) -> User:
        user = self.get_user(user_id)
        updated_user = self.user_repo.update(user, user_in.model_dump(exclude_unset=True))
        return updated_user

    def delete_user(self, user_id: uuid.UUID):
        user = self.get_user(user_id)
        self.user_repo.delete(user)

    def authenticate_user(self, username: str, password: str) -> User | None:
        user = self.user_repo.get_by_username(username)
        if not user or not verify_password(password, user.hashed_password):
            return None
        return user