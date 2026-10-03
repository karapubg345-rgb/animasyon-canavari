"""Kaynak video indirici.

Instagram CDN dogrudan istekleri 403 ile reddedebiliyor; tarayici benzeri
basliklar ve Referer ile deneniyor.
"""
from __future__ import annotations

from pathlib import Path

import httpx

BASLIKLAR = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.instagram.com/",
}


class IndirmeHatasi(RuntimeError):
    pass


def video_indir(url: str, hedef: Path, *, zaman_asimi: int = 120) -> Path:
    hedef.parent.mkdir(parents=True, exist_ok=True)
    try:
        with httpx.stream(
            "GET", url, headers=BASLIKLAR, timeout=zaman_asimi, follow_redirects=True
        ) as r:
            if r.status_code != 200:
                raise IndirmeHatasi(f"HTTP {r.status_code} - {url[:80]}")
            with hedef.open("wb") as f:
                for parca in r.iter_bytes(1 << 16):
                    f.write(parca)
    except httpx.HTTPError as e:
        raise IndirmeHatasi(f"Ag hatasi: {e}") from e

    if hedef.stat().st_size < 10_000:
        raise IndirmeHatasi(f"Dosya cok kucuk ({hedef.stat().st_size} B) - muhtemelen hata sayfasi")
    return hedef
