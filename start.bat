@echo off
echo 🏥 TÜSEP Healthcare Equipment Maintenance System
echo ================================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker çalışmıyor! Lütfen Docker Desktop'ı başlatın.
    pause
    exit /b 1
)

echo ✓ Docker çalışıyor
echo.

REM Start services
echo 🚀 Servisleri başlatıyorum...
docker-compose up -d

echo.
echo ⏳ Servislerin hazır olması bekleniyor...
timeout /t 10 /nobreak >nul

REM Seed database
echo 🌱 Demo verileri oluşturuluyor...
docker exec tusep-backend python seed_data.py

echo.
echo ================================================
echo ✅ Kurulum tamamlandı!
echo ================================================
echo.
echo 📱 Uygulamayı açmak için:
echo    Frontend: http://localhost:3000
echo    Backend API: http://localhost:8001
echo    API Docs: http://localhost:8001/docs
echo.
echo 🔐 Demo Kullanıcılar (Şifre: 12345):
echo    Sağlık Personeli: ayse@hastane.com
echo    Teknisyen 1: mehmet@hastane.com
echo    Teknisyen 2: ali@hastane.com
echo    Yönetici: fatma@hastane.com
echo    Kalite Birimi: zeynep@hastane.com
echo.
echo 📝 Logları görmek için: docker-compose logs -f
echo 🛑 Durdurmak için: docker-compose down
echo.
pause
