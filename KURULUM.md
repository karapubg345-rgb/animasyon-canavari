# Kurulum — adım adım

İlk kurulum yaklaşık 10–15 dakika sürer. Bir kez yapılır; sonra her seferinde yalnızca
`baslat.bat`'a tıklarsın.

## Neye ihtiyacın var

| Ne | Neden | Ücret |
|---|---|---|
| **Claude aboneliği** (Pro veya üstü) | Arka planda çalışan Claude Code için | Ücretli |
| **Apify hesabı** | Instagram videosunu indirmek için | Ücretsiz (aylık 5 $ kota yeter) |
| **Üretim platformu hesabı** — Higgsfield, TopView veya OpenArt | Görsel ve video üretimi | Kredi alırsın |

Bilgisayara kurulacaklar (kurulum betiği kontrol eder, eksikse sorup kurar):

| Program | Neden |
|---|---|
| **Python 3.10+** | Pipeline ve arayüz Python'la çalışır |
| **ffmpeg** | Kaynak videodan kare çıkarmak ve videoyu denetlemek için |
| **Claude Code** | İşi yürüten yapay zekâ |

---

## 1. Projeyi indir

**[⬇ Animasyon-Canavari.zip'i indir](https://github.com/karapubg345-rgb/animasyon-canavari/releases/latest/download/Animasyon-Canavari.zip)**
→ ZIP'e sağ tıkla → **Tümünü ayıkla** → bir klasör seç (ör. `Belgeler`). İçinden
`animasyon-canavari` klasörü çıkar.

Git kullanıyorsan:

```bash
git clone https://github.com/karapubg345-rgb/animasyon-canavari.git
```

> Klasör yolunda Türkçe karakter ve boşluk olmaması en sorunsuzudur
> (`C:\Users\Ali\animasyon-canavari` iyi, `C:\Masaüstü\Yeni klasör (2)` riskli).

## 2. Kurulum betiğini çalıştır

**Windows:** klasördeki `kur.bat`'a çift tıkla.
**macOS / Linux:** klasörde terminal aç → `chmod +x kur.sh baslat.sh && ./kur.sh`

Betik sırayla şunları kontrol eder:

1. **Python** — yoksa "winget ile kurulsun mu?" diye sorar. `E` de.
2. **ffmpeg** — yoksa aynı şekilde sorar. `E` de.
3. **Claude Code** — yoksa resmi kurulum betiğiyle kurmayı önerir. `E` de.

Bunlardan biri kurulursa betik **"pencereyi kapat, kur.bat'i yeniden çalıştır"** der.
Bu normal: Windows yeni kurulan programı ancak yeni açılan pencerede görür. Kapat,
yeniden çift tıkla; kaldığı yerden devam eder.

4. **Python paketleri** — otomatik kurulur.
5. **`.env` dosyası** — oluşturulur ve Not Defteri'nde açılır (bir sonraki adım).

### Windows'ta karşına çıkabilecekler

| Ne görürsün | Ne yaparsın |
|---|---|
| "Windows kişisel bilgisayarınızı korudu" (SmartScreen) | **Ek bilgi** → **Yine de çalıştır** |
| winget lisans sözleşmesi soruları | Betik bunları zaten kabul ediyor; bir şey sorarsa `Y` |
| Kullanıcı Hesabı Denetimi (UAC) | **Evet** — Python/ffmpeg kurulumu için |
| `winget` bulunamadı | Microsoft Store'dan **Uygulama Yükleyicisi**'ni güncelle, ya da betiğin verdiği linkten elle kur |

## 3. Apify token'ını yapıştır

1. [apify.com](https://apify.com)'da ücretsiz hesap aç.
2. **Settings → API & Integrations** → **Personal API token**'ı kopyala.
3. Açılan `.env` dosyasında `APIFY_TOKEN=` satırının devamına yapıştır, kaydet.

```
APIFY_TOKEN=apify_api_AbC123...
```

> `.env` yalnızca senin bilgisayarında durur ve repoya hiç girmez. Kimseyle paylaşma.

## 4. Claude Code'a ilk giriş (yalnızca bir kez)

Proje klasöründe bir terminal aç (Windows: klasörde adres çubuğuna `cmd` yaz, Enter) ve:

```
claude
```

1. Tarayıcı açılır → **Claude hesabınla giriş yap**.
2. Terminalde **"Do you trust the files in this folder?"** sorulur → **Yes**.
3. `/exit` yazıp çık.

Bu adım bir kez yapılır. Sonrasında arayüz Claude Code'u arka planda kendisi çalıştırır;
izinleri arayüz önceden verdiği için **üretim sırasında sana izin soran bir pencere çıkmaz**.

## 5. Üretim platformunu bağla

1. Platformda hesap aç: [Higgsfield](https://higgsfield.ai/?fpr=serkan-e69d0e) ·
   [TopView](https://www.topview.ai/?via=serkan) ·
   [OpenArt](https://tolt.link/serkan20)
   *(reklam linkleri)*
2. [claude.ai → Ayarlar → Connectors](https://claude.ai/settings/connectors) → **Add custom connector**
3. Adı istediğin gibi yaz, adresi yapıştır:

| Platform | MCP adresi |
|---|---|
| Higgsfield | `https://mcp.higgsfield.ai/mcp` |
| TopView | `https://mcp.topview.ai/mcp` |
| OpenArt | `https://mcp.openart.ai/mcp` |

4. **Connect** → platformun giriş sayfası açılır → giriş yap, izin ver.

claude.ai'ye eklediğin bağlantılar Claude Code'da otomatik görünür.

## 6. Başlat

**Windows:** `baslat.bat` · **macOS / Linux:** `./baslat.sh`

Tarayıcıda `http://127.0.0.1:8765` açılır. Siyah pencereyi **kapatma** — arayüz onunla çalışır.

1. **Kurulum durumu**nda üç yeşil rozet görmelisin: Claude Code kurulu · Pipeline hazır · Apify token var.
2. **Platformlar**da bağladığın platform "Bağlı" görünmeli. Görünmüyorsa
   **Bağlantıları yenile** (ilk kontrol bir dakika kadar sürebilir).
3. **Karakterlerim** sekmesinde ilk karakterini ekle — "Canavar çizsin" ya da "Görsel yükle".
4. **Yeni iş**: Instagram linkini yapıştır, kadroyu ve karakterleri seç, **Başlat**.
5. Storyboard gelince kontrol et → **Onayla ve videoyu üret**.

---

## Sorun giderme

| Belirti | Çözüm |
|---|---|
| "Claude Code yok" rozeti | Terminalde `claude --version` çalışıyor mu bak. Çalışmıyorsa 2. adımı tekrarla, bilgisayarı yeniden başlat. |
| Platform "Bağlı değil" | claude.ai'de connector'ın bağlı olduğunu kontrol et → **Bağlantıları yenile**. |
| Platform "Giriş gerekli" | Terminalde `claude` → `/mcp` → platformu seç → giriş yap. |
| "Apify token yok" | `.env` dosyasındaki `APIFY_TOKEN=` satırını kontrol et, `baslat.bat`'ı kapatıp aç. |
| İş "Hata" verdi | Loglardaki kırmızı satırı oku. Kredi bitmişse platformdan kredi al. |
| `python` çalışmıyor (Windows) | Normal — Windows'taki `python` komutu Store kısayoludur. Betikler `py` ve `.venv` kullanır. |
| Port 8765 dolu | `.env`'e `ARAYUZ_PORT=8790` ekle. |

## Güncelleme

ZIP ile kurduysan [son sürümü](https://github.com/karapubg345-rgb/animasyon-canavari/releases/latest)
indir; `isler/`, `karakterlerim/` ve `.env`'i yeni klasöre kopyala, `kur.bat`'ı bir kez çalıştır. Git ile kurduysan `git pull` — kendi işlerin ve karakterlerin repoya girmediği
için çakışma olmaz.
