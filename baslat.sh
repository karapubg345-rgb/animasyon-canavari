#!/usr/bin/env bash
cd "$(dirname "$0")"
[ -x .venv/bin/python ] || { echo "Önce ./kur.sh'i çalıştır."; exit 1; }
.venv/bin/python -c 'import yaml, apify_client, PIL, httpx' 2>/dev/null \
  || { echo "Python paketleri eksik — kurulum yarıda kalmış. Önce ./kur.sh'i yeniden çalıştır."; exit 1; }
export PYTHONIOENCODING=utf-8
echo "Animasyon Canavarı açılıyor... Bu terminali kapatma; kapatırsan arayüz durur."
exec .venv/bin/python arayuz/sunucu.py
