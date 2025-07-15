import os
from dotenv import load_dotenv

if os.getenv("ENV") != "production":
    load_dotenv()
    
class Settings:
    PROJECT_NAME: str = "IoT Project Manager API"
    PROJECT_VERSION: str = "1.0.0"

    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@db_host:5432/iot_db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey") 
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 

settings = Settings()