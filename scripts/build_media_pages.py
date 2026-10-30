#!/usr/bin/env python3
"""Build the WebVTT subtitles and the video pages in docs/media/, or verify them with ``--check``.

Browsers play an MP4 but do not show the subtitles or chapter markers embedded in it. The MP4 files and
their ``.srt`` subtitles stay the source of truth and are never modified. This script derives what a
``<video>`` page needs from them:

* one ``.vtt`` (WebVTT) subtitle file next to every ``.srt``;
* ``index.html`` (English) and ``ko.html`` (Korean), which play the videos with subtitles on by default
  and a clickable chapter list built from ``chapters.json`` (the chapter markers embedded in each MP4).

Only the standard library is used, so the check also runs where ffmpeg is not installed. After a video is
rebuilt, refresh its entry in ``chapters.json`` from ``ffprobe -show_chapters -show_format -of json`` (chapter
``start_time`` and ``tags.title``, format ``duration``) and run this script without ``--check``; the tests
compare the file with the MP4 chapters whenever ffprobe is available.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path
from typing import Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MEDIA_DIR = PROJECT_ROOT / "docs" / "media"
CHAPTERS_PATH = MEDIA_DIR / "chapters.json"
LOCALES = json.loads((PROJECT_ROOT / "web" / "locales.json").read_text(encoding="utf-8"))
LANGUAGES = ("en", "ko")
KINDS = ("Foundry-Lab-Replay", "Foundry-Portal-Walkthrough")
PAGE_FILES = {"en": "index.html", "ko": "ko.html"}
LANGUAGE_LABELS = {"en": "English", "ko": "한국어"}
THEME_MESSAGE_KEYS = (
    "themeInvalid", "themeReadError", "themeWriteError",
    "themeLight", "themeDark", "themeLightLabel", "themeDarkLabel",
)
# The Walkthrough MP4s start with one blank frame, so the preview (and the start of playback) is the next frame.
PREVIEW_START = "0.05"
SRT_TIMING = re.compile(r"^(\d{2}:\d{2}:\d{2}),(\d{3}) --> (\d{2}:\d{2}:\d{2}),(\d{3})$")
PLACEHOLDER = re.compile(r"\{\{([A-Z_]+)\}\}")

COPY = {
    "en": {
        "title": "Narrated lab videos",
        "description": (
            "Narrated videos of the Microsoft Foundry learning-loop lab: a CLI/SDK replay and a walkthrough "
            "of the real portal, with subtitles and a chapter list."
        ),
        "context": "Narrated videos",
        "lead": (
            "Two narrated videos replay the most recent full lab run. Subtitles are on by default "
            "(turn them off with the CC button), and the chapter list jumps to any step."
        ),
        "chapters": "Chapters",
        "meta": "{duration} · {count} chapters",
        "files": "Files",
        "fallback": "Your browser cannot play this video.",
        "open_mp4": "Open the MP4",
        "track_error": (
            "Subtitles could not be loaded. If you opened this page straight from disk (file://), the browser "
            "blocks subtitle files: open it over http(s), or play the MP4 in a player such as VLC or QuickTime, "
            "which show the embedded subtitles and chapters."
        ),
        "note": (
            "Synthetic Contoso data from one real lab run. "
            "Scores are evidence on twelve questions, not production approval."
        ),
        "guide_href": "../index.html",
        "videos": {
            "Foundry-Lab-Replay": (
                "replay", "CLI/SDK lab replay",
                "Replays the actual command and managed-service records of one full run, with long waits "
                "removed. It is not a portal screen recording.",
            ),
            "Foundry-Portal-Walkthrough": (
                "walkthrough", "Portal walkthrough",
                "Records the real Microsoft Foundry portal for the same run, with personal information and "
                "connection addresses hidden. It stops before Submit, so no evaluation or optimization job "
                "is created again.",
            ),
        },
    },
    "ko": {
        "title": "내레이션 실습 영상",
        "description": (
            "Microsoft Foundry 학습 루프 실습의 내레이션 영상입니다. CLI/SDK 요약영상과 실제 포털 화면 녹화를 "
            "자막·챕터 목록과 함께 재생합니다."
        ),
        "context": "내레이션 영상",
        "lead": (
            "가장 최근 전체 실습 한 번을 재생하는 내레이션 영상 두 편입니다. 자막은 기본으로 켜져 있고"
            "(CC 버튼으로 끌 수 있습니다) 챕터 목록으로 원하는 단계로 바로 이동합니다."
        ),
        "chapters": "챕터",
        "meta": "{duration} · 챕터 {count}개",
        "files": "파일",
        "fallback": "이 브라우저에서는 영상을 재생할 수 없습니다.",
        "open_mp4": "MP4 열기",
        "track_error": (
            "자막을 불러오지 못했습니다. 이 페이지를 디스크에서 직접(file://) 열었다면 브라우저가 자막 파일을 "
            "차단합니다. http(s)로 열거나, 내장 자막과 챕터를 표시하는 VLC·QuickTime 같은 플레이어에서 "
            "MP4를 재생하세요."
        ),
        "note": (
            "합성 Contoso 데이터로 진행한 실제 실습 한 번의 기록입니다. "
            "점수는 열두 개 질문에 대한 근거일 뿐 운영 승인이 아닙니다."
        ),
        "guide_href": "../ko/index.html",
        "videos": {
            "Foundry-Lab-Replay": (
                "replay", "CLI/SDK 실습 요약영상",
                "한 번의 전체 실습에서 남은 실제 명령과 관리형 서비스 기록을 긴 대기 시간을 줄여 재생합니다. "
                "포털 화면 녹화가 아닙니다.",
            ),
            "Foundry-Portal-Walkthrough": (
                "walkthrough", "실제 포털 화면 녹화",
                "같은 실행의 실제 Microsoft Foundry 포털 화면을 녹화한 것으로, 개인정보와 연결 주소는 가렸습니다. "
                "Submit을 누르기 전까지만 보여 주므로 평가나 최적화 작업을 다시 만들지 않습니다.",
            ),
        },
    },
}

PAGE_CSS = """
    .video-main { max-width: 74rem; margin: 0 auto; padding: 2rem 1.5rem 4rem; word-break: keep-all; overflow-wrap: anywhere; }
    .video-main:focus { outline: none; }
    .video-main .return-link { margin: 0 0 1rem; font-size: 0.9rem; }
    .video-main h1 { margin: 0 0 0.6rem; color: var(--ink); font-size: clamp(1.7rem, 3.2vw, 2.3rem); line-height: 1.25; letter-spacing: -0.02em; }
    .video-main .lead { max-width: 52rem; margin: 0; color: var(--muted); }
    .video-card { margin-top: 1.75rem; padding: 1.25rem; border: 1px solid var(--line); border-radius: var(--radius); background: var(--paper); }
    .video-card .card-head { display: flex; flex-wrap: wrap; align-items: baseline; gap: 0.25rem 1rem; }
    .video-card h2 { margin: 0; color: var(--ink); font-size: 1.3rem; line-height: 1.35; }
    .video-card .meta { margin: 0; color: var(--muted); font-size: 0.85rem; }
    .video-card .summary { max-width: 56rem; margin: 0.5rem 0 0; }
    .player { display: grid; gap: 1rem; margin-top: 1rem; }
    .player video { display: block; width: 100%; height: auto; aspect-ratio: 16 / 9; border-radius: 0.5rem; background: #000; }
    .chapters h3 { margin: 0 0 0.5rem; color: var(--ink); font-size: 0.8rem; letter-spacing: 0.06em; text-transform: uppercase; }
    .chapter-list { position: relative; margin: 0; padding: 0; list-style: none; overflow-y: auto; border: 1px solid var(--line); border-radius: 0.5rem; background: var(--paper); }
    .chapter-list li + li { border-top: 1px solid var(--line); }
    .chapter-list a { display: grid; grid-template-columns: 3rem minmax(0, 1fr); gap: 0.5rem; padding: 0.55rem 0.75rem; border-left: 3px solid transparent; color: var(--body-ink); font-size: 0.9rem; line-height: 1.4; text-decoration: none; }
    .chapter-list a:hover { background: var(--canvas); color: var(--ink); }
    .chapter-list a[aria-current="true"] { border-left-color: var(--teal); background: var(--teal-soft); color: var(--ink); font-weight: 650; }
    .chapter-list .t { color: var(--muted); font-variant-numeric: tabular-nums; }
    .video-card .files { margin: 0.9rem 0 0; color: var(--muted); font-size: 0.85rem; }
    .video-card .track-error { margin: 0.9rem 0 0; padding: 0.7rem 1rem; border: 1px solid #eadbc5; border-left: 3px solid #956120; border-radius: 0 0.5rem 0.5rem 0; background: #fcf8ee; color: #684d2c; font-size: 0.88rem; }
    :root[data-theme="dark"] .video-card .track-error { border-color: #82672f; background: #3c301e; color: #f4d298; }
    .video-main .video-note { margin: 2rem 0 0; color: var(--muted); font-size: 0.85rem; }
    @media (max-width: 61.99rem) { .chapter-list { max-height: 19rem; } }
    @media (min-width: 62rem) {
      .player { grid-template-columns: minmax(0, 1fr) 19rem; }
      .chapters { position: relative; min-height: 12rem; }
      .chapters-inner { position: absolute; inset: 0; display: flex; flex-direction: column; }
      .chapters-inner h3 { flex: 0 0 auto; }
      .chapter-list { flex: 1 1 auto; min-height: 0; }
    }
"""

PAGE_JS = """
(() => {
  "use strict";
  const videos = Array.from(document.querySelectorAll("[data-player] video"));
  document.querySelectorAll("[data-player]").forEach((card) => {
    const video = card.querySelector("video");
    const list = card.querySelector(".chapter-list");
    const links = Array.from(card.querySelectorAll("[data-start]"));
    if (!video || !list || !links.length) return;
    const starts = links.map((link) => Number(link.dataset.start));
    let current = -1;

    video.addEventListener("play", () => {
      videos.forEach((other) => {
        if (other !== video) other.pause();
      });
    });

    const track = video.querySelector("track");
    const notice = card.querySelector(".track-error");
    if (track && notice) {
      const showNotice = () => {
        notice.hidden = false;
      };
      track.addEventListener("error", showNotice);
      if (track.readyState === HTMLTrackElement.ERROR) showNotice();
    }

    function keepVisible(link) {
      const item = link.parentElement;
      if (item.offsetTop < list.scrollTop) {
        list.scrollTop = item.offsetTop;
      } else if (item.offsetTop + item.offsetHeight > list.scrollTop + list.clientHeight) {
        list.scrollTop = item.offsetTop + item.offsetHeight - list.clientHeight;
      }
    }

    function mark() {
      let index = 0;
      starts.forEach((start, position) => {
        if (video.currentTime + 0.25 >= start) index = position;
      });
      if (index === current) return;
      current = index;
      links.forEach((link, position) => {
        if (position === index) link.setAttribute("aria-current", "true");
        else link.removeAttribute("aria-current");
      });
      keepVisible(links[index]);
    }

    links.forEach((link, position) => {
      link.addEventListener("click", (event) => {
        event.preventDefault();
        video.currentTime = starts[position];
        const started = video.play();
        if (started && typeof started.catch === "function") started.catch(() => {});
        mark();
      });
    });
    ["timeupdate", "seeked", "loadedmetadata"].forEach((name) => video.addEventListener(name, mark));
    mark();
  });
})();
"""

PAGE = """<!doctype html>
<html lang="{{LANG}}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light dark">
  <meta name="description" content="{{DESCRIPTION}}">
  <title>{{TITLE}} · {{SITE_TITLE}}</title>
  <link rel="icon" type="image/svg+xml" href="../../web/assets/foundry.svg">
  <script id="guide-messages" type="application/json">{{MESSAGES}}</script>
  <script src="../../web/theme.js"></script>
  <link rel="stylesheet" href="../../web/styles.css">
  <style>{{CSS}}  </style>
</head>
<body>
  <a class="skip-link" href="#main-content">{{SKIP_LINK}}</a>

  <header class="site-header">
    <div class="header-inner">
      <a class="brand" href="{{GUIDE_HREF}}" aria-label="{{BRAND_LABEL}}">
        <img class="brand-symbol" src="../../web/assets/foundry.svg" width="42" height="42" alt="" aria-hidden="true">
        <span class="brand-text"><strong>Microsoft Foundry</strong><span>{{BRAND_SUBTITLE}}</span></span>
      </a>
      <span class="header-context">{{CONTEXT}}</span>
      <nav class="language-switcher" aria-label="{{LANGUAGE_NAV_LABEL}}">
        {{LANGUAGE_LINKS}}
      </nav>
      <div class="header-actions">
        <button class="toolbar-button" type="button" data-theme-toggle aria-label="{{THEME_DARK_LABEL}}" hidden>{{THEME_DARK}}</button>
      </div>
    </div>
  </header>
  <p class="theme-feedback no-print" data-theme-feedback role="status" hidden></p>

  <main id="main-content" class="video-main" tabindex="-1">
    <p class="return-link"><a href="{{GUIDE_HREF}}">{{RETURN_LABEL}}</a></p>
    <h1>{{TITLE}}</h1>
    <p class="lead">{{LEAD}}</p>
{{CARDS}}
    <p class="video-note">{{NOTE}}</p>
  </main>

  <script>{{JS}}</script>
</body>
</html>
"""


def fill(template: str, values: Mapping[str, str]) -> str:
    return PLACEHOLDER.sub(lambda match: values[match.group(1)], template)


def stem(kind: str, language: str) -> str:
    return f"{kind}-{language.upper()}"


def number(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".") or "0"


def clock(seconds: int) -> str:
    hours, rest = divmod(seconds, 3600)
    minutes, remainder = divmod(rest, 60)
    return f"{hours}:{minutes:02d}:{remainder:02d}" if hours else f"{minutes}:{remainder:02d}"


def srt_to_vtt(srt: str, source: str = "subtitles") -> str:
    """Convert SRT to WebVTT: dot millisecond separators, a header, and escaped cue text."""
    blocks = [block for block in re.split(r"\n\s*\n", srt.replace("\r\n", "\n").strip()) if block.strip()]
    cues = []
    for position, block in enumerate(blocks, 1):
        lines = block.split("\n")
        timing = SRT_TIMING.match(lines[1]) if len(lines) >= 3 else None
        if not lines[0].strip().isdigit() or timing is None:
            raise ValueError(f"{source}: {position}번째 자막 블록이 SRT 형식이 아닙니다.")
        start = f"{timing.group(1)}.{timing.group(2)}"
        end = f"{timing.group(3)}.{timing.group(4)}"
        text = "\n".join(html.escape(line, quote=False) for line in lines[2:])
        cues.append(f"{lines[0].strip()}\n{start} --> {end}\n{text}")
    return "WEBVTT\n\n" + "\n\n".join(cues) + "\n"


def load_chapters() -> dict:
    data = json.loads(CHAPTERS_PATH.read_text(encoding="utf-8"))
    for name, entry in data.items():
        starts = [chapter["start"] for chapter in entry["chapters"]]
        if not starts or starts[0] != 0 or starts != sorted(set(starts)) or starts[-1] >= entry["duration"]:
            raise ValueError(f"{name}: 챕터 시작 시간은 0에서 시작해 영상 길이 안에서 증가해야 합니다.")
    return data


def render_card(language: str, kind: str, chapters: Mapping[str, dict]) -> str:
    copy = COPY[language]
    anchor, title, summary = copy["videos"][kind]
    name = stem(kind, language)
    entry = chapters[name]
    rows = []
    for chapter in entry["chapters"]:
        start = number(chapter["start"])
        rows.append(
            f'            <li><a href="{name}.mp4#t={start}" data-start="{start}">'
            f'<span class="t">{clock(int(chapter["start"]))}</span><span>{html.escape(chapter["title"])}</span></a></li>'
        )
    items = "\n".join(rows)
    meta = html.escape(copy["meta"].format(duration=clock(int(entry["duration"])), count=len(entry["chapters"])))
    title, summary = html.escape(title), html.escape(summary)
    chapters_label = html.escape(copy["chapters"])
    fallback, open_mp4, files = (html.escape(copy[key]) for key in ("fallback", "open_mp4", "files"))
    track_error = html.escape(copy["track_error"])
    label = LANGUAGE_LABELS[language]
    return f"""    <section id="{anchor}" class="video-card" aria-labelledby="{anchor}-title" data-player>
      <div class="card-head">
        <h2 id="{anchor}-title">{title}</h2>
        <p class="meta">{meta}</p>
      </div>
      <p class="summary">{summary}</p>
      <div class="player">
        <video controls preload="metadata" playsinline width="1920" height="1080" aria-labelledby="{anchor}-title">
          <source src="{name}.mp4#t={PREVIEW_START}" type="video/mp4">
          <track kind="subtitles" src="{name}.vtt" srclang="{language}" label="{label}" default>
          <p>{fallback} <a href="{name}.mp4">{open_mp4}</a></p>
        </video>
        <nav class="chapters" aria-label="{chapters_label}">
          <div class="chapters-inner">
            <h3>{chapters_label}</h3>
            <ol class="chapter-list">
{items}
            </ol>
          </div>
        </nav>
      </div>
      <p class="track-error" hidden>{track_error}</p>
      <p class="files">{files}: <a href="{name}.mp4">MP4</a> · <a href="{name}.srt">SRT</a> · <a href="{name}.vtt">WebVTT</a></p>
    </section>"""


def language_links(language: str) -> str:
    links = []
    for code in LANGUAGES:
        current = ' aria-current="page"' if code == language else ""
        links.append(f'<a href="{PAGE_FILES[code]}" lang="{code}" hreflang="{code}"{current}>{LANGUAGE_LABELS[code]}</a>')
    return "\n        ".join(links)


def render_page(language: str, chapters: Mapping[str, dict]) -> str:
    copy = COPY[language]
    locale = LOCALES[language]
    shell = locale["shell"]
    messages = {key: locale["messages"][key] for key in THEME_MESSAGE_KEYS}
    values = {
        "LANG": language,
        "DESCRIPTION": html.escape(copy["description"]),
        "TITLE": html.escape(copy["title"]),
        "SITE_TITLE": html.escape(shell["SITE_TITLE"]),
        "MESSAGES": json.dumps(messages, ensure_ascii=False).replace("<", "\\u003c"),
        "CSS": PAGE_CSS,
        "SKIP_LINK": html.escape(shell["SKIP_LINK"]),
        "GUIDE_HREF": copy["guide_href"],
        "BRAND_LABEL": html.escape(shell["BRAND_LABEL"]),
        "BRAND_SUBTITLE": html.escape(shell["BRAND_SUBTITLE"]),
        "CONTEXT": html.escape(copy["context"]),
        "LANGUAGE_NAV_LABEL": html.escape(shell["LANGUAGE_NAV_LABEL"]),
        "LANGUAGE_LINKS": language_links(language),
        "THEME_DARK_LABEL": html.escape(shell["THEME_DARK_LABEL"]),
        "THEME_DARK": html.escape(shell["THEME_DARK"]),
        "RETURN_LABEL": html.escape(shell["RETURN_LABEL"]),
        "LEAD": html.escape(copy["lead"]),
        "CARDS": "\n".join(render_card(language, kind, chapters) for kind in KINDS),
        "NOTE": html.escape(copy["note"]),
        "JS": PAGE_JS,
    }
    return fill(PAGE, values)


def outputs() -> dict[Path, str]:
    chapters = load_chapters()
    pages: dict[Path, str] = {}
    for kind in KINDS:
        for language in LANGUAGES:
            source = MEDIA_DIR / f"{stem(kind, language)}.srt"
            pages[source.with_suffix(".vtt")] = srt_to_vtt(source.read_text(encoding="utf-8"), source.name)
    for language in LANGUAGES:
        pages[MEDIA_DIR / PAGE_FILES[language]] = render_page(language, chapters)
    return pages


def check_or_write(pages: Mapping[Path, str], *, check: bool) -> int:
    stale = False
    for path, rendered in pages.items():
        if check:
            try:
                current = path.read_bytes()
            except FileNotFoundError:
                print(f"생성 파일이 없습니다: {path}. 먼저 영상 페이지를 빌드해야 합니다.", file=sys.stderr)
                stale = True
                continue
            if current != rendered.encode("utf-8"):
                print(f"생성 파일이 최신이 아닙니다: {path}. 영상 페이지를 다시 빌드해야 합니다.", file=sys.stderr)
                stale = True
            else:
                print(f"최신 상태 확인: {path}")
        else:
            with path.open("w", encoding="utf-8", newline="\n") as output:
                output.write(rendered)
            print(f"영상 페이지 생성: {path}")
    return 1 if stale else 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="영상 자막(WebVTT)과 영상 재생 페이지를 빌드합니다.")
    parser.add_argument("--check", action="store_true", help="파일을 쓰지 않고 모든 대상의 최신 상태 확인")
    args = parser.parse_args(argv)
    try:
        return check_or_write(outputs(), check=args.check)
    except (OSError, ValueError, KeyError) as error:
        print(f"영상 페이지 빌드 실패: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
