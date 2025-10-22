#!/bin/bash

clear

cat << "EOF"
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║     🏥 TÜSEP Healthcare Equipment Maintenance System    ║
║           Tıbbi Cihaz Bakım Yönetim Sistemi             ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
EOF

echo ""
echo "🔍 Ön kontroller yapılıyor..."
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker bulunamadı!"
    echo ""
    echo "📥 Docker Desktop'ı indirmek için:"
    echo "   https://www.docker.com/products/docker-desktop/"
    echo ""
    exit 1
fi

echo "✅ Docker kurulu"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "⚠️  Docker çalışmıyor!"
    echo ""
    echo "🚀 Docker Desktop'ı başlatın ve tekrar deneyin:"
    echo "   1. Applications klasöründen Docker.app'i açın"
    echo "   2. Docker ikonu menü çubuğunda görünene kadar bekleyin"
    echo "   3. Bu script'i tekrar çalıştırın"
    echo ""
    exit 1
fi

echo "✅ Docker çalışıyor"

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ docker-compose.yml bulunamadı!"
    echo ""
    echo "📂 Lütfen proje klasöründe olduğunuzdan emin olun:"
    echo "   cd /path/to/tusep-dashboard"
    echo ""
    exit 1
fi

echo "✅ Proje dosyaları bulundu"
echo ""

# Ask user if they want to continue
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📦 Şimdi şunlar yapılacak:"
echo "   1. Docker image'ları indirilecek (ilk seferde 5-10 dakika)"
echo "   2. MongoDB, Backend ve Frontend başlatılacak"
echo "   3. Demo kullanıcılar ve örnek veriler oluşturulacak"
echo ""
read -p "Devam etmek istiyor musunuz? (E/H): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[EeYy]$ ]]; then
    echo "İşlem iptal edildi."
    exit 0
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Stop any existing containers
echo "🧹 Eski container'lar temizleniyor..."
docker-compose down > /dev/null 2>&1

# Start services
echo "🚀 Servisler başlatılıyor..."
echo "   (Bu işlem ilk seferde biraz uzun sürebilir)"
echo ""

docker-compose up -d

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Servisler başlatılamadı!"
    echo ""
    echo "🔍 Hata detayları için:"
    echo "   docker-compose logs"
    echo ""
    exit 1
fi

echo ""
echo "⏳ Servislerin hazır olması bekleniyor..."

# Wait for services to be ready
for i in {1..30}; do
    if docker exec tusep-backend python -c "import sys; sys.exit(0)" > /dev/null 2>&1; then
        break
    fi
    echo -n "."
    sleep 1
done
echo ""

# Check if backend is ready
if ! docker exec tusep-backend python -c "import sys; sys.exit(0)" > /dev/null 2>&1; then
    echo ""
    echo "⚠️  Backend hazır değil, biraz daha bekleniyor..."
    sleep 10
fi

echo ""
echo "🌱 Demo verileri oluşturuluyor..."
echo ""

# Seed database
docker exec tusep-backend python seed_data.py

if [ $? -ne 0 ]; then
    echo ""
    echo "⚠️  Demo verileri oluşturulamadı, ancak sistem çalışıyor"
    echo "   Manuel olarak oluşturmak için:"
    echo "   docker exec tusep-backend python seed_data.py"
    echo ""
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Kurulum başarıyla tamamlandı!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 Tarayıcınızda açın:"
echo ""
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8001"
echo "   API Docs:  http://localhost:8001/docs"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🔐 Demo Kullanıcılar (Tüm şifreler: 12345)"
echo ""
echo "   👨‍⚕️  Sağlık Personeli:  ayse@hastane.com"
echo "   🔧  Teknisyen 1:        mehmet@hastane.com"
echo "   🔧  Teknisyen 2:        ali@hastane.com"
echo "   👔  Yönetici:          fatma@hastane.com"
echo "   📊  Kalite Birimi:     zeynep@hastane.com"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📝 Yararlı Komutlar:"
echo ""
echo "   Logları izle:        docker-compose logs -f"
echo "   Servisleri durdur:   docker-compose down"
echo "   Yeniden başlat:      docker-compose restart"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Try to open browser automatically
if command -v open &> /dev/null; then
    read -p "🌐 Tarayıcıda otomatik açılsın mı? (E/H): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[EeYy]$ ]]; then
        echo "🚀 Tarayıcı açılıyor..."
        sleep 2
        open http://localhost:3000
    fi
fi

echo ""
echo "🎉 İyi çalışmalar!"
echo ""
