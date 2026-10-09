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

On October 9, the two original SI scopes were restored byte-for-byte and measured without generation. Their current requirements, including the unchanged reserves, are 20,494 and 17,913 tokens. The three unchanged earlier packets require 22,834, 21,864 and 19,679 tokens. These five known requirements fit below the requested 32,768 ceiling; they do not establish a context fitting all fifteen because ten input packets still lack confirmed bindings. The unchanged 12,000-byte input guard also remains in effect. No larger context was selected or tested.

Read-only GPU sampling covered the restored-SI count interval from 2026-10-09T03:41:33Z to 03:45:17Z. Across 213 samples, direct `nvidia-smi memory.used` peaked at 22,396 MiB (21.87 GiB), with at least 9,792 MiB free. These are observed whole-GPU samples during token counting at 8,192 context, not a completed development-run peak. Exact runner/model/context/idle checks passed and the owned reservation was released. No generation, truth reads, held-out work or machine publication occurred.

The subsequent frozen Sharma main/SI packet contains thirty pages and requires 25,295 tokens including the unchanged reserves (23,769 rendered tokens). Six complete packets have now been counted, ranging from 17,913 to 25,295 tokens; nine bindings remain unresolved. The minimum context for all fifteen remains unknown. Its count-only GPU interval, 2026-10-09T04:12:55Z–04:15:08Z, recorded 127 direct samples with peak memory.used of 22,452 MiB (21.93 GiB) and minimum free memory of 9,736 MiB. Context remains 8,192. The packet also exceeds the unchanged byte guard, so counting it does not admit generation. No input pages were removed, prompt/schema rules changed, truth read, held-out inference run or machine values published.
