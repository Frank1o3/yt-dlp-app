"""Run yt-dlp in a worker thread and forward logs and progress to the UI."""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from threading import Event
from typing import Any

import yt_dlp
from PyQt6.QtCore import QObject, QThread, pyqtSignal

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_ansi(value: str) -> str:
    """Remove terminal color codes before showing yt-dlp output in Qt."""
    return _ANSI_RE.sub("", value)


class _DownloadLogger:
    """Adapt yt-dlp's logger callbacks to the worker's Qt progress signal."""

    def __init__(self, emit: Callable[[str], None]) -> None:
        self._emit = emit

    def debug(self, message: str) -> None:
        if message and not message.startswith("[debug]"):
            self._emit(_strip_ansi(message))

    def warning(self, message: str) -> None:
        if message:
            self._emit(f"Warning: {_strip_ansi(message)}")

    def error(self, message: str) -> None:
        if message:
            self._emit(f"Error: {_strip_ansi(message)}")


class DownloadWorker(QThread):
    """Execute one yt-dlp download without blocking Qt's main thread."""

    progress = pyqtSignal(str, int)
    completed = pyqtSignal()
    failed = pyqtSignal(str)
    cancelled = pyqtSignal()

    def __init__(
        self,
        url: str,
        ydl_options: Mapping[str, Any],
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.url = url
        self.ydl_options = dict(ydl_options)
        self._cancel_requested = Event()

    def cancel(self) -> None:
        """Request cancellation; yt-dlp stops at its next progress callback."""
        self._cancel_requested.set()

    def _emit_log(self, message: str) -> None:
        self.progress.emit(message, -1)

    def _progress_hook(self, data: dict[str, Any]) -> None:
        if self._cancel_requested.is_set():
            raise yt_dlp.utils.DownloadError("Download cancelled by user.")

        status = data.get("status")
        filename = str(data.get("filename") or "media item")

        if status == "downloading":
            downloaded = data.get("downloaded_bytes")
            total = data.get("total_bytes") or data.get("total_bytes_estimate")
            percentage = -1
            if (
                isinstance(downloaded, (int, float))
                and isinstance(total, (int, float))
                and total > 0
            ):
                percentage = round(downloaded / total * 100)

            percent_text = _strip_ansi(str(data.get("_percent_str") or "")).strip()
            speed = _strip_ansi(str(data.get("_speed_str") or "")).strip()
            eta = _strip_ansi(str(data.get("_eta_str") or "")).strip()
            details = [part for part in (percent_text, speed, f"ETA {eta}" if eta else "") if part]
            summary = "  ·  ".join(details)
            message = f"Downloading {filename}"
            if summary:
                message = f"{message}  —  {summary}"
            self.progress.emit(message, percentage)
        elif status == "finished":
            self.progress.emit(f"Download finished; processing {filename}", 100)

    def run(self) -> None:
        options = dict(self.ydl_options)
        options["progress_hooks"] = [self._progress_hook]
        options["logger"] = _DownloadLogger(self._emit_log)
        options.setdefault("quiet", True)

        try:
            with yt_dlp.YoutubeDL(options) as downloader:
                error_code = downloader.download([self.url])

            if self._cancel_requested.is_set():
                self.cancelled.emit()
            elif error_code:
                self.failed.emit(f"yt-dlp exited with status code {error_code}.")
            else:
                self.completed.emit()
        except yt_dlp.utils.DownloadError as exc:
            if self._cancel_requested.is_set():
                self.cancelled.emit()
            else:
                self.failed.emit(str(exc))
        except Exception as exc:  # noqa: BLE001 - surface unexpected worker failures to the UI
            if self._cancel_requested.is_set():
                self.cancelled.emit()
            else:
                self.failed.emit(f"Unexpected download error: {exc}")
