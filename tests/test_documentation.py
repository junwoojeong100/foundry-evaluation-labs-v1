import contextlib
import hashlib
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import re
import shlex
import struct
import unittest
from urllib.parse import unquote, urlsplit

from lab.cli import parser as lab_parser
from lab.sft import parser as sft_parser


ROOT = Path(__file__).resolve().parents[1]
PAGES = ("index.html", "facilitator.html", "admin.html", "sft.html", "verification.html", "data-guide.html", "english.html", "print.html")


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


class OutputExampleParser(LearningPathParser):
    def __init__(self):
        super().__init__()
        self.examples = {}
        self.chapter = None
        self.pending = None
        self.current = None

    def handle_starttag(self, tag, attrs):
        super().handle_starttag(tag, attrs)
        attrs = dict(attrs)
        if self.in_article and tag == "h2":
            self.chapter = attrs["id"]
        if self.in_article and tag == "p" and "output-label" in attrs.get("class", "").split():
            self.pending = attrs["id"]
        if tag == "pre" and self.pending:
            self.current = {"chapter": self.chapter, "language": "", "text": ""}
        if tag == "code" and self.current is not None:
            self.current["language"] = attrs.get("class", "").removeprefix("language-")

    def handle_data(self, data):
        if self.current is not None:
            self.current["text"] += data

    def handle_endtag(self, tag):
        if tag == "pre" and self.current is not None:
            self.examples[self.pending] = self.current
            self.current = None
            self.pending = None
        super().handle_endtag(tag)


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


class DocumentationTests(unittest.TestCase):
    def test_only_the_latest_verification_and_current_guides_are_retained(self):
        evidence = ROOT / "evidence"
        self.assertEqual(
            {path.relative_to(evidence).as_posix() for path in evidence.rglob("*") if path.is_file()},
            {"latest.json"},
        )
        latest = json.loads((evidence / "latest.json").read_text(encoding="utf-8"))
        self.assertEqual(latest["schema_version"], 1)
        for name in ("README.md", "README.en.md"):
            self.assertIn("evidence/latest.json", (ROOT / name).read_text(encoding="utf-8"))
        self.assertFalse((ROOT / "guide/integration-migration.md").exists())
        self.assertFalse((ROOT / "migration.html").exists())

    def test_pages_entry_uses_the_public_static_project_site(self):
        url = "https://junwoojeong100.github.io/foundry-evaluation-labs-v1/"
        self.assertTrue((ROOT / ".nojekyll").is_file())
        for name in ("README.md", "README.en.md"):
            source = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn(f"{url}#start", source)
            self.assertIn(".nojekyll", source)
            self.assertIn("`main`", source)
        from scripts.package_lab import package_files

        self.assertIn(ROOT / ".nojekyll", package_files(ROOT))

    def test_each_participant_step_explains_the_feature_purpose_and_usage(self):
        source = (ROOT / "guide/handbook.md").read_text(encoding="utf-8")
        steps = re.split(r"^## ", source, flags=re.MULTILINE)[1:]
        self.assertEqual(len(steps), 6)
        for step in steps:
            with self.subTest(step=step.splitlines()[0]):
                introduction = step.split("**할 일:**", 1)[0]
                self.assertIn('class="lab-concept"', introduction)
                for label in ("경험할 기능:", "왜 중요한가:", "어떻게 경험하나:"):
                    self.assertIn(label, introduction)

    def test_each_instruction_block_has_a_command_explanation(self):
        for name in ("handbook.md", "admin-setup.md", "facilitator.md", "sft-appendix.md"):
            source = (ROOT / "guide" / name).read_text(encoding="utf-8")
            blocks = list(re.finditer(r"```bash\s*\n(.*?)```", source, flags=re.DOTALL))
            self.assertTrue(blocks, name)
            for index, block in enumerate(blocks):
                end = blocks[index + 1].start() if index + 1 < len(blocks) else len(source)
                with self.subTest(document=name, command=block.group(1).splitlines()[0]):
                    self.assertIn("**명령 해설:**", source[block.end():end])

    def test_portal_media_is_captioned_local_and_matches_capture_provenance(self):
        directory = ROOT / "web/assets/portal"
        manifest = json.loads((directory / "captures.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["portal_origin"], "https://ai.azure.com")
        self.assertEqual(manifest["captured_date"], "2026-09-30")
        self.assertTrue(manifest["headless_verified"])
        self.assertFalse(manifest["new_paid_runs_submitted"])
        self.assertFalse(manifest["cloud_configuration_changed"])
        captures = {item["file"]: item for item in manifest["screenshots"]}
        self.assertEqual(len(captures), 14)
        self.assertEqual(set(captures), {path.name for path in directory.glob("*.png")})
        for filename, record in captures.items():
            with self.subTest(screenshot=filename):
                data = (directory / filename).read_bytes()
                self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
                self.assertEqual(struct.unpack(">II", data[16:24]), (record["width"], record["height"]))
                self.assertEqual(hashlib.sha256(data).hexdigest(), record["sha256"])
                self.assertTrue(record["redactions"])
                self.assertNotIn("?", record["route"])

        figures = []
        for name in ("index.html", "sft.html"):
            page = PortalFigureParser()
            page.feed((ROOT / name).read_text(encoding="utf-8"))
            self.assertEqual(len(page.figures), 13 if name == "index.html" else 1)
            figures.extend(page.figures)
        self.assertEqual(len({figure["id"] for figure in figures}), 14)
        self.assertEqual({Path(figure["images"][0]["src"]).name for figure in figures}, set(captures))
        for figure in figures:
            with self.subTest(figure=figure["id"]):
                self.assertEqual(len(figure["images"]), 1)
                image = figure["images"][0]
                record = captures[Path(image["src"]).name]
                self.assertTrue(image["src"].startswith("web/assets/portal/"))
                self.assertGreater(len(image["alt"]), 20)
                self.assertEqual((int(image["width"]), int(image["height"])), (record["width"], record["height"]))
                self.assertIn(image["src"], figure["links"])
                self.assertIn("원본 크기로 보기", figure["caption"])
                self.assertGreater(len(figure["caption"]), 80)
        book = PortalFigureParser()
        book.feed((ROOT / "print.html").read_text(encoding="utf-8"))
        self.assertEqual(len(book.figures), 14)
        self.assertTrue(all(figure["id"].startswith("book-") for figure in book.figures))

    def test_current_portal_navigation_does_not_imply_extra_runs_or_promotions(self):
        source = (ROOT / "guide/handbook.md").read_text(encoding="utf-8")
        for text in (
            "Optimize 버튼 → Agent",
            "Choose targets → Instruction만 체크",
            "Select dataset and criteria → Upload dataset",
            "사진은 작성 예시가 아닌 실제 화면",
            "로컬 Contoso 업무 Judge나 최종 fresh 시험의 점수가 아닙니다",
            "최종 fresh run의 화면이 아닙니다",
            "Promote candidate는 누르지 않습니다",
        ):
            self.assertIn(text, source)
        css = (ROOT / "web/styles.css").read_text(encoding="utf-8")
        print_css = css.split("@media print", 1)[1]
        self.assertIn(".guide-content .portal-shot", print_css)
        self.assertIn("max-height: 112mm", print_css)

    def test_guide_version_labels_are_v1_without_rewriting_judge_history(self):
        sources = [
            ROOT / "README.md", ROOT / "README.en.md", ROOT / "data/README.md",
            ROOT / "infra/README.md", *(ROOT / "guide").glob("*.md"),
        ]
        for path in [*sources, *(ROOT / name for name in PAGES)]:
            with self.subTest(document=path.name):
                self.assertNotRegex(path.read_text(encoding="utf-8"), r"(?i)\bv1\.1\b")
        handbook = (ROOT / "guide/handbook.md").read_text(encoding="utf-8")
        self.assertTrue(handbook.startswith("# 좋은 에이전트는 평가에서 시작된다 · v1\n"))
        verification = (ROOT / "guide/verification.md").read_text(encoding="utf-8")
        self.assertIn("검색 Judge 1.1.0", verification)

    def test_source_attribution_uses_the_archived_repository_not_the_reused_name(self):
        source = (ROOT / "guide/verification.md").read_text(encoding="utf-8")
        references = re.findall(r"^\[source-workshop\]: (\S+)", source, flags=re.MULTILINE)
        self.assertEqual(len(references), 1)
        for reference in references:
            self.assertTrue(reference.startswith("https://github.com/junwoojeong100/foundry-evaluation-labs-v0.9/"))
            self.assertIn("93bc07e31373c4cfc278a2dc3757785946404cf2", reference)

    def test_readable_gate_summary_matches_the_actual_workshop_configuration(self):
        source = (ROOT / "guide/handbook.md").read_text(encoding="utf-8")
        gates = json.loads((ROOT / "config/gates.json").read_text(encoding="utf-8"))

        def criterion(label):
            return next(
                line.split("|")[3].strip()
                for line in source.splitlines() if line.startswith(f"| {label} |")
            )

        minimums = gates["minimums"]
        self.assertEqual(criterion("출력 형식"), f"{minimums['format_pass_rate']:.0%}")
        self.assertEqual(criterion("행동 분류"), f"≥{minimums['route_accuracy']:.0%}")
        self.assertEqual(
            criterion("인용·사람 판단 표시"),
            f"인용 ≥{minimums['citation_pass_rate']:.0%}, 사람 판단 표시 {minimums['human_flag_accuracy']:.0%}",
        )
        for label, score in (
            ("업무 정확성", gates["business_policy"]["minimum_mean"]),
            ("검색 근거성", gates["judge"]["minimum_mean"]["groundedness"]),
            ("질문 적합성", gates["judge"]["minimum_mean"]["relevance"]),
        ):
            self.assertEqual(criterion(label), f"1–5점 평균 ≥{score:g}")
        self.assertIn(f"금지 주장 검사도 {minimums['forbidden_claim_pass_rate']:.0%} 통과", source)

    def test_each_existing_evaluation_has_a_sharing_checkpoint_in_the_same_path(self):
        page = LearningPathParser()
        page.feed((ROOT / "index.html").read_text(encoding="utf-8"))
        self.assertEqual(page.sharing_checkpoints, [
            ("share-calibration", "baseline"),
            ("share-baseline", "baseline"),
            ("share-iq", "iq"),
            ("share-optimizer", "optimize"),
            ("share-optimized", "optimize"),
            ("share-holdout", "decision"),
        ])
        source = (ROOT / "guide/handbook.md").read_text(encoding="utf-8")
        for run_id in ("baseline-smoke", "iq-dev", "optimized-dev", "optimized-fresh"):
            score = f"python -m lab score --run-id {run_id}"
            report = f"python -m lab explain --run-id {run_id}"
            self.assertIn(report, source)
            self.assertLess(source.index(score), source.index(report))
        self.assertIn("겹치는 3개 사례 ID", source)
        self.assertIn("dev 12건과 fresh12는 다른 질문", source)
        self.assertIn("자동 외부 전송·업로드는 없습니다", source)

    def test_criteria_reasons_hold_actions_and_improvements_are_connected(self):
        source = (ROOT / "guide/handbook.md").read_text(encoding="utf-8")
        for anchor in ("score-rubric", "hold-actions", "worked-evaluation"):
            self.assertIn(f'id="{anchor}"', source)
        self.assertLess(source.index('id="score-rubric"'), source.index("judge calibrate"))
        self.assertIn("reasons.policy", source)
        self.assertIn("reasons.retrieval", source)
        self.assertIn("python -m lab explain --run-id optimized-dev --baseline iq-dev", source)
        self.assertNotIn("explain --run-id optimized-fresh --baseline", source)
        self.assertIn("답변·점수·해석은 AI가 작성한 교육 예시", source)
        self.assertIn('<table class="worked-comparison">', source)
        self.assertIn("정책 점수 하락의 별도 자동 허용폭은 설정되어 있지 않으며", source)

    def output_examples(self):
        page = OutputExampleParser()
        page.feed((ROOT / "index.html").read_text(encoding="utf-8"))
        return page.examples

    def assert_excerpt(self, example, actual):
        self.assertIs(type(example), type(actual))
        if isinstance(example, dict):
            for key, value in example.items():
                self.assertIn(key, actual)
                self.assert_excerpt(value, actual[key])
        else:
            self.assertEqual(example, actual)

    def test_every_step_has_labelled_non_executable_output_examples(self):
        examples = self.output_examples()
        self.assertEqual(len(examples), 11)
        self.assertEqual({item["chapter"] for item in examples.values()}, {
            "start", "prepare", "baseline", "iq", "optimize", "decision",
        })
        for identifier, example in examples.items():
            with self.subTest(example=identifier):
                self.assertIn(example["language"], {"json", "text"})
                if example["language"] == "json":
                    self.assertIsInstance(json.loads(example["text"]), dict)
        source = (ROOT / "guide/handbook.md").read_text(encoding="utf-8")
        self.assertIn("출력 예시는 설명용으로 작성한 발췌", source)
        self.assertEqual(source.count("**완료 확인:**"), 6)
        shell_blocks = "\n".join(re.findall(r"```bash\s*\n(.*?)```", source, flags=re.DOTALL))
        self.assertEqual(shell_blocks.count('export APPLICATIONINSIGHTS_RESOURCE_ID='), 1)
        self.assertLess(source.index('export APPLICATIONINSIGHTS_RESOURCE_ID='), source.index("## 03."))
        self.assertEqual(source.count("python -m lab score --run-id baseline-smoke"), 1)
        for step in re.split(r"^## ", source, flags=re.MULTILINE)[1:]:
            self.assertIn("**실행 명령", step)
            self.assertIn('class="output-label"', step)
            self.assertIn("**완료 확인:**", step)

    def test_demo_example_matches_actual_offline_output(self):
        from lab.demo import run_demo

        example = json.loads(self.output_examples()["example-demo"]["text"])
        self.assert_excerpt(example, run_demo())

    def test_calibration_example_is_hold_with_one_disagreement_not_a_false_pass(self):
        from lab.calibration import load_fixtures, summarize_calibration

        fixtures = load_fixtures()
        records = [{
            "id": fixture["id"],
            "judge": {
                **{
                    metric: None if expected is None else 5 if expected else 2
                    for metric, expected in fixture["reference_labels"].items()
                },
                "critical_failure": "critical" in fixture["tags"] and not fixture["reference_labels"]["policy_correctness"],
            },
        } for fixture in fixtures]
        index = next(index for index, fixture in enumerate(fixtures) if fixture["reference_labels"]["relevance"] is True)
        records[index]["judge"]["relevance"] = 2
        report = {"execution_status": "completed", **summarize_calibration(fixtures, records)}
        example = json.loads(self.output_examples()["example-calibration"]["text"])
        self.assert_excerpt(example, report)
        self.assertEqual(report["quality_status"], "HOLD")

    def test_trace_example_does_not_claim_no_errors_or_zero_cost(self):
        from lab.control_plane import classify_trace_result

        result = classify_trace_result({"tables": []}, ["resp_EXAMPLE_NOT_LIVE"])
        example = json.loads(self.output_examples()["example-traces"]["text"])
        self.assert_excerpt(example, result)

    def test_candidate_and_final_examples_never_grant_production_approval(self):
        examples = self.output_examples()
        candidate = json.loads(examples["example-optimizer-candidate"]["text"])
        verdict = json.loads(examples["example-final-verdict"]["text"])
        self.assertEqual(candidate["status"], "CANDIDATE_CAPTURED_NOT_LAB_APPROVED")
        self.assertEqual(candidate["imported_fields"], ["system_prompt"])
        self.assertEqual(candidate["human_operational_approval"], "NOT_GRANTED")
        self.assertEqual(verdict["quality_status"], "HOLD")
        self.assertEqual(verdict["manual_operational_approval"], "not_granted")
        self.assertIs(verdict["production_ready"], False)

    def test_participant_has_exactly_six_steps_and_one_forward_path(self):
        page = LearningPathParser()
        page.feed((ROOT / "index.html").read_text(encoding="utf-8"))
        expected = ["start", "prepare", "baseline", "iq", "optimize", "decision"]
        links = ["#" + chapter for chapter in expected]
        self.assertEqual(page.chapters, expected)
        self.assertEqual(page.subchapters, [])
        self.assertEqual(page.toc_links, links)
        self.assertEqual(page.overview_links, links)
        self.assertEqual(page.next_links, links[1:])

    def test_old_participant_anchors_remain_resolvable(self):
        page = LinkParser()
        page.feed((ROOT / "index.html").read_text(encoding="utf-8"))
        self.assertTrue({
            "start", "demo", "prepare", "environment", "first-infrastructure-failure",
            "understand", "data", "baseline", "model-smoke", "calibration",
            "iq", "optimize", "decision", "review", "operate", "cleanup",
            "tune", "troubleshooting", "sources",
        }.issubset(page.ids))

    def test_participant_commands_keep_one_judge_and_optimizer_without_reprovisioning(self):
        source = (ROOT / "guide/handbook.md").read_text(encoding="utf-8")
        commands = []
        paid_commands = []
        for block in re.findall(r"```bash\s*\n(.*?)```", source, flags=re.DOTALL):
            for line in block.replace("\\\n", " ").splitlines():
                tokens = shlex.split(line, comments=True)
                if "-m" not in tokens:
                    continue
                position = tokens.index("-m")
                module = tokens[position + 1]
                args = tokens[position + 2:]
                self.assertNotEqual(module, "lab.sft")
                if module == "lab.bootstrap":
                    self.assertEqual(args[0], "status")
                if module == "lab":
                    parsed = lab_parser().parse_args(args)
                    commands.append(parsed.command)
                    if getattr(parsed, "confirm", False):
                        if parsed.command == "judge":
                            paid_commands.append(("judge", parsed.judge_action, getattr(parsed, "run_id", getattr(parsed, "calibration_id", None))))
                        elif parsed.command == "agent":
                            paid_commands.append(("agent", parsed.stage))
                        elif parsed.command == "iq":
                            paid_commands.append(("iq", parsed.action))
                        else:
                            paid_commands.append((parsed.command, parsed.run_id))
                    self.assertNotIn(parsed.command, {
                        "evaluate", "optimizer-result", "tune-prepare", "bootstrap", "review",
                    })
                    if parsed.command == "agent":
                        self.assertIsNone(parsed.prompt)
                    if parsed.command == "cleanup":
                        self.assertIsNone(parsed.confirm_prefix)
        self.assertEqual(commands.count("demo"), 1)
        self.assertEqual(commands.count("optimize"), 1)
        self.assertEqual(commands.count("optimizer-agent-result"), 1)
        self.assertEqual(commands.count("judge"), 5)
        self.assertEqual(paid_commands, [
            ("smoke", "model-smoke"),
            ("agent", "baseline"), ("run", "baseline-smoke"),
            ("judge", "calibrate", "cal-01"), ("judge", "score", "baseline-smoke"),
            ("iq", "prepare"), ("iq", "vectors"), ("iq", "probe"),
            ("agent", "iq"), ("run", "iq-dev"), ("judge", "score", "iq-dev"),
            ("agent", "optimized"), ("run", "optimized-dev"), ("judge", "score", "optimized-dev"),
            ("run", "optimized-fresh"), ("judge", "score", "optimized-fresh"),
        ])
        self.assertLess(source.index("judge calibrate"), source.index("freeze --freeze-id"))
        self.assertLess(source.index("freeze --freeze-id"), source.index("holdout create"))
        self.assertLess(source.index("holdout create"), source.index("run --stage optimized --split test"))

    def test_every_rendered_page_has_resolvable_local_links_and_unique_ids(self):
        parsed = {}
        for name in PAGES:
            path = ROOT / name
            self.assertTrue(path.is_file(), f"Run the full guide/print builders first: {name}")
            page = LinkParser()
            page.feed(path.read_text(encoding="utf-8"))
            self.assertFalse(page.duplicate_ids, (name, page.duplicate_ids))
            parsed[path.resolve()] = page
        for path, page in parsed.items():
            for href in page.links:
                url = urlsplit(href)
                if url.scheme or url.netloc:
                    self.assertFalse(url.hostname in {"127.0.0.1", "localhost"}, (path.name, href))
                    continue
                target = (path.parent / unquote(url.path)).resolve() if url.path else path
                self.assertTrue(target.is_relative_to(ROOT), (path.name, href))
                self.assertTrue(target.exists(), (path.name, href))
                if url.fragment and target in parsed:
                    self.assertIn(unquote(url.fragment), parsed[target].ids, (path.name, href))

    def test_workshop_cli_commands_in_markdown_are_parseable(self):
        checked = 0
        for path in (ROOT / "guide").glob("*.md"):
            source = path.read_text(encoding="utf-8")
            for block in re.findall(r"```bash\s*\n(.*?)```", source, flags=re.DOTALL):
                for line in block.replace("\\\n", " ").splitlines():
                    tokens = shlex.split(line, comments=True)
                    if "-m" not in tokens:
                        continue
                    position = tokens.index("-m")
                    if len(tokens) <= position + 1:
                        continue
                    module = tokens[position + 1]
                    if module not in {"lab", "lab.sft"}:
                        continue
                    command_parser = lab_parser() if module == "lab" else sft_parser()
                    with self.subTest(document=path.name, command=line), \
                         contextlib.redirect_stdout(io.StringIO()), \
                         contextlib.redirect_stderr(io.StringIO()):
                        try:
                            command_parser.parse_args(tokens[position + 2:])
                        except SystemExit as exc:
                            self.assertEqual(exc.code, 0, f"Documented CLI syntax is invalid: {line}")
                    checked += 1
        self.assertGreaterEqual(checked, 40)


if __name__ == "__main__":
    unittest.main()
