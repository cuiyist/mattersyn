# Qwen3-32B development context report

October 9, 2026. Scope: the existing frozen fifteen-development-paper experiment only.

## Measured GPU capacity

Qwen3-32B Q4_K_M loaded successfully with a 32,768-token context and all 65 layers on the RTX 5090. Thinking remained off. The model, batch settings and all other runner arguments were unchanged. The original 8,192-token configuration was restored after this load-only probe; the runner was verified healthy and idle, and the exact GPU reservation was released.

| Measurement | Observed result |
| --- | ---: |
| Context tested | 32,768 tokens |
| Whole-GPU peak memory.used | 28,355 MiB (27.69 GiB) |
| Minimum observed memory.free | 3,833 MiB (3.74 GiB) |
| GPU memory reported by the driver | 32,607 MiB |
| Samples covering loading and restoration | 608 |
| Samples in the 32K probe phase | 305 |
| Sample interval, UTC | 06:50:21–06:55:57 |
| Development generation requests | 0 |

Memory.used and memory.free were read directly from the driver. The peak describes the whole GPU during loading, startup warmup, idle checks and restoration. It is not a peak from completing the fifteen-paper development generation run, and it does not establish scientific accuracy or generation throughput. The earlier unsuccessful probe remains recorded; it failed before starting a larger-context runner and supplies no memory peak.

## Smallest context for all fifteen remains undetermined

Six complete original input packets have exact token counts. Including the unchanged framing and output reserves, they require 20,494; 17,913; 22,834; 21,864; 19,679; and 25,295 tokens. Thus 8,192 is insufficient for those packets, and all six fit below the 32,768 ceiling.

Nine other papers still lack fully bound source-page inputs under the unchanged experiment. Their requirements are unknown. The unchanged 12,000-byte source-input admission guard is a separate blocker: increasing context alone does not remove it. The smallest common context for all fifteen has therefore not been selected. No pages were removed to make an input fit.

The probe made no source-text, tokenization, generation, truth or held-out requests. The frozen prompt, schema, paper split, byte guard, output reserves and pass rules remain unchanged. Machine publication stays disabled. All source text, model inputs and outputs, detailed receipts and scoring references remain on this machine.

## Earlier development diagnostic remains unchanged

The earlier diagnostic retained fifteen papers, thirty pass attempts and 150 field/pass slots. It completed zero generations, produced zero values and left all slots masked. Accuracy is unmeasured; its measured completed-paper rate was zero over 128.4405636 reserved seconds. The 32K load probe does not replace that diagnostic or turn its failed inputs into successful extraction results. The 32 held-out papers remain untouched.

The saved actual probe receipt was independently checked against all 608 samples, both startup logs and the restored runner metadata. Its SHA256 is `623ee61976f4ff40e4ae5d624b31e29895b6c3e6bc8bb59c94bcf1d04ad0978b`; the independent result-review seal is `ca12ef6faa992781dbdcd770f11b7cddd3c1908b08c52aa6984860516aa15f1e`. Detailed evidence remains private.


## Six-ready 32K attempt, 21:10:59–21:16:15 UTC

The owner-authorized six-ready development attempt used 32,768 context, thinking off and the unchanged schema-constrained A/B protocol. All 65 layers loaded. It failed at a runtime ownership safety check before any generation request; two pass slots failed and the remaining ten were not attempted. This is a failed diagnostic, not a completed six-paper evaluation. The original healthy idle 8,192-token runner arguments were restored and the exact reservation released.

| Field | Values produced | Values correct | Active field/pass slots | Training share masked |
| --- | ---: | --- | ---: | ---: |
| Composition | 0 | N/A: not measured | 12 | 100% |
| Precursor with amount | 0 | N/A: not measured | 12 | 100% |
| Reaction temperature | 0 | N/A: not measured | 12 | 100% |
| Reaction time | 0 | N/A: not measured | 12 | 100% |
| Product statement | 0 | N/A: not measured | 12 | 100% |

The whole-adapter peak was **28,461 MiB (27.79 GiB)**; minimum observed free memory was **3,727 MiB**. All 566 samples covering load, attempted development and restoration were present with no sampler errors. The reservation lasted **346.4511145 seconds**. Zero papers completed both passes, giving **0 completed papers per GPU-hour** for this attempt. Successful loading does not establish generation fit or accuracy.

The six-packet context admission used exact original packet hashes and full token/framing/schema/output reserves in place of the old context-only byte bound. Frozen prompts, schema, split, scorer and scientific pass rules were unchanged. No input pages were omitted. Nine remaining source inputs were not admitted, and their full 32K fit is unknown. Certified truth mappings are still absent, so correctness is N/A, not zero or A/B agreement. No held-out paper, truth read or machine publication occurred.

The runtime defect is parked while audited-paper display and publication work continues. Its owned claim readback must be repaired without weakening process, file-sharing or source boundaries before another attempt. All earlier failed results remain recorded.

Actual restoration receipt SHA256: `f63dc569dff1a64e539073cf0b1c97315803c01dbe58d0db66c250fb3e33ba94`. Final aggregate receipt SHA256: `05bb5a4dca92da83b2210c2034308e96a3cd8b7503647e6bb786c0b05bfa7205`. Source text, prompts, responses, scoring references and detailed receipts remain local.


## Six-ready 32K retry, partial result at 22:38 UTC

The retry loaded all 65 layers at **32,768 context**, with thinking off and the unchanged schema-constrained A/B protocol. It issued four generation requests: **three passes completed, one failed, and eight of the twelve ready-subset slots were not attempted**. One paper completed both passes. This is a partial failed run, not a completed six-paper evaluation.

| Field | Values produced | Values correct | Active field/pass slots | Training share masked |
| --- | ---: | --- | ---: | ---: |
| Composition | 3 | N/A: not measured | 12 | 100% |
| Precursor with amount | 0 | N/A: not measured | 12 | 100% |
| Reaction temperature | 3 | N/A: not measured | 12 | 100% |
| Reaction time | 2 | N/A: not measured | 12 | 100% |
| Product statement | 0 | N/A: not measured | 12 | 100% |

The produced counts pass mechanical source-span checks; they are not independently measured correctness. Exact certified truth mappings remain absent. All machine values remain masked, and none satisfies scientific publication or training admission.

The measured whole-GPU peak was **28,549 MiB (27.88 GiB)**, with **3,639 MiB** minimum observed free memory. All 960 samples covered the measured attempt. It recorded **542.7653456 seconds** through failure and **78.1863665 seconds** in generation calls. One two-pass completion over that recorded interval gives a provisional diagnostic rate of **6.63 papers/hour**; this is not a finalized papers-per-GPU-hour result because the GPU reservation remains occupied after the failure. Scientific eligible-paper rate is zero.

Restoration to the original 8,192 configuration was rejected by the existing active-job guard. The exact reservation is retained. No new generation is admitted until the owned job is safely terminal and normal restoration and claim closure are verified. This runtime task is parked while CPU-side audited publication work continues. No guard, prompt, schema, pass rule, sample denominator or earlier result was changed.

Nine development source inputs remain held. No held-out paper or truth was read, and no machine contribution was published. Paper text, prompts, responses and detailed evidence remain local.

Partial restoration/failure receipt SHA256: `646ec313497379301fcede00a3492d59a62a1adbf90944a1c5b69b41126a0b0f`. Aggregate-only result SHA256: `1234563101b2912aa996c5d3a94ab6bf041ba1aa7f77514c164353a826969b23`.
