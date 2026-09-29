"""Check the generated lab PDF; install requirements-verification.lock first."""

import argparse
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

import pymupdf


def inspect_pdf(path: Path) -> dict:
    with pymupdf.open(path) as document:
        texts = [page.get_text() for page in document]
        normalized = " ".join(" ".join(texts).split())
        local_links = []
        outside = []
        for number, page in enumerate(document, start=1):
            for link in page.get_links():
                uri = link.get("uri")
                if uri:
                    parsed = urlsplit(uri)
                    if parsed.scheme == "file" or parsed.hostname in {"127.0.0.1", "localhost", "::1"}:
                        local_links.append({"page": number, "uri": uri})
            for block in page.get_text("dict")["blocks"]:
                for line in block.get("lines", []):
                    for span in line["spans"]:
                        x0, y0, x1, y1 = span["bbox"]
                        if span["text"].strip() and (
                            x0 < -1 or y0 < -1 or x1 > page.rect.width + 1 or y1 > page.rect.height + 1
                        ):
                            outside.append({"page": number, "text": span["text"][:80], "bbox": span["bbox"]})
        required = (
            "Frontier Tuning", "Foundry IQ", "Optimizer", "North Central US",
            "준비 완료는 학습 완료가 아닙니다.", "Foundry SFT",
            "학습 전", "미노출", "검증 기록과 한계",
        )
        missing = [term for term in required if term not in normalized]
        almost_empty = [i + 1 for i, text in enumerate(texts) if len(text.strip()) < 80]
        result = {
            "file": path.name,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "pages": len(document),
            "bytes": path.stat().st_size,
            "korean_characters": len(re.findall("[가-힣]", normalized)),
            "minimum_page_characters": min((len(text.strip()) for text in texts), default=0),
            "missing_required_text": missing,
            "almost_empty_pages": almost_empty,
            "local_machine_links": local_links,
            "out_of_page_text": outside,
        }
        result["status"] = "PASS" if (
            result["pages"] > 0 and result["korean_characters"] > 1000
            and not missing and not almost_empty and not local_links and not outside
        ) else "FAIL"
        return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--out", type=Path, default=Path("artifacts/verification/pdf-check.json"))
    args = parser.parse_args()
    report = inspect_pdf(args.pdf)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

