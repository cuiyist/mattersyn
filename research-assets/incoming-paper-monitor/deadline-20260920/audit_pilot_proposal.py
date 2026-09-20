"""Independent local-only pilot proposal quality audit; no author/source mutations."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
from decimal import Decimal
import ast, hashlib, json, math, re

D=Path(__file__).resolve().parent
Q=D.parent
checks=[]; bound={}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):
    p=Path(p).resolve(); bound[str(p)]=sha(p); return p
def load(p): return json.loads(bind(p).read_bytes())
def ck(scope, text, ok, detail=None):
    checks.append(dict(scope=scope,check=text,passed=bool(ok),detail=detail))
def hashcheck(p,h): ck('provenance',str(p),sha(bind(p))==h)
def norm(s):
    s=str(s).strip().lower()
    s=re.sub(r'^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)','',s).strip()
    return s if s.startswith('10.') and '/' in s else None
def samplekeys(c):
    return {('doi',x) for d in c['doi_candidates'] if (x:=norm(d))} | {('main',h.lower()) for h in c['screen_main_hashes']}
def screenkeys(s):
    return {('doi',x) for d in s['doi_candidates'] if (x:=norm(d))} | {('main',h.lower()) for h in s['main_hashes']}
def match(s,st):
    f=s['manual_flags'];r=s['recipe_score'];t=s['structure_score']
    rules={
      'scanned_or_no_usable_text':bool(set(f)&{'no_usable_text_is_not_evidence_of_no_recipe','some_source_pages_have_no_usable_text'}),
      'complex_or_ambiguous_bundle':bool(set(f)&{'embedded_images_or_archive_structure_uninspected','bounded_reader_limit_requires_manual_inspection','main_si_role_ambiguous','main_document_missing_or_unmatched'}),
      'coordinate_and_recipe_signal':s['priority_tier']=='A_recipe_and_coordinate_candidates',
      'recipe_and_structure_signal':r>=10 and t>=8,
      'recipe_signal_other':r>=10 and t<8,
      'structure_with_weak_recipe_signal':r<10 and t>=8,
      'low_signal_no_recipe_candidates':r<=2 and t<=2,
      'si_not_present_in_frozen_group':'si_not_present_in_frozen_candidate_group' in f,
      'deterministic_shortfall_reserve':True}
    return rules[st]

budget=load(D/'pilot-budget-model.json');proposal=bind(D/'PILOT_PROPOSAL.md').read_text(encoding='utf-8')
revision=load(D/'pilot-proposal-revision-2.json');pointer=load(D/'pilot-sample-current.json')
manifest=load(pointer['manifest_path']);sample=load(pointer['sample_path']);v1=load(D/'pilot-sample-candidates.json')
hashcheck(D/'PILOT_PROPOSAL.md','0edd364fe0254326caf1f98bbe775a61fbc87f32b5ddddda09c7b9f0e6c52898')
hashcheck(D/'pilot-budget-model.json','ef252ce129556d5381ec6c061c11b2c228fc3a6ad4b1aeb35f79c5913afc628f')
hashcheck(pointer['manifest_path'],'20f226baf49a065407fc40e93e85ffc9ac268406120f3b0a469d66052fef3faa')
hashcheck(pointer['sample_path'],pointer['sample_sha256']);hashcheck(pointer['manifest_path'],pointer['manifest_sha256'])
for path,h in {**manifest['files'],**manifest['v1_files_unchanged'],**sample['source_provenance']}.items(): hashcheck(path,h)
for row in budget['bound_local_inputs']+budget['revision_provenance']['previous_files']: hashcheck(row['path'],row['sha256'])
for name,h in revision['before'].items(): hashcheck(D/'revisions/v1'/name,h)
for name,h in revision['after'].items(): hashcheck(D/name,h)
bind(D/'pilot-proposal-revision-2.md');bind(D/'revise_pilot_proposal_v2.py');bind(__file__)
oldbudget=load(D/'revisions/v1/pilot-budget-model.json')
for k in ('authorization','pricing','token_envelopes','cost_scenarios','proposed_cap','Batch_option'):
    ck('revision preservation',k+' unchanged from v1',budget[k]==oldbudget[k])

cut=D/sample['cutoff_id'];ledger=load(cut/'ledger-at-cutoff.json');mapping=load(cut/'last-authoritative-group-mapping.json')
current=load(Q/'ledger.json')
screen_path=next(p for p in sample['source_provenance'] if '/reports/' in p.replace('\\','/'))
screen=load(screen_path);byid={s['group_id']:(i,s) for i,s in enumerate(screen['scopes'])}
pending=set(mapping['pending_group_ids']);aliases=set(ledger.get('group_aliases',{}))
excluded={'10.1021_ja048427j','10.1021_ja0496423','10.1021_jp0219348','10.1021_jp0473669','10.1021_la036034c'}
rows=sample['candidates'];ids=[c['group_id'] for c in rows]
ck('selection','Exactly 50 distinct canonical scope IDs',len(rows)==50 and len(set(ids))==50)
ck('selection','All five previous/current batch scopes explicitly excluded',set(sample['already_claimed_group_ids_excluded'])==excluded and not set(ids)&excluded)
ck('selection','Numbers 1–50 retained',sorted(c['candidate_number'] for c in rows)==list(range(1,51)))
owners={};all_dois=[];all_main=[]
for c in rows:
    gid=c['group_id'];g=ledger['groups'][gid];now=current['groups'].get(gid);i,s=byid[gid]
    ck(gid,'Pending in immutable cutoff, nonalias, excluded-five absent',gid in pending and gid not in aliases and gid not in excluded and g['review']['status']=='queued')
    ck(gid,'Screened current cutoff generation and priority-applicable',g['generation']==c['source_generation_at_cutoff']==s['source_generation'] and s['priority_applicable'])
    ck(gid,'Still queued, same generation and files in read-only current ledger',now is not None and now['review']['status']=='queued' and now['generation']==g['generation'] and now['files']==g['files'])
    ck(gid,'Original queue metadata retained',c['queue_order_at_cutoff']==g['queue_order'] and c['review_status_at_cutoff']==g['review']['status'])
    ck(gid,'Source hashes and DOI candidates exactly bound screen scope',c['screen_source_hashes']==s['source_hashes'] and c['screen_main_hashes']==s['main_hashes'] and c['doi_candidates']==s['doi_candidates'])
    ck(gid,'Exact screen pointer and hash',c['evidence_provenance']['screen_scope_index']==i and c['evidence_provenance']['screen_json_pointer']==f'/scopes/{i}' and c['evidence_provenance']['source_report_sha256']==sha(screen_path))
    ck(gid,'Descriptive stratum membership matches text signals only',match(s,c['assigned_stratum']) and c['stratum_is_sampling_design_not_scientific_label'] is True)
    expected=[dict(file_key=k,role_at_cutoff=ledger['files'][k].get('role'),source_id=ledger['files'][k].get('source_id'),relative_filename=ledger['files'][k].get('relative_filename'),size_bytes=ledger['files'][k].get('size')) for k in g['files'] if k in ledger['files'] and ledger['files'][k].get('exists')]
    ck(gid,'Candidate file membership and cutoff metadata exact',c['source_bundle_candidate_files']==expected)
    ck(gid,'No recipe/nonrecipe or retained scientific disposition assigned',c['recipe_present'] is None and c['no_recipe_confirmed'] is False and c['end_to_end_retained'] is False and c['actual_pilot_review_status']=='not_started' and c['paid_api_calls']==0)
    ck(gid,'Main/SI pairing remains unverified',c['main_si_pairing_status']=='provisional_requires_actual_identity_and_content_check')
    ks=samplekeys(c)
    ck(gid,'Has valid available sampling keys; absent main explicitly flagged',bool(c['doi_candidates']) and all(re.fullmatch('[0-9a-f]{64}',h) for h in c['screen_main_hashes']) and (bool(c['screen_main_hashes']) or 'main_document_missing_or_unmatched' in c['screen_signals']['manual_flags']))
    overlap=ks&owners.keys();ck(gid,'No reused normalized DOI or main-content key',not overlap,sorted(overlap))
    for k in ks:owners[k]=gid
    all_dois += [v for k,v in ks if k=='doi'];all_main += [v for k,v in ks if k=='main']

unchanged=[c['candidate_number'] for c,o in zip(rows,v1['candidates']) if c==o]
changed=[c['candidate_number'] for c,o in zip(rows,v1['candidates']) if c!=o]
ck('v2 correction','49 exact candidate objects unchanged and only candidate 9 replaced',len(unchanged)==49 and unchanged==sample['unchanged_candidate_numbers'] and changed==[9])
ck('v2 correction','All eight stratum counts unchanged',Counter(c['assigned_stratum'] for c in rows)==Counter(c['assigned_stratum'] for c in v1['candidates']))
ck('v2 correction','Actual v1 candidate 7/9 overlap agrees correction',samplekeys(v1['candidates'][6])&samplekeys(v1['candidates'][8])=={('doi','10.1021/acs.inorgchem.7b01711'),('main','4b2a67c728c3594486f5080a645e3fffc67a39130c36234b7f1a35b706b8ef55')})
others=[c for c in rows if c['candidate_number']!=9];used=set().union(*(samplekeys(c) for c in others));usedids={c['group_id'] for c in others}
choices=[]
for gid,(i,s) in byid.items():
    g=ledger['groups'].get(gid)
    if not g or gid not in pending or gid in aliases|excluded|usedids:continue
    if g['generation']!=s['source_generation'] or not s['priority_applicable'] or not match(s,'coordinate_and_recipe_signal') or screenkeys(s)&used:continue
    choices.append((hashlib.sha256((sample['seed']+'\0coordinate_and_recipe_signal\0'+gid).encode()).hexdigest(),gid))
ck('v2 correction','Same-stratum deterministic replacement independently reproduced',min(choices)[1]==rows[8]['group_id']=='10.1021_ja103805s' and len(choices)==sample['corrections'][0]['replacement_pool_size']==1)
pool=[gid for gid,(i,s) in byid.items() if gid in ledger['groups'] and gid in pending and gid not in aliases|excluded and s['source_generation']==ledger['groups'][gid]['generation'] and s['priority_applicable']]
ck('selection','Screen-covered eligible pool independently counted',len(pool)==sample['eligible_screened_pool_size']==9164)
src=bind(D/'select_pilot_candidates_v2.py').read_text(encoding='utf-8');ast.parse(src)
ck('selector static scope','Selector references frozen ledger, writes versioned proposals only, no network clients','ledger-at-cutoff.json' in src and "'ledger.json'" not in src and not re.search(r'\b(?:requests|urllib|httpx|openai|subprocess)\b',src))
ck('selector static scope','Existing v1 and v2 bytes protected',"Frozen v2 output differs; create a new version." in src and 'for p,h in oldhashes.items():assert sha(p)==h' in src)

ck('scientific scope','No predetermined recipe prevalence or end-to-end IDs',sample['recipe_bearing_fraction'] is None and sample['retained_end_to_end_cap']==20 and sample['retained_end_to_end_group_ids']==[])
ck('statistical scope','No inclusion probabilities or weighted/corpus prevalence support',sample['inclusion_probabilities'] is None and sample['weighted_corpus_prevalence_supported'] is False and sample['corpus_recipe_prevalence_estimation_supported'] is False and sample['corpus_eta_requires_separate_representative_prevalence_assessment'] is True)
ck('statistical scope','Proposal expressly limits retention to this pilot','not a probability sample' in proposal and 'Do not estimate whole-corpus recipe prevalence' in proposal and "no corpus retention/prevalence estimate" in budget['measurement_plan']['outputs'][3])
ck('pilot quality','All 50 dispositions independently checked; uncertain scopes not excluded',budget['pilot_scope']['independent_triage_scopes']==50 and budget['pilot_scope']['all_no_recipe_decisions_audited'] is True and 'Uncertain scopes remain unresolved' in budget['pilot_scope']['negative_decision_rule'])
ck('pilot cap','At most 20, shortfall reported without silent extension',budget['pilot_scope']['retained_end_to_end_maximum']==20 and 'do not silently extend the sample' in budget['pilot_scope']['if_fewer_than_20_retained'])
prices=budget['pricing']['models']
def cost(n,inp,out,model):
    p=prices[model];return Decimal(n)*(Decimal(inp)*Decimal(str(p['input_per_million_USD']))+Decimal(out)*Decimal(str(p['output_per_million_USD'])))/Decimal(1000000)
screen_cost=cost(50,30000,3000,'gpt-5.4-mini');triage=cost(50,30000,3000,'gpt-5.5')
ck('budget arithmetic','50 first-pass scopes cost $1.80 under stated rates',screen_cost==Decimal('1.80'))
ck('budget arithmetic','50 independent triages cost $12.00 under stated rates',triage==Decimal('12.00'))
allocation=budget['token_envelopes']['retained_base_stage_allocation_assumed']
ck('budget arithmetic','Stage allowances sum to 200K input and 40K output',sum(x['input'] for x in allocation)==200000 and sum(x['output'] for x in allocation)==40000)
for sc in budget['cost_scenarios']:
    retained=cost(sc['retained_count_budgeted'],sc['input_tokens_per_retained_aggregate'],sc['output_tokens_per_retained_aggregate_including_reasoning'],'gpt-5.5');total=retained+screen_cost+triage
    for key,value in [('retained_subtotal_USD',retained),('standard_uncached_model_subtotal_USD',total),('reserve_to_proposed_200_USD_cap',Decimal(200)-total),('if_only_both_triage_passes_use_eligible_Batch_USD',retained+(screen_cost+triage)/2),('all_eligible_Batch_arithmetic_only_USD',total/2)]:
        ck('budget arithmetic',sc['name']+' '+key,Decimal(str(sc[key]))==value)
ck('budget arithmetic','$200 minus $145.80 equals $54.20',budget['proposed_cap']['API_model_spend_hard_cap_USD']==200 and Decimal('200')-Decimal('145.80')==Decimal(str(budget['proposed_cap']['unallocated_reserve_USD'])))
ck('budget limits','Reasoning/image token accounting and pre-execution hard stop explicit','all billable reasoning in output' in proposal and 'image-converted tokens in input' in proposal and 'not an implemented hard stop' in proposal and '600K prompt' in proposal)
cap=budget['capacity_gate_after_functional_pilot']
ck('capacity phase','72 hours separately budgeted and unapproved',cap['sustained_elapsed_hours']==72 and cap['included_in_this_200_USD_cap'] is False and cap['additional_spend_approved'] is False)
ck('capacity arithmetic','9470/50 × 3 =568.2; ceiling569',Decimal(9470)/50==Decimal(str(cap['daily_scope_target_from_50_processing_day_scenario'])) and Decimal(9470)/50*3==Decimal(str(cap['three_day_scope_target'])) and math.ceil(cap['three_day_scope_target'])==cap['rounded_three_day_scope_target']==569)
ck('capacity scope','Assumed retention scenarios are explicitly scenarios, not observations',all('assumed_retained_fraction' in r for r in cap['retention_scenarios']) and 'Fifty scopes do not validate' in proposal)
for r in cap['retention_scenarios']:
    n=math.ceil(Decimal(9470)*Decimal(str(r['assumed_retained_fraction'])))
    ck('capacity arithmetic',str(r['assumed_retained_fraction'])+' retention scenario',n==r['retained_papers_or_scopes_ceiling'] and 9470-n==r['excluded_after_checked_screening'] and Decimal(n)/50==Decimal(str(r['retained_complete_and_published_per_processing_day'])))
auth=budget['authorization']
ck('authorization','Preparation only; no paid jobs, keys or spending authorized',auth['paid_execution_approved'] is False and auth['paid_jobs_submitted']==0 and auth['keys_read_or_requested'] is False and auth['API_spend_by_this_task_USD']==0 and sample['no_paid_calls_or_jobs_started'] is True)
ck('infrastructure scope','Storage and runner costs outside API proposal; availability not assumed',budget['website_capacity']['infrastructure_in_200_USD_API_cap'] is False and 'always-on runner' in proposal and 'no provider' in proposal)

missing_main=[{'candidate_number':c['candidate_number'],'group_id':c['group_id'],'files':c['source_bundle_candidate_files'],'manual_flags':c['screen_signals']['manual_flags']} for c in rows if not c['screen_main_hashes']]
ck('unresolved source coverage','Five SI-only candidates explicitly held for main identity review',len(missing_main)==5 and [c['candidate_number'] for c in missing_main]==[4,6,39,40,44] and all(all(f['role_at_cutoff']=='si' for f in c['files']) for c in missing_main))
for p in (D/'pilot-audit-checker-draft-1.json',D/'pilot-audit-checker-draft-1.md'):bind(p)
fail=[x for x in checks if not x['passed']]
report={'schema':'mattersyn-pilot-proposal-independent-audit/1','at':datetime.now(timezone.utc).isoformat(),'authors':['/root','/root/norberg2004_extract'],'auditor':'/root/backlog_eta','reviewer':'/root/backlog_eta','status':'passed' if not fail else 'findings_require_resolution','scope':'Local proposal quality, immutable candidate selection, budget arithmetic and no-paid-execution contract. Not an independent scientific paper review, spending approval or production-capacity validation.','counts':{'checks':len(checks),'failed':len(fail),'sample_scopes':50,'unique_normalized_doi_keys':len(set(all_dois)),'unique_main_hash_keys':len(set(all_main)),'unchanged_v1_candidates':49,'replaced_candidates':1,'retained_selected':0,'retained_cap':20},'findings':fail,'checks':checks,'bound_files':bound,'confirmed_scope':['All 50 candidates are queued at cutoff and in the current read-only ledger snapshot, with unchanged group generation/file membership; all five earlier batch scopes are excluded.','Sampling DOI/main-hash keys are distinct, but remain candidate identifiers, not verified unique experiments or verified main/SI matches.','No recipe/nonrecipe prevalence or retention count has been decided. Descriptive strata support QA/calibration only.','All fixed-model subtotal and reserve arithmetic was recomputed from the proposal’s stated rates; rates/model access were not queried or independently reverified in this local audit.','The 72-hour, approximately 569-disposition test is separately costed in the future and outside the unapproved $200 API model-token cap.'],'limits':['No paper originals were newly read or hashed; exact raw-source readiness and matching are execution gates.','No API key, network/API job, browser, paid request, source mutation or ledger mutation was performed.','This audit does not guarantee pricing availability, hard-cap enforcement or continuous worker capacity; those require verification/implementation before paid execution.'],'mutations':'Only this private audit script and its JSON/Markdown outputs.'}
report['unresolved_source_coverage']={'missing_main_candidates':missing_main,'meaning':'Five SI-only candidate bundles have no classified main hash. They remain unresolved QA candidates and cannot support no-recipe exclusion or full-paper completion until the relevant source evidence is sufficient.'}
report['checker_revision_note']='Draft 1 incorrectly required a main-document hash for every QA candidate. The sample explicitly includes missing-main bundles. The corrected check verifies a usable DOI key and explicit missing-main flag, retaining five unresolved scopes; no author scientific data or candidate selection changed. Draft reports are preserved.'
(D/'pilot-proposal-independent-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
md=f'''# Pilot proposal independent audit

**{report['status']}** — {len(checks):,} checks; {len(fail)} unresolved findings. Authors: `/root` and `/root/norberg2004_extract`; independent reviewer: `/root/backlog_eta`.

All 50 candidate scopes are pending in the immutable cutoff and still queued with unchanged generation/file membership in the current ledger snapshot. All five prior/current batch scopes are excluded. There are {len(set(all_dois))} distinct normalized DOI keys and {len(set(all_main))} distinct main-content hashes. Version 2 preserves 49 candidate objects exactly and replaces candidate 9 within the same stratum; the deterministic replacement was independently reproduced. Original v1 sample/proposal files remain byte-exact.

The selection is deliberately diverse QA/calibration, with descriptive strata and no inclusion probabilities. It cannot establish whole-corpus recipe prevalence or extrapolate a corpus ETA. Main/SI matching and actual source review remain pending. Candidates **4, 6, 39, 40 and 44** are SI-only DOCX bundles with an explicit missing/unmatched-main flag: these are unresolved QA cases, not source-ready complete papers, and cannot support a no-recipe exclusion from missing evidence. No candidate is confirmed recipe-bearing or no-recipe; zero retained IDs are selected, with a maximum of 20 after review.

The stated rate/token assumptions recompute to **$57.80 base**, **$145.80 high**, and **$54.20 reserve** under the proposed **$200 API model-token cap**. Rates/model account availability were not independently queried in this local audit. The cap is unapproved and unenforced pending an actual budget guard; paid jobs and API-key access have not been initiated by this preparation. The separately proposed **72-hour test targets approximately 569 completed dispositions** and is outside the $200 cap, also unapproved. Neither the 50-scope pilot nor scenario arithmetic proves the two-month deadline.

This is proposal quality review, not paper scientific approval or permission to execute paid work. Exact source/proposal/selector/current-ledger hashes are in the JSON report. No source, ledger, Site or external service was changed. A preliminary checker incorrectly required main hashes for every QA candidate; its reports are retained, and the final check preserves the five explicitly unresolved bundles.
'''
for f in fail:md+='\nRequired: '+f['scope']+' — '+f['check']+'\n'
(D/'pilot-proposal-independent-audit.md').write_text(md,encoding='utf-8')
print(json.dumps({'status':report['status'],'checks':len(checks),'findings':fail,'audit_sha256':sha(D/'pilot-proposal-independent-audit.json'),'markdown_sha256':sha(D/'pilot-proposal-independent-audit.md'),'unique_doi':len(set(all_dois)),'unique_main_hashes':len(set(all_main))}))
