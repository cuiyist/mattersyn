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
