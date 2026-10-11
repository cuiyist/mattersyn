# Agent prompt: Qwen3-32B accuracy test, second pass

*Written 2026-10-11 for the owner to paste, after the first test report. No new model extraction is needed: the saved output of the first run is checked again with a corrected checker.*

**Why.** In the first run 183 of 475 values were dropped as "quote not in paper". The checker compared text too literally (line-break hyphens, ligatures, degree signs), so the report could not say how many quotes were really invented. The checker is fixed and now reports how close each rejected quote came. The score also needs the non-matching values looked up in the papers, because a value counts as a miss whenever the audited record does not contain it.

## Prompt to paste

```
Owner instruction, 2026-10-11: second pass of the Qwen3-32B accuracy test. About one hour.
The website job stays paused; this publishes nothing and changes no rule.

Get the updated script into a NEW folder (read-only; do not merge the branch):
  git fetch origin simple-pipeline-20261010
  git archive --format=zip -o simple-pipeline-2.zip origin/simple-pipeline-20261010 research-assets/simple-pipeline-20261010
Do not run `extract` again. Copy the first run's work15 folder next to the new script and use
its saved passes. Do not edit the script or the prompt.

Steps, from the new `simple` folder, with the Qwen3-32B server running as before:
  python mattersyn_simple.py figures dev15/*.pdf --out work15 --model qwen3-32b
  python mattersyn_simple.py check   work15 --out pairs15b
  python mattersyn_simple.py score   pairs15b --records <path to data/records.jsonl> --details unmatched15.json

Then, reading the papers yourself:
1. For every item in unmatched15.json, look it up in its paper and put it in one class:
   A. correct, and attached to the right product or step (the audited record lacks it or
      writes it differently);
   B. a real value from the paper, but attached to the wrong product or step;
   C. wrong value.
2. Xu 2007 gave no pairs. Say which PDF pages were sent to the model (the [page N] markers in
   its work15 text file) and on which page its synthesis is described.
3. Urban 2007 gave no figures. Say in one line how its captions are laid out (for example
   "captions begin with FIG. 1 in capitals on their own line").
4. Open 10 new randomly chosen crops and judge each: whole figure visible? label right?

Report to me, in chat, with counts only and no paper text:
- the TOTAL block printed by `check`, including the "of which" lines;
- the table printed by `score`;
- a table of classes A, B and C per field from step 1;
- your answers to steps 2 and 3, and the 10 crop judgments.

Limits
- Everything stays on this machine. Do not push work15, pairs15b or unmatched15.json: they
  contain quoted paper text.
- Do not publish, integrate or release anything, and do not run this on other papers.
- This instruction does not resume or change anything else.
```
