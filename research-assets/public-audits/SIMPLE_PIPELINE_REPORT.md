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


### simple-batch05-caption-repair-r4-20261011

Anonymous verification passed at 2026-10-11T15:42:48+00:00: 816 files, zero mismatches. [Source commit](https://github.com/cuiyist/mattersyn/commit/3df0f9b15183f58054b4db28bff9f1e7a47f8c96) and [Site commit](https://github.com/cuiyist/mattersyn-site/commit/6817a4a523d82e91a46afc6279ae6e5cffbcc6dc). This batch contains 39 source groups, 55 records and 229 source figure crops; 39 distinct newly contributing primary papers after DOI deduplication. Every new contribution remains machine extracted and not independently audited. The final built site is 1,421,685,200 bytes / 28,419 files.

Live counter: **244 audited + 167 machine extracted = 411 papers**, 3,269 canonical records, 309 direct material families, 354 material/component pages and 864 displayed recipe–structure pairs (6 more comprehensive; 858 partial). These display counts do not establish extraction accuracy, measured atomic coordinates or training eligibility.

Recorded source pr: [19](https://github.com/cuiyist/mattersyn/pull/19).

Recorded source ci run: [38149304791](https://github.com/cuiyist/mattersyn/actions/runs/38149304791).

| Primary DOI | Records | Figure crops | Public page |
| --- | ---: | ---: | --- |
| 10.1016/j.cap.2021.07.001 | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/a2021-j-cap-2021-07-001-cdse-zns-qds-1.html) |
| 10.1103/physrevb.66.205312 | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/braun2002-physrevb-66-205312-cds-hgs-cds-quantum-dotquantum-well-qdqw-1.html) |
| 10.1021/acs.chemmater.0c04569 | 1 | 7 | [Open](https://cuiyist.github.io/mattersyn-site/records/brown2021-acs-chemmater-0c04569-cspbbr3-nanocrystals-ncs-1.html) |
| 10.1039/b315332k | 3 | 8 | [Open](https://cuiyist.github.io/mattersyn-site/records/bullen2004-b315332k-cdse-core-particles-in-zro2sio2-solgel-f-1.html) |
| 10.1039/c6ra14241a | 2 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/c6ra14241a-zcis-qds-1.html) |
| 10.1021/am403531q | 2 | 8 | [Open](https://cuiyist.github.io/mattersyn-site/records/chang2013-am403531q-cuins2-qds-ex-situ-synthesized-1.html) |
| 10.1016/j.snb.2020.129035 | 1 | 13 | [Open](https://cuiyist.github.io/mattersyn-site/records/chizhov2021-j-snb-2020-129035-zno-cspbbr3-nanocomposite-1.html) |
| 10.1063/1.3429226 | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/clarke2010-1-3429226-inas-gaas-qd-bilayer-with-seed-layer-gro-1.html) |
| 10.1039/d2na00734g | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/d2na00734g-inp-zns-core-shell-qds-1.html) |
| 10.1063/1.112568 | 2 | 2 | [Open](https://cuiyist.github.io/mattersyn-site/records/danek1994-1-112568-znse-cdse-qd-composite-with-3-5-nm-ncs-1.html) |
| 10.1021/acs.chemmater.6b01577 | 3 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/das2016-acs-chemmater-6b01577-inas-quantum-dots-1.html) |
| 10.1063/1.2133904 | 1 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/howe2005-1-2133904-inas-gaas-001-quantum-dot-qd-bilayer-str-1.html) |
| 10.1063/1.1808472 | 2 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/hu2004-1-1808472-si-zns-core-shell-nanocrystal-structures-1.html) |
| 10.1021/acsmaterialslett.1c00592 | 2 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/hu2022-acsmaterialslett-1c00592-rcspbi3-qds-1.html) |
| 10.1021/bm200889k | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/huang2011-bm200889k-cdse-zns-core-shell-qds-1.html) |
| 10.1021/acs.langmuir.5c01176 | 4 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/jena2025-acs-langmuir-5c01176-zns-cubes-370-nm-1.html) |
| 10.1186/1477-3155-6-7 | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/jr2008-1477-3155-6-7-cdse-zns-core-shell-qds-1.html) |
| 10.1016/j.solener.2019.02.019 | 1 | 9 | [Open](https://cuiyist.github.io/mattersyn-site/records/khodam2019-j-solener-2019-02-019-znti-ldh-cds-1.html) |
| 10.1021/acsanm.5c00275 | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/kim2025-acsanm-5c00275-znste-znse-zns-core-shell-shell-qds-1.html) |
| 10.1021/cg800457u | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/li2008-cg800457u-cds-ms-1.html) |
| 10.1063/1.1840098 | 1 | 8 | [Open](https://cuiyist.github.io/mattersyn-site/records/lippen2005-1-1840098-inas-qd-molecules-on-ten-period-sl-templ-1.html) |
| 10.1021/acs.chemmater.8b04876 | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/lu2019-acs-chemmater-8b04876-cspbbr3-nanoplatelets-nps-1.html) |
| 10.1039/b607124d | 2 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/oh2006-b607124d-qdp-clusters-made-from-3-nm-cdse-qds-1.html) |
| 10.1021/acsnano.3c09490 | 2 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/ondry2024-acsnano-3c09490-in1xgaxas-nanocrystals-1.html) |
| 10.1039/c9cp01923e | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/patwari2019-c9cp01923e-pbs-qd-tio2-ptz-triohybrid-1.html) |
| 10.1021/acs.bioconjchem.8b00100 | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/popow-stellmaszyk2018-acs-bioconjchem-8b00100-znonh2-qds-1.html) |
| 10.1002/crat.200410534 | 2 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/provided2006-crat-200410534-cds-nanocrystallites-sample-s1-1.html) |
| 10.1063/1.373573 | 1 | 9 | [Open](https://cuiyist.github.io/mattersyn-site/records/rodr-guez-viejo2000-1-373573-cdse-zns-core-shell-nanocrystals-embedde-1.html) |
| 10.1002/pola.23816 | 1 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/shao2010-pola-23816-cds-quantum-dot-polymer-microspheres-1.html) |
| 10.1016/j.jpowsour.2016.11.069 | 1 | 7 | [Open](https://cuiyist.github.io/mattersyn-site/records/sisman2017-j-jpowsour-2016-11-069-zno-bnrs-cds1-xsex-1.html) |
| 10.1039/b006950g | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/suyver2000-b006950g-znse-mn2-nanocrystals-1.html) |
| 10.1021/acssuschemeng.1c04985 | 1 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/terada2022-acssuschemeng-1c04985-decyl-passivated-siqds-1.html) |
| 10.1021/am501235v | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/townsend2014-am501235v-cdte-nanocrystals-1.html) |
| 10.1166/jnn.2009.j050 | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/uehara2009-jnn-2009-j050-zns-cdse-zns-core-shell-shell-1.html) |
| 10.1039/b820204d | 1 | 8 | [Open](https://cuiyist.github.io/mattersyn-site/records/weaver2009-b820204d-cdse-zns-qds-1.html) |
| 10.1039/c4ta02052a | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/x2014-c4ta02052a-cds-cdse-zno-nras-1.html) |
| 10.1021/am300877v | 2 | 9 | [Open](https://cuiyist.github.io/mattersyn-site/records/xu2012-am300877v-ncsi-mpm1-1.html) |
| 10.1021/acsaelm.9b00460 | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/xue2019-acsaelm-9b00460-n-gqd-cspbbr3-composite-1.html) |
| 10.1021/am500026a | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/yun2014-am500026a-cdse-qds-1.html) |


### simple-batch06-20261011

Anonymous verification passed at 2026-10-11T21:29:20+00:00: 624 files, zero mismatches. [Source commit](https://github.com/cuiyist/mattersyn/commit/87dd84a16767bd02841f3bc1c2c87fee797992bb) and [Site commit](https://github.com/cuiyist/mattersyn-site/commit/7bd17fb86b8cc68cfea7b797a82d4755d228c1a3). This batch contains 34 source groups, 42 records and 204 source figure crops; 34 distinct newly contributing primary papers after DOI deduplication. Every new contribution remains machine extracted and not independently audited. The final built site is 1,474,043,687 bytes / 28,962 files.

Live counter: **244 audited + 201 machine extracted = 445 papers**, 3,311 canonical records, 314 direct material families, 358 material/component pages and 1190 displayed recipe–structure pairs (6 more comprehensive; 1184 partial). These display counts do not establish extraction accuracy, measured atomic coordinates or training eligibility.

Recorded source pr: [23](https://github.com/cuiyist/mattersyn/pull/23).

Recorded source ci run: [38172845573](https://github.com/cuiyist/mattersyn/actions/runs/38172845573).

| Primary DOI | Records | Figure crops | Public page |
| --- | ---: | ---: | --- |
| 10.1021/jp909310a | 3 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/al2010-jp909310a-cdse-msqd-family-463-1.html) |
| 10.1021/nn3029716 | 1 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/al2012-nn3029716-pbse-qd-solid-with-eda-ligands-1.html) |
| 10.1007/s00339-010-6005-5 | 2 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/chakrabarti2011-s00339-010-6005-5-bilayer-inas-gaas-quantum-dot-structure-1.html) |
| 10.1021/nl100669s | 1 | 7 | [Open](https://cuiyist.github.io/mattersyn-site/records/chan2010-nl100669s-cdse-nanocrystals-1.html) |
| 10.1103/physrevlett.100.057403 | 1 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/chilla2008-physrevlett-100-057403-cdse-cds-zns-core-shell-shell-nanocrysta-1.html) |
| 10.1039/b9nr00323a | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/chu2010-b9nr00323a-qdbsa-nanospheres-1.html) |
| 10.1021/nl061165u | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/dixit2006-nl061165u-hs-peg-cooh-coated-cdse-zns-qds-1.html) |
| 10.1021/jp025541k | 1 | 9 | [Open](https://cuiyist.github.io/mattersyn-site/records/gaponik2002-jp025541k-thiol-capped-cdte-nanocrystals-1.html) |
| 10.1002/adfm.200900852 | 1 | 9 | [Open](https://cuiyist.github.io/mattersyn-site/records/heinemann2009-adfm-200900852-cdse-nanocrystals-1.html) |
| 10.1007/s11458-006-0053-6 | 2 | 7 | [Open](https://cuiyist.github.io/mattersyn-site/records/hongye2006-s11458-006-0053-6-cdse-quantum-dots-1.html) |
| 10.1186/s11671-018-2842-5 | 1 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/huang2019-s11671-018-2842-5-cds-cdse-qd-sensitized-tio2-nss-photoano-1.html) |
| 10.1021/la1034382 | 1 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/im2010-la1034382-cdse-qds-having-a-zns-glue-layer-1.html) |
| 10.1021/ja308088d | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/ithurria2012-ja308088d-cdse-cds-nanoplatelets-1.html) |
| 10.1021/ja056494n | 1 | 10 | [Open](https://cuiyist.github.io/mattersyn-site/records/ja056494n-cdse-qds-1.html) |
| 10.1021/jp103617m | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/jeong2010-jp103617m-cdse-qd-silica-composite-film-1.html) |
| 10.1021/nn3052428 | 1 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/jun2013-nn3052428-cdse-cds-zns-qdsm-1.html) |
| 10.1021/ja208670r | 1 | 8 | [Open](https://cuiyist.github.io/mattersyn-site/records/kinder2011-ja208670r-pbs-cds-core-shell-nanocrystals-1.html) |
| 10.1021/ja108261h | 2 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/li2011-ja108261h-cis-ncs-1.html) |
| 10.1063/1.2202195 | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/liu2006-1-2202195-1-32-m-inas-quantum-dot-laser-with-five-1.html) |
| 10.1103/physrevb.77.075316 | 1 | 7 | [Open](https://cuiyist.github.io/mattersyn-site/records/mentzel2008-physrevb-77-075316-pbse-nanocrystals-1.html) |
| 10.1021/ja991249n | 1 | 8 | [Open](https://cuiyist.github.io/mattersyn-site/records/mikulec2000-ja991249n-cd1-xmnxse-qds-1.html) |
| 10.1021/nl034206k | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/nl034206k-cdse-quantum-dot-microspheres-qdms-1.html) |
| 10.1021/nn101772n | 1 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/nn101772n-inas-cd-nc-films-1.html) |
| 10.1021/ja068360v | 1 | 7 | [Open](https://cuiyist.github.io/mattersyn-site/records/pradhan2007-ja068360v-mn-znse-d-dots-nucleation-doping-strateg-1.html) |
| 10.1021/jp2040604 | 1 | 11 | [Open](https://cuiyist.github.io/mattersyn-site/records/radychev2011-jp2040604-butylamine-capped-cdse-quantum-dots-1.html) |
| 10.1021/jp072463y | 2 | 9 | [Open](https://cuiyist.github.io/mattersyn-site/records/rogach2007-jp072463y-tga-capped-cdte-ncs-1.html) |
| 10.1021/cm401202t | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/schornbaum2013-cm401202t-pbse-swnt-hybrid-1.html) |
| 10.1038/ncomms3981 | 1 | 2 | [Open](https://cuiyist.github.io/mattersyn-site/records/stavrinadis2013-ncomms3981-bi-pbs-qds-bi-pb-3-2-1.html) |
| 10.1021/jp074319i | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/talapin2007-jp074319i-pbse-pbs-core-shell-nanowires-1.html) |
| 10.1021/cm303206s | 1 | 8 | [Open](https://cuiyist.github.io/mattersyn-site/records/text2013-cm303206s-iroxnh2o-modified-cdse-cds-zno-nanowire-1.html) |
| 10.1021/nl2028848 | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/x2011-nl2028848-pbse-nc-fet-infilled-with-1-nm-of-al2o3-1.html) |
| 10.1063/1.2354448 | 3 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/zhang2006-1-2354448-dot-shaped-cdte-ncs-1.html) |
| 10.1021/jp1025152 | 1 | 10 | [Open](https://cuiyist.github.io/mattersyn-site/records/zhang2010-jp1025152-pbs-qds-1.html) |
| 10.1021/jp4113816 | 1 | 11 | [Open](https://cuiyist.github.io/mattersyn-site/records/zhang2014-jp4113816-cdse-qdcepo4-tb-nanowire-heterostructure-1.html) |


### simple-batch07-20261011

Anonymous verification passed at 2026-10-11T22:58:07+00:00: 747 files, zero mismatches. [Source commit](https://github.com/cuiyist/mattersyn/commit/f9fde794a8df00b52dc3de32f2c5e6477fb59425) and [Site commit](https://github.com/cuiyist/mattersyn-site/commit/be9ae7143ec7835330d2b9cf3d74a2e8b9560362). This batch contains 36 source groups, 54 records and 216 source figure crops; 36 distinct newly contributing primary papers after DOI deduplication. Every new contribution remains machine extracted and not independently audited. The final built site is 1,548,485,559 bytes / 29,631 files.

Live counter: **244 audited + 237 machine extracted = 481 papers**, 3,365 canonical records, 325 direct material families, 371 material/component pages and 1244 displayed recipe–structure pairs (6 more comprehensive; 1238 partial). These display counts do not establish extraction accuracy, measured atomic coordinates or training eligibility.

Recorded source pr: [24](https://github.com/cuiyist/mattersyn/pull/24).

Recorded source ci run: [38178370238](https://github.com/cuiyist/mattersyn/actions/runs/38178370238).

| Primary DOI | Records | Figure crops | Public page |
| --- | ---: | ---: | --- |
| 10.1021/la703812t | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/algar2008-la703812t-cdse-zns-quantum-dots-qds-capped-with-th-1.html) |
| 10.1021/cg201682s | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/altamura2012-cg201682s-bimodal-pbs-nanocrystal-superlattice-1.html) |
| 10.1016/j.orgel.2016.03.023 | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/ankah2016-j-orgel-2016-03-023-pbs-qds-1.html) |
| 10.1021/ie402911w | 2 | 8 | [Open](https://cuiyist.github.io/mattersyn-site/records/antony2014-ie402911w-pss2cds-composite-1.html) |
| 10.1021/ja0437297 | 1 | 8 | [Open](https://cuiyist.github.io/mattersyn-site/records/battaglia2005-ja0437297-cdse-zns-cdse-dual-quantum-systems-1.html) |
| 10.1021/jacs.4c11172 | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/behera2024-jacs-4c11172-cspbbr3pbse-epitaxial-heterostructures-1.html) |
| 10.1021/jp2023346 | 1 | 8 | [Open](https://cuiyist.github.io/mattersyn-site/records/blumling2011-jp2023346-cdse-quantum-dots-1.html) |
| 10.1021/ja0459678 | 1 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/cao2004-ja0459678-cds-nanocrystals-1.html) |
| 10.1021/jp7113434 | 4 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/carlson2008-jp7113434-mpa-cdse-quantum-dots-diameter-2-1-nm-1.html) |
| 10.1021/cm202796s | 4 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/casavola2012-cm202796s-pbse-cubic-ncs-1.html) |
| 10.1021/la303812y | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/cho2013-la303812y-ldh-inp-zns-qd-composite-1.html) |
| 10.1021/acsami.4c13618 | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/gong2024-acsami-4c13618-cspbbr3-zro2-hybrid-phosphor-1.html) |
| 10.1021/jp4118369 | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/h2014-jp4118369-cu2s-fto-ce-1.html) |
| 10.1021/jp405053k | 1 | 9 | [Open](https://cuiyist.github.io/mattersyn-site/records/hanley2013-jp405053k-cdse-cds-coreshell-quantum-dots-qds-embe-1.html) |
| 10.1021/cm990371i | 2 | 8 | [Open](https://cuiyist.github.io/mattersyn-site/records/huang1999-cm990371i-cds-pei-nanocomposite-1.html) |
| 10.1021/ja800040c | 1 | 14 | [Open](https://cuiyist.github.io/mattersyn-site/records/ja800040c-pbse-nanocrystals-1.html) |
| 10.1021/jp303712y | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/kaniyankandy2012-jp303712y-g-cdte-1.html) |
| 10.1021/jp9044429 | 2 | 8 | [Open](https://cuiyist.github.io/mattersyn-site/records/keeble2009-jp9044429-cds-meh-ppv-1.html) |
| 10.1021/la703655v | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/la703655v-oleate-capped-cds-qds-1.html) |
| 10.1016/j.cap.2019.05.016 | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/noha2019-j-cap-2019-05-016-red-emitting-cdse-cds-cdzns-qds-2.html) |
| 10.1021/jp504156c | 2 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/park2014-jp504156c-l-zno-da200-1.html) |
| 10.1021/jp210528n | 1 | 11 | [Open](https://cuiyist.github.io/mattersyn-site/records/patra2012-jp210528n-cysteine-capped-cdte-quantum-dots-1.html) |
| 10.1021/cm504716s | 2 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/provided2015-cm504716s-pbse-in-n2h4-2znte-2.html) |
| 10.1021/acscentsci.5b00327 | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/pu2016-acscentsci-5b00327-mn-znse-d-dots-1.html) |
| 10.1021/acs.bioconjchem.9b00279 | 2 | 7 | [Open](https://cuiyist.github.io/mattersyn-site/records/roy2019-acs-bioconjchem-9b00279-silicon-quantum-dots-sqds-1.html) |
| 10.1021/la300515a | 2 | 7 | [Open](https://cuiyist.github.io/mattersyn-site/records/samanta2012-la300515a-cdte-cds-zns-1.html) |
| 10.1021/ja8033075 | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/santra2009-ja8033075-zns-cdse-zns-qdqw-s01-1.html) |
| 10.1021/la062497h | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/tang2007-la062497h-ag2s-nc-thin-film-1.html) |
| 10.1021/jp305388c | 2 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/text2012-jp305388c-15-s-cds-tnta-1.html) |
| 10.1021/la504139m | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/text2015-la504139m-acac-capped-5-6-mn2-doped-zns-qdot-with-1.html) |
| 10.1021/ja208878h | 1 | 7 | [Open](https://cuiyist.github.io/mattersyn-site/records/webber2012-ja208878h-cdse-tbt-1.html) |
| 10.1021/jp1110828 | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/x2011-jp1110828-cdte-qd-nbza-cbsh-supramolecular-complex-1.html) |
| 10.1021/jp206120p | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/x2011-jp206120p-cdse-cds-cdzns-zns-qds-1.html) |
| 10.1021/ja076363h | 2 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/xie2007-ja076363h-inp-nanocrystals-1.html) |
| 10.1021/ic201333y | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/yao2011-ic201333y-topo-capped-cdte-aerogel-1.html) |
| 10.1021/cm034729t | 4 | 8 | [Open](https://cuiyist.github.io/mattersyn-site/records/yu2003-cm034729t-cdte-nanocrystals-with-wurtzite-structur-1.html) |


### simple-batch08-20261011

Anonymous verification passed at 2026-10-12T00:31:26+00:00: 4,125 files, zero mismatches. [Source commit](https://github.com/cuiyist/mattersyn/commit/6da4670e33a024fa39aa52478be303cf62245e39) and [Site commit](https://github.com/cuiyist/mattersyn-site/commit/708ba0c4feb13abce6696d6ba4bce7cb157e319f). This batch contains 35 source groups, 52 records and 196 source figure crops; 35 distinct newly contributing primary papers after DOI deduplication. Every new contribution remains machine extracted and not independently audited. The final built site is 1,602,746,579 bytes / 30,293 files.

Live counter: **244 audited + 272 machine extracted = 516 papers**, 3,417 canonical records, 335 direct material families, 383 material/component pages and 1296 displayed recipe–structure pairs (6 more comprehensive; 1290 partial). These display counts do not establish extraction accuracy, measured atomic coordinates or training eligibility.

Recorded source pr: [25](https://github.com/cuiyist/mattersyn/pull/25).

Recorded source ci run: [38184483692](https://github.com/cuiyist/mattersyn/actions/runs/38184483692).

| Primary DOI | Records | Figure crops | Public page |
| --- | ---: | ---: | --- |
| 10.1002/pssa.200622106 | 4 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/al2006-pssa-200622106-sample-a-1.html) |
| 10.1021/cm1006229 | 1 | 7 | [Open](https://cuiyist.github.io/mattersyn-site/records/al2010-cm1006229-pbse-nanocrystals-capped-with-oleic-acid-1.html) |
| 10.1021/la904474h | 2 | 8 | [Open](https://cuiyist.github.io/mattersyn-site/records/al2010-la904474h-q-cdse-3-1-nm-1.html) |
| 10.1021/nn402844m | 1 | 8 | [Open](https://cuiyist.github.io/mattersyn-site/records/al2013-nn402844m-zns-nanoparticles-2.html) |
| 10.1021/nn405236k | 1 | 7 | [Open](https://cuiyist.github.io/mattersyn-site/records/al2014-nn405236k-pbs-qds-synthesized-from-pbcl2-1.html) |
| 10.1021/nl801685a | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/evans2008-nl801685a-pbse-mscs-1.html) |
| 10.1021/nn101319x | 2 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/fuke2010-nn101319x-cdse-nqd-topo-1.html) |
| 10.1016/j.materresbull.2019.110588 | 4 | 7 | [Open](https://cuiyist.github.io/mattersyn-site/records/hassan2019-j-materresbull-2019-110588-tio2-pbs-nc-1.html) |
| 10.1021/nl903217w | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/hensel2010-nl903217w-cdse-tio2-n-nanoparticle-films-1.html) |
| 10.1021/am900917n | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/hwang2010-am900917n-cds-sensitized-tio2-electrode-1.html) |
| 10.1016/j.snb.2019.02.042 | 1 | 8 | [Open](https://cuiyist.github.io/mattersyn-site/records/j-snb-2019-02-042-pbs-cqds-1.html) |
| 10.1021/nl201282v | 2 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/jasieniak2011-nl201282v-cdte-nanocrystals-1.html) |
| 10.1063/1.3028070 | 2 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/kang2008-1-3028070-topo-capped-cdse-zns-qds-1.html) |
| 10.1021/cm502763z | 1 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/kim2014-cm502763z-pbs-nanocrystals-5-5-nm-1.html) |
| 10.1039/b108062h | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/lee2002-b108062h-cds-tp-n-0-086mos2-nanohybrid-1.html) |
| 10.1039/b917634a | 1 | 7 | [Open](https://cuiyist.github.io/mattersyn-site/records/liu2009-b917634a-cdse-qd-sensitized-bicontinuous-tio2-fil-1.html) |
| 10.1038/nmat2222 | 1 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/mahler2008-nmat2222-cdsecds-coreshell-quantum-dots-with-5-nm-1.html) |
| 10.1063/1.1510157 | 1 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/mazur2002-1-1510157-vertically-aligned-double-layer-inas-gaa-1.html) |
| 10.1021/cm071410q | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/moreels2007-cm071410q-q-pbse-3-3-nm-1.html) |
| 10.1103/physrevb.73.155303 | 1 | 11 | [Open](https://cuiyist.github.io/mattersyn-site/records/porter2006-physrevb-73-155303-cdte-nanocrystals-1.html) |
| 10.1557/jmr.2010.0077 | 2 | 8 | [Open](https://cuiyist.github.io/mattersyn-site/records/reda2010-jmr-2010-0077-cds-nanoparticles-1.html) |
| 10.1007/s10854-007-9340-3 | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/ren2008-s10854-007-9340-3-zns-mn-nanoparticles-1.html) |
| 10.1021/nn406126u | 2 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/schimpf2014-nn406126u-photodoped-zno-nanocrystals-r-1-75-nm-1.html) |
| 10.1021/nn900735y | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/shallcross2009-nn900735y-ligand-capped-cdse-nanocrystal-diffracti-1.html) |
| 10.1149/1.3465655 | 2 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/song2010-1-3465655-ba2si3o8-eu2-phosphor-1.html) |
| 10.1063/1.1609634 | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/stewart2003-1-1609634-30-stack-inas-gaas-quantum-dot-infrared-1.html) |
| 10.1021/acs.chemmater.6b03585 | 2 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/tamang2016-acs-chemmater-6b03585-inas-nanoclusters-1.html) |
| 10.1063/1.1467961 | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/tang2002-1-1467961-two-stacked-inas-gaas-quantum-dot-pin-di-1.html) |
| 10.1021/nn901564q | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/tang2010-nn901564q-pbs-ncs-with-930-nm-excitonic-peak-1.html) |
| 10.1021/ac201016c | 1 | 7 | [Open](https://cuiyist.github.io/mattersyn-site/records/text2011-ac201016c-mn2-doped-zns-cys-mn-zns-cys-qds-1.html) |
| 10.1021/acsomega.0c00019 | 1 | 7 | [Open](https://cuiyist.github.io/mattersyn-site/records/text2020-acsomega-0c00019-si-qd-cluster-1.html) |
| 10.1021/am5033567 | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/tian2014-am5033567-cdse-zns-coreshell-qds-1.html) |
| 10.1021/cm034081k | 3 | 7 | [Open](https://cuiyist.github.io/mattersyn-site/records/yu2003-cm034081k-cdte-nanocrystals-1.html) |
| 10.1021/cm050260l | 2 | 9 | [Open](https://cuiyist.github.io/mattersyn-site/records/zhang2005-cm050260l-cdte-ps-composites-cfp-method-1.html) |
| 10.1021/am505371g | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/zhang2014-am505371g-cdse-cds-au-qd-au-coresatellite-hncs-ass-1.html) |


### simple-batch09-20261012

Anonymous verification passed at 2026-10-12T02:14:36+00:00: 635 files, zero mismatches. [Source commit](https://github.com/cuiyist/mattersyn/commit/4faf4932e7e8969de9406351e10c1914f845734c) and [Site commit](https://github.com/cuiyist/mattersyn-site/commit/7d53adb44fd36b1b3a32323637788e307ad81d98). This batch contains 35 source groups, 45 records and 182 source figure crops; 35 distinct newly contributing primary papers after DOI deduplication. Every new contribution remains machine extracted and not independently audited. The final built site is 1,654,212,947 bytes / 30,849 files.

Live counter: **244 audited + 307 machine extracted = 551 papers**, 3,462 canonical records, 341 direct material families, 391 material/component pages and 1341 displayed recipe–structure pairs (6 more comprehensive; 1335 partial). These display counts do not establish extraction accuracy, measured atomic coordinates or training eligibility.

Recorded source pr: [26](https://github.com/cuiyist/mattersyn/pull/26).

Recorded source ci run: [38190616336](https://github.com/cuiyist/mattersyn/actions/runs/38190616336).

| Primary DOI | Records | Figure crops | Public page |
| --- | ---: | ---: | --- |
| 10.1063/1.1374235 | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/borgstrom2001-1-1374235-inas-quantum-dot-stacks-embedded-in-inp-1.html) |
| 10.1039/c3ta10255f | 1 | 7 | [Open](https://cuiyist.github.io/mattersyn-site/records/chen2013-c3ta10255f-core-shell-cdte-cds-qd-tio2-nanotube-arr-1.html) |
| 10.1038/s41598-017-00669-9 | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/choi2017-s41598-017-00669-9-pbs-qd-ink-1.html) |
| 10.1063/1.2011768 | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/choudhury2005-1-2011768-pbse-quantum-dots-in-poly-n-vinylcarbazo-1.html) |
| 10.1021/jp807591d | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/cui2008-jp807591d-topo-capped-cdte-qd-1.html) |
| 10.1038/nature03832 | 2 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/erwin2005-nature03832-mn-doped-znse-nanocrystals-1.html) |
| 10.1063/1.1781361 | 1 | 2 | [Open](https://cuiyist.github.io/mattersyn-site/records/holub2004-1-1781361-inas-mn-quantum-dot-multilayer-1.html) |
| 10.1021/jacs.0c10916 | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/imran2021-jacs-0c10916-cspbbr3pb4s3br2-heterostructures-1.html) |
| 10.1103/physrevb.70.195327 | 1 | 8 | [Open](https://cuiyist.github.io/mattersyn-site/records/jarosz2004-physrevb-70-195327-cdse-quantum-dots-qds-with-a-diameter-of-1.html) |
| 10.1021/la052197k | 1 | 9 | [Open](https://cuiyist.github.io/mattersyn-site/records/joumaa2006-la052197k-topo-coated-cdse-zns-qd-tagged-polystyre-1.html) |
| 10.1021/jp4110773 | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/jumabekov2014-jp4110773-pbs-qd-sensitized-tio2-electrodes-1.html) |
| 10.1063/1.2966341 | 2 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/kim2008-1-2966341-cdse-decorated-fluorinated-double-walled-1.html) |
| 10.1021/acsanm.2c00717 | 1 | 8 | [Open](https://cuiyist.github.io/mattersyn-site/records/koc2022-acsanm-2c00717-nitrogen-doped-carbon-quantum-dots-n-cqd-1.html) |
| 10.1039/b817000b | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/lan2009-b817000b-tio2-3-pdda-qdcdte-3-fto-1.html) |
| 10.1021/jp205844r | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/lee2011-jp205844r-cdse-cds-zno-nw-1.html) |
| 10.1021/jp508315m | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/lee2014-jp508315m-cdse-a-tio2-1.html) |
| 10.1021/jp101695s | 1 | 9 | [Open](https://cuiyist.github.io/mattersyn-site/records/leschkies2010-jp101695s-edt-treated-pbse-qd-films-1.html) |
| 10.1021/ja204538f | 3 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/li2011-ja204538f-cds-nanocrystals-classic-approach-1.html) |
| 10.1021/jp066018z | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/liu2007-jp066018z-mwnts-sno2-1.html) |
| 10.1021/ie501035s | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/liu2014-ie501035s-fluorescent-spherical-polyelectrolyte-br-1.html) |
| 10.1038/nmat902 | 1 | 1 | [Open](https://cuiyist.github.io/mattersyn-site/records/manna2003-nmat902-cdte-tetrapods-1.html) |
| 10.1063/1.370578 | 2 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/nan1999-1-370578-undoped-nanocrystalline-zno-pz1-1.html) |
| 10.1021/nl3027444 | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/otto2012-nl3027444-cdte-qds-embedded-in-nacl-mixed-crystals-1.html) |
| 10.1021/jp803845n | 3 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/ouyang2008-jp803845n-family-513-cdse-msns-1.html) |
| 10.1021/nl203620f | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/pal2012-nl203620f-cdse-16cds-g-nqds-1.html) |
| 10.1021/jp020453l | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/plass2002-jp020453l-pbs-quantum-dots-on-tio2-1.html) |
| 10.1021/ja017002j | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/qu2002-ja017002j-cdse-nanocrystals-1.html) |
| 10.1021/jp410599q | 1 | 8 | [Open](https://cuiyist.github.io/mattersyn-site/records/shen2014-jp410599q-cdse-qds-capped-with-top-1.html) |
| 10.1021/jp306255g | 3 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/shepherd2012-jp306255g-cdse-qds-capped-with-oleic-acid-tri-n-oc-1.html) |
| 10.1021/am500429c | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/sohn2014-am500429c-cuins2-zns-qdes-1.html) |
| 10.1021/jp209832h | 1 | 8 | [Open](https://cuiyist.github.io/mattersyn-site/records/text2012-jp209832h-cdte-qds-1.html) |
| 10.1557/jmr.2004.0420 | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/wang2004-jmr-2004-0420-cdse-magic-sized-nanoclusters-1.html) |
| 10.1021/jp210062x | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/wang2012-jp210062x-cdse-zns-qds-1.html) |
| 10.1021/jp044531b | 2 | 8 | [Open](https://cuiyist.github.io/mattersyn-site/records/warner2005-jp044531b-1-nm-pbs-nc-p-composite-1.html) |
| 10.1038/nmat3118 | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/x2011-nmat3118-br-capped-pbs-cqd-film-1.html) |


### simple-batch10-20261012

Anonymous verification passed at 2026-10-12T03:55:31+00:00: 645 files, zero mismatches. [Source commit](https://github.com/cuiyist/mattersyn/commit/f1e3acd3d1a2666f7b09e04e3f0ae1593b248817) and [Site commit](https://github.com/cuiyist/mattersyn-site/commit/a4b117846e4f1e36701201acb53b2dfeb9b8644c). This batch contains 35 source groups, 53 records and 181 source figure crops; 35 distinct newly contributing primary papers after DOI deduplication. Every new contribution remains machine extracted and not independently audited. The final built site is 1,711,933,632 bytes / 31,409 files.

Live counter: **244 audited + 342 machine extracted = 586 papers**, 3,515 canonical records, 353 direct material families, 407 material/component pages and 1394 displayed recipe–structure pairs (6 more comprehensive; 1388 partial). These display counts do not establish extraction accuracy, measured atomic coordinates or training eligibility.

Recorded source pr: [27](https://github.com/cuiyist/mattersyn/pull/27).

Recorded source ci run: [38197718624](https://github.com/cuiyist/mattersyn/actions/runs/38197718624).

| Primary DOI | Records | Figure crops | Public page |
| --- | ---: | ---: | --- |
| 10.1021/la701012j | 3 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/al2007-la701012j-qdps-colloids-4-m-540-nm-1.html) |
| 10.1021/nn103024b | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/al2011-nn103024b-qd-fen-1.html) |
| 10.1021/nn203683s | 1 | 7 | [Open](https://cuiyist.github.io/mattersyn-site/records/al2011-nn203683s-cdse-c1-1.html) |
| 10.1021/nn2044388 | 1 | 7 | [Open](https://cuiyist.github.io/mattersyn-site/records/al2012-nn2044388-cdses-zns-1.html) |
| 10.1021/nn403132x | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/al2013-nn403132x-cdse-nanowires-nws-1.html) |
| 10.1021/nn403190s | 1 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/al2013-nn403190s-pbs-qds-1.html) |
| 10.1021/cm501739h | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/al2014-cm501739h-pbs-cds-core-shell-nanocrystals-1.html) |
| 10.1021/bc400157z | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/bestel2013-bc400157z-cdse-zns-quantum-dots-qds-encapsulated-i-1.html) |
| 10.1039/c9na00334g | 3 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/c9na00334g-cdse-cds-qd-mpa-1.html) |
| 10.1038/srep04085 | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/chen2014-srep04085-zncdses-qds-1.html) |
| 10.1038/s41560-020-0617-6 | 3 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/du2020-s41560-020-0617-6-zn-cuinse2-qds-with-oam-ligands-1.html) |
| 10.1021/nn7003469 | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/gooding2008-nn7003469-cdse-cds-zns-nanocrystals-1.html) |
| 10.1021/am403173n | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/ho2013-am403173n-green-cdsezns-qds-1.html) |
| 10.1021/ja061644v | 2 | 2 | [Open](https://cuiyist.github.io/mattersyn-site/records/houtepen2006-ja061644v-pbse-ncs-spherical-1.html) |
| 10.1021/am504536a | 1 | 8 | [Open](https://cuiyist.github.io/mattersyn-site/records/huang2014-am504536a-oa-cdse-qds-1.html) |
| 10.1021/jp312190x | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/itzhakov2013-jp312190x-cdte-cdse-core-shell-nanocrystals-1.html) |
| 10.1021/nn100076f | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/jiang2010-nn100076f-cdse-nanorods-1.html) |
| 10.1021/acs.chemmater.3c01359 | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/jo2023-acs-chemmater-3c01359-in-zn-p-znse-zns-qds-1.html) |
| 10.1021/nl071225b | 2 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/jua-rez2007-nl071225b-cdse-nanorods-1.html) |
| 10.1038/s41467-019-08432-6 | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/jung2019-s41467-019-08432-6-cdse-cd1xznxse1ysy-core-alloyed-shell-co-1.html) |
| 10.1039/c8ra08136k | 1 | 14 | [Open](https://cuiyist.github.io/mattersyn-site/records/kathirgamanathan2018-c8ra08136k-zno-m1-1.html) |
| 10.1021/jp906096a | 1 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/kim2009-jp906096a-cds-quantum-dots-1.html) |
| 10.1038/nnano.2011.46 | 2 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/lee2011-nnano-2011-46-cdse-nanocrystals-with-in2se4-2-ligands-1.html) |
| 10.1021/nn402870e | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/lee2013-nn402870e-cdzns-zns-qds-3-h-shelled-1.html) |
| 10.1021/am5012782 | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/li2014-am5012782-cdse-cds-cdxzn1xs-zns-qd-nanobeads-1.html) |
| 10.1021/nn403594j | 2 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/lim2013-nn403594j-inp-znses-qds-with-1-1-nm-shell-thicknes-1.html) |
| 10.1021/jp0646123 | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/murphy2006-jp0646123-oleate-capped-pbse-nanocrystals-1.html) |
| 10.1002/pssc.200671556 | 2 | 2 | [Open](https://cuiyist.github.io/mattersyn-site/records/passow2006-pssc-200671556-inas-gaas-quantum-dots-qds-with-high-den-1.html) |
| 10.1063/1.3530466 | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/s-g-pawar-1-3530466-nanocrystalline-pbs-thin-films-1.html) |
| 10.1021/jp109301d | 2 | 9 | [Open](https://cuiyist.github.io/mattersyn-site/records/x2011-jp109301d-si-ncs-fragmented-in-ethanol-1.html) |
| 10.1021/jz5015086 | 3 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/x2014-jz5015086-oleic-acid-capped-pbs-ncs-1.html) |
| 10.1063/1.121906 | 3 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/xua1998-1-121906-zns-cu-1.html) |
| 10.1039/b815034f | 2 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/yang2008-b815034f-cds-nc-1-1.html) |
| 10.1021/nn100339b | 2 | 7 | [Open](https://cuiyist.github.io/mattersyn-site/records/zarghami2010-nn100339b-6-1-nm-pbse-qds-1.html) |
| 10.1021/nn5040444 | 1 | 8 | [Open](https://cuiyist.github.io/mattersyn-site/records/zhou2014-nn5040444-cdte-nc-self-assembly-materials-1.html) |


### simple-batch11-20261012

Anonymous verification passed at 2026-10-12T05:46:50+00:00: 565 files, zero mismatches. [Source commit](https://github.com/cuiyist/mattersyn/commit/28de5bb49100fbc39efb13568568e57a4f994abd) and [Site commit](https://github.com/cuiyist/mattersyn-site/commit/cac61f2667fe351fc771d7ea0be91a1df0a6f1e8). This batch contains 32 source groups, 43 records and 141 source figure crops; 32 distinct newly contributing primary papers after DOI deduplication. Every new contribution remains machine extracted and not independently audited. The final built site is 1,749,842,236 bytes / 31,894 files.

Live counter: **244 audited + 374 machine extracted = 618 papers**, 3,558 canonical records, 360 direct material families, 415 material/component pages and 1437 displayed recipe–structure pairs (6 more comprehensive; 1431 partial). These display counts do not establish extraction accuracy, measured atomic coordinates or training eligibility.

Recorded source pr: [28](https://github.com/cuiyist/mattersyn/pull/28).

Recorded source ci run: [38204759466](https://github.com/cuiyist/mattersyn/actions/runs/38204759466).

| Primary DOI | Records | Figure crops | Public page |
| --- | ---: | ---: | --- |
| 10.1063/1.46441 | 1 | 0 | [Open](https://cuiyist.github.io/mattersyn-site/records/11994-1-46441-cds-nanocrystalline-materials-1.html) |
| 10.1016/j.electacta.2011.02.071 | 3 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/al2011-j-electacta-2011-02-071-zn2sno4-nanoparticles-1.html) |
| 10.1021/nn401657n | 1 | 8 | [Open](https://cuiyist.github.io/mattersyn-site/records/al2013-nn401657n-pbse-nanoparticles-capped-with-pb-oleate-1.html) |
| 10.1021/nn500852g | 2 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/al2014-nn500852g-cdse-zns-qds-1.html) |
| 10.1021/nn502588k | 2 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/al2014-nn502588k-cdse-zns-core-shell-qds-green-emitting-1.html) |
| 10.1039/d4tc01805b | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/cao2024-d4tc01805b-sno2-qds-pbs-i-qds-pbs-edt-qds-1.html) |
| 10.1021/jz401780w | 1 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/cate2013-jz401780w-pbse-edt-qd-solid-1.html) |
| 10.1021/cm803248j | 1 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/cm803248j-p3ht-cdse-nanocomposite-1.html) |
| 10.1021/jp302992k | 1 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/dutta2012-jp302992k-graphene-quantum-dots-gqds-1.html) |
| 10.1038/nature10569 | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/galland12011-nature10569-cdse-cds-nanocrystals-1.html) |
| 10.1021/jp9823603 | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/gao1998-jp9823603-cdte-nanocrystals-fraction-i-1.html) |
| 10.1021/ac202910y | 1 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/han2012-ac202910y-zns-nccs-44-nm-1.html) |
| 10.1021/ja903445f | 4 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/joo2009-ja903445f-pbse-nqds-radius-1-2-nm-1.html) |
| 10.1021/jp411214n | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/lee2014-jp411214n-cdse-tps-1.html) |
| 10.1063/1.3100196 | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/li2009-1-3100196-cds-quantum-rods-qrs-1.html) |
| 10.1186/s11671-016-1606-3 | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/liu2016-s11671-016-1606-3-cdse-zns-qds-1.html) |
| 10.1063/1.110838 | 3 | 2 | [Open](https://cuiyist.github.io/mattersyn-site/records/mukherjee1994-1-110838-pbs-polyacrylamide-composite-specimen-no-1.html) |
| 10.1007/s00604-007-0770-7 | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/munro2008-s00604-007-0770-7-cdse-cdzns-zns-core-shell-shell-quantum-1.html) |
| 10.1038/s41467-019-14014-3 | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/nurmikko2020-s41467-019-14014-3-cg-qds-cdse-cdxzn1xse-znse0-5s0-5-zns-1.html) |
| 10.1021/ph400011z | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/parand2014-ph400011z-graphene-pbs-composite-counter-electrode-1.html) |
| 10.1021/ja0027766 | 1 | 2 | [Open](https://cuiyist.github.io/mattersyn-site/records/peng2001-ja0027766-cdse-quantum-rods-1.html) |
| 10.1021/jp409937z | 1 | 9 | [Open](https://cuiyist.github.io/mattersyn-site/records/rath2013-jp409937z-mn-doped-zns-nanocrystals-with-a-shell-l-1.html) |
| 10.1063/1.2993178 | 3 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/sritirawisarn2008-1-2993178-2-6-ml-inas-qd-arrays-with-0-6-ml-gaas-i-1.html) |
| 10.1007/s11671-007-9040-1 | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/strom2007-s11671-007-9040-1-inas-quantum-dots-on-gaas-ring-like-nano-1.html) |
| 10.1038/srep10626 | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/sun2015-srep10626-pbs-quantum-dots-1.html) |
| 10.1021/jp505812q | 1 | 7 | [Open](https://cuiyist.github.io/mattersyn-site/records/tournebize2014-jp505812q-eht-capped-cuins2-ncs-1.html) |
| 10.1111/j.1551-2916.2004.00084.x | 1 | 1 | [Open](https://cuiyist.github.io/mattersyn-site/records/wang2004-j-1551-2916-2004-00084-x-zno-nanocrystalline-coatings-1.html) |
| 10.1021/jp112010m | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/x2011-jp112010m-pbs-counter-electrode-pbs-ce-1.html) |
| 10.1007/s11426-010-3098-9 | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/xianxiang12010-s11426-010-3098-9-guvs-cdte-1.html) |
| 10.1021/la904488w | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/yu2010-la904488w-lac-qds-1.html) |
| 10.1021/am404811j | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/yu2014-am404811j-cdte-cds-coreshell-qds-capped-with-3-mer-1.html) |
| 10.1021/jp303766d | 1 | 8 | [Open](https://cuiyist.github.io/mattersyn-site/records/zillner2012-jp303766d-cdse-qds-4-5-nm-with-pyridine-surfactant-3.html) |


### simple-batch12-20261012

Anonymous verification passed at 2026-10-12T08:53:49+00:00: 517 files, zero mismatches. [Source commit](https://github.com/cuiyist/mattersyn/commit/4a8118eb2b80c5c1f5cf37502edbc62beccd06b6) and [Site commit](https://github.com/cuiyist/mattersyn-site/commit/6877d67fa957d8e057388cff277cff7aead590c9). This batch contains 30 source groups, 36 records and 140 source figure crops; 30 distinct newly contributing primary papers after DOI deduplication. Every new contribution remains machine extracted and not independently audited. The final built site is 1,791,003,129 bytes / 32,335 files.

Live counter: **244 audited + 404 machine extracted = 648 papers**, 3,594 canonical records, 365 direct material families, 422 material/component pages and 1473 displayed recipe–structure pairs (6 more comprehensive; 1467 partial). These display counts do not establish extraction accuracy, measured atomic coordinates or training eligibility.

Recorded source pr: [29](https://github.com/cuiyist/mattersyn/pull/29).

Recorded source ci run: [38216306647](https://github.com/cuiyist/mattersyn/actions/runs/38216306647).

| Primary DOI | Records | Figure crops | Public page |
| --- | ---: | ---: | --- |
| 10.1021/nn203728t | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/al2011-nn203728t-pbs-nanocrystals-capped-with-c18-oleic-a-1.html) |
| 10.1021/nn4017845 | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/al2013-nn4017845-cdse-cds-seeded-rods-1.html) |
| 10.1021/nn4021983 | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/al2013-nn4021983-pbs-cqds-with-cdcl2-passivation-1.html) |
| 10.1021/jp9019574 | 2 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/banerjee2009-jp9019574-cds-mn-zns-qdots-1.html) |
| 10.1021/nn100021b | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/buhbut2010-nn100021b-cdse-cds-zns-qds-1.html) |
| 10.1002/smll.200600218 | 3 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/chang2006-smll-200600218-cdse-cds-core-shell-qds-with-no-peg-coat-1.html) |
| 10.1063/1.3117221 | 1 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/chen2009-1-3117221-oa-capped-cdse-qd-3-nm-1.html) |
| 10.1021/jp8099169 | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/halpert2009-jp8099169-qd550-ttbc-1.html) |
| 10.1021/nn303769h | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/hendricks2012-nn303769h-cds-nanocrystals-1.html) |
| 10.1002/adfm.201000711 | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/hu2010-adfm-201000711-qdmm-sio2-1.html) |
| 10.1063/1.126759 | 1 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/kim2000-1-126759-cdse-pyridine-1.html) |
| 10.1166/jnn.2008.1221 | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/kim2008-jnn-2008-1221-zno-nanowire-cdte-quantum-dot-hybrid-sys-1.html) |
| 10.1021/nl200704h | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/kim2011-nl200704h-pbse-nanocrystal-layer-1.html) |
| 10.1039/d4mh01182a | 2 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/kim2025-d4mh01182a-ingap-qds-1.html) |
| 10.1021/nn8003247 | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/koole2008-nn8003247-cdse-qds-2-8-nm-qy-40-1.html) |
| 10.1021/ic401587r | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/l2014-ic401587r-znse-zns-qds-1.html) |
| 10.1063/1.2906121 | 1 | 8 | [Open](https://cuiyist.github.io/mattersyn-site/records/lioudakis2008-1-2906121-pbs-qds-pei-multilayers-1.html) |
| 10.1063/1.2358847 | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/mi2006-1-2358847-metamorphic-inas-tunnel-injection-quantu-1.html) |
| 10.1021/jp205419z | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/pang2011-jp205419z-mpa-qds-4-atp-gce-1.html) |
| 10.1016/j.jpowsour.2014.12.022 | 1 | 8 | [Open](https://cuiyist.github.io/mattersyn-site/records/shen2015-j-jpowsour-2014-12-022-cdte-cds-qds-1.html) |
| 10.1016/j.cej.2024.158969 | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/shen2025-j-cej-2024-158969-pbs-qds-1.html) |
| 10.1039/b111013f | 1 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/sun2002-b111013f-pdda-cdte-n-film-1.html) |
| 10.1021/nl204323j | 2 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/tang2012-nl204323j-pbs-nanocrystals-1.html) |
| 10.1021/ac503134r | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/text2014-ac503134r-zns-mn-ncs-1.html) |
| 10.1007/s10853-008-3138-4 | 1 | 2 | [Open](https://cuiyist.github.io/mattersyn-site/records/wang2009-s10853-008-3138-4-mps-capped-cdse-zns-core-shell-qds-1.html) |
| 10.1021/nn3045215 | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/wang2013-nn3045215-520-nm-cdse-cds-zns-qd-barcodes-1.html) |
| 10.1021/ac501020b | 2 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/wang2014-ac501020b-paa-qds-1.html) |
| 10.1007/s11671-010-9632-z | 1 | 2 | [Open](https://cuiyist.github.io/mattersyn-site/records/x2010-s11671-010-9632-z-si-ncs-1.html) |
| 10.1021/jp206443p | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/zhao2011-jp206443p-qd-encoded-sio2-nps-1.html) |
| 10.1021/am505130a | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/zhou2014-am505130a-cdse-qds-modified-with-1-4-benzenedithio-1.html) |


### simple-batch13-20261012

Anonymous verification passed at 2026-10-12T10:56:14+00:00: 692 files, zero mismatches. [Source commit](https://github.com/cuiyist/mattersyn/commit/4f19ef73a2d26e90f30ab858e533ba32759229de) and [Site commit](https://github.com/cuiyist/mattersyn-site/commit/d97167b301b7a95cd5c3791a23fa4c0d1131348f). This batch contains 34 source groups, 56 records and 192 source figure crops; 34 distinct newly contributing primary papers after DOI deduplication. Every new contribution remains machine extracted and not independently audited. The final built site is 1,836,734,561 bytes / 32,948 files.

Live counter: **244 audited + 438 machine extracted = 682 papers**, 3,650 canonical records, 376 direct material families, 437 material/component pages and 1529 displayed recipe–structure pairs (6 more comprehensive; 1523 partial). These display counts do not establish extraction accuracy, measured atomic coordinates or training eligibility.

Recorded source pr: [30](https://github.com/cuiyist/mattersyn/pull/30).

Recorded source ci run: [38231455521](https://github.com/cuiyist/mattersyn/actions/runs/38231455521).

| Primary DOI | Records | Figure crops | Public page |
| --- | ---: | ---: | --- |
| 10.1007/s12645-010-0003-3 | 1 | 9 | [Open](https://cuiyist.github.io/mattersyn-site/records/al-s12645-010-0003-3-cdte-folic-acid-nanoconjugates-1.html) |
| 10.1002/smll.200600558 | 1 | 2 | [Open](https://cuiyist.github.io/mattersyn-site/records/al2007-smll-200600558-a-iii-1.html) |
| 10.1021/nn201455a | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/al2011-nn201455a-cdte-qds-1.html) |
| 10.1021/nn505343e | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/al2014-nn505343e-lead-oleatempa-complex-1.html) |
| 10.1007/s00339-003-2503-z | 2 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/arici12004-s00339-003-2503-z-topo-capped-cuinse2-nanoparticles-1.html) |
| 10.1021/cg049752l | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/belman2005-cg049752l-ag2s-nanocrystals-on-pda-1.html) |
| 10.1021/acsenergylett.2c01486 | 2 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/bera2022-acsenergylett-2c01486-cd-doped-cspbbr3-star-nanocrystals-1.html) |
| 10.1021/jp027485t | 2 | 10 | [Open](https://cuiyist.github.io/mattersyn-site/records/borchert2003-jp027485t-cds-hgs-cds-quantum-dot-quantum-well-nan-1.html) |
| 10.1021/jz4007492 | 3 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/cate2013-jz4007492-infilled-pbse-edt-qd-solid-with-al2o3-1.html) |
| 10.1021/cm980715p | 3 | 10 | [Open](https://cuiyist.github.io/mattersyn-site/records/dijken1998-cm980715p-cds-1.html) |
| 10.1021/ja4072207 | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/gamelin2013-ja4072207-cd1xmnxse-nanocrystals-1.html) |
| 10.1016/j.jcis.2011.02.002 | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/generalova2011-j-jcis-2011-02-002-polyacrolein-particles-labeled-with-cdse-1.html) |
| 10.1021/cm2021593 | 2 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/han2011-cm2021593-cdse-zns-qdots-1-qdots-1.html) |
| 10.1063/1.1525396 | 1 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/hens2002-1-1525396-cdse-nanocrystals-linked-via-hdt-to-au-1-1.html) |
| 10.1016/j.jcat.2016.11.028 | 2 | 7 | [Open](https://cuiyist.github.io/mattersyn-site/records/j-jcat-2016-11-028-cqds-zno-ga-zno-composite-nanorod-array-1.html) |
| 10.1021/jp5005242 | 1 | 7 | [Open](https://cuiyist.github.io/mattersyn-site/records/jin2014-jp5005242-cdse-qds-capped-with-sns4-4-ligands-1.html) |
| 10.1021/jp305607t | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/kramer2012-jp305607t-cdse-nanocrystal-film-1.html) |
| 10.1021/acs.nanolett.1c03011 | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/lan2021-acs-nanolett-1c03011-h-t-cspbi3-qds-1.html) |
| 10.1021/jp0644356 | 3 | 11 | [Open](https://cuiyist.github.io/mattersyn-site/records/lifshitz2006-jp0644356-pbse-core-nqds-1.html) |
| 10.1021/acs.cgd.3c01273 | 4 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/lopez-dominguez2024-acs-cgd-3c01273-bazro3-ncs-1.html) |
| 10.1021/jp9828179 | 1 | 9 | [Open](https://cuiyist.github.io/mattersyn-site/records/murase1999-jp9828179-mn-zns-nanocrystals-1.html) |
| 10.1021/ja803325b | 1 | 7 | [Open](https://cuiyist.github.io/mattersyn-site/records/murcia2008-ja803325b-lipo-coated-cdse-zns-qds-2.html) |
| 10.1021/ja209062d | 2 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/nagaoka2012-ja209062d-pbse-nc-superlattice-face-centered-cubic-1.html) |
| 10.1007/s10854-009-9920-5 | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/patil2010-s10854-009-9920-5-zno-thin-film-1.html) |
| 10.1021/la8022985 | 1 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/schabas2008-la8022985-quantum-dot-compound-micelles-qdcms-1.html) |
| 10.1039/b800028j | 4 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/stouwdam2008-b800028j-zno-nanocrystals-1.html) |
| 10.1021/jp014559c | 1 | 8 | [Open](https://cuiyist.github.io/mattersyn-site/records/tang2002-jp014559c-12-nm-pbse-nanocrystals-1.html) |
| 10.1021/cm503626s | 3 | 8 | [Open](https://cuiyist.github.io/mattersyn-site/records/tisdale-mit-edu2015-cm503626s-pbs-qds-small-diameter-1.html) |
| 10.1021/la200509z | 1 | 2 | [Open](https://cuiyist.github.io/mattersyn-site/records/travert-branger2011-la200509z-cdse-zns-nanocrystals-encapsulated-in-po-1.html) |
| 10.1021/jp073022h | 1 | 13 | [Open](https://cuiyist.github.io/mattersyn-site/records/wang2007-jp073022h-pbse-nc-tiox-heterostructured-films-1.html) |
| 10.1021/jz200080d | 1 | 5 | [Open](https://cuiyist.github.io/mattersyn-site/records/wolcott2011-jz200080d-pbse-qds-d-5-4-0-3-nm-with-oa-capping-1.html) |
| 10.1021/la102407s | 1 | 6 | [Open](https://cuiyist.github.io/mattersyn-site/records/yang2010-la102407s-hgs-nanocrystal-aggregates-1.html) |
| 10.1021/am503580j | 1 | 4 | [Open](https://cuiyist.github.io/mattersyn-site/records/yang2014-am503580j-gnrs-and-qds-codoped-polymer-nanofiber-1.html) |
| 10.1021/la7002904 | 3 | 3 | [Open](https://cuiyist.github.io/mattersyn-site/records/yusuf2007-la7002904-bc-qd-1.html) |

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

## Batch05 normal-preview caption repair

Status at 2026-10-11T14:29:22.463923+00:00: Source R3 CI 38144237490 passed all three required jobs and PR #18 merged as `f9fcc60c53921d4c038848eaea3b649d5ad79ed4`. The normal release built byte-identical candidate/final artifacts and both final and staged-site boundary checks passed all 28,411 files with zero failures. Root then observed all 79 required preview routes at desktop width: 76 met the loaded-figure criterion; three routes for two papers had no figure cards. All identity, machine-status, conceptual-caption, cell-or-unavailable, overflow and console predicates passed. No browser approval, Site push or new-paper credit is asserted for this attempt. Live totals remain the verified Batch04 totals, 372 source groups and 128 new simple-lane papers.

Local technical inspection found zero caption candidates before model classification for JR2008 and Shao2010, despite image/graphic geometry. The narrow causes are standalone caption labels inside a text block and case-sensitive matching of uppercase plain labels. Empty extraction is not evidence that a source has no figures. Choice: repair these two caption-layout cases and rerun only their local figure extraction; this preserves the waiting batch's figures without changing extraction values or the three quote/number/two-pass checks. Omit either paper if a usable crop still cannot be produced. Preserve the previous R1/R2/R3 failure and check history. Batch06's automatic approval rejection remains parked without retry or workaround.


## Batch 05 caption repair R4 preparation

At 2026-10-11T14:39:37.628854+00:00, the normal local figure command recovered five crops for JR (10.1186/1477-3155-6-7) and three for Shao (10.1002/pola.23816). Root inspected all eight crops: whole panels are visible; two crops also include a journal running header. Their paper-level categories and locators remain separate from sample assignments. The correction adds eight registered crops (229 in the pending batch), leaves all 3,269 canonical record files byte-identical and preserves every other paper’s presentation. It adds no live paper credit.

Script fix: accept all-capital unpunctuated caption labels while retaining the body-text guard; restore one detached figure label only when its line occupies the caption block’s physical top-left. No extraction prompt or quote/number/two-pass agreement rule changed. All 14 focused caption tests and all 95 synthetic pipeline tests passed with no skipped test. Choice: repair the caption detector and re-extract only these two papers’ figures, because their scientific values and earlier accepted work do not need re-extraction. The fresh Source and Site gates and browser review remain pending; the R3 sealed-preview figure failure is retained.

## Batch05 verified milestone

Batch05 is deployed and anonymously verified at 2026-10-11T15:42:48+00:00, from Source `3df0f9b15183f58054b4db28bff9f1e7a47f8c96` and Site `6817a4a523d82e91a46afc6279ae6e5cffbcc6dc`. The verified final artifacts contain 39 distinct newly contributing primary papers, 55 records and 229 source crops; built site size is 1,421,685,200 bytes. The earlier preparation and failed-build entries are retained as historical results; this milestone supersedes their unpublished status.

R2 corrected 30 selected chemical display bindings (6 in this batch and 24 on older simple-lane pages), with 14 new name cards and no changed canonical recipe values. Older-page display corrections add no new-paper credit. The original R1 proofs and failed visual result remain preserved. R2 initially encountered a strict filesystem access denial (WinError 5); its failure log remains preserved. Ordinary approved escalation then completed normal R2 Source preparation, binding 22,797 files. This was not an automatic approval rejection, and a path-formatting bug was not established. The focused chemical matcher suite had 10 passing tests; the prior ordered receipt and crystal-default suites had 11 and 20 passing tests. These historical focused-test counts do not claim additional reruns.

R2 local checks and its pre-push visual check passed, but exact-head Source CI 38142224825 failed on both Ubuntu and Windows at the reviewed-source-figure-access tests; compare-artifacts was skipped. R2 was not merged or published and earned zero new-paper credit. The failed CI diagnostic and all R1/R2 evidence remain preserved. R3 corrected stale extracted-reference title expectations and added local JavaScript-test parity before the unchanged normal five phases. Its own actual Source preparation bound 22,797 files. Exact-head R3 CI 38144237490 passed and its Source merge succeeded, but the sealed browser review found missing figures on two papers. R3 was not pushed to Site and earned zero publication credit.

R4 repaired only caption detection for 2 papers and retained 8 additional source crops after normal local figure generation. All those crops were visually checked for whole panels and category labels; 2 include a journal running header. The caption detector had 14 passing synthetic tests. No scientific value extraction was rerun, no independent audit was asserted, and the extraction prompt and three checking predicates were unchanged. Its actual Source preparation, exact-head CI, sealed browser approval, Site push and anonymous verification are separately bound to R4 receipts.

The selected cohort has 50 distinct papers: 39 deployed and 11 omitted or held. The omissions comprise 3 identity holds, 0 failures after one redo, and 8 papers with no retained eligible route. There were 47 supported identities and 47 successful two-pass papers. Before rare reading, the automatic check considered 1,642 values, kept 1,054, and retained 65 pairs.

Actual pass executions including the one permitted redo were 96: 95 successful and 1 failed (1 original failures, 0 redo failures). These execution counts are distinct from final valid two-pass files and published papers.

One-reader rare-material checks covered 19 papers and removed 78 field/path entries (72 scientific value objects, 1 wrong page locators and 5 coupled unit fields), with zero replacement facts. These deletion counts are not an independent audit or a post-reading accuracy score. Common-material papers were not audited. New records remain source extracted, not independently audited or training eligible.

| Stage | Actual UTC timestamp |
| --- | --- |
| Extraction start | 2026-10-11T10:12:03.233177+00:00 |
| Extraction finish | 2026-10-11T11:29:48.202258+00:00 |
| Figures/check final handoff | 2026-10-11T11:31:09.223215+00:00 |
| Site push | 2026-10-11T15:35:40+00:00 |
| Anonymous verification | 2026-10-11T15:42:48+00:00 |

Extraction elapsed 77.749485 minutes; figures/check metadata records 1.350349 minutes. Cohort extraction-start to verified publication elapsed 330.746114 minutes, or 7.074913 newly published primary papers per elapsed wall-clock hour. This interval includes release preparation/waiting and makes no claim of uninterrupted agent work or achieved 20-paper/hour capacity.

| Paper left out | Metadata reason |
| --- | --- |
| 10.1002/(sici)1521-4095(199906)11_8_643__aid-adma643_3.0.co;2-i | identity_hold |
| 10.1002/adma.200602373 | no_route_eligible_record |
| 10.1002/polb.10754 | no_route_eligible_record |
| 10.1007/s11671-008-9133-5 | no_usable_pairs |
| 10.1021/am404355m | no_usable_pairs |
| 10.1038/s41565-021-00871-x | no_route_eligible_record |
| 10.1039/a809779h | identity_hold |
| 10.1039/b100968k | no_route_eligible_record |
| 10.1039/c0nr00232a | no_route_eligible_record |
| 10.1088/1361-6528_28_4_045701 | identity_hold |
| 10.1103/physrevb.66.075316 | no_usable_pairs |

The existing batch choices, source-preparation failures and engineering fixes remain recorded above as actual history. The quote-found, number-in-quote and both-passes-agree rules and all normal release gates remain in force. The audited lane, original findings, denominator, sampling/stop rules and every owner question remain paused and unchanged.


### R4 local build path history

For the unchanged prepared Source `3df0f9b15183f58054b4db28bff9f1e7a47f8c96`, the entire JavaScript suite and the first four normal Source phases passed on the first run. The complete build then failed at 2026-10-11T14:47:50.088806+00:00 while copying into the long temporary destination; the actual error was a Windows path-length copy failure. The original failed result and log remain preserved, and that result remains `passed: false`.

The choice was to use the shorter private `batch05/r4-build` output and repeat only the failed complete build. The earlier successful phases were reused at the same clean Source head; no check was removed, weakened or relabeled. The complete-build retry ran from 2026-10-11T14:49:13.693367+00:00 to 2026-10-11T14:54:11.886901+00:00, exited 0 and took 298.188 seconds. Its separate successful retry receipt preserves the SHA-256 pin of the original failure. The subsequent Source-only document checkpoint uses the short `batch05/doccheck` output to avoid the same temporary-path problem.

This technical retry adds no paper credit, asserts no scientific audit or calibration, and does not clear the refused Batch06 launch. Earlier R1/R2/R3 failures, original findings, paused audited-lane denominator and waiting-owner questions remain unchanged.

Checkpoint choice: refresh the current control timestamp to the actual 2026-10-11 15:47:32 UTC observation; historical event times, owner questions and paused audit data are unchanged. The sealed Source version was kept unchanged until its normal deployment and anonymous verification completed.

The first Source-only checkpoint receipt attempt failed before preparation because nested Git lacked the process-local trusted-directory setting for the existing authorized checkout. Choice: pass the exact Source/Site directories to child Git through process-local configuration, then rerun that failed receipt/preparation; no global or repository setting changes and no release check is removed. The failed attempt is preserved privately and adds no paper credit.

Batch06 launch authorization (recorded 2026-10-11T16:29:42+00:00): Root observed the explicit owner reply "Approve Batch 6 local extraction" at 2026-10-11 16:23 UTC (minute precision). The owner then instructed launching Batch06 now and authorized local model/controller launches of every later simple-pipeline batch. This resolves only the pending Batch06 launch question; its original automatic-approval refusal and question remain as history. The earlier Qwen test-only pause and other-paper prohibition ended for the simple job with its October10 evening start. This checkpoint records authorization, not a launch: no PID, generation start or new publication credit is claimed. All four audit-lane owner questions and sampled-record denominator remain unchanged, and the audited lane stays paused. Any fresh automatic approval refusal must not be bypassed.


Batch06 actually launched at 2026-10-11T16:29:34.6578461Z, with controller 45896, owned local server 32512 and two paper workers at 32,768 tokens per slot. The 50-paper cohort has 48 identity-supported generation inputs and 2 unchanged technical identity holds. Extraction is in progress; no Batch06 paper is integrated or published and publication credit is zero. Choice: reuse the existing verified CUDA server and unchanged two-worker controller, avoiding a model reload and preserving local private text/pass/pair payloads. Two prelaunch metadata checks failed technically before generation: implicit JSON timestamp conversion and nested REST-array enumeration. They were corrected by preserving ISO strings and enumerating the returned slot array; exact ownership and capacity predicates were unchanged. Historical refusals and all four paused audit-lane questions remain preserved.

Choice: finish the normal Source-only code/control checkpoint while Batch06 GPU extraction continues, to publish the current launch authorization and preserve the integration helper's clean-Source requirement.

The guarded document apply preserved its two technical prewrite failures (question_id mismatch, then sandbox OpenProcess access denied); ordinary escalation applied it successfully at 2026-10-11 16:33:48 UTC. These were not automatic approval rejections, and no model restart or extraction rerun occurred. The current Batch06 launch has actual controller 45896/server 32512 evidence, 48 generation PDFs and two identity holds; this Source-only checkpoint adds no paper publication credit and leaves the audited lane and its four questions/denominator unchanged.

## October 11 current engineering and machine-paper inventory

At 2026-10-11T17:08:35.407601+00:00, the metadata-only inventory lists 167 distinct live `source_extracted` papers and 284 records, all reconciled to their actual Batch 1–5 Source/Site push and anonymous receipts. Each DOI line records exact IDs, batch, anonymous live time and whether an owner-scoped rare-product reading was recorded. See [MACHINE_EXTRACTED_PAPERS.md](MACHINE_EXTRACTED_PAPERS.md). No quoted source, pass or pair payload is included.

Recommended choice: prepare neutral Reader text and the combined display-pair metadata in one engineering merge/deployment, while Batch 6 generation continues. Engineering publication remains pending, adds no paper credit, and will be reported only after the normal gates and anonymous pass. Data stays `source_extracted`; audited-pair data and training-ready exports stay unchanged. Existing failed tests, launch refusals and audit questions remain on record. The latest owner approval covers every later local simple-pipeline batch launch; the older test-only restriction does not hold this job.

The owner additionally requests captions on the figures. Choice: display full existing registered public captions on figure cards and enlarged views; supply meaningful public paraphrases for new figures through a local caption pass, keeping original caption-bearing work files private. The converter accepts only an explicit `public_caption`, never the private original caption or pair quotes. Existing extracted figures still carry locator-only captions until that backfill is completed; meaningful-caption coverage is not claimed for them yet.

Root applied the private 25-file neutral display/pair/caption proposal and five canonical metadata corrections. Citation metadata is corrected for Neo (cm501595u), Srivastava (ja1089809) and Miao (nn500414u); Miao's three SP1 variants are grouped as source-stated CdTe quantum-dot/protein assemblies, preserving their sample labels and record URLs. A targeted pattern scan covered 136 extracted ACS papers / 242 records, not a full scientific audit. Recipe values, all 2,985 other canonical records, source-extracted status and the 284-record total remain unchanged. The normal dependency build passed its data/page stages and stopped at the expected material-sidecar dependency; empty-pair Reader sync then reconciled the new material membership without regenerating any historical pair or source ID. Complete clean build, local visual review, exact-source CI and anonymous deployment remain pending; this is zero new-paper credit.

At 17:29:42 UTC, Batch 6 finished local extraction, figure selection and check: 48 successful two-pass papers, 96 successful pass executions, 48 pair files and 301 figure crops; zero failed passes or retries. Before rare-material reading, 34 papers have ordinary-route eligible records, with 42 eligible records and 10 rare-material papers. These are private processing results, not published contributions. Batch 7's first launch attempt stopped before a claim or generation because its capacity guard expected dictionary rows while the local REST client returned objects. The actual two server slots were idle at 32,768 tokens each. The private launcher now copies the exact returned properties without changing the existing capacity checks; 48 guard tests passed. The freshly rebuilt Reader projection and actual preview show the registered Zhong figure galleries and captions; the earlier empty preview was observed before the rebuilt projection had loaded.

Batch 7 actually launched at 17:35:12 UTC with controller 28444, existing server 32512 and 47 identity-supported inputs; three unchanged identity holds remain excluded. A serial caption client started at 17:35:31 UTC against that same local server without reloading it. Its first completed snapshot supplied 18 public paraphrases for four existing papers, applied to 50 Reader figure instances; canonical records and figure bytes are unchanged. One caption packet failed validation and remains omitted, with its private response preserved. These captions await the same engineering build, visual and release gates. The remaining caption work continues privately and will join later ready batches; full backfill or new-paper publication is not claimed.

The normal engineering Source preparation retained two failures: the five owner-requested metadata corrections needed their exact snapshot-digest overrides; the new caption helper contained private machine-specific defaults. The five overrides use the existing separate metadata review and unchanged preparer; all other approvals, eligibility and audited records are preserved. The public helper now derives its checkout path and requires an explicit local input folder. Fourteen existing tests and two portable-CLI tests passed; the unchanged public boundary accepts the proposed bytes exactly. The already running private client, prompt, schema and validation remain unchanged. No check, policy or permission rule was weakened, and neither failed preparation earned publication credit.

### Full-caption engineering build correction

2026-10-11T18:17:26.260839+00:00: the complete local candidate ran 245 Python tests and found one stale display assertion expecting the audited-only 864 rows. The corrected regression expects 864 unchanged audited rows plus 284 source_extracted record rows, 1,148 display pairs; it additionally verifies that extracted IDs do not enter audited broad rows and appear exactly once in the display. Existing broad, strict and training assertions are retained. Its zero comprehensive count is the deliberate empty reference fixture; the actual registry produces six, all audited. The first failed build is preserved. No production metric, policy or allowlist rule changes, new paper credit or deployment are claimed.

### Exact chemical-viewer metadata refresh

2026-10-11T18:34:42.241559+00:00: the second complete local candidate passed the Python tests, site and atlas checks, then the complete quality check found only five stale chemical-viewer canonical digest pins after the earlier bibliographic corrections. Refresh exactly those five source_extracted record hashes. All chemical identity/state maps, 3,264 other record pins, canonical records and registry/depiction assets remain unchanged; seven focused guard tests passed. No gate or policy is edited. Preserve both failed candidates; publication and new-paper credit remain zero until the normal release succeeds.

## Verified zero-paper Reader engineering milestone

The neutral Reader engineering release was deployed and anonymously verified at 2026-10-11T19:54:08+00:00: 3,668 files checked, zero mismatches. [Source commit](https://github.com/cuiyist/mattersyn/commit/032fec83c44d6fc25c344359995432b83aa50a76), [ordinary merge](https://github.com/cuiyist/mattersyn/commit/09b9a236757d2690417849a9641bd840dbb75512) and [Site commit](https://github.com/cuiyist/mattersyn-site/commit/2e5ddaf840f941ed113c7f308c7ea9e575522811). This is an engineering milestone with **zero new papers and zero new records**; the latest Batch 5 paper event and the distinct-paper ledger are unchanged.

Actual built display: 244 audited + 167 machine extracted = **411 papers**, 3,269 canonical records and **1,148 displayed pairs** (864 audited pairs + 284 machine record rows). The audited pair artifact and audited-only training exports retain their previous scope. Display labels are neutral; underlying machine records remain source_extracted and are not independently audited.

This deployment includes only the pinned caption snapshot: **18 unique figures / 50 Reader presentation instances** (32 record entries + 18 source-gallery entries). The later completed caption backfill is a separate private handoff and is not claimed as deployed here. Final site size: 1,423,128,107 bytes / 28,417 files. The audited lane, original findings, stop-rule denominator and owner questions remain paused and unchanged. No throughput or uninterrupted background activity is asserted.

<!-- end verified zero-paper Reader engineering milestone -->

## Batch 6 current preparation

2026-10-11T20:02:40.433920+00:00: 34 candidate papers, 42 ordinary records and 204 figures are integrated locally, with zero new publication credit. The one-reader rare-material read covered 10 papers and deleted 34 incorrect scientific objects plus six coupled units; originals and common-pair facts remain unchanged. Four retained papers had bibliography-only corrections from DOI authority; all 3,269 existing canonical records remain byte-identical.

The completed local caption snapshots, unchanged-validator recovery and one bounded missing-subset retry provide 1,021/1,027 existing B1–5 captions and 203/204 captions for the final retained Batch 6 figures. These public paraphrases and exact locators are applied locally; seven omitted semantic captions retain the authored locator fallback. Original rejected packets remain private and unchanged. The retry accepted eight existing and four pending figures; three pending retry figures belong to retained Batch 6 papers. No raw original captions, pass files or quoted pairs enter this report or GitHub.

Batch 8 launched locally at 19:41:31 UTC with 45 supported inputs and five identity holds, independently of the UI deployment. Batch 7 has 47 successful two-pass papers, 74 checked private pairs, 278 crops, zero failed passes and three identity holds; it is not published. Its local caption run is active. The audited lane, questions and sampled denominator remain paused. The earlier UI checkpoint helper failed because it compared a normal eight-field summary with the full anonymous receipt; a private shape-only adapter corrected the comparison, preserving all normal receipts and gates.

Choice: local reading proceeds independently of the UI publication, as instructed; the former private launcher's unnecessary UI dependency was removed while all actual ownership/input/slot guards remain. The public control update was delayed during the pinned UI Source freeze; that delay implies neither inactivity nor uninterrupted background work. Next: fresh asset registration and unchanged complete build, source, CI, browser, publication and anonymous verification.

### Final caption preparation — 2026-10-11T20:18:33.720606+00:00

The pending Batch 6 transaction now carries descriptive public captions for all 1,231 applicable figures: 1,027 from Batches 1–5 and 204 retained Batch 6 crops. A scoped reader authored the seven remaining paraphrases and they passed the unchanged validator; normal apply filled 17 empty Reader instances, changed zero canonical records and changed zero crop bytes. Rejected model packets and retry results remain recorded. This is presentation work, not scientific audit, and is not yet live.

PowerShell argument replay converted the saved ISO timestamp to a local culture date, causing a normal asset-guard rejection. Replaying the identical JSON argument strings through Python succeeded: 401 assets checked, 385 exact registry additions, zero new path rules; only the registry checksum changed in the policy. The guard and actual permission status were unchanged. The prior source preparation is retained; the final seven captions require fresh ordinary file-list binding in the same uncommitted transaction. No extra bind commit or publication credit is added.

### Full captions deployed; next batch prepared

Batch 6's verified release carries full descriptive public captions for all 1,231 applicable figures (1,027 existing + 204 new), with exact figure/page locators in cards and native enlarged views. All 59 required sealed preview routes passed, with loaded figures/diagrams and captions; phone wrapping was checked. Root also opened a public live card and its enlarged figure after deployment and confirmed the caption and locator. Original caption text and model payloads remain local.

Next batch: 36 papers, 54 records and 216 crops are prepared locally with all 216 unique caption bindings (535 Reader instances). One-reader rare-material corrections deleted 53 incorrect scientific objects, nine coupled units and one wrong locator; four retained papers received bibliography-only corrections. All 3,311 prior canonical records remain protected. Batch 7 has zero publication credit pending normal release. No nonempty sync follows final caption/citation application.

Choice: private caption generation proceeds alongside the next local extraction batch, without adding another model server or changing its two slots. The local checkpoint parser was corrected to read the normal preview/public tree distinction, integer summary counts and DOI/source membership; every normal release gate remains unchanged. Earlier failed parser attempts are preserved. Site size after Batch 6: 1,474,043,687 bytes / 28,962 files; Pages deployed successfully, so no size-triggered repository split occurred.

## Batch 8 caption preparation — 2026-10-11T23:07:48.007667+00:00

Batch 7 is verified live: 36 new papers, 54 records and 216 captioned crops; 747 anonymously checked files, zero mismatches. Live counters: 481 papers and 1,244 recipe–structure pairs. Batch 8 has 35 papers / 52 records / 196 crops locally prepared, zero publication credit. All 196 retained crops have bound descriptive public captions: 171 accepted local, 20 recovered local, five manual paraphrases, covering 484 Reader instances. Original caption text remains private. Twelve rare papers were read once; 62 scientific objects and four coupled units were removed. Twelve retained papers received citation-only corrections; old record bytes remain protected.

The existing-caption display fix selects 13 already-public paraphrases and shows captions in legacy cards/enlargements with phone wrapping. Twenty-one display/cache/test files changed; no scientific record, crop, provenance, permission or release gate changes. Normal source/build/CI/browser/deployment checks are still pending. One fresh asset dry run failed because PowerShell parsed an ISO timestamp to DateTime before replay; replaying the saved exact string through Python passed, with the same timestamp and unchanged guard. All 487 assets checked, 465 new registry entries, zero path-rule additions. No gate was changed to pass.

## Batch 9 prepared with captions — publication pending

2026-10-12T00:47:30+00:00: **35 papers, 45 ordinary records and 182 figure crops** are locally prepared, with **zero Batch 9 publication credit**. The current live total remains 516 papers / 1,296 displayed pairs. All 182 retained crops have validated descriptive public captions and page/figure locators, bound to 409 Reader instances. These retained captions came from accepted local paraphrases; recovery/manual captions from omitted papers are not claimed as shipped.

The one-reader rare-material scope covered nine papers and deleted 18 incorrect scientific objects, three coupled units and one wrong locator (22 paths); no facts were added. Ten retained papers / 14 records received authority-bound citation-only corrections in 17 dependent files. All 3,417 prior canonical rows remain byte-identical. Status remains `source_extracted`; audited records and the six training exports keep their existing scope.

The 50-paper cohort had 47 supported generation inputs and 46 successful two-pass papers. Extraction took 71.6445 wall-clock minutes; one original failed pass and one failed pass on the permitted retry left DOI 10.1021/am504615x out. Three identity holds (a_1022608802635, a_1026714004563 and cm00055a009) remain technical holds. Before rare reading, the unchanged checker retained 878 of 1,423 assessed values in 63 private pairs; conversion then selected the 35-paper payload above. Missing stage timestamps were not inferred.

| Additional omitted paper or route | Normal conversion reason |
| --- | --- |
| 10.1002/jbm.a.30410 | no_route_eligible_record |
| 10.1007/s12274-010-0010-z | no_route_eligible_record |
| 10.1021/ac400250j | no_route_eligible_record |
| 10.1021/jp053621t | no_usable_pairs |
| 10.1021/jp061453e | no_route_eligible_record |
| 10.1021/jp066018z; pair 2 only | no_synthesis_operation |
| 10.1021/jp5111218 | no_route_eligible_record |
| 10.1021/jp809538z | no_usable_pairs |
| 10.1021/ma701983y | no_route_eligible_record |
| 10.1021/nl403889u | no_route_eligible_record |
| 10.1039/c6ta04934f | no_usable_pairs |
| 10.1063/1.1759788 | no_usable_pairs |

Normal asset registration checked 409 assets, added 384 exact entries and added zero new path rules. An initial invocation used an unsupported `--out` argument and wrote no asset changes; the correction saved the normal tool's JSON stdout without modifying it. Fresh registration and the dependent metadata build passed. Complete local release checks, CI, preview, deployment and anonymous verification remain required. No policy or gate was weakened.

Choice: ship available public descriptive captions with exact source locators; keep original source captions, quoted pass/pair files and local-model payloads local. Batch 11 continues local generation independently; its completion is not inferred. Batches 12–13 have private inputs prepared and are not launched.

The first Source-preparation attempt rejected the newly updated machine-paper list as an unexpected path before staging. Use the existing exact --extra-path argument for research-assets/public-audits/MACHINE_EXTRACTED_PAPERS.md; no tool, policy or path rule is changed.


## Caption completion and Batch10 preparation — 2026-10-12T02:30:52.683357+00:00

Batch9 live verification succeeded at2026-10-12T02:14:36+00:00 (635 files,zero mismatches). Initial failed Reader-file retrieval and the exact-byte probe/retry are preserved; this is not a second deployment. Live card/enlargement captions were inspected on Imran2021 at02:23:49 UTC.

Batch10 prepared scope is35 papers,53 records,181 retained crops; all have public captions (176 accepted local,4 saved-response recovered,1 manual),435 Reader instances. Seventeen retained papers received citation-only metadata corrections,26 records,29 dependent files; no scientific facts changed. Missing captions on20 distinct legacy crops are added across116 record views and116 source-gallery views;232 caption fields only. The complete build, local visual checks, Source CI/merge and normal Site publication remain pending; Batch10 paper credit is0.

NN4002825 is omitted because its retained record no longer matches the immutable original citation ID. The strict binding was not changed. Initial integration was retained privately and the prior Source payload restored with3,462 old canonical rows unchanged; two stale generated files were retained explicitly before ordinary integration of the other35 papers. All original pairs, receipts, figures and unsuccessful attempts remain local. No data was destroyed.

Batch12:44 two-pass successes,55 checked pairs,213 private figure rows;51.5253 extraction minutes; original controller OS exit isunknown. Local caption client returned0 with199 accepted captions,43 requests and2 original failures; recovery/manual completion is private and separate. All three rare groups completed. Batch13 local controller47724 launched45 supported papers on owned server32512;5 identity holds; no publication credit. The source job continues; the audited lane and its four questions/history remain paused. No uninterrupted work or unmeasured hourly rate is asserted.


## Root caption/publication checkpoint — 2026-10-12T04:14:37.294927+00:00

Batch10 actual Source PR27 passed Ubuntu/Windows/compare-artifacts CI at prepared`f1e3acd3d1a2666f7b09e04e3f0ae1593b248817` and merged normally as`42e870c879df940f5d9eed4f79c243366b8100dc`. Actual Site`a4b117846e4f1e36701201acb53b2dfeb9b8644c` was pushed at03:49:01UTC and anonymously verified at03:55:31UTC. The normal verification passed645 files with0 mismatches and0 failed paper/material routes, recording35 distinct new paper events. Built size:1,711,933,632bytes /31,409files; this successful deployment is not a size-refusal trigger. Counts are586 papers /1,394 displayed pairs, including342 source-extracted papers /530 pairs; scientific audit or calibrated accuracy is not asserted.

Caption display is verified on all73 sealed preview routes, three phone pages and both repaired legacy pages at desktop/phone. Two initial stale-node actions were retried after fresh DOM snapshots and passed; original errors remain local. Live He2021 card and enlargement showed their complete descriptive caption and source/page/figure locator at03:55:27.296Z and at phone width. Legacy corrections cover20 descriptions/232 Reader contexts/82 existing record IDs, with zero additional paper or figure credit. The caption inventory has4,088 renderable unique asset paths /13,666 contexts and no missing meaningful caption;20 nonrenderable descriptors were excluded. These are presentation checks, not a scientific audit.

Preserved operational failures: initial Source-preparation WinError5; subsequent strict Git ownership rejection; accepted per-process safe-directory retry; successful Source push followed by API HTTP502 and API-only retry. No force-push, gate change or automatic-approval bypass occurred. Whole-DOI NN4002825 remains a strict original-ID technical hold; no repaired identity or science is inferred.

Batch11 is locally prepared only:32 papers /43 records /141 retained figures;112 accepted,22 recovered and7 manual captions bound in322 Reader contexts. The one-reader rare pass deleted29 scientific objects,7 coupled units and2 wrong page locators,38 paths total,0 additions. Exact bibliography metadata correction affects19 retained papers/23 records/26 dependency files. All3,515 previous canonical records remain unchanged. No nonempty Reader sync follows metadata application. Fresh asset/dependency checks and the normal cohesive Source/CI/browser/Site release remain pending; zero publication credit until anonymous verification.

Choice: continue the ready batch and retain the existing guarded cleanup hold, because unknown process ancestry remains unresolved and the only unreferenced code ZIPs total268KB. No local data deletion was attempted. The audited lane, historical tests/denominator and four owner questions remain paused and unchanged. No uninterrupted work or achieved throughput is claimed.


Root delivery checkpoint, 2026-10-12T05:59:27.638583+00:00. Batch11 normal release and both published Peng2001 desktop/phone caption checks passed as recorded above. Batch12 current preparation:30 papers,36 records,140 captions (126 accepted/10 recovered/4 manual),312 Reader instances; no live credit. All prior canonical rows protected. Strict citation plan applied to11 retained papers/15 records with18 mechanical dependency files. Initial Root caption pin check had a transcription omission; the completed input was unchanged and its original full hash matched before any binding. Failed attempt preserved privately. No script, scientific check or release gate changed.

Storage: completed owned regenerable-copy cleanup removed6,269,699,643 logical bytes from22 B10 targets and3,305,639,942 logical bytes from8 B11Q targets. Only verified Root-owned preview processes were stopped. Papers, training payloads, unique evidence, normal release payloads and all receipts remain. B11 cleanup measured26.253GiB free afterward, not continuous/current availability. Batch11 built site:1,749,842,236 bytes /31,894 files; deployment succeeded, so the size-failure trigger for mattersyn2 did not fire.

Batch14 final collector exited0; original controller OS exit was not observed. Batch15 controller51360 was observed in phaseextract with21 two-pass papers at2026-10-12T05:58:36.051084+00:00; this is an observation, not a promise of uninterrupted activity. Batch16 has50 copied local QD PDFs,41 supported identities and9 technical holds; it is unlaunched. Remaining metadata candidate counts731QD /311metal are not publishable-paper counts. No new paper download, held-out test, machine calibration, audit-lane resume or changed training admission occurred.

At 2026-10-12T06:28:51.068692+00:00, Batch12's first complete local build failed the unchanged component-architecture check before any push: the new Mn-ZnS single-material record had been mechanically split into standalone Mn and ZnS component links. The narrow importer fix preserves the composition and architecture and suppresses those separate links; only this new record's component metadata and its exact dependent hashes changed. All3,558 prior canonical records, recipe values, figure/caption bytes and statuses remain unchanged. The existing component regression suite passed7 tests. The failed build is retained, and fresh normal Source preparation/build/browser/CI/release checks are required; Batch12 still earns zero publication credit. The caption requirement remains in force.


Root current delivery checkpoint, 2026-10-12T09:18:16.830465+00:00. Batch12 anonymous verification passed517 files with0 mismatches/0 failed paper or material routes; Source4a8118eb2b80c5c1f5cf37502edbc62beccd06b6, Site6877d67fa957d8e057388cff277cff7aead590c9. Source PR29/CI38216306647 merged normally; live caption card and enlarged-view checks passed at08:55:34.528Z desktop and08:55:40.502Z phone. Built1,791,003,129 bytes/32,335 files, successfully deployed: no size-failure trigger.

Batch13 preparation retained34 papers/56 records/192 crops after51 scientific-object,6 coupled-unit and1 wrong-locator deletions (58 paths); zero additions. Applied authority-bound citation-only metadata to16 papers/27 new records and30 dependency files. Bound186 accepted/5 recovered/1 manual captions in517 Reader instances. All3,594 old canonical rows protected; dependency build returned0. Normal complete Source/build/browser/CI/deployment checks are still pending, with zero B13 credit. No nonempty Reader sync follows caption/citation metadata.

Batch15 final49 successful two-pass papers/80 checked pairs/263 crops and planned captions/rare reading complete, unpublished. Batch16 collector native24178 returned0:40 successful two-pass papers/60 checked pairs/174 crops;9 identity holds and one omission after redo. Native caption64090 returned0,40 requests/168 accepted/2 failed packets; saved-response recovery returned0 and retained4 valid captions, leaving2 long-verbatim refusals for manual paraphrase. Original controller OS exits remain unknown. Batch17 native launch returned0 with actual controller7888,44 supported papers/6 identity holds. No publication count follows generation or these observations.

Verified rebuildable-copy cleanup removed3,386,759,600 logical bytes from40 finite original failed-q public targets; all155 private-build files, original PDFs/training payloads and small failure receipts remained. Native cleanup63176 returned0; simultaneous release work means logical removal is not asserted as physical net disk gain. Choices: release ready B13 and reuse accepted work; keep rejected caption packets and valid recoveries separate; continue local generation while integrating. No audits, stopped checks, external paper transfer, audited-record rewrite, storage-repository split or uninterrupted work claim.


Root verified delivery checkpoint, 2026-10-12T11:31:40.703969+00:00. B13 Source4f19ef73a2d26e90f30ab858e533ba32759229de / Site d97167b301b7a95cd5c3791a23fa4c0d1131348f. Source PR30 / CI38231455521 passed and merged ordinarily; normal publisher native7864 returned0. Anonymous verification at10:56:14 checked692 files,34 paper routes and66 material bindings with zero mismatches/failures;34 distinct ledger events. Built1,836,734,561 bytes/32,948 files and successfully deployed, so no mattersyn2 size-failure condition occurred. Live caption and enlargement probes passed at11:05:11.987Z desktop1280×720 and11:05:13.269Z phone390×844.

Publication interval since B12:08:53:49–10:56:14UTC, 2.040278 elapsed hours,34 new papers / 16.66 papers per wall-clock hour. This interval is below the20/hour target and does not assert uninterrupted work. The publisher stage markers are cumulative:push228.7 seconds,verification750.3 seconds; the verification segment is521.6 seconds.

B13 private browser wrapper stopped after successful sealed preparation because a batch-label substitution corrupted one checksum literal. A new revision restored the exact unchanged generic checksum; function logic and gates stayed intact, with failed history preserved. B14–17 inherited writers received the same pin-only correction. The first B13 preview process exited before review; a new receipt/log-name revision relaunched the same sealed preview. Root then inspected69 required routes and three phone views. An initial live Reader wait timed out while loading; follow-up rendered DOM and image/caption observations passed.

B14 selected26 papers/35 records/114 crops after eight scientific-object and three coupled-unit deletion paths; zero additions. Initial dependency generation recorded a Reader metadata stop before the normal final sync; final post-metadata build remains required. Five retained papers/records received citation-only corrections through13 files. Exact caption coverage is108 accepted +5 recovered +1 manual, updating268 instances without canonical or image-byte changes. No nonempty Reader sync follows these metadata writes.

Choice: compact only the large Reader JSON through existing serializers because it approached the100MiB GitHub single-file limit. Public Source copies are separate from the frozen private model/caption adapters. A first Git patch check failed on line-ending context and wrote nothing; use a new exact-byte/base-pin application, never ignore whitespace or weaken checks. Full data/order equality, canonical protection and normal build/source/visual/release checks still apply. Record actual final sizes after application; the size saving remains estimated here.

B18 collector18531 and caption client65986 actually returned0. The original detached controller OS exit remains unobserved.41 successful two-pass papers,36 nonempty checked files/56 pairs/185 crops;9 technical identity holds. Prospective30 papers/46 records are not publication. Six rare readings yielded14 scientific objects plus one coupled unit deleted, no additions.41 caption requests produced153 accepted figures and five failed packets; saved-response recovery added24 valid captions, leaving eight keys for manual source paraphrase. All original132 source/model/plan/guard files remain pinned and local. The genuine B13 anonymous timestamp10:56:14 preceded B18 inventory collection11:01; earlier pending notes reflected Root knowledge until its later completion observation, and separate addenda preserve that distinction.

B17 International Edition DOI anie.200600545 is retained; its German alternate ange.200600545 is a duplicate-primary-edition exclusion, not a no-synthesis skip. Originals/IDs are preserved; only International has an eligible record. B19 native readiness and launch returned0 with controller35476/server32512,43 generation papers/seven identity holds,50 existing byte-identical copies reused and no new payload. Its actual working Source includes unpublished B14, while Site is verified B13. Saved metadata queue3590 includes581 QD and311 metal candidates, not proven synthesis eligibility.

Storage: new B12 successful-q-r2 finite cleanup remains unexecuted. Its56,159 manifest-pinned public-copy files are reconstructible, but older preview launch details are incomplete; ten legacy launcher gaps were recorded without fabricated proofs, stops or deletions. Private155 build files, PDFs and quoted training evidence remain protected. No net space gain is claimed from an unexecuted plan. Safe runtime facts were kept privately while sealed publication work froze Source; this is the next cohesive Source status promotion, not a claim of exact hourly GitHub updates. No paused audit/question/sampling change, machine calibration, disabled release check or gold review assertion occurred.


Actual B14 metadata checkpoint 2026-10-12T11:44:03.929215+00:00. Public Reader JSON93,801,030→70,450,640 bytes, saving23,350,390 bytes. Full parsed value and ordered-pair equality passed; all3,685 canonical file bytes unchanged during compaction, all3,650 prior HEAD record rows separately byte-verified, and frozen private model/caption code unchanged. Nine new focused compaction tests passed. The four substantive Source changes are exact-filename serialization in to_site.py and local_caption_backfill.py, existing display-filter serialization in build_reader_metadata.py, and test_reader_json_compaction.py. No schema, scientific value, status, gate or policy permission changed. The original whitespace-context patch refusal remains preserved; exact-byte application passed.

The first post-metadata wrapper mistakenly supplied --out to the unchanged asset CLI, which accepts JSON on stdout; it exited2 without applying assets. A new wrapper captured stdout through the documented CLI, succeeded and retained both failure logs. Normal asset apply checked242 assets,227 new entries,zero new exact-path rules; rights retain factual unverified publisher-permission status. All seven normal post-metadata dependency stages returned0, with no Reader metadata stop. This is preparation, not deployment; B14 gives zero paper credit. B18 manual residual captions are now complete8/8 privately; rejected replies/original inputs remain preserved.
