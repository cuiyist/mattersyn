"""Bounded author revision: actual diverse sample and website capacity metric."""
from pathlib import Path
from datetime import datetime, timezone
from copy import deepcopy
from decimal import Decimal
import json,hashlib
D=Path(__file__).resolve().parent
OLD={'PILOT_PROPOSAL.md':'9ccc15b7d7621795771fca5316d9313a0128153697ee7bd50faa5f19b8c3373c',
     'pilot-budget-model.json':'8bc2230d6f5c7e8ab121a59dd8138c488b8f88c9ddca33027bf982cea756c42b'}
R=D/'revisions/v1';R.mkdir(parents=True,exist_ok=True)
for name,expected in OLD.items():
 p=D/name;raw=p.read_bytes()
 assert hashlib.sha256(raw).hexdigest()==expected,(name,'unexpected author boundary')
 archive=R/name
 if archive.exists():assert archive.read_bytes()==raw
 else:archive.write_bytes(raw)
before=json.loads((R/'pilot-budget-model.json').read_text(encoding='utf-8'))
after=deepcopy(before)
at=datetime.now(timezone.utc).isoformat()
after['proposal_revision']=2
after['revised_at']=at
after['purpose']='Measure pilot-source eligibility, cost, scientific error/rework and end-to-end capacity before promising the fixed-collection deadline. This deliberately diverse pilot does not estimate corpus recipe prevalence.'
p=after['pilot_scope'];p['deliberately_diverse_sampled_scopes']=p.pop('representatively_selected_scopes')
p['source_sampling']='Deliberately diverse round-robin QA/calibration sample from the frozen collection, covering evidence tiers, families, main/SI availability, length, scanned sources and table density. Strata describe coverage only; no inclusion probabilities were assigned. This is not a probability sample and cannot support corpus recipe-prevalence estimation.'
p['corpus_prevalence_rule']='Use a separately designed probability sample with known inclusion probabilities, or complete audited screening, before estimating whole-corpus retention or using it to extrapolate the total workload. Report this pilot\'s eligibility counts as within-sample descriptive results only.'
p['candidate_sample_version']='v2; normalized-DOI duplicates excluded by the separate candidate-selection author; candidate source/audit readiness must be checked before paid execution.'
p['candidate_sample_files']=['pilot-sample-candidates-v2.json','pilot-sample-candidates-v2.md']
after['measurement_plan']['per_scope'][1]='descriptive selection stratum and selection order; no probability weight or population inference'
after['measurement_plan']['per_scope'].append('incremental published asset bytes and deduplicated storage growth per retained paper; shared-asset reuse recorded separately')
after['measurement_plan']['outputs'][3]='eligibility counts within the deliberately diverse pilot only; no corpus retention/prevalence estimate'
after['capacity_gate_after_functional_pilot']['insufficient_result']='If sample size, diversity coverage or sustained capacity is insufficient, propose a larger pilot or more provisioned review capacity with a new budget. Use a separate probability sample or complete audited screening before estimating corpus prevalence. Do not claim the deadline is validated.'
url='https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits'
after['website_capacity']={
 'root_reported_current_clean_site_bytes':205026368,'measurement_origin':'Root supplied clean-site measurement on2026-09-20; not independently remeasured by this bounded proposal revision.',
 'published_site_size_limit_GB':1,'soft_builds_per_hour':10,
 'build_limit_exception':'The soft10-build/hour limit does not apply to a custom GitHub Actions build-and-publish workflow; verify the actual deployment mode.',
 'official_source':url,'official_source_checked_UTC':'2026-09-20',
 'pilot_metric':'Measure incremental public assets/storage per completed paper after deduplication, build time and root publication effort; separate shared assets from new per-paper assets.',
 'no_linear_extrapolation':'Do not divide the205026368-byte baseline by31 sources or assume linear growth; shared assets and source complexity make that misleading.',
 'planning_action':'Batch approved publications. If measured growth approaches the host limit, prepare a separately priced external-asset/storage or hosting proposal. No provider selected, migration performed or charge authorized.',
 'infrastructure_in_200_USD_API_cap':False}
after['revision_provenance']={'previous_files':[{'path':str(R/name),'sha256':sha}for name,sha in OLD.items()],
 'reason':'Root identified that the concrete sample is deliberately diverse round-robin without inclusion probabilities; probability-sampling/weighted-prevalence claims were incorrect. Root also requested a bounded website asset-growth metric.',
 'budget_changed':False,'paid_execution_authorized':False,'sustained_72h_test_budget_approved':False}

md=(R/'PILOT_PROPOSAL.md').read_text(encoding='utf-8')
replacements={
 '50 representative source scopes independently screened':'50 deliberately diverse QA/calibration scopes independently screened',
 'Use a stratified probability sample covering evidence-rich and weak-signal papers, several material families, different main/SI availability, long sources and scanned numerical tables. Save the sample seed and inclusion probabilities.':'Use the deliberately diverse round-robin QA/calibration selection documented in the [v2 candidate table](pilot-sample-candidates-v2.md) and [v2 candidate manifest](pilot-sample-candidates-v2.json). Version 2 excludes normalized-DOI duplicates; its readiness is checked separately before execution. It covers evidence-rich and weak-signal papers, material families, main/SI availability, long sources and scanned tables. **Strata are descriptive only: no inclusion probabilities were assigned, so this is not a probability sample.**',
 'select the detailed-review subset by representative complexity rather than speed.':'select the detailed-review subset to cover different complexities rather than speed.',
 '- Report weighted eligibility, error/rework rate and stage-effort distributions, including failed or unfinished cases. A fast extractor is not a fast pipeline when audits or publication lag.':'- Report eligibility counts **within this selected pilot only**, error/rework rates and stage-effort distributions, including failed or unfinished cases. **Do not estimate whole-corpus recipe prevalence or use this pilot\'s retained fraction to extrapolate the backlog.** That requires a separately designed probability sample with known inclusion probabilities, or complete audited screening. A fast extractor is not a fast pipeline when audits or publication lag.',
 'or a larger, more representative pilot':'or a larger pilot covering missing source types'
}
for old,new in replacements.items():
 assert old in md,old
 md=md.replace(old,new)
website='''\nMeasure **incremental published asset/storage growth per completed paper**, together with build and root publication time. The current clean-site baseline supplied by root is **205,026,368 bytes**; shared assets make dividing that total by the source count misleading. GitHub Pages limits published sites to **1 GB** and normally has a soft **10 builds/hour** limit, with an exception for custom GitHub Actions build-and-publish workflows. Batch approved releases and verify the actual deployment mode. If measured growth requires external asset storage or different hosting, prepare a separate infrastructure budget; no provider, migration or charge is selected now, and infrastructure is outside the $200 API cap. [GitHub Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits).\n'''
needle='\nThe current desktop session has **four agent slots including root**.'
assert needle in md
md=md.replace(needle,website+needle)
md+='\nRevision 2 corrects the sample-design description and adds the website-capacity metric. Version 1 is preserved under `revisions/v1/`; the $57.80 base, $145.80 high allowance and proposed $200 API cap are unchanged. Approving this functional pilot would not approve the separately budgeted 72-hour load test.\n'
assert after['pricing']==before['pricing']
assert after['token_envelopes']==before['token_envelopes']
assert after['cost_scenarios']==before['cost_scenarios']
assert after['proposed_cap']==before['proposed_cap']
assert after['authorization']==before['authorization']
assert after['capacity_gate_after_functional_pilot']['additional_spend_approved'] is False
assert after['capacity_gate_after_functional_pilot']['included_in_this_200_USD_cap'] is False
for x in after['cost_scenarios']:
 assert Decimal(str(x['standard_uncached_model_subtotal_USD']))+Decimal(str(x['reserve_to_proposed_200_USD_cap']))==200

changes=[]
def delta(a,b,ptr=''):
 if isinstance(a,dict)and isinstance(b,dict):
  for k in sorted(set(a)|set(b)):
   p=ptr+'/'+str(k)
   if k not in a:changes.append({'pointer':p,'operation':'add','new':b[k]})
   elif k not in b:changes.append({'pointer':p,'operation':'remove','old':a[k]})
   else:delta(a[k],b[k],p)
 elif isinstance(a,list)and isinstance(b,list):
  for i in range(max(len(a),len(b))):
   p=ptr+'/'+str(i)
   if i>=len(a):changes.append({'pointer':p,'operation':'add','new':b[i]})
   elif i>=len(b):changes.append({'pointer':p,'operation':'remove','old':a[i]})
   else:delta(a[i],b[i],p)
 elif a!=b:changes.append({'pointer':ptr,'operation':'replace','old':a,'new':b})
delta(before,after)
(D/'pilot-budget-model.json').write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(D/'PILOT_PROPOSAL.md').write_text(md,encoding='utf-8')
record={'schema':'mattersyn-pilot-proposal-author-revision/1','revision':2,'at':at,
 'author':'/root/norberg2004_extract','reason':after['revision_provenance']['reason'],
 'before':OLD,'after':{name:hashlib.sha256((D/name).read_bytes()).hexdigest()for name in OLD},
 'json_field_changes':changes,'markdown_replacements':[{'old':a,'new':b}for a,b in replacements.items()],
 'markdown_additions':['Website capacity paragraph','Revision2 scope/budget note'],
 'validation':{'budget_rates_envelopes_subtotals_cap_unchanged':True,'authorization_unchanged':True,'72h_load_test_unapproved_and_separate':True,'v1_originals_preserved_byte_exact':True,'no_paid_execution':True},
 'candidate_v2_files_present_at_revision':{name:(D/name).exists()for name in p['candidate_sample_files']}}
(D/'pilot-proposal-revision-2.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(D/'pilot-proposal-revision-2.md').write_text('''Revision2 author note

The concrete50-scope candidate set is deliberately diverse round-robin, not a probability sample. Its strata describe coverage only. Removed representative/probability-sampling/weighted-prevalence claims; pilot eligibility counts cannot estimate corpus retention. A separate probability sample or complete audited screening is required for population extrapolation. The proposal links the separately authored, normalized-DOI-deduplicated v2 candidates.

Added root's clean-site baseline and a metric for incremental assets/storage, with official GitHub Pages limits and the custom-Actions build-limit exception. No provider, migration or infrastructure spend selected.

Original two files are preserved byte-for-byte in revisions/v1/. API prices, token envelopes, $57.80/$145.80 totals, proposed$200cap and paid-execution=false are unchanged. The72-hour load test is separately budgeted and remains unapproved. Exact old/new hashes and field changes are in pilot-proposal-revision-2.json. No other expanded work performed.
''',encoding='utf-8')
print(json.dumps({'status':'revision2_saved','after':record['after'],'json_field_change_count':len(changes),'candidate_v2_files_present':record['candidate_v2_files_present_at_revision'],'delta_sha256':hashlib.sha256((D/'pilot-proposal-revision-2.json').read_bytes()).hexdigest()},indent=2))
