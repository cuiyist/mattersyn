"""Deterministic, read-only-source selection of 50 provisional API-pilot scopes.

This does not open papers, claim work, classify confirmed recipes, or call an API.
Existing outputs may only be reproduced byte-for-byte; revisions need a new file.
"""
from pathlib import Path
import json, hashlib, re, collections

D=Path(__file__).resolve().parent
C=D/'cutoff-20260920T033439542641Z'
SCREEN=D.parent/'corpus-screening/20260919/reports/d5d9e7efb9dabecd2f46e6d6bfde6be650f0b58de30864c2d44485b16e819d0f.json'
SEED='mattersyn-api-pilot-50-deadline-20260920-v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def stable(x):return hashlib.sha256((SEED+'\0'+x).encode()).hexdigest()
def freeze(p,raw):
    if p.exists():assert p.read_bytes()==raw,'Immutable output differs; use a new version instead of overwriting.'
    else:p.write_bytes(raw)

def main():
    ledger_path=C/'ledger-at-cutoff.json';mapping_path=C/'last-authoritative-group-mapping.json'
    assert sha(SCREEN)==SCREEN.stem
    assert sha(ledger_path)=='c2385936db180fd856ba521572fb2e75c852ba118d2c40325c4a438bbfcd74ca'
    assert sha(mapping_path)=='691f1cc9762f399977495715d60497fcd4d8c479219ac853afb4c1b2019b1747'
    ledger=load(ledger_path);mapping=load(mapping_path);screen=load(SCREEN)
    pending=set(mapping['pending_group_ids']);aliases=set(ledger.get('group_aliases',{}))
    active={p['group_id'] for p in (ledger.get('current_batch') or {}).get('papers',[])}
    if isinstance(ledger.get('current_paper'),dict):active.add(ledger['current_paper'].get('group_id'))
    active.add('10.1021_jp0219348')
    excluded=collections.Counter();pool=[]
    for s in screen['scopes']:
        gid=s['group_id'];g=ledger['groups'].get(gid)
        if not g or gid not in pending:excluded['closed_or_not_pending_in_immutable_cutoff']+=1;continue
        if gid in aliases:excluded['alias']+=1;continue
        if gid in active:excluded['already_claimed_or_current_heo']+=1;continue
        if s['source_generation']!=g['generation']:excluded['screen_generation_does_not_match_cutoff']+=1;continue
        if not s.get('priority_applicable'):excluded['screen_not_applicable']+=1;continue
        files=[dict(file_key=k,role_at_cutoff=ledger['files'][k].get('role'),source_id=ledger['files'][k].get('source_id'),relative_filename=ledger['files'][k].get('relative_filename'),size_bytes=ledger['files'][k].get('size')) for k in g['files'] if k in ledger['files'] and ledger['files'][k].get('exists')]
        flags=s['manual_flags'];fc=s['feature_counts']
        # These are literal source-text mentions only, never a product/family assignment.
        mentions={}
        for sn in s.get('candidate_snippets',[]):
            for token in re.findall(r'(?<![A-Za-z0-9])(?:CdSe|CdS|CdTe|PbSe|PbS|ZnO|ZnS|TiO2|SnO2|SiO2|Fe3O4|FePt|CoFe2O4|perovskite|zeolite|silicon)(?![A-Za-z0-9])',sn.get('text',''),re.I):
                mentions.setdefault(token,{'source_sha256':sn.get('source_sha256'),'page':sn.get('page'),'line_start_in_text_block':sn.get('line_start_in_text_block'),'line_end_in_text_block':sn.get('line_end_in_text_block'),'status':'literal_unreviewed_mention_may_be_precursor_reference_or_product'})
        family=g.get('material_family') or g.get('verified_material_family')
        pool.append({'s':s,'g':g,'files':files,'flags':flags,'mentions':mentions,'family':family,'balance_bucket':str(family) if family else ('mention:'+sorted(mentions,key=str.lower)[0].lower() if mentions else 'unknown')})
    used=set();selected=[];strata=[]
    def take(name,target,predicate,description):
        eligible=[x for x in pool if x['s']['group_id'] not in used and predicate(x)]
        buckets=collections.defaultdict(list)
        for x in eligible:buckets[x['balance_bucket']].append(x)
        for xs in buckets.values():xs.sort(key=lambda x:stable(name+'\0'+x['s']['group_id']))
        order=sorted(buckets,key=lambda k:stable(name+'\0bucket\0'+k));chosen=[]
        while len(chosen)<target and any(buckets.values()):
            for b in order:
                if buckets[b] and len(chosen)<target:chosen.append(buckets[b].pop(0))
        for x in chosen:used.add(x['s']['group_id']);selected.append((name,x))
        strata.append({'stratum':name,'requested':target,'selected':len(chosen),'available_after_previous_strata':len(eligible),'definition':description})
    take('scanned_or_no_usable_text',3,lambda x:any(f in x['flags'] for f in ['no_usable_text_is_not_evidence_of_no_recipe','some_source_pages_have_no_usable_text']), 'Machine-screen flags indicate missing usable page text; scanned status and recipe presence require inspection.')
    take('complex_or_ambiguous_bundle',3,lambda x:any(f in x['flags'] for f in ['embedded_images_or_archive_structure_uninspected','bounded_reader_limit_requires_manual_inspection','main_si_role_ambiguous','main_document_missing_or_unmatched']), 'Archive/image/reader-limit or main/SI ambiguity flags; no pairing is assumed.')
    take('coordinate_and_recipe_signal',4,lambda x:x['s']['priority_tier']=='A_recipe_and_coordinate_candidates','Joint recipe and coordinate text signals; target-product and sample-coordinate linkage unverified.')
    take('recipe_and_structure_signal',12,lambda x:x['s']['recipe_score']>=10 and x['s']['structure_score']>=8,'High procedural and structural text signals; not verified recipes or structures.')
    take('recipe_signal_other',10,lambda x:x['s']['recipe_score']>=10 and x['s']['structure_score']<8,'Procedural text signals with weaker structure signal; actual recipe completeness unknown.')
    take('structure_with_weak_recipe_signal',6,lambda x:x['s']['structure_score']>=8 and x['s']['recipe_score']<10,'Structure signals with weak procedural evidence; may prove to contain no usable synthesis recipe.')
    take('low_signal_no_recipe_candidates',8,lambda x:x['s']['recipe_score']<=2 and x['s']['structure_score']<=2,'Low-signal candidates deliberately retained to measure no-recipe decisions and false negatives. None is pre-labeled no-recipe.')
    take('si_not_present_in_frozen_group',4,lambda x:'si_not_present_in_frozen_candidate_group' in x['flags'],'SI is absent from the frozen candidate grouping; this is not proof that the paper has no SI.')
    if len(selected)<50:take('deterministic_shortfall_reserve',50-len(selected),lambda x:True,'Deterministic fill only if a requested stratum lacks candidates; actual counts retain the shortfall.')
    assert len(selected)==50 and len(used)==50 and not used&active
    candidates=[]
    for n,(stratum,x) in enumerate(selected,1):
        s=x['s'];g=x['g'];gid=s['group_id']
        candidates.append({'candidate_number':n,'group_id':gid,'doi_candidates':s['doi_candidates'],'source_generation_at_cutoff':g['generation'],'queue_order_at_cutoff':g['queue_order'],'review_status_at_cutoff':g['review'].get('status'),'assigned_stratum':stratum,'stratum_is_sampling_design_not_scientific_label':True,'recipe_present':None,'no_recipe_confirmed':False,'material_family':x['family'],'material_family_status':'existing_explicit_ledger_metadata_unverified_for_pilot' if x['family'] else 'unknown_no_family_inferred','unverified_literal_material_mentions':x['mentions'],'diversity_bucket':x['balance_bucket'],'screen_signals':{'recipe_score':s['recipe_score'],'structure_score':s['structure_score'],'combined_score':s['score'],'priority_tier':s['priority_tier'],'feature_counts':s['feature_counts'],'manual_flags':s['manual_flags']},'source_bundle_candidate_files':x['files'],'screen_source_hashes':s['source_hashes'],'screen_main_hashes':s['main_hashes'],'main_si_pairing_status':'provisional_requires_actual_identity_and_content_check','actual_pilot_review_status':'not_started','paid_api_calls':0,'end_to_end_retained':False,'evidence_provenance':{'screen_scope_index':next(i for i,z in enumerate(screen['scopes']) if z['group_id']==gid),'screen_json_pointer':'/scopes/'+str(next(i for i,z in enumerate(screen['scopes']) if z['group_id']==gid)),'source_report_sha256':SCREEN.stem},'required_first_steps':['Verify current source bytes/generation against frozen cutoff and detect any new evidence.','Verify main/SI identity by title, authors and content; filename grouping is provisional.','Read actual synthesis/experimental content before a retained or no-recipe decision.']})
    result={'schema':'mattersyn-provisional-api-pilot-sample/1','version':1,'status':'frozen_candidate_sample_pending_identity_matching_and_actual_review','seed':SEED,'determinism':'SHA256(seed + stratum + group ID), round-robin over explicit ledger family where present or clearly labeled literal-mention diversity buckets; source scientific family is never inferred.','cutoff_id':C.name,'cutoff_at':'2026-09-20T03:34:39.542641+00:00','target_at_utc':'2026-11-20T03:34:39.542641+00:00','sample_size':50,'eligible_screened_pool_size':len(pool),'selection_exclusion_counts':dict(excluded),'already_claimed_group_ids_excluded':sorted(x for x in active if x),'strata':strata,'recipe_bearing_fraction':None,'recipe_bearing_fraction_status':'unknown_to_be_measured_by_actual_pilot_review','retained_end_to_end_cap':20,'retained_end_to_end_group_ids':[],'retention_rule':'Select up to20 synthesis-bearing scopes after actual matching/review, balancing the observed retained families and difficulties. Retention is not predetermined by scores; all50 contribute to screening and no-recipe-decision assessment.','no_paid_calls_or_jobs_started':True,'scientific_extraction_performed_by_selection':False,'source_files_or_ledger_modified':False,'source_provenance':{str(p):sha(p) for p in [ledger_path,mapping_path,C/'cutoff-snapshot-manifest.json',SCREEN]},'selector_sha256':sha(__file__),'candidates':candidates,'limitations':['This is a deliberately stratified evaluation sample, not an unbiased prevalence survey of the corpus. Report stratum-specific findings; do not infer corpus recipe prevalence from an unweighted retained fraction.','Literal material mentions are source text signals only and may identify a precursor, background reference or product. Unknown material families remain null.','No-recipe candidates are not confirmed no-recipe sources; absence of usable text is especially not evidence of absent synthesis.','Screen hashes are inherited from the immutable screen; this selector does not freshly read or hash original paper files.']}
    raw=(json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    freeze(D/'pilot-sample-candidates.json',raw)
    lines=['# Provisional 50-scope API pilot sample','',f'Frozen deterministic sample for cutoff `{C.name}`. Seed: `{SEED}`. No API calls, paper extraction, queue claims or scientific labels were made.','', 'Actual main/SI identity checks and source review must precede retention. Up to 20 synthesis-bearing scopes may then be selected for end-to-end work. The recipe-bearing fraction is unknown. Low-signal candidates test no-recipe decisions; they are not pre-classified exclusions.','', 'Material families are unknown unless already explicit in the frozen ledger. Literal chemical mentions are used only for sampling diversity and are not product assignments.','', '| Stratum | Selected |','|---|---:|']
    lines += [f"| {x['stratum']} | {x['selected']} |" for x in strata]
    lines += ['', '| # | Candidate group | Stratum | Recipe / structure signal |','|---:|---|---|---:|']
    lines += [f"| {x['candidate_number']} | `{x['group_id']}` | {x['assigned_stratum']} | {x['screen_signals']['recipe_score']} / {x['screen_signals']['structure_score']} |" for x in candidates]
    lines += ['', 'This stratified sample is not an unbiased corpus prevalence estimate. Report performance and retention by stratum. The JSON retains exact cutoff generations, candidate file memberships, screen hashes and source-report pointers.', '', 'JSON SHA256: `'+hashlib.sha256(raw).hexdigest()+'`','']
    freeze(D/'pilot-sample-candidates.md','\n'.join(lines).encode('utf-8'))
    print(json.dumps({'status':result['status'],'count':50,'strata':[(x['stratum'],x['selected']) for x in strata],'json_sha256':hashlib.sha256(raw).hexdigest(),'excluded_current_or_closed':dict(excluded),'unknown_families':sum(x['material_family'] is None for x in candidates)},indent=2))

if __name__=='__main__':main()
