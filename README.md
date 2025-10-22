# 🏥 TÜSEP Healthcare Equipment Maintenance System

Kapsamlı tıbbi cihaz bakım ve güvenilirlik yönetim sistemi. MTBF, MTTR ve Kullanılabilirlik metrikleri ile TÜSEP standartlarına uygun raporlama.

![TÜSEP Dashboard](https://img.shields.io/badge/TÜSEP-Healthcare-blue)
![Docker](https://img.shields.io/badge/Docker-Ready-green)
![React](https://img.shields.io/badge/React-19.0-61dafb)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688)

## 🚀 Hızlı Başlangıç (3 Adım)

### MacOS Kullanıcıları

```bash
# 1. Zip dosyasını açın ve klasöre girin
cd tusep-dashboard

# 2. Tek komutla başlatın
chmod +x quickstart-mac.sh && ./quickstart-mac.sh

# 3. Tarayıcınızda açın: http://localhost:3000
```

📖 **Detaylı:** [KURULUM_MACOS.md](KURULUM_MACOS.md)

### Windows Kullanıcıları

1. `start.bat` dosyasına çift tıklayın
2. http://localhost:3000 adresini açın

### 🔐 Giriş Yapın

**Email:** `fatma@hastane.com`  
**Şifre:** `12345`

[Tüm demo kullanıcılar](#-demo-kullanıcılar)

---

## 🌟 Özellikler

✅ Arıza yönetim iş akışı (Bildir → Ata → Onar → Onayla)  
✅ MTBF, MTTR, Kullanılabilirlik hesaplaması  
✅ TÜSEP uyumlu raporlama (Gİ.YD.DH.08, 07, 05)  
✅ Teknisyen performans takibi  
✅ Rol bazlı erişim (4 farklı rol)  
✅ Gerçek zamanlı dashboard ve grafikler  
✅ Türkçe arayüz  
✅ Responsive tasarım  

## 📊 Demo Kullanıcılar

**Tüm şifreler:** `12345`

| Rol | Email | Yapabilecekleri |
|-----|-------|-----------------|
| 👨‍⚕️ Sağlık Personeli | `ayse@hastane.com` | Arıza bildirir, onarımı onaylar |
| 🔧 Teknisyen | `mehmet@hastane.com` | Onarım yapar (15 başarılı) |
| 🔧 Teknisyen | `ali@hastane.com` | Onarım yapar (12 başarılı) |
| 👔 Yönetici | `fatma@hastane.com` | Teknisyen atar, tüm raporları görür |
| 📊 Kalite Birimi | `zeynep@hastane.com` | TÜSEP raporlarını görür |

## 📐 Teknoloji

- **Frontend:** React 19 + Shadcn UI + Recharts
- **Backend:** FastAPI + JWT Auth
- **Database:** MongoDB 7.0
- **Deployment:** Docker + Docker Compose

## 🛠️ Yararlı Komutlar

```bash
# Başlat
docker-compose up -d

# Logları izle
docker-compose logs -f

# Durdur
docker-compose down

# Yeniden başlat
docker-compose restart

# Demo verileri yenile
docker exec tusep-backend python seed_data.py
```

## 📚 Dokümantasyon

- 📖 [MacOS Kurulum](KURULUM_MACOS.md) - Detaylı MacOS rehberi
- 🐳 [Docker Rehberi](README_DOCKER.md) - Docker detayları
- 🔌 [API Docs](http://localhost:8001/docs) - Swagger UI

## 📄 Lisans

MIT License

---

**Made with ❤️ for Healthcare**
