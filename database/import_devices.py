import psycopg2
import uuid
from datetime import datetime

# PostgreSQL bağlantısı
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="postgres",
    user="admin",
    password="1234"
)
cursor = conn.cursor()

print("🔌 PostgreSQL'e bağlanıldı")

# Excel'den örnek cihazlar (1000 tanesini sen ekleyeceksin)
sample_devices = [
    {
        "d_no": "8972",
        "kat": "-2. KAT",
        "oda": "AMELİYATHANE",
        "demirbas_adi": "Ameliyat Lambası",
        "marka": "BIÇAKCILAR",
        "model": "",
        "seri": "1019",
        "adet": 1
    },
    {
        "d_no": "10630",
        "kat": "-2. KAT",
        "oda": "AMELİYATHANE",
        "demirbas_adi": "Ameliyat Lambası",
        "marka": "BIÇAKCILAR",
        "model": "",
        "seri": "988",
        "adet": 1
    },
    # ... daha fazlası eklenecek
]

# Cihazları ekle
for device_data in sample_devices:
    device_id = str(uuid.uuid4())
    
    # Code: D.No değeri
    code = f"CIH-{device_data['d_no']}"
    
    # Type: Demirbaş adı
    device_type = device_data['demirbas_adi']
    
    # Location: Kat + Oda
    location = f"{device_data['kat']} - {device_data['oda']}"
    
    cursor.execute("""
        INSERT INTO devices (
            id, code, type, location, 
            kat, demirbas_adi, marka, model, seri_no, adet,
            total_operating_hours
        ) VALUES (
            %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s,
            8760.0
        )
    """, (
        device_id, code, device_type, location,
        device_data['kat'], device_data['demirbas_adi'], 
        device_data['marka'], device_data.get('model', ''), 
        device_data['seri'], device_data['adet']
    ))
    
    print(f"✓ Eklendi: {code} - {device_type}")

conn.commit()
cursor.close()
conn.close()

print("\n✅ Cihazlar başarıyla eklendi!")
print("\n💡 1000 cihazı eklemek için:")
print("1. Excel'i CSV olarak kaydet")
print("2. Bu script'i güncelleyip tüm satırları oku")
