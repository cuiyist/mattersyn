"""Independent, read-only checks of the actual Morrison Site integration."""
from pathlib import Path
import json, hashlib, copy, sys, re
from datetime import datetime, timezone
A=Path(__file__).resolve().parent; N=A.parent; O=N/'site-integration-proposal'; P=O/'v1'; C=O/'product-context-v1'
S=N.parents[4]/'recipe-atlas'; B=O/'base-site-inputs'
sys.path.insert(0,str(S/'scripts'))
from dataset_lib import validate_record, eligibility, build_groups, training_view, digest
from build_atlas import synthesis_route
from review_scope import source_review_scope
from build_dataset import measurement_table
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]; bound={}; counts={}
def bind(p):
    p=p.resolve(); bound[str(p)]=sha(p); return p
def ck(ok,label): checks.append({'ok':bool(ok),'label':label})
def rd(p): bind(p); return read(p)
def ptr(o,p):
    if p=='': return o
    for t in p.lstrip('/').split('/'):
        t=t.replace('~1','/').replace('~0','~'); o=o[int(t)] if isinstance(o,list) else o[t]
    return o
for name,directory in [('promotion-delta-audit.json',P),('product-context-audit.json',C)]:
    a=rd(A/name); f=rd(directory/'package-freeze.json')
    ck(a['status']=='passed' and not a['open_findings'],name+' passed')
    ck(a['proposal_freeze_sha256']==sha(directory/'package-freeze.json'),name+' current freeze')
    for entry in f['files']: ck(sha(bind(directory/entry['path']))==entry['sha256'],'projection frozen '+entry['path'])
oldhash=rd(O/'base-record-hashes.json'); current={p.stem:rd(p) for p in sorted((S/'data/records').glob('*.json'))}
new={p.stem:rd(p) for p in sorted((P/'records').glob('*.json'))}
ck(len(oldhash)==512 and len(new)==18 and len(current)==530,'512 + 18 = 530 actual records')
for name,h in oldhash.items(): ck(sha(S/'data/records'/name)==h,'old record unchanged '+name)
for rid,r in current.items():
    errs=validate_record(r); ck(not errs,'schema/semantics '+rid+(' '+str(errs) if errs else ''))
    pub=S/'dist/data/records'/f'{rid}.json'; ck(rd(pub)==r,'canonical/public equality '+rid)
for rid,r in new.items():
    ck(sha(P/'records'/f'{rid}.json')==sha(S/'data/records'/f'{rid}.json'),'new record bytes '+rid)
    ck(not r['quality']['requested_tasks'] and not any(v['eligible'] for v in eligibility(r).values()),'new training closed '+rid)
ck(sum(synthesis_route(r) for r in new.values())==2,'two synthesis routes')
ck(sum(r['record_type']=='procedure' for r in new.values())==8,'eight procedures')
ck(sum(r['record_type']=='observation' for r in new.values())==8,'eight observations')
counts.update(records=len(current),old_records_preserved=len(oldhash),new_records=len(new),new_routes=2,new_procedures=8,new_observations=8,operations=sum(len(r['operations']) for r in new.values()),materials=sum(len(r['materials']) for r in new.values()),measurements=sum(len(r['measurements']) for r in new.values()))
oldrecords=[r for rid,r in current.items() if rid not in new]; oldgroups=build_groups(oldrecords); groups=build_groups(list(current.values()))
for rid,g in oldgroups.items(): ck(groups[rid]==g,'old split group preserved '+rid)
ck(len({groups[rid] for rid in new})==1,'Morrison one split group')
elig={t:sum(eligibility(r)[t]['eligible'] for r in current.values()) for t in eligibility(next(iter(current.values())))}
oldelig={t:sum(eligibility(r)[t]['eligible'] for r in oldrecords) for t in elig}; ck(elig==oldelig,'all task counts unchanged')
counts['training_eligibility']=elig
for task in elig:
    export=bind(S/'dist/data/exports'/f'{task}.jsonl'); rows=[json.loads(x) for x in export.read_text(encoding='utf-8').splitlines() if x.strip()]
    expected={r['record_id']:training_view(r,task) for r in oldrecords if eligibility(r)[task]['eligible']}
    ck({x['record_id'] for x in rows}==set(expected),'export IDs '+task)
    for row in rows:
        rid=row['record_id']; value={k:v for k,v in row.items() if k not in {'group_id','split','record_sha256'}}
        ck(value==expected[rid],f'allowlisted export values {task} {rid}')
        ck(row['group_id']==groups[rid],f'export source group {task} {rid}')
        ck(row['record_sha256']==digest(current[rid]),f'export record digest {task} {rid}')
prom=rd(P/'promotion-manifest.json')
for asset in prom['public_assets']:
    p=S/'dist'/asset['public_path']; ck(sha(bind(p))==asset['sha256']==sha(P/'dist'/asset['public_path']),'public exact asset '+asset['public_path'])
    ck(p.suffix not in {'.pdf','.cif','.txt'} and 'source-render' not in str(p),'selected public asset type '+asset['public_path'])
ck(len(prom['public_assets'])==87,'87 public asset allowlist')
counts['public_assets']=len(prom['public_assets']); counts['selected_crops']=sum(a['kind']=='selected_original_scientific_crop' for a in prom['public_assets'])
regfile='dist/assets/chemical-registry/registry.json'; expected=rd(B/regfile); add=rd(P/'molecules/registry-additions.json')
expected=copy.deepcopy(expected)
for ent in add['entries']:
    e=copy.deepcopy(ent); e['published']=True; expected['entries'].append(e)
actual=rd(S/regfile); ck(expected==actual,'registry exact append with published metadata only')
reg={e['id']:e for e in actual['entries']}; counts['new_registry_entries']=len(add['entries'])
bf='dist/assets/chemical-registry/bindings.json'; expected=copy.deepcopy(rd(B/bf)); ba=rd(P/'molecules/bindings-additions.json')
for key in ['recordBindings','bindingNotes','sourceRecordSha256']: expected[key].update(ba.get(key,{}))
initial=rd(O/'bindings-before-empty-completion.json'); ck(expected==initial,'pre-empty binding merge exact')
delta=rd(O/'empty-binding-delta.json'); ck(sha(O/'bindings-before-empty-completion.json')==delta['before_sha256'],'empty correction before hash')
for rid in delta['records']:
    ck(rid in new and not current[rid]['materials'],'empty record has no materials '+rid)
    expected['recordBindings'][rid]={};expected['bindingNotes'][rid]={}
actual=rd(S/bf); ck(expected==actual,'exact seven-empty-map correction only'); ck(sha(S/bf)==delta['after_sha256'],'empty correction final hash')
ck(set(actual['recordBindings'])==set(current),'bindings complete record coverage')
for rid,r in new.items():
    ck(set(actual['recordBindings'][rid])=={m['id'] for m in r['materials']},'exact material slot map '+rid)
    for m in r['materials']:
        note=actual['bindingNotes'][rid][m['id']]; eid=actual['recordBindings'][rid][m['id']]
        ck(eid in reg and note['registry_id']==eid,'entry exists '+rid+' '+m['id'])
        ck(ptr(r,note['json_pointer'])==m==note['canonical_identity'],'canonical material identity '+rid+' '+m['id'])
        ck(note['canonical_record_sha256']==sha(bind(N/'canonical-proposal/v2'/f'{rid}.json')),'historical audited-input binding hash '+rid+' '+m['id'])
        ck(actual['sourceRecordSha256'][rid]==sha(S/'data/records'/f'{rid}.json'),'effective promoted binding hash '+rid+' '+m['id'])
        for q in note['quantity_links']: ck(ptr(r,q['json_pointer'])==q['quantity'],'exact slot quantity '+rid+' '+q['json_pointer'])
sf='dist/assets/chemical-registry/solution-components.json'; expected=copy.deepcopy(rd(B/sf)); sa=rd(P/'molecules/solution-components-additions.json'); expected['contexts']+=sa['contexts']; ck(rd(S/sf)==expected,'solution contexts append only')
for c in sa['contexts']:
    r=new[c['record_id']]
    for x in c['components']: ck(x['material_id'] in {m['id'] for m in r['materials']} and x['registry_id'] in reg,'stock component identity '+c['id']+' '+x['material_id'])
counts['solution_contexts']=len(sa['contexts']);counts['solution_components']=sum(len(x['components']) for x in sa['contexts'])
pf='dist/assets/chemical-registry/product-contexts.json'; expected=copy.deepcopy(rd(B/pf)); pa=rd(C/'product-contexts-additions.json')
for k in ['recordContexts','sourceNotices']: expected[k].update(pa[k])
ck(rd(S/pf)==expected,'product contexts append only')
for rid,cs in pa['recordContexts'].items():
    for c in cs:
        p=ptr(new[rid],c['canonical_product_pointer']); ck(p['sample_id']==c['sample_id'] and p['phase']==c['phase'] and p['morphology']==c['morphology'],'product scope '+rid+' '+c['sample_id'])
        ck(c['registry_id'] in reg and c['atomic_model'] is False and c['training_eligible'] is False,'symbolic product qualification '+rid+' '+c['sample_id'])
counts['product_contexts']=sum(len(v) for v in pa['recordContexts'].values())
display=copy.deepcopy(rd(B/'data/measurement-display.json'))
for kind,key in [('structures','record_structural_measurement_ids'),('properties','record_property_measurement_ids')]:
    addition=rd(P/f'record-{kind}-measurements.json'); ck(set(addition)==set(new),'scoped '+kind+' record IDs')
    for rid,ids in addition.items(): ck(set(ids)<={m['id'] for m in new[rid]['measurements']},'valid '+kind+' IDs '+rid)
    display[key].update(addition); counts[kind+'_measurements']=sum(map(len,addition.values()))
ck(rd(S/'data/measurement-display.json')==display,'measurement classification append only');ck(rd(S/'dist/data/measurement-display.json')==display,'public classification identical')
reader=copy.deepcopy(rd(P/'reader/morrison2017.json'))
reader['presentation_gates']['site_integration']=True
reader['publication_status']='Source-reviewed contribution integrated locally; browser and live release tracked separately.'
reader['audit_details']['promotion_audit_sha256']=sha(A/'promotion-delta-audit.json');reader['audit_details']['symbolic_product_context_audit_sha256']=sha(A/'product-context-audit.json')
ck(rd(S/'data/paper-reviews/morrison2017.json')==reader,'reader scientific bytes restored after only integration-status metadata')
public_reader=copy.deepcopy(reader);public_reader['review_scope_label']=source_review_scope(reader)['label']
ck(rd(S/'dist/data/paper-reviews/morrison2017.json')==public_reader,'reader public transport with derived review-scope label')
fieldcount=0
for sec in reader['reader_sections']:
    expectedmap={rid:set() for rid in new}
    for item in sec['items']:
        for f in item.get('facts',[]):
            if 'canonical_quantity' in f:
                fieldcount+=1;ck(ptr(new[f['canonical_record_id']],f['json_pointer'])==f['canonical_quantity'],'reader quantity '+f['id'])
        for l in item.get('canonical_links',[]):
            ck(l['record_id'] in new and ptr(new[l['record_id']],l['json_pointer']) is not None,'reader pointer '+item['id']+' '+l['json_pointer'])
        for l in item.get('canonical_links',[]):
            if l['json_pointer'].startswith('/measurements/'):
                expectedmap[l['record_id']].add(ptr(new[l['record_id']],'/'.join(l['json_pointer'].split('/')[:3]))['id'])
    if sec['id'] in ['structures','properties']:
        actualmap=rd(P/f"record-{sec['id']}-measurements.json")
        ck({k:set(v) for k,v in actualmap.items()}==expectedmap,'display map directly from reader '+sec['id'])
counts['reader_exact_fields']=fieldcount
# Reconstruct every source-code change from the saved previous bytes.
cd=rd(O/'code-delta.json'); files=set(x['file'] for x in cd['changes'])|{x for x in cd['cache_revision_files'] if not x.endswith('.html')}
for rel in sorted(files):
    before=bind(B/rel).read_text(encoding='utf-8'); rebuilt=before
    for d in cd['changes']:
        if d['file']==rel:
            ck(rebuilt.count(d['before'])==d['occurrences'],'exact code replacement multiplicity '+rel+' '+d['before']);rebuilt=rebuilt.replace(d['before'],d['after'])
    if rel in cd['cache_revision_files']:rebuilt=rebuilt.replace('0.25.0-r1','0.26.0-r1')
    if rel=='scripts/build_dataset.py':
        ld=rd(O/'reader-link-label-delta.json');ck(sha(bind(O/'build-dataset-before-reader-label.py'))==ld['before_sha256'],'reader label preserved pre-correction hash')
        ck(rebuilt== (O/'build-dataset-before-reader-label.py').read_text(encoding='utf-8'),'reader label snapshot equals reconstructed initial code')
        ck(rebuilt.count(ld['before'])==1,'reader label correction single occurrence');rebuilt=rebuilt.replace(ld['before'],ld['after'])
        ck(sha(S/rel)==ld['after_sha256'],'reader label corrected final hash')
    ck(bind(S/rel).read_text(encoding='utf-8')==rebuilt,'code delta complete '+rel)
css=rd(O/'mobile-provenance-wrap-delta.json');oldcss=bind(B/css['path']);actualcss=bind(S/css['path'])
ck(sha(oldcss)==css['before_sha256'] and sha(actualcss)==css['after_sha256'],'mobile CSS before/after hashes')
ck(actualcss.read_text(encoding='utf-8')==oldcss.read_text(encoding='utf-8')+css['addition'],'mobile CSS exact provenance wrapping only')
apparatus=N/'visuals/apparatus/morrison2017-protocol.mjs'; ck(sha(bind(S/'dist/morrison2017-protocol.mjs'))==sha(bind(apparatus)),'audited apparatus bytes retained')
appAudit=rd(N/'visuals/apparatus-independent-audit/independent-audit.json');ck(appAudit['status']=='passed','distinct apparatus scientific audit passed')
# Check actual generated pages and hubs contain all new records and their source links.
for rid in new:
    hp=bind(S/'dist/records'/f'{rid}.html'); txt=hp.read_text(encoding='utf-8')
    ck('paper-review.html?id=morrison2017' in txt,'record reader hyperlink '+rid)
    ck('Source document review' in txt,'record neutral reviewed link '+rid)
    ck('C:\\Users' not in txt and '[local path redacted]' not in txt,'record no private filesystem paths '+rid)
    for m in new[rid]['measurements']:
        row=measurement_table([m]).split('<tbody>',1)[1].split('</tbody>',1)[0]
        ck(row in txt,'generated measurement value/sample/source row retained '+rid+' '+m['id'])
inv=rd(S/'data/inventory-summary.json'); ck(rd(S/'dist/data/inventory-summary.json')==inv,'inventory public equality')
ck(inv['summary']['canonical_records']==530 and inv['summary']['synthesis_route_variant_records']==103 and inv['summary']['public_material_hubs']==44,'actual inventory headline counts')
ck(inv['training_eligibility']==elig,'inventory training counts')
ck(inv['summary']['full_corpus_recipe_count'] is None and inv['summary']['full_corpus_distinct_synthesized_material_count'] is None,'unknown full corpus totals preserved')
routeids={rid for rid,r in new.items() if synthesis_route(r)};contributing=[]
for p in (S/'dist/data/materials').glob('*.json'):
    hub=rd(p); present=set(hub['record_ids'])&set(new)
    if present:
        contributing.append(hub['formula']);ck(present==routeids,'two shell routes in hub '+hub['formula'])
        ck(set(hub['direct_record_ids'])&set(new)==(routeids if hub['formula']=='CdSe/CdS' else set()),'composite versus component route '+hub['formula'])
        want=routeids|set(reader['material_evidence_records'].get(hub['formula'],[]))
        ck({x['record_id'] for x in hub['evidence_records']} & set(new)==want,'reader-scoped evidence in hub '+hub['formula'])
ck(set(contributing)=={'CdSe/CdS','CdSe','CdS'},'only composite and two component hubs receive Morrison routes')
ri=rd(S/'dist/data/paper-review-index.json');mri=next(x for x in ri['papers'] if x['id']=='morrison2017')
ck(set(mri['record_ids'])==set(new) and mri['pages_read']==27 and mri['review_scope']=='supplied_main_and_matched_si','reader index all 18 records and 27 supplied pages')
baseinv=rd(B/'data/inventory-summary.json');ck(baseinv['training_eligibility']==inv['training_eligibility'],'stored baseline training counts unchanged')
for f in ['dataset-manifest.json','validation-report.json','materials-index.json','library-index.json','paper-review-index.json']:rd(S/'dist/data'/f)
for p in [O/'final-check-output.json',O/'browser-validation.json',O/'reader-label-rebuild-check.json',N/'correct_reader_link_label.py']:bind(p)
for p in [N/'import_reviewed_morrison.py',N/'complete_empty_bindings.py',N/'build_morrison_inventory.py',N/'build_and_check_site.py',O/'site-import-manifest.json',O/'validation.json',O/'build-check-output.json',S/'scripts/dataset_lib.py',S/'scripts/schema_definition.py',S/'scripts/build_atlas.py',S/'scripts/build_inventory.py',S/'scripts/build_paper_reviews.py',S/'dist/chemical-viewer.mjs',S/'dist/source-evidence.mjs',S/'dist/quantity-value.mjs',Path(__file__)]:bind(p)
result={'at':datetime.now(timezone.utc).isoformat(),'status':'passed' if all(c['ok'] for c in checks) else 'open_findings','counts':counts,'checks':len(checks),'failures':[c['label'] for c in checks if not c['ok']],'bound_files':bound}
(A/'integration-mechanical-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='bound_files'},ensure_ascii=False,indent=2))
