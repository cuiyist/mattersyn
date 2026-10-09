# Qwen3-32B development diagnostic, October 8, 2026

The offline Qwen3-32B Q4_K_M runner fits the RTX 5090 at 8192 context with thinking disabled and schema-constrained output. Synthetic fit checks observed at least 9,922 MiB of spare memory on the 32,607 MiB adapter. These checks establish GPU fit, not scientific accuracy or extraction speed.

The first real input diagnostic retained all 15 frozen development papers and both independent pass slots. Five supplied original-audit packets exceeded the unchanged whole-request budget in both passes. Ten papers had unresolved source-provenance packets, retaining twenty explicit failed slots. No model generation completed and no scientific value was produced. All 32 held-out papers remained untouched.

| Field | Values produced | Independently verified correct | Pass slots masked |
| --- | ---: | ---: | ---: |
| Composition | 0 | 0 | 30/30 (100%) |
| Precursor identity with amount | 0 | 0 | 30/30 (100%) |
| Reaction temperature | 0 | 0 | 30/30 (100%) |
| Reaction time | 0 | 0 | 30/30 (100%) |
| Product statement | 0 | 0 | 30/30 (100%) |

Correctness and precision are unmeasured because no values were produced or independently scored. The diagnostic reserved the GPU for 128.4405636 seconds (0.0356779343 hours), including failed input handling. Its measured completed-paper rate is **0 papers per GPU-hour**; generation time was zero, so this does not measure the model's generation capacity. Zero papers met the five-field counter rule.

The 15-row roster, failed cases and 150 field/pass slots remain in the report. Three supplied packets cover complete projected original audit scopes; two are explicitly main-only selections omitting 19 SI pages whose exact audited hashes are outside the frozen PDF inventory. No scope was pruned to fit the request, and no missing reference value was invented. The original scopes and failures remain preserved.

Next work is to bind the remaining original audit scope authorities, establish explicit primary-synthesis page selections and certify local scoring references. Any successor must preserve frozen paper membership, held-out separation, extraction prompt, schema, pass rules and truthful failure denominators. All paper text, extracted candidates, prompts, responses, detailed receipts and reference truth remain on this machine. Only this aggregate report is suitable for public memory.

The diagnostic passed its runtime safety closure and released the exact owned GPU reservation. It grants no calibration, unmasking, training or machine-publication approval. Held-out inference and machine publication remain disabled pending the owner's review and a later explicit instruction.

## Context-sizing follow-up

The owner permits a context increase for these same fifteen development papers only, to the smallest size fitting all fifteen and at most 32,768 tokens if GPU memory allows. Exact local tokenization of five existing packets measured 14,739–22,834 tokens including the existing reserves. These measurements prove that 8,192 is insufficient for those packets; they do not establish the minimum for all fifteen. UTF-8 byte counts must not be presented as actual token counts.

The current runner remains at 8,192. Metadata recovery identifies six directly bound input candidates, three exact normalization candidates and six unresolved input selections; normalization candidates are not generation admission. No larger-context GPU fit or development-run peak is claimed. The earlier source-free GPU check recorded peak memory_used of 22,266 MiB (21.74 GiB). Frozen prompt, schema, reference split and pass rules are unchanged. Held-out inference and machine publication remain disabled.
