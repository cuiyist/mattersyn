"""Scoped GitHub release inspection and Pages configuration; no secrets logged."""
import argparse, json, os, subprocess, urllib.request, urllib.error

IDS={'mattersyn':1377877572,'mattersyn-site':1377878442}
def credential():
    p=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\nusername=cuiyist\n\n',text=True,capture_output=True,env=dict(os.environ,GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='never'))
    fields=dict(x.split('=',1) for x in p.stdout.splitlines() if '=' in x) if p.returncode==0 else {}
    if not fields.get('password'):raise RuntimeError('Existing GitHub credential unavailable')
    return fields['password']
def request(token,path,method='GET',data=None):
    req=urllib.request.Request('https://api.github.com'+path,method=method,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','Content-Type':'application/json','X-GitHub-Api-Version':'2026-03-10','User-Agent':'MatterSyn-release-repair'},data=json.dumps(data).encode() if data is not None else None)
    try:
        with urllib.request.urlopen(req,timeout=45) as r:return json.loads(r.read() or b'{}')
    except urllib.error.HTTPError as e:raise RuntimeError('GitHub request failed with HTTP '+str(e.code)) from None
def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['inspect','pages-workflow','runs']);p.add_argument('--expected-site-head');a=p.parse_args();token=credential()
    u=request(token,'/user')
    if u.get('login')!='cuiyist' or u.get('id')!=147659097:raise RuntimeError('Unexpected account')
    rows=[]
    for name,rid in IDS.items():
        r=request(token,'/repos/cuiyist/'+name)
        if r.get('id')!=rid or r.get('private'):raise RuntimeError('Repository identity or public visibility changed')
        b=request(token,'/repos/cuiyist/'+name+'/branches/main')
        refs=request(token,'/repos/cuiyist/'+name+'/git/matching-refs/heads/')+request(token,'/repos/cuiyist/'+name+'/git/matching-refs/tags/')
        rows.append({'name':name,'id':rid,'head':b['commit']['sha'],'protected':b['protected'],'forks':r.get('forks_count'),'private':False,'refs':[{'ref':x['ref'],'sha':x['object']['sha']}for x in refs]})
    if a.action=='pages-workflow':
        if not a.expected_site_head or rows[1]['head']!=a.expected_site_head:raise RuntimeError('Expected site head required and must match')
        request(token,'/repos/cuiyist/mattersyn-site/pages','PUT',{'build_type':'workflow'})
    pages=request(token,'/repos/cuiyist/mattersyn-site/pages')
    result={'repositories':rows,'pages':{k:pages.get(k) for k in ['html_url','build_type','status','source']}}
    if a.action=='runs':
        runs=request(token,'/repos/cuiyist/mattersyn-site/actions/runs?per_page=3')
        result['runs']=[{k:r.get(k) for k in ['id','name','head_sha','status','conclusion','html_url','created_at','updated_at']} for r in runs.get('workflow_runs',[])]
    print(json.dumps(result,indent=2))
if __name__=='__main__':
    try:main()
    except RuntimeError as e:raise SystemExit(str(e))
