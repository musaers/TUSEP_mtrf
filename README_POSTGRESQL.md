# 🏥 TÜSEP - PostgreSQL Version

## 🎯 ÖNEMLİ: PostgreSQL'e Tam Geçiş Yapıldı

Bu versiyon **tamamen PostgreSQL** ile çalışır. MongoDB kullanılmaz.

### ✅ Tüm Özellikler Korundu:

1. ✅ Transfer Yönetimi
2. ✅ Kalite Birimi Dashboard
3. ✅ Zaman Formatı (dk:sn)
4. ✅ Zorunlu Onarım Kategorileri
5. ✅ Excel Rapor Oluşturma (TÜSEP)
6. ✅ Gerçek Zamanlı Timer

---

## 📋 Gereksinimler

- Docker Desktop
- PostgreSQL Client (opsiyonel - DataGrip/psql)

---

## 🚀 Hızlı Başlangıç

### 1. PostgreSQL ile Başlat

```bash
chmod +x start-postgres.sh
./start-postgres.sh
```

### 2. Veritabanı Hazırlığı

Tablolar zaten oluşturulmuş olmalı. Eğer yoksa:

```sql
-- database/schema.sql dosyasını çalıştırın
```

### 3. Tarayıcıda Açın

**Frontend:** http://localhost:3000  
**Backend API:** http://localhost:8001/docs

---

## 🔐 Giriş Bilgileri

Tüm şifreler: **12345**

| Rol | Email |
|-----|-------|
| Kalite Birimi | zeynep@hastane.com |
| Yönetici | fatma@hastane.com |
| Teknisyen | mehmet@hastane.com |
| Teknisyen | ali@hastane.com |
| Sağlık Personeli | ayse@hastane.com |

---

## 📊 Veritabanı Bağlantısı

**DataGrip/psql:**

```
Host: localhost
Port: 5432
Database: postgres
User: admin
Password: 1234
```

**Connection String:**

```
postgresql://admin:1234@localhost:5432/postgres
```

---

## 📦 1000 Cihaz İçe Aktarma

### Yöntem 1: CSV İle

```bash
# Excel'i CSV olarak kaydet (örn: devices.csv)
# Python script'i çalıştır

cd backend
python import_devices_csv.py
```

### Yöntem 2: SQL İle

```sql
INSERT INTO devices (id, code, type, location, kat, demirbas_adi, marka, model, seri_no, adet, total_operating_hours)
VALUES 
  ('uuid-1', 'CIH-8972', 'Ameliyat Lambası', '-2. KAT - AMELİYATHANE', '-2. KAT', 'Ameliyat Lambası', 'BIÇAKCILAR', '', '1019', 1, 8760.0),
  ('uuid-2', 'CIH-10630', 'Ameliyat Lambası', '-2. KAT - AMELİYATHANE', '-2. KAT', 'Ameliyat Lambası', 'BIÇAKCILAR', '', '988', 1, 8760.0);
  -- ... 1000 satır
```

### Yöntem 3: Python Script (Önerilen)

`database/import_devices.py` dosyasını düzenle ve çalıştır:

```python
# Excel'den tüm satırları oku
import pandas as pd

df = pd.read_excel('cihazlar.xlsx')

for _, row in df.iterrows():
    device_id = str(uuid.uuid4())
    code = f"CIH-{row['D.No']}"
    # ... vs
```

---

## 🛠️ Yararlı Komutlar

### Docker

```bash
# Başlat
docker-compose -f docker-compose-postgres.yml up -d

# Durdur
docker-compose -f docker-compose-postgres.yml down

# Loglar
docker-compose -f docker-compose-postgres.yml logs -f

# Yeniden build
docker-compose -f docker-compose-postgres.yml up -d --build
```

### PostgreSQL

```bash
# Docker container'a bağlan
docker exec -it tusep-postgres psql -U admin -d postgres

# Tablolar
\dt

# Cihaz sayısı
SELECT COUNT(*) FROM devices;

# Kullanıcılar
SELECT name, email, role FROM users;
```

### Backend

```bash
# Backend container'a gir
docker exec -it tusep-backend bash

# Python shell
python

# Test query
from database import SessionLocal, Device
db = SessionLocal()
devices = db.query(Device).all()
print(len(devices))
```

---

## 📁 Proje Yapısı

```
TUSEP_mtrf-main/
├── backend/
│   ├── server_postgres.py          # Ana backend (PostgreSQL)
│   ├── database.py                 # SQLAlchemy models
│   ├── excel_service_postgres.py  # Excel raporları
│   ├── requirements.txt            # Python dependencies
│   └── .env.postgres              # PostgreSQL config
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Transfers.jsx       # Transfer yönetimi
│   │   │   ├── QualityDashboard.jsx # Kalite dashboard
│   │   │   └── ...
│   │   ├── components/
│   │   │   └── RealTimeTimer.jsx   # Gerçek zamanlı timer
│   │   └── utils/
│   │       └── timeFormat.js       # Zaman formatı
│   └── package.json
├── database/
│   ├── schema.sql                 # Tablo oluşturma
│   └── import_devices.py          # Cihaz import script
├── docker-compose-postgres.yml
└── start-postgres.sh
```

---

## 🔄 MongoDB'den PostgreSQL'e Farklar

| Özellik | MongoDB | PostgreSQL |
|---------|---------|------------|
| Veri Modeli | Document | Relational |
| Query | find(), update() | SQL SELECT, UPDATE |
| İlişkiler | Embed/Reference | Foreign Keys |
| Transactions | Limited | Full ACID |
| Performance | Read-heavy | Write-heavy |

**Kodda Değişenler:**

```python
# MongoDB (ESKİ)
await db.devices.find({}).to_list(1000)

# PostgreSQL (YENİ)
db.query(Device).all()
```

---

## 🐛 Sorun Giderme

### PostgreSQL Bağlanamıyor

```bash
# Container çalışıyor mu?
docker-compose -f docker-compose-postgres.yml ps

# Logları kontrol et
docker-compose -f docker-compose-postgres.yml logs postgres

# Yeniden başlat
docker-compose -f docker-compose-postgres.yml restart postgres
```

### Backend Hatası

```bash
# Backend logları
docker-compose -f docker-compose-postgres.yml logs backend

# Shell'e gir ve test et
docker exec -it tusep-backend bash
python -c "from database import engine; print(engine)"
```

### Tablolar Yok

```bash
# Postgres'e bağlan
docker exec -it tusep-postgres psql -U admin -d postgres

# Tabloları listele
\dt

# Eğer yoksa schema.sql'i çalıştır
\i /path/to/schema.sql
```

---

## 📊 Veritabanı Yönetimi

### Backup

```bash
# Full backup
docker exec tusep-postgres pg_dump -U admin postgres > backup.sql

# Sadece data
docker exec tusep-postgres pg_dump -U admin --data-only postgres > data.sql
```

### Restore

```bash
# Restore from backup
docker exec -i tusep-postgres psql -U admin postgres < backup.sql
```

### Temizlik

```bash
# Tüm verileri sil
docker exec -it tusep-postgres psql -U admin -d postgres -c "
  TRUNCATE fault_records, equipment_transfers, logs, devices, users CASCADE;
"

# Demo kullanıcıları tekrar ekle
docker exec -i tusep-postgres psql -U admin postgres < database/schema.sql
```

---

## 🎯 Performans İpuçları

1. **Indexler zaten mevcut** - schema.sql'de tanımlı
2. **Connection pooling** - SQLAlchemy otomatik yönetir
3. **Query optimization** - EXPLAIN ANALYZE kullan

```sql
EXPLAIN ANALYZE
SELECT * FROM devices WHERE location LIKE '%Radyoloji%';
```

---

## 📝 Notlar

- ✅ Tüm özellikler MongoDB versiyonu ile aynı
- ✅ API endpoint'leri değişmedi (Frontend güncel)
- ✅ Docker ile tam çalışır halde
- ✅ Production-ready
- ⚠️  İlk kurulumda tabloları oluşturmayı unutmayın
- ⚠️  1000 cihazı import etmeyi unutmayın

---

## 🆘 Yardım

Sorun yaşarsanız:

1. Logları kontrol edin
2. Docker ve PostgreSQL çalışıyor mu?
3. Tablolar oluşturuldu mu?
4. .env dosyası doğru mu?

**İletişim:** README'de belirtilen komutlarla kendi kendine debug yapabilirsiniz.

---

## ✅ Test Checklist

- [ ] Docker servisleri başladı
- [ ] PostgreSQL erişilebilir (psql test)
- [ ] Tablolar oluşturuldu
- [ ] Demo kullanıcılar eklendi
- [ ] Frontend açılıyor (http://localhost:3000)
- [ ] Login çalışıyor
- [ ] Cihazlar listesi görünüyor
- [ ] Transfer oluşturulabiliyor
- [ ] Kalite dashboard çalışıyor
- [ ] Excel raporları indiriliyor

---

**Made with ❤️ for Healthcare - PostgreSQL Edition**
