# Seedance 2.5 (Dreamina) — model sınırları ve pipeline sonuçları

Kaynak: ByteDance Seed / Dreamina-Seedance-2.5 ürün brošürü (kullanıcı tarafından
10 Eyl 2026'da verildi). Bu dosya **ajanlar için tek doğruluk kaynağıdır** —
15 saniyeden uzun bir iş üreten her ajan, prompt veya config yazmadan önce bunu okur.

## Önce kapsam: bu dosya YALNIZCA 2.5'i anlatır

**Seedance 2.0 emekliye ayrılmadı.** 15 saniyelik üretimlerin yolu odur ve öyle
kalıyor. 2.5 onun yerine geçmez, **yanına eklenir**: 2.0'ın çıkaramadığı uzun
işleri karşılar.

| Kaynak süresi | Model | Storyboard | Panel |
|---|---|---|---|
| ≤ 15 sn | **Seedance 2.0** | 1 sayfa | 12 (6×2) |
| 16–30 sn | **Seedance 2.5** | 2 sayfa | 24 (global no) |

Seçim elle yapılmaz: `plan_yap()` süreye bakıp `plan.model` döndürür
(`src/animasyon/uyarlama/sureleme.py`, tablo `config/pipeline.yaml` →
`storyboard.sure_dilimleri`).

> **Aşağıdaki her sayı 2.5 içindir.** 480p/720p tavanı, Akıllı Oran zorunluluğu,
> 50 varlıklık referans bütçesi, token fiyatı — hiçbiri 2.0 hakkında bir şey
> söylemez. 15 sn'lik bir iş 2.0 ile üretiliyorsa o modelin kendi davranışı
> geçerlidir; iki modelin sınırlarını karıştırmak sessiz üretim hatası doğurur.

### 2.5 ne ekliyor

Uzun iş artık **bölünmüyor**: tek geçişte 30 sn, tek çekim, dikişsiz. Eskiden 2.0'ın
15 sn sınırı yüzünden 19 sn'lik bir kaynak iki ayrı videoya bölünmek zorunda kalmıştı;
böyle bir kaynak bugün 2.5'e gider. Bölme yalnızca kaynak 30 sn'yi aşarsa devreye girer.

## Sert sınırlar (ihlal edilirse üretim reddedilir veya bozulur)

| Boyut | Değer |
|---|---|
| Süre | 4–30 sn arası **tam sayı** (ondalık yok) + Akıllı Süre |
| Oran | 21:9, 16:9, 4:3, 1:1, 3:4, 9:16 + Akıllı Oran |
| Çözünürlük | **yalnızca 480p ve 720p** — 1080p yok |
| FPS | 24 |
| Çıktı formatı | MP4, MOV |
| Eşzamanlılık | bireysel hesap 3 iş, kurumsal 10 |
| RPM | bireysel 180 |

### Referans varlıkları — toplam en fazla 50

| Tür | Adet | Boyut | Klip süresi |
|---|---|---|---|
| Görsel | 0–30 | ≤30 MB/adet | — |
| Video | 0–10 | ≤200 MB/adet | 2–30 sn, **toplam ≤30 sn** |
| Ses | 0–10 | ≤15 MB/adet | 2–30 sn, **toplam ≤30 sn** |

Sayılar tavan; **kalite tavsiyesi bambaşka**:

- **İdeal varlık sayısı 6–10.** 50 varlık yüklemek kararlılığı artırmaz.
- **Özne sayısı en fazla 5.** Özne = kilitlenmesi istenen kişi/ürün/mekân/kilit obje.
  Stil ve atmosfer referansları özne sayılmaz, modelin serbest yorumuna bırakılır.
- Her özne için **bir net görünüm** verilir.
- Referans video/ses için **ideal klip 5–10 sn**. Çok kısa veya çok uzun klipte
  model hangi modaliteye referans verildiğini çözemez, isabet düşer.
- **Ses-yalnız referans** yeni: görüntüsüz, sadece sesle yönlendirme mümkün.

### Akıllı Oran / Akıllı Süre zorunluluğu — en kritik tuzak

Şu senaryolarda **yalnızca Akıllı Oran** çalışır ve çıktı **girdinin oranını devralır**:

- ilk kare (first-frame)
- ilk + son kare
- **video uzatma (video extension)**
- **video düzenleme (video editing)**

Video düzenlemede ayrıca **yalnızca Akıllı Süre** çalışır — çıktı girdinin süresini devralır.

**Pipeline sonucu:** çıktımız 9:16. Uzatma veya düzenleme yoluna girilecekse
**girdi klibi zaten 9:16 olmak zorundadır**, yoksa 9:16 çıkmaz ve `--oran 9:16`
yazmak işe yaramaz. 16:9 bir kaynağı uzatıp 9:16 beklemek sessizce yanlış oran üretir.

## @ referans sözdizimi

Varlıklar yüklendikten sonra **otomatik numaralanır**; prompt'ta `@Image1`,
`@Video1`, `@Audio1` ile gösterilir. Kural:

> Referans verilen her varlığın hemen ardından, o varlığın **nasıl kullanılacağını**
> söyleyen bir cümle gelmeli.

Bizim `config/prompt_sablonu.yaml` kalıbı bu kurala zaten uyuyor
(`Use @X as Maya, the mother.`) — bozma. Yükleme sırası numaraları belirler,
eşleşme `isler/<kod>/referans_eslesme.json` içine yazılır.

## 2.5'in pipeline'a eklediği yetenekler

- **30 sn tek çekim** — post'ta dikiş atmadan tam duygusal yay ve olay akışı.
- **Yüksek doğrulukta zamansal uzatma** — kısa klip, karakter/mekân/kamera
  tutarlılığı korunarak ileri veya geri uzatılır; iki klip arası geçiş köprülenir.
- **Yerel video düzenleme** — kare, kamera ve ritim sabit kalırken arka plan,
  ürün, karakter gibi yerel öğeler değiştirilir; karakter yaşı ve
  mikro-ifadeler bile ayarlanabilir. "Tek üretim, çok teslim" buradan gelir.
- **Görsel stil değişimi** — kompozisyon ve kamera aynı, stil tek komutla değişir.
- **10+ dil native** — prompt ana dilde yazılabilir; çok dilli seslendirme
  cümle cümle hizalanır. (Bizim prompt gövdesi yine İngilizce kalıyor, çünkü
  `config/stil.yaml` blokları İngilizce ve birebir prompt'a gidiyor.)
- **Daha isabetli talimat takibi** — karmaşık kamera koreografisi, duygu
  dönüşleri ve çok katmanlı sahne tarifleri daha sadık uygulanıyor.
- Kamera kontrolü, ifade/mikro-ifade okuması, ışık fiziği ve görsel
  gerçekçilik 2.0'a göre belirgin daha iyi.

## Fiyatlandırma — token tabanlı, süreyle doğrusal değil

| Girdi | Birim fiyat |
|---|---|
| Video girdisi **yok** | 10.7 USD / M token |
| Video girdisi **var** | 6.4 USD / M token |

Token tahmini:

```
token = (girdi_video_sn + cikti_video_sn) x genislik x yukseklik x fps / 1024
```

Dikkat edilecek iki nokta:

1. **Girdi video süresi de faturalanır.** Referans olarak 10 sn video vermek,
   30 sn çıktıda toplamı 40 sn'ye çıkarır.
2. **Çözünürlük maliyeti karesel büyütür.** 720p, 480p'nin ~2.25 katı token yakar.
   Uzun iş + 720p birleşimi maliyeti iki yönden birden şişirir.

Bu, bağlı platformun kredi muhasebesinin yerine geçmez — maliyet her zaman
platformun bakiye aracıyla (TopView `topview_get_credit`, Higgsfield `balance`)
önce/sonra bakiye farkından ölçülür (broşürdeki USD fiyatı doğrudan API kullanımı
içindir).

## 15 sn üstü işlerde uygulanacak kurallar

1. **Bölme yapma.** 16–30 sn tek üretimde çıkar. Bölme yalnızca kaynak 30 sn'yi
   aşarsa devreye girer.
2. **Storyboard sayfa sayısı artar, panel yoğunluğu artmaz.** Grid **6x2 = 12 panel**
   sabit kalır; 16–30 sn iş **2 sayfa** storyboard üretir (toplam 24 beat).
   Gerekçe: 24 paneli tek 16:9 tuvale sıkıştırmak panel başına çözünürlüğü yarıya
   düşürür ve kimlik okunmaz hale gelir — 1K'da zaten sınırdayız.
   Hücre oranı 6x2'de 0.59 (≈9:16), dikey videoyla kadraj uyumu buradan geliyor;
   sütun/satır sayısını değiştirmek bu uyumu bozar.
3. **Her sayfa kendi zaman aralığını taşır** ve prompt'ta hangi beat'leri
   kapsadığı açıkça yazılır. Panel numaraları **global** (1–24), sayfa başına
   sıfırlanmaz — yoksa beat eşleşmesi belirsizleşir.
4. **Süre tam sayı.** `toplam_sure_sn` asla ondalıklı verilmez.
5. **Onay kapısı uzun işte daha da kritik.** 24 panelli bir storyboard'da hata
   yapma yüzeyi iki katı; panel panel denetlenir.
6. **Referans bütçesini kontrol et.** 2 storyboard sayfası + karakter referansları
   toplamı ideal 6–10 bandında kalsın; özne sayısı 5'i aşmasın.
