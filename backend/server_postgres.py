from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import traceback

# Import database models
from database import get_db, User, Device, FaultRecord, EquipmentTransfer, Log
from excel_service import ExcelReportService

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

security = HTTPBearer()

app = FastAPI()
api_router = APIRouter(prefix="/api")

# ===== PYDANTIC MODELS =====

class UserRole:
    HEALTH_STAFF = "health_staff"
    TECHNICIAN = "technician"
    MANAGER = "manager"
    QUALITY = "quality"

class FaultStatus:
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"

class RepairCategory:
    PART_REPLACEMENT = "part_replacement"
    ADJUSTMENT = "adjustment"
    COMPLETE_REPAIR = "complete_repair"
    OTHER = "other"

class TransferStatus:
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    email: EmailStr
    role: str
    successful_repairs: int = 0
    failed_repairs: int = 0
    created_at: datetime

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = UserRole.HEALTH_STAFF

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class DeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    code: str
    type: str
    location: str
    total_failures: int = 0
    total_operating_hours: float = 0.0
    total_repair_hours: float = 0.0
    mtbf: float = 0.0
    mttr: float = 0.0
    availability: float = 100.0
    created_at: datetime

class DeviceCreate(BaseModel):
    code: str
    type: str
    location: str
    total_operating_hours: float = 8760.0

class FaultRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_by: str
    created_by_name: str = ""
    created_at: datetime
    device_id: str
    device_code: str = ""
    device_type: str = ""
    description: str
    assigned_to: Optional[str] = None
    assigned_to_name: Optional[str] = None
    repair_start: Optional[datetime] = None
    repair_end: Optional[datetime] = None
    repair_duration: float = 0.0
    repair_notes: str = ""
    repair_category: Optional[str] = None
    breakdown_iteration: int = 0
    status: str = FaultStatus.OPEN
    confirmed_by: Optional[str] = None
    confirmed_at: Optional[datetime] = None

class FaultRecordCreate(BaseModel):
    device_id: str
    description: str

class FaultRecordAssign(BaseModel):
    assigned_to: str

class FaultRecordEndRepair(BaseModel):
    repair_notes: str
    repair_category: str

class TransferResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    device_id: str
    device_code: str = ""
    device_type: str = ""
    from_location: str
    to_location: str
    requested_by: str
    requested_by_name: str = ""
    requested_at: datetime
    reason: str
    status: str = TransferStatus.PENDING
    approved_by: Optional[str] = None
    approved_by_name: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    completed_at: Optional[datetime] = None

class TransferCreate(BaseModel):
    device_id: str
    to_location: str
    reason: str

class TransferReject(BaseModel):
    rejection_reason: str

# ===== AUTHENTICATION =====

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

# ===== HELPER FUNCTIONS =====

def create_log(db: Session, record_id: str, event: str, user_id: str = None, user_name: str = None):
    log = Log(
        id=str(uuid.uuid4()),
        record_id=record_id,
        event=event,
        user_id=user_id,
        user_name=user_name
    )
    db.add(log)
    db.commit()

def calculate_device_metrics(db: Session, device_id: str):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        return
    
    total_failures = device.total_failures
    total_operating_hours = device.total_operating_hours
    total_repair_hours = device.total_repair_hours
    
    if total_failures > 0:
        mttr = total_repair_hours / total_failures
        if total_operating_hours > 0:
            mtbf = (total_operating_hours - total_repair_hours) / total_failures
        else:
            mtbf = 0.0
        
        if (mtbf + mttr) > 0:
            availability = (mtbf / (mtbf + mttr)) * 100
        else:
            availability = 100.0
    else:
        mtbf = 0.0
        mttr = 0.0
        availability = 100.0
    
    device.mtbf = mtbf
    device.mttr = mttr
    device.availability = availability
    db.commit()

# ===== AUTH ROUTES =====

@api_router.post("/auth/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if email already exists
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    hashed_password = pwd_context.hash(user_data.password)
    
    # Create user
    user = User(
        id=str(uuid.uuid4()),
        name=user_data.name,
        email=user_data.email,
        password=hashed_password,
        role=user_data.role
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user

@api_router.post("/auth/login")
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not pwd_context.verify(credentials.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user.id, "email": user.email})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
    }

@api_router.get("/auth/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# ===== USERS ROUTES =====

@api_router.get("/users", response_model=List[UserResponse])
def get_users(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role not in [UserRole.MANAGER, UserRole.QUALITY]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    users = db.query(User).all()
    return users

@api_router.get("/users/technicians", response_model=List[UserResponse])
def get_technicians(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    users = db.query(User).filter(User.role == UserRole.TECHNICIAN).all()
    return users

# ===== DEVICES ROUTES =====

@api_router.post("/devices", response_model=DeviceResponse)
def create_device(device_data: DeviceCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role not in [UserRole.MANAGER, UserRole.TECHNICIAN]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check if code already exists
    existing = db.query(Device).filter(Device.code == device_data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Device code already exists")
    
    device = Device(
        id=str(uuid.uuid4()),
        code=device_data.code,
        type=device_data.type,
        location=device_data.location,
        total_operating_hours=device_data.total_operating_hours
    )
    
    db.add(device)
    db.commit()
    db.refresh(device)
    
    return device

@api_router.get("/devices", response_model=List[DeviceResponse])
def get_devices(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    devices = db.query(Device).all()
    return devices

@api_router.get("/devices/{device_id}", response_model=DeviceResponse)
def get_device(device_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device

@api_router.get("/devices/{device_id}/faults", response_model=List[FaultRecordResponse])
def get_device_faults(device_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    faults = db.query(FaultRecord).filter(FaultRecord.device_id == device_id).order_by(FaultRecord.created_at.desc()).all()
    return faults

# ===== FAULT RECORDS ROUTES =====

@api_router.post("/faults", response_model=FaultRecordResponse)
def create_fault(fault_data: FaultRecordCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Get device
    device = db.query(Device).filter(Device.id == fault_data.device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Increment device failure count
    device.total_failures += 1
    
    fault = FaultRecord(
        id=str(uuid.uuid4()),
        created_by=current_user.id,
        created_by_name=current_user.name,
        device_id=fault_data.device_id,
        device_code=device.code,
        device_type=device.type,
        description=fault_data.description,
        breakdown_iteration=device.total_failures
    )
    
    db.add(fault)
    db.commit()
    db.refresh(fault)
    
    # Create log
    create_log(db, fault.id, f"Arıza kaydı oluşturuldu: {fault_data.description}", current_user.id, current_user.name)
    
    return fault

@api_router.get("/faults", response_model=List[FaultRecordResponse])
def get_faults(status: Optional[str] = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(FaultRecord)
    
    if status:
        query = query.filter(FaultRecord.status == status)
    
    # Role-based filtering
    if current_user.role == UserRole.TECHNICIAN:
        query = query.filter(FaultRecord.assigned_to == current_user.id)
    elif current_user.role == UserRole.HEALTH_STAFF:
        query = query.filter(FaultRecord.created_by == current_user.id)
    
    faults = query.order_by(FaultRecord.created_at.desc()).all()
    return faults

@api_router.get("/faults/all", response_model=List[FaultRecordResponse])
def get_all_faults(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role not in [UserRole.MANAGER, UserRole.QUALITY]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    faults = db.query(FaultRecord).order_by(FaultRecord.created_at.desc()).all()
    return faults

@api_router.get("/faults/{fault_id}", response_model=FaultRecordResponse)
def get_fault(fault_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    fault = db.query(FaultRecord).filter(FaultRecord.id == fault_id).first()
    if not fault:
        raise HTTPException(status_code=404, detail="Fault not found")
    return fault

@api_router.post("/faults/{fault_id}/assign")
def assign_fault(fault_id: str, assign_data: FaultRecordAssign, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != UserRole.MANAGER:
        raise HTTPException(status_code=403, detail="Only managers can assign faults")
    
    fault = db.query(FaultRecord).filter(FaultRecord.id == fault_id).first()
    if not fault:
        raise HTTPException(status_code=404, detail="Fault not found")
    
    technician = db.query(User).filter(User.id == assign_data.assigned_to).first()
    if not technician or technician.role != UserRole.TECHNICIAN:
        raise HTTPException(status_code=400, detail="Invalid technician")
    
    fault.assigned_to = assign_data.assigned_to
    fault.assigned_to_name = technician.name
    fault.status = FaultStatus.IN_PROGRESS
    db.commit()
    
    create_log(db, fault_id, f"Teknisyene atandı: {technician.name}", current_user.id, current_user.name)
    
    return {"message": "Fault assigned successfully"}

@api_router.post("/faults/{fault_id}/start-repair")
def start_repair(fault_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != UserRole.TECHNICIAN:
        raise HTTPException(status_code=403, detail="Only technicians can start repairs")
    
    fault = db.query(FaultRecord).filter(FaultRecord.id == fault_id).first()
    if not fault:
        raise HTTPException(status_code=404, detail="Fault not found")
    
    if fault.assigned_to != current_user.id:
        raise HTTPException(status_code=403, detail="Not assigned to you")
    
    if fault.repair_start:
        raise HTTPException(status_code=400, detail="Repair already started")
    
    fault.repair_start = datetime.now(timezone.utc)
    db.commit()
    
    create_log(db, fault_id, "Onarım başlatıldı", current_user.id, current_user.name)
    
    return {"message": "Repair started"}

@api_router.post("/faults/{fault_id}/end-repair")
def end_repair(fault_id: str, repair_data: FaultRecordEndRepair, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != UserRole.TECHNICIAN:
        raise HTTPException(status_code=403, detail="Only technicians can end repairs")
    
    if not repair_data.repair_category:
        raise HTTPException(status_code=400, detail="Onarım kategorisi seçilmelidir")
    
    if len(repair_data.repair_notes) < 20:
        raise HTTPException(status_code=400, detail="Onarım notları en az 20 karakter olmalıdır")
    
    fault = db.query(FaultRecord).filter(FaultRecord.id == fault_id).first()
    if not fault:
        raise HTTPException(status_code=404, detail="Fault not found")
    
    if fault.assigned_to != current_user.id:
        raise HTTPException(status_code=403, detail="Not assigned to you")
    
    if not fault.repair_start:
        raise HTTPException(status_code=400, detail="Repair not started yet")
    
    if fault.repair_end:
        raise HTTPException(status_code=400, detail="Repair already ended")
    
    repair_end = datetime.now(timezone.utc)
    repair_duration = (repair_end - fault.repair_start).total_seconds() / 3600
    
    fault.repair_end = repair_end
    fault.repair_duration = repair_duration
    fault.repair_notes = repair_data.repair_notes
    fault.repair_category = repair_data.repair_category
    
    # Update device total repair hours
    device = db.query(Device).filter(Device.id == fault.device_id).first()
    if device:
        device.total_repair_hours += repair_duration
        calculate_device_metrics(db, fault.device_id)
    
    db.commit()
    
    create_log(db, fault_id, f"Onarım tamamlandı ({repair_duration:.2f} saat)", current_user.id, current_user.name)
    
    return {"message": "Repair ended", "duration_hours": repair_duration}

@api_router.post("/faults/{fault_id}/confirm")
def confirm_fault(fault_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    fault = db.query(FaultRecord).filter(FaultRecord.id == fault_id).first()
    if not fault:
        raise HTTPException(status_code=404, detail="Fault not found")
    
    if fault.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Only the creator can confirm")
    
    if not fault.repair_end:
        raise HTTPException(status_code=400, detail="Repair not completed yet")
    
    if fault.status == FaultStatus.CLOSED:
        raise HTTPException(status_code=400, detail="Already confirmed")
    
    fault.status = FaultStatus.CLOSED
    fault.confirmed_by = current_user.id
    fault.confirmed_at = datetime.now(timezone.utc)
    
    # Update technician stats
    if fault.assigned_to:
        technician = db.query(User).filter(User.id == fault.assigned_to).first()
        if technician:
            technician.successful_repairs += 1
    
    db.commit()
    
    create_log(db, fault_id, "Onarım onaylandı ve kayıt kapatıldı", current_user.id, current_user.name)
    
    return {"message": "Fault confirmed and closed"}

# Devam ediyor... (Karakter limiti nedeniyle bölündü)
