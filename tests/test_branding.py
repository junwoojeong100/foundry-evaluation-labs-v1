"""Offline checks for the unchanged Microsoft-published Foundry service icon."""

from __future__ import annotations

import hashlib
import re
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
ICON_PATH = "web/assets/foundry.svg"
ICON_SHA256 = "fab039a771f72780ae34e59065d61c66a02d3c347d50923ef2956f34912ea02c"
SOURCE_URL = "https://arch-center.azureedge.net/icons/Azure_Public_Service_Icons_V24.zip"
SOURCE_ENTRY = (
    "Azure_Public_Service_Icons/Icons/ai + machine learning/"
    "035746832-icon-service-AI-Foundry.svg"
)
TERMS_URL = "https://learn.microsoft.com/en-us/azure/architecture/icons/"
SVG_NAMESPACE = "http://www.w3.org/2000/svg"


class BrandingParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.favicons: list[dict[str, str | None]] = []
        self.brand_elements: list[tuple[str, dict[str, str | None]]] = []
        self.brand_label: str | None = None
        self.in_brand = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "link" and "icon" in (attributes.get("rel") or "").split():
            self.favicons.append(attributes)
        if tag == "a" and "brand" in (attributes.get("class") or "").split():
            self.in_brand = True
            self.brand_label = attributes.get("aria-label")
        if self.in_brand:
            self.brand_elements.append((tag, attributes))

    def handle_endtag(self, tag: str) -> None:
        if tag == "a":
            self.in_brand = False


class BrandingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.icon_bytes = (ROOT / ICON_PATH).read_bytes()
        cls.template = (ROOT / "web/template.html").read_text(encoding="utf-8")
        cls.css = (ROOT / "web/styles.css").read_text(encoding="utf-8")
        cls.notice = (ROOT / "web/assets/NOTICE.txt").read_text(encoding="utf-8")
        cls.page = BrandingParser()
        cls.page.feed(cls.template)

    def test_header_and_favicon_reference_the_same_local_svg(self) -> None:
        images = [attrs for tag, attrs in self.page.brand_elements if tag == "img"]
        self.assertEqual(len(images), 1)
        self.assertEqual(len(self.page.favicons), 1)
        self.assertEqual(images[0].get("src"), ICON_PATH)
        self.assertEqual(self.page.favicons[0].get("href"), ICON_PATH)
        self.assertEqual(self.page.favicons[0].get("type"), "image/svg+xml")
        url = urlsplit(ICON_PATH)
        self.assertFalse(url.scheme or url.netloc or url.query or url.fragment)
        self.assertFalse(url.path.startswith("/"))
        self.assertTrue((ROOT / url.path).is_file())
        self.assertFalse(any(tag == "svg" for tag, _ in self.page.brand_elements))

    def test_decorative_header_icon_preserves_accessible_link_name(self) -> None:
        image = next(attrs for tag, attrs in self.page.brand_elements if tag == "img")
        self.assertEqual(image.get("alt"), "")
        self.assertEqual(image.get("aria-hidden"), "true")
        self.assertEqual(image.get("width"), image.get("height"))
        self.assertEqual(image.get("width"), "42")
        self.assertIn("Microsoft Foundry", self.page.brand_label or "")

    def test_artwork_matches_the_official_source_hash(self) -> None:
        self.assertEqual(hashlib.sha256(self.icon_bytes).hexdigest(), ICON_SHA256)

    def test_legacy_favicon_is_a_byte_identical_compatibility_copy(self) -> None:
        self.assertEqual(
            (ROOT / "web/assets/favicon.svg").read_bytes(),
            self.icon_bytes,
        )

    def test_svg_is_valid_self_contained_and_has_the_original_viewbox(self) -> None:
        self.assertNotIn(b"<!DOCTYPE", self.icon_bytes.upper())
        self.assertNotIn(b"<!ENTITY", self.icon_bytes.upper())
        root = ET.fromstring(self.icon_bytes)
        self.assertEqual(root.tag, f"{{{SVG_NAMESPACE}}}svg")
        self.assertEqual(root.attrib["viewBox"], "0 0 18 18")
        self.assertEqual(root.attrib["width"], "18")
        self.assertEqual(root.attrib["height"], "18")
        self.assertEqual(len(root.findall(f"{{{SVG_NAMESPACE}}}path")), 4)
        identifiers = [node.attrib["id"] for node in root.iter() if "id" in node.attrib]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        allowed_elements = {"svg", "defs", "linearGradient", "stop", "path"}
        for node in root.iter():
            with self.subTest(element=node.tag):
                self.assertTrue(node.tag.startswith(f"{{{SVG_NAMESPACE}}}"))
                self.assertIn(node.tag.split("}", 1)[1], allowed_elements)
                for attribute, value in node.attrib.items():
                    name = attribute.rsplit("}", 1)[-1].lower()
                    self.assertFalse(name.startswith("on"))
                    if name in {"href", "src"}:
                        self.assertTrue(value.startswith("#"))
                        self.assertIn(value[1:], identifiers)
                    for reference in re.findall(r"url\(([^)]+)\)", value):
                        self.assertTrue(reference.startswith("#"))
                        self.assertIn(reference[1:], identifiers)

    def test_responsive_icon_preserves_proportions_without_custom_framing(self) -> None:
        rules = re.findall(r"\.brand-symbol\s*\{([^}]+)\}", self.css)
        self.assertEqual(len(rules), 2)
        expected_sizes = ("2.65rem", "2.2rem")
        for rule, size in zip(rules, expected_sizes):
            declarations = dict(
                (name.strip(), value.strip())
                for name, value in (
                    declaration.split(":", 1)
                    for declaration in rule.split(";")
                    if declaration.strip()
                )
            )
            self.assertEqual(declarations["width"], size)
            self.assertEqual(declarations["height"], size)
            for forbidden in (
                "background", "background-color", "border", "border-radius",
                "clip-path", "filter", "transform", "overflow",
            ):
                self.assertNotIn(forbidden, declarations)
        self.assertIn("object-fit: contain", rules[0])
        self.assertIn("flex: 0 0 auto", rules[0])
        self.assertNotIn(".brand-symbol svg", self.css)

    def test_notice_records_source_identity_hash_and_restricted_usage(self) -> None:
        for required in (
            "Microsoft Corporation",
            SOURCE_URL,
            SOURCE_ENTRY,
            TERMS_URL,
            ICON_SHA256,
            "architectural diagrams, training",
            "Microsoft reserves all other rights.",
            "Don't crop, flip, or rotate icons.",
            "Don't distort or change icon shape in any way.",
            "Don't use Microsoft product icons to represent your product or service.",
            "not a claim that the artwork is a",
        ):
            with self.subTest(required=required):
                self.assertIn(required, self.notice)


if __name__ == "__main__":
    unittest.main()
