import uuid
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Numeric, Table
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base import Base

project_tags = Table(
    'project_tags',
    Base.metadata,
    Column('project_id', UUID(as_uuid=True), ForeignKey('projects.id', ondelete="CASCADE"), primary_key=True),
    Column('tag_id', UUID(as_uuid=True), ForeignKey('tags.id', ondelete="CASCADE"), primary_key=True)
)

device_tags = Table(
    'device_tags',
    Base.metadata,
    Column('device_id', UUID(as_uuid=True), ForeignKey('devices.id', ondelete="CASCADE"), primary_key=True),
    Column('tag_id', UUID(as_uuid=True), ForeignKey('tags.id', ondelete="CASCADE"), primary_key=True)
)

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=False), server_default=func.now())
    updated_at = Column(DateTime(timezone=False), onupdate=func.now(), server_default=func.now())

    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")

class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=False), server_default=func.now())
    updated_at = Column(DateTime(timezone=False), onupdate=func.now(), server_default=func.now())

    owner = relationship("User", back_populates="projects")
    devices = relationship("Device", back_populates="project", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary=project_tags, back_populates="projects")

class Device(Base):
    __tablename__ = "devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    serial_number = Column(String(100), unique=True, nullable=False)
    device_type = Column(String(50), nullable=False) # e.g., 'sensor', 'actuator', 'gateway'
    status = Column(String(20), default='offline') # e.g., 'online', 'offline', 'error'
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=False), server_default=func.now())
    updated_at = Column(DateTime(timezone=False), onupdate=func.now(), server_default=func.now())

    project = relationship("Project", back_populates="devices")
    sensors = relationship("Sensor", back_populates="device", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary=device_tags, back_populates="devices")
    commands = relationship("Command", back_populates="device", cascade="all, delete-orphan")


class Sensor(Base):
    __tablename__ = "sensors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    unit_of_measurement = Column(String(20))
    min_value = Column(Numeric)
    max_value = Column(Numeric)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=False), server_default=func.now())
    updated_at = Column(DateTime(timezone=False), onupdate=func.now(), server_default=func.now())

    device = relationship("Device", back_populates="sensors")
    sensor_data = relationship("SensorData", back_populates="sensor", cascade="all, delete-orphan")

class SensorData(Base):
    __tablename__ = "sensor_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    value = Column(Numeric, nullable=False)
    timestamp = Column(DateTime(timezone=False), server_default=func.now())
    sensor_id = Column(UUID(as_uuid=True), ForeignKey("sensors.id", ondelete="CASCADE"), nullable=False)

    sensor = relationship("Sensor", back_populates="sensor_data")

class Tag(Base):
    __tablename__ = "tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, nullable=False)

    projects = relationship("Project", secondary=project_tags, back_populates="tags")
    devices = relationship("Device", secondary=device_tags, back_populates="tags")
    
class Command(Base):
    __tablename__ = "commands"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    command_type = Column(String(50), nullable=False) # Ex: 'ligar_bomba', 'desligar_luz'
    parameters = Column(Text, nullable=True) # JSON string ou texto com parâmetros adicionais
    status = Column(String(20), default='pending') # 'pending', 'sent', 'acknowledged', 'failed', 'completed'
    issued_at = Column(DateTime(timezone=False), server_default=func.now())
    completed_at = Column(DateTime(timezone=False), nullable=True)
    response_message = Column(Text, nullable=True) # Mensagem de resposta do dispositivo

    device = relationship("Device", back_populates="commands")
    