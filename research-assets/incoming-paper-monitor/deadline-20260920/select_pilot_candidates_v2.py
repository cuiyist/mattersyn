"""Bounded v2 sampling correction; preserve v1 and do not merge source groups."""
from pathlib import Path
import json,hashlib,re,collections,copy
D=Path(__file__).resolve().parent
SEED='mattersyn-api-pilot-50-deadline-20260920-v2-sampling-dedup'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def freeze(p,obj):
    b=(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode()
    if p.exists():assert p.read_bytes()==b,'Frozen v2 output differs; create a new version.'
    else:p.write_bytes(b)
def normdoi(s):
    s=str(s).strip().lower()
    for prefix in ['https://doi.org/','http://doi.org/','https://dx.doi.org/','doi:']:
        if s.startswith(prefix):s=s[len(prefix):].strip()
    return s if s.startswith('10.') and '/' in s else None
def keys(c):return {('doi',n) for s in c['doi_candidates'] if (n:=normdoi(s))}|{('main_sha256',h.lower()) for h in c['screen_main_hashes'] if re.fullmatch('[a-fA-F0-9]{64}',h)}
def score(s):return hashlib.sha256((SEED+'\0'+s).encode()).hexdigest()
def matches(s,stratum):
    f=s['manual_flags'];r=s['recipe_score'];t=s['structure_score']
    return {'scanned_or_no_usable_text':any(z in f for z in ['no_usable_text_is_not_evidence_of_no_recipe','some_source_pages_have_no_usable_text']),
      'complex_or_ambiguous_bundle':any(z in f for z in ['embedded_images_or_archive_structure_uninspected','bounded_reader_limit_requires_manual_inspection','main_si_role_ambiguous','main_document_missing_or_unmatched']),
      'coordinate_and_recipe_signal':s['priority_tier']=='A_recipe_and_coordinate_candidates',
      'recipe_and_structure_signal':r>=10 and t>=8,'recipe_signal_other':r>=10 and t<8,
      'structure_with_weak_recipe_signal':t>=8 and r<10,'low_signal_no_recipe_candidates':r<=2 and t<=2,
      'si_not_present_in_frozen_group':'si_not_present_in_frozen_candidate_group' in f,
      'deterministic_shortfall_reserve':True}[stratum]
def main():
    v1path=D/'pilot-sample-candidates.json';v1hash=sha(v1path)
    assert v1hash=='0b430892f4c2c0e6c7b5f2e965cce39d5fdd126040f3248a0b9000072309595a'
    oldhashes={str(p):sha(p) for p in [v1path,D/'pilot-sample-candidates.md',D/'select_pilot_candidates.py']}
    v1=load(v1path);C=D/v1['cutoff_id'];lp=C/'ledger-at-cutoff.json';mp=C/'last-authoritative-group-mapping.json'
    sp=next(Path(p) for p in v1['source_provenance'] if '/reports/' in p.replace('\\','/'))
    for p,h in v1['source_provenance'].items():assert sha(p)==h
    ledger=load(lp);mapping=load(mp);screen=load(sp);pending=set(mapping['pending_group_ids']);active=set(v1['already_claimed_group_ids_excluded']);aliases=set(ledger.get('group_aliases',{}))
    byid={s['group_id']:(i,s) for i,s in enumerate(screen['scopes'])}
    selected=copy.deepcopy(v1['candidates']);seen={};collisions=[]
    for i,c in enumerate(selected):
        overlap=keys(c)&seen.keys()
        if overlap:collisions.append((i,sorted(overlap)))
        else:
            for k in keys(c):seen[k]=c['candidate_number']
    collided={i for i,_ in collisions};retained=[c for i,c in enumerate(selected) if i not in collided]
    usedkeys=set().union(*(keys(c) for c in retained));usedids={c['group_id'] for c in retained};corrections=[]
    for index,overlap in collisions:
        old=selected[index];st=old['assigned_stratum'];options=[]
        for gid,(si,s) in byid.items():
            g=ledger['groups'].get(gid)
            if not g or gid not in pending or gid in active or gid in aliases or gid in usedids:continue
            if s['source_generation']!=g['generation'] or not s['priority_applicable'] or not matches(s,st):continue
            ckeys={('doi',n) for z in s['doi_candidates'] if (n:=normdoi(z))}|{('main_sha256',h.lower()) for h in s['main_hashes']}
            if ckeys&usedkeys:continue
            options.append((score(st+'\0'+gid),gid,si,s,g,ckeys))
        assert options,'No same-stratum unique replacement; do not silently alter the sampling design.'
        _,gid,si,s,g,ckeys=min(options,key=lambda z:z[0]);new=copy.deepcopy(old)
        files=[dict(file_key=k,role_at_cutoff=ledger['files'][k].get('role'),source_id=ledger['files'][k].get('source_id'),relative_filename=ledger['files'][k].get('relative_filename'),size_bytes=ledger['files'][k].get('size')) for k in g['files'] if k in ledger['files'] and ledger['files'][k].get('exists')]
        mentions={}
        for sn in s.get('candidate_snippets',[]):
            for token in re.findall(r'(?<![A-Za-z0-9])(?:CdSe|CdS|CdTe|PbSe|PbS|ZnO|ZnS|TiO2|SnO2|SiO2|Fe3O4|FePt|CoFe2O4|perovskite|zeolite|silicon)(?![A-Za-z0-9])',sn.get('text',''),re.I):
                mentions.setdefault(token,{'source_sha256':sn.get('source_sha256'),'page':sn.get('page'),'line_start_in_text_block':sn.get('line_start_in_text_block'),'line_end_in_text_block':sn.get('line_end_in_text_block'),'status':'literal_unreviewed_mention_may_be_precursor_reference_or_product'})
        family=g.get('material_family') or g.get('verified_material_family')
        new.update(group_id=gid,doi_candidates=s['doi_candidates'],source_generation_at_cutoff=g['generation'],queue_order_at_cutoff=g['queue_order'],review_status_at_cutoff=g['review'].get('status'),material_family=family,material_family_status='existing_explicit_ledger_metadata_unverified_for_pilot' if family else 'unknown_no_family_inferred',unverified_literal_material_mentions=mentions,diversity_bucket=str(family) if family else 'mention:'+sorted(mentions,key=str.lower)[0].lower() if mentions else 'unknown',screen_signals={'recipe_score':s['recipe_score'],'structure_score':s['structure_score'],'combined_score':s['score'],'priority_tier':s['priority_tier'],'feature_counts':s['feature_counts'],'manual_flags':s['manual_flags']},source_bundle_candidate_files=files,screen_source_hashes=s['source_hashes'],screen_main_hashes=s['main_hashes'],evidence_provenance={'screen_scope_index':si,'screen_json_pointer':'/scopes/'+str(si),'source_report_sha256':sp.stem})
        selected[index]=new;usedids.add(gid);usedkeys|=ckeys
        corrections.append({'candidate_number':old['candidate_number'],'stratum':st,'old_group_id':old['group_id'],'new_group_id':gid,'shared_sampling_keys':[{'type':kind,'value':value,'retained_candidate_number':seen[(kind,value)]} for kind,value in overlap],'replacement_pool_size':len(options),'selection_rule':'Lowest SHA256(v2 seed + NUL + stratum + NUL + group ID) among eligible, same-stratum scopes with no shared normalized DOI or main-hash sampling key.','source_identity_resolution_claimed':False})
    assert len(selected)==50 and len({c['group_id'] for c in selected})==50
    keyowner={}
    for c in selected:
        for k in keys(c):assert k not in keyowner;keyowner[k]=c['candidate_number']
    assert collections.Counter(c['assigned_stratum'] for c in selected)==collections.Counter(c['assigned_stratum'] for c in v1['candidates'])
    unchanged=[c['candidate_number'] for c,o in zip(selected,v1['candidates']) if c==o]
    out=copy.deepcopy(v1);out.update(version=2,seed=SEED,parent_version={'path':str(v1path),'sha256':v1hash},sample_purpose='deliberately_stratified_QA_calibration',determinism='Preserve all noncolliding v1 candidates. Replace later duplicate sampling keys in the same stratum by deterministic SHA256 ordering. This is not a probability sample.',inclusion_probabilities=None,weighted_corpus_prevalence_supported=False,corpus_recipe_prevalence_estimation_supported=False,corpus_eta_requires_separate_representative_prevalence_assessment=True,sampling_duplicate_rule='No repeated normalized candidate DOI or screened main-source SHA256 within this QA sample. These are diversity keys only, not a global deduplication, document identity verification or scientific merge.',sampling_key_identity_review='Shared DOI/hash discovery is recorded for intake review; original source groups and ledger are unchanged.',corrections=corrections,unchanged_candidate_numbers=unchanged,candidates=selected,selector_sha256=sha(__file__))
    out['limitations']+=['Inclusion probabilities are unavailable. This QA calibration sample must not support weighted corpus recipe prevalence or be used alone to extrapolate a corpus ETA. A separate representative prevalence assessment is required.','A shared DOI or main hash is used only to avoid redundant sampling. Actual main/SI pairing and any group reconciliation still require review.']
    path=D/'pilot-sample-candidates-v2.json';freeze(path,out)
    lines=['# API pilot QA calibration sample — v2','','This immutable v2 preserves v1 and replaces only repeated sampling keys within the same stratum. It does not merge source groups or verify main/SI identities.','', '**Purpose:** deliberately stratified QA calibration. Inclusion probabilities are unavailable; this sample cannot support weighted corpus prevalence or corpus-ETA extrapolation. Obtain a separate representative prevalence assessment.','', 'Up to 20 retained end-to-end scopes will be chosen after actual matching/review. Recipe-bearing prevalence remains unknown; no paid calls or extraction have started.','', '| Candidate | Replaced group | New group | Stratum |','|---:|---|---|---|']
    lines += [f"| {c['candidate_number']} | `{c['old_group_id']}` | `{c['new_group_id']}` | {c['stratum']} |" for c in corrections]
    lines += ['', '| # | Candidate group | Stratum |','|---:|---|---|']+[f"| {c['candidate_number']} | `{c['group_id']}` | {c['assigned_stratum']} |" for c in selected]
    lines += ['',f'v2 JSON SHA256: `{sha(path)}`','']
    md=D/'pilot-sample-candidates-v2.md';b='\n'.join(lines).encode()
    if md.exists():assert md.read_bytes()==b
    else:md.write_bytes(b)
    for p,h in oldhashes.items():assert sha(p)==h
    manifest={'schema':'mattersyn-pilot-sample-version-manifest/1','active_version':2,'purpose':'QA_calibration_not_probability_sample','candidate_count':50,'correction_count':len(corrections),'unchanged_candidates':len(unchanged),'duplicate_normalized_doi_keys':0,'duplicate_main_hash_keys':0,'stratum_counts_unchanged':True,'v1_files_unchanged':oldhashes,'files':{str(p):sha(p) for p in [path,md,Path(__file__)]},'requires_main_si_matching':True,'requires_separate_representative_prevalence_assessment':True,'global_group_merge_performed':False,'ledger_modified':False,'api_calls':0}
    freeze(D/'pilot-sample-v2-manifest.json',manifest)
    freeze(D/'pilot-sample-current.json',{'version':2,'sample_path':str(path),'sample_sha256':sha(path),'manifest_path':str(D/'pilot-sample-v2-manifest.json'),'manifest_sha256':sha(D/'pilot-sample-v2-manifest.json'),'purpose':'QA_calibration_only_no_corpus_prevalence'})
    print(json.dumps({'status':'passed_v2_immutable_sampling_correction','sample_sha256':sha(path),'manifest_sha256':sha(D/'pilot-sample-v2-manifest.json'),'corrections':corrections,'unchanged':len(unchanged)},indent=2))
if __name__=='__main__':main()
