"""Kaynak reel filtreleme ve secim."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Apify reel ogelerinde metrik alanlari saglayiciya gore degisebiliyor;
# ilk dolu olani kullanilir.
IZLENME_ALANLARI = ("videoPlayCount", "videoViewCount", "playsCount", "viewsCount")
BEGENI_ALANLARI = ("likesCount", "likeCount")


def _ilk_sayi(d: dict, alanlar: tuple[str, ...]) -> int:
    for a in alanlar:
        v = d.get(a)
        if isinstance(v, (int, float)) and v > 0:
            return int(v)
    return 0


@dataclass
class Aday:
    kimlik: str
    kisa_kod: str
    url: str
    video_url: str | None
    izlenme: int
    begeni: int
    sure_sn: float
    aciklama: str
    sahip: str
    ham: dict = field(repr=False, default_factory=dict)

    @property
    def etkilesim_orani(self) -> float:
        return self.begeni / self.izlenme if self.izlenme else 0.0


def ogeden_aday(o: dict) -> Aday | None:
    kod = o.get("shortCode") or o.get("shortcode")
    if not kod:
        return None
    return Aday(
        kimlik=str(o.get("id") or kod),
        kisa_kod=kod,
        url=o.get("url") or f"https://www.instagram.com/reel/{kod}/",
        video_url=o.get("videoUrl"),
        izlenme=_ilk_sayi(o, IZLENME_ALANLARI),
        begeni=_ilk_sayi(o, BEGENI_ALANLARI),
        sure_sn=float(o.get("videoDuration") or 0.0),
        aciklama=(o.get("caption") or "")[:300],
        sahip=o.get("ownerUsername") or "",
        ham=o,
    )


def filtrele(
    ogeler: list[dict],
    *,
    min_izlenme: int,
    min_begeni: int,
    sure_araligi: tuple[float, float],
    haric_kodlar: set[str] | None = None,
) -> list[Aday]:
    haric = haric_kodlar or set()
    alt, ust = sure_araligi
    gorulen: set[str] = set()
    sonuc: list[Aday] = []

    for o in ogeler:
        a = ogeden_aday(o)
        if a is None or a.kisa_kod in haric or a.kisa_kod in gorulen:
            continue
        gorulen.add(a.kisa_kod)
        if a.izlenme < min_izlenme or a.begeni < min_begeni:
            continue
        # sure bilgisi yoksa eleme - bazi ogelerde alan bos geliyor
        if a.sure_sn and not (alt <= a.sure_sn <= ust):
            continue
        sonuc.append(a)

    sonuc.sort(key=lambda x: (x.etkilesim_orani, x.izlenme), reverse=True)
    return sonuc
