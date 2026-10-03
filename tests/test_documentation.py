"""Check the published, native Foundry Evaluation and Agent Optimizer guide."""

import hashlib
from html.parser import HTMLParser
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import re
import shlex
import struct
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from urllib.parse import unquote, urlsplit

from scripts.build_guide import DOCUMENTS, SITE_URL, documents_for
from scripts.package_lab import GUIDE_FILES, package_files

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "docs"
PAGES = tuple(document.output for document in DOCUMENTS) + ("english.html", "print.html", "ko/print.html")
STEPS = ["setup", "resources", "agent", "start", "prepare", "baseline", "analyze", "optimize", "decision", "cleanup"]
SUBSTEPS = {
    "setup": ["setup-account", "setup-local", "setup-login"],
    "resources": ["resources-plan", "resources-approval", "resources-create"],
    "agent": ["agent-knowledge", "agent-create"],
    "cleanup": ["cleanup-records", "cleanup-scope", "cleanup-delete"],
}
ONBOARDING_IMAGES = {
    "23-resource-group.png", "24-select-project.png", "25-project-overview.png",
    "26-knowledge-base.png", "27-agent-configuration.png", "28-delete-review.png",
}
SHARED_IMAGES = {"21-subscription-overview.png", "22-check-access.png"}
SHARED_CAPTURES = ROOT / "web/assets/portal/shared"


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
        self.learning_frames = []
        self.step_figures = []
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
        if self.in_article and "data-learning-frame" in attrs:
            self.learning_frames.append((attrs["data-learning-frame"], self.chapters[-1] if self.chapters else None))
        if self.in_article and tag == "figure" and "portal-shot" in attrs.get("class", "").split():
            self.step_figures.append((attrs.get("id"), self.chapters[-1] if self.chapters else None))
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
            self.current = {
                "id": attrs.get("id"), "images": [], "links": [], "caption": "",
                "capture_scope": attrs.get("data-capture-scope"),
            }
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
    def __init__(self, *, target_tag="article", target_id="guide-start"):
        super().__init__(convert_charrefs=True)
        self.target_tag = target_tag
        self.target_id = target_id
        self.depth = 0
        self.in_article = False
        self.text = []
        self.alt = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == self.target_tag and attrs.get("id") == self.target_id:
            self.in_article = True
            self.depth = 1
        elif self.in_article and tag == self.target_tag:
            self.depth += 1
        if self.in_article and tag == "img":
            self.alt.append(attrs.get("alt", ""))

    def handle_endtag(self, tag):
        if self.in_article and tag == self.target_tag:
            self.depth -= 1
            if self.depth == 0:
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

    def test_both_participant_guides_have_one_complete_ten_step_path(self):
        for language, filename in (("en", "index.html"), ("ko", "ko/index.html")):
            with self.subTest(language=language):
                page = LearningPathParser()
                page.feed((SITE / filename).read_text())
                links = ["#" + step for step in STEPS]
                self.assertEqual(page.chapters, STEPS)
                self.assertEqual(page.subchapters, [item for values in SUBSTEPS.values() for item in values])
                self.assertEqual(page.toc_links, [
                    "#" + item for step in STEPS for item in [step, *SUBSTEPS.get(step, [])]
                ])
                self.assertEqual(page.overview_links, links)
                self.assertEqual(page.next_links, links[1:])
                self.assertIn('data-progress-revision="end-to-end-10"', (SITE / filename).read_text())

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
                for required in (
                    "az login", "az account show", "bootstrap plan",
                    "bootstrap preflight", "bootstrap apply", "bootstrap status",
                    "LAB_LANGUAGE", "LAB_ARTIFACTS_DIR", "iq prepare", "iq probe",
                    "native-agent --version 1", "native-agent --version 2",
                    "native-evals --name", "az group delete", "az group exists",
                    "OWNED_OBJECTS_ABSENT", "troubleshooting.md",
                ):
                    self.assertIn(required, source)
                self.assertIn("python3 -m venv", source)
                self.assertIn("py -3 -m venv", source)
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
            self.assertEqual(en_page.subchapters, ko_page.subchapters, korean.key)
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
            entry_links = [
                urlsplit(href.removeprefix(SITE_URL))
                for href in re.findall(r"\]\(([^)\s]+)\)", source)
                if href.startswith(SITE_URL)
                and urlsplit(href.removeprefix(SITE_URL)).path
                in {"", "index.html", "docs/index.html", "docs/ko/index.html"}
            ]
            self.assertGreaterEqual(len(entry_links), 2, name)
            for link in entry_links:
                self.assertEqual(link.fragment, "", (name, link.geturl()))
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
        hashes = {}
        directories = {
            "en": ROOT / "web/assets/portal/en",
            "ko": ROOT / "web/assets/portal",
            "not_applicable": SHARED_CAPTURES,
        }
        for language, directory in directories.items():
            manifest = json.loads((directory / "captures.json").read_text())
            self.assertTrue(manifest["headless_verified"])
            self.assertEqual(manifest["data_language"], language)
            self.assertEqual(manifest["ui_language"], "en-US")
            if language == "not_applicable":
                self.assertEqual(set(manifest["intended_guide_languages"]), {"en", "ko"})
                self.assertFalse(manifest["new_paid_runs_submitted"])
                self.assertFalse(manifest["cloud_configuration_changed"])
            captures = {item["file"]: item for item in manifest["screenshots"]}
            self.assertEqual(len(captures), len(manifest["screenshots"]))
            self.assertEqual(set(captures), {path.name for path in directory.glob("*.png")})
            hashes[language] = set()
            for name, record in captures.items():
                with self.subTest(language=language, capture=name):
                    image = (directory / name).read_bytes()
                    self.assertEqual(image[:8], b"\x89PNG\r\n\x1a\n")
                    self.assertEqual(struct.unpack(">II", image[16:24]), (record["width"], record["height"]))
                    digest = hashlib.sha256(image).hexdigest()
                    self.assertEqual(digest, record["sha256"])
                    hashes[language].add(digest)
                    self.assertTrue(record["redactions"])
                    self.assertNotIn("?", record["route"])
        self.assertTrue(hashes["en"].isdisjoint(hashes["ko"]))
        self.assertTrue(hashes["not_applicable"].isdisjoint(hashes["en"] | hashes["ko"]))

    def test_screenshots_use_the_document_language_in_sources_pages_and_print(self):
        required = {
            "en": {
                "00-resource-group.png", "02-model-deployments.png",
                "07-optimizer-target.png", "08-optimizer-dataset.png",
                "09-optimizer-results.png", "10-optimizer-changes.png",
                "15-evaluation-dataset.png", "16-evaluation-criteria.png", "17-evaluation-review.png",
                "18-evaluation-results.png", "19-evaluation-case.png", "20-evaluation-comparison.png",
            },
            "ko": {
                "01-project-overview.png", "02-model-deployments.png",
                "07-optimizer-target.png", "08-optimizer-dataset.png",
                "09-optimizer-results.png", "10-optimizer-changes.png", "11-evaluation-results.png",
                "15-evaluation-dataset.png", "16-evaluation-criteria.png", "17-evaluation-review.png",
                "19-evaluation-case.png", "20-evaluation-comparison.png",
            },
        }
        for images in required.values():
            images.update(ONBOARDING_IMAGES | SHARED_IMAGES)
        shared = json.loads((SHARED_CAPTURES / "captures.json").read_text())
        shared_records = {item["file"]: item for item in shared["screenshots"]}
        self.assertEqual(set(shared_records), SHARED_IMAGES)
        for language, prefix in (("en", ""), ("ko", "ko/")):
            directory = ROOT / "web/assets/portal" / ("en" if language == "en" else "")
            manifest = json.loads((directory / "captures.json").read_text())
            captures = {**shared_records, **{item["file"]: item for item in manifest["screenshots"]}}

            def inspect(path, *, full_size_links=True):
                text = path.read_text()
                links = LinkParser()
                links.feed(text)
                for value in links.links:
                    url = urlsplit(value)
                    if url.scheme or url.netloc:
                        continue
                    target = (path.parent / unquote(url.path)).resolve()
                    if target.is_relative_to(ROOT / "web/assets/portal"):
                        allowed = {directory, SHARED_CAPTURES}
                        if target.name == "captures.json":
                            allowed.update({ROOT / "web/assets/portal", ROOT / "web/assets/portal/en"})
                        self.assertIn(target.parent, allowed, (path, value))
                page = PortalFigureParser()
                page.feed(text)
                for figure in page.figures:
                    with self.subTest(language=language, document=path.relative_to(ROOT), figure=figure["id"]):
                        self.assertTrue(figure["id"])
                        self.assertEqual(len(figure["images"]), 1)
                        image = figure["images"][0]
                        image_path = (path.parent / image["src"]).resolve()
                        self.assertIn(image_path.parent, {directory, SHARED_CAPTURES})
                        if image_path.parent == SHARED_CAPTURES:
                            self.assertIn(image_path.name, SHARED_IMAGES)
                            self.assertEqual(figure["capture_scope"], "shared")
                        else:
                            self.assertNotEqual(figure["capture_scope"], "shared")
                        self.assertIn(image_path.name, captures)
                        record = captures[image_path.name]
                        self.assertEqual((int(image["width"]), int(image["height"])), (record["width"], record["height"]))
                        self.assertGreater(len(image["alt"]), 15)
                        if full_size_links:
                            self.assertIn(image["src"], figure["links"])
                        self.assertGreater(len(figure["caption"]), 60)
                return page.figures

            book_ids = set()
            used = []
            for document in documents_for(language):
                path = SITE / document.output
                source_path = ROOT / document.source
                source_figures = inspect(source_path)
                page_figures = inspect(path)
                self.assertEqual(
                    [(figure["id"], (source_path.parent / figure["images"][0]["src"]).resolve()) for figure in source_figures],
                    [(figure["id"], (path.parent / figure["images"][0]["src"]).resolve()) for figure in page_figures],
                )
                book_ids.update(f'book-{document.key}--{figure["id"]}' for figure in page_figures)
                used.extend(Path(figure["images"][0]["src"]).name for figure in page_figures)
            self.assertCountEqual(required[language], used)
            book = inspect(SITE / prefix / "print.html", full_size_links=False)
            self.assertEqual({figure["id"] for figure in book}, book_ids)
            self.assertCountEqual([Path(figure["images"][0]["src"]).name for figure in book], used)

    def test_every_step_explains_what_why_how_and_new_steps_have_real_images(self):
        expected_figures = {
            "setup": ["portal-subscription-overview", "portal-check-access"],
            "resources": ["portal-created-resources", "portal-select-project", "portal-project-endpoint"],
            "agent": ["portal-policy-connection", "portal-agent-configuration"],
            "cleanup": ["portal-delete-review"],
        }
        for language, filename in (("en", "index.html"), ("ko", "ko/index.html")):
            page = LearningPathParser()
            page.feed((SITE / filename).read_text())
            self.assertEqual(page.learning_frames, [(step, step) for step in STEPS])
            for step, identifiers in expected_figures.items():
                self.assertEqual([identifier for identifier, chapter in page.step_figures if chapter == step], identifiers)
            intro = self.source(language).split("## 01.", 1)[0]
            for term in (
                "hero-summary", "Contoso Atlas Cloud", "12", "Azure Portal", "Microsoft Foundry",
                "WHY IT MATTERS" if language == "en" else "중요한 이유",
                "model weights" if language == "en" else "모델 가중치",
            ):
                self.assertIn(term, intro)

    def test_learner_content_omits_production_history_in_web_and_print(self):
        production_notes = re.compile(
            r"Playwright|Headless|촬영|캡처|리허설|현재 실행|최신 보고서|"
            r"rehearsal|historical|during capture|capture account|masked|cropped|"
            r"latest (?:v2 )?report|current (?:run|report):",
            re.IGNORECASE,
        )
        for language in ("en", "ko"):
            book = (SITE / ("ko/print.html" if language == "ko" else "print.html")).read_text()
            for document in documents_for(language):
                figures = PortalFigureParser()
                figures.feed((SITE / document.output).read_text())
                for figure in figures.figures:
                    description = figure["caption"] + " ".join(image["alt"] for image in figure["images"])
                    self.assertNotRegex(description, production_notes, (language, document.key, figure["id"]))
                if document.key not in {"index", "data-guide"}:
                    continue
                page = ArticleTextParser()
                page.feed((SITE / document.output).read_text())
                print_section = ArticleTextParser(target_tag="section", target_id=f"book-{document.key}")
                print_section.feed(book)
                for edition, parsed in (("web", page), ("print", print_section)):
                    with self.subTest(language=language, document=document.key, edition=edition):
                        visible = "".join(parsed.text + parsed.alt)
                        self.assertGreater(len(visible), 500)
                        self.assertNotRegex(visible, production_notes)
                source = (ROOT / document.source).read_text()
                self.assertNotIn("portal-screenshots-note", source)
                self.assertNotIn("verification.md", source)

    def test_provenance_remains_in_maintainer_references_not_learner_copy(self):
        for language in ("en", "ko"):
            folder = ROOT / "guide" / ("en" if language == "en" else "")
            self.assertIn("Playwright Headless", (folder / "troubleshooting.md").read_text())
            self.assertIn("captures.json", (folder / "verification.md").read_text())

    def test_onboarding_capture_provenance_keeps_cloud_changes_and_deletion_unsubmitted(self):
        for language in ("en", "ko"):
            directory = ROOT / "web/assets/portal" / ("en" if language == "en" else "")
            text = (directory / "captures.json").read_text()
            manifest = json.loads(text)
            observation = manifest["onboarding_capture_verification"]
            self.assertTrue(observation["headless_user_agent_verified"])
            self.assertEqual(observation["language_specific_new_screenshots"], 6)
            self.assertEqual(observation["shared_administrative_screenshots"], 2)
            for count in ("resource_count", "agent_count", "agent_version_count", "evaluation_count", "evaluation_run_count"):
                self.assertEqual(observation[count + "_before"], observation[count + "_after"])
            self.assertTrue(observation["resource_ids_agent_versions_and_run_ids_unchanged"])
            for flag in (
                "new_paid_runs_submitted", "agent_save_or_chat_submitted",
                "resource_creation_or_deletion_submitted", "authentication_state_exported_to_disk",
            ):
                self.assertFalse(observation[flag])
            self.assertTrue(observation["temporary_login_browser_closed"])
            self.assertTrue(observation["authenticated_headless_context_closed"])
            captures = {item["file"]: item for item in manifest["screenshots"]}
            for filename in ONBOARDING_IMAGES:
                self.assertEqual(captures[filename]["capture_session_date"], "2026-10-03")
            deletion = captures["28-delete-review.png"]
            self.assertTrue(deletion["confirmation_empty"])
            self.assertTrue(deletion["final_delete_disabled"])
            self.assertFalse(deletion["deletion_submitted"])
            agent = captures["27-agent-configuration.png"]
            self.assertEqual(agent["agent_version"], "1")
            self.assertTrue(agent["save_disabled"])
            self.assertFalse(agent["chat_submitted"])
            self.assertNotRegex(text, r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|/Users/|Bearer |sig=")
        english = json.loads((ROOT / "web/assets/portal/en/captures.json").read_text())
        agent = next(item for item in english["screenshots"] if item["file"] == "27-agent-configuration.png")
        self.assertEqual(agent["instructions_sha256"], hashlib.sha256((ROOT / "prompts/en/baseline.txt").read_bytes()).hexdigest())

    def test_reference_format_is_attributed_without_changing_the_lab_contract(self):
        reference = "https://junwoojeong100.github.io/microsoft-foundry-labs-v1.5/index.ko.html"
        for language in ("en", "ko"):
            folder = ROOT / "guide" / ("en" if language == "en" else "")
            self.assertIn(reference, (folder / "verification.md").read_text())
            source = self.source(language)
            self.assertIn("Active", source)
            self.assertIn("Enabled", source)
            self.assertIn("Check access", source)
            self.assertIn("View my access", source)
            self.assertIn("Select a project to continue", source)
            self.assertIn("Let's go", source)

    def test_every_english_screenshot_has_a_korean_counterpart_with_the_same_anchor(self):
        english = {document.key: document for document in documents_for("en")}
        for document in documents_for("ko"):
            en_page, ko_page = PortalFigureParser(), PortalFigureParser()
            en_page.feed((ROOT / english[document.key].source).read_text())
            source = (ROOT / document.source).read_text()
            ko_page.feed(source)
            self.assertNotIn("한국어 화면 캡처 미제공", source)
            korean_ids = {figure["id"] for figure in ko_page.figures}
            self.assertEqual({figure["id"] for figure in en_page.figures}, korean_ids)
            for output, prefix in ((document.output, ""), ("ko/print.html", f"book-{document.key}--")):
                page = LinkParser()
                page.feed((SITE / output).read_text())
                self.assertTrue({prefix + anchor for anchor in korean_ids}.issubset(page.ids))

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

    def test_all_documented_lab_commands_match_the_cli_parser(self):
        from lab.cli import parser

        for language in ("en", "ko"):
            blocks = re.findall(r"```(?:bash|sh)\s*\n(.*?)```", self.source(language), re.DOTALL)
            for block in blocks:
                for line in block.replace("\\\n", " ").splitlines():
                    command = shlex.split(line, comments=True)
                    if command[:3] == ["python", "-m", "lab"]:
                        with self.subTest(language=language, command=line):
                            if "--help" in command:
                                with redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as result:
                                    parser().parse_args(command[3:])
                                self.assertEqual(result.exception.code, 0)
                            else:
                                parser().parse_args(command[3:])

    def test_documented_plans_execute_locally_and_unapproved_apply_is_blocked(self):
        replacements = {
            "YOUR_SUBSCRIPTION_ID": "00000000-0000-0000-0000-000000000001",
            "YOUR_TENANT_ID": "00000000-0000-0000-0000-000000000002",
            "YOUR_SIGN_IN_NAME": "operator@example.invalid",
        }
        for language in ("en", "ko"):
            command = next(
                line for line in self.source(language).splitlines()
                if line.startswith("python -m lab bootstrap plan ")
            )
            with self.subTest(language=language), TemporaryDirectory() as directory:
                arguments = [replacements.get(item, item) for item in shlex.split(command)[1:]]
                created = subprocess.run(
                    [sys.executable, *arguments, "--root", str(Path(directory).resolve())],
                    cwd=ROOT, capture_output=True, text=True, timeout=30,
                )
                self.assertEqual(created.returncode, 0, created.stderr)
                record = json.loads(created.stdout)
                self.assertEqual(record["plan_status"], "CREATED_LOCAL_ONLY")
                self.assertEqual(record["status"], "BLOCKED_AWAITING_APPROVAL")
                self.assertFalse(record["mutations_performed"])
                self.assertFalse(Path(record["env_path"]).exists())
                blocked = subprocess.run(
                    [sys.executable, "-m", "lab", "bootstrap", "apply", "--config", record["config_path"]],
                    cwd=ROOT, capture_output=True, text=True, timeout=30,
                )
                self.assertEqual(blocked.returncode, 2, blocked.stderr)
                refusal = json.loads(blocked.stdout)
                self.assertEqual(refusal["status"], "BLOCKED_AWAITING_APPROVAL")
                self.assertFalse(refusal["mutations_performed"])
                self.assertFalse(Path(record["env_path"]).exists())

    def test_copyable_dataset_commands_report_the_actual_count_and_hash(self):
        for language in ("en", "ko"):
            source = ROOT / ("data/en/optimizer/dev.jsonl" if language == "en" else "data/optimizer/dev.jsonl")
            command = next(
                line for line in self.source(language).splitlines()
                if line.startswith('python -c "import hashlib,pathlib;')
            )
            result = subprocess.run(
                [sys.executable, *shlex.split(command)[1:]], cwd=ROOT,
                capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.splitlines(), [
                "rows = 12", "sha256 = " + hashlib.sha256(source.read_bytes()).hexdigest(),
            ])

    def test_cleanup_is_explicit_scoped_and_not_an_unconditional_delete(self):
        for language in ("en", "ko"):
            source = self.source(language)
            cleanup = source.split("{#cleanup}", 1)[1]
            for term in (
                "az resource list", "az group show", "az group delete", "az group exists",
                "YOUR_LAB_RESOURCE_GROUP", "YOUR_SUBSCRIPTION_ID",
                "LOCAL_PLAN_ONLY", "--confirm-prefix", "false", "Locks",
                "Cost Management", "soft-delete",
            ):
                self.assertIn(term, cleanup)
            commands = re.findall(r"```bash\s*\n(.*?)```", cleanup, re.DOTALL)
            for block in commands:
                self.assertNotIn("--yes", block)
                self.assertNotIn("purge", block)
                self.assertNotIn("rm -rf", block)

    def test_issue_records_are_bilingual_packaged_and_keep_measurement_boundaries(self):
        for language in ("en", "ko"):
            document = next(item for item in documents_for(language) if item.key == "troubleshooting")
            source = (ROOT / document.source).read_text()
            for required in (
                "2026-10-03", "Unable to create data source configuration from item schema",
                "native-evals", "native-agent", "receipt", "403", "Inconclusive",
                "repair-dependencies", "repair-trace-routing",
            ):
                self.assertIn(required, source)
            self.assertIn(document.output, (ROOT / "scripts/package_lab.py").read_text())
        self.assertEqual(
            json.loads((ROOT / "evidence/latest.json").read_text())["guide_reference_date"],
            "2026-10-01",
        )


if __name__ == "__main__":
    unittest.main()
