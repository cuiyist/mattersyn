"""Build a private, source-qualified symbolic display proposal; inputs stay read-only."""
from pathlib import Path
from copy import deepcopy
from datetime import datetime,timezone
import json,hashlib,html,textwrap,shutil,re
from context_data import CARDS,SPECS,EXCLUDED_SOURCE_CONTEXTS
O=Path(__file__).resolve().parent; F=O.parents[1]
C=F/'canonical-proposal/draft-v2'; SOURCE=F/'source-extraction-revision-2'
SITE=Path('[local path redacted]')
assert not (O/'package-freeze.json').exists(),'Never overwrite a frozen proposal.'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def jsha(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def save(name,x):(O/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
checks=[]
def ck(label,v):
 checks.append({'check':label,'passed':bool(v)})
 assert v,label
for d in ['svg','previews','consumer-snapshot']:(O/d).mkdir(parents=True,exist_ok=True)
ck('canonical freeze exact',sha(C/'package-freeze.json')=='ff8767ef6a51f4184825de335dfe9906fab80e53b97e641fa534f6344f25a112')
ck('source overlay exact',sha(SOURCE/'package-freeze.json')=='9f76d5810d3bd2caef97dca7c96fc6ae8ad0a8362bdab8f9ac2d4811867de816')
audit=F/'source-independent-audit/independent-audit-v2.json'
ck('distinct source audit exact',sha(audit)=='0da964026bc39b05289890fbcda3a51ab307dfd95c7227a7f01d686a25622f6d')
ck('source audit passed',read(audit)['status']=='passed' and read(audit)['source_freeze_sha256']==sha(SOURCE/'package-freeze.json'))
records={};paths={};inputs=[C/'package-freeze.json',C/'record-manifest.json',SOURCE/'package-freeze.json',SOURCE/'source-facts.json',SOURCE/'source-inventory.json',SOURCE/'original-assets-manifest.json',audit]
for ent in read(C/'record-manifest.json')['records']:
 p=Path(ent['path']);ck(ent['record_id']+' hash',sha(p)==ent['sha256'])
 r=read(p);records[r['record_id']]=r;paths[r['record_id']]=p;inputs.append(p)
 ck(ent['record_id']+' exact record source',r['lineage']['source_group']=='friedfeld2019')
sf=read(SOURCE/'source-facts.json');facts={x['id']:x for x in sf['facts']};source_contexts={x['id']:x for x in sf['sample_contexts']}
ck('every source context explicitly considered',set(SPECS)|set(EXCLUDED_SOURCE_CONTEXTS)==set(source_contexts))
ck('no inclusion/exclusion overlap',not set(SPECS)&set(EXCLUDED_SOURCE_CONTEXTS))

def tx(x,y,s,size=22,color='#244756',anchor='start'):
 return f'<text x="{x}" y="{y}" font-family="Arial,sans-serif" font-size="{size}" fill="{color}" text-anchor="{anchor}">{html.escape(s)}</text>'
def wrap(s,x,y,width=78,size=22):return ''.join(tx(x,y+31*i,line,size) for i,line in enumerate(textwrap.wrap(s,width)))
entries=[];bykey={}
symbol_note='Symbolic source context only. No atom positions, particle envelope, phase fraction or ligand geometry is depicted.'
for key,(title,headline,detail) in CARDS.items():
 eid='friedfeld2019-'+key+'-product-symbol'
 body=tx(46,62,title,28)+tx(46,108,'Friedfeld et al. · Inorganic Chemistry 2019',21,'#687f8b')
 body+='<rect x="47" y="151" width="1006" height="318" rx="18" fill="#f1f6f8" stroke="#b5cdd7"/>'
 body+=wrap(headline,85,229,49,32)+wrap(detail,85,347,77,23)
 body+=wrap(symbol_note,51,528,84,22)+tx(51,650,'Source-scoped illustration · no atomic model or training admission',21,'#687f8b')
 svg='<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="700" viewBox="0 0 1100 700"><title>'+html.escape(title)+'</title><desc>'+html.escape(symbol_note)+'</desc><rect x="1" y="1" width="1098" height="698" rx="20" fill="white" stroke="#b9ced8"/>'+body+'</svg>'
 rel='svg/'+eid+'.svg';(O/rel).write_text(svg,encoding='utf8')
 entry={'id':eid,'name':title,'formula':'','displayFormula':headline,'depictionKind':'symbolic_context','svgPath':rel,'model2dPath':None,'model3dPath':None,'functionalGroups':[],'caption':symbol_note+' '+detail,'limitations':['No current sample coordinates or exact physical aliquot linkage.','Component and technique-local source claims do not overwrite whole-specimen composition.'],'sourceUrls':['https://doi.org/10.1021/acs.inorgchem.8b02945'],'assetHashes':{'svgPath':sha(O/rel)},'binding_approved':False,'published':False,'eligible_training':False}
 entries.append(entry);bykey[key]=entry

# Index exact frozen source claim and quantity transport. No quantities are recreated.
claim_index={};measurement_index={}
for rid,r in records.items():
 for i,m in enumerate(r['measurements']):
  for fid in facts:
   if m['id']==fid+'-claim' or m['id'].startswith(fid+'-q'):
    row={'record_id':rid,'record_sha256':sha(paths[rid]),'json_pointer':f'/measurements/{i}','measurement_id':m['id'],'canonical_measurement':deepcopy(m)}
    measurement_index.setdefault(fid,[]).append(row)
    if m['id']==fid+'-claim':
     ck(fid+' exact canonical claim',m['value']['value']==facts[fid]['claim'])
     claim_index.setdefault(fid,[]).append(row)

contexts={};bindings=[];excluded=[];coverage=[]
def exclusion_reason(rid,sid):
 if sid in EXCLUDED_SOURCE_CONTEXTS:return EXCLUDED_SOURCE_CONTEXTS[sid]
 if sid.startswith('table-context-') or sid=='source-table-context':return 'A numeric table row or fit parameter set is retained as measurement evidence, not an independent physical sample or new product.'
 if rid.endswith(('source-materials','source-context','cited-phosphine-context')):return 'Bibliographic, reagent, source-note or cited upstream context is not a current measured final product.'
 if rid.endswith('mechanistic-context'):return 'Cited prior cluster geometry and proposed monomer pathways remain source evidence; no current isolated product or coordinate binding follows.'
 if sid=='source-payload-context' or sid=='source-unit-context':return 'Aggregate source payload/unit context is not a single specimen; explicit named sample contexts are mapped separately.'
 if sid.startswith('fact-context-'):return 'This is the canonical claim/acquisition/operation evidence carrier, not another physical specimen. Supported named sample contexts have separate mappings; the complete fact remains in the reader.'
 return 'No independently supported product identity or single specimen can be assigned from this context; source data remain available without a symbolic product binding.'
for rid,r in records.items():
 for i,prod in enumerate(r['products']):
  sid=prod['sample_id'];ptr=f'/products/{i}'
  ck(rid+'/'+sid+' unique canonical sample',sum(x['sample_id']==sid for x in r['products'])==1)
  common={'record_id':rid,'sample_id':sid,'canonical_product_pointer':ptr,'canonical_product_snapshot':deepcopy(prod),'canonical_record_path':str(paths[rid]),'canonical_record_sha256':sha(paths[rid]),'canonical_product_sha256':jsha(prod)}
  if sid not in SPECS:
   row={**common,'reason':exclusion_reason(rid,sid)};excluded.append(row)
   coverage.append({'record_id':rid,'sample_id':sid,'pointer':ptr,'disposition':'excluded','reason':row['reason']});continue
  spec=SPECS[sid];entry=bykey[spec['key']];fids=['friedfeld2019-'+x for x in spec['facts']]
  ck(rid+'/'+sid+' source context exists',sid in source_contexts)
  ck(rid+'/'+sid+' all fact IDs exact',all(fid in facts and fid in claim_index for fid in fids))
  links=[deepcopy(x) for fid in fids for x in claim_index[fid]]
  evidence=list({json.dumps(ev,sort_keys=True):ev for link in links for ev in link['canonical_measurement']['evidence']}.values())
  quantities=[deepcopy(x) for fid in fids for x in measurement_index[fid] if x['measurement_id']!=fid+'-claim']
  conflicts=sorted(set(v for fid in fids for v in facts[fid].get('conflict_ids',[])))
  caption=spec['caption']+' The card is symbolic; it supplies no atomic coordinates, particle envelope, ligand geometry or exact training pair.'
  row={'sample_id':sid,'label':spec['label'],'registry_id':entry['id'],'caption':caption,
       'phase':{'value':spec['phase'],'status':'reported_context' if spec['phase'] else 'not_assigned','evidence':evidence,'note':'This display preserves the canonical unknown composition and phase fields. Any named phase is limited to the explicitly described source comparison or local evidence.'},
       'morphology':deepcopy(prod['morphology']),'source_fact_ids':fids,
       'source_fact_links':[{'path':str(SOURCE/'source-facts.json'),'json_pointer':'/facts/'+str(sf['facts'].index(facts[fid])),'sha256':jsha(facts[fid])} for fid in fids],
       'source_context_snapshot':deepcopy(source_contexts[sid]),'canonical_product_pointer':ptr,'canonical_product_snapshot':deepcopy(prod),
       'canonical_claim_links':links,'canonical_quantity_links':quantities,'conflict_ids':conflicts,
       'same_physical_batch_asserted':False,'projection_kind':'source_scoped_symbolic_context','training_eligible':False,'atomic_model':False,'binding_approved':False}
  contexts.setdefault(rid,[]).append(row)
  bindings.append({**common,'registry_id':entry['id'],'entry_sha256':jsha(entry),'source_fact_ids':fids,'symbol_key':spec['key']})
  coverage.append({'record_id':rid,'sample_id':sid,'pointer':ptr,'disposition':'mapped','registry_id':entry['id']})

total=sum(len(x['products']) for x in records.values())
ck('complete product-slot accounting',len(coverage)==total==len(bindings)+len(excluded))
ck('coverage unique',len({(x['record_id'],x['pointer']) for x in coverage})==total)
ck('all source context specifications used',set(x['sample_id'] for x in bindings)==set(SPECS))
ck('all symbols used',set(x['symbol_key'] for x in bindings)==set(CARDS))
ck('no geometry paths',all(e['model2dPath'] is None and e['model3dPath'] is None for e in entries))
ck('no asserted whole formulas',all(e['formula']=='' for e in entries))
ck('prior and model contexts excluded',all(x['record_id']!='friedfeld-2019-mechanistic-context' for x in bindings))
ck('only exact structural contexts assign phase',all(row['sample_id'] in ['xrd-context','temp-150-tem','temp-250-tem'] for rows in contexts.values() for row in rows if row['phase']['value']))
notice='Optical conversion conditions, local TEM specimens, powder phase comparisons, Scherrer domains, NMR solutions and thermal/pretreatment contexts remain separate. InP/In2O3 diffraction assignments do not establish pure whole products. Prior cluster coordinates and proposed monomers are not supplied current structures. No atomic model, exact aliquot join or structure–recipe training pair is admitted.'
save('registry-additions.json',{'schemaVersion':'1.0','source_id':'friedfeld2019','entries':entries,'binding_approved':False})
save('product-contexts-additions.json',{'recordContexts':contexts,'sourceNotices':{'friedfeld2019':notice}})
publickeys=['sample_id','label','registry_id','caption','phase','morphology','source_fact_ids','conflict_ids','same_physical_batch_asserted','projection_kind','training_eligible','atomic_model','binding_approved']
save('public-product-contexts-proposal.json',{'recordContexts':{rid:[{k:deepcopy(row[k]) for k in publickeys} for row in rows] for rid,rows in contexts.items()},'sourceNotices':{'friedfeld2019':notice}})
save('bindings.json',{'schema':'mattersyn-symbolic-product-context-proposal/1','author':'/root/peng1998_reader_assets','status':'private_author_proposal_pending_distinct_audit','canonical_package':{'path':str(C/'package-freeze.json'),'sha256':sha(C/'package-freeze.json')},'canonical_manifest':{'path':str(C/'record-manifest.json'),'sha256':sha(C/'record-manifest.json')},'source_freeze':{'path':str(SOURCE/'package-freeze.json'),'sha256':sha(SOURCE/'package-freeze.json')},'source_audit':{'path':str(audit),'sha256':sha(audit)},'bindings':bindings,'excluded_contexts':excluded,'scientific_records_unchanged':True,'independent_approval':False,'canonical_independent_review':'separate gate; no approval inferred'})
save('slot-coverage.json',{'total_slots':total,'mapped':len(bindings),'excluded':len(excluded),'source_contexts':len(source_contexts),'rows':coverage})
save('public-asset-proposal.json',{'status':'unapproved_public_candidates','assets':[{'path':str(O/e['svgPath']),'sha256':e['assetHashes']['svgPath'],'public_path':'assets/chemical-registry/friedfeld2019-products/'+Path(e['svgPath']).name,'entry_id':e['id']} for e in entries],'excluded':'Original PDFs/SI, full source pages/text, source snapshots, private bindings and test artifacts are not public image assets.'})
originals={d['source_path']:d['sha256'] for d in read(F/'source-preparation.json')['documents']}
for p,digest in originals.items():ck('original source hash '+Path(p).name,sha(p)==digest)
save('input-bindings.json',{'files':{str(p):sha(p) for p in inputs},'source_originals':originals,'no_mutations':True})
save('author-validation.json',{'author':'/root/peng1998_reader_assets','status':'passed_author_mapping_checks_visuals_pending','check_count':len(checks),'checks':checks,'counts':{'canonical_records':len(records),'canonical_product_context_slots':total,'contexts':len(bindings),'records_with_mappings':len(contexts),'excluded_contexts':len(excluded),'symbols':len(entries),'atomic_models':0},'independent_audit':False,'browser_approval':False})
consumer=SITE/'dist/crystal-viewer.mjs';shutil.copyfile(consumer,O/'consumer-snapshot/crystal-viewer.mjs')
save('consumer-snapshot/provenance.json',{'path':str(consumer),'sha256':sha(consumer),'snapshot':'crystal-viewer.mjs','purpose':'Actual consumer function tests only; no mounted-browser approval.'})
(O/'README.md').write_text('''# Friedfeld 2019 symbolic product contexts

This private author proposal uses the existing `recordContexts` / `sourceNotices` consumer in `crystal-viewer.mjs`. Every canonical product/sample slot has a mapped or excluded disposition. A slot is not a physical replicate. Only the allowlisted SVGs are public image candidates. Rewrite each registry `svgPath` to its exact public path during reviewed integration; use the path-free `public-product-contexts-proposal.json` for the public context map. No consumer architecture change is required.

No geometry, CIF or atomic model is created. Optical conversion conditions do not inherit TEM diameters or powder phase identities. The InP/In2O3 comparison is a component-level source assignment, not a pure whole-product formula. TEM agglomerates, spherical-particle statistics and coherent diffraction domains remain separate. Prior phenylacetate-cluster coordinates are cited evidence only. NMR mixtures and low-temperature intermediates do not receive solved complexes. The 130 °C 30/72 h and oleate/myristate ambiguities remain visible.

The frozen canonical draft-v2 remains unchanged. Source revision 2 has a distinct passed audit; canonical review, this proposal’s independent review, integration and browser approval are separate gates. Any later canonical change requires a preserved, explicitly verified overlay.
''',encoding='utf8')
print(json.dumps({'counts':read(O/'author-validation.json')['counts'],'checks':len(checks)}))
