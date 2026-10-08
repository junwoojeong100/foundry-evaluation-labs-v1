#!/usr/bin/env python3
"""Build the offline HTML documents in docs/, or verify them with ``--check``.

The source is trusted, locally authored Markdown. Relative document links are
rebased for the output location; fenced-code contents remain unchanged. Use
``--source fixture.md --output fixture.html`` to build just one document.
"""

from __future__ import annotations

import argparse
import ast
import html
import json
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

BUILD_DATE = "2026-10-05"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SITE_DIRECTORY = "docs"
SITE_URL = "https://junwoojeong100.github.io/foundry-evaluation-labs-v1/"
LANGUAGES = ("en", "ko")
LOCALES = json.loads((PROJECT_ROOT / "web/locales.json").read_text(encoding="utf-8"))
REQUIRED_PLACEHOLDERS = ("CONTENT", "TOC", "BUILD_DATE")
PLACEHOLDER = re.compile(r"\{\{([A-Z_]+)\}\}")
SOURCE_DIRECTIVE = re.compile(r"<!-- source-code: ([A-Za-z0-9_./:-]+) -->")
SOURCE_FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
COMMAND_BLOCK = re.compile(r'<pre><code class="language-(sh|bash|powershell)">')


@dataclass(frozen=True)
class Document:
    source: str
    output: str
    label: str
    language: str = "en"

    @property
    def key(self) -> str:
        return posixpath.basename(self.output).removesuffix(".html")


DOCUMENTS = (
    Document("guide/en/handbook.md", "index.html", "Hands-on guide"),
    Document("guide/en/facilitator.md", "facilitator.html", "Lab checklist"),
    Document("guide/en/admin-setup.md", "admin.html", "Environment setup reference"),
    Document("guide/en/troubleshooting.md", "troubleshooting.html", "Troubleshooting"),
    Document("data/README.en.md", "data-guide.html", "Data guide"),
    Document("guide/handbook.md", "ko/index.html", "실습 가이드", "ko"),
    Document("guide/facilitator.md", "ko/facilitator.html", "실습 체크리스트", "ko"),
    Document("guide/admin-setup.md", "ko/admin.html", "환경 설정 참고", "ko"),
    Document("guide/troubleshooting.md", "ko/troubleshooting.html", "문제 해결", "ko"),
    Document("data/README.md", "ko/data-guide.html", "데이터 설명", "ko"),
)
DOCUMENT_LINKS = {
    document.source: posixpath.join(SITE_DIRECTORY, document.output)
    for document in DOCUMENTS
}


def locale(language: str) -> dict:
    if language not in LANGUAGES:
        raise ValueError(f"Unsupported guide language: {language}")
    return LOCALES[language]


def documents_for(language: str) -> tuple[Document, ...]:
    locale(language)
    return tuple(document for document in DOCUMENTS if document.language == language)


def localized_filename(filename: str, language: str) -> str:
    locale(language)
    return posixpath.join("ko", filename) if language == "ko" else filename


def language_links(filename: str, language: str, output_base: str) -> str:
    links = []
    for code, label in (("en", "English"), ("ko", "한국어")):
        path = posixpath.join(SITE_DIRECTORY, localized_filename(filename, code))
        href = html.escape(output_relative(path, output_base), quote=True)
        current = ' aria-current="page"' if code == language else ""
        links.append(
            f'<a href="{href}" lang="{code}" hreflang="{code}" data-language-link{current}>{label}</a>'
        )
    return "\n".join(links)


def output_relative(path: str, output_base: str = "") -> str:
    root = PROJECT_ROOT.as_posix()
    return posixpath.relpath(
        posixpath.join(root, path), posixpath.join(root, output_base or ".")
    )


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


def implementation_source(reference: str, *, root: Path = PROJECT_ROOT) -> tuple[str, str, str, int, int]:
    """Read a complete source symbol without importing or executing its module."""
    filename, separator, symbol = reference.partition(":")
    relative = Path(filename)
    if (
        relative.is_absolute()
        or not relative.parts
        or any(part.startswith(".") for part in relative.parts)
        or relative.parts[0] not in {"lab", "scripts", "schemas", "infra"}
        or relative.suffix not in {".py", ".json"}
    ):
        raise ValueError(f"허용되지 않은 구현 코드 경로입니다: {reference}")
    root = root.resolve()
    path = root / relative
    if not path.resolve().is_relative_to(root) or any(
        root.joinpath(*relative.parts[:index]).is_symlink()
        for index in range(1, len(relative.parts) + 1)
    ):
        raise ValueError(f"구현 코드 경로가 저장소 범위를 벗어납니다: {reference}")
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines(keepends=True)
    if not separator:
        return filename, source, "python" if relative.suffix == ".py" else "json", 1, len(lines)
    if relative.suffix != ".py" or not symbol:
        raise ValueError(f"Python 구현 기호를 지정해야 합니다: {reference}")
    node = ast.parse(source, filename=filename)
    for part in symbol.split("."):
        matches = [
            child for child in getattr(node, "body", [])
            if (
                isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                and child.name == part
            ) or (
                isinstance(child, ast.Assign)
                and any(isinstance(target, ast.Name) and target.id == part for target in child.targets)
            )
        ]
        if len(matches) != 1:
            raise ValueError(f"구현 코드 기호가 없거나 중복되었습니다: {reference}")
        node = matches[0]
    start = min([node.lineno, *(item.lineno for item in getattr(node, "decorator_list", []))])
    end = node.end_lineno
    if end is None:
        raise ValueError(f"구현 코드의 끝을 확인할 수 없습니다: {reference}")
    return filename, "".join(lines[start - 1:end]), "python", start, end


def expand_implementation_sources(markdown_text: str, *, relative_base: str, language: str) -> str:
    text = locale(language)["source"]
    output = []
    fence = None
    for line in markdown_text.splitlines(keepends=True):
        marker = SOURCE_FENCE.match(line)
        if marker:
            value = marker.group(1)
            if fence is None:
                fence = value
            elif value[0] == fence[0] and len(value) >= len(fence) and not line.strip().strip(value[0]):
                fence = None
        match = SOURCE_DIRECTIVE.fullmatch(line.rstrip("\r\n")) if fence is None else None
        if match is None:
            output.append(line)
            continue
        reference = match.group(1)
        filename, source, syntax, start, end = implementation_source(reference)
        local = posixpath.relpath(filename, relative_base or ".") + f"#L{start}-L{end}"
        online = f"https://github.com/junwoojeong100/foundry-evaluation-labs-v1/blob/main/{filename}#L{start}-L{end}"
        output.append(
            '<details class="implementation-code">\n'
            f'<summary>{html.escape(text["LABEL"])} · <code>{html.escape(reference)}</code></summary>\n'
            f'<p class="implementation-note">{html.escape(text["NOTE"])}</p>\n'
            '<p class="implementation-links">'
            f'<a href="{html.escape(local, quote=True)}">{html.escape(text["FILE"])} · {start}–{end}</a> · '
            f'<a href="{html.escape(online, quote=True)}">{html.escape(text["ONLINE"])}</a></p>\n'
            f'<pre class="implementation-source" data-source-reference="{html.escape(reference, quote=True)}">'
            f'<code class="language-{syntax}">{html.escape(source)}</code></pre>\n'
            '</details>\n'
        )
    return "".join(output)


def add_command_labels(content: str, language: str) -> str:
    messages = locale(language)["messages"]
    shells = {"sh": "shellShared", "bash": "shellBash", "powershell": "shellPowerShell"}

    def label(match: re.Match[str]) -> str:
        syntax = match.group(1)
        text = messages["commandLabel"].format(language=messages[shells[syntax]])
        return (
            f'<p class="command-label">{html.escape(text)}</p>\n'
            f'<pre class="terminal-command"><code class="language-{syntax}">'
        )

    return COMMAND_BLOCK.sub(label, content)


def add_code_portal_labels(content: str) -> str:
    class PortalTables(HtmlRewriter):
        def __init__(self) -> None:
            super().__init__()
            self.pending = False
            self.active = False
            self.headers: list[str] = []
            self.header: list[str] | None = None
            self.column = 0

        def handle_starttag(self, tag: str, attrs: list) -> None:
            attributes = dict(attrs)
            if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
                self.pending = tag == "h4" and attributes.get("id", "").endswith("-code-portal")
            if tag == "table":
                self.active = self.pending
                self.pending = False
                self.headers = []
                if self.active:
                    attrs = [(name, value) for name, value in attrs if name != "class"]
                    attrs.append(("class", (attributes.get("class", "") + " code-portal-map").strip()))
            if self.active and tag == "tr":
                self.column = 0
            if self.active and tag == "th":
                self.header = []
            if self.active and tag == "table":
                self.parts.append(self.start_tag(tag, attrs))
            else:
                super().handle_starttag(tag, attrs)
            if self.active and tag == "td":
                if self.column >= len(self.headers):
                    raise ValueError("코드 ↔ 포털 표의 데이터 열에 대응하는 제목이 없습니다.")
                self.parts.append(
                    '<span class="mobile-cell-label" aria-hidden="true">'
                    + html.escape(self.headers[self.column]) + "</span>"
                )
                self.column += 1

        def handle_data(self, data: str) -> None:
            super().handle_data(data)
            if self.header is not None:
                self.header.append(data)

        def handle_entityref(self, name: str) -> None:
            super().handle_entityref(name)
            if self.header is not None:
                self.header.append(html.unescape(f"&{name};"))

        def handle_charref(self, name: str) -> None:
            super().handle_charref(name)
            if self.header is not None:
                self.header.append(html.unescape(f"&#{name};"))

        def handle_endtag(self, tag: str) -> None:
            if tag == "th" and self.header is not None:
                title = " ".join("".join(self.header).split())
                if not title:
                    raise ValueError("코드 ↔ 포털 표의 열 제목이 비어 있습니다.")
                self.headers.append(title)
                self.header = None
            if tag == "table":
                self.active = False
            super().handle_endtag(tag)

    parser = PortalTables()
    parser.feed(content)
    parser.close()
    return "".join(parser.parts)


def render_markdown(
    markdown_text: str,
    *,
    relative_base: str = "",
    link_map: Mapping[str, str] | None = None,
    output_base: str = "",
    language: str = "en",
    toc_depth: str = "2-3",
) -> RenderedMarkdown:
    text = locale(language)["shell"]
    converter = Markdown(
        extensions=["fenced_code", "tables", "toc", "attr_list", "md_in_html"],
        extension_configs={
            "toc": {"slugify": slugify_unicode, "toc_depth": toc_depth},
        },
        output_format="html5",
    )
    if relative_base not in {"", "."} or link_map or output_base not in {"", "."}:
        def rebase(value: str, attribute: str) -> str:
            parsed = urlsplit(value)
            if parsed.scheme or parsed.netloc or not parsed.path or parsed.path.startswith("/"):
                return value
            path = posixpath.normpath(posixpath.join(relative_base, parsed.path))
            if attribute == "href" and link_map:
                path = link_map.get(unquote(path), path)
            if output_base not in {"", "."}:
                path = output_relative(path, output_base)
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
    content = converter.convert(expand_implementation_sources(
        markdown_text.lstrip("\ufeff"), relative_base=relative_base, language=language,
    ))
    content = add_code_portal_labels(add_command_labels(content, language))
    title_parser = _TitleParser()
    title_parser.feed(content)
    title = "".join(title_parser.parts).strip() or text["SITE_TITLE"]
    toc = converter.toc
    if not converter.toc_tokens:
        toc = f'<ul><li><a href="#guide-start">{text["FALLBACK_TOC"]}</a></li></ul>'
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
    output_base: str = "",
    language: str = "en",
) -> str:
    """Return deterministic UTF-8-ready HTML without reading or writing files."""
    filename = posixpath.basename(document_id)
    auxiliary = filename != "index.html"
    rendered = render_markdown(
        markdown_text, relative_base=relative_base, link_map=link_map,
        output_base=output_base, language=language,
        toc_depth="2-3" if auxiliary else "2-2",
    )
    text = locale(language)["shell"]
    chapter_unit = text["CHAPTER_UNIT" if auxiliary else "STEP_UNIT"]

    def site_href(filename: str) -> str:
        return html.escape(
            output_relative(posixpath.join(SITE_DIRECTORY, filename), output_base),
            quote=True,
        )

    navigation = ["<ul>"]
    for document in documents_for(language):
        current = ' aria-current="page"' if document.output == document_id else ""
        navigation.append(f'<li><a href="{site_href(document.output)}"{current}>{document.label}</a></li>')
    navigation.append("</ul>")
    home_href = site_href(localized_filename("index.html", language))
    replacements = {
        **{
            key: html.escape(value.replace("{unit}", chapter_unit), quote=True)
            for key, value in text.items()
        },
        "CONTENT": rendered.content,
        "TOC": rendered.toc,
        "BUILD_DATE": BUILD_DATE,
        "WEB_PATH": html.escape(output_relative("web", output_base), quote=True),
        "TITLE": html.escape(rendered.title, quote=True),
        "DOCUMENT_ID": html.escape(filename, quote=True),
        "PROGRESS_REVISION": "" if auxiliary else "end-to-end-10",
        "CHAPTER_UNIT": chapter_unit,
        "CONTENTS_LABEL": text["REFERENCE_CONTENTS" if auxiliary else "MAIN_CONTENTS"],
        "SIDEBAR_NOTE": text["REFERENCE_NOTE" if auxiliary else "MAIN_NOTE"],
        "CONTENT_LANGUAGE": language,
        "LANGUAGE_LINKS": language_links(filename, language, output_base),
        "MESSAGES": json.dumps(locale(language)["messages"], ensure_ascii=False).replace("<", "\\u003c"),
        "CANONICAL_HREF": SITE_URL + posixpath.join(SITE_DIRECTORY, localized_filename(filename, language)),
        "EN_HREF": SITE_URL + posixpath.join(SITE_DIRECTORY, filename),
        "KO_HREF": SITE_URL + posixpath.join(SITE_DIRECTORY, "ko", filename),
        "DOCUMENT_LINKS": "\n".join(navigation),
        "HOME_HREF": home_href if auxiliary else "#guide-start",
        "RETURN_LINK": (
            f'<a class="back-to-main no-print" href="{home_href}">{text["RETURN_LABEL"]}</a>'
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


def render_site(sources: Mapping[str, str], template: str) -> dict[str, str]:
    """Render every document before any output is written."""
    require_sources(sources)
    pages = {
        posixpath.join(SITE_DIRECTORY, document.output): render_guide(
            sources[document.source],
            template,
            relative_base=posixpath.dirname(document.source),
            link_map=DOCUMENT_LINKS,
            document_id=document.output,
            output_base=posixpath.dirname(posixpath.join(SITE_DIRECTORY, document.output)),
            language=document.language,
        )
        for document in DOCUMENTS
    }
    pages[posixpath.join(SITE_DIRECTORY, "english.html")] = render_english_redirect()
    return pages


def render_english_redirect() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Microsoft Foundry Lab Guide · English</title>
  <link rel="icon" type="image/svg+xml" href="../web/assets/foundry.svg">
  <script>window.location.replace("index.html" + window.location.search + window.location.hash);</script>
  <noscript><meta http-equiv="refresh" content="0; url=index.html"></noscript>
</head>
<body>
  <p>The full English guide is now the default. <a href="index.html">Open the English guide</a> · <a href="ko/index.html" lang="ko">한국어</a></p>
</body>
</html>
"""


def check_or_write(pages: Mapping[Path, str], *, check: bool) -> int:
    stale = False
    for path, rendered in pages.items():
        if check:
            try:
                current = path.read_bytes()
            except FileNotFoundError:
                print(f"생성 파일이 없습니다: {path}. 먼저 가이드를 빌드해야 합니다.", file=sys.stderr)
                stale = True
                continue
            if current != rendered.encode("utf-8"):
                print(f"생성 파일이 최신이 아닙니다: {path}. 가이드를 다시 빌드해야 합니다.", file=sys.stderr)
                stale = True
            else:
                print(f"최신 상태 확인: {path}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8", newline="\n") as output:
                output.write(rendered)
            print(f"가이드 생성: {path}")
    return 1 if stale else 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="가이드와 보조 문서를 함께 빌드합니다.")
    parser.add_argument("--source", type=Path, help="단일 문서 모드의 원문 (--output과 함께 사용)")
    parser.add_argument("--template", type=Path, default=PROJECT_ROOT / "web" / "template.html")
    parser.add_argument("--output", type=Path, help="단일 문서 모드의 HTML 경로 (--source와 함께 사용)")
    parser.add_argument("--language", choices=LANGUAGES, default="en", help="단일 문서의 언어. 전체 빌드는 항상 영어·한국어를 모두 생성합니다.")
    parser.add_argument("--check", action="store_true", help="파일을 쓰지 않고 모든 대상의 최신 상태 확인")
    args = parser.parse_args(argv)
    if (args.source is None) != (args.output is None):
        parser.error("단일 문서는 --source와 --output을 함께 지정해야 합니다.")
    try:
        if args.source is not None:
            output_dir = args.output.resolve().parent
            rendered = render_guide(
                args.source.read_text(encoding="utf-8"),
                args.template.read_text(encoding="utf-8"),
                relative_base=os.path.relpath(args.source.resolve().parent, PROJECT_ROOT).replace(os.sep, "/"),
                link_map=DOCUMENT_LINKS,
                document_id=args.output.name,
                output_base=os.path.relpath(output_dir, PROJECT_ROOT).replace(os.sep, "/"),
                language=args.language,
            )
            pages = {args.output: rendered}
        else:
            sources = read_sources()
            rendered_pages = render_site(
                sources,
                args.template.read_text(encoding="utf-8"),
            )
            pages = {PROJECT_ROOT / name: content for name, content in rendered_pages.items()}
        return check_or_write(pages, check=args.check)
    except (OSError, ValueError) as error:
        print(f"가이드 빌드 실패: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
