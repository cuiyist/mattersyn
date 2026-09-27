# MatterSyn local silver calibration kit

This is a working, standard-library-only **private preparation tool**, not a deployment pipeline or an independently audited dataset. It never launches a model, opens a network connection, downloads a paper, modifies gold records, or publishes a website. The root integrator owns those separate actions. Two separately produced machine drafts are not an independent scientific audit.

The owner confirmed the proposed precision thresholds on September 26, 2026: high 98%, medium 95%, low 90%. The kit requires a frozen family-popularity assignment and exact pipeline configuration fingerprint. Those thresholds do not by themselves establish achieved accuracy or authorize publication of uncalibrated outputs.

## Files and commands

`silver.py` is the library and CLI; `test_silver.py` contains synthetic regression tests. `extraction-prompt.txt` and `draft-example.json` describe the restricted draft interface. Examples are synthetic, not research evidence.

`local_runner.py` is a separate development-only loopback Ollama client for the
already installed, digest-pinned 9B/27B models. It never pulls a model and rejects
redirects, proxies, non-GGUF models and private output paths inside Git checkouts.
Select explicit page chunks; run pass A and B separately. Its pipeline identity
binds model digests, the prompt, validator, runner bytes and generation options.
Every run is labelled development, not heldout calibration. Construct and freeze
the source-separated calibration set before extending the runner to that mode.
The API contract follows the [Ollama chat documentation](https://docs.ollama.com/api/chat).

```powershell
python -B -m unittest -v test_silver.py
python -B silver.py reconcile --pages pages.json --draft-a a.json --draft-b b.json --policy policy.json --chemistry chemistry.json --out private-reconciliation.json
python -B silver.py calibrate --truth frozen-reviewed-holdout.json --predictions reconciliations.json --policy policy.json --out calibration.json
python -B silver.py project --input private-reconciliation.json --pages pages.json --calibration calibration.json --policy policy.json --approval separate-calibration-review.json --out public-candidate.json
```

All input/output documents in those commands are **local private artifacts**. `--chemistry` and `--approval` are optional: unresolved chemical identity is withheld without the former, and no values are admitted without the latter. The calibration CLI returns exit code 2 on STOP. Projection is only a whitelisted candidate export: its `publication_enabled` is always false. Existing public release gates must separately inspect/admit/deploy it. No automatic source-paper credit is awarded.

## Input contracts

The page map is `{"documents":{"main":{"source_id":"paper-id","pages":{"1":"local PDF page text"}}}}`. Page numbers are one-based PDF pages, not inferred printed-page numbers. Multiple documents may share a canonical primary paper-group ID, but different papers must not. Main text and SI may still be processed separately; the canonical group prevents counting them twice as distinct published papers.

Policy schema:

```json
{
  "schema":"mattersyn-silver/0.1/policy",
  "pipeline_id":"local-qwen-v1",
  "pipeline_sha256":"64 hex characters: exact models, prompt templates, validator and runner configuration",
  "thresholds_confirmed":true,
  "thresholds":{"high":0.98,"medium":0.95,"low":0.90},
  "confidence":0.95,
  "family_bands":{"cdse":"high","example-rare-family":"low"},
  "family_count_snapshot_sha256":"64 hex characters: frozen screened-pass source-count snapshot"
}
```

The literal descriptions above must be replaced with actual hashes. Family bands are a release input; this kit does not infer popularity from a model's output. The private ranked queue must establish them from grouped screened-pass source counts.

Drafts follow `draft-example.json`. Required provenance includes source/family ID, local runner, distinct pass ID, no access to the other pass, actual model and prompt hashes, and matching pipeline hash. A second model or changed seed alone is not proof of independence. The runner must enforce isolation. Gold/audit claims are never accepted from model metadata.

Recipe IDs and non-null sample IDs must be literal source labels. Recipe-level precursor amounts, solvent volumes, concentrations, reaction temperatures and durations may have `sample_id:null`. Structural outcomes require a non-null product/sample label and an exact source span containing the recipe and sample labels. Co-occurrence is a necessary mechanical check, **not proof that the source asserts the relationship**; independent heldout truth must test semantic correctness. Ambiguous or unlabelled links remain unextracted in this conservative pilot.

Each claim's `slot_id` identifies its experimental entity/context, not an arbitrary array position. The two independent drafts must use the same source-derived recipe/sample/slot identities for agreement. Unicode/case/punctuation formatting is normalized in slot IDs (for example `iron(III) acetate-amount` and `iron-iii-acetate-amount`); words, numbers and oxidation-state text are preserved. There is no fuzzy chemical alias matching. Collisions and conflicting repeated claims remain as private alternatives and cannot become an agreed field. Remaining spelling differences cause missingness rather than an invented join.

`chemistry.json` maps established registry IDs to source aliases: `{"known-id":{"source_aliases":["exact source name"]}}`. It is a curated identity cache, not a PubChem query. No chemical identity or atomic structure is inferred from a formula alone.

## What is validated

- Contiguous verbatim evidence on the **cited page and source document**, allowing Unicode normalization, whitespace collapse and PDF line-end hyphenation. Case is retained because units can be case-sensitive.
- Scalar numeric spelling and the adjacent source value/unit pair, preventing an unrelated number elsewhere in a quote from becoming a duration. `value_text` may lexically contain just the scalar or that scalar followed by the exact already-declared unit; this does not permit ranges or a different unit. Original units are retained for publication. Unit normalization is used only for draft equivalence and numerical consistency.
- Positive quantities and broad physical checks; no temperatures below absolute zero. Unsupported units, ranges, approximate values, nested quantities and unknown fields stop that field rather than being repaired.
- DLS hydrodynamic diameter is not particle/core diameter; XRD crystallite size is separate; absorption-derived sizes are not accepted. Phase and morphology need an explicitly named supported characterization technique in the quote or an additional exact `technique_quote`/`technique_page` span.
- Core diameter + twice shell thickness must agree with particle diameter within 5% when all three are supplied for one sample. This is a conservative consistency screen, not evidence of ideal spherical geometry; complex cases remain gold work.
- Explicit recipe/sample text anchors, chemical registry resolution, separate pass provenance and full pipeline/policy bindings.

These checks do **not** establish semantic entailment, exhaustive extraction, correct measurement interpretation, correct phase assignments or actual specimen identity. The heldout scientific audit is the source of those labels. Text-only silver does not read figure pixels or promote website illustrations to measured data.

Current deliberate limits: scalar numeric fields only; no ranges/approximations, procedural graph inference, free-form sample co-reference resolution, figure/table reconstruction, morphology image interpretation, SI completeness claim, complex reagent preparation or implicit conversion. Retain unsupported cases privately and route them to gold. The pilot cannot justify a 500-paper/day claim from model-token speed or a short page run.

## Reconciliation and training

Both passes must provide the same field, context and canonically equivalent value, with every validator passing, to reach `agreed`. Invalid evidence is withheld. High-band disagreements are withheld; medium/low disagreements retain private alternatives and may project only a labeled `uncertain` state with **null value, zero training weight and masking** after field calibration. The kit does not silently choose one alternative. All quotes and rejected alternatives remain private.

Public projection validates the reconciled schema, family/band, bounded public IDs, row/alternative key agreement, two-pass counts, agreement and mask states. Before admitting values it revalidates both alternatives against the original hash-bound private page map. It uses an explicit allowlist of public keys: values, units, qualified state and page locators. It omits source quotes, link quotes, local paths, draft text and private audit details. Accepted training weights use the smaller of the instance and source-cluster bounds as a conservative noise weight; weights are not per-example probabilities. Silver is excluded from gold evaluation. `count_sources` deduplicates primary source IDs, not records or field counts; it is candidate inventory only. The release ledger must separately prove deployment and anonymous access before a source contributes to public throughput.

## Heldout calibration and the stop rule

`frozen-reviewed-holdout.json` contains:

```json
{
  "schema":"mattersyn-silver/0.1/gold-holdout",
  "pipeline_id":"local-qwen-v1",
  "gold_snapshot_sha256":"64 hex characters",
  "split":"heldout",
  "frozen_before_extraction":true,
  "independent_scientific_audit":true,
  "auditor_id":"independent-reviewer",
  "extractor_id":"author",
  "heldout_source_ids":["paper-id"],
  "training_source_ids":[],
  "selection_source_ids":[],
  "records":[{"source_id":"paper-id","band":"high","recipe_id":"Method A","sample_id":null,"slot_id":"growth-temperature","field":"reaction_temperature","value":270,"unit":"°C"}]
}
```

The truth inventory must contain **all in-scope expected field instances**, not just values emitted by the model. An absent truth key is scored as a false positive; missed truth keys are false negatives. Freeze labels, source universe and development/selection exclusions before running final calibration. Existing Tirosh development runs and other tuned examples are **not heldout**. Gold inputs are read-only; the scorer never writes them. The caller must verify the snapshot hash and independent audit receipts against immutable gold artifacts. A JSON `independent_scientific_audit:true` flag is an assertion to audit, not cryptographic proof.

Each field × popularity band has separate precision, recall, false positives/negatives, sample size and **exact one-sided 95% Clopper–Pearson lower precision bound on field instances**. Following the adopted plan, this field-instance bound is the admission statistic and assumes IID instances. It is **not a dependence-adjusted confidence guarantee**. A second, conservative source-cluster sensitivity bound treats an entire paper as failed for that field if any accepted instance is wrong. It is reported separately with the number of distinct sources and a dependence warning, rather than silently imposing a 149-paper requirement.

With zero errors, the field-instance interval requires at least **149 high-band, 59 medium-band or 29 low-band audited instances for each field**. Roughly 60 gold papers may provide enough instances for some fields, but coverage must be measured separately per field and band. Repeated variants or SI from the same paper can be correlated and must not be presented as independent source evidence. The independent calibration reviewer must assess the IID assumption, sampling design and source-cluster sensitivity before admitting a field. A numerical instance-bound pass alone is insufficient. Confidence bounds here are per field; they are not simultaneous family-wide guarantees.

Insufficient evidence yields `STOP`, never an automatic threshold relaxation. Even a numerical pass yields `INDEPENDENT_REVIEW_REQUIRED`. An independent reviewer must inspect the holdout selection, truth labels, pipeline fingerprint and scoring outputs before issuing an approval bound to the exact calibration digest. Required approval keys: `approved:true`, `calibration_sha256`, `reviewer_id`, `independent:true`, nonempty `extractor_ids` that excludes that reviewer, and `field_instance_iid_assumption_reviewed:true`. This flag records a real review, not permission to ignore dependence. All future model/prompt/validator changes require a new frozen configuration and recalibration.

For the daily random audit, select sources independently from the actual deployed silver population and prepare a separate immutable reviewed truth set. Run this same scorer on that set; a field's failing lower bound or observed error threshold violation suspends that field. The sampling schedule, audit sample construction, publication revocation and public accuracy page are integration responsibilities, **not implemented by this private kit**. Do not treat a small daily sample as enough to re-prove a 98% bound each day; use a predeclared cumulative monitoring window and report its sample size and dependence limits.

## Verification performed

Synthetic regression tests cover wrong-page quotes, paraphrases, K/°C mismatches, mismatched value/unit pairing, unsupported ranges, NaN, duplicate/conflicting alternatives, DLS/optical size leakage, unlinked samples, inconsistent core/shell dimensions, unknown chemicals, calibration leakage, source correlation, exact confidence endpoints, field-specific stop gates, immutable gold input and public projection masking. These are software tests, **not scientific calibration results**.
