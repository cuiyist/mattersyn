"""Build the bounded private Sasongko context proposal from immutable inputs."""
from pathlib import Path
from copy import deepcopy
import json,hashlib,html,textwrap,sys,shutil
from context_data import SPECS,add
O=Path(__file__).resolve().parent;J=O.parents[1];M=J.parents[4];C=J/'canonical-proposal/v1';S=J/'source-extraction-revision-2';SITE=M/'recipe-atlas'
assert not (O/'package-freeze.json').exists()
sys.path[:0]=[str(M/'research-assets/rdkit-runtime'),str(M/'research-assets/corpus-20260917/runtime')]
import pymupdf
from PIL import Image,ImageDraw
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def jsha(v):return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def save(n,v):(O/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
checks=[]
def ck(n,v):checks.append({'check':n,'passed':bool(v)});assert v,n
for d in ['svg','previews','contacts','consumer-snapshot']:(O/d).mkdir(parents=True,exist_ok=True)
ck('canonical exact',sha(C/'package-freeze.json')=='3cab2fe6181dbf2149b2a0ac59f4a80d99c05cab4870342e141815c904549fb5')
ck('source v2 exact',sha(S/'package-freeze.json')=='d34778349e9942a73a1d275536af354e93d52739692e689fe2f12d394db7fddc')
sa=J/'source-independent-audit/independent-audit-v2.json';ca=J/'canonical-independent-audit/independent-audit-v1.json'
ck('distinct source audit exact',sha(sa)=='c709225b9555ba89d3d952a6153561b011351c00fb2c62733c920447479edb58')
ck('canonical audit exact',sha(ca)=='86691d16cedb8115d02e46c9d658e6a25f96593cc9f8d2363733ec81bffd71aa')
inputs=[C/'package-freeze.json',C/'record-manifest.json',C/'reader/sasongko2025.json',S/'package-freeze.json',S/'source-facts.json',J/'source-tables.json',J/'original-assets-manifest.json',sa,ca]
records={};paths={}
for x in read(C/'record-manifest.json')['records']:
 p=Path(x['path']);ck('record digest '+x['record_id'],sha(p)==x['sha256']);r=read(p);records[r['record_id']]=r;paths[r['record_id']]=p;inputs.append(p)
sf=read(S/'source-facts.json');facts={x['id']:x for x in sf['facts']};sc={x['id']:x for x in sf['sample_contexts']};tables=read(J/'source-tables.json')['tables'];assets=read(J/'original-assets-manifest.json')['assets'];reader=read(C/'reader/sasongko2025.json')
items={x['id']:x for sec in reader['reader_sections'] for x in sec['items']};tableRows={};tableRowLinks={}
for ti,t in enumerate(tables):
 for ri,row in enumerate(t['rows']):
  sid=row['sample_context'];tableRows.setdefault(sid,[]).append((t,row));tableRowLinks.setdefault(sid,[]).append({'path':str(J/'source-tables.json'),'json_pointer':f'/tables/{ti}/rows/{ri}','sha256':jsha(row),'row':deepcopy(row)})
  if t['id']=='table-s1':
   num=row['cells'][0]['raw_text'];current=num=='11';sample=row['cells'][1]['raw_text'];kind='Current-study summary' if current else 'Cited literature specimen'
   title=f'Table S1 row {num} — '+('current study' if current else 'literature comparison')
   caption=f'{kind}: {sample}. The listed methods and transition values are preserved as this table row’s scope. '+('This rounded QD summary is not a new sample or an exact join to a TEM aliquot.' if current else 'It is not a newly synthesized specimen in the current paper. A blank transition cell is unknown, not a negative result.')
   add(sid,title,kind,caption,['literature-transition'])
ck('33 named contexts exact',set(SPECS)==set(sc) and len(sc)==33)
def loc(ev):return {'source_id':'sasongko2025','locator':f"{ev['document_role'].upper()} PDF p. {ev['pdf_page']} (printed {ev.get('printed_page')}), {ev['locator']}; original SHA256 {ev['source_sha256']}"}
def unique(rows):return list({json.dumps(x,sort_keys=True):x for x in rows}.values())
def tx(x,y,s,size=22,color='#244756'):return f'<text x="{x}" y="{y}" font-family="Arial,sans-serif" font-size="{size}" fill="{color}">{html.escape(str(s))}</text>'
def wrap(s,width):return textwrap.wrap(s,width,break_long_words=False,break_on_hyphens=False)
def qtxt(c):
 if not c['raw_text']:return 'not reported (blank in source)'
 unit=c.get('unit') or ''
 if unit in ['source specimen text','source method text','row_number']:unit=''
 unit={'volume_parts':'volume parts','deg 2theta (axis)':'° 2θ (axis)','angstrom':'Å','degC':'°C'}.get(unit,unit)
 if unit=='volume parts' and c.get('value')==1:unit='volume part'
 return c['raw_text']+(' '+unit if unit else '')
def metrics(sid):
 out=[]
 if SPECS[sid]['phase']:out.append('Source XRD assignment: '+SPECS[sid]['phase'])
 for t,row in tableRows.get(sid,[]):
  if t['id']=='table-s1':
   out.append('Source specimen: '+row['cells'][1]['raw_text']);out.append('γ→β: '+qtxt(row['cells'][2])+'; β→α: '+qtxt(row['cells'][3]));out.append('Method: '+row['cells'][4]['raw_text']);out.append('Citation: '+((row.get('reference_id') or 'current study').replace('si-reference-','SI reference ')))
  elif t['id']=='pl-slopes':
   out.append(qtxt(row['cells'][0])+': energy slope '+qtxt(row['cells'][1])+'; FWHM slope '+qtxt(row['cells'][2]))
  else:
   out += [c['meaning'].replace('_',' ')+': '+qtxt(c) for c in row['cells'] if c['unit']!='row_number']
 return out
entrymap={};entries=[]
symbol_note='Symbolic context only. No atomic positions, particle envelope, ligand geometry or exact structure–recipe pair.'
for sid,spec in SPECS.items():
 eid='sasongko2025-'+sid+'-product-context';lines=[]
 for st in metrics(sid):lines+=wrap(st,94)
 cap=wrap(spec['caption'],99);h=max(820,290+len(lines)*27+70+len(cap)*27+150)
 body=tx(40,55,spec['title'],27)+tx(40,95,'Sasongko et al. · Journal of Physical Chemistry C 2025',20,'#687f8b')
 head=wrap(spec['headline'],53);y=160
 for l in head:body+=tx(55,y,l,29);y+=38
 body+=f'<rect x="36" y="{y+10}" width="1028" height="{max(70,len(lines)*27+30)}" rx="14" fill="#edf5f8"/>';y+=45
 for l in lines or ['Source-scoped process, observation or interpretation context']:body+=tx(55,y,l,21);y+=27
 y=max(y+65,350)
 for l in cap:body+=tx(45,y,l,21);y+=27
 for i,l in enumerate(wrap(symbol_note,100)):body+=tx(45,h-94+i*27,l,20,'#687f8b')
 svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="{h}" viewBox="0 0 1100 {h}"><title>{html.escape(spec["title"])}</title><rect x="1" y="1" width="1098" height="{h-2}" rx="18" fill="white" stroke="#b9ced8"/>'+body+'</svg>'
 rel='svg/'+eid+'.svg';(O/rel).write_text(svg,'utf8');d=pymupdf.open(stream=svg.encode(),filetype='svg');d[0].get_pixmap(alpha=False).save(O/'previews'/(eid+'.png'))
 e={'id':eid,'name':spec['title'],'formula':'','displayFormula':spec['headline'],'depictionKind':'symbolic_context','svgPath':rel,'model2dPath':None,'model3dPath':None,'functionalGroups':[],'caption':spec['caption']+' '+symbol_note,'limitations':['Source context is not an exact physical aliquot or independent replicate.','No current-sample coordinates, CIF, phase-pure whole composition or training admission.'],'sourceUrls':['https://doi.org/10.1021/acs.jpcc.5c05144'],'assetHashes':{'svgPath':sha(O/rel)},'binding_approved':False,'published':False,'eligible_training':False}
 entries.append(e);entrymap[sid]=e
# Exact original excerpts already approved at source level; no recropping or extra
# image publication approval is inferred. Reuse current reader-relative paths.
assetmap={};originalLinks={}
for a in assets:
 ck('selected crop hash '+a['id'],sha(a['path'])==a['sha256']);ck('no whole page '+a['id'],a['contains_complete_source_page'] is False);inputs.append(Path(a['path']));assetmap[a['object_id']]=a
 for sid in a['sample_context_ids']:
  if sid not in sc:continue
  originalLinks.setdefault(sid,[]).append({'asset_id':a['id'],'object_id':a['object_id'],'local_path':a['path'],'sha256':a['sha256'],'public_asset':'assets/figures/sasongko2025/'+Path(a['path']).name,'source_locator':deepcopy(a['evidence']),'sample_scope':'Original source context; not an exact shared physical aliquot.'})
claim_index={};sample_measurements={}
for rid,r in records.items():
 for i,m in enumerate(r['measurements']):
  link={'record_id':rid,'record_sha256':sha(paths[rid]),'json_pointer':f'/measurements/{i}','measurement_id':m['id'],'canonical_measurement':deepcopy(m)}
  if m['id'].endswith('-claim') and m['id'][:-6] in facts:
   fid=m['id'][:-6];ck('literal claim '+fid,m['value']['value']==facts[fid]['claim']);claim_index.setdefault(fid,[]).append(link)
  if m['sample_id'] in sc and not m['id'].startswith('payload-'):sample_measurements.setdefault(m['sample_id'],[]).append(link)
contexts={};bindings=[];excluded=[];coverage=[]
for rid,r in records.items():
 for i,p in enumerate(r['products']):
  sid=p['sample_id'];common={'record_id':rid,'sample_id':sid,'canonical_product_pointer':f'/products/{i}','canonical_product_snapshot':deepcopy(p),'canonical_record_path':str(paths[rid]),'canonical_record_sha256':sha(paths[rid]),'canonical_product_sha256':jsha(p)}
  if sid not in SPECS:
   reason=('Fact/operation/acquisition evidence carrier, not an additional physical product.' if sid.startswith('fact-context-') else 'Aggregate source/table/unit payload or bookkeeping context, not a single physical specimen. Named source contexts have separate mappings.')
   excluded.append({**common,'reason':reason});coverage.append({'record_id':rid,'sample_id':sid,'pointer':common['canonical_product_pointer'],'disposition':'excluded','reason':reason});continue
  spec=SPECS[sid];fids=spec['facts'];ck('all source facts exact '+sid,all(f in facts and f in claim_index for f in fids));cl=[deepcopy(x) for f in fids for x in claim_index[f]]
  # Comparison-wide claims remain explanatory evidence. Numeric sample links are
  # selected by exact canonical sample ID, never all quantities of a shared fact.
  numeric=deepcopy(sample_measurements.get(sid,[]));ev=unique([loc(x) for f in fids for x in facts[f]['evidence']]);conf=sorted({x for f in fids for x in facts[f].get('conflict_ids',[])})
  orig=deepcopy(originalLinks.get(sid,[]));phase={'value':spec['phase'],'status':'source_scoped_assignment' if spec['phase'] else 'not_assigned','evidence':ev,'note':'Technique-local source assignment only; canonical unknown whole composition remains unchanged. Reference-cell and literature contexts are not current-particle refinements.'}
  row={'sample_id':sid,'label':spec['title'],'registry_id':entrymap[sid]['id'],'caption':spec['caption']+' '+symbol_note,'phase':phase,'morphology':deepcopy(p['morphology']),'source_fact_ids':fids,'conflict_ids':conf,'source_context_snapshot':deepcopy(sc[sid]),'canonical_product_pointer':common['canonical_product_pointer'],'canonical_product_snapshot':deepcopy(p),'canonical_claim_links':cl,'canonical_quantity_links':numeric,'source_table_rows':deepcopy(tableRowLinks.get(sid,[])),'original_evidence_links':orig,'same_physical_batch_asserted':False,'projection_kind':'source_scoped_symbolic_context','training_eligible':False,'atomic_model':False,'binding_approved':False}
  contexts.setdefault(rid,[]).append(row);bindings.append({**common,'registry_id':entrymap[sid]['id'],'entry_sha256':jsha(entrymap[sid]),'source_fact_ids':fids,'source_context_id':sid});coverage.append({'record_id':rid,'sample_id':sid,'pointer':common['canonical_product_pointer'],'disposition':'mapped','registry_id':entrymap[sid]['id']})
total=sum(len(r['products']) for r in records.values());ck('all slots accounted',total==len(coverage)==len(bindings)+len(excluded));ck('all 33 names mapped',set(b['sample_id'] for b in bindings)==set(sc));ck('unique slot accounting',len({(x['record_id'],x['pointer']) for x in coverage})==total)
ck('no atom models',all(not e['model2dPath'] and not e['model3dPath'] and not e['formula'] for e in entries));ck('literal Pm3m','Pm3m' in SPECS['alpha-reference']['headline'] and 'overbar' in SPECS['alpha-reference']['caption'])
notice='Condition comparisons, discarded and retained fractions, TEM dimensions, XRD component assignments, variable-temperature optical/Raman experiments and cited reference cells remain separate. No exact physical-aliquot join, current particle coordinates, CIF or structure–recipe training pair is supplied. Pm3m and the d(002)/reference-cell conflict remain literal source evidence.'
save('registry-additions.json',{'schemaVersion':'1.0','source_id':'sasongko2025','entries':entries,'binding_approved':False})
save('product-contexts-additions.json',{'recordContexts':contexts,'sourceNotices':{'sasongko2025':notice}})
keys=['sample_id','label','registry_id','caption','phase','morphology','source_fact_ids','conflict_ids','same_physical_batch_asserted','projection_kind','training_eligible','atomic_model','binding_approved']
public={'recordContexts':{rid:[{k:deepcopy(x[k]) for k in keys} for x in rows] for rid,rows in contexts.items()},'sourceNotices':{'sasongko2025':notice}}
for rid,rows in public['recordContexts'].items():
 for row in rows:
  row['original_evidence_links']=[{'asset_id':x['asset_id'],'label':'Original '+x['object_id'].replace('-',' '),'public_asset':x['public_asset'],'sha256':x['sha256'],'scope':'Source context; no exact shared aliquot.'} for x in originalLinks.get(row['sample_id'],[])]
save('public-product-contexts-proposal.json',public)
save('card-display-data.json',{'cards':[{'source_context_id':sid,'title':spec['title'],'headline':spec['headline'],'caption':spec['caption'],'metric_lines':metrics(sid),'table_source_links':deepcopy(tableRowLinks.get(sid,[]))} for sid,spec in SPECS.items()]})
save('source-evidence-links.json',{'status':'private_link_proposal','links':originalLinks,'integration_note':'Original crop public paths are already specified by the frozen reader. Use original_evidence_links to link the matching reader figure; the existing productIdentity consumer displays source locators but does not itself add clickable image links. No copied or modified source image in this package.'})
save('bindings.json',{'schema':'mattersyn-symbolic-product-context-proposal/1','author':'/root/peng1998_reader_assets','status':'private_author_proposal_pending_distinct_audit','bindings':bindings,'excluded_contexts':excluded,'scientific_records_unchanged':True,'independent_approval':False,'role_disclosure':'This author wrote the source extraction and performed the distinct canonical transport audit of Norberg’s records. Backlog independently passed source v2. Root must separately audit this new authored product proposal.'})
save('slot-coverage.json',{'total_slots':total,'mapped':len(bindings),'excluded':len(excluded),'source_contexts':33,'rows':coverage})
save('public-asset-proposal.json',{'status':'unapproved_public_candidates','assets':[{'path':str(O/e['svgPath']),'sha256':e['assetHashes']['svgPath'],'public_path':'assets/chemical-registry/sasongko2025-products/'+Path(e['svgPath']).name,'entry_id':e['id']} for e in entries],'excluded':'No original PDFs/SI/pages/raw text or private proof snapshots.'})
consumer=SITE/'dist/crystal-viewer.mjs';shutil.copyfile(consumer,O/'consumer-snapshot/crystal-viewer.mjs');save('consumer-snapshot/provenance.json',{'path':str(consumer),'sha256':sha(consumer),'snapshot':'crystal-viewer.mjs'})
anchor="for(const e of c.phase?.evidence||[])view.append(el('small',e.source_id+' · '+e.locator));"
addition="if(r.lineage?.source_group==='sasongko2025'&&r.record_id.startsWith('sasongko-2025-'))for(const link of c.original_evidence_links||[]){if(!/^assets\\/figures\\/sasongko2025\\/[a-z0-9-]+\\.png$/.test(link.public_asset)||! /^[a-f0-9]{64}$/.test(link.sha256))continue;const a=el('a',link.label+' ↗','molecule-link');a.href=new URL(link.public_asset,import.meta.url).href+'?sha='+link.sha256;a.target='_blank';a.rel='noopener noreferrer';view.append(a);}"
ck('single consumer insertion anchor',consumer.read_text('utf8').count(anchor)==1)
save('original-evidence-consumer-insertion.json',{'status':'private_optional_integration_proposal','target':'dist/crystal-viewer.mjs','baseline_sha256':sha(consumer),'anchor':anchor,'replacement':anchor+addition,'scope':'Only Sasongko source/group and exact permitted figure-path prefix; no other source dispatch changes. Reviewed root integration required; Site unchanged.'})
save('input-bindings.json',{'files':{str(p):sha(p) for p in inputs},'no_mutations':True})
counts={'canonical_records':len(records),'canonical_product_slots':total,'mapped':len(bindings),'excluded':len(excluded),'named_contexts':33,'symbols':len(entries),'records_with_mappings':len(contexts),'atomic_models':0}
save('author-validation.json',{'status':'passed_author_checks','independent_approval':False,'counts':counts,'check_count':len(checks),'checks':checks})
panels=sorted((O/'previews').glob('*.png'));contacts=[]
for start in range(0,len(panels),4):
 canvas=Image.new('RGB',(1600,1400),'#e4ecf0');draw=ImageDraw.Draw(canvas)
 for i,p in enumerate(panels[start:start+4]):
  im=Image.open(p);im.thumbnail((790,650));x=i%2*800+(800-im.width)//2;y=i//2*700+30;canvas.paste(im,(x,y));draw.text((i%2*800+10,i//2*700+8),p.stem.replace('sasongko2025-',''),fill='black')
 p=O/'contacts'/f'contact-{start//4+1:02}.png';canvas.save(p);contacts.append({'path':str(p),'sha256':sha(p),'panels':[{'path':str(x),'sha256':sha(x)} for x in panels[start:start+4]]})
save('contact-index.json',{'panel_count':len(panels),'contacts':contacts})
print(json.dumps({'counts':counts,'checks':len(checks)}))
