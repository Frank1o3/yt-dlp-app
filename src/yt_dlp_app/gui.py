"""Qt interface for configuring and monitoring yt-dlp downloads."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QStandardPaths, Qt
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
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
    is_valid_media_url,
    video_format_string,
)
from .worker import DownloadWorker


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("yt-dlp-app")
        self.setMinimumSize(720, 680)
        self.resize(820, 760)

        self.worker: DownloadWorker | None = None
        download_location = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.DownloadLocation
        )
        self.output_dir = (
            Path(download_location) if download_location else Path.home() / "Downloads"
        ) / "VideoDownloader"

        self._build_ui()
        self._apply_style()

    def _build_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(26, 24, 26, 24)
        root_layout.setSpacing(16)

        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)

        eyebrow = QLabel("MEDIA DOWNLOADER")
        eyebrow.setObjectName("eyebrow")
        header_layout.addWidget(eyebrow)

        title = QLabel("Download media")
        title.setObjectName("pageTitle")
        header_layout.addWidget(title)

        subtitle = QLabel("Paste a link, choose a format, and save it to your device.")
        subtitle.setObjectName("mutedText")
        header_layout.addWidget(subtitle)
        root_layout.addLayout(header_layout)

        source_card = QFrame()
        source_card.setObjectName("card")
        source_layout = QVBoxLayout(source_card)
        source_layout.setContentsMargins(18, 16, 18, 16)
        source_layout.setSpacing(10)

        source_label = QLabel("Media URL")
        source_label.setObjectName("sectionTitle")
        source_layout.addWidget(source_label)

        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://www.youtube.com/watch?v=...")
        self.url_edit.setClearButtonEnabled(True)
        self.url_edit.setMinimumHeight(42)
        self.url_edit.returnPressed.connect(self._start_download)
        source_layout.addWidget(self.url_edit)

        self.playlist_check = QCheckBox("Download the full playlist when the link contains one")
        source_layout.addWidget(self.playlist_check)
        root_layout.addWidget(source_card)

        destination_card = QFrame()
        destination_card.setObjectName("card")
        destination_layout = QVBoxLayout(destination_card)
        destination_layout.setContentsMargins(18, 16, 18, 16)
        destination_layout.setSpacing(10)

        destination_title = QLabel("Save location")
        destination_title.setObjectName("sectionTitle")
        destination_layout.addWidget(destination_title)

        destination_row = QHBoxLayout()
        destination_row.setSpacing(12)
        self.output_label = QLabel(str(self.output_dir))
        self.output_label.setObjectName("pathLabel")
        self.output_label.setWordWrap(True)
        self.output_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.output_label.setToolTip(str(self.output_dir))
        destination_row.addWidget(self.output_label, stretch=1)

        choose_button = QPushButton("Choose folder")
        choose_button.setObjectName("secondaryButton")
        choose_button.clicked.connect(self._choose_output_dir)
        destination_row.addWidget(choose_button)
        destination_layout.addLayout(destination_row)
        root_layout.addWidget(destination_card)

        format_card = QFrame()
        format_card.setObjectName("card")
        format_layout = QVBoxLayout(format_card)
        format_layout.setContentsMargins(12, 10, 12, 12)
        format_layout.setSpacing(8)

        format_title = QLabel("Download format")
        format_title.setObjectName("sectionTitle")
        format_layout.addWidget(format_title)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.addTab(self._build_video_tab(), "Video")
        self.tabs.addTab(self._build_audio_tab(), "Audio only")
        format_layout.addWidget(self.tabs)
        root_layout.addWidget(format_card)

        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("statusLabel")
        controls_layout.addWidget(self.status_label, stretch=1)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setObjectName("dangerButton")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self._cancel_download)
        controls_layout.addWidget(self.cancel_button)

        self.download_button = QPushButton("Download")
        self.download_button.setObjectName("primaryButton")
        self.download_button.setMinimumWidth(132)
        self.download_button.setMinimumHeight(40)
        self.download_button.clicked.connect(self._start_download)
        controls_layout.addWidget(self.download_button)
        root_layout.addLayout(controls_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setFixedHeight(9)
        root_layout.addWidget(self.progress_bar)

        log_header = QHBoxLayout()
        log_title = QLabel("Activity")
        log_title.setObjectName("sectionTitle")
        log_header.addWidget(log_title)
        log_header.addStretch(1)

        clear_button = QPushButton("Clear")
        clear_button.setObjectName("textButton")
        clear_button.clicked.connect(self._clear_log)
        log_header.addWidget(clear_button)
        root_layout.addLayout(log_header)

        self.log = QPlainTextEdit()
        self.log.setObjectName("logView")
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(500)
        self.log.setPlaceholderText("Download activity and messages will appear here.")
        self.log.setMinimumHeight(118)
        root_layout.addWidget(self.log, stretch=1)

        if shutil.which("ffmpeg"):
            ffmpeg_message = "ffmpeg detected — merging and audio conversion are available."
        else:
            ffmpeg_message = "ffmpeg not found — install it for video merging and audio conversion."
        self.ffmpeg_label = QLabel(ffmpeg_message)
        self.ffmpeg_label.setObjectName("mutedText")
        root_layout.addWidget(self.ffmpeg_label)

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background: #10131a;
                color: #e7eaf0;
                font-family: "Inter", "Segoe UI", sans-serif;
                font-size: 13px;
            }
            QLabel#eyebrow {
                color: #8b9bb6;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 1.6px;
            }
            QLabel#pageTitle {
                color: #f5f7fb;
                font-size: 27px;
                font-weight: 700;
            }
            QLabel#sectionTitle {
                color: #f0f2f7;
                font-size: 14px;
                font-weight: 650;
            }
            QLabel#mutedText {
                color: #98a2b3;
                font-size: 11px;
            }
            QLabel#pathLabel {
                color: #bdc6d5;
                selection-background-color: #334b79;
            }
            QFrame#card {
                background: #181d27;
                border: 1px solid #2a3342;
                border-radius: 13px;
            }
            QLineEdit, QComboBox, QPlainTextEdit {
                background: #111620;
                color: #e7eaf0;
                border: 1px solid #303b4d;
                border-radius: 8px;
                padding: 8px 10px;
                selection-background-color: #365b9a;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #6d9df4;
            }
            QComboBox {
                min-height: 25px;
            }
            QComboBox QAbstractItemView {
                background: #181d27;
                color: #e7eaf0;
                selection-background-color: #304a76;
                border: 1px solid #303b4d;
            }
            QCheckBox, QRadioButton {
                spacing: 8px;
                color: #cbd3df;
            }
            QCheckBox::indicator, QRadioButton::indicator {
                width: 15px;
                height: 15px;
            }
            QGroupBox {
                background: #141a24;
                border: 1px solid #2b3545;
                border-radius: 10px;
                margin-top: 12px;
                padding: 12px 12px 10px 12px;
                font-weight: 600;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 5px;
                color: #aebbd0;
            }
            QTabWidget::pane {
                border: 1px solid #2b3545;
                border-radius: 9px;
                background: #141a24;
                top: -1px;
            }
            QTabBar::tab {
                background: transparent;
                color: #9ba8bb;
                padding: 10px 17px;
                margin-right: 4px;
                border-bottom: 2px solid transparent;
            }
            QTabBar::tab:selected {
                color: #f3f6fc;
                border-bottom: 2px solid #7aa7f7;
            }
            QPushButton {
                border: 1px solid #344154;
                border-radius: 8px;
                padding: 8px 13px;
                color: #dfe5ef;
                background: #252d3a;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #303b4d;
            }
            QPushButton:disabled {
                color: #687386;
                background: #202631;
                border-color: #29313e;
            }
            QPushButton#primaryButton {
                color: #ffffff;
                background: #3568b8;
                border-color: #4b7dcb;
            }
            QPushButton#primaryButton:hover {
                background: #4278ca;
            }
            QPushButton#dangerButton {
                color: #f1b7b7;
                background: #392328;
                border-color: #61333c;
            }
            QPushButton#dangerButton:hover {
                background: #4b2a32;
            }
            QPushButton#textButton {
                background: transparent;
                border-color: transparent;
                color: #91a8ce;
            }
            QProgressBar {
                background: #252d3a;
                border: none;
                border-radius: 4px;
                color: transparent;
            }
            QProgressBar::chunk {
                background: #6e9fe9;
                border-radius: 4px;
            }
            QPlainTextEdit#logView {
                background: #0d1118;
                border: 1px solid #293241;
                border-radius: 9px;
                color: #b8c5d8;
                font-family: "JetBrains Mono", "Cascadia Code", monospace;
                font-size: 11px;
            }
            """
        )

    def _build_video_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(14, 12, 14, 14)
        layout.setSpacing(12)

        quality_box = QGroupBox("Maximum resolution")
        quality_layout = QGridLayout(quality_box)
        quality_layout.setHorizontalSpacing(22)
        quality_layout.setVerticalSpacing(9)
        self.video_quality_group = QButtonGroup(tab)
        for index, label in enumerate(VIDEO_QUALITIES):
            button = QRadioButton(label)
            button.setChecked(index == 0)
            self.video_quality_group.addButton(button, index)
            quality_layout.addWidget(button, index // 2, index % 2)
        layout.addWidget(quality_box)

        container_row = QFormLayout()
        container_row.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        self.video_container_combo = QComboBox()
        self.video_container_combo.addItems(VIDEO_CONTAINERS)
        container_row.addRow("Container", self.video_container_combo)
        layout.addLayout(container_row)
        layout.addStretch(1)
        return tab

    def _build_audio_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(14, 12, 14, 14)
        layout.setSpacing(12)

        format_row = QFormLayout()
        self.audio_format_combo = QComboBox()
        self.audio_format_combo.addItems(AUDIO_CODECS)
        self.audio_format_combo.currentTextChanged.connect(self._on_audio_codec_changed)
        format_row.addRow("Audio format", self.audio_format_combo)
        layout.addLayout(format_row)

        self.audio_quality_box = QGroupBox("Audio quality")
        quality_layout = QGridLayout(self.audio_quality_box)
        quality_layout.setHorizontalSpacing(22)
        quality_layout.setVerticalSpacing(9)
        self.audio_quality_group = QButtonGroup(tab)
        for index, label in enumerate(AUDIO_QUALITIES):
            button = QRadioButton(label)
            button.setChecked(index == 0)
            self.audio_quality_group.addButton(button, index)
            quality_layout.addWidget(button, index // 2, index % 2)
        layout.addWidget(self.audio_quality_box)
        layout.addStretch(1)
        self._on_audio_codec_changed(self.audio_format_combo.currentText())
        return tab

    def _on_audio_codec_changed(self, codec: str) -> None:
        self.audio_quality_box.setEnabled(codec not in LOSSLESS_CODECS)

    def _choose_output_dir(self) -> None:
        selected = QFileDialog.getExistingDirectory(
            self,
            "Choose download folder",
            str(self.output_dir),
        )
        if selected:
            self.output_dir = Path(selected)
            self.output_label.setText(str(self.output_dir))
            self.output_label.setToolTip(str(self.output_dir))

    @staticmethod
    def _selected_label(group: QButtonGroup, labels: tuple[str, ...]) -> str:
        selected_id = group.checkedId()
        if 0 <= selected_id < len(labels):
            return labels[selected_id]
        return labels[0]

    def _start_download(self) -> None:
        if self.worker is not None and self.worker.isRunning():
            return

        url = self.url_edit.text().strip()
        if not is_valid_media_url(url):
            QMessageBox.warning(
                self,
                "Invalid URL",
                "Enter a complete media URL beginning with http:// or https://.",
            )
            self.url_edit.setFocus()
            return

        is_playlist = self.playlist_check.isChecked()
        filename_template = (
            "%(playlist_title)s/%(playlist_index)03d - %(title)s.%(ext)s"
            if is_playlist
            else "%(title)s.%(ext)s"
        )
        output_template = str(self.output_dir / filename_template)

        ydl_options: dict[str, Any] = {
            "outtmpl": output_template,
            "noplaylist": not is_playlist,
            "ignoreerrors": is_playlist,
            "windowsfilenames": True,
            "color": "no_color",
            "quiet": True,
        }

        if self.tabs.currentIndex() == 0:
            quality_labels = tuple(VIDEO_QUALITIES)
            selected_label = self._selected_label(self.video_quality_group, quality_labels)
            maximum_height = VIDEO_QUALITIES[selected_label]
            ydl_options.update(
                {
                    "format": video_format_string(maximum_height),
                    "merge_output_format": self.video_container_combo.currentText(),
                }
            )
        else:
            codec = self.audio_format_combo.currentText()
            quality_labels = tuple(AUDIO_QUALITIES)
            selected_label = self._selected_label(self.audio_quality_group, quality_labels)
            audio_processor: dict[str, str] = {
                "key": "FFmpegExtractAudio",
                "preferredcodec": codec,
            }
            if codec not in LOSSLESS_CODECS:
                audio_processor["preferredquality"] = AUDIO_QUALITIES[selected_label]
            ydl_options.update(
                {
                    "format": "bestaudio/best",
                    "postprocessors": [audio_processor],
                }
            )

        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            QMessageBox.critical(
                self,
                "Cannot create output folder",
                f"The selected folder could not be created:\n{exc}",
            )
            return

        self.log.appendPlainText(f"Starting download: {url}")
        self.status_label.setText("Preparing download…")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.download_button.setEnabled(False)
        self.download_button.setText("Downloading…")
        self.cancel_button.setEnabled(True)
        self.url_edit.setEnabled(False)
        self.playlist_check.setEnabled(False)
        self.tabs.setEnabled(False)

        self.worker = DownloadWorker(url, ydl_options)
        self.worker.progress.connect(self._on_progress)
        self.worker.completed.connect(self._on_download_completed)
        self.worker.failed.connect(self._on_download_failed)
        self.worker.cancelled.connect(self._on_download_cancelled)
        self.worker.finished.connect(self._on_worker_thread_finished)
        self.worker.start()

    def _on_progress(self, message: str, percentage: int) -> None:
        self.log.appendPlainText(message)
        if percentage >= 0:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(min(100, percentage))
            self.status_label.setText("Downloading")

    def _cancel_download(self) -> None:
        if self.worker is not None and self.worker.isRunning():
            self.worker.cancel()
            self.cancel_button.setEnabled(False)
            self.status_label.setText("Stopping download…")
            self.log.appendPlainText("Cancellation requested.")

    def _on_download_completed(self) -> None:
        self.log.appendPlainText("Download completed.")
        self.status_label.setText("Completed")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self._set_idle()

    def _on_download_failed(self, message: str) -> None:
        self.log.appendPlainText(f"Download failed: {message}")
        self.status_label.setText("Failed")
        self._set_idle()
        QMessageBox.critical(self, "Download failed", message)

    def _on_download_cancelled(self) -> None:
        self.log.appendPlainText("Download cancelled.")
        self.status_label.setText("Cancelled")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self._set_idle()

    def _on_worker_thread_finished(self) -> None:
        if self.worker is not None and not self.worker.isRunning():
            self.worker.deleteLater()
            self.worker = None

    def _set_idle(self) -> None:
        self.download_button.setEnabled(True)
        self.download_button.setText("Download")
        self.cancel_button.setEnabled(False)
        self.url_edit.setEnabled(True)
        self.playlist_check.setEnabled(True)
        self.tabs.setEnabled(True)

    def _clear_log(self) -> None:
        self.log.clear()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.worker is not None and self.worker.isRunning():
            self.worker.cancel()
            if not self.worker.wait(3000):
                QMessageBox.warning(
                    self,
                    "Download still stopping",
                    (
                        "The current network request has not finished yet. "
                        "Try closing the window again shortly."
                    ),
                )
                event.ignore()
                return
            self.worker.deleteLater()
            self.worker = None
        event.accept()
