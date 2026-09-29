import contextlib
from html.parser import HTMLParser
import io
from pathlib import Path
import re
import shlex
import unittest
from urllib.parse import unquote, urlsplit

from lab.cli import parser as lab_parser
from lab.sft import parser as sft_parser


ROOT = Path(__file__).resolve().parents[1]
PAGES = ("index.html", "facilitator.html", "admin.html", "sft.html", "verification.html", "data-guide.html", "migration.html", "english.html", "print.html")


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


class DocumentationTests(unittest.TestCase):
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
