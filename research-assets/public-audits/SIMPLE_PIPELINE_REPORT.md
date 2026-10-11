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

Historical preparation before the first verified simple-pipeline batch (publication results follow below): Batch 1 selected 20 screened papers, with 18 supported identities and two unresolved identity holds. Extraction and one retry per failed paper took 52.9375 wall-clock minutes across 44 pass executions. Four papers remain excluded after the permitted retry: three persistent model/JSON failures and one malformed pair-entry failure. These are technical failures, not evidence that their sources lack synthesis.

`check` processed 18 papers, saw 587 values and retained 362 values in 24 pairs from 14 papers. Its three predicates remain unchanged. Conversion retains 13 papers, 20 route-eligible records and 65 figure crops. One paper and three additional pairs produced no ordinary synthesis route and remain private. Optional five-field completeness is reported separately and is not a new admission gate. All new records retain `source_extracted`; at that preparation checkpoint, integration had no live publication credit.

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
- Fixed the dynamic Reader losing its extraction notice after replacing the initial page header. It now keeps “Machine extracted · Not independently audited” for canonical `source_extracted` records, including method changes. Unresolved extracted component defaults use neutral comparison titles; audited and explicitly assigned core/shell displays are unchanged.
- Extended the material-hub status check only to recognize extracted-only hubs. It derives the required status from canonical route records, rejects falsely reviewed extracted hubs, and retains all membership, privacy, figure and training checks. Three status regressions pass; the corrected check passes all 163,498 checks on the waiting candidate.
- Corrected the local Source export's Windows path prefix; the subsequent boundary check passed all 20,217 files. The malformed-path generated copy was moved outside the checkout, with no source data deleted.

Two additional verified public copies from Part A were removed: 42,975 files / 1,978,677,064 logical bytes. Observed free space increased 2,013,970,432 bytes, including concurrent allocation. Five uncertain cleanup targets were left intact. All papers, quoted training files, receipts and working checkouts were preserved.

Cleanup removed 32 historical generated targets containing 70,339 files and 1,415,166,126 logical bytes only after exact public Git verification. Observed C-drive free space rose 1,610,690,560 bytes; that observation includes concurrent allocation. No papers, private evidence, current run or working checkouts were removed. No automatic approval rejection occurred. Private target paths remain local.

## Verified simple-pipeline batches

### simple-batch01-20261011

Anonymous verification passed at 2026-10-11T06:06:36+00:00: 3,294 files, zero mismatches. [Source commit](https://github.com/cuiyist/mattersyn/commit/2bf52eb2931a3ff0eb508b605fe4a081250bf7b0) and [Site commit](https://github.com/cuiyist/mattersyn-site/commit/2a6d0edd2f9db48d3651608105e854f76aa920ce). This batch contains 13 source groups, 20 records and 65 source figure crops; 13 distinct newly contributing primary papers after DOI deduplication. Every new contribution remains machine extracted and not independently audited. The final built site is 1,084,521,926 bytes / 25,407 files.

Live counter: **244 audited + 13 machine extracted = 257 papers**, 3,005 canonical records, 252 direct material families, 289 material/component pages and 864 displayed recipe–structure pairs (6 more comprehensive; 858 partial). These display counts do not establish extraction accuracy, measured atomic coordinates or training eligibility.

Recorded source pr: [14](https://github.com/cuiyist/mattersyn/pull/14).

Recorded source ci run: [38114276173](https://github.com/cuiyist/mattersyn/actions/runs/38114276173).

Recorded pages run: [38116679526](https://github.com/cuiyist/mattersyn-site/actions/runs/38116679526).

| Primary DOI | Records | Figure crops | Public page |
| --- | ---: | ---: | --- |
| 10.1007/s00396-009-2037-9 | 2 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/chen2009-s00396-009-2037-9-cds-pmma-hybrids-1.html) |
| 10.1021/acs.chemmater.5c00408 | 2 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/das2025-acs-chemmater-5c00408-cspbbr3-rhombicuboctahedron-nanocrystals-1.html) |
| 10.1021/acsami.1c06627 | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/dong2021-acsami-1c06627-as-evaporated-cspbbr3-and-cs4pbbr6-embed-1.html) |
| 10.1021/acsami.0c20349 | 2 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/hu2021-acsami-0c20349-cspbbr3-cncs-1.html) |
| 10.1002/adfm.200600955 | 2 | 9 | [Open](https://cuiyist.github.io/mattersyn-site/records/jasieniak2007-adfm-200600955-cdsezns-qd-doped-tio2-waveguide-1.html) |
| 10.1006/jcis.2000.6894 | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/kho2000-jcis-2000-6894-zns-ncs-old-1-1.html) |
| 10.1021/acs.chemmater.4c00011 | 2 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/ko2024-acs-chemmater-4c00011-cs1xrbxpbbr3-ncs-with-0-rb-alloying-1.html) |
| 10.1007/s10971-006-9120-1 | 1 | 7 | [Open](https://cuiyist.github.io/mattersyn-site/records/leventis2006-s10971-006-9120-1-cds-quantum-dots-1.html) |
| 10.1007/s10853-006-7461-3 | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/murugan2006-s10853-006-7461-3-zns-nanoparticles-1.html) |
| 10.1021/acs.chemmater.3c02503 | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/rusch2023-acs-chemmater-3c02503-cspbbr3pbxbiysz-nc-heterostructures-1.html) |
| 10.1002/adma.200501523 | 2 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/torre2006-adma-200501523-cdtecnt-composites-1.html) |
| 10.1021/acs.chemmater.9b03709 | 1 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/wen2019-acs-chemmater-9b03709-cspbbr3-nanocrystals-1.html) |
| 10.1002/smll.200600298 | 2 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/xie2006-smll-200600298-znte-cdse-tetrapod-1.html) |

## Latest continuation checkpoint

At 2026-10-11T06:09:34+00:00, Batch01 is live and anonymously verified; Batch02 remains in local processing with 47/49 two-pass-complete papers at its last saved checkpoint. These are processing counts, not additional published papers. The audited lane stays paused.

Recommended choice: save this verified publication checkpoint on the next substantive batch branch now, then merge it with that batch; this keeps the GitHub record current without a status-only website deployment.

Additional Part A cleanup removed 12 verified rebuildable child targets: 85,754 files and 3,879,530,160 logical bytes. Observed free space increased 4,105,388,032 bytes, including concurrent allocation. Original papers, quoted training files, receipts, active batches and working checkouts were preserved.

## Simple-pipeline preparation checkpoints

### batch02

Preparation only: 36 retained papers, 68 ordinary route records and 252 available figure crops. This checkpoint adds zero live paper credit. Publication requires the normal release and passed anonymous verification. New records remain source extracted, not independently audited or training eligible.

Final extraction handoff: 48 successful two-pass papers.

Extraction wall-clock minutes: 118.4057. No publication-rate claim follows from this duration.

Identity holds: 10.1021/j100054a032.

| Paper left out | Metadata reason |
| --- | --- |
| 10.1021/ja805655b | invalid_or_failed_pass_after_one_redo |
| 10.1021/acsnano.5b01154 | no_route_eligible_record |
| 10.1021/am4038068 | no_route_eligible_record |
| 10.1021/am504057y | no_route_eligible_record |
| 10.1021/cm010291q | no_route_eligible_record |
| 10.1021/ja0173167 | no_usable_pairs |
| 10.1021/ja068351m | no_usable_pairs |
| 10.1021/ja103956p | no_usable_pairs |
| 10.1021/ja2029415 | no_route_eligible_record |
| 10.1021/ja206303g | no_usable_pairs |
| 10.1021/ja301285x | no_usable_pairs |
| 10.1021/ja308200f | no_route_eligible_record |
| 10.1021/ja410165f | no_route_eligible_record |

## Batch02 processing and changes

Preparation only; this batch has not yet added live papers. Selected 50 screened local papers: 49 confirmed identities, 48 successful two-pass papers after one permitted redo. Automatic check: 2,045 values considered, 1,249 retained and 91 checked pairs. Normal route conversion retains 36 papers, 68 records and 252 crops. Extraction took 118.4057 wall-clock minutes; figures and check took 2.7578 minutes. These are extraction measurements, not a published-paper rate.

The 15 rare-material papers received one scoped reading each. Corrected private copies removed 88 field/path entries (86 validated value objects reported by the readers), with no replacement facts. Wrong route/product/step bindings, component versus whole-product sizes/phases, unsupported vessel/method claims and incorrectly typed optical statements were removed. The automatic check totals above describe the original checked outputs; they do not claim post-reading accuracy. All 36 papers remain source extracted and excluded from reviewed/training-ready counts.

Choices and fixes:

- Keep the existing prompt: the fresh development run cleared the owner's threshold.
- Raise only future extraction response capacity from 10,240 to 12,288 tokens: saved failures reached the former output limit, and the measured representative input plus the new output reserve fits 32,768. The omitted Batch02 paper is not given another retry.
- Use two local paper workers: an actual load test found two 32,768-token slots fully on the RTX5090 through the installed Vulkan backend, with q8_0 K/V cache. Load-only peak was 28,800 MiB and minimum free memory 3,388 MiB. Changed cache precision can change outputs; no accuracy or throughput gain is claimed.
- Keep extraction A/B calls sequential within each paper and preserve the single-redo reservation across restart. Serial directory creation fixes a measured Windows snapshot-directory race without serializing model requests or weakening admission. Synthetic tests cover both contention and permanent technical holds.
- Preserve ISO timestamps as strings when loading private PowerShell JSON arguments; automatic date conversion had lost precision/format. The capacity helper also recognizes the recorded completed handoff and the actual RTX5090 Vulkan cache evidence, retaining exact PID, ownership, cache, context, full GPU and memory checks. Its first rejected load restored the original server. No automatic approval refusal occurred.
- Use an ordinary copied crop when the local filesystem refuses a hard link. Original quoted text, pass and pair files remain private and intact.

The quote-found, number-in-quote and both-passes-agree rules are unchanged. No audited record is rewritten. The public batch archive contains no quotes.

Additional verified cleanup after Batch01: removed 326 exact published copies (325 PNG copies and one quote-free archive copy), 123,482,315 logical bytes. A separate 8.00 GB whole-directory cleanup plan is only a proposal; no space is claimed freed from it yet.


## Batch02 complete-build correction

At 2026-10-11T07:18:39+00:00, the complete local candidate failed only three legacy Si assertions that assumed every contribution was reviewed. The narrow correction pins the original six reviewed Littau/Heath/Stiger routes and their exact DOI set, and keeps those component routes out of direct Si synthesis. New source-extracted routes still pass the existing canonical membership, status, source and paper-link checks. Sixteen focused regressions and all 166,133 checks on the existing candidate passed privately; fresh full Source/build/browser checks remain pending. No paper from Batch02 is claimed live and no old audited record is changed.

The complete local engineering suites reported 812 tests: 806 passed and six existing Windows environment skips, with zero final failures. The initial missing-library failure and initial complete-build failure remain saved. The first staging attempt exceeded the Windows command-line limit; normal NUL-separated exact path-list staging fixes that technical failure without broadening the payload.

Recommended choice: preserve the first failed attempt, bind this code-and-test fix normally in the same Batch02 branch, then run a fresh complete candidate and publish the batch. The 8.00 GB directory cleanup remains parked because its active-process guard found an unrelated process referencing an ancestor; no targets from that plan were deleted and no automatic approval refusal occurred.


At 2026-10-11T07:32:47+00:00, the fresh R2 candidate caught an encoding mistake introduced during Root's application of the Si patch: an unrelated Ag–Te literal had been garbled by the default Windows decoder. The original UTF-8 bytes were restored from the pre-fix commit. An inverse-replacement comparison proves that only the two intended Si regions differ from the original checker; the unchanged Ag–Te check is preserved. All 166,133 quality checks now pass on the existing complete candidate, with zero warnings. Both failed candidates remain recorded, and a fresh complete R3 build and exact-commit CI are still required before pushing. No records were changed for this repair.
