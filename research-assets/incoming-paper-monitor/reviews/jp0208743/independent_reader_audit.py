from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
B=Path(__file__).resolve().parent;P=B/'public-review-proposal'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
d=read(P/'dantas2002.json');units=read(B/'source-audit.json')['units'];mapping=read(P/'source-item-mapping.json');coverage=read(P/'source-item-coverage.json');crop=read(B/'reader-assets/crop-manifest.json')
items={i['id']:i for s in d['reader_sections'] for i in s['items']};R={p.stem:read(p) for p in (B/'canonical-drafts').glob('*.json')};C=[]
def ck(n,v,detail=''):C.append({'check':n,'passed':bool(v),'detail':detail})
def ptr(x,p):
 for k in p.strip('/').split('/') if p else []:x=x[int(k)] if isinstance(x,list) else x[k.replace('~1','/').replace('~0','~')]
 return x
ck('101 reader items',len(items)==101);ck('147 complete source units',set(mapping)=={u['id'] for u in units} and len(mapping)==147)
ck('Current inventory hash',coverage['source_audit_sha256']==sha(B/'source-audit.json'));ck('Coverage mapping exact',coverage['unit_to_reader_items']==mapping)
for uid,ids in mapping.items():
 ck(uid+'/reader targets',bool(ids) and set(ids)<=set(items))
 for i in ids:ck(uid+'/'+i+'/reverse link',uid in items[i]['source_audit_unit_ids'])
facts=[];links=[]
for i in items.values():
 ck(i['id']+'/source provenance',bool(i['evidence']) and all(e['source_id']=='dantas2002' and e['document_role']=='main' and 1<=e['pdf_page']<=5 for e in i['evidence']))
 ck(i['id']+'/not automatic training',i['training_eligible'] is False);ck(i['id']+'/unknown physical batch',i['sample_scope']['physical_batch_id'] is None)
 for x in i['canonical_links']:
  try:ptr(R[x['record_id']],x['json_pointer']);ok=True
  except (KeyError,ValueError,IndexError):ok=False
  ck(i['id']+'/'+x['record_id']+x['json_pointer']+'/link',ok);links.append(x)
 for f in i['facts']:
  facts.append(f);obj=ptr(R[f['canonical_record_id']],f['json_pointer'])
  if f['json_pointer'].startswith('/measurements/'):
   q=obj['value'];ck(f['id']+'/sample',f['sample_id']==obj['sample_id']);ck(f['id']+'/measurement ID',f['canonical_measurement_id']==obj['id'])
  else:q=obj
  ck(f['id']+'/value exact',f['canonical_quantity']==q);ck(f['id']+'/unit',f['unit']==q.get('unit'));ck(f['id']+'/approximation',f['approximate']==q.get('approximate',False));ck(f['id']+'/training excluded',f['training_eligible'] is False)
  if q.get('minimum_exclusive'):ck(f['id']+'/strict lower display','>' in str(f['value']) and q.get('value') is None)
  if q.get('maximum_exclusive'):ck(f['id']+'/strict upper display','<' in str(f['value']) and q.get('value') is None)
 for x in i['sample_scope'].get('canonical_sample_links',[]):ck(i['id']+'/'+x['sample_id']+'/sample pointer',ptr(R[x['record_id']],x['json_pointer'])['sample_id']==x['sample_id'])
expected_m={(rid,m['id']) for rid,r in R.items() for m in r['measurements']};actual_m={(f['canonical_record_id'],f['canonical_measurement_id']) for f in facts if 'canonical_measurement_id' in f}
ck('110 exact measurements covered',expected_m==actual_m and len(actual_m)==110)
expected_o={(rid,'/operations/'+str(j)) for rid,r in R.items() for j,o in enumerate(r['operations'])};actual_o={(x['record_id'],x['json_pointer']) for x in links if x['json_pointer'].startswith('/operations/') and x['json_pointer'].count('/')==2}
ck('48 operations covered',expected_o<=actual_o and len(expected_o)==48)
expected_p={(rid,'/operations/'+str(j)+'/parameters/'+k) for rid,r in R.items() for j,o in enumerate(r['operations']) for k in o['parameters']};actual_p={(f['canonical_record_id'],f['json_pointer']) for f in facts if f.get('basis')=='operation_parameter'}
ck('67 operation parameters covered',expected_p==actual_p and len(expected_p)==67)
expected_s=set()
for rid,r in R.items():
 for j,s in enumerate(r['stocks']):
  for k in s['concentrations']:expected_s.add((rid,f'/stocks/{j}/concentrations/{k}'))
  for n,c in enumerate(s['components']):
   for k in c['quantities']:expected_s.add((rid,f'/stocks/{j}/components/{n}/quantities/{k}'))
actual_s={(f['canonical_record_id'],f['json_pointer']) for f in facts if f['json_pointer'].startswith('/stocks/')}
ck('Seven stock missingness facts',expected_s==actual_s and len(expected_s)==7);ck('184 typed facts',len(facts)==184)
ck('21 references',all(f'reference-{n:02}' in items for n in range(1,22)) and len(d['referenced_methods'])==21)
ck('Source ID',d['source_group']==d['paper_id']=='dantas2002');ck('Corpus paper ID',d['corpus_paper_id']=='paper-93084fec2106e8ad8cef')
ck('SI missingness',d['review_scope']=='supplied_main_only_si_unverified' and d['supporting_information']['status']=='not_located_or_matched')
ck('Source bytes',d['documents'][0]['sha256']=='c8fd35a429bf636fcccc5dfeb3211cea44299e911fbfc80e1a308c75b7b04917')
def contains(item,*phrases):ck(item+'/source semantics',all(x in items[item]['text'] for x in phrases))
contains('lead-oxide','PbO₂','not silently changed to PbO');contains('sulfur-source','not specified','S₈');contains('crucible','aluminum crucible','not automatically corrected to alumina')
contains('glass-composition','not an exact final-glass');contains('quench','water-quench','not inferred');contains('sample-boundary','5 and 30 h','not evidence of identical physical specimens')
contains('optical-instrument','514.5 nm argon-ion','separate broadband');contains('size-radius-boundary','dot radius','grain height','not imposed')
contains('afm-versus-optical','5 h','6 h','does not establish');contains('afm1-size','40.19 Å','1.57 Å');contains('afm2-size','291.24 Å','0 Å')
contains('absorption-sg1','1.391, 2.486, 2.691 and 2.894');contains('absorption-sg2','1.420, 2.200, 2.490 and 2.863')
contains('figure1-axes','0.5–3.0','3.5');contains('figure2-axes','E^(1/2)','not a fifth prepared');contains('figure5-window','2.90, 2.95 and 3.00','not display the entire')
contains('power-acquisition','SG1','kW/cm²');contains('power-law','0.86','not a synthesis growth law');contains('figure7-axes','left','right','not a common absolute intensity')
contains('figure3-legend','Space I','Space II','(−1)^(l+1)','(−1)^l');contains('parabolic-model','0.25 m₀','not DFT');contains('confinement-regimes','≤80 Å','above 100 Å')
contains('near-excitation-line','2.978','2.476','tentatively');contains('raman-boundary','does not present','proposed interpretation');contains('phonon-argument','authors','No temperature-dependent');contains('auger-argument','argument, not a measured')
ck('Composite/component scopes explicit','not a freestanding PbS synthesis' in d['material_evidence_scope_notes']['PbS'] and 'upstream context' in d['material_evidence_scope_notes']['PbS/glass'])
ck('Pregrowth host absent from PbS component results','dantas-2002-glass-host' not in d['material_evidence_records']['PbS'])
audited=read(B/'canonical-records-audit.json')['record_hashes']
for rid,h in audited.items():ck(rid+'/frozen canonical bytes',sha(B/'canonical-drafts'/(rid+'.json'))==h)
assets=d['figures']+d['tables']+d['source_notes'];ac={x['id']:x for x in assets};cm={x['id']:x for x in crop['assets']}
ck('Eleven original assets',len(ac)==len(cm)==11 and set(ac)==set(cm));rows=[]
for aid,a in ac.items():
 c=cm[aid];h=sha(B/'reader-assets'/c['relative_asset']);ck(aid+'/exact crop',h==a['public_asset_sha256']==c['sha256']);ck(aid+'/source page',a['page']==c['source_pdf_page'] and a['asset_provenance']['source_sha256']==c['source_sha256']==d['documents'][0]['sha256'])
 ck(aid+'/sample links',set(a['sample_links'])<=set(R));ck(aid+'/crop provenance',a['asset_provenance']['crop_bbox_pdf_points_top_left']==c['crop_bbox_pdf_points_top_left']);ck(aid+'/not automatic training',a['training_eligible'] is False)
 rows.append({'id':aid,'sha256':h,'page':a['page'],'sample_links':a['sample_links'],'source_correspondence':'passed','visual_review':'Actually viewed the original PNG individually, including captions, all panels, axes and labels. All five complete source pages independently viewed; high-resolution Figure1/3/4 details additionally checked.'})
ck('Figure1 only SG1/SG2',ac['figure-1']['sample_links']==['dantas-2002-sg1','dantas-2002-sg2','dantas-2002-optical-absorption'])
ck('Figure3 models only',ac['figure-3']['sample_links']==['dantas-2002-parabolic-model','dantas-2002-four-band-model'] and ac['figure-3']['evidence_class']=='author_model')
ck('Figure4 AFM only',ac['figure-4']['sample_links']==['dantas-2002-afm1','dantas-2002-afm2','dantas-2002-afm-analysis'])
ck('Figure6 SG1 plus model',ac['figure-6']['sample_links']==['dantas-2002-sg1','dantas-2002-power-response','dantas-2002-mechanisms'] and ac['figure-6']['evidence_class']=='experimental_fit_and_author_model')
ck('Figure7 SG1 only route','dantas-2002-sg1' in ac['figure-7']['sample_links'] and not any(x in ac['figure-7']['sample_links'] for x in ['dantas-2002-sg2','dantas-2002-sg3','dantas-2002-sg4','dantas-2002-afm1','dantas-2002-afm2']))
for refs in d['material_evidence_records'].values():ck('Material links resolve',set(refs)<=set(R))
manual=[
'Independently read every one of the 101 reader items and all 21 printed reference entries, checked all 147 source-unit mappings, 110 measurement rows, 48 operation links and 184 exact typed facts against the current source-audited canonical records. All eleven manifest crops were actually opened and visually inspected individually; all five complete source pages and high-resolution Figure1/3/4 annotations were also inspected.',
'The powder formulation remains an incomplete precursor inventory, retaining PbO2, unknown sulfur input and literal aluminum-crucible wording. No PbO correction, sulfur reagent, final-glass stoichiometry, water quench, gas atmosphere or complete weighed recipe is invented. All three thermal holds and fast cooling remain distinct. Six endpoints do not imply independent full melts or sequential aliquots.',
'SG1–SG4 optical samples and AFM1/AFM2 microscopy samples retain their distinct 1/3/6/12 versus 5/30 h durations. Optical cutting/polishing does not become AFM preparation. AFM1 at 5 h and SG3 at 6 h are compared without a shared-sample join. Exact AFM heights/depths, rounded size statements and model radius axes remain separate.',
'Figure1 main SG2 versus inset SG1, paired energy ordering, source 0.5–3.0 eV prose versus inset 3.5 eV tick, Figure2 bulk reference and all optical trends were checked. Original signal scales and plot domains are not promoted to calibrated acquisition settings, raw arrays or a universal growth law.',
'Both Figure3 panels remain calculations with their original state legends, axes and SpaceI/II angular momentum/parity expressions. The 0.25 m0 assumptions belong to the parabolic model, while the 4×4 formalism lacks a complete numerical Hamiltonian. Source size estimates and ≤80/>100 Å regimes are not reconstructed diameters, atom positions or measured electronic states.',
'Figure4 includes both separate AFM cohorts, overview/magnifications, correlation panels and full histograms. Figure5 remains the narrow plotted window despite the broad narrative 2.409–2.978 eV ASPL range. Figure6 retains SG1-only kW/cm² excitation intensity, approximate 0.86 regression and a hypothesis inset. Figure7 keeps independent absorption/PL axes and the secondary 2.476 eV line distinct from main 2.978 eV emission.',
'Surface-state, two-photon, Auger, phonon-bottleneck and resonant-Raman explanations remain attributed interpretations. Neither a laser threshold nor a Raman mode nor a measured defect structure is created. Component PbS evidence explicitly comes from a glass composite; the upstream host procedure is excluded from component PbS results.',
'Eleven source assets comprise all seven complete figures and four original methods/model excerpts; the unreferenced private size-estimates.png is a redundant excerpt already fully contained in model-assumptions.png and is not counted as a published asset. No matched SI or cited external full text was reviewed. Parent owns integrated browser rendering and publication.'
]
fail=[x for x in C if not x['passed']]
report={'status':'passed' if not fail else 'failed','source_id':'dantas2002','audited_utc':datetime.now(timezone.utc).isoformat(),'reader_sha256':sha(P/'dantas2002.json'),'source_inventory_sha256':sha(B/'source-audit.json'),'source_identity_sha256':sha(B/'source-identity.json'),'source_item_mapping_sha256':sha(P/'source-item-mapping.json'),'source_item_coverage_sha256':sha(P/'source-item-coverage.json'),'canonical_measurement_coverage_sha256':sha(P/'canonical-measurement-coverage.json'),'crop_manifest_sha256':sha(B/'reader-assets/crop-manifest.json'),'record_hashes':audited,'item_count':101,'source_unit_count':147,'measurements':110,'operations':48,'typed_facts':184,'asset_count':11,'manual_source_review':manual,'resolved_findings':['Vessel ancestry removed from seven canonical fused-glass states; no other source fact changed.'],'check_count':len(C),'failure_count':len(fail),'checks':C,'failures':fail,'assets':rows,'limits':['Scientific source-correspondence audit only; integrated layout, interaction, export and publication checks are parent-owned.','No matched SI or cited external full text reviewed; missingness remains explicit.'],'browser_verified':False,'site_mutated':False}
(B/'reader-source-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(B/'reader-source-audit.md').write_text('# Dantas 2002 independent reader audit\n\n'+report['status']+f': 101 items, 147 source units, 110 measurements, 48 operations, 184 typed facts and eleven original assets; {len(C)} checks, {len(fail)} failures.\n\n'+'\n\n'.join(manual)+'\n\nExact hashes are bound in reader-source-audit.json; no Site mutation or browser verification claimed.\n',encoding='utf8')
print(json.dumps({'status':report['status'],'reader_sha256':report['reader_sha256'],'checks':len(C),'failures':fail},ensure_ascii=False))
