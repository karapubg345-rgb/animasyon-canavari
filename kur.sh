#!/usr/bin/env bash
# Animasyon Canavarı — macOS / Linux kurulumu
set -e
cd "$(dirname "$0")"

sor() { read -r -p "  $1 [e/h] " c; [[ "$c" =~ ^[eEyY] ]]; }

echo
echo "  Animasyon Canavarı — kurulum"
echo

echo "[1/5] Python kontrol ediliyor..."
if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
  echo "  Python 3.10 veya üstü bulunamadı."
  if command -v brew >/dev/null && sor "Homebrew ile Python kurulsun mu?"; then brew install python@3.12
  else echo "  https://www.python.org/downloads/ adresinden kur ve tekrar çalıştır."; exit 1; fi
fi
echo "  Tamam."

echo "[2/5] ffmpeg kontrol ediliyor..."
if ! command -v ffmpeg >/dev/null; then
  echo "  ffmpeg bulunamadı (kaynak video analizi için gerekli)."
  if command -v brew >/dev/null && sor "Homebrew ile ffmpeg kurulsun mu?"; then brew install ffmpeg
  elif command -v apt-get >/dev/null && sor "apt ile ffmpeg kurulsun mu?"; then sudo apt-get install -y ffmpeg
  else echo "  https://ffmpeg.org/download.html adresinden kur ve tekrar çalıştır."; exit 1; fi
fi
echo "  Tamam."

echo "[3/5] Claude Code kontrol ediliyor..."
if ! command -v claude >/dev/null; then
  echo "  Claude Code bulunamadı."
  if sor "Resmi kurulum betiğiyle kurulsun mu?"; then
    curl -fsSL https://claude.ai/install.sh | bash
    echo "  Kuruldu. Yeni bir terminal açıp ./kur.sh'i tekrar çalıştır."; exit 0
  else echo "  https://docs.claude.com/en/docs/claude-code/setup"; exit 1; fi
fi
echo "  Tamam."

echo "[4/5] Python paketleri kuruluyor..."
[ -x .venv/bin/python ] || python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt -q
.venv/bin/python -c 'import yaml, apify_client, PIL, httpx'
echo "  Tamam."

echo "[5/5] Ayar dosyası..."
if [ ! -f .env ]; then cp .env.example .env; echo "  .env oluşturuldu — içine Apify token'ını yapıştır."; else echo "  .env zaten var."; fi

echo
echo "  Kurulum bitti."
echo
echo "  Son bir adım (yalnızca ilk seferde):"
echo "    1. Bu klasörde  claude  yaz."
echo "    2. Claude hesabınla giriş yap, 'bu klasöre güveniyor musun' sorusuna Evet de."
echo "    3. /exit ile çık."
echo
echo "  Sonra her seferinde:  ./baslat.sh"
