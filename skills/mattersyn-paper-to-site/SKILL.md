---
name: mattersyn-paper-to-site
description: Create or refine interactive materials-synthesis websites from research papers and supporting information, especially colloidal nanocrystals and quantum dots. Use for evidence-linked recipes, molecular and crystal viewers, stage-specific apparatus illustrations, and synthesis atlas pages.
---

# MatterSyn: paper to interactive synthesis

Turn a synthesis paper into a structured, source-linked recipe and a clear interactive page on the
MatterSyn website, without presenting an incomplete historical method as a complete lab SOP.

For a focused edit, do only that edit. Don't rebuild the site, re-extract unchanged papers, or
add records merely because this skill was invoked.

## Start here

**Adding papers to the website:** follow [references/workflow-v5.md](references/workflow-v5.md),
the only active workflow (quantum-dot/colloidal papers only, quick audit + 10% deep audit,
figures and visuals with each paper, continuous work, one-command release). The older workflow
files are historical; see the index below.

## Rules that are never relaxed

- Every value is traced to a page, table or figure of the source. Never invent, average, or
  carry over a value from a neighbouring step or variant. Unreported stays "not reported".
- Keep reported vs calculated vs inferred values distinct. Keep measured samples distinct from
  reference structures, illustrations and models.
- Show conflicting source statements side by side with their locators. Never silently pick one.
- Recipe → sample → structure links need actual evidence. Unknown links stay unknown.
- Source figures keep their citation, locator, sample assignment, hashes and factual rights status.
  Authored images are never labelled as measured data.
- Papers, SI, extracted text, page renders, private quotes and audits stay local. Only reviewed
  data, code, skills, memory and citations go to GitHub, through the existing boundary gates.
- Training eligibility is separate from publication.
- A model draft or a fast check is never an audit. The public counter counts only live,
  anonymously verified papers.

## Reference index

| Read | When |
|---|---|
| [workflow-v5.md](references/workflow-v5.md) | Always, before adding papers |
| [standards.md](references/standards.md) | Extraction, page design, figures, validation and publication details |
| [recipe-and-evidence.md](references/recipe-and-evidence.md) | Creating or changing experimental content |
| [structure-descriptor-v0.2.md](references/structure-descriptor-v0.2.md) | Structure fields and pair counting |
| [visuals-and-models.md](references/visuals-and-models.md) | Molecules, crystal models, apparatus scenes |
| [shared-reader-integration.md](references/shared-reader-integration.md) | Packaging a paper for the shared Reader |
| [reader-and-training-views.md](references/reader-and-training-views.md) | Reader/Data view or structure-metric changes |
| [training-dataset.md](references/training-dataset.md) | Training exports |
| [full-paper-review.md](references/full-paper-review.md) | A deep audit (sampled 10%) or a completeness correction |
| [corpus-atlas.md](references/corpus-atlas.md), [incoming-corpus.md](references/incoming-corpus.md) | Corpus indexing and screening details |
| [delivery-and-memory.md](references/delivery-and-memory.md), [mattersyn-project.md](references/mattersyn-project.md) | Hand-off, memory and project context |

**Historical, do not follow:** `processing-workflow-v4.md`, `throughput-workflow-v3.md`,
`throughput-workflow.md`, `scaling-workflow-v2.md`. Heartbeat/continuation and staffing limits
in `incoming-corpus.md` are also superseded by workflow-v5.
