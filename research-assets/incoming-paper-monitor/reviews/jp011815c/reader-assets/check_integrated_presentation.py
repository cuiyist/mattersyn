"""Read-only Site audit; run AFTER integration/build and the companion Node checker.

Run with an environment that can import Site dataset_lib/jsonschema (e.g. miniforge).
Only reports in this private folder are written. No Site edits or publication.
"""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
from html.parser import HTMLParser
import sys,json,hashlib,html,re
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;B=O.parent;S=B.parents[3]/'recipe-atlas';SID='shah2001'
sys.path.insert(0,str(S/'scripts'))
from dataset_lib import validate_record,fmt,digest,eligibility
from build_paper_reviews import validate as validate_review
read=lambda p:json.loads(p.read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
plain=lambda s:re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]*>',' ',str(s)))).strip()
human=lambda s:s.replace('_',' ').replace('.',' · ')
def ptr(d,p):
 for k in p.split('/')[1:]:
  k=k.replace('~1','/').replace('~0','~');d=d[int(k)] if isinstance(d,list) else d[k]
 return d
def diff(a,b,p=''):
 if type(a)!=type(b):return[p]
 if isinstance(a,dict):return[q for k in a.keys()|b.keys() for q in ([p+'/'+k] if k not in a or k not in b else diff(a[k],b[k],p+'/'+k))]
 if isinstance(a,list):return[p] if len(a)!=len(b) else[q for i,(x,y) in enumerate(zip(a,b)) for q in diff(x,y,p+'/'+str(i))]
 return[] if a==b else[p]
class Node:
 def __init__(self,tag,attrs=()):self.tag=tag;self.attrs=dict(attrs);self.children=[]
 @property
 def text(self):return plain(' '.join(c.text if isinstance(c,Node) else c for c in self.children))
 def find(self,tag=None,cls=None):
  out=[]
  for c in self.children:
   if isinstance(c,Node):
    if (not tag or c.tag==tag) and (not cls or cls in c.attrs.get('class','').split()):out.append(c)
    out+=c.find(tag,cls)
  return out
class Tree(HTMLParser):
 def __init__(self,text):super().__init__(convert_charrefs=True);self.root=Node('root');self.stack=[self.root];self.feed(text)
 def handle_starttag(self,t,a):
  n=Node(t,a);self.stack[-1].children.append(n)
  if t not in {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}:self.stack.append(n)
 def handle_startendtag(self,t,a):self.handle_starttag(t,a);self.handle_endtag(t)
 def handle_endtag(self,t):
  for i in range(len(self.stack)-1,0,-1):
   if self.stack[i].tag==t:self.stack=self.stack[:i];break
 def handle_data(self,d):self.stack[-1].children.append(d)

def main():
 checks=[];hashes={};promotions={}
 def ck(name,value,detail=''):checks.append({'name':name,'passed':bool(value),'detail':detail})
 def bind(p):
  key=str(p.relative_to(S)).replace('\\','/') if p.is_relative_to(S) else 'private/'+str(p.relative_to(B)).replace('\\','/');hashes[key]=sha(p)
 drafts={p.stem:read(p) for p in (B/'canonical-drafts').glob('*.json')}
 records={rid:read(S/'data/records'/f'{rid}.json') for rid in drafts}
 proposal=read(B/'public-review-proposal/shah2001.json');reader=read(S/'data/paper-reviews/shah2001.json');generated=read(S/'dist/data/paper-reviews/shah2001.json')
 science=read(B/'canonical-records-audit.json');source=read(B/'source-audit.json');coverage=read(B/'public-review-proposal/canonical-measurement-coverage.json');sourcecoverage=read(B/'public-review-proposal/source-item-coverage.json')
 cm=read(O/'crop-manifest.json');crops={a['id']:a for a in cm['assets']}
 items={i['id']:i for s in reader['reader_sections'] for i in s['items']};pi={i['id']:i for s in proposal['reader_sections'] for i in s['items']}
 ck('Audited private canonical baseline',science['status'].startswith('passed') and set(science['record_hashes'])==set(records))
 ck('19 records / 74 operations / 111 measurements',len(records)==19 and sum(len(r['operations']) for r in records.values())==74 and sum(len(r['measurements']) for r in records.values())==111)
 ck('11 routes / 4 procedures / 4 observations',Counter(r['record_type'] for r in records.values())==Counter(literature_protocol=11,procedure=4,observation=4))
 manifest=read(S/'dist/data/dataset-manifest.json');mr={r['record_id']:r for r in manifest['records']}
 rows={r['record_id']:r for r in map(json.loads,(S/'dist/data/records.jsonl').read_text(encoding='utf8').splitlines())}
 for rid,r in records.items():
  dp=B/'canonical-drafts'/f'{rid}.json';rp=S/'data/records'/f'{rid}.json';gp=S/'dist/data/records'/f'{rid}.json';hp=S/'dist/records'/f'{rid}.html'
  for p in [dp,rp,gp,hp]:bind(p)
  ck(rid+' source-audited hash',sha(dp)==science['record_hashes'][rid]);delta=diff(drafts[rid],r);promotions[rid]=delta
  allowed={'/quality/review_status','/quality/review_scope','/quality/requested_tasks','/sources/0/main_status','/sources/0/si_status'}
  ck(rid+' only review metadata promoted',set(delta)<=allowed,repr(delta));ck(rid+' actual record schema',not validate_record(r),repr(validate_record(r)))
  ck(rid+' generated JSON and JSONL exact',r==read(gp)==rows[rid]);ck(rid+' dataset digest matches',mr[rid]['record_sha256']==digest(r))
  ck(rid+' source review promoted',r['quality']['review_status']=='source_reviewed')
  ck(rid+' physical batch IDs remain unknown',r['lineage']['batch_id'] is None and all(p['batch_id'] is None for p in r['products']))
  ck(rid+' no guessed atomic measured label',not any(a['eligible_as_measured_label'] for a in r['structure_assets']))
  raw=hp.read_text(encoding='utf8');tree=Tree(raw).root;cards=tree.find('article','operation-card');trs=tree.find('tr')
  ck(rid+' record HTML links to source reader','paper-review.html?id=shah2001' in raw)
  ck(rid+' operation-card count',len(cards)==len(r['operations']))
  for n,op in enumerate(r['operations']):
   text=cards[n].text if n<len(cards) else ''
   ck(rid+'/'+op['id']+' label/description visible',plain(op['label']) in text and plain(op['description']) in text)
   ck(rid+'/'+op['id']+' lineage visible',all(x in text for x in op['inputs']+op['outputs']+op['depends_on']))
   for key,q in op['parameters'].items():
    matches=[x for x in cards[n].find('div','quantity') if x.find('dt') and x.find('dt')[0].text==human(key)]
    ck(rid+'/'+op['id']+'/'+key+' scoped quantity visible',len(matches)==1 and plain(fmt(q)) in matches[0].text and q['status'].replace('_',' ') in matches[0].text)
   for e in op['evidence']:ck(rid+'/'+op['id']+' source '+e['locator'],e['locator'] in text)
   dest=coverage['operation_to_reader_item'].get(rid+'::'+op['id']);ck(rid+'/'+op['id']+' reader operation link',dest in items and any(x['record_id']==rid and x['json_pointer']==f'/operations/{n}' for x in items[dest]['canonical_links']))
  for n,m in enumerate(r['measurements']):
   key=rid+'::'+m['id'];dest=coverage['measurement_to_reader_item'].get(key);facts=[f for f in items[dest]['facts'] if f.get('canonical_record_id')==rid and f.get('canonical_measurement_id')==m['id']]
   ck(key+' reader exact quantity/sample/pointer',len(facts)==1 and facts[0]['canonical_quantity']==m['value'] and facts[0]['sample_id']==m['sample_id'] and ptr(r,facts[0]['json_pointer'])==m)
   ck(key+' generated measurement row',any(human(m['property']) in row.text and plain(fmt(m['value'])) in row.text and m['sample_id'] in row.text and all(e['locator'] in row.text for e in m['evidence']) for row in trs))
   if m['conditions']:ck(key+' conditions visible',any(human(m['property']) in row.text and m['sample_id'] in row.text and plain(m['conditions']) in row.text for row in trs))
 ck('138 reader items intact',set(items)==set(pi) and len(items)==138)
 for key,i in items.items():
  for field in ['title','text','claim_type','evidence','source_locators','canonical_links','sample_scope','notes','facts','training_eligible','source_audit_unit_ids']:
   ck(key+' '+field+' unchanged',i.get(field)==pi[key].get(field))
  for link in i['canonical_links']:ck(key+' actual canonical pointer '+link['record_id']+link['json_pointer'],ptr(records[link['record_id']],link['json_pointer']) is not None)
 ck('214 source units retained',set(sourcecoverage['unit_to_reader_items'])=={u['id'] for u in source['units']} and len(source['units'])==214)
 for uid,targets in sourcecoverage['unit_to_reader_items'].items():ck(uid+' reader coverage',all(uid in items[t].get('source_audit_unit_ids',[]) for t in targets))
 ck('Full-reader validation',not validate_review(reader),repr(validate_review(reader)))
 generated.pop('review_scope_label',None);ck('Generated paper JSON matches authored',generated==reader)
 for field in ['material_evidence_records','material_evidence_scope_notes','evidence_conflicts','referenced_methods','record_formulation_labels']:ck('Reader '+field+' unchanged',reader[field]==proposal[field])
 assets={a['id']:a for key in ['figures','tables','schemes','equations','source_notes'] for a in reader[key]};pa={a['id']:a for key in ['figures','tables','schemes','equations','source_notes'] for a in proposal[key]}
 ck('21 original assets and category counts',set(assets)==set(crops) and len(assets)==21 and [len(reader[k]) for k in ['figures','tables','equations','source_notes']]==[11,1,7,2])
 for key,a in assets.items():
  p=S/'dist'/a['public_asset'];bind(p);ck(key+' exact original bytes',sha(p)==a['public_asset_sha256']==crops[key]['sha256'])
  ck(key+' only final asset flags differ',set(diff(pa[key],a))<={'/reviewed','/reader_render_verified'},repr(diff(pa[key],a)))
  ck(key+' source identity retained',a['asset_provenance']['source_sha256']==cm['sources'][0]['sha256'])
 ck('Ag EDS cannot cross to Ir/Pt',assets['figure-6']['sample_links']==['shah-2001-ag-structure'] and all(x['record_id']!='shah-2001-tem-eds' for x in items['ag-eds']['canonical_links']))
 bindings=read(S/'dist/assets/chemical-registry/bindings.json')['recordBindings'];wanted=read(B/'visuals/bindings-additions.json')['recordBindings'];n=0
 for rid,bs in wanted.items():
  ck(rid+' identity bindings exact',bindings.get(rid)==bs)
  for mid,cid in bs.items():n+=1;ck(rid+'/'+mid+' binds actual canonical material',mid in {m['id'] for m in records[rid]['materials']})
 ck('99 bindings accounted for',n==99)
 index=read(S/'dist/data/materials-index.json')
 for formula in ['Ag','Ir','Pt']:
  entry=next(x for x in index['materials'] if x['formula']==formula);hp=S/'dist/data/materials'/f"{entry['id']}.json";hub=read(hp);bind(hp)
  expected={rid for rid,r in records.items() if r['material']['formula']==formula and r['record_type']=='literature_protocol'}
  ck(formula+' actual route scope',set(hub['record_ids'])&set(records)==expected)
  actual={e['record_id'] for e in hub['evidence_records'] if e['record_id'] in records};ck(formula+' exact material-specific evidence scope',actual==set(reader['material_evidence_records'][formula]))
  ck(formula+' full-source review attached',any(p['doi']==reader['doi'] and p.get('fullDocumentReview') for p in hub['papers']))
 runtime=read(O/'reader-runtime-check.json');ck('Actual source-reader/apparatus execution passed',runtime['status']=='passed' and runtime['reader_items']==138 and runtime['unique_original_assets']==21 and runtime['operation_count']==74 and runtime['binding_count']==99)
 ck('Runtime hashes are current',all(sha(S/p)==h for p,h in runtime['artifact_sha256'].items()))
 for p in [S/'data/paper-reviews/shah2001.json',S/'dist/data/paper-reviews/shah2001.json',S/'dist/data/dataset-manifest.json',S/'dist/data/materials-index.json',S/'dist/data/records.jsonl',S/'dist/paper-review.mjs',S/'dist/source-evidence.mjs',S/'dist/shah2001-protocol.mjs',S/'dist/protocol-visuals.mjs',S/'dist/assets/chemical-registry/bindings.json',S/'dist/assets/chemical-registry/registry.json',B/'canonical-records-audit.json',B/'source-audit.json',B/'public-review-proposal/shah2001.json',O/'reader-runtime-check.json']:bind(p)
 failures=[c for c in checks if not c['passed']]
 result={'status':'passed' if not failures else 'findings','checked_utc':datetime.now(timezone.utc).isoformat(),'scope':'Actual integrated records, generated record HTML, source reader, 21 originals, material hubs, 74 operation scenes and 99 bindings. Browser geometry and publication are separate.','counts':{'records':19,'operations':74,'measurements':111,'reader_items':138,'source_units':214,'original_assets':21,'material_bindings':99},'check_count':len(checks),'checks_passed':len(checks)-len(failures),'findings':failures,'promotion_differences':promotions,'artifact_sha256':hashes,'checks':checks}
 (O/'integrated-presentation-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 (O/'integrated-presentation-audit.md').write_text('# Shah 2001 integrated presentation check\n\n'+result['status']+f"; {result['checks_passed']}/{len(checks)} checks.\n\n"+result['scope']+'\n\nFindings: '+json.dumps(failures,ensure_ascii=False)+'\n',encoding='utf8')
 print(json.dumps({k:result[k] for k in ['status','counts','check_count','checks_passed','findings']},ensure_ascii=False))
 return bool(failures)
if __name__=='__main__':raise SystemExit(main())
