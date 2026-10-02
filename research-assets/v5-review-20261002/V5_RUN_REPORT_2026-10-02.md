# MatterSyn workflow v5: first 35 hours, and how to fix quality and speed

*Prepared 2026-10-02 11:30 CDT; updated the same day with the owner's decisions (§0). Window: workflow v5 adopted (2026-10-01 00:35 CDT) to 2026-10-02 11:11 CDT, 34.6 hours.*

**How this was measured.** Everything here is read-only:

- the commit history of `cuiyist/mattersyn` and `cuiyist/mattersyn-site`
- the live site
- the published records

I changed nothing on GitHub during the analysis and did not contact your agent. At the owner's request, this report and its two support files were then saved to the side branch `v5-fix-plan-20261002` (folder `research-assets/v5-review-20261002/`); `main` was not touched. Your agent's private ledger and deep-audit log are on the curation machine, so I estimated stage times from commit times. Paper text was not read. My checks in §5 use only the published records.

---

## 0. Owner decisions (2026-10-02)

| # | Question | Decision | Where it is applied |
|---|---|---|---|
| 1 | Stop rule counts only critical and major (S1/S2) errors? | **Yes** | §7.1 step 2 |
| 2 | Rank semiconductor quantum-dot papers above Ag/Au/Bi nanocrystals? | **Yes.** Metal nanocrystals stay in scope, ranked after QDs | §7.3, §9 |
| 3 | How many agents after the hold lifts? | **As many as possible**, added in steps, with auditor and integrator ratios kept | §7.4, §7.5 |
| 4 | Deep-audit a sample of 10 older papers? | **Yes** | §7.2 (list of 10) |
| 5 | Who makes the release-script fixes? | **The owner's agent** | §7.3, §9 |

These decisions are final; §8 records them. The agent instructions in §9 include all of them.

---

## 1. Summary

- **Speed.** 36 new papers went live in 17 releases: **1.04 papers/hour**. Before v5 the rate was 0.8/hour. The pace is steadier (no idle gaps), but far below my 3–5/hour estimate and the 20/hour target. New records per paper fell from about 8.5 to 3.9 (median 2), and 18 of the 36 papers added a single record.
- **Quality hold.** The deep audit (the sampled ~10%) found an error in **7 of the 9 sampled papers**. That triggered the stop rule at about 07:57 this morning. The agent has stopped new extraction and is only correcting and re-auditing papers it already extracted. **The current rate of new papers is about 0.**
- **My checks of the 36 published papers.**
  - Numbers, stoichiometry and internal links are clean: 1,424 quoted values match their source quotes, there are no mass/mole errors, and no links are broken.
  - The problems are of other kinds:
    - key inputs not connected to any step in the recipe structure (5 papers)
    - reagents named in a step but not attached to it (12 papers)
    - temperatures or times that may be observed events rather than set-points (11 papers to check)
    - four public material pages with formulas like "CdSe/ZnS4", where "4" is a shell monolayer count
  - On these checks, v5 papers are **no worse than older papers**. Older papers have 12 mass/mole mismatches across 8 papers, and v5 papers have none. The quality problem is probably not new to v5. The deep audit is simply the first strict measurement of it.
- **Why speed stayed low:**
  - Small batches: 2.1 papers per release, each release taking about 35 minutes from source push to live. That is about 29% of the window.
  - Release-gate patches and repairs: 16 of the 38 commits were binding, gate or repair work, including one 3-hour continuous-integration (CI) repair.
  - Long per-release notes: about 4,400 words in MEMORY.md and PUBLICATION.md.
  - The number of parallel agents isn't visible from GitHub.
- **The fix, in order:**
  1. Lift the hold safely: rate errors by severity (only critical and major errors count toward the stop rule), add a blind completeness check, run automated checks before each audit, and test the new quick audit on the 9 known cases.
  2. Deep-audit 8 of the 36 published papers, then 10 older papers.
  3. Your agent makes the process changes: QD papers first, bigger batches, no gate patching, automatic baseline, short notes.
  4. Run as many agents as possible once the quality check passes, added in steps with fixed auditor ratios.
- **Expected after the fixes:**
  - about 1.2–1.5 papers/hour with the current staffing
  - **about 3–5/hour** with 4 extractors, 2 auditors and 1 integrator
  - possibly 6–9/hour with 8 extractors and 12–18/hour with 16 extractors (untested; limited by paper supply and release cadence)
  - 20/hour still most likely needs the calibrated machine-extraction lane (silver)

---

## 2. What happened: the 17 releases

| Live (CDT) | Papers | Records | Push → live | Source commits in the batch |
|---|---:|---:|---:|---|
| 10-01 03:12 | 2 (Chen 2020 CQD, Zou 2022 MnO₂) | 2 | 15 min | v5 setup (3), 2 papers, 3 release-helper fixes |
| 04:22 | 1 (Chen 2014 Cu–Zn–Sn–S) | 6 | 34 min | 1 |
| 06:20 | 2 (Massasa 2024, Zhang 2012) | 10 | 42 min | 1 paper + 2 bind + 1 correction + 1 illustration |
| 07:32 | 3 (Slejko 2017 c-ALD, Huang 2015, Dierick 2014) | 20 | 39 min | 1 |
| 09:42 | 3 (Buschmann 1998, Jasieniak 2005, Li 2001) | 14 | 39 min | 1 |
| 11:35 | 1 (Yang 2009) | 7 | 32 min | 1 |
| 13:02 | 2 (Tan 2006, Li 1999) | 7 | 38 min | 1 |
| 14:23 | 2 (Bhattacharya 2023, Fafarman 2014) | 10 | 42 min | 1 |
| 16:12 | 1 (Fanfair 2005) | 1 | 23 min | 1 paper + 1 bind + 1 gate patch |
| 17:47 | 2 (Urban 2007, Sahoo 2010) | 7 | 26 min | 1 paper + 1 gate patch |
| 20:07 | 3 (Yuan 2026, Lin 2021, Klecha 2009) | 10 | 35 min | 3 papers + 1 bind |
| 21:43 | 3 (Choi 1999, Klecha 2010, Ouhenia-Ouadahi 2016) | 3 | 42 min | 1 |
| 22:52 | 1 (Munechika 2011) | 1 | 33 min | 1 |
| 10-02 00:04 | 1 (Saikia 2022) | 1 | 36 min | 1 |
| 02:51 | 3 (Naiki 2013, Liu 2008, Jung 2024) | 3 | 35 min | 1 paper + 1 gate patch + 1 illustration |
| 06:33 | 4 (Chan 2007, Ko 2010, Routzahn 2014, Yao 2009) | 4 | 58 min | 1 paper + 1 gate patch |
| 10:06 | 2 (Henkel 2009, Xu 2008) | 33 | 30 min | 1 paper + baseline repair + 2 illustration corrections |
| **Total** | **36** | **139** | **≈10 h** | 38 agent commits |

The live site now has 174 papers and 1,703 records (version 0.41.2), and it matches GitHub.

Packages that were extracted but not published include Jacobson and Knowles (errors found), Fu and Masuo (corrections pending) and Sahu (held). So the agent extracted more than 36 papers.

---

## 3. Speed

### 3.1 Measured

| | Papers/hour |
|---|---:|
| v5, whole window (34.6 h) | **1.04** |
| v5, adoption to hold (31.4 h) | 1.08 |
| Best 4-hour stretch | 2.0 |
| Best 12-hour stretch | 1.33 |
| Before v5 (9/26–9/30): overall / while active / peak | 0.8 / 1.6 / 2.6 |
| Since the hold (07:57) | ≈0 new papers (only the already deep-audited Henkel/Xu were released) |

Time between releases: 69–222 minutes, median 109.

### 3.2 Where the time went (estimated from commit times)

| Activity | Share of 34.6 h | Evidence |
|---|---:|---|
| Release: source push → live (CI wait, two builds, browser review, Pages, live check) | **≈29%** (≈10 h) | 17 releases × 15–58 min, median 35 |
| Gate patches, bind commits, repairs, corrections | **≈12–15%** | 16 of 38 commits; the Henkel/Xu batch took 3 h from integration to live instead of the usual ~35 min (failed CI on stale baseline counts, then two illustration corrections) |
| Extraction, quick audits, deep audits, figures and visuals, unpublished packages | ≈55–60% | the remainder |

If several agents worked in parallel, these shares overlap. Running `package_workflow.py metrics` on the private ledger gives the exact split.

### 3.3 Why the speed is below my estimate

My 3–5/hour estimate assumed **3 extractors running in parallel**, and it treated the quick audit as a sufficient check. The measured ~1 paper/hour matches what **one** extractor produces, and the quick audit turned out not to be sufficient (§4). I got both of those wrong.

Specific drags:

1. **Small batches.** 17 releases averaged 2.1 papers each. Every release pays the same ~35 minutes regardless of size, which is about 17 minutes per paper.
2. **Fragile release gate.** The scoped-paper route check, added on 10-01, compares the status text against a fixed list of ten wordings. Every new wording blocked a release until someone patched `release_batch.py`. That happened four times (15:49, 17:20, 01:29, 05:36).
3. **A manual baseline step.** The record count and release baseline had to be updated by hand. Forgetting it failed CI on the Henkel/Xu batch (07:06 → 10:06).
4. **Separate "bind" commits** (5 of them), which workflow v5 retired.
5. **Per-release notes** in MEMORY.md, PUBLICATION.md and curation-control.json: 17 + 12 + 4 commits, about 4,400 words, or about 120 words per paper. This is the same status-reporting overhead found on 9/26, returning in a smaller form.
6. **Low yield per paper.** 18 of 36 papers added exactly one record. Many are assembly or deposition studies (for example Ag superlattices) rather than synthesis series. They count as papers but add little recipe data.

---

## 4. The quality hold

### 4.1 What the agent found

From the agent's commit `c6d2495b` (10:24 today):

- The private deep-audit log has 9 distinct sampled papers, **7 with at least one error**.
- The runbook's stop rule (more than 5 of the last 50) fired. New extraction and claims are paused.
- Frozen packages with open findings (Jacobson, Knowles and others) stay unpublished.
- The agent strengthened the quick-audit checklist itself and wrote that the revised checks must be tested independently before extraction resumes.

The agent followed the stop rule correctly and did not relax any gate.

### 4.2 Error types (inferred from the checks the agent added)

| Type | What goes wrong |
|---|---|
| **Omissions** | Inputs left out, even unquantified ones. Deposition, purification or assembly branches missing. Exclusions that hide variants. |
| **Sample assignment** | A typical or study-wide preparation presented as an individually measured sample. A general-context relation shown as an exact recipe→structure pair. |
| **Conditions** | An observed event (for example "until the solution clears") recorded as if it were the heater set-point, or the reverse. |
| **Shared visuals** | A reused molecule card with the wrong role or caption. Illustrations or legends that don't match the source figure (the Xu illustrations were corrected). |
| **Conflicts and locators** | Figure labels, body text and captions not kept as separate statements. Locators not tied to exact panels. |

The private log doesn't separate serious errors from minor ones. The stop rule counts **any** error, so a caption mistake counts the same as a wrong temperature. With 9 samples, we can't yet tell how many of the 7 are serious.

### 4.3 What it means

- **The quick audit as I designed it misses too much.** It checks the extracted package against its receipts. That catches mistakes in what was extracted, but it can't see what was **left out**, and it rarely catches a plausible but wrong sample assignment. Those need someone to read the methods section of the paper.
- **The 36 published papers had only the quick audit.** If the 7-of-9 rate held for serious errors, many of them would need corrections. That is not established, so §7.2 deep-audits a sample of them.
- **Older papers may be affected too.** My checks show no sign that v5 papers are worse than older ones (§5.2).

---

## 5. My checks of the 36 published papers

I wrote `check_records.py` (in the same folder as this report). It uses only the standard library and reads no paper text. It runs over the canonical records and flags internal inconsistencies as questions for an auditor, not as verdicts.

### 5.1 Results (139 records, 36 papers)

| Check | Result | Papers |
|---|---|---:|
| Each value matches the numbers in its own quoted source text | **1,424 values checked, 0 mismatches** | 0 |
| Mass ↔ moles from the formula; concentration × volume ↔ moles | **0 mismatches** | 0 |
| Broken references (step inputs, measurement→sample, figure→sample, link evidence) | **0** | 0 |
| Illustration marked as a measured structure | **0** | 0 |
| Declared input that never enters any step | 18 flags | **5** |
| Reagent named in a step's text but not attached to that step | 40 flags | **12** |
| Temperature or time in a step that describes an event ("until clear", "turns", "reaches") | 66 flags in 16 steps | **11** |
| Shell monolayer count written as a formula subscript | 4 records | **1** |
| Unit spellings that aren't standardized (°C vs degC, uL vs µL, M vs mol/L) | 237 values | 20 |

**Examples worth fixing:**

- **Slejko 2017 (Chem. Mater., c-ALD shells).** Four records use formulas such as `CdSe/ZnS4`, `CdSe/CdS4` and `CdSe/CdS2/ZnS2`, where the digit is a monolayer count. Each became a separate public material page, for example "CdSe/ZnS4 literature collection" (`material.html?id=cdse-zns4-d24dd9`). Readers will see "ZnS4" as a compound. It should be a core/shell formula plus a separate shell-thickness field.
- **Li 1999 (DBS-aged Ag), Massasa 2024 (AMTP-Br, OAM-Br), Yuan 2026 (MeOAc, DMF), Urban 2007 (TOPO, toluene), Jung 2024 (APTES).** Declared reagents never enter a step. For Li 1999, hydrazine and DBS sit in a stock that isn't linked to the step that uses it. The reader page still shows the text, but the recipe structure (what model training uses) is missing the reductant.
- **Bhattacharya 2023, Slejko 2017, Dierick 2014, Massasa 2024 and others.** Steps such as "heat to 180 °C until clear" or "heat until a clear solution forms" with a recorded temperature. These are exactly the event vs set-point class the deep audit found, and an auditor should check each against the paper.

### 5.2 v5 papers compared with older papers (same checks, all 1,703 records)

| Check | Older papers flagged (of 137) | v5 papers flagged (of 36) |
|---|---:|---:|
| Mass ↔ moles mismatch | **8 (6%)** | 0 |
| Value differs from its own quote | 4 (all unit or word formats such as "1 min" → 60 s; no real mismatch) | 0 |
| Declared input never used | 57 (42%) | 5 (14%) |
| Named but not attached | 42 (31%) | 12 (33%) |
| Event vs set-point question | 26 (19%) | 11 (31%) |

Some older mismatches look like real record errors and need a source check:

- **Owen 2008 shell recipe:** 0.608 g ZnEt₂ is 4.9 mmol, but the record says 0.492 mmol (a factor of 10).
- **Gu 2004:** 2.28 g CdCl₂ is 12.4 mmol, but the record says 10 mmol. The hydrate CdCl₂·2.5H₂O would give 10 mmol, so the formula may be missing the hydrate.

**Reading:** v5 papers are not worse on what can be checked automatically. The deep-audit result probably reflects a long-standing gap in what audits check, not a v5 regression.

---

## 6. Root causes

**Quality**

1. The quick audit checks the package, not the paper, so omissions and plausible misassignments get through (my design gap).
2. The stop rule doesn't separate severity, so presentation slips and wrong recipe values count the same.
3. Figures and visuals ship with every paper (your decision, which I keep). That adds an error surface (illustrations, reused molecule cards) that the old checklist didn't cover.
4. No automatic consistency checks run before the audit, so auditor attention isn't directed at the risky spots.

**Speed**

1. Release overhead is paid per batch, and batches are small.
2. A fixed list of status wordings in the release gate breaks on new wording.
3. The baseline and record-count update is manual.
4. Bind commits and per-release notes are back.
5. Staffing is probably one extractor; the agent count isn't visible from GitHub.

---

## 7. The fix

### 7.1 Lift the hold safely (in order)

1. **Rate the 9 deep-audit findings by severity** (private, by the agent):
   - **S1 critical:** a wrong or missing value that changes how the recipe is run; a wrong recipe→sample or sample→structure link; a missing variant or essential input; a measured claim that wasn't measured.
   - **S2 major:** a set-point/event mix-up; a wrong reagent identity or role; an illustration that contradicts the source figure; a conflict silently resolved.
   - **S3 minor:** a caption or wording slip, locator precision, unit spelling, card styling.

   Report two counts to you: papers with any S1/S2 error, and papers with only S3 errors.
2. **New stop rule (approved by the owner on 2026-10-02):** stop when more than 5 of the last 50 sampled papers have an **S1 or S2** error. S3 errors are logged and fixed in weekly batches and don't stop extraction. The current hold is lifted only through the resume test in step 5, not by re-counting the old log under the new rule.
3. **Add a blind completeness pass to the quick audit** (about 10–15 minutes per paper). Before opening the package, the auditor reads the in-scope Methods/Experimental text and figure captions and writes their own list of inputs, steps, variants and samples. Then they compare it with the package. This is the only cheap way to catch omissions.
4. **Run automatic checks before every quick audit.** Run `check_records.py` on the candidate records and resolve every flag that isn't a style issue in the audit notes. It targets binding gaps, event vs set-point steps, mass/mole and concentration math, quote numbers and formula notation.
5. **Test the revised quick audit (the resume gate).** An auditor who hasn't seen the deep-audit findings re-audits the **original frozen versions** of the 9 deep-audited papers, using steps 3 and 4. The test **passes if it catches at least 80% of the S1/S2 findings**. If it fails, look at what was missed, revise the checklist and test again.
6. **Resume with a 25% deep-audit rate for the next 40 papers** (about 10 samples). If at most 1 of them has an S1/S2 error, return to 10%. If more, stop again.

### 7.2 Check the 36 published papers

Deep-audit **8 of them** (22%), chosen as 6 highest-risk plus 2 random so the result also says something about the low-risk ones:

| # | Paper | Why |
|---|---|---|
| 1 | Slejko 2017, CdSe c-ALD shells (`chemmater2017-cdse-cald-7b01873`) | 11 records; formula notation; event step |
| 2 | Massasa 2024, layered perovskites (`massasa2024-cgd3c01472`) | unused precursors; 2 event steps |
| 3 | Urban 2007, PbTe/Ag₂Te (`urban2007-pbte-ag2te-nmat1826`) | unused additives; 6 records |
| 4 | Bhattacharya 2023, AgInTe₂/ZnS (`bhattacharya2023-aginte2-zns-ic3c03156`) | 5 dissolve/"until clear" steps with set temperatures; 9 records |
| 5 | Ouhenia-Ouadahi 2016, Ag superlattices (`ouhenia-ouadahi2016-ag-superlattices-cm6b01374`) | 9 named-but-unattached solvents |
| 6 | Yuan 2026, AgBiS₂ (`yuan2026-agbis2-nl5c06337`) | unused antisolvent/dispersion |
| 7 | Chen 2020, CQD (`chen2020-cqd-d0ra03970e`) | random |
| 8 | Li 2001, Ag₂Te/Ag₇Te₄ (`li2001-ag2te-ag7te4-jssc9103`) | random |

Henkel 2009, Xu 2008 and Sahoo 2010 were already deep-audited, so they're excluded. If any paper above is already in the deep-audit log, take the next one from `published-36-risk.json` (same folder).

Corrections go through the normal release path, in one batch. Also fix the four `CdSe/…n` formulas and the binding gaps found in §5.1, after checking each against the source.

### 7.2b Check 10 older (pre-v5) papers (approved by the owner)

Run these after the 8 v5 papers above. The list is 5 papers flagged by the mass/mole check plus 5 random semiconductor colloidal papers (a deterministic hash draw from the 57 older ones), so the result also estimates the error rate in the older collection.

| # | Paper (source group) | Why |
|---|---|---|
| 1 | Owen 2008, CdSe shells (`owen2008-cdse-ja804414f`) | ZnEt₂ 0.608 g is 4.9 mmol, record says 0.492 mmol; (TMS)₂S also off by a factor of 10; 21 records |
| 2 | Veinot 1997, CdS (`veinot1997`) | Cd acetate 5.05 g is 21.9 mmol, record says 29 mmol; 21 records |
| 3 | Evans 2010, PbSe (`evans2010`) | Pb oleate and Se-phosphine mass vs mmol differ by a factor of 2; 32 records |
| 4 | Gu 2004, FePt/CdS (`gu2004`) | CdCl₂ 2.28 g fits 10 mmol only as the hydrate; the formula may be missing it |
| 5 | Basel 2020, CuFeS₂ and others (`basel2020`) | S 6 mg is 0.187 mmol, record says 0.2 mmol (small; check rounding) |
| 6 | Zhan 1999, jaipurite CoS (`zhan1999jaipurite`) | random |
| 7 | Sn₄P₃ 1999 (`sn4p3-1999-jssc19998315`) | random |
| 8 | Yu 1998, CdE (`yu1998cde`) | random |
| 9 | Li 2000, Cu₂SnS₃ (`li2000cu2sns3`) | random |
| 10 | Li 2009, CdS (`li2009-nn9009455`) | random |

Record these results in a **separate retrospective log**, not the v5 rolling window. The older papers went through earlier workflows, so they don't count toward the v5 stop rule. Correct confirmed errors through the normal release path. If 3 or more of the 5 random papers have an S1/S2 error, tell the owner: the older collection then needs a wider review.

### 7.3 Speed fixes (none relaxes a quality gate)

| Change | Expected effect |
|---|---|
| **Release when at least 6 papers are ready or 3 hours have passed**, whichever comes first | Release overhead drops from ~17 to ~5–6 min per paper (about +15–20% throughput) |
| **One enumerated status field** (for example `review_scope_kind: scoped_independent_audit`), checked when the package is frozen, replacing the free-text wording list in `release_batch.py` | No more release-blocking gate patches |
| **Regenerate the release baseline and record count automatically** inside the source-release preparation step | No more failed-CI repairs like Henkel/Xu (≈2.5 h) |
| **Stop per-release notes.** The ledger is the record; one short daily line in MEMORY.md at most; PUBLICATION.md only for process changes | Removes ~120 words of writing per paper |
| **No separate bind commits** (as v5 already says) | Fewer CI cycles |
| **Queue order (owner decision): semiconductor QD papers first, Ag/Au/Bi and other metal nanocrystals after them.** Within each group, favor papers whose chemistry already has molecule cards, unit cells and apparatus scenes | More records per paper; cheaper figures and visuals |
| **Keep the browser review, but only on the new paper routes plus one affected material page** | Shorter release step |

**Who makes the code changes (owner decision): your agent.** There are three:

1. the enumerated status field
2. the automatic baseline and record count
3. QD-first ordering in `package_workflow.py rank`

The agent makes them during the hold, while no release is running, on a branch with tests. It merges through the normal single-commit source path only after CI passes, and reports the diff to you. Neither change may loosen a check. The enumerated field must reject everything the wording list rejected today, and the baseline step must still fail on a changed prior record or eligibility.

### 7.4 Staffing (owner decision: as many agents as possible)

Run as many agents as the curation machine and the agent service allow, but keep these ratios and add agents in steps.

| Role | How many | Why |
|---|---|---|
| Extractor | as many as possible | one active paper plus one claimed next each |
| Quick auditor | **1 per 2 extractors** while deep audits run at 25%; **1 per 3** after returning to 10% | the quick audit now includes the completeness pass (~25–30 min), and auditors also do the deep audits |
| Integrator / releaser | **1** up to about 8 papers/hour; above that a **2nd** integrator prepares merges, but only one release runs at a time | releases are serialized (one site push at a time) |

**Ramp in steps:**

1. Start at 4 extractors (+2 auditors, 1 integrator).
2. Go to 8, then 12, then 16 extractors, with matching auditors.
3. Move up a step only when:
   - (a) the last step's deep audits show at most 1 S1/S2 error per 10 sampled papers
   - (b) no claim collisions happened (two agents on one paper)
   - (c) the integrator has no backlog of more than 2 batches
   - (d) the machine isn't saturated (CPU, memory, disk, service rate limits)

**Rules that don't change with scale:**

- Every agent has its own ID. The reviewer is never the author. Deep audits are done by someone other than the quick auditor.
- **Paper supply:** at more than 10 papers/hour, the screened semiconductor-QD queue may run out within days. The agent should report the remaining queue size (QD and metal separately) at each ramp step.

### 7.5 Expected speed (conservative)

| Stage | New papers/hour |
|---|---:|
| Now (hold) | ≈0 |
| Resume with current staffing, revised quick audit, 25% deep audits | 0.7–1.0 |
| + speed fixes (§7.3) | 1.2–1.5 |
| + 4 extractors, 2 auditors, 1 integrator | **3–5** |
| + 8 extractors, 4 auditors, 1 integrator | 6–9 (untested) |
| + 16 extractors, 8 auditors, 2 integrators | 12–18 (untested; likely limited by paper supply and release cadence) |
| + machine-extraction lane after calibration (needs a local model on the curation machine) | +10–25 |

Each extractor is assumed to produce 0.8–1.2 papers/hour after the extra quality steps. That rate is measured only for about one extractor; the larger rows are projections. Measure each ramp step from the ledger (`package_workflow.py metrics`) before taking the next. 20 papers/hour with audited papers alone needs roughly 16–20 extractors plus 8–10 auditors. The calibrated silver lane remains the cheaper route.

---

## 8. Decisions (answered by the owner, 2026-10-02)

1. **Severity-based stop rule:** yes. Only S1/S2 errors count toward the stop rule (§7.1 step 2).
2. **Semiconductor QD papers ranked above Ag/Au/Bi nanocrystals:** yes. Metal nanocrystals stay in scope after QDs (§7.3).
3. **Number of agents:** as many as possible, ramped in steps with fixed auditor and integrator ratios (§7.4).
4. **Deep-audit 10 older papers:** yes. The list is in §7.2b.
5. **Code changes:** made by the owner's agent, on a branch with tests, without loosening any check (§7.3).

Still open (no decision needed now): the silver-lane calibration. It needs a local model on the curation machine.

---

## 9. Instructions for your agent (paste into its chat; nothing was pushed to GitHub)

```
How to read this from GitHub (read-only; do not merge this branch into main):
  git fetch origin v5-fix-plan-20261002
  git show origin/v5-fix-plan-20261002:research-assets/v5-review-20261002/V5_RUN_REPORT_2026-10-02.md
  git show origin/v5-fix-plan-20261002:research-assets/v5-review-20261002/check_records.py > <private work dir>/check_records.py
  git show origin/v5-fix-plan-20261002:research-assets/v5-review-20261002/published-36-risk.json > <private work dir>/published-36-risk.json

Owner instructions, 2026-10-02 (workflow v5 quality hold). The owner has decided:
(1) the stop rule counts only S1/S2 errors; (2) semiconductor QD papers are ranked before Ag/Au/Bi
and other metal nanocrystals; (3) run as many agents as possible after the hold, in steps;
(4) deep-audit 10 older papers; (5) you (the agent) make the code changes below.

Keep the hold: start no new extraction or source claims until step 6 passes and the owner confirms.

1. Rate every finding in the private deep-audit log by severity:
   S1 critical = wrong or missing value that changes how the recipe is run; wrong recipe->sample
     or sample->structure link; missing variant or essential input; claimed measurement not measured.
   S2 major = set-point vs observed-event mix-up; wrong reagent identity or role; illustration
     contradicting the source figure; conflict silently resolved.
   S3 minor = caption or wording, locator precision, unit spelling, card styling.
   Report to the owner: papers with any S1/S2, papers with only S3, and the error types.
   New stop rule: stop when more than 5 of the last 50 sampled papers have an S1/S2 error. S3 errors
   are logged and fixed in weekly batches. Do not lift the current hold by re-counting; use step 6.

2. Use check_records.py from research-assets/v5-review-20261002/ on branch v5-fix-plan-20261002 (read-only, standard library
   only). Do not merge that branch as it is. In your step 4 branch, add the checker as
   tools/workflow/check_records.py through the normal single-commit path, so later agents have it.
   Run it on recipe-atlas/data/records. Triage every non-style flag for the 36 v5 papers against the source.
   Also fix the four Slejko 2017 formulas (CdSe/ZnS4 etc.: shell monolayer counts written as subscripts).

3. Deep-audit these 8 published v5 papers (skip any already in the deep-audit log; replace with the
   next one from published-36-risk.json): chemmater2017-cdse-cald-7b01873, massasa2024-cgd3c01472,
   urban2007-pbte-ag2te-nmat1826, bhattacharya2023-aginte2-zns-ic3c03156,
   ouhenia-ouadahi2016-ag-superlattices-cm6b01374, yuan2026-agbis2-nl5c06337,
   chen2020-cqd-d0ra03970e, li2001-ag2te-ag7te4-jssc9103.
   Then deep-audit these 10 older papers, in a SEPARATE retrospective log (not the v5 rolling 50):
   owen2008-cdse-ja804414f, veinot1997, evans2010, gu2004, basel2020, zhan1999jaipurite,
   sn4p3-1999-jssc19998315, yu1998cde, li2000cu2sns3, li2009-nn9009455.
   If 3 or more of the last 5 (the random ones) have an S1/S2 error, tell the owner.
   Publish confirmed corrections through the normal release path, batched.

4. Code changes (you make them now, during the hold, while no release is running; one branch,
   with tests; merge through the normal single-commit source path only after CI passes; report the
   diff to the owner; never loosen a check):
   a. Replace the free-text main_status wording list in release_batch.py with one enumerated field
      (e.g. review_scope_kind: scoped_independent_audit) set and validated when the package is
      frozen. It must reject everything the wording list rejects today.
   b. Regenerate the release baseline and the blueprint record count automatically inside the
      source-release preparation step; it must still fail if any prior record digest or task
      eligibility changes.
   c. package_workflow.py rank: order semiconductor QD units before metal (Ag/Au/Bi/Pt/Pd/Cu
      metal) nanocrystal units; keep the existing evidence ordering within each group.

5. Quick-audit changes: before opening a package, the auditor reads the in-scope Methods/Experimental
   text and figure captions and writes an independent list of inputs, steps, variants and samples,
   then compares it with the package. Run check_records.py on every candidate and resolve each
   non-style flag in the audit notes.

6. Resume test: an auditor who has not seen the deep-audit findings re-audits the ORIGINAL frozen
   versions of the 9 deep-audited papers using step 5. Report the share of S1/S2 findings caught.
   Resume only if it is at least 80% and the owner confirms.

7. After resuming:
   - Deep-audit 25% of the next 40 papers; return to 10% only if at most 1 has an S1/S2 error.
   - Staffing: as many agents as possible, added in steps (4 -> 8 -> 12 -> 16 extractors). Keep
     1 quick auditor per 2 extractors while deep audits are at 25% (1 per 3 at 10%) and 1 integrator
     (a 2nd only to prepare merges above ~8 papers/hour; one release at a time). Go up a step only
     if the last step had at most 1 S1/S2 per 10 deep audits, no claim collisions, an integrator
     backlog of at most 2 batches, and spare machine capacity. Every agent has its own ID; the
     reviewer is never the author. Report the remaining QD and metal queue sizes at each step.
   - Release when at least 6 papers are ready or 3 hours have passed.
   - No per-release notes in MEMORY.md, PUBLICATION.md or curation-control.json (the ledger is the
     record; one daily line at most). No separate bind commits.
   - Do not edit policies or allowlists to pass a gate.
```

---

## 10. Files

On GitHub: branch `v5-fix-plan-20261002`, folder `research-assets/v5-review-20261002/`. Locally: `~/Desktop/mattersyn/` (report) and `~/Desktop/mattersyn/v5-review/` (the rest).

| File | Contents | On GitHub? |
|---|---|---|
| `V5_RUN_REPORT_2026-10-02.md` | This report | Yes |
| `check_records.py` | The read-only record checker (standard library only). `python3 check_records.py <records dir> [--groups g.json] [--out flags.json]` | Yes (§9 steps 2 and 5 use it) |
| `published-36-risk.json` | Risk ranking used for §7.2 (replacement papers) | Yes (§9 step 3) |
| `published-36-flags.json` | All flags for the 36 v5 papers (record, location, message) | No (running the checker recreates it) |
| `release-timeline.json` | The 17 releases with their papers, record counts and source commits | No (for the owner) |
