"""Preserve v1; correct only three duplicated PbO lower-bound captions."""
from pathlib import Path
from datetime import datetime,timezone
from copy import deepcopy
import json,hashlib
V=Path(__file__).resolve().parent;O=V.parent
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def diff(a,b,p=''):
 if isinstance(a,dict) and isinstance(b,dict):
  assert a.keys()==b.keys()
  return [d for k in a for d in diff(a[k],b[k],p+'/'+k)]
 if isinstance(a,list) and isinstance(b,list):
  assert len(a)==len(b)
  return [d for i,(x,y) in enumerate(zip(a,b)) for d in diff(x,y,p+'/'+str(i))]
 return [] if a==b else [{'path':p,'before':a,'after':b}]
assert not (V/'package-freeze.json').exists()
prior=O/'package-freeze.json';assert sha(prior)=='d32f066455e62cf3620fbc1421891a37dc6ba6dc87fb6a6bf95def64259b6fd0'
freeze=read(prior);checks=0
for f in freeze['bound_files']:assert sha(f['path'])==f['sha256'];checks+=1
slots=read(O/'material-slot-map.json');bindings=read(O/'bindings-proposal.json');oldslots=deepcopy(slots);oldbindings=deepcopy(bindings)
expected={'evans-2010-pb-oleate','evans-2010-pbse-msc-family','evans-2010-reagents'};found=set()
for slot in slots:
 if slot['material_id']!='pbo':continue
 rid=slot['record_id'];found.add(rid);q=slot['canonical_identity']['quantities']['purity']
 assert q['value'] is None and q['minimum']==99.9 and q['minimum_exclusive'] is False and q['raw_text']=='99.9+% as printed';checks+=1
 before=slot['viewOverrides']['caption'];assert before.count('Source commercial purity: None%')==1;checks+=1
 after=before.replace('Source commercial purity: None%','Source commercial purity: ≥99.9% (99.9+% as printed)')
 slot['viewOverrides']['caption']=after
 assert bindings['bindingNotes'][rid]['pbo']['viewOverrides']['caption']==before;checks+=1
 bindings['bindingNotes'][rid]['pbo']['viewOverrides']['caption']=after
assert found==expected;checks+=1
changes={'material-slot-map.json':diff(oldslots,slots),'bindings-proposal.json':diff(oldbindings,bindings)}
assert all(len(x)==3 for x in changes.values());checks+=1
assert all(d['path'].endswith('/viewOverrides/caption') for ds in changes.values() for d in ds);checks+=6
for slot in slots:
 assert slot==bindings['bindingNotes'][slot['record_id']][slot['material_id']];checks+=1
 assert slot['binding_approved'] is False;checks+=1
 assert 'None%' not in slot['viewOverrides']['caption'];checks+=1
for fn,x in [('material-slot-map.json',slots),('bindings-proposal.json',bindings)]:save(V/fn,x)
history={'finding_id':'EVANS-MOL-PBO-PURITY','reported_by':'/root/peng1998_reader_assets','author':'/root/norberg2004_extract','status':'corrected_pending_independent_delta_check','prior_freeze':{'path':str(prior),'sha256':sha(prior)},'scientific_basis':'Canonical PbO purity is a reported lower bound: minimum=99.9%, numeric value=null, raw_text=99.9+% as printed. The old human caption interpolated null as None%.','correction':'Display ≥99.9% (99.9+% as printed) in three material-slot captions and their mirrored binding notes.','changed_record_ids':sorted(expected),'deltas':changes,'changed_string_leaves':6,'canonical_data_changed':False,'chemical_assignments_changed':False,'registry_assets_graphs_coordinates_changed':False,'prior_package_unchanged':True}
save(V/'correction-history.json',history)
for f in freeze['bound_files']:assert sha(f['path'])==f['sha256'];checks+=1
assert sha(prior)==history['prior_freeze']['sha256'];checks+=1
save(V/'author-validation.json',{'status':'passed_bounded_caption_revision_checks','checks':checks,'changed_caption_leaves':6,'material_slots':123,'all_original_freeze_files_unchanged':True,'canonical_numeric_values_unchanged':True,'all_binding_flags_false':True,'independent_audit':'pending','browser_publication':'pending'})
notes='''# Molecular proposal revision 2 — PbO purity caption

The original package and every bound file remain unchanged. The three PbO slot captions and their three mirrored binding-note captions now show **≥99.9% (99.9+% as printed)**. The source value is a lower bound, not an exact purity. No canonical field, source quantity, chemical assignment, stock component, SVG, model or coordinate changed.

Use this directory's `bindings-proposal.json` and `material-slot-map.json` as the effective replacements; all other assets and maps resolve to the original molecular package. `correction-history.json` enumerates exactly six changed string leaves. Independent delta review remains required; approval flags stay false.
'''
(V/'README.md').write_text(notes,encoding='utf-8')
bound=freeze['bound_files']+[{'path':str(prior),'sha256':sha(prior),'role':'preserved_prior_freeze'}]
bound += [{'path':str(p),'sha256':sha(p),'role':'caption_revision_output'} for p in sorted(V.iterdir()) if p.is_file() and p.name!='package-freeze.json']
save(V/'package-freeze.json',{'schema':'mattersyn-private-molecular-proposal/1','source_id':'evans2010','version':2,'author':'/root/norberg2004_extract','created_at':datetime.now(timezone.utc).isoformat(),'status':'bounded_caption_revision_frozen_for_independent_delta_review','prior_freeze_sha256':sha(prior),'counts':freeze['counts'],'effective_files':{'registry':str(O/'registry-additions.json'),'bindings':str(V/'bindings-proposal.json'),'material_slot_map':str(V/'material-slot-map.json'),'stock_component_map':str(O/'stock-component-map.json'),'public_asset_proposal':str(O/'public-asset-proposal.json')},'registry_sha256':sha(O/'registry-additions.json'),'bindings_sha256':sha(V/'bindings-proposal.json'),'material_slot_map_sha256':sha(V/'material-slot-map.json'),'correction_history_sha256':sha(V/'correction-history.json'),'bound_files':bound,'independent_audit':'pending','binding_approved':False,'published':False,'training_eligible':False})
print(json.dumps({'freeze':sha(V/'package-freeze.json'),'bindings':sha(V/'bindings-proposal.json'),'material_map':sha(V/'material-slot-map.json'),'history':sha(V/'correction-history.json'),'checks':checks,'bound_files':len(bound)}))
