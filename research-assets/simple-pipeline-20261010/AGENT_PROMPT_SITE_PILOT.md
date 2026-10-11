# Agent prompt: first website batch from the local model

*Written 2026-10-11 for the owner to paste, after the two Qwen3-32B test reports. It resumes the website job for this pilot only.*

**What it does.** Puts the unit-cell fix on the site, re-checks the model with the current prompt, then prepares 20 new papers for the existing Reader and stops for the owner's "go" before they go live.

## Prompt to paste

```
Owner instruction, 2026-10-11: first website batch from the local model. This resumes the
job for the three parts below only. The October 9 standing rules apply (keep going, park a
blocked item and continue, write questions under waiting_on_owner). Everything from papers
stays on this machine.

Get the current files (read-only branch; do not merge it):
  git fetch origin simple-pipeline-20261010
  git archive --format=zip -o simple-pipeline-3.zip origin/simple-pipeline-20261010 research-assets/simple-pipeline-20261010
Unpack into a new folder. Read simple/README.md and site-patches/README.md first.
Do not edit the scripts, the prompt or the patches. If one of them fails, report the error
and what you were running; do not rewrite it.

Part A. Site code, one pull request.
1. Apply site-patches/unit-cell-default.patch and site-patches/extracted-records.patch.
2. Run site-patches/add_crystal_references.py as its README shows.
3. Run the JavaScript tests and the complete build. Regenerate the file lists, allowlist and
   rights entries with the existing project tools.
4. Merge through the normal path after the checks pass, and deploy. This release adds no
   papers; it shows unit cells on existing pages.

Part B. Check the current prompt (about 40 minutes).
Run extract, check and score on the same 15 development papers with the new script, and
report the TOTAL block and the score table. Do not classify non-matching values this time.

Part C. Pilot of 20 new papers, prepared but NOT deployed.
1. Choose 20 papers from the downloaded queue whose main subject is the synthesis of
   quantum dots or colloidal nanocrystals and whose experimental section describes that
   synthesis. Skip papers already on the site.
2. Run:  extract (two passes)  ->  figures --model qwen3-32b  ->  check
3. Review only rare materials: if a paper's product has fewer than three routes on the site,
   read its pair file against the paper once and delete any value that is wrong. One reader,
   no second auditor. Do not review papers on common materials.
4. Run to_site.py records, one site build, to_site.py sync, then regenerate the file lists
   and rights entries with the project tools and build again, as simple/README.md describes.
   Register the figure crops the same way as existing source-figure crops.
5. Open three of the new pages, chosen at random, at desktop and phone width.
6. Stop before deployment and report.

No audits, sampling, receipts or checks beyond what the release tools themselves require.
If a paper fails at any step, leave it out, note why, and continue with the rest.

Report to me, in chat:
- Part A: merged and deployed, or what blocked it.
- Part B: the TOTAL block and the score table.
- Part C: the TOTAL block from check; papers, records and figures prepared; papers left out
  and why; values deleted in step 3; what you saw on the three pages; where the candidate
  build is on this machine so I can look at it.
Then wait for my "go" before deploying Part C.
```

## Notes for the owner

- **Optical peaks are held back.** Absorption and emission peaks and quantum yield are not written to the site in this batch, because 3 of 14 were wrong in the test. The prompt now tells the model more precisely what counts as a peak; Part B shows whether that helped.
- **Part A goes live without your "go".** It is the unit-cell change you already approved. Parts B and C publish nothing until you say so.
- **The step in Part C that has never run** is the release tooling on these new records (file lists, rights entries). That is where a hold-up is most likely.
