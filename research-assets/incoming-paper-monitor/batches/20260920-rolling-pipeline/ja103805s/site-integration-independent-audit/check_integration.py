import json,hashlib,copy,sys,re,ast
from pathlib import Path
from datetime import datetime,timezone
from inspect_delta import load,diff
O=Path(__file__).resolve().parent;E=O.parent;I=E/'site-integration-proposal';P=I/'v2';B=I/'base-site-inputs';S=Path(r'[local path redacted]')
checks=[];findings=[];bound={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bind(p):bound[str(p)]={'path':str(p),'sha256':sha(p)};return sha(p)
def read(p):bind(p);return load(p)
def ck(v,msg):
 checks.append({'check':msg,'passed':bool(v)})
 if not v:findings.append(msg)
manifest=read(I/'site-import-manifest.json');delta=read(I/'code-delta.json');oldhash=read(I/'base-record-hashes.json');refine=read(I/'reader-refinement-delta.json');adapter=read(I/'product-adapter-integration.json')
ck(len(oldhash)==480,'480 preserved record hashes recorded')
records={}
for p in (S/'data/records').glob('*.json'):
 r=read(p);records[r['record_id']]=r
 if p.name in oldhash:ck(sha(p)==oldhash[p.name],'Old canonical unchanged '+p.stem)
new={p.stem:read(p) for p in (P/'records').glob('*.json')}
ck(len(records)==512 and set(records)=={Path(n).stem for n in oldhash}|set(new),'Only32 added canonical records')
for rid,r in new.items():ck(records[rid]==r and sha(S/'data/records'/(rid+'.json'))==sha(P/'records'/(rid+'.json')),'Imported record exact '+rid)
ck(manifest['promotion_audit_sha256']==bind(O/'promotion-delta-audit.json'),'Imported approval binds passed promotion audit')
ck(manifest['proposal_freeze_sha256']==bind(P/'package-freeze.json'),'Imported frozen v2')
for rel in {c['file'] for c in delta['changes']}|set(delta['cache_revision_files']):
 if rel in {'dist/inventory.html','dist/library.html','dist/dataset.html'}:continue # generated pages checked below against actual data
 base=B/rel;current=S/rel;bind(base);bind(current);expected=base.read_text(encoding='utf-8')
 if rel=='dist/protocol-visuals.mjs':expected=delta['new_import']+'\n'+expected
 for c in delta['changes']:
  if c['file']==rel:ck(expected.count(c['before'])==c['occurrences'],'Exact original code token '+rel+' '+c['before'][:32]);expected=expected.replace(c['before'],c['after'])
 if rel in delta['cache_revision_files']:expected=expected.replace('0.24.0-r1','0.25.0-r1')
 for c in refine['changes']:
  if c['path']==rel:ck(expected.count(c['old'])==c.get('count',1),'Exact presentation token '+rel+' '+c['old'][:32]);expected=expected.replace(c['old'],c['new'])
 if rel=='scripts/build_dataset.py':expected=expected.replace("links=[dict(l,url=('../'+l['url'] if l['url'].startswith('paper-review.html') else record_href(l['url']))) for l in r['context_links']]","links=[dict(l,url=('../'+l['url'] if l['url'].startswith('paper-review.html') else record_href(l['url'])),relation=('Source document review' if r['lineage']['source_group']=='evans2010' and l['relation']=='source_reader_pending_independent_audit' else l['relation'])) for l in r['context_links']]")
 if rel=='dist/crystal-viewer.mjs':expected="import {mountEvansSpecies9} from './evans2010-products.mjs';\n"+expected.replace(adapter['before'],adapter['after'])
 if rel.endswith('.html') and '<a href="progress.html">Review progress</a>' not in expected:expected=expected.replace('Synthesis dataset</a></nav>','Synthesis dataset</a><a href="progress.html">Review progress</a></nav>')
 ck(current.read_text(encoding='utf-8')==expected,'Only declared code/cache changes '+rel)
reg0=read(B/'dist/assets/chemical-registry/registry.json');reg=read(S/'dist/assets/chemical-registry/registry.json');add=read(P/'molecules/registry-additions.json')
ex=copy.deepcopy(reg0)
for e in add['entries']:e['published']=True;ex['entries'].append(e)
ck(reg==ex,'Registry merge only50 new approved entries plus publication-candidate flag')
b0=read(B/'dist/assets/chemical-registry/bindings.json');b=read(S/'dist/assets/chemical-registry/bindings.json');addb=read(P/'molecules/bindings-additions.json');ex=copy.deepcopy(b0)
for k in ['recordBindings','bindingNotes','sourceRecordSha256']:
 ck(not(set(ex.get(k,{}))&set(addb[k])),'No old binding overwritten '+k);ex.setdefault(k,{}).update(addb[k])
ck(b==ex,'Bindings merge only32 Evans records')
for k in ['recordBindings','bindingNotes','sourceRecordSha256']:ck(len(set(b[k])-set(b0.get(k,{})))==32,'32 added binding record maps '+k)
display0=read(B/'data/measurement-display.json');display=read(S/'data/measurement-display.json');newmap=read(P/'record-structural-measurements.json');ex=copy.deepcopy(display0);ex.setdefault('record_structural_measurement_ids',{}).update(newmap)
source_reader=read(P/'reader/evans2010.json');properties={rid:set() for rid in new}
for sec in source_reader['reader_sections']:
 if sec['id']=='properties':
  for item in sec['items']:
   for link in item.get('canonical_links',[]):
    mt=re.match(r'^/measurements/(\d+)(?:/|$)',link['json_pointer'])
    if mt:properties[link['record_id']].add(new[link['record_id']]['measurements'][int(mt[1])]['id'])
ck(sum(map(len,properties.values()))==193,'193 exact audited-reader property fields')
ex['record_property_measurement_ids']={k:sorted(v) for k,v in properties.items()}
ck(display==ex,'Global measurement property classifier unchanged; only32 scoped entries added')
ck(all(not(set(newmap[k])&v) for k,v in properties.items()),'Properties and structural contexts do not overlap')
reader0=read(P/'reader/evans2010.json');reader=read(S/'data/paper-reviews/evans2010.json');ex=copy.deepcopy(reader0);ex['presentation_gates']['site_integration']=True;ex['publication_status']='Source-reviewed contribution integrated locally; browser and live release tracked separately.';ex['audit_details']['promotion_audit_sha256']=sha(O/'promotion-delta-audit.json')
ck(reader==ex,'Reader only local-import metadata changes')
ck(reader['presentation_gates']['browser_render'] is False and reader['presentation_gates']['publication'] is False,'Reader does not infer browser/publication approval')
for a in read(P/'promotion-manifest.json')['public_assets']:ck(bind(S/'dist'/a['public_path'])==a['sha256'],'Installed approved asset '+a['public_path'])
sys.path.insert(0,str(S/'scripts'));import dataset_lib,build_dataset
for name in ['dataset_lib.py','schema_definition.py','build_dataset.py']:bind(S/'scripts'/name)
countold=0;countnew=0;oldtasks={};newtasks={};extra=0
for rid,r in records.items():
 if rid in new:
  ck(not dataset_lib.validate_record(r),'Actual imported schema '+rid)
  ck(not any(v['eligible'] for v in dataset_lib.eligibility(r).values()),'No Evans training task '+rid)
  for m in r['measurements']:ck(build_dataset.is_structural(m,rid)==(m['id'] in newmap[rid]),'Evans classification '+rid+'/'+m['id']);countnew+=1
  for m in r['measurements']:
   st=build_dataset.is_structural(m,rid);prop=build_dataset.is_property(m,rid);ck(prop==(m['id'] in properties[rid]),'Evans property classification '+rid+'/'+m['id']);extra+=not st and not prop
 else:
  for m in r['measurements']:
   oldscope=display0.get('record_structural_measurement_ids',{})
   before=m['id'] in oldscope[rid] if rid in oldscope else (m['property'] in display0['structural_properties'] or any(p in m['property'] for p in display0['structural_property_fragments']))
   ck(build_dataset.is_structural(m,rid)==before,'Old measurement classification unchanged '+rid+'/'+m['id']);countold+=1
   ck(build_dataset.is_property(m,rid)==(not before),'Old property classification unchanged '+rid+'/'+m['id'])
ck(len(set(dataset_lib.build_groups(list(new.values())).values()))==1,'Evans records remain one source split')
ck(extra==367,'All367 remaining Evans fields retained as additional source observations')
for rel,h in refine['file_hashes'].items():
 if rel=='scripts/build_dataset.py':bind(S/rel) # final exact byte comparison above includes the separately declared source-link display label
 else:ck(bind(S/rel)==h,'Final presentation code/data hash '+rel)
pf=read(E/'visuals/products/package-freeze.json');ck(sha(E/'visuals/products/package-freeze.json')==adapter['freeze_sha256']=='47fa08d95c2a553768bd190966ab9cf5a15201d5bdf1bc1faf4e2f037c3d5e33','Frozen product adapter identity')
for p,h in pf['bound_files'].items():ck(bind(Path(p))==h,'Frozen product input '+Path(p).name)
ck(len(pf['public_allowlist'])==1 and pf['new_atomic_models']==0,'One adapter module and zero new atomic models')
ck(bind(S/'dist/evans2010-products.mjs')==adapter['module_sha256'],'Installed product adapter exact authored module')
ck(bind(S/'dist/crystal-viewer.mjs')==adapter['crystal_viewer_sha256'],'Final adapter caller exact')
for rid in records:
 page=S/'dist/records'/(rid+'.html')
 if page.exists():ck('progress.html' in page.read_text(encoding='utf-8'),'Progress nav retained on record '+rid)
for name in ['dataset','library','inventory']:
 p=S/'dist'/(name+'.html');bind(p);ck('<a href="progress.html">Review progress</a>' in p.read_text(encoding='utf-8'),'Progress navigation '+name)
base_inv=read(B/'data/inventory-summary.json');inv=read(S/'data/inventory-summary.json');proposed=read(I/'inventory-summary.json');ck(inv==proposed,'Installed inventory exact proposal')
from build_atlas import synthesis_route
from collections import Counter
routes={rid for rid,r in records.items() if synthesis_route(r)};lit={rid for rid,r in records.items() if r['collection']=='reviewed_literature'};procedures={rid for rid in lit if records[rid]['record_type']=='procedure'};observations={rid for rid in lit if records[rid]['record_type']=='observation'};controls=lit-routes-procedures-observations;benchmark={rid for rid,r in records.items() if r['collection']=='published_benchmark'}
ss=inv['summary'];expected_counts={'canonical_records':512,'synthesis_route_variant_records':len(routes),'shared_preparation_workup_characterization_assay_procedures':len(procedures),'contextual_observation_records':len(observations),'contextual_control_variant_records':len(controls),'reviewed_literature_records':len(lit),'total_canonical_source_groups':len({r['lineage']['source_group']for r in records.values()})}
for k,v in expected_counts.items():ck(ss[k]==v,'Independent inventory count '+k)
ck((len(routes),len(procedures),len(observations),len(controls),len(benchmark))==(101,195,102,14,100),'Record category partition101+195+102+14+100')
ck(ss['full_corpus_recipe_count'] is None and ss['full_corpus_distinct_synthesized_material_count'] is None,'Full corpus unknown counts remain unknown')
elig={t:sum(dataset_lib.eligibility(r)[t]['eligible']for r in records.values())for t in dataset_lib.eligibility(next(iter(records.values())))}
ck(inv['training_eligibility']==elig==base_inv['training_eligibility'],'All training task counts unchanged')
ck({rid for row in inv['per_paper']for rid in row['record_ids']}==set(records),'Per-paper inventory covers512 exact records')
for row in base_inv['per_paper']:ck(next(x for x in inv['per_paper']if x['source_group']==row['source_group'])==row,'Existing per-paper inventory unchanged '+row['source_group'])
ev=next(x for x in inv['per_paper']if x['source_group']=='evans2010');ck((ev['canonical_record_count'],ev['synthesis_route_variant_count'],ev['procedure_count'],ev['contextual_observation_count'],ev['measurement_entry_count'])==(32,3,13,16,3687),'Evans inventory32records3routes13procedures16observations')
library=read(S/'dist/data/library-index.json');reviews=read(S/'dist/data/paper-review-index.json');materials=read(S/'dist/data/materials-index.json')
ck(len(library['papers'])==4177==ss['local_paper_groups_indexed'],'4177 current generated library groups')
ck(ss['local_document_files_indexed']==base_inv['summary']['local_document_files_indexed']==7373,'7373 explicitly retained legacy document count')
ck('retained legacy corpus index snapshot' in inv['count_definitions']['local_document_files_indexed'],'Legacy document count definition explicit')
ck(sum(x['doi'].lower()=='10.1021/ja103805s'for x in library['papers'])==1,'Evans unique source-library DOI')
ck(len(materials['materials'])==44==ss['public_material_hubs'],'44 actual material hubs')
ck(len(reviews['papers'])==28,'28 actual full-source reader records')
ck(inv['provenance']['canonical_tree_sha256']==dataset_lib.digest({k:dataset_lib.digest(r)for k,r in sorted(records.items())}),'Inventory tree digest actual canonical data')
for rel,h in inv['provenance']['summary_artifact_sha256'].items():ck(bind(S/rel)==h,'Inventory actual summary/input digest '+rel)
import html
for rid,r in records.items():
 for stock in r['stocks']:
  output=build_dataset.stock_scope(stock,rid)
  if rid not in new:ck(output=='<p>'+html.escape(stock['scope'],quote=True)+'</p>','Old stock text unchanged '+rid+'/'+stock['id']);continue
  raw=stock['scope'];fields,end=json.JSONDecoder().raw_decode(raw)
  for k,v in fields.items():
   if k in {'id','source_unit_id'}:ck(html.escape(k+': '+str(v),quote=True) in output,'Stock provenance ID retained '+rid+'/'+stock['id']+'/'+k)
   else:
    val='Not explicitly reported' if v is None else json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else str(v).replace('_',' ') if isinstance(v,str) else str(v)
    ck('<dt>'+html.escape(k.replace('_',' '),quote=True)+'</dt><dd>'+html.escape(val,quote=True)+'</dd>' in output,'Stock field retained '+rid+'/'+stock['id']+'/'+k)
  ck(html.escape(raw[end:].strip(),quote=True) in output,'Stock source-scope suffix retained '+rid+'/'+stock['id'])
out={'status':'pending_product_adapter_audit' if not findings else 'open_findings','checked_at':datetime.now(timezone.utc).isoformat(),'auditor':'/root/norberg2004_extract','checks':len(checks),'failed_checks':findings,'old_records':480,'new_records':32,'old_measurements_classification_checked':countold,'new_measurements_classification_checked':countnew,'bound_files':list(bound.values()),'scope':'Read-only local import/code delta checks; final product adapter and executed module checks are separate pending gates.'}
(O/'integration-checkpoint.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');(O/'integration-checks.json').write_text(json.dumps(checks,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in out.items() if k!='bound_files'}))
