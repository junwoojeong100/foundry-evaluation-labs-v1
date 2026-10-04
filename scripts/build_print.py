#!/usr/bin/env python3
"""Build docs/print.html; --check verifies it without writing. No PDF is produced."""

from __future__ import annotations

import argparse
import html
import os
import posixpath
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Mapping, Sequence
from urllib.parse import quote, unquote, urlsplit

if __package__:
    from . import build_guide as guide
else:
    import build_guide as guide

BOOK_ORDER = ("index", "facilitator", "admin", "troubleshooting", "data-guide")
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}


class _Anchors(HTMLParser):
    def __init__(self, source: str) -> None:
        super().__init__(convert_charrefs=True)
        self.source = source
        self.ids: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list) -> None:
        attributes = dict(attrs)
        for value in {attributes.get("id"), attributes.get("name") if tag == "a" else None} - {None}:
            if value in self.ids:
                raise ValueError(f"문서 안에 중복된 앵커가 있습니다: {self.source}#{value}")
            self.ids.add(value)


def _anchor(document: guide.Document, fragment: str = "") -> str:
    return f"book-{document.key}" + (f"--{fragment}" if fragment else "")


class _BookContent(guide.HtmlRewriter):
    def __init__(
        self,
        document: guide.Document,
        anchors: Mapping[str, set[str]],
        documents: Mapping[str, guide.Document],
        output_base: str,
    ) -> None:
        super().__init__()
        self.document = document
        self.anchors = anchors
        self.documents = documents
        self.output_base = output_base
        self.text = guide.locale(document.language)["book"]
        self.links: list[str | None] = []

    def _target(self, document: guide.Document, fragment: str) -> str:
        fragment = unquote(fragment)
        if fragment and fragment not in self.anchors[document.key]:
            raise ValueError(f"인쇄본 링크의 앵커가 없습니다: {document.source}#{fragment}")
        return "#" + quote(_anchor(document, fragment), safe="-._~")

    def _link(self, value: str) -> tuple[str | None, str | None]:
        parsed = urlsplit(value)
        local_http = parsed.scheme in {"http", "https"} and (
            parsed.hostname in LOCAL_HOSTS or (parsed.hostname or "").endswith(".localhost")
        )
        if (parsed.scheme or parsed.netloc) and not local_http and parsed.scheme != "file":
            return value, None
        if not parsed.path and not local_http:
            return self._target(self.document, parsed.fragment), None
        path = posixpath.normpath(unquote(parsed.path).lstrip("/"))
        if not parsed.scheme and not parsed.netloc and not parsed.path.startswith("/"):
            path = guide.output_relative(posixpath.join(self.output_base, path))
        document = self.documents.get(path)
        if document:
            return self._target(document, parsed.fragment), None
        label = path if path != "." else self.text["PACKAGE_ROOT"]
        if parsed.fragment:
            label += "#" + unquote(parsed.fragment)
        return None, label

    def _attributes(self, tag: str, attrs: list) -> list:
        updated = []
        for name, value in attrs:
            if value is not None:
                if name == "id" or (tag == "a" and name == "name"):
                    value = _anchor(self.document, value)
                elif name in {"aria-labelledby", "aria-describedby", "aria-controls", "for", "headers"}:
                    value = " ".join(_anchor(self.document, part) for part in value.split())
            updated.append((name, value))
        return updated

    def handle_starttag(self, tag: str, attrs: list) -> None:
        updated = self._attributes(tag, attrs)
        if tag == "a":
            attributes = dict(updated)
            href = attributes.get("href")
            label = None
            if href is not None:
                target, label = self._link(href)
                if label is not None:
                    updated = [(name, value) for name, value in updated if name not in {"href", "target", "rel", "download", "class"}]
                    updated.append(("class", (attributes.get("class", "") + " book-file-link").strip()))
                    tag = "span"
                else:
                    updated = [(name, target if name == "href" else value) for name, value in updated]
            self.links.append(label)
        self.parts.append(self.start_tag(tag, updated))

    def handle_startendtag(self, tag: str, attrs: list) -> None:
        self.parts.append(self.start_tag(tag, self._attributes(tag, attrs), closed=True))

    def handle_endtag(self, tag: str) -> None:
        if tag == "a":
            label = self.links.pop() if self.links else None
            if label is not None:
                self.parts.append(
                    f'<span class="book-file-label"> ({self.text["FILE_LABEL"]}: <code>{html.escape(label)}</code>)</span></span>'
                )
                return
        super().handle_endtag(tag)


def render_book(
    sources: Mapping[str, str], template: str, *,
    output_base: str | None = None, language: str = "en",
) -> str:
    """Assemble all source documents with book-local IDs and portable links."""
    guide.require_sources(sources)
    text = guide.locale(language)["book"]
    if output_base is None:
        output_base = posixpath.dirname(
            posixpath.join(guide.SITE_DIRECTORY, guide.localized_filename("print.html", language))
        )
    specifications = {document.key: document for document in guide.documents_for(language)}
    documents = {
        path: document
        for document in guide.documents_for(language)
        for path in (
            document.source, document.output,
            posixpath.join(guide.SITE_DIRECTORY, document.output),
        )
    }
    rendered = {}
    anchors = {}
    for key in BOOK_ORDER:
        document = specifications[key]
        part = guide.render_markdown(
            sources[document.source],
            relative_base=posixpath.dirname(document.source),
            link_map=guide.DOCUMENT_LINKS,
            output_base=output_base,
            language=language,
        )
        rendered[key] = part
        parser = _Anchors(document.source)
        parser.feed(part.content)
        anchors[key] = parser.ids

    sections = []
    toc = ["<ol>"]
    for index, key in enumerate(BOOK_ORDER):
        document = specifications[key]
        parser = _BookContent(document, anchors, documents, output_base)
        parser.feed(rendered[key].content)
        parser.close()
        label = document.label if index == 0 else f'{text["APPENDIX"]} {index} · {document.label}'
        section_class = "book-section guide-content" + (" book-appendix" if index else "")
        sections.append(
            f'<section id="{_anchor(document)}" class="{section_class}" lang="{language}" aria-label="{html.escape(label)}">\n'
            f'<p class="book-part-label">{html.escape(label)}</p>\n'
            + "".join(parser.parts)
            + "\n</section>"
        )
        toc.append(f'<li><a href="#{_anchor(document)}">{html.escape(label)}</a></li>')
    toc.append("</ol>")
    return guide.fill_template(
        template,
        {
            **{key: html.escape(value, quote=True) for key, value in text.items()},
            "CONTENT_LANGUAGE": language,
            "LANGUAGE_NAV_LABEL": guide.locale(language)["shell"]["LANGUAGE_NAV_LABEL"],
            "LANGUAGE_LINKS": guide.language_links("print.html", language, output_base),
            "BUILD_DATE": guide.BUILD_DATE,
            "WEB_PATH": html.escape(guide.output_relative("web", output_base), quote=True),
            "HOME_HREF": html.escape(
                guide.output_relative(
                    posixpath.join(guide.SITE_DIRECTORY, guide.localized_filename("index.html", language)),
                    output_base,
                ),
                quote=True,
            ),
            "CONTENT": "\n".join(sections),
            "BOOK_TOC": "\n".join(toc),
        },
        ("TITLE", "BUILD_DATE", "CONTENT", "BOOK_TOC"),
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="필수 문서를 모아 통합 인쇄본 HTML을 만듭니다. PDF는 생성하지 않습니다.")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--language", choices=guide.LANGUAGES, default="en")
    parser.add_argument("--template", type=Path, default=guide.PROJECT_ROOT / "web" / "print-template.html")
    parser.add_argument("--check", action="store_true", help="파일을 쓰지 않고 인쇄본의 최신 상태 확인")
    args = parser.parse_args(argv)
    if args.output is None:
        args.output = guide.PROJECT_ROOT / guide.SITE_DIRECTORY / guide.localized_filename("print.html", args.language)
    try:
        rendered = render_book(
            guide.read_sources(), args.template.read_text(encoding="utf-8"),
            output_base=os.path.relpath(args.output.resolve().parent, guide.PROJECT_ROOT).replace(os.sep, "/"),
            language=args.language,
        )
        return guide.check_or_write({args.output: rendered}, check=args.check)
    except (OSError, ValueError) as error:
        print(f"인쇄본 빌드 실패: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
