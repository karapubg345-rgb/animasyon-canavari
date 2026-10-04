"""Storyboard grid ve Seedance 2.5 video promptlarini uretir.

Seedance 2.5 tek geciste 30sn uretiyor. 15sn ustu islerde panel YOGUNLUGU
artmaz, storyboard SAYFA sayisi artar (6x2 grid sabit) - gerekce ve sert
sinirlar: docs/seedance_2_5.md
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml


def _yukle(p: Path) -> dict:
    return (
        json.loads(p.read_text(encoding="utf-8"))
        if p.suffix == ".json"
        else yaml.safe_load(p.read_text(encoding="utf-8"))
    )


class PromptUretici:
    def __init__(self, is_dizini: Path, kok: Path):
        self.dizin = is_dizini
        self.kok = kok
        self.sb = _yukle(is_dizini / "storyboard.json")
        self.kadro = _yukle(kok / "karakterlerim" / self.sb["kadro"] / "kadro.yaml")
        self.stil = _yukle(kok / "config" / "stil.yaml")
        # kiyafet_seti opsiyonel. Bos string'i is_dizini ile birlestirmek dizinin
        # KENDISINI verir (Path / "" == Path), bu yuzden once konf degeri kontrol
        # edilir - yoksa dizin dosya gibi okunmaya calisiliyor.
        ks = (self.sb.get("kiyafet_seti") or "").strip()
        kp = is_dizini / ks if ks else None
        self.kiyafet = _yukle(kp) if kp and kp.is_file() else {}

    # ---- sayfalama: 15sn ustu isler cok sayfali storyboard kullanir ----
    @property
    def sayfa_sayisi(self) -> int:
        return int(self.sb["tuval"].get("sayfa_sayisi", 1))

    @property
    def sayfa_panel(self) -> int:
        """Sayfa basina panel sayisi. Grid 6x2 sabit oldugu icin normalde 12."""
        return self.sb["tuval"]["sutun"] * self.sb["tuval"]["satir"]

    def sayfa_panelleri(self, sayfa: int) -> list[dict]:
        """Verilen sayfaya dusen panelleri dondurur. Panel no'lari GLOBAL kalir."""
        if not 1 <= sayfa <= self.sayfa_sayisi:
            raise ValueError(f"sayfa {sayfa} aralik disi (1..{self.sayfa_sayisi})")
        n = self.sayfa_panel
        return self.sb["paneller"][(sayfa - 1) * n : sayfa * n]

    @property
    def oran(self) -> str:
        return self.sb["video"].get("oran", "9:16")

    @property
    def yon(self) -> str:
        """Oranin Ingilizce yonu: "9:16" -> vertical, "16:9" -> horizontal."""
        g, y = (float(x) for x in self.oran.split(":"))
        return "vertical" if y > g else "horizontal" if g > y else "square"

    # ---- bolumler: 30sn ustu is sayfalari ikiser gruplanip ayri uretilir ----
    @property
    def bolumler(self) -> list[dict]:
        """Bolum listesi. plan.json (ekle yazar) varsa oradan, yoksa ikiser sayfa."""
        pj = self.dizin / "plan.json"
        if pj.is_file():
            b = json.loads(pj.read_text(encoding="utf-8")).get("bolumler") or []
            if b and b[-1]["sayfa_son"] == self.sayfa_sayisi:
                return b
        return [
            {"no": i // 2 + 1, "sayfa_ilk": i + 1, "sayfa_son": min(i + 2, self.sayfa_sayisi)}
            for i in range(0, self.sayfa_sayisi, 2)
        ]

    def _bolum(self, no: int | None) -> dict | None:
        if no is None:
            return None
        b = next((x for x in self.bolumler if x["no"] == no), None)
        if b is None:
            raise ValueError(f"bolum {no} yok (1..{len(self.bolumler)})")
        return b

    def _bolum_sayfalari(self, bolum: dict | None) -> list[int]:
        if bolum is None:
            return list(range(1, self.sayfa_sayisi + 1))
        return list(range(bolum["sayfa_ilk"], bolum["sayfa_son"] + 1))

    @staticmethod
    def _goreli_zaman(zaman: str, bas: float) -> str:
        """Global "31.25-32.50" araligini bolum basina gore kaydirir."""
        a, b = (float(x) - bas for x in zaman.split("-"))
        return f"{a:.2f}-{b:.2f}"

    @staticmethod
    def _zaman_araligi(paneller: list[dict]) -> tuple[str, str]:
        """Panel dizisinin ilk basi ve son sonu ("0.00", "15.00")."""
        return paneller[0]["zaman"].split("-")[0], paneller[-1]["zaman"].split("-")[-1]

    # ---- karakter tanimi: kimlik (sabit) + kiyafet (sahneye ozel) ----
    # ---- referans plani: yukleme sirasi @ImageN numaralarini belirler ----
    def referans_plani(self, bolum: int | None = None) -> list[dict]:
        """Uretim platformuna hangi dosyanin kacinci yuklenecegini ve etiketini dondurur.

        TUZAK: karakterler eskiden kadro.yaml'daki kalici platform ID'leriyle (`topview_ref`)
        ID'siyle prompt'a yaziliyordu. TopView bu ID'leri parse etmiyor - duz
        metin kaliyorlar ve referans hic devreye girmiyor. Yalnizca YUKLENEN
        dosyalar <<<ImageN>>> oluyor, o yuzden karakterler de storyboard
        sayfalari gibi yuklenir. Sira: once sayfalar, sonra karakterler.

        bolum verilirse (30sn ustu is) yalnizca o bolumun sayfalari ve
        karakterleri girer; 2. bolumden itibaren sona onceki bolumun son karesi
        eklenir (bolumN_son_kare.png) ki dikis yerinde sahne kopmasin.
        """
        b = self._bolum(bolum)
        sayfalar = self._bolum_sayfalari(b)
        plan: list[dict] = []
        for s in sayfalar:
            ad = (
                f"storyboard_sayfa{s}.png" if self.sayfa_sayisi > 1 else "storyboard.png"
            )
            sp = self.sayfa_panelleri(s)
            bas, son = self._zaman_araligi(sp)
            plan.append({
                "sira": len(plan) + 1,
                "etiket": f"Image{len(plan) + 1}",
                "tur": "storyboard",
                "sayfa": s,
                "dosya": ad,
                "kapsam": f"beat {sp[0]['n']}-{sp[-1]['n']} ({bas}-{son}s)",
            })
        kadro_ad = self.sb["kadro"]
        paneller = [x for s in sayfalar for x in self.sayfa_panelleri(s)]
        for cid in self.kullanilan_karakterler(paneller):
            c = self.kadro["karakterler"][cid]
            plan.append({
                "sira": len(plan) + 1,
                "etiket": f"Image{len(plan) + 1}",
                "tur": "karakter",
                "id": cid,
                "ad": c["ad"],
                "dosya": f"karakterlerim/{kadro_ad}/{c['referans_dosya']}",
            })
        if b and b["no"] > 1:
            plan.append({
                "sira": len(plan) + 1,
                "etiket": f"Image{len(plan) + 1}",
                "tur": "onceki_kare",
                "dosya": f"bolum{b['no'] - 1}_son_kare.png",
            })
        return plan

    def _kiyafet(self, cid: str) -> str:
        """Sahne kiyafeti varsa onu, yoksa kadronun varsayilan kiyafetini dondurur."""
        c = self.kadro["karakterler"][cid]
        return (
            (self.kiyafet.get("kiyafetler") or {}).get(cid) or c["varsayilan_kiyafet"]
        ).strip()

    def _kiyafet_cumlesi(self, cid: str) -> str:
        """Kiyafeti "<Ad> wears ..." cumlesine cevirir.

        Kiyafet metinleri iki bicimde yazilmis: bazilari ozneyle basliyor
        ("Daniel wears home night clothes..."), bazilari dogrudan giysiyle
        ("Navy short-sleeve pocket t-shirt..."). Onek kosulsuz eklenirse
        "Daniel wears Daniel wears ..." cikiyor.
        """
        ad = self.kadro["karakterler"][cid]["ad"]
        k = self._kiyafet(cid).rstrip(".").strip()
        return k if k.lower().startswith(ad.lower()) else f"{ad} wears {k}"

    def karakter_tanimi(self, cid: str) -> str:
        c = self.kadro["karakterler"][cid]
        parcalar = [c["kimlik_kilidi"].strip(), f"Wearing: {self._kiyafet(cid)}"]
        aks = c.get("aksesuar")
        if aks and aks.get("kalici"):
            parcalar.append(aks["aciklama"].strip())
        return " ".join(parcalar)

    def kullanilan_karakterler(self, paneller: list[dict] | None = None) -> list[str]:
        gorulen: list[str] = []
        for p in paneller if paneller is not None else self.sb["paneller"]:
            for c in p["karakterler"]:
                if c not in gorulen:
                    gorulen.append(c)
        return gorulen

    # ---- 1) storyboard grid promptu (GPT Image 2) ----
    def grid_promptu(self, sayfa: int = 1) -> str:
        t = self.sb["tuval"]
        ort = (self.kiyafet.get("ortam_override") or {})
        paneller = self.sayfa_panelleri(sayfa)
        bas, son = self._zaman_araligi(paneller)
        cok = self.sayfa_sayisi > 1
        baslik = (
            f"A single {t['oran']} storyboard sheet containing exactly "
            f"{len(paneller)} equal panels arranged in a strict "
            f"{t['sutun']}-column x {t['satir']}-row grid, thin white gutters between panels."
        )
        if cok:
            baslik += (
                f" This is sheet {sayfa} of {self.sayfa_sayisi}, covering beats "
                f"{paneller[0]['n']}-{paneller[-1]['n']} ({bas}-{son}s) of one "
                "continuous video."
            )
            # Sira bilgisi ANLATI diliyle veriliyor. Eski metin "panel numbering
            # continues..." diyordu; model bunu "panellere numara yaz" diye okuyup
            # her paneli damgaladi (docs/damga_tuzagi.md). Numaralar GLOBAL kalmaya
            # devam ediyor - ama yalnizca storyboard.json icinde, goruntude degil.
            baslik += (
                " The story is already in progress: the first panel here "
                "continues directly from the last panel of the previous sheet."
                if sayfa > 1
                else " The story continues on the next sheet; the last panel here "
                "is not the end of the video."
            )
        satirlar = [
            baslik,
            f"Each panel is a {self.yon} {self.oran} frame of the same "
            "continuous scene, in consistent stylized 3D family-animation style.",
            "",
            f"SETTING: {ort.get('mekan', '')}. {ort.get('arka_plan', '')}. "
            f"Lighting: {ort.get('isik', '')}",
            "",
            "CHARACTERS (identical appearance in every panel they appear in):",
        ]
        for cid in self.kullanilan_karakterler(paneller):
            satirlar.append(f"- {self.karakter_tanimi(cid)}")

        nesne = self._sahne_nesnesi_satiri()
        if nesne:
            satirlar += ["", nesne]

        satirlar += ["", "PANELS, in reading order (left to right, then next row):"]
        for p in paneller:
            kim = ", ".join(self.kadro["karakterler"][c]["ad"] for c in p["karakterler"]) or "no characters"
            satirlar.append(
                f"Panel {p['n']} [{p['kadraj']}, {p['kamera']}] ({kim}): {p['aksiyon']}"
            )

        satirlar += [
            "",
            f"STYLE: {self.stil['stil_blogu'].strip()}",
            # DAMGA YASAGI - kaldirma. Bu sayfa Seedance'a REFERANS olarak
            # gidiyor ve referanstaki her yanik iz video karelerine kopyalaniyor.
            # Panele numara bastiran eski satir 2026-09-11'de 30sn'lik videoyu
            # bastan sona kose damgasiyla uretti (bkz. docs/damga_tuzagi.md).
            # Panel sirasi okuma duzeninden zaten belli; numara gerekmiyor.
            self._damga_yasagi(),
            "",
            f"AVOID: {self._negatif_prompt()}",
        ]
        return "\n".join(satirlar)

    # ---- metin yasagi + dar istisna ----
    @property
    def metin_istisnasi(self) -> str:
        """Sahnenin ANLATISI bir yaziyi/rakami zorunlu kiliyorsa onun tanimi.

        Bos string varsayilan ve oyle kalmali: referansa yanan her iz video
        karelerine kopyalaniyor (docs/damga_tuzagi.md). Istisna yalnizca
        anlatinin ustunde durdugu tek bir nesne icin, is bazinda ve
        MUMKUN OLDUGU KADAR DAR yazilir - "hangi nesne, hangi panelde".
        """
        return (self.sb.get("metin_istisnasi") or "").strip()

    def _damga_yasagi(self) -> str:
        istisna = self.metin_istisnasi
        kuyruk = (
            "Panel order is conveyed by the reading order alone. This sheet is "
            "used as a reference for video generation, so any mark burned into "
            "a panel would be copied into the video frames."
        )
        if not istisna:
            return (
                "Absolutely no text anywhere in the image: no panel numbers, no "
                "digits, no letters, no captions, no labels, no speech bubbles, "
                f"no timecodes, no watermarks. {kuyruk}"
            )
        # Istisna varken "hic rakam yok" demek prompt'u kendi icinde celiskiye
        # dusuruyor; yasak korunur ama izin verilen tek yer acikca adlandirilir.
        return (
            f"The ONLY text or digits allowed anywhere in this sheet are {istisna}. "
            "That reading is part of the scene itself, printed on the object's own "
            "screen. Everywhere else the sheet is completely free of text: no panel "
            "numbers, no digits, no letters, no captions, no labels, no speech "
            f"bubbles, no timecodes, no watermarks, no corner markings. {kuyruk}"
        )

    def _negatif_prompt(self) -> str:
        """Negatif prompt. Istisna varsa onunla CELISEN maddeler cikarilir.

        Ayni prompt'ta hem "36.9 yaz" hem "numbers, digits, numerals yasak"
        demek modelin ikisini birden kaybetmesine yol aciyor. Yalnizca genel
        rakam maddeleri dusuyor; panel damgasina bakan maddeler (panel number,
        panel label, timecode, frame counter, corner marking) KALIYOR.
        """
        ham = " ".join(self.stil["negatif_prompt"].split())
        if not self.metin_istisnasi:
            return ham
        dusen = {"numbers", "digits", "numerals", "text"}
        return ", ".join(
            m for m in (p.strip().rstrip(".") for p in ham.split(","))
            if m and m.lower() not in dusen
        )

    def _sahne_nesnesi_satiri(self) -> str:
        """kiyafet.yaml -> sahne_nesnesi bloğunu prompt satirina cevirir.

        Anlatinin uzerinde durdugu nesne (termometre, alyans, cop poseti...)
        her panelde AYNI okunmak zorunda; tanim prompt'a girmezse paneller
        arasinda nesne degisiyor.
        """
        n = self.kiyafet.get("sahne_nesnesi") or {}
        tanim = (n.get("tanim_en") or "").strip()
        if not tanim:
            return ""
        kural = (n.get("kural") or "").strip()
        satir = f"KEY PROP (identical in every panel it appears in): {tanim}"
        return f"{satir} {kural}" if kural else satir

    def _ortam_ifadesi(self) -> str:
        """Sahne override'i varsa onu, yoksa kadronun varsayilan ortamini dondurur."""
        o = self.kiyafet.get("ortam_override") or {}
        mekan = o.get("mekan")
        if not mekan:
            return self.kadro["ortam"]["mekan"]
        arka = (o.get("arka_plan") or "").strip()
        return f"{mekan} with {arka}" if arka else mekan

    # ---- 2) Seedance 2.5 video promptu ----
    def video_promptu(
        self, storyboard_ref: str | list[str] | None = None, bolum: int | None = None
    ) -> str:
        """Video promptunu uretir.

        Etiketler referans_plani()'ndan gelir - yukleme sirasi @ImageN'i belirler.
        storyboard_ref artik gerekmiyor; verilirse yalnizca sayfa etiketlerini
        ezmek icin kullanilir (eski cagrilar kirilmasin diye tutuluyor).

        bolum verilirse yalnizca o bolumun promptu cikar: sayfalar bolum icinde
        1'den numaralanir, zamanlar bolum basina gore kayar, sure bolum suresidir.
        """
        b = self._bolum(bolum)
        sayfa_nolari = self._bolum_sayfalari(b)
        bpaneller = [x for s in sayfa_nolari for x in self.sayfa_panelleri(s)]
        bas_sn = float(bpaneller[0]["zaman"].split("-")[0]) if b else 0.0
        son_sn = float(bpaneller[-1]["zaman"].split("-")[-1])
        plan = self.referans_plani(bolum)
        sayfalar = [p for p in plan if p["tur"] == "storyboard"]
        karakterler = [p for p in plan if p["tur"] == "karakter"]
        onceki = next((p for p in plan if p["tur"] == "onceki_kare"), None)
        # Bolum promptunda beat'ler de 1'den sayilir: "24-panel storyboard" deyip
        # Beat 25..48 yazmak modele iki ayri numara sistemi verir.
        ilk_n = bpaneller[0]["n"] - 1 if b else 0
        if storyboard_ref is not None:
            refler = (
                [storyboard_ref] if isinstance(storyboard_ref, str) else list(storyboard_ref)
            )
            if len(refler) != len(sayfa_nolari):
                raise ValueError(
                    f"{len(sayfa_nolari)} storyboard sayfasi var, {len(refler)} referans verildi"
                )
        else:
            refler = [p["etiket"] for p in sayfalar]

        sab = _yukle(self.kok / "config" / "prompt_sablonu.yaml")
        parcalar = []
        # Karakter satirlari: her biri YUKLENEN bir model sheet'e isaret eder.
        for p in karakterler:
            c = self.kadro["karakterler"][p["id"]]
            parcalar.append(
                " ".join(sab["karakter_satiri"].split()).format(
                    etiket=p["etiket"], ad=c["ad"], rol_en=c["rol_en"]
                )
            )
        # Model sheet karakterin GUNLUK kiyafetini gosterir; sahne kiyafeti
        # farkliysa bu satir olmadan model sheet'teki kiyafet sahneye sizar.
        if karakterler:
            kiyafetler = "; ".join(
                self._kiyafet_cumlesi(p["id"]) for p in karakterler
            )
            parcalar.append(
                " ".join(sab["kimlik_kiyafet_ayrimi"].split()).format(
                    kiyafetler=f"{kiyafetler}."
                )
            )
        if len(refler) == 1:
            parcalar.append(
                " ".join(sab["storyboard_satiri"].split()).format(
                    storyboard_ref=refler[0],
                    panel_sayisi=len(bpaneller),
                )
            )
        else:
            for i, ref in enumerate(refler, 1):
                sp = self.sayfa_panelleri(sayfa_nolari[i - 1])
                bas, son = self._zaman_araligi(
                    [{"zaman": self._goreli_zaman(x["zaman"], bas_sn)} for x in sp]
                )
                parcalar.append(
                    " ".join(sab["storyboard_sayfa_satiri"].split()).format(
                        storyboard_ref=ref,
                        sayfa=i,
                        sayfa_toplam=len(refler),
                        beat_ilk=sp[0]["n"] - ilk_n,
                        beat_son=sp[-1]["n"] - ilk_n,
                        zaman_ilk=bas,
                        zaman_son=son,
                    )
                )
            kapanis = " ".join(sab["storyboard_sayfa_kapanisi"].split()).format(
                sayfa_toplam=len(refler),
                beat_son=bpaneller[-1]["n"] - ilk_n,
            )
            if self.metin_istisnasi:
                # Sablon metni "sayfalar hicbir yazi tasimaz" diyor; istisnali
                # iste bu YANLIS oluyor (sayfada gercekten bir okuma var) ve
                # model celiskiyi cozerken istisnayi da silebiliyor.
                kapanis = kapanis.replace(
                    "The sheets carry no numbers, labels or text of any kind;",
                    f"The only text the sheets carry is {self.metin_istisnasi}, "
                    "which is part of the scene and must be reproduced; apart "
                    "from that they carry no numbers, labels or text of any kind;",
                ).replace(
                    "never render a number, label, caption or panel marking",
                    "never render a panel number, label, caption or panel marking",
                )
            parcalar.append(kapanis)
        if onceki:
            parcalar.append(
                " ".join(sab["onceki_bolum_satiri"].split()).format(etiket=onceki["etiket"])
            )
        parcalar.append(
            " ".join(sab["ana_talimat"].split()).format(
                sure=round(son_sn - bas_sn) if b else self.sb["video"]["toplam_sure_sn"],
                ortam=self._ortam_ifadesi(),
                panel_sayisi=len(bpaneller),
                yon=self.yon,
                oran=self.oran,
            )
        )
        for p in bpaneller:
            parcalar.append(
                sab["beat_satiri"].format(
                    n=p["n"] - ilk_n,
                    zaman=self._goreli_zaman(p["zaman"], bas_sn) if b else p["zaman"],
                    aciklama=p["aksiyon"],
                )
            )
        nesne = self._sahne_nesnesi_satiri()
        if nesne:
            parcalar.append(nesne)
        parcalar.append(self._video_kurallari())
        return " ".join(parcalar)

    def _video_kurallari(self) -> str:
        """Kapanis kurallari. Istisna varsa mutlak rakam yasagi daraltilir."""
        k = " ".join(self.stil["video_kurallari"].split())
        istisna = self.metin_istisnasi
        if not istisna:
            return k
        return k.replace(
            "No text, no subtitles, no logos. Never burn a number, digit, label, "
            "caption or panel marking into any frame,",
            f"The only text anywhere in the video is {istisna}; render that "
            "reading, and nothing else. No subtitles, no logos, no captions. "
            "Never burn a panel number, label, caption, timecode or corner "
            "marking into any frame,",
        )
