"""Kullanicinin dogrudan verdigi Instagram linkinden is olusturma.

Kesif adimini atlar: link -> metadata -> indirme -> normal pipeline.
"""
from __future__ import annotations

import re

from .apify_istemci import actor_calistir
from .filtre import Aday, ogeden_aday

REEL_ACTOR = "apify~instagram-reel-scraper"
POST_ACTOR = "apify~instagram-scraper"

# /reel/KOD/, /reels/KOD/, /p/KOD/, /tv/KOD/
KOD_KALIBI = re.compile(r"instagram\.com/(?:reels?|p|tv)/([A-Za-z0-9_-]+)")


class GecersizLink(ValueError):
    pass


def kod_cikar(url: str) -> str:
    m = KOD_KALIBI.search(url.strip())
    if not m:
        raise GecersizLink(
            f"Instagram reel/post linki taninmadi: {url!r}\n"
            "Beklenen bicim: https://www.instagram.com/reel/KOD/"
        )
    return m.group(1)


def linkten_aday(url: str, *, min_kalan: float = 0.30) -> Aday:
    """Verilen linkin metadata'sini ceker ve Aday olarak dondurur."""
    kod = kod_cikar(url)
    temiz = f"https://www.instagram.com/reel/{kod}/"

    ogeler = actor_calistir(
        REEL_ACTOR,
        {"username": [temiz], "resultsLimit": 1},
        min_kalan=min_kalan,
    )
    if not ogeler:
        # reel-scraper bos donerse genel scraper'i dene (post olabilir)
        ogeler = actor_calistir(
            POST_ACTOR,
            {"directUrls": [temiz], "resultsType": "posts", "resultsLimit": 1},
            min_kalan=min_kalan,
        )
    if not ogeler:
        raise GecersizLink(f"Link icin veri donmedi: {temiz}")

    aday = ogeden_aday(ogeler[0])
    if aday is None or not aday.video_url:
        raise GecersizLink(f"Video URL'i alinamadi: {temiz}")
    return aday
