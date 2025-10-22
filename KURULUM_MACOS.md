# 🍎 MacBook'ta TÜSEP Sistemini Çalıştırma Rehberi

## 📋 Ön Gereksinimler

### 1. Docker Desktop'ı Yükleyin

1. Docker Desktop'ı indirin: https://www.docker.com/products/docker-desktop/
2. DMG dosyasını açın ve Docker.app'i Applications klasörüne sürükleyin
3. Docker Desktop'ı başlatın
4. İlk açılışta izinleri onaylayın

**Docker'ın çalıştığını kontrol edin:**
```bash
docker --version
docker-compose --version
```

## 🚀 Kurulum Adımları

### Adım 1: Zip Dosyasını Açın

```bash
# Downloads klasörüne gidin
cd ~/Downloads

# Zip dosyasını açın (dosya adını kendi dosyanıza göre değiştirin)
unzip tusep-dashboard.zip

# Proje klasörüne girin
cd tusep-dashboard
```

### Adım 2: Gerekli Dosyaları Kontrol Edin

```bash
# Dosya yapısını kontrol edin
ls -la

# Şunları görmelisiniz:
# - backend/
# - frontend/
# - docker-compose.yml
# - Dockerfile.backend
# - Dockerfile.frontend
```

### Adım 3: Environment Dosyalarını Ayarlayın

Backend .env dosyası zaten hazır olmalı ama kontrol edelim:

```bash
# Backend .env'yi kontrol edin
cat backend/.env
```

Eğer yoksa, oluşturun:

```bash
cat > backend/.env << 'EOF'
MONGO_URL=mongodb://mongodb:27017
DB_NAME=tusep_db
CORS_ORIGINS=*
SECRET_KEY=tusep-healthcare-secret-key-change-in-production-12345
EOF
```

Frontend .env dosyası:

```bash
cat > frontend/.env << 'EOF'
REACT_APP_BACKEND_URL=http://localhost:8001
WDS_SOCKET_PORT=0
CHOKIDAR_USEPOLLING=true
EOF
```

### Adım 4: Docker ile Başlatın

**Otomatik (Önerilen):**

```bash
# Start script'ini çalıştırılabilir yapın
chmod +x start.sh

# Tüm sistemi başlatın
./start.sh
```

**Manuel:**

```bash
# 1. Docker Desktop'ın çalıştığından emin olun

# 2. Servisleri başlatın (ilk seferde 5-10 dakika sürebilir)
docker-compose up -d

# 3. Servislerin hazır olmasını bekleyin (30 saniye)
sleep 30

# 4. Demo verileri oluşturun
docker exec tusep-backend python seed_data.py
```

### Adım 5: Uygulamayı Açın

**Web tarayıcınızda açın:**

1. **Frontend:** http://localhost:3000
2. **Backend API:** http://localhost:8001
3. **API Dokümantasyonu:** http://localhost:8001/docs

## 🔐 Giriş Bilgileri

Tüm kullanıcılar için şifre: **12345**

### Demo Kullanıcılar:

| Rol | Email | Özellikler |
|-----|-------|-----------|
| 👨‍⚕️ Sağlık Personeli | ayse@hastane.com | Arıza bildirir, onarımı onaylar |
| 🔧 Teknisyen 1 | mehmet@hastane.com | Onarım yapar (15 başarılı) |
| 🔧 Teknisyen 2 | ali@hastane.com | Onarım yapar (12 başarılı) |
| 👔 Yönetici | fatma@hastane.com | Arıza atar, rapor görür |
| 📊 Kalite Birimi | zeynep@hastane.com | TÜSEP raporlarını görür |

## 📝 Yararlı Komutlar

### Logları Görüntüleme

```bash
# Tüm servislerin logları
docker-compose logs -f

# Sadece backend
docker-compose logs -f backend

# Sadece frontend
docker-compose logs -f frontend
```

### Servisleri Kontrol Etme

```bash
# Çalışan servisleri görüntüle
docker-compose ps

# Servis durumlarını kontrol et
docker ps
```

### Servisleri Yeniden Başlatma

```bash
# Tüm servisleri yeniden başlat
docker-compose restart

# Sadece backend
docker-compose restart backend
```

### Container'a Bağlanma

```bash
# Backend container'ına bağlan
docker exec -it tusep-backend bash

# Frontend container'ına bağlan
docker exec -it tusep-frontend sh

# MongoDB'ye bağlan
docker exec -it tusep-mongodb mongosh
```

### Servisleri Durdurma

```bash
# Servisleri durdur (veriler korunur)
docker-compose down

# Servisleri durdur ve tüm verileri temizle
docker-compose down -v
```

### Veritabanını Sıfırlama

```bash
# MongoDB'ye bağlan
docker exec -it tusep-mongodb mongosh

# Veritabanını sil
use tusep_db
db.dropDatabase()
exit

# Demo verileri yeniden oluştur
docker exec tusep-backend python seed_data.py
```

## 🔧 VSCode ile Geliştirme

### 1. VSCode'u Açın

```bash
# Proje klasöründe VSCode'u açın
code .
```

### 2. Önerilen Eklentiler

VSCode'da şu eklentileri yükleyin:

- **Docker** (Microsoft)
- **Python** (Microsoft)
- **ESLint** (Microsoft)
- **Prettier** (Prettier)

### 3. Kod Değişiklikleri

Docker volumes sayesinde yaptığınız değişiklikler otomatik yansır:

- **Backend:** Kod değiştirdiğinizde uvicorn otomatik yeniden başlar
- **Frontend:** React hot-reload aktif, sayfa otomatik yenilenir

## 🐛 Sorun Giderme

### Port Zaten Kullanılıyor Hatası

Port 3000 veya 8001 kullanılıyorsa:

```bash
# Portları kullanan process'leri bulun
lsof -i :3000
lsof -i :8001

# Process'i sonlandırın
kill -9 <PID>
```

Veya `docker-compose.yml` dosyasında portları değiştirin:

```yaml
frontend:
  ports:
    - "3001:3000"  # 3000 yerine 3001 kullan
```

### Docker Desktop Başlamıyor

1. Docker Desktop'ı tamamen kapatın
2. Mac'i yeniden başlatın
3. Docker Desktop'ı tekrar açın

### Container Başlamıyor

```bash
# Logları kontrol edin
docker-compose logs backend

# Container'ı yeniden oluşturun
docker-compose up -d --force-recreate backend
```

### MongoDB Bağlantı Hatası

```bash
# MongoDB'nin çalıştığını kontrol edin
docker-compose ps mongodb

# MongoDB'yi yeniden başlatın
docker-compose restart mongodb

# MongoDB loglarını kontrol edin
docker-compose logs mongodb
```

### Frontend Boş Sayfa Gösteriyor

```bash
# Browser cache'i temizleyin (Cmd + Shift + R)

# Veya frontend'i yeniden build edin
docker-compose restart frontend

# Logları kontrol edin
docker-compose logs frontend
```

### "Permission Denied" Hatası

```bash
# Script'lere execute yetkisi verin
chmod +x start.sh

# Veya sudo ile çalıştırın
sudo ./start.sh
```

## 📦 Production Build (Opsiyonel)

### Frontend Production Build

```bash
# Frontend container'ına girin
docker exec -it tusep-frontend sh

# Production build oluşturun
yarn build

# Çıkış
exit
```

Build dosyaları `frontend/build` klasöründe oluşacak.

## 🧹 Temizlik

### Docker Temizliği (Disk Alanı Kazanmak)

```bash
# Kullanılmayan container'ları temizle
docker container prune

# Kullanılmayan image'ları temizle
docker image prune -a

# Kullanılmayan volume'leri temizle
docker volume prune

# Hepsini birden temizle
docker system prune -a --volumes
```

**⚠️ DİKKAT:** `--volumes` parametresi tüm veritabanı verilerini siler!

## 🎯 Hızlı Komut Özeti

```bash
# Başlat
docker-compose up -d

# Durdur
docker-compose down

# Logları izle
docker-compose logs -f

# Yeniden başlat
docker-compose restart

# Demo verileri oluştur
docker exec tusep-backend python seed_data.py

# Temizle (verilerle birlikte)
docker-compose down -v
```

## 📚 Ek Kaynaklar

- **Docker Desktop Docs:** https://docs.docker.com/desktop/mac/
- **React Docs:** https://react.dev
- **FastAPI Docs:** https://fastapi.tiangolo.com
- **MongoDB Docs:** https://docs.mongodb.com

## 🆘 Yardım

Sorun yaşıyorsanız:

1. Önce `docker-compose logs` ile logları kontrol edin
2. Docker Desktop'ın çalıştığından emin olun
3. Mac'inizi yeniden başlatıp tekrar deneyin
4. Bu README'deki sorun giderme adımlarını takip edin

## ✅ Başarılı Kurulum Kontrolü

Aşağıdaki komutlar çalışıyorsa kurulum başarılı:

```bash
# 1. Docker servislerinin durumu
docker-compose ps
# Çıktı: 3 servis "Up" durumunda olmalı

# 2. Backend'e erişim
curl http://localhost:8001/api/
# Çıktı: {"message":"Hello World"}

# 3. Frontend'e erişim
curl http://localhost:3000
# Çıktı: HTML içeriği dönmeli
```

---

## 🎉 İyi Geliştirmeler!

Artık TÜSEP Healthcare Equipment Maintenance System'i MacBook'unuzda çalıştırıyorsunuz!

**Soru ve önerileriniz için:** GitHub Issues veya email
