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
