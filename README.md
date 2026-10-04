# Animasyon Canavarı 👾

[![İndir](https://img.shields.io/badge/%E2%AC%87%20%C4%B0ndir-Animasyon--Canavari.zip-8b5cf6)](https://github.com/karapubg345-rgb/animasyon-canavari/releases/latest/download/Animasyon-Canavari.zip)
[![İndirme](https://img.shields.io/github/downloads/karapubg345-rgb/animasyon-canavari/total?label=indirme&color=ec4899)](https://github.com/karapubg345-rgb/animasyon-canavari/releases)
[![Lisans: MIT](https://img.shields.io/badge/lisans-MIT-10b981)](LICENSE)

Instagram'da beğendiğin bir 3D animasyonun **linkini ver**; canavar videonun anlatı
yapısını, ritmini ve kamera dilini çıkarsın, **senin karakterlerinle** yeniden üretsin.

```
Instagram linki → analiz → storyboard (onayın) → 9:16 video
```

Kaynak videodan yalnızca *yapı* alınır — beat sırası, ritim, kamera. Karakter tasarımı,
kostüm ve sahne kopyalanmaz; her üretim senin kadronla yapılır.

- **Yerel arayüz:** tarayıcıda açılır, her şeyi tıklayarak yaparsın.
- **Arka planda Claude Code:** analizi, storyboard planını ve promptları yazar; canlı logunu arayüzde izlersin.
- **Kendi hesabın, kendi kredin:** görsel ve video, senin bağladığın üretim platformunda üretilir.
- **Karakter stüdyosu:** karakterini anlat, canavar model sheet'ini çizsin; ya da kendi görselini yükle.

## Kurulum

**[⬇ Animasyon-Canavari.zip'i indir](https://github.com/karapubg345-rgb/animasyon-canavari/releases/latest/download/Animasyon-Canavari.zip)**, bir klasöre çıkar. Adım adım anlatım: **[KURULUM.md](KURULUM.md)**. Kısaca:

| | Windows | macOS / Linux |
|---|---|---|
| 1. Kur | `kur.bat`'a çift tıkla | `./kur.sh` |
| 2. İlk giriş (bir kez) | klasörde `claude` yaz, giriş yap, klasöre güven | aynı |
| 3. Aç | `baslat.bat` | `./baslat.sh` |

Kurulum betiği Python, ffmpeg ve Claude Code'u kontrol eder, eksikleri senin onayınla kurar.

## Üretim platformunu bağla

Videolar senin platform hesabında, senin kredinle üretilir. En az birini bağla:

| Platform | Hesap *(reklam linki)* | Claude'a bağlanacak MCP adresi |
|---|---|---|
| **Higgsfield** | [Kayıt ol ↗](https://higgsfield.ai/?fpr=serkan-e69d0e) | `https://mcp.higgsfield.ai/mcp` |
| **TopView** | [Kayıt ol ↗](https://www.topview.ai/?via=serkan) | `https://mcp.topview.ai/mcp` |
| **OpenArt** | [Kayıt ol ↗](https://tolt.link/serkan20) | `https://mcp.openart.ai/mcp` |

Bağlamak için: [claude.ai → Ayarlar → Connectors](https://claude.ai/settings/connectors) →
**Add custom connector** → adresi yapıştır → hesabınla giriş yap. Arayüzde
**Bağlantıları yenile**'ye bastığında platform "Bağlı" görünür.

## Bilmen gerekenler

- **Her üretim kredi harcar.** Storyboard görseli, karakter model sheet'i ve video bağlı
  platformdan, senin kredinle üretilir. Bu uygulamada ücretsiz bir üretim yolu yoktur.
- **Onay kapısı:** storyboard hazır olunca iş durur. Video, storyboard'un yapısını birebir
  devraldığı için hatayı burada yakalamak çok daha ucuzdur. Onaylamadan video üretilmez.
- **Videolar senin bilgisayarında kalır.** İndirilen kaynaklar ve ürettiklerin `isler/`
  klasöründedir; hiçbir yere gönderilmez ve repoya girmez.
- **Kaynak içerik:** Araç başkasının videosunun yalnızca yapısını referans alır. İndirme
  ve üretilen içeriğin kullanımıyla ilgili platform kurallarına uymak senin sorumluluğundadır.
- **Gereksinimler:** Claude aboneliği (Claude Code için), ücretsiz bir Apify hesabı
  (Instagram videosunu indirmek için) ve en az bir üretim platformu hesabı.

## Süre yolları

| Kaynak | Model | Storyboard |
|---|---|---|
| ≤ 15 sn | Seedance 2.0 | 1 sayfa · 12 panel |
| 16–30 sn | Seedance 2.5 | 2 sayfa · 24 panel |
| 30 sn üstü | bölüm bölüm (2.5, kalan 2.0) → birleştirilir | her ~15 sn 1 sayfa · 12 panel |

Model süreye göre otomatik seçilir. Ayrıntılı mimari ve kurallar: [CLAUDE.md](CLAUDE.md),
[docs/seedance_2_5.md](docs/seedance_2_5.md), [docs/damga_tuzagi.md](docs/damga_tuzagi.md).

## Dizin düzeni

| Yol | İçerik |
|---|---|
| `arayuz/` | Yerel sunucu ve tek sayfalık arayüz |
| `src/animasyon/` | Pipeline (indirme, analiz, süre planı, prompt üretimi, damga denetimi) |
| `config/` | Stil, prompt şablonu, grid ve süre ayarları |
| `karakterlerim/<kadro>/` | Kadrolar: `kadro.yaml` + model sheet görselleri |
| `isler/<hafta>/<kod>/` | Her işin kaynağı, storyboard'u, promptları ve videosu (yerel) |
| `docs/` | Model sınırları ve bilinen tuzaklar |

## Lisans

[MIT](LICENSE) — özgürce kullan, değiştir, paylaş.
