from sqlalchemy import create_engine, Column, String, Integer, Float, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# PostgreSQL connection
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://admin:1234@localhost:5432/postgres')

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Database Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    successful_repairs = Column(Integer, default=0)
    failed_repairs = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    created_faults = relationship("FaultRecord", foreign_keys="FaultRecord.created_by", back_populates="creator")
    assigned_faults = relationship("FaultRecord", foreign_keys="FaultRecord.assigned_to", back_populates="assignee")
    requested_transfers = relationship("EquipmentTransfer", foreign_keys="EquipmentTransfer.requested_by", back_populates="requester")

class Device(Base):
    __tablename__ = "devices"
    
    id = Column(String(50), primary_key=True)
    type = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False)
    total_failures = Column(Integer, default=0)
    total_operating_hours = Column(Float, default=0.0)
    total_repair_hours = Column(Float, default=0.0)
    mtbf = Column(Float, default=0.0)
    mttr = Column(Float, default=0.0)
    availability = Column(Float, default=100.0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Extra fields from Excel
    kat = Column(String(50))
    demirbas_adi = Column(String(255))
    marka = Column(String(255))
    model = Column(String(255))
    seri_no = Column(String(255))
    adet = Column(Integer, default=1)
    ariza_adeti = Column(Integer, default=0)
    ortalama_yil_sure = Column(String(50))
    
    # Relationships
    faults = relationship("FaultRecord", back_populates="device", cascade="all, delete-orphan")
    transfers = relationship("EquipmentTransfer", back_populates="device", cascade="all, delete-orphan")

class FaultRecord(Base):
    __tablename__ = "fault_records"
    
    id = Column(String(50), primary_key=True)
    created_by = Column(String(50), ForeignKey('users.id'), nullable=False)
    created_by_name = Column(String(255))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    device_id = Column(String(50), ForeignKey('devices.id'), nullable=False)
    device_code = Column(String(100))
    device_type = Column(String(255))
    description = Column(Text, nullable=False)
    assigned_to = Column(String(50), ForeignKey('users.id'))
    assigned_to_name = Column(String(255))
    repair_start = Column(DateTime(timezone=True))
    repair_end = Column(DateTime(timezone=True))
    repair_duration = Column(Float, default=0.0)
    repair_notes = Column(Text)
    repair_category = Column(String(50))
    breakdown_iteration = Column(Integer, default=0)
    status = Column(String(50), default='open')
    confirmed_by = Column(String(50), ForeignKey('users.id'))
    confirmed_at = Column(DateTime(timezone=True))
    
    # Relationships
    device = relationship("Device", back_populates="faults")
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_faults")
    assignee = relationship("User", foreign_keys=[assigned_to], back_populates="assigned_faults")

class EquipmentTransfer(Base):
    __tablename__ = "equipment_transfers"
    
    id = Column(String(50), primary_key=True)
    device_id = Column(String(50), ForeignKey('devices.id'), nullable=False)
    device_code = Column(String(100))
    device_type = Column(String(255))
    from_location = Column(String(255), nullable=False)
    to_location = Column(String(255), nullable=False)
    requested_by = Column(String(50), ForeignKey('users.id'), nullable=False)
    requested_by_name = Column(String(255))
    requested_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    reason = Column(Text, nullable=False)
    status = Column(String(50), default='pending')
    approved_by = Column(String(50), ForeignKey('users.id'))
    approved_by_name = Column(String(255))
    approved_at = Column(DateTime(timezone=True))
    rejection_reason = Column(Text)
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    device = relationship("Device", back_populates="transfers")
    requester = relationship("User", foreign_keys=[requested_by], back_populates="requested_transfers")

class Log(Base):
    __tablename__ = "logs"
    
    id = Column(String(50), primary_key=True)
    record_id = Column(String(50))
    event = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    user_id = Column(String(50), ForeignKey('users.id'))
    user_name = Column(String(255))

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
