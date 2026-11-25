"""Unit tests for the pure format and URL helpers."""

from __future__ import annotations

import unittest

from yt_dlp_app.formats import is_valid_media_url, video_format_string


class VideoFormatStringTests(unittest.TestCase):
    def test_best_available_does_not_apply_a_height_limit(self) -> None:
        self.assertEqual(video_format_string(None), "bestvideo+bestaudio/best")

    def test_height_limit_is_applied_to_both_fallbacks(self) -> None:
        self.assertEqual(
            video_format_string(1080),
            "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        )


class MediaUrlValidationTests(unittest.TestCase):
    def test_accepts_http_and_https_urls(self) -> None:
        self.assertTrue(is_valid_media_url("https://example.com/video"))
        self.assertTrue(is_valid_media_url("http://example.com/video"))

    def test_rejects_missing_scheme_or_host(self) -> None:
        self.assertFalse(is_valid_media_url("example.com/video"))
        self.assertFalse(is_valid_media_url("https:///video"))

    def test_rejects_non_http_schemes(self) -> None:
        self.assertFalse(is_valid_media_url("javascript:alert(1)"))
        self.assertFalse(is_valid_media_url("file:///tmp/video.mp4"))


if __name__ == "__main__":
    unittest.main()
