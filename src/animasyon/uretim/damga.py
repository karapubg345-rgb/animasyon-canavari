"""Yanik damga (panel numarasi / yazi) tespiti, temizligi ve prompt denetimi.

NEDEN VAR: storyboard sayfasi Seedance'a REFERANS olarak veriliyor. Referans
goruntudeki her yanik iz - ozellikle panel kosesindeki numara - video karelerine
kopyalaniyor. 2026-09-11'de uretilen 30sn'lik is bastan sona sol ust kose
rakamiyla cikti ve ~26 saatlik kuyruk bosa gitti. Tam vaka: docs/damga_tuzagi.md

Uc katmanli savunma, en gucluden en zayifa:
  1. promptu_denetle()   - deterministik. Damga isteyen ifade prompta hic girmesin.
  2. goruntuyu_denetle() - sezgisel. Yuklemeden ONCE referansta damga ara.
  3. videoyu_denetle()   - sezgisel. Uretimden SONRA sonucu dogrula.

2 ve 3 sezgiseldir: parlak/kompakt leke arar, "yazi" okumaz. Bu yuzden her bulgu
icin kanit PNG'si yazilir - karar gozle verilir, sayiya guvenilmez.
"""
from __future__ import annotations

import io
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image

# Prompta asla girmemesi gereken kaliplar. Storyboard sayfasina damga bastiran
# ifadeler; kucuk harfe cevrilmis metinde aranir.
YASAKLI_KALIPLAR = (
    "panel number",
    "number in its top-left",
    "number in the top-left",
    "number in its corner",
    "numbered panel",
    "label each panel",
    "write the panel",
    "panel numbering",
    "show a small number",
    "timecode",
)

# Damganin arandigi kose kutusu, kare boyutunun orani olarak (sol ust).
# Olculen gercek damga (720x1280 video): x 0-101, y 4-93 -> %14 x %7.
# ROI bunun ~2.5 kati tutuluyor ki model damgayi biraz kaydirdiginda da yakalansin.
KOSE_ORANI = (0.35, 0.18)


@dataclass
class Bulgu:
    """Bir damga suphesi. kanit her zaman yazilir - karar gozle verilir."""

    yer: str                      # "panel 7" / "t=12s"
    kutu: tuple[int, int, int, int]
    parlak_oran: float
    kanit: Path | None = None

    def __str__(self) -> str:
        return (
            f"{self.yer}: kutu={self.kutu} parlak_oran={self.parlak_oran:.1%}"
            + (f" kanit={self.kanit.name}" if self.kanit else "")
        )


@dataclass
class Rapor:
    bulgular: list[Bulgu] = field(default_factory=list)
    prompt_ihlalleri: list[str] = field(default_factory=list)

    @property
    def temiz(self) -> bool:
        return not self.bulgular and not self.prompt_ihlalleri


def karar(bulgu_sayisi: int, ornek_sayisi: int) -> str:
    """Bulgu yogunlugunu "TEMIZ" / "SUPHE" / "DAMGA" kararina cevirir.

    Esik olculerek secildi, tahminle degil. Bu depodaki tum storyboard'lar ve
    iki video uzerinde:
        damgali sayfa   7-12 / 12 panel        damgali video  10/10 kare
        damgasiz sayfa  0-2  / 12 panel        temiz video     0/10 kare
    Aradaki bosluk genis; ornek sayisinin %25'i iki kumeyi ayiriyor. Tek tuk
    bulgu yanlis alarm olabilir (parlak fayans, ayna kenari) ama yine de
    durdurur: 10 saniyelik goz kontrolu, saatlerce kuyruktan ucuz.
    """
    if not bulgu_sayisi:
        return "TEMIZ"
    return "DAMGA" if bulgu_sayisi >= max(2, round(ornek_sayisi * 0.25)) else "SUPHE"


# Kalibi OLUMSUZLAYAN belirtecler. "no panel numbers" bir damga TALEBI degil,
# tam tersi - yasak cumlesinin kendisi. Ayni sekilde AVOID/negatif prompt
# listesinde gecen "panel number" bir istek degil, yasak. Bunlar ayirt
# edilmezse duzeltilmis prompt kendi yasagi yuzunden ihlal sayiliyor.
OLUMSUZLAMA = ("no ", "not ", "never ", "without ", "avoid", "don't", "do not")


# --------------------------------------------------------------- 1) prompt
def promptu_denetle(metin: str) -> list[str]:
    """Prompt'ta damga ISTEYEN ifade var mi. Deterministik - sezgisel degil.

    Tek gercek garanti bu: model olmayan bir seyi kopyalayamaz. Sezgisel
    goruntu/video taramalari yalnizca bu katmanin kacirdigini yakalar.
    """
    kucuk = metin.lower()
    bulunan: list[str] = []
    for kalip in YASAKLI_KALIPLAR:
        bas = 0
        while (i := kucuk.find(kalip, bas)) != -1:
            # Baglam SATIR/CUMLE basindan alinir, sabit karakter penceresinden
            # degil: "AVOID: ..., logo, panel number" gibi uzun yasak listelerinde
            # olumsuzlama belirteci satirin ta basinda duruyor.
            kok = max(kucuk.rfind("\n", 0, i), kucuk.rfind(". ", 0, i)) + 1
            if not any(o in kucuk[kok:i] for o in OLUMSUZLAMA):
                bulunan.append(kalip)
                break
            bas = i + len(kalip)
    return bulunan


# ------------------------------------------------------- sezgisel cekirdek
def _persentil(gri: Image.Image, oran: float) -> int:
    """Gri goruntunun verilen persentildeki parlaklik degeri (numpy'siz)."""
    hist = gri.histogram()
    hedef = sum(hist) * oran
    birikim = 0
    for deger, adet in enumerate(hist):
        birikim += adet
        if birikim >= hedef:
            return deger
    return 255


def _bilesenler(maske: Image.Image) -> list[tuple[int, tuple[int, int, int, int]]]:
    """Maskedeki tum BAGLI bilesenleri (alan, bbox) olarak dondurur.

    Bilesen analizi sart, ve "en buyuk bileseni" almak da yetmiyor: ROI'de
    panelin kendi parlak dikey kenari (ayna cercevesi, gutter kalintisi) damgadan
    daha buyuk bir bilesen olusturuyor ve gercek rakami golgeliyordu. Bileşenlerin
    HEPSI ayri ayri "rakam profiline" gore elenir.
    """
    w, h = maske.size
    piksel = maske.load()
    gorulen = bytearray(w * h)
    bulunan: list[tuple[int, tuple[int, int, int, int]]] = []

    for by in range(h):
        for bx in range(w):
            if not piksel[bx, by] or gorulen[by * w + bx]:
                continue
            yigin = [(bx, by)]
            gorulen[by * w + bx] = 1
            alan = 0
            x0 = x1 = bx
            y0 = y1 = by
            while yigin:
                x, y = yigin.pop()
                alan += 1
                x0, x1 = min(x0, x), max(x1, x)
                y0, y1 = min(y0, y), max(y1, y)
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < w and 0 <= ny < h and piksel[nx, ny]:
                        i = ny * w + nx
                        if not gorulen[i]:
                            gorulen[i] = 1
                            yigin.append((nx, ny))
            bulunan.append((alan, (x0, y0, x1 + 1, y1 + 1)))
    return bulunan


def _rakam_gibi(alan: int, bb: tuple[int, int, int, int], w: int, h: int) -> bool:
    """Bilesen bir HANE'ye benziyor mu.

    Olculen gercek damgalar (storyboard 1K sayfa ve 720p video) bu bandin
    ortasinda duruyor; gutter seritleri yukseklik/en-boy, sahne parlamalari ise
    alan ve doluluk kriterinde eleniyor.
    """
    gen, yuk = bb[2] - bb[0], bb[3] - bb[1]
    if not gen or not yuk:
        return False
    return (
        0.004 <= alan / (w * h) <= 0.15          # gurultu degil, sahne de degil
        and 0.04 <= gen / w <= 0.55              # hane dardir
        and 0.12 <= yuk / h <= 0.72              # ama ROI'yi bastan basa kesmez
        and 0.7 <= yuk / gen <= 5.0              # dikey dikdortgen
        and 0.20 <= alan / (gen * yuk) <= 0.95   # harf govdesi; ne sacak ne dolu blok
    )


def _leke_ara(roi: Image.Image, esik_fark: int = 70) -> tuple[tuple, float] | None:
    """ROI'de hane profiline uyan parlak bir bilesen var mi.

    Damga neredeyse saf beyaz ve arka plandan kopuk: piksel esigi
    max(215, medyan + esik_fark). Cok haneli damgada ("24") her hane ayri
    bilesendir, birinin gecmesi yeterli - en genis olani raporlanir.
    """
    gri = roi.convert("L")
    alan = gri.width * gri.height
    if not alan:
        return None
    esik = max(215, _persentil(gri, 0.50) + esik_fark)
    maske = gri.point(lambda v: 255 if v >= esik else 0)

    adaylar = [
        (a, bb) for a, bb in _bilesenler(maske)
        if _rakam_gibi(a, bb, gri.width, gri.height)
    ]
    if not adaylar:
        return None
    en_iyi = max(adaylar, key=lambda t: t[0])
    return en_iyi[1], en_iyi[0] / alan


def _beyaz_bloklar(profil: list[float], esik: int = 225) -> list[tuple[int, int]]:
    """Profildeki ardisik "beyaz" araliklari dondurur (gutter ve sayfa kenarlari)."""
    bloklar: list[tuple[int, int]] = []
    bas = None
    for i, v in enumerate(profil):
        if v >= esik and bas is None:
            bas = i
        elif v < esik and bas is not None:
            bloklar.append((bas, i))
            bas = None
    if bas is not None:
        bloklar.append((bas, len(profil)))
    return bloklar


def _eksen_profili(gri: Image.Image, dikey: bool) -> list[float]:
    """Sutun (dikey=True) veya satir ortalama parlakliklari."""
    w, h = gri.size
    px = gri.load()
    if dikey:
        return [sum(px[x, y] for y in range(h)) / h for x in range(w)]
    return [sum(px[x, y] for x in range(w)) / w for y in range(h)]


def panel_kutulari(im: Image.Image, sutun: int, satir: int) -> list[tuple[int, int, int, int]]:
    """Panel kutularini GUTTER'lardan olcerek dondurur, okuma sirasinda.

    Esit bolme ise yaramiyor: model gutter'lari tam esit birakmiyor ve sayfa
    2'de ustte siyah bir letterbox seridi vardi - hiza kayinca ROI gutter'in
    uzerine binip beyaz serit ile rakami tek bilesen yapiyordu, damga da
    "yayilmis parlaklik" diye eleniyordu. Beyaz gutter'lar dogrudan olculuyor.

    Beklenen sayida ayrac bulunamazsa esit bolmeye duser ve pay birakir -
    bozuk bir olcumle sessizce yanlis kutu uretmektense kaba ama guvenli kutu.
    """
    gri = im.convert("L")
    kutular: list[tuple[int, int]] = []
    for eksen, adet in ((True, sutun), (False, satir)):
        bloklar = _beyaz_bloklar(_eksen_profili(gri, eksen))
        uzunluk = im.width if eksen else im.height
        if len(bloklar) == adet + 1:                       # kenarlar + ic ayraclar
            sinirlar = [(bloklar[i][1], bloklar[i + 1][0]) for i in range(adet)]
        else:
            adim = uzunluk / adet
            pay = adim * 0.08
            sinirlar = [(int(i * adim + pay), int((i + 1) * adim - pay)) for i in range(adet)]
        kutular.append(sinirlar)  # type: ignore[arg-type]

    x_sinir, y_sinir = kutular  # type: ignore[misc]
    return [(x0, y0, x1, y1) for (y0, y1) in y_sinir for (x0, x1) in x_sinir]


def _kose_roi(im: Image.Image) -> Image.Image:
    w = max(1, int(im.width * KOSE_ORANI[0]))
    h = max(1, int(im.height * KOSE_ORANI[1]))
    return im.crop((0, 0, w, h))


# ------------------------------------------------------------- 2) goruntu
def goruntuyu_denetle(
    png: Path, sutun: int = 6, satir: int = 2, kanit_dizini: Path | None = None
) -> list[Bulgu]:
    """Storyboard sayfasinin HER PANELININ sol ust kosesinde damga arar.

    Yuklemeden once calistirilir. Bir panelde bile damga varsa o sayfa
    Seedance'a verilmez - referanstaki iz videoya gecer.
    """
    im = Image.open(png).convert("RGB")
    kanit_dizini = kanit_dizini or png.parent / "damga_kanit"
    bulgular: list[Bulgu] = []

    for n, kutu in enumerate(panel_kutulari(im, sutun, satir), start=1):
        roi = _kose_roi(im.crop(kutu))
        sonuc = _leke_ara(roi)
        if sonuc is None:
            continue
        bb, oran = sonuc
        kanit_dizini.mkdir(parents=True, exist_ok=True)
        yol = kanit_dizini / f"{png.stem}_panel{n:02d}.png"
        roi.resize((roi.width * 3, roi.height * 3), Image.LANCZOS).save(yol)
        bulgular.append(Bulgu(f"{png.name} panel {n}", bb, oran, yol))
    return bulgular


# ---------------------------------------------------------------- 3) video
def _ffmpeg() -> str:
    yol = shutil.which("ffmpeg")
    if not yol:
        raise SystemExit("ffmpeg bulunamadi - video denetimi ve temizligi ffmpeg istiyor.")
    return yol


def _kare_al(video: Path, saniye: int, kirp: str | None = None) -> Image.Image | None:
    vf = ["-vf", kirp] if kirp else []
    p = subprocess.run(
        [_ffmpeg(), "-hide_banner", "-loglevel", "error", "-ss", str(saniye),
         "-i", str(video), *vf, "-frames:v", "1", "-f", "image2pipe",
         "-vcodec", "png", "-"],
        capture_output=True,
    )
    return Image.open(io.BytesIO(p.stdout)) if p.stdout else None


def video_suresi(video: Path) -> float:
    p = subprocess.run(
        ["ffprobe", "-hide_banner", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
        capture_output=True, text=True,
    )
    try:
        return float(p.stdout.strip())
    except ValueError:
        return 0.0


def videoyu_denetle(
    video: Path, adim_sn: int = 1, kanit_dizini: Path | None = None
) -> list[Bulgu]:
    """Videonun sol ust kosesini adim_sn araliklarla tarar.

    Uretimden sonra calistirilir. Damga genelde TUM kareler boyunca durur, bu
    yuzden 1sn'lik ornekleme yeterli - tek kare kacsa bile digerleri yakalar.
    """
    sure = video_suresi(video)
    kanit_dizini = kanit_dizini or video.parent / "damga_kanit"
    bulgular: list[Bulgu] = []
    for t in range(0, int(sure), max(1, adim_sn)):
        kare = _kare_al(video, t)
        if kare is None:
            continue
        roi = _kose_roi(kare.convert("RGB"))
        sonuc = _leke_ara(roi)
        if sonuc is None:
            continue
        bb, oran = sonuc
        kanit_dizini.mkdir(parents=True, exist_ok=True)
        yol = kanit_dizini / f"{video.stem}_t{t:03d}.png"
        roi.resize((roi.width * 3, roi.height * 3), Image.LANCZOS).save(yol)
        bulgular.append(Bulgu(f"{video.name} t={t}s", bb, oran, yol))
    return bulgular


def damga_kutusu(video: Path, adim_sn: int = 1, pay: int = 8) -> tuple[int, int, int, int] | None:
    """Damganin TUM video boyunca kapladigi birlesik kutu (x, y, w, h).

    Temizlik kutusu tek kareden cikarilamaz: model damgayi her kesmede birkac
    piksel kaydiriyor. Olculen ornek: tek kare 37x50, birlesik kutu 101x89.
    """
    sure = video_suresi(video)
    bir: tuple[int, int, int, int] | None = None
    for t in range(0, int(sure), max(1, adim_sn)):
        kare = _kare_al(video, t)
        if kare is None:
            continue
        roi = _kose_roi(kare.convert("RGB"))
        sonuc = _leke_ara(roi)
        if sonuc is None:
            continue
        bb = sonuc[0]
        bir = bb if bir is None else (
            min(bir[0], bb[0]), min(bir[1], bb[1]),
            max(bir[2], bb[2]), max(bir[3], bb[3]),
        )
    if bir is None:
        return None
    x = max(0, bir[0] - pay)
    y = max(0, bir[1] - pay)
    return x, y, bir[2] - x + pay, bir[3] - y + pay


def videoyu_temizle(
    giris: Path, cikis: Path, kutu: tuple[int, int, int, int] | None = None
) -> tuple[int, int, int, int]:
    """Damgayi delogo ile siler, sesi oldugu gibi kopyalar. Kullanilan kutuyu dondurur.

    delogo kutusunun kareye TAMAMEN ic olmasi sart; x=0 veya y=0 verilince
    "Logo area is outside of the frame" ile duser. Bu yuzden kutu 1,1'den
    baslatilip kalan 1 piksellik kenar seridi fillborders=smear ile komsudan
    yayiliyor - damga kareyi kenardan kesiyorsa o serit de temizlensin.
    """
    kutu = kutu or damga_kutusu(giris)
    if kutu is None:
        raise SystemExit(f"{giris.name}: damga bulunamadi, temizlenecek bir sey yok.")
    x, y, w, h = kutu
    ix, iy = max(1, x), max(1, y)
    iw, ih = w + (x - ix), h + (y - iy)
    subprocess.run(
        [_ffmpeg(), "-hide_banner", "-loglevel", "error", "-i", str(giris),
         "-vf", f"delogo=x={ix}:y={iy}:w={iw}:h={ih},"
                "fillborders=left=1:top=1:mode=smear",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-pix_fmt", "yuv420p", "-c:a", "copy", str(cikis), "-y"],
        check=True,
    )
    return kutu
