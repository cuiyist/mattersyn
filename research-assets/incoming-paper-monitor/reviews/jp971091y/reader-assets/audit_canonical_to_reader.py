"""Bounded, read-only final Dabbousi canonical/source/reader/inventory audit.

Only private audit artifacts are written. This does not approve publication or
replace the root's browser/apparatus acceptance checks.
"""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import json,hashlib,re,html,sys
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent;B=OUT.parent
SITE=B.parents[3]/'recipe-atlas';SID='dabbousi1997'
sys.path.insert(0,str(SITE/'scripts'))
from dataset_lib import validate_record,eligibility,training_view,digest,fmt,build_groups
from build_paper_reviews import validate as validate_review
from build_atlas import synthesis_route
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def plain(s):return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',s))).strip()
def pointer(v,p):
    for x in p.split('/')[1:]:v=v[int(x)] if isinstance(v,list) else v[x.replace('~1','/').replace('~0','~')]
    return v
def differences(a,b,p=''):
    if type(a)!=type(b):return [p]
    if isinstance(a,dict):return [q for k in a.keys()|b.keys() for q in ([p+'/'+k] if k not in a or k not in b else differences(a[k],b[k],p+'/'+k))]
    if isinstance(a,list):
        if len(a)!=len(b):return [p]
        return [q for i,(x,y) in enumerate(zip(a,b)) for q in differences(x,y,p+'/'+str(i))]
    return [] if a==b else [p]
def reader_ids(rid,m):
    s=m['sample_id'];mid=m['id']
    if rid.endswith('cdse-seed-preparation'):return ['core-preparation']
    if rid.endswith('core-size-optical-series'):return ['six-dispersion-photograph'] if s.startswith('photo-') else ['core-size-optics']
    if rid.endswith('air-exposure-observations'):return ['air-exposure-results']
    if rid.endswith('solution-saxs-series'):return ['solution-saxs-cohort','solution-saxs-fitting']
    if rid.endswith('cds-optical-comparison'):return ['cds-optical-comparison']
    if rid.endswith('coverage-series'):
        if s=='coverage-optical-shift':return ['zns-energy-shifts']
        if s.startswith('xps-'):return ['xps-composition'] if mid=='bare-se-cd' else ['auger-parameters']
        if mid.endswith('yield'):return ['coverage-pl']
        return ['table1-structure']
    raise AssertionError((rid,mid,s))

def main():
    checks=[];hashes={};joins=[];deltas={}
    def check(name,ok,detail=''):checks.append({'name':name,'passed':bool(ok),'detail':detail})
    def bind(p):hashes[str(p.relative_to(SITE)) if p.is_relative_to(SITE) else 'private/'+str(p.relative_to(B))]=sha(p)
    audited=read(B/'canonical-records-audit.json');ah={r['record_id']:r for r in audited['records']}
    records={rid:read(SITE/'data/records'/f'{rid}.json') for rid in ah}
    routes={'dabbousi-1997-zns-overgrowth','dabbousi-1997-cds-overgrowth'}
    l=read(SITE/'data/paper-reviews'/f'{SID}.json');proposal=read(B/'public-review-proposal'/f'{SID}.json')
    source=read(B/'source-audit.json');cov=read(B/'public-review-proposal/source-item-coverage.json')
    items={i['id']:i for s in l['reader_sections'] for i in s['items']};olditems={i['id']:i for s in proposal['reader_sections'] for i in s['items']}
    manifest=read(SITE/'dist/data/dataset-manifest.json');mr={r['record_id']:r for r in manifest['records']}
    check('Independent scientific audit120measurements60operations with zero must-fix',audited['status'].startswith('passed') and audited['open_must_fix_count']==0 and audited['measurement_count']==120 and audited['operation_count']==60)
    allowed={'/quality/review_status','/quality/review_scope','/quality/requested_tasks','/sources/0/main_status'}
    for rid,r in records.items():
        path=SITE/'data/records'/f'{rid}.json';built=SITE/'dist/data/records'/f'{rid}.json';dp=B/'canonical-drafts'/f'{rid}.json';hp=SITE/'dist/records'/f'{rid}.html'
        for p in [path,built,dp,hp]:bind(p)
        draft=read(dp);diff=differences(draft,r);deltas[rid]=diff
        check(rid+' audited draft hash',sha(dp)==ah[rid]['sha256'])
        check(rid+' permitted promotion differences only',set(diff)<=allowed,repr(diff))
        errors=validate_record(r);check(rid+' canonical schema/graph',not errors,repr(errors))
        check(rid+' generated record identical',path.read_bytes()==built.read_bytes())
        check(rid+' manifest normalized digest',mr[rid]['record_sha256']==digest(r))
        check(rid+' source reviewed with SI unverified',r['quality']['review_status']=='source_reviewed' and 'SI not located or verified' in r['quality']['review_scope'])
        wanted={'precursor_selection','partial_protocol'} if rid in routes else set()
        check(rid+' actual eligibility',{k for k,v in eligibility(r).items() if v['eligible']}==wanted and mr[rid]['eligibility']==eligibility(r))
        check(rid+' no measured atom coordinates',not any(x['eligible_as_measured_label'] for x in r['structure_assets']))
        page=hp.read_text(encoding='utf-8');text=plain(page);rows=[plain(x) for x in re.findall(r'<tr>(.*?)</tr>',page,re.S)]
        check(rid+' main-only scope and review link visible','SI not located or verified' in text and 'paper-review.html?id='+SID in page)
        check(rid+' evidence type visible',r['record_type'].replace('_',' ') in text)
        for o in r['operations']:
            if o['description']:check(rid+'/'+o['id']+' operation description visible',plain(o['description']) in text)
        for m in r['measurements']:
            labels=reader_ids(rid,m)
            check(rid+'/'+m['id']+' numeric row/property/sample visible',any(m['property'].replace('_',' ') in row and plain(fmt(m['value'])) in row and m['sample_id'] in row for row in rows))
            check(rid+'/'+m['id']+' specimen resolves',m['sample_id'] in {p['sample_id'] for p in r['products']})
            check(rid+'/'+m['id']+' semantic reader join',all(i in items and rid in [x['record_id'] for x in items[i]['canonical_links']] for i in labels))
            joins.append({'record_id':rid,'measurement_id':m['id'],'property':m['property'],'sample_id':m['sample_id'],'reader_item_ids':labels,'source_evidence':m['evidence']})
        for task in wanted:
            v=training_view(r,task)
            check(rid+'/'+task+' no outcome leakage',set(v['input'])=={'composition','method'})
            if task=='partial_protocol':check(rid+' missing fields preserved',v['output']['missing_fields']==r['quality']['missing_fields'] and bool(v['output']['missing_fields']))
    check('17records120measurements60operations2routes10procedures5observations',len(records)==17 and len(joins)==120 and sum(len(r['operations']) for r in records.values())==60 and Counter(r['record_type'] for r in records.values())==Counter(literature_protocol=2,procedure=10,observation=5))
    allr=[read(p) for p in (SITE/'data/records').glob('*.json')];groups=build_groups(allr)
    check('201 records14groups; Dabbousi one group and split',len(allr)==201 and len(set(groups.values()))==14 and len({groups[rid] for rid in records})==1 and len({mr[rid]['split'] for rid in records})==1)
    totals={k:sum(eligibility(r)[k]['eligible'] for r in allr) for k in eligibility(allr[0])}
    check('Task counts match validation and no new outcome tasks',totals==read(SITE/'dist/data/validation-report.json')['eligible_by_task']=={'precursor_selection':42,'partial_protocol':58,'size_conditioned_recipe':6,'exact_structure_recipe':0,'success_prediction':0,'optical_outcome':95})
    check('204scientific units126readerasset units101items',len(cov['source_audit_unit_map'])==204 and len(cov['reader_units'])==126 and len(items)==101)
    for u in cov['source_audit_unit_map']:check('Source unit '+u['source_audit_pointer'],bool(pointer(source,u['source_audit_pointer'])) and all(bool(pointer(l,p)) for p in u['public_targets']))
    for u in cov['reader_units']:check('Reader unit '+u['source_item_id'],pointer(l,u['target'])['id']==u['source_item_id'])
    for key,item in items.items():
        diff=differences(olditems[key],item)
        check(key+' source science unchanged after integration',all(re.fullmatch(r'/canonical_links/\d+/relation',p) for p in diff),repr(diff))
        check(key+' evidence and typed source links',bool(item['claim_type']) and bool(item['evidence']) and all(e['source_id']==SID for e in item['evidence']) and all(x['record_id'] in records for x in item['canonical_links']))
        for link in item['sample_scope'].get('canonical_sample_links',[]):check(key+'/'+link['sample_id']+' exact product pointer',pointer(records[link['record_id']],link['json_pointer'])['sample_id']==link['sample_id'])
    check('40references and3direct notes retain source scope',len(l['referenced_methods'])==40 and [r['reference_number'] for r in l['referenced_methods'] if r['direct_source_note_reviewed']]==[22,26,38] and all(not x['import_experimental_evidence'] and not x['cited_work_independently_reviewed_in_this_task'] for x in l['referenced_methods']))
    check('Table1 source numbers and nulls preserved',l['tables'][0]['structured_rows']==proposal['tables'][0]['structured_rows'] and len(l['tables'][0]['structured_rows'])==5)
    check('XPS products not merged into Table1',all(z['sample_id'].startswith('xps-') for k in ['xps-composition','auger-parameters','xps-intensity-model','xps-finite-size-correction'] for z in items[k]['sample_scope']['canonical_sample_links']))
    check('Initial baseline scope and nonreplicate warning retained',all('without representing an independent replicate' in ' '.join(items[k]['notes']) and 'physical identity with the later exposure film is unresolved' in ' '.join(items[k]['notes']) for k in ['air-exposure-method','air-exposure-results','xps-composition']))
    check('Six paired method settings not six batches',len(items['size-temperature-pairs']['facts'])==6 and 'not six fully documented batches' in items['size-temperature-pairs']['text'] and len(records['dabbousi-1997-zns-overgrowth']['condition_options'])==6)
    assets=[*l['figures'],*l['tables'],*l['equations'],*l['source_notes']]
    original={Path(x['relative_asset']).name:x for x in read(B/'crop-assets/manifest.json')['assets']}
    for a in assets:
        p=SITE/'dist'/a['public_asset'];bind(p)
        check(a['id']+' original bytes and source scope',sha(p)==a['public_asset_sha256']==original[p.name]['sha256'] and bool(a['sample_scope']) and bool(a['quantitative_context']) and not a['training_eligible'])
    check('25assetviews16figures1table5numberedequations2formulacontexts1note',[len(l[k]) for k in ['figures','tables','equations','source_notes']]==[16,1,7,1] and len(assets)==25 and sum(x['source_asset_type']=='equation' for x in l['equations'])==5)
    note=items['size-temperature-pairs']['original_assets'][0]
    check('Source note22 item link matches dedicated asset',note['public_asset']==l['source_notes'][0]['public_asset'] and note['sha256']==l['source_notes'][0]['public_asset_sha256'])
    check('Model-only Figure14 and equations do not create measured specimens',not next(f for f in l['figures'] if f['id']=='figure-14')['sample_links'] and all(not e['sample_links'] for e in l['equations']))
    errors=validate_review(l);check('Actual source-review validator',not errors,repr(errors))
    generated=read(SITE/'dist/data/paper-reviews'/f'{SID}.json');generated.pop('review_scope_label',None)
    check('Generated review agrees with authored ledger',generated==l)
    check('Main only, SI unverified',l['review_scope']=='supplied_main_only_si_unverified' and l['supporting_information']['status']=='not_located_or_verified')
    check('No pending canonical audit labels remain',not any('canonical' in g.lower() for x in l['recipe_inventory'] for g in x.get('gaps',[])) and not any('pending' in x['relation'].lower() for i in items.values() for x in i['canonical_links']))
    for k in ['cds-addition-storage','solution-saxs-cohort','solution-saxs-fitting','electronic-model-assumptions','zns-cds-confinement','cds-optical-comparison','escape-depths','xps-intensity-model','xps-finite-size-correction','table1-structure']:
        check(k+' substantial scoped reader context',len(items[k]['text'])>150)
    chem=SITE/'dist/assets/chemical-registry';bindings=read(chem/'bindings.json');entries={e['id']:e for e in read(chem/'registry.json')['entries']};binding_count=0;assetids=set()
    for rid,r in records.items():
        bb=bindings['recordBindings'][rid];binding_count+=len(bb);assetids.update(bb.values())
        check(rid+' all material bindings',set(bb)=={m['id'] for m in r['materials']})
        check(rid+' exact source-record binding hash',bindings['sourceRecordSha256'][rid]==sha(SITE/'data/records'/f'{rid}.json'))
        for mid,eid in bb.items():check(rid+'/'+mid+' chemical registry entry resolves',eid in entries)
    for eid in assetids:
        e=entries[eid]
        check(eid+' reference/illustration limitations',bool(e.get('caption')) and (bool(e.get('limitations')) or bool(e.get('provenance',{}).get('limitations'))))
        for key in ['svgPath','model2dPath','model3dPath']:
            if e.get(key):
                p=chem/e[key];bind(p);check(eid+'/'+key+' asset bytes',sha(p)==e['assetHashes'][key])
    index=read(SITE/'dist/data/materials-index.json');hub_summary={}
    for formula in ['CdSe/ZnS','ZnS','CdSe/CdS','CdS','CdSe']:
        meta=next(h for h in index['materials'] if h['formula']==formula);p=SITE/'dist/data/materials'/f'{meta["id"]}.json';bind(p);h=read(p)
        wanted=routes if formula=='CdSe' else {'dabbousi-1997-zns-overgrowth'} if formula in ['CdSe/ZnS','ZnS'] else {'dabbousi-1997-cds-overgrowth'}
        present={x['record_id'] for x in h['evidence_records'] if x['record_id'] in records}
        check(formula+' only matching synthesis routes',set(h['record_ids'])&records.keys()==wanted)
        check(formula+' typed supporting evidence',all(e['record_type']==records[e['record_id']]['record_type'] for e in h['evidence_records'] if e['record_id'] in records))
        check(formula+' material evidence map agrees',set(l['material_evidence_records'][formula])==present)
        check(formula+' supplied-main scope',next(x for x in h['papers'] if x['doi']=='10.1021/jp971091y')['fullDocumentReview']['scope']=='supplied_main_only_si_unverified')
        check(formula+' composition/component scope note',bool(h['evidence_scope_notes']))
        hub_summary[formula]={'new_route_ids':sorted(wanted),'new_evidence_records':len(present),'component_only':h['component_only']}
    check('Five hubs preserve15/15/4/4/17evidence scopes',[hub_summary[x]['new_evidence_records'] for x in ['CdSe/ZnS','ZnS','CdSe/CdS','CdS','CdSe']]==[15,15,4,4,17])
    runtime=read(OUT/'reader-runtime-check.json');bind(OUT/'reader-runtime-check.json')
    check('Actual reader runtime has101cards25originalassets',runtime['status']=='passed' and runtime['reader_items']==101 and runtime['unique_original_assets']==25)
    check('Runtime binds current ledger/modules',all(sha(SITE/p)==h for p,h in runtime['artifact_sha256'].items()))
    # Independently reconcile inventory from actual records and generated hubs.
    inv=read(SITE/'data/inventory-summary.json');summary=inv['summary'];ic=[]
    def icheck(name,ok,detail=''):ic.append({'name':name,'passed':bool(ok),'detail':detail})
    rr={r['record_id']:r for r in allr};routeids={rid for rid,r in rr.items() if synthesis_route(r)}
    bench={rid for rid in rr if mr[rid]['collection']=='published_benchmark'}
    literature=set(rr)-bench;procedures={rid for rid in literature if rr[rid]['record_type']=='procedure'};obs={rid for rid in literature if rr[rid]['record_type']=='observation'};controls=literature-routeids-procedures-obs
    actual={'canonical_records':len(rr),'reviewed_literature_records':len(literature),'published_benchmark_rows':len(bench),'synthesis_route_variant_records':len(routeids),'contextual_control_variant_records':len(controls),'shared_preparation_workup_characterization_assay_procedures':len(procedures),'contextual_observation_records':len(obs),'total_canonical_source_groups':len({r['lineage']['source_group'] for r in allr}),'reviewed_literature_source_groups':len({rr[rid]['lineage']['source_group'] for rid in literature}),'public_material_hubs':len(index['materials']),'direct_synthesis_target_systems':sum(not h['component_only'] for h in index['materials']),'component_only_hubs':sum(h['component_only'] for h in index['materials']),'canonical_record_type_counts':dict(sorted(Counter(r['record_type'] for r in allr).items()))}
    for k,v in actual.items():icheck(k+' matches actual',summary[k]==v,repr(v))
    icheck('Five distinct categories partition actual201records',len(rr)==sum(map(len,[routeids,controls,procedures,obs,bench])) and set(rr)==routeids|controls|procedures|obs|bench)
    icheck('Legacy corpus counts not inflated with incomingfolder',summary['local_document_files_indexed']==7373 and summary['local_paper_groups_indexed']==4176 and summary['unique_document_content_hashes']==6857)
    icheck('No invented independent experiment/fullcorpus totals',all(summary[k] is None for k in ['independent_experiment_count','full_corpus_distinct_synthesized_material_count','full_corpus_recipe_count']))
    reviews=[read(p) for p in (SITE/'data/paper-reviews').glob('*.json')]
    mainonly=[r for r in reviews if r['review_scope']=='supplied_main_only_si_unverified']
    icheck('Four mainonlyreviews34pages remain separate',len(mainonly)==summary['formal_full_main_reviews_si_unverified']==4 and sum(d['page_count'] for r in mainonly for d in r['documents'])==summary['formal_full_main_only_review_pages']==34)
    icheck('Matched SI baseline not promoted by newmain',summary['formal_full_main_and_matched_si_reviews']==5 and summary['formal_full_review_pages']==74)
    row=next(p for p in inv['per_paper'] if p['source_group']==SID)
    icheck('Newpaper exact17records2routes10procedures5observations120measurements',set(row['record_ids'])==set(records) and [row[k] for k in ['canonical_record_count','synthesis_route_variant_count','procedure_count','contextual_observation_count','measurement_entry_count']]==[17,2,10,5,120] and row['si_status']=='not_located_or_verified')
    for key,expected in [('canonical_record_count',len(rr)),('synthesis_route_variant_count',len(routeids)),('contextual_control_count',len(controls)),('procedure_count',len(procedures)),('contextual_observation_count',len(obs))]:icheck('Perpaper sum '+key,sum(p.get(key,0) for p in inv['per_paper'])==expected)
    icheck('Eligibility totals reported accurately',inv['training_eligibility'].get('eligible_by_task',inv['training_eligibility'])==totals)
    inventory={'status':'passed' if all(x['passed'] for x in ic) else 'findings','checked_utc':datetime.now(timezone.utc).isoformat(),'scope':'Actual local canonical records, generated hubs and inventory. Corpus baseline7373files/4176groups remains separate from incoming-folder queue. Not a count of all scientifically read papers or independent syntheses.','actual_counts':actual,'eligible_by_task':totals,'dabbousi_row':row,'checks':ic,'findings':[x for x in ic if not x['passed']],'artifact_sha256':{str(p.relative_to(SITE)):sha(p) for p in [SITE/'data/inventory-summary.json',SITE/'dist/data/inventory-summary.json',SITE/'dist/data/materials-index.json',SITE/'dist/data/dataset-manifest.json',SITE/'dist/data/validation-report.json']}}
    (OUT/'inventory-audit.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (OUT/'inventory-audit.md').write_text('# Dabbousi1997 integrated inventory audit\n\n'+inventory['status']+'\n\n201 records = 42 synthesis routes + 11 controls + 38 procedures + 10 observations + 100 benchmark rows. 19 material hubs = 13 direct systems + 6 component-only hubs. 14 source/evaluation groups. The new source adds two routes, ten procedures, five observations and 120 measurement entries; these are not 17 independent experiments.\n\nMain-only formal review totals are four sources /34pages. Five matched-main/SI reviews /74pages remain unchanged. The legacy indexed corpus remains7373files/4176groups; incoming queue documents are not folded into those totals.\n\nFindings: '+json.dumps(inventory['findings'],ensure_ascii=False)+'\n',encoding='utf-8')
    check('Independent inventory reconciliation',inventory['status']=='passed',repr(inventory['findings']))
    for p in [SITE/'data/paper-reviews'/f'{SID}.json',SITE/'dist/data/paper-reviews'/f'{SID}.json',SITE/'data/inventory-summary.json',SITE/'dist/data/inventory-summary.json',SITE/'dist/data/paper-review-index.json',SITE/'dist/data/dataset-manifest.json',SITE/'dist/data/validation-report.json',SITE/'dist/data/materials-index.json',chem/'registry.json',chem/'bindings.json',SITE/'dist/material-guide.mjs',SITE/'dist/material-hub.mjs',SITE/'dist/paper-review.mjs',SITE/'dist/source-evidence.mjs',SITE/'scripts/dataset_lib.py',SITE/'scripts/build_paper_reviews.py',B/'canonical-records-audit.json',B/'source-audit.json',B/'public-review-proposal/source-item-coverage.json',B/'public-review-proposal/proposal-checks.json',OUT/'inventory-audit.json']:bind(p)
    failures=[c for c in checks if not c['passed']]
    result={'status':'passed_bounded_canonical_to_reader_audit' if not failures else 'findings','checked_utc':datetime.now(timezone.utc).isoformat(),'doi':'10.1021/jp971091y','source_id':SID,'scope':'Actual canonical/generated records, controlled source-reader runtime, explicit source/sample joins, five affected material hubs, original assets and molecular asset bytes. Browser/apparatus geometry and publication remain separate.','checks_passed':len(checks)-len(failures),'check_count':len(checks),'findings':failures,'counts':{'records':17,'measurements':120,'operations':60,'reader_items':101,'scientific_source_units':204,'reader_asset_units':126,'figures':16,'tables':1,'numbered_equations':5,'unnumbered_formula_assets':2,'source_note_assets':1,'references_and_notes':40,'material_bindings':binding_count,'unique_chemical_entries':len(assetids)},'eligible_by_task':totals,'source_groups':14,'evaluation_group':groups[next(iter(records))],'split':mr[next(iter(records))]['split'],'hub_summary':hub_summary,'authorized_promotion_differences':deltas,'measurement_to_reader_links':joins,'checks':checks,'artifact_sha256':hashes,'limitations':['Matched SI remains unverified.','No curves are digitized and no missing batch/specimen identities or atomic coordinates are inferred.','A source-context relation is not proof of exact recipe-to-outcome linkage.','Root owns final browser/apparatus visual acceptance and publication.']}
    (OUT/'canonical-to-reader-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Dabbousi1997 canonical-to-reader audit','',f'**{result["status"]}** — {result["checks_passed"]}/{len(checks)} checks passed.',f'Snapshot: {result["checked_utc"]}','','17 exact audited records retain120measurement entries and60operations. All204scientific source units resolve to101reader items and25original asset views. Allsource-note links, 40references/notes, Table1nulls, XPS-vs-Table1 specimen distinctions and initial-air baseline ambiguity are retained.','','Only two synthesis routes enable precursor selection and partial protocol. All17records share one evaluation group/split. No new size, exact-structure, success or optical-outcome examples were enabled. Characterization procedures, observations and electronic/scattering models remain separate.','','Five material pages retain matching routes and typed supporting evidence: CdSe/ZnS, ZnS, CdSe/CdS, CdS and CdSe. Component pages do not imply isolated shell-material synthesis.','','## Findings','']
    lines+=['- '+f['name']+(': '+f['detail'] if f['detail'] else '') for f in failures] if failures else ['No outstanding findings in this bounded data/static/runtime semantic audit.']
    lines+=['','Matching SI, browser/apparatus visual acceptance and publication remain separate gates. Artifact hashes and all measurement-to-reader links are in the companion JSON.']
    (OUT/'canonical-to-reader-audit.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['status','checks_passed','check_count','findings','counts']},ensure_ascii=False))
    return bool(failures)
if __name__=='__main__':raise SystemExit(main())
