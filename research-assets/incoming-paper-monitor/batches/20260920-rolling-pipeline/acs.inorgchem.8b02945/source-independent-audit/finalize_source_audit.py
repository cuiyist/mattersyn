"""Bind independent v1 findings and the author's narrowly corrected v2 overlay."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,copy
O=Path(__file__).resolve().parent;F=O.parent;R=F/'source-extraction-revision-2'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf8'))
def write(p,j):
 if p.exists():raise RuntimeError('Refuse to replace frozen audit '+str(p))
 p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def diff(a,b,p=''):
 if type(a)!=type(b):yield p,a,b
 elif isinstance(a,dict):
  for k in sorted(set(a)|set(b)):
   if k not in a or k not in b:yield p+'/'+k,a.get(k,'<absent>'),b.get(k,'<absent>')
   else:yield from diff(a[k],b[k],p+'/'+k)
 elif isinstance(a,list):
  if len(a)!=len(b):yield p,a,b
  else:
   for i,(x,y) in enumerate(zip(a,b)):yield from diff(x,y,p+'/'+str(i))
 elif a!=b:yield p,a,b
def walk(j,p=''):
 yield p,j
 if isinstance(j,dict):
  for k,v in j.items():yield from walk(v,p+'/'+k)
 elif isinstance(j,list):
  for k,v in enumerate(j):yield from walk(v,p+'/'+str(k))
checks=[]
def ck(n,ok):
 checks.append({'check':n,'passed':bool(ok)})
 if not ok:raise AssertionError(n)
base=read(F/'package-freeze.json');mech=read(O/'mechanical-checks-v1.json');frozen=read(R/'package-freeze.json');mapping=read(R/'effective-file-map.json')
ck('3391 baseline supporting checks pass',mech['executed_checks']==3391 and mech['passed_checks']==3391 and not mech['failed_checks'])
ck('exact corrected freeze',sha(R/'package-freeze.json')=='9f76d5810d3bd2caef97dca7c96fc6ae8ad0a8362bdab8f9ac2d4811867de816')
ck('base exact preserved',sha(F/'package-freeze.json')==frozen['base_freeze_sha256']==mapping['base_freeze_sha256'])
for fn,e in base['bound_files'].items():ck('preserved v1 '+fn,sha(F/fn)==e['sha256'])
for fn,h in frozen['bound_files'].items():ck('v2 bound '+fn,sha(fn)==h)
ck('four effective replacements',set(mapping['replacements'])=={'source-facts.json','source-inventory.json','original-assets-manifest.json','page-coverage.json'})
for fn,e in mapping['replacements'].items():ck('effective map exact '+fn,sha(e['path'])==e['sha256'] and frozen['effective_files'][fn]==e)
old=read(F/'source-facts.json');new=read(R/'source-facts.json')
expected={
 'source-facts.json':{'/facts/33/evidence',*[f'/facts/33/quantities/{i}/evidence' for i in range(4)],'/facts/34/quantities/1/meaning','/facts/43/evidence','/facts/43/quantities/0/evidence','/figures/5/sample_context_ids',*[f'/missingness/{i}/evidence' for i in [3,4,5]],'/sample_contexts/22/evidence'},
 'source-inventory.json':{*[f'/remaining_gaps/{i}/evidence' for i in [3,4,5]],*[f'/{k}/{i}/{field}' for k in ['semantic_units','units'] for i in [33,43] for field in ['evidence','source_payload_ids']]},
 'original-assets-manifest.json':{'/assets/5/sample_context_ids'},'page-coverage.json':{'/pages/3/source_unit_ids'}
}
deltas={}
for fn,allowed in expected.items():
 ds=list(diff(read(F/fn),read(R/fn)));ck('only requested delta paths '+fn,{p for p,_,_ in ds}==allowed)
 deltas[fn]=[{'path':p,'before':a,'after':b} for p,a,b in ds]
 for p,a,b in ds:
  if p.endswith('/evidence'):
   ck('existing evidence retained '+fn+p,all(x in b for x in a))
   for e in b:
    if e not in a:ck('new exact main4 locator '+fn+p,e['document_role']=='main' and e['pdf_page']==4 and e['printed_page']==806 and e['source_sha256']==base['source_files'][next(k for k in base['source_files'] if k.endswith('8b02945.pdf'))] and bool(e['locator']))
  elif p.endswith('source_payload_ids'):ck('only main4 payload add '+p,b==a+['friedfeld2019-main-p04'])
  elif p.endswith('sample_context_ids'):ck('both S1 source identities '+p,b==['phenylacetate-reference','nmr-labeled'])
  elif p.endswith('/meaning'):ck('uncertainty definition honest',a=='diameter standard deviation' and b=='reported ± diameter uncertainty; statistical definition unspecified')
  elif p.endswith('source_unit_ids'):ck('only two main4 units added',set(b)-set(a)=={'friedfeld2019-unit-fact-growth-time','friedfeld2019-unit-fact-scheme2-model'} and set(a)<=set(b))
 # All other scalar science and metadata leaves remain unchanged, independently of author assertion.
 before=dict(walk(read(F/fn)));after=dict(walk(read(R/fn)))
 for p,v in before.items():
  if isinstance(v,(dict,list)) or any(p==a or p.startswith(a+'/') for a in allowed):continue
  ck('unchanged leaf '+fn+p,p in after and after[p]==v)
ck('TEM numeric values retained',new['facts'][34]['quantities'][0]['value']==2.6 and new['facts'][34]['quantities'][1]['value']==0.5 and new['facts'][34]['quantities'][2]['value']==315)
ck('65facts153quantities',len(new['facts'])==65 and sum(len(f['quantities']) for f in new['facts'])==153)
ck('original tables remain byteidentical',sha(F/'source-tables.json')==base['bound_files']['source-tables.json']['sha256'])
ck('sample identity labels unchanged',old['sample_contexts']==[{**s,'evidence':old['sample_contexts'][i]['evidence']} if i==22 else s for i,s in enumerate(new['sample_contexts'])])
for a in read(R/'original-assets-manifest.json')['assets']:ck('all51 exact original crop bytes '+a['id'],sha(a['path'])==a['sha256'])
for fn,h in base['source_files'].items():ck('source unchanged at final '+fn,sha(fn)==h)
findings=[
 {'id':'FRIED-SRC-01','category':'evidence_locator','target':'source-facts.json /facts/43 friedfeld2019-scheme2-model and quantity','finding':'130–150°C is explicitly Scheme2 footnote on main PDF4/printed806; original fact only citedmain6.','required_change':'Append precise main4 Scheme2-footnote evidence and mirrored inventory/page/source-context evidence; retain main6 mechanism prose.','numeric_change_required':False},
 {'id':'FRIED-SRC-02','category':'evidence_locator','target':'source-facts.json /facts/33 friedfeld2019-growth-time and four quantities','finding':'>8h,within20min,near0.2a.u.,550–650nm are printed on main PDF4/806; original onlycitedmain3 with continuation text.','required_change':'Append exact main4 evidence and mirrored inventory/page coverage.','numeric_change_required':False},
 {'id':'FRIED-SRC-03','category':'uncertainty_definition','target':'source-facts.json /facts/34/quantities/1/meaning','finding':'The source reports2.6±0.5nm for315particles without specifying standarddeviation or standarderror; original typed meaning asserted standarddeviation.','required_change':'Keep0.5nm exactly; label reported±uncertainty with statistical definition unspecified.','numeric_change_required':False},
 {'id':'FRIED-SRC-04','category':'sample_context_mapping','target':'source-facts.json /figures/5 and matching originalasset','finding':'FigureS1 explicitlycompares natural-abundance and labeledMSC, but typed sample list onlyincludednatural reference.','required_change':'Addexistingnmr-labeled context tofigure and matchingasset; retainunknownexactphysicalbatch linkage.','numeric_change_required':False}
]
scope={
 'original_main_pages_read_and_viewed':list(range(1,9)),'original_si_pages_read_and_viewed':list(range(1,26)),
 'independent_precomparison_reading_checkpoint':{'path':str(O/'independent-reading-checkpoint.json'),'sha256':sha(O/'independent-reading-checkpoint.json')},
 'actual_manual_comparison':['All65 claim prose and153typedquantity meanings/units/bounds againstthe prior reading and targeted main/SI rereads.','All39material identities,5stocks/10components,16protocols/34operations and62samplecontexts read for actual source role and aliquot/batch limits.','All185tablefields manually compared:16Table1,12S22,72printedfitcoefficients,30Scherrerprose,30Gaussianbox,25NMRfields. All31equationentries checked.','All44figures,2schemes,56references andoriginalfigure/sampleassignments read. All51selectedcrops actuallyviewed across9contacts; main4/6/7 andSI24/25 originaldetails reopened asneeded.'],
 'mechanical_comparison':['Exact author/source/crop hashes and207inventoryunit pointers.','All51crops replayed pixel-identically fromfresh original PDFiumrender at each manifestedresolution, with no authorbuilderexecution.','Independenttablebaseline compared mechanically; NMR and mainFigure5 additions checked directly against originalmain7/main5.'],
 'not_claimed':['No curve digitization or raw experimental refit.','No outside literature retrieval or validation of cited papers.','No current atomic-coordinate/CIF model, exact physical batch joins, training eligibility or publication approval.','No repeat all-page manual read in revision2: only the four precise corrections and unchanged source/values/assets rechecked.']}
bound1=dict(mech['bound_files']);bound1[str(O/'mechanical-checks-v1.json')]=sha(O/'mechanical-checks-v1.json')
for c in (F/'source-render/crop-contacts').glob('*.png'):bound1[str(c)]=sha(c)
v1={'schema':'mattersyn-independent-source-audit/1','source_id':'friedfeld2019','source_doi':'10.1021/acs.inorgchem.8b02945','author':'/root/peng1998_reader_assets','auditor':'/root/backlog_eta','reviewer':'/root/backlog_eta','created_at':datetime.now(timezone.utc).isoformat(),'revision':1,'status':'revision_required','overall_pass':False,'source_freeze_sha256':sha(F/'package-freeze.json'),'findings':findings,'open_findings':[f['id'] for f in findings],'manual_scope':scope,'supporting_checks':3391,'supporting_checks_passed':3391,'bound_files':bound1,'limits':'Originalsource tensions are preserved; the four findings concern extractiontyping, exactlocators andmapping, not changes toreported scientificvalues.'}
write(O/'independent-audit-v1.json',v1)
(O/'independent-audit-v1.md').write_text('# Friedfeld independent source audit — revision1\n\nRevision required. All33sourcepages read/viewed before authorcomparison; all65facts,153quantities,185tablefields,34operations and51selectedcrops compared. 3,391 supportingmechanical checks pass.\n\n'+ '\n'.join('- '+f['id']+': '+f['finding']+' '+f['required_change'] for f in findings)+'\n\nNo reported numericalvalue orcrop requires alteration. Originalauthorfreeze remainsunchanged.\n',encoding='utf8')
for f in findings:f['resolution']='Verified in exact revision2 overlay; originalv1 preserved.'
receipt={'schema':'mattersyn-independent-source-delta/1','author':'/root/peng1998_reader_assets','auditor':'/root/backlog_eta','created_at':datetime.now(timezone.utc).isoformat(),'base_freeze_sha256':sha(F/'package-freeze.json'),'corrected_freeze_sha256':sha(R/'package-freeze.json'),'changed_groups':sum(len(x) for x in deltas.values()),'deltas':deltas,'executed_checks':len(checks),'passed_checks':sum(x['passed'] for x in checks),'checks':checks}
write(O/'bounded-delta-checks-v2.json',receipt)
bound2=dict(bound1)
for fn,h in frozen['bound_files'].items():bound2[fn]=h
for p in [R/'package-freeze.json',O/'bounded-delta-checks-v2.json',O/'independent-audit-v1.json',Path(__file__)]:bound2[str(p)]=sha(p)
v2={**v1,'revision':2,'created_at':datetime.now(timezone.utc).isoformat(),'status':'passed','overall_pass':True,'source_freeze_path':str(R/'package-freeze.json'),'source_freeze_sha256':sha(R/'package-freeze.json'),'base_source_freeze_sha256':sha(F/'package-freeze.json'),'effective_file_map':{'path':str(R/'effective-file-map.json'),'sha256':sha(R/'effective-file-map.json')},'effective_source_facts_sha256':sha(R/'source-facts.json'),'findings':findings,'open_findings':[],'counts':read(R/'source-inventory.json')['counts'],'fact_quantities':153,'supporting_checks':3391+len(checks),'supporting_checks_passed':3391+len(checks),'initial_comparison_checks':3391,'bounded_revision_checks':len(checks),'bound_files':bound2,'source_limitations':['The cited priorclusterstructure is not a supplied current product atomicmodel.','The 130°C30/72h comparison and S14 oleate/myristate naming remainunresolved.','S22 literal eV magnitudes, Scherrerbox/prose/HWHM differences, sourcefitcoefficients and malformedDSCrate remainasprinted.','Table1 andS6 rates remain independently located and are not reconciled byassumingidenticalrawruns.','Absorbance is a yieldproxy;noisolatedQDyield, calibratedconversion or universalphysicalbatchjoin isclaimed.','Canonical,reader,molecular,apparatus,productmodel,training andpublicationgates remainseparate.']}
write(O/'independent-audit-v2.json',v2)
md='# Friedfeld independent source audit — revision2\n\n**Passed for the exact source-extraction overlay.** Allfour bounded findings are resolved; no open extractioncorrection remains. Originalv1 files anditsfindingreport arepreserved.\n\nThe review coveredall8main+25SIpages,65facts/153typedfactquantities,39materials,5stocks/10components,16protocols/34operations,62samplecontexts,44figures,2schemes,6numericlistings/185fields,31equations and56references. All51selectedcrops wereactuallyviewed and independentlypixel-replayed fromoriginalPDFs. The 207sourceunit mappingsresolve.\n\nThe completev1comparison passed3,391mechanical checks. The boundedv2recheck passed'+str(len(checks))+'checks, includingexactallowed26changedgroups, allotherleaves, originalsources, all145v1-boundfiles andall51cropbytes. Actualmanualscope is recorded separately; revision2 doesnotclaim asecondfullpageread.\n\nCorrections: appendmainPDF4/printed806evidence forScheme2 andgrowth-time claims; qualify0.5nm asreported±uncertainty withstatisticaldefinitionunknown; addthelabeledMSCcontext toFigureS1 anditsasset. Allquantities, tablebytes, operations andscientificpixels remainunchanged.\n\nEffectivefreeze: `'+sha(R/'package-freeze.json')+'`. Effectivefacts: `'+sha(R/'source-facts.json')+'`. Use `source-extraction-revision-2/effective-file-map.json`; allotherbasefiles remain effective.\n\nSourceconflicts and upstreamrecipe/rawdata/atomicstructure limitationsremain. This pass doesnotapprove canonicalrecords, downstreamvisuals, traininglabels orpublication.\n'
md=md.replace('extractioncorrection','extraction correction').replace('allfour','all four')
(O/'independent-audit-v2.md').write_text(md,encoding='utf8')
(O/'independent-audit.json').write_bytes((O/'independent-audit-v2.json').read_bytes());(O/'independent-audit.md').write_bytes((O/'independent-audit-v2.md').read_bytes())
print(json.dumps({'audit':str(O/'independent-audit.json'),'sha256':sha(O/'independent-audit.json'),'v1_audit_sha256':sha(O/'independent-audit-v1.json'),'supporting_checks':v2['supporting_checks'],'revision_checks':len(checks),'bound_files':len(bound2),'open_findings':[]},ensure_ascii=False))
