# Animasyon Canavarı (Animation Monster) 👾

[![Download](https://img.shields.io/badge/%E2%AC%87%20Download-Animasyon--Canavari.zip-8b5cf6)](https://github.com/karapubg345-rgb/animasyon-canavari/releases/latest/download/Animasyon-Canavari.zip)
[![Downloads](https://img.shields.io/github/downloads/karapubg345-rgb/animasyon-canavari/total?label=downloads&color=ec4899)](https://github.com/karapubg345-rgb/animasyon-canavari/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-10b981)](LICENSE)

🇹🇷 [Türkçe](README.md) · 🇬🇧 English

**Paste the link** of a 3D animation you like on Instagram. The monster extracts its
story structure, rhythm and camera language, then **rebuilds it with your own characters**.

```
Instagram link → analysis → your idea → storyboard (your approval) → 9:16 or 16:9 video
```

Only the *structure* is taken from the source video: beat order, rhythm, camera. Character
design, costumes and sets are never copied. Every video is made with your own cast.

- **Local interface:** opens in your browser, everything is point-and-click.
- **Claude Code in the background:** writes the analysis, the storyboard plan and the prompts; you watch its live log in the interface.
- **Your account, your credits:** images and videos are generated on the platform you connect.
- **Character studio:** describe your character and the monster draws a model sheet, or upload your own image.
- **Your own twist:** after the analysis you can write an idea ("she spills food instead of trash")
  and the storyboard is drawn with it. Rhythm, beats and camera stay as in the source.
- **Real footage works too:** a viral live-action reel (up to 30 s) is turned into stylized
  3D with your characters. Faces, clothes and on-screen text are never taken from it.

> **The interface is in Turkish.** Everything works the same for any language. See the
> [button glossary](#interface-glossary) below.

## Setup

**[⬇ Download Animasyon-Canavari.zip](https://github.com/karapubg345-rgb/animasyon-canavari/releases/latest/download/Animasyon-Canavari.zip)** and extract it to a folder.
The first setup takes about 10–15 minutes and is done only once.

| | Windows | macOS / Linux |
|---|---|---|
| 1. Install | double-click `kur.bat` | `chmod +x kur.sh baslat.sh && ./kur.sh` |
| 2. First login (once) | type `claude` in the folder, log in, trust the folder | same |
| 3. Open | `baslat.bat` | `./baslat.sh` |

`kur` = install, `baslat` = start.

### What you need

| What | Why | Cost |
|---|---|---|
| **Claude subscription** (Pro or higher) | Runs Claude Code in the background | Paid |
| **Apify account** | Downloads the Instagram video | Free ($5 monthly quota is enough) |
| **A generation platform account**: Higgsfield, TopView or OpenArt | Image and video generation | You buy credits |

The setup script checks for **Python 3.10+**, **ffmpeg** and **Claude Code**, and installs
anything missing after asking you (answer `E` = yes). If it installs something it will say
*"close the window and run kur.bat again"*. This is normal: close it and double-click again.

> Avoid spaces and non-English characters in the folder path
> (`C:\Users\Ali\animasyon-canavari` is fine, `C:\Desktop\New folder (2)` is risky).

### Step by step

1. **Apify token:** create a free account on [apify.com](https://apify.com) →
   **Settings → API & Integrations** → copy your **Personal API token**. The setup script
   opens a `.env` file in Notepad; paste it after `APIFY_TOKEN=` and save.
   The `.env` file stays on your computer and never enters the repo.
2. **First Claude Code login:** open a terminal in the project folder (Windows: type `cmd`
   in the folder's address bar, press Enter) and run `claude`. Log in with your Claude
   account in the browser, answer **Yes** to *"Do you trust the files in this folder?"*,
   then type `/exit`. After this the interface runs Claude Code on its own and
   **no permission pop-ups appear during generation**.
3. **Connect a generation platform** (at least one):

   | Platform | Account *(affiliate link)* | MCP address for Claude |
   |---|---|---|
   | **Higgsfield** | [Sign up ↗](https://higgsfield.ai/?fpr=serkan-e69d0e) | `https://mcp.higgsfield.ai/mcp` |
   | **TopView** | [Sign up ↗](https://www.topview.ai/?via=serkan) | `https://mcp.topview.ai/mcp` |
   | **OpenArt** | [Sign up ↗](https://tolt.link/serkan20) | `https://mcp.openart.ai/mcp` |

   Go to [claude.ai → Settings → Connectors](https://claude.ai/settings/connectors) →
   **Add custom connector** → paste the address → **Connect** and log in with the platform.
   Connectors added on claude.ai show up in Claude Code automatically.
4. **Start:** run `baslat.bat` (or `./baslat.sh`). The interface opens at
   `http://127.0.0.1:8765`. **Don't close** the black window; the interface runs on it.
5. **Make your first video:**
   1. **Sistem durumu** should show three green badges; your platform should say **Bağlı**.
   2. In **Karakterlerim**, add your first character (**Canavar çizsin** or **Görsel yükle**).
   3. In **Yeni iş**, paste the Instagram Reel link, pick the cast, the platform and the
      video ratio, then **İşi başlat**.
   4. When the analysis is ready, optionally write your idea and press **Storyboard'u çiz**.
   5. Check the storyboard → **Onayla ve videoyu üret**.

### Windows prompts you may see

| You see | Do this |
|---|---|
| "Windows protected your PC" (SmartScreen) | **More info** → **Run anyway** |
| User Account Control (UAC) | **Yes** (for the Python / ffmpeg install) |
| `winget` not found | Update **App Installer** from the Microsoft Store |

## Interface glossary

| Turkish label | Meaning |
|---|---|
| **Sistem durumu** | System status: three green badges = Claude Code kurulu (installed) · Pipeline hazır (ready) · Apify token var (present) |
| **Platformlar** · **Bağlı** · **Bağlı değil** · **Giriş gerekli** | Platforms · Connected · Not connected · Login required |
| **Bağlantıları yenile** | Refresh connections (the first check can take a minute) |
| **Karakterlerim** · **Kadro** · **+ Yeni kadro** | My characters · Cast (a group of characters) · New cast |
| **Canavar çizsin** · **Görsel yükle** · **Kadroya kaydet** | Let the monster draw it · Upload an image · Save to cast |
| **Başka kadroya taşı** | Move to another cast |
| **Yeni iş** · **Instagram Reel bağlantısı** | New job · Instagram Reel link |
| **Üretim platformu** · **Video oranı** · **Çözünürlük** | Generation platform · Video ratio (9:16 vertical / 16:9 horizontal) · Resolution |
| **İşi başlat** | Start the job |
| **Kendi fikrin (isteğe bağlı)** · **Storyboard'u çiz** | Your own idea (optional) · Draw the storyboard |
| **Storyboard'u yeniden çiz** | Redraw the storyboard |
| **Onayla ve videoyu üret** | Approve and generate the video |
| **Devam et** · **Durdur** · **Vazgeç** | Continue · Stop · Cancel |
| **Hata** | Error: read the red line in the log |

## Good to know

- **Every generation costs credits.** Storyboard images, character model sheets and videos
  are generated on your connected platform with your credits. The app itself is free;
  there is no free generation path inside it.
- **Approval gate:** the job stops when the storyboard is ready. The video inherits the
  storyboard's structure one-to-one, so catching a mistake here is much cheaper.
  No video is generated without your approval.
- **Your videos stay on your computer.** Downloaded sources and your outputs live in the
  `isler/` folder; nothing is uploaded anywhere and nothing enters the repo.
- **Source content:** the tool only references the *structure* of someone else's video.
  You are responsible for following the platform rules on downloading and on using what you generate.

## Duration paths

| Source | Model | Storyboard |
|---|---|---|
| ≤ 15 s | Seedance 2.0 | 1 page · 12 panels |
| 16–30 s | Seedance 2.5 | 2 pages · 24 panels |
| over 30 s | section by section (2.5, rest 2.0) → merged | 1 page · 12 panels per ~15 s |

The model is picked automatically from the duration.

## Troubleshooting

| Symptom | Fix |
|---|---|
| "Claude Code yok" (no Claude Code) badge | Check that `claude --version` works in a terminal. If not, repeat the install and restart the computer. |
| Platform "Bağlı değil" | Check the connector on claude.ai → **Bağlantıları yenile**. |
| Platform "Giriş gerekli" (login required) | In a terminal: `claude` → `/mcp` → pick the platform → log in. |
| "Apify token yok" (no Apify token) | Check the `APIFY_TOKEN=` line in `.env`, then close and reopen `baslat.bat`. |
| `python` doesn't work (Windows) | Normal: the scripts use `py` and `.venv`. |
| Port 8765 busy | Add `ARAYUZ_PORT=8790` to `.env`. |

## Updating

Installed from the ZIP: download the [latest release](https://github.com/karapubg345-rgb/animasyon-canavari/releases/latest),
copy `isler/`, `karakterlerim/` and `.env` into the new folder, run `kur.bat` once.
Installed with git: `git pull`. Your jobs and characters never enter the repo, so there are no conflicts.

## Folder layout

| Path | Contents |
|---|---|
| `arayuz/` | Local server and single-page interface |
| `src/animasyon/` | Pipeline (download, analysis, duration plan, prompt generation, stamp check) |
| `config/` | Style, prompt template, grid and duration settings |
| `karakterlerim/<cast>/` | Casts: `kadro.yaml` + model sheet images |
| `isler/<week>/<code>/` | Each job's source, storyboard, prompts and video (local) |
| `docs/` | Model limits and known pitfalls (Turkish) |

## License

[MIT](LICENSE): use, modify and share freely.
