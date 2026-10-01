"""Check the published, native Foundry Evaluation and Agent Optimizer guide."""

import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shlex
import struct
import unittest
from urllib.parse import unquote, urlsplit

from scripts.build_guide import DOCUMENTS, SITE_URL, documents_for
from scripts.package_lab import GUIDE_FILES, package_files

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "docs"
PAGES = tuple(document.output for document in DOCUMENTS) + ("english.html", "print.html", "ko/print.html")
STEPS = ["start", "prepare", "baseline", "analyze", "optimize", "decision"]


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.links = []
        self.duplicate_ids = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            if attrs["id"] in self.ids:
                self.duplicate_ids.add(attrs["id"])
            self.ids.add(attrs["id"])
        for key in ("href", "src"):
            if key in attrs:
                self.links.append(attrs[key])


class LearningPathParser(LinkParser):
    def __init__(self):
        super().__init__()
        self.chapters = []
        self.subchapters = []
        self.toc_links = []
        self.overview_links = []
        self.next_links = []
        self.sharing_checkpoints = []
        self.in_article = False
        self.in_toc = False
        self.in_overview = False

    def handle_starttag(self, tag, attrs):
        super().handle_starttag(tag, attrs)
        attrs = dict(attrs)
        if tag == "article" and attrs.get("id") == "guide-start":
            self.in_article = True
        if tag == "nav" and attrs.get("id") == "chapter-nav":
            self.in_toc = True
        if tag == "ol" and "learning-path" in attrs.get("class", "").split():
            self.in_overview = True
        if self.in_article and tag == "h2":
            self.chapters.append(attrs.get("id"))
        if self.in_article and tag == "h3":
            self.subchapters.append(attrs.get("id"))
        if self.in_article and tag == "p" and "share-checkpoint" in attrs.get("class", "").split():
            self.sharing_checkpoints.append((attrs.get("id"), self.chapters[-1] if self.chapters else None))
        if tag == "a":
            if self.in_toc:
                self.toc_links.append(attrs.get("href"))
            if self.in_overview:
                self.overview_links.append(attrs.get("href"))
            if self.in_article and "data-next-step" in attrs:
                self.next_links.append(attrs.get("href"))

    def handle_endtag(self, tag):
        if tag == "article":
            self.in_article = False
        elif tag == "nav":
            self.in_toc = False
        elif tag == "ol":
            self.in_overview = False


class PortalFigureParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.figures = []
        self.current = None
        self.in_caption = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "figure" and "portal-shot" in attrs.get("class", "").split():
            self.current = {"id": attrs.get("id"), "images": [], "links": [], "caption": ""}
        if self.current is not None:
            if tag == "img":
                self.current["images"].append(attrs)
            elif tag == "a":
                self.current["links"].append(attrs.get("href"))
            elif tag == "figcaption":
                self.in_caption = True

    def handle_data(self, data):
        if self.in_caption and self.current is not None:
            self.current["caption"] += data

    def handle_endtag(self, tag):
        if tag == "figcaption":
            self.in_caption = False
        elif tag == "figure" and self.current is not None:
            self.figures.append(self.current)
            self.current = None


class ArticleTextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_article = False
        self.text = []
        self.alt = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "article" and attrs.get("id") == "guide-start":
            self.in_article = True
        if self.in_article and tag == "img":
            self.alt.append(attrs.get("alt", ""))

    def handle_endtag(self, tag):
        if tag == "article":
            self.in_article = False

    def handle_data(self, data):
        if self.in_article:
            self.text.append(data)


class DocumentationTests(unittest.TestCase):
    def source(self, language):
        return (ROOT / ("guide/en/handbook.md" if language == "en" else "guide/handbook.md")).read_text(encoding="utf-8")

    def test_english_is_the_default_and_all_guides_are_packaged(self):
        self.assertEqual({path.name for path in ROOT.glob("*.html")}, {"index.html"})
        self.assertFalse(list(ROOT.glob("*.pdf")))
        entry = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('<html lang="en">', entry)
        self.assertIn('"docs/index.html" + window.location.search + window.location.hash', entry)
        self.assertIn("<noscript>", entry)
        self.assertIn('href="docs/ko/index.html"', entry)
        self.assertTrue((ROOT / ".nojekyll").is_file())
        packaged = {path.relative_to(ROOT).as_posix() for path in package_files(ROOT)}
        self.assertTrue(set(GUIDE_FILES).issubset(packaged))
        self.assertIn(".nojekyll", packaged)
        for name in PAGES:
            self.assertTrue((SITE / name).is_file(), name)

    def test_only_the_current_verification_record_is_published(self):
        self.assertEqual(
            {path.relative_to(ROOT / "evidence").as_posix() for path in (ROOT / "evidence").rglob("*") if path.is_file()},
            {"latest.json"},
        )
        latest = json.loads((ROOT / "evidence/latest.json").read_text())
        self.assertEqual(latest["schema_version"], 1)
        for name in ("README.md", "README.en.md", "README.ko.md"):
            self.assertIn("evidence/latest.json", (ROOT / name).read_text())

    def test_latest_v2_publishes_every_case_without_obsolete_reports(self):
        latest = json.loads((ROOT / "evidence/latest.json").read_text())
        self.assertEqual(latest["kind"], "LATEST_SOL_V2_MANAGED_EVALUATION")
        self.assertEqual(latest["models"]["agent"]["name"], "gpt-6-sol")
        self.assertEqual(latest["scope"]["released_versions"], ["1", "2"])
        self.assertEqual(latest["baseline"]["agent_version"], "1")
        self.assertEqual(latest["candidate"]["agent_version"], "2")
        self.assertEqual(latest["agent"]["active_lab_version"], "2")
        self.assertNotIn("follow_up_refinement", latest)
        self.assertNotIn("native_foundry", latest)
        self.assertFalse(latest["decision"]["guarantees_future_results"])
        self.assertEqual(latest["decision"]["production_approval"], "NOT_GRANTED")
        dataset = [json.loads(line) for line in (ROOT / "data/en/optimizer/dev.jsonl").read_text().splitlines()]
        self.assertEqual(len(latest["case_evidence"]), len(dataset))
        for expected, actual in zip(dataset, latest["case_evidence"], strict=True):
            self.assertEqual(expected["query"], actual["query"])
            self.assertEqual(expected["context"], actual["reference_context"])
            self.assertEqual(expected["ground_truth"], actual["reference_answer"])
            for arm in ("baseline", "candidate"):
                self.assertTrue(actual[arm]["response"])
                self.assertEqual(set(actual[arm]["metrics"]), {"Relevance", "TaskAdherence"})
                for metric in actual[arm]["metrics"].values():
                    self.assertTrue(metric["reason"])
                    self.assertIs(type(metric["passed"]), bool)
                self.assertNotIn("conversation_id", actual[arm])
        for edition in ("guide/verification.md", "guide/en/verification.md"):
            text = (ROOT / edition).read_text()
            self.assertIn(latest["candidate"]["run_id"], text)
            self.assertNotIn("evalrun_edcc42822c0c4d27ad734b474379964e", text)
            self.assertNotIn("evalrun_9609268e6d30446abc01c6b1fe2011d8", text)

    def test_removed_training_guides_do_not_return_in_any_edition(self):
        for name in ("guide/sft-appendix.md", "guide/en/sft-appendix.md", "docs/sft.html", "docs/ko/sft.html", "web/assets/portal/14-sft-job.png"):
            self.assertFalse((ROOT / name).exists(), name)
        paths = [
            *(ROOT / "guide").rglob("*.md"),
            ROOT / "README.md", ROOT / "README.en.md", ROOT / "README.ko.md",
            ROOT / "data/README.md", ROOT / "data/README.en.md",
            *(SITE / name for name in PAGES),
        ]
        for path in paths:
            with self.subTest(document=path.relative_to(ROOT)):
                self.assertNotRegex(path.read_text(encoding="utf-8"), r"(?i)\bSFT\b|sft-appendix|sft\.html|Supervised Fine.Tuning")
        self.assertTrue(all(document.key != "sft" for document in DOCUMENTS))

    def test_both_participant_guides_have_exactly_one_six_step_path(self):
        for language, filename in (("en", "index.html"), ("ko", "ko/index.html")):
            with self.subTest(language=language):
                page = LearningPathParser()
                page.feed((SITE / filename).read_text())
                links = ["#" + step for step in STEPS]
                self.assertEqual(page.chapters, STEPS)
                self.assertEqual(page.subchapters, [])
                self.assertEqual(page.toc_links, links)
                self.assertEqual(page.overview_links, links)
                self.assertEqual(page.next_links, links[1:])
                self.assertIn('data-progress-revision="native-eval-optimizer-6"', (SITE / filename).read_text())
                self.assertLess(len(self.source(language).splitlines()), 500)

    def test_native_foundry_actions_not_a_custom_local_judge_are_the_core(self):
        for language in ("en", "ko"):
            source = self.source(language)
            with self.subTest(language=language):
                for required in (
                    "Foundry Evaluation", "Agent Optimizer", "Evaluations", "Create",
                    "Individual turns", "One time", "Existing dataset", "Relevance",
                    "TaskAdherence", "Submit", "Compare runs", "12",
                ):
                    self.assertIn(required, source)
                self.assertNotRegex(source, r"python(?:3)?\s+-m\s+lab\s+(?:judge|freeze|governance|tune-prepare|demo)\b")
                self.assertNotIn("iq prepare", source)
                self.assertIn("add_foundry_eval_run.py", source)
                self.assertIn("{{item.query}}", source)
                self.assertIn("--baseline", source)
                self.assertIn("--version", source)

    def test_the_two_datasets_and_evaluator_scales_are_not_conflated(self):
        for language in ("en", "ko"):
            source = self.source(language)
            with self.subTest(language=language):
                self.assertIn("data/en/optimizer/dev.jsonl" if language == "en" else "data/optimizer/dev.jsonl", source)
                self.assertIn("ground_truth", source)
                self.assertIn("context", source)
                self.assertIn("query", source)
                self.assertRegex(source, r"0\s*(?:/|–|-|또는|or)\s*1|Pass/Fail")
                self.assertRegex(source, r"1\s*(?:–|-|~|to)\s*5")
                self.assertRegex(source, r"(?:Threshold|threshold|임계값|기준).{0,80}4|4.{0,80}(?:Threshold|threshold|임계값|기준)")
                self.assertNotIn("TaskAdherence 4", source)
                self.assertNotIn("Task Adherence 4", source)

    def test_verified_model_roles_and_fixed_release_boundaries_are_visible(self):
        for language in ("en", "ko"):
            source = self.source(language)
            admin = (ROOT / ("guide/en/admin-setup.md" if language == "en" else "guide/admin-setup.md")).read_text()
            with self.subTest(language=language):
                self.assertIn("gpt-6-luna", source + admin)
                self.assertIn("gpt-5.5", source + admin)
                self.assertIn("gpt-6-sol", source + admin)
                self.assertIn("2026-09-22", source + admin)
                self.assertIn("ensure_fixed_release", admin)
                self.assertIn("native_response_format", admin)
                self.assertIn("draft-", admin)
                self.assertNotIn("gpt-4.1-mini", source + admin)
                self.assertIn("agent-optimizer-overview#models", source + admin)

    def test_optimizer_changes_only_instructions_and_requires_a_real_reevaluation(self):
        for language in ("en", "ko"):
            source = self.source(language)
            with self.subTest(language=language):
                for required in ("Choose targets", "Instruction", "Max candidates", "Custom only", "View built-in evaluators"):
                    self.assertIn(required, source)
                self.assertIn("Promote", source)
                self.assertIn("version" if language == "en" else "버전", source)
                self.assertIn("0–1", source)
                self.assertIn("same" if language == "en" else "같은", source)
                self.assertIn("production" if language == "en" else "운영", source)

    def test_source_attribution_keeps_the_archived_repository_reference(self):
        for name in ("guide/verification.md", "guide/en/verification.md"):
            source = (ROOT / name).read_text()
            references = re.findall(r"^\[source-workshop\]: (\S+)", source, re.MULTILINE)
            self.assertEqual(len(references), 1)
            self.assertIn("foundry-evaluation-labs-v0.9/tree/93bc07e31373c4cfc278a2dc3757785946404cf2", references[0])

    def test_all_rendered_links_and_fragments_resolve_without_private_paths(self):
        parsed = {}
        for path in [ROOT / "index.html", *(SITE / name for name in PAGES)]:
            page = LinkParser()
            page.feed(path.read_text())
            self.assertFalse(page.duplicate_ids, (path, page.duplicate_ids))
            parsed[path.resolve()] = page
        for path, page in parsed.items():
            for href in page.links:
                with self.subTest(page=path.name, link=href):
                    url = urlsplit(href)
                    self.assertNotIn("sig=", url.query)
                    if url.scheme or url.netloc:
                        self.assertNotEqual(url.scheme, "file")
                        self.assertNotIn(url.hostname, {"localhost", "127.0.0.1", "::1"})
                        continue
                    target = (path.parent / unquote(url.path)).resolve() if url.path else path
                    self.assertTrue(target.is_relative_to(ROOT))
                    self.assertFalse(target.is_relative_to(ROOT / ".lab"))
                    self.assertTrue(target.exists())
                    if url.fragment and target in parsed:
                        self.assertIn(unquote(url.fragment), parsed[target].ids)

    def test_language_links_and_sections_are_reciprocal(self):
        english = {document.key: document for document in documents_for("en")}
        for korean in documents_for("ko"):
            en_page, ko_page = LearningPathParser(), LearningPathParser()
            en_page.feed((SITE / english[korean.key].output).read_text())
            ko_page.feed((SITE / korean.output).read_text())
            self.assertEqual(en_page.chapters, ko_page.chapters, korean.key)
            for document in (korean, english[korean.key]):
                path = SITE / document.output
                rendered = path.read_text()
                self.assertIn(f'<html lang="{document.language}">', rendered)
                links = re.findall(r'<a href="([^"]+)" lang="(en|ko)" hreflang="\2" data-language-link([^>]*)>', rendered)
                self.assertEqual(len(links), 2)
                for href, code, attributes in links:
                    target = SITE / ("ko" if code == "ko" else "") / path.name
                    self.assertEqual((path.parent / href).resolve(), target)
                    self.assertEqual('aria-current="page"' in attributes, code == document.language)

    def test_english_content_and_accessibility_text_are_actually_english(self):
        for document in documents_for("en"):
            page = ArticleTextParser()
            page.feed((SITE / document.output).read_text())
            text = "".join(page.text)
            self.assertGreater(len(text), 500)
            self.assertNotRegex(text + "".join(page.alt), r"[가-힣]", document.key)

    def test_readme_html_links_open_pages_not_github_source_views(self):
        for name in ("README.md", "README.en.md", "README.ko.md"):
            source = (ROOT / name).read_text()
            links = re.findall(r"\]\(([^)\s]+\.html[^)\s]*)\)", source)
            self.assertTrue(links, name)
            for href in links:
                self.assertTrue(href.startswith(SITE_URL), (name, href))
                self.assertTrue((ROOT / urlsplit(href.removeprefix(SITE_URL)).path).is_file(), href)
        for name in ("README.md", "README.ko.md"):
            source = (ROOT / name).read_text()
            for output in PAGES:
                if output != "english.html":
                    self.assertIn(SITE_URL + "docs/" + output, source)

    def test_actual_screenshot_provenance_dimensions_and_redactions_match(self):
        directory = ROOT / "web/assets/portal/en"
        manifest = json.loads((directory / "captures.json").read_text())
        self.assertTrue(manifest["headless_verified"])
        self.assertEqual(manifest["data_language"], "en")
        self.assertEqual(manifest["ui_language"], "en-US")
        captures = {item["file"]: item for item in manifest["screenshots"]}
        self.assertTrue({
            "15-evaluation-dataset.png", "16-evaluation-criteria.png", "17-evaluation-review.png",
            "18-evaluation-results.png", "19-evaluation-case.png", "20-evaluation-comparison.png",
            "07-optimizer-target.png", "08-optimizer-dataset.png", "09-optimizer-results.png", "10-optimizer-changes.png",
        }.issubset(captures))
        self.assertEqual(set(captures), {path.name for path in directory.glob("*.png")})
        for name, record in captures.items():
            image = (directory / name).read_bytes()
            self.assertEqual(image[:8], b"\x89PNG\r\n\x1a\n")
            self.assertEqual(struct.unpack(">II", image[16:24]), (record["width"], record["height"]))
            self.assertEqual(hashlib.sha256(image).hexdigest(), record["sha256"])
            self.assertTrue(record["redactions"])
            self.assertNotIn("?", record["route"])
        for language, prefix in (("en", ""), ("ko", "ko/")):
            count = 0
            for document in documents_for(language):
                path = SITE / document.output
                page = PortalFigureParser()
                page.feed(path.read_text())
                count += len(page.figures)
                for figure in page.figures:
                    self.assertTrue(figure["id"])
                    self.assertEqual(len(figure["images"]), 1)
                    image = figure["images"][0]
                    image_path = (path.parent / image["src"]).resolve()
                    self.assertEqual(image_path.parent, directory)
                    record = captures[image_path.name]
                    self.assertEqual((int(image["width"]), int(image["height"])), (record["width"], record["height"]))
                    self.assertGreater(len(image["alt"]), 15)
                    self.assertIn(image["src"], figure["links"])
                    self.assertGreater(len(figure["caption"]), 60)
            self.assertGreaterEqual(count, 10)
            book = PortalFigureParser()
            book.feed((SITE / prefix / "print.html").read_text())
            self.assertEqual(len(book.figures), count)
            self.assertTrue(all(figure["id"].startswith("book-") for figure in book.figures))

    def test_documented_native_add_run_command_is_parseable(self):
        for language in ("en", "ko"):
            source = self.source(language)
            blocks = re.findall(r"```(?:bash|sh)\s*\n(.*?)```", source, re.DOTALL)
            commands = [
                shlex.split(line, comments=True)
                for block in blocks for line in block.replace("\\\n", " ").splitlines()
                if "scripts/add_foundry_eval_run.py" in line
            ]
            self.assertTrue(commands, language)
            for command in commands:
                for flag in ("--endpoint", "--subscription", "--evaluation", "--baseline", "--version", "--out"):
                    self.assertIn(flag, command)
                self.assertEqual(command[command.index("--version") + 1], "2")


if __name__ == "__main__":
    unittest.main()
