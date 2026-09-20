"""Read existing author outputs and actual sources; write a private author validation only."""
from pathlib import Path
import json,hashlib,re,math
from datetime import datetime,timezone
from PIL import Image,ImageChops
import pypdfium2
P=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(n):return json.loads((P/n).read_bytes())
src=read('source-facts.json');inv=read('source-inventory.json');coverage=read('page-coverage.json');assets=read('original-assets-manifest.json');payload=read('complete-source-payloads.json');tables=read('source-tables.json')['tables']
checks=[]
def ck(ok,what):
 checks.append({'check':what,'passed':bool(ok)})
 if not ok:raise AssertionError(what)
docs={d['document_id']:d for d in payload['documents']}
for f in payload['source_copies']:ck(sha(f['source_path'])==f['sha256'],'actual source copy '+f['source_path'])
ck(src['source_generation']==2 and payload['source_generation']==2,'generation 2')
ck(src['bundle_sha256']==payload['bundle_sha256']=='01ea96ad06d784be78ea09cfe8bff0c2e4ee325610d7c46d0319bea855e43236','exact intake bundle')
ck(len(coverage['pages'])==19,'all nineteen pages')
for pg in coverage['pages']:
 ck(pg['text_read_in_full'] and pg['native_page_image_visually_inspected'],'recorded actual read/view '+pg['document_role']+str(pg['pdf_page']))
 ck(sha(pg['text_path'])==pg['text_sha256'],'page text hash '+pg['text_path'])
 ck(sha(pg['render_path'])==pg['render_sha256'],'native page render hash '+pg['render_path'])
 ck(Path(pg['render_path']).parent.name=='source-render','full page policy path')
def visit(obj,path=''):
 if isinstance(obj,dict):
  if 'source_sha256'in obj and 'pdf_page'in obj and 'document_role'in obj:
   d=docs[obj['document_role']];ck(obj['source_sha256']==d['source_sha256'],'evidence source '+path);ck(1<=obj['pdf_page']<=d['page_count'],'evidence page '+path)
  for k,v in obj.items():visit(v,path+'/'+str(k))
 elif isinstance(obj,list):
  for i,v in enumerate(obj):visit(v,path+'/'+str(i))
visit(src)
for key in['facts','tables','materials','stocks','protocols','samples','figures','schemes','equations','references']:
 ids=[v['id']for v in src[key]];ck(len(ids)==len(set(ids)),'unique '+key+' IDs')
uids=[u['id']for u in inv['inventory_units']];ck(len(uids)==len(set(uids)),'global unique inventory IDs')
for unit in inv['inventory_units']:
 ob=src
 for part in unit['json_pointer'].strip('/').split('/'):ob=ob[int(part)]if isinstance(ob,list)else ob[part]
 ck(ob['id']==unit['source_object_id'],'inventory pointer '+unit['id'])
ck(tables==src['tables'],'separate source table transport')
bytable={t['id']:t for t in tables};ck([len(t['rows'])for t in tables]==[5,6,4,18,11],'all table rows')
ck(sum(len(r['cells'])for t in tables for r in t['rows'])==272,'all 272 typed/image cells')
raw=Path(docs['si']['pages'][5]['text_path']).read_text(encoding='utf-8')
native_tokens=[line.strip()for line in raw.split('Table S1.',1)[0].splitlines()if re.fullmatch(r'\s*\d+\.\d+\s*',line)]
ck(len(native_tokens)==180,'SI S1 native text channel supplies 180 decimal tokens')
textrows=[native_tokens[i:i+10]for i in range(0,180,10)]
ck(len(textrows)==18,'SI S1 source-order ten-column grouping supplies eighteen rows')
for ir,(tokens,row)in enumerate(zip(textrows,bytable['table-s1']['rows']),1):
 for ic,(tok,cell)in enumerate(zip(tokens,row['cells']),1):
  ck(tok==cell['raw_text'],f'S1 literal token {ir}:{ic}')
  ck(float(tok)==cell['value'],f'S1 numeric token {ir}:{ic}')
  ck(cell['comparison']is None and not cell['approximate'],f'S1 raw precision retained {ir}:{ic}')
for row in bytable['table-1']['rows']:
 for cell in row['cells'][2:]:
  ck((cell['approximate']and cell['comparison']is None)or(cell['comparison']=='>'and not cell['approximate']),'Table 1 QY bounds/approximation '+cell['id'])
for name in['table-2','table-3']:
 for row in bytable[name]['rows']:
  cell=next(c for c in row['cells']if c['column']=='thick_shell_QY');ck(cell['value']is None and cell['status']=='reported_text','qualitative QY remains text '+cell['id'])
  imagecell=row['cells'][-1];ck(imagecell['status']=='original_image'and imagecell['asset_id']in{a['id']for a in assets['assets']},'table image joins '+row['sample_id'])
facts={f['id'].removeprefix('ghosh2012-'):f for f in src['facts']}
ck(facts['shell-anneal']['quantities'][2]['value']==2.5,'preferred post-Cd is 2.5 h')
ck(bytable['table-1']['rows'][3]['cells'][1]['value']==3,'comparison post-Cd remains 3 h')
ck(facts['shell-withdraw']['quantities'][0]['meaning']=='withdrawn reaction volume fraction','withdrawal basis explicit')
ck(facts['core-small']['quantities'][1]['value']is None,'several seconds not fabricated as exact value')
ck(facts['core-standard']['quantities'][2]['value']is None,'several minutes not fabricated as exact value')
ck(facts['materials']['quantities'][5]['comparison']=='>=','selenium purity lower bound')
ck(facts['lifetime-excitation']['quantities'][5]['value']==1e-5 and facts['lifetime-excitation']['quantities'][5]['approximate'],'small exciton count typed correctly')
ck(facts['nonblinking-definition']['quantities'][0]['comparison']=='>'and facts['nonblinking-large']['quantities'][1]['comparison']=='>=','both nonblinking inequalities preserved')
ck(facts['lifetime-example']['quantities'][1]['value']==16.9 and bytable['table-s1']['rows'][-1]['cells'][1]['value']==15.57,'unresolved large-core shell labels preserved')
ck('moderately thick'in bytable['table-3']['notes'][1],'Table 3 TEM/QY scope separation')
ck(len(src['references'])==23 and len(src['references'][7]['subreferences'])==2,'23 numbered refs / 24 individual works')
ck(all(not r['full_text_read']for r in src['references']),'no external reference reading claim')
ck(src['training_admission']=={'approved':False,'requested_tasks':[],'exact_recipe_structure_pair':False,'atomistic_model_qualified':False},'downstream gates remain closed')
factids={f['id']for f in src['facts']}
for pr in src['protocols']:
 for op in pr['operations']:
  for fid in op['source_fact_ids']:ck(fid in factids,'operation source fact '+fid)
  ck(not pr['complete_laboratory_sop'],'incomplete practical details explicitly retained')
# Re-render each cropped page once, then compare every delivered crop pixel-for-pixel.
pdfs={r:pypdfium2.PdfDocument(d['source_path'])for r,d in docs.items()};cache={}
for a in assets['assets']:
 ck(sha(a['path'])==a['sha256'],'asset byte hash '+a['id'])
 ck(a['whole_source_page']is False and not a['public_import_approval'],'selected original pending public approval '+a['id'])
 key=(a['source_role'],a['pdf_page'],a['render_scale'])
 if key not in cache:
  pg=pdfs[key[0]][key[1]-1];bm=pg.render(scale=key[2]);cache[key]=bm.to_pil().copy();bm.close();pg.close()
 im=cache[key];rect=[round(v*(im.width if k%2==0 else im.height))for k,v in enumerate(a['bbox_normalized'])]
 ck(rect==a['bbox_pixels_at_render'],'asset bounding box '+a['id'])
 with Image.open(a['path'])as actual:
  expected=im.crop(rect);ck(actual.size==expected.size and ImageChops.difference(actual.convert('RGB'),expected.convert('RGB')).getbbox()is None,'native pixel replay '+a['id']);expected.close()
for im in cache.values():im.close()
for pdf in pdfs.values():pdf.close()
diagnostics=[]
for r in bytable['table-s1']['rows']:
 v=[c['value']for c in r['cells']];aa=v[3::2][:3];tt=[v[4],v[6],v[8]]
 calc=sum(a*t*t for a,t in zip(aa,tt))/sum(a*t for a,t in zip(aa,tt));vol=math.pi/6*(v[0]+2*v[1]*.3375)**3
 diagnostics.append({'row':r['row_label'],'printed_amplitude_sum':sum(aa),'mean_coefficient_recomputed_lifetime_ns':calc,'reported_average_lifetime_ns':v[9],'difference_ns':calc-v[9],'spherical_model_volume_nm3':vol,'reported_TEM_volume_nm3':v[2],'volume_difference_nm3':vol-v[2],'scope':'Author diagnostic from rounded/mean fitted inputs and stated monolayer model only; never substitutes for source values or certifies exact geometry.'})
out={'schema':'mattersyn-source-author-validation/1','author':'/root/backlog_eta','created_at':datetime.now(timezone.utc).isoformat(),'status':'author_checks_passed_independent_audit_pending','check_count':len(checks),'checks':checks,'source_table_diagnostics':diagnostics,'manual_scope':'All nineteen page images/texts read. All thirty-six selected assets viewed on six contact sheets; four adjusted crops reopened individually before freeze. This is author review only.','counts':src['counts'],'bound_inputs':{str(P/n):sha(P/n)for n in['source-facts.json','source-tables.json','source-inventory.json','page-coverage.json','original-assets-manifest.json','complete-source-payloads.json','source_author_data.py','build_extraction.py','validate_extraction.py']}}
(P/'extraction-validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'checks':len(checks),'status':out['status'],'max_abs_mean_fit_lifetime_difference_ns':max(abs(x['difference_ns'])for x in diagnostics)},ensure_ascii=False))
