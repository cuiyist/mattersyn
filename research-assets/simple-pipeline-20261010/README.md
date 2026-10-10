# Simple pipeline and site patches (2026-10-10)

Prepared for the owner. This branch is for reading only: do not merge it into `main`.

| Path | What it is |
|---|---|
| `simple/` | One script that reads papers with a local model, checks the extracted synthesis–structure pairs automatically, finds and crops figures, scores against audited records and builds plain pages. See `simple/README.md`. |
| `AGENT_PROMPT_QWEN_TEST.md` | The owner's instruction for the Qwen3-32B accuracy test on the 15 development papers. |
| `site-patches/` | A tested change to the site code that shows a unit cell for routes without a hand-bound reference. See `site-patches/README.md`. |

No paper text is included. The examples used for testing were made up.
