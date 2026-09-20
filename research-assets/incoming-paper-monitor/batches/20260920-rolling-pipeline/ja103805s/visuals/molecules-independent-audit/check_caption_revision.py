"""Independent exact delta check of the three mirrored PbO purity captions."""
from pathlib import Path
import json, hashlib, collections
O=Path(__file__).parent;E=O.parents[1];B=E/'visuals/molecules';R=B/'revision-2'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
bound={};checks=collections.Counter();fail=[]
def read(p):
    bound[str(p)]=sha(p);return json.loads(p.read_text(encoding='utf-8-sig'))
def ck(ok,category,detail):
    checks[category]+=1
    if not ok:fail.append({'category':category,'detail':detail})
f1=read(B/'package-freeze.json');f2=read(R/'package-freeze.json')
for f in [f1,f2]:
    for row in f['bound_files']:
        p=Path(row['path']);ck(p.is_file() and sha(p)==row['sha256'],'freeze_hash',str(p))
        if p.is_file():bound[str(p)]=sha(p)
ck(f2['prior_freeze_sha256']==sha(B/'package-freeze.json'),'prior_boundary','original freeze retained')
oldslots=read(B/'material-slot-map.json');newslots=read(R/'material-slot-map.json')
oldbind=read(B/'bindings-proposal.json');newbind=read(R/'bindings-proposal.json')
def diff(a,b,path=''):
    ck(type(a) is type(b),'delta_type',path)
    if isinstance(a,dict) and isinstance(b,dict):
        ck(a.keys()==b.keys(),'delta_keys',path)
        return sum((diff(a[k],b[k],path+'/'+k) for k in a if k in b),[])
    if isinstance(a,list) and isinstance(b,list):
        ck(len(a)==len(b),'delta_length',path)
        return sum((diff(x,y,path+'/'+str(i)) for i,(x,y) in enumerate(zip(a,b))),[])
    ck(a==b or isinstance(a,str),'delta_only_strings',path)
    return [] if a==b else [{'path':path,'before':a,'after':b}]
deltas={'material-slot-map.json':diff(oldslots,newslots),'bindings-proposal.json':diff(oldbind,newbind)}
targets={'evans-2010-pb-oleate','evans-2010-pbse-msc-family','evans-2010-reagents'}
expected_slots={f'/{i}/viewOverrides/caption' for i,s in enumerate(oldslots) if s['record_id'] in targets and s['material_id']=='pbo'}
expected_bindings={f'/bindingNotes/{rid}/pbo/viewOverrides/caption' for rid in targets}
for name,expected in [('material-slot-map.json',expected_slots),('bindings-proposal.json',expected_bindings)]:
    ck({x['path'] for x in deltas[name]}==expected and len(expected)==3,'exact_six_caption_delta',name)
    for row in deltas[name]:
        ck(row['after']==row['before'].replace('None%','≥99.9% (99.9+% as printed)'),'replacement_exact',row['path'])
for s in newslots:
    caption=s['viewOverrides']['caption'];rid=s['record_id'];mid=s['material_id']
    ck(not any(x in caption for x in ['None%','null%','NaN%']),'no_null_numeric_caption',rid+' '+mid)
    ck(newbind['bindingNotes'][rid][mid]['viewOverrides']==s['viewOverrides'],'slot_mirror_exact',rid+' '+mid)
    if mid=='pbo':
        q=s['canonical_identity']['quantities']['purity']
        ck(q['value'] is None and q['minimum']==99.9 and q['unit']=='%' and not q['minimum_exclusive'],'source_bound_semantics',rid)
        ck('≥99.9% (99.9+% as printed)' in caption,'visible_bound_semantics',rid)
history=read(R/'correction-history.json')
ck(history['deltas']==deltas,'history_exact','author delta independently reproduced')
oldproof=read(O/'initial-review/mechanical-audit.json')
ck(oldproof['status']=='passed' and oldproof['failures']==[],'prior_scope','unchanged graph/coordinate/slot audit passes')
for p,h in oldproof['bound_files'].items():
    ck(sha(Path(p))==h,'prior_audited_input_unchanged',p);bound[p]=h
report={'schema':'mattersyn-independent-molecular-caption-delta/1','reviewer':'/root/peng1998_reader_assets',
    'status':'passed' if not fail else 'findings','checks':sum(checks.values()),'categories':dict(checks),'failures':fail,
    'deltas':deltas,'finding_resolved':'EVANS-MOLECULE-01','effective_files':f2['effective_files'],'bound_files':bound,
    'scope':'Exact six caption leaves only. Prior full molecular/source/visual audit remains bound to unchanged inputs; no canonical or chemical quantity changed.'}
p=O/'caption-revision-audit.json';p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
src=(O/'check_viewer.mjs').read_text()
src=src.replace("new URL(name,input)","new URL(['bindings-proposal.json','material-slot-map.json'].includes(name)?'revision-2/'+name:name,input)")
src=src.replace("new URL('viewer-function-audit.json',out)","new URL('viewer-revision2-function-audit.json',out)")
(O/'check_viewer_revision2.mjs').write_text(src,encoding='utf-8')
print(json.dumps({'status':report['status'],'checks':report['checks'],'categories':report['categories'],'failures':fail,'report_sha256':sha(p)},ensure_ascii=False,indent=2))
