#!/usr/bin/env python3
"""
Initialize PostgreSQL database with tables and test data
"""

import sys
import os
sys.path.append('/app/backend')

from database import Base, engine, SessionLocal, User, Device
from passlib.context import CryptContext
import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def init_database():
    """Initialize database with tables and test data"""
    print("Creating database tables...")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")
    
    # Create test users
    db = SessionLocal()
    try:
        # Check if users already exist
        existing_users = db.query(User).count()
        if existing_users > 0:
            print(f"✅ Database already has {existing_users} users")
            return
        
        print("Creating test users...")
        
        # Create test users
        users = [
            {
                "name": "Hospital Manager",
                "email": "manager@hospital.com",
                "password": "password123",
                "role": "manager"
            },
            {
                "name": "Medical Technician",
                "email": "tech@hospital.com", 
                "password": "password123",
                "role": "technician"
            },
            {
                "name": "Health Staff",
                "email": "staff@hospital.com",
                "password": "password123", 
                "role": "health_staff"
            }
        ]
        
        for user_data in users:
            hashed_password = pwd_context.hash(user_data["password"])
            user = User(
                id=str(uuid.uuid4()),
                name=user_data["name"],
                email=user_data["email"],
                password=hashed_password,
                role=user_data["role"]
            )
            db.add(user)
        
        # Create test devices
        print("Creating test devices...")
        devices = [
            {
                "type": "MRI Scanner",
                "location": "Radiology Department",
                "total_operating_hours": 8760.0
            },
            {
                "type": "CT Scanner", 
                "location": "Imaging Center",
                "total_operating_hours": 7200.0
            },
            {
                "type": "X-Ray Machine",
                "location": "Emergency Department", 
                "total_operating_hours": 6000.0
            },
            {
                "type": "Ultrasound Machine",
                "location": "Cardiology Department",
                "total_operating_hours": 5500.0
            },
            {
                "type": "Ventilator",
                "location": "ICU",
                "total_operating_hours": 8000.0
            }
        ]
        
        for device_data in devices:
            device = Device(
                id=str(uuid.uuid4()),
                type=device_data["type"],
                location=device_data["location"],
                total_operating_hours=device_data["total_operating_hours"]
            )
            db.add(device)
        
        db.commit()
        print("✅ Test users and devices created successfully")
        
    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_database()