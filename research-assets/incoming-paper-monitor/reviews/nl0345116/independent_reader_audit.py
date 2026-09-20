from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,re,unicodedata
B=Path(__file__).resolve().parent;P=B/'public-review-proposal';load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
d=load(P/'sashchiuk2004.json');units=load(B/'source-audit.json')['units'];mapping=load(P/'source-item-mapping.json');coverage=load(P/'source-item-coverage.json');crop=load(B/'reader-assets/crop-manifest.json');items={i['id']:i for s in d['reader_sections']for i in s['items']};R={p.stem:load(p)for p in(B/'canonical-drafts').glob('*.json')};C=[]
def ck(n,v,detail=''):C.append({'check':n,'passed':bool(v),'detail':detail})
def ptr(x,p):
 for k in p.strip('/').split('/')if p else[]:x=x[int(k)]if isinstance(x,list)else x[k.replace('~1','/').replace('~0','~')]
 return x
def evok(e):return e['source_id']=='sashchiuk2004'and e['document_role']=='main'and 1<=e['pdf_page']<=7
ck('147 reader items',len(items)==147);ck('184 exact source units',set(mapping)=={u['id']for u in units}and len(mapping)==184);ck('Current source hash',coverage['source_audit_sha256']==sha(B/'source-audit.json'));ck('Exact mapping file',coverage['unit_to_reader_items']==mapping)
for uid,ids in mapping.items():
 ck(uid+'/targets',bool(ids)and set(ids)<=set(items))
 for i in ids:ck(uid+'/'+i+'/reverse',uid in items[i]['source_audit_unit_ids'])
facts=[];links=[]
for i in items.values():
 ck(i['id']+'/source evidence',bool(i['evidence'])and all(evok(e)for e in i['evidence']));ck(i['id']+'/no training',i['training_eligible']is False);ck(i['id']+'/no physical batch',i['sample_scope']['physical_batch_id']is None)
 for x in i['canonical_links']:
  try:ptr(R[x['record_id']],x['json_pointer']);ok=True
  except(KeyError,ValueError,IndexError):ok=False
  ck(i['id']+'/'+x['record_id']+x['json_pointer']+'/link',ok);links.append(x)
 for f in i['facts']:
  facts.append(f);obj=ptr(R[f['canonical_record_id']],f['json_pointer'])
  if f['json_pointer'].startswith('/measurements/'):
   q=obj['value'];ck(f['id']+'/sample',f['sample_id']==obj['sample_id']);ck(f['id']+'/measurement ID',f['canonical_measurement_id']==obj['id'])
  else:q=obj
  ck(f['id']+'/exact canonical quantity',f['canonical_quantity']==q);ck(f['id']+'/unit',f['unit']==q.get('unit'));ck(f['id']+'/approximate',f['approximate']==q.get('approximate',False));ck(f['id']+'/no training',f['training_eligible']is False);ck(f['id']+'/evidence',bool(f['evidence'])and all(evok(e)for e in f['evidence']))
  if q.get('status')=='not_reported':ck(f['id']+'/missing value display',f['value']=='Not reported')
  if q.get('status')=='inherited':ck(f['id']+'/inherited qualifier',bool(f.get('qualifier')))
 for x in i['sample_scope'].get('canonical_sample_links',[]):ck(i['id']+'/'+x['sample_id']+'/sample pointer',ptr(R[x['record_id']],x['json_pointer'])['sample_id']==x['sample_id'])
expected_m={(rid,m['id'])for rid,r in R.items()for m in r['measurements']};actual_m={(f['canonical_record_id'],f['canonical_measurement_id'])for f in facts if'canonical_measurement_id'in f};ck('137 measurements all exact',expected_m==actual_m and len(actual_m)==137)
expected_o={(rid,'/operations/'+str(j))for rid,r in R.items()for j,o in enumerate(r['operations'])};actual_o={(x['record_id'],x['json_pointer'])for x in links if x['json_pointer'].startswith('/operations/')and x['json_pointer'].count('/')==2};ck('47 operations all linked',expected_o<=actual_o and len(expected_o)==47)
expected_p={(rid,f'/operations/{j}/parameters/{k}')for rid,r in R.items()for j,o in enumerate(r['operations'])for k in o['parameters']};actual_p={(f['canonical_record_id'],f['json_pointer'])for f in facts if f.get('basis')=='operation_parameter'};ck('All operation parameters',expected_p==actual_p)
expected_s=set();expected_mat=set();expected_opt=set()
for rid,r in R.items():
 for j,s in enumerate(r['stocks']):
  for k in s['concentrations']:expected_s.add((rid,f'/stocks/{j}/concentrations/{k}'))
  for n,c in enumerate(s['components']):
   for k in c['quantities']:expected_s.add((rid,f'/stocks/{j}/components/{n}/quantities/{k}'))
 for j,m in enumerate(r['materials']):
  for k in m['quantities']:expected_mat.add((rid,f'/materials/{j}/quantities/{k}'))
 for j,opt in enumerate(r.get('condition_options',[])):
  for k in opt['parameters']:expected_opt.add((rid,f'/condition_options/{j}/parameters/{k}'))
actual_s={(f['canonical_record_id'],f['json_pointer'])for f in facts if f['json_pointer'].startswith('/stocks/')};actual_mat={(f['canonical_record_id'],f['json_pointer'])for f in facts if f['json_pointer'].startswith('/materials/')};actual_opt={(f['canonical_record_id'],f['json_pointer'])for f in facts if f['json_pointer'].startswith('/condition_options/')}
ck('All stocks',expected_s==actual_s);ck('All reagent quantities',expected_mat==actual_mat);ck('All purity option quantities',expected_opt==actual_opt);ck('251 typedfacts',len(facts)==251)
ck('67 references',all(f'reference-{n:02}'in items for n in range(1,68))and len(d['referenced_methods'])==67)
def norm(t):return re.sub('[^a-z0-9]','',unicodedata.normalize('NFKD',t).lower())
for ref in load(B/'reference-candidates.json'):ck('Reference'+str(ref['number'])+'/complete bibliography',norm(ref['text'])in norm(items[f'reference-{ref["number"]:02}']['text']))
ck('Identity',d['paper_id']==d['source_group']=='sashchiuk2004'and d['doi']=='10.1021/nl0345116'and d['paper']['year']==2004);ck('Corpus IDs',d['corpus_paper_id']=='paper-adc6656f392b990ec3de'and d['corpus_document_ids']==['doc-7075b083635013db0673'])
SH='72684e3bf22a2ef173ea1d6d6e31648a1222b2b15bc069bb8fe6cef8d1876a33';ck('Main only correct hash',len(d['documents'])==1 and d['documents'][0]['sha256']==SH and d['documents'][0]['page_count']==7);ck('SI gap explicit',d['supporting_information']['status']=='not_located'and d['supporting_information']['scientific_pages']==0)
def has(i,*terms):ck(i+'/source meaning',all(t in items[i]['text']for t in terms))
has('lead-source','exact salt formula'if'exact salt formula'in items['lead-source']['text']else'An exact salt formula','not specified');has('selenium','no isolated TBP','one molecular species');has('topo','6.0 g','90% or 99%');has('argon','glovebox','flowing argon');has('low-stock','0.25:0.6:50','relative mass parts','0.25:0.6:0.5');has('intermediate-stock','0.5:1.2:50','0.5:1:50');has('high-stock','40 min','not shown')
has('individual-growth','118 °C','15 min','70 °C','approximately 5 min');has('heated-growth','up to 150 min','gradually','fast heating');has('wire-intermediate','90 min','5%','contradictory');has('wire-high','40 min','not shown');has('aliquot-quench','aliquots','1 mL');has('purification','methanol–butanol','no recovery yield');has('microscopy-method','4 kV','200 kV','300 kV','no elemental spectrum')
has('device-materials','p-doped','200 nm','trimethylsilane','PMMA','Ti/Au');has('device-positioning','anneal','not reported');has('contact-optimization','not disclosed','incomplete');has('electrical-method','room temperature','no gate-dependent result')
has('individual-morphology','3.5–10.0 nm','below 10%','spherical','cubic');has('individual-hrtem','5 nm','5 min','3.05 Å','15 min');has('sphere-morphology','10/25/40','50–450','50–500');has('sphere-saed','actual selected-area','not substituted');has('sphere-growth','plateau above 50','no exact digitized');has('wire-overview','60–150','1–5','20 to 150');has('wire-saed','020','[100]','6.1 Å','not shown');has('bent-wire','10 nm','3.05 Å','[100]');has('device-sem','10.0 kV','6.6 mm','×18.0k','not assigned');has('electrical-specimens','110×700','60×1000','150×1200','squares','circles','triangles')
has('absorption-cohorts','30, 35 and 40','0.5:1.2:50','0.5:1:50','not established');has('absorption-spectrum','1000','1600','0.775–1.240','arbitrary');has('absorption-shift','0.04 eV','0.5 eV','separate comparisons');has('conductivity','0.15','7.0','3.5×10⁴','not tabulated');has('conductivity-comparators','55×10⁻³','10–20','not additional specimens')
has('dipole-equation','500 D','10 nm','diameter');has('interaction-energy','single μ','−28','8.9×10⁻¹²','dimensional');has('entropy','Negative ΔS alone does not establish');has('topo-impurities','15%','not reported');has('internal-field','7.0×10³','18 kΩ','no corrected');has('capacitance','1.5×10⁻¹⁸','2.7×10⁻¹⁴','not direct');has('transfer-energy','76 meV','100 meV','not conclusively');has('barrier','7.0 µeV','20 µeV','external reference');has('model-limits','unsquared μ','diameter','No independent recalculation')
has('structure-boundary','no refined atomic coordinates','XRD','photoluminescence','Raman');has('coverage','No supporting-information declaration');has('identity','2004','2003');has('terminology-conflicts','voltage per nanocrystal','gradual','fast');has('missing-fields','absolute stock charges','yield','specimen-to-batch')
audited=load(B/'canonical-records-audit.json')['record_hashes']
for rid,h in audited.items():ck(rid+'/current audited canonical',sha(B/'canonical-drafts'/(rid+'.json'))==h)
ck('PbSe only current material',set(d['material_evidence_records'])=={'PbSe'});ck('All material evidence resolves',set(d['material_evidence_records']['PbSe'])<=set(R));ck('Four routecontext keys',set(d['route_evidence_contexts'])=={'sashchiuk-2004-'+k for k in ['individual-low','sphere-intermediate','wire-intermediate','wire-high']})
ck('Individual route no wire electrical context',not set(d['route_evidence_contexts']['sashchiuk-2004-individual-low'])&{'sashchiuk-2004-electrical','sashchiuk-2004-wire-structure','sashchiuk-2004-absorption'})
assets=d['figures']+d['tables']+d['schemes']+d['equations']+d['source_notes'];ac={x['id']:x for x in assets};cm={x['id']:x for x in crop['assets']};rows=[]
ck('13 originalassets',len(ac)==len(cm)==13 and set(ac)==set(cm));ck('Fivefigures no tables',len(d['figures'])==5 and not d['tables']and not d['schemes']);ck('All13onPbSe hub',set(d['material_original_asset_ids']['PbSe'])==set(ac))
for aid,a in ac.items():
 c=cm[aid];h=sha(B/'reader-assets'/c['relative_asset']);ck(aid+'/exact bytes',h==a['public_asset_sha256']==c['sha256']);ck(aid+'/page source',a['page']==c['source_pdf_page']and a['asset_provenance']['source_sha256']==c['source_sha256']==SH);ck(aid+'/links resolve',set(a['sample_links'])<=set(R));ck(aid+'/crop geometry',a['asset_provenance']['crop_bbox_pdf_points_top_left']==c['crop_bbox_pdf_points_top_left']);ck(aid+'/not training',a['training_eligible']is False);ck(aid+'/no premature runtime claim',a['reader_render_verified']is False and a['reviewed']is False)
 rows.append({'id':aid,'sha256':h,'source_page':a['page'],'source_semantics_reviewed':True,'visual_inspection':'Actually viewed in one of four source-compared contact sheets; all captions/axes/scale labels retained. Inline-method/equation continuation crops intentionally disclose boundary.'})
ck('Figure1 mixedsourcepopulations only',set(ac['figure-1']['sample_links'])=={'sashchiuk-2004-individual-structure','sashchiuk-2004-sphere-structure'});ck('Figure2 ambiguouswirecontext only',ac['figure-2']['sample_links']==['sashchiuk-2004-wire-structure']);ck('Figure3 nothigh40exactroute',ac['figure-3']['sample_links']==['sashchiuk-2004-wire-structure']);ck('Figure4 opticalonly',ac['figure-4']['sample_links']==['sashchiuk-2004-absorption']);ck('Figure5deviceandtransportonly',set(ac['figure-5']['sample_links'])=={'sashchiuk-2004-device-fabrication','sashchiuk-2004-electrical'});ck('Dipolecropmodelonly',ac['dipole-model']['sample_links']==['sashchiuk-2004-assembly-model']);ck('Transportcropmodelonly',ac['transport-model']['sample_links']==['sashchiuk-2004-transport-model'])
manual=[
'All147reader items read and compared with the full7page source inventory, including67individual referenceentries. All184sourceunits mapbidirectionally to thecorrectsemanticprose; exact originalfigures preserve axes/labels withoutdigitizedimaginarytables.',
'All 137 measurements, 47 operations and 251 typed facts resolve to exact audited canonical objects. Ratios are mass parts; missing absolute charges, unknown Pb-cHxBu identity, butanol isomer and TOPO grade alternatives remain explicit. The eight formerly missing purity-option pointers are now present.',
'The15min low-routeendpoint is separated fromapproximately5minFigure1A; sphere10/25/40min andoptical30/35/40min remainindependent aliquotcohorts. Medium/high stockcaptionconflicts do notforceFigure2/3intotheunshown40minrecipe.',
'Both originalSAEDimages are retained. Figure5threewirewidth/lengthsymbols arecorrectlypaired; representativeSEM isnotassignedtoonecurve. General4kV andimage10kV,6.6mm,18k overlaysareseparate.',
'Calculateddipole/enthalpy/internalfield/capacitance/RC/transferenergy/barrier valuesstaymodels. Literalunusual equations/sourceconventions andnegativeentropylogicalcaveatpreserved. Noexperimentalgate/temperature/PL/Raman/XRDdataset fabricated.',
'Actually viewed all13originalcrops onfourcontact sheets againstoriginalsourcepages. Completefigurepanels/captions/scale bars/axes intact; methods/modelcolumns have disclosedcontinuations, withpairedexcerpts preserving the missing halves. Alloriginalsourceprocessing unchanged.',
'No new currentmaterial created fromcited priornanocrystal/devicecomparators. ExistingPbSe materialscope includes relevantcontribution; idealreferencegeometry isseparatelylabelled.',
'This is an independent scientific/file-link audit oftheprivatecandidate. Publicreview/browserflags remainfalse; rootownsactualrendering/build/publication. NoSitewritesordownloads.']
failed=[x for x in C if not x['passed']];out={'status':'passed'if not failed else'failed','source_id':'sashchiuk2004','audited_utc':datetime.now(timezone.utc).isoformat(),'reader_sha256':sha(P/'sashchiuk2004.json'),'source_audit_sha256':sha(B/'source-audit.json'),'source_map_sha256':sha(P/'source-item-mapping.json'),'canonical_record_hashes':audited,'crop_manifest_sha256':sha(B/'reader-assets/crop-manifest.json'),'reader_item_count':len(items),'source_unit_count':len(units),'measurement_count':len(expected_m),'operation_count':len(expected_o),'typed_fact_count':len(facts),'asset_count':len(ac),'assets':rows,'visual_coverage':[{'path':str(B/'reader-assets'/f'contact-{i}.png'),'sha256':sha(B/'reader-assets'/f'contact-{i}.png'),'actually_viewed':True}for i in range(1,5)],'check_count':len(C),'checks':C,'failure_count':len(failed),'failures':failed,'manual_review':manual,'site_mutated':False,'browser_verified':False}
(B/'reader-source-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8');(B/'reader-source-audit.md').write_text('# Sashchiuk 2004 independent reader audit\n\n'+out['status']+'; 147 items, 184 source units, 137 measurements, 47 operations, 251 typed facts and 13 original assets. '+str(len(C))+' supporting checks; '+str(len(failed))+' failures.\n\n'+'\n\n'.join(manual)+'\n\nReader SHA256 `'+out['reader_sha256']+'`. No Site edits or browser verification claim.\n',encoding='utf8');print(json.dumps({'status':out['status'],'reader_sha256':out['reader_sha256'],'checks':len(C),'failures':failed}))
if failed:raise SystemExit(1)
