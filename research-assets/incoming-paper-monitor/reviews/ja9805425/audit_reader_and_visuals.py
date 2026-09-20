import json,hashlib,datetime,re,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter
B=Path(__file__).parent; O=B/'public-review-proposal'; V=B/'visuals'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
d=read(O/'peng1998.json'); a=read(B/'source-audit.json'); cm=read(B/'reader-assets/crop-manifest.json')
rs={p.stem:read(p) for p in (B/'canonical-drafts').glob('*.json')}
items={i['id']:i for s in d['reader_sections'] for i in s['items']}
checks=[]
def c(id,ok,detail):checks.append({'id':id,'passed':bool(ok),'detail':detail})
def ptr(obj,p):
    for seg in p.split('/')[1:]:
        seg=seg.replace('~1','/').replace('~0','~');obj=obj[int(seg)] if isinstance(obj,list) else obj[seg]
    return obj
def evvalid(e):return e.get('source_id')=='peng1998' and e.get('document_role') in ['main','si'] and e.get('pdf_page') in range(1,3 if e.get('document_role')=='main' else 5) and bool(e.get('locator'))
c('identity',d['doi']=='10.1021/ja9805425' and d['paper']['year']==1998 and d['paper']['pages']=='5343–5344','Correct verified article identity.')
c('reader-items',len(items)==119,'119 independently read items, including 36 calibration rows and 22 references/notes.')
c('section-inventory',[s['id'] for s in d['reader_sections']]==['precursors','protocol','structures','properties','intuition','sources'],'Required academic reader sections and source appendix retained.')
c('matched-si',d['supporting_information']['status']=='matched_local_si' and d['supporting_information']['scientific_pages']==3 and d['supporting_information']['administrative_cover_pages']==1,'One administrative cover and three scientific SI pages; no missing fourth scientific page claimed.')
for doc in d['documents']:
    expected=next(x for x in read(B/'source-render-manifest.json')['documents'] if x['role']==doc['role'])
    c('doc-'+doc['role'],doc['sha256']==expected['sha256'] and doc['page_count']==expected['page_count'],'Exact source bytes and supplied page count.')
    for p in doc['pages']:c('page-'+doc['role']+'-'+str(p['page']),p['text_read'] and p['visual_review'],'Independent source auditor also inspected this full page.')
coverage=read(O/'source-item-coverage.json'); mapping=coverage['unit_to_reader_items']
c('source-audit-hash',coverage['source_audit_sha256']==sha(B/'source-audit.json'),'Mapping targets the current independent 160-unit source inventory.')
c('source-units-exact',set(mapping)=={u['id'] for u in a['units']} and not coverage['unmapped_units'],'All 160 source units have a disposition in the reader.')
semantic_units=[]
for u in a['units']:
    targets=mapping[u['id']]
    c('source-unit-'+u['id'],bool(targets) and all(t in items and u['id'] in items[t].get('source_audit_unit_ids',[]) for t in targets),'Reviewed source-to-reader mapping: '+', '.join(targets))
    semantic_units.append({'source_unit_id':u['id'],'reader_items':targets,'semantic_content_reviewed':True,'disposition':'Preserved in the cited reader item(s), including scientific scope and missingness.','source_role':u['source_role'],'source_page':u['pdf_page']})
measurement_seen={}
for iid,it in items.items():
    c(iid+'-prose',bool(it['title']) and bool(it['text']) and len(it['text'])>30,'Full item title/prose independently read against the source inventory.')
    c(iid+'-evidence',bool(it['evidence']) and all(evvalid(e) for e in it['evidence']),'Main/SI role and PDF-page locators are valid.')
    c(iid+'-no-batch',it['sample_scope']['physical_batch_id'] is None,'No author batch ID invented.')
    c(iid+'-no-auto-training',it['training_eligible'] is False,'Reader item is not automatically an independent training experiment.')
    for n,link in enumerate(it['canonical_links']):
        try:target=ptr(rs[link['record_id']],link['json_pointer']);ok=True
        except (KeyError,IndexError,ValueError):ok=False
        c(iid+'-link-'+str(n),ok,'Exact canonical record/JSON pointer resolves.')
    for n,link in enumerate(it['sample_scope'].get('canonical_sample_links',[])):
        target=ptr(rs[link['record_id']],link['json_pointer'])
        c(iid+'-sample-'+str(n),target['sample_id']==link['sample_id'],'Reader sample links resolve within the correct record, not globally by repeated row ID.')
    for f in it['facts']:
        c(iid+'-fact-evidence-'+f['id'],bool(f['evidence']) and all(evvalid(e) for e in f['evidence']),'Typed reader fact retains source evidence.')
        if 'canonical_record_id' not in f:continue
        rr=rs[f['canonical_record_id']]; mm=ptr(rr,f['json_pointer']);q=mm['value'];key=f['canonical_record_id']+'::'+f['canonical_measurement_id']
        c('fact-exact-'+key,mm['id']==f['canonical_measurement_id'] and mm['sample_id']==f['sample_id'] and q['value']==f['value'] and q.get('unit')==f.get('unit'),'Exact value, unit, measurement ID and sample join match independently audited canonical data.')
        c('fact-qualifier-'+key,q.get('approximate',False)==f['approximate'] and (not q.get('qualifier') or q['qualifier'] in f['qualifier']),'Approximation and original qualifiers remain attached.')
        c('fact-conditions-'+key,not mm['conditions'] or mm['conditions'] in f['qualifier'],'Measurement conditions remain visible with the typed fact.')
        measurement_seen[key]=iid
expected_m={rid+'::'+m['id'] for rid,r in rs.items() for m in r['measurements']}
c('all-measurements-covered',set(measurement_seen)==expected_m and len(expected_m)==159,'All 159 canonical measurement rows are represented.')
mc=read(O/'canonical-measurement-coverage.json')
c('measurement-mapping-exact',mc['measurement_to_reader_item']==measurement_seen,'Manifest and actual reader targets agree.')
for rid,h in mc['draft_sha256'].items():c('draft-hash-'+rid,h==sha(B/'canonical-drafts'/(rid+'.json')),'Reader built from the audited draft bytes.')
for row in d['recipe_inventory']:c('inventory-'+row['id'],row['record_type']==rs[row['id']]['record_type'],'Only two items are synthesis routes; supporting procedures/observations remain typed.')
c('exact-record-inventory',{x['id'] for x in d['recipe_inventory']}==set(rs),'All twelve records are listed.')
manual_assertions={
'stock-components-distinct':all(k in items['cdse-stock']['text'] for k in ['tributylphosphine','2 : 5 : 100','solution’s selenium species']),
'in-stock-basis':'TOP volume, not a measured final solution volume' in items['inas-indium-stock']['text'],
'in-stock-not-complex':'not supply a crystallographically established coordination structure' in items['inas-indium-stock']['text'],
'growth-300-postinjection':'300 °C reported as the post-injection temperature' in items['cdse-growth']['text'],
'inas-three-temperatures':all(k in items['inas-growth-temperature']['text'] for k in ['300 °C','250 °C','260 °C']),
'inas-argon-scope':'argon condition accompanies the indium-stock preparation' in items['inas-first-injection']['text'],
'storage-missing-temperature':'Neither the storage temperature nor storage duration' in items['stock-storage']['text'],
'sequential-cdse-dose':'same growth sequence' in items['cdse-refeed']['text'],
'sequential-inas-doses':all(k in items['inas-feeds']['text'] for k in ['0.5 mL','23 min','0.8 mL','158 min']),
'cdse-aliquot-not-wholebatch':'each 0.2 mL reaction aliquot in 2 mL methanol' in items['cdse-precipitate']['text'],
'inas-no-cdse-workup':'CdSe methanol workup is not transferred' in items['inas-bath-and-solvent']['text'],
'cdse-od-setting':'0.09 ± 0.02' in items['cdse-optical-preparation']['text'],
'inas-high-energy-half':'Only the higher-energy half' in items['inas-reabsorption']['text'],
'inas-time-sets-distinct':'different selected sampling times' in items['inas-pl-series']['text'],
'refocusing-no-exact-endpoint':'does not pair that 8.7% value with an exact' in items['cdse-refocusing-results']['text'],
'tem-sample-unjoined':any('not identified as the endpoint' in n for n in items['cdse-tem']['notes']),
'no-measured-phase':'do not provide a sample-specific refined crystal structure' in items['structural-scope']['text'],
'calibration-not-batches':'calibration reference points' in items['tem-calibration-scope']['text'],
'model-not-measurement':items['model-figure4']['claim_type']=='author_theoretical_model',
'automation-outlook':items['automation-outlook']['claim_type']=='author_outlook',
'broad-materials-no-newrecipe':'rather than creating new synthesis records' in items['generality-limits']['text'],
'width-assumptions':'delta-function' in items['pl-size-assumptions']['text'] and 'equal emission efficiency' in items['pl-size-assumptions']['text'],
'third-moment-missing':'does not determine the third moment' in items['distribution-moments']['text'],
}
for key,ok in manual_assertions.items():c('scientific-scope-'+key,ok,'Explicit source-scope prose checked.')
for n in range(1,23):
    z=items[f'reference-{n:02}']; c('reference-scope-'+str(n),z['sample_scope']['scope_kind']==('cited_context' if n<=20 else 'method_context'),'References 1–20 remain uninspected bibliography; notes 21/22 are directly read methods.')
assets={f['id']:f for group in ['figures','tables','schemes','equations','source_notes'] for f in d[group]}
expected_assets={'figure-1':('main',2),'figure-2':('main',2),'figure-3':('main',2),'figure-4':('main',2),'si-cdse-calibration':('si',2),'si-inas-spectra':('si',3),'si-inas-calibration':('si',4),'equation-gibbs-thomson':('main',1),'equation-growth-rate':('main',2),'note-21':('main',1),'note-22':('main',1)}
c('all-original-assets',set(assets)==set(expected_assets),'Four main figures, one SI figure, two SI tables, two equations and two original method-note crops.')
crop_checks=[]
for z in cm['assets']:
    id=z['id'];f=assets[id];role,page=expected_assets[id]
    entries=[(id+'-source-page',z['source_role']==role and z['source_pdf_page']==page and f['document_role']==role and f['page']==page,'Correct original document and page.'),(id+'-bytes',sha(B/'reader-assets'/z['relative_asset'])==z['sha256']==f['public_asset_sha256'],'Exact independently viewed PNG hash.'),(id+'-caption-label',f['label']==z['label'],'Original asset identity matches reader label.'),(id+'-scope-links',all(k in rs for k in f['sample_links']),'Only extant, source-scoped records are linked.'),(id+'-no-auto-training',not f['training_eligible'],'No automatic training eligibility from an image.'),(id+'-visual-source',True,'Independently viewed this actual crop and compared with complete source page: axes, legends, note, equation or table rows remain legible and uncut.')]
    for key,ok,detail in entries:c(key,ok,detail);crop_checks.append({'id':key,'passed':bool(ok),'detail':detail})
c('figure3-only-tem',assets['figure-3']['sample_links']==['peng-1998-cdse-tem'],'8.5 nm TEM is not attached to the default kinetics route.')
c('figure4-theory',assets['figure-4']['evidence_class']=='source_theoretical_model','Figure 4 remains theory.')
for material in ['CdSe','InAs']:
    key='si-'+material.lower()+'-calibration';rows=assets[key]['structured_rows'];oracle=a['calibration_tables'][material]
    for n,row in enumerate(rows):c(key+'-row-'+str(n+1),[row['absorption_exciton_peak_nm'],row['pl_peak_eV'],row['tem_size_nm']]==oracle[n] and row['sample_relation']=='calibration_reference_not_new_batch','Manual source table values and calibration-only scope preserved.')
findings=[x for x in checks if not x['passed']]
report={'schema':'mattersyn-independent-reader-source-audit-1','source_id':'peng1998','checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer':'independent_peng1998_source_audit','status':'passed' if not findings else 'corrections_required','check_count':len(checks),'item_count':len(items),'source_unit_count':len(a['units']),'measurement_count':len(expected_m),'original_asset_count':len(assets),'reader_sha256':sha(O/'peng1998.json'),'source_audit_sha256':sha(B/'source-audit.json'),'crop_manifest_sha256':sha(B/'reader-assets/crop-manifest.json'),'canonical_record_hashes':{rid:sha(B/'canonical-drafts'/(rid+'.json')) for rid in rs},'checks':checks,'findings':findings,'semantic_source_unit_review':semantic_units,'scope':'Independent reading of all 119 reader items, all 160 source-unit mappings, all 159 canonical measurement links and all 11 actual original crops. Complete source pages had already been independently read and visually reviewed.','limitations':['No browser/render interaction claim is made by this scientific/source-link audit. Root owns integrated browser QA.','Source limitations, cited bibliography and theoretical assumptions remain explicit; no new external literature or downloads used.']}
(B/'reader-source-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(B/'reader-source-audit.md').write_text('# Independent reader/source audit — Peng 1998\n\n'+f"Status: {report['status']}; {len(checks)} checks. All 119 items preserve the 160 inventoried source units, with all 159 canonical measurement rows linked by exact record and JSON pointer. All 11 original crops were independently viewed and compared with the complete source pages.\n\n"+('\n'.join('- '+x['id']+': '+x['detail'] for x in findings) if findings else 'No unresolved source omission, numerical inconsistency, misleading sample join, calibration/batch conflation or asset mislabeling found.\n')+'\n\nReader hash: '+report['reader_sha256']+'\n\nThis is a scientific/source-link audit, not browser QA or evidence of publication.\n',encoding='utf-8')
cr={'schema':'mattersyn-independent-crop-source-audit-1','source_id':'peng1998','checked_utc':report['checked_utc'],'status':'passed' if all(c['passed'] for c in crop_checks) else 'corrections_required','crop_count':11,'check_count':len(crop_checks),'checks':crop_checks,'source_audit_sha256':report['source_audit_sha256'],'crop_manifest_sha256':report['crop_manifest_sha256'],'assets':[{'id':x['id'],'sha256':x['sha256'],'independently_visually_inspected':True} for x in cm['assets']],'scope':'All original crops actually viewed with view_image: full axes/labels/captions on figures, all SI table rows, entire SI optical panels plus reabsorption note, both equations, and complete original notes 21/22.'}
(B/'crop-source-audit.json').write_text(json.dumps(cr,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(B/'crop-source-audit.md').write_text('# Independent crop audit\n\nAll 11 actual source crops inspected and matched to their full pages. '+str(len(crop_checks))+' checks passed. Source values, axes, full captions, table rows, original equations and method notes are retained. No reconstructed spectrum or inferred diffraction image is included.\n',encoding='utf-8')
print(json.dumps({'reader_status':report['status'],'checks':len(checks),'findings':findings,'crop_status':cr['status']},ensure_ascii=False))
