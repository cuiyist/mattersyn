"""Bounded actual Yao reader/export audit. Only writes this private directory.

Run only after root confirms the final actual Site build is ready.
Scientific rereading is not repeated: exact independently audited record hashes,
source-scoped reader semantics and generated data/HTML are checked instead.
"""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import sys, json, hashlib, html, re
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent; B=OUT.parent
SITE=B.parents[3]/'recipe-atlas'; SID='yao1998'; P='yao-1998-'
sys.path.insert(0,str(SITE/'scripts'))
from dataset_lib import validate_record, eligibility, training_view, fmt, digest, build_groups
from build_atlas import synthesis_route
from build_paper_reviews import validate as validate_review
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def plain(s):return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',s))).strip()
def ptr(v,p):
    for k in p.split('/')[1:]:v=v[int(k)] if isinstance(v,list) else v[k.replace('~1','/').replace('~0','~')]
    return v
def diff(a,b,p=''):
    if type(a)!=type(b):return [p]
    if isinstance(a,dict):return [q for k in a.keys()|b.keys() for q in ([p+'/'+k] if k not in a or k not in b else diff(a[k],b[k],p+'/'+k))]
    if isinstance(a,list):return [p] if len(a)!=len(b) else [q for i,(x,y) in enumerate(zip(a,b)) for q in diff(x,y,p+'/'+str(i))]
    return [] if a==b else [p]

def main():
    checks=[];hashes={};joins=[];promotions={}
    def check(name,ok,detail=''):checks.append({'name':name,'passed':bool(ok),'detail':detail})
    def bind(path):hashes[str(path.relative_to(SITE)).replace('\\','/') if path.is_relative_to(SITE) else 'private/'+str(path.relative_to(B)).replace('\\','/')]=sha(path)
    drafts={p.stem:read(p) for p in (B/'canonical-drafts').glob('*.json')}
    records={rid:read(SITE/'data/records'/f'{rid}.json') for rid in drafts}
    ledger=read(SITE/'data/paper-reviews/yao1998.json');generated=read(SITE/'dist/data/paper-reviews/yao1998.json')
    proposal=read(B/'public-review-proposal/yao1998.json');coverage=read(B/'public-review-proposal/source-item-coverage.json');source=read(B/'source-audit.json')
    science=read(B/'canonical-records-audit.json');audited={r['record_id']:r for r in science['records']}
    manifest=read(SITE/'dist/data/dataset-manifest.json');mr={r['record_id']:r for r in manifest['records']}
    items={i['id']:i for s in ledger['reader_sections'] for i in s['items']};olditems={i['id']:i for s in proposal['reader_sections'] for i in s['items']}
    char=read(B/'characterization-draft.json');rawchar={x['id']:x for x in char['measurement_rows']}
    factitems={}
    for i in items.values():
        for f in i['facts']:factitems.setdefault(f['id'],[]).append(i['id'])
    routeids={P+'sample-a',P+'sample-b'}
    check('11 records, 61 measurements, 47 operations',len(records)==11 and sum(len(r['measurements']) for r in records.values())==61 and sum(len(r['operations']) for r in records.values())==47)
    check('Two routes, seven procedures and two observations',Counter(r['record_type'] for r in records.values())==Counter(literature_protocol=2,procedure=7,observation=2))
    check('Final independent audit covers all 11 records',science['status'].startswith('passed') and not science.get('open_findings') and not science.get('failed_checks') and set(audited)==set(records))
    for rid,r in records.items():
        dp=B/'canonical-drafts'/f'{rid}.json';rp=SITE/'data/records'/f'{rid}.json';gp=SITE/'dist/data/records'/f'{rid}.json';hp=SITE/'dist/records'/f'{rid}.html'
        for p in [dp,rp,gp,hp]:bind(p)
        check(rid+' schema and graph',not validate_record(r),repr(validate_record(r)))
        check(rid+' exact independently audited private bytes',rid in audited and sha(dp)==audited.get(rid,{}).get('sha256'))
        dd=diff(drafts[rid],r);promotions[rid]=dd
        check(rid+' only authorized promotion differences',set(dd)<={'/quality/review_status','/quality/review_scope','/quality/requested_tasks','/sources/0/main_status'},repr(dd))
        check(rid+' actual exported bytes and digest',rp.read_bytes()==gp.read_bytes() and mr[rid]['record_sha256']==digest(r))
        check(rid+' scope remains main only',r['quality']['review_status']=='source_reviewed' and 'SI not located or verified' in r['quality']['review_scope'])
        check(rid+' no asserted exact batches',r['lineage']['batch_id'] is None and all(p['batch_id'] is None for p in r['products']))
        check(rid+' no reference asset promoted to measured label',not any(a['eligible_as_measured_label'] for a in r['structure_assets']))
        wanted={'precursor_selection','partial_protocol'} if rid in routeids else set()
        check(rid+' actual task eligibility is source-scoped',{k for k,v in eligibility(r).items() if v['eligible']}==wanted and mr[rid]['eligibility']==eligibility(r))
        raw=hp.read_text(encoding='utf-8');text=plain(raw);table_rows=[plain(s) for s in re.findall(r'<tr>(.*?)</tr>',raw,re.S)]
        check(rid+' source link, record type and SI scope visible','paper-review.html?id='+SID in raw and r['record_type'].replace('_',' ') in text and 'SI not located or verified' in text)
        for op in r['operations']:
            if op['description']:check(rid+'/'+op['id']+' operation text rendered',plain(op['description']) in text)
        for m in r['measurements']:
            if m['id'].startswith('char-'):labels=factitems.get(m['id'],[])
            elif rid.endswith('cadmium-loading'):labels=['cadmium-loading'] if m['id']=='loading-fraction' else ['loading-test']
            elif rid.endswith('other-electrolytes'):labels=['alternative-salts']
            else:labels=[]
            check(rid+'/'+m['id']+' reader destination',bool(labels) and all(rid in {c['record_id'] for c in items[k]['canonical_links']} for k in labels),repr(labels))
            check(rid+'/'+m['id']+' sample resolves',m['sample_id'] in {p['sample_id'] for p in r['products']})
            check(rid+'/'+m['id']+' actual typed HTML row',any(m['property'].replace('_',' ') in tr and plain(fmt(m['value'])) in tr and m['sample_id'] in tr for tr in table_rows))
            if m['id'].startswith('char-'):
                old=rawchar[m['id']];v=m['value'];q=old.get('quantity')
                check(m['id']+' source numeric or qualitative payload retained',(v['value']==q.get('value') and v.get('minimum')==q.get('lower_bound') and v.get('maximum')==q.get('upper_bound') and v.get('unit','')==(q.get('unit') or '')) if q else v['value']==old['fact'])
                expected_sample='a-and-b-context' if isinstance(old['sample_id'],list) else old['sample_id']
                check(m['id']+' source cohort model or region preserved',m['sample_id']==expected_sample)
            joins.append({'record_id':rid,'measurement_id':m['id'],'property':m['property'],'sample_id':m['sample_id'],'value_kind':'quantity' if 'unit' in m['value'] else 'qualitative_fact','reader_item_ids':labels})
        if rid in routeids:
            check(rid+' composite host target retained',r['schema_version']=='1.2.0' and r['material']['formula']=='CdS/polymer' and r['intended_target']['host']['value'].startswith('Chelex 100'))
            check(rid+' no exact intended size or phase filled',r['intended_target']['size']['value'] is None and r['intended_target']['phase']['value'] is None)
            for task in wanted:
                v=training_view(r,task)
                check(rid+'/'+task+' requested host survives task view',v['input'].get('requested_host')==r['intended_target']['host'])
                check(rid+'/'+task+' no measured-output leakage',set(v['input'])<={'composition','method','requested_host','requested_surface'} and 'CdS' in v['input']['composition'])
                if task=='partial_protocol':check(rid+' missing conditions survive export',v['output']['missing_fields']==r['quality']['missing_fields'] and bool(v['output']['missing_fields']))
                if rid.endswith('sample-b') and task=='precursor_selection':check('NaCl electrolyte survives in separate process materials',any(p['role']=='electrolyte' and p['formula']=='NaCl' for p in v['output'].get('process_materials',[])) and not any(p['role']=='electrolyte' for p in v['output']['precursors']))
    check('53 unique characterization rows and 8 other observations',len(records[P+'characterization']['measurements'])==53 and len(joins)==61)
    check('All 54 source characterization facts represented in reader',set(rawchar)==set(factitems))
    check('100 reader items and 144 source-audit crosswalk units',len(items)==100 and len(coverage['source_audit_unit_map'])==144)
    for u in coverage['source_audit_unit_map']:check('Source unit '+u['source_audit_id'],ptr(source,u['source_audit_pointer'])['id']==u['source_audit_id'] and all(bool(ptr(ledger,p)) for p in u['public_targets']))
    for u in coverage['reader_units']:check('Reader/asset target '+u['source_item_id'],ptr(ledger,u['target'])['id']==u['source_item_id'])
    for key,item in items.items():
        dd=diff(olditems[key],item)
        check(key+' exact reviewed reader content preserved',all(re.fullmatch(r'/canonical_links/\d+/relation',p) for p in dd),repr(dd))
        for link in item['sample_scope'].get('canonical_sample_links',[]):check(key+'/'+link['sample_id']+' actual product pointer',ptr(records[link['record_id']],link['json_pointer'])['sample_id']==link['sample_id'])
    for key,need in {'salt-pretreatment':['10 mL','0.5 M','100 mL','not reconciled'],'regional-histograms':['2.7 nm','0.4','4.6 nm','1.8 nm','unit and mathematical definition'],'early-time-profile':['4.6 × 10⁻³','8.9 × 10⁻³','absorbance','√t'],'donnan-values':['−390 mV','−10 mV','−26 meV','hypothetical'],'pretreatment-diffusion-context':['Chelex 100','Dowex A-1','1.2 × 10⁻⁷'],'conflict-12':['Figure 2','sample b','Figures 8–9']}.items():check(key+' critical semantic boundaries',all(s in items[key]['text'] for s in need))
    check('All 33 source references and four direct notes',len(ledger['referenced_methods'])==33 and [r['reference_number'] for r in ledger['referenced_methods'] if r['direct_source_note_reviewed']]==[15,25,27,33])
    check('Main-only review scope preserved',ledger['review_scope']=='supplied_main_only_si_unverified' and ledger['supporting_information']['status']=='not_located_or_verified')
    check('Actual source ledger validator',not validate_review(ledger),repr(validate_review(ledger)))
    generated.pop('review_scope_label',None);check('Actual generated source ledger equals authored ledger',generated==ledger)
    assets=[a for cat in ['figures','tables','schemes','equations','source_notes'] for a in ledger[cat]]
    originals={a['relative_asset']:a for a in read(B/'crop-assets/manifest.json')['assets']}
    check('16 originals: 9 figures, 3 equations, 4 context assets',len(assets)==16 and [len(ledger[k]) for k in ['figures','equations','source_notes','tables']]==[9,3,4,0])
    for a in assets:
        p=SITE/'dist'/a['public_asset'];bind(p)
        check(a['id']+' exact original bytes and contextual qualifiers',sha(p)==a['public_asset_sha256']==originals[p.name]['sha256'] and bool(a['sample_scope']) and bool(a['quantitative_context']) and not a['training_eligible'])
    runtime=read(OUT/'reader-runtime-check.json')
    check('Actual reader DOM execution passed',runtime['status']=='passed' and runtime['reader_items']==100 and runtime['unique_original_assets']==16)
    check('Runtime actual module and ledger hashes current',all(sha(SITE/p)==h for p,h in runtime['artifact_sha256'].items()))
    allr=[read(p) for p in (SITE/'data/records').glob('*.json')];groups=build_groups(allr)
    check('All 11 records in one evaluation group and split',len({groups[rid] for rid in records})==1 and len({mr[rid]['split'] for rid in records})==1)
    raw_exports={r['record_id']:r for r in [json.loads(line) for line in (SITE/'dist/data/records.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]}
    for rid,r in records.items():check(rid+' full JSONL record export unchanged',raw_exports[rid]==r)
    bind(SITE/'dist/data/records.jsonl')
    for task in eligibility(next(iter(records.values()))):
        ep=SITE/'dist/data/exports'/f'{task}.jsonl';bind(ep)
        exports=[json.loads(line) for line in ep.read_text(encoding='utf-8').splitlines() if line.strip()]
        own={e['record_id']:e for e in exports if e['record_id'] in records}
        expected_ids=routeids if task in ['precursor_selection','partial_protocol'] else set()
        check(task+' actual JSONL scope and no duplicate rows',set(own)==expected_ids and sum(e['record_id'] in records for e in exports)==len(own))
        for rid,e in own.items():
            v=training_view(records[rid],task)
            check(rid+'/'+task+' exact JSONL input and output',e['input']==v['input'] and e['output']==v['output'])
            check(rid+'/'+task+' same-group curriculum split and record digest',e['group_id']==groups[rid] and e['split']==mr[rid]['split'] and e['record_sha256']==digest(records[rid]))
    totals={k:sum(eligibility(r)[k]['eligible'] for r in allr) for k in eligibility(allr[0])}
    check('Task totals agree with generated validation',totals==read(SITE/'dist/data/validation-report.json')['eligible_by_task'])
    check('No added size, exact structure, success or optical labels',{k:totals[k] for k in ['size_conditioned_recipe','exact_structure_recipe','success_prediction','optical_outcome']}==dict(size_conditioned_recipe=6,exact_structure_recipe=0,success_prediction=0,optical_outcome=95))
    index=read(SITE/'dist/data/materials-index.json');hubinfo={}
    for formula in ['CdS/polymer','CdS']:
        meta=next(h for h in index['materials'] if h['formula']==formula);hp=SITE/'dist/data/materials'/f"{meta['id']}.json";bind(hp);hub=read(hp)
        actual_routes=set(hub['record_ids'])&records.keys();evidence=[e for e in hub['evidence_records'] if e['record_id'] in records]
        check(formula+' exactly two active-paper routes',actual_routes==routeids)
        check(formula+' no supporting observations as routes',not ({e['record_id'] for e in evidence if e['record_type']!='literature_protocol'}&actual_routes))
        check(formula+' material evidence map preserved',{e['record_id'] for e in evidence}==set(ledger['material_evidence_records'][formula]))
        check(formula+' source paper remains main only',next(p for p in hub['papers'] if p['doi']==ledger['doi'])['fullDocumentReview']['scope']=='supplied_main_only_si_unverified')
        check(formula+' correct direct route relationship',bool(routeids&set(hub['direct_record_ids']))==(formula=='CdS/polymer'))
        check(formula+' Cd and S periodic lookup elements retained',{'Cd','S'}<=set(meta.get('elements',hub.get('elements',[]))))
        if formula=='CdS':check('Existing CdS direct routes retained',P+'sample-a' not in hub['direct_record_ids'] and 'veinot-1997-qdoh' in hub['direct_record_ids'])
        hubinfo[formula]={'id':hub['id'],'new_routes':sorted(actual_routes),'typed_evidence_records':len(evidence),'component_only':hub['component_only']}
    inv=read(SITE/'data/inventory-summary.json');summary=inv['summary'];rr={r['record_id']:r for r in allr};routes={rid for rid,r in rr.items() if synthesis_route(r)};benchmark={rid for rid in rr if mr[rid]['collection']=='published_benchmark'};lit=set(rr)-benchmark;procs={rid for rid in lit if rr[rid]['record_type']=='procedure'};obs={rid for rid in lit if rr[rid]['record_type']=='observation'}
    actual_counts={'canonical_records':len(rr),'synthesis_route_variant_records':len(routes),'contextual_control_variant_records':len(lit-routes-procs-obs),'shared_preparation_workup_characterization_assay_procedures':len(procs),'contextual_observation_records':len(obs),'published_benchmark_rows':len(benchmark),'public_material_hubs':len(index['materials']),'direct_synthesis_target_systems':sum(not h['component_only'] for h in index['materials']),'component_only_hubs':sum(h['component_only'] for h in index['materials']),'total_canonical_source_groups':len({r['lineage']['source_group'] for r in allr})}
    for k,v in actual_counts.items():check('Actual inventory '+k,summary[k]==v,repr(v))
    check('Legacy index not replaced with incoming count',summary['local_document_files_indexed']==7373 and summary['local_paper_groups_indexed']==4176)
    check('Unreviewed corpus counts not invented',all(summary[k] is None for k in ['independent_experiment_count','full_corpus_recipe_count','full_corpus_distinct_synthesized_material_count']))
    inventory={'checked_utc':datetime.now(timezone.utc).isoformat(),'actual_counts':actual_counts,'eligible_by_task':totals,'source_group':groups[next(iter(records))],'split':mr[next(iter(records))]['split'],'scope':'Generated inventory reconciliation, not whole-corpus scientific completion.'}
    (OUT/'inventory-audit.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for p in [SITE/'data/paper-reviews/yao1998.json',SITE/'dist/data/paper-reviews/yao1998.json',SITE/'dist/data/dataset-manifest.json',SITE/'dist/data/validation-report.json',SITE/'data/inventory-summary.json',SITE/'dist/data/materials-index.json',SITE/'dist/paper-review.mjs',SITE/'dist/source-evidence.mjs',SITE/'dist/material-guide.mjs',SITE/'dist/material-hub.mjs',SITE/'scripts/dataset_lib.py',SITE/'scripts/build_dataset.py',B/'canonical-records-audit.json',B/'source-audit.json',B/'public-review-proposal/source-item-coverage.json',B/'public-review-proposal/yao1998.json',OUT/'reader-runtime-check.json']:bind(p)
    failures=[c for c in checks if not c['passed']]
    result={'status':'passed_bounded_canonical_to_reader_audit' if not failures else 'findings','checked_utc':datetime.now(timezone.utc).isoformat(),'check_count':len(checks),'checks_passed':len(checks)-len(failures),'findings':failures,'scope':'Actual record/export bytes, original assets, source reader execution, measurement and source-item links, task scope, material hubs and inventory. Browser geometry, apparatus visual acceptance and publication are separately tracked.','counts':{'records':len(records),'measurements':len(joins),'operations':sum(len(r['operations']) for r in records.values()),'reader_items':len(items),'source_units':len(coverage['source_audit_unit_map']),'original_assets':len(assets)},'measurement_reader_links':joins,'authorized_promotion_differences':promotions,'eligible_by_task':totals,'hubs':hubinfo,'inventory':inventory,'artifact_sha256':hashes,'checks':checks}
    (OUT/'canonical-to-reader-audit.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    (OUT/'canonical-to-reader-audit.md').write_text('# Yao 1998 actual source-to-reader audit\n\n'+result['status']+f" — {result['checks_passed']}/{len(checks)} checks.\n\n"+result['scope']+'\n\n'+json.dumps(result['counts'],indent=2)+'\n\nFindings: '+json.dumps(failures,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['status','check_count','checks_passed','findings','counts']},ensure_ascii=False));return bool(failures)
if __name__=='__main__':raise SystemExit(main())
