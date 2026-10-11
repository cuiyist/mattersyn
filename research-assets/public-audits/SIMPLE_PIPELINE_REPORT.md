# Simple pipeline website job

Owner instruction: October 10, 2026, evening. This report records only measured results. The audit lane stays paused; new contributions retain `source_extracted`. Source PDFs, full text, pass files and pair files with quotes remain local. Site records contain locators without quotes.

## Part A

In progress: the provided unit-cell default and extracted-record patches are applied, and 27 reference cells imported. All 146 JavaScript tests pass, including eight new default-cell regression tests. Five status/counter regressions and 21 release-route regressions pass. Complete build, source boundary, browser, CI and deployment checks are pending. This engineering release adds zero papers.

## Part B

In progress: fresh two-pass Qwen3-32B extraction of the same 15 development main-text PDFs at 32,768 context, thinking off. No held-out papers. TOTAL and score will be recorded when commands finish.

## Choices and fixes

- Recommended choice: keep optical fields out of converted website records; the converter default avoids the optical errors observed in the earlier test.
- Require two successful passes before production `check`; retry a failed pass pair once with `--redo`, then leave the paper out. Fixed the checker to reject missing, failed or malformed A/B passes and move stale outputs outside the converter input folder; 19 synthetic regressions pass.
- Fixed two default-cell defects: an unknown reported phase cannot be treated as missing, and conflicting qualifiers cannot admit an incompatible cell. Reported product phase takes precedence over intended target; manually bound cells are unchanged.
- Registered exact COD archive-comment exceptions for new supplied CIF paths and hashes; coordinate bytes and the existing comment validator are unchanged.
- Used the existing public-report path after the source boundary rejected a new unlisted report folder; no path rule was widened.
- Converter fixes: original figure captions remain local; published captions contain only figure/page/category locators. Separate model passes are not called an independent audit.
- Public export now recursively removes quote fields and private paths, and replaces source captions with locator captions; four synthetic regressions pass.
- Extended ordinary Reader, source coverage and release-route bindings for explicitly labelled source-extracted records. DOI/record/page/browser bindings and training exclusion remain required; audited route checks are unchanged.
- No release check has been removed or switched off.

## Batches

No simple-pipeline batch deployed yet. Twenty screened PDFs are selected for batch 1; one ambiguous filename DOI was held out and replaced. Only eight verified metadata DOIs are overrides; twelve filename keys require PDF/model identity confirmation. The local model will start batch 1 when the development threshold clears; no paper credit follows from selection or extraction.
