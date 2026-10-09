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

from scripts.build_guide import DOCUMENTS, SITE_URL, SOURCE_DIRECTIVE, documents_for, implementation_source, render_markdown
from scripts.package_lab import GUIDE_FILES, package_files

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "docs"
PAGES = tuple(document.output for document in DOCUMENTS) + ("english.html",)
STEPS = ["setup", "resources", "agent", "start", "prepare", "baseline", "analyze", "optimize", "decision", "cleanup"]
SUBSTEPS = {
    "setup": ["setup-account", "setup-local", "setup-login"],
    "resources": ["resources-quickstart", "resources-plan", "resources-tpm", "resources-approval", "resources-create", "resources-runtime-check"],
    "agent": ["agent-knowledge", "agent-create", "agent-playground"],
    "start": ["dataset-check", "dataset-register"],
    "prepare": ["criteria-configure"],
    "baseline": ["baseline-submit", "baseline-results", "baseline-identifiers"],
    "analyze": ["analysis-details", "analysis-notes"],
    "optimize": ["optimizer-configure", "optimizer-results", "optimizer-candidate"],
    "decision": ["decision-agent", "decision-run", "decision-compare"],
    "cleanup": ["cleanup-records", "cleanup-scope", "cleanup-delete", "cleanup-verify"],
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
        self.completion_checks = []
        self.wizard_steps = []
        self.concept_figures = []
        self.step_routes = []
        self.execution_guides = []
        self.command_labels = 0
        self.terminal_commands = []
        self.last_heading = None
        self.active_action = None
        self.active_command = None
        self.in_article = False
        self.in_toc = False
        self.in_overview = False
        self.detail_stack = []
        self.reference_details = []
        self.reference_headings = []
        self.hidden_required_actions = []
        self.optional_anchors = set()

    def handle_starttag(self, tag, attrs):
        super().handle_starttag(tag, attrs)
        attrs = dict(attrs)
        if tag == "article" and attrs.get("id") == "guide-start":
            self.in_article = True
        if tag == "nav" and attrs.get("id") == "chapter-nav":
            self.in_toc = True
        if tag == "ol" and "learning-path" in attrs.get("class", "").split():
            self.in_overview = True
        classes = attrs.get("class", "").split()
        if tag == "details":
            self.detail_stack.append(classes)
            if "implementation-notes" in classes:
                self.reference_details.append(attrs)
        in_reference = any("implementation-notes" in entry for entry in self.detail_stack)
        in_optional = any("optional-path" in entry for entry in self.detail_stack)
        if in_optional and "id" in attrs:
            self.optional_anchors.add(attrs["id"])
        if self.in_article and tag == "h4" and attrs.get("id", "").endswith("-code-portal"):
            self.reference_headings.append((attrs["id"], in_reference))
        if self.in_article and self.detail_stack:
            if tag == "h2" or (tag == "h3" and not in_optional) or {"step-route", "completion-check", "portal-shot"} & set(classes):
                self.hidden_required_actions.append(attrs.get("id") or classes)
            if in_reference and "terminal-command" in classes:
                self.hidden_required_actions.append("terminal-command")
        if self.in_article and tag == "h2":
            self.chapters.append(attrs.get("id"))
        if self.in_article and tag == "h3":
            self.subchapters.append(attrs.get("id"))
        if self.in_article and tag in {"h2", "h3", "h4"}:
            self.last_heading = attrs.get("id")
        if self.in_article and tag == "p":
            if "step-route" in classes:
                self.active_action = {"chapter": self.chapters[-1], "links": []}
                self.step_routes.append(self.active_action)
            elif "execution-guide" in classes:
                self.active_action = {"heading": self.last_heading, "links": []}
                self.execution_guides.append(self.active_action)
            elif "command-label" in classes:
                self.command_labels += 1
        if self.in_article and tag == "pre" and "terminal-command" in classes:
            self.active_command = {"syntax": None, "text": "", "optional": in_optional}
            self.terminal_commands.append(self.active_command)
        if tag == "code" and self.active_command is not None:
            self.active_command["syntax"] = next(
                (name.removeprefix("language-") for name in classes if name.startswith("language-")),
                None,
            )
        if self.in_article and "data-learning-frame" in attrs:
            self.learning_frames.append((attrs["data-learning-frame"], self.chapters[-1] if self.chapters else None))
        if self.in_article and tag == "figure" and "portal-shot" in attrs.get("class", "").split():
            self.step_figures.append((attrs.get("id"), self.chapters[-1] if self.chapters else None))
        if self.in_article and tag == "figure" and "concept-flow" in attrs.get("class", "").split():
            self.concept_figures.append((attrs.get("id"), self.chapters[-1] if self.chapters else None))
        if self.in_article and tag == "p" and "completion-check" in attrs.get("class", "").split():
            self.completion_checks.append(self.chapters[-1] if self.chapters else None)
        if self.in_article and "data-wizard-step" in attrs:
            self.wizard_steps.append((attrs["data-wizard-step"], self.chapters[-1] if self.chapters else None))
        if self.in_article and tag == "p" and "share-checkpoint" in attrs.get("class", "").split():
            self.sharing_checkpoints.append((attrs.get("id"), self.chapters[-1] if self.chapters else None))
        if tag == "a":
            if self.active_action is not None:
                self.active_action["links"].append(attrs.get("href"))
            if self.in_toc:
                self.toc_links.append(attrs.get("href"))
            if self.in_overview:
                self.overview_links.append(attrs.get("href"))
            if self.in_article and "data-next-step" in attrs:
                self.next_links.append(attrs.get("href"))

    def handle_endtag(self, tag):
        if tag == "details":
            self.detail_stack.pop()
        if tag == "p":
            self.active_action = None
        elif tag == "pre":
            self.active_command = None
        if tag == "article":
            self.in_article = False
        elif tag == "nav":
            self.in_toc = False
        elif tag == "ol":
            self.in_overview = False

    def handle_data(self, data):
        if self.active_command is not None:
            self.active_command["text"] += data


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
    def __init__(self, *, target_tag="article", target_id="guide-start", exclude_implementation=False):
        super().__init__(convert_charrefs=True)
        self.target_tag = target_tag
        self.target_id = target_id
        self.depth = 0
        self.in_article = False
        self.text = []
        self.alt = []
        self.exclude_implementation = exclude_implementation
        self.in_implementation = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == self.target_tag and attrs.get("id") == self.target_id:
            self.in_article = True
            self.depth = 1
        elif self.in_article and tag == self.target_tag:
            self.depth += 1
        if self.in_article and tag == "img":
            self.alt.append(attrs.get("alt", ""))
        if tag == "pre" and "implementation-source" in attrs.get("class", "").split():
            self.in_implementation = True

    def handle_endtag(self, tag):
        if tag == "pre":
            self.in_implementation = False
        if self.in_article and tag == self.target_tag:
            self.depth -= 1
            if self.depth == 0:
                self.in_article = False

    def handle_data(self, data):
        if self.in_article and not (self.exclude_implementation and self.in_implementation):
            self.text.append(data)


class ImplementationParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.sources = []
        self.current = None
        self.details = []
        self.chapter = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "h2":
            self.chapter = attrs.get("id", "")
        if tag == "details" and "implementation-code" in attrs.get("class", "").split():
            self.details.append(attrs)
        if tag == "pre" and "implementation-source" in attrs.get("class", "").split():
            self.current = {"reference": attrs["data-source-reference"], "text": "", "chapter": self.chapter}

    def handle_data(self, data):
        if self.current is not None:
            self.current["text"] += data

    def handle_endtag(self, tag):
        if tag == "pre" and self.current is not None:
            self.sources.append(self.current)
            self.current = None


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

    def test_guides_do_not_publish_print_or_pdf_artifacts(self):
        self.assertFalse(list(SITE.rglob("*.pdf")))
        for name in ("print.html", "ko/print.html"):
            self.assertFalse((SITE / name).exists(), name)
        for name in PAGES:
            with self.subTest(document=name):
                page = LinkParser()
                page.feed((SITE / name).read_text())
                for link in page.links:
                    self.assertNotRegex(urlsplit(link).path, r"(?:\.pdf|(?:^|/)print\.html)$")

    def test_run_specific_verification_reports_are_not_published(self):
        for name in (
            "evidence/latest.json", "guide/verification.md", "guide/en/verification.md",
            "docs/verification.html", "docs/ko/verification.html", "prompts/en/optimized.txt",
        ):
            self.assertFalse((ROOT / name).exists(), name)
        self.assertTrue(all(document.key != "verification" for document in DOCUMENTS))
        sources = [ROOT / document.source for document in DOCUMENTS]
        sources.extend(ROOT / name for name in ("README.md", "README.en.md", "README.ko.md"))
        for source in sources:
            with self.subTest(source=source):
                text = source.read_text()
                self.assertNotIn("evidence/latest.json", text)
                self.assertNotIn("verification.md", text)
                self.assertNotRegex(text, r"\b(?:evalrun|opt)_[0-9a-f]{24,}\b")
                self.assertNotIn("onboarding_capture_verification", text)

    def test_bilingual_videos_are_separate_from_reusable_guides(self):
        for language in ("en", "ko"):
            for family in ("Foundry-Lab-Replay", "Foundry-Portal-Walkthrough"):
                with self.subTest(language=language, family=family):
                    video = ROOT / f"docs/media/{family}-{language.upper()}.mp4"
                    with video.open("rb") as stream:
                        self.assertEqual(stream.read(8)[4:], b"ftyp")
                    subtitles = video.with_suffix(".srt").read_text(encoding="utf-8")
                    self.assertGreater(len(re.findall(r"(?m)^\d+$", subtitles)), 40 if family == "Foundry-Lab-Replay" else 30)
                    if language == "ko":
                        self.assertGreater(len(re.findall("[가-힣]", subtitles)), 1000)
                    else:
                        self.assertNotRegex(subtitles, "[가-힣]")
                    for name in ("README.md", "README.ko.md"):
                        self.assertIn(video.name, (ROOT / name).read_text())
                    self.assertNotIn(video.name, self.source(language))

    def test_current_portal_navigation_is_explicit_without_execution_history(self):
        for language in ("en", "ko"):
            source = self.source(language)
            folder = ROOT / ("guide/en" if language == "en" else "guide")
            admin = (folder / "admin-setup.md").read_text(encoding="utf-8")
            for label in ("**Home**", "**Agent / Cost**", "**Optimize**"):
                self.assertIn(label, source)
            self.assertIn("Details", admin)
            self.assertIn("Tokens per Minute Rate Limit", admin)

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
                source = path.read_text(encoding="utf-8")
                if path.suffix == ".html":
                    source = re.sub(
                        r'<pre class="implementation-source"[^>]*>.*?</pre>', "",
                        source, flags=re.DOTALL,
                    )
                self.assertNotRegex(source, r"(?i)\bSFT\b|sft-appendix|sft\.html|Supervised Fine.Tuning")
        self.assertTrue(all(document.key != "sft" for document in DOCUMENTS))

    def test_tpm_requirements_and_readonly_check_are_documented_before_model_calls(self):
        for language in ("en", "ko"):
            with self.subTest(language=language):
                source = self.source(language)
                folder = ROOT / ("guide/en" if language == "en" else "guide")
                admin = (folder / "admin-setup.md").read_text()
                for term in (
                    "{#resources-tpm}", "100,000", "10,000", "TPM", "RPM",
                    "agent_tpm", "judge_tpm", "optimizer_tpm", "iq_planner_tpm", "embedding_tpm",
                    "observed", "expected", "BLOCKED", "admin-setup.md#throughput",
                ):
                    self.assertIn(term, source)
                self.assertLess(source.index("{#resources-tpm}"), source.index("smoke --run-id"))
                for term in ("{#throughput}", "rateLimits", "key: token", "100,000", "10,000"):
                    self.assertIn(term, admin)
                self.assertNotIn("GlobalStandard 20", admin)

    def test_both_participant_guides_have_one_complete_ten_step_path(self):
        for language, filename in (("en", "index.html"), ("ko", "ko/index.html")):
            with self.subTest(language=language):
                page = LearningPathParser()
                page.feed((SITE / filename).read_text())
                links = ["#" + step for step in STEPS]
                self.assertEqual(page.chapters, STEPS)
                self.assertEqual(page.subchapters, [item for values in SUBSTEPS.values() for item in values])
                self.assertEqual(page.toc_links, links)
                self.assertEqual(page.overview_links, links)
                self.assertEqual(page.next_links, links[1:])
                self.assertIn('data-progress-revision="end-to-end-10"', (SITE / filename).read_text())

    def test_learning_path_groups_the_ten_steps_into_four_phases(self):
        for filename in ("index.html", "ko/index.html"):
            with self.subTest(filename=filename):
                path = re.search(
                    r'<ol class="learning-path".*?</ol>', (SITE / filename).read_text(), re.DOTALL,
                ).group(0)
                phases = re.findall(r'<li><p class="phase-title">.*?</ul></li>', path, re.DOTALL)
                self.assertEqual(
                    [re.findall(r'href="#([^"]+)"', phase) for phase in phases],
                    [STEPS[:3], STEPS[3:7], STEPS[7:9], STEPS[9:]],
                )

    def test_all_guides_and_entry_points_are_role_neutral(self):
        role_terms = re.compile(
            r"\b(?:operator|facilitator|instructor|administrator)s?\b|강사|운영자|관리자|인수표",
            re.IGNORECASE,
        )
        for document in DOCUMENTS:
            with self.subTest(document=document.source):
                self.assertNotRegex(document.label, role_terms)
                page = ArticleTextParser(exclude_implementation=True)
                page.feed((SITE / document.output).read_text())
                self.assertIsNone(role_terms.search(" ".join(page.text + page.alt)))
        for filename, language in (
            ("README.md", "en"), ("README.en.md", "en"), ("README.ko.md", "ko"),
            ("infra/README.md", "en"),
        ):
            with self.subTest(document=filename):
                page = ArticleTextParser()
                page.feed(
                    '<article id="guide-start">'
                    + render_markdown((ROOT / filename).read_text(), language=language).content
                    + "</article>"
                )
                self.assertIsNone(role_terms.search(" ".join(page.text + page.alt)))

    def test_self_service_path_keeps_setup_records_and_all_execution_steps(self):
        for language in ("en", "ko"):
            source = self.source(language)
            environment = "lab-" + language
            with self.subTest(language=language):
                intro = source.split("## 01.", 1)[0]
                self.assertIn(
                    "Every participant completes" if language == "en" else "모든 실습 참여자가",
                    intro,
                )
                provisioning = source.split("{#resources}", 1)[1].split("## 03.", 1)[0]
                self.assertIn(f".lab/{environment}/notes.md", provisioning)
                self.assertIn("admin-setup.md#handoff", provisioning)
                for command in (
                    "bootstrap plan", "bootstrap preflight", "bootstrap apply", "bootstrap status",
                    "iq prepare", "iq probe", "native-agent --version 1",
                    "native-evals --name", "native-agent --version 2",
                    "scripts/add_foundry_eval_run.py", "az group delete", "az group exists",
                ):
                    self.assertIn(command, source)
                criteria = source.split("{#prepare}", 1)[1].split("## 06.", 1)[0]
                self.assertIn("unsubmitted" if language == "en" else "아직 제출하지 않은", criteria)
                self.assertIn("06", criteria)
                cleanup = source.split("{#cleanup}", 1)[1]
                self.assertIn("default path" if language == "en" else "기본 경로", cleanup)
                self.assertIn("separate option" if language == "en" else "별도 선택 사항", cleanup)

    def test_setup_reference_documents_participant_authorization_and_registration(self):
        for language in ("en", "ko"):
            folder = ROOT / "guide" / ("en" if language == "en" else "")
            source = (folder / "admin-setup.md").read_text()
            with self.subTest(language=language):
                for term in (
                    "expected_user", "approved_by", "Microsoft.Authorization/roleAssignments/write",
                    "/register/action", "**Register**", "Microsoft.CognitiveServices",
                    "Microsoft.Search", "Microsoft.OperationalInsights", "Microsoft.Insights",
                ):
                    self.assertIn(term, source)
                self.assertIn(
                    "digital signature" if language == "en" else "전자서명",
                    source,
                )
                self.assertIn(
                    "not run" if language == "en" else "미실행",
                    source,
                )
                self.assertIn("{#operator-guide}", source)
                self.assertIn("{#handoff}", source)
                self.assertIn("{#facilitator-guide}", (folder / "facilitator.md").read_text())

    def test_optimizer_requires_complete_instructions_and_documents_safe_waits(self):
        for language in ("en", "ko"):
            folder = ROOT / "guide" / ("en" if language == "en" else "")
            source = self.source(language)
            troubleshooting = (folder / "troubleshooting.md").read_text()
            with self.subTest(language=language):
                for term in ("Compare across models", "Token usage", "--wait-seconds", "result_counts.total: 12"):
                    self.assertIn(term, source)
                self.assertIn("candidate.txt.txt", source)
                self.assertIn(
                    "complete instructions unavailable" if language == "en" else "전체 지침 확인 불가",
                    troubleshooting,
                )
                self.assertIn(
                    "Stopping your wait does not cancel" if language == "en" else "기다림을 중단해도",
                    source,
                )

    def test_implementation_panels_show_exact_current_source_in_both_languages(self):
        references = None
        for language, prefix in (("en", ""), ("ko", "ko/")):
            expected = [
                match.group(1) for line in self.source(language).splitlines()
                if (match := SOURCE_DIRECTIVE.fullmatch(line))
            ]
            self.assertGreaterEqual(len(expected), 20)
            if references is None:
                references = expected
            self.assertEqual(expected, references)
            with self.subTest(language=language):
                page = ImplementationParser()
                page.feed((SITE / prefix / "index.html").read_text())
                self.assertEqual([item["reference"] for item in page.sources], expected)
                self.assertTrue(all("open" not in detail for detail in page.details))
                for item in page.sources:
                    self.assertEqual(item["text"], implementation_source(item["reference"])[1])
                self.assertNotIn("<!-- source-code:", (SITE / prefix / "index.html").read_text())

    def test_every_stage_maps_code_or_portal_only_actions_without_replacing_commands(self):
        anchors = (
            "setup", "resources", "runtime", "sdk", "knowledge", "agent", "dataset", "criteria",
            "baseline", "analysis", "optimizer", "decision", "cleanup",
        )
        for language, prefix in (("en", ""), ("ko", "ko/")):
            source = self.source(language)
            for anchor in anchors:
                self.assertIn("{#" + anchor + "-code-portal}", source)
                self.assertIn(f'id="{anchor}-code-portal"', (SITE / prefix / "index.html").read_text())
            optimizer = source.split("{#optimizer-code-portal}", 1)[1].split("## 09.", 1)[0]
            self.assertIn(
                "No local program submits" if language == "en" else "로컬 프로그램이 최적화 작업을 제출하는 단계가 아닙니다",
                optimizer,
            )
            baseline = source.split("{#baseline-code-portal}", 1)[1].split("## 07.", 1)[0]
            self.assertIn("list", baseline)
            self.assertIn("create", baseline)
            self.assertNotRegex(source, r"python\s+examples/|examples/.*\.py")

    def test_optional_explanations_do_not_hide_the_required_participant_path(self):
        for filename in ("index.html", "ko/index.html"):
            with self.subTest(filename=filename):
                page = LearningPathParser()
                page.feed((SITE / filename).read_text())
                self.assertEqual(len(page.reference_details), 13)
                self.assertTrue(all("open" not in attrs for attrs in page.reference_details))
                self.assertEqual(
                    [anchor for anchor, in_reference in page.reference_headings if in_reference],
                    [guide["heading"] for guide in page.execution_guides],
                )
                self.assertEqual(page.hidden_required_actions, [])
                self.assertEqual(page.detail_stack, [])

    def test_comparison_worksheet_keeps_three_columns_without_a_markup_row(self):
        for filename in ("index.html", "ko/index.html"):
            with self.subTest(filename=filename):
                rendered = (SITE / filename).read_text()
                table = re.search(
                    r'<div class="worked-comparison">\s*(<table>.*?</table>)\s*</div>',
                    rendered, re.DOTALL,
                )
                self.assertIsNotNone(table)
                self.assertEqual(table.group(1).count("<th>"), 3)
                self.assertEqual(table.group(1).count("<tr>"), 7)
                self.assertNotIn("{: .worked-comparison}", rendered)

    def test_default_setup_path_uses_codespaces_and_one_guided_creation_command(self):
        for language, filename in (("en", "index.html"), ("ko", "ko/index.html")):
            with self.subTest(language=language):
                page = LearningPathParser()
                page.feed((SITE / filename).read_text())
                for anchor in ("setup-codespaces", "resources-quickstart", "resources-notes", "resources-runtime-check"):
                    self.assertIn(anchor, page.ids)
                    self.assertNotIn(anchor, page.optional_anchors)
                for anchor in ("setup-local-install", "setup-windows", "resources-plan", "resources-approval", "resources-create"):
                    self.assertIn(anchor, page.optional_anchors)
                commands = "".join(command["text"] for command in page.terminal_commands if not command["optional"])
                self.assertIn(f"python -m lab bootstrap setup --environment lab-{language}\n", commands)
                self.assertIn("az login --use-device-code\n", commands)
                for manual in ("bootstrap plan", "bootstrap apply", "pip install", "git clone"):
                    self.assertNotIn(manual, commands)
                source = self.source(language)
                for anchor in ("dataset-download", "optimizer-candidate", "cleanup-codespaces"):
                    self.assertIn(anchor, page.ids)
                self.assertIn(f"python -m zipfile -c .lab/lab-{language}-records.zip .lab/lab-{language}", source)
                self.assertIn("troubleshooting.md#codespaces", source)
                self.assertIn(f"CREATE lab-{language}", source)

    def test_codespaces_lifecycle_prepares_dependencies_without_cloud_actions(self):
        configuration = json.loads((ROOT / ".devcontainer/devcontainer.json").read_text())
        command = configuration["postCreateCommand"]
        syntax = subprocess.run(["bash", "-n"], input=command, text=True, capture_output=True, check=False)
        self.assertEqual(syntax.returncode, 0, syntax.stderr)
        self.assertIn("-m venv .venv", command)
        self.assertIn(".venv/bin/python -m pip install -r requirements.lock", command)
        hooks = "\n".join(str(value) for key, value in configuration.items() if key.endswith("Command"))
        self.assertNotRegex(hooks, r"\baz\s+|bootstrap|--confirm|AZURE_CLIENT_SECRET|access.token")
        self.assertIn(".devcontainer/devcontainer.json", {path.relative_to(ROOT).as_posix() for path in package_files(ROOT)})

    def test_learner_prose_uses_full_product_names_except_exact_ui_and_roles(self):
        short_name = re.compile(r"(?<!Microsoft )(?<!New )(?<![A-Za-z0-9_])(?:Azure|Foundry)(?![A-Za-z0-9_/-])")
        role_name = re.compile(r"(?:Foundry|Azure AI) (?:Account Owner|Project Manager|User|Owner)(?![A-Za-z0-9_])")
        for filename in ("index.html", "docs/english.html"):
            self.assertIn("<title>Microsoft Foundry Lab Guide", (ROOT / filename).read_text())
        for document in DOCUMENTS:
            with self.subTest(document=document.output):
                page = ArticleTextParser(exclude_implementation=True)
                page.feed((SITE / document.output).read_text())
                prose = role_name.sub("", " ".join(page.text + page.alt))
                matches = [prose[max(0, match.start() - 25):match.end() + 45] for match in short_name.finditer(prose)]
                self.assertEqual(matches, [])
                self.assertNotIn("Microsoft Microsoft", prose)

    def test_all_steps_and_code_portal_sections_link_to_actual_actions(self):
        mappings = (
            "setup", "resources", "runtime", "sdk", "knowledge", "agent", "dataset", "criteria",
            "baseline", "analysis", "optimizer", "decision", "cleanup",
        )
        for language, filename in (("en", "index.html"), ("ko", "ko/index.html")):
            with self.subTest(language=language):
                page = LearningPathParser()
                page.feed((SITE / filename).read_text())
                self.assertEqual([route["chapter"] for route in page.step_routes], STEPS)
                self.assertEqual(
                    [guide["heading"] for guide in page.execution_guides],
                    [name + "-code-portal" for name in mappings],
                )
                for action in page.step_routes + page.execution_guides:
                    self.assertTrue(action["links"])
                    for href in action["links"]:
                        self.assertTrue(href.startswith("#"), href)
                        self.assertIn(href.removeprefix("#"), page.ids)
                actions = {guide["heading"]: guide["links"] for guide in page.execution_guides}
                self.assertEqual(actions["setup-code-portal"], ["#setup-login", "#setup-language"])
                self.assertEqual(actions["runtime-code-portal"], ["#resources-preflight"])
                self.assertEqual(actions["sdk-code-portal"], ["#agent-smoke"])

    def test_authentication_guidance_matches_the_step_that_actually_uses_it(self):
        expected = {
            "lab/preflight.py:check_identity": "resources",
            "lab/auth.py:credential_for": "agent",
        }
        for language, prefix in (("en", ""), ("ko", "ko/")):
            source = self.source(language)
            setup = source.split("## 01.", 1)[1].split("## 02.", 1)[0]
            resources = source.split("## 02.", 1)[1].split("## 03.", 1)[0]
            agent = source.split("## 03.", 1)[1].split("## 04.", 1)[0]
            with self.subTest(language=language):
                for term in ("check_identity", "credential_for", "AzureCliCredential", ".env"):
                    self.assertNotIn(term, setup)
                for term in ("az login", "az account set", "az account show", "--environment", "--config"):
                    self.assertIn(term, setup)
                self.assertIn("EXPECTED_AZURE_USER", resources)
                self.assertIn("<!-- source-code: lab/preflight.py:check_identity -->", resources)
                self.assertNotIn("<!-- source-code: lab/auth.py:credential_for -->", resources)
                self.assertIn("<!-- source-code: lab/auth.py:credential_for -->", agent)
                page = ImplementationParser()
                page.feed((SITE / prefix / "index.html").read_text())
                self.assertFalse(any(item["chapter"] == "setup" for item in page.sources))
                for reference, chapter in expected.items():
                    matches = [item for item in page.sources if item["reference"] == reference]
                    self.assertEqual(len(matches), 1, (language, reference))
                    self.assertEqual(matches[0]["chapter"], chapter)

    def test_every_terminal_block_is_labeled_without_javascript_and_keeps_original_commands(self):
        for document in DOCUMENTS:
            with self.subTest(source=document.source):
                source = (ROOT / document.source).read_text()
                expected = re.findall(r"```(sh|bash|powershell)\n(.*?)```", source, re.DOTALL)
                page = LearningPathParser()
                page.feed((SITE / document.output).read_text())
                self.assertEqual(
                    [(command["syntax"], command["text"]) for command in page.terminal_commands],
                    expected,
                )
                self.assertEqual(page.command_labels, len(expected))

    def test_optimizer_next_actions_include_the_no_candidate_cleanup_branch(self):
        for language in ("en", "ko"):
            with self.subTest(language=language):
                optimizer = self.source(language).split("{#optimize}", 1)[1].split("## 09.", 1)[0]
                self.assertRegex(
                    optimizer,
                    r'<p class="step-next no-print"><a href="#decision" data-next-step>[^<]+</a> '
                    r'<a href="#cleanup">[^<]+</a></p>',
                )

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
                    "bootstrap setup", "--config", "iq prepare", "iq probe",
                    "native-agent --version 1", "native-agent --version 2",
                    "native-evals --name", "az group delete", "az group exists",
                    "OWNED_OBJECTS_ABSENT", "troubleshooting.md",
                ):
                    self.assertIn(required, source)
                self.assertIn("python3 -m venv", source)
                self.assertIn("python3.13 -m venv", source)
                self.assertIn("py -3.13 -m venv", source)
                self.assertIn("add_foundry_eval_run.py", source)
                self.assertIn("{{item.query}}", source)
                self.assertIn("--baseline", source)
                self.assertIn("--version", source)

    def test_beginner_landmarks_and_completion_checks_survive_web_build(self):
        for language, prefix in (("en", ""), ("ko", "ko/")):
            with self.subTest(language=language):
                page = LearningPathParser()
                rendered = (SITE / prefix / "index.html").read_text()
                page.feed(rendered)
                self.assertIn("basics", page.ids)
                self.assertEqual(page.completion_checks, STEPS)
                self.assertEqual(page.wizard_steps, [
                    ("1", "start"), ("2", "prepare"), ("3", "baseline"),
                ])
                self.assertEqual(page.concept_figures, [
                    ("resource-map", "resources"), ("evaluation-flow", "start"),
                ])
                self.assertNotIn("{: .completion-check}", rendered)

    def test_tool_installation_and_verification_precede_download_and_venv(self):
        anchors = (
            "setup-windows", "setup-macos", "setup-linux",
            "setup-verify", "setup-download", "setup-venv", "setup-login",
        )
        commands = (
            "winget install --exact --id Python.Python.3.13 --source winget",
            "winget install --exact --id Git.Git --source winget",
            "winget install --exact --id Microsoft.AzureCLI --source winget",
            "brew install python@3.13 git azure-cli",
            "sudo apt install python3 python3-venv python3-pip git curl",
            "curl -fsSL 'https://azurecliprod.blob.core.windows.net/$root/deb_install.sh' -o install-azure-cli.sh",
            "sudo bash install-azure-cli.sh",
            "py -3.13 --version", "python3.13 --version", "python3 --version",
            "git --version", "az version",
            "py -3.13 -m venv .venv", "python3.13 -m venv .venv", "python3 -m venv .venv",
        )
        links = (
            "https://www.python.org/downloads/windows/",
            "https://git-scm.com/install/windows",
            "https://learn.microsoft.com/cli/azure/install-azure-cli-windows?pivots=msi",
            "https://brew.sh/",
            "https://learn.microsoft.com/cli/azure/install-azure-cli-macos",
            "https://learn.microsoft.com/cli/azure/install-azure-cli-linux?pivots=apt",
        )
        for language, prefix in (("en", ""), ("ko", "ko/")):
            with self.subTest(language=language):
                source = self.source(language)
                positions = [source.index("{#" + anchor + "}") for anchor in anchors]
                self.assertEqual(positions, sorted(positions))
                for command in commands:
                    self.assertIn(command, source)
                for link in links:
                    self.assertIn(link, source)
                for term in (
                    "3.11–3.14", "Ubuntu 24.04 LTS", "Add python.exe to PATH",
                    "Python Launcher", "Next steps", "command not found",
                    "not recognized", "troubleshooting.md#environment",
                ):
                    self.assertIn(term, source)
                checks = source.split("{#setup-verify}", 1)[1].split("#### ", 1)[0]
                for python in ("py -3.13", "python3.13", "python3"):
                    self.assertIn(f"{python} --version\ngit --version\naz version", checks)
                self.assertNotIn("az login", checks)
                venv = source.split("{#setup-venv}", 1)[1].split("### ", 1)[0]
                self.assertLess(venv.index("python -m pip --version"), venv.index("python -m pip install"))
                text = (SITE / prefix / "index.html").read_text()
                for anchor in anchors:
                    self.assertIn(f'id="{anchor}"', text)
                article = ArticleTextParser()
                article.feed(text)
                visible = "".join(article.text)
                for command in commands:
                    self.assertIn(command, visible)

    def test_setup_references_cover_all_three_tools_and_link_to_verification(self):
        for language in ("en", "ko"):
            folder = ROOT / "guide" / ("en" if language == "en" else "")
            for name in ("admin-setup.md", "facilitator.md", "troubleshooting.md"):
                with self.subTest(language=language, document=name):
                    source = (folder / name).read_text()
                    self.assertIn("3.11–3.14", source)
                    self.assertIn("Git", source)
                    self.assertIn("Azure CLI", source)
                    self.assertIn("handbook.md#setup-verify", source)
        for name in ("README.md", "README.en.md", "README.ko.md"):
            with self.subTest(document=name):
                source = (ROOT / name).read_text()
                for term in ("3.11–3.14", "Git", "Azure CLI", "index.html#setup-local"):
                    self.assertIn(term, source)

    def test_shared_commands_are_distinguished_from_os_specific_setup(self):
        for language in ("en", "ko"):
            with self.subTest(language=language):
                blocks = re.findall(r"```(bash|sh|powershell)\s*\n(.*?)```", self.source(language), re.DOTALL)
                bash = "\n".join(text for syntax, text in blocks if syntax == "bash")
                powershell = "\n".join(text for syntax, text in blocks if syntax == "powershell")
                shared = "\n".join(text for syntax, text in blocks if syntax == "sh")
                for command in (
                    "brew install", "sudo apt install", "python3.13 --version", "python3 --version",
                    "python3.13 -m venv", "python3 -m venv", "source .venv/bin/activate",
                ):
                    self.assertIn(command, bash)
                    self.assertNotIn(command, shared + powershell)
                for command in (
                    "winget install", "py -3.13 --version", "py -3.13 -m venv",
                    ".venv\\Scripts\\Activate.ps1",
                ):
                    self.assertIn(command, powershell)
                    self.assertNotIn(command, shared + bash)
                for command in ("az login", "bootstrap plan", "native-agent --version 1", "native-evals", "add_foundry_eval_run.py", "az group delete"):
                    self.assertIn(command, shared)
                self.assertNotIn("source .venv", shared)
                self.assertNotIn("$env:", shared)

    def test_setup_and_resume_do_not_require_language_or_record_folder_exports(self):
        for language in ("en", "ko"):
            with self.subTest(language=language):
                source = self.source(language)
                commands = "\n".join(re.findall(r"```(?:sh|bash|powershell)\n(.*?)```", source, re.DOTALL))
                self.assertNotIn("LAB_LANGUAGE", commands)
                self.assertNotIn("LAB_ARTIFACTS_DIR", commands)
                setup = source.split("{#setup-language}", 1)[1].split("<details", 1)[0]
                self.assertNotIn("```", setup)
                self.assertIn(f"--environment lab-{language}", setup)
                self.assertIn("--config", setup)
                self.assertIn("automatically" if language == "en" else "자동", setup)
                self.assertIn(f"python -m lab bootstrap setup --environment lab-{language}\n", commands)
                self.assertIn(f"python -m lab --config .lab/lab-{language}/.env preflight", commands)

    def test_advanced_mapping_checks_have_a_linked_operator_home(self):
        for language in ("en", "ko"):
            folder = ROOT / "guide" / ("en" if language == "en" else "")
            source = self.source(language)
            admin = (folder / "admin-setup.md").read_text()
            with self.subTest(language=language):
                self.assertIn("admin-setup.md#evaluation-mapping", source)
                self.assertIn("{#evaluation-mapping}", admin)
                admin_page = SITE / ("ko/admin.html" if language == "ko" else "admin.html")
                self.assertIn('class="print-with-table"', admin_page.read_text())
                self.assertIn("response={{sample.output_text}}", admin)
                self.assertIn("response={{sample.output_items}}", admin)
                self.assertIn("{{item.query}}", source)
                self.assertIn("candidate.txt.txt", source)
                self.assertIn("handbook.md#basics", (folder / "facilitator.md").read_text())
                self.assertIn("handbook.md#evaluation-flow", (folder / "facilitator.md").read_text())

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
        source = (ROOT / "web/assets/NOTICE.txt").read_text()
        reference = "https://github.com/junwoojeong100/foundry-evaluation-labs-v0.9/tree/93bc07e31373c4cfc278a2dc3757785946404cf2"
        self.assertEqual(source.count(reference), 1)

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

    def test_all_markdown_document_links_and_fragments_resolve(self):
        paths = sorted(ROOT.glob("*.md")) + [
            *sorted((ROOT / "guide").rglob("*.md")),
            *sorted((ROOT / "data").rglob("*.md")),
            ROOT / "infra/README.md",
        ]
        parsed = {}
        for path in paths:
            page = LinkParser()
            directory = path.parent.relative_to(ROOT).as_posix()
            page.feed(render_markdown(
                path.read_text(), relative_base=directory, output_base=directory,
            ).content)
            parsed[path.resolve()] = page
        for path, page in parsed.items():
            for href in page.links:
                with self.subTest(page=path.relative_to(ROOT), link=href):
                    url = urlsplit(href)
                    if url.scheme or url.netloc:
                        continue
                    target = (path.parent / unquote(url.path)).resolve() if url.path else path
                    self.assertTrue(target.is_relative_to(ROOT))
                    self.assertTrue(target.exists(), f"{path.relative_to(ROOT)} links to missing {href}")
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
            page = ArticleTextParser(exclude_implementation=True)
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
            self.assertGreaterEqual(sum(not link.fragment for link in entry_links), 2, name)
            links = re.findall(r"\]\(([^)\s]+\.html[^)\s]*)\)", source)
            self.assertTrue(links, name)
            for href in links:
                if href == "https://junwoojeong100.github.io/microsoft-foundry-labs-v1.5/index.ko.html":
                    self.assertIn(href, (ROOT / "web/assets/NOTICE.txt").read_text())
                    continue
                self.assertTrue(href.startswith(SITE_URL), (name, href))
                link = urlsplit(href.removeprefix(SITE_URL))
                target = ROOT / link.path
                self.assertTrue(target.is_file(), href)
                if link.fragment:
                    page = LinkParser()
                    page.feed(target.read_text())
                    self.assertIn(unquote(link.fragment), page.ids, href)
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
            self.assertIn("playwright", manifest["tool"].lower())
            self.assertEqual(manifest["data_language"], language)
            self.assertEqual(manifest["ui_language"], "en-US")
            if language == "not_applicable":
                self.assertEqual(set(manifest["intended_guide_languages"]), {"en", "ko"})
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

    def test_screenshots_use_the_document_language_in_sources_and_pages(self):
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
        for language in ("en", "ko"):
            directory = ROOT / "web/assets/portal" / ("en" if language == "en" else "")
            manifest = json.loads((directory / "captures.json").read_text())
            captures = {**shared_records, **{item["file"]: item for item in manifest["screenshots"]}}

            def inspect(path):
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
                        self.assertIn(image["src"], figure["links"])
                        self.assertGreater(len(figure["caption"]), 60)
                return page.figures

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
                used.extend(Path(figure["images"][0]["src"]).name for figure in page_figures)
            self.assertCountEqual(required[language], used)

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

    def test_learner_content_omits_production_history(self):
        production_notes = re.compile(
            r"Playwright|Headless|촬영|캡처|리허설|현재 실행|최신 보고서|"
            r"rehearsal|historical|during capture|capture account|masked|cropped|"
            r"latest (?:v2 )?report|current (?:run|report):",
            re.IGNORECASE,
        )
        for language in ("en", "ko"):
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
                with self.subTest(language=language, document=document.key):
                    visible = "".join(page.text + page.alt)
                    self.assertGreater(len(visible), 500)
                    self.assertNotRegex(visible, production_notes)
                source = (ROOT / document.source).read_text()
                self.assertNotIn("portal-screenshots-note", source)
                self.assertNotIn("verification.md", source)

    def test_provenance_remains_in_maintainer_references_not_learner_copy(self):
        notice = (ROOT / "web/assets/NOTICE.txt").read_text()
        self.assertIn("Playwright Headless", notice)
        self.assertIn("captures.json", notice)
        for language in ("en", "ko"):
            folder = ROOT / "guide" / ("en" if language == "en" else "")
            self.assertNotIn("Playwright Headless", (folder / "troubleshooting.md").read_text())
            self.assertFalse((folder / "verification.md").exists())

    def test_capture_manifests_keep_asset_provenance_without_old_validation_history(self):
        for language in ("en", "ko"):
            directory = ROOT / "web/assets/portal" / ("en" if language == "en" else "")
            text = (directory / "captures.json").read_text()
            manifest = json.loads(text)
            self.assertNotIn("onboarding_capture_verification", manifest)
            self.assertNotIn("additional_capture_verification", manifest)
            self.assertNotIn("new_paid_runs_submitted", manifest)
            self.assertNotIn("cloud_configuration_changed", manifest)
            captures = {item["file"]: item for item in manifest["screenshots"]}
            for filename in ONBOARDING_IMAGES:
                self.assertIn(filename, captures)
                self.assertTrue(captures[filename]["capture_session_date"])
                self.assertNotIn("instructions_sha256", captures[filename])
            self.assertNotRegex(text, r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|/Users/|Bearer |sig=")

    def test_reference_format_is_attributed_without_changing_the_lab_contract(self):
        reference = "https://junwoojeong100.github.io/microsoft-foundry-labs-v1.5/index.ko.html"
        self.assertIn(reference, (ROOT / "web/assets/NOTICE.txt").read_text())
        for language in ("en", "ko"):
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
            page = LinkParser()
            page.feed((SITE / document.output).read_text())
            self.assertTrue(korean_ids.issubset(page.ids))

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
                for flag in ("--config", "--evaluation", "--baseline", "--version"):
                    self.assertIn(flag, command)
                self.assertNotIn("--endpoint", command)
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
            commands = re.findall(r"```(?:bash|sh)\s*\n(.*?)```", cleanup, re.DOTALL)
            self.assertTrue(commands)
            for block in commands:
                self.assertNotIn("--yes", block)
                self.assertNotIn("purge", block)
                self.assertNotIn("rm -rf", block)

    def test_troubleshooting_is_bilingual_packaged_and_not_a_validation_log(self):
        for language in ("en", "ko"):
            document = next(item for item in documents_for(language) if item.key == "troubleshooting")
            source = (ROOT / document.source).read_text()
            for required in (
                "Unable to create data source configuration from item schema",
                "native-evals", "native-agent", "receipt", "403", "Inconclusive",
                "repair-dependencies", "repair-trace-routing",
            ):
                self.assertIn(required, source)
            self.assertIn(document.output, (ROOT / "scripts/package_lab.py").read_text())
            self.assertNotRegex(source, r"\{#(?:verification|beginner-review|portal-captures)\}")

    def test_retention_and_shared_monitoring_are_explicit_in_both_guides(self):
        for language in ("en", "ko"):
            source = self.source(language)
            self.assertIn("Smart Detection", source)
            self.assertIn("LOCAL_PLAN_ONLY", source)
            self.assertIn("approved for retention" if language == "en" else "보존 승인", source)


if __name__ == "__main__":
    unittest.main()
