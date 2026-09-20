"""Independent root consistency audit after complete reader prose/source-scope review."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json
B=Path(__file__).resolve().parent
def read(p): return json.loads(p.read_text(encoding='utf8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def check(ok,label):
    checks.append({'check':label,'passed':bool(ok)})
def ptr(obj,pointer):
    if pointer=='':return obj
    for key in pointer.strip('/').split('/'):
        key=key.replace('~1','/').replace('~0','~')
        obj=obj[int(key)] if isinstance(obj,list) else obj[key]
    return obj
rp=B/'public-review-proposal/gu2004.json'; r=read(rp)
drafts={p.stem:read(p) for p in (B/'canonical-drafts').glob('*.json')}
inv=read(B/'source-inventory.json'); sf=read(B/'source-facts.json')
units={u['id']:u for u in inv['units']}; facts={f['id']:f for f in sf['facts']}
assets={a['id']:a for a in read(B/'reader-assets/crop-manifest.json')['assets']}
items=[i for sec in r['reader_sections'] for i in sec['items']]
byid={i['id']:i for i in items}; bound={}
def bind(p):
    p=Path(p); bound[str(p)]=sha(p)
for p in [rp,B/'source-inventory.json',B/'source-facts.json',B/'source-scientific-audit.json',B/'canonical-records-audit.json',B/'canonical-record-manifest.json',B/'reader-assets/crop-manifest.json',B/'public-review-proposal/reader-bindings-proposal.json',B/'public-review-proposal/source-item-coverage.json',B/'public-review-proposal/canonical-measurement-coverage.json',B/'public-review-proposal/proposal-validation.json']+list((B/'canonical-drafts').glob('*.json')):bind(p)
ca=read(B/'canonical-records-audit.json')
for rel,h in ca['bound_record_files'].items():check(sha(B/'canonical-drafts'/rel)==h,'Frozen independently audited record '+rel)
for role,d in inv['source_documents'].items():
    bind(d['path']);check(sha(Path(d['path']))==d['sha256'],'Current source bytes '+role)
    rd=next(x for x in r['documents'] if x['role']==role)
    check(rd['sha256']==d['sha256'] and rd['page_count']==d['page_count'] and all(p['text_read'] and p['visual_review'] for p in rd['pages']),'Source scope and page coverage '+role)
check(len(items)==len(byid)==138,'138 unique reader items')
check([s['id'] for s in r['reader_sections']]==['precursors','protocol','structures','properties','intuition','sources'],'Five academic sections and source appendix')
check(set(u for i in items for u in i['source_audit_unit_ids'])==set(units),'All 126 source units covered exactly as set')
check(set(f for i in items for f in i['source_fact_ids'])==set(facts),'All 95 source facts have reader links')
expected={}
for rid,d in drafts.items():
    for ix,m in enumerate(d['measurements']):expected[(rid,f'/measurements/{ix}/value')]=m['value']
    for ix,o in enumerate(d['operations']):
        for key,q in o['parameters'].items():expected[(rid,f'/operations/{ix}/parameters/{key}')]=q
    for ix,m in enumerate(d['materials']):
        for key,q in m['quantities'].items():expected[(rid,f'/materials/{ix}/quantities/{key}')]=q
seen=set(); linkedops=set(); seenfacts=[]
for i in items:
    check(i['training_eligible'] is False and i['sample_scope']['physical_batch_id'] is None,'No invented admission or physical batch '+i['id'])
    check(bool(i['text']) and bool(i['evidence']) and bool(i['canonical_links']),'Readable source-linked content '+i['id'])
    for e in i['evidence']:
        check(e['source_id']=='gu2004' and 1<=e['pdf_page']<=inv['source_documents'][e['document_role']]['page_count'],'Valid source locator '+i['id'])
    for link in i['canonical_links']:
        value=ptr(drafts[link['record_id']],link['json_pointer'])
        check(value is not None,'Canonical pointer '+i['id']+' '+link['json_pointer'])
        parts=link['json_pointer'].strip('/').split('/')
        if parts[0]=='operations':linkedops.add((link['record_id'],int(parts[1])))
    for link in i['sample_scope']['canonical_sample_links']:
        v=ptr(drafts[link['record_id']],link['json_pointer'])
        check(v['sample_id']==link['sample_id'] and v['source_sample_label']==link['source_label'] and v['batch_id'] is None,'Source sample pointer '+i['id'])
    for f in i['facts']:
        key=(f['canonical_record_id'],f['json_pointer']);seen.add(key);seenfacts.append(f['id'])
        q=ptr(drafts[key[0]],key[1])
        if key[1].startswith('/measurements/') and key[1].count('/')==2:
            seen.remove(key);seen.add((key[0],key[1]+'/value'));q=q['value']
        check(q==f['canonical_quantity'],'Full quantity/status/evidence unchanged '+f['id'])
        check(f['unit']==q.get('unit') and f['status']==q['status'] and f['approximate']==q.get('approximate',False),'Display unit/status/approximation '+f['id'])
        if q.get('value') is not None:check(f['value']==q['value'],'Displayed reported value '+f['id'])
        elif q.get('minimum') is None and q.get('maximum') is None:check(f['value']=='Not reported' and q['value'] is None,'Unknown has explicit label and canonical null '+f['id'])
        else:
            display=(str(q['minimum'])+'–'+str(q['maximum'])) if q.get('minimum') is not None else ('< ' if q.get('maximum_exclusive') else '≤ ')+str(q['maximum'])
            check(f['value']==display,'Displayed source range/bound '+f['id'])
        check(f['training_eligible'] is False,'Reader fact not admitted by display '+f['id'])
    for a in i.get('original_assets',[]):
        source=assets[a['id']]
        check(a['public_asset_sha256']==source['sha256'] and Path(a['public_asset']).name==Path(source['path']).name,'Item original-asset binding '+i['id']+' '+a['id'])
check(seen==set(expected) and len(seenfacts)==len(set(seenfacts))==224,'All 224 distinct canonical quantities/context values rendered')
check(linkedops=={(rid,i) for rid,d in drafts.items() for i in range(len(d['operations']))},'All 33 operations linked')
for a in assets.values():bind(a['path']);check(sha(Path(a['path']))==a['sha256'],'Original unchanged crop '+a['id'])
assetitems=[a for category in ['figures','tables','schemes','equations','source_notes'] for a in r[category]]
check({a['public_asset'] for a in assetitems}=={a['public_asset'] for i in items for a in i.get('original_assets',[])},'Gallery and reader expose same 12 original assets')
for a in assetitems:
    source=next(s for s in assets.values() if s['sha256']==a['public_asset_sha256'])
    ap=a['asset_provenance']
    check(ap['source_sha256']==source['source_sha256'] and ap['source_pdf_page']==source['pdf_page'] and a['document_role']==source['source_role'],'Original asset source identity '+a['id'])
    for sl in a['canonical_sample_links']:
        check(sl['sample_id'] in {p['sample_id'] for p in drafts[sl['record_id']]['products']},'Gallery source sample '+a['id']+' '+sl['sample_id'])
check(len(r['referenced_methods'])==26 and sum(x['inspection_status']=='not_inspected_in_this_extraction' for x in r['referenced_methods'])==25,'26 citations/internal notes; 25 external works not claimed read')
check(len(r['tables'])==1 and r['tables'][0]['row_count']==6,'Six XRF software rows retained')
check('gu-2004-fept-control' not in r['material_evidence_records']['CdS'],'FePt-only control not assigned to CdS hub')
check(all(x in drafts for a in r['material_evidence_records'].values() for x in a),'Material evidence record IDs valid')
check(all(x in assets for a in r['material_original_asset_ids'].values() for x in a),'Material asset IDs valid')
check(r['route_evidence_contexts']['gu-2004-heterodimer']==[x for x in r['route_evidence_contexts']['gu-2004-heterodimer'] if x in drafts],'All route context IDs valid')
check('100 Oe' in byid['figure-s3']['text'] or any('100 Oe' in x for x in byid['figure-s3']['notes']),'SI control field nontransfer note explicit')
check('SAED' in byid['figure-1d']['text'] or 'diffraction' in byid['figure-1d']['text'].lower(),'Actual final SAED reader item present')
manual=[
'All 138 reader titles, prose and notes read; first four sections reviewed before root audit script, then intuition and source appendix. Checked against previously fully read five-page source bundle and frozen independent source/canonical audits.',
'Precursor grades, 80.5% CdCl2 hydration/assay ambiguity, technical reagents, DI dissolution versus unspecified recrystallization water, staged charges, about-five-minute preheat, unreported ether boiling point and correct retained workup fractions preserved.',
'Original Figure1D is final-product SAED. The separately claimed SAED of FePt1 is not supplied. TEM scales, particle/domain sizes, failed intermediate isolation and absence of lattice coordinates/atomic interface remain scoped.',
'XRF main ratio and SI six-row mol%/energies remain conflicting representations; blank Rh and Type cells not zeros, Si/Rh not product dopants. XRF not XRD.',
'Final 100Oe and 5K magnetism, separate unreported-field FePt control, author-model parameters, optical peaks/shoulder/QY/reference standard, 365nm excitation and unknown photograph lamp wavelength not mixed.',
'Source labels and canonical product contexts stay separate from exact physical batches; no extra synthesis replicates inferred from figures, controls or model records.',
'Five academic reader sections and all references, original excerpts, source limitations and material-component context notes are retained. Public UI behavior is not approved by this private source audit.'
]
result={'schema':'mattersyn.reader-source-audit.v1','source_id':'gu2004','auditor':'/root','author':'/root/peng1998_reader_assets','at':datetime.now(timezone.utc).isoformat(),'status':'passed' if all(c['passed'] for c in checks) else 'failed','scope':'Independent reader scientific, sample/pointer, quantity and original-byte review. Runtime/integration/publication gates separate.','reader_sha256':sha(rp),'crop_manifest_sha256':sha(B/'reader-assets/crop-manifest.json'),'bound_files':bound,'counts':{'reader_items':len(items),'source_units':len(units),'source_facts':len(facts),'typed_reader_facts':len(seenfacts),'operations':len(linkedops),'original_assets':len(assets)},'manual_review':manual,'checks':checks,'check_count':len(checks),'open_findings':[c for c in checks if not c['passed']]}
(B/'reader-source-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(B/'reader-source-audit.md').write_text('# Gu 2004 reader source audit\n\nStatus: '+result['status']+'. Root independent of reader author.\n\n'+'\n\n'.join(manual)+'\n\n'+str(len(checks))+' mechanical consistency checks. Exact inputs are bound in the JSON report. Runtime, integration and deployment remain separate gates.\n',encoding='utf8')
print(json.dumps({k:result[k] for k in ['status','counts','check_count','open_findings']}))
