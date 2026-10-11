# Simple pipeline website job

Owner instruction: October 10, 2026, evening. This report records only measured results. The audit lane stays paused; new contributions retain `source_extracted`. Source PDFs, full text, pass files and pair files with quotes remain local. Site records contain locators without quotes.

## Part A

Completed: both supplied patches and 27 COD reference cells are deployed. [Source PR #13](https://github.com/cuiyist/mattersyn/pull/13) merged as `8c2bdd4ec7fb2c3505b58408177b114453b53e7d`; the exact prepared source is `27bd172b177f6a6694072f6be3f0b2948eb551fb`. [Source CI 38109023795](https://github.com/cuiyist/mattersyn/actions/runs/38109023795) passed. Site commit `030073dfc70b254a0f0d60c62702a210301b073e` [deployed successfully](https://github.com/cuiyist/mattersyn-site/actions/runs/38109850772) at 2026-10-11 03:58:25 UTC. Anonymous verification passed at 04:05 UTC: 4,699 files checked, zero mismatches. The built site is 1,058,028,840 bytes. This engineering release adds **zero papers and zero records**. The mixed tetragonal/monoclinic display defect was fixed before release. The size contingency is not triggered: this deployment succeeded.

## Part B

Completed fresh extraction of the same 15 development main-text PDFs with Qwen3-32B Q4_K_M, 32,768 context and thinking off. All 30 passes succeeded. Extraction took 26.0253 wall-clock minutes. The current prompt is retained because 328 values were kept and zero passes failed; no prompt rerun was needed. No held-out papers were processed.

TOTAL printed by `check`:

```json
{
  "papers": 15,
  "values": 516,
  "kept": 328,
  "dropped: quote not in paper": 89,
  "  of which: partly found in the paper": 73,
  "  of which: wording nearly matches the paper": 14,
  "pairs": 21,
  "dropped: passes disagree": 77,
  "dropped: number not in quote": 16,
  "  of which: not found in the paper": 2,
  "dropped: no quote": 9,
  "pairs_dropped": 2
}
```

| Field | Extracted | Matched in audited records | Share |
| --- | ---: | ---: | ---: |
| composition | 14 | 14 | 100% |
| chemical name | 76 | 62 | 82% |
| chemical amount | 51 | 48 | 94% |
| temperature | 42 | 36 | 86% |
| time | 39 | 36 | 92% |
| size | 10 | 10 | 100% |
| optical peak | 14 | 8 | 57% |

These are DOI-level matches against recorded values, not an independent determination of product/step accuracy or calibration.

## Choices and fixes

- Recommended choice: keep optical fields out of converted website records; the converter default avoids the optical errors observed in the earlier test.
- Require two successful passes before production `check`; retry a failed pass pair once with `--redo`, then leave the paper out. Fixed the checker to reject missing, failed or malformed A/B passes and move stale outputs outside the converter input folder; 19 synthetic regressions pass.
- Fixed two default-cell defects: an unknown reported phase cannot be treated as missing, and conflicting qualifiers cannot admit an incompatible cell. Reported product phase takes precedence over intended target; manually bound cells are unchanged.
- Registered exact COD archive-comment exceptions for new supplied CIF paths and hashes; coordinate bytes and the existing comment validator are unchanged.
- Used the existing public-report path after the source boundary rejected a new unlisted report folder; no path rule was widened.
- Converter fixes: original figure captions remain local; published captions contain only figure/page/category locators. Separate model passes are not called an independent audit.
- Public export now recursively removes quote fields and private paths, and replaces source captions with locator captions; four synthetic regressions pass.
- Extended ordinary Reader, source coverage and release-route bindings for explicitly labelled source-extracted records. DOI/record/page/browser bindings and training exclusion remain required; audited route checks are unchanged.
- Fixed the browser-discovered mixed-phase selector: separate explicitly percentage-labelled phase clauses may select parallel references; compatible qualifiers remain conjunctive.
- No release check has been removed or switched off.

## Batches

No simple-pipeline paper batch has been deployed yet. Batch 1 selected 20 screened papers, with 18 supported identities and two unresolved identity holds. Extraction and one retry per failed paper took 52.9375 wall-clock minutes across 44 pass executions. Four papers remain excluded after the permitted retry: three persistent model/JSON failures and one malformed pair-entry failure. These are technical failures, not evidence that their sources lack synthesis.

`check` processed 18 papers, saw 587 values and retained 362 values in 24 pairs from 14 papers. Its three predicates remain unchanged. Conversion retains 13 papers, 20 route-eligible records and 65 figure crops. One paper and three additional pairs produced no ordinary synthesis route and remain private. Optional five-field completeness is reported separately and is not a new admission gate. All new records retain `source_extracted`; integration is pending publication and adds zero live paper credit so far.

The owner-authorized rare-material read is complete for five papers: four corrected, one unchanged. It made 27 deletion operations; no replacement facts were added. Originals and retained quote/check data remain local. This is a limited single-reader check, not an independent audit. The next 49 identity-supported papers are generating locally while this batch is prepared; two subsequent cohorts have metadata prepared. No common-material review or audited-lane work has resumed.

| Rare paper DOI | Deletion operations | Main correction scope |
| --- | ---: | --- |
| 10.1007/s00396-009-2037-9 | 8 | Product/step assignments, unsupported morphology and vessel identity |
| 10.1021/acs.chemmater.4c00011 | 4 | Ambient conditions used as vessel identity; zero-Rb variant inputs |
| 10.1002/smll.200600298 | 3 | Injection method and size assigned to the wrong component product |
| 10.1002/adfm.200600955 | 12 | Other host-matrix branch, core size assigned to a composite, temperature range reduced to a scalar; six numeric values removed |
| 10.1021/acs.chemmater.3c02503 | 0 | Retained fields unchanged after the scoped read |

| Paper left out | Reason |
| --- | --- |
| 10.1007/bf03218647 | DOI identity unresolved |
| 10.1007/s12034-007-0022-9 | DOI identity unresolved |
| 10.1002/adfm.200700683 | Persistent model/JSON failure after one retry |
| 10.1002/pssa.200824446 | Persistent output-length/JSON failure after one retry |
| 10.1021/acs.nanolett.8b00861 | Persistent output-length/JSON failure after one retry |
| 10.1007/s10904-009-9278-4 | Persistent malformed pair entry after one retry |
| 10.1016/j.cplett.2020.137454 | Checked output produced no ordinary synthesis operation |

Three other non-route pairs are retained privately rather than converted: DOI 10.1021/acs.chemmater.5c00408, 10.1021/acs.chemmater.9b03709 and 10.1021/acsami.1c06627. Each paper still has an eligible route in this batch. These omissions do not increase public totals.

## Current engineering and storage

- Refresh the connected Reader module/CSS cache versions to 0.41.4 and use the neutral loading label; no record values change.
- Use at most eight workers for independent anonymous file GET/hash probes; preserve every probe, mandatory route check, mismatch and deterministic result order.
- Register exact source-extracted crop/diagram paths and provenance, with user-directed display and permission not established; do not claim independent audit or publisher permission.
- Set production extraction response capacity to 10,240 tokens and retain payload-free JSON failure diagnostics; the prompt and three check predicates are unchanged.
- Public pair exports use a known-field projection, retain numeric values/page locators and figure provenance pins, and drop quote-bearing fields and private paths; six focused privacy regressions pass.
- Reject non-object pair entries explicitly instead of crashing the batch checker; continue with other papers and keep failed output private.
- Preserve variable stoichiometry and Unicode formula separators; do not interpret NC/QD abbreviations as chemical formulas. Five synthetic formula regressions pass.
- Split explicitly separated component formulas for parallel reference-cell display while retaining stoichiometric minus signs. Compound punctuation alone does not assert a core–shell architecture; reported architecture remains authoritative. Six synthetic component regressions pass.
- The complete installed simple-pipeline engineering suite passes 55 synthetic tests, with no skipped tests; this measures software behavior, not extraction accuracy.
- Use neutral published-material labels and keep the audited filter restricted to records actually reviewed; extracted records retain their separate label.
- Add PyMuPDF 1.28.2 to the build dependency lock for synthetic-PDF pipeline tests. CI uses generated fixtures and no source papers.
- Recommended choice: retain the current prompt and raise only production response capacity to 10,240 tokens after observed length-truncated JSON; keep the context, thinking setting and check predicates unchanged.

Cleanup removed 32 historical generated targets containing 70,339 files and 1,415,166,126 logical bytes only after exact public Git verification. Observed C-drive free space rose 1,610,690,560 bytes; that observation includes concurrent allocation. No papers, private evidence, current run or working checkouts were removed. No automatic approval rejection occurred. Private target paths remain local.
