"""Preserved four-finding source correction overlay; original author freeze is immutable."""
from pathlib import Path
from datetime import datetime,timezone
import copy,json,hashlib
P=Path(__file__).resolve().parent;O=P/'source-extraction-revision-2';O.mkdir(exist_ok=True)
assert not(O/'package-freeze.json').exists()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(name,x):(O/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
base=read(P/'package-freeze.json');assert sha(P/'package-freeze.json')=='7599e47c1ef1d43d56b2f4f835e4b550a1ef652aecca2e9dd8e593abc5769c04'
for rel,item in base['bound_files'].items():assert sha(P/rel)==item['sha256'],rel
files=['source-facts.json','source-inventory.json','original-assets-manifest.json','page-coverage.json']
before={n:read(P/n)for n in files};after=copy.deepcopy(before)
sf=before['source-facts.json'];facts={f['id']:f for f in sf['facts']}
added=[]
for fid,locator in [('friedfeld2019-scheme2-model','Scheme2 footnotea: critical interval130–150°C; PDFp4/printed806'),('friedfeld2019-growth-time','PartII growth duration, optical plateau and550–650nm transition claims; PDFp4/printed806')]:
    old=facts[fid]['evidence'][0];new=copy.deepcopy(old);new.update(pdf_page=4,printed_page=806,locator=locator);added.append((old,new))
def change(obj):
    if isinstance(obj,dict):
        for key,value in list(obj.items()):
            if key=='meaning' and value=='diameter standard deviation':obj[key]='reported ± diameter uncertainty; statistical definition unspecified'
            else:change(value)
    elif isinstance(obj,list):
        for old,new in added:
            if any(x==old for x in obj) and new not in obj:obj.append(copy.deepcopy(new))
        for x in obj:change(x)
for obj in after.values():change(obj)
figure=next(f for f in after['source-facts.json']['figures']if f['id']=='figure-s1')
assert figure['sample_context_ids']==['phenylacetate-reference'];figure['sample_context_ids'].append('nmr-labeled')
asset=next(a for a in after['original-assets-manifest.json']['assets']if a['object_id']=='figure-s1')
assert asset['sample_context_ids']==['phenylacetate-reference'];asset['sample_context_ids'].append('nmr-labeled')
for key in ['units','semantic_units']:
    for unit in after['source-inventory.json'][key]:unit['source_payload_ids']=[f'friedfeld2019-{e["document_role"]}-p{e["pdf_page"]:02d}'for e in unit['evidence']]
for page in after['page-coverage.json']['pages']:
    page['source_unit_ids']=[u['id']for u in after['source-inventory.json']['units']if any(e['document_role']==page['document_role']and e['pdf_page']==page['pdf_page']for e in u['evidence'])]
def diff(a,b,path=''):
    if type(a)!=type(b):return[{'path':path,'before':a,'after':b}]
    if isinstance(a,dict):
        out=[]
        for k in sorted(set(a)|set(b)):
            if k not in a or k not in b:out.append({'path':path+'/'+k,'before':a.get(k),'after':b.get(k)})
            else:out.extend(diff(a[k],b[k],path+'/'+k))
        return out
    if isinstance(a,list):
        if len(a)!=len(b):return[{'path':path,'before':a,'after':b}]
        return[d for i,(x,y)in enumerate(zip(a,b))for d in diff(x,y,path+'/'+str(i))]
    return[]if a==b else[{'path':path,'before':a,'after':b}]
deltas={n:diff(before[n],after[n])for n in files}
for n,ds in deltas.items():
    for d in ds:assert any(x in d['path']for x in['/evidence','/meaning','/sample_context_ids','/source_payload_ids','/source_unit_ids']),d
def quantity_core(obj):
    if isinstance(obj,dict):
        if all(k in obj for k in ['raw_text','value','unit','uncertainty','range']):yield{k:obj[k]for k in ['raw_text','value','unit','uncertainty','range','ordered_endpoints','comparison','approximate','status']}
        for v in obj.values():yield from quantity_core(v)
    elif isinstance(obj,list):
        for v in obj:yield from quantity_core(v)
assert list(quantity_core(before['source-facts.json']))==list(quantity_core(after['source-facts.json']))
assert before['source-inventory.json']['counts']==after['source-inventory.json']['counts']
assert [a['sha256']for a in before['original-assets-manifest.json']['assets']]==[a['sha256']for a in after['original-assets-manifest.json']['assets']]
for n,x in after.items():save(n,x)
history={'schema':'mattersyn-source-correction-history/1','source_id':'friedfeld2019','revision':2,'author':'/root/peng1998_reader_assets','reason':'Four bounded findings from distinct Backlog source audit','base_freeze':{'path':str(P/'package-freeze.json'),'sha256':sha(P/'package-freeze.json')},'findings':['Add Scheme2 PDF4/printed806 locator while retaining main6 mechanistic context.','Add growth-time PDF4/printed806 locator while retaining main3 preceding context.','Qualify0.5nm as source ± uncertainty with undefined statistic, not SD.','Add existing labeledMSC context to S1 source figure and crop mapping.'],'changes':deltas,'all_numeric_values_units_bounds_unchanged':True,'all_crop_bytes_unchanged':True,'original_145_files_unchanged':True,'independent_audit_status':'pending'}
save('source-correction-history.json',history)
effective={n:{'path':str(O/n),'sha256':sha(O/n)}for n in files}
save('effective-file-map.json',{'schema':'mattersyn-source-effective-files/1','base_freeze':str(P/'package-freeze.json'),'base_freeze_sha256':sha(P/'package-freeze.json'),'replacements':effective,'unchanged_base_files':'All other base freeze paths remain unchanged and effective; original source-facts are preserved at their old paths.'})
bound={str(p):sha(p)for p in[O/n for n in files]+[O/'source-correction-history.json',O/'effective-file-map.json',Path(__file__)]}
save('package-freeze.json',{'schema':'mattersyn-source-extraction-overlay/1','source_id':'friedfeld2019','revision':2,'created_at':datetime.now(timezone.utc).isoformat(),'status':'immutable_author_correction_pending_independent_audit','base_freeze_sha256':sha(P/'package-freeze.json'),'base_freeze_path':str(P/'package-freeze.json'),'bound_files':bound,'effective_files':effective,'unchanged_values_and_assets':True,'independent_audit_status':'pending','counts':base['counts']})
print(json.dumps({'freeze':sha(O/'package-freeze.json'),'facts':sha(O/'source-facts.json'),'history':sha(O/'source-correction-history.json'),'delta_counts':{n:len(v)for n,v in deltas.items()}},indent=2))
