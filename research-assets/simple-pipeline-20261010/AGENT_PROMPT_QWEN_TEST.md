# Agent prompt: accuracy test of Qwen3-32B

*Written 2026-10-10 for the owner to paste. It replaces the earlier 15-paper development experiment for this purpose. The script is on the side branch `simple-pipeline-20261010` of `cuiyist/mattersyn` (folder `research-assets/simple-pipeline-20261010/simple`); the prompt tells the agent how to fetch it.*

## Prompt to paste

```
Owner instruction, 2026-10-10: accuracy test of Qwen3-32B. One task, expected to take under
two hours. The website job stays paused; this test publishes nothing and changes no rule.

Goal: one table that says, per field, how many values Qwen3-32B extracts from a paper and how
many of them match the audited record of the same paper.

Get the script (read-only; do not merge this branch into main):
  git fetch origin simple-pipeline-20261010
  git archive --format=zip -o simple-pipeline.zip origin/simple-pipeline-20261010 research-assets/simple-pipeline-20261010
Unpack the zip into a new folder outside the repository. The script is in
research-assets/simple-pipeline-20261010/simple inside it.

Use only the script in the folder `simple` (mattersyn_simple.py and PROMPT.md). Do not use the
earlier local-model runner, its admission checks, input bindings, receipts, hashes or
monitoring for this test. Do not edit the script or the prompt. If something fails, write
down the paper and the error and continue with the next paper.

Steps
1. Start your llama.cpp server for Qwen3-32B Q4_K_M with a 32,768-token context on
   127.0.0.1:8080 (the OpenAI-compatible endpoint), as in your October 9 runs.
2. Install PyMuPDF if it is missing (pip install pymupdf). This one install is approved.
3. Put the main-text PDFs of the 15 development papers in one folder, dev15. Use the original
   PDFs, not the audit packets. Supporting information is not needed. Do not use any of the
   32 held-out papers.
4. Run, from the `simple` folder:
     python mattersyn_simple.py extract dev15/*.pdf --out work15 --model qwen3-32b
     python mattersyn_simple.py figures dev15/*.pdf --out work15
     python mattersyn_simple.py check   work15 --out pairs15
     python mattersyn_simple.py score   pairs15 --records <path to the site's data/records.jsonl>
   If `check` reports a paper without a DOI, add a file work15/<pdf name>.meta.json containing
   {"doi": "<the paper's DOI>"} and run `check` and `score` again.
5. Open 10 of the cropped figures in work15/figures, chosen at random, and note for each
   whether the crop shows the whole figure and whether its label (structure or property)
   is right.

Report to me, in chat:
- the TOTAL block printed by `check`;
- the table printed by `score`;
- wall-clock minutes for `extract`, and the number of passes that failed;
- figures found per paper, and your 10 crop judgments;
- any paper that failed, with its error.

Limits
- Everything stays on this machine. The script refuses any model server that is not local.
  Do not push work15 or pairs15 to GitHub: they contain quoted paper text.
- Do not publish, integrate or release anything from this test.
- Do not run it on other papers until I have seen the report.
- This instruction does not resume or change anything else.
```

## What the numbers mean

- **check TOTAL**: of the values the model produced, how many survived the automatic check (quote found in the paper, number in the quote, both passes agree), and why the rest were dropped.
- **score table**: of the surviving values, how many match a value of the same kind in the audited record for that paper. This is the accuracy number. It does not prove a value is attached to the right product, so a few pages should also be read by eye.
