@echo off
chcp 65001 > nul
echo ============================================
echo   YT Downloader - EXE Build
echo ============================================
echo.
echo NOT: Video indirme icin FFmpeg gereklidir.
echo.
echo [1/2] Paketler kontrol ediliyor...
python -m pip install -r requirements.txt pyinstaller -q
echo.
echo [2/2] EXE olusturuluyor...
python -m PyInstaller ^
  --onefile ^
  --windowed ^
  --name "YTDownloader" ^
  --distpath "." ^
  --workpath "%TEMP%\ytdl_build" ^
  --specpath "%TEMP%\ytdl_build" ^
  --hidden-import=yt_dlp ^
  --hidden-import=yt_dlp.utils ^
  --collect-all yt_dlp ^
  --hidden-import=PyQt5.QtWidgets ^
  --hidden-import=PyQt5.QtCore ^
  --hidden-import=PyQt5.QtGui ^
  main.py

echo.
echo ============================================
echo   Hazir: YTDownloader.exe
echo ============================================
pause
