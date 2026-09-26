# MatterSyn frozen-package importer (Thomson Bi2S3 fixture)

## Shared new-paper preflight

`preflight.py` is source-independent and checks an isolated additive candidate against a base checkout before the full build. The older `importer.py` remains the exact Thomson fixture described below; this new checker does not silently generalize its mutation rules.

```powershell
python -B tools/package-importer/preflight.py --candidate <private-candidate> --base <base-checkout> --new-records <private-record-id-array.json> --report <private-receipt.json>
```

The record-ID file is a JSON array. The receipt must be outside both checkouts. The command is read-only apart from that receipt and makes no network calls. It verifies the declared additive record set and preserves prior record bytes; checks schema, required collection/review status, exact reagent and process-state namespaces, registry IDs and record hashes; checks Reader views, source hashes, route-only hub membership and sample IDs; and validates document scope, page coverage and characterization links in both inventory formats. It returns nonzero with a consolidated error list. It does not infer missing scientific fields or approve source reading, image rights, eligibility changes, a full build, browser rendering or publication.

Run `python -B -m unittest discover -s tools/package-importer/tests` from the repository root. The new regression tests cover the missing-collection, state/reagent mixing, stale-hash, wrong Reader-item, cross-paper and observation-as-route failures found during actual integration. The source-independent checker has passed a real 13-record candidate against 865 unchanged prior records; this is not an end-to-end throughput result.

This prototype, operated entirely on local files, turns one independently reviewed paper package into a deterministic, hash-pinned repository overlay. It never applies files to the checkout, starts a website build, publishes, or marks a record training-eligible. The Thomson fixture is intentionally narrow: one new material hub, one source group, one source-reviewed synthesis route, a main-only paper review, 12 source figure/table crops, two authored apparatus diagrams, two authored molecular identities, one stock context, and exact dual-delivery rights rows.

The importer verifies the frozen package inventory, source PDF and audit receipts; exact reviewed record and final Reader review bytes; target Git commit and every touched base-file hash; DOI/record/material/registry/path collisions; schema and route DAG; source-review scope; the two specifically reviewed operational release-policy additions; chemical and stock bindings; source and site image rights; and protocol-router registration. The canonical record and review are copied byte-for-byte. Aggregates are additive proposals produced against the exact base hashes. Scientific input and evidence files are not rewritten.

## Run the fixture

Use a Python runtime that has the repository's `jsonschema` dependencies. The local tested runtime was Python 3.13 in the `ptyrad` environment.

```powershell
python importer.py `
  --checkout <clean-or-reviewed-mattersyn-checkout> `
  --package <private-frozen-package> `
  --evidence-root <private-source-review-root> `
  --source-pdf <local-main-pdf> `
  --output-root <existing-private-staging-directory> `
  --stage-name thomson2010-bi2s3-r1
```

Omit `--stage` for a read-only preflight. Add `--stage` only to create a new child directory below the explicit private output root. Existing output directories are rejected. Use a new stage name for every run; do not overwrite an earlier stage.

The stage separates `repo/` from `control/`. Only `repo/` contains candidate repository files. `control/` contains private merge plans, source-to-field maps, rights deltas, dependency receipts, and review sidecars; do not copy it into either repository. The plan uses `create_only` or exact-base `replace_if_exact_base_sha256` operations. The target checkout is input-only. `sys.dont_write_bytecode` is set before its Python modules are imported.

## After staging

The repository owner must inspect the exact overlay and apply it to an isolated checkout only if each base hash still matches. Then run the repository's schema, dataset, atlas, Reader, inventory, release-gate, build, and browser checks. The target Bi2S3 hub's generated input digest and any release-path rules are downstream build outputs and are not invented here. A passing importer preflight is not a source re-audit, publication approval, legal rights determination, or post-import site QA.

The frozen Thomson package has a reviewed main article but no verified SI. Its current status is main-only; the SI remains unverified, and the record has no exact coordinate-to-recipe assignment or training eligibility. Source figures have user-directed display provenance while publisher permission remains unverified.

## Tests

```powershell
python -B -X utf8 -m unittest discover -s tests -v
```

The tests cover path traversal, duplicate figure de-duplication, protocol-router registration, stale chemical hashes, create-only behavior, bundle tampering, private-stage integrity, and synthetic frozen-stage manifest verification. The historical full-package integration fixture remains local and is not required by the public unit tests.

This is a first-source fixture, not a universal importer. It deliberately rejects an existing Bi2S3 material hub rather than trying to merge routes into one; a later importer revision must add separately tested append-to-existing-hub behavior before handling that case.

## Current limits

The first integration exposed two checks that this preflight did not cover: text-only source notes in the review builder, and measurement IDs incorrectly used as Reader-card IDs. The shared builder and Reader bindings were corrected through separate integration review. Full material-ID coverage also remains a mandatory downstream check, including formula cards for non-molecular materials. The importer does not replace those gates or establish end-to-end throughput. The supplied contract is a historical, exact-base fixture; it intentionally rejects a later checkout. Generalized multi-paper and existing-hub support is future work.

## Declarative additive importer

Use [merger.py](merger.py) with the source-independent contract described in [MERGER.md](MERGER.md) to stage new files, object keys and unique list entries. It preserves prior items and rejects conflicting identities, stale hashes and unsafe paths. It stages a private overlay and does not apply it or grant scientific/publication approval. Rights registries remain separately reviewed.
