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


class PortalV11MediaTests(unittest.TestCase):
    name = "Foundry-Portal-Walkthrough-KO.v1.1"

    def test_versioned_player_links_match_its_video_and_chapters(self):
        path = MEDIA / "portal.v1.1.html"
        html = path.read_text(encoding="utf-8")
        parser = VideoPageParser()
        parser.feed(html)
        self.assertEqual(parser.language, "ko")
        self.assertEqual(len(parser.videos), 1)
        video = parser.videos[0]
        self.assertEqual(urlsplit(video["source"]).path, self.name + ".mp4")
        self.assertEqual(video["track"]["src"], self.name + ".vtt")
        self.assertEqual(video["track"]["srclang"], "ko")
        entry = json.loads((MEDIA / "chapters.v1.1.json").read_text())[self.name]
        starts = [chapter["start"] for chapter in entry["chapters"]]
        self.assertEqual(video["starts"], starts)
        self.assertEqual(starts[0], 0)
        self.assertEqual(starts, sorted(set(starts)))
        self.assertLess(starts[-1], entry["duration"])
        for link in re.findall(r'(?:href|src)="([^"]+)"', html):
            if not link.startswith("#") and "://" not in link:
                self.assertTrue((MEDIA / unquote(urlsplit(link).path)).is_file(), link)

    def test_versioned_subtitles_preserve_the_same_timeline_and_text(self):
        srt = (MEDIA / f"{self.name}.srt").read_text(encoding="utf-8")
        vtt = (MEDIA / f"{self.name}.vtt").read_text(encoding="utf-8")
        self.assertEqual(vtt, build_media_pages.srt_to_vtt(srt))
        entry = json.loads((MEDIA / "chapters.v1.1.json").read_text())[self.name]
        previous_end = 0
        for match in re.finditer(r"(\d\d):(\d\d):(\d\d)\.(\d{3}) --> (\d\d):(\d\d):(\d\d)\.(\d{3})", vtt):
            values = list(map(int, match.groups()))
            start = values[0] * 3600 + values[1] * 60 + values[2] + values[3] / 1000
            end = values[4] * 3600 + values[5] * 60 + values[6] + values[7] / 1000
            self.assertGreaterEqual(start, previous_end)
            self.assertGreater(end, start)
            self.assertLessEqual(end, entry["duration"])
            previous_end = end
        self.assertGreater(previous_end, 0)

    @unittest.skipUnless(shutil.which("ffprobe"), "ffprobe is not installed")
    def test_versioned_recording_has_real_video_captions_and_matching_chapters(self):
        probe = json.loads(subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_streams", "-show_chapters", "-show_format",
             "-of", "json", str(MEDIA / f"{self.name}.mp4")],
            encoding="utf-8", timeout=60,
        ))
        entry = json.loads((MEDIA / "chapters.v1.1.json").read_text())[self.name]
        video = next(stream for stream in probe["streams"] if stream["codec_type"] == "video")
        self.assertEqual(video["codec_name"], "h264")
        self.assertEqual((video["width"], video["height"]), (entry["width"], entry["height"]))
        self.assertFalse(any(stream["codec_type"] == "audio" for stream in probe["streams"]))
        self.assertTrue(any(
            stream["codec_name"] == "mov_text" and stream["tags"]["language"] == "kor"
            for stream in probe["streams"]
        ))
        self.assertEqual(
            [(float(chapter["start_time"]), chapter["tags"]["title"]) for chapter in probe["chapters"]],
            [(chapter["start"], chapter["title"]) for chapter in entry["chapters"]],
        )
        self.assertAlmostEqual(float(probe["format"]["duration"]), entry["duration"], delta=.01)


if __name__ == "__main__":
    unittest.main()
