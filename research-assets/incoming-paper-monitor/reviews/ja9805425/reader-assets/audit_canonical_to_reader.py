"""Audit actual built Peng records, reader, exports and source associations.

Run only after the Site-owning root confirms its build is ready. Writes only
this private audit directory. Browser rendering and deployment are separate.
"""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
from html.parser import HTMLParser
import sys,json,hashlib,html,re
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent;B=OUT.parent;SITE=B.parents[3]/'recipe-atlas'
SID='peng1998';P='peng-1998-'
sys.path.insert(0,str(SITE/'scripts'))
from dataset_lib import validate_record,eligibility,training_view,fmt,digest,build_groups
from build_paper_reviews import validate as validate_review

def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def plain(s):return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]*>',' ',str(s)))).strip()
def human(s):return s.replace('_',' ').replace('.',' · ')
def ptr(data,p):
 for k in p.split('/')[1:]:data=data[int(k)] if isinstance(data,list) else data[k.replace('~1','/').replace('~0','~')]
 return data
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
  result=[]
  for c in self.children:
   if isinstance(c,Node):
    if (not tag or c.tag==tag) and (not cls or cls in c.attrs.get('class','').split()):result.append(c)
    result+=c.find(tag,cls)
  return result
class Tree(HTMLParser):
 def __init__(self,text):super().__init__(convert_charrefs=True);self.root=Node('root');self.stack=[self.root];self.feed(text)
 def handle_starttag(self,tag,attrs):
  node=Node(tag,attrs);self.stack[-1].children.append(node)
  if tag not in {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}:self.stack.append(node)
 def handle_startendtag(self,tag,attrs):self.handle_starttag(tag,attrs);self.handle_endtag(tag)
 def handle_endtag(self,tag):
  for i in range(len(self.stack)-1,0,-1):
   if self.stack[i].tag==tag:self.stack=self.stack[:i];break
 def handle_data(self,data):self.stack[-1].children.append(data)

def main():
 checks=[];hashes={};measure_links=[];oprows=[];promotions={}
 def check(name,value,detail=''):checks.append({'name':name,'passed':bool(value),'detail':detail})
 def bind(p):
  label=str(p.relative_to(SITE)).replace('\\','/') if p.is_relative_to(SITE) else 'private/'+str(p.relative_to(B)).replace('\\','/')
  hashes[label]=sha(p)
 drafts={p.stem:read(p)for p in (B/'canonical-drafts').glob('*.json')}
 records={rid:read(SITE/'data/records'/f'{rid}.json')for rid in drafts}
 science=read(B/'canonical-records-audit.json');audit_hashes={x.get('record_id',Path(x.get('file','')).stem):x['sha256']for x in science['records']}
 ledger=read(SITE/'data/paper-reviews/peng1998.json');generated=read(SITE/'dist/data/paper-reviews/peng1998.json')
 proposal=read(B/'public-review-proposal/peng1998.json');source=read(B/'source-audit.json')
 coverage=read(B/'public-review-proposal/source-item-coverage.json');mc=read(B/'public-review-proposal/canonical-measurement-coverage.json')
 manifest=read(SITE/'dist/data/dataset-manifest.json');mr={r['record_id']:r for r in manifest['records']}
 items={i['id']:i for s in ledger['reader_sections']for i in s['items']};olditems={i['id']:i for s in proposal['reader_sections']for i in s['items']}
 routeids={P+'cdse-focusing',P+'inas-focusing'}
 check('Twelve records, 159 measurements, 28 operations',len(records)==12 and sum(len(r['measurements'])for r in records.values())==159 and sum(len(r['operations'])for r in records.values())==28)
 check('Two routes, four procedures, six observations',Counter(r['record_type']for r in records.values())==Counter(literature_protocol=2,procedure=4,observation=6))
 check('Independent canonical audit passed for all records',science['status'].startswith('passed') and set(audit_hashes)==set(records))
 for rid,r in records.items():
  dp=B/'canonical-drafts'/f'{rid}.json';rp=SITE/'data/records'/f'{rid}.json';gp=SITE/'dist/data/records'/f'{rid}.json';hp=SITE/'dist/records'/f'{rid}.html'
  for path in[dp,rp,gp,hp]:bind(path)
  check(rid+' actual schema/graph validation',not validate_record(r),repr(validate_record(r)))
  check(rid+' audited private source fingerprint',sha(dp)==audit_hashes[rid])
  dd=diff(drafts[rid],r);promotions[rid]=dd
  check(rid+' only review-status promotion changes',set(dd)<={'/quality/review_status','/quality/review_scope','/quality/requested_tasks','/sources/0/main_status','/sources/0/si_status'},repr(dd))
  check(rid+' exact generated record and manifest digest',rp.read_bytes()==gp.read_bytes() and mr[rid]['record_sha256']==digest(r))
  check(rid+' main/SI status correctly scoped',r['quality']['review_status']=='source_reviewed' and 'matched SI' in r['quality']['review_scope'] and 'three scientific' in r['sources'][0]['si_status'])
  check(rid+' no fabricated physical batch IDs',r['lineage']['batch_id'] is None and all(p['batch_id'] is None for p in r['products']))
  check(rid+' no atomic reference promoted to measured structure',not any(a['eligible_as_measured_label']for a in r['structure_assets']))
  wanted={'precursor_selection','partial_protocol'}if rid in routeids else set()
  check(rid+' task eligibility restricted to two routes',{k for k,v in eligibility(r).items()if v['eligible']}==wanted and mr[rid]['eligibility']==eligibility(r))
  raw=hp.read_text(encoding='utf8');tree=Tree(raw).root;pagetext=tree.text
  check(rid+' source record type and review link displayed',human(r['record_type'])in pagetext and 'paper-review.html?id='+SID in raw and r['quality']['review_scope'] in pagetext)
  cards=tree.find('article','operation-card');check(rid+' operation count in generated page',len(cards)==len(r['operations']))
  for index,o in enumerate(r['operations']):
   card=cards[index]if index<len(cards)else Node('missing');text=card.text
   check(rid+'/'+o['id']+' label and description displayed',o['label']in text and (not o['description']or plain(o['description'])in text))
   check(rid+'/'+o['id']+' inputs outputs dependencies displayed',all(x in text for x in o['inputs']+o['outputs']+o['depends_on']))
   for field in['environment','endpoint']:
    value=o[field]['value']
    check(rid+'/'+o['id']+' '+field+' value/missingness retained',(plain(value)in text if value is not None else o[field]['status'].replace('_',' ').capitalize()in text))
   quantitynodes=card.find('div','quantity')
   for key,q in o['parameters'].items():
    expected=plain(fmt(q));label=human(key)
    matching=[n for n in quantitynodes if n.find('dt')and n.find('dt')[0].text==label]
    check(rid+'/'+o['id']+'/'+key+' correctly scoped displayed quantity',len(matching)==1 and expected in matching[0].text and q['status'].replace('_',' ')in matching[0].text,repr(expected))
    oprows.append({'record_id':rid,'operation_id':o['id'],'parameter':key,'canonical_value':q,'displayed_expected':expected})
   for e in o['evidence']:check(rid+'/'+o['id']+' source locator '+e['locator'],e['locator']in text)
  mrows=tree.find('tr')
  for n,m in enumerate(r['measurements']):
   key=rid+'::'+m['id'];target=mc['measurement_to_reader_item'].get(key)
   check(key+' destination exists',target in items)
   facts=[f for f in items.get(target,{}).get('facts',[])if f.get('canonical_record_id')==rid and f.get('canonical_measurement_id')==m['id']]
   check(key+' exact canonical value/unit/sample/pointer in reader',len(facts)==1 and facts[0]['value']==m['value']['value'] and facts[0].get('unit')==m['value'].get('unit') and facts[0]['sample_id']==m['sample_id'] and ptr(r,facts[0]['json_pointer'])==m)
   check(key+' actual HTML measurement row',any(human(m['property'])in row.text and plain(fmt(m['value']))in row.text and m['sample_id']in row.text and all(e['locator']in row.text for e in m['evidence'])for row in mrows))
   if m['conditions']:check(key+' measurement conditions visible',any(human(m['property'])in row.text and m['sample_id']in row.text and plain(m['conditions'])in row.text for row in mrows))
   measure_links.append({'record_id':rid,'measurement_id':m['id'],'reader_item':target,'sample_id':m['sample_id']})
  if rid in routeids:
   check(rid+' target does not fabricate measured size or phase',r['intended_target']['size']['value']is None and r['intended_target']['phase']['value']is None)
   for task in wanted:
    view=training_view(r,task)
    check(rid+'/'+task+' outcome fields excluded from model input','measurements'not in view['input']and 'products'not in view['input'])
 # Source audit independently described all pages; public mapping must preserve that unit set.
 check('119 reader items, all160 independent units and159measurement links',len(items)==119 and len(coverage['unit_to_reader_items'])==160 and len(measure_links)==159)
 check('Public source coverage agrees with independent inventory',set(coverage['unit_to_reader_items'])=={u['id']for u in source['units']})
 for uid,targets in coverage['unit_to_reader_items'].items():check(uid+' public mapped destinations resolve',all(t in items and uid in items[t].get('source_audit_unit_ids',[])for t in targets))
 for key,item in items.items():
  old=olditems[key]
  for field in['text','title','claim_type','evidence','notes','facts','sample_scope']:
   check(key+' reviewed '+field+' retained',item[field]==old[field])
  for link in item['canonical_links']:check(key+' actual canonical pointer '+link['record_id']+link['json_pointer'],link['record_id']in records and ptr(records[link['record_id']],link['json_pointer'])is not None)
  for link in item['sample_scope'].get('canonical_sample_links',[]):check(key+' actual scoped sample '+link['sample_id'],ptr(records[link['record_id']],link['json_pointer'])['sample_id']==link['sample_id'])
 check('Both inspected direct method notes and all22references',len(ledger['referenced_methods'])==22 and {r['reference_number']for r in ledger['referenced_methods']if r['direct_source_note_reviewed']}=={21,22})
 check('Main and matchedSI cover/scientific pages distinct',ledger['review_scope']=='supplied_main_and_matched_si' and [(d['role'],d['page_count'])for d in ledger['documents']]==[('main',2),('si',4)] and ledger['supporting_information']['scientific_pages']==3)
 check('Actual full-reader validator',not validate_review(ledger),repr(validate_review(ledger)))
 generated.pop('review_scope_label',None);check('Generated source JSON equals authored source JSON',generated==ledger)
 # Critical distinctions are checked independently of count/mapping completeness.
 semantic={'cdse-stock':['2 : 5 : 100','tributylphosphine','not the total stock mass'],
 'inas-indium-stock':['0.33 g','per mL','not a measured final solution volume'],
 'inas-growth-temperature':['250 °C','260 °C'],
 'cdse-injection':['360','300','less than 0.1 s'],
 'inas-first-injection':['300','250','less than 0.1 s'],
 'inas-feeds':['0.5 mL at 23 min','0.8 mL at 158 min'],
 'cdse-tem':['8.5 nm','25 nm','No injection history'],
 'inas-reabsorption':['around 1 eV','higher-energy half'],
 'model-figure4':['infinite','arbitrary units'],
 'automation-outlook':['does not demonstrate'],
 'structural-scope':['SAED','do not provide'],
 'generality-limits':['CdS','InP','do not provide']}
 for key,need in semantic.items():check(key+' scientific interpretation boundary',all(n in items[key]['text']for n in need))
 assets=[a for cat in['figures','tables','schemes','equations','source_notes']for a in ledger[cat]]
 originals={a['id']:a for a in read(OUT/'crop-manifest.json')['assets']}
 check('Eleven originals:5figures2tables2equations2notes',len(assets)==11 and [len(ledger[k])for k in['figures','tables','equations','source_notes']]==[5,2,2,2])
 for a in assets:
  p=SITE/'dist'/a['public_asset'];bind(p)
  check(a['id']+' original bytes/source fingerprint retained',sha(p)==a['public_asset_sha256']==originals[a['id']]['sha256'] and a['asset_provenance']['source_sha256']==originals[a['id']]['source_sha256'])
  check(a['id']+' explicit sample/model scope',bool(a['sample_scope'])and bool(a['quantitative_context'])and not a['training_eligible'])
 check('TEM figure only attached to unassigned observation',next(a for a in assets if a['id']=='figure-3')['sample_links']==[P+'cdse-tem'])
 check('No provided SAED invented',not any('saed' in a['id'].lower()for a in assets))
 runtime=read(OUT/'reader-runtime-check.json')
 check('Actual reader DOM execution passed',runtime['status']=='passed'and runtime['reader_items']==119 and runtime['unique_original_assets']==11)
 check('Runtime fingerprints current',all(sha(SITE/p)==h for p,h in runtime['artifact_sha256'].items()))
 # Correlated data remain together and optical/calibration/theory rows do not become recipes.
 allrecords=[read(p)for p in(SITE/'data/records').glob('*.json')];groups=build_groups(allrecords)
 check('All12records share one evaluation group and split',len({groups[rid]for rid in records})==1 and len({mr[rid]['split']for rid in records})==1)
 rawexport={r['record_id']:r for r in[json.loads(s)for s in(SITE/'dist/data/records.jsonl').read_text(encoding='utf8').splitlines()if s.strip()]}
 for rid,r in records.items():check(rid+' complete JSONL record retained',rawexport[rid]==r)
 for task in eligibility(next(iter(records.values()))):
  ep=SITE/'dist/data/exports'/f'{task}.jsonl';bind(ep);rows=[json.loads(s)for s in ep.read_text(encoding='utf8').splitlines()if s.strip()]
  own=[r for r in rows if r['record_id']in records];expected=routeids if task in['precursor_selection','partial_protocol']else set()
  check(task+' correct route-only export scope',len(own)==len(expected)and{r['record_id']for r in own}==expected)
  for e in own:
   rid=e['record_id'];v=training_view(records[rid],task)
   check(rid+'/'+task+' exact actual task input/output',e['input']==v['input']and e['output']==v['output'])
   check(rid+'/'+task+' same source group and record digest',e['group_id']==groups[rid]and e['record_sha256']==digest(records[rid]))
 index=read(SITE/'dist/data/materials-index.json');hubs={}
 for formula,route in[('CdSe',P+'cdse-focusing'),('InAs',P+'inas-focusing')]:
  meta=next(h for h in index['materials']if h['formula']==formula);hp=SITE/'dist/data/materials'/f"{meta['id']}.json";bind(hp);hub=read(hp)
  check(formula+' only material-specific route added',set(hub['record_ids'])&set(records)=={route})
  check(formula+' existing-source paper review links matchedSI',next(p for p in hub['papers']if p['doi']==ledger['doi'])['fullDocumentReview']['scope']=='supplied_main_and_matched_si')
  own_evidence={r['record_id']for r in hub['evidence_records']if r['record_id']in records}
  check(formula+' preserved material evidence map',own_evidence==set(ledger['material_evidence_records'][formula]))
  check(formula+' separate procedures not promoted to routes',not(set(records)-routeids)&set(hub['record_ids']))
  hubs[formula]={'id':hub['id'],'active_route':route,'source_records':sorted(own_evidence)}
 for p in[SITE/'data/paper-reviews/peng1998.json',SITE/'dist/data/paper-reviews/peng1998.json',SITE/'dist/data/dataset-manifest.json',SITE/'dist/data/records.jsonl',SITE/'dist/data/materials-index.json',SITE/'dist/paper-review.mjs',SITE/'dist/source-evidence.mjs',SITE/'dist/protocol-visuals.mjs',SITE/'dist/peng1998-protocol.mjs',SITE/'scripts/build_dataset.py',SITE/'scripts/dataset_lib.py',B/'canonical-records-audit.json',B/'source-audit.json',B/'public-review-proposal/source-item-coverage.json',B/'public-review-proposal/peng1998.json',OUT/'reader-runtime-check.json']:bind(p)
 failures=[c for c in checks if not c['passed']]
 result={'status':'passed_bounded_canonical_to_reader_audit'if not failures else'findings','checked_utc':datetime.now(timezone.utc).isoformat(),'scope':'Actual canonical records, generated HTML quantity/value/sample context, reader execution, exact original assets, source coverage, task exports and material-hub associations. Browser geometry and publication are separate.',
 'check_count':len(checks),'checks_passed':len(checks)-len(failures),'findings':failures,'counts':{'records':12,'operations':28,'operation_quantities':len(oprows),'measurements':159,'reader_items':119,'source_units':160,'original_assets':11},
 'measurement_reader_links':measure_links,'operation_quantity_checks':oprows,'promotion_differences':promotions,'hubs':hubs,'asset_flags':[{k:a[k]for k in['id','reviewed','reader_render_verified']}for a in assets],
 'artifact_sha256':hashes,'checks':checks}
 (OUT/'canonical-to-reader-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 (OUT/'canonical-to-reader-audit.md').write_text('# Peng 1998 actual canonical-to-reader audit\n\n'+result['status']+f"; {result['checks_passed']}/{len(checks)} checks.\n\n"+result['scope']+'\n\n'+json.dumps(result['counts'],indent=2)+'\n\nFindings: '+json.dumps(failures,ensure_ascii=False)+'\n',encoding='utf8')
 print(json.dumps({k:result[k]for k in['status','check_count','checks_passed','counts','findings']},ensure_ascii=False))
 return bool(failures)
if __name__=='__main__':raise SystemExit(main())
