# MatterSyn job review: full-audit run, Oct 2–6, 2026

*Prepared 2026-10-06 22:40 CDT; updated the same day with the owner's decision on step 4 (raise the sampling rate). Window: restart under the full-audit plan (Oct 2, 22:40 CDT) to the pause (Oct 6, 19:14 CDT).*

**How this was measured.** Read-only, from the commits of `cuiyist/mattersyn` and `cuiyist/mattersyn-site`, the live site, the published records, and the agent's own public status notes. The agent's private ledger and audit findings are on the curation machine. I changed nothing during the review and did not contact the agent. No paper text was read. At the owner's request this file was then saved to the side branch `job-review-20261006` (folder `research-assets/job-review-20261006/`); `main` was not touched.

---

## 1. Summary

- **Output.** 58 new papers and 1,262 new records went live in 18 releases. The site now has 231 papers and 2,965 records.
- **Speed.** 0.63 papers/hour over 92 hours. The best day (Oct 4) reached 32 papers, or 1.33/hour, with three sessions running.
- **Much more data per paper.** The median new paper has 22 records; under the quick workflow it was 2. Measured in records, the run produced 13.7 records/hour against 4.0 before, about 3.4 times more.
- **Scope is right.** Every new paper is a semiconductor quantum-dot paper (InP, CdSe/CdS, CdS, CdSe, CdTe, PbS, PbSe).
- **Quality stopped the run again.** The third-agent deep audits found a critical or major error in 5 of 14 sampled papers (6 of 15 with one supplemental audit). That is over the stop rule's limit of 5, so the agent stopped on Oct 6 and is waiting for you.
- **Known errors are still live.** The 20 older quick-audited papers were all re-audited: 97 findings, 25 corrected on the site, **72 not yet corrected**.

---

## 2. Speed

| | Papers | Papers/hour |
|---|---:|---:|
| Whole window (92.2 h) | 58 | 0.63 |
| Agent's own figure for its first 40 papers (61.6 h) | 40 | 0.65 |
| Oct 3 (first batch, one session) | 5 | — |
| Oct 4 (three sessions) | 32 | 1.33 |
| Oct 5 | 10 | 0.42 |
| Oct 6 (stopped at 13:41, then four papers finished) | 11 | — |

- **Three sessions worked.** On Oct 3 you approved two extra extract-and-audit sessions, each with up to 4 agents, sharing claim files. The original session does all releases. Oct 4 shows what this setup can do when nothing is waiting.
- **Oct 5–6 were slower** because of waits for your instructions, the re-audit of the 20 older papers, and corrections.
- **My estimate held.** I estimated 1–2.5 papers/hour for three sessions. The best day was 1.33.

### The release step is getting slower

| | Quick workflow (Oct 1–2) | This run |
|---|---:|---:|
| Last source commit → live (median) | 35 min | **84 min** |
| First source commit of the batch → live (median) | — | 126 min |
| Papers per release | 2.1 | 3.2 |

- The site has grown from 1,703 to 2,965 records, and the release checks read everything each time. The agent measured 504 seconds for the inventory passes alone.
- 17 of 41 source commits were fixes rather than new papers. Six of them fixed long chemical names overflowing on phone screens, one case at a time.
- Batches stayed small because the 3-hour rule usually fired before 6 papers were ready.

---

## 3. Quality

### 3.1 Deep-audit results in this run

| Sample | Papers audited | With a critical or major error |
|---|---:|---:|
| First 40 papers | 10 | 4 |
| All so far (formal) | 14 | 5 (36%) |
| All so far, including one supplemental audit | 15 | 6 (40%) |
| Earlier quick-audit workflow, for comparison | 9 | 7 (78%) |

- An extractor plus a full independent auditor halves the error rate of the quick audit, but about 1 paper in 3 still reaches the site with a serious error.
- Errors found in sampled papers were corrected. The 43 or so unsampled new papers probably contain serious errors at a similar rate, so roughly 15 of them.
- The agent applied the stop rule correctly and did not reset the count.

### 3.2 The measure itself now works against rich papers

The stop rule counts a paper as failed if it has **any** critical or major error. That was reasonable when a paper had 2 records. A paper now has 22 records on the median and up to 58, each with dozens of values. One wrong value among a thousand fails the whole paper.

The public notes don't say how many errors each failed paper had. If it is one or two per paper, the error rate per record is a few percent, and per value far lower. For a training dataset, the rate per record or per value is the number that matters, and it matches how the machine-extraction lane is already judged (98%, 95% and 90% of values correct).

### 3.3 My checks of the 58 new papers (1,262 records)

| Check | Result |
|---|---|
| Values match their own quoted source text | 19 flags, all word or unit formats ("2 min and 30 s" stored as 2.5 min); no real mismatch |
| Mass ↔ moles | 13 flags in 4 papers. Dhaene 2019, Sun 2025 and Peveler 2016 are recorded as conflicts in the source paper. Park 2020 (CdO 60 mg printed with 0.44 mmol, a 6% gap) is not noted as a conflict |
| Broken references, illustrations marked as measured | none |
| Sample label used as a formula | 6 Mazumdar 2015 records ("CdS160/TiO2 photovoltaic cell") |
| Reagent declared but never used in a step | 17 papers |
| Possible set-point vs observed-event mix-up | 29 papers to check |

The agent ran the checker before each audit as instructed, and conflicts in the source papers are written down instead of silently fixed. The checker only sees internal consistency; the deep-audit errors are the kind only reading the paper finds.

---

## 4. Suggested next steps

1. **Correct the 72 open findings on the 20 older papers.** These are known errors on the live site. It needs no new extraction and doesn't touch the stop rule.
2. **Ask for the error numbers per record.** For the 15 deep-audited papers: errors per paper, records per paper, and error types. That shows whether quality is actually poor or the paper-level measure is too strict for large papers.
3. **Then decide the stop rule.** If the per-record rate is low, switch the rule to errors per 100 sampled records, with a limit you choose. If it is high, find the error types the full audit keeps missing and add a targeted check for each before resuming.
4. **Unsampled new papers: raise the sampling rate (owner decision, 2026-10-06).** The deep-audit rate goes from 25% to **50%**. The 50% figure is my proposal; change it if you prefer another.
   - **Papers already live:** deep-audit 14 more of the 43 unsampled papers, so that 29 of the 58 are covered. Pick them with the existing deterministic selection at 50%, so the 15 already audited stay in the sample.
   - **New papers after resuming:** deep-audit 50%. Step down to 25% and then 10% only when the error rate over the last 20 sampled papers is under the limit set in step 3.
   - All of these results count toward the stop rule as usual. Errors found are corrected through the normal release path.
5. **Speed, once quality is settled:**
   - Keep the three sessions; they gave 32 papers in a day.
   - Have the agent make the release checks read only what changed, so the release time stops growing with the site.
   - Fix the phone-screen text overflow once, with one general style rule.
   - Let batches reach 6 papers by relaxing the 3-hour rule to 4–5 hours.

---

## 5. Message for your agent

```
How to read this from GitHub (read-only; do not merge this branch into main):
  git fetch origin job-review-20261006
  git show origin/job-review-20261006:research-assets/job-review-20261006/JOB_REVIEW_2026-10-06.md

Owner instructions, 2026-10-06. Stay paused for new extraction. Do these now:
1. Correct the 72 open findings on the 20 historical v5 papers and release the corrections
   (no new-paper credit). Report how many were S1, S2 and S3.
2. Report, for each of the 15 third-agent audited papers in the full-audit regime: number of
   records, number of S1 and S2 findings, and the error type of each finding. Give the total
   S1/S2 findings per 100 sampled records.
3. From those error types, propose targeted checks the full auditor should add. Do not change
   the stop rule or the checklist yourself; wait for my decision.
4. Sampling rate (owner decision): raise third-agent deep audits from 25% to 50%.
   a. Among the 58 full-audit papers already live, deep-audit 14 more of the 43 unsampled papers,
      to reach 29 of 58. Use the existing deterministic selection at 50% so the 15 already
      audited stay in the sample. Count the results toward the stop rule; correct errors through
      the normal release path. This audit work is allowed during the pause.
   b. After I approve a resume, deep-audit 50% of new papers. Step down to 25% and then 10% only
      when the error rate over the last 20 sampled papers is under the limit I set.
5. Propose (do not merge without my approval) two release changes: inventory and verification
   passes that read only changed files where the gates allow it, and one general CSS rule for
   long chemical names and formulas on narrow screens.
6. Report when steps 1, 2 and 4a are done, then wait.
```
