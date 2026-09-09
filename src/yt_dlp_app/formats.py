"""
Format/quality option tables and helpers for building yt-dlp option dicts.

Keeping these separate from the GUI code means you can add new quality
tiers or codecs here without touching any Qt code.
"""

from __future__ import annotations

# Label shown in the UI -> max height in pixels (None = no cap, i.e. "best")
VIDEO_QUALITIES: dict[str, int | None] = {
    "Best available": None,
    "2160p (4K)": 2160,
    "1440p (2K / QHD)": 1440,
    "1080p (Full HD)": 1080,
    "720p (HD)": 720,
    "480p (SD)": 480,
    "360p": 360,
}

# Container format used when muxing/remuxing downloaded video
VIDEO_CONTAINERS: list[str] = ["mp4", "mkv", "webm"]

# Audio-only output codecs that yt-dlp/ffmpeg can produce out of the box
AUDIO_CODECS: list[str] = ["mp3", "m4a", "opus", "vorbis", "wav", "flac"]

# Label shown in the UI -> preferredquality value passed to the
# FFmpegExtractAudio postprocessor. For lossy codecs (mp3/m4a/opus/vorbis)
# lower numbers mean better quality for VBR-style values; yt-dlp accepts
# "0" (best) through "9" (worst), or an explicit bitrate like "192".
# For lossless codecs (wav/flac) this value is ignored by yt-dlp/ffmpeg.
AUDIO_QUALITIES: dict[str, str] = {
    "Best": "0",
    "High (~192 kbps)": "192",
    "Medium (~128 kbps)": "128",
    "Low (~64 kbps)": "64",
}

# Codecs where the "quality" concept doesn't really apply
LOSSLESS_CODECS = {"wav", "flac"}


def video_format_string(max_height: int | None) -> str:
    """Build a yt-dlp -f format selector string for a given height cap."""
    if max_height is None:
        return "bestvideo+bestaudio/best"
    return f"bestvideo[height<={max_height}]+bestaudio/best[height<={max_height}]"


def is_probably_youtube_url(url: str) -> bool:
    """Very small sanity check, not a substitute for yt-dlp's own validation."""
    url = url.strip().lower()
    return ("youtube.com/watch" in url
            or "youtube.com/playlist" in url
            or "youtu.be/" in url
            or "youtube.com/shorts" in url)
