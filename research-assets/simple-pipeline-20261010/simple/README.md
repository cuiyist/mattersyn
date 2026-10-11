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
| `to_site.py` | Converter from checked pair files to the inputs of the existing site (see below) |

## What each step does

1. **extract.** Picks the pages that describe the synthesis and the product, sends them to a local model, and asks for the pairs twice. It refuses any server that is not on this machine.
2. **figures.** Finds each figure and its caption in the PDF, crops it, and labels it *structure* (TEM, XRD, SEM, …) or *property* (absorption, emission, device curves, …) from the caption. Schemes, mechanisms, kinetics and other figures are skipped unless you pass `--all`. A crop stops at the neighbouring figure's caption. Labels come from caption keywords, or from the local model if you pass `--model`.
3. **check.** Keeps a value only if all three hold:
   - its quote is found in the paper, letter for letter and digit for digit (line-break hyphens, spacing, symbols and ligatures are ignored; a quote shortened with "..." is accepted if its parts appear in order);
   - the number is in that quote, in a sensible range;
   - both passes agree.

   Anything else becomes "not reported". Nothing is corrected by hand and nothing waits for a decision.
   For rejected quotes the summary says how close each came: nearly matching, partly found, or not found.
4. **build.** Writes a searchable table of pairs, one page per paper with its structure and property figures, the structure, chemicals, steps and a temperature profile drawn from the data, and `pairs.json` for download and training. Quotes stay on the machine unless you pass `--quotes`.

## The pair format

One file per paper. Each pair has a product, its structure (composition, architecture, phase, shape, ligand, size, optical peaks, quantum yield) and its recipe (method, reactor, atmosphere, reaction temperature and time, chemicals with amounts, steps in order). Every value carries its quote. A value the paper does not state is absent and shows as "not reported". The full template is in `PROMPT.md`.

## Result of the first test (15 development papers, Qwen3-32B, 2026-10-11)

- **Speed:** 25 minutes for 15 papers, two passes each, no failures: about 36 papers an hour on one RTX 5090.
- **Kept:** 298 of 475 extracted values (63%). Of the 86 rejected quotes, 3 were not in the paper at all; the rest were reworded or stitched together.
- **Correct:** 224 of the 232 scored values (97%), after the 34 that did not match the audited records were looked up in the papers: 26 were right, 3 were real values on the wrong product or step, 4 were wrong, 1 could not be decided.
- **By field:** composition 15/15, chemical name 75/77, amount 47/48, temperature 42/43, time 27/28, size 7/7, optical peak 11/14.
- **Caveat:** a value that matched the audited record was not checked for being on the right product, and 15 papers is a small sample.

## First test: is the local model good enough?

Run it on papers that already have audited answers, then compare. The 15 development papers are the obvious set.

```
python mattersyn_simple.py extract dev15/*.pdf --out work15 --model qwen3-32b --base-url http://127.0.0.1:8080/v1
python mattersyn_simple.py check   work15 --out pairs15
python mattersyn_simple.py score   pairs15 --records records.jsonl
```

- `records.jsonl` is the site's own data file (`data/records.jsonl`).
- `check` needs each paper's DOI. The model usually finds it in the text; otherwise put `{"doi": "10.xxxx/..."}` in `work15/<name>.meta.json`.
- `score` prints, per field, how many extracted values match what the auditors recorded for that paper. With `--details file.json` it also saves the values that did not match, so they can be looked up in the paper; that file contains quoted paper text and stays on the machine. It cannot tell whether a value is attached to the right product, so read ten pages by eye as well.
- Start the model server with a 32,768-token context and thinking off.

## If an agent does the reading

Run `extract` with `--passes 0`. It only prepares each paper's text. The agent then follows `PROMPT.md` and saves its answer as `work/<name>.passA.json` (a second agent may save `passB.json`). `check` and `build` are unchanged.

## Into the existing site (`to_site.py`)

`build` above writes plain pages. To show the papers in the existing MatterSyn Reader, with molecule cards, step diagrams, unit cells and figures like the current papers, use the converter. It needs the site-code change in `site-patches/extracted-records.patch` applied first.

```
python to_site.py records pairs --repo <mattersyn checkout>        # one site record per pair, plus the per-paper inventory entry
<run the site build once; it stops at the Reader metadata stage>
python to_site.py sync pairs --repo <mattersyn checkout> --dist <that build's dist folder>
<regenerate the file lists with the project's tools, then build and release as usual>
```

What `sync` writes for each paper:

- a diagram for every step, and the binding file that attaches them;
- the figures, sorted into structure and property, with their captions;
- the Reader entry, and the material page's list of routes taken from the build;
- links from each chemical to the site's molecule library. A chemical the library does not know gets a plain name card, with no structure drawn;
- the record baseline rows, copied from the build.

Unit cells come from the composition default in `site-patches/`; the converter does not bind them.

**Held back.** Absorption and emission peaks and quantum yield are not written to the site unless you pass `--include-optical`: in the 15-paper test 3 of 14 optical peaks were wrong. A paper whose DOI is already on the site as a reviewed paper is skipped.

**How the records are marked.** Review status `source_extracted`, shown on the record page as "source extracted". They carry no "machine-extracted, not reviewed" badge, and they are not marked as reviewed. A page that includes such a record is headed "Synthesis and evidence" instead of "Reviewed synthesis and evidence". They stay out of the audited training exports and the audited pair table; `pairs.json` is the data for machines.

**Tested.** Two made-up papers went through `records`, `sync` and the complete site build (13 stages, 206 tests, all site checks) and were opened in the Reader with no console errors. Between them they cover: a single-material product, a core/shell product with component unit cells, a material the site had never seen, two products from one paper, a chemical the molecule library does not know, and structure and property figures.

**Not tested.** A real paper through the converter; the release gate, rights register and allowlist, which the project's own tools regenerate; the JavaScript tests.

## What this leaves out, on purpose

Audit chains, receipts and hashes, per-paper hand-made drawings, per-step reactor blocks, sampling windows, storage caps and release gates. The quality control is the automatic check, plus reading a random sample.

## What it cannot do

- It does not catch a correct number attached to the wrong sample when both passes make the same mistake.
- It drops values more readily than it keeps them, so some real data is lost.
- It was tested on a made-up paper with a stand-in model server, its scoring on one real audited record with planted errors, and its figure finder on a made-up two-column PDF. **It has not yet run on a real paper with a real model**, and real journal layouts will trip the figure finder in ways the test did not.
