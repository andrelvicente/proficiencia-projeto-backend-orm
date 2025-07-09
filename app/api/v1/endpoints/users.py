from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid

from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.core.dependencies import get_db, get_current_user
from app.services.user_service import UserService
from app.db.models import User as DBUser

router = APIRouter()

def add_user_links(user: UserOut) -> dict:
    links = {
        "self": {"href": f"/api/v1/users/{user.id}", "method": "GET"},
        "update": {"href": f"/api/v1/users/{user.id}", "method": "PUT"},
        "delete": {"href": f"/api/v1/users/{user.id}", "method": "DELETE"},
    }
    return user.model_dump(by_alias=True, exclude_unset=True) | {"_links": links}

@router.get("/", response_model=list[dict])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
               current_user: DBUser = Depends(get_current_user)):
    """
    Lista todos os usuários. Requer autenticação.
    """
    user_service = UserService(db)
    users = user_service.get_all_users(skip=skip, limit=limit)
    return [add_user_links(UserOut.from_orm(user)) for user in users]

@router.get("/{user_id}", response_model=dict)
def read_user(user_id: uuid.UUID, db: Session = Depends(get_db),
              current_user: DBUser = Depends(get_current_user)):
    """
    Obtém detalhes de um usuário específico por ID. Requer autenticação.
    """
    user_service = UserService(db)
    if str(user_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this user's data")
    user = user_service.get_user(user_id)
    return add_user_links(UserOut.from_orm(user))

@router.put("/{user_id}", response_model=dict)
def update_user(user_id: uuid.UUID, user_in: UserUpdate, db: Session = Depends(get_db),
                current_user: DBUser = Depends(get_current_user)):
    """
    Atualiza um usuário existente. Requer autenticação e ser o próprio usuário.
    """
    if str(user_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this user")
    user_service = UserService(db)
    updated_user = user_service.update_user(user_id, user_in)
    return add_user_links(UserOut.from_orm(updated_user))

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: uuid.UUID, db: Session = Depends(get_db),
                current_user: DBUser = Depends(get_current_user)):
    """
    Exclui um usuário. Requer autenticação e ser o próprio usuário.
    """
    if str(user_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this user")
    user_service = UserService(db)
    user_service.delete_user(user_id)
    return {"message": "User deleted successfully"}