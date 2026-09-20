from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parent;P=R/'yao-protocol.mjs'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
s=P.read_text(encoding='utf8')
s=s.replace('Wash until the eluent is approximately pH 10; this is not a reaction-pH setting.','The reported eluent pH was approximately 10; this is not a reaction-pH setting.')
s=s.replace("txt(445,139,'4–5 µm inside the bead',18)","txt(445,139,'≈4 µm: histogram region',18)")
P.write_text(s,encoding='utf8')
assert 'Wash until' not in s
assert '≈4 µm: histogram region' in s
entries={e['id']:e for e in read(R/'molecular-assets/registry-additions.json')['entries']};refs={};products={};hashes={};notes={};checks=[]
for p in sorted((R/'canonical-drafts').glob('*.json')):
 r=read(p);rid=r['record_id'];ref='identity-yao-resin' if rid=='yao-1998-resin-conditioning' else 'identity-yao-cd-loaded-resin' if rid=='yao-1998-cadmium-loading' else 'identity-yao-hybrid'
 nonphysical={'donnan-model-no-salt','donnan-model-salt','donnan-model-one-third-swelling','donnan-model-context','pretreatment-context'}
 refs[rid]=ref;products[rid]={q['sample_id']:ref for q in r['products'] if q['sample_id'] not in nonphysical};hashes[rid]=sha(p)
 notes[rid]='Reader identity illustration only. '+entries[ref]['caption']+' This reference does not join distinct analytical specimens or establish phase, dimensions, atomic coordinates or a physical batch.'
 checks.append({'check':rid+' reference exists and is a card','passed':ref in entries and entries[ref]['model2dPath'] is None and entries[ref]['model3dPath'] is None})
 if rid in ('yao-1998-resin-conditioning','yao-1998-cadmium-loading'):
  checks.append({'check':rid+' no sulfur/CdS reference','passed':ref!='identity-yao-hybrid'})
save(R/'molecular-assets/product-reference-proposal.json',{'scope':'Optional reader identity illustrations; not measured structures or canonical synthesis inputs','sourceDoi':'10.1021/la970480g','eligible_training':False,'references':refs,'productBindings':products,'bindingNotes':notes,'sourceRecordSha256':hashes,'validation':{'status':'passed' if all(q['passed'] for q in checks) else 'failed','checks':checks}})
print(json.dumps({'references':len(refs),'product_bindings':sum(map(len,products.values())),'module_sha256':sha(P)}))
