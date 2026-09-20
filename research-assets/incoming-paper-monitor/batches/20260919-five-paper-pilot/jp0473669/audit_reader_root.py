"""Independent reader consistency audit, accompanying root's actual source/prose review.

This script checks bindings, not scientific truth by itself. The separate manual
scope below records what root actually read and viewed in the current review.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json
B=Path(__file__).resolve().parent
P=B/'public-review-proposal'
def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def value_sha(v): return hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def ptr(d,p):
    if not p or p=='/': return d
    for k in p.lstrip('/').split('/'):
        k=k.replace('~1','/').replace('~0','~')
        d=d[int(k)] if isinstance(d,list) else d[k]
    return d
checks=[]; bound={}
def check(ok,label): checks.append({'check':label,'passed':bool(ok)})
def bind(p):
    p=Path(p);bound[str(p)]=sha(p)

r=read(P/'ribeiro2004.json'); manifest=read(P/'reader-author-manifest.json')
drafts={p.stem:read(p) for p in (B/'canonical-drafts').glob('*.json')}
inv=read(B/'source-inventory.json'); sf=read(B/'source-facts.json')
units={u['id']:u for u in read(B/'canonical-source-unit-index.json')['units']}
facts={f['id']:f for f in sf['facts']}
assets={a['id']:a for a in inv['assets']}
items=[i for s in r['reader_sections'] for i in s['items']]; byid={i['id']:i for i in items}
fc=read(P/'canonical-field-coverage.json'); sc=read(P/'source-item-coverage.json')
for p in [P/'ribeiro2004.json',P/'reader-author-manifest.json',P/'canonical-field-coverage.json',P/'source-item-coverage.json',
          P/'reader-bindings-proposal.json',P/'proposal-validation.json',P/'reader-render-check.json',
          B/'source-inventory.json',B/'source-facts.json',B/'canonical-source-unit-index.json',
          B/'source-scientific-audit.json',B/'canonical-records-audit.json',B/'canonical-record-manifest.json',Path(__file__)]:
    bind(p)
for key in ['input_hashes','source_pdf_hashes','site_readonly_contract_hashes']:
    for p,h in manifest[key].items():
        bind(p);check(sha(p)==h,'Frozen author input '+str(p))
for name,h in manifest['output_hashes'].items():
    bind(P/name);check(sha(P/name)==h,'Frozen reader output '+name)
freeze=read(P/'reader-freeze-manifest.json');bind(P/'reader-freeze-manifest.json')
for name,h in freeze['files'].items():
    bind(P/name);check(sha(P/name)==h,'Final frozen package '+name)
ca=read(B/'canonical-records-audit.json')
for rid,h in ca['record_hashes'].items():
    p=B/'canonical-drafts'/(rid+'.json');bind(p)
    check(sha(p)==h==fc['record_hashes'][rid],'Independent canonical audit unchanged '+rid)
check(manifest['author']=='/root/backlog_eta','Reader author is distinct from root auditor')
check(len(items)==len(byid)==93,'93 distinct reader items')
check([s['id'] for s in r['reader_sections']]==['precursors','protocol','structures','properties','intuition','sources'],'Five academic sections plus source appendix')
check(r['supporting_information']['status']=='not_located_or_verified' and len(r['documents'])==1,'Main-only supplied scope, SI remains unverified')
check(r['documents'][0]['page_count']==6 and len(r['documents'][0]['pages'])==6,'Exactly six supplied main pages')
check(all(p['text_read'] and p['visual_review'] for p in r['documents'][0]['pages']),'Existing source-review page coverage carried through')
check(r['training_eligible'] is False and not r['source_review_promoted'],'Private reader does not grant training or publication')
check(r['presentation_gates']['molecular_bindings']=='pending' and r['presentation_gates']['apparatus_bindings']=='pending','Molecule/apparatus gates remain open')
check(set(u for i in items for u in i['source_audit_unit_ids'])==set(units),'All 101 inventory units linked')
check(set(f for i in items for f in i['source_fact_ids'])==set(facts),'All 63 source facts linked')
check(not sc['unmapped_units'] and not sc['unmapped_facts'],'Coverage map reports no unmapped source facts or units')
expected={};expected_ops=set();expected_materials=set();expected_samples=set()
for rid,d in drafts.items():
    for ix,m in enumerate(d['measurements']):expected[(rid,f'/measurements/{ix}/value')]=m['value']
    for ix,o in enumerate(d['operations']):
        expected_ops.add((rid,ix))
        for k,v in o['parameters'].items():expected[(rid,f'/operations/{ix}/parameters/{k}')]=v
        for k in ['environment','endpoint']:expected[(rid,f'/operations/{ix}/{k}')]=o[k]
    for ix,m in enumerate(d['materials']):
        expected_materials.add((rid,ix))
        for k,v in m['quantities'].items():expected[(rid,f'/materials/{ix}/quantities/{k}')]=v
    for ix,s in enumerate(d.get('stocks',[])):
        for k,v in s.get('concentrations',{}).items():expected[(rid,f'/stocks/{ix}/concentrations/{k}')]=v
    for ix,s in enumerate(d['products']):expected_samples.add((rid,ix))
visible={}; linkedops=set(); linkedmaterials=set(); linkedsamples=set()
for i in items:
    check(i['training_eligible'] is False and i['sample_scope']['physical_batch_id'] is None,'No invented physical batch or admission '+i['id'])
    check(bool(i['text']) and bool(i['evidence']) and bool(i['canonical_links']),'Readable prose with evidence and canonical links '+i['id'])
    for e in i['evidence']:
        check(e['source_id']=='ribeiro2004' and e['document_role']=='main' and 1<=e['pdf_page']<=6,'Scoped main locator '+i['id'])
    for link in i['canonical_links']:
        p=link['json_pointer'];rid=link['record_id']; ptr(drafts[rid],p)
        parts=p.strip('/').split('/')
        if len(parts)>1 and parts[0]=='operations':linkedops.add((rid,int(parts[1])))
        if len(parts)>1 and parts[0]=='materials':linkedmaterials.add((rid,int(parts[1])))
    spl=i['sample_scope']['canonical_sample_links']
    check(len(spl)==len({(s['record_id'],s['json_pointer']) for s in spl}),'Sample links deduplicated '+i['id'])
    for s in spl:
        q=ptr(drafts[s['record_id']],s['json_pointer'])
        check(q['sample_id']==s['sample_id'] and q.get('batch_id') is None,'Exact scoped product pointer '+i['id'])
        if 'source_label' in s:check(q['source_sample_label']==s['source_label'],'Source sample label unchanged '+i['id'])
        linkedsamples.add((s['record_id'],int(s['json_pointer'].split('/')[2])))
    for f in i['facts']:
        key=(f['canonical_record_id'],f['json_pointer']);q=ptr(drafts[key[0]],key[1])
        check(q==f['canonical_quantity'],'Exact quantity payload '+f['id'])
        ratio=key==('ribeiro-2004-hydrolysis','/operations/1/parameters/water_to_tin_relative_ratio')
        check((f['unit']==q.get('unit') or (ratio and f['unit']=='water:Sn²⁺; basis unreported')) and f['status']==q['status'] and f['approximate']==q.get('approximate',False),'Displayed unit, status and approximation '+f['id'])
        if ratio:
            check(q['value']==500 and q['raw_text']=='approximately 500:1' and f['value']=='500:1' and bool(f.get('presentation_note')),
                  'Source-reported relative ratio is faithfully formatted; basis remains unreported')
        elif q.get('value') is not None:check(f['value']==q['value'],'Exact reported display '+f['id'])
        elif q.get('minimum') is None and q.get('maximum') is None:check(f['value']=='Not reported','Null is explicit unknown '+f['id'])
        else:
            lo=q.get('minimum');hi=q.get('maximum')
            shown=f'{lo}–{hi}' if lo is not None and hi is not None else ('> ' if q.get('minimum_exclusive') else '≥ ')+str(lo) if lo is not None else ('< ' if q.get('maximum_exclusive') else '≤ ')+str(hi)
            check(f['value']==shown,'Exact displayed bound/range '+f['id'])
        check(f['training_eligible'] is False,'Fact display not training approval '+f['id'])
        check(key not in visible,'Visible typed field unique '+f['id']);visible[key]=f
    for a in i.get('original_assets',[]):
        src=next(s for s in assets.values() if s['sha256']==a['public_asset_sha256'])
        check(Path(a['public_asset']).name==Path(src['filename']).name,'Original asset byte/name mapping '+i['id'])
check(linkedops==expected_ops and len(linkedops)==13,'All 13 operations have exact reader pointers')
check(linkedmaterials==expected_materials and len(linkedmaterials)==13,'All 13 material slots linked')
check(linkedsamples==expected_samples and len(linkedsamples)==29,'All 29 canonical sample/context products exposed')
mapped={}
for link in fc['typed_field_to_reader'].values():
    key=(link['record_id'],link['json_pointer']); q=ptr(drafts[key[0]],key[1]);mapped[key]=link
    check(key in expected and link['reader_item_id'] in byid,'Canonical field has existing reader item '+str(key))
    check(value_sha(q)==link['canonical_value_sha256'],'Coverage map binds exact canonical value '+str(key))
    if link['rendering']=='typed_quantity':
        check(key in visible and visible[key]['canonical_quantity']==q,'Mapped field actually visible as typed fact '+str(key))
    else:
        check(link['rendering']=='source_context_prose' and isinstance(q.get('value'),str),'Inventory context is labeled prose, not a numerical measurement '+str(key))
        check(any(x['record_id']==key[0] and x['json_pointer'] in [key[1],key[1].rsplit('/',1)[0]] for x in byid[link['reader_item_id']]['canonical_links']),
              'Prose context has exact payload pointer '+str(key))
check(set(mapped)==set(expected) and len(mapped)==193,'All 193 typed canonical fields mapped without additions')
check(len(visible)==101 and sum(v['rendering']=='source_context_prose' for v in mapped.values())==92,'101 typed fact displays plus 92 retained prose contexts; no inflated measurement count')
for aid,a in assets.items():
    p=B/a['filename'];bind(p);check(sha(p)==a['sha256'],'Original crop bytes '+aid)
gallery=[a for k in ['figures','tables','schemes','equations','source_notes'] for a in r[k] if a.get('public_asset')]
check(len(r['schemes'])==1 and r['schemes'][0]['same_as_figure_id']=='ribeiro2004-figure-3' and r['schemes'][0]['separate_asset_count']==0,
      'Conceptual Figure 3 is not counted twice as a separate scheme asset')
check(len(gallery)==15,'All 15 original assets in gallery')
check({a['public_asset_sha256'] for a in gallery}=={a['sha256'] for a in assets.values()},'Exact original gallery asset set')
check({a['public_asset_sha256'] for a in gallery}=={a['public_asset_sha256'] for i in items for a in i['original_assets']},'Reader and gallery original assets agree')
for a in gallery:
    src=next(s for s in assets.values() if s['sha256']==a['public_asset_sha256'])
    check(a['asset_provenance']['source_sha256']==inv['source_sha256'] and a['page']==src['pdf_page'],'Gallery source page/hash '+a['id'])
check(len(r['referenced_methods'])==31,'All 31 references retained')
check(len(r['tables'])==0 and len(r['equations'])==4 and len(r['figures'])==7,'Seven numbered figures, four equations, no invented table')
for fid in ['figure-1','figure-2','figure-4','figure-5','figure-6','figure-7']:
    check(bool(byid[fid]['sample_scope']['canonical_sample_links']),'Figure has existing scoped specimen/model context '+fid)
check('differs from unreported' not in byid['figure-6']['text'],'Unknown final pH does not assert a measured difference')
check('diameter' in byid['overview-concentration-structure']['text'] and 'radius' in byid['overview-concentration-structure']['text'],'TEM radius and scale-bar distinctions visible')
check('no XRD trace' in byid['gap-7']['text'],'XRD prose not an invented diffraction trace')
manual=[
    'Root independently read supplied main-text pages 1–6 and all reader prose, titles and notes across 93 items. This is reader verification; the separate full source and canonical audits remain immutable evidence, not a newly claimed full re-extraction.',
    'Root visually inspected all 15 retained original crops: Figures 1–7, Equations 1–4, experimental procedure, water-ratio discussion, and two reference blocks. Checked original axes, labels, captions, scale bars and equation symbols against the reader claims.',
    'SnCl2·2H2O identity, absolute ethanol, hydrolysis versus dialysis water, unspecified 500:1 ratio basis, unknown absolute charges, room-temperature wording, dialysis and retained colloid are preserved. No oxidation pathway, vessel, timing or numerical temperature is invented.',
    'Acid-set aging 24 h, 0.4 mol/L TBAOH stock and 2 min probe sonication remain optical-preparation context. Treatment pH is not asserted to equal or differ numerically from the unreported post-base pH. TEM and zeta specimens do not silently inherit the optical treatment.',
    'Figure 4/7 scale bars are 4 nm; Figure 5 histograms use radius, not diameter. The Figure 3/4 prose reference typo is retained. No raw particle list, fitted distribution or cross-technique physical batch identity is invented.',
    'Acquisition ranges, visible plot ranges, excitation wavelength and relative normalized intensities remain distinct. Two-hour monitoring is an observation window rather than a synthesis hold. Isoelectric pH is not a process setpoint. No optical quantum yield, Raman trace or device result is added.',
    'Equations 1–4 retain radius/gas-constant distinctions, effective reduced mass, density/reference inputs, empirical coefficients and quoted uncertainties. Author model assumptions, polycondensation versus conclusion ion-deposition language and unverified solution speciation remain interpretations.',
    'SI is not located/verified; fuller preparation and optical calibration citations remain external uninspected references. Cassiterite comes from source XRD prose; no supplied XRD/SAED trace, unit-cell constants or atom coordinates is claimed. No exact structure pair or training promotion is approved.',
    'Author revised compressed captions into academic prose, removed duplicate sample pointers, added supported figure sample contexts and changed the pH wording after root review. These are bounded reader corrections without modification of frozen canonical values.'
]
result={'schema':'mattersyn.reader-source-audit.v1','source_id':'ribeiro2004','auditor':'/root','author':manifest['author'],
    'at':datetime.now(timezone.utc).isoformat(),'status':'passed' if all(c['passed'] for c in checks) else 'failed',
    'scope':'Independent private reader scientific/prose, field-pointer, sample-context and original-asset consistency. Molecular/apparatus assets, browser QA, integration, training and publication remain separate.',
    'reader_sha256':sha(P/'ribeiro2004.json'),'bound_files':bound,
    'counts':{'reader_items':len(items),'source_units':len(units),'source_facts':len(facts),'typed_fields':len(mapped),
              'visible_typed_facts':len(visible),'prose_context_fields':92,'operations':len(linkedops),'original_assets':len(assets)},
    'manual_review':manual,'checks':checks,'check_count':len(checks),'open_findings':[c for c in checks if not c['passed']],
    'checker_revision_note':'The first checker draft omitted 26 operation environment/endpoint fields and treated the explicitly documented 500:1 display formatting as a scalar/unit mismatch. Those checker assumptions were corrected from the frozen source and canonical contract; the draft report is preserved separately. No reader or canonical values were altered to clear these checker findings.',
    'training_approved':False,'visual_bindings_approved':False,'publication_approved':False}
(B/'reader-source-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(B/'reader-source-audit.md').write_text('# Ribeiro 2004 reader source audit\n\nStatus: '+result['status']+'. Root is independent of the reader author.\n\n'+'\n\n'.join(manual)+'\n\n'+str(len(checks))+' mechanical checks; these do not substitute for the manual scientific scope above. Runtime, visual assets and publication remain pending.\n',encoding='utf-8')
print(json.dumps({k:result[k] for k in ['status','counts','check_count','open_findings']},ensure_ascii=False))
