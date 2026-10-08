"""Offline corpus-selection tests; no Azure calls or claims of live quality."""

import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from lab import calibration, governance
from lab.batch import dataset_for_metadata
from lab.config import Config, LabError
from lab.content import content_path, dataset_files, require_content_language, selected_language
from lab.files import ROOT, read_jsonl, workspace
from lab.handoffs import prepare_tuning
from scripts import build_datasets


class ContentLanguageTests(unittest.TestCase):
    def setUp(self):
        language = patch.dict(os.environ, {"LAB_LANGUAGE": "ko"})
        language.start()
        self.addCleanup(language.stop)

    def test_original_korean_generated_bytes_are_preserved(self):
        artifacts = build_datasets.build_artifacts(ROOT)
        self.assertEqual(len(artifacts), 8)
        for name, expected in artifacts.items():
            self.assertEqual((ROOT / name).read_bytes(), expected, name)
        self.assertEqual(content_path(ROOT, "data/cases.jsonl"), ROOT / "data/cases.jsonl")

    def test_english_corpus_has_complete_deterministic_exports(self):
        first = build_datasets.build_artifacts(ROOT, language="en")
        self.assertEqual(first, build_datasets.build_artifacts(ROOT, language="en"))
        self.assertEqual(len(first), 8)
        self.assertTrue(all(name.startswith("data/en/") for name in first))
        for name, expected in first.items():
            self.assertEqual((ROOT / name).read_bytes(), expected, name)
        manifest = json.loads(first["data/en/manifest.json"])
        self.assertEqual(manifest["dataset"], "contoso-atlas-cloud-en-v1")
        self.assertEqual(manifest["language"], "en")
        self.assertEqual(manifest["counts"], {"train": 56, "validation": 12, "dev": 12, "test": 20})
        self.assertEqual(manifest["critical_counts"], {"train": 13, "validation": 3, "dev": 4, "test": 9})
        self.assertFalse(manifest["provenance"]["network_or_model_calls"])

    def test_translation_preserves_structural_metadata_and_reference_routes(self):
        original = read_jsonl(ROOT / "data/cases.jsonl")
        english = read_jsonl(ROOT / "data/en/cases.jsonl")
        self.assertEqual(len(original), len(english))
        prose = {"query", "context", "ground_truth", "forbidden_claims"}
        for ko, en in zip(original, english, strict=True):
            with self.subTest(case=ko["id"]):
                self.assertEqual(set(ko), set(en))
                self.assertEqual(
                    {key: value for key, value in ko.items() if key not in prose},
                    {key: value for key, value in en.items() if key not in prose},
                )
                ko_answer, en_answer = json.loads(ko["ground_truth"]), json.loads(en["ground_truth"])
                self.assertEqual(
                    {key: value for key, value in ko_answer.items() if key != "answer"},
                    {key: value for key, value in en_answer.items() if key != "answer"},
                )
                self.assertNotRegex(en["query"] + en["context"] + en_answer["answer"], r"[가-힣]")

    def test_english_policies_preserve_ids_dates_and_paragraph_structure(self):
        ko = json.loads((ROOT / "data/knowledge/documents.json").read_text())
        en = build_datasets.load_documents(ROOT / "data/en/knowledge/documents.json", language="en")
        self.assertEqual(len(en), 8)
        for document in ko:
            translated = en[document["id"]]
            self.assertEqual(translated["effective_date"], document["effective_date"])
            self.assertEqual(
                len(translated["content"].split("\n\n")),
                len(document["content"].split("\n\n")),
            )

    def test_invalid_or_missing_english_content_never_falls_back_to_korean(self):
        with patch.dict(os.environ, {"LAB_LANGUAGE": "invalid"}):
            with self.assertRaisesRegex(LabError, "Unsupported LAB_LANGUAGE"):
                selected_language()
        with patch.dict(os.environ, {"LAB_LANGUAGE": "en"}):
            self.assertEqual(content_path(ROOT, "prompts/baseline.txt"), ROOT / "prompts/en/baseline.txt")
            with self.assertRaises(LabError):
                content_path(ROOT, "../data/cases.jsonl")
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                build_datasets.build_artifacts(Path(directory), language="en")
        with self.assertRaises(build_datasets.DatasetError):
            build_datasets.load_documents(ROOT / "data/knowledge/documents.json", language="en")

    def test_saved_run_language_is_explicit_and_legacy_runs_remain_korean(self):
        self.assertEqual(dataset_for_metadata({"source_split": "dev"}), ROOT / "data/splits/dev.jsonl")
        with self.assertRaisesRegex(LabError, "LAB_LANGUAGE=en"):
            dataset_for_metadata({"source_split": "dev", "language": "en"})
        with patch.dict(os.environ, {"LAB_LANGUAGE": "en"}):
            self.assertEqual(
                dataset_for_metadata({"source_split": "dev", "language": "en"}),
                ROOT / "data/en/splits/dev.jsonl",
            )
            with self.assertRaisesRegex(LabError, "LAB_LANGUAGE=ko"):
                require_content_language({})
            with self.assertRaisesRegex(LabError, "Invalid recorded"):
                require_content_language({"language": None})

    def test_workspace_cannot_be_reused_across_languages(self):
        config = Config(
            subscription_id="00000000-0000-0000-0000-000000000001",
            tenant_id="00000000-0000-0000-0000-000000000002",
            expected_user="unit@example.invalid", location="northcentralus",
            resource_group="unit-rg", account="unit-ai", project="unit-project",
            project_endpoint="https://unit-ai.services.ai.azure.com/api/projects/unit-project",
            openai_endpoint="https://unit-ai.openai.azure.com",
            search_service="unit-search", search_endpoint="https://unit-search.search.windows.net",
            model="unit-agent", judge="unit-judge", optimizer="unit-planner",
            prefix="unit-lab", planner="unit-planner",
        )
        with tempfile.TemporaryDirectory() as directory, patch("lab.files.artifacts_dir", return_value=Path(directory)):
            with patch.dict(os.environ, {"LAB_LANGUAGE": "en"}):
                state = workspace(config, create=True)
                self.assertEqual(state["language"], "en")
            with self.assertRaisesRegex(LabError, "LAB_LANGUAGE=en"):
                workspace(config)

    def test_freeze_inputs_are_isolated_by_language(self):
        korean = dataset_files(ROOT)
        self.assertTrue(korean)
        self.assertFalse(any(path.is_relative_to(ROOT / "data/en") for path in korean))
        with patch.dict(os.environ, {"LAB_LANGUAGE": "en"}):
            english = dataset_files(ROOT)
        self.assertTrue(english)
        self.assertTrue(all(path.is_relative_to(ROOT / "data/en") for path in english))
        self.assertTrue(set(korean).isdisjoint(english))
        self.assertFalse(any("calibration" in path.parts for path in korean + english))

    def test_english_calibration_and_dialogue_preserve_their_contracts(self):
        ko = calibration.load_fixtures()
        with patch.dict(os.environ, {"LAB_LANGUAGE": "en"}):
            en = calibration.load_fixtures()
            contract = calibration.evaluator_contract()
            dialogue_path = dataset_for_metadata({
                "language": "en", "source_split": "dev", "dialogue_diagnostic": True,
            })
        self.assertEqual(len(en), 16)
        self.assertEqual([row["reference_labels"] for row in en], [row["reference_labels"] for row in ko])
        self.assertEqual(contract["language"], "en")
        self.assertTrue(all(value["pass_threshold"] == 4 for value in contract["definitions"].values()))
        dialogue = read_jsonl(dialogue_path)
        self.assertEqual(len(dialogue), 1)
        self.assertNotRegex(dialogue[0]["query"] + dialogue[0]["follow_up"], r"[가-힣]")

    def test_english_holdout_recipes_are_complete_and_nonce_is_not_a_leakage_bypass(self):
        ko = governance._templates()
        with patch.dict(os.environ, {"LAB_LANGUAGE": "en"}):
            en = governance._templates()
        self.assertEqual([row[:3] for row in en], [row[:3] for row in ko])
        self.assertEqual(len(en), 20)
        self.assertTrue(all(not re.search("[가-힣]", row[3] + row[4]) for row in en))
        self.assertEqual(
            governance._normal_query("Synthetic scenario deadbeef: Same question 12"),
            governance._normal_query("Synthetic scenario 1234abcd: Same question 12"),
        )

    def test_english_demo_is_sdk_free_and_explicitly_authored(self):
        completed = subprocess.run(
            [sys.executable, "-S", "-m", "lab", "demo"], cwd=ROOT,
            env={**os.environ, "LAB_LANGUAGE": "en"}, text=True, capture_output=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(result["kind"], "AUTHORED_DEMO_NOT_LIVE")
        self.assertEqual(result["language"], "en")
        self.assertEqual(result["network_calls"], 0)
        self.assertNotRegex(completed.stdout, r"[가-힣]")

    def test_english_training_preparation_uses_only_english_train_and_validation(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.dict(os.environ, {"LAB_LANGUAGE": "en"}), \
             patch("lab.handoffs.artifacts_dir", return_value=Path(directory)), \
             patch("lab.governance.artifacts_dir", return_value=Path(directory)):
            target = prepare_tuning("sft")
            manifest = json.loads((target / "manifest.json").read_text())
            self.assertEqual(manifest["language"], "en")
            self.assertFalse(manifest["test_data_included"])
            for split, count in (("train", 56), ("validation", 12)):
                path = target / f"sft-{split}.jsonl"
                self.assertTrue(path.read_bytes().startswith(b"\xef\xbb\xbf"))
                rows = read_jsonl(path)
                self.assertEqual(len(rows), count)
                self.assertNotRegex(path.read_text(encoding="utf-8-sig"), r"[가-힣]")
                self.assertEqual(rows, read_jsonl(ROOT / f"data/en/tuning/sft-{split}.jsonl"))


if __name__ == "__main__":
    unittest.main()
