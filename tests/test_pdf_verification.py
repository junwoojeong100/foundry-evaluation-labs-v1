"""Optional PDF-checker tests; no cloud calls or published file writes."""

from importlib.util import find_spec
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


@unittest.skipUnless(find_spec("pymupdf"), "Install requirements-verification.lock for PDF tests")
class PdfVerificationTests(unittest.TestCase):
    def test_original_code_terms_do_not_restore_a_training_lesson(self):
        import pymupdf
        from scripts.verify_pdf import inspect_pdf

        with TemporaryDirectory() as directory:
            path = Path(directory) / "source.pdf"
            with pymupdf.open() as document:
                page = document.new_page()
                page.insert_text((40, 40), "Actual implementation: cleanup_plan", fontname="helv")
                page.insert_text((40, 70), '"SFT/FDE training jobs require their own scoped cleanup."', fontname="cour")
                document.save(path)
            report = inspect_pdf(path, language="en")
            self.assertFalse(report["removed_sft_content_present"])
            self.assertTrue(report["monospace_sft_reference_present"])

    def test_training_prose_and_removed_appendix_paths_still_fail(self):
        import pymupdf
        from scripts.verify_pdf import inspect_pdf

        for text, font in (("SFT training lesson", "helv"), ("sft-appendix.md", "cour")):
            with self.subTest(text=text), TemporaryDirectory() as directory:
                path = Path(directory) / "training.pdf"
                with pymupdf.open() as document:
                    page = document.new_page()
                    page.insert_text((40, 40), text, fontname=font)
                    document.save(path)
                report = inspect_pdf(path, language="en")
                self.assertTrue(report["removed_sft_content_present"])
                self.assertEqual(report["status"], "FAIL")
