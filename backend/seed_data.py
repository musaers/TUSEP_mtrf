import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime, timezone, timedelta
import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

async def seed_database():
    print("🌱 Demo verileri oluşturuluyor...")
    
    # Clear existing data
    await db.users.delete_many({})
    await db.devices.delete_many({})
    await db.fault_records.delete_many({})
    await db.logs.delete_many({})
    print("✓ Eski veriler temizlendi")
    
    # Create demo users
    demo_users = [
        {
            "id": "user-1",
            "name": "Dr. Ayşe Yılmaz",
            "email": "ayse@hastane.com",
            "password": pwd_context.hash("12345"),
            "role": "health_staff",
            "successful_repairs": 0,
            "failed_repairs": 0,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "user-2",
            "name": "Mehmet Kaya",
            "email": "mehmet@hastane.com",
            "password": pwd_context.hash("12345"),
            "role": "technician",
            "successful_repairs": 15,
            "failed_repairs": 2,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "user-3",
            "name": "Ali Demir",
            "email": "ali@hastane.com",
            "password": pwd_context.hash("12345"),
            "role": "technician",
            "successful_repairs": 12,
            "failed_repairs": 1,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "user-4",
            "name": "Fatma Şahin",
            "email": "fatma@hastane.com",
            "password": pwd_context.hash("12345"),
            "role": "manager",
            "successful_repairs": 0,
            "failed_repairs": 0,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "user-5",
            "name": "Zeynep Arslan",
            "email": "zeynep@hastane.com",
            "password": pwd_context.hash("12345"),
            "role": "quality",
            "successful_repairs": 0,
            "failed_repairs": 0,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    await db.users.insert_many(demo_users)
    print("✓ 5 demo kullanıcı oluşturuldu")
    
    # Create demo devices
    demo_devices = [
        {
            "id": "device-1",
            "code": "MR-001",
            "type": "MR Cihazı",
            "location": "Radyoloji Bölümü",
            "total_failures": 3,
            "total_operating_hours": 8760.0,
            "total_repair_hours": 12.5,
            "mtbf": 2915.83,
            "mttr": 4.17,
            "availability": 99.86,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "device-2",
            "code": "BT-001",
            "type": "BT Cihazı",
            "location": "Radyoloji Bölümü",
            "total_failures": 2,
            "total_operating_hours": 8760.0,
            "total_repair_hours": 8.0,
            "mtbf": 4376.0,
            "mttr": 4.0,
            "availability": 99.91,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "device-3",
            "code": "USG-001",
            "type": "Ultrason Cihazı",
            "location": "Kadın Hastalıkları",
            "total_failures": 1,
            "total_operating_hours": 8760.0,
            "total_repair_hours": 2.5,
            "mtbf": 8757.5,
            "mttr": 2.5,
            "availability": 99.97,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "device-4",
            "code": "ANJ-001",
            "type": "Anjiyografi Cihazı",
            "location": "Kardiyoloji",
            "total_failures": 5,
            "total_operating_hours": 8760.0,
            "total_repair_hours": 35.0,
            "mtbf": 1745.0,
            "mttr": 7.0,
            "availability": 99.60,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "device-5",
            "code": "VNT-001",
            "type": "Ventilatör",
            "location": "Yoğun Bakım",
            "total_failures": 0,
            "total_operating_hours": 8760.0,
            "total_repair_hours": 0.0,
            "mtbf": 0.0,
            "mttr": 0.0,
            "availability": 100.0,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    await db.devices.insert_many(demo_devices)
    print("✓ 5 demo cihaz oluşturuldu")
    
    # Create demo fault records
    demo_faults = [
        {
            "id": "fault-1",
            "created_by": "user-1",
            "created_by_name": "Dr. Ayşe Yılmaz",
            "created_at": (datetime.now(timezone.utc) - timedelta(days=10)).isoformat(),
            "device_id": "device-1",
            "device_code": "MR-001",
            "device_type": "MR Cihazı",
            "description": "Görüntü kalitesinde bozulma var",
            "assigned_to": "user-2",
            "assigned_to_name": "Mehmet Kaya",
            "repair_start": (datetime.now(timezone.utc) - timedelta(days=10, hours=-1)).isoformat(),
            "repair_end": (datetime.now(timezone.utc) - timedelta(days=10, hours=-5)).isoformat(),
            "repair_duration": 4.0,
            "repair_notes": "RF bobini değiştirildi, kalibrasyon yapıldı",
            "breakdown_iteration": 1,
            "status": "closed",
            "confirmed_by": "user-1",
            "confirmed_at": (datetime.now(timezone.utc) - timedelta(days=10, hours=-6)).isoformat()
        },
        {
            "id": "fault-2",
            "created_by": "user-1",
            "created_by_name": "Dr. Ayşe Yılmaz",
            "created_at": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
            "device_id": "device-2",
            "device_code": "BT-001",
            "device_type": "BT Cihazı",
            "description": "X-ray tüpü ısınma hatası veriyor",
            "assigned_to": "user-3",
            "assigned_to_name": "Ali Demir",
            "repair_start": (datetime.now(timezone.utc) - timedelta(days=5, hours=-2)).isoformat(),
            "repair_end": (datetime.now(timezone.utc) - timedelta(days=5, hours=-6)).isoformat(),
            "repair_duration": 4.0,
            "repair_notes": "Soğutma sistemi temizlendi, fan değiştirildi",
            "breakdown_iteration": 1,
            "status": "closed",
            "confirmed_by": "user-1",
            "confirmed_at": (datetime.now(timezone.utc) - timedelta(days=5, hours=-7)).isoformat()
        },
        {
            "id": "fault-3",
            "created_by": "user-1",
            "created_by_name": "Dr. Ayşe Yılmaz",
            "created_at": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
            "device_id": "device-4",
            "device_code": "ANJ-001",
            "device_type": "Anjiyografi Cihazı",
            "description": "Görüntü kayıt sistemi çalışmıyor",
            "assigned_to": "user-2",
            "assigned_to_name": "Mehmet Kaya",
            "repair_start": (datetime.now(timezone.utc) - timedelta(days=2, hours=-3)).isoformat(),
            "repair_end": (datetime.now(timezone.utc) - timedelta(days=2, hours=-10)).isoformat(),
            "repair_duration": 7.0,
            "repair_notes": "Hard disk değiştirildi, yazılım güncellendi",
            "breakdown_iteration": 1,
            "status": "closed",
            "confirmed_by": "user-1",
            "confirmed_at": (datetime.now(timezone.utc) - timedelta(days=2, hours=-11)).isoformat()
        },
        {
            "id": "fault-4",
            "created_by": "user-1",
            "created_by_name": "Dr. Ayşe Yılmaz",
            "created_at": (datetime.now(timezone.utc) - timedelta(hours=5)).isoformat(),
            "device_id": "device-1",
            "device_code": "MR-001",
            "device_type": "MR Cihazı",
            "description": "Masa hareket sistemi çalışmıyor",
            "assigned_to": "user-2",
            "assigned_to_name": "Mehmet Kaya",
            "repair_start": (datetime.now(timezone.utc) - timedelta(hours=4)).isoformat(),
            "repair_end": None,
            "repair_duration": 0.0,
            "repair_notes": "",
            "breakdown_iteration": 2,
            "status": "in_progress",
            "confirmed_by": None,
            "confirmed_at": None
        },
        {
            "id": "fault-5",
            "created_by": "user-1",
            "created_by_name": "Dr. Ayşe Yılmaz",
            "created_at": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
            "device_id": "device-3",
            "device_code": "USG-001",
            "device_type": "Ultrason Cihazı",
            "description": "Prob bağlantı hatası",
            "assigned_to": None,
            "assigned_to_name": None,
            "repair_start": None,
            "repair_end": None,
            "repair_duration": 0.0,
            "repair_notes": "",
            "breakdown_iteration": 1,
            "status": "open",
            "confirmed_by": None,
            "confirmed_at": None
        }
    ]
    
    await db.fault_records.insert_many(demo_faults)
    print("✓ 5 demo arıza kaydı oluşturuldu")
    
    print("\n✅ Demo verileri başarıyla oluşturuldu!\n")
    print("=" * 60)
    print("DEMO KULLANICI BİLGİLERİ (Tüm şifreler: 12345)")
    print("=" * 60)
    print("\n1. Sağlık Personeli:")
    print("   Email: ayse@hastane.com")
    print("   Şifre: 12345")
    print("\n2. Teknisyen 1:")
    print("   Email: mehmet@hastane.com")
    print("   Şifre: 12345")
    print("\n3. Teknisyen 2:")
    print("   Email: ali@hastane.com")
    print("   Şifre: 12345")
    print("\n4. Yönetici:")
    print("   Email: fatma@hastane.com")
    print("   Şifre: 12345")
    print("\n5. Kalite Birimi:")
    print("   Email: zeynep@hastane.com")
    print("   Şifre: 12345")
    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(seed_database())
