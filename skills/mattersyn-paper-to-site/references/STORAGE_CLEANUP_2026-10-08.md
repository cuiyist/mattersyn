# Storage cleanup, October 8, 2026

This is an administrative checkpoint. Track 1 remains on its failed-blind-test quality hold; cleanup adds no published papers or records.

All cleanup helpers finished before the accounting checkpoint at **2026-10-08T20:27:41+00:00**.

| Measurement | Confirmed value |
| --- | --- |
| Removed logical file bytes, lower bound | 228,280,325,587 bytes (212.60 GiB) |
| Removed files, lower bound | 2,676,059 |
| Original papers/SI deleted | 0 |
| C: free space at the checkpoint | 376,432,660,480 bytes (350.58 GiB) |
| New published papers / records | 0 / 0 |

The sealed private aggregate receipt has SHA256 `daf1319d8ac833c8be9e098fa0b2a4d3500ab01235f70adbaa227f39e6633c76`. Its nineteen final event receipts are bound below; detailed paths and per-file evidence stay private.

| Final event receipt | Removed bytes | Removed files | SHA256 |
| --- | ---: | ---: | --- |
| deletion-r2.private.json | 39,603,294,705 | 724,403 | `86fd4ffd2458fd6cd9353852849a69abb81b385b8251d64e28c24de4339b1f6f` |
| deletion-r3-before-restart.private.json | 4,805,350,616 | 120,622 | `665aa6d7a8c016c2d223baf8f7579d5ecf63affdc7e80c3de5798f75c627c26f` |
| deletion-r3-large-first.private.json | 65,978,084,553 | 407,809 | `14b7633f2e8b4aa3f7dbd81608f9438a4df75367ea52b3e239073e51e18b977e` |
| visual-deletion-r1.private.json | 11,764,119,569 | 62,037 | `cab3655f40cb043ec15d9425258ea71db25573daa01859b81c132a671ed1361d` |
| visual-deletion-r2.private.json | 17,328,058,152 | 80,812 | `9e32c552e0564d9d03d6c1f079a9996ea963470e3d1c6838160614d1fe40f210` |
| data-deletion-r2.private.json | 7,429,398,135 | 1,451 | `5581bf94ed06398937ef319f1ada856c938161d2edb814253dcb81a6f14aa2e6` |
| subtree-deletion-r1.private.json | 10,585,799,766 | 53,011 | `0475ce75bdeb57ebe100a84d61d6030c977f1ee859f2cf4145d48c08fed59c3a` |
| research-visual-deletion-r1.private.json | 24,754,693,964 | 126,708 | `0bccdc4737e62de4fb2f1a4cb206f353248e13c552209e9101b93fc20080b307` |
| data-deletion-extra-r1.private.json | 4,159,014,964 | 784 | `f1db241660a0f988597982436a0e6c3147ea2357a150f5186f4eb6d34380df84` |
| data-deletion-extra-r2.private.json | 620,256,417 | 134 | `87db85664e2e4e3341ed37eb4178ba9cf2bd4b5451a5606ad01d9707fb02375a` |
| data-deletion-salvage-r1.private.json | 17,397,734,408 | 3,316 | `503c427667f43358f9b0fa82828c143fc0919199b02f753cb678f54fcb0e8591` |
| deletion-r4-small-0-before-resplit.private.json | 2,279,111,431 | 105,095 | `a475d0133e67744bebe30c909e640489404fc635a12fd9568fd08edaee60a105` |
| deletion-r4-small-1-before-resplit.private.json | 2,413,664,990 | 112,308 | `a84ead68774957da96152777496f26c15fda8dce302e870c25e26c8c75600b25` |
| remaining-visual-deletion-r1.private.json | 1,312,696,653 | 7,352 | `a406bf233e3b5cfad44af71b75c344661bd0d8d9ca86429a7f670d7e3da6e915` |
| remaining-visual-deletion-r2.private.json | 1,312,696,653 | 7,352 | `e1784e77d3cc56c1b9d616f9fa986eeabd6088aba24b06dc2f7c9b8aa779c4fa` |
| deletion-r5-small-0.private.json | 4,474,153,414 | 225,174 | `9967a30fa9668a4b94f9c7d18d77252da0a4dedaacc6ff67ae4f7d47621f8878` |
| deletion-r5-small-1.private.json | 4,094,356,400 | 215,438 | `2f994f6fe2fd86d09844cc4e00a99b4ba4bc98b0da41f939e936b15cdd097012` |
| deletion-r5-small-2.private.json | 4,196,895,509 | 232,883 | `71509f475949f966a70e425d3f14b13703d6ccbcc17c5be067aa2b6558eb0b49` |
| deletion-r5-small-3.private.json | 3,770,945,288 | 189,370 | `9d24d8535c56c189bb4f1d52db43970c1d05f4a64ecb30731fd160218115022a` |

The initial read-only inventory measured 775,994,833,226 bytes (722.7 GiB) in the MatterSyn workspace across 12,858,559 files. This is the starting inventory, not the amount removed. C: had 148,004,110,336 bytes (137.84 GiB) free at that checkpoint.

Removal was limited to obsolete generated output with retained reconstruction evidence and files proved identical to approved, remote-backed public Git content. Each deletion scope was rechecked for content, path containment, protected directories, reparse points and active use. Selected source figures remain in the canonical public repositories; only their redundant working copies were removed.

Original papers/SI and owner-created folders were preserved. The two canonical working repositories, the current unpublished candidate, pending packages, unique private receipts, the authorized local model and its offline runtime remain local. No full papers, raw source text, private audits, unreviewed drafts or credentials were uploaded. Mixed archived Git/worktree copies and private evidence directories lack whole-copy reconstruction proof and remain retained; this checkpoint does not claim that every non-paper file has been removed.

Deletion accounting counts each completed event once. Identical receipt snapshots are excluded; later removals of residual files at the same path are separate events. Interrupted work without a persisted receipt is uncredited, so confirmed logical bytes and files are lower bounds. Changes in C: free space are measured separately and can also reflect allocation and other activity on the computer. No fresh full-workspace inventory was substituted for the starting inventory.

Follow [the storage workflow](storage-workflow.md): keep reviewed code, data, citations, memory, skills and safe summaries durably in GitHub; use the necessary working checkouts and a bounded staging area; retire verified obsolete payloads at checkpoints. GitHub's ordinary repository limits and the public/private boundary prevent treating it as a backup for hundreds of gigabytes of caches, private source evidence or local model weights.
