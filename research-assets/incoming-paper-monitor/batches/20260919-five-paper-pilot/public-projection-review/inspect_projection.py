"""Independent local-only comparison; writes one private evidence snapshot."""
from pathlib import Path
import hashlib,json,os,subprocess
O=Path(__file__).resolve().parent;M=O.parents[4];D=M/'recipe-atlas/dist';C=M.parent/'mattersyn-github-public-clean/mattersyn-site';OLD=M.parent/'mattersyn-github-public/mattersyn-site'
GIT='C:/Program Files/Git/cmd/git.exe'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def files(root):
    result={}
    for directory,dirs,names in os.walk(root):
        dirs[:]=[x for x in dirs if x!='.git']
        for name in names:
            p=Path(directory)/name;result[p.relative_to(root).as_posix()]=p
    return result
def git(*args):return subprocess.run([GIT,'-c','safe.directory='+OLD.as_posix(),'-C',str(OLD),*args],capture_output=True,check=True).stdout
src=files(D);clean=files(C);oldworking=files(OLD);hashes={};changes=[]
for label,rows in [('site',src),('clean',clean),('old_working',oldworking)]:
    for rel,p in rows.items():hashes[label+'/'+rel]=sha(p.read_bytes())
missing=sorted(set(src)-set(clean));added=sorted(set(clean)-set(src));different=[p for p in sorted(set(src)&set(clean)) if hashes['site/'+p]!=hashes['clean/'+p]]
def diffs(a,b,p=''):
    out=[]
    if type(a)!=type(b):return [{'pointer':p,'kind':'type','before':a,'after':b}]
    if isinstance(a,dict):
        for k in sorted(set(a)|set(b)):
            ptr=p+'/'+k.replace('~','~0').replace('/','~1')
            if k not in b:out.append({'pointer':ptr,'kind':'removed','before':a[k]})
            elif k not in a:out.append({'pointer':ptr,'kind':'added','after':b[k]})
            else:out+=diffs(a[k],b[k],ptr)
    elif isinstance(a,list):
        if len(a)!=len(b):return [{'pointer':p,'kind':'array_length','before':len(a),'after':len(b)}]
        for i,(x,y) in enumerate(zip(a,b)):out+=diffs(x,y,p+'/'+str(i))
    elif a!=b:out.append({'pointer':p,'kind':'value','before':a,'after':b})
    return out
for rel in different:
    a=src[rel].read_bytes();b=clean[rel].read_bytes()
    row={'path':rel,'source_sha256':sha(a),'clean_sha256':sha(b)}
    if rel.endswith('.json'):row['json_differences']=diffs(json.loads(a),json.loads(b))
    else:row['old_site_host_replacement_only']=a.replace(b'https://mattersyn-recipe-atlas.cuiy781513.chatgpt.site',b'https://cuiyist.github.io/mattersyn-site')==b
    changes.append(row)
head=git('rev-parse','HEAD').decode().strip();tree={}
for line in git('ls-tree','-rz','--full-tree','HEAD').split(b'\0'):
    if not line:continue
    headpart,path=line.split(b'\t',1);mode,kind,oid=headpart.split()
    if kind==b'blob':tree[path.decode()]=oid.decode()
baseline_changed=[];baseline_same=[]
for rel,p in clean.items():
    raw=p.read_bytes();blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    if rel in tree and tree[rel]==blob:baseline_same.append(rel)
    elif rel in tree:baseline_changed.append(rel)
baseline_new=sorted(set(clean)-set(tree));baseline_omitted=sorted(set(tree)-set(clean))
recordpaths=sorted(p for p in clean if p.startswith('data/records/') and p.endswith('.json'))
readers=sorted(p for p in clean if p.startswith('data/paper-reviews/') and p.endswith('.json'))
crops=sorted(p for p in src if p.startswith('assets/figures/norberg2004/') and '/pages/' not in p)
out={'source':str(D),'clean':str(C),'old_working':str(OLD),'old_baseline_commit':head,'source_file_count':len(src),'clean_file_count':len(clean),'old_working_status':git('status','--porcelain').decode(),'missing_from_clean':missing,'added_to_clean':added,'differences':changes,'baseline_comparison':{'same_count':len(baseline_same),'changed':sorted(baseline_changed),'new':baseline_new,'omitted':baseline_omitted},'record_count':len(recordpaths),'records_byte_identical_source_and_baseline':all(p in baseline_same and hashes['clean/'+p]==hashes['site/'+p] for p in recordpaths),'readers_count':len(readers),'reader_changes':[x for x in changes if x['path'] in readers],'norberg_selected_crops':crops,'all_selected_crops_retained_byte_identical':all(p in clean and hashes['clean/'+p]==hashes['site/'+p] for p in crops),'full_file_sha256':hashes}
(O/'projection-comparison.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k not in ['full_file_sha256','differences','reader_changes','norberg_selected_crops']}|{'differences_summary':[{'path':x['path'],'json_difference_count':len(x.get('json_differences',[])),'host_only':x.get('old_site_host_replacement_only')} for x in changes],'selected_crops':len(crops),'report_sha256':sha((O/'projection-comparison.json').read_bytes())},ensure_ascii=False))
