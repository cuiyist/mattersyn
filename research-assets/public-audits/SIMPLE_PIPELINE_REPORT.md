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


### simple-batch02-20261011-r3

Anonymous verification passed at 2026-10-11T08:39:37+00:00: 867 files, zero mismatches. [Source commit](https://github.com/cuiyist/mattersyn/commit/e45d3c4d32b66bcdff526349cd5208ea45321432) and [Site commit](https://github.com/cuiyist/mattersyn-site/commit/492e4b39eb153e2f5d6d25b1be841341506e3cef). This batch contains 36 source groups, 68 records and 252 source figure crops; 36 distinct newly contributing primary papers after DOI deduplication. Every new contribution remains machine extracted and not independently audited. The final built site is 1,180,293,790 bytes / 26,190 files.

Live counter: **244 audited + 49 machine extracted = 293 papers**, 3,073 canonical records, 272 direct material families, 312 material/component pages and 864 displayed recipe–structure pairs (6 more comprehensive; 858 partial). These display counts do not establish extraction accuracy, measured atomic coordinates or training eligibility.

Recorded source pr: [15](https://github.com/cuiyist/mattersyn/pull/15).

Recorded source ci run: [38122536953](https://github.com/cuiyist/mattersyn/actions/runs/38122536953).

| Primary DOI | Records | Figure crops | Public page |
| --- | ---: | ---: | --- |
| 10.1021/cm031003o | 2 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/al2003-cm031003o-ps-pe3-hgte-nc-2-pe2-colloidal-crystals-1.html) |
| 10.1021/cm047874v | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/al2005-cm047874v-znse-nanorods-1.html) |
| 10.1021/cm070214g | 2 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/al2007-cm070214g-cdse-zns-quantum-dots-qds-encapsulated-i-1.html) |
| 10.1021/ja1089809 | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/b-b-s2011-ja1089809-zns-zn1-xcdxs-surface-alloyed-nanocrysta-1.html) |
| 10.1021/ja051455x | 1 | 9 | [Open](https://cuiyist.github.io/mattersyn-site/records/bharali2005-ja051455x-inp-zns-qds-1.html) |
| 10.1021/cm070898s | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/cao2007-cm070898s-cdte-wpu-composite-1.html) |
| 10.1021/acsanm.3c02221 | 3 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/chatterjee2023-acsanm-3c02221-insb-qds-sample-a-1.html) |
| 10.1021/acsami.4c21582 | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/chen2025-acsami-4c21582-cpb-gns-10-1.html) |
| 10.1021/cm501595u | 1 | 7 | [Open](https://cuiyist.github.io/mattersyn-site/records/chicago2014-cm501595u-pbs-cds-core-shell-cqd-with-0-1-nm-cds-s-1.html) |
| 10.1021/ja110454b | 2 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/choi2011-ja110454b-pbs-nanocrystals-n2-aged-1.html) |
| 10.1021/ja1013695 | 1 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/debnath2010-ja1013695-tmpmdtc-capped-pbs-cqds-1.html) |
| 10.1021/ja413026h | 1 | 10 | [Open](https://cuiyist.github.io/mattersyn-site/records/hughes2014-ja413026h-pbse-qd-dimer-1.html) |
| 10.1021/cm102370a | 5 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/iii2010-cm102370a-cdse414-nm-1.html) |
| 10.1021/cm5040886 | 3 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/jara2014-cm5040886-cuins2-qds-2-9-nm-1.html) |
| 10.1021/ja0357902 | 5 | 8 | [Open](https://cuiyist.github.io/mattersyn-site/records/joo2003-ja0357902-pbs-nanocrystals-13-nm-1.html) |
| 10.1021/ja051713q | 3 | 8 | [Open](https://cuiyist.github.io/mattersyn-site/records/kwon2005-ja051713q-fe2o3-cds-1.html) |
| 10.1021/cm0621390 | 2 | 7 | [Open](https://cuiyist.github.io/mattersyn-site/records/kwon2006-cm0621390-fe3o4-cds-nc-heterostructures-1.html) |
| 10.1021/cm900103b | 1 | 7 | [Open](https://cuiyist.github.io/mattersyn-site/records/li2009-cm900103b-cuins2-zns-core-shell-nanocrystals-1.html) |
| 10.1021/cm903648c | 3 | 9 | [Open](https://cuiyist.github.io/mattersyn-site/records/li2010-cm903648c-155-nm-pbs-cncs-1.html) |
| 10.1021/cm502812c | 1 | 10 | [Open](https://cuiyist.github.io/mattersyn-site/records/liang2014-cm502812c-indium-doped-zinc-oxide-izo-nanocrystals-1.html) |
| 10.1021/ja003055+ | 1 | 8 | [Open](https://cuiyist.github.io/mattersyn-site/records/manna2000-ja003055-cdse-nanorods-1.html) |
| 10.1021/ja0574973 | 2 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/murphy2006-ja0574973-spherical-oleate-capped-pbte-nanocrystal-1.html) |
| 10.1021/ja805845q | 2 | 13 | [Open](https://cuiyist.github.io/mattersyn-site/records/panthani2008-ja805845q-cuins2-nanocrystals-1.html) |
| 10.1021/ja5020025 | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/peng2014-ja5020025-5-nm-cdse-nanocrystals-1.html) |
| 10.1021/ja710437r | 2 | 8 | [Open](https://cuiyist.github.io/mattersyn-site/records/pietryga2008-ja710437r-pbse-cdse-core-shell-nanocrystals-1.html) |
| 10.1021/acsami.4c13822 | 1 | 9 | [Open](https://cuiyist.github.io/mattersyn-site/records/provided2024-acsami-4c13822-cspbbr3-nanocrystals-1.html) |
| 10.1021/ja306651x | 2 | 9 | [Open](https://cuiyist.github.io/mattersyn-site/records/qu2012-ja306651x-zinc-blende-cdse-cds-core-shell-nanocrys-1.html) |
| 10.1021/cm403373q | 1 | 9 | [Open](https://cuiyist.github.io/mattersyn-site/records/robertson2014-cm403373q-pbte-nanocrystals-on-graphene-1.html) |
| 10.1021/acssuschemeng.8b05345 | 2 | 7 | [Open](https://cuiyist.github.io/mattersyn-site/records/sharma2019-acssuschemeng-8b05345-si-qds-1.html) |
| 10.1021/cg4001973 | 4 | 8 | [Open](https://cuiyist.github.io/mattersyn-site/records/siah2013-cg4001973-ni-nanocube-cdse-coreshell-1.html) |
| 10.1021/cm102156v | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/siy2010-cm102156v-cdse-nanocrystal-quantum-dots-1.html) |
| 10.1021/ja0123599 | 3 | 9 | [Open](https://cuiyist.github.io/mattersyn-site/records/talapin2002-ja0123599-cdse-nanocrystals-1.html) |
| 10.1021/ja058269b | 1 | 8 | [Open](https://cuiyist.github.io/mattersyn-site/records/urban2006-ja058269b-pbte-nanocrystals-7-nm-1.html) |
| 10.1021/ja302964e | 3 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/washington2012-ja302964e-zb-cdse-qds-5-2-nm-1.html) |
| 10.1021/cm049476y | 1 | 9 | [Open](https://cuiyist.github.io/mattersyn-site/records/yu2004-cm049476y-pbse-semiconductor-nanocrystals-3-5-nm-1.html) |
| 10.1021/ja504310w | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/zhongxh-ecust-edu-cn2014-ja504310w-cis-z-qds-1.html) |


### simple-batch03-20261011

Anonymous verification passed at 2026-10-11T10:06:46+00:00: 740 files, zero mismatches. [Source commit](https://github.com/cuiyist/mattersyn/commit/2bf0ae47a4249b3c9ffe507631643bd0a93f93a2) and [Site commit](https://github.com/cuiyist/mattersyn-site/commit/bdd0cfc92e8abe761cc0d87074e5b7b69e335517). This batch contains 36 source groups, 56 records and 239 source figure crops; 36 distinct newly contributing primary papers after DOI deduplication. Every new contribution remains machine extracted and not independently audited. The final built site is 1,251,142,322 bytes / 26,846 files.

Live counter: **244 audited + 85 machine extracted = 329 papers**, 3,129 canonical records, 278 direct material families, 317 material/component pages and 864 displayed recipe–structure pairs (6 more comprehensive; 858 partial). These display counts do not establish extraction accuracy, measured atomic coordinates or training eligibility.

Recorded source pr: [16](https://github.com/cuiyist/mattersyn/pull/16).

Recorded source ci run: [38127860470](https://github.com/cuiyist/mattersyn/actions/runs/38127860470).

| Primary DOI | Records | Figure crops | Public page |
| --- | ---: | ---: | --- |
| 10.1021/jp036497r | 2 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/achermann2003-jp036497r-octylamine-capped-cdse-nqds-1.html) |
| 10.1021/jp0278364 | 1 | 8 | [Open](https://cuiyist.github.io/mattersyn-site/records/al2003-jp0278364-cdse-cds-core-shell-nanocrystals-1.html) |
| 10.1021/ja807874e | 5 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/al2009-ja807874e-znte-cds-tetrapods-1.html) |
| 10.1021/jacs.6c03275 | 1 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/ban2026-jacs-6c03275-inas-cqds-with-excitonic-features-at-180-1.html) |
| 10.1021/jp050424l | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/biju2005-jp050424l-cdse-qd-clusters-1.html) |
| 10.1021/jacs.5b04765 | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/chen2015-jacs-5b04765-qd1-mc-1.html) |
| 10.1021/jacs.5c23366 | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/chen2026-jacs-5c23366-insb-qds-7-1-nm-1.html) |
| 10.1021/jp406369a | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/cordones2014-jp406369a-pbsesnse2-nanocomposite-1.html) |
| 10.1021/jp072516b | 1 | 7 | [Open](https://cuiyist.github.io/mattersyn-site/records/dagtepe2007-jp072516b-magic-sized-cdte-qds-1.html) |
| 10.1021/jp802254n | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/dagtepe2008-jp802254n-magic-sized-cdte-quantum-dots-1.html) |
| 10.1021/jp502356d | 2 | 9 | [Open](https://cuiyist.github.io/mattersyn-site/records/ding2014-jp502356d-pbs-qds-excitonic-peak-at-740-nm-1.html) |
| 10.1021/jp808091d | 2 | 7 | [Open](https://cuiyist.github.io/mattersyn-site/records/guijarro2009-jp808091d-cdse-qds-direct-adsorption-1.html) |
| 10.1021/jp210949v | 1 | 8 | [Open](https://cuiyist.github.io/mattersyn-site/records/guo2012-jp210949v-cdse-5-2cds-1.html) |
| 10.1021/jp053103i | 2 | 7 | [Open](https://cuiyist.github.io/mattersyn-site/records/houtepen2005-jp053103i-cdse-quantum-dots-2-9-nm-1.html) |
| 10.1021/jp0039520 | 1 | 18 | [Open](https://cuiyist.github.io/mattersyn-site/records/jp0039520-ag2s-nanocrystals-1.html) |
| 10.1021/jp5051904 | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/jumabekov2014-jp5051904-pbs-gsh-qds-1.html) |
| 10.1021/jp0708906 | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/kloper2007-jp0708906-cdte-nqds-with-4-0-nm-diameter-1.html) |
| 10.1021/jp308706b | 2 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/lei2013-jp308706b-pbse-qd-clusters-qda-diameter-5-0-0-3-nm-1.html) |
| 10.1021/ja906503w | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/luther2009-ja906503w-pbs-nanorods-1.html) |
| 10.1021/jp210720v | 2 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/milekhin2012-jp210720v-cds-nc-array-cd440ag-1.html) |
| 10.1021/jp107043z | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/morfa2010-jp107043z-zno-thin-films-1.html) |
| 10.1021/jp0535285 | 2 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/norberg2005-jp0535285-zno-nanocrystals-capped-with-dda-1.html) |
| 10.1021/jp071979e | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/osovsky2007-jp071979e-cdte-nqds-1.html) |
| 10.1021/jp900252e | 1 | 12 | [Open](https://cuiyist.github.io/mattersyn-site/records/ouyang2009-jp900252e-cds-qds-myristic-acid-240-c-120-min-1.html) |
| 10.1021/jp108165g | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/pijpers2010-jp108165g-pbse-qds-5-5-nm-coupled-to-sno2-mesoporo-1.html) |
| 10.1021/jp308500r | 3 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/silva2013-jp308500r-cdse-bare-core-msqds-sample-s0-1.html) |
| 10.1021/jp900564r | 1 | 7 | [Open](https://cuiyist.github.io/mattersyn-site/records/spoerke2009-jp900564r-cds-coated-zno-nanorods-1.html) |
| 10.1021/jp208879f | 1 | 10 | [Open](https://cuiyist.github.io/mattersyn-site/records/text2012-jp208879f-t-nt-cdse-taa-n2-1.html) |
| 10.1021/jp054774j | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/venugopal2006-jp054774j-ldh-cdse-composite-mcdse-mldh-1-100-1.html) |
| 10.1021/jp0566313 | 2 | 10 | [Open](https://cuiyist.github.io/mattersyn-site/records/wang2006-jp0566313-zno-nanocrystals-from-zinc-ketoacidoxima-1.html) |
| 10.1021/ja9005767 | 3 | 8 | [Open](https://cuiyist.github.io/mattersyn-site/records/xie2009-ja9005767-cuins2-nanocrystals-1.html) |
| 10.1021/jp903199y | 1 | 8 | [Open](https://cuiyist.github.io/mattersyn-site/records/yu2009-jp903199y-oa-capped-cds-ncs-1.html) |
| 10.1021/jp504755a | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/zane2014-jp504755a-cdse-cds-zns-quantum-dots-qds-with-40-qu-1.html) |
| 10.1021/jp711778u | 3 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/zhang2008-jp711778u-znte-quasi-spheres-1.html) |
| 10.1021/jp1044282 | 3 | 7 | [Open](https://cuiyist.github.io/mattersyn-site/records/zhang2010-jp1044282-f280-1.html) |
| 10.1021/jacs.9b06932 | 1 | 7 | [Open](https://cuiyist.github.io/mattersyn-site/records/zhang2019-jacs-9b06932-cdse-cds-dot-platelet-2d-nanocrystals-1.html) |


### simple-batch04-20261011

Anonymous verification passed at 2026-10-11T11:55:05+00:00: 931 files, zero mismatches. [Source commit](https://github.com/cuiyist/mattersyn/commit/28133151f968c8e2e71f7a355da579cbf1f8baf9) and [Site commit](https://github.com/cuiyist/mattersyn-site/commit/f3137b4e98846684c2114828de3f63bc014e0c7d). This batch contains 43 source groups, 85 records and 242 source figure crops; 43 distinct newly contributing primary papers after DOI deduplication. Every new contribution remains machine extracted and not independently audited. The final built site is 1,341,834,607 bytes / 27,695 files.

Live counter: **244 audited + 128 machine extracted = 372 papers**, 3,214 canonical records, 292 direct material families, 334 material/component pages and 864 displayed recipe–structure pairs (6 more comprehensive; 858 partial). These display counts do not establish extraction accuracy, measured atomic coordinates or training eligibility.

Recorded source pr: [17](https://github.com/cuiyist/mattersyn/pull/17).

Recorded source ci run: [38133780425](https://github.com/cuiyist/mattersyn/actions/runs/38133780425).

| Primary DOI | Records | Figure crops | Public page |
| --- | ---: | ---: | --- |
| 10.1021/la102983c | 4 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/al2010-la102983c-c11-functionalized-si-ncs-1.html) |
| 10.1021/nn103303q | 2 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/al2011-nn103303q-pbse-nc-film-1.html) |
| 10.1021/nn204601n | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/al2012-nn204601n-znse-zns-nrs-1.html) |
| 10.1021/nn301405j | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/al2012-nn301405j-alkylselenide-capped-pbse-qds-1.html) |
| 10.1021/nn3024255 | 1 | 7 | [Open](https://cuiyist.github.io/mattersyn-site/records/al2012-nn3024255-cdse-cds-dot-in-plate-ncs-sample-p4-1.html) |
| 10.1021/nl304753n | 1 | 9 | [Open](https://cuiyist.github.io/mattersyn-site/records/al2013-nl304753n-sulfide-exchanged-alumina-infilled-6-3-n-1.html) |
| 10.1021/nn403893b | 3 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/al2014-nn403893b-cdte-cdse-3-nm-1-ml-1.html) |
| 10.1021/nn500414u | 3 | 7 | [Open](https://cuiyist.github.io/mattersyn-site/records/al2014-nn500414u-sp1-qd1-1.html) |
| 10.1021/nn504679k | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/al2014-nn504679k-pbse-qd-films-treated-with-2da-1.html) |
| 10.1021/la100249t | 2 | 7 | [Open](https://cuiyist.github.io/mattersyn-site/records/amelia2010-la100249t-cds-nanocrystals-precursor-thioglycerol-1.html) |
| 10.1021/nl101079u | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/bui2010-nl101079u-cdse-zns-core-shell-streptavidin-conjuga-1.html) |
| 10.1021/la991498p | 1 | 7 | [Open](https://cuiyist.github.io/mattersyn-site/records/carnes2000-la991498p-nc-zno-1.html) |
| 10.1021/nl025767z | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/chen2002-nl025767z-cdse-qd-doped-micelles-1.html) |
| 10.1021/nn502442g | 1 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/crisp2014-nn502442g-cdte-tetrapod-nanocrystals-1.html) |
| 10.1021/nl102705p | 3 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/evers2010-nl102705p-pbse-nanocrystals-11-0-nm-effective-diam-1.html) |
| 10.1021/nn402931y | 3 | 8 | [Open](https://cuiyist.github.io/mattersyn-site/records/groeneveld2013-nn402931y-znse-nanocrystals-3-7-nm-diameter-1.html) |
| 10.1021/nn901008r | 2 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/hanrath2009-nn901008r-pbse-nanocrystals-1.html) |
| 10.1021/nn2033117 | 3 | 8 | [Open](https://cuiyist.github.io/mattersyn-site/records/ihly2011-nn2033117-pbs-qd-film-5-0-0-6-nm-1.html) |
| 10.1021/la3027573 | 2 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/jaiswal2012-la3027573-hgs-q-dots-2.html) |
| 10.1021/la202892h | 1 | 8 | [Open](https://cuiyist.github.io/mattersyn-site/records/jin2012-la202892h-cdse-qds-with-sulfonate-ligands-1.html) |
| 10.1021/nn5037812 | 3 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/justo2014-nn5037812-pbscl-qds-1.html) |
| 10.1021/nn505375n | 1 | 7 | [Open](https://cuiyist.github.io/mattersyn-site/records/kholmicheva2014-nn505375n-pbs-cds-core-shell-nanocrystals-2.html) |
| 10.1021/la903415n | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/ko2010-la903415n-cdse-nanocrystal-chains-1.html) |
| 10.1021/nl100483v | 1 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/kung2010-nl100483v-nc-cdse-nanowires-60-nm-200-nm-1.html) |
| 10.1021/nl801629f | 9 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/lees2008-nl801629f-core-cdse-qd-1-1.html) |
| 10.1021/nl300524j | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/liang2012-nl300524j-pbte-nanocrystal-coated-glass-fibers-1.html) |
| 10.1021/nl101284k | 3 | 7 | [Open](https://cuiyist.github.io/mattersyn-site/records/mayer2010-nl101284k-oleate-capped-pbse-ncs-3-1-nm-diameter-1.html) |
| 10.1021/nn800737a | 1 | 7 | [Open](https://cuiyist.github.io/mattersyn-site/records/mcdaniel2009-nn800737a-fe3o4-cds-nanocrystal-heterostructures-1.html) |
| 10.1021/nn201988w | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/miszta2011-nn201988w-cu2-xse-core-cu2s-pods-octapod-1.html) |
| 10.1038/nmat1505 | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/mokari2005-nmat1505-cdseau-nbts-504-nm-rods-1.html) |
| 10.1021/nn900863a | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/moreels2009-nn900863a-pbs-qdots-3-6-nm-1.html) |
| 10.1021/nn2007817 | 5 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/murray2011-nn2007817-pbte-nanocrystals-a-1.html) |
| 10.1021/nn9004507 | 4 | 7 | [Open](https://cuiyist.github.io/mattersyn-site/records/narayanaswamy2009-nn9004507-inp-zns-core-shell-quantum-dots-1-8-nm-1.html) |
| 10.1021/mz300427d | 1 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/negele2012-mz300427d-polyfluorene-cdse-cds-quantum-dot-hybrid-2.html) |
| 10.1021/nn900138d | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/nn900138d-cdse-cds-zns-core-shell-shell-qds-1.html) |
| 10.1021/jp984833b | 2 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/rogach1999-jp984833b-cdse-nanoparticles-2-mercaptoethanol-sta-1.html) |
| 10.1021/nn301182h | 3 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/ruberu2012-nn301182h-cds1xsex-nanodots-1.html) |
| 10.1021/jz400181m | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/santra2013-jz400181m-cuins2-qds-1.html) |
| 10.1021/nl061054v | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/schill2006-nl061054v-cds-cdse-cds-quantum-dot-quantum-well-he-1.html) |
| 10.1021/nn303130d | 2 | 8 | [Open](https://cuiyist.github.io/mattersyn-site/records/segets2012-nn303130d-pbs-small-qds-1.html) |
| 10.1021/nl0155126 | 2 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/talapin2001-nl0155126-cdse-nanocrystals-1.html) |
| 10.1021/nn5018654 | 1 | 9 | [Open](https://cuiyist.github.io/mattersyn-site/records/weidman2014-nn5018654-pbs-nanocrystals-24-1-pb-s-precursor-rat-1.html) |
| 10.1021/nn2001118 | 2 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/yarema2011-nn2001118-ag2se-nanocrystals-2-0-nm-1.html) |

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

## Batch02 verified milestone

Batch02 is deployed and anonymously verified at 2026-10-11T08:39:37+00:00, from Source `e45d3c4d32b66bcdff526349cd5208ea45321432` and Site `492e4b39eb153e2f5d6d25b1be841341506e3cef`. The verified final artifacts contain 36 distinct newly contributing primary papers, 68 records and 252 source crops; built site size is 1,180,293,790 bytes. The earlier preparation and failed-build entries are retained as historical results; this milestone supersedes their unpublished status.

The selected cohort has 50 distinct papers: 36 deployed and 14 omitted or held. There were 49 supported identities and 48 successful two-pass papers. Before rare reading, the automatic check considered 2,045 values, kept 1,249, and retained 91 pairs.

One-reader rare-material checks covered 15 papers and removed 88 field/path entries (86 validated value objects reported by the readers), with zero replacement facts. These deletion counts are not an independent audit or a post-reading accuracy score. Common-material papers were not audited. New records remain source extracted, not independently audited or training eligible.

| Stage | Actual UTC timestamp |
| --- | --- |
| Extraction start | 2026-10-11T04:20:49.289787+00:00 |
| Extraction finish | 2026-10-11T06:19:13.626028+00:00 |
| Figures/check final handoff | 2026-10-11T06:21:59.092408+00:00 |
| Site push | 2026-10-11T08:33:31+00:00 |
| Anonymous verification | 2026-10-11T08:39:37+00:00 |

Extraction elapsed 118.405604 minutes; figures/check metadata records 2.7578 minutes. Cohort extraction-start to verified publication elapsed 258.79517 minutes, or 8.346369 newly published primary papers per elapsed wall-clock hour. This interval includes release preparation/waiting and makes no claim of uninterrupted agent work or achieved 20-paper/hour capacity.

| Paper left out | Metadata reason |
| --- | --- |
| 10.1021/acsnano.5b01154 | no_route_eligible_record |
| 10.1021/am4038068 | no_route_eligible_record |
| 10.1021/am504057y | no_route_eligible_record |
| 10.1021/cm010291q | no_route_eligible_record |
| 10.1021/j100054a032 | identity_hold |
| 10.1021/ja0173167 | no_usable_pairs |
| 10.1021/ja068351m | no_usable_pairs |
| 10.1021/ja103956p | no_usable_pairs |
| 10.1021/ja2029415 | no_route_eligible_record |
| 10.1021/ja206303g | no_usable_pairs |
| 10.1021/ja301285x | no_usable_pairs |
| 10.1021/ja308200f | no_route_eligible_record |
| 10.1021/ja410165f | no_route_eligible_record |
| 10.1021/ja805655b | invalid_or_failed_pass_after_one_redo |

The choices and fixes already recorded above remain part of this batch: future response-cap increase, the two-worker local runtime and directory-race repair, precise timestamp handling, ordinary crop-copy fallback, the status-aware Si regression correction and UTF-8 restoration of the unrelated Ag–Te literal. Both failed build attempts remain preserved. The quote-found, number-in-quote and both-passes-agree rules and all normal release gates remain in force. The audited lane, original findings, denominator, sampling/stop rules and every owner question remain paused and unchanged.


## Batch03 integrated preparation

At 2026-10-11T08:57:20+00:00, Batch03 has 36 papers, 56 ordinary route records and 239 source crops integrated locally, with zero new live publication credit pending the normal complete build, source, browser, CI, deployment and anonymous checks. The prior 3,073 canonical records remain byte identical. The quote-free batch archive contains no unknown/private fields or local paths. All new records retain `source_extracted`.

The selected cohort contains 50 papers: 45 supported identities and 43 successful two-pass papers. Extraction took 91.3016 wall-clock minutes; figures/check took 1.7361 minutes. The original automatic check saw 1,426 values, kept 944 and retained 63 pairs. Those figures are historical checker results before rare reading and route selection, not independent accuracy or publication throughput. Five identity holds, two persistent pass failures, three zero-pair papers and four papers with no ordinary eligible route remain private and receive no publication credit.

One-reader rare-material checks covered four papers and nine product pairs. They removed 20 scientific value objects across 27 exact paths, including four wrong page locators and two coupled units, with no replacement facts. Wrong product/step/property bindings, unsupported vessel geometry and wrongly generalized sizes or duration endpoints were removed. Common-material products were not reviewed; original quoted training files and checker history remain intact. Missing locators are not replaced by invented page numbers.

Choice: use ordinary private crop copies after Windows denied hardlinks, verifying identical bytes; no script predicate or release gate was changed. The local model continues the next batch during this release preparation.

Post-Batch02 cleanup completed: 1,009 exact published duplicate files removed, 357,324,929 logical bytes. Observed free-space increase was 358,154,240 bytes, including concurrent disk activity. No original papers, page text, saved passes, quoted pairs, receipts, active R3 artifacts or checkouts were removed. The separately parked whole-directory cleanup remains unchanged.

The exact staging helper initially omitted the generated release baseline manifest. Added only that actual derived path through its existing --extra-path argument; no checklist, policy or release predicate was altered.

The normal source preparer rejected treating the derived baseline as a manually approved payload. Preserved that failed attempt and the dependency-generated copy privately, restored only the regenerable baseline to HEAD, and let prepare_source_release regenerate and bind it normally. No approval was fabricated and no gate changed.

## Batch03 verified milestone

Batch03 is deployed and anonymously verified at 2026-10-11T10:06:46+00:00, from Source `2bf0ae47a4249b3c9ffe507631643bd0a93f93a2` and Site `bdd0cfc92e8abe761cc0d87074e5b7b69e335517`. The verified final artifacts contain 36 distinct newly contributing primary papers, 56 records and 239 source crops; built site size is 1,251,142,322 bytes. The earlier preparation and failed-build entries are retained as historical results; this milestone supersedes their unpublished status.

The selected cohort has 50 distinct papers: 36 deployed and 14 omitted or held. There were 45 supported identities and 43 successful two-pass papers. Before rare reading, the automatic check considered 1,426 values, kept 944, and retained 63 pairs.

One-reader rare-material checks covered 4 papers and removed 27 field/path entries (20 scientific value objects, 4 wrong page locators and 2 coupled unit fields), with zero replacement facts. These deletion counts are not an independent audit or a post-reading accuracy score. Common-material papers were not audited. New records remain source extracted, not independently audited or training eligible.

| Stage | Actual UTC timestamp |
| --- | --- |
| Extraction start | 2026-10-11T06:33:03.848740+00:00 |
| Extraction finish | 2026-10-11T08:04:21.970455+00:00 |
| Figures/check final handoff | 2026-10-11T08:06:06.137648+00:00 |
| Site push | 2026-10-11T10:00:23+00:00 |
| Anonymous verification | 2026-10-11T10:06:46+00:00 |

Extraction elapsed 91.302029 minutes; figures/check metadata records 1.7361 minutes. Cohort extraction-start to verified publication elapsed 213.702521 minutes, or 10.107508 newly published primary papers per elapsed wall-clock hour. This interval includes release preparation/waiting and makes no claim of uninterrupted agent work or achieved 20-paper/hour capacity.

| Paper left out | Metadata reason |
| --- | --- |
| 10.1021/ja9074425 | no_usable_pairs |
| 10.1021/ja970754m | identity_hold |
| 10.1021/jacs.3c08897 | invalid_or_failed_pass_after_one_redo |
| 10.1021/jp0103880 | no_route_eligible_record |
| 10.1021/jp1084668 | no_route_eligible_record |
| 10.1021/jp300509f | invalid_or_failed_pass_after_one_redo |
| 10.1021/jp506043n | no_route_eligible_record |
| 10.1021/jp508769f | no_usable_pairs |
| 10.1021/jp710173q | no_route_eligible_record |
| 10.1021/jp809171f | no_usable_pairs |
| 10.1021/jp9530562 | identity_hold |
| 10.1021/jp953719f | identity_hold |
| 10.1021/jp971487+ | identity_hold |
| 10.1021/jp982397n | identity_hold |

The existing batch choices, source-preparation failures and engineering fixes remain recorded above as actual history. The quote-found, number-in-quote and both-passes-agree rules and all normal release gates remain in force. The audited lane, original findings, denominator, sampling/stop rules and every owner question remain paused and unchanged.


## Batch04 preparation and Batch05 backend choice

At 2026-10-11T10:19:18+00:00, Batch04 has completed local extraction and checking: 46 successful two-pass papers, 97 checked pairs, 1,342 of 2,121 values retained and 251 crops. Two papers failed again after the permitted redo; two further papers have identity holds. These are pre-reading checker counts with no publication credit. The rare-material pass is deletion-only, one reader per assigned paper; common records remain unreviewed. Batch05 started locally at 2026-10-11T10:12Z with 47 supported identities and three holds.

Choice: use the official same-version CUDA backend at the completed Batch04 idle boundary, preserving the exact model, two 32,768-token slots, q8 K/V and output settings. Load, health and capacity checks passed on the RTX 5090; sampled load-only GPU-wide peak was 29,656 MiB with at least 2,532 MiB free. No inference ran during that fit check. CUDA production throughput and accuracy are not yet measured.

Engineering change: tree digests now hash the unchanged complete file inventory with eight independent readers. Every file is hashed afresh; digest representation, exclusions, error propagation and every release check remain unchanged. All eight focused synthetic regressions passed. No production speedup is claimed.

Storage: the expanded 14,557,671,270-byte exact-file cleanup proposal remains parked because an unrelated active process references the Desktop ancestor. No files from that proposal were removed, and no foreign process was stopped. The earlier verified 357,324,929-byte cleanup remains the only new completed cleanup.


## Batch04 integrated preparation

At 2026-10-11T10:30:44+00:00, Batch04 has 43 distinct paper contributions, 85 ordinary recipe records and 242 crops integrated locally. It has zero new publication credit until the normal complete build, source, browser, CI, deployment and anonymous checks pass. All 3,129 existing canonical records are byte identical; new records retain `source_extracted`, with no reviewed or calibrated claim. The quote-free archive contains no quoted text, unknown private fields or local paths.

The 50-paper cohort had 48 supported identities and 46 valid two-pass extractions. Extraction took 118.1912 minutes; figures/check took 1.6866 minutes. The original checker kept 1,342 of 2,121 values in 97 pairs. These are checker results before rare reading and route selection, not accuracy or published throughput.

Seven papers are left out: two unresolved DOI identities (`10.1021/la960426k`, `10.1023/a_1008650027769`), two repeated pass failures (`10.1021/nn3057356`, `10.1021/ph5002704`), and three without an ordinary eligible route after the existing converter checks (`10.1021/nl015651n`, `10.1021/nl900534m`, `10.1038/nnano.2008.360`). Technical holds are not claims that synthesis is absent. Four additional noneligible variants were omitted from otherwise retained papers; original pair ordinals and training files remain preserved.

Single-reader rare-material checks covered 14 papers and removed 63 scientific objects, one wrong page locator and seven coupled units, across 71 paths, without replacement facts. Deletions cover wrong product/step/property bindings, parent-only sizes or optical peaks, generalized synthesis durations, unsupported vessels or phases, and stock/variant assignments. Common-material pairs were unchanged and were not scientifically reviewed. One reader count was mechanically reconciled to its exact proposed paths; the proposal itself was unchanged.

Choice: retain the existing ordinary route predicate and report five-field completeness separately, rather than inventing an additional admission gate. A private preparation helper incorrectly expected 329 normalized DOI papers; actual verified Batch03 inventory has 328 normalized DOIs and 329 source groups. That redundant private assertion was removed; all normal inventory, hash and release checks remain.

Small release-tool change: hash the same complete tree with at most eight threads, preserving file exclusions, sorted paths, digest bytes and failure propagation. Eight synthetic tests passed for equality, coverage, exclusions, order, concurrency and errors. No gate or file was omitted and no production speedup is claimed from these tests.

## Batch04 verified milestone

Batch04 is deployed and anonymously verified at 2026-10-11T11:55:05+00:00, from Source `28133151f968c8e2e71f7a355da579cbf1f8baf9` and Site `f3137b4e98846684c2114828de3f63bc014e0c7d`. The verified final artifacts contain 43 distinct newly contributing primary papers, 85 records and 242 source crops; built site size is 1,341,834,607 bytes. The earlier preparation and failed-build entries are retained as historical results; this milestone supersedes their unpublished status.

The selected cohort has 50 distinct papers: 43 deployed and 7 omitted or held. The omissions comprise 2 identity holds, 2 failures after one redo, and 3 papers with no retained eligible route. There were 48 supported identities and 46 successful two-pass papers. Before rare reading, the automatic check considered 2,121 values, kept 1,342, and retained 97 pairs.

One-reader rare-material checks covered 14 papers and removed 71 field/path entries (63 scientific value objects, 1 wrong page locators and 7 coupled unit fields), with zero replacement facts. These deletion counts are not an independent audit or a post-reading accuracy score. Common-material papers were not audited. New records remain source extracted, not independently audited or training eligible.

| Stage | Actual UTC timestamp |
| --- | --- |
| Extraction start | 2026-10-11T08:09:23.100874+00:00 |
| Extraction finish | 2026-10-11T10:07:33.263735+00:00 |
| Figures/check final handoff | 2026-10-11T10:09:14.459042+00:00 |
| Site push | 2026-10-11T11:46:35+00:00 |
| Anonymous verification | 2026-10-11T11:55:05+00:00 |

Extraction elapsed 118.169381 minutes; figures/check metadata records 1.686588 minutes. Cohort extraction-start to verified publication elapsed 225.698319 minutes, or 11.431188 newly published primary papers per elapsed wall-clock hour. This interval includes release preparation/waiting and makes no claim of uninterrupted agent work or achieved 20-paper/hour capacity.

| Paper left out | Metadata reason |
| --- | --- |
| 10.1021/la960426k | identity_hold |
| 10.1021/nl015651n | no_route_eligible_record |
| 10.1021/nl900534m | no_route_eligible_record |
| 10.1021/nn3057356 | invalid_or_failed_pass_after_one_redo |
| 10.1021/ph5002704 | invalid_or_failed_pass_after_one_redo |
| 10.1023/a_1008650027769 | identity_hold |
| 10.1038/nnano.2008.360 | no_route_eligible_record |

The existing batch choices, source-preparation failures and engineering fixes remain recorded above as actual history. The quote-found, number-in-quote and both-passes-agree rules and all normal release gates remain in force. The audited lane, original findings, denominator, sampling/stop rules and every owner question remain paused and unchanged.


## Batch05 checked handoff and Batch06 launch block

At 2026-10-11T11:37:46.244732+00:00, Batch05 extraction, figures and check are complete with controller and check exit codes zero. These are local checker results before final rare-material reading and ordinary route selection. Batch05 has **zero newly published papers**; its final conversion/record/crop counts are not yet determined. The original quoted training files remain private and preserved.

| Metadata | Actual count |
| --- | ---: |
| Selected cohort | 50 |
| Identity-supported inputs | 47 |
| Successful final two-pass papers | 47 |
| Checked pair files | 47 |
| Nonempty checked papers | 44 |
| Checked pairs before rare reading | 65 |
| Values assessed before rare reading | 1642 |
| Values kept before rare reading | 1054 |
| Checked crops, including zero-pair papers | 271 |
| Crops on nonempty checked papers | 255 |

One original pass failed, the allowed single redo succeeded, and all 94 final A/B pass files are valid. There were 96 pass executions including that redo: 95 succeeded and one failed. No paper was left out for a persistent extraction failure. Three technical DOI identity holds remain: `10.1039/a809779h`, `10.1088/1361-6528_28_4_045701` and `10.1002/(sici)1521-4095(199906)11_8_643__aid-adma643_3.0.co;2-i`. Three generated papers retained no checked pairs: `10.1007/s11671-008-9133-5`, `10.1021/am404355m` and `10.1103/physrevb.66.075316`. These outcomes do not assert that the papers lack synthesis. Final identity diagnostics show zero metadata conflicts.

| Stage | Actual UTC timestamp |
| --- | --- |
| Extraction start | 2026-10-11T10:12:03.233177+00:00 |
| Extraction finish | 2026-10-11T11:29:48.202258+00:00 |
| Figures/check finish | 2026-10-11T11:31:09.223215+00:00 |

Extraction elapsed 77.749485 minutes; figures/check elapsed 1.350349 minutes; the combined interval was 79.099834 minutes. The observed two-pass extraction rate was 36.270337 papers per elapsed hour, or 35.651149 through the full extraction/figures/check interval. Neither is publication throughput, an accuracy score or papers per GPU-hour. Sampled GPU-wide peak usage was 29,768 MiB with at least 2,420 MiB free; the measurement is not attributable solely to Qwen. No controlled same-paper CUDA/Vulkan speed or accuracy comparison was run.

Batch04 subsequently passed normal deployment and anonymous verification at 2026-10-11T11:55:05Z. The verified Batch01–Batch04 credit is 128 new machine-extracted papers, and the homepage contains 372 source groups. Batch05 remains unpublished and contributes zero additional paper credit.

**Blocked action:** automatic approval review rejected the Batch06 local model/controller launch, citing the earlier test-only website pause. This records the review reason, not a new owner pause or absence of current owner authorization. The launch is omitted; no retry, alternate launch or workaround was attempted. Existing Batch04 publication and completed Batch05 handling continue. A narrow asynchronous permission request for this refused launch is recorded in curation-control.json. It does not block the completed Batch05 work.

The inherited Batch05 private handoff sentence saying Batch06 was not authorized is historical template wording; it is not used as the current owner's intent. The current simple-pipeline instruction remains the active scope, with audited work paused. All original audit findings, sampled denominator/stop rules and owner questions remain unchanged. No release gate, extraction predicate or policy was changed for this report.



## Batch05 final rare-reading selection — publication pending

Final deletion-only consolidation completed at 2026-10-11T12:04:37.223722+00:00. The 50-paper cohort now has **39 papers, 55 ordinary source-extracted records and 221 source crops selected for integration**. They have not yet been deployed or anonymously verified; Batch05 still earns zero publication credit. The latest verified total remains Batch01–Batch04's 128 machine-extracted additions and 372 homepage source groups. The built-site size and publication rate for Batch05 will be recorded only after the normal completed build and live verification.

One scoped reader per rare paper covered 19 papers. The three disjoint groups removed 78 paths: 72 scientific value objects, one wrong page locator and five coupled unit fields, with zero replacement facts. Original quoted training pairs, original checker/figure metadata and common-product pairs are preserved. This is deletion-only reading, not an independent audit or a measured accuracy result. The original automatic check remains 1,054 of 1,642 values kept in 65 pairs; those historical counts precede deletions and route selection.

Eleven cohort papers are held or omitted: three technical identity holds, three with no checked pairs, and five with no retained ordinary route under the existing converter. The five route omissions are `10.1002/adma.200602373`, `10.1002/polb.10754`, `10.1038/s41565-021-00871-x`, `10.1039/b100968k`, `10.1039/c0nr00232a`. Two additional noneligible variants were left out of otherwise retained papers. These are pipeline outcomes, not findings that the original papers contain no synthesis. Five-field completeness remains informational: eight eligible records across seven papers; no new admission gate was added.

Two small Root code changes accompany preparation. Exact-change receipt construction now uses an ordered map with at most eight concurrent readers of the same fresh HEAD/index Git blobs; byte/mode/hash pins, exclusions, coverage, ordering, exception propagation and all gates are unchanged. Root ran 11 focused tests successfully. For machine-extracted composite default bulk references only, inherited trailing core/shell comparison wording is removed from the reference title so it cannot assign an interface role; existing audited records are unchanged. Root ran 20 focused JavaScript tests successfully. The initial Git patch application failed on CRLF representation; the same small change was applied manually, without weakening any check. These tests demonstrate their stated protections, not a production speedup or scientific accuracy gain.

The audited lane, its original findings and denominator, all historical failed results and every owner question remain paused and unchanged. The specifically refused Batch06 local model/controller launch remains parked with no retry or indirect workaround. Completed Batch05 integration and the unchanged local/source/browser/CI/publication path continue. No raw source quotes or training payloads are included in this report.


At 2026-10-11T12:12:16+00:00, normal conversion and asset registration have completed locally for these 39 papers, 55 records and 221 crops. All 3,214 prior canonical records remain byte identical. The quote-free 39-paper archive contains zero quote-bearing or unknown fields and zero local paths. The applied asset result matches the inspected dry run except its apply flag: 506 assets checked, 497 additions and zero new exact path rules. Only the rights-registry checksum changed in the release policy; every permission and gate remains unchanged. Build, browser, CI and publication are still pending and no Batch05 paper credit is added.


## Batch05 waiting-display correction

At 2026-10-11T12:47:35.261072+00:00, the complete R1 local Source boundary and build passed at Source `58712516d1ac75246df476a6c043bda7eb7887e7`, but Root's actual desktop visual check failed: the Cd(ClO4)2 card opened the unrelated Cd(acac)2 reference. That failed observation and all R1 proofs are retained. No R1 Source push or Batch05 publication occurred.

The converter stripped every parenthesized chemical group, causing distinct salts, polymers and tris reagents to collide. The small fix preserves exact normalized names and explicit aliases. A terminal abbreviation resolves only when both its full-name prefix and token explicitly identify the same registry entry; safe existing bindings are retained. Ten focused tests pass, including salt/polymer/tris collisions, oxidation/hydrate qualifications, abbreviation identity, safe-binding retention and immutable canonical records. The quote, number and two-pass agreement rules are unchanged.

Root corrected 30 demonstrably mismatched display bindings in 25 machine-extracted records: six bindings in five waiting Batch05 records and 24 bindings in 20 already-live machine records. All 3,269 canonical record files, every audited binding, every record-state binding, unrelated bindings and prior registry entries remain unchanged. Fourteen truthful name cards were added where an exact asset was unavailable; no molecular graph or formula was inferred. The 868 safe bindings and 71 unresolved legacy spellings were retained. These mechanical display corrections add zero paper credit and are not a scientific error-rate measurement.

Normal asset registration refreshed 698 distinct exact asset paths, added 14 registry rows and 0 exact path rules. Existing rights remain unchanged, including unverified source-figure publisher permission; the policy refresh is limited to its registry checksum.

Choice: fix the concrete display collisions and use truthful name cards for unmatched names, preserving recipe values and existing audited content. A cohesive correction commit on the same Batch05 branch keeps the eventual ordinary batch merge reversible. Fresh complete checks and desktop/phone visuals precede any push. Batch05 remains 39 papers, 55 records and 221 crops pending publication, with zero credit; Batch06's refused launch remains omitted with no workaround.


## Batch05 CI correction — publication pending

At 2026-10-11T13:22:36.991640+00:00, exact-head Source [CI 38142224825](https://github.com/cuiyist/mattersyn/actions/runs/38142224825) failed on Ubuntu and Windows at the existing reviewed-source-figure-access step. Its two assertions still expected inherited core/shell or component suffixes on machine-extracted composite reference titles. The artifact comparison was skipped; PR #18 was not merged, and Batch05 adds zero published papers. The failed CI logs and R2 full-check and visual evidence are retained.

Root reproduced the result locally: 167 JavaScript tests, 165 passed and two failed. The narrow test correction requires exact neutral titles for machine-extracted composites across six architecture states, while preserving original core/shell titles for audited, pending and unknown statuses. It also checks cell/model/CIF/formula identities and input immutability. All 167 existing JavaScript tests now pass, with zero failures or skips. No runtime, canonical record, reviewed content, extraction predicate, rights rule or release gate was changed for this correction.

Choice: run the existing full JavaScript test set locally before the unchanged five Source/boundary/snapshot/build phases, so CI does not discover those assertions first. Fresh normal file-list binding, complete local checks and exact-head CI are still required; the earlier 13-step build contained Python checks but did not itself run the separate JavaScript suites. The prior chemical display correction and its actual desktop/phone review remain on record; no future build, merge or deployment success is asserted.

The Batch04 crop-copy cleanup verification remains parked because an HTTP preview directory was unknown to its existing active-use guard. No deletion occurred. The first diagnostic wrapper returned without native inspection because its imported LibraryOnly flag affected its caller; no process ownership was inferred. The earlier R2 preview timeout and error-page reload restriction were resolved by a fresh tab in the same browser after the normal escalated loopback preview started; no browser security warning was bypassed. Batch06's specifically refused generation launch is still omitted, with no retry or indirect workaround.
