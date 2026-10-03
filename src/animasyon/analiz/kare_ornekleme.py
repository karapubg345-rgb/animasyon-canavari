"""Kaynak videodan analiz kareleri cikarma (ffmpeg)."""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class VideoBilgi:
    genislik: int
    yukseklik: int
    sure_sn: float
    fps: float

    @property
    def oran(self) -> str:
        from math import gcd

        g = gcd(self.genislik, self.yukseklik) or 1
        return f"{self.genislik // g}:{self.yukseklik // g}"


def video_bilgi(kaynak: Path) -> VideoBilgi:
    r = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height,avg_frame_rate:format=duration",
            "-of", "json", str(kaynak),
        ],
        capture_output=True, text=True, check=True,
    )
    d = json.loads(r.stdout)
    s = d["streams"][0]
    pay, _, payda = (s.get("avg_frame_rate") or "0/1").partition("/")
    fps = float(pay) / float(payda) if float(payda or 0) else 0.0
    return VideoBilgi(
        genislik=int(s["width"]),
        yukseklik=int(s["height"]),
        sure_sn=float(d["format"]["duration"]),
        fps=round(fps, 3),
    )


def esit_kareler(kaynak: Path, hedef_dizin: Path, adet: int) -> list[Path]:
    """Videoyu `adet` esit dilime bolup her dilimin ortasindan kare cikarir.

    Panel planlamasi icin kullanilir: N kare -> N panel.
    """
    bilgi = video_bilgi(kaynak)
    hedef_dizin.mkdir(parents=True, exist_ok=True)
    dilim = bilgi.sure_sn / adet
    yollar: list[Path] = []

    for i in range(adet):
        an = dilim * i + dilim / 2
        cikti = hedef_dizin / f"kare{i + 1:02d}.jpg"
        subprocess.run(
            [
                "ffmpeg", "-nostdin", "-loglevel", "error", "-y",
                "-ss", f"{an:.3f}", "-i", str(kaynak),
                "-frames:v", "1", "-q:v", "3", str(cikti),
            ],
            check=True, capture_output=True,
        )
        yollar.append(cikti)
    return yollar


def kontakt_sayfa(
    kareler: list[Path], cikti: Path, sutun: int = 4, hucre_gen: int = 300
) -> Path:
    """Kareleri numarali tek bir izgara goruntusunde birlestirir.

    ffmpeg concat demuxer'i sabit goruntu girdisinde framerate istedigi icin
    Pillow kullaniliyor - hem daha az kirilgan hem panel numarasi yazabiliyor.
    """
    from PIL import Image, ImageDraw

    cikti.parent.mkdir(parents=True, exist_ok=True)
    gorseller = [Image.open(k).convert("RGB") for k in kareler]
    o_gen, o_yuk = gorseller[0].size
    hucre_yuk = round(hucre_gen * o_yuk / o_gen)
    satir = (len(gorseller) + sutun - 1) // sutun
    bosluk, ust_bant = 8, 26

    tuval = Image.new(
        "RGB",
        (sutun * hucre_gen + (sutun + 1) * bosluk,
         satir * (hucre_yuk + ust_bant) + (satir + 1) * bosluk),
        "white",
    )
    ciz = ImageDraw.Draw(tuval)
    for i, g in enumerate(gorseller):
        s, k = divmod(i, sutun)
        x = bosluk + k * (hucre_gen + bosluk)
        y = bosluk + s * (hucre_yuk + ust_bant + bosluk)
        ciz.text((x + 2, y + 4), f"{i + 1:02d}", fill="black")
        tuval.paste(g.resize((hucre_gen, hucre_yuk), Image.LANCZOS), (x, y + ust_bant))
    tuval.save(cikti, quality=88)
    return cikti
