"""Check the WebVTT subtitles and the video pages derived from the narrated MP4 videos."""

from __future__ import annotations

import io
import json
import re
import shutil
import subprocess
import unittest
from contextlib import redirect_stdout
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from scripts import build_media_pages
from scripts.build_guide import SITE_URL

ROOT = Path(__file__).resolve().parents[1]
MEDIA = ROOT / "docs/media"
FAMILIES = ("Foundry-Lab-Replay", "Foundry-Portal-Walkthrough")
PAGES = {"en": "index.html", "ko": "ko.html"}


class VideoPageParser(HTMLParser):
    """Collect each <video> with its source, subtitle track and the chapter links that follow it."""

    def __init__(self) -> None:
        super().__init__()
        self.language = ""
        self.videos: list[dict] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "html":
            self.language = values.get("lang") or ""
        elif tag == "video":
            self.videos.append({"source": "", "track": {}, "starts": []})
        elif self.videos and tag == "source":
            self.videos[-1]["source"] = values["src"]
        elif self.videos and tag == "track":
            self.videos[-1]["track"] = values
        elif self.videos and tag == "a" and "data-start" in values:
            self.videos[-1]["starts"].append(float(values["data-start"]))


class MediaPageTests(unittest.TestCase):
    def chapters(self) -> dict:
        return json.loads((MEDIA / "chapters.json").read_text(encoding="utf-8"))

    def test_generated_subtitles_and_pages_are_current(self) -> None:
        with redirect_stdout(io.StringIO()):
            self.assertEqual(build_media_pages.main(["--check"]), 0)

    def test_srt_conversion_uses_webvtt_timestamps_and_escapes_markup(self) -> None:
        srt = (
            "1\r\n00:00:01,500 --> 00:00:03,000\r\nFirst & <second>\r\nline\r\n\r\n"
            "2\r\n00:01:00,000 --> 00:01:02,250\r\nNext\r\n"
        )
        self.assertEqual(
            build_media_pages.srt_to_vtt(srt),
            "WEBVTT\n\n1\n00:00:01.500 --> 00:00:03.000\nFirst &amp; &lt;second&gt;\nline\n\n"
            "2\n00:01:00.000 --> 00:01:02.250\nNext\n",
        )
        with self.assertRaisesRegex(ValueError, r"bad\.srt: 1"):
            build_media_pages.srt_to_vtt("1\n00:00:01.500 --> 00:00:03.000\ntext\n", "bad.srt")

    def test_each_video_has_default_subtitles_and_the_embedded_chapters(self) -> None:
        chapters = self.chapters()
        for language, page in PAGES.items():
            parser = VideoPageParser()
            parser.feed((MEDIA / page).read_text(encoding="utf-8"))
            self.assertEqual(parser.language, language)
            self.assertEqual(len(parser.videos), len(FAMILIES))
            for family, video in zip(FAMILIES, parser.videos):
                name = f"{family}-{language.upper()}"
                with self.subTest(page=page, video=name):
                    self.assertEqual(urlsplit(video["source"]).path, f"{name}.mp4")
                    track = video["track"]
                    self.assertEqual((track["kind"], track["src"], track["srclang"]), ("subtitles", f"{name}.vtt", language))
                    self.assertIn("default", track)
                    vtt = (MEDIA / f"{name}.vtt").read_text(encoding="utf-8")
                    srt = (MEDIA / f"{name}.srt").read_text(encoding="utf-8")
                    self.assertTrue(vtt.startswith("WEBVTT\n"))
                    self.assertEqual(vtt.count(" --> "), srt.count(" --> "))
                    starts = [chapter["start"] for chapter in chapters[name]["chapters"]]
                    self.assertEqual(video["starts"], starts)
                    self.assertEqual(starts[0], 0)
                    self.assertEqual(starts, sorted(set(starts)))
                    self.assertLess(starts[-1], chapters[name]["duration"])

    def test_pages_reference_only_existing_local_files(self) -> None:
        for page in PAGES.values():
            html = (MEDIA / page).read_text(encoding="utf-8")
            for link in re.findall(r'(?:href|src)="([^"]+)"', html):
                if link.startswith("#") or "://" in link:
                    continue
                with self.subTest(page=page, link=link):
                    self.assertTrue((MEDIA / unquote(urlsplit(link).path)).is_file())

    @unittest.skipUnless(shutil.which("ffprobe"), "ffprobe is not installed")
    def test_chapter_data_matches_the_chapters_embedded_in_each_mp4(self) -> None:
        for name, entry in self.chapters().items():
            with self.subTest(video=name):
                result = subprocess.run(
                    ["ffprobe", "-v", "error", "-show_chapters", "-show_format", "-of", "json", str(MEDIA / f"{name}.mp4")],
                    capture_output=True, encoding="utf-8", check=True, timeout=60,
                )
                probe = json.loads(result.stdout)
                self.assertEqual(
                    [(float(chapter["start_time"]), chapter["tags"]["title"]) for chapter in probe["chapters"]],
                    [(chapter["start"], chapter["title"]) for chapter in entry["chapters"]],
                )
                self.assertAlmostEqual(float(probe["format"]["duration"]), entry["duration"], delta=0.01)

    def test_readmes_link_the_video_pages_next_to_the_mp4_files(self) -> None:
        base = f"{SITE_URL}docs/media/"
        for readme in ("README.md", "README.ko.md"):
            text = (ROOT / readme).read_text(encoding="utf-8")
            for page in ("", "ko.html"):
                for anchor in ("replay", "walkthrough"):
                    self.assertIn(f"({base}{page}#{anchor})", text, (readme, page, anchor))
        english = (ROOT / "README.en.md").read_text(encoding="utf-8")
        for page in ("", "ko.html"):
            self.assertIn(f"({base}{page})", english)


if __name__ == "__main__":
    unittest.main()
