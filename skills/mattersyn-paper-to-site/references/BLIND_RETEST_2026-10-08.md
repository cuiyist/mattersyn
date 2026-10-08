# Fresh original-version blind retest, October 8, 2026

**Result: failed. Track 1 is on hold.** Two fresh, isolated auditors checked the same ten original, pre-correction papers. Neither was given the previous findings or corrected versions. Each reviewed all 233 records and the 177 scoped source pages. The frozen pass criterion was at least eight of the nine known findings for each auditor.

Auditor A detected **4/9 (44.4%)**; auditor B detected **5/9 (55.6%)**. Their combined coverage was 6/9 (66.7%), a secondary diagnostic only. It does not satisfy either auditor's pass criterion. Neither reported an additional finding in the four clean controls. These deliberately selected cases do not estimate the error rate of the whole collection.

| Known defect | A | B | Targeted deep-audit check |
| --- | --- | --- | --- |
| Sun: optimized PLQY assigned to an insufficiently identified recipe/sample | Found | Found | Trace a measured property to the exact specimen and recipe. |
| Sun: ambiguous coating repetition count made exact | Missed | Found | Preserve ambiguity in operation counts rather than resolve it silently. |
| Sun: dissolution/completion endpoints omitted | Found | Found | Compare ordered operations and explicit source endpoints. |
| Xu: Methods preparation joined to the wrong Results/control condition | Missed | Missed | Trace Methods-to-Results sample lineage. |
| Yang: aqueous extraction phase invented in apparatus illustrations | Found | Missed | Check the phase and vessel at each depicted stage. |
| Yang: later methanol antisolvent role leaked into another stage | Missed | Missed | Check each chemical's role against its own operation. |
| Chambrier: 16-hour Results joined to a 24-hour Methods recipe | Missed | Found | Keep conflicting recipe/outcome contexts separate. |
| Mittag: storage directions generalized beyond their supported material/architecture | Missed | Missed | Check workup/storage scope for each product architecture. |
| Peveler: NMR value transcribed incorrectly | Found | Found | Compare each reported value, unit and source context directly. |

The eight types missed in the earlier test already have explicit checks in the [fast-track reference](fasttrack-workflow-20261007.md). This retest shows that adding those checks was insufficient. Detection was scored by the actual defect and affected claim; different severity labels did not erase or double-count a finding.

The two sealed outputs and unchanged input inventories remain private. Their result receipt is SHA256 `8cbfa331d8a4be229908f235a3962b886c5cce7f29c3deb2a4d47aa52a16c29a`. Auditor A's sealed result is `0ed37c19acd58b7918340e8ac5b9da2d8c9551164aa4b26e83e9ef5d29e5c736`; auditor B's is `8b152ca15c0d2e3847b0eea2bd30ee7570478f3b949e4f4e6f2d4f6eeff60736`.

Both worker sessions were instructed to stop new claims, extraction and publication and to preserve their pending packages. The three locally integrated core contributions remain unpublished. The live baseline remains **231 contributing papers and 2,965 records**. Original findings and sampling denominators are retained. Restart requires a new owner instruction; cleanup and durable checkpoint preservation do not resume Track 1.

The authorized Qwen3-32B Q4_K_M download passed the official SHA256. The guarded runner-switch attempt stopped the exactly owned 4B process, then stopped at the occupied-port check before starting a new runner or sending any model request. The runner reservation remains held. Actual GPU fit, paper inference and scientific calibration are unmeasured; machine publication is disabled. A downloaded model is not evidence of improved scientific accuracy or publication throughput.
