from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
B=Path(__file__).resolve().parent;P=B/'public-review-proposal'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
d=read(P/'braun2001.json');units=read(B/'source-audit.json')['units'];mapping=read(P/'source-item-mapping.json');coverage=read(P/'source-item-coverage.json');crop=read(B/'reader-assets/crop-manifest.json')
items={i['id']:i for s in d['reader_sections'] for i in s['items']};R={p.stem:read(p) for p in (B/'canonical-drafts').glob('*.json')};C=[]
def ck(n,ok,detail=''):C.append({'check':n,'passed':bool(ok),'detail':detail})
def pointer(obj,p):
 for k in p.strip('/').split('/') if p else []:obj=obj[int(k)] if isinstance(obj,list) else obj[k.replace('~1','/').replace('~0','~')]
 return obj
ck('85 items',len(items)==85)
ck('all 132 source units mapped',set(mapping)=={u['id'] for u in units} and len(mapping)==132)
ck('mapping exact current inventory',coverage['source_audit_sha256']==sha(B/'source-audit.json'))
ck('coverage mapping equality',coverage['unit_to_reader_items']==mapping)
for uid,ii in mapping.items():
 ck(uid+'/valid reader targets',bool(ii) and set(ii)<=set(items))
 for i in ii:ck(uid+'/'+i+'/reverse link',uid in items[i]['source_audit_unit_ids'])
facts=[];links=[]
for i in items.values():
 ck(i['id']+'/source provenance',bool(i['evidence']) and all(e['source_id']=='braun2001' and e['document_role']=='main' and 1<=e['pdf_page']<=4 for e in i['evidence']))
 ck(i['id']+'/not automatic training',i['training_eligible'] is False)
 ck(i['id']+'/unknown batch preserved',i['sample_scope']['physical_batch_id'] is None)
 for link in i['canonical_links']:
  try:pointer(R[link['record_id']],link['json_pointer']);ok=True
  except (KeyError,ValueError,IndexError):ok=False
  ck(i['id']+'/'+link['record_id']+link['json_pointer']+'/link resolves',ok);links.append(link)
 for f in i['facts']:
  facts.append(f);rid=f['canonical_record_id'];p=f['json_pointer'];obj=pointer(R[rid],p)
  if p.startswith('/measurements/'):
   q=obj['value'];ck(f['id']+'/sample exact',f['sample_id']==obj['sample_id']);ck(f['id']+'/measurement ID',f['canonical_measurement_id']==obj['id'])
  else:q=obj
  ck(f['id']+'/canonical quantity exact',f['canonical_quantity']==q)
  ck(f['id']+'/unit preserved',f['unit']==q.get('unit'))
  ck(f['id']+'/approximation preserved',f['approximate']==q.get('approximate',False))
  ck(f['id']+'/not training by default',f['training_eligible'] is False)
  if q.get('maximum_exclusive'):ck(f['id']+'/strict display bound','<' in str(f['value']) and q.get('value') is None)
  if q.get('minimum') is not None and q.get('maximum') is None:ck(f['id']+'/lower display bound','≥' in str(f['value']))
 for sl in i['sample_scope'].get('canonical_sample_links',[]):
  obj=pointer(R[sl['record_id']],sl['json_pointer']);ck(i['id']+'/'+sl['sample_id']+'/sample pointer',obj['sample_id']==sl['sample_id'])
expected_m={(rid,m['id']) for rid,r in R.items() for m in r['measurements']};actual_m={(f['canonical_record_id'],f['canonical_measurement_id']) for f in facts if 'canonical_measurement_id' in f}
ck('all 75 measurements covered',expected_m==actual_m and len(actual_m)==75)
expected_o={(rid,'/operations/'+str(j)) for rid,r in R.items() for j,o in enumerate(r['operations'])};actual_o={(x['record_id'],x['json_pointer']) for x in links if x['json_pointer'].startswith('/operations/') and x['json_pointer'].count('/')==2}
ck('all 45 operations covered',expected_o<=actual_o and len(expected_o)==45)
expected_p={(rid,'/operations/'+str(j)+'/parameters/'+k) for rid,r in R.items() for j,o in enumerate(r['operations']) for k in o['parameters']}
actual_p={(f['canonical_record_id'],f['json_pointer']) for f in facts if f.get('basis')=='operation_parameter'}
ck('all 95 operation parameters covered',expected_p==actual_p and len(expected_p)==95)
ck('179 typed facts',len(facts)==179)
ck('all 19 source references',all(f'reference-{n:02}' in items for n in range(1,20)) and len(d['referenced_methods'])==19)
ck('source group and paper ID',d['source_group']==d['paper_id']=='braun2001')
ck('no matched SI claimed',d['review_scope']=='supplied_main_only_si_unverified' and d['supporting_information']['status']=='not_located_or_matched')
ck('source hash exact',d['documents'][0]['sha256']=='00ac817e60651f0e7f9faabe85ba18372ac37fea1f0f5d174779c982064b4184')
ck('no rapid injection inferred','rapid core-nucleation addition' not in items['h2s-gas']['text'] and 'core-nucleation gas addition' in items['h2s-gas']['text'])
ck('PL pulse duration pump-scoped','Nd:YAG pump' in items['pl-method']['text'] and 'OPO output pulse-width' in items['pl-method']['text'])
ck('core disagreement explicit','3.5 nm' in items['core-size-conflict']['text'] and '3.2 nm' in items['core-size-conflict']['text'])
ck('printed inset labels retained','650, 900 and 750 nm' in items['inset-label-conflict']['text'] and 'stimulated emission' in items['inset-label-conflict']['text'])
ck('Source S-minus notation preserved','S⁻' in items['nucleation-ph']['text'])
ck('Reference13 not silently completed','submitted' in items['reference-13']['text'] and 'no journal, year, pages or DOI' in items['reference-13']['text'])
ck('no pure HgS evidence mapping',d['material_evidence_records']['HgS']==[])
ck('bare CdS scope states composite distinction','a-cds-core' in d['material_evidence_scope_notes']['CdS'] and 'not bare CdS' in d['material_evidence_scope_notes']['CdS'])
audited=read(B/'canonical-records-audit.json')['record_hashes']
for rid,h in audited.items():ck(rid+'/frozen canonical bytes',sha(B/'canonical-drafts'/(rid+'.json'))==h)
assets=d['figures']+d['tables']+d['source_notes'];ac={a['id']:a for a in assets};cm={a['id']:a for a in crop['assets']}
ck('eight original assets',len(ac)==len(cm)==8 and set(ac)==set(cm))
rows=[]
for aid,a in ac.items():
 c=cm[aid];p=B/'reader-assets'/c['relative_asset'];h=sha(p)
 ck(aid+'/crop bytes',h==a['public_asset_sha256']==c['sha256'])
 ck(aid+'/source page',a['page']==c['source_pdf_page'] and a['asset_provenance']['source_sha256']==c['source_sha256']==d['documents'][0]['sha256'])
 ck(aid+'/sample records',set(a['sample_links'])<=set(R))
 ck(aid+'/crop transform',a['asset_provenance']['crop_bbox_pdf_points_top_left']==c['crop_bbox_pdf_points_top_left'])
 ck(aid+'/not training figure data',a['training_eligible'] is False)
 rows.append({'id':aid,'sha256':h,'page':a['page'],'source_correspondence':'passed','sample_links':a['sample_links'],'visual_review':'Actual original PNG individually viewed in this audit; full four-page source also independently viewed. Panels, axes, symbols and complete captions/source continuations retained.'})
for n in (2,3,4):ck('Figure'+str(n)+'/only source systems',ac['figure-'+str(n)]['sample_links']==['braun-2001-system-'+s for s in ('i','ii','iii')])
ck('Figure1 schematic evidence class',ac['figure-1']['evidence_class']=='author_structure_schematic')
for ref in d['material_evidence_records'].values():ck('material record links exist',set(ref)<=set(R))
manual=[
 'All 85 reader items and their claim types, sample scopes, source locators, 19 bibliographic entries, eight asset captions and eight original PNGs were independently read/viewed. All 132 source-unit mappings were checked against the independently authored source inventory; typed facts supplement prose where needed, including the 2 mm cell, 470 nm core feature and wavelength-dependent decay distribution.',
 'Three synthesis routes retain A/B/C exchange versus deposition semantics. Only consecutive C steps require additional Cd; repeated B doses inherit the shared source step definition. No unreported salt, counterion, pH titrant, stock amount, synthesis temperature, yield, isolation or batch identifier supplied.',
 'System II is one contiguous double-layer well; III has two monolayer wells separated by a two-CdS-layer barrier. Source 3.5 versus 3.2 nm core descriptions remain unresolved. Figure1 layer and wavefunction drawings are source schematics, not newly measured morphology, lattice, phase or atomistic coordinates.',
 'Figure2 preserves all 3/5/6 source spectra and stage labels; source does not show a separate trace after the first extra C step in III. Repeated initial spectra are not unique physical batch evidence. Figure3 arbitrary intensity and background excursions are unchanged; study-wide estimated QY <1% remains a bound.',
 'Absorption minima (625/700/670 nm), PL maxima (820/950/820 nm) and transient crossover (600/700/650 nm) are separate properties. Figure4 retains six exact inset probe labels and original bleach terminology, while the text attributes long-lived response to stimulated emission. The ~5 ps component and visual-aid fits are not universal exact lifetimes.',
 'PL pump versus OPO duration wording and unsupported rapid-addition phrasing were corrected before the final hash. PL 440 nm/5 ns pump/10 Hz and TA400 nm/100 fs/100 µJ methods remain distinct; 3 µm(21 fs) delay resolution and 2 mm rotating TA cell are not transferred to other protocols.',
 'Cited TEM, ODMR/ESR and prior theory remain context. No current micrograph, diffraction, Raman property, raw numeric spectrum, unit cell or SystemIII theoretical exciton computation invented. Reference13 remains submitted/unidentified; future barrier/well sweeps are not extra performed recipes.',
 'Current supplied main is complete across four pages; SI was neither declared in those pages nor locally matched. This is not proof that no SI exists. Component CdS evidence is explicitly limited to core measurements, and no isolated HgS material evidence is assigned.'
]
fail=[c for c in C if not c['passed']]
report={'status':'passed' if not fail else 'failed','source_id':'braun2001','audited_utc':datetime.now(timezone.utc).isoformat(),'reader_sha256':sha(P/'braun2001.json'),'source_inventory_sha256':sha(B/'source-audit.json'),'source_identity_sha256':sha(B/'source-identity.json'),'source_item_mapping_sha256':sha(P/'source-item-mapping.json'),'source_item_coverage_sha256':sha(P/'source-item-coverage.json'),'canonical_measurement_coverage_sha256':sha(P/'canonical-measurement-coverage.json'),'crop_manifest_sha256':sha(B/'reader-assets/crop-manifest.json'),'record_hashes':audited,'item_count':85,'source_unit_count':132,'measurements':75,'operations':45,'typed_facts':179,'asset_count':8,'manual_source_review':manual,'resolved_findings':['Removed unsupported rapid-addition inference; source reports rapid nucleation but no injection duration.','Explicitly attributed 5 ns/10 Hz to the Nd:YAG pump rather than measured OPO output.'],'check_count':len(C),'failure_count':len(fail),'checks':C,'failures':fail,'assets':rows,'limitations':['Complete supplied-main source review; local SI still unmatched, existence not ruled out.','Independent scientific/source-link audit only. Parent owns public layout, interactions, integration, publication and training-export eligibility.'],'browser_verified':False,'site_mutated':False}
(B/'reader-source-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(B/'reader-source-audit.md').write_text('# Braun 2001 independent reader audit\n\n'+report['status']+f': 85 reader items, 132 source units, 75 measurements, 45 operations, 179 typed facts and eight original assets; {len(C)} supporting checks, {len(fail)} failures.\n\n'+'\n\n'.join(manual)+'\n\nExact hashes are recorded in reader-source-audit.json. No Site edit or browser verification performed.\n',encoding='utf8')
print(json.dumps({'status':report['status'],'reader_sha256':report['reader_sha256'],'check_count':len(C),'failures':fail},ensure_ascii=False))
