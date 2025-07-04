from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Configura o motor do banco de dados (PostgreSQL)
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# Cria uma sessão local do banco de dados
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)