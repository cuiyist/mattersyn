from pathlib import Path
import json,re,hashlib
B=Path(__file__).resolve().parent
old=json.loads((B/'canonical-before-prose-cleanup.json').read_text(encoding='utf8'))
maps={x['old']:x['new'] for x in json.loads((B/'prose-replacements.json').read_text(encoding='utf-8-sig'))['replacements']}
pat=re.compile('|'.join(re.escape(k) for k in sorted(maps,key=len,reverse=True)))
changes=[];checked=0
def compare(a,b,p):
 global checked
 checked+=1
 if a==b:return
 assert type(a)==type(b),(p,'type changed')
 if isinstance(a,dict):
  assert a.keys()==b.keys(),(p,'dictionary keys changed')
  for k in a:compare(a[k],b[k],p+'/'+k)
 elif isinstance(a,list):
  assert len(a)==len(b),(p,'array length changed')
  for i,(x,y) in enumerate(zip(a,b)):compare(x,y,p+'/'+str(i))
 elif isinstance(a,str):
  assert pat.sub(lambda m:maps[m.group()],a)==b,(p,a,b)
  assert not re.search(r'/(id|record_id|sample_id|formula|doi|source_id|url|unit|status|action|stage|branch|kind|property|schema_version)$',p),p
  changes.append({'path':p,'before':a,'after':b})
 else:raise AssertionError((p,a,b))
for f,a in old.items():compare(a,json.loads((B/'canonical-drafts'/f).read_text(encoding='utf8')),f)
out={'status':'passed','scope':'Exact audited explicit human-prose substitutions only; data shape, numeric/Boolean/null fields, identifiers, formulas, units, statuses, action/stage and links unchanged.','visited_nodes':checked,'changed_prose_values':len(changes),'changes':changes,'records':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((B/'canonical-drafts').glob('*.json'))}}
(B/'prose-delta-validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in out.items() if k not in ('changes','records')}))
