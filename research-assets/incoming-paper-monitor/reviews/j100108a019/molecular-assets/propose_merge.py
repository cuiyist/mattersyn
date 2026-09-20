"""Prepare merged JSON privately; never write to the Site or copy existing assets.

The site owner can inspect merged-proposal/ and copy the package's svg/models
files plus the approved merged JSON through the normal Site workflow.
"""
import argparse,copy,collections,hashlib,json
from pathlib import Path
BASE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--existing',type=Path,default=Path('[local path redacted]'))
args=parser.parse_args()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
registry=read(args.existing/'registry.json');bindings=read(args.existing/'bindings.json')
add=read(BASE/'registry-additions.json');badd=read(BASE/'bindings-additions.json')
known={e['id']:e for e in registry['entries']}
assert not set(known).intersection(e['id'] for e in add['entries']),'New entry ID already exists; reconcile explicitly.'
assert not set(bindings['recordBindings']).intersection(badd['recordBindings']),'Record bindings already exist; reconcile explicitly.'
for e in read(BASE/'reused-references.json')['entries']:
 assert e['id'] in known
 for key,path in e['assetPaths'].items():
  assert known[e['id']][key]==path and sha(args.existing/path)==e['assetHashes'][key],(e['id'],key)
for e in add['entries']:
 for key in ['svgPath','model2dPath','model3dPath']:
  if e.get(key):
   assert not (args.existing/e[key]).exists(),'Asset collision: '+e[key]
   assert sha(BASE/e[key])==e['assetHashes'][key]
registry['entries'].extend(copy.deepcopy(add['entries']))
for key in ['recordBindings','bindingNotes','sourceRecordSha256']:
 bindings.setdefault(key,{}).update(badd[key])
registry['summary'].update({'entryCount':len(registry['entries']),
 'recordCount':len(bindings['recordBindings']),'bindingCount':sum(map(len,bindings['recordBindings'].values())),
 'depictionKinds':dict(collections.Counter(e['depictionKind'] for e in registry['entries'])),
 'twoDimensionalModels':sum(bool(e.get('model2dPath')) for e in registry['entries']),
 'rotatableThreeDimensionalModels':sum(bool(e.get('model3dPath')) for e in registry['entries'])})
registry['summary']['materialFormulas']=sorted(set(registry['summary'].get('materialFormulas',[])+['Si/SiOx']))
for note in add['notes']:
 if note not in registry['notes'] and not note.startswith('This is a delta'):registry['notes'].append(note)
out=BASE/'merged-proposal';out.mkdir(exist_ok=True)
dump(out/'registry.json',registry);dump(out/'bindings.json',bindings)
dump(out/'merge-report.json',{'status':'private_proposal_only','summary':registry['summary'],
 'existingRegistrySha256':sha(args.existing/'registry.json'),'existingBindingsSha256':sha(args.existing/'bindings.json'),
 'registryAdditionsSha256':sha(BASE/'registry-additions.json'),'bindingsAdditionsSha256':sha(BASE/'bindings-additions.json'),
 'mergedRegistrySha256':sha(out/'registry.json'),'mergedBindingsSha256':sha(out/'bindings.json'),
 'important':'Before publication, recheck each imported Site record against the reviewed private draft. If only JSON serialization changes, verify parsed equality before updating raw-byte sourceRecordSha256 values.'})
print(json.dumps({'status':'private_proposal_only','entries':len(registry['entries']),
 'records':len(bindings['recordBindings']),'bindings':sum(map(len,bindings['recordBindings'].values()))}))
