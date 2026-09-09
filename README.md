# yt-dlp-app

A small PyQt6 GUI front-end for [yt-dlp](https://github.com/yt-dlp/yt-dlp).

Paste a URL, tick "playlist" if it is one, pick a quality tier on the
**Video** or **Audio only** tab, hit Download.

## Requirements

- Python 3.10+
- [`uv`](https://docs.astral.sh/uv/)
- **ffmpeg** installed and on your `PATH` (needed for merging video+audio
  streams and for audio extraction/transcoding). This is *not* a Python
  dependency and `uv sync` will not install it for you:
  - Fedora/RHEL: `sudo dnf install ffmpeg`
  - Debian/Ubuntu: `sudo apt install ffmpeg`
  - Arch: `sudo pacman -S ffmpeg`
  - macOS (Homebrew): `brew install ffmpeg`

## Setup

```bash
cd yt-dlp-app
uv sync
uv run yt-dlp-app
```

`uv sync` reads `pyproject.toml`, creates `.venv/`, and installs `yt-dlp`
and `PyQt6`. `uv run yt-dlp-app` launches the GUI using the entry point
defined in `pyproject.toml`.

## Project layout

```
yt-dlp-app/
  pyproject.toml
  README.md
  src/
    yt_dlp_app/
      __init__.py
      main.py       # entry point, creates QApplication + MainWindow
      gui.py         # MainWindow: all widgets & the download-trigger logic
      worker.py      # QThread subclass that runs yt-dlp off the UI thread
      formats.py     # quality/codec tables + format-string helpers
```

## Notes / things you'll likely want to tweak

- **Quality tiers** live in `formats.py` (`VIDEO_QUALITIES`, `AUDIO_CODECS`,
  `AUDIO_QUALITIES`) - add or remove entries there and the UI picks them
  up automatically, no GUI code changes needed.
- **Output filenames** use yt-dlp's `outtmpl` templating, set in
  `gui.py -> _start_download`. Currently: flat `Title.ext` for single
  videos, `PlaylistName/001 - Title.ext` for playlists.
- **Cancellation** is best-effort (`DownloadWorker.cancel()`) - it stops
  after the file currently being fetched finishes, since yt-dlp doesn't
  offer a clean mid-file abort. There's no cancel button wired up in the
  UI yet if you want to add one.
- **yt-dlp updates itself independently** of this app - since it's used
  here as a normal pinned dependency, run `uv lock --upgrade-package yt-dlp`
  occasionally (YouTube changes break older yt-dlp versions fairly often).

## Packaging as a Flatpak later

This app itself doesn't need any Flatpak-specific code - a Flatpak
manifest just describes how to build this same project inside a sandboxed
runtime. The two things worth knowing ahead of time:

- You'll want the `org.kde.Platform` / `org.kde.Sdk` runtime (has Qt6
  already), plus python3-yt-dlp packaged as a module or via pip inside
  the build.
- ffmpeg isn't in the base runtime - you'd add the
  `org.freedesktop.Platform.ffmpeg-full` extension to the manifest rather
  than compiling ffmpeg yourself.

Happy to help write the actual `.yml`/`.json` Flatpak manifest once the
app itself is working the way you want.
