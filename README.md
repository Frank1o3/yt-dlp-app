# yt-dlp-app

A lightweight PyQt6 desktop interface for [yt-dlp](https://github.com/yt-dlp/yt-dlp). Paste a supported media URL, choose video or audio output, and download without using the terminal.

## Features

- Video downloads with maximum-resolution presets from 360p through 4K
- Audio extraction to MP3, M4A, Opus, Vorbis, WAV, or FLAC
- Playlist downloads with a separate folder and numbered filenames
- Configurable output directory
- Background downloads so the interface remains responsive
- Progress and activity output, with cancellation support
- Uses yt-dlp's supported sites rather than being limited to YouTube

## Requirements

- Python 3.14 or newer
- [uv](https://docs.astral.sh/uv/)
- ffmpeg available on PATH for merging separate video/audio streams and audio conversion

On Arch Linux and CachyOS:

```bash
sudo pacman -S ffmpeg
```

Other platforms can install FFmpeg from their package manager or from the [official download page](https://ffmpeg.org/download.html).

## Install and run

```bash
git clone https://github.com/Frank1o3/yt-dlp-app.git
cd yt-dlp-app
uv sync
uv run yt-dlp-app
```

uv sync creates .venv/, installs the two runtime dependencies, and installs the application in editable mode so the yt-dlp-app command is available inside the project environment.

To refresh dependency versions within the ranges in pyproject.toml:

```bash
uv sync --upgrade
```

uv sync --upgrade updates the environment and uv.lock; it does not rewrite the version ranges in pyproject.toml. Commit uv.lock so other machines resolve the same versions. The lockfile is intentionally not ignored by Git.

## Development in Visual Studio Code

The repository includes .vscode/settings.json, .vscode/extensions.json, and .editorconfig.

The workspace uses:

- **Pylance** for completions, navigation, hover, and import support
- **ty** for workspace-wide type diagnostics
- **Ruff** for linting, import organization, and formatting
- **EditorConfig** for consistent whitespace and line endings

Pylance type checking is disabled in the workspace to avoid duplicate type diagnostics. The ty extension is configured with its language features disabled, so it acts as the type checker while Pylance remains the primary language server. Ruff reads its configuration from pyproject.toml.

After opening the project, select the repository's .venv interpreter if VS Code has not selected it automatically. Run uv sync again after changing the runtime dependencies.

## Project layout

```text
yt-dlp-app/
├── .editorconfig
├── .vscode/
│   ├── extensions.json
│   ├── launch.json
│   └── settings.json
├── pyproject.toml
├── README.md
├── tests/
│   └── test_formats.py
└── src/
    └── yt_dlp_app/
        ├── __init__.py
        ├── formats.py
        ├── gui.py
        ├── main.py
        └── worker.py
```

## Configuration

The application dependencies are deliberately limited to PyQt6 and yt-dlp. Ruff and ty are editor/tooling integrations and are not runtime dependencies. No Flatpak manifest, installer packaging workflow, or Makefile is required to run the application from source.

Video quality presets, output containers, audio codecs, and audio quality choices are defined in src/yt_dlp_app/formats.py.
