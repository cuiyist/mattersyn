# Scoped gold packages and event-derived workflow metrics

This kit implements the local package contract, scientific diff, evidence-ranked
screened queue and idempotent publication metrics proposed in the September 26
scaling plan. It does **not** import, approve, merge, create GitHub issues/PRs,
publish, call a model or make network requests. The existing root integration
owner, additive merger, preflight, source checks and release gates remain in force.

## One scientific package, one independent audit

A package is `papers/<package_id>/package.json` plus exactly declared record,
binding and asset files. `package.schema.json` defines
the structure; `package_workflow.py validate` adds scientific cross-reference,
byte-integrity and the current canonical-schema checks. Canonical record bytes
are never rewritten by this kit. The canonical validator is imported from the
explicit current source checkout, not copied into a stale second schema.

The primary source and every document have separate IDs. Main and SI are separate
documents; an SI-only package is valid. A DOI-like filename is not verified paper
identity. `scope.unit`, each document's reviewed pages and exclusions, and scope
omissions describe the actual review. A main-only package must not claim that its
SI or entire paper was completely reviewed.

Each record needs exact field locators within the explicitly reviewed source
pages. Textual facts require a private quote-check receipt; nontext facts require
their existing independent visual/source-check receipt. Quotes, PDFs, raw text,
renders and full private audits remain outside the package. Machine validation
checks the supplied metadata; it does not manufacture or independently verify
an auditor's claim. Existing private source/quote checks remain mandatory.

The fixed scientific checklist is:

1. Document and minimum-publishable scope are accurate, including omissions.
2. All recipes and parameter/sample variants inside that scope are represented.
3. Quantities, units, temperature, duration, atmosphere and conditions match.
4. Chemical identities and precursor/stock bindings match the source.
5. Recipe-to-sample, structural and property assignments have actual evidence.
6. Conflicts, uncertainty, missingness and reference-vs-measured distinctions remain.
7. Field/figure/table/page locators resolve to the checked evidence.
8. Scientific asset provenance and figure/sample assignments are exact.

The independent auditor supplies the accepted audit, its receipt ID, and the
scientific fingerprint. The script never sets audit acceptance. The auditor ID
must differ from the author. Each checklist item is `passed` or an explicit
`not_applicable: <reason>`. A follow-up scientific-diff audit names the previously
accepted scientific hash and supplies that accepted base package for verification.

The scientific fingerprint includes the paper's own record facts, uncertainties,
sample links, field locators, document coverage, asset hashes/provenance and
reagent bindings. It excludes only four explicit canonical bookkeeping paths
(`/revision`, `/updated_at`, `/quality/reviewed_at`, `/quality/reviewer`), package
screen/quote receipt IDs and the audit itself.
Collection, review status, requested training tasks and source review/reuse claims
remain bound because they can change the meaning or scope of the contribution.
Thus changing another paper's hub counts or a bookkeeping receipt does not force
this paper through another source audit. Scientific conditions, missingness,
sample links, source document bytes and original figure changes do.

`presentation.state` is separate. Accepted main-text science can be `pending`
for molecules, additional cells or morphology artwork and enter the existing
integration gates. Neither structural validation nor presentation completion is
publication approval. Reader/browser checks still protect display correctness.
`derived_files` is reserved and **must be empty**. Build outputs are generated
outside the scientific input package; a self-declared `derived_from_science`
flag cannot bypass scientific review. Authored assets in the input package must
be listed with provenance and their exact bytes remain in the science hash.

```powershell
python -B package_workflow.py validate <package>/package.json `
  --checkout <source-checkout> --output <private-new-validation-receipt.json>
python -B package_workflow.py diff <old>/package.json <new>/package.json `
  --output <private-new-diff.json>
```

For a scientific-diff audit, add `--base-package <old>/package.json` to validation.
Successful draft validation is allowed before audit, but the receipt explicitly
sets `scientific_package_ready_for_existing_integration_gates: false`. Even an
accepted package sets `publication_authorized: false`.

Next integration step: map accepted package files into the existing declarative
`tools/package-importer/merger.py` create-only/additive contract, run `preflight.py`
on the isolated candidate and retain current boundary/build/browser gates. Do not
replace canonical data with an untested new writer. PR/CI automation can call this
same validation function later without changing the scientific contract.

## Rank the existing screened pass set

```powershell
python -B package_workflow.py identity-map <source>/recipe-atlas/data/paper-reviews `
  --output <private-identities.json> --report <private-identity-report.json>
python -B package_workflow.py rank <screened_papers>/accepted-manifest.jsonl `
  --identities <private-identities.json> --output <private-ranked-queue.json>
```

The adapter reuses only explicit `source_review_promoted: true` plus existing
document-identity receipts and actual document hashes. Conflicting identities are
withheld. Main/SI grouping is optional and never a dispatch prerequisite. Known
primary sources group together; unresolved documents remain distinct document
units. An optional `--live-sources` JSON array may exclude sources **only after**
their live publication was independently verified.

Priority uses existing preparation and structure locators/summaries. Verified
main documents get a small priority preference. Explicit screening audit flags
lower priority slightly. Family grouping occurs within evidence-score bands;
the material label from screening remains explicitly unnormalized. This does not
assert complete recipes, sample correspondence, calibrated popularity bands or
training eligibility. Normalized family identities and exact completeness must
come from separate checked evidence. No new paper or PDF is opened by ranking.

The real pass manifest contains 5,587 file rows / **5,539 unique document hashes**.
The first run removed 48 duplicate copies and ranked those documents in under one
second on the current machine. This is a queue operation, not extraction speed.

### Quantum-dot / colloidal scope (workflow v5)

Add `--scope quantum-dot` to `rank`. Each unit is classified from the screen's own wording
(material label, preparation and structure summaries): colloidal/QD wording or a QD composition
is **in**; bulk, thin-film, CVD, ceramic, sintering, glass or melt wording without colloidal
wording is **out** and excluded (`excluded.outside_quantum_dot_scope`). Mixed or missing wording
is kept with `scope_check_required: true` and ranked after all in-scope units. No paper is opened.

### Deep-audit sample (workflow v5)

```powershell
python -B package_workflow.py audit-sample <pkg>/package.json --output <private-sample.json>
```

After extraction is frozen, the package's scientific fingerprint selects about 10% of papers
for a full deep audit: `int(scientific_sha256[:8], 16) % 100 < 10`. The selection is reproducible
and cannot be chosen without changing the science. Every paper still gets the quick audit.

## Metrics from a complete local PR-event ledger

Append observed events to a private JSONL ledger. Each event needs `event_id`,
timezone-aware `at`, `stage`, `package_id` and optional `pull_request`. Supported
stages distinguish claim, extraction, independent audit, changes requested,
integration, merge, deploy, anonymous live verification, errors and blocks.
Do not synthesize historical stage events from current record counts.

A `live_verified` event additionally requires a verified primary source ID,
`tier` (`gold`/`silver`), source commit, HTTPS URL, record IDs and an actual anonymous
verification receipt SHA-256 with `anonymous: true` and `passed: true`. A merge
or successful build alone earns no live paper credit.

```powershell
python -B package_workflow.py metrics <private-complete-event-history.jsonl> `
  --start 2026-09-26T00:00:00Z --end 2026-09-27T00:00:00Z `
  --output <private-new-daily-metrics.json>
```

The interval is `[start, end)`. Supply the **complete prior ledger**, not only the
current day, to deduplicate earlier publications. Identical event retries are
idempotent; conflicting event IDs fail. One PR maps to one package. Multiple
records/variants count as one source paper. Re-publications and silver-to-gold
promotions are not new distinct papers; each tier's contributions are reported
separately. Stage event counts and latest package-state counts remain separate.
Elapsed throughput uses the actual requested interval; active work or continuous
background execution is never inferred. Outputs are create-only receipts.

`accepted_live_event_ids` shows all properly verified events in the interval,
including corrections that contribute zero new paper credit. The caller must
validate event provenance against the actual PR/CI/deployment receipts; this kit
validates the ledger contract rather than contacting GitHub.

## Verification

```powershell
python -B build_schema.py
python -B -m unittest discover -s tests -v
```

Tests are synthetic and labeled as such. They cover science-vs-metadata changes,
pending presentation, accepted-audit independence, main/SI scope, path and hash
failures, exact source locators, duplicate copy/source handling, distinct-paper
counting, late/duplicate/unverified events and gold/silver promotions. A separate
read-only ranking receipt uses the actual current screened-pass manifest.

No new paper was extracted, audited, made training-ready or published by this kit.
