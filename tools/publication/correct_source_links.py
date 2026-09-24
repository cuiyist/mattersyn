"""Correct only public record links to images withheld from redistribution."""
from pathlib import Path
import argparse, hashlib, json
from urllib.parse import urlsplit
from source_link_artifacts import rows, url_for
from safe_paths import checked_path, preflight_tree

def main():
    p=argparse.ArgumentParser();p.add_argument('--atlas',required=True);p.add_argument('--registry',required=True);a=p.parse_args();atlas=preflight_tree(Path(a.atlas).absolute());registry=json.loads(Path(a.registry).read_text(encoding='utf-8'))
    held={entry['path']:url_for(asset)for asset,entry in rows(registry)};changes=[]
    for path in sorted((atlas/'data/records').glob('*.json')):
        checked_path(atlas,path)
        raw=path.read_bytes();d=json.loads(raw);edits=[]
        for i,link in enumerate(d.get('context_links',[])):
            old=link.get('url','');normalized=old
            while normalized.startswith('../'):normalized=normalized[3:]
            if normalized.startswith('./'):normalized=normalized[2:]
            if normalized not in held:continue
            target=held[normalized]
            parsed=urlsplit(target)
            if parsed.scheme!='https'or parsed.hostname not in {'doi.org','dx.doi.org'}or not parsed.path.startswith('/10.')or parsed.username or parsed.password:raise RuntimeError('Exact source DOI must be verified for canonical-link correction')
            link['url']=target;edits.append({'pointer':'/context_links/'+str(i)+'/url','original_source_asset_locator':old,'public_source_url':target})
        if edits:
            new=(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode('utf-8');check=json.loads(new)
            for edit in edits:check['context_links'][int(edit['pointer'].split('/')[2])]['url']=edit['original_source_asset_locator']
            if check!=json.loads(raw):raise RuntimeError('Unexpected scientific field change')
            path.write_bytes(new);changes.append({'record_id':d['record_id'],'original_record_sha256':hashlib.sha256(raw).hexdigest(),'public_record_sha256':hashlib.sha256(new).hexdigest(),'only_changes':edits})
    out=checked_path(atlas,atlas/'data/release-notes/source-link-corrections.json');out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({'schema':'mattersyn-publication-link-corrections/1','scientific_fields_changed':False,'scope':'Public links to source figures; original numerical data, source/sample claims and audit evidence unchanged.','changes':changes},indent=2)+'\n',encoding='utf-8');print(json.dumps({'records_corrected':len(changes),'scientific_fields_changed':False}))

if __name__=='__main__':main()
