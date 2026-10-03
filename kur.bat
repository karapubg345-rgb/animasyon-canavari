@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
title Animasyon Canavari - Kurulum

echo.
echo  ==============================================
echo    Animasyon Canavari - kurulum
echo  ==============================================
echo.

rem ---------------------------------------------------------------- Python
echo [1/5] Python kontrol ediliyor...
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if errorlevel 1 (
  echo   Python 3.10 veya ustu bulunamadi.
  choice /C EH /M "  Simdi winget ile Python 3.12 kurulsun mu (E=evet, H=hayir)"
  if errorlevel 2 goto python_elle
  winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
  echo.
  echo   Python kuruldu. Bu pencereyi KAPAT ve kur.bat'i yeniden calistir.
  pause
  exit /b 0
)
echo   Tamam.

rem ---------------------------------------------------------------- ffmpeg
echo [2/5] ffmpeg kontrol ediliyor...
where ffmpeg >nul 2>&1
if errorlevel 1 (
  echo   ffmpeg bulunamadi. Kaynak videoyu analiz etmek icin gerekli.
  choice /C EH /M "  Simdi winget ile ffmpeg kurulsun mu (E=evet, H=hayir)"
  if errorlevel 2 goto ffmpeg_elle
  winget install -e --id Gyan.FFmpeg --accept-source-agreements --accept-package-agreements
  echo.
  echo   ffmpeg kuruldu. Bu pencereyi KAPAT ve kur.bat'i yeniden calistir.
  pause
  exit /b 0
)
echo   Tamam.

rem ---------------------------------------------------------------- Claude Code
echo [3/5] Claude Code kontrol ediliyor...
where claude >nul 2>&1
if errorlevel 1 (
  echo   Claude Code bulunamadi.
  choice /C EH /M "  Simdi resmi kurulum betigiyle kurulsun mu (E=evet, H=hayir)"
  if errorlevel 2 goto claude_elle
  powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://claude.ai/install.ps1 | iex"
  echo.
  echo   Claude Code kuruldu. Bu pencereyi KAPAT ve kur.bat'i yeniden calistir.
  pause
  exit /b 0
)
echo   Tamam.

rem ---------------------------------------------------------------- sanal ortam
echo [4/5] Python paketleri kuruluyor...
if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv || goto hata
)
".venv\Scripts\python.exe" -m pip install --upgrade pip -q
".venv\Scripts\python.exe" -m pip install -r requirements.txt -q || goto hata
echo   Tamam.

rem ---------------------------------------------------------------- .env
echo [5/5] Ayar dosyasi...
if not exist ".env" (
  copy ".env.example" ".env" >nul
  echo   .env olusturuldu. Icine Apify token'ini yapistir.
  start "" notepad ".env"
) else (
  echo   .env zaten var.
)

echo.
echo  ==============================================
echo    Kurulum bitti.
echo  ==============================================
echo.
echo  Son bir adim (yalnizca ilk seferde):
echo    1. Bu klasorde bir terminal ac ve  claude  yaz.
echo    2. Claude hesabinla giris yap, "bu klasore guveniyor musun" sorusuna Evet de.
echo    3. /exit ile cik.
echo.
echo  Sonra her seferinde:  baslat.bat
echo.
pause
exit /b 0

:python_elle
echo   Python'u https://www.python.org/downloads/ adresinden kur.
echo   Kurulumda "Add python.exe to PATH" kutusunu isaretle. Sonra kur.bat'i yeniden calistir.
pause
exit /b 1

:ffmpeg_elle
echo   ffmpeg'i https://www.gyan.dev/ffmpeg/builds/ adresinden indirip PATH'e ekle.
echo   Sonra kur.bat'i yeniden calistir.
pause
exit /b 1

:claude_elle
echo   Claude Code kurulumu: https://docs.claude.com/en/docs/claude-code/setup
echo   Sonra kur.bat'i yeniden calistir.
pause
exit /b 1

:hata
echo.
echo   Bir sey ters gitti. Yukaridaki hata mesajini kontrol et.
pause
exit /b 1
