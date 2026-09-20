"""Finalize private Yao assets and validate serialized connectivity/provenance."""
from pathlib import Path
import json,hashlib,re,collections
R=Path(__file__).resolve().parent;O=R/'molecular-assets'
def load(p):return json.loads(p.read_text(encoding='utf8'))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
# Source-precision wording: high magnification does not establish lattice resolution.
p=R/'yao-protocol.mjs';s=p.read_text(encoding='utf8')
s=s.replace("txt(300,103,'Distilled water',19)","txt(300,103,optics?'Water':'Distilled water',19)")
s=s.replace("'wash-water':'Distilled water'","'wash-water':isConditioning(r)?'Distilled water':'Water'")
s=s.replace("'Acquire higher-resolution TEM fields'","'Acquire high-magnification TEM fields'")
s=s.replace("hi?'Figure 4 · a':'Figures 3a–c / 7b'","hi?'Figure 4 · sample a':'Figures 3 / 7'")
p.write_text(s,encoding='utf8')
checks=[]
def check(v,label):checks.append({'passed':bool(v),'check':label})
expected={'cadmium-acetate-dihydrate':('C4H10CdO6',5),'sodium-chloride':('ClNa',2),'hydrochloric-acid-aqueous':('HCl',2),'sodium-hydroxide':('HNaO',2),'lithium-chloride':('ClLi',2),'potassium-chloride':('ClK',2),'tetramethylammonium-chloride':('C4H12ClN',2)}
def formula(s):return collections.Counter({e:int(n or 1) for e,n in re.findall(r'([A-Z][a-z]?)(\d*)',s)})
entries={e['id']:e for e in load(O/'registry-additions.json')['entries']}
for rid,(f,n) in expected.items():
 e=entries[rid];m=load(O/e['model2dPath']);ats=m['atoms'];bonds=m['bonds'];ct=collections.Counter();adj={a['index']:set() for a in ats}
 check([a['index'] for a in ats]==list(range(len(ats))),rid+' contiguous atom indices')
 for a in ats:ct[a['element']]+=1;ct['H']+=a.get('implicitHydrogenCount',0)
 check(+ct==formula(f),rid+' serialized atomic and hydrogen stoichiometry')
 check(sum(a.get('formalCharge',0) for a in ats)==0,rid+' serialized net charge')
 for b in bonds:
  check(b['a'] in adj and b['b'] in adj and b['a']!=b['b'],rid+' bond endpoints')
  adj[b['a']].add(b['b']);adj[b['b']].add(b['a'])
 groups=[];seen=set()
 for a in adj:
  if a in seen:continue
  stack=[a];g=set()
  while stack:
   at=stack.pop()
   if at in g:continue
   g.add(at);stack.extend(adj[at]-g)
  groups.append(g);seen|=g
 check(len(groups)==n,rid+' disconnected component count')
 check(not m['has3D'] and not m['allowRotation'] and all(a['z']==0 for a in ats),rid+' honest 2D-only geometry')
 check(m['eligible_training'] is False,rid+' reference-only training scope')
 for k,h in e['assetHashes'].items():check(sha(O/e[k])==h,rid+' actual '+k+' hash')
for rid in ['identity-yao-resin','identity-yao-cd-loaded-resin','identity-yao-hybrid','identity-yao-diagnostic-hs']:
 e=entries[rid];check(e['model2dPath'] is None and e['model3dPath'] is None,rid+' no invented full molecular model')
bindings=load(O/'bindings-additions.json')
for p in sorted((R/'canonical-drafts').glob('*.json')):
 d=load(p);rid=d['record_id'];check(bindings['sourceRecordSha256'].get(rid)==sha(p),rid+' current source-record hash')
 check(set(bindings['recordBindings'][rid])=={m['id'] for m in d['materials']},rid+' exhaustive material bindings')
check(not any(w in json.dumps(bindings['bindingNotes']).lower() for w in ['danek','veinot','littau','twofold pyridine','electrospray']), 'No cross-paper conditions in binding notes')
save(O/'serialized-validation.json',{'status':'passed' if all(x['passed'] for x in checks) else 'failed','passed':sum(x['passed'] for x in checks),'failed':sum(not x['passed'] for x in checks),'checks':checks,'scope':'Serialized atom/bond/charge/components, reference flags, hashes, exhaustive current bindings and historical-context exclusion. No claim of independent scientific audit.'})
print(json.dumps({'serialized_passed':sum(x['passed'] for x in checks),'failed':sum(not x['passed'] for x in checks)}))
