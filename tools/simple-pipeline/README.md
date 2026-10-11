# Local simple pipeline for ordinary MatterSyn pages

This package implements the owner's October 10 evening job. It extracts main-text
synthesis–structure pairs in two local-model passes, keeps automatically checked
values, and prepares ordinary Reader records with status `source_extracted`.
These records have not received an independent scientific audit. Agreement and
quote matching do not establish accuracy, review status or training eligibility.
The audited lane and its questions remain paused. This package neither resets
that lane's ledger nor changes its sampling, calibration or stop rules.

Use Python 3.11 or later, the project's existing Python environment and the
dependencies in `requirements.txt`. The extraction script is otherwise standard
library Python. The converter and summary also use the schema and route functions
from the current MatterSyn checkout. The installed location is
`tools/simple-pipeline/`. `PROMPT.md` is the extraction prompt. No worker prompt
or inherited speed/accuracy claim is part of this package.

## Local extraction and checking

Use the local Qwen3-32B Q4_K_M server with 32,768-token context and thinking disabled,
as configured for this job. The script requests JSON-object output and validates
converted records against the canonical schema. Its OpenAI-compatible
address is `http://127.0.0.1:8080/v1`. No source processing uses an outside model.
Do not use `--allow-remote` or single-pass generation in this workflow.

Take the next existing screened, locally available primary PDFs whose DOI is not
on the site. Do not run new reading-based screening before extraction. The first
batch has 20 papers; subsequent batches have about 50. Expand globs in PowerShell
before invoking Python; `*.pdf` is not expanded by Python's argument parser:

```powershell
$batchPdfs = @(Get-ChildItem -LiteralPath $pdfFolder -Filter *.pdf | ForEach-Object FullName)
python mattersyn_simple.py extract @batchPdfs --out $privateWork --model qwen3-32b
python mattersyn_simple.py figures @batchPdfs --out $privateWork --model qwen3-32b
python mattersyn_simple.py check $privateWork --out $privatePairs
```

The three value checks stay intact: the quote is found in the paper, the number
is in the quote, and the two extraction passes agree. Text lookup tolerates PDF
spacing and typography; it is not an independent reading of the source.
`check` excludes a paper unless both pass files are successful. If a pass fails,
retry that paper once with `extract <PDF> --redo`; leave it out if it fails again.
A pair with no usable preparation is omitted. Parser, file and identity errors
are technical failures, not evidence that a paper lacks synthesis.

For the same 15 development papers only, `score` compares retained values with
the existing record collection. It does not certify calibration or authorize
held-out runs. No measured speed, precision or release count is implied here.

## Post-check metadata and rare-material reading

```powershell
python summarize_batch.py $privatePairs --repo $sourceRepo --site $siteRepo --out $safeSummary
```

The summary reports primary-DOI duplicates within the batch and against the
supplied site checkout, protected source identities, eligible ordinary routes,
figure-file counts and materials with fewer than three existing site routes.
It reads private pairs but exports no quotes, captions, fact values or private
paths. A checkout baseline is not proof of anonymous live deployment.

Five-field completeness is reported separately: composition, a quantified metal
or anion precursor, nucleation/growth temperature, nucleation/growth time and a
named product statement. These are checked-pair presence flags, not scientific
acceptance. The simple job does not reuse the earlier machine admission checks.
Its ordinary-page counter eligibility follows the current canonical route
predicate and schema, not this optional completeness metric. Missing unit cell,
morphology or other optional fields alone is not a skip. Chemical-only and
workup-only records are not ordinary synthesis routes. Top-level reaction
temperature/time are retained as source-located product notes when no individual
step reports them; the converter never invents a step assignment.

Read rare-material pairs against their source once, using one reader, and remove
wrong values. Common-material papers do not receive this additional reading.
If the batch is otherwise ready, the owner permits rare-material corrections in
the next batch. `records --replace` and `sync` protect audited records and reject
different source/DOI/record identities; only the same `source_extracted` identity
can be replaced. Scope each replacement to that paper's private pairs folder.

## Prepare a regular-page batch

```powershell
python to_site.py records $privatePairs --repo $sourceRepo
# Run the existing first build to supply its exact material-page route inventory.
python to_site.py sync $privatePairs --repo $sourceRepo --dist $firstBuildDist
```

Conversion requires the exact successful two-pass `check` marker. It preserves
page locators and missingness; the default holds optical-property conversion
back. It registers chemical bindings, uses a name card for unresolved chemical
identity, and creates conceptual action diagrams without asserting unreported
apparatus. A vessel reported at recipe level is labelled as recipe-level context,
not assigned to any individual step, including workup. Long vessel labels wrap
within the diagram, while the full reported value stays in its authored caption.
Cropped figures retain printed figure/page/DOI, exact checksum and
available PDF/crop/render metadata. Public captions are authored locator/category
descriptions; private original captions stay local. Figure and sample assignments
must not be inferred from a crop alone.

Use `register_batch_assets.py` after sync. It defaults to a dry run and verifies
the existing registry pin before adding only exact new asset rows/path rules.
It preserves old rows/rules and records user-directed display with publisher
permission not established. It does not create scientific audit approval.

```powershell
python register_batch_assets.py --repo $sourceRepo --record-id <record-id> --recorded-at <actual-UTC-time> --direction-id owner-simple-website-20261010-evening --reviewer <actual-registration-reviewer>
# Add one --record-id argument per new record. Inspect the dry-run result, then
# repeat the same invocation with --apply to bind the verified new assets.
```

The project release guard must support the narrowly scoped `source_extracted`
crop provenance. It still checks every exact asset hash, delivery path and
permission state. An existing denial or mismatched hash fails registration.
Do not change a permission fact or audited record to pass a check.

Regenerate project file lists and allowlists through the normal tools, run the
complete build, source checks and local visual checks, and fix any waiting-batch
display defect first. Source preparation is documented in
[`../publication/SINGLE_COMMIT_RELEASE.md`](../publication/SINGLE_COMMIT_RELEASE.md);
the build path is documented in
[`../../recipe-atlas/README.md`](../../recipe-atlas/README.md). These tools do not
replace exact-source CI, browser review, boundary gates, deployment or anonymous
verification. Use one ordinary batch merge for each release so it can be reverted.
The root integrator alone mutates shared repositories and publishes.

For batch 1, inspect three new pages at desktop and phone widths; inspect one page
in later batches. Ship working figures, diagrams and supported unit-cell displays
with the batch. A conceptual or composition-reference cell must retain its label.
No hidden or broken display is released. While a batch builds and deploys, the
local model may extract the next disjoint batch.

Only newly deployed, anonymously verified primary-paper contributions increase
the homepage count; variants count as records, not additional papers. Audited and
machine-extracted statuses remain separate. Failures, skipped papers and private
pairs do not increase the public counter. Automatic-approval refusals are left
out and reported, never bypassed.

## Public and private storage

```powershell
python mattersyn_simple.py build $privatePairs --out $temporaryExport
```

Take only the resulting **no-quote `pairs.json`** for the public batch archive.
Do not pass `--quotes`, and do not publish the standalone preview as a preliminary
collection. Public export recursively removes quote keys, drops private metadata
and replaces original figure captions with authored descriptions. Original PDFs,
page text, pass files and quoted pair files remain private and unchanged.

Push canonical records, registered crops, diagrams, no-quote pairs and the single
safe job report with the batch. Update `research-assets/curation-control.json`.
Report actual deployment counts, omissions/reasons, rare-material deletions,
script fixes, choices and built-site bytes. Do not claim a publication rate from
an extraction count. Reconstructible local build/candidate copies may be removed
only under the owner's storage instructions after their deployment is verified.
Private text/pass/pair files are retained for training. This package deletes none.

## Focused regression tests

```powershell
python -B tools/simple-pipeline/check_simple_pipeline.py
```

Tests use synthetic facts/crops/registries. They cover public-export privacy,
original-record protection, two-pass conversion, crop metadata, exact asset
registration and metadata-only summaries. They do not read research PDFs, query a
model or establish extraction accuracy. The asset-registration integration test
locates the current release guard beside this installed package.
The aggregate runner fails on a failed, empty or skipped suite. It can save a
metadata-only result using `--report`; it adds no model admission or audit rule.
