"""
Background worker that runs a yt-dlp download without blocking the GUI.

yt-dlp's progress_hooks callback fires on whatever thread .download() is
called from -- since that's this QThread's run() method, it's safe to
emit Qt signals from inside the hook; Qt marshals the signal back to the
main thread automatically because the receiver (MainWindow) lives there.
"""

from __future__ import annotations

import re

import yt_dlp
from PyQt6.QtCore import QThread, pyqtSignal

# yt-dlp's _percent_str/_speed_str/_eta_str come pre-colored with ANSI
# escape codes (it assumes it's writing to a terminal). A QPlainTextEdit
# doesn't interpret those, so they show up as literal "[0;94m" noise -
# strip them before they ever reach the UI.
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


class DownloadWorker(QThread):
    progress = pyqtSignal(str)
    finished_ok = pyqtSignal()
    failed = pyqtSignal(str)

    def __init__(self, url: str, ydl_opts: dict, parent=None):
        super().__init__(parent)
        self.url = url
        self.ydl_opts = ydl_opts
        self._cancelled = False

    def cancel(self):
        # yt-dlp checks this via a match_filter trick isn't ideal for
        # mid-download cancellation; simplest reliable approach is to
        # just let the current file finish and stop the queue.
        self._cancelled = True

    def _hook(self, d: dict):
        if self._cancelled:
            raise yt_dlp.utils.DownloadError("Cancelled by user")

        status = d.get("status")
        if status == "downloading":
            pct = _strip_ansi((d.get("_percent_str") or "").strip())
            speed = _strip_ansi((d.get("_speed_str") or "").strip())
            eta = _strip_ansi((d.get("_eta_str") or "").strip())
            name = d.get("filename", "")
            self.progress.emit(f"{pct}  {speed}  ETA {eta}  -  {name}")
        elif status == "finished":
            self.progress.emit(f"Downloaded, post-processing: {d.get('filename', '')}")

    def run(self):
        opts = dict(self.ydl_opts)
        opts["progress_hooks"] = [self._hook]
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([self.url])
            if self._cancelled:
                self.failed.emit("Cancelled.")
            else:
                self.finished_ok.emit()
        except Exception as exc:  # noqa: BLE001 - surface any failure to the UI
            self.failed.emit(str(exc))
