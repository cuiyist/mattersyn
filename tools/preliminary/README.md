# Preliminary synthesis tooling

This lane publishes concise, author-source-checked synthesis contributions. It is **preliminary, not independently audited, accuracy unmeasured, and excluded from training**. Mechanical quote checks do not establish scientific correctness, full-paper coverage or a complete laboratory SOP. Gold records and verified-pair counters are unchanged.

`recipe-atlas/scripts/preliminary_contract.py` is the one public schema implementation. `validate_catalog(data)` returns a list of errors; an empty list means schema-valid. It imports only the standard library. `public-schema.json` documents the same field shapes; cross-field requirements remain authoritative in `validate_catalog`. `synthetic-example.json` is an engineering example, not a real paper, and must never be merged into a live catalog.

## Author once, then project and merge

1. Keep the candidate and evidence in a private work folder. Use a canonical lowercase bare DOI and `prelim-` plus the first 16 hexadecimal characters of SHA256(DOI). Do not create a second entry for main and SI of the same DOI. Render links only as `https://doi.org/` plus the DOI. Do not change or guess a DOI to bypass deduplication.
2. Read the declared recipe and its linked product. Write at least one precursor, two distinct ordered operations, one quantitative amount/condition and one source-explicit structural descriptor. State omitted variants, deferred scope, and missing information. A disconnected size value, title or property result is insufficient. Strings are concise authored paraphrases; retain literal reported values/ranges. All keys are required, including an `evidence_fingerprint` placeholder. The projector replaces only that digest, not scientific fields.
3. Create a private page map, with exact PDF SHA256 and actual page count. Version1 uses pypdf `PdfReader(BytesIO(exact_pdf_bytes), strict=True).pages[index].extract_text()`, normalized only with Unicode NFKC and collapsed whitespace. Page numbers are one-based. Existing cache maps can be reused if they exactly match this extraction; otherwise regenerate only the map from the same local PDF. Scanned/OCR-only pages fail closed in this version. No external processing is performed.
4. Save the companion as `<source_id>.json` in the evidence directory. It must pin the PDF, actual strict-pass JSONL row and page map. Claims cover every pointer returned by `scientific_fields(entry)`: DOI/title, material label/elements, method, precursor name/amount/role, operation action and condition fields, outcome link/sample, descriptor kind/value/technique. A claim has an exact normalized quote on a pinned page, source value/unit tokens, and the extractor's `semantic_link_checked: true`. That flag is an author assertion; it is not an independent audit. A claim page must match the field's public locators. Scope/deferred/missing/review fields are editorial metadata, not source measurements.
5. Run `project` in a local Python environment with pypdf available. It reads actual PDF bytes, verifies actual page count and inspected text pages, checks the real screened-pass row, all quotes/pointers/value tokens, and rereads dependency hashes. All checks must pass before a public candidate is written. No partial entry is silently accepted. The private validation receipt binds the exact public bytes and checked dependencies.

```text
python tools/preliminary/preliminary.py project PRIVATE/candidate.json --evidence-dir PRIVATE/evidence --output PRIVATE/validated-public.json --receipt PRIVATE/validation.private.json
python tools/preliminary/preliminary.py merge recipe-atlas/static/data/preliminary-synthesis.json --candidate PRIVATE/validated-public.json --validation PRIVATE/validation.private.json --output PRIVATE/next-catalog.json
python tools/preliminary/preliminary.py validate-public PRIVATE/next-catalog.json
```

Repeat `--candidate` and `--validation` in matching order to merge a batch. The merger checks exact candidate/dependency hashes, rejects duplicate primary DOI/source IDs, preserves existing entries semantically and in order, and writes to a new path. It does not modify the source checkout, deploy, count gold papers, or credit a publication. Root reviews and applies the catalog through the normal single batch build/CI/privacy/publication gates. New-paper credit also excludes any DOI already published in another lane; this repository-wide accounting belongs to the integrator, not this isolated catalog merger.

## Private companion and page map

Paths below are placeholders for private local files. Hashes are SHA256 of exact bytes. The screened-pass line is an actual one-based JSONL line with `decision: pass` and matching `source_sha256`; it is never created by this tool.

```json
{"schema":"mattersyn-preliminary-evidence/1","source_id":"prelim-<16hex>","document":{"path":"source.pdf","sha256":"<64hex>"},"screened_pass":{"path":"existing-pass.jsonl","sha256":"<64hex>","line_number":1},"identity":{"doi":"10.xxxx/actual-doi","title":"Actual title","checked":true},"page_map":{"path":"pages.private.json","sha256":"<64hex>"},"claims":[{"pointer":"/precursors/0/amount","page":1,"quote":"A short exact source span with 1 g","value_tokens":["1","g"],"semantic_link_checked":true}]}
```

```json
{"schema":"mattersyn-preliminary-page-map/1","document_sha256":"<64hex>","source_pages":1,"pages":[{"page":1,"text":"Actual full extracted text of inspected page 1"}]}
```

The claim list above is intentionally incomplete as a shape example; the validator requires every scientific pointer. A public amount of `1 g` cannot be supported by a quote containing only `10 g`, and converted units cannot be smuggled through as literal source values. The validator checks adjacent literal number–unit spans (including M/mM, ranges, inequalities and simple compound units); unsupported unit associations are held. Long source-body copies are rejected in all public fields except title/DOI/citation metadata. Unit aliases, OCR corrections and semantic/sample ambiguity need explicit author correction or a hold, not quota-driven filling.

The DOI field uses a complete, case-insensitive literal identifier match against
its exact source quote. Letters inside a DOI are not measurement units; this
metadata rule does not change scientific quantity checks.

## Tests and practical limits

Run `python -m unittest discover -s tools/preliminary -p 'test_*.py'`. Pure schema/anchor tests use the standard library. Three additional synthetic real-PDF checks run when local pypdf is installed and otherwise are explicitly skipped; they grant no source or publication credit. No dependency is downloaded. The public build imports only `preliminary_contract`.

This tooling intentionally does not generate custom figures, molecules, coordinates, audit approvals, or per-paper release scripts. Source interpretation, unresolved sample links and visual evidence still require the extractor's judgment; an independent audit remains deferred and labelled pending.
