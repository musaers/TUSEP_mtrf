# TÜSEP Healthcare Equipment Maintenance System - Docker Setup

## 📋 Gereksinimler

- Docker Desktop (Windows/Mac) veya Docker Engine (Linux)
- Docker Compose
- VSCode (opsiyonel)
- Git

## 🚀 Kurulum Adımları

### 1. Projeyi Klonlayın

```bash
git clone <your-repo-url>
cd tusep-dashboard
```

### 2. Docker Desktop'ı Başlatın

Docker Desktop uygulamasını açın ve çalıştığından emin olun.

### 3. Uygulamayı Başlatın

```bash
# Tüm servisleri başlat (MongoDB + Backend + Frontend)
docker-compose up -d
```

İlk çalıştırmada image'ları indirip build edeceği için biraz zaman alabilir (5-10 dakika).

### 4. Demo Verileri Oluşturun

```bash
# Backend container'ına bağlanın
docker exec -it tusep-backend python seed_data.py
```

### 5. Uygulamayı Açın

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8001
- **API Dokümantasyonu:** http://localhost:8001/docs

## 🔐 Demo Kullanıcılar

Tüm kullanıcılar için şifre: **12345**

1. **Sağlık Personeli:** ayse@hastane.com
2. **Teknisyen 1:** mehmet@hastane.com
3. **Teknisyen 2:** ali@hastane.com
4. **Yönetici:** fatma@hastane.com
5. **Kalite Birimi:** zeynep@hastane.com

## 📝 Yararlı Komutlar

### Logları Görüntüleme

```bash
# Tüm servislerin logları
docker-compose logs -f

# Sadece backend logları
docker-compose logs -f backend

# Sadece frontend logları
docker-compose logs -f frontend
```

### Servisleri Yeniden Başlatma

```bash
# Tüm servisleri yeniden başlat
docker-compose restart

# Sadece backend'i yeniden başlat
docker-compose restart backend

# Sadece frontend'i yeniden başlat
docker-compose restart frontend
```

### Container'a Bağlanma

```bash
# Backend container'ına bash ile bağlan
docker exec -it tusep-backend bash

# Frontend container'ına bağlan
docker exec -it tusep-frontend sh

# MongoDB container'ına bağlan
docker exec -it tusep-mongodb mongosh
```

### Servisleri Durdurma

```bash
# Tüm servisleri durdur
docker-compose down

# Servisleri durdur ve volume'leri temizle (VERİLER SİLİNİR!)
docker-compose down -v
```

### Yeniden Build Etme

```bash
# Değişikliklerden sonra yeniden build et
docker-compose up -d --build

# Sadece backend'i yeniden build et
docker-compose up -d --build backend
```

## 🔧 VSCode ile Geliştirme

### 1. VSCode Eklentilerini Yükleyin

- **Docker** (Microsoft)
- **Remote - Containers** (Microsoft)
- **Python** (Backend için)
- **ESLint** (Frontend için)

### 2. Kod Değişikliklerini İzleme

Docker Compose, volumes sayesinde kod değişikliklerinizi otomatik olarak izler:

- **Backend:** `uvicorn --reload` ile otomatik yeniden başlar
- **Frontend:** React hot-reload aktif

Sadece kod düzenleyin, değişiklikler otomatik yansıyacaktır!

### 3. Debugging

**Backend (Python):**

`.vscode/launch.json` oluşturun:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Remote Attach",
      "type": "python",
      "request": "attach",
      "connect": {
        "host": "localhost",
        "port": 5678
      },
      "pathMappings": [
        {
          "localRoot": "${workspaceFolder}/backend",
          "remoteRoot": "/app"
        }
      ]
    }
  ]
}
```

**Frontend (React):**

Chrome DevTools ile debug edebilirsiniz.

## 🗄️ MongoDB Yönetimi

### MongoDB Compass ile Bağlanma

1. MongoDB Compass'ı indirin: https://www.mongodb.com/products/compass
2. Bağlantı string'i: `mongodb://localhost:27017/tusep_db`

### Veritabanını Sıfırlama

```bash
# MongoDB container'ına bağlan
docker exec -it tusep-mongodb mongosh

# Veritabanını temizle
use tusep_db
db.dropDatabase()
exit

# Demo verileri tekrar oluştur
docker exec -it tusep-backend python seed_data.py
```

## 🐛 Sorun Giderme

### Port Çakışması

Eğer portlar kullanılıyorsa, `docker-compose.yml` dosyasında port numaralarını değiştirin:

```yaml
services:
  frontend:
    ports:
      - "3001:3000"  # 3000 yerine 3001 kullan
```

### Container Başlamıyor

```bash
# Logları kontrol et
docker-compose logs backend

# Container'ı yeniden oluştur
docker-compose up -d --force-recreate backend
```

### Node Modules Sorunu (Frontend)

```bash
# Frontend container'ını durdur
docker-compose down frontend

# Volume'leri temizle ve yeniden başlat
docker-compose up -d --build frontend
```

### MongoDB Bağlantı Hatası

```bash
# MongoDB'nin çalıştığını kontrol et
docker-compose ps

# MongoDB loglarını kontrol et
docker-compose logs mongodb

# MongoDB'yi yeniden başlat
docker-compose restart mongodb
```

## 📦 Production Build

### Frontend Production Build

```bash
# Frontend'i production modda build et
docker exec -it tusep-frontend yarn build
```

### Backend Production

`Dockerfile.backend` içinde CMD satırını değiştirin:

```dockerfile
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "4"]
```

## 🌐 Network Yapısı

```
tusep-network (bridge)
├── mongodb:27017
├── backend:8001
└── frontend:3000
```

Tüm servisler aynı Docker network üzerinde birbirleriyle iletişim kurar.

## 📁 Proje Yapısı

```
tusep-dashboard/
├── backend/
│   ├── server.py
│   ├── seed_data.py
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── .env
├── Dockerfile.backend
├── Dockerfile.frontend
├── docker-compose.yml
├── .dockerignore
└── README_DOCKER.md
```

## 🎉 Başarılı Kurulum!

Artık TÜSEP Healthcare Equipment Maintenance System'i Docker ile çalıştırıyorsunuz!

**Sorularınız için:**
- GitHub Issues
- Email: support@example.com

---

**Made with ❤️ for Healthcare**