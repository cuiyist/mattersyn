"""Bind a reviewed, already projected tree to exact public file identities.

This prepares a gate input; it does not perform scientific review, pass the gate,
or publish. Use only after the file set and its candidate checks are reviewed.
"""
from pathlib import Path
import argparse,datetime,hashlib,importlib.util,json,sys

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--guard',required=True);p.add_argument('--policy',required=True);p.add_argument('--registry',required=True);p.add_argument('--repo',required=True);p.add_argument('--source-commit',required=True);p.add_argument('--release-id',required=True);p.add_argument('--reviewer',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    root=Path(a.root).resolve();out=Path(a.out).resolve()
    if out==root or out.is_relative_to(root):raise RuntimeError('Write the allowlist outside the reviewed tree')
    spec=importlib.util.spec_from_file_location('public_guard',a.guard);g=importlib.util.module_from_spec(spec);sys.modules[spec.name]=g;spec.loader.exec_module(g);config=g.load_config(a.policy,a.registry)
    rows=[];at=datetime.datetime.now(datetime.timezone.utc).isoformat()
    for path in sorted(root.rglob('*')):
        if not path.is_file()or'.git'in path.relative_to(root).parts:continue
        rel=path.relative_to(root).as_posix();raw=path.read_bytes();decision=g.history_project(a.repo,rel,raw,config)
        if decision['action']!='allow'or decision['content']!=raw:raise RuntimeError('Tree requires review/projection before approval: '+rel)
        refs=[]
        if path.suffix=='.json':
            data=json.loads(raw)
            if isinstance(data,dict):
                for source in data.get('sources',[])if isinstance(data.get('sources'),list)else[]:
                    if not isinstance(source,dict):continue
                    if source.get('doi'):refs.append({'doi':source['doi'],'url':'https://doi.org/'+source['doi']})
        for exception in config.get('structure_path_exceptions',[]):
            if exception['repo']==a.repo and exception['path']==rel:refs+=exception['source_refs']
        refs=list({json.dumps(row,sort_keys=True):row for row in refs}.values())
        rows.append({'path':rel,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'content_class':decision['content_class'],
                     'decision':'allow','review_status':'approved','reviewer':a.reviewer,'reviewed_at':at,'source_refs':refs})
    data={'schema_version':'mattersyn-public-release-allowlist/1','release_id':a.release_id,'repo':a.repo,'source_commit':a.source_commit,
          'policy_sha256':hashlib.sha256(Path(a.policy).read_bytes()).hexdigest(),'asset_rights_registry_sha256':hashlib.sha256(Path(a.registry).read_bytes()).hexdigest(),
          'review_scope':'Exact identity and public-delivery approval of the reviewed candidate; individual scientific review and training eligibility remain in the records.','files':rows}
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'files':len(rows),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'gate_passed':False}))
if __name__=='__main__':main()
