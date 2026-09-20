from pathlib import Path
import json,hashlib,sys
A=Path(__file__).parent;R=A.parent;S=A/'author-v1-read-snapshot'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def diff(a,b,p=''):
 if type(a)!=type(b):return [{'path':p,'before':a,'after':b}]
 if isinstance(a,dict):
  out=[]
  for k in sorted(a.keys()|b.keys()):
   q=p+'/'+k.replace('~','~0').replace('/','~1')
   if k not in a:out.append({'path':q,'added':b[k]})
   elif k not in b:out.append({'path':q,'removed':a[k]})
   else:out+=diff(a[k],b[k],q)
  return out
 if isinstance(a,list):
  out=[]
  for i in range(max(len(a),len(b))):
   q=p+'/'+str(i)
   if i>=len(a):out.append({'path':q,'added':b[i]})
   elif i>=len(b):out.append({'path':q,'removed':a[i]})
   else:out+=diff(a[i],b[i],q)
  return out
 return [] if a==b else [{'path':p,'before':a,'after':b}]
if __name__=='__main__':
 for name in sys.argv[1:] or ['source-facts.json','source-inventory.json']:
  d=diff(load(S/name),load(R/name));print(name,len(d))
  for v in d:print(json.dumps(v,ensure_ascii=False))
