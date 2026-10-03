"""Apify istemcisi.

Kritik kural: her actor run'indan ONCE kota kontrolu yapilir. Ucretsiz planda
aylik $5 limit var ve limit dolunca run sessizce yarida kesiliyor. Ayrica run
basina varsayilan bir maliyet tavani var; maxTotalChargeUsd bunu YUKSELTMIYOR
(kalan aylik krediye gore yeniden hesaplaniyor).
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import httpx

API = "https://api.apify.com/v2"


def token_yukle() -> str:
    """.env dosyasindan veya ortamdan APIFY_TOKEN okur."""
    if tok := os.environ.get("APIFY_TOKEN"):
        return tok
    env = Path(__file__).resolve().parents[3] / ".env"
    if env.exists():
        for satir in env.read_text(encoding="utf-8").splitlines():
            satir = satir.strip()
            if satir.startswith("APIFY_TOKEN="):
                return satir.split("=", 1)[1].strip()
    raise RuntimeError("APIFY_TOKEN bulunamadi (.env veya ortam degiskeni)")


@dataclass
class Kota:
    kalan_usd: float
    kullanilan_usd: float
    limit_usd: float
    donem_sonu: str | None

    @property
    def yeterli(self) -> bool:
        return self.kalan_usd > 0


class KotaYetersiz(RuntimeError):
    pass


def kota_getir(token: str | None = None) -> Kota:
    token = token or token_yukle()
    r = httpx.get(
        f"{API}/users/me/limits",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    r.raise_for_status()
    d = r.json()["data"]

    kullanim = d.get("current", {})
    limitler = d.get("limits", {})
    kullanilan = float(kullanim.get("monthlyUsageUsd", 0.0))
    limit = float(limitler.get("maxMonthlyUsageUsd", 0.0))
    return Kota(
        kalan_usd=round(limit - kullanilan, 4),
        kullanilan_usd=kullanilan,
        limit_usd=limit,
        donem_sonu=d.get("monthlyUsageCycle", {}).get("endAt"),
    )


def kota_dogrula(min_kalan: float) -> Kota:
    """Kota yetersizse run BASLATMADAN hata verir."""
    k = kota_getir()
    if k.kalan_usd < min_kalan:
        raise KotaYetersiz(
            f"Apify kredisi yetersiz: kalan ${k.kalan_usd:.2f}, "
            f"gereken ${min_kalan:.2f}. Donem sonu: {k.donem_sonu}"
        )
    return k


def actor_calistir(
    actor: str,
    girdi: dict,
    *,
    min_kalan: float = 0.30,
    zaman_asimi_sn: int = 600,
) -> list[dict]:
    """Kota dogrula, actor'u calistir, dataset ogelerini dondur.

    Kota kontrolu run BASLAMADAN yapilir - limit dolu bir hesapta run sessizce
    yarida kesildigi icin bu adim atlanamaz.
    """
    kota_dogrula(min_kalan)
    token = token_yukle()
    h = {"Authorization": f"Bearer {token}"}

    r = httpx.post(
        f"{API}/acts/{actor}/run-sync-get-dataset-items",
        headers=h,
        json=girdi,
        params={"timeout": zaman_asimi_sn},
        timeout=zaman_asimi_sn + 30,
    )
    r.raise_for_status()
    return r.json()
