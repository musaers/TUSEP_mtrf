from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
import traceback

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

security = HTTPBearer()

app = FastAPI()
api_router = APIRouter(prefix="/api")

# ===== MODELS =====

class UserRole:
    HEALTH_STAFF = "health_staff"
    TECHNICIAN = "technician"
    MANAGER = "manager"
    QUALITY = "quality"

class FaultStatus:
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: EmailStr
    role: str
    successful_repairs: int = 0
    failed_repairs: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = UserRole.HEALTH_STAFF

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Device(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str
    type: str
    location: str
    total_failures: int = 0
    total_operating_hours: float = 0.0
    total_repair_hours: float = 0.0
    mtbf: float = 0.0
    mttr: float = 0.0
    availability: float = 100.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DeviceCreate(BaseModel):
    code: str
    type: str
    location: str
    total_operating_hours: float = 8760.0  # Default: 1 year

class RepairCategory:
    PART_REPLACEMENT = "part_replacement"
    ADJUSTMENT = "adjustment"
    COMPLETE_REPAIR = "complete_repair"
    OTHER = "other"

class FaultRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_by: str
    created_by_name: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
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
    repair_category: Optional[str] = None  # YENI: Onarım kategorisi
    breakdown_iteration: int = 0
    status: str = FaultStatus.OPEN
    confirmed_by: Optional[str] = None
    confirmed_at: Optional[datetime] = None

class FaultRecordCreate(BaseModel):
    device_id: str
    description: str

class FaultRecordAssign(BaseModel):
    assigned_to: str

class FaultRecordUpdate(BaseModel):
    repair_notes: Optional[str] = None
    status: Optional[str] = None

class FaultRecordStartRepair(BaseModel):
    pass

class FaultRecordEndRepair(BaseModel):
    repair_notes: str
    repair_category: str  # YENI: Zorunlu onarım kategorisi

class Log(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    record_id: str
    event: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: Optional[str] = None
    user_name: Optional[str] = None

# ===== AUTHENTICATION =====

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user_doc = await db.users.find_one({"id": user_id}, {"_id": 0})
    if user_doc is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Convert ISO strings to datetime
    if isinstance(user_doc.get('created_at'), str):
        user_doc['created_at'] = datetime.fromisoformat(user_doc['created_at'])
    
    return User(**user_doc)

# ===== HELPER FUNCTIONS =====

async def create_log(record_id: str, event: str, user_id: str = None, user_name: str = None):
    log = Log(record_id=record_id, event=event, user_id=user_id, user_name=user_name)
    log_dict = log.model_dump()
    log_dict['timestamp'] = log_dict['timestamp'].isoformat()
    await db.logs.insert_one(log_dict)

async def calculate_device_metrics(device_id: str):
    device = await db.devices.find_one({"id": device_id}, {"_id": 0})
    if not device:
        return
    
    total_failures = device.get('total_failures', 0)
    total_operating_hours = device.get('total_operating_hours', 0.0)
    total_repair_hours = device.get('total_repair_hours', 0.0)
    
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
    
    await db.devices.update_one(
        {"id": device_id},
        {"$set": {"mtbf": mtbf, "mttr": mttr, "availability": availability}}
    )

# ===== AUTH ROUTES =====

@api_router.post("/auth/register", response_model=User)
async def register(user_data: UserCreate):
    # Check if email already exists
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    hashed_password = pwd_context.hash(user_data.password)
    
    # Create user
    user = User(
        name=user_data.name,
        email=user_data.email,
        role=user_data.role
    )
    
    user_dict = user.model_dump()
    user_dict['password'] = hashed_password
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    
    await db.users.insert_one(user_dict)
    return user

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    user_doc = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not pwd_context.verify(credentials.password, user_doc['password']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user_doc['id'], "email": user_doc['email']})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user_doc['id'],
            "name": user_doc['name'],
            "email": user_doc['email'],
            "role": user_doc['role']
        }
    }

@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# ===== USERS ROUTES =====

@api_router.get("/users", response_model=List[User])
async def get_users(current_user: User = Depends(get_current_user)):
    if current_user.role not in [UserRole.MANAGER, UserRole.QUALITY]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(1000)
    for user in users:
        if isinstance(user.get('created_at'), str):
            user['created_at'] = datetime.fromisoformat(user['created_at'])
    return users

@api_router.get("/users/technicians", response_model=List[User])
async def get_technicians(current_user: User = Depends(get_current_user)):
    users = await db.users.find({"role": UserRole.TECHNICIAN}, {"_id": 0, "password": 0}).to_list(1000)
    for user in users:
        if isinstance(user.get('created_at'), str):
            user['created_at'] = datetime.fromisoformat(user['created_at'])
    return users

# ===== DEVICES ROUTES =====

@api_router.post("/devices", response_model=Device)
async def create_device(device_data: DeviceCreate, current_user: User = Depends(get_current_user)):
    if current_user.role not in [UserRole.MANAGER, UserRole.TECHNICIAN]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check if code already exists
    existing = await db.devices.find_one({"code": device_data.code})
    if existing:
        raise HTTPException(status_code=400, detail="Device code already exists")
    
    device = Device(**device_data.model_dump())
    device_dict = device.model_dump()
    device_dict['created_at'] = device_dict['created_at'].isoformat()
    
    await db.devices.insert_one(device_dict)
    return device

@api_router.get("/devices", response_model=List[Device])
async def get_devices(current_user: User = Depends(get_current_user)):
    devices = await db.devices.find({}, {"_id": 0}).to_list(1000)
    for device in devices:
        if isinstance(device.get('created_at'), str):
            device['created_at'] = datetime.fromisoformat(device['created_at'])
    return devices

@api_router.get("/devices/{device_id}", response_model=Device)
async def get_device(device_id: str, current_user: User = Depends(get_current_user)):
    device = await db.devices.find_one({"id": device_id}, {"_id": 0})
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    if isinstance(device.get('created_at'), str):
        device['created_at'] = datetime.fromisoformat(device['created_at'])
    return device

@api_router.get("/devices/{device_id}/faults")
async def get_device_faults(device_id: str, current_user: User = Depends(get_current_user)):
    faults = await db.fault_records.find({"device_id": device_id}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    for fault in faults:
        for field in ['created_at', 'repair_start', 'repair_end', 'confirmed_at']:
            if isinstance(fault.get(field), str):
                fault[field] = datetime.fromisoformat(fault[field])
    return faults

# ===== FAULT RECORDS ROUTES =====

@api_router.post("/faults", response_model=FaultRecord)
async def create_fault(fault_data: FaultRecordCreate, current_user: User = Depends(get_current_user)):
    # Get device
    device = await db.devices.find_one({"id": fault_data.device_id}, {"_id": 0})
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Increment device failure count
    new_failure_count = device.get('total_failures', 0) + 1
    
    fault = FaultRecord(
        created_by=current_user.id,
        created_by_name=current_user.name,
        device_id=fault_data.device_id,
        device_code=device['code'],
        device_type=device['type'],
        description=fault_data.description,
        breakdown_iteration=new_failure_count
    )
    
    fault_dict = fault.model_dump()
    fault_dict['created_at'] = fault_dict['created_at'].isoformat()
    
    await db.fault_records.insert_one(fault_dict)
    
    # Update device
    await db.devices.update_one(
        {"id": fault_data.device_id},
        {"$set": {"total_failures": new_failure_count}}
    )
    
    # Create log
    await create_log(fault.id, f"Arıza kaydı oluşturuldu: {fault_data.description}", current_user.id, current_user.name)
    
    return fault

@api_router.get("/faults", response_model=List[FaultRecord])
async def get_faults(status: Optional[str] = None, current_user: User = Depends(get_current_user)):
    query = {}
    if status:
        query['status'] = status
    
    # Role-based filtering
    if current_user.role == UserRole.TECHNICIAN:
        query['assigned_to'] = current_user.id
    elif current_user.role == UserRole.HEALTH_STAFF:
        # Can see their own created faults
        query['created_by'] = current_user.id
    
    faults = await db.fault_records.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    for fault in faults:
        for field in ['created_at', 'repair_start', 'repair_end', 'confirmed_at']:
            if isinstance(fault.get(field), str):
                fault[field] = datetime.fromisoformat(fault[field])
    return faults

@api_router.get("/faults/all")
async def get_all_faults(current_user: User = Depends(get_current_user)):
    if current_user.role not in [UserRole.MANAGER, UserRole.QUALITY]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    faults = await db.fault_records.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    for fault in faults:
        for field in ['created_at', 'repair_start', 'repair_end', 'confirmed_at']:
            if isinstance(fault.get(field), str):
                fault[field] = datetime.fromisoformat(fault[field])
    return faults

@api_router.get("/faults/{fault_id}", response_model=FaultRecord)
async def get_fault(fault_id: str, current_user: User = Depends(get_current_user)):
    fault = await db.fault_records.find_one({"id": fault_id}, {"_id": 0})
    if not fault:
        raise HTTPException(status_code=404, detail="Fault not found")
    
    for field in ['created_at', 'repair_start', 'repair_end', 'confirmed_at']:
        if isinstance(fault.get(field), str):
            fault[field] = datetime.fromisoformat(fault[field])
    return fault

@api_router.post("/faults/{fault_id}/assign")
async def assign_fault(fault_id: str, assign_data: FaultRecordAssign, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.MANAGER:
        raise HTTPException(status_code=403, detail="Only managers can assign faults")
    
    fault = await db.fault_records.find_one({"id": fault_id}, {"_id": 0})
    if not fault:
        raise HTTPException(status_code=404, detail="Fault not found")
    
    technician = await db.users.find_one({"id": assign_data.assigned_to}, {"_id": 0})
    if not technician or technician['role'] != UserRole.TECHNICIAN:
        raise HTTPException(status_code=400, detail="Invalid technician")
    
    await db.fault_records.update_one(
        {"id": fault_id},
        {"$set": {
            "assigned_to": assign_data.assigned_to,
            "assigned_to_name": technician['name'],
            "status": FaultStatus.IN_PROGRESS
        }}
    )
    
    await create_log(fault_id, f"Teknisyene atandı: {technician['name']}", current_user.id, current_user.name)
    
    return {"message": "Fault assigned successfully"}

@api_router.post("/faults/{fault_id}/start-repair")
async def start_repair(fault_id: str, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.TECHNICIAN:
        raise HTTPException(status_code=403, detail="Only technicians can start repairs")
    
    fault = await db.fault_records.find_one({"id": fault_id}, {"_id": 0})
    if not fault:
        raise HTTPException(status_code=404, detail="Fault not found")
    
    if fault.get('assigned_to') != current_user.id:
        raise HTTPException(status_code=403, detail="Not assigned to you")
    
    if fault.get('repair_start'):
        raise HTTPException(status_code=400, detail="Repair already started")
    
    repair_start = datetime.now(timezone.utc)
    await db.fault_records.update_one(
        {"id": fault_id},
        {"$set": {"repair_start": repair_start.isoformat()}}
    )
    
    await create_log(fault_id, "Onarım başlatıldı", current_user.id, current_user.name)
    
    return {"message": "Repair started"}

@api_router.post("/faults/{fault_id}/end-repair")
async def end_repair(fault_id: str, repair_data: FaultRecordEndRepair, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.TECHNICIAN:
        raise HTTPException(status_code=403, detail="Only technicians can end repairs")
    
    fault = await db.fault_records.find_one({"id": fault_id}, {"_id": 0})
    if not fault:
        raise HTTPException(status_code=404, detail="Fault not found")
    
    if fault.get('assigned_to') != current_user.id:
        raise HTTPException(status_code=403, detail="Not assigned to you")
    
    if not fault.get('repair_start'):
        raise HTTPException(status_code=400, detail="Repair not started yet")
    
    if fault.get('repair_end'):
        raise HTTPException(status_code=400, detail="Repair already ended")
    
    repair_end = datetime.now(timezone.utc)
    repair_start = datetime.fromisoformat(fault['repair_start']) if isinstance(fault['repair_start'], str) else fault['repair_start']
    repair_duration = (repair_end - repair_start).total_seconds() / 3600  # hours
    
    await db.fault_records.update_one(
        {"id": fault_id},
        {"$set": {
            "repair_end": repair_end.isoformat(),
            "repair_duration": repair_duration,
            "repair_notes": repair_data.repair_notes
        }}
    )
    
    # Update device total repair hours
    device = await db.devices.find_one({"id": fault['device_id']}, {"_id": 0})
    if device:
        new_repair_hours = device.get('total_repair_hours', 0.0) + repair_duration
        await db.devices.update_one(
            {"id": fault['device_id']},
            {"$set": {"total_repair_hours": new_repair_hours}}
        )
        await calculate_device_metrics(fault['device_id'])
    
    await create_log(fault_id, f"Onarım tamamlandı ({repair_duration:.2f} saat)", current_user.id, current_user.name)
    
    return {"message": "Repair ended", "duration_hours": repair_duration}

@api_router.post("/faults/{fault_id}/confirm")
async def confirm_fault(fault_id: str, current_user: User = Depends(get_current_user)):
    fault = await db.fault_records.find_one({"id": fault_id}, {"_id": 0})
    if not fault:
        raise HTTPException(status_code=404, detail="Fault not found")
    
    # Health staff who created it can confirm
    if fault.get('created_by') != current_user.id:
        raise HTTPException(status_code=403, detail="Only the creator can confirm")
    
    if not fault.get('repair_end'):
        raise HTTPException(status_code=400, detail="Repair not completed yet")
    
    if fault.get('status') == FaultStatus.CLOSED:
        raise HTTPException(status_code=400, detail="Already confirmed")
    
    confirmed_at = datetime.now(timezone.utc)
    await db.fault_records.update_one(
        {"id": fault_id},
        {"$set": {
            "status": FaultStatus.CLOSED,
            "confirmed_by": current_user.id,
            "confirmed_at": confirmed_at.isoformat()
        }}
    )
    
    # Update technician stats
    if fault.get('assigned_to'):
        await db.users.update_one(
            {"id": fault['assigned_to']},
            {"$inc": {"successful_repairs": 1}}
        )
    
    await create_log(fault_id, "Onarım onaylandı ve kayıt kapatıldı", current_user.id, current_user.name)
    
    return {"message": "Fault confirmed and closed"}

# ===== REPORTS & DASHBOARD =====

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
    total_devices = await db.devices.count_documents({})
    total_faults = await db.fault_records.count_documents({})
    open_faults = await db.fault_records.count_documents({"status": FaultStatus.OPEN})
    in_progress_faults = await db.fault_records.count_documents({"status": FaultStatus.IN_PROGRESS})
    closed_faults = await db.fault_records.count_documents({"status": FaultStatus.CLOSED})
    
    # Average MTBF, MTTR, Availability
    devices = await db.devices.find({}, {"_id": 0}).to_list(1000)
    avg_mtbf = sum(d.get('mtbf', 0) for d in devices) / len(devices) if devices else 0
    avg_mttr = sum(d.get('mttr', 0) for d in devices) / len(devices) if devices else 0
    avg_availability = sum(d.get('availability', 100) for d in devices) / len(devices) if devices else 100
    
    # Top 5 most reliable and least reliable devices
    devices_by_availability = sorted(devices, key=lambda x: x.get('availability', 100), reverse=True)
    most_reliable = devices_by_availability[:5]
    least_reliable = devices_by_availability[-5:] if len(devices_by_availability) > 5 else []
    
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
async def breakdown_frequency_report(current_user: User = Depends(get_current_user)):
    if current_user.role not in [UserRole.MANAGER, UserRole.QUALITY]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    devices = await db.devices.find({}, {"_id": 0}).to_list(1000)
    
    report_data = []
    for device in devices:
        if device.get('total_operating_hours', 0) > 0 and device.get('total_failures', 0) > 0:
            frequency = (device['total_operating_hours'] / device['total_failures'])
        else:
            frequency = 0
        
        report_data.append({
            "device_code": device['code'],
            "device_type": device['type'],
            "location": device['location'],
            "total_failures": device.get('total_failures', 0),
            "operating_hours": device.get('total_operating_hours', 0),
            "breakdown_frequency": round(frequency, 2)
        })
    
    return report_data

@api_router.get("/reports/intervention-duration")
async def intervention_duration_report(current_user: User = Depends(get_current_user)):
    if current_user.role not in [UserRole.MANAGER, UserRole.QUALITY]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    faults = await db.fault_records.find({"status": FaultStatus.CLOSED}, {"_id": 0}).to_list(1000)
    
    device_interventions = {}
    for fault in faults:
        device_id = fault['device_id']
        if device_id not in device_interventions:
            device_interventions[device_id] = {
                "device_code": fault['device_code'],
                "device_type": fault['device_type'],
                "total_interventions": 0,
                "total_duration": 0.0
            }
        
        device_interventions[device_id]['total_interventions'] += 1
        device_interventions[device_id]['total_duration'] += fault.get('repair_duration', 0.0)
    
    report_data = []
    for device_id, data in device_interventions.items():
        avg_duration = data['total_duration'] / data['total_interventions'] if data['total_interventions'] > 0 else 0
        report_data.append({
            "device_code": data['device_code'],
            "device_type": data['device_type'],
            "total_interventions": data['total_interventions'],
            "average_duration_hours": round(avg_duration, 2)
        })
    
    return report_data

@api_router.get("/reports/technician-performance")
async def technician_performance_report(current_user: User = Depends(get_current_user)):
    if current_user.role not in [UserRole.MANAGER, UserRole.QUALITY]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    technicians = await db.users.find({"role": UserRole.TECHNICIAN}, {"_id": 0, "password": 0}).to_list(1000)
    
    report_data = []
    for tech in technicians:
        total_assigned = await db.fault_records.count_documents({"assigned_to": tech['id']})
        completed = await db.fault_records.count_documents({"assigned_to": tech['id'], "status": FaultStatus.CLOSED})
        success_rate = (completed / total_assigned * 100) if total_assigned > 0 else 0
        
        report_data.append({
            "name": tech['name'],
            "email": tech['email'],
            "total_assigned": total_assigned,
            "completed": completed,
            "successful_repairs": tech.get('successful_repairs', 0),
            "failed_repairs": tech.get('failed_repairs', 0),
            "success_rate": round(success_rate, 2)
        })
    
    return report_data

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

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()