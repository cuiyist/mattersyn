"""Cost proposal only. No API client, key access, jobs or spending."""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal
import json,hashlib
B=Path(__file__).resolve().parent
M=B.parent.parent
D=M/'deadline-20260920'
cutpath=D/'active-cutoff.json';cutraw=cutpath.read_bytes();cut=json.loads(cutraw)
planpath=B/'two-month-capacity-plan-20260920.json';planraw=planpath.read_bytes();plan=json.loads(planraw)
sources={
 'gpt55':{'url':'https://developers.openai.com/api/docs/models/gpt-5.5','title':'GPT-5.5 model documentation','accessed_UTC':'2026-09-20','facts':['Standard uncached input $5 and output $30 per million tokens.','Prompts over 272K input tokens incur higher full-session rates; the proposed budget avoids that band.']},
 'mini':{'url':'https://developers.openai.com/api/docs/models/gpt-5.4-mini','title':'GPT-5.4 Mini model documentation','accessed_UTC':'2026-09-20','facts':['Standard uncached input $0.75 and output $4.50 per million tokens.']},
 'reasoning':{'url':'https://developers.openai.com/api/docs/guides/reasoning','title':'Reasoning models','accessed_UTC':'2026-09-20','facts':['Reasoning tokens are billed as output tokens.']},
 'vision':{'url':'https://developers.openai.com/api/docs/guides/images-vision','title':'Images and vision','accessed_UTC':'2026-09-20','facts':['Image inputs convert to billable input tokens and count toward token rate limits.']},
 'batch':{'url':'https://developers.openai.com/api/docs/guides/batch','title':'Batch API','accessed_UTC':'2026-09-20','facts':['Eligible Batch processing offers 50% lower model costs with a 24-hour completion window.','Expired batches can contain completed, billed requests and uncompleted requests; reconcile per-request results and usage.']}
}
prices={'gpt-5.5':{'input_per_million_USD':5.0,'output_per_million_USD':30.0},'gpt-5.4-mini':{'input_per_million_USD':0.75,'output_per_million_USD':4.5}}
def cost(model,n,i,o):
 p=prices[model]
 return float(Decimal(n)*(Decimal(i)*Decimal(str(p['input_per_million_USD']))+Decimal(o)*Decimal(str(p['output_per_million_USD'])))/Decimal(1000000))
screen=cost('gpt-5.4-mini',50,30000,3000)
triage=cost('gpt-5.5',50,30000,3000)
scenarios=[]
for name,i,o in [('base_assumption',200000,40000),('high_assumption',600000,120000)]:
 retained=cost('gpt-5.5',20,i,o);total=screen+triage+retained
 scenarios.append({'name':name,'retained_count_budgeted':20,'input_tokens_per_retained_aggregate':i,'output_tokens_per_retained_aggregate_including_reasoning':o,
  'retained_USD_per_paper':retained/20,'retained_subtotal_USD':retained,'screening_subtotal_USD':screen,'independent_triage_subtotal_USD':triage,
  'standard_uncached_model_subtotal_USD':round(total,2),'reserve_to_proposed_200_USD_cap':round(200-total,2),
  'if_only_both_triage_passes_use_eligible_Batch_USD':round(retained+(screen+triage)/2,2),
  'all_eligible_Batch_arithmetic_only_USD':round(total/2,2)})
assert screen==1.8 and triage==12 and scenarios[0]['standard_uncached_model_subtotal_USD']==57.8 and scenarios[1]['standard_uncached_model_subtotal_USD']==145.8
data={
 'schema':'mattersyn-unapproved-pilot-budget/1','created_at':datetime.now(timezone.utc).isoformat(),'author':'/root/norberg2004_extract',
 'authorization':{'proposal_requested':True,'paid_execution_approved':False,'paid_jobs_submitted':0,'keys_read_or_requested':False,'API_spend_by_this_task_USD':0},
 'purpose':'Measure true source eligibility, cost, scientific error/rework, and end-to-end capacity before promising the two-month fixed-collection deadline.',
 'fixed_collection':{'cutoff_at':cut['cutoff_at'],'target_at_UTC':cut['target_at_utc'],'target_basis':cut['target_basis'],
  'pending_known_provisional_scopes':cut['counts']['included_pending_scopes'],'unmapped_cutoff_files':cut['counts']['unmapped_cutoff_files'],
  'nested_cutoff_candidates_held':cut['counts']['nested_cutoff_candidates_held'],'later_new_papers_separate':True,
  'caveat':'Scope count is provisional, not verified unique papers; reconcile held/unmapped cutoff files and version source updates. The earlier 60-day capacity model is a conservative scheduling scenario; the accepted target record uses two calendar months.'},
 'pilot_scope':{'representatively_selected_scopes':50,'initial_screening_model':'gpt-5.4-mini','independent_triage_scopes':50,'independent_triage_model':'gpt-5.5',
  'retained_end_to_end_maximum':20,'retained_model_provisional':'gpt-5.5',
  'source_sampling':'Stratified probability sample from the frozen collection across candidate evidence tiers, families, main/SI availability, source length, text/scanned format and table density; save inclusion probabilities, seed and source hashes. Do not choose only the easiest papers.',
  'all_no_recipe_decisions_audited':True,'negative_decision_rule':'An independent reviewer checks original main/SI source evidence for every proposed pilot exclusion. A cheap classifier/keyword score cannot authorize exclusion. Uncertain scopes remain unresolved.',
  'retained_selection':'Take at most 20 eligible sources through complete extraction, canonical records, separate scientific audit, CdSe-standard reader/visuals, site QA and verified publication. Choose a balanced retained subset; do not count the remaining eligible scopes as completed.',
  'if_fewer_than_20_retained':'Complete the eligible subset found and report the shortfall; do not silently extend the sample or claim a 20-paper benchmark. A separately specified larger pilot may be required.',
  'capacity_limit':'A 50-scope pilot, even if all 20 retained papers pass, cannot demonstrate sustained 190-scope/day production.'},
 'pricing':{'currency':'USD','verified_date_UTC':'2026-09-20','models':prices,'sources':sources,
  'basis':'Standard uncached model-token rates; no assumed cache discount, Batch discount, free credits or subscription coverage.',
  'request_context_policy':'Keep each GPT-5.5 billed prompt/session within the <=272K input pricing band. High 600K input/120K output allowance is aggregate across separate bounded author/auditor/repair/reader calls, never a single 600K prompt.',
  'not_included':'Paid hosted tools, external OCR services, compute/storage, taxes/regional surcharges, human expert labor or a later sustained throughput test. No prices for these have been assumed; they need separate approval if used.',
  'desktop_vs_API':'This is a separate proposed API token budget. It does not measure or convert the current desktop Codex plan usage. No API billing access or model availability has been verified for the user account.'},
 'token_envelopes':{
  'screening':{'count':50,'model':'gpt-5.4-mini','input_tokens_per_scope':30000,'output_tokens_per_scope':3000,'subtotal_USD':screen},
  'independent_triage':{'count':50,'model':'gpt-5.5','input_tokens_per_scope':30000,'output_tokens_per_scope':3000,'subtotal_USD':triage},
  'retained_base_stage_allocation_assumed':[{'stage':'source extraction and canonical authoring','input':80000,'output':16000},{'stage':'independent source/canonical audit','input':80000,'output':12000},{'stage':'reader and visual binding preparation','input':20000,'output':8000},{'stage':'bounded correction and recheck','input':20000,'output':4000}],
  'retained_high_allocation':'Three times the aggregate base allowance, preserving independent contexts and complete scientific work.',
  'accounting_contract':['Every input envelope includes instructions, source text, all model-billed image tokens, schema/tool outputs and source contexts resent to independent reviewers.',
   'Every output allowance includes visible output, billable reasoning and other billed output; reasoning is not an unbudgeted add-on.',
   'All author, independent auditor, correction, reader and visual-association calls count. Do not report cost for one model call as the cost of a finished paper.',
   'Image estimates depend on model/detail/resolution; reconcile estimates against each API response usage record. Never reduce legibility or omit source pages merely to fit an allowance.',
   'If a scanned/long paper exceeds the allowance, pause/reforecast within the cap or report it unfinished. Budget pressure does not justify weaker review.']},
 'cost_scenarios':scenarios,
 'proposed_cap':{'API_model_spend_hard_cap_USD':200,'status':'candidate_for_later_explicit_approval_not_currently_enabled','high_envelope_subtotal_USD':145.8,'unallocated_reserve_USD':54.2,
  'reserve_use':'Extra source-page image tokens, longer independent contexts, corrected responses and bounded rechecks; not permission to add unrelated services or a production run.',
  'enforcement_required_before_paid_execution':['Dedicated run budget ledger with billed plus conservatively reserved in-flight charges. Admit a request only if its worst-case capped token cost fits the remaining approved budget.',
   'Set bounded request input and total output limits including reasoning, and reserve concurrently queued/batched requests before submitting them.',
   'Stop submissions on missing usage, unresolved charge accounting, request-size overflow or cap risk. Reconcile completed/expired/retried requests by stable request ID before any retry.',
   'Keep a safety margin for estimation uncertainty. A project budget alert alone must not be represented as an implemented hard stop.',
   'Any expansion or spending above the approved cap requires a new explicit decision; the current task authorizes preparation only.']},
 'Batch_option':{'baseline_budget_uses_Batch':False,'eligible_discount_fraction':0.5,'completion_window_hours':24,'citation':sources['batch']['url'],
  'recommended_candidate':'Independent first-screen tasks, then a separate source-based triage wave when all needed source inputs are ready.',
  'tradeoff':'Dependent author-to-auditor-to-repair waves can accumulate multiple completion windows. Use synchronous calls on the critical path when quality and iteration speed require it; the discount does not prove faster completion.',
  'expiration':'Completed requests in an expired batch are billed. Reconcile output/error IDs, charge completed work, and resubmit only uncompleted eligible items after budget reservation.',
  'limits':'Model/account eligibility and queue/token limits must be verified before execution; not assumed from documentation availability.'},
 'measurement_plan':{
  'per_scope':['matched document/page counts and hashes','stratum/inclusion probability','eligibility and independent exclusion result','worker-active minutes by preprocessing/author/auditor/visual/repair','elapsed queue/start/finish times','root integration and publication minutes','actual billed input/cached/image and total output/reasoning token counts','retries, errors, rework and conflicts','canonical/figure/sample-pointer coverage','original-data errors found and fixed','record-level completeness and allowed missingness','actual browser/release verification'],
  'root_or_human_work':'Log desktop/root/human integration time separately from API cost and machine runtime. Record any expert adjudication time and unresolved chemistry conflicts.',
  'outputs':['50-scope sampling/disposition manifest','up to20 separately audited published contributions','per-stage cost and effort distribution, not only averages','weighted retention estimate with uncertainty','failed/censored work and reasons','updated pipeline bottleneck and capacity/budget recommendation'],
  'quality_gate':'No open critical factual, quantity/unit, sample-lineage, structure-identity, source-reference or reader/visual association error in a published item. Explicit source uncertainty is preserved, never silently treated as verified. All planned source items have a disposition; independent auditor signs the exact files.',
  'model_quality_gate':'Model choices are provisional. Compare accepted output against the established CdSe-standard evidence contract; reject or revise a routing choice if it misses synthesis, numbers, figures or sample associations. Two calls by one model are separate reviews, not a claim of statistically independent errors.'},
 'capacity_gate_after_functional_pilot':{'sustained_elapsed_hours':72,'included_in_this_200_USD_cap':False,'additional_spend_approved':False,
  'purpose':'After functional quality passes, run a separately budgeted sustained test across several cohorts to measure new end-to-end completions including independent negative decisions, retained-paper audits, visuals, corrections and root publication.',
  'daily_scope_target_from_50_processing_day_scenario':189.4,'three_day_scope_target':568.2,'rounded_three_day_scope_target':569,
  'retention_scenarios':plan['retention_scenarios'],
  'acceptance':'Every stage must sustain its retention-adjusted required rate with measured rework headroom. A queue that merely accumulates author outputs while audits or publication lag is a failed capacity test.',
  'current_concurrency':'Desktop session remains four concurrent agents including root. Additional API/cloud workers require a separately provisioned runner, account limits and evidence/audit coordination; cannot silently raise this session to40.',
  'insufficient_result':'If sample size, representative mix or sustained capacity is insufficient, propose a larger pilot or more provisioned review capacity with a new budget. Do not claim the two-month deadline is validated.'},
 'user_help_after_review':['Approve a specific pilot dollar cap later; no payment action is required to read this proposal.','Provide an always-on runner with agreed availability and source-file access if moving to API execution.','Optionally nominate a lab expert to adjudicate chemistry/sample conflicts; expert work is not priced in the token subtotal.'],
 'bound_local_inputs':[{'path':str(cutpath),'sha256':hashlib.sha256(cutraw).hexdigest()},{'path':str(planpath),'sha256':hashlib.sha256(planraw).hexdigest()}],
 'mutations':'Only this private proposal JSON/Markdown and builder; no paid calls, keys, source downloads, shared queue/memory/site/repository changes.'}
J=D/'pilot-budget-model.json';J.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
md='''**MatterSyn pilot budget and capacity proposal — 20 September 2026**

Propose a **$200 API model-spend cap** for **50 representative source scopes independently screened, with up to 20 eligible papers completed through audit and website publication**. This is a proposal, not spending authorization. No paid jobs have been started and no API keys have been accessed.

The accepted collection currently has 9,470 known pending provisional scopes, plus 45 unmapped cutoff files and three nested candidates to reconcile. New papers go into a separate queue. The recorded cutoff is September 20, 2026 UTC and the two-calendar-month project target is November 20 UTC. Scope groups are not yet a verified unique-paper total.

Use a stratified probability sample covering evidence-rich and weak-signal papers, several material families, different main/SI availability, long sources and scanned numerical tables. Save the sample seed and inclusion probabilities. A low-cost first pass proposes a disposition; a separate reviewer checks the original sources for **all 50 decisions, including every proposed no-recipe exclusion**. A classifier score cannot justify skipping a paper.

Take at most 20 eligible papers through complete source extraction, canonical records, independent scientific audit, academic reader pages, molecule/apparatus/product views, website checks and verified publication. If the 50 scopes yield fewer than 20 eligible papers, report the smaller result; do not quietly extend the sample. If there are more than 20, leave the others explicitly pending and select the detailed-review subset by representative complexity rather than speed.

The provisional models are GPT-5.4 Mini for the initial screen and GPT-5.5 for independent triage and retained-paper work. Current standard uncached prices per million tokens are **$0.75 input/$4.50 output** for Mini and **$5 input/$30 output** for GPT-5.5. Model routing must pass the scientific quality evaluation. [GPT-5.4 Mini documentation](https://developers.openai.com/api/docs/models/gpt-5.4-mini), [GPT-5.5 documentation](https://developers.openai.com/api/docs/models/gpt-5.5).

| Pilot stage | Explicit aggregate token assumption | Model-cost subtotal |
|---|---|---:|
| Initial screening, 50 scopes | 30,000 input + 3,000 output per scope, Mini | $1.80 |
| Independent source-based triage, all 50 | 30,000 input + 3,000 output per scope, GPT-5.5 | $12.00 |
| Up to 20 retained papers, base allowance | 200,000 input + 40,000 output **total per paper**, GPT-5.5 | $44.00 |
| **Base model subtotal** | All above | **$57.80** |
| Retained-paper high allowance, replacing the base row | 600,000 input + 120,000 output total per paper | $132.00 |
| **High model subtotal** | Both screening passes + high retained allowance | **$145.80** |
| **Proposed cap and high-case reserve** | $200 cap minus $145.80 | **$54.20 reserve** |

These are assumed envelopes, not measured paper costs. The per-paper allowance includes authoring, a separate auditor's repeated source context, reader/visual binding work, corrections and rechecks. The high allowance is accumulated across separate bounded calls; keep each GPT-5.5 billed prompt/session within the ≤272K input pricing band rather than sending one 600K prompt. [GPT-5.5 pricing condition](https://developers.openai.com/api/docs/models/gpt-5.5).

Count **all billable reasoning in output** and **image-converted tokens in input**, including page crops resent to the independent reviewer. Reconcile estimated tokens against actual usage. Long or scanned papers may exceed these allowances; pause and reforecast rather than reduce legibility, omit pages or weaken the audit. [Reasoning-token accounting](https://developers.openai.com/api/docs/guides/reasoning), [Image-input accounting](https://developers.openai.com/api/docs/guides/images-vision).

The $200 candidate cap covers API model tokens only. It does not include desktop Codex usage, an always-on runner, storage, external OCR or hosted tools, taxes, or expert labor. No prices or subscription credits are assumed for these. Before paid execution, the runner needs a fail-closed budget ledger that reserves worst-case in-flight charges and stops before exceeding the approved cap; an alert alone is not an implemented hard stop. More work requires a new decision.

Batch processing can reduce eligible model charges by 50%, using a 24-hour completion window. If only the two screening waves use Batch, the modeled totals become **$50.90–$138.90**. Dependent author/audit/repair waves can add serial waiting, so the baseline proposal assumes standard calls. Completed requests in an expired batch still incur charges; reconcile output/error IDs before resubmitting unfinished work. [Batch API](https://developers.openai.com/api/docs/guides/batch).

The pilot must measure both quality and capacity:

- Record the independent disposition for every scope; record pages, figures, tables, recipes and sample associations covered, with explicit source gaps.
- Log actual API tokens/costs and author, auditor, visual and correction effort. Separately log root/human integration time, queue delays, runtime availability and actual publication timestamps.
- Publish only exact audited files with no open critical factual, quantity/unit, lineage, structure or visual-association error. Preserve unresolved facts as unresolved.
- Report weighted eligibility, error/rework rate and stage-effort distributions, including failed or unfinished cases. A fast extractor is not a fast pipeline when audits or publication lag.

**Fifty scopes do not validate a production rate of 190 scopes/day.** After the functional pilot passes, propose a separately costed **72-hour sustained throughput test**. It is outside this pilot cap and is not approved yet. At the conservative 50-processing-day schedule, the fixed backlog requires 189.4 closed scopes/day: at 10%, 25%, 50% or 100% recipe retention, approximately 19, 48, 95 or 190 fully audited and published papers/day, respectively, plus the remaining independently checked exclusions. A meaningful three-day test would target about 569 completed dispositions, not merely generated drafts.

The current desktop session has **four agent slots including root**. Raising batch size cannot turn it into 40 workers. Additional API/cloud workers need an always-on runner, account capacity, isolated outputs, distinct review identities and a controlled integration queue. The pilot may show that more capacity—or a larger, more representative pilot—is necessary before supporting the deadline.

What would help after reviewing this proposal: approve a concrete spending cap later; provide an agreed always-on runner if using API workers; optionally nominate a lab expert for disputed chemistry or sample interpretation. No paid execution is part of this preparation step.

The companion `pilot-budget-model.json` contains the calculations, source URLs, exact local input hashes and proposed stop conditions. The current website work can continue independently of this unapproved pilot.
'''
MD=D/'PILOT_PROPOSAL.md';MD.write_text(md,encoding='utf-8')
print(json.dumps({'status':'proposal_saved_no_paid_execution','json':str(J),'json_sha256':hashlib.sha256(J.read_bytes()).hexdigest(),'markdown':str(MD),'markdown_sha256':hashlib.sha256(MD.read_bytes()).hexdigest(),'base_USD':57.8,'high_USD':145.8,'proposed_cap_USD':200,'high_reserve_USD':54.2},indent=2))
