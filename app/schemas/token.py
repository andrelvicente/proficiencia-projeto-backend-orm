from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    id: str | None = None # Aqui armazena o ID do usuário (subject do token)
    username: str | None = None