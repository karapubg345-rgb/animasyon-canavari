"""Storyboard sayfasinin numarali DENETIM kopyasini uretir.

Panel <-> beat eslesmesini onay kapisinda gozle dogrulayabilmek icin numara
gerekiyor. Ama numarayi MODELDEN istemek yasak: storyboard Seedance'a referans
olarak gidiyor ve panele yanan her iz video karelerine kopyalaniyor
(docs/damga_tuzagi.md). Cozum: temiz sayfayi uret, numarayi uretimden SONRA
yerel olarak bas, ve iki dosyayi birbirine karistirilamayacak sekilde ayir.

  storyboard_sayfaN.png          -> TEMIZ. Seedance'a yuklenen dosya budur.
  storyboard_sayfaN_denetim.png  -> numarali. Yalnizca insan denetimi icin.

Denetim kopyasi ayirt edilebilir olsun diye ustune kirmizi bir uyari bandi
basiliyor; boylece yanlislikla yuklenirse ekranda aninda goze carpar - ve
"_denetim" son eki damga.py'nin referans denetiminde de reddedilir.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BANT_YUKSEKLIGI_ORANI = 0.045
UYARI = "DENETIM KOPYASI - SEEDANCE'A YUKLEMEYIN"


def _font(boyut: int) -> ImageFont.ImageFont:
    for ad in ("arialbd.ttf", "arial.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(ad, boyut)
        except OSError:
            continue
    return ImageFont.load_default()


def denetim_kopyasi_uret(
    temiz_png: Path,
    paneller: list[dict],
    sutun: int = 6,
    satir: int = 2,
    cikis: Path | None = None,
) -> Path:
    """Temiz sayfaya panel no + zaman araligi basar, ayri dosyaya yazar.

    paneller: bu SAYFAYA dusen panel kayitlari (storyboard.json -> paneller
    diliminden). Numaralar global oldugu icin p["n"] oldugu gibi basilir.
    """
    beklenen = sutun * satir
    if len(paneller) > beklenen:
        raise ValueError(f"{len(paneller)} panel {sutun}x{satir} grid'e sigmaz")

    im = Image.open(temiz_png).convert("RGB")
    bant = int(im.height * BANT_YUKSEKLIGI_ORANI)
    tuval = Image.new("RGB", (im.width, im.height + bant), (200, 0, 0))
    tuval.paste(im, (0, bant))
    ciz = ImageDraw.Draw(tuval)

    ciz.text((im.width // 2, bant // 2), UYARI, font=_font(max(12, bant // 2)),
             fill=(255, 255, 255), anchor="mm")

    pw, ph = im.width / sutun, im.height / satir
    # Etiket panelin icerigini ortmemeli - zaman damgasi uzun ("15.00-16.25"),
    # %7.5'te etiket panel genisliginin neredeyse tamamini kapliyordu.
    etiket = _font(max(12, int(ph * 0.05)))
    for i, p in enumerate(paneller):
        x0, y0 = (i % sutun) * pw, (i // sutun) * ph + bant
        metin = f"{p['n']}  {p.get('zaman', '')}".strip()
        kutu = ciz.textbbox((0, 0), metin, font=etiket)
        gen, yuk = kutu[2] - kutu[0], kutu[3] - kutu[1]
        pay = max(3, int(gen * 0.06))
        ciz.rectangle(
            [x0 + 4, y0 + 4, x0 + 4 + gen + 2 * pay, y0 + 4 + yuk + 2 * pay],
            fill=(200, 0, 0),
        )
        ciz.text((x0 + 4 + pay - kutu[0], y0 + 4 + pay - kutu[1]), metin,
                 font=etiket, fill=(255, 255, 255))

    cikis = cikis or temiz_png.with_name(f"{temiz_png.stem}_denetim.png")
    tuval.save(cikis)
    return cikis
