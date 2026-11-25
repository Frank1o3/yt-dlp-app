from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QStandardPaths
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .formats import (
    AUDIO_CODECS,
    AUDIO_QUALITIES,
    LOSSLESS_CODECS,
    VIDEO_CONTAINERS,
    VIDEO_QUALITIES,
    is_probably_youtube_url,
    video_format_string,
)
from .worker import DownloadWorker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("yt-dlp-app")
        # Fixed-size utility window: setFixedSize pins min == max, which
        # also disables the maximize button and drag-to-resize handles.
        self.setFixedSize(640, 560)

        self.worker: DownloadWorker | None = None
        self.output_dir = Path(
            QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation)
            or str(Path.home() / "Downloads")
        ) / "VideoDownloader"

        self._build_ui()

    # ------------------------------------------------------------------ UI

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # --- URL + playlist row ---
        url_row = QFormLayout()
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://www.youtube.com/watch?v=...")
        url_row.addRow("Video URL:", self.url_edit)
        root.addLayout(url_row)

        self.playlist_check = QCheckBox("This is a playlist - download all videos in it")
        root.addWidget(self.playlist_check)

        # --- output folder row ---
        out_row = QHBoxLayout()
        self.output_label = QLabel(str(self.output_dir))
        self.output_label.setWordWrap(True)
        choose_btn = QPushButton("Choose folder...")
        choose_btn.clicked.connect(self._choose_output_dir)
        out_row.addWidget(QLabel("Save to:"))
        out_row.addWidget(self.output_label, stretch=1)
        out_row.addWidget(choose_btn)
        root.addLayout(out_row)

        # --- tabs: Video / Audio only ---
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_video_tab(), "Video")
        self.tabs.addTab(self._build_audio_tab(), "Audio only")
        root.addWidget(self.tabs)

        # --- download button ---
        self.download_btn = QPushButton("Download")
        self.download_btn.clicked.connect(self._start_download)
        root.addWidget(self.download_btn)

        # --- log ---
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(500)
        root.addWidget(self.log, stretch=1)

    def _build_video_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        quality_box = QGroupBox("Video quality")
        quality_layout = QVBoxLayout(quality_box)
        self.video_quality_group = QButtonGroup(tab)
        for i, label in enumerate(VIDEO_QUALITIES):
            btn = QRadioButton(label)
            if i == 0:
                btn.setChecked(True)
            self.video_quality_group.addButton(btn, i)
            quality_layout.addWidget(btn)
        layout.addWidget(quality_box)

        container_row = QFormLayout()
        self.video_container_combo = QComboBox()
        self.video_container_combo.addItems(VIDEO_CONTAINERS)
        container_row.addRow("Container:", self.video_container_combo)
        layout.addLayout(container_row)

        layout.addStretch(1)
        return tab

    def _build_audio_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        format_row = QFormLayout()
        self.audio_format_combo = QComboBox()
        self.audio_format_combo.addItems(AUDIO_CODECS)
        self.audio_format_combo.currentTextChanged.connect(self._on_audio_codec_changed)
        format_row.addRow("Audio format:", self.audio_format_combo)
        layout.addLayout(format_row)

        self.audio_quality_box = QGroupBox("Audio quality")
        quality_layout = QVBoxLayout(self.audio_quality_box)
        self.audio_quality_group = QButtonGroup(tab)
        for i, label in enumerate(AUDIO_QUALITIES):
            btn = QRadioButton(label)
            if i == 0:
                btn.setChecked(True)
            self.audio_quality_group.addButton(btn, i)
            quality_layout.addWidget(btn)
        layout.addWidget(self.audio_quality_box)

        layout.addStretch(1)
        return tab

    def _on_audio_codec_changed(self, codec: str):
        # Bitrate doesn't mean anything for lossless formats.
        self.audio_quality_box.setEnabled(codec not in LOSSLESS_CODECS)

    # ------------------------------------------------------------ actions

    def _choose_output_dir(self):
        chosen = QFileDialog.getExistingDirectory(self, "Choose output folder", str(self.output_dir))
        if chosen:
            self.output_dir = Path(chosen)
            self.output_label.setText(str(self.output_dir))

    def _selected_label(self, group: QButtonGroup, labels: list[str]) -> str:
        return labels[group.checkedId()]

    def _start_download(self):
        url = self.url_edit.text().strip()
        if not url:
            QMessageBox.warning(self, "Missing URL", "Paste a YouTube video or playlist URL first.")
            return
        if not is_probably_youtube_url(url):
            reply = QMessageBox.question(
                self,
                "Unrecognized URL",
                "That doesn't look like a typical YouTube video/playlist URL. Continue anyway?",
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        is_playlist = self.playlist_check.isChecked()
        outtmpl = str(
            self.output_dir
            / ("%(playlist_title)s/%(playlist_index)03d - %(title)s.%(ext)s" if is_playlist
               else "%(title)s.%(ext)s")
        )

        base_opts = {
            "outtmpl": outtmpl,
            "noplaylist": not is_playlist,
            "ignoreerrors": True,
            "windowsfilenames": True,
            "color": "no_color",
        }

        if self.tabs.currentIndex() == 0:
            # Video tab
            labels = list(VIDEO_QUALITIES.keys())
            chosen_label = self._selected_label(self.video_quality_group, labels)
            max_height = VIDEO_QUALITIES[chosen_label]
            ydl_opts = {
                **base_opts,
                "format": video_format_string(max_height),
                "merge_output_format": self.video_container_combo.currentText(),
            }
        else:
            # Audio-only tab
            codec = self.audio_format_combo.currentText()
            labels = list(AUDIO_QUALITIES.keys())
            chosen_label = self._selected_label(self.audio_quality_group, labels)
            quality = AUDIO_QUALITIES[chosen_label]
            ydl_opts = {
                **base_opts,
                "format": "bestaudio/best",
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": codec,
                        "preferredquality": quality,
                    }
                ],
            }

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log.appendPlainText(f"Starting download: {url}")
        self.download_btn.setEnabled(False)
        self.download_btn.setText("Downloading...")

        self.worker = DownloadWorker(url, ydl_opts)
        self.worker.progress.connect(self.log.appendPlainText)
        self.worker.finished_ok.connect(self._on_finished)
        self.worker.failed.connect(self._on_failed)
        self.worker.start()

    def _reset_button(self):
        self.download_btn.setEnabled(True)
        self.download_btn.setText("Download")

    def _on_finished(self):
        self.log.appendPlainText("Done.")
        self._reset_button()

    def _on_failed(self, message: str):
        self.log.appendPlainText(f"Error: {message}")
        QMessageBox.critical(self, "Download failed", message)
        self._reset_button()
