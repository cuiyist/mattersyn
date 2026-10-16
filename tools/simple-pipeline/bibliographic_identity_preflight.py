"""Read-only bibliographic alias proposals; never edits DOI identities or records."""
import argparse
import hashlib
import html
import json
from pathlib import Path
import re
import unicodedata


def normalized(value):
    value = html.unescape(re.sub(r"<[^>]+>", " ", str(value)))
    value = unicodedata.normalize("NFKD", value).casefold()
    return "".join(c for c in value if c.isalnum() and not unicodedata.combining(c))


def identity(row):
    citation = row.get("citation", row)
    doi = str(row.get("doi", citation.get("DOI", ""))).strip().lower()
    title = citation.get("title", "")
    if isinstance(title, list):
        title = " ".join(title) if all(isinstance(x, str) for x in title) else ""
    if not isinstance(title, str):
        title = ""
    year = citation.get("year")
    if year is None:
        for key in ("published", "published-print", "published-online", "issued"):
            date = citation.get(key)
            parts = date.get("date-parts") if isinstance(date, dict) else None
            if isinstance(parts, list) and parts and isinstance(parts[0], list) and parts[0]:
                year = parts[0][0]
                break
    raw_authors = citation.get("authors", citation.get("author"))
    if isinstance(raw_authors, str):
        # Comma strings can mean either author separators or family/given order.
        raw_authors = raw_authors.split(";") if "," not in raw_authors else None
    author_ids = []
    if isinstance(raw_authors, list) and raw_authors:
        for author in raw_authors:
            if isinstance(author, dict):
                author = f"{author.get('given', '')} {author.get('family', '')}".strip()
            if not isinstance(author, str) or len(author.split()) < 2:
                author_ids = []
                break
            author_ids.append(normalized(author))
    if not doi:
        raise ValueError("Bibliographic DOI is missing")
    year_valid = type(year) is int and 1000 <= year <= 2999
    return {"doi": doi, "title": normalized(title),
            "year": year if year_valid else None, "authors": author_ids or None}


def paired_wiley(a, b):
    x = re.fullmatch(r"10\.1002/(ange|anie)\.(.+)", a)
    y = re.fullmatch(r"10\.1002/(ange|anie)\.(.+)", b)
    return bool(x and y and x[1] != y[1] and x[2] == y[2])


def relation(a, b):
    if a["doi"] == b["doi"]:
        return None
    title_year = bool(a["title"] and a["title"] == b["title"]
                      and a["year"] is not None and a["year"] == b["year"])
    paired = paired_wiley(a["doi"], b["doi"])
    if not (title_year or paired):
        return None
    strong = bool(paired and title_year and a["authors"]
                  and a["authors"] == b["authors"])
    return "strong_same_primary" if strong else "ambiguous_technical_hold"


def screen(incoming_rows, existing_rows):
    incoming = [identity(row) for row in incoming_rows]
    existing = [identity(row) for row in existing_rows]
    aliases, holds, same_doi = [], [], []
    missing = [{"doi": row["doi"], "fields": [key for key in ("title", "year", "authors")
               if not row[key]]} for row in incoming if not all(row[k] for k in ("title", "year", "authors"))]
    represented = {row["doi"] for row in existing}
    for row in incoming:
        if row["doi"] in represented:
            same_doi.append(row["doi"])
        for old in existing:
            match = relation(row, old)
            if match == "strong_same_primary":
                aliases.append({"incoming_doi": row["doi"], "represented_doi": old["doi"],
                                "scope": "existing_primary", "proposal": "omit_incoming_duplicate"})
                break  # Preserve the first already-represented DOI.
            if match:
                holds.append({"DOIs": [old["doi"], row["doi"]], "scope": "existing_primary"})
    for index, left in enumerate(incoming):
        for right in incoming[index + 1:]:
            match = relation(left, right)
            if match == "strong_same_primary":
                # An existing representation always takes precedence over English preference.
                if left["doi"] in represented or right["doi"] in represented:
                    continue
                keep, omit = (left, right) if left["doi"].startswith("10.1002/anie.") else (right, left)
                aliases.append({"incoming_doi": omit["doi"], "represented_doi": keep["doi"],
                                "scope": "incoming_queue", "proposal": "omit_incoming_duplicate"})
            elif match:
                holds.append({"DOIs": [left["doi"], right["doi"]], "scope": "incoming_queue"})
    def unique(rows):
        return list({json.dumps(row, sort_keys=True): row for row in rows}.values())
    return {"schema": "bibliographic-identity-proposals/1", "proposal_only": True,
            "incoming_rows": len(incoming), "existing_rows": len(existing),
            "strong_alias_proposals": unique(aliases), "ambiguous_technical_holds": unique(holds),
            "missing_or_unsupported_identity_fields": unique(missing),
            "already_represented_same_DOI": sorted(set(same_doi)),
            "DOIs_or_existing_records_rewritten": False, "scientific_statuses_changed": False}


def trusted_authority(document):
    rows = document["records"]
    for row in rows:
        if row.get("metadata_only") is not True or row.get("doi_exact_match") is not True:
            raise ValueError("Authority row lacks exact trusted metadata flags")
        if row["doi"].strip().lower() != row["citation"]["DOI"].strip().lower():
            raise ValueError("Authority DOI and citation DOI differ")
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authority", action="append", type=Path, default=[])
    parser.add_argument("--existing-metadata", type=Path,
                        help="Explicit records-shaped published bibliographic metadata, not a live-tree assumption")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    if not args.execute:
        print(json.dumps({"inert": True, "file_reads_or_writes": 0}))
        return 0
    if not args.authority or args.existing_metadata is None or args.out is None:
        parser.error("--execute requires --authority, --existing-metadata and --out")
    if args.out.exists():
        raise FileExistsError("Output already exists")
    paths = [args.existing_metadata] + args.authority
    blobs = [path.read_bytes() for path in paths]
    existing = json.loads(blobs[0])["records"]
    incoming = [row for data in blobs[1:] for row in trusted_authority(json.loads(data))]
    result = screen(incoming, existing)
    result["input_pins"] = [{"path": str(path), "bytes": len(data),
                             "sha256": hashlib.sha256(data).hexdigest()}
                            for path, data in zip(paths, blobs)]
    with args.out.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"aliases": len(result["strong_alias_proposals"]),
                      "ambiguous": len(result["ambiguous_technical_holds"]),
                      "identity_field_holds": len(result["missing_or_unsupported_identity_fields"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
