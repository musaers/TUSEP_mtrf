#!/usr/bin/env python3
"""
1000 Cihazı CSV'den PostgreSQL'e İçe Aktarma Script'i
Excel'i önce CSV olarak kaydedin
"""

import psycopg2
import uuid
import csv
import sys

# PostgreSQL bağlantısı
try:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="postgres",
        user="admin",
        password="1234"
    )
    cursor = conn.cursor()
    print("✓ PostgreSQL'e bağlanıldı")
except Exception as e:
    print(f"❌ Bağlantı hatası: {e}")
    sys.exit(1)

# CSV dosyasını oku
csv_file = input("CSV dosya yolu (örn: cihazlar.csv): ")

try:
    with open(csv_file, 'r', encoding='utf-8-sig') as file:
        csv_reader = csv.DictReader(file)
        
        count = 0
        for row in csv_reader:
            device_id = str(uuid.uuid4())
            
            # CSV sütun isimleri - Excel'inizdeki başlıklara göre düzenleyin
            d_no = row.get('D.No', row.get('d_no', ''))
            kat = row.get('Kat', row.get('kat', ''))
            oda = row.get('Oda', row.get('oda', ''))
            demirbas_adi = row.get('Demirbaş Adı', row.get('demirbas_adi', ''))
            marka = row.get('Marka', row.get('marka', ''))
            model = row.get('Model', row.get('model', ''))
            seri = row.get('Seri', row.get('seri', ''))
            adet = int(row.get('Adet', row.get('adet', 1)))
            
            # Code: D.No değeri
            code = f"CIH-{d_no}"
            
            # Type: Demirbaş adı
            device_type = demirbas_adi
            
            # Location: Kat + Oda
            location = f"{kat} - {oda}"
            
            try:
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
                    kat, demirbas_adi, marka, model, seri, adet
                ))
                
                count += 1
                if count % 100 == 0:
                    print(f"✓ {count} cihaz eklendi...")
                    
            except Exception as e:
                print(f"⚠️  {code} eklenirken hata: {e}")
                continue
        
        conn.commit()
        print(f"\n✅ Toplam {count} cihaz başarıyla eklendi!")
        
except FileNotFoundError:
    print(f"❌ Dosya bulunamadı: {csv_file}")
except Exception as e:
    print(f"❌ Hata: {e}")
finally:
    cursor.close()
    conn.close()

print("\n📊 Kontrol et:")
print("docker exec -it tusep-postgres psql -U admin -d postgres -c 'SELECT COUNT(*) FROM devices;'")
