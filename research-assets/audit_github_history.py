"""Check preserved Site history for raw documents, oversized blobs and literal credentials."""
from pathlib import Path
import subprocess,re,json,hashlib
GIT=r'C:\Program Files\Git\cmd\git.exe'
ROOT=Path('[local path redacted]')
SITE=ROOT/'recipe-atlas'
def run(args, data=None):
    p=subprocess.run([GIT,*args],cwd=SITE,input=data,capture_output=True)
    if p.returncode:raise SystemExit('Git history inspection failed.')
    return p.stdout
objects={}
for line in run(['rev-list','--objects','--all']).decode('utf8').splitlines():
    fields=line.split(' ',1)
    if len(fields)==2:objects[fields[0]]=fields[1]
meta=run(['cat-file','--batch-check=%(objecttype) %(objectname) %(objectsize)'],('\n'.join(objects)+'\n').encode()).decode().splitlines()
findings=[];selected=[];blobs=0
text_ext={'.py','.js','.mjs','.json','.jsonl','.html','.css','.md','.txt','.toml','.yaml','.yml','.xml','.csv','.tsv'}
for line in meta:
    kind,sha,size=line.split();size=int(size)
    if kind!='blob':continue
    blobs+=1;name=objects[sha]
    if size>=100*1024*1024:findings.append({'path':name,'object':sha,'reason':'oversized_blob'})
    if Path(name).suffix.lower() in {'.pdf','.docx','.zip','.pem','.key'} or Path(name).name=='.env':
        findings.append({'path':name,'object':sha,'reason':'raw_document_or_secret_file'})
    if Path(name).suffix.lower() in text_ext:selected.append(sha)
patterns=[re.compile(p) for p in [rb'gh[opusr]_[A-Za-z0-9]{30,}',rb'github_pat_[A-Za-z0-9_]{50,}',rb'(?<![A-Za-z])sk-[A-Za-z0-9_-]{35,}',rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----']]
for index in range(0,len(selected),150):
    group=selected[index:index+150];raw=run(['cat-file','--batch'],('\n'.join(group)+'\n').encode());pos=0
    for expected in group:
        end=raw.index(b'\n',pos);header=raw[pos:end].decode().split();sha,kind,size=header;size=int(size)
        assert sha==expected and kind=='blob'
        data=raw[end+1:end+1+size];pos=end+size+2
        if any(p.search(data) for p in patterns):findings.append({'path':objects[sha],'object':sha,'reason':'possible_literal_secret'})
report={'history_source_head':run(['rev-parse','HEAD']).decode().strip(),'blobs_checked_for_size_and_name':blobs,
    'text_blobs_scanned':len(selected),'findings':findings,'status':'passed' if not findings else 'needs_review'}
(ROOT/'research-assets/github-history-audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps(report,indent=2))
raise SystemExit(bool(findings))
