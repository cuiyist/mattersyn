"""Independent exact pointer/hash and semantic checks for Heo bindings revision 2."""
from pathlib import Path
import json, hashlib, copy, re, datetime
HERE=Path(__file__).resolve().parent
H=HERE.parent.parent
P=H/'canonical-binding-proposal/revision-2'
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ptr(obj,s):
    for key in s.strip('/').split('/') if s else []:
        key=key.replace('~1','/').replace('~0','~')
        obj=obj[int(key)] if isinstance(obj,list) else obj[key]
    return obj
checks=[];bound={};pointer_count=0
def ck(s,v,d=None):checks.append({'check':s,'pass':bool(v),'detail':d})
def bind(p):
    p=Path(p);bound[str(p)]=sha(p);return bound[str(p)]
F=read(P/'package-manifest.json');bind(P/'package-manifest.json')
for rel,expected in F['files'].items():ck('manifest:'+rel,bind(P/rel)==expected)
for rid,expected in F['record_hashes'].items():ck('record:'+rid,bind(H/f'canonical-proposal/v1/canonical-drafts/{rid}.json')==expected)
ck('canonical manifest exact',bind(H/'canonical-proposal/v1/proposal-package-manifest.json')==F['canonical_v1_manifest_sha256'])
ck('original molecule freeze exact',bind(H/'visuals/molecules/package-freeze.json')==F['molecule_freeze_sha256'])
ck('revision builder exact',bind(H/F['builder']['file'])==F['builder']['sha256'])
def visit(x,label=''):
    global pointer_count
    if isinstance(x,dict):
        if {'file','sha256','json_pointer'}<=x.keys():
            path=H/x['file'];actual=read(path);pointer_count+=1
            ck(label+' pointer file hash',bind(path)==x['sha256'])
            target=ptr(actual,x['json_pointer'])
            if 'payload' in x:ck(label+' exact payload',target==x['payload'])
            elif 'value' in x:ck(label+' exact value',target==x['value'])
        for k,v in x.items():visit(v,label+'/'+k)
    elif isinstance(x,list):
        for i,v in enumerate(x):visit(v,label+'/'+str(i))
M=read(P/'material-slot-map.json');S=read(P/'stock-component-map.json');D=read(P/'unbound-context-dispositions.json');R=read(P/'bindings-proposal.json')
for name,x in [('materials',M),('stocks',S)]:visit(x,name)
slots=M['bindings'];ck('14 material slots',len(slots)==14)
ck('14 distinct canonical slots',len({(x['record_id'],x['canonical']['json_pointer']) for x in slots})==14)
ck('nine distinct used references',len({x['registry_id'] for x in slots})==9)
records={rid:read(H/f'canonical-proposal/v1/canonical-drafts/{rid}.json') for rid in F['record_hashes']}
want={(rid,'/materials/'+str(i)) for rid,r in records.items() for i,m in enumerate(r['materials'])}
ck('every material in all 10 records bound exactly once',want=={(x['record_id'],x['canonical']['json_pointer']) for x in slots})
def formula(f):return {e:int(n or 1) for e,n in re.findall(r'([A-Z][a-z]?)(\d*)',f)} if f else None
for x in slots:
    label=x['binding_id'];entry=ptr(read(H/x['reference']['file']),x['reference']['json_pointer'])
    ck(label+' registry ID',entry['id']==x['registry_id'])
    ck(label+' material ID',x['canonical']['payload']['id']==x['material_id'])
    ck(label+' formula equivalence',formula(entry['formula'])==formula(x['canonical']['payload']['formula']))
    ck(label+' record binding',R['recordBindings'][x['record_id']][x['material_id']]==x['registry_id'])
    note=R['bindingNotes'][x['record_id']][x['material_id']]
    ck(label+' same display scope',note['viewOverrides']==x['viewOverrides'])
    ck(label+' note pointer/hash',note['canonical_json_pointer']==x['canonical']['json_pointer'] and note['canonical_sha256']==x['canonical']['sha256'])
    ck(label+' pending gates',x['binding_approved'] is False and x['published'] is False and x['eligible_training'] is False and x['exact_structure_or_dft_eligibility'] is False)
    for a in x['reference_assets']:ck(label+' asset '+a['kind'],bind(H/a['file'])==a['sha256']==entry['assetHashes'][a['kind']])
    if x['registry_id']=='identity-heo2003-in66-x':
        ck(label+' effective corrected registry','revision-2/registry-additions-effective.json' in x['reference']['file'])
stock=S['stocks'][0]
ck('one stock two components',len(S['stocks'])==1 and len(stock['components'])==2)
ck('two source stock quantities',len(stock['canonical_concentrations'])==2)
ck('no solution model or stock preparation',stock['solution_model'] is None and stock['preparation_operation_ids']==[])
byid={x['binding_id']:x for x in slots}
for c in stock['components']:
    x=byid[c['material_binding_id']]
    ck('stock identity:'+c['component_id'],c['registry_id']==x['registry_id'] and c['material_json_pointer']==x['canonical']['json_pointer'] and c['component_id']==c['canonical_component']['payload']['material_id'])
    ck('stock display scope:'+c['component_id'],c['viewOverrides']==x['viewOverrides'])
ck('stock concentration and pH exact',[q['payload']['value'] for q in stock['canonical_concentrations']]==[0.1,6.4])
ck('two context-only references explicitly deferred',len(D['contexts'])==2 and all(x['binding_created'] is False for x in D['contexts']))
for ctx in D['contexts']:
    ck(ctx['registry_id']+' absent from bindings',ctx['registry_id'] not in {x['registry_id'] for x in slots})
    for link in ctx.get('canonical_contexts',[]):ck(ctx['registry_id']+' existing state',ptr(records[link['record_id']],link['json_pointer'])['id']==link['state_id'])
ck('no canonical patch',read(P/'canonical-patch-proposal.json')['patches']==[])
orig=read(H/'visuals/molecules/registry-additions.json');effective=read(P/'registry-additions-effective.json')
initial=copy.deepcopy(orig);initial['entries'][4]['provenance']['sourceLocators'][1]='Main PDF p. 5, printed p. 1124, Table 2 and footnote c'
ck('one exact locator leaf correction only',initial==effective)
ck('preserved initial freeze',sha(H/'visuals/molecules/package-freeze.json')==sha(H/'visuals/molecules-independent-audit/initial-inputs/package-freeze.json'))
ck('preserved initial registry',sha(H/'visuals/molecules/registry-additions.json')==sha(H/'visuals/molecules-independent-audit/initial-inputs/registry-additions.json'))
delta=read(P/'registry-metadata-delta.json');visit(delta,'locator-delta')
for n in [2,3,4,5]:bind(H/f'main-{n:02}.png')
result={'schema':'mattersyn-independent-Heo-binding-checks/1','reviewer':'/root/norberg2004_extract','author':'/root/peng1998_reader_assets','checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks_count':len(checks),'pointer_objects':pointer_count,'failures':[x for x in checks if not x['pass']],'checks':checks,'bound_files':bound}
(HERE/'binding-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
print(json.dumps({'check_count':len(checks),'pointer_objects':pointer_count,'bound_files':len(bound),'failures':result['failures']},ensure_ascii=False,indent=2))
