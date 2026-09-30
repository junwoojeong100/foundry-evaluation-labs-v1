#!/usr/bin/env python3
"""Build all offline HTML documents, or verify them with ``--check``.

The source is trusted, locally authored Markdown. Relative document links are
rebased for the output location; fenced-code contents remain unchanged. Use
``--source fixture.md --output fixture.html`` to build just one document.
"""

from __future__ import annotations

import argparse
import html
import os
import posixpath
import re
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable, Mapping, Sequence
from urllib.parse import unquote, urlsplit, urlunsplit

from markdown import Markdown
from markdown.extensions.toc import slugify_unicode
from markdown.treeprocessors import Treeprocessor

BUILD_DATE = "2026-09-30"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_PLACEHOLDERS = ("CONTENT", "TOC", "BUILD_DATE")
PLACEHOLDER = re.compile(r"\{\{([A-Z_]+)\}\}")


@dataclass(frozen=True)
class Document:
    source: str
    output: str
    label: str

    @property
    def key(self) -> str:
        return self.output.removesuffix(".html")


DOCUMENTS = (
    Document("guide/handbook.md", "index.html", "참가자 실습 가이드"),
    Document("guide/facilitator.md", "facilitator.html", "강사용 진행 가이드"),
    Document("guide/admin-setup.md", "admin.html", "관리자 사전 준비"),
    Document("guide/sft-appendix.md", "sft.html", "SFT 심화 부록"),
    Document("guide/verification.md", "verification.html", "검증 기록"),
    Document("data/README.md", "data-guide.html", "데이터 설명"),
    Document("guide/integration-migration.md", "migration.html", "v1 이관·아카이브 준비"),
    Document("README.en.md", "english.html", "English quickstart"),
)
DOCUMENT_LINKS = {document.source: document.output for document in DOCUMENTS}


@dataclass(frozen=True)
class RenderedMarkdown:
    content: str
    toc: str
    title: str


class HtmlRewriter(HTMLParser):
    """Rewrite real attributes while preserving text, entities, and code verbatim."""

    def __init__(self, rewrite: Callable[[str, list], list] | None = None) -> None:
        super().__init__(convert_charrefs=False)
        self.parts: list[str] = []
        self.rewrite = rewrite or (lambda tag, attrs: attrs)

    @staticmethod
    def start_tag(tag: str, attrs: list, *, closed: bool = False) -> str:
        attributes = "".join(
            f" {name}" if value is None else f' {name}="{html.escape(value, quote=True)}"'
            for name, value in attrs
        )
        return f"<{tag}{attributes}{' /' if closed else ''}>"

    def handle_starttag(self, tag: str, attrs: list) -> None:
        changed = self.rewrite(tag, attrs)
        self.parts.append(self.get_starttag_text() if changed == attrs else self.start_tag(tag, changed))

    def handle_startendtag(self, tag: str, attrs: list) -> None:
        changed = self.rewrite(tag, attrs)
        self.parts.append(self.get_starttag_text() if changed == attrs else self.start_tag(tag, changed, closed=True))

    def handle_endtag(self, tag: str) -> None:
        self.parts.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def handle_entityref(self, name: str) -> None:
        self.parts.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self.parts.append(f"&#{name};")

    def handle_comment(self, data: str) -> None:
        self.parts.append(f"<!--{data}-->")

    def handle_decl(self, decl: str) -> None:
        self.parts.append(f"<!{decl}>")

    def handle_pi(self, data: str) -> None:
        self.parts.append(f"<?{data}>")


class _TitleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.in_title = False
        self.finished = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "h1" and not self.finished:
            self.in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "h1" and self.in_title:
            self.in_title = False
            self.finished = True

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.parts.append(data)


def render_markdown(
    markdown_text: str,
    *,
    relative_base: str = "",
    link_map: Mapping[str, str] | None = None,
) -> RenderedMarkdown:
    converter = Markdown(
        extensions=["fenced_code", "tables", "toc", "attr_list"],
        extension_configs={
            "toc": {"slugify": slugify_unicode, "toc_depth": "2-3"},
        },
        output_format="html5",
    )
    if relative_base not in {"", "."} or link_map:
        def rebase(value: str, attribute: str) -> str:
            parsed = urlsplit(value)
            if parsed.scheme or parsed.netloc or not parsed.path or parsed.path.startswith("/"):
                return value
            path = posixpath.normpath(posixpath.join(relative_base, parsed.path))
            if attribute == "href" and link_map:
                path = link_map.get(unquote(path), path)
            return urlunsplit(("", "", path, parsed.query, parsed.fragment))

        class RebaseLinks(Treeprocessor):
            def run(self, root):
                for element in root.iter():
                    for attribute in ("href", "src"):
                        value = element.get(attribute)
                        if value:
                            element.set(attribute, rebase(value, attribute))
                # Raw HTML and fenced blocks live outside Markdown's element tree.
                # Parsing attributes, not replacing strings, leaves escaped code intact.
                for index, block in enumerate(self.md.htmlStash.rawHtmlBlocks):
                    if not isinstance(block, str):
                        continue
                    parser = HtmlRewriter(
                        lambda tag, attrs: [
                            (name, rebase(value, name) if name in {"href", "src"} and value else value)
                            for name, value in attrs
                        ]
                    )
                    parser.feed(block)
                    parser.close()
                    self.md.htmlStash.rawHtmlBlocks[index] = "".join(parser.parts)

        converter.treeprocessors.register(RebaseLinks(converter), "rebase_links", 1)
    content = converter.convert(markdown_text.lstrip("\ufeff"))
    title_parser = _TitleParser()
    title_parser.feed(content)
    title = "".join(title_parser.parts).strip() or "Foundry 평가·개선 실습 가이드"
    toc = converter.toc
    if not converter.toc_tokens:
        toc = '<ul><li><a href="#guide-start">본문 읽기</a></li></ul>'
    return RenderedMarkdown(content, toc, title)


def fill_template(template_text: str, replacements: Mapping[str, str], required: Sequence[str]) -> str:
    for name in required:
        if "{{" + name + "}}" not in template_text:
            raise ValueError(f"필수 템플릿 자리표시자가 없습니다: {{{{{name}}}}}")

    def substitute(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in replacements:
            raise ValueError(f"알 수 없는 템플릿 자리표시자입니다: {match.group(0)}")
        return replacements[name]

    # One pass over the template, so literal {{TOKENS}} inside code stay intact.
    return PLACEHOLDER.sub(substitute, template_text).rstrip() + "\n"


def render_guide(
    markdown_text: str,
    template_text: str,
    *,
    relative_base: str = "",
    link_map: Mapping[str, str] | None = None,
    document_id: str = "index.html",
) -> str:
    """Return deterministic UTF-8-ready HTML without reading or writing files."""
    rendered = render_markdown(markdown_text, relative_base=relative_base, link_map=link_map)
    navigation = ["<ul>"]
    for document in DOCUMENTS:
        current = ' aria-current="page"' if document.output == document_id else ""
        navigation.append(f'<li><a href="{document.output}"{current}>{document.label}</a></li>')
    navigation.append('<li><a href="print.html">전체 인쇄본</a></li></ul>')
    auxiliary = document_id != "index.html"
    replacements = {
        "CONTENT": rendered.content,
        "TOC": rendered.toc,
        "BUILD_DATE": BUILD_DATE,
        "TITLE": html.escape(rendered.title, quote=True),
        "DOCUMENT_ID": html.escape(document_id, quote=True),
        "CONTENT_LANGUAGE": "en" if document_id == "english.html" else "ko",
        "DOCUMENT_LINKS": "\n".join(navigation),
        "HOME_HREF": "index.html" if auxiliary else "#guide-start",
        "RETURN_LINK": (
            '<a class="back-to-main no-print" href="index.html">← 참가자 가이드로 돌아가기</a>'
            if auxiliary else ""
        ),
    }
    return fill_template(template_text, replacements, REQUIRED_PLACEHOLDERS)


def read_sources(root: Path = PROJECT_ROOT) -> dict[str, str]:
    sources = {}
    missing = []
    for document in DOCUMENTS:
        try:
            sources[document.source] = (root / document.source).read_text(encoding="utf-8")
        except FileNotFoundError:
            missing.append(document.source)
    if missing:
        raise ValueError("필수 원문이 없습니다: " + ", ".join(missing))
    return sources


def require_sources(sources: Mapping[str, str]) -> None:
    missing = [document.source for document in DOCUMENTS if document.source not in sources]
    if missing:
        raise ValueError("필수 원문이 없습니다: " + ", ".join(missing))


def render_site(sources: Mapping[str, str], template: str, print_template: str) -> dict[str, str]:
    """Render every document before any output is written."""
    require_sources(sources)
    if __package__:
        from .build_print import render_book
    else:
        from build_print import render_book
    pages = {
        document.output: render_guide(
            sources[document.source],
            template,
            relative_base=posixpath.dirname(document.source),
            link_map=DOCUMENT_LINKS,
            document_id=document.output,
        )
        for document in DOCUMENTS
    }
    pages["print.html"] = render_book(sources, print_template)
    return pages


def check_or_write(pages: Mapping[Path, str], *, check: bool) -> int:
    stale = False
    for path, rendered in pages.items():
        if check:
            try:
                current = path.read_bytes()
            except FileNotFoundError:
                print(f"생성 파일이 없습니다: {path}. 먼저 가이드를 빌드하세요.", file=sys.stderr)
                stale = True
                continue
            if current != rendered.encode("utf-8"):
                print(f"생성 파일이 최신이 아닙니다: {path}. 가이드를 다시 빌드하세요.", file=sys.stderr)
                stale = True
            else:
                print(f"최신 상태 확인: {path}")
        else:
            with path.open("w", encoding="utf-8", newline="\n") as output:
                output.write(rendered)
            print(f"가이드 생성: {path}")
    return 1 if stale else 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="가이드·보조 문서·통합 인쇄본을 함께 빌드합니다.")
    parser.add_argument("--source", type=Path, help="단일 문서 모드의 원문 (--output과 함께 사용)")
    parser.add_argument("--template", type=Path, default=PROJECT_ROOT / "web" / "template.html")
    parser.add_argument("--output", type=Path, help="단일 문서 모드의 HTML 경로 (--source와 함께 사용)")
    parser.add_argument("--check", action="store_true", help="파일을 쓰지 않고 모든 대상의 최신 상태 확인")
    args = parser.parse_args(argv)
    if (args.source is None) != (args.output is None):
        parser.error("단일 문서는 --source와 --output을 함께 지정하세요.")
    try:
        if args.source is not None:
            output_dir = args.output.resolve().parent
            link_map = {
                os.path.relpath(PROJECT_ROOT / document.source, output_dir).replace(os.sep, "/"):
                os.path.relpath(PROJECT_ROOT / document.output, output_dir).replace(os.sep, "/")
                for document in DOCUMENTS
            }
            rendered = render_guide(
                args.source.read_text(encoding="utf-8"),
                args.template.read_text(encoding="utf-8"),
                relative_base=os.path.relpath(args.source.resolve().parent, output_dir).replace(os.sep, "/"),
                link_map=link_map,
                document_id=args.output.name,
            )
            pages = {args.output: rendered}
        else:
            sources = read_sources()
            rendered_pages = render_site(
                sources,
                args.template.read_text(encoding="utf-8"),
                (PROJECT_ROOT / "web" / "print-template.html").read_text(encoding="utf-8"),
            )
            pages = {PROJECT_ROOT / name: content for name, content in rendered_pages.items()}
        return check_or_write(pages, check=args.check)
    except (OSError, ValueError) as error:
        print(f"가이드 빌드 실패: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
