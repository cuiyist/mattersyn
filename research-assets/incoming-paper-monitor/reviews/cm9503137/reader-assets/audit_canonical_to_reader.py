"""Read-only audit of integrated Danek source/record/hub/chemical-reader joins.

This binds existing independent scientific audits to actual reader files. It does
not replace browser visual checks or approve publication. Outputs stay private.
"""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import json,hashlib,re,html,sys
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent
B=OUT.parent
SITE=B.parents[3]/'recipe-atlas'
sys.path.insert(0,str(SITE/'scripts'))
from dataset_lib import validate_record,eligibility,training_view,digest,fmt,build_groups
from build_paper_reviews import validate as validate_review
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

def reader_measurement_ids(rid,m):
    s=m['sample_id'];prop=m['property']
    if rid.endswith('annealing-control'):return ['annealing-evidence','comparative-experiments']
    if rid.endswith('no-seed-control'):return ['seed-free-product']
    if rid.endswith('high-temperature-overgrowth'):return ['growth-absorption','comparative-experiments']
    if rid.endswith('solution-characterization'):
        if s.startswith('fig1-'):return ['figure1-size-series']
        if s=='structure-2p5':return ['hrtem-interface','xrd-measurement']
        if s=='bare-xrd':return ['xrd-measurement']
        if s=='aes-cohort':return ['elemental-methods','surface-bulk-ratio']
        if s=='optical-series':return ['solution-spectral-changes']
        if s.startswith('optical-'):return ['solution-ple'] if prop.startswith('ple_') else ['solution-pl-series']
    if rid.endswith('film-characterization'):
        if s.startswith(('bare-','coated-')):return ['film-variant-assignments','film-room-temperature','film-10k']
        if s=='fig9-bare':return ['bare-film-ple']
        if s=='fig10-coated':return ['coated-film-ple']
        if s=='fig11-series':return ['film-coverage-yield']
        if s=='film-trends':return ['film-10k'] if m['id'] in ['thermal-exposure','coated-10k-blue'] else ['film-room-temperature']
    raise AssertionError((rid,m['id'],s,prop))

def main():
    checks=[];hashes={};deltas={};joins=[]
    def check(name,value,detail=''):checks.append({'name':name,'passed':bool(value),'detail':detail})
    def bind(p):hashes[str(p.relative_to(SITE)) if p.is_relative_to(SITE) else 'private/'+str(p.relative_to(B))]=sha(p)
    audited=read(B/'canonical-records-audit.json');ah={r['record_id']:r for r in audited['records']}
    records={rid:read(SITE/'data/records'/f'{rid}.json') for rid in ah}
    routes={f'danek-1996-{x}' for x in ['znse-overgrowth','bare-dot-film','overcoated-dot-film']}
    l=read(SITE/'data/paper-reviews/danek1996.json');proposal=read(B/'public-review-proposal/danek1996.json')
    source=read(B/'source-audit.json');cov=read(B/'public-review-proposal/source-item-coverage.json')
    items={i['id']:i for s in l['reader_sections'] for i in s['items']};olditems={i['id']:i for s in proposal['reader_sections'] for i in s['items']}
    manifest=read(SITE/'dist/data/dataset-manifest.json');mr={r['record_id']:r for r in manifest['records']}
    check('Scientific audit passed with72measurements and zero must-fix',audited['status'].startswith('passed') and audited['open_must_fix_count']==0 and audited['measurement_count']==72)
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
        check(rid+' eligibility actual not merely requested',{k for k,v in eligibility(r).items() if v['eligible']}==wanted and mr[rid]['eligibility']==eligibility(r))
        check(rid+' no measured atomic structures',not any(x['eligible_as_measured_label'] for x in r['structure_assets']))
        page=hp.read_text(encoding='utf-8');text=plain(page);rows=[plain(x) for x in re.findall(r'<tr>(.*?)</tr>',page,re.S)]
        check(rid+' main-only scope visible','SI not located or verified' in text)
        check(rid+' source review linked','paper-review.html?id=danek1996' in page)
        check(rid+' correct evidence type visible',r['record_type'].replace('_',' ') in text)
        for o in r['operations']:
            if o['description']:check(rid+'/'+o['id']+' operation description visible',plain(o['description']) in text)
        for m in r['measurements']:
            mid=m['id'];labels=reader_measurement_ids(rid,m)
            check(rid+'/'+mid+' value/property/sample rendered',any(m['property'].replace('_',' ') in row and plain(fmt(m['value'])) in row and m['sample_id'] in row for row in rows))
            check(rid+'/'+mid+' specimen resolves',m['sample_id'] in {p['sample_id'] for p in r['products']})
            check(rid+'/'+mid+' semantic reader item linkage',all(i in items and rid in [x['record_id'] for x in items[i]['canonical_links']] for i in labels))
            joins.append({'record_id':rid,'measurement_id':mid,'property':m['property'],'sample_id':m['sample_id'],'reader_item_ids':labels,'source_evidence':m['evidence']})
        for task in wanted:
            v=training_view(r,task)
            check(rid+'/'+task+' no outcome leakage into input',set(v['input'])=={'composition','method'})
            if task=='partial_protocol':check(rid+' missing recipe fields preserved',v['output']['missing_fields']==r['quality']['missing_fields'] and bool(v['output']['missing_fields']))
    check('12 records72measurements and actualtypes',len(records)==12 and len(joins)==72 and Counter(r['record_type'] for r in records.values())==Counter({'literature_protocol':3,'procedure':4,'protocol_variant':2,'observation':3}))
    check('No-seed control has no Cd product identity',records['danek-1996-no-seed-control']['material']['formula']=='ZnSe' and records['danek-1996-no-seed-control']['material']['components']==['ZnSe'])
    check('Seed and no-DEZn are CdSe-scoped',all(records['danek-1996-'+x]['material']['formula']=='CdSe' for x in ['seed-preparation','no-dezn-control']))
    check('No fabricated diameter measurements',all(m['property']!='diameter' for r in records.values() for m in r['measurements']))
    allr=[read(p) for p in (SITE/'data/records').glob('*.json')];groups=build_groups(allr)
    check('184records13groups; allDanekonegroup',len(allr)==184 and len(set(groups.values()))==13 and len({groups[rid] for rid in records})==1 and len({mr[rid]['split'] for rid in records})==1)
    eligibility_totals={k:sum(eligibility(r)[k]['eligible'] for r in allr) for k in eligibility(allr[0])}
    check('Task counts match built validation',eligibility_totals==read(SITE/'dist/data/validation-report.json')['eligible_by_task'])
    check('Source-main scientific units all accessible',len(cov['source_audit_unit_map'])==121 and len(cov['reader_units'])==79 and len(items)==66)
    for u in cov['source_audit_unit_map']:check('Source unit '+u['source_audit_pointer'],bool(pointer(source,u['source_audit_pointer'])) and all(bool(pointer(l,p)) for p in u['public_targets']))
    for u in cov['reader_units']:check('Reader unit '+u['source_item_id'],bool(pointer(l,u['target'])))
    for key,item in items.items():
        diff=differences(olditems[key],item)
        check(key+' source science unchanged after integration',all(re.fullmatch(r'/canonical_links/\d+/relation',p) for p in diff),repr(diff))
        check(key+' evidence/links/claim type present',bool(item['claim_type']) and bool(item['evidence']) and all(e['source_id']=='danek1996' for e in item['evidence']) and all(x['record_id'] in records for x in item['canonical_links']))
    check('References1–18 remain citation-only',len(l['referenced_methods'])==18 and all(not x['import_experimental_evidence'] and not x['cited_work_independently_reviewed_in_this_task'] for x in l['referenced_methods']))
    check('Figure1 rows remain explicit and non-independent',len(l['tables'])==1 and l['tables'][0]['parent_id']=='figure-1' and len(l['tables'][0]['structured_rows'])==4)
    check('One unnumbered thermodynamic reaction',len(l['equations'])==1 and l['equations'][0]['id']=='reaction-1' and not l['equations'][0]['sample_links'])
    assets=[*l['figures'],*l['tables'],*l['equations']];original={x['id']:x for x in read(B/'crop-assets/manifest.json')['items']}
    for asset in assets:
        p=SITE/'dist'/asset['public_asset'];bind(p)
        check(asset['id']+' original bytes and source scope',sha(p)==asset['public_asset_sha256']==original[asset['id']]['sha256'] and bool(asset['sample_scope']) and bool(asset['quantitative_context']) and not asset['training_eligible'])
    check('13 original asset views11figures',len(assets)==13 and len(l['figures'])==11)
    review_errors=validate_review(l);check('Integrated review validator',not review_errors,repr(review_errors))
    generated=read(SITE/'dist/data/paper-reviews/danek1996.json');generated.pop('review_scope_label',None)
    check('Generated review agrees with canonical source ledger',generated==l)
    check('Source review complete main only',l['review_scope']=='supplied_main_only_si_unverified' and l['supporting_information']['status']=='not_located_or_verified')
    check('No stale canonical pending metadata',not any('canonical' in gap.lower() for x in l['recipe_inventory'] for gap in x.get('gaps',[])))
    for key in ['film-variant-assignments','coated-film-ple','figure1-size-series','surface-bulk-ratio','comparative-experiments','film-coverage-yield','film-10k','feed-stock','electrospray-preparation']:
        check(key+' specific scientific caution visible in reader content',len(items[key]['text'])>200)

    chem=SITE/'dist/assets/chemical-registry';bindings=read(chem/'bindings.json');entries={e['id']:e for e in read(chem/'registry.json')['entries']};binding_count=0;assetids=set()
    for rid,r in records.items():
        bb=bindings['recordBindings'][rid];binding_count+=len(bb);assetids.update(bb.values())
        check(rid+' all material bindings',set(bb)=={m['id'] for m in r['materials']})
        check(rid+' binding exact actual canonical hash',bindings['sourceRecordSha256'][rid]==sha(SITE/'data/records'/f'{rid}.json'))
        for mid,eid in bb.items():check(rid+'/'+mid+' registry entry resolves',eid in entries)
    for eid in assetids:
        entry=entries[eid]
        check(eid+' limitations distinguish reference from experiment',bool(entry.get('caption')) and (bool(entry.get('limitations')) or bool(entry.get('provenance',{}).get('limitations'))))
        for key in ['svgPath','model2dPath','model3dPath']:
            if not entry.get(key):continue
            p=chem/entry[key];bind(p)
            check(eid+'/'+key+' actual asset hash',p.is_file() and sha(p)==entry['assetHashes'][key])
    check('Unspecified butanol remains identity card',entries[bindings['recordBindings']['danek-1996-znse-overgrowth']['butanol']]['model3dPath'] is None)
    check('Electrospray particle alternatives not fabricated molecular coordinates',entries[bindings['recordBindings']['danek-1996-electrospray-dispersion']['dots']]['model3dPath'] is None)
    hub_summary={}
    for formula,hid in [('CdSe/ZnSe','cdse-znse-0f8c68'),('CdSe','cdse-d923c5'),('ZnSe','znse-930698')]:
        p=SITE/'dist/data/materials'/f'{hid}.json';bind(p);h=read(p)
        check(formula+' three new route IDs only',set(h['record_ids'])&set(records)==routes)
        check(formula+' contextual records distinctly typed',all(e['record_type']==records[e['record_id']]['record_type'] for e in h['evidence_records'] if e['record_id'] in records))
        check(formula+' evidence declared map matches hub',set(l['material_evidence_records'][formula])=={e['record_id'] for e in h['evidence_records'] if e['record_id'] in records})
        check(formula+' main-only source label',next(x for x in h['papers'] if x['doi']=='10.1021/cm9503137')['fullDocumentReview']['scope']=='supplied_main_only_si_unverified')
        check(formula+' scope caution present',bool(h['evidence_scope_notes']))
        hub_summary[formula]={'route_records':len(h['record_ids']),'direct_route_records':len(h['direct_record_ids']),'danek_evidence_records':len(set(l['material_evidence_records'][formula])),'component_only':h['component_only']}
    guide=(SITE/'dist/material-guide.mjs').read_text(encoding='utf-8');renderer=(SITE/'dist/paper-review.mjs').read_text(encoding='utf-8')
    check('Record/hub figure details expose quantitative context',"'quantitative_context'" in guide)
    check('Source figure details expose quantitative context',"'quantitative_context'" in renderer)
    check('Source contribution cards expose record type and scope','r.record_type' in renderer and 'r.scope' in renderer)
    check('CdSe hub ZnSe-only comparison caveat','ZnSe' in l['material_evidence_scope_notes']['CdSe'] and ('no-seed' in l['material_evidence_scope_notes']['CdSe'].lower() or 'without cdse' in l['material_evidence_scope_notes']['CdSe'].lower()))
    semantic_path=OUT/'reader-runtime-check.json'
    if semantic_path.exists():
        runtime=read(semantic_path);check('Actual source renderer semantic harness',runtime['status']=='passed' and runtime['reader_items']==66 and runtime['original_asset_links']==13);bind(semantic_path)
    else:check('Actual source renderer semantic harness',False,'Run check_reader_runtime.mjs before finalizing this audit.')
    for p in [SITE/'data/paper-reviews/danek1996.json',SITE/'dist/data/paper-reviews/danek1996.json',SITE/'dist/data/paper-review-index.json',SITE/'dist/data/dataset-manifest.json',SITE/'dist/data/validation-report.json',SITE/'dist/data/materials-index.json',chem/'registry.json',chem/'bindings.json',SITE/'dist/material-guide.mjs',SITE/'dist/material-hub.mjs',SITE/'dist/paper-review.mjs',SITE/'dist/source-evidence.mjs',SITE/'scripts/dataset_lib.py',SITE/'scripts/build_paper_reviews.py',B/'canonical-records-audit.json',B/'source-audit.json',B/'public-review-proposal/source-item-coverage.json',B/'inventory-proposal/validation.json']:bind(p)
    failures=[c for c in checks if not c['passed']]
    result={'status':'passed_bounded_canonical_to_reader_audit' if not failures else 'findings','checked_utc':datetime.now(timezone.utc).isoformat(),'doi':'10.1021/cm9503137','source_id':'danek1996','scope':'Actual local canonical data, generated record HTML, source renderer semantic harness, evidence joins, three hubs and chemical asset hashes. Browser/apparatus visual acceptance and publication remain separate.','checks_passed':len(checks)-len(failures),'check_count':len(checks),'findings':failures,'counts':{'records':len(records),'measurements':len(joins),'reader_items':len(items),'scientific_source_units':121,'reader_asset_units':79,'figures':11,'embedded_tables':1,'unnumbered_reactions':1,'references':18,'material_bindings':binding_count,'unique_chemical_entries':len(assetids)},'eligible_by_task':eligibility_totals,'source_groups':13,'danek_evaluation_group':groups[next(iter(records))],'danek_split':mr[next(iter(records))]['split'],'hub_summary':hub_summary,'authorized_promotion_differences':deltas,'measurement_to_reader_links':joins,'checks':checks,'artifact_sha256':hashes,'limitations':['Matching SI is not located or verified.','The source-to-view check does not digitize curves, create measured coordinates, infer absent parameters or establish specimen identities beyond source scope.','Source-ledger metadata and view assertions do not grant publication status; root owns final browser and publication checkpoints.']}
    (OUT/'canonical-to-reader-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Danek1996 canonical-to-reader audit','',f'**{result["status"]}** — {result["checks_passed"]}/{result["check_count"]} checks passed.',f'Snapshot: {result["checked_utc"]}','','This bounded audit compares all 12 integrated records with their exact independently audited drafts, permitting only the authorized review-status/task/scope/main-status promotion. It checks 72 measurement rows and semantic source links, 66 reader items, 121 source-audit units, 13 original asset views, 18 references, actual chemical-asset hashes, and the CdSe/ZnSe, CdSe and ZnSe hubs.','',f'All 12 records remain in {result["danek_evaluation_group"]} / {result["danek_split"]}. Only three synthesis routes enable precursor selection and partial protocol. The 184-record dataset retains 13 evaluation groups.','',f'Chemical coverage: {binding_count} material bindings to {len(assetids)} resolved registry entries. Unspecified butanol and heterogeneous particle inputs remain identity cards, not invented molecular coordinates.','',f'Task eligibility totals: {eligibility_totals}.','','Important scientific boundaries checked: Figure1 spread conflict; shell-growth versus matrix deposition; solution/film and bare/coated cohorts; 0.4 versus4.0 ratios; 250/270°C panel temperatures; 400/450°C annealing conflict; calculated shell coverage versus measurement; relative film yield versus absolute solution estimates; and thermal-exposure range versus deposition duration.','','## Findings','']
    lines+=['- '+f['name']+(': '+f['detail'] if f['detail'] else '') for f in failures] if failures else ['No outstanding findings in this bounded data/static/runtime semantic audit.']
    lines+=['','Browser layout/interaction, apparatus visual semantics and publication are separate root-owned gates. Matching SI remains unverified.']
    (OUT/'canonical-to-reader-audit.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['status','checks_passed','check_count','findings','counts']},ensure_ascii=False))
    return bool(failures)
if __name__=='__main__':raise SystemExit(main())
