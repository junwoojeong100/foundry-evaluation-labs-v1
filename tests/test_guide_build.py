"""Offline shell tests use in-memory Markdown fixtures, never the real handbook."""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import mock_open, patch
from urllib.parse import unquote

from scripts import build_guide

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = """# 평가 안내 & 검증

한국어 본문을 오프라인에서 읽는 임시 가이드입니다.

## 시작하기

지식 기반과 평가 지표를 확인합니다.
[관련 실습](labs/first-step.md)

![예시 그림](web/assets/example-diagram.svg)

### 명령 실행

```python
if left < right:
    print("{{TOC}} & <tag>")
```

| 항목 | 확인 방법 |
| --- | --- |
| 평가 | 보류 데이터로 검증 |

## 시작하기

같은 제목도 서로 다른 앵커를 갖습니다.

## 다음 단계 {#next-step}

본문에서 [처음 단계](#시작하기)로 돌아갈 수 있습니다.
"""


class PageInspector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.elements: list[tuple[str, dict[str, str | None]]] = []
        self.pre_text: list[str] = []
        self._pre: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
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


class GuideBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.template = (ROOT / "web" / "template.html").read_text(encoding="utf-8")
        cls.css = (ROOT / "web" / "styles.css").read_text(encoding="utf-8")
        cls.rendered = build_guide.render_guide(FIXTURE, cls.template)
        cls.page = PageInspector()
        cls.page.feed(cls.rendered)

    def test_build_is_deterministic_and_date_is_fixed(self) -> None:
        self.assertEqual(build_guide.BUILD_DATE, "2026-09-30")
        self.assertEqual(self.rendered, build_guide.render_guide(FIXTURE, self.template))
        self.assertIn('datetime="2026-09-30"', self.rendered)
        self.assertTrue(self.rendered.endswith("\n"))
        self.assertFalse(self.rendered.endswith("\n\n"))

    def test_all_shell_placeholders_are_replaced(self) -> None:
        rendered = build_guide.render_guide("# 임시 가이드\n\n## 첫 장\n\n본문입니다.", self.template)
        self.assertNotRegex(rendered, r"\{\{[A-Z_]+\}\}")
        self.assertIn("<title>임시 가이드 · Foundry 실습 가이드</title>", rendered)

    def test_title_is_escaped_and_inline_markup_is_not_in_the_title(self) -> None:
        rendered = build_guide.render_guide('# 평가 & <em>검증</em> "안내"\n\n## 본문', self.template)
        self.assertIn("<title>평가 &amp; 검증 &quot;안내&quot; · Foundry 실습 가이드</title>", rendered)
        self.assertIn('aria-label="평가 &amp; 검증 &quot;안내&quot;"', rendered)

    def test_fenced_code_is_escaped_without_changing_code_or_template_literals(self) -> None:
        code = 'if left < right:\n    print("{{TOC}} & <tag>")\n'
        self.assertEqual(self.page.pre_text, [code])
        self.assertIn("&lt; right", self.rendered)
        self.assertIn("&lt;tag&gt;", self.rendered)
        self.assertIn("{{TOC}}", self.rendered)
        self.assertIn('class="language-python"', self.rendered)

    def test_relative_links_and_local_asset_paths_are_unchanged(self) -> None:
        for value in (
            'href="labs/first-step.md"',
            'src="web/assets/example-diagram.svg"',
            'href="web/styles.css"',
            'src="web/app.js"',
        ):
            self.assertIn(value, self.rendered)
        self.assertTrue(any(tag == "table" for tag, _ in self.page.elements))

    def test_authored_intro_classes_are_supported(self) -> None:
        source = (
            '<p class="eyebrow">한국어 실습 문서</p>\n\n'
            "# 임시 안내서\n\n리드 문단입니다.\n{: .hero-summary}\n\n"
            '<div class="hero-summary">\n'
            "<div><strong>고객 질문</strong><span>개선 근거를 어떻게 확인하나요?</span></div>\n"
            "<div><strong>완성 결과</strong><span>버전별 평가 근거</span></div>\n"
            "</div>\n\n## 시작\n"
        )
        rendered = build_guide.render_guide(source, self.template)
        self.assertIn('<p class="eyebrow">한국어 실습 문서</p>', rendered)
        self.assertIn('<p class="hero-summary">리드 문단입니다.</p>', rendered)
        self.assertIn("<strong>고객 질문</strong><span>개선 근거를 어떻게 확인하나요?</span>", rendered)
        self.assertIn(".guide-content .eyebrow", self.css)
        self.assertIn(".guide-content .hero-summary", self.css)
        self.assertIn(".guide-content div.hero-summary { display: grid;", self.css)
        self.assertIn(".guide-content .hero-summary > div > strong", self.css)

    def test_source_relative_document_links_are_rebased_for_root_html(self) -> None:
        source = (
            "# 링크 검사\n\n## 시작\n\n"
            "![그림](../web/assets/example-diagram.svg)\n\n"
            "[강사](facilitator.md#준비) [외부](https://learn.microsoft.com/) [본문](#시작)"
        )
        rendered = build_guide.render_guide(source, self.template, relative_base="guide")
        self.assertIn('src="web/assets/example-diagram.svg"', rendered)
        self.assertIn('href="guide/facilitator.md#준비"', rendered)
        self.assertIn('href="https://learn.microsoft.com/"', rendered)
        self.assertIn('href="#시작"', rendered)

    def test_document_links_map_to_html_after_rebasing(self) -> None:
        source = (
            "# 문서 연결\n\n## 시작\n\n"
            "[강사](facilitator.md#준비) [관리자](admin-setup.md?mode=read#rbac)\n\n"
            "[SFT](sft-appendix.md) [검증](verification.md) [데이터](../data/README.md)\n\n"
            '<a href="../guide/handbook.md#start">참가자</a>\n\n'
            '<img src="../web/assets/example-diagram.svg" alt="구조">\n'
        )
        rendered = build_guide.render_guide(
            source, self.template, relative_base="guide", link_map=build_guide.DOCUMENT_LINKS
        )
        for href in (
            "docs/facilitator.html#준비", "docs/admin.html?mode=read#rbac", "docs/sft.html",
            "docs/verification.html", "docs/data-guide.html", "docs/index.html#start",
        ):
            self.assertIn(f'href="{href}"', rendered)
        self.assertIn('src="web/assets/example-diagram.svg"', rendered)

    def test_nested_output_rebases_docs_assets_and_source_files_independently(self) -> None:
        source = (
            "# 안내\n\n[강사](facilitator.md#start) [정책](../data/knowledge/documents.json)\n\n"
            "![사진](../web/assets/portal/01-project-overview.png)\n\n"
            "```bash\npython -m lab validate\n```\n"
        )
        rendered = build_guide.render_guide(
            source, self.template, relative_base="guide",
            link_map=build_guide.DOCUMENT_LINKS, output_base="docs",
        )
        for value in (
            'href="facilitator.html#start"', 'href="../data/knowledge/documents.json"',
            'src="../web/assets/portal/01-project-overview.png"',
            'src="../web/theme.js"', 'href="../web/styles.css"', 'src="../web/app.js"',
            'href="Foundry-Learning-Loop-Lab-KO.pdf"',
        ):
            self.assertIn(value, rendered)
        self.assertIn("python -m lab validate", rendered)
        readme = build_guide.render_markdown(
            "[가이드](docs/index.html?from=readme#start) [검증](evidence/latest.json)",
            output_base="docs",
        )
        self.assertIn('href="index.html?from=readme#start"', readme.content)
        self.assertIn('href="../evidence/latest.json"', readme.content)

    def test_output_writer_creates_only_requested_directories_and_check_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "docs/index.html"
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(build_guide.check_or_write({output: "page\n"}, check=True), 1)
                self.assertFalse(output.parent.exists())
                self.assertEqual(build_guide.check_or_write({output: "page\n"}, check=False), 0)
                self.assertEqual(build_guide.check_or_write({output: "page\n"}, check=True), 0)
            self.assertEqual(output.read_bytes(), b"page\n")

    def test_mapping_does_not_rewrite_code_that_looks_like_html_or_markdown(self) -> None:
        code = '<a href="facilitator.md">예시</a>\n![그림](../web/assets/example-diagram.svg)\n{{CONTENT}} & < >\n'
        rendered = build_guide.render_guide(
            "# 코드\n\n## 원문\n\n```html\n" + code + "```\n",
            self.template, relative_base="guide", link_map=build_guide.DOCUMENT_LINKS,
        )
        page = PageInspector()
        page.feed(rendered)
        self.assertEqual(page.pre_text, [code])

    def _site_sources(self) -> dict[str, str]:
        return {
            document.source: FIXTURE.replace("(web/assets/", "(../web/assets/")
            for document in build_guide.DOCUMENTS
        }

    def _site_pages(self) -> dict[str, str]:
        print_template = (ROOT / "web" / "print-template.html").read_text(encoding="utf-8")
        return build_guide.render_site(self._site_sources(), self.template, print_template)

    def test_full_site_is_deterministic_and_namespaces_document_progress(self) -> None:
        pages = self._site_pages()
        self.assertEqual(pages, self._site_pages())
        self.assertEqual(
            set(pages),
            {"docs/" + document.output for document in build_guide.DOCUMENTS} | {"docs/print.html"},
        )
        identities = []
        for document in build_guide.DOCUMENTS:
            page = PageInspector()
            rendered = pages["docs/" + document.output]
            page.feed(rendered)
            identity = next(attrs["data-document-id"] for tag, attrs in page.elements if tag == "body")
            self.assertEqual(identity, document.output)
            identities.append(identity)
            if document.output != "index.html":
                self.assertIn('class="back-to-main no-print" href="index.html"', rendered)
            self.assertIn('href="../web/styles.css"', rendered)
            self.assertIn('src="../web/app.js"', rendered)
        self.assertEqual(len(identities), len(set(identities)))
        app = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
        self.assertIn("document.body.dataset.documentId", app)
        self.assertIn("progress:v2:${encodeURIComponent(documentId)}", app)
        self.assertIn('stored === null && documentId === "index.html"', app)

    def test_full_build_requires_all_sources_instead_of_placeholder_pages(self) -> None:
        sources = self._site_sources()
        del sources["guide/verification.md"]
        with self.assertRaisesRegex(ValueError, "guide/verification.md"):
            build_guide.render_site(sources, self.template, "unused")

    def test_single_path_progress_is_separate_from_old_chapters_and_reference_pages(self) -> None:
        pages = self._site_pages()
        for name in ("index.html", "facilitator.html", "admin.html", "english.html"):
            page = PageInspector()
            page.feed(pages["docs/" + name])
            body = next(attrs for tag, attrs in page.elements if tag == "body")
            self.assertEqual(body["data-document-id"], name)
            self.assertEqual(body["data-progress-revision"], "single-path-6" if name == "index.html" else "")
        self.assertIn("실습 순서", pages["docs/index.html"])
        self.assertIn("참고 문서 목차", pages["docs/admin.html"])
        app = (ROOT / "web/app.js").read_text(encoding="utf-8")
        self.assertIn("document.body.dataset.progressRevision", app)
        self.assertIn('stored === null && documentId === "index.html" && !progressRevision', app)
        self.assertIn("authoredNextTargets.has(next.id)", app)
        self.assertNotIn("localStorage.removeItem", app)

    def test_default_check_validates_all_outputs_and_does_not_write(self) -> None:
        pages = self._site_pages()
        print_template = (ROOT / "web" / "print-template.html").read_text(encoding="utf-8")
        for stale in (None, "admin.html", "print.html", "missing:verification.html"):
            with self.subTest(stale=stale):
                def read_output(path: Path) -> bytes:
                    if stale == "missing:" + path.name:
                        raise FileNotFoundError(path)
                    self.assertEqual(path.parent, ROOT / "docs")
                    return b"stale\n" if path.name == stale else pages[path.relative_to(ROOT).as_posix()].encode("utf-8")

                with patch.object(build_guide, "read_sources", return_value=self._site_sources()), \
                     patch.object(Path, "read_text", autospec=True, side_effect=lambda path, **kwargs: print_template if path.name == "print-template.html" else self.template), \
                     patch.object(Path, "read_bytes", autospec=True, side_effect=read_output) as reads, \
                     patch.object(Path, "open") as output_open, \
                     redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    self.assertEqual(build_guide.main(["--check"]), 1 if stale else 0)
                    self.assertEqual(reads.call_count, len(pages))
                    output_open.assert_not_called()

    def test_missing_source_aborts_full_build_before_any_write(self) -> None:
        def read_source(path: Path, **kwargs: object) -> str:
            if path.name == "verification.md":
                raise FileNotFoundError(path)
            return FIXTURE

        error = io.StringIO()
        with patch.object(Path, "read_text", autospec=True, side_effect=read_source), \
             patch.object(Path, "open") as output_open, \
             redirect_stdout(io.StringIO()), redirect_stderr(error):
            self.assertEqual(build_guide.main([]), 2)
            output_open.assert_not_called()
        self.assertIn("guide/verification.md", error.getvalue())

    def test_single_document_mode_requires_explicit_source_and_output(self) -> None:
        for args in (["--source", "fixture.md"], ["--output", "fixture.html"]):
            with self.subTest(args=args), redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    build_guide.main(args)
                self.assertEqual(raised.exception.code, 2)

    def test_korean_toc_and_duplicate_headings_have_valid_unique_targets(self) -> None:
        ids = [attrs["id"] for _, attrs in self.page.elements if "id" in attrs]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn("시작하기", ids)
        self.assertIn("시작하기_1", ids)
        self.assertIn("next-step", ids)
        for tag, attrs in self.page.elements:
            href = attrs.get("href", "") or ""
            if tag == "a" and href.startswith("#"):
                self.assertIn(unquote(href[1:]), ids, href)

    def test_accessible_landmarks_and_control_references(self) -> None:
        elements = {attrs["id"]: (tag, attrs) for tag, attrs in self.page.elements if "id" in attrs}
        self.assertEqual(elements["main-content"][0], "main")
        self.assertEqual(elements["main-content"][1]["tabindex"], "-1")
        self.assertEqual(elements["chapter-nav"][0], "nav")
        self.assertNotIn("search-dialog", elements)
        self.assertNotIn("search-input", elements)
        self.assertEqual(elements["reset-dialog"][0], "dialog")
        self.assertEqual(elements["announcements"][1]["aria-live"], "polite")
        self.assertIn('class="skip-link" href="#main-content"', self.rendered)
        self.assertIn('class="chapter-pagination no-print"', self.rendered)
        self.assertIn('method="dialog"', self.rendered)
        self.assertIn("<noscript>", self.rendered)
        self.assertIn('<html lang="ko">', self.rendered)
        for _, attrs in self.page.elements:
            for attribute in ("aria-labelledby", "aria-describedby", "aria-controls"):
                for target in (attrs.get(attribute) or "").split():
                    self.assertIn(target, elements, f"{attribute}: {target}")

    def test_header_has_theme_current_print_and_full_pdf_in_reference_order(self) -> None:
        expected = ["data-theme-toggle", "data-print-one", "data-print-all"]
        controls = [
            attribute for tag, attrs in self.page.elements if tag == "button"
            for attribute in expected if attribute in attrs
        ]
        self.assertEqual(controls, expected)
        self.assertNotIn("본문 검색", self.rendered)
        self.assertNotIn("data-search-open", self.rendered)
        self.assertNotIn("data-print ", self.rendered)
        self.assertLess(self.rendered.index('src="web/theme.js"'), self.rendered.index('href="web/styles.css"'))
        self.assertIn(':root[data-theme="dark"]', self.css)
        self.assertIn('body[data-print="one"] .print-excluded', self.css)
        app = (ROOT / "web/app.js").read_text(encoding="utf-8")
        self.assertIn('window.addEventListener("afterprint", restorePrint)', app)
        self.assertNotIn("openSearch", app)

    def test_runtime_dependencies_are_local(self) -> None:
        for tag, attrs in self.page.elements:
            if tag == "script" or (tag == "link" and attrs.get("rel") == "stylesheet"):
                path = attrs.get("src") or attrs.get("href") or ""
                self.assertTrue(path.startswith("web/"), path)
                self.assertNotIn("://", path)
        self.assertNotRegex(self.css, r"@import\b")
        self.assertNotRegex(self.css, r"url\(\s*[\"']?(?:https?:)?//")

    def test_a4_print_wraps_instead_of_clipping_code_and_tables(self) -> None:
        self.assertRegex(self.css, r"@page\s*\{\s*size:\s*A4")
        print_css = self.css.split("@media print", 1)[1]
        for rule in (
            "white-space: pre-wrap !important",
            "overflow-wrap: anywhere !important",
            "overflow: visible !important",
            "min-width: 0 !important",
            "table-layout: fixed",
            "display: table-header-group",
            "page-break-inside: auto",
        ):
            self.assertIn(rule, print_css)
        self.assertRegex(print_css, r"\.no-print[^}]+display:\s*none\s*!important")
        self.assertIn("@media (prefers-reduced-motion: reduce)", self.css)
        self.assertRegex(self.css, r":focus-visible\s*\{[^}]*outline:\s*3px")

    def test_anchor_offset_is_not_applied_twice(self) -> None:
        self.assertIn("scroll-margin-top: calc(var(--header-height) + 1.5rem)", self.css)
        self.assertRegex(self.css, r"\.share-checkpoint[^{}]*\{[^}]*scroll-margin-top:")
        self.assertNotRegex(self.css, r"scroll-padding-top:\s*calc\(")

    def test_missing_or_unknown_template_placeholders_fail_clearly(self) -> None:
        for placeholder in build_guide.REQUIRED_PLACEHOLDERS:
            with self.subTest(placeholder=placeholder):
                template = self.template.replace("{{" + placeholder + "}}", "")
                with self.assertRaisesRegex(ValueError, "필수 템플릿"):
                    build_guide.render_guide(FIXTURE, template)
        with self.assertRaisesRegex(ValueError, "알 수 없는"):
            build_guide.render_guide(FIXTURE, self.template + "{{UNKNOWN}}")

    def test_heading_free_markdown_remains_readable(self) -> None:
        rendered = build_guide.render_guide("제목 없는 짧은 메모입니다.", self.template)
        self.assertIn("<p>제목 없는 짧은 메모입니다.</p>", rendered)
        self.assertIn('href="#guide-start">본문 읽기</a>', rendered)

    def _read_fixture(self, path: Path, *args: object, **kwargs: object) -> str:
        if path.name == "fixture.md":
            return FIXTURE
        if path.name == "template.html":
            return self.template
        raise FileNotFoundError(path)

    def _cli_args(self) -> list[str]:
        return ["--source", "fixture.md", "--template", "web/template.html", "--output", "index.html"]

    def test_check_matches_and_never_opens_output_for_writing(self) -> None:
        with patch.object(Path, "read_text", autospec=True, side_effect=self._read_fixture), \
             patch.object(Path, "read_bytes", return_value=self.rendered.encode("utf-8")), \
             patch.object(Path, "open") as output_open, \
             redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(build_guide.main([*self._cli_args(), "--check"]), 0)
            output_open.assert_not_called()

    def test_check_rejects_stale_missing_and_different_line_endings(self) -> None:
        cases = (b"outdated\n", self.rendered.replace("\n", "\r\n").encode("utf-8"), FileNotFoundError("index.html"))
        for current in cases:
            with self.subTest(current=type(current).__name__):
                read = {"side_effect": current} if isinstance(current, Exception) else {"return_value": current}
                with patch.object(Path, "read_text", autospec=True, side_effect=self._read_fixture), \
                     patch.object(Path, "read_bytes", **read), \
                     patch.object(Path, "open") as output_open, \
                     redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    self.assertEqual(build_guide.main([*self._cli_args(), "--check"]), 1)
                    output_open.assert_not_called()

    def test_build_writes_utf8_with_explicit_lf_newlines(self) -> None:
        output = mock_open()
        with patch.object(Path, "read_text", autospec=True, side_effect=self._read_fixture), \
             patch.object(Path, "open", output), \
             redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(build_guide.main(self._cli_args()), 0)
        output.assert_called_once_with("w", encoding="utf-8", newline="\n")
        output().write.assert_called_once_with(self.rendered)

    def test_missing_source_returns_an_error_without_writing(self) -> None:
        with patch.object(Path, "read_text", side_effect=FileNotFoundError("fixture.md")), \
             patch.object(Path, "open") as output_open, \
             redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(build_guide.main(self._cli_args()), 2)
            output_open.assert_not_called()

if __name__ == "__main__":
    unittest.main()
