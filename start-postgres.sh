#!/bin/bash

echo "🏥 TÜSEP - PostgreSQL Version"
echo "================================================"
echo ""

# Check Docker
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker çalışmıyor! Docker Desktop'ı başlatın."
    exit 1
fi

echo "✓ Docker çalışıyor"
echo ""

# Start services
echo "🚀 Servisleri başlatıyorum (PostgreSQL)..."
docker-compose -f docker-compose-postgres.yml up -d

echo ""
echo "⏳ PostgreSQL'in hazır olması bekleniyor..."
sleep 15

echo ""
echo "📊 Veritabanı tablolarını kontrol edin:"
echo "   DataGrip veya psql ile bağlanın:"
echo "   Host: localhost"
echo "   Port: 5432"
echo "   Database: postgres"
echo "   User: admin"
echo "   Password: 1234"
echo ""
echo "================================================"
echo "✅ Sistem başlatıldı!"
echo "================================================"
echo ""
echo "📱 Uygulamayı açın:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8001"
echo "   API Docs: http://localhost:8001/docs"
echo ""
echo "🔐 Demo Kullanıcılar (Şifre: 12345):"
echo "   Kalite Birimi: zeynep@hastane.com"
echo "   Yönetici: fatma@hastane.com"
echo "   Teknisyen: mehmet@hastane.com"
echo ""
echo "📝 Loglar: docker-compose -f docker-compose-postgres.yml logs -f"
echo "🛑 Durdur: docker-compose -f docker-compose-postgres.yml down"
echo ""
