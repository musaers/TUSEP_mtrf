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
from excel_service_postgres import ExcelReportService

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
# Bu dosya server_postgres.py'nin devamıdır - birleştirilecek

# ===== REPORTS & DASHBOARD =====

@api_router.get("/dashboard/stats")
def get_dashboard_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    total_devices = db.query(Device).count()
    total_faults = db.query(FaultRecord).count()
    open_faults = db.query(FaultRecord).filter(FaultRecord.status == FaultStatus.OPEN).count()
    in_progress_faults = db.query(FaultRecord).filter(FaultRecord.status == FaultStatus.IN_PROGRESS).count()
    closed_faults = db.query(FaultRecord).filter(FaultRecord.status == FaultStatus.CLOSED).count()
    
    # Average MTBF, MTTR, Availability
    devices = db.query(Device).all()
    avg_mtbf = sum(d.mtbf for d in devices) / len(devices) if devices else 0
    avg_mttr = sum(d.mttr for d in devices) / len(devices) if devices else 0
    avg_availability = sum(d.availability for d in devices) / len(devices) if devices else 100
    
    # Top 5 most reliable and least reliable devices
    devices_by_availability = sorted(devices, key=lambda x: x.availability, reverse=True)
    most_reliable = [
        {
            "id": d.id,
            "code": d.code,
            "type": d.type,
            "location": d.location,
            "availability": d.availability,
            "mtbf": d.mtbf
        } for d in devices_by_availability[:5]
    ]
    least_reliable = [
        {
            "id": d.id,
            "code": d.code,
            "type": d.type,
            "location": d.location,
            "availability": d.availability,
            "mtbf": d.mtbf
        } for d in devices_by_availability[-5:] if len(devices_by_availability) > 5
    ]
    
    return {
        "total_devices": total_devices,
        "total_faults": total_faults,
        "open_faults": open_faults,
        "in_progress_faults": in_progress_faults,
        "closed_faults": closed_faults,
        "avg_mtbf": round(avg_mtbf, 2),
        "avg_mttr": round(avg_mttr, 2),
        "avg_availability": round(avg_availability, 2),
        "most_reliable_devices": most_reliable,
        "least_reliable_devices": least_reliable
    }

@api_router.get("/reports/breakdown-frequency")
def breakdown_frequency_report(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role not in [UserRole.MANAGER, UserRole.QUALITY]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    devices = db.query(Device).all()
    
    report_data = []
    for device in devices:
        if device.total_operating_hours > 0 and device.total_failures > 0:
            frequency = device.total_operating_hours / device.total_failures
        else:
            frequency = 0
        
        report_data.append({
            "device_code": device.code,
            "device_type": device.type,
            "location": device.location,
            "total_failures": device.total_failures,
            "operating_hours": device.total_operating_hours,
            "breakdown_frequency": round(frequency, 2)
        })
    
    return report_data

@api_router.get("/reports/intervention-duration")
def intervention_duration_report(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role not in [UserRole.MANAGER, UserRole.QUALITY]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    faults = db.query(FaultRecord).filter(FaultRecord.status == FaultStatus.CLOSED).all()
    
    device_interventions = {}
    for fault in faults:
        device_id = fault.device_id
        if device_id not in device_interventions:
            device_interventions[device_id] = {
                "device_code": fault.device_code,
                "device_type": fault.device_type,
                "total_interventions": 0,
                "total_duration": 0.0
            }
        
        device_interventions[device_id]["total_interventions"] += 1
        device_interventions[device_id]["total_duration"] += fault.repair_duration
    
    report_data = []
    for device_id, data in device_interventions.items():
        avg_duration = data["total_duration"] / data["total_interventions"] if data["total_interventions"] > 0 else 0
        report_data.append({
            "device_code": data["device_code"],
            "device_type": data["device_type"],
            "total_interventions": data["total_interventions"],
            "average_duration_hours": round(avg_duration, 2)
        })
    
    return report_data

@api_router.get("/reports/technician-performance")
def technician_performance_report(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role not in [UserRole.MANAGER, UserRole.QUALITY]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    technicians = db.query(User).filter(User.role == UserRole.TECHNICIAN).all()
    
    report_data = []
    for tech in technicians:
        total_assigned = db.query(FaultRecord).filter(FaultRecord.assigned_to == tech.id).count()
        completed = db.query(FaultRecord).filter(
            FaultRecord.assigned_to == tech.id,
            FaultRecord.status == FaultStatus.CLOSED
        ).count()
        success_rate = (completed / total_assigned * 100) if total_assigned > 0 else 0
        
        report_data.append({
            "name": tech.name,
            "email": tech.email,
            "total_assigned": total_assigned,
            "completed": completed,
            "successful_repairs": tech.successful_repairs,
            "failed_repairs": tech.failed_repairs,
            "success_rate": round(success_rate, 2)
        })
    
    return report_data

# ===== TRANSFER MANAGEMENT ROUTES =====

@api_router.post("/transfers", response_model=TransferResponse)
def create_transfer(transfer_data: TransferCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == transfer_data.device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    transfer = EquipmentTransfer(
        id=str(uuid.uuid4()),
        device_id=transfer_data.device_id,
        device_code=device.code,
        device_type=device.type,
        from_location=device.location,
        to_location=transfer_data.to_location,
        requested_by=current_user.id,
        requested_by_name=current_user.name,
        reason=transfer_data.reason
    )
    
    db.add(transfer)
    db.commit()
    db.refresh(transfer)
    
    return transfer

@api_router.get("/transfers", response_model=List[TransferResponse])
def get_transfers(status: Optional[str] = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(EquipmentTransfer)
    
    if status:
        query = query.filter(EquipmentTransfer.status == status)
    
    transfers = query.order_by(EquipmentTransfer.requested_at.desc()).all()
    return transfers

@api_router.post("/transfers/{transfer_id}/approve")
def approve_transfer(transfer_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != UserRole.QUALITY:
        raise HTTPException(status_code=403, detail="Only quality department can approve transfers")
    
    transfer = db.query(EquipmentTransfer).filter(EquipmentTransfer.id == transfer_id).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")
    
    if transfer.status != TransferStatus.PENDING:
        raise HTTPException(status_code=400, detail="Transfer is not pending")
    
    approved_at = datetime.now(timezone.utc)
    
    transfer.status = TransferStatus.APPROVED
    transfer.approved_by = current_user.id
    transfer.approved_by_name = current_user.name
    transfer.approved_at = approved_at
    
    # Update device location
    device = db.query(Device).filter(Device.id == transfer.device_id).first()
    if device:
        device.location = transfer.to_location
    
    # Mark as completed
    transfer.status = TransferStatus.COMPLETED
    transfer.completed_at = approved_at
    
    db.commit()
    
    return {"message": "Transfer approved and completed"}

@api_router.post("/transfers/{transfer_id}/reject")
def reject_transfer(transfer_id: str, reject_data: TransferReject, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != UserRole.QUALITY:
        raise HTTPException(status_code=403, detail="Only quality department can reject transfers")
    
    transfer = db.query(EquipmentTransfer).filter(EquipmentTransfer.id == transfer_id).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")
    
    if transfer.status != TransferStatus.PENDING:
        raise HTTPException(status_code=400, detail="Transfer is not pending")
    
    transfer.status = TransferStatus.REJECTED
    transfer.approved_by = current_user.id
    transfer.approved_by_name = current_user.name
    transfer.approved_at = datetime.now(timezone.utc)
    transfer.rejection_reason = reject_data.rejection_reason
    
    db.commit()
    
    return {"message": "Transfer rejected"}

# ===== EXCEL REPORT ROUTES =====

@api_router.get("/reports/excel/device-failure-frequency")
async def download_device_failure_frequency(year: Optional[int] = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != UserRole.QUALITY:
        raise HTTPException(status_code=403, detail="Only quality department can download reports")
    
    if not year:
        year = datetime.now(timezone.utc).year
    
    excel_file = await ExcelReportService.generate_device_failure_frequency_report_postgres(db, year)
    
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=Cihaz_Arizalanma_Sikligi_{year}.xlsx"}
    )

@api_router.get("/reports/excel/intervention-duration")
async def download_intervention_duration(year: Optional[int] = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != UserRole.QUALITY:
        raise HTTPException(status_code=403, detail="Only quality department can download reports")
    
    if not year:
        year = datetime.now(timezone.utc).year
    
    excel_file = await ExcelReportService.generate_intervention_duration_report_postgres(db, year)
    
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=Mudahale_Suresi_{year}.xlsx"}
    )

@api_router.get("/reports/excel/facility-issues")
async def download_facility_issues(year: Optional[int] = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != UserRole.QUALITY:
        raise HTTPException(status_code=403, detail="Only quality department can download reports")
    
    if not year:
        year = datetime.now(timezone.utc).year
    
    excel_file = await ExcelReportService.generate_facility_issues_report_postgres(db, year)
    
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=Tesis_Sorunlari_{year}.xlsx"}
    )

# ===== QUALITY DASHBOARD LOGS =====

@api_router.get("/quality/all-logs")
def get_all_system_logs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != UserRole.QUALITY:
        raise HTTPException(status_code=403, detail="Only quality department can view all logs")
    
    logs = db.query(Log).order_by(Log.timestamp.desc()).limit(500).all()
    return [
        {
            "id": log.id,
            "record_id": log.record_id,
            "event": log.event,
            "timestamp": log.timestamp,
            "user_id": log.user_id,
            "user_name": log.user_name
        } for log in logs
    ]

@api_router.get("/quality/system-stats")
def get_quality_system_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != UserRole.QUALITY:
        raise HTTPException(status_code=403, detail="Only quality department can view system stats")
    
    total_users = db.query(User).count()
    total_devices = db.query(Device).count()
    total_faults = db.query(FaultRecord).count()
    total_transfers = db.query(EquipmentTransfer).count()
    pending_transfers = db.query(EquipmentTransfer).filter(EquipmentTransfer.status == TransferStatus.PENDING).count()
    
    return {
        "total_users": total_users,
        "total_devices": total_devices,
        "total_faults": total_faults,
        "total_transfers": total_transfers,
        "pending_transfers": pending_transfers
    }

# ===== FASTAPI APP SETUP =====

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
def startup():
    logger.info("TÜSEP Backend Started - PostgreSQL Mode")

@app.on_event("shutdown")
def shutdown():
    logger.info("TÜSEP Backend Shutdown")
