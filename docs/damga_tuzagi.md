# Damga tuzağı — storyboard'daki panel numarası videoya kopyalanıyor

**Vaka (Eylül 2026).** 30 sn'lik bir video baştan sona sol üst köşesinde beyaz
rakamla üretildi; saatlerce kuyrukta beklenen çıktı kullanılamaz durumdaydı. Aynı
hata daha önce bir kez daha yaşanmış ve video elle temizlenmişti. İki kez olduğuna
göre üçüncüsü de olur — bu dosya ve `animasyon dogrula` komutu onu engellemek için var.

## Zincir

1. `prompt_uretici.py` storyboard grid prompt'unun sonuna şunu yazıyordu:
   `"Each panel must show a small panel number in its top-left corner."`
   Amaç iyiydi: onay kapısında panel ↔ beat eşleşmesini gözle doğrulayabilmek.
2. GPT Image 2 numarayı **piksel olarak** sayfaya yaktı.
3. O sayfa Seedance'a **Omni Referans** olarak verildi.
4. Seedance referanstaki rakamı sahnenin bir parçası sandı ve her video karesine
   kopyaladı — konumu kesmeden kesmeye birkaç piksel kaydırarak.

Video prompt'undaki `"No text, no subtitles, no logos"` bunu **durdurmadı**.
Kritik nokta bu: **referans görsel negatif prompt'tan güçlüdür.** Referansta
fiziksel olarak duran bir işareti metinle yasaklayamazsın. Tek çözüm işaretin
referansa hiç girmemesi.

Kanıt — üretilen videodaki rakamlar sırayla:
`4, 3, 3, 6, 7, 8, 11, 12, 19, 19, 17, 16, 22, 22, 24`. Sıralı bile değiller;
model panel numarasını anlatı verisi olarak değil, **kopyalanacak bir grafik
katman** olarak okumuş.

## Düzeltme

| Nerede | Ne değişti |
|---|---|
| `prompt_uretici.py` | Numara talebi → kesin yasak. Gerekçe de prompt'a yazıldı: sayfa video referansıdır, yanan iz videoya geçer. |
| `prompt_uretici.py` | `"Panel numbering continues…"` → anlatı dili (`"The story is already in progress…"`). Eski ifade "panellere numara yaz" diye okunuyordu. |
| `config/stil.yaml` | `negatif_prompt`'a `panel number, panel label, numbers, digits, numerals, timecode, frame counter, corner marking`. `video_kurallari`'na kare içine damga ve grid çizme yasağı. |
| `config/prompt_sablonu.yaml` | `storyboard_sayfa_kapanisi` artık görünmeyen bir numaraya atıf yapmıyor; sıra okuma düzeninden veriliyor + damga yasağı tekrarlanıyor. |
| `config/pipeline.yaml` | `storyboard.damga: false` (açma), `damga_yerel_denetim: true`. |

Panel numarası hâlâ gerekli — ama artık **modelden istenmiyor**. Üretimden sonra
yerel olarak Pillow ile ayrı bir dosyaya basılıyor:

```
storyboard_sayfaN.png          TEMIZ    -> Seedance'a yüklenen budur
storyboard_sayfaN_denetim.png  numaralı -> yalnızca onay kapısı, ASLA yüklenmez
```

Denetim kopyasında üstte kırmızı `DENETIM KOPYASI - SEEDANCE'A YUKLEMEYIN` bandı
var; yanlışlıkla yüklenirse ekranda anında göze çarpar. `dogrula` da `_denetim`
ekli dosyaları referans taramasının dışında tutar.

## Kullanım

```bash
PYTHONPATH=src PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m animasyon <komut>
```

| Komut | Ne zaman |
|---|---|
| `dogrula <kod>` | **Video üretimine basmadan önce zorunlu.** Prompt + referans + varsa video. |
| `denetim-kopyasi <kod>` | Storyboard onaya sunulmadan önce; numaralı kopyayı üretir. |
| `temizle <kod>` | Damga kaçtıysa kurtarma. `video_ham.mp4` → `video_temiz.mp4`. |

## Üç katmanlı savunma

| Katman | Yöntem | Güç |
|---|---|---|
| `promptu_denetle()` | Yasaklı kalıp araması | **Deterministik.** Asıl garanti. |
| `goruntuyu_denetle()` | Panel köşelerinde parlak/kompakt bileşen | Sezgisel |
| `videoyu_denetle()` | Kare örnekleme, aynı test | Sezgisel |

Sezgisel katmanlar yazı **okumaz**, hane biçimli parlak leke arar. Bu yüzden her
bulgu için `damga_kanit/` altına büyütülmüş PNG yazılır — **karar gözle verilir.**

### Ölçülen doğruluk

Bu depodaki tüm storyboard'lar ve iki video üzerinde:

| Girdi | Bulgu |
|---|---|
| Damgalı storyboard sayfası | 7–12 / 12 panel |
| Damgasız storyboard sayfası | 0–2 / 12 panel |
| Damgalı video | 10 / 10 kare |
| Temizlenmiş video | 0 / 10 kare |

Aradaki boşluk geniş; `karar()` eşiği örnek sayısının %25'i. Tek tük bulgu yanlış
alarm olabilir (parlak fayans, ayna kenarı) — yine de durdurur, çünkü 10 saniyelik
göz kontrolü saatlerce kuyruktan ucuzdur.

### Tespitte iki tuzak (ikisi de bu vakada yaşandı)

- **Toplu bbox işe yaramaz.** Sahnedeki tek bir uzak parlama bbox'ı ROI kadar
  büyütüp damgayı "yayılmış parlaklık" diye eletiyor. Bağlı bileşen analizi şart,
  ve "en büyük bileşen" de yetmez: panelin kendi parlak dikey kenarı rakamı
  gölgeliyor. Bileşenlerin **hepsi** hane profiline göre elenir.
- **Panel sınırları eşit bölmeyle bulunamaz.** Model gutter'ları tam eşit
  bırakmıyor ve sayfa 2'de üstte siyah bir letterbox şeridi vardı. Hiza kayınca
  ROI gutter'ın üzerine binip beyaz şeritle rakamı tek bileşen yapıyor.
  `panel_kutulari()` beyaz gutter'ları doğrudan ölçer.

## Kurtarma

`temizle` damgayı `ffmpeg delogo` ile siler, sesi olduğu gibi kopyalar. Kutu tek
kareden çıkarılamaz — model damgayı her kesmede birkaç piksel kaydırıyor (ölçülen:
tek kare 37×50, tüm video birleşik 101×89), bu yüzden `damga_kutusu()` tüm videoyu
tarayıp birleşik kutuyu alır.

`delogo` kutunun kareye **tamamen iç** olmasını ister; `x=0` verilince
`Logo area is outside of the frame` ile düşer. Kutu 1,1'den başlatılıp kalan 1
piksellik kenar şeridi `fillborders=smear` ile komşudan yayılır — damga kareyi
kenardan kesiyorsa o şerit de temizlensin.

Delogo arka planı interpolasyonla doldurur; köşe genelde düz duvar olduğu için iz
bırakmaz. Köşede karakter/saç varsa hafif yumuşama olur — kabul edilebilir, ama
**kurtarma her zaman ikinci tercihtir.** Doğrusu damganın hiç oluşmaması.
