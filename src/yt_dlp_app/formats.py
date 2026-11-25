"""Quality presets and small helpers for building yt-dlp options."""

from __future__ import annotations

from urllib.parse import urlsplit

# UI label -> maximum video height in pixels. None means no height cap.
VIDEO_QUALITIES: dict[str, int | None] = {
    "Best available": None,
    "2160p (4K)": 2160,
    "1440p (QHD)": 1440,
    "1080p (Full HD)": 1080,
    "720p (HD)": 720,
    "480p (SD)": 480,
    "360p": 360,
}

VIDEO_CONTAINERS: tuple[str, ...] = ("mp4", "mkv", "webm")
AUDIO_CODECS: tuple[str, ...] = ("mp3", "m4a", "opus", "vorbis", "wav", "flac")

# UI label -> preferredquality value accepted by FFmpegExtractAudio.
AUDIO_QUALITIES: dict[str, str] = {
    "Best": "0",
    "High (~192 kbps)": "192",
    "Medium (~128 kbps)": "128",
    "Low (~64 kbps)": "64",
}

LOSSLESS_CODECS = frozenset({"wav", "flac"})


def video_format_string(max_height: int | None) -> str:
    """Return a yt-dlp format selector with an optional height ceiling."""
    if max_height is None:
        return "bestvideo+bestaudio/best"
    return f"bestvideo[height<={max_height}]+bestaudio/best[height<={max_height}]"


def is_valid_media_url(url: str) -> bool:
    """Check for an absolute HTTP(S) URL before passing it to yt-dlp."""
    parsed = urlsplit(url.strip())
    return parsed.scheme.casefold() in {"http", "https"} and bool(parsed.netloc)
