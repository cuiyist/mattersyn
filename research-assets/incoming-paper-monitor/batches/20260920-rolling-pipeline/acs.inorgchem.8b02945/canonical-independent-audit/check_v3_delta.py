"""Independent exact delta check; run only after the author identifies final v3 freeze."""
from pathlib import Path
from copy import deepcopy
import json,hashlib,sys
O=Path(__file__).resolve().parent;F=O.parent;V2=F/'canonical-proposal/draft-v2';V3=Path(sys.argv[1])
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def differences(a,b,p=''):
 if type(a)!=type(b):return [{'path':p,'before':a,'after':b}]
 if isinstance(a,dict):
  out=[]
  for k in sorted(set(a)|set(b)):
   if k not in a or k not in b:out.append({'path':p+'/'+k,'before':a.get(k),'after':b.get(k)})
   else:out.extend(differences(a[k],b[k],p+'/'+k))
  return out
 if isinstance(a,list):
  if len(a)!=len(b):return [{'path':p,'before':a,'after':b}]
  return [d for i,(x,y) in enumerate(zip(a,b)) for d in differences(x,y,p+'/'+str(i))]
 return [] if a==b else [{'path':p,'before':a,'after':b}]
checks=[];bound={}
def ck(n,b):checks.append({'check':n,'passed':bool(b)})
freeze=read(V3/'package-freeze.json');bound[str(V3/'package-freeze.json')]=sha(V3/'package-freeze.json')
for category in ['bound_files','external_bound_inputs']:
 for p,h in freeze.get(category,{}).items():
  fp=Path(p) if Path(p).is_absolute() else V3/p
  ck('v3 hash '+p,sha(fp)==(h.get('sha256') if isinstance(h,dict) else h));bound[str(fp)]=sha(fp)
oldrecords={x['record_id']:x for x in read(V2/'record-manifest.json')['records']};newrecords={x['record_id']:x for x in read(V3/'record-manifest.json')['records']}
ck('all 30 record IDs unchanged',set(oldrecords)==set(newrecords) and len(newrecords)==30)
for rid,x in oldrecords.items():ck(rid+' original canonical bytes unchanged',sha(x['path'])==sha(newrecords[rid]['path'])==x['sha256'])
a=read(V2/'reader/friedfeld2019.json');b=read(V3/'reader/friedfeld2019.json');d=differences(a,b)
items2={x['id']:x for s in a['reader_sections'] for x in s['items']};items3={x['id']:x for s in b['reader_sections'] for x in s['items']};ck('417 item IDs unchanged',set(items2)==set(items3) and len(items3)==417)
omissions={x['item_id']:x for x in read(O/'sample-link-omissions.json')};texts=[]
for iid,x in items2.items():
 y=items3[iid];cp=deepcopy(y)
 for k in ['title','text','notes']:
  if x.get(k)!=y.get(k):texts.append({'item_id':iid,'field':k,'before':x.get(k),'after':y.get(k)})
  if k in x:cp[k]=x[k]
  else:cp.pop(k,None)
 if iid in omissions:
  expected=omissions[iid];old=x['sample_scope']['canonical_sample_links'];new=y['sample_scope']['canonical_sample_links'];key=lambda z:(z['record_id'],z['sample_id'],z['json_pointer'])
  ck(iid+' exact one named link added',len(new)==len(old)+1 and all(z in new for z in old) and set(map(key,new))-set(map(key,old))=={(expected['record_id'],expected['sample_id'],expected['pointer'])})
  cp['sample_scope']['canonical_sample_links']=old
 if iid=='table-gaussian-boxes':
  for j,num in enumerate([38,39]):
   ck('Gaussian asset label '+str(num)+' spacing only',x['original_assets'][j]['label']==f'Open original S {num} three Gaussian fit boxes at readable scale' and y['original_assets'][j]['label']==f'Open original S{num} three Gaussian fit boxes at readable scale')
   cp['original_assets'][j]['label']=x['original_assets'][j]['label']
 ck(iid+' every other field and raw scientific object unchanged',x==cp)
 for text in [y['title'],y['text'],*y.get('notes',[])]:ck(iid+' no raw panel JSON or empty gap prose','Source panel assignments:' not in text and 'Unreported details: .' not in text)
allowed_top=set(['/equations/0/label','/equations/1/label','/evidence_conflicts/11/title','/remaining_gaps/0','/schemes/0/caption_paraphrase','/schemes/1/caption_paraphrase','/source_notes/0/caption_paraphrase'])
allowed_top.update('/evidence_conflicts/'+str(i)+'/description' for i in range(12))
allowed_top.update('/figures/'+str(i)+'/caption_paraphrase' for i in range(44))
allowed_top.update('/recipe_inventory/'+str(i)+'/label' for i in [5,7,8,12,18])
for change in d:
 if not change['path'].startswith('/reader_sections/'):
  ck('top-level permitted display-only path '+change['path'],change['path'] in allowed_top)
for i in [0,1]:
 ck('equation label spacing '+str(i),b['equations'][i]['label']==a['equations'][i]['label'].replace('S 38','S38').replace('S 39','S39'))
for i in [5,7,8,12,18]:
 ck('recipe label spacing '+str(i),''.join(b['recipe_inventory'][i]['label'].split())==''.join(a['recipe_inventory'][i]['label'].split()))
ck('remaining gap citation wording only',b['remaining_gaps'][0]==a['remaining_gaps'][0].replace('cited43/45','cited references 43 and 45'))
for fig in b['figures']:
 iid='source-figures-'+fig['id'].removeprefix('asset-friedfeld2019-')
 ck(fig['id']+' caption matches actually reviewed item prose',iid in items3 and fig['caption_paraphrase']==items3[iid]['text'])
sys.path.insert(0,'[local path redacted]')
import build_paper_reviews as consumer
consumer.ROOT=V3/'isolated-reader-fixture'
reader_errors=consumer.validate(b)
ck('actual current reader validator on private v3 fixture',not reader_errors)
bound[str(V2/'package-freeze.json')]=sha(V2/'package-freeze.json')
(O/'reader-v3-changed-prose.json').write_text(json.dumps(texts,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(O/'reader-v3-changed-prose.txt').write_text('\n\n'.join(x['item_id']+' / '+x['field']+'\n'+str(x['after']) for x in texts),encoding='utf8')
(O/'reader-v3-all-delta.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
bound[str(Path(consumer.__file__))]=sha(Path(consumer.__file__))
result={'status':'passed' if all(x['passed'] for x in checks) else 'findings','check_count':len(checks),'failures':[x for x in checks if not x['passed']],'reader_validator_errors':reader_errors,'changed_prose_fields':len(texts),'all_reader_delta_paths':[x['path'] for x in d],'checks':checks,'bound_files':bound}
(O/'v3-delta-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({k:v for k,v in result.items() if k not in ['checks','bound_files','all_reader_delta_paths']},ensure_ascii=False))
