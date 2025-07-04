from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.schemas.user import UserCreate, UserOut
from app.schemas.token import Token
from app.core.dependencies import get_db
from app.core.security import create_access_token
from app.services.user_service import UserService

router = APIRouter()

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Registra um novo usuário no sistema.
    """
    user_service = UserService(db)
    return user_service.create_user(user_in)

@router.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Endpoint para login de usuário e obtenção de token JWT.
    Retorna um token de acesso que deve ser usado para autenticar outras requisições.
    """
    user_service = UserService(db)
    user = user_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": str(user.id), "username": user.username})
    return {"access_token": access_token, "token_type": "bearer"}