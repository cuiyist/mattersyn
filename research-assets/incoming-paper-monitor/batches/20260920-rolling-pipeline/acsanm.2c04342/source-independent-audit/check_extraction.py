import json, hashlib, re, sys
from pathlib import Path
from datetime import datetime, timezone
P=Path(__file__).resolve().parent.parent
A=P/'source-independent-audit'
sys.path[:0]=[r'[local path redacted]',r'[local path redacted]',r'[local path redacted]']
import pypdfium2 as pdfium
from PIL import Image
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks=[]
def ck(k,v,detail=None):
 checks.append({'check':k,'passed':bool(v),**({'detail':detail} if detail is not None else {})})
freeze=read(P/'package-freeze.json');facts=read(P/'source-facts.json');tables=read(P/'source-tables.json');inv=read(P/'source-inventory.json');assets=read(P/'original-assets-manifest.json');coverage=read(P/'page-coverage.json');payloads=read(P/'complete-source-payloads.json')
for p,h in freeze['bound_files'].items():ck('frozen-hash:'+p,Path(p).is_file() and sha(p)==h)
ck('author-distinct',freeze['author']!='/root/norberg2004_extract')
ck('original-pairing-count',len(payloads['original_files'])==4)
for p in payloads['original_files']+payloads['payloads']:
 ck('payload-hash:'+p['path'],sha(p['path'])==p['sha256']);ck('payload-local-only:'+p['path'],p['public_export_allowed'] is False)
ck('payload-count',len(payloads['payloads'])==78)
for role in ['main','si']:
 ck('all-pages:'+role,sorted(x['pdf_page'] for x in coverage['pages'] if x['document_role']==role)==list(range(1,14)))
for p in coverage['pages']:
 for field,hfield in [('text_path','text_sha256'),('layout_text_path','layout_text_sha256'),('image_path','image_sha256')]:ck('page-hash:'+p[field],sha(p[field])==p[hfield])
 ck('page-source:'+p['document_role']+str(p['pdf_page']),p['source_sha256'] in [x['sha256'] for x in payloads['original_files']])
docs={'source-facts.json':facts,'source-tables.json':tables}
ids=[]
for u in inv['inventory_units']:
 ids.append(u['id']);obj=docs[u['path']]
 try:
  for part in u['json_pointer'].split('/')[1:]:obj=obj[int(part)] if isinstance(obj,list) else obj[part.replace('~1','/').replace('~0','~')]
  ck('inventory-pointer:'+u['id'],obj.get('id')==u['source_object_id'])
 except Exception as e:ck('inventory-pointer:'+u['id'],False,str(e))
ck('unique-inventory-identities',len(ids)==len(set(ids))==353)
conflicts={x['id'] for x in facts['conflicts']};gaps={x['id'] for x in facts['missingness']}
def visit(obj,ptr=''):
 if isinstance(obj,dict):
  if 'document_role' in obj and 'source_sha256' in obj and 'pdf_page' in obj:
   expected={'main':'9e1d2860f09d5eb835cb3c2595fcec92e4fe529d4fb4974e5b269edaa6a9d852','si':'1d548be9eff43114c371a6f2210d2037ddc80e08fd9743c49e0fb5f0ed526662'}
   ck('source-locator:'+ptr,obj['source_sha256']==expected.get(obj['document_role']) and 1<=obj['pdf_page']<=13 and bool(obj.get('locator')))
  for key in ['conflict_ids','gap_ids']:
   if key in obj:ck('known-'+key+':'+ptr,set(obj[key])<=(conflicts if key=='conflict_ids' else gaps))
  for k,v in obj.items():visit(v,ptr+'/'+str(k))
 elif isinstance(obj,list):
  for i,v in enumerate(obj):visit(v,ptr+'/'+str(i))
visit(facts,'facts');visit(tables,'tables')
baseline=read(A/'independent-table-transcription.json')['tables']
def norm(s):
 s=str(s).replace('@NCs','').replace('NCs@','').replace('NC@','').replace('→','->').replace('Δ','Delta').replace('−','-')
 return re.sub(r'\s+','',s)
comparison=[]
for ti,(bt,at) in enumerate(zip(baseline,tables['tables'])):
 ck('table-row-count:'+at['id'],len(bt['rows'])==len(at['rows']))
 for ri,(br,ar) in enumerate(zip(bt['rows'],at['rows'])):
  if ti==4:br=br[1:]
  raw=[c['raw_text'] for c in ar['cells']]
  ck('table-column-count:'+ar['id'],len(raw)==len(br))
  for ci,(bv,av,c) in enumerate(zip(br,raw,ar['cells'])):
   same=norm(bv)==norm(av);ck('independent-table-token:'+c['id'],same,{'baseline':bv,'author':av} if not same else None)
   comparison.append({'id':c['id'],'baseline_raw':bv,'author_raw':av,'equal_after_declared_label_whitespace_normalization':same})
   rv=norm(av)
   if c['status']=='reported_text':pass
   elif re.fullmatch(r'[+-]?\d+(?:\.\d+)?',rv):ck('numeric-table-value:'+c['id'],c['value']==float(rv))
   elif '±' in rv:
    parts=rv.split('±');ck('numeric-uncertainty:'+c['id'],c['value']==float(parts[0]) and c['uncertainty']==float(parts[1]))
   elif rv in ['', '-']:ck('table-missing-not-zero:'+c['id'],c['value'] is None and c['status']=='not_reported')
ck('typed-table-count',len(comparison)==321)
ck('printed-body-count',sum(c['is_printed_body_cell'] for t in tables['tables'] for r in t['rows'] for c in r['cells'])==301)
ck('numeric-cell-count',sum(c['value'] is not None for t in tables['tables'] for r in t['rows'] for c in r['cells'])==230)
ck('fact-count',len(facts['facts'])==62);ck('fact-quantity-count',sum(len(f['quantities']) for f in facts['facts'])==186)
ck('protocol-count',len(facts['protocols'])==14);ck('operation-count',sum(len(p['operations']) for p in facts['protocols'])==39)
for k,v in [('materials',28),('stocks',5),('sample_contexts',41),('figures',20),('equations',8),('conflicts',13),('references',55)]:ck('count:'+k,len(facts[k])==v)
refs=facts['references'];ck('reference-numbers',sorted(r['number'] for r in refs)==list(range(1,56)))
for r in refs:
 page=r['evidence'][0]['pdf_page'];txt=(A/'audit-text-normal'/f'main-{page:02d}.txt').read_text(encoding='utf-8')
 if r['number']==14:
  # Printed reference 14 spans pages 11-12, with both pages already cited by the author.
  txt=txt[txt.index('(14)'):].split('ACS Applied Nano Materials')[0]+(A/'audit-text-normal'/'main-12.txt').read_text(encoding='utf-8').split('(15)')[0]
 # Native-layout extraction can break formula subscripts/hyphenated words; compare punctuation-neutral whole entry to its bound page.
 clean=lambda t:re.sub(r'[^\w]','',t.casefold(),flags=re.UNICODE)
 ck('reference-page-token-transport:'+r['id'],clean(r['text']) in clean(txt),{'page':page} if clean(r['text']) not in clean(txt) else None)
 ck('reference-cited-scope:'+r['id'],'not independently read' in r['scope'])
rendered={};pixel=[]
for a in assets['assets']:
 ck('crop-source-hash:'+a['id'],sha(a['source_path'])==a['source_sha256']);ck('crop-file-hash:'+a['id'],sha(a['path'])==a['sha256'])
 key=(a['source_path'],a['pdf_page'],a['render_scale'])
 if key not in rendered:
  d=pdfium.PdfDocument(a['source_path']);page=d[a['pdf_page']-1];rendered[key]=page.render(scale=a['render_scale']).to_pil().copy();page.close();d.close()
 original=rendered[key];crop=original.crop(tuple(a['pixel_bbox'])).convert('RGB');actual=Image.open(a['path']).convert('RGB')
 same=crop.size==actual.size and crop.tobytes()==actual.tobytes();ck('fresh-original-crop-pixels:'+a['id'],same)
 ck('crop-not-whole-page:'+a['id'],not a['contains_complete_source_page'] and crop.size!=original.size)
 pixel.append({'id':a['id'],'page':a['pdf_page'],'source_role':a['source_role'],'expected_size':crop.size,'actual_size':actual.size,'pixel_identical':same})
out={'reviewer':'/root/norberg2004_extract','created_at':datetime.now(timezone.utc).isoformat(),'author_package_freeze_sha256':sha(P/'package-freeze.json'),'checks_run':len(checks),'checks_passed':sum(c['passed'] for c in checks),'failures':[c for c in checks if not c['passed']],'checks':checks,'table_comparison':comparison,'pixel_replays':pixel,'scope':'Independent consistency/pointer/hash and original-pixel replay after separately completed manual source reading; not a substitute for manual scientific review.'}
(A/'mechanical-checks-v1.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:out[k] for k in ['checks_run','checks_passed','failures']},ensure_ascii=False))
