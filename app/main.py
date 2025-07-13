from fastapi import FastAPI
from app.api.v1.endpoints import (
    command, users, projects, devices, sensors, sensor_data, tags, auth
)
from app.db.base import Base
from app.db.session import engine

def create_app():
    Base.metadata.create_all(bind=engine)

    app = FastAPI(
        title="IoT Project Manager API",
        description="API RESTful para gerenciar projetos, dispositivos e sensores de IoT, com HATEOAS e autenticação.",
        version="1.0.0",
    )

    # Inclui os routers da API
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
    app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
    app.include_router(projects.router, prefix="/api/v1/projects", tags=["Projects"])
    app.include_router(devices.router, prefix="/api/v1/devices", tags=["Devices"])
    app.include_router(sensors.router, prefix="/api/v1/sensors", tags=["Sensors"])
    app.include_router(sensor_data.router, prefix="/api/v1/sensor-data", tags=["Sensor Data"])
    app.include_router(tags.router, prefix="/api/v1/tags", tags=["Tags"])
    app.include_router(command.router, prefix="/api/v1/commands", tags=["Commands"])

    @app.get("/")
    async def read_root():
        return {"message": "Welcome to the IoT Project Manager API!"}

    return app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(create_app(), host="0.0.0.0", port=8000)