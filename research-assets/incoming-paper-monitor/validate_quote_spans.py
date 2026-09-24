"""Check whether extracted evidence quotes occur on the cited PDF text page.

This is a mechanical citation-presence check only. It does not validate the
scientific interpretation, figure reading, sample assignment, or completeness.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path
from typing import Any


PAGE_MARKER = re.compile(r"(?m)^===== PDF PAGE (\d+) =====\s*$")


def split_pdf_pages(text: str) -> dict[int, str]:
    """Split text made by the project PDF extractor's page-marker format."""
    markers = list(PAGE_MARKER.finditer(text))
    pages: dict[int, str] = {}
    for index, marker in enumerate(markers):
        end = markers[index + 1].start() if index + 1 < len(markers) else len(text)
        pages[int(marker.group(1))] = text[marker.end() : end]
    return pages


def normalize_for_quote_match(text: str) -> str:
    """Normalize PDF line wrapping while preserving wording and symbols.

    Only line-end hyphenation is removed. Footnote numbers, punctuation, units,
    and ordinary hyphens stay in place so a paraphrase is not accepted as a
    verbatim source span.
    """
    normalized = unicodedata.normalize("NFKC", text).replace("\r", "")
    normalized = re.sub(r"(?<=\w)-\n[ \t]*(?=\w)", "", normalized)
    return re.sub(r"\s+", " ", normalized).casefold().strip()


def get_by_path(data: Any, path: str) -> Any:
    value = data
    for part in filter(None, path.split(".")):
        if isinstance(value, dict):
            value = value.get(part)
        elif isinstance(value, list):
            value = value[int(part)]
        else:
            return None
    return value


def load_draft(path: Path) -> Any:
    draft = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(draft, dict) and isinstance(draft.get("response"), str):
        try:
            return json.loads(draft["response"])
        except json.JSONDecodeError:
            return draft
    return draft


def validate_quotes(
    pages: dict[int, str],
    draft: Any,
    claims_path: str = "procedure_claims",
    quote_key: str = "exact_verbatim_quote",
    page_key: str = "pdf_page",
) -> dict[str, Any]:
    claims = get_by_path(draft, claims_path)
    if not isinstance(claims, list):
        raise ValueError(f"Expected a list at claims path: {claims_path}")

    default_page = draft.get(page_key) if isinstance(draft, dict) else None
    results = []
    for index, claim in enumerate(claims):
        page_no = claim.get(page_key, default_page) if isinstance(claim, dict) else None
        quote = claim.get(quote_key, "") if isinstance(claim, dict) else ""
        source = pages.get(page_no) if isinstance(page_no, int) else None
        matched = bool(
            source
            and quote
            and normalize_for_quote_match(quote)
            in normalize_for_quote_match(source)
        )
        results.append(
            {
                "claim_index": index,
                "pdf_page": page_no,
                "quote_present": matched,
            }
        )

    matched_count = sum(row["quote_present"] for row in results)
    return {
        "check": "quoted text presence only; not scientific verification",
        "claim_count": len(results),
        "matched_count": matched_count,
        "unmatched_count": len(results) - matched_count,
        "claims": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-text", required=True, type=Path)
    parser.add_argument("--draft-json", required=True, type=Path)
    parser.add_argument("--claims-path", default="procedure_claims")
    parser.add_argument("--quote-key", default="exact_verbatim_quote")
    parser.add_argument("--page-key", default="pdf_page")
    args = parser.parse_args()

    source = args.source_text.read_text(encoding="utf-8-sig")
    draft = load_draft(args.draft_json)
    result = validate_quotes(
        split_pdf_pages(source),
        draft,
        claims_path=args.claims_path,
        quote_key=args.quote_key,
        page_key=args.page_key,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
