# MatterSyn, the simple way

*Written 2026-10-10. One script, four commands. No paper text leaves the curation machine.*

**The whole process:** read each paper → write one small file of synthesis–structure pairs → check it automatically → rebuild the website.

```
python mattersyn_simple.py extract papers/*.pdf --out work      # read: about a minute of GPU per paper
python mattersyn_simple.py figures papers/*.pdf --out work      # find, crop and label the figures: seconds
python mattersyn_simple.py check   work --out pairs             # check: seconds
python mattersyn_simple.py build   pairs --out site             # website: seconds
```

Then publish the `site` folder. That is all a release is.

## Files

| File | What it is |
|---|---|
| `mattersyn_simple.py` | The pipeline (about 520 lines, standard-library Python; PyMuPDF only if you feed it PDFs) |
| `PROMPT.md` | The reading instructions and the pair format. A local model or an agent uses the same text |

## What each step does

1. **extract.** Picks the pages that describe the synthesis and the product, sends them to a local model, and asks for the pairs twice. It refuses any server that is not on this machine.
2. **figures.** Finds each figure and its caption in the PDF, crops it, and labels it *structure* (TEM, XRD, SEM, …) or *property* (absorption, emission, device curves, …) from the caption. Schemes and other figures are skipped unless you pass `--all`. No model is used.
3. **check.** Keeps a value only if all three hold:
   - its quote is found word for word in the paper;
   - the number is in that quote, in a sensible range;
   - both passes agree.

   Anything else becomes "not reported". Nothing is corrected by hand and nothing waits for a decision.
4. **build.** Writes a searchable table of pairs, one page per paper with its structure and property figures, the structure, chemicals, steps and a temperature profile drawn from the data, and `pairs.json` for download and training. Quotes stay on the machine unless you pass `--quotes`.

## The pair format

One file per paper. Each pair has a product, its structure (composition, architecture, phase, shape, ligand, size, optical peaks, quantum yield) and its recipe (method, reactor, atmosphere, reaction temperature and time, chemicals with amounts, steps in order). Every value carries its quote. A value the paper does not state is absent and shows as "not reported". The full template is in `PROMPT.md`.

## First test: is the local model good enough?

Run it on papers that already have audited answers, then compare. The 15 development papers are the obvious set.

```
python mattersyn_simple.py extract dev15/*.pdf --out work15 --model qwen3-32b --base-url http://127.0.0.1:8080/v1
python mattersyn_simple.py check   work15 --out pairs15
python mattersyn_simple.py score   pairs15 --records records.jsonl
```

- `records.jsonl` is the site's own data file (`data/records.jsonl`).
- `check` needs each paper's DOI. The model usually finds it in the text; otherwise put `{"doi": "10.xxxx/..."}` in `work15/<name>.meta.json`.
- `score` prints, per field, how many extracted values match what the auditors recorded for that paper. It cannot tell whether a value is attached to the right product, so read ten pages by eye as well.
- Start the model server with a 32,768-token context and thinking off.

## If an agent does the reading

Run `extract` with `--passes 0`. It only prepares each paper's text. The agent then follows `PROMPT.md` and saves its answer as `work/<name>.passA.json` (a second agent may save `passB.json`). `check` and `build` are unchanged.

## What this leaves out, on purpose

Audit chains, receipts and hashes, per-paper hand-made drawings, per-step reactor blocks, sampling windows, storage caps and release gates. The quality control is the automatic check, plus reading a random sample.

## What it cannot do

- It does not catch a correct number attached to the wrong sample when both passes make the same mistake.
- It drops values more readily than it keeps them, so some real data is lost.
- It was tested on a made-up paper with a stand-in model server, its scoring on one real audited record with planted errors, and its figure finder on a made-up two-column PDF. **It has not yet run on a real paper with a real model**, and real journal layouts will trip the figure finder in ways the test did not.
- `build` writes plain pages. Showing these papers in the existing MatterSyn Reader needs a converter into the site's record format and a change to the site code, which are not written yet.
