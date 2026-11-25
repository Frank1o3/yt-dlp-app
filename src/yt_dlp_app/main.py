"""Application entry point."""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from . import __version__
from .gui import MainWindow


def main() -> int:
    """Create the Qt application and start its event loop."""
    app = QApplication(sys.argv)
    app.setApplicationName("yt-dlp-app")
    app.setApplicationDisplayName("yt-dlp-app")
    app.setApplicationVersion(__version__)

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
