"""Kaynak suresinden uretim planini (model, sure, sayfa, panel) cikarir.

IKI MODEL BIRLIKTE KULLANILIYOR ve sure hangisine gidilecegini belirler:
  <=15sn -> Seedance 2.0  (1 sayfa / 12 panel)
  16-30sn -> Seedance 2.5 (2 sayfa / 24 panel)

Seedance 2.0 emekli DEGIL - 15sn'lik uretimlerin yolu odur. 2.5 onun yerine
gecmez, yanina eklenir: 2.0'in cikaramadigi uzun isleri karsilar.

15sn ustu isler BOLUNMEZ; storyboard SAYFA sayisi artar, panel yogunlugu
artmaz. 2.5'in sert sinirlari: docs/seedance_2_5.md
"""
from __future__ import annotations

from dataclasses import dataclass


class SureHatasi(ValueError):
    pass


@dataclass(frozen=True)
class Plan:
    model: str            # "Seedance 2.0" veya "Seedance 2.5" - sure belirler
    sure_sn: int          # uretilecek video suresi (tam sayi)
    sayfa: int            # storyboard sayfa sayisi
    panel: int            # toplam panel (= sayfa * sayfa_panel)
    sayfa_panel: int      # sayfa basina panel (grid sutun*satir)
    panel_sn: float       # panel basina sure
    bolunmeli: bool       # kaynak 30sn'yi asiyor -> birden fazla videoya bolunur

    def ozet(self) -> str:
        s = (
            f"{self.model} / {self.sure_sn}s / {self.sayfa} storyboard sayfasi / "
            f"{self.panel} panel / panel basina {self.panel_sn:.2f}s"
        )
        return f"{s}  [BOLUNMELI]" if self.bolunmeli else s


def plan_yap(p: dict, kaynak_sure_sn: float) -> Plan:
    """pipeline.yaml ve kaynak suresinden uretim planini dondurur."""
    sb, v, s25 = p["storyboard"], p["video"], p["seedance_2_5"]
    alt, ust = s25["sure_araligi_sn"]
    sayfa_panel = sb["sutun"] * sb["satir"]

    # Seedance ondalikli sure kabul etmiyor.
    sure = int(round(kaynak_sure_sn))
    # Ust sinir en uzun modelin tavani (2.5 -> 30sn); asilirsa is bolunur.
    bolunmeli = sure > ust
    if bolunmeli:
        sure = ust
    # Alt sinir model secilmeden once kontrol edildigi icin mesaj model adi
    # vermiyor - hangi dilime dusecegi bu noktada henuz belli degil.
    if sure < alt:
        raise SureHatasi(f"sure {sure}s < {alt}s; en kisa uretilebilir sure {alt}s")

    # Model dilimden gelir - elle secilmez. Dilim tablosunu degistirmeden
    # model degistirmek iki modelin sinirlarini karistirmaya yol acar.
    for d in sb["sure_dilimleri"]:
        if sure <= d["ust_sure_sn"]:
            break
    else:
        d = sb["sure_dilimleri"][-1]
    model, sayfa, panel = d["model"], d["sayfa"], d["panel"]

    # Dilim tablosu ile grid tutarsizsa sessizce yanlis sayfa kesilir.
    if panel != sayfa * sayfa_panel:
        raise SureHatasi(
            f"pipeline.yaml tutarsiz: {sayfa} sayfa x {sayfa_panel} panel != {panel}"
        )

    # Panel basina sure tavani asilirsa ritim kaynaktan yavas kalir.
    panel_sn = sure / panel
    tavan = v.get("panel_basina_sn_tavan")
    if tavan and panel_sn > tavan + 1e-9:
        raise SureHatasi(
            f"panel basina {panel_sn:.2f}s > tavan {tavan}s; sure_dilimleri'ni gozden gecir"
        )

    return Plan(model, sure, sayfa, panel, sayfa_panel, panel_sn, bolunmeli)
