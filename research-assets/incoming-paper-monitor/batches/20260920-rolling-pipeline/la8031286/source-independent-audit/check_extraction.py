import json,hashlib,re,sys,unicodedata
from pathlib import Path
from datetime import datetime,timezone
A=Path(__file__).resolve().parent;P=A.parent
sys.path[:0]=[r'[local path redacted]',r'[local path redacted]',r'[local path redacted]']
import pypdfium2 as pdfium
from PIL import Image
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
freeze=load(P/'package-freeze.json');f=load(P/'source-facts.json');t=load(P/'source-tables.json');inv=load(P/'source-inventory.json');assets=load(P/'original-assets-manifest.json');cov=load(P/'page-coverage.json');prep=load(P/'source-preparation.json');baseline=load(A/'independent-reading-notes.json')
checks=[]
def ck(n,b,detail=None):checks.append({'check':n,'passed':bool(b),**({'detail':detail}if detail is not None else{})})
ck('exact-author-freeze',sha(P/'package-freeze.json')=='b2d275bdd94514bba3b2b4e9f4c91920791801f268bc86a5616b8af87e89c0ce')
ck('distinct-authorship',freeze['author']!='/root/norberg2004_extract')
for p,h in freeze['bound_files'].items():ck('frozen-hash:'+p,sha(p)==h)
sourcehash={'main':'eb93e8ce4e893bde4215914cc7920bd7567388fdd895537334e80e5d3354d581','si':'1669359b67be6fcf7362dbf33d708d76b76d70e079b91b6c70d2856683de431e'}
for d in prep['documents']:
 ck('original-source:'+d['role'],sha(d['source_path'])==sourcehash[d['role']]==d['sha256'])
 ck('page-count:'+d['role'],d['page_count']==4)
for role in sourcehash:ck('all-coverage-pages:'+role,sorted(x['pdf_page'] for x in cov['pages'] if x['document_role']==role)==list(range(1,5)))
units=inv['inventory_units'];ids={x['id'] for x in units};ck('unit-count-and-uniqueness',len(units)==len(ids)==218)
payloads={'source-facts.json':f,'source-tables.json':t}
for u in units:
 try:
  obj=payloads[u['payload_path']]
  for part in u['json_pointer'].split('/')[1:]:obj=obj[int(part)]if isinstance(obj,list)else obj[part.replace('~1','/').replace('~0','~')]
  ck('unit-resolves:'+u['id'],obj is not None)
 except Exception as e:ck('unit-resolves:'+u['id'],False,str(e))
for p in cov['pages']:
 ck('page-text-hash:'+p['document_role']+str(p['pdf_page']),sha(p['text_path'])==p['text_sha256'])
 ck('page-render-hash:'+p['document_role']+str(p['pdf_page']),sha(p['render_path'])==p['render_sha256'])
 ck('page-known-units:'+p['document_role']+str(p['pdf_page']),set(p['source_unit_ids'])<=ids)
factids={x['id'] for x in f['facts']};conflictids={x['id'] for x in f['conflicts']};gapids={x['id'] for x in f['missingness']};sampleids={x['id'] for x in f['sample_contexts']};materialids={x['id'] for x in f['materials']}
def walk(x,path=''):
 if isinstance(x,dict):
  if 'document_role'in x and 'pdf_page'in x and 'source_sha256'in x:ck('valid-source-locator:'+path,x['source_sha256']==sourcehash.get(x['document_role']) and 1<=x['pdf_page']<=4 and bool(x.get('locator')))
  for key,allowed in [('source_fact_ids',factids),('context_fact_ids',factids),('conflict_ids',conflictids),('gap_ids',gapids)]:
   if key in x:ck('known-'+key+':'+path,set(x[key])<=allowed)
  for k,v in x.items():walk(v,path+'/'+str(k))
 elif isinstance(x,list):
  for i,v in enumerate(x):walk(v,path+'/'+str(i))
walk(f,'facts');walk(t,'tables')
for st in f['stocks']:
 ck('stock-components:'+st['id'],len(st['components'])==2 and all(c['material_id']in materialids for c in st['components']))
 ck('stock-no-full-volume:'+st['id'],st['final_volume']is None and st['subsequent_transfer_volume']['value']==100)
 ck('stock-concentration:'+st['id'],st['quantities'][0]['value']==(0.4 if '-tea-'in st['id'] else 0.1))
for pr in f['protocols']:
 ck('known-protocol-samples:'+pr['id'],set(pr['sample_ids'])<=sampleids)
 for op in pr['operations']:
  sourcequant=[q for fid in op['source_fact_ids'] for fact in f['facts']if fact['id']==fid for q in fact['quantities']]
  for i,q in enumerate(op['quantities']):ck('operation-quantity-source:'+op['id']+str(i),q in sourcequant)
for fig in f['figures']:
 for panel in fig['panels']:ck('figure-known-sample:'+fig['id']+panel['label'],panel['sample_id']in sampleids)
bt=baseline['independent_table'];at=t['tables'][0];ck('numeric-table-rows',len(bt['rows'])==len(at['rows'])==10)
prime=lambda s:s.replace('tripleprime','‴').replace('doubleprime','″').replace('prime','′')
for br,ar in zip(bt['rows'],at['rows']):
 ck('table-group:'+ar['id'],br[0]==ar['source_group_header']);ck('table-peak:'+ar['id'],prime(br[1])==ar['peak_label']);ck('table-valence:'+ar['id'],br[2]==ar['oxidation_assignment_as_printed'])
 for i,c in enumerate(ar['cells']):
  ck('independent-table-raw:'+ar['id']+str(i),br[i+3]==c['raw_text']);ck('independent-table-number:'+ar['id']+str(i),float(br[i+3])==c['value']);ck('table-unit:'+ar['id']+str(i),c['unit']=='eV')
 # Ensure the source-shaped raw matrix agrees with every separately transcribed cell.
 rowbase=0 if ar['source_group_header']=='Ce3d7/2' else 3;col=ar['source_column_in_group']
 for i,c in enumerate(ar['cells']):ck('raw-grid-transport:'+ar['id']+str(i),at['raw_grid'][rowbase+1+i][col]==c['raw_text'])
ck('raw-grid-36cells',sum(len(row)for row in at['raw_grid'])==36)
def normalized(s):
 s=unicodedata.normalize('NFKD',s)
 return ''.join(c.casefold()for c in s if c.isalnum())
for r in f['references']:
 ev=r['evidence'][0];txt=(A/'audit-text'/f"{ev['document_role']}-{ev['pdf_page']:02d}.txt").read_text(encoding='utf-8')
 ck('reference-token-transport:'+r['id'],normalized(r['raw_citation'])in normalized(txt))
 ck('reference-cited-only:'+r['id'],'not read'in r['access_level'])
ck('main-ref27-not-invented',{r['number']for r in f['references']if r['id'].startswith('main-')}==set(range(1,27))|{28})
ck('si-reference-set',{r['number']for r in f['references']if r['id'].startswith('si-')}=={1,2,3,4})
cached={};pixel=[]
for a in assets['assets']:
 ck('asset-source-hash:'+a['id'],sha(a['source_path'])==a['source_sha256']);ck('asset-file-hash:'+a['id'],sha(a['path'])==a['sha256'])
 key=(a['source_path'],a['pdf_page'],a['dpi'])
 if key not in cached:
  doc=pdfium.PdfDocument(a['source_path']);page=doc[a['pdf_page']-1];cached[key]=page.render(scale=a['dpi']/72).to_pil().copy();page.close();doc.close()
 original=cached[key];expected=original.crop(a['crop_box_pixels']).convert('RGB');actual=Image.open(a['path']).convert('RGB')
 same=expected.size==actual.size and expected.tobytes()==actual.tobytes();ck('fresh-pixel-replay:'+a['id'],same)
 ck('crop-not-fullpage:'+a['id'],not a['contains_complete_source_page'] and expected.size!=original.size)
 pixel.append({'asset_id':a['id'],'pixel_identical':same,'dimensions':list(actual.size)})
ck('selected-crops',len(pixel)==20)
actualcounts={'facts':len(f['facts']),'fact_quantities':sum(len(x['quantities'])for x in f['facts']),'materials':len(f['materials']),'stocks':len(f['stocks']),'protocol_families':len(f['protocols']),'operations':sum(len(x['operations'])for x in f['protocols']),'sample_contexts':len(f['sample_contexts']),'figures':len(f['figures']),'figure_panels':sum(len(x['panels'])for x in f['figures']),'tables':len(t['tables']),'table_numeric_cells':sum(len(x['cells'])for x in at['rows']),'table_raw_grid_cells':sum(len(x)for x in at['raw_grid']),'equations':len(f['equations']),'printed_reference_entries':len(f['references']),'conflicts':len(f['conflicts']),'missingness':len(f['missingness']),'inventory_units':len(units),'selected_crops':len(pixel)}
for k,v in actualcounts.items():ck('counts:'+k,v==freeze['counts'][k])
result={'reviewer':'/root/norberg2004_extract','created_at':datetime.now(timezone.utc).isoformat(),'source_package_freeze_sha256':sha(P/'package-freeze.json'),'checks_run':len(checks),'checks_passed':sum(x['passed']for x in checks),'failures':[x for x in checks if not x['passed']],'checks':checks,'pixel_replays':pixel,'actual_counts':actualcounts,'manual_basis':{'path':str(A/'independent-reading-notes.json'),'sha256':sha(A/'independent-reading-notes.json')},'scope':'Executed independent data/hash/locator/source-pixel checks; separate from prior complete manual source reading and actual frozen fact/crop review.'}
(A/'mechanical-checks-v1.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:result[k]for k in ['checks_run','checks_passed','failures']},ensure_ascii=False))
