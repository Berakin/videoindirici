#!/usr/bin/env python3
"""
YT Downloader - YouTube video/ses indirme aracı
"""

import sys
import os
import shutil
import threading
import re
import urllib.request
import tempfile
from pathlib import Path

import yt_dlp
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QComboBox, QProgressBar,
    QFileDialog, QFrame, QScrollArea, QSizePolicy, QSystemTrayIcon,
    QMenu, QAction, QCheckBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QSettings, QTimer
from PyQt5.QtGui import QIcon, QColor, QPixmap, QPainter, QFont


# ─────────────────────────────────────────────────────────
#  DARK THEME
# ─────────────────────────────────────────────────────────

STYLE = """
QMainWindow, QWidget {
    background-color: #1a1a2e;
    color: #e2e2f0;
    font-family: 'Segoe UI', sans-serif;
    font-size: 14px;
}
QPushButton {
    background-color: #242445;
    color: #e2e2f0;
    border: 1px solid #3a3a6a;
    border-radius: 6px;
    padding: 6px 16px;
    min-height: 30px;
}
QPushButton:hover  { background-color: #2e2e5e; border-color: #6c5ce7; }
QPushButton:pressed { background-color: #6c5ce7; }
QPushButton:disabled { background-color: #1e1e38; color: #555; border-color: #2a2a4a; }
QPushButton#accent {
    background-color: #6c5ce7;
    border-color: #a29bfe;
    color: #fff;
    font-weight: bold;
}
QPushButton#accent:hover { background-color: #7d6ff0; }
QPushButton#accent:disabled { background-color: #3a3060; color: #888; border-color: #4a4080; }
QPushButton#danger {
    background-color: #3d1a1a;
    border-color: #c0392b;
    color: #ff6b6b;
}
QPushButton#danger:hover { background-color: #5a2020; }
QPushButton#folder_btn {
    background-color: #1a2d3d;
    border-color: #2980b9;
    color: #74b9ff;
    min-width: 36px;
    max-width: 36px;
}
QPushButton#folder_btn:hover { background-color: #1e3a50; }
QLineEdit {
    background-color: #242445;
    color: #e2e2f0;
    border: 1px solid #3a3a6a;
    border-radius: 6px;
    padding: 6px 12px;
    min-height: 36px;
}
QLineEdit:focus { border-color: #6c5ce7; }
QLineEdit::placeholder { color: #555; }
QComboBox {
    background-color: #242445;
    color: #e2e2f0;
    border: 1px solid #3a3a6a;
    border-radius: 6px;
    padding: 5px 10px;
    min-height: 30px;
    min-width: 160px;
}
QComboBox:hover { border-color: #6c5ce7; }
QComboBox::drop-down { border: none; width: 22px; }
QComboBox QAbstractItemView {
    background-color: #242445;
    color: #e2e2f0;
    border: 1px solid #6c5ce7;
    selection-background-color: #6c5ce7;
    outline: none;
}
QProgressBar {
    background-color: #242445;
    border: 1px solid #3a3a6a;
    border-radius: 6px;
    text-align: center;
    color: #e2e2f0;
    min-height: 26px;
}
QProgressBar::chunk {
    background-color: #6c5ce7;
    border-radius: 5px;
}
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical {
    background: #242445; width: 8px; border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #6c5ce7; border-radius: 4px; min-height: 20px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QFrame#card {
    background-color: #242445;
    border: 1px solid #3a3a6a;
    border-radius: 10px;
}
QFrame#separator { background-color: #3a3a6a; max-height: 1px; }
QLabel#title { font-size: 23px; font-weight: bold; color: #a29bfe; }
QLabel#section { font-size: 12px; font-weight: bold; color: #74b9ff; letter-spacing: 1px; }
QLabel#hint { font-size: 12px; color: #666; }
QLabel#status_ok  { color: #00b894; font-size: 13px; }
QLabel#status_err { color: #ff4757; font-size: 13px; }
QLabel#status_dl  { color: #74b9ff; font-size: 13px; }
QLabel#video_title { color: #a29bfe; font-size: 13px; font-weight: bold; }
QLabel#warn_ffmpeg {
    color: #fdcb6e;
    font-size: 13px;
    background-color: #2d2510;
    border: 1px solid #856404;
    border-radius: 6px;
    padding: 6px 10px;
}
"""


# ─────────────────────────────────────────────────────────
#  FORMAT / KALİTE SEÇENEKLERİ
# ─────────────────────────────────────────────────────────

VIDEO_QUALITIES = [
    ("En İyi Kalite",  "bestvideo+bestaudio/best"),
    ("1080p",          "bestvideo[height<=1080]+bestaudio/best[height<=1080]"),
    ("720p",           "bestvideo[height<=720]+bestaudio/best[height<=720]"),
    ("480p",           "bestvideo[height<=480]+bestaudio/best[height<=480]"),
    ("360p",           "bestvideo[height<=360]+bestaudio/best[height<=360]"),
]

FORMATS = [
    ("MP4  (Video)",  "mp4",  "video"),
    ("WEBM (Video)",  "webm", "video"),
    ("MKV  (Video)",  "mkv",  "video"),
    ("MP3  (Ses)",    "mp3",  "audio"),
    ("AAC  (Ses)",    "aac",  "audio"),
    ("OGG  (Ses)",    "ogg",  "audio"),
    ("WAV  (Ses)",    "wav",  "audio"),
    ("FLAC (Ses)",    "flac", "audio"),
    ("M4A  (Ses)",    "m4a",  "audio"),
]

AUDIO_QUALITIES = [
    ("En İyi",  "0"),
    ("320 kbps", "320"),
    ("192 kbps", "192"),
    ("128 kbps", "128"),
]


# ─────────────────────────────────────────────────────────
#  İNDİRME THREAD'İ
# ─────────────────────────────────────────────────────────

class DownloadThread(QThread):
    progress   = pyqtSignal(float, str)   # (yüzde, hız_metni)
    finished   = pyqtSignal(str)          # dosya yolu
    error      = pyqtSignal(str)
    info_ready = pyqtSignal(str)          # video başlığı

    def __init__(self, url: str, out_dir: str, fmt: dict, quality_fmt: str,
                 audio_quality: str, download_subs: bool = False):
        super().__init__()
        self.url            = url
        self.out_dir        = out_dir
        self.fmt            = fmt            # FORMATS[i] dict
        self.quality_fmt    = quality_fmt    # yt-dlp format string (video için)
        self.audio_quality  = audio_quality  # "0","320","192","128"
        self.download_subs  = download_subs
        self._cancelled     = False

    def run(self):
        os.makedirs(self.out_dir, exist_ok=True)
        is_audio = self.fmt["type"] == "audio"
        ext      = self.fmt["ext"]

        ydl_opts = {
            "outtmpl":  os.path.join(self.out_dir, "%(title)s.%(ext)s"),
            "progress_hooks": [self._hook],
            "quiet":    True,
            "no_warnings": True,
        }

        # Altyazı indirme
        if self.download_subs:
            ydl_opts["writesubtitles"] = True
            ydl_opts["writeautomaticsub"] = True
            ydl_opts["subtitleslangs"] = ["tr", "en"]
            ydl_opts["subtitlesformat"] = "srt/best"

        ffmpeg_ok = shutil.which("ffmpeg") is not None

        if is_audio:
            if not ffmpeg_ok:
                self.error.emit(
                    "Ses indirmek için FFmpeg gereklidir.\n"
                    "ffmpeg.org/download adresinden indirip PATH'e ekleyin."
                )
                return
            ydl_opts["format"] = "bestaudio/best"
            ydl_opts["postprocessors"] = [{
                "key":              "FFmpegExtractAudio",
                "preferredcodec":   ext,
                "preferredquality": self.audio_quality,
            }]
        else:
            if ffmpeg_ok:
                # FFmpeg var → yüksek kalite, ayrı stream'leri birleştir
                ydl_opts["format"] = self.quality_fmt
                ydl_opts["merge_output_format"] = ext
            else:
                # FFmpeg yok → AAC sesli birleşik dosya indir (Opus'tan kaçın)
                ydl_opts["format"] = (
                    f"best[ext={ext}][acodec^=mp4a]"
                    f"/best[ext={ext}][acodec=aac]"
                    f"/best[ext=mp4][acodec^=mp4a]"
                    f"/best[ext=mp4][acodec=aac]"
                    f"/18"   # YouTube standart 360p MP4+AAC yedek
                )

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
                self.info_ready.emit(info.get("title", ""))
                if not self._cancelled:
                    ydl.download([self.url])
            if not self._cancelled:
                self.finished.emit(self.out_dir)
        except yt_dlp.utils.DownloadCancelled:
            self.error.emit("İptal edildi.")
        except Exception as e:
            self.error.emit(str(e))

    def _hook(self, d):
        if self._cancelled:
            raise yt_dlp.utils.DownloadCancelled("cancelled")
        if d["status"] == "downloading":
            total      = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            speed      = d.get("_speed_str", "").strip()
            eta        = d.get("_eta_str", "").strip()
            pct        = (downloaded / total * 100) if total else 0
            label      = f"{speed}  —  ETA {eta}" if speed else ""
            self.progress.emit(pct, label)
        elif d["status"] == "finished":
            self.progress.emit(100, "Dönüştürülüyor...")

    def cancel(self):
        self._cancelled = True


# ─────────────────────────────────────────────────────────
#  THUMBNAIL FETCHER
# ─────────────────────────────────────────────────────────

class ThumbnailFetcher(QThread):
    """Video bilgisi ve thumbnail'i arka planda indir."""
    result = pyqtSignal(str, str, str)  # (title, duration_str, thumb_path)
    error  = pyqtSignal()

    def __init__(self, url: str):
        super().__init__()
        self.url = url

    def run(self):
        try:
            with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
                info = ydl.extract_info(self.url, download=False)
            title    = info.get("title", "")
            duration = info.get("duration", 0)
            dur_str  = f"{duration // 60}:{duration % 60:02d}" if duration else ""
            thumb_url = info.get("thumbnail", "")

            thumb_path = ""
            if thumb_url:
                tmp = os.path.join(tempfile.gettempdir(), "yt_thumb.jpg")
                try:
                    urllib.request.urlretrieve(thumb_url, tmp)
                    thumb_path = tmp
                except Exception:
                    pass

            self.result.emit(title, dur_str, thumb_path)
        except Exception:
            self.error.emit()


# ─────────────────────────────────────────────────────────
#  İNDİRME KARTI (geçmiş listesi)
# ─────────────────────────────────────────────────────────

class DownloadCard(QFrame):
    def __init__(self, title: str, out_dir: str):
        super().__init__()
        self.setObjectName("card")
        self.setFixedHeight(60)
        row = QHBoxLayout(self)
        row.setContentsMargins(14, 0, 14, 0)
        row.setSpacing(10)

        icon = QLabel("✓")
        icon.setStyleSheet("color: #00b894; font-size: 16px; font-weight: bold;")
        icon.setFixedWidth(22)
        row.addWidget(icon)

        lbl = QLabel(title)
        lbl.setWordWrap(False)
        lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        row.addWidget(lbl, 1)

        open_btn = QPushButton("📁 Klasörü Aç")
        open_btn.setFixedHeight(28)
        open_btn.clicked.connect(lambda: os.startfile(out_dir))
        row.addWidget(open_btn)


# ─────────────────────────────────────────────────────────
#  ANA PENCERE
# ─────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YT Downloader")
        self.setMinimumSize(920, 660)
        self.setStyleSheet(STYLE)
        self._thread: DownloadThread = None
        self._thumb_fetcher: ThumbnailFetcher = None
        self._settings = QSettings("YTDownloader", "YTDownloader")
        self._out_dir = self._settings.value(
            "last_out_dir", str(Path.home() / "Downloads")
        )
        self._build_ui()
        self._restore_settings()
        self._setup_tray()
        self._check_ffmpeg()
        self._start_clipboard_watcher()

    # ── FFmpeg kontrol ────────────────────────────────────

    def _check_ffmpeg(self):
        if shutil.which("ffmpeg") is None:
            self._ffmpeg_warn.show()
        else:
            self._ffmpeg_warn.hide()

    # ── UI ────────────────────────────────────────────────

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Başlık
        title = QLabel("▼  YT Downloader")
        title.setObjectName("title")
        layout.addWidget(title)

        # ── URL Kartı ──
        url_card = QFrame()
        url_card.setObjectName("card")
        url_layout = QVBoxLayout(url_card)
        url_layout.setContentsMargins(18, 16, 18, 16)
        url_layout.setSpacing(10)

        sec1 = QLabel("VİDEO LİNKİ")
        sec1.setObjectName("section")
        url_layout.addWidget(sec1)

        url_row = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.youtube.com/watch?v=...")
        self.url_input.returnPressed.connect(self._start_download)
        url_row.addWidget(self.url_input, 1)

        paste_btn = QPushButton("Yapıştır")
        paste_btn.setFixedWidth(80)
        paste_btn.clicked.connect(self._paste_url)
        url_row.addWidget(paste_btn)
        url_layout.addLayout(url_row)

        self.video_title_lbl = QLabel("")
        self.video_title_lbl.setObjectName("video_title")
        self.video_title_lbl.setWordWrap(True)
        self.video_title_lbl.hide()
        url_layout.addWidget(self.video_title_lbl)

        # Thumbnail önizleme
        thumb_row = QHBoxLayout()
        self._thumb_lbl = QLabel()
        self._thumb_lbl.setFixedSize(160, 90)
        self._thumb_lbl.setAlignment(Qt.AlignCenter)
        self._thumb_lbl.setStyleSheet(
            "background: #1e1e38; border: 1px solid #3a3a6a; border-radius: 6px;"
        )
        self._thumb_lbl.hide()
        thumb_row.addWidget(self._thumb_lbl)

        self._video_info_lbl = QLabel("")
        self._video_info_lbl.setObjectName("hint")
        self._video_info_lbl.setWordWrap(True)
        self._video_info_lbl.hide()
        thumb_row.addWidget(self._video_info_lbl, 1)
        url_layout.addLayout(thumb_row)

        layout.addWidget(url_card)

        # ── Ayarlar Kartı ──
        settings_card = QFrame()
        settings_card.setObjectName("card")
        s_layout = QVBoxLayout(settings_card)
        s_layout.setContentsMargins(18, 16, 18, 16)
        s_layout.setSpacing(10)

        sec2 = QLabel("İNDİRME AYARLARI")
        sec2.setObjectName("section")
        s_layout.addWidget(sec2)

        opts_row = QHBoxLayout()
        opts_row.setSpacing(16)

        # Format
        fmt_w = QWidget()
        fmt_col = QVBoxLayout(fmt_w)
        fmt_col.setContentsMargins(0, 0, 0, 0)
        fmt_col.setSpacing(4)
        fmt_col.addWidget(QLabel("Format:"))
        self.fmt_combo = QComboBox()
        for label, ext, typ in FORMATS:
            self.fmt_combo.addItem(label, {"ext": ext, "type": typ})
        self.fmt_combo.currentIndexChanged.connect(self._on_format_change)
        fmt_col.addWidget(self.fmt_combo)
        opts_row.addWidget(fmt_w)

        # Video kalitesi
        self.qual_w = QWidget()
        qual_col = QVBoxLayout(self.qual_w)
        qual_col.setContentsMargins(0, 0, 0, 0)
        qual_col.setSpacing(4)
        qual_col.addWidget(QLabel("Video Kalitesi:"))
        self.quality_combo = QComboBox()
        for label, fmt in VIDEO_QUALITIES:
            self.quality_combo.addItem(label, fmt)
        qual_col.addWidget(self.quality_combo)
        opts_row.addWidget(self.qual_w)

        # Ses kalitesi
        self.aq_w = QWidget()
        aq_col = QVBoxLayout(self.aq_w)
        aq_col.setContentsMargins(0, 0, 0, 0)
        aq_col.setSpacing(4)
        aq_col.addWidget(QLabel("Ses Kalitesi:"))
        self.aq_combo = QComboBox()
        for label, val in AUDIO_QUALITIES:
            self.aq_combo.addItem(label, val)
        aq_col.addWidget(self.aq_combo)
        opts_row.addWidget(self.aq_w)

        opts_row.addStretch()
        s_layout.addLayout(opts_row)
        self._on_format_change()   # başlangıç görünürlüğü

        # Altyazı indirme
        self._sub_chk = QCheckBox("Altyazı indir (TR + EN)")
        self._sub_chk.setToolTip("Varsa Türkçe ve İngilizce altyazıları SRT olarak indirir")
        s_layout.addWidget(self._sub_chk)

        # Kayıt klasörü
        dir_lbl = QLabel("Kayıt Klasörü:")
        s_layout.addWidget(dir_lbl)
        dir_row = QHBoxLayout()
        self.dir_input = QLineEdit(self._out_dir)
        self.dir_input.textChanged.connect(lambda t: setattr(self, "_out_dir", t))
        folder_btn = QPushButton("📁")
        folder_btn.setObjectName("folder_btn")
        folder_btn.setToolTip("Klasör seç")
        folder_btn.clicked.connect(self._choose_dir)
        dir_row.addWidget(self.dir_input, 1)
        dir_row.addWidget(folder_btn)
        s_layout.addLayout(dir_row)

        layout.addWidget(settings_card)

        # ── İndirme Kartı ──
        dl_card = QFrame()
        dl_card.setObjectName("card")
        dl_layout = QVBoxLayout(dl_card)
        dl_layout.setContentsMargins(18, 16, 18, 16)
        dl_layout.setSpacing(10)

        # FFmpeg uyarı etiketi
        self._ffmpeg_warn = QLabel(
            "⚠ FFmpeg bulunamadı — video indirme bazı formatlarda çalışmayabilir. "
            "FFmpeg'i yükleyin."
        )
        self._ffmpeg_warn.setObjectName("warn_ffmpeg")
        self._ffmpeg_warn.setWordWrap(True)
        self._ffmpeg_warn.hide()
        dl_layout.addWidget(self._ffmpeg_warn)

        btn_row = QHBoxLayout()
        self.dl_btn = QPushButton("⬇  İndir")
        self.dl_btn.setObjectName("accent")
        self.dl_btn.clicked.connect(self._start_download)
        self.cancel_btn = QPushButton("✕  İptal")
        self.cancel_btn.setObjectName("danger")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._cancel)
        btn_row.addWidget(self.dl_btn, 1)
        btn_row.addWidget(self.cancel_btn)
        dl_layout.addLayout(btn_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        dl_layout.addWidget(self.progress_bar)

        self.status_lbl = QLabel("Hazır")
        self.status_lbl.setObjectName("status_ok")
        dl_layout.addWidget(self.status_lbl)

        layout.addWidget(dl_card)

        # ── Geçmiş ──
        history_lbl = QLabel("TAMAMLANANLAR")
        history_lbl.setObjectName("section")
        layout.addWidget(history_lbl)

        self._history_widget = QWidget()
        self._history_layout = QVBoxLayout(self._history_widget)
        self._history_layout.setContentsMargins(0, 0, 0, 0)
        self._history_layout.setSpacing(6)
        self._history_layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(self._history_widget)
        layout.addWidget(scroll, 1)

        self.empty_history = QLabel("Henüz indirme yok.")
        self.empty_history.setObjectName("hint")
        self.empty_history.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.empty_history)

    # ── QSettings: kaydet / geri yükle ───────────────────

    def _restore_settings(self):
        geom = self._settings.value("window_geometry")
        if geom:
            self.restoreGeometry(geom)
        else:
            self.resize(980, 720)

        fmt_idx = self._settings.value("last_format_index", 0, type=int)
        if 0 <= fmt_idx < self.fmt_combo.count():
            self.fmt_combo.setCurrentIndex(fmt_idx)

        qual_idx = self._settings.value("last_quality_index", 0, type=int)
        if 0 <= qual_idx < self.quality_combo.count():
            self.quality_combo.setCurrentIndex(qual_idx)

        aq_idx = self._settings.value("last_aq_index", 0, type=int)
        if 0 <= aq_idx < self.aq_combo.count():
            self.aq_combo.setCurrentIndex(aq_idx)

        self._on_format_change()

    def _save_settings(self):
        self._settings.setValue("window_geometry", self.saveGeometry())
        self._settings.setValue("last_out_dir", self._out_dir)
        self._settings.setValue("last_format_index", self.fmt_combo.currentIndex())
        self._settings.setValue("last_quality_index", self.quality_combo.currentIndex())
        self._settings.setValue("last_aq_index", self.aq_combo.currentIndex())

    # ── Format değişimi ──────────────────────────────────

    def _on_format_change(self):
        data = self.fmt_combo.currentData()
        if not data:
            return
        is_video = data["type"] == "video"
        self.qual_w.setVisible(is_video)
        self.aq_w.setVisible(not is_video)

    # ── Yardımcı ────────────────────────────────────────

    # ── Clipboard watcher ─────────────────────────────────

    def _start_clipboard_watcher(self):
        self._last_clip = ""
        self._clip_timer = QTimer(self)
        self._clip_timer.timeout.connect(self._check_clipboard)
        self._clip_timer.start(1500)

    def _check_clipboard(self):
        """Panoda YouTube linki varsa otomatik yapıştır."""
        if self._thread and self._thread.isRunning():
            return
        if self.url_input.text().strip():
            return
        cb = QApplication.clipboard().text().strip()
        if cb == self._last_clip:
            return
        self._last_clip = cb
        if re.match(r'https?://(www\.)?(youtube\.com|youtu\.be)/', cb):
            self.url_input.setText(cb)
            self._fetch_thumbnail(cb)

    def _paste_url(self):
        cb = QApplication.clipboard()
        url = cb.text().strip()
        self.url_input.setText(url)
        if re.match(r'https?://(www\.)?(youtube\.com|youtu\.be)/', url):
            self._fetch_thumbnail(url)

    # ── Thumbnail ─────────────────────────────────────────

    def _fetch_thumbnail(self, url: str):
        if self._thumb_fetcher and self._thumb_fetcher.isRunning():
            return
        self._thumb_fetcher = ThumbnailFetcher(url)
        self._thumb_fetcher.result.connect(self._on_thumbnail)
        self._thumb_fetcher.error.connect(self._on_thumb_error)
        self._thumb_fetcher.start()

    def _on_thumbnail(self, title: str, dur: str, thumb_path: str):
        if title:
            self.video_title_lbl.setText(f"📺  {title}")
            self.video_title_lbl.show()
        if thumb_path and os.path.exists(thumb_path):
            pix = QPixmap(thumb_path)
            if not pix.isNull():
                self._thumb_lbl.setPixmap(
                    pix.scaled(160, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
                self._thumb_lbl.show()
        if dur:
            self._video_info_lbl.setText(f"Süre: {dur}")
            self._video_info_lbl.show()

    def _on_thumb_error(self):
        pass  # Thumbnail alınamazsa sessizce geç

    def _choose_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Kayıt Klasörü Seç", self._out_dir)
        if d:
            self._out_dir = d
            self.dir_input.setText(d)

    # ── İndirme ─────────────────────────────────────────

    def _start_download(self):
        url = self.url_input.text().strip()
        if not url:
            self._set_status("URL girin.", "err")
            return
        if self._thread and self._thread.isRunning():
            return

        fmt         = self.fmt_combo.currentData()
        quality_fmt = self.quality_combo.currentData()
        audio_q     = self.aq_combo.currentData()

        self._thread = DownloadThread(
            url, self._out_dir, fmt, quality_fmt, audio_q,
            download_subs=self._sub_chk.isChecked()
        )

        # Eski bağlantıları koparmak için yeni thread nesnesi üzerinde bağla
        # (yeni nesne olduğundan eski sinyaller zaten yok; güvenli)
        self._thread.progress.connect(self._on_progress)
        self._thread.finished.connect(self._on_finished)
        self._thread.error.connect(self._on_error)
        self._thread.info_ready.connect(self._on_info)
        self._thread.start()

        self.dl_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self._set_status("Bilgi alınıyor...", "dl")

    def _cancel(self):
        if self._thread:
            self._thread.cancel()
        self.cancel_btn.setEnabled(False)
        self._set_status("İptal ediliyor...", "dl")

    # ── Sinyaller ────────────────────────────────────────

    def _on_info(self, title: str):
        if title:
            self.video_title_lbl.setText(f"📺  {title}")
            self.video_title_lbl.show()
        self._set_status("İndiriliyor...", "dl")

    def _on_progress(self, pct: float, label: str):
        self.progress_bar.setValue(int(pct))
        if label:
            self._set_status(label, "dl")

    def _on_finished(self, out_dir: str):
        self.progress_bar.setValue(100)
        self._set_status("✓ İndirme tamamlandı!", "ok")
        self.dl_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)

        title = self.video_title_lbl.text().replace("📺  ", "")
        self._add_history(title or "İndirildi", out_dir)

    def _on_error(self, msg: str):
        msg_lower = msg.lower()
        if "cancelled" in msg_lower or "i̇ptal" in msg_lower or "iptal" in msg_lower:
            self._set_status(f"ℹ {msg}", "dl")
        else:
            self._set_status(f"Hata: {msg}", "err")
        self.dl_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)

    def _set_status(self, text: str, kind: str = "ok"):
        obj = {"ok": "status_ok", "err": "status_err", "dl": "status_dl"}.get(kind, "status_ok")
        self.status_lbl.setText(text)
        self.status_lbl.setObjectName(obj)
        self.status_lbl.setStyle(self.status_lbl.style())

    def _add_history(self, title: str, out_dir: str):
        card = DownloadCard(title, out_dir)
        idx  = self._history_layout.count() - 1
        self._history_layout.insertWidget(idx, card)
        self.empty_history.hide()

    # ── System tray ──────────────────────────────────────

    def _setup_tray(self):
        px = QPixmap(32, 32)
        px.fill(Qt.transparent)
        p = QPainter(px)
        p.setBrush(QColor("#6c5ce7"))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(0, 0, 32, 32, 8, 8)
        p.setPen(QColor("#fff"))
        f = QFont("Arial", 14, QFont.Bold)
        p.setFont(f)
        p.drawText(px.rect(), Qt.AlignCenter, "▼")
        p.end()

        self.tray = QSystemTrayIcon(QIcon(px), self)
        self.tray.setToolTip("YT Downloader")

        menu = QMenu()
        show_act = QAction("Göster", self)
        show_act.triggered.connect(self._show_window)
        quit_act = QAction("Çıkış", self)
        quit_act.triggered.connect(QApplication.quit)
        menu.addAction(show_act)
        menu.addSeparator()
        menu.addAction(quit_act)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(
            lambda r: self._show_window() if r == QSystemTrayIcon.DoubleClick else None
        )
        self.tray.show()

    def _show_window(self):
        self.show()
        self.activateWindow()
        self.raise_()

    def closeEvent(self, event):
        self._save_settings()
        event.ignore()
        self.hide()


# ─────────────────────────────────────────────────────────
#  GİRİŞ NOKTASI
# ─────────────────────────────────────────────────────────

def main():
    if getattr(sys, "frozen", False):
        os.chdir(os.path.dirname(sys.executable))
    else:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("YT Downloader")

    win = MainWindow()
    win.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
