"""Portable print-book tests use in-memory sources and never write a PDF."""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import mock_open, patch
from urllib.parse import unquote, urlsplit

from scripts import build_guide, build_print

ROOT = Path(__file__).resolve().parents[1]
CODE = '<a href="facilitator.md#start">원문 링크 예시</a>\n{{BOOK_TOC}} & <tag>\n'


def source_fixtures() -> dict[str, str]:
    sources = {}
    for document in build_guide.DOCUMENTS:
        prefix = "../" if Path(document.source).parent != Path(".") else ""
        sources[document.source] = (
            f"# {document.label}\n\n## 시작 {{#start}}\n\n"
            f"[이 문서](#start) [참가자]({prefix}guide/handbook.md#start) "
            f"[SFT]({prefix}guide/sft-appendix.md#start) [강사]({prefix}guide/facilitator.md#start)\n\n"
            f"[관리자]({prefix}guide/admin-setup.md) [검증]({prefix}guide/verification.md) "
            f"[데이터]({prefix}data/README.md#start)\n\n"
            f"[코드 파일]({prefix}scripts/demo.py) [평가 데이터]({prefix}data/splits/test.jsonl)\n\n"
            "[공식 문서](https://learn.microsoft.com/azure/foundry/)\n\n"
            f"![예시 그림]({prefix}web/assets/example-diagram.svg)\n\n"
            '<p id="caption">설명</p>\n<div id="panel" aria-describedby="caption">안내</div>\n\n'
            "```html\n" + CODE + "```\n"
        )
    return sources


class BookInspector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.elements: list[tuple[str, dict]] = []
        self.pre_text: list[str] = []
        self._pre: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list) -> None:
        self.elements.append((tag, dict(attrs)))
        if tag == "pre":
            self._pre = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "pre" and self._pre is not None:
            self.pre_text.append("".join(self._pre))
            self._pre = None

    def handle_data(self, data: str) -> None:
        if self._pre is not None:
            self._pre.append(data)


class PrintBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.template = (ROOT / "web" / "print-template.html").read_text(encoding="utf-8")
        cls.sources = source_fixtures()
        cls.rendered = build_print.render_book(cls.sources, cls.template)
        cls.page = BookInspector()
        cls.page.feed(cls.rendered)

    def test_book_is_deterministic_and_uses_fixed_reference_date(self) -> None:
        self.assertEqual(self.rendered, build_print.render_book(self.sources, self.template))
        self.assertIn('datetime="2026-09-30"', self.rendered)
        self.assertTrue(self.rendered.endswith("\n"))
        plain = {source: "# 제목\n\n## 시작 {#start}\n\n본문" for source in self.sources}
        self.assertNotRegex(build_print.render_book(plain, self.template), r"\{\{[A-Z_]+\}\}")

    def test_main_and_appendices_follow_the_requested_order(self) -> None:
        sections = [attrs for tag, attrs in self.page.elements if tag == "section"]
        self.assertEqual([attrs["id"] for attrs in sections], ["book-" + key for key in build_print.BOOK_ORDER])
        self.assertNotIn("book-appendix", sections[0]["class"])
        self.assertTrue(all("book-appendix" in attrs["class"] for attrs in sections[1:]))
        self.assertIn("부록 1 · SFT 심화 부록", self.rendered)

    def test_all_heading_ids_are_unique_and_fragment_links_resolve(self) -> None:
        ids = [attrs["id"] for _, attrs in self.page.elements if "id" in attrs]
        self.assertEqual(len(ids), len(set(ids)))
        for document in build_guide.DOCUMENTS:
            self.assertIn(f"book-{document.key}--start", ids)
        for tag, attrs in self.page.elements:
            href = attrs.get("href", "")
            if tag == "a" and href.startswith("#"):
                self.assertIn(unquote(href[1:]), ids)
            for attribute in ("aria-labelledby", "aria-describedby", "aria-controls"):
                for target in attrs.get(attribute, "").split():
                    self.assertIn(target, ids)

    def test_cross_document_links_target_the_book_not_html_or_markdown_pages(self) -> None:
        for target in ("index", "sft", "facilitator", "data-guide"):
            self.assertIn(f'href="#book-{target}--start"', self.rendered)
        self.assertIn('href="#book-admin"', self.rendered)
        self.assertIn('href="#book-verification"', self.rendered)
        self.assertNotIn('href="sft.html', self.rendered)
        self.assertNotIn('href="guide/', self.rendered)
        self.assertIn('href="https://learn.microsoft.com/azure/foundry/"', self.rendered)

    def test_package_files_become_readable_labels_without_pdf_uri_links(self) -> None:
        self.assertIn('class="book-file-link"', self.rendered)
        self.assertIn("파일: <code>scripts/demo.py</code>", self.rendered)
        self.assertIn("파일: <code>data/splits/test.jsonl</code>", self.rendered)
        for tag, attrs in self.page.elements:
            if tag == "a":
                self.assertNotIn("scripts/", attrs.get("href", ""))
                self.assertNotIn("data/splits/", attrs.get("href", ""))

    def test_raw_html_and_local_preview_urls_are_portable(self) -> None:
        sources = dict(self.sources)
        sources["guide/handbook.md"] += (
            '\n<a href="sft-appendix.md#start">원시 HTML</a>\n'
            '<img src="../web/assets/example-diagram.svg" alt="구조">\n\n'
            "[미리보기](http://localhost:8000/facilitator.html#start)\n\n"
            "[로컬 파일](http://127.0.0.1:8000/scripts/demo.py)\n"
        )
        rendered = build_print.render_book(sources, self.template)
        page = BookInspector()
        page.feed(rendered)
        self.assertIn('href="#book-sft--start">원시 HTML</a>', rendered)
        self.assertIn('href="#book-facilitator--start">미리보기</a>', rendered)
        self.assertIn('src="../web/assets/example-diagram.svg"', rendered)
        for tag, attrs in page.elements:
            if tag == "a":
                self.assertNotIn(urlsplit(attrs.get("href", "")).hostname, build_print.LOCAL_HOSTS)

    def test_code_is_not_rewritten_or_turned_into_book_links(self) -> None:
        self.assertEqual(self.page.pre_text, [CODE] * len(build_guide.DOCUMENTS))
        self.assertIn("{{BOOK_TOC}} &amp; &lt;tag&gt;", self.rendered)

    def test_static_book_has_no_javascript_or_application_controls(self) -> None:
        forbidden = {"script", "button", "dialog", "input", "progress"}
        self.assertFalse(any(tag in forbidden for tag, _ in self.page.elements))
        self.assertIn('href="../web/styles.css"', self.rendered)
        self.assertIn('src="../web/assets/example-diagram.svg"', self.rendered)
        self.assertIn('<html lang="ko">', self.rendered)
        self.assertIn('class="skip-link" href="#book-main"', self.rendered)

    def test_print_css_starts_appendices_on_pages_without_fixed_height_spacers(self) -> None:
        css = (ROOT / "web" / "styles.css").read_text(encoding="utf-8")
        print_css = css.split("@media print", 1)[1]
        self.assertIn(".book-appendix { break-before: page; page-break-before: always;", print_css)
        self.assertIn("white-space: pre-wrap !important", print_css)
        self.assertIn("overflow: visible !important", print_css)
        self.assertIn("box-decoration-break: slice", print_css)
        self.assertNotRegex(print_css, r"(?:min-)?height:\s*(?:297mm|100vh)")

    def test_missing_sources_and_broken_book_anchors_fail_explicitly(self) -> None:
        missing = dict(self.sources)
        del missing["guide/verification.md"]
        with self.assertRaisesRegex(ValueError, "guide/verification.md"):
            build_print.render_book(missing, self.template)
        broken = dict(self.sources)
        broken["guide/handbook.md"] += "\n\n[없는 제목](sft-appendix.md#missing)\n"
        with self.assertRaisesRegex(ValueError, "sft-appendix.md#missing"):
            build_print.render_book(broken, self.template)

    def test_duplicate_raw_anchors_fail_instead_of_generating_ambiguous_targets(self) -> None:
        sources = dict(self.sources)
        sources["guide/handbook.md"] += '\n<div id="same">첫째</div>\n<div id="same">둘째</div>\n'
        with self.assertRaisesRegex(ValueError, "중복된 앵커"):
            build_print.render_book(sources, self.template)

    def test_check_is_read_only_and_rejects_stale_or_missing_book(self) -> None:
        for current in (self.rendered.encode("utf-8"), b"stale\n", FileNotFoundError("print.html")):
            with self.subTest(current=type(current).__name__):
                read = {"side_effect": current} if isinstance(current, Exception) else {"return_value": current}
                with patch.object(build_guide, "read_sources", return_value=self.sources), \
                     patch.object(Path, "read_text", return_value=self.template), \
                     patch.object(Path, "read_bytes", **read), \
                     patch.object(Path, "open") as output_open, \
                     redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    expected = 0 if current == self.rendered.encode("utf-8") else 1
                    self.assertEqual(build_print.main(["--check"]), expected)
                    output_open.assert_not_called()

    def test_book_build_writes_only_the_requested_html_with_utf8_lf(self) -> None:
        output = mock_open()
        with patch.object(build_guide, "read_sources", return_value=self.sources), \
             patch.object(Path, "read_text", return_value=self.template), \
             patch.object(Path, "open", output), \
             redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(build_print.main(["--output", "print.html"]), 0)
        output.assert_called_once_with("w", encoding="utf-8", newline="\n")
        output().write.assert_called_once_with(
            build_print.render_book(self.sources, self.template, output_base=".")
        )

    def test_missing_source_stops_book_command_without_writing(self) -> None:
        with patch.object(build_guide, "read_sources", side_effect=ValueError("필수 원문이 없습니다: guide/verification.md")), \
             patch.object(Path, "open") as output_open, \
             redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(build_print.main([]), 2)
            output_open.assert_not_called()


if __name__ == "__main__":
    unittest.main()
