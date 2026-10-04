"""Kaynak suresinden uretim planini (model, sure, sayfa, panel) cikarir.

IKI MODEL BIRLIKTE KULLANILIYOR ve sure hangisine gidilecegini belirler:
  <=15sn -> Seedance 2.0  (1 sayfa / 12 panel)
  16-30sn -> Seedance 2.5 (2 sayfa / 24 panel)

Seedance 2.0 emekli DEGIL - 15sn'lik uretimlerin yolu odur. 2.5 onun yerine
gecmez, yanina eklenir: 2.0'in cikaramadigi uzun isleri karsilar.

15sn ustu isler BOLUNMEZ; storyboard SAYFA sayisi artar, panel yogunlugu
artmaz. 2.5'in sert sinirlari: docs/seedance_2_5.md

30sn ustu isler REDDEDILMEZ: her ~15sn icin bir storyboard sayfasi uretilir ve
sayfalar ikiser gruplanip BOLUM olur (2 sayfa -> 2.5, tek kalan sayfa -> 2.0).
Her bolum ayri video olarak uretilir, sonra ffmpeg ile birlestirilir.
"""
from __future__ import annotations

from dataclasses import dataclass


class SureHatasi(ValueError):
    pass


@dataclass(frozen=True)
class Bolum:
    """Tek geciste uretilen video parcasi (<=30sn). Sayfa no'lari GLOBAL."""
    no: int
    model: str
    sure_sn: int
    sayfa_ilk: int
    sayfa_son: int
    baslangic_sn: int     # birlesik videodaki baslangic


@dataclass(frozen=True)
class Plan:
    model: str            # "Seedance 2.0" veya "Seedance 2.5" - sure belirler
    sure_sn: int          # uretilecek video suresi (tam sayi)
    sayfa: int            # storyboard sayfa sayisi
    panel: int            # toplam panel (= sayfa * sayfa_panel)
    sayfa_panel: int      # sayfa basina panel (grid sutun*satir)
    panel_sn: float       # panel basina sure (bolumlu iste en uzun sayfanin degeri)
    bolunmeli: bool       # kaynak 30sn'yi asiyor -> birden fazla videoya bolunur
    sayfa_sureleri: tuple[int, ...] = ()
    bolumler: tuple[Bolum, ...] = ()

    def ozet(self) -> str:
        s = (
            f"{self.model} / {self.sure_sn}s / {self.sayfa} storyboard sayfasi / "
            f"{self.panel} panel / panel basina {self.panel_sn:.2f}s"
        )
        if not self.bolunmeli:
            return s
        b = ", ".join(
            f"B{x.no}: sayfa {x.sayfa_ilk}-{x.sayfa_son} {x.sure_sn}s {x.model}"
            for x in self.bolumler
        )
        return f"{s}  [{len(self.bolumler)} BOLUM: {b}]"


def _dilim(p: dict, sure: int) -> dict:
    """Sureye dusen sure_dilimi (model + sayfa + panel)."""
    dilimler = p["storyboard"]["sure_dilimleri"]
    for d in dilimler:
        if sure <= d["ust_sure_sn"]:
            return d
    return dilimler[-1]


def plan_yap(p: dict, kaynak_sure_sn: float) -> Plan:
    """pipeline.yaml ve kaynak suresinden uretim planini dondurur."""
    sb, v, s25 = p["storyboard"], p["video"], p["seedance_2_5"]
    alt, ust = s25["sure_araligi_sn"]
    sayfa_panel = sb["sutun"] * sb["satir"]
    sayfa_ust = sb.get("sayfa_basina_sn", 15)

    # Seedance ondalikli sure kabul etmiyor.
    sure = int(round(kaynak_sure_sn))
    if sure < alt:
        raise SureHatasi(f"sure {sure}s < {alt}s; en kisa uretilebilir sure {alt}s")

    # Sayfa basina en fazla ~15sn. Sure sayfalara TAM SAYI olarak dagitilir ki
    # ikiser gruplanan bolum sureleri de tam sayi ciksin (Seedance sarti).
    sayfa = -(-sure // sayfa_ust)
    taban, artan = divmod(sure, sayfa)
    sayfa_sureleri = tuple(taban + (1 if i < artan else 0) for i in range(sayfa))

    # Sayfalar ikiser gruplanir: 2 sayfa <=30sn -> tek 2.5 gecisi; tek kalan
    # sayfa <=15sn -> 2.0. Model dilim tablosundan gelir - elle secilmez.
    bolumler: list[Bolum] = []
    bas = 0
    for i in range(0, sayfa, 2):
        ss = sayfa_sureleri[i : i + 2]
        bs = sum(ss)
        d = _dilim(p, bs)
        # Dilim tablosu ile grid tutarsizsa sessizce yanlis sayfa kesilir.
        if d["panel"] != d["sayfa"] * sayfa_panel or d["sayfa"] != len(ss):
            raise SureHatasi(
                f"pipeline.yaml tutarsiz: {bs}s bolum {len(ss)} sayfa, dilim "
                f"{d['sayfa']} sayfa x {sayfa_panel} panel (={d['panel']}) diyor"
            )
        if bs > ust:
            raise SureHatasi(f"bolum {bs}s > {ust}s; sayfa_basina_sn'yi gozden gecir")
        bolumler.append(Bolum(len(bolumler) + 1, d["model"], bs, i + 1, i + len(ss), bas))
        bas += bs

    # Panel basina sure tavani asilirsa ritim kaynaktan yavas kalir.
    panel_sn = max(sayfa_sureleri) / sayfa_panel
    tavan = v.get("panel_basina_sn_tavan")
    if tavan and panel_sn > tavan + 1e-9:
        raise SureHatasi(
            f"panel basina {panel_sn:.2f}s > tavan {tavan}s; sure_dilimleri'ni gozden gecir"
        )

    modeller = list(dict.fromkeys(b.model for b in bolumler))
    return Plan(
        model=" + ".join(modeller),
        sure_sn=sure,
        sayfa=sayfa,
        panel=sayfa * sayfa_panel,
        sayfa_panel=sayfa_panel,
        panel_sn=panel_sn,
        bolunmeli=len(bolumler) > 1,
        sayfa_sureleri=sayfa_sureleri,
        bolumler=tuple(bolumler),
    )
