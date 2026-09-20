"""Apply only the three independent-review corrections; retain frozen v1.
This author script writes only canonical-proposal/v2 and public-review-proposal/v2.
"""
from pathlib import Path
from copy import deepcopy
from datetime import datetime, timezone
import json, hashlib, shutil, sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parent
C1=R/'canonical-proposal/v1'; V1=R/'public-review-proposal/v1'
C=R/'canonical-proposal/v2'; V=R/'public-review-proposal/v2'
S=R.parents[4]/'recipe-atlas'
sys.path.insert(0,str(S/'scripts'))
from dataset_lib import validate_record, eligibility

def read(p): return json.loads(Path(p).read_bytes())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x): Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def ptr(x,p):
    if not p or p=='/':return x
    for k in p.strip('/').split('/'):
        k=k.replace('~1','/').replace('~0','~'); x=x[int(k)] if isinstance(x,list) else x[k]
    return x
def delta(a,b,p=''):
    if type(a)!=type(b): return [{'pointer':p,'before':a,'after':b}]
    if isinstance(a,dict):
        out=[]
        for k in sorted(set(a)|set(b)):
            path=p+'/'+k.replace('~','~0').replace('/','~1')
            if k not in a or k not in b:out.append({'pointer':path,'before':a.get(k),'after':b.get(k)})
            else:out+=delta(a[k],b[k],path)
        return out
    if isinstance(a,list):
        if len(a)!=len(b):return [{'pointer':p,'before':a,'after':b}]
        return [d for i,(x,y) in enumerate(zip(a,b)) for d in delta(x,y,p+'/'+str(i))]
    return [] if a==b else [{'pointer':p,'before':a,'after':b}]

assert not (C/'package-manifest.json').exists(),'Never overwrite a frozen revision.'
oldfreeze=read(C1/'package-manifest.json')
assert sha(C1/'package-manifest.json')=='336d7db442acd6433aa08453cb1b530d58eb46c133588b8deb7c2c3cb3e52ffd'
oldhashes={p:sha(p) for p in oldfreeze['bound_files']}
assert all(h==oldfreeze['bound_files'][p] for p,h in oldhashes.items())
ap=R/'canonical-reader-independent-audit/independent-audit-v1.json'
assert sha(ap)=='7b50d573ae2a6bfd44eadbada1890ff1ddcab5806aa3721b626ef55d948ff5fd'
shutil.copytree(C1,C,ignore=shutil.ignore_patterns('package-manifest.json'),dirs_exist_ok=True)
shutil.copytree(V1,V,dirs_exist_ok=True)
now=datetime.now(timezone.utc).isoformat()
checks=[]
def ck(label,value):
    checks.append({'check':label,'passed':bool(value)})
    assert value,label
cm=read(C1/'record-manifest.json'); records={}; record_delta=[]; changed_quantity={}
SCF='sommer-2020-scf-route'
new_name='Aqueous SCF solvent'
new_note='SCF solvent-water context; grade is not separately reported. No in situ nitrate-stock preparation, salt charge or solution volume is inherited by this material slot.'
composition_note='The preparation label and intended ZnAl2O4 target do not establish the observed product composition. Sample-specific phase and result observations remain in their separate source contexts; no pure-target product composition is assigned here.'
modified_products=0
for row in cm['records']:
    old=read(row['path']); new=deepcopy(old); rid=old['record_id']
    if rid in ['sommer-2020-mw-route',SCF,'sommer-2020-acs-route']:
        for i,p in enumerate(new['products']):
            if p['composition']['value']=='ZnAl2O4':
                p['composition']['value']=None; p['composition']['status']='not_reported'; p['composition']['note']=composition_note
                changed_quantity[(rid,f'/products/{i}/composition')]=deepcopy(p['composition']); modified_products+=1
        new['revision']=2
    if rid==SCF:
        m=next(m for m in new['materials'] if m['id']=='insitu-water')
        m['name']=new_name; m['notes'][0]=new_note
    changes=delta(old,new)
    if changes:write(C/(rid+'.json'),new)
    else:ck(rid+' byte-identical record',sha(C/(rid+'.json'))==row['sha256'])
    records[rid]=new
    record_delta.append({'record_id':rid,'before_path':row['path'],'before_sha256':row['sha256'],'after_path':str(C/(rid+'.json')),'after_sha256':sha(C/(rid+'.json')),'changes':changes})
    for field in ['operations','stocks','material_states','condition_options','measurements','intended_target','lineage','quality','structure_assets','context_links']:
        ck(rid+' invariant '+field,old[field]==new[field])
    ck(rid+' source and specimen IDs unchanged',old['sources']==new['sources'] and [p['sample_id'] for p in old['products']]==[p['sample_id'] for p in new['products']])
    ck(rid+' schema/semantic',not validate_record(new))
    ck(rid+' no eligible training task',not any(x['eligible'] for x in eligibility(new).values()))
ck('Exactly17 product composition corrections',modified_products==17)

oldreader=read(V1/'sommer2020.json'); reader=deepcopy(oldreader)
updated_fields=0; material_label_count=0; flow_label_count=0
for section in reader['reader_sections']:
    for item in section['items']:
        for f in item.get('facts',[]):
            key=(f.get('canonical_record_id'),f.get('json_pointer'))
            if key in changed_quantity:
                q=changed_quantity[key]; f['value']='Not reported';f['status']=q['status'];f['qualifier']=q['note'];f['canonical_quantity']=deepcopy(q);updated_fields+=1
        for m in item.get('material_identities',[]):
            if m.get('canonical_record_id')==SCF and m.get('source_material_id')=='insitu-water':m['name']=new_name;material_label_count+=1
        oc=item.get('operation_context',{})
        if oc.get('record_id')==SCF and 'insitu-water' in oc.get('material_flow_labels',{}):
            oc['material_flow_labels']['insitu-water']=new_name
            item['notes']=[n.replace('Water-based nitrate-stock solvent',new_name) for n in item['notes']]
            flow_label_count+=1
        if item['id']=='source-material-insitu-water':
            item['text']+=' The separate SCF material slot is an aqueous solvent reference with unreported grade; no in situ stock charges or preparation volume are transferred.'
        if item['id']=='source-figure-figure-11':
            item['title']='Autoclave impurity phase fractions versus duration'
            for a in item.get('original_assets',[]):a['label']=a['label'].replace('Autoclave phase fractions and diffraction','Autoclave impurity phase fractions versus duration')
            item['notes'].append('The inherited source-title label in the typed context is historical extraction metadata. Figure 11 shows impurity phase fractions versus duration and has no diffraction panel.')
for f in reader['figures']:
    if f.get('id')=='figure-11' or 'Autoclave phase fractions and diffraction' in f.get('label',''):
        f['label']=f['label'].replace('Autoclave phase fractions and diffraction','Autoclave impurity phase fractions versus duration')
ck('17 mirrored composition fields updated',updated_fields==17)
ck('One scoped material and one operation label',material_label_count==1 and flow_label_count==1)
fig11=next(it for ss in reader['reader_sections'] for it in ss['items'] if it['id']=='source-figure-figure-11')
ck('Figure11 display corrected',fig11['title']=='Autoclave impurity phase fractions versus duration')
ck('Reader counts invariant',oldreader['counts']==reader['counts'])
field_count=0
for section in reader['reader_sections']:
    for item in section['items']:
        for f in item.get('facts',[]):
            if 'canonical_quantity' in f:
                ck(f['id']+' exact final field',ptr(records[f['canonical_record_id']],f['json_pointer'])==f['canonical_quantity']);field_count+=1
        for link in item.get('canonical_links',[]):ck(item['id']+' canonical pointer '+link['json_pointer'],ptr(records[link['record_id']],link['json_pointer']) is not None)
ck('1515 typed fields retained',field_count==1515)
write(V/'sommer2020.json',reader)
write(C/'canonical-correction-delta.json',{'author':'/root/backlog_eta','version':2,'basis_audit':{'path':str(ap),'sha256':sha(ap)},'scope':'17 route-product composition assignments, SCF material name/scope, record revision metadata only. Intended targets, source values, recipe operations, conditions, sample links, all quantities and coverage pointers unchanged.','records':record_delta})
write(V/'reader-correction-delta.json',{'author':'/root/backlog_eta','version':2,'before_sha256':sha(V1/'sommer2020.json'),'after_sha256':sha(V/'sommer2020.json'),'changes':delta(oldreader,reader),'scope':'Corresponding17 unknown-composition field displays, scoped SCF material/input labels, Figure11 curated display labels and clarifications; source payloads/quantities/evidence/assets remain unchanged.'})
for name in ['source-to-field-coverage.json','lossless-source-map.json','operation-quantity-scope.json']:
    ck(name+' unchanged source mappings',sha(C/name)==sha(C1/name))
for name in ['source-item-coverage.json']:
    ck(name+' unchanged reader source coverage',sha(V/name)==sha(V1/name))
for p,h in oldhashes.items():ck('Original freeze preserved '+p,sha(p)==h)

# Versioned provenance; old validation files are historical, new checks bind v2.
for folder in [C,V]:
    shutil.copy2(folder/'author-validation.json',folder/'author-validation-v1-history.json')
validation={'status':'passed_author_v2_delta_schema_transport_checks','author':'/root/backlog_eta','created_at':now,'check_count':len(checks),'checks':checks,'schema_errors':[],'counts':cm['counts'],'source_audit':'passed','canonical_reader_independent_audit':'pending_v2_recheck','unchanged_source_freeze_sha256':sha(R/'package-freeze.json'),'not_independent_approval':True}
write(C/'author-validation.json',validation);write(V/'author-validation.json',validation)
cm['version']=2;cm['created_at']=now;cm['author_script_sha256']=sha(__file__);cm['validation_sha256']=sha(C/'author-validation.json')
for row in cm['records']:row['path']=str(C/(row['record_id']+'.json'));row['sha256']=sha(row['path'])
cm['prior_manifest']={'path':str(C1/'record-manifest.json'),'sha256':sha(C1/'record-manifest.json')}
cm['correction_delta_sha256']=sha(C/'canonical-correction-delta.json')
cm['input_modules']={str(S/'scripts'/n):sha(S/'scripts'/n) for n in ['dataset_lib.py','record_helpers.py','schema_definition.py']}
write(C/'record-manifest.json',cm)
rb=read(V/'reader-bindings-proposal.json');rb['reader_sha256']=sha(V/'sommer2020.json');write(V/'reader-bindings-proposal.json',rb)
rm=read(V1/'reader-manifest.json');rm['version']=2;rm['created_at']=now;rm['author_script_sha256']=sha(__file__)
updated_inputs={}
for p,h in rm['input_hashes'].items():
    target=Path(p)
    if target.is_relative_to(C1):target=C/target.relative_to(C1)
    updated_inputs[str(target)]=sha(target)
rm['input_hashes']=updated_inputs
rm['outputs']={n:sha(V/n) for n in rm['outputs']};rm['outputs']['reader-correction-delta.json']=sha(V/'reader-correction-delta.json')
write(V/'reader-manifest.json',rm)
notes=(C1/'proposal-notes.md').read_text(encoding='utf8').replace('proposal v1','proposal v2')
notes+='\nRevision2 resolves the three independent review findings:17 preparation-label product compositions are unknown rather than the nominal target; the SCF water slot has its own method-specific name/notes; Figure11 display identifies impurity fractions versus duration. All intended targets, sample IDs, recipe links, numeric fields, operations, stocks, source maps and original crops are unchanged. The source extraction title payload for Figure11 is retained as historical metadata, explicitly distinguished in reader notes. Original v1 and the v1 audit remain immutable.\n'
(C/'proposal-notes.md').write_text(notes,encoding='utf8')
(V/'README.md').write_text('Private Sommer reader revision2. Narrow changes and exact paths are recorded in reader-correction-delta.json; canonical-correction-delta.json resides in canonical-proposal/v2. Original v1 remains immutable. Source v2 passed; final canonical/reader recheck is pending. SI remains unlocated/unverified. No Site import, training approval, visual approval or publication.\n',encoding='utf8')
paths=[p for folder in [C,V] for p in folder.rglob('*') if p.is_file()]
paths += [Path(__file__),C1/'package-manifest.json',ap]
paths += [Path(p) for p in oldfreeze['bound_files'] if not Path(p).is_relative_to(C1) and not Path(p).is_relative_to(V1)]
paths += list(map(Path,cm['input_modules']))
freeze=deepcopy(oldfreeze);freeze.update(version=2,frozen_at=now,canonical_record_manifest_sha256=sha(C/'record-manifest.json'),reader_manifest_sha256=sha(V/'reader-manifest.json'),reader_sha256=sha(V/'sommer2020.json'),scope_notes_path=str(C/'proposal-notes.md'),input_snapshots_path=str(C/'input-snapshots.json'))
freeze['author_checks']={'v1_canonical':oldfreeze['author_checks']['canonical'],'v1_reader':oldfreeze['author_checks']['reader'],'v2_delta_schema_transport':len(checks)}
freeze['prior_package']={'path':str(C1/'package-manifest.json'),'sha256':sha(C1/'package-manifest.json')}
freeze['revision_basis']={'path':str(ap),'sha256':sha(ap),'finding_count':3}
freeze['bound_files']={str(p.resolve()):sha(p) for p in sorted(set(paths),key=str)};freeze['bound_file_count']=len(freeze['bound_files'])
write(C/'package-manifest.json',freeze)
print(json.dumps({'package_manifest':str(C/'package-manifest.json'),'package_sha256':sha(C/'package-manifest.json'),'canonical_manifest_sha256':sha(C/'record-manifest.json'),'reader_sha256':sha(V/'sommer2020.json'),'checks':len(checks),'record_changes':sum(len(x['changes']) for x in record_delta),'reader_changes':len(delta(oldreader,reader)),'bound_files':len(freeze['bound_files'])},indent=2))
