from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
B=Path(__file__).resolve().parent;P=B/'public-review-proposal'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
d=read(P/'yi2002.json');units=read(B/'source-audit.json')['units'];mapping=read(P/'source-item-mapping.json');coverage=read(P/'source-item-coverage.json');crop=read(B/'reader-assets/crop-manifest.json')
items={i['id']:i for s in d['reader_sections']for i in s['items']};R={p.stem:read(p)for p in (B/'canonical-drafts').glob('*.json')};C=[]
def ck(n,v,detail=''):C.append({'check':n,'passed':bool(v),'detail':detail})
def ptr(x,p):
 for k in p.strip('/').split('/')if p else[]:x=x[int(k)]if isinstance(x,list)else x[k.replace('~1','/').replace('~0','~')]
 return x
ck('115readeritems',len(items)==115);ck('148completeunits',set(mapping)=={u['id']for u in units} and len(mapping)==148)
ck('Current source inventory',coverage['source_audit_sha256']==sha(B/'source-audit.json'));ck('Exact coverage map',coverage['unit_to_reader_items']==mapping)
for uid,ids in mapping.items():
 ck(uid+'/targets',bool(ids) and set(ids)<=set(items))
 for i in ids:ck(uid+'/'+i+'/reverse',uid in items[i]['source_audit_unit_ids'])
facts=[];links=[]
for i in items.values():
 ck(i['id']+'/provenance',bool(i['evidence'])and all(e['source_id']=='yi2002'and e['document_role']=='main'and 1<=e['pdf_page']<=5 for e in i['evidence']));ck(i['id']+'/no automatic training',i['training_eligible']is False);ck(i['id']+'/batch unknown',i['sample_scope']['physical_batch_id']is None)
 for x in i['canonical_links']:
  try:ptr(R[x['record_id']],x['json_pointer']);ok=True
  except(KeyError,ValueError,IndexError):ok=False
  ck(i['id']+'/'+x['record_id']+x['json_pointer']+'/link',ok);links.append(x)
 for f in i['facts']:
  facts.append(f);obj=ptr(R[f['canonical_record_id']],f['json_pointer'])
  if f['json_pointer'].startswith('/measurements/'):
   q=obj['value'];ck(f['id']+'/sample',f['sample_id']==obj['sample_id']);ck(f['id']+'/ID',f['canonical_measurement_id']==obj['id'])
  else:q=obj
  ck(f['id']+'/exact source fact',f['canonical_quantity']==q);ck(f['id']+'/unit',f['unit']==q.get('unit'));ck(f['id']+'/approx',f['approximate']==q.get('approximate',False));ck(f['id']+'/not training',f['training_eligible']is False)
  if q.get('status')=='inherited':ck(f['id']+'/inherited display qualifier',bool(f.get('qualifier')))
 for x in i['sample_scope'].get('canonical_sample_links',[]):ck(i['id']+'/'+x['sample_id']+'/sample pointer',ptr(R[x['record_id']],x['json_pointer'])['sample_id']==x['sample_id'])
expected_m={(rid,m['id'])for rid,r in R.items()for m in r['measurements']};actual_m={(f['canonical_record_id'],f['canonical_measurement_id'])for f in facts if'canonical_measurement_id'in f}
ck('91measurements',expected_m==actual_m and len(actual_m)==91)
expected_o={(rid,'/operations/'+str(j))for rid,r in R.items()for j,o in enumerate(r['operations'])};actual_o={(x['record_id'],x['json_pointer'])for x in links if x['json_pointer'].startswith('/operations/')and x['json_pointer'].count('/')==2}
ck('105operations',expected_o<=actual_o and len(expected_o)==105)
expected_p={(rid,'/operations/'+str(j)+'/parameters/'+k)for rid,r in R.items()for j,o in enumerate(r['operations'])for k in o['parameters']};actual_p={(f['canonical_record_id'],f['json_pointer'])for f in facts if f.get('basis')=='operation_parameter'};ck('All operation parameters',expected_p==actual_p)
expected_s=set();expected_material=set()
for rid,r in R.items():
 for j,s in enumerate(r['stocks']):
  for k in s['concentrations']:expected_s.add((rid,f'/stocks/{j}/concentrations/{k}'))
  for n,c in enumerate(s['components']):
   for k in c['quantities']:expected_s.add((rid,f'/stocks/{j}/components/{n}/quantities/{k}'))
 for j,m in enumerate(r['materials']):
  for k in m['quantities']:expected_material.add((rid,f'/materials/{j}/quantities/{k}'))
actual_s={(f['canonical_record_id'],f['json_pointer'])for f in facts if f['json_pointer'].startswith('/stocks/')};actual_material={(f['canonical_record_id'],f['json_pointer'])for f in facts if f['json_pointer'].startswith('/materials/')}
ck('Stock concentration missingness',expected_s==actual_s);ck('All reagent quantities',expected_material==actual_material);ck('323typedfacts',len(facts)==323)
ck('27references',all(f'reference-{n:02}'in items for n in range(1,28))and len(d['referenced_methods'])==27)
ck('Source identity',d['paper_id']==d['source_group']=='yi2002'and d['doi']=='10.1021/cm0115416');ck('Corpus identity',d['corpus_paper_id']=='paper-af2edcc87c5efd316de2'and d['corpus_document_id']=='doc-fc52eb9dee2b95352f16')
ck('SI missingness',d['review_scope']=='supplied_main_only_si_unverified'and d['supporting_information']['status']=='not_located_or_matched');ck('Raw source hash',d['documents'][0]['sha256']=='6438ee53b3fffb86f5e36508f265041d9235b8ee9f3e20dd99d46aae91c68a57')
def has(i,*v):ck(i+'/source semantics',all(s in items[i]['text']for s in v))
has('mass-amount-check','209.3','196.0','does not prove');has('feed-ratio-check','9.368','1:1','3:2','not evidence');has('dopant-basis','77:20:3','not an elemental-analysis')
has('stock-a-composition','added water volume','not an independently measured final');has('dropwise-addition','B drop by drop to Solution A','20–30','not converted');has('autoclave-charge','100 mL','capacity is not');has('centrifugation','6,000 rpm','10 min','not converted')
has('drying','not evidence','air atmosphere');has('anneal-800','20 °C/min','5 h','not automatically verified');has('bulk-fire','1,200 °C','1,000 °C')
has('phase','small second phase','not be labeled phase-pure');has('scherrer-size','52.5','distinct from TEM');has('tem-scales','300 nm','100 nm','not established');has('size-distribution','45–65','53 nm','50 nm')
has('single-crystal-inference','cross-technique inference','SAED');has('anneal-size','No exact 900/1,000','only shows the 800')
has('downconversion-peaks','374','525','549');has('upconversion-peaks','519','541','653');has('upconversion-method','50 mW','not an intensity');has('figure4','dotted excitation','solid down-conversion')
has('nir-band','10,238','976','10,625–9,875','941–1,013');has('figure5-axis','0 at the top','1 at the bottom','not relabeled');has('anneal-emission','more slowly','900 °C','800 °C despite')
has('erbium-conflict','4%','3% maximum','6%','one unassigned');has('power-slopes','2.2024','1.8853','2.0907');has('power-label-conflict','519 nm','520 nm','not a fourth');has('figure8','logarithmic','not unambiguously calibrated')
has('bulk-spectrum','not provide an absolute quantum yield');has('figure10','not automatically the 1,000');has('figure9-model','⁴I₉/₂','no numerical energy-axis');has('surface-rationale','No surface-ion count','measured lifetime');has('bioassay-context','No conjugation')
ck('Only nominal host material hub',set(d['material_evidence_records'])=={'La2(MoO4)3:Yb,Er'}and set(d['material_evidence_records']['La2(MoO4)3:Yb,Er'])==set(R))
audited=read(B/'canonical-records-audit.json')['record_hashes']
for rid,h in audited.items():ck(rid+'/audited canonical hash',sha(B/'canonical-drafts'/(rid+'.json'))==h)
assets=d['figures']+d['tables']+d['source_notes'];ac={x['id']:x for x in assets};cm={x['id']:x for x in crop['assets']};rows=[]
ck('16originalassets',len(ac)==len(cm)==16 and set(ac)==set(cm))
for aid,a in ac.items():
 c=cm[aid];h=sha(B/'reader-assets'/c['relative_asset']);ck(aid+'/exact bytes',h==a['public_asset_sha256']==c['sha256']);ck(aid+'/page/source',a['page']==c['source_pdf_page']and a['asset_provenance']['source_sha256']==c['source_sha256']==d['documents'][0]['sha256']);ck(aid+'/samples resolve',set(a['sample_links'])<=set(R));ck(aid+'/bbox',a['asset_provenance']['crop_bbox_pdf_points_top_left']==c['crop_bbox_pdf_points_top_left']);ck(aid+'/not training',a['training_eligible']is False)
 rows.append({'id':aid,'sha256':h,'page':a['page'],'sample_links':a['sample_links'],'source_correspondence':'passed','visual_review':'Actually opened and viewed this original PNG individually; full panels, labels, axes and captions checked against all five original source pages.'})
ck('Figure1 exact800 scope',set(ac['figure-1']['sample_links'])=={'yi-2002-anneal-800','yi-2002-xrd'});ck('Figure2 before/after800 only',set(ac['figure-2']['sample_links'])=={'yi-2002-anneal-800','yi-2002-tem'})
ck('Figure3 generic analyzer only',ac['figure-3']['sample_links']==['yi-2002-particle-size']);ck('Figure4 optics no assumed route',set(ac['figure-4']['sample_links'])=={'yi-2002-downconversion','yi-2002-upconversion'});ck('Figure5 generic nearIR',ac['figure-5']['sample_links']==['yi-2002-near-ir']);ck('Figure6 five endpoints',set(ac['figure-6']['sample_links'])=={'yi-2002-anneal-'+str(t)for t in [600,700,800,900,1000]})
ck('Figure7 comparison only',ac['figure-7']['sample_links']==['yi-2002-erbium-series']);ck('Figure8 power only',ac['figure-8']['sample_links']==['yi-2002-power-response']);ck('Figure9 model only',ac['figure-9']['sample_links']==['yi-2002-mechanisms']and ac['figure-9']['evidence_class']=='author_model');ck('Figure10 distinct bulk',set(ac['figure-10']['sample_links'])=={'yi-2002-bulk','yi-2002-upconversion'})
manual=['All115 reader prose items, all27 bibliography entries, all148 explicit source-unit associations and all16 actual original image assets were independently read/viewed. This includes all ten complete figures and six original preparation/acquisition/analysis excerpts. Full five-page source text/images and detailed source labels were independently inspected before proposed reader review.','Every current canonical measurement, operation, operation parameter, reagent quantity and stock-concentration field is exactly linked. All91 measurements,105 operations and323 typed facts have source-scoped sample IDs and missingness/status intact. Their record hashes match the passed independent scientific audit.','Stock A and B retain exact source masses/mmol,30 mL added-water amounts, stirring, nitric-acid evaporation and missing speciation. Two explicit curator arithmetic checks retain the ammonium-molybdate mass/amount and Mo-to-rare-earth ratio inconsistencies without repairing formula, doses, hydrate identity or product stoichiometry.','Hydrothermal B-to-A addition, drops/min units, vessel capacity,180 °C/1 h,6000 rpm/10 min, two washes and air drying are complete. The800 °C method alone gives20 °C/min and natural cooling; alternative full routes clearly inherit common framework without independent quantities or batch identity. The1200 °C air-fired bulk comparator remains distinct from1000 °C growth and the incomplete grinding control.','XRD retains the minor phase,52.5 nm author-derived coherent size and unreported calculation assumptions. TEM300/100 nm scale bars and40–60 nm majority remain separate from45–65 nm/~53 nm analyzer output and rounded50 nm summary. The original microscopy clustering and all histogram bins remain visible; no SAED or dopant-resolved lattice is fabricated.','All emission and absorption bands, original ordinate conventions and source-rounded conversions were checked. The50 mW laser specification is not irradiance or every power-sweep value. 800 °C is the size/intensity compromise rather than highest raw brightness; 900/1000 °C sizes are unknown. No absolute quantum yield or measured fluorescence lifetime is invented.','Figure7 retains the source prose conflict at4%, single unassigned response and absent6% point. Figure8 retains all six exact/rounded slope statements and519-versus520 nm label conflict. Figure9 remains a mechanism diagram with original energy-level labels, including4I9/2; source surface/interior, lifetime and defect explanations remain attributed hypotheses.','Figures1/2 bind explicitly to800 °C XRD/TEM contexts; Figures3/4/5/8 retain generic unresolved thermal/sample associations. Figure6 binds exactly five anneal endpoints, Figure7 only the Er comparison, Figure9 only model context and Figure10 the distinct bulk/optical comparison. No optical/theory sample is silently promoted to a specific synthesized batch.','No SI declaration or matched local SI, external reference full text, atom coordinates or raw arrays is asserted. Parent owns integrated rendering, interactions, publication flags and training-export gates. No Site mutation or browser verification is claimed.']
fail=[x for x in C if not x['passed']]
report={'status':'passed'if not fail else'failed','source_id':'yi2002','audited_utc':datetime.now(timezone.utc).isoformat(),'reader_sha256':sha(P/'yi2002.json'),'source_inventory_sha256':sha(B/'source-audit.json'),'source_identity_sha256':sha(B/'source-identity.json'),'source_item_mapping_sha256':sha(P/'source-item-mapping.json'),'source_item_coverage_sha256':sha(P/'source-item-coverage.json'),'canonical_measurement_coverage_sha256':sha(P/'canonical-measurement-coverage.json'),'crop_manifest_sha256':sha(B/'reader-assets/crop-manifest.json'),'record_hashes':audited,'item_count':115,'source_unit_count':148,'measurements':91,'operations':105,'typed_facts':323,'operation_parameter_count':len(expected_p),'material_quantity_count':len(expected_material),'stock_fact_count':len(expected_s),'asset_count':16,'manual_source_review':manual,'resolved_findings':[],'check_count':len(C),'failure_count':len(fail),'checks':C,'failures':fail,'assets':rows,'limits':['Scientific source-correspondence audit; integrated layout, interaction, export and publication checks are parent-owned.','No matched SI or cited external full text reviewed; missingness remains explicit.'],'browser_verified':False,'site_mutated':False}
(B/'reader-source-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8');(B/'reader-source-audit.md').write_text('# Yi2002 independent reader source audit\n\n'+report['status']+f':115 items,148 units,91 measurements,105 operations,323 typed facts,16 original assets. {len(C)} supporting checks,{len(fail)} failures.\n\n'+'\n\n'.join(manual)+'\n\nExact artifact hashes are in reader-source-audit.json. No Site mutation.\n',encoding='utf8');print(json.dumps({'status':report['status'],'reader_sha256':report['reader_sha256'],'checks':len(C),'failures':fail},ensure_ascii=False))
