"""animasyon pipeline CLI.

Kullanim: PYTHONPATH=src ./.venv/Scripts/python.exe -m animasyon <komut>
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import yaml

KOK = Path(__file__).resolve().parents[2]


def konf(ad: str) -> dict:
    return yaml.safe_load((KOK / "config" / f"{ad}.yaml").read_text(encoding="utf-8"))


def kadro_yukle(ad: str = "ornek") -> dict:
    p = KOK / "karakterlerim" / ad / "kadro.yaml"
    if not p.exists():
        raise SystemExit(f"Kadro bulunamadi: {p}")
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def hafta_etiketi(t: dt.date | None = None) -> str:
    t = t or dt.date.today()
    y, h, _ = t.isocalendar()
    return f"{y}-W{h:02d}"


def is_dizini(kod: str, hafta: str | None = None) -> Path:
    return KOK / "isler" / (hafta or hafta_etiketi()) / kod


def _aday_kaydet(a, dizin: Path) -> None:
    dizin.mkdir(parents=True, exist_ok=True)
    (dizin / "meta.json").write_text(
        json.dumps(
            {
                "kisa_kod": a.kisa_kod,
                "url": a.url,
                "video_url": a.video_url,
                "izlenme": a.izlenme,
                "begeni": a.begeni,
                "sure_sn": a.sure_sn,
                "sahip": a.sahip,
                "aciklama": a.aciklama,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


# ---------------------------------------------------------------- komutlar


def _sure_plani_yaz(p: dict, sure_sn: float) -> None:
    """Kaynak suresinden uretim planini hesaplar ve ekrana yazar.

    Seedance 2.5 ile 30sn'ye kadar BOLUNMEDEN uretiliyor; 15sn ustu isler cok
    sayfali storyboard yoluna giriyor. bkz. docs/seedance_2_5.md
    """
    from animasyon.uyarlama.sureleme import SureHatasi, plan_yap

    try:
        plan = plan_yap(p, sure_sn)
    except SureHatasi as e:
        print(f"  UYARI: plan cikarilamadi - {e}")
        return
    print(f"  Plan: {plan.ozet()}")
    if plan.bolunmeli:
        ust = p["seedance_2_5"]["sure_araligi_sn"][1]
        print(
            f"  UYARI: kaynak {sure_sn:.1f}s > {ust}s. Seedance 2.5 en fazla "
            f"{ust}s uretiyor; yapi birden fazla videoya BOLUNMELI."
        )
    elif plan.sayfa > 1:
        print(
            f"  NOT: 15s ustu is -> {plan.sayfa} storyboard sayfasi uretilecek, "
            f"panel numaralari global (1..{plan.panel})."
        )


def cmd_apify_kota(_a) -> int:
    from animasyon.kesif import kota_getir

    k = kota_getir()
    esik = konf("pipeline")["kredi"]["apify_min_kalan_usd"]
    print(f"  Kalan      : ${k.kalan_usd:.4f}")
    print(f"  Kullanilan : ${k.kullanilan_usd:.4f}")
    print(f"  Aylik limit: ${k.limit_usd:.2f}")
    print(f"  Donem sonu : {k.donem_sonu}")
    if k.kalan_usd < esik:
        print(f"\n  YETERSIZ (esik ${esik}) - run baslatilmamali.")
        return 1
    print(f"\n  Yeterli (esik ${esik}).")
    return 0


def cmd_karakterler(a) -> int:
    kadro = kadro_yukle(a.kadro)
    kok = KOK / "karakterlerim" / a.kadro
    print(f"Kadro: {kadro['kadro_adi']} - {kadro.get('aciklama', '')}\n")
    eksik = 0
    for c in kadro["karakterler"].values():
        var = (kok / c["referans_dosya"]).exists()
        eksik += not var
        # Referans, asagida varligi denetlenen model sheet dosyasidir.
        print(
            f"  [{'OK ' if var else 'EKSIK'}] {c['ad']:8s} {c['rol']:20s} "
            f"yas {c['yas_araligi']:6s} {c['referans_dosya']}"
        )
    print(f"\n  {len(kadro['karakterler'])} karakter, {eksik} eksik dosya.")
    print("  Referanslar uretim platformuna DOSYA olarak yuklenir; yukleme sirasi @ImageN'i belirler.")
    return 1 if eksik else 0


def cmd_ekle(a) -> int:
    """Kullanicinin verdigi Instagram linkinden is olusturur."""
    from animasyon.indirme.indirici import IndirmeHatasi, video_indir
    from animasyon.kesif import GecersizLink, linkten_aday

    p = konf("pipeline")
    try:
        aday = linkten_aday(a.url, min_kalan=p["kredi"]["apify_min_kalan_usd"])
    except GecersizLink as e:
        print(f"HATA: {e}")
        return 1

    dizin = is_dizini(aday.kisa_kod, a.hafta)
    _aday_kaydet(aday, dizin)
    print(f"  {aday.kisa_kod}  @{aday.sahip}  izl={aday.izlenme:,}  {aday.sure_sn:.1f}s")

    _sure_plani_yaz(p, aday.sure_sn)

    hedef = dizin / "kaynak.mp4"
    if hedef.exists():
        print(f"  Zaten indirilmis: {hedef}")
        return 0
    try:
        v = video_indir(aday.video_url, hedef)
        print(f"  Indirildi: {v}  ({v.stat().st_size / 1048576:.2f} MB)")
    except IndirmeHatasi as e:
        print(f"  INDIRME HATASI: {e}")
        return 1
    return 0


def cmd_kesif(a) -> int:
    from animasyon.indirme.indirici import IndirmeHatasi, video_indir
    from animasyon.kesif import actor_calistir, filtrele, kota_getir

    p = konf("pipeline")
    k = p["kesif"]
    once = kota_getir()
    girdi = {
        "hashtags": k["aramalar"],
        "keywordSearch": k["keyword_arama"],
        "resultsType": "reels",
        "resultsLimit": k["sonuc_limiti"],
    }
    if a.kuru_calisma:
        print(f"[kuru] Apify girdisi: {json.dumps(girdi, ensure_ascii=False)}")
        print(f"[kuru] Tahmini maliyet: ${0.006 + len(k['aramalar']) * k['sonuc_limiti'] * 0.0011:.4f}")
        return 0

    ogeler = actor_calistir(k["actor"], girdi, min_kalan=p["kredi"]["apify_min_kalan_usd"])
    sonra = kota_getir()
    print(f"Ham oge: {len(ogeler)}  harcanan ${once.kalan_usd - sonra.kalan_usd:.4f}  kalan ${sonra.kalan_usd:.4f}")

    adaylar = filtrele(
        ogeler,
        min_izlenme=k["min_izlenme"],
        min_begeni=k["min_begeni"],
        sure_araligi=tuple(k["sure_araligi_sn"]),
    )
    limit = a.limit or k["haftalik_hedef"]
    secilen = adaylar[:limit]
    print(f"Esikleri gecen: {len(adaylar)} / {len(ogeler)}   secilen: {len(secilen)}\n")

    for i, ad in enumerate(secilen, 1):
        dizin = is_dizini(ad.kisa_kod, a.hafta)
        _aday_kaydet(ad, dizin)
        durum = ""
        if a.indir:
            hedef = dizin / "kaynak.mp4"
            if hedef.exists():
                durum = "zaten var"
            else:
                try:
                    video_indir(ad.video_url, hedef)
                    durum = f"{hedef.stat().st_size / 1048576:.1f} MB"
                except IndirmeHatasi as e:
                    durum = f"HATA {e}"
        print(
            f"{i:2d}. {ad.kisa_kod:13s} izl={ad.izlenme:>11,} or={ad.etkilesim_orani:5.1%} "
            f"{ad.sure_sn:5.1f}s @{ad.sahip[:18]:18s} {durum}"
        )
    return 0


def _is_bul(kod: str, hafta: str | None) -> Path:
    """Isi hafta verilmeden de bulur - kod benzersiz, hafta ezberlemeye gerek yok."""
    if hafta:
        d = is_dizini(kod, hafta)
        if not d.is_dir():
            raise SystemExit(f"Is bulunamadi: {d}")
        return d
    adaylar = sorted((KOK / "isler").glob(f"*/{kod}"))
    if not adaylar:
        raise SystemExit(f"Is bulunamadi: {kod}")
    return adaylar[-1]


def cmd_dogrula(a) -> int:
    """Damga denetimi: prompt + storyboard referanslari + (varsa) uretilen video.

    Video uretimine girmeden ONCE calistirilmasi gereken kapi. Referansta damga
    varsa is baslatilmaz - kuyruk saatler suruyor ve bozuk cikti o sureyi yakiyor
    (olculen: 26 saat). Gerekce ve vaka: docs/damga_tuzagi.md
    """
    from animasyon.uretim import damga

    dizin = _is_bul(a.kod, a.hafta)
    print(f"Is: {dizin.relative_to(KOK)}\n")
    kusur = 0

    # 1) prompt - deterministik katman
    promptlar = sorted(dizin.glob("prompt_*.txt"))
    for p in promptlar:
        ihlal = damga.promptu_denetle(p.read_text(encoding="utf-8"))
        if ihlal:
            kusur += 1
            print(f"  [IHLAL] {p.name}: damga isteyen ifade -> {', '.join(ihlal)}")
        else:
            print(f"  [OK   ] {p.name}")
    if not promptlar:
        print("  [ATLA ] prompt_*.txt yok")

    # 2) Seedance'a gidecek referanslar - "_denetim" ekli dosya asla yuklenmez
    t = konf("pipeline")["storyboard"]
    # Tek sayfali eski isler "storyboard.png" adini kullaniyor; ikisi de taranir.
    sayfalar = sorted(
        s for s in dizin.glob("storyboard*.png") if "_denetim" not in s.stem
    )
    panel = t["sutun"] * t["satir"]
    for s in sayfalar:
        bulgular = damga.goruntuyu_denetle(s, t["sutun"], t["satir"])
        k = damga.karar(len(bulgular), panel)
        kusur += k != "TEMIZ"
        ek = " - YUKLEME" if k == "DAMGA" else ""
        print(f"  [{k:5s}] {s.name}: {len(bulgular)}/{panel} panel{ek}")
        for b in bulgular[:4]:
            print(f"            {b}")
        if len(bulgular) > 4:
            print(f"            ... +{len(bulgular) - 4} panel")
    if not sayfalar:
        print("  [ATLA ] storyboard*.png yok")

    # 3) uretilen video - sonucun kendisi
    videolar = sorted(v for v in dizin.glob("video_*.mp4") if v.stem != "video_temiz")
    for v in videolar:
        bulgular = damga.videoyu_denetle(v, a.adim)
        ornek = max(1, int(damga.video_suresi(v)) // max(1, a.adim))
        k = damga.karar(len(bulgular), ornek)
        kusur += k != "TEMIZ"
        print(f"  [{k:5s}] {v.name}: {len(bulgular)}/{ornek} kare")
        for b in bulgular[:4]:
            print(f"            {b}")
        if len(bulgular) > 4:
            print(f"            ... +{len(bulgular) - 4} kare")
        if k == "DAMGA":
            print(f"            temizlemek icin: temizle {a.kod}")
    if not videolar:
        print("  [ATLA ] video_*.mp4 yok")

    if kusur:
        print(f"\n  {kusur} kusur. Kanit PNG'leri: damga_kanit/ - GOZLE dogrula.")
        print("  Sezgisel tarayici: parlak kompakt leke arar, yaziyi okumaz.")
        return 1
    print("\n  Temiz.")
    return 0


def cmd_temizle(a) -> int:
    """Yanik damgayi delogo ile siler. Ham dosyaya dokunmaz."""
    from animasyon.uretim import damga

    dizin = _is_bul(a.kod, a.hafta)
    giris = dizin / a.dosya
    if not giris.is_file():
        raise SystemExit(f"Video yok: {giris}")
    cikis = dizin / "video_temiz.mp4"
    kutu = damga.videoyu_temizle(giris, cikis)
    print(f"  Damga kutusu : x={kutu[0]} y={kutu[1]} w={kutu[2]} h={kutu[3]}")
    print(f"  Yazildi      : {cikis.relative_to(KOK)}")
    kalan = damga.videoyu_denetle(cikis, a.adim)
    print(f"  Dogrulama    : {'TEMIZ' if not kalan else f'{len(kalan)} karede iz kaldi'}")
    return 1 if kalan else 0


def cmd_denetim_kopyasi(a) -> int:
    """Storyboard sayfalarinin numarali denetim kopyasini uretir (yuklenmez)."""
    from animasyon.uyarlama.denetim_kopyasi import denetim_kopyasi_uret

    dizin = _is_bul(a.kod, a.hafta)
    sb = json.loads((dizin / "storyboard.json").read_text(encoding="utf-8"))
    sutun, satir = sb["tuval"]["sutun"], sb["tuval"]["satir"]
    sayfa_panel = sutun * satir
    # Tek sayfali eski isler "storyboard.png" adini kullaniyor; ikisi de taranir.
    sayfalar = sorted(
        s for s in dizin.glob("storyboard*.png") if "_denetim" not in s.stem
    )
    if not sayfalar:
        raise SystemExit(f"storyboard*.png bulunamadi: {dizin}")
    for i, s in enumerate(sayfalar):
        dilim = sb["paneller"][i * sayfa_panel : (i + 1) * sayfa_panel]
        yol = denetim_kopyasi_uret(s, dilim, sutun, satir)
        ilk, son = dilim[0]["n"], dilim[-1]["n"]
        print(f"  {yol.name}  panel {ilk}-{son}")
    print("\n  Bu kopyalar YALNIZCA onay kapisi icin. Seedance'a temiz sayfalar yuklenir.")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="animasyon")
    alt = p.add_subparsers(dest="komut", required=True)

    alt.add_parser("apify-kota", help="Apify kalan kredisi").set_defaults(f=cmd_apify_kota)

    k = alt.add_parser("karakterler", help="Kadroyu dogrula")
    k.add_argument("--kadro", default="ornek")
    k.set_defaults(f=cmd_karakterler)

    e = alt.add_parser("ekle", help="Instagram linkinden is olustur")
    e.add_argument("url")
    e.add_argument("--hafta", default=None)
    e.set_defaults(f=cmd_ekle)

    d = alt.add_parser("kesif", help="Otomatik haftalik kesif")
    d.add_argument("--limit", type=int, default=None)
    d.add_argument("--indir", action="store_true", help="Adaylari indir")
    d.add_argument("--kuru-calisma", action="store_true", dest="kuru_calisma")
    d.add_argument("--hafta", default=None)
    d.set_defaults(f=cmd_kesif)

    g = alt.add_parser("dogrula", help="Damga denetimi (prompt + referans + video)")
    g.add_argument("kod")
    g.add_argument("--hafta", default=None)
    g.add_argument("--adim", type=int, default=1, help="Video ornekleme araligi (sn)")
    g.set_defaults(f=cmd_dogrula)

    t = alt.add_parser("temizle", help="Videodaki yanik damgayi delogo ile siler")
    t.add_argument("kod")
    t.add_argument("--hafta", default=None)
    t.add_argument("--dosya", default="video_ham.mp4")
    t.add_argument("--adim", type=int, default=1)
    t.set_defaults(f=cmd_temizle)

    n = alt.add_parser("denetim-kopyasi", help="Storyboard'un numarali denetim kopyasi")
    n.add_argument("kod")
    n.add_argument("--hafta", default=None)
    n.set_defaults(f=cmd_denetim_kopyasi)

    a = p.parse_args(argv)
    return a.f(a)


if __name__ == "__main__":
    sys.exit(main())
