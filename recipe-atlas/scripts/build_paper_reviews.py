"""Publish reviewed coverage ledgers without private source paths or full-text caches."""
import json, hashlib, re, shutil
from pathlib import Path
from review_scope import source_review_scope
from asset_display import display_view
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/paper-reviews'

def read(p): return json.loads(p.read_text(encoding='utf-8'))
def write(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
from pathlib import PurePosixPath, PureWindowsPath

def stage_reader_evidence(c):
    """Copy declared CSVs and a matching reader sidecar within one paper's dist folder."""
    paper_id=c.get('paper_id')
    if not isinstance(paper_id,str) or not re.fullmatch(r'[a-z0-9-]+',paper_id):
        raise ValueError('Invalid paper id for evidence sidecars')
    rels={x.get('source_data_path') for x in c.get('tables',[]) if x.get('source_data_path')}
    sidecar=PurePosixPath('data')/'paper-evidence'/paper_id/'reader-sidecar.json'
    sidecar_src=ROOT.joinpath(*sidecar.parts)
    if sidecar_src.is_file():rels.add(sidecar.as_posix())
    source_root_path=ROOT.resolve()/'data'/'paper-evidence'/paper_id
    source_root=source_root_path.resolve()
    dist_root_path=ROOT.resolve()/'dist'/'data'/'paper-evidence'/paper_id
    dist_root=dist_root_path.resolve()
    dist_base=(ROOT.resolve()/'dist').resolve()
    root_path=ROOT.resolve()
    if not dist_base.is_relative_to(root_path):
        raise ValueError('Generated dist root leaves the project root')
    if source_root!=source_root_path or not source_root.is_relative_to((ROOT.resolve()/'data'/'paper-evidence').resolve()):
        raise ValueError('Paper evidence source root leaves data/paper-evidence')
    if dist_root!=dist_root_path or not dist_root.is_relative_to(dist_base):
        raise ValueError('Paper evidence destination root leaves dist')
    for raw in sorted(rels):
        if not isinstance(raw,str) or not raw or '\\' in raw or '?' in raw or '#' in raw:
            raise ValueError('Unsafe paper-evidence path syntax: '+str(raw))
        posix=PurePosixPath(raw);win=PureWindowsPath(raw)
        if posix.is_absolute() or win.is_absolute() or win.drive or win.root:
            raise ValueError('Absolute paper-evidence path rejected: '+raw)
        raw_parts=raw.split('/')
        parts=posix.parts
        if any(part in ('','.','..') for part in raw_parts) or any(part in ('','.','..') for part in parts):
            raise ValueError('Traversal or empty paper-evidence path segment: '+raw)
        if len(parts)<4 or parts[:3]!=('data','paper-evidence',paper_id):
            raise ValueError('Sidecar must be under this paper id: '+raw)
        if not all(re.fullmatch(r'[A-Za-z0-9._-]+',part) for part in parts):
            raise ValueError('Unsupported paper-evidence path character: '+raw)
        src=ROOT.joinpath(*parts).resolve()
        if not src.is_relative_to(source_root) or not src.is_file():
            raise ValueError('Unsafe or missing paper-evidence source: '+raw)
        dst=dist_root.joinpath(*parts[3:])
        dst.parent.mkdir(parents=True,exist_ok=True)
        resolved_dst=dst.resolve()
        if not resolved_dst.is_relative_to(dist_root):
            raise ValueError('Paper-evidence destination leaves this paper folder: '+raw)
        shutil.copy2(src,resolved_dst)
        if hashlib.sha256(src.read_bytes()).hexdigest()!=hashlib.sha256(resolved_dst.read_bytes()).hexdigest():
            raise ValueError('Evidence sidecar copy hash mismatch: '+raw)

def declared_review_assets(c, errors):
    """Separate textual source notes from declared assets without skipping bad assets."""
    assets=[]
    for category in ('figures','tables','equations','schemes','source_notes'):
        entries=c.get(category,[])
        if not isinstance(entries,list):
            errors.append('Unsupported '+category+' inventory format')
            continue
        for index,entry in enumerate(entries):
            if category=='source_notes' and isinstance(entry,str):
                continue
            if not isinstance(entry,dict):
                errors.append('Unsupported '+category+' entry: '+str(index))
                continue
            if category=='figures' or entry.get('public_asset'):
                assets.append(entry)
    return assets

def validate(c):
    errors=[]
    chars=c.get('characterization_inventory',[])
    if isinstance(chars,dict):
        ids={x['id'] for s in c.get('reader_sections',[]) for x in s.get('items',[])}
        if not isinstance(chars.get('reader_item_ids'),list) or not set(chars['reader_item_ids'])<=ids:errors.append('Unresolved characterization reader links')
    elif not isinstance(chars,list):errors.append('Unsupported characterization inventory format')
    try:source_review_scope(c)
    except (ValueError,KeyError) as exc:errors.append(str(exc))
    for d in c['documents']:
        pages=d['pages'];nums=[p['page'] for p in pages]
        if sorted(nums)!=list(range(1,d['page_count']+1)):errors.append('Incomplete or duplicate page inventory')
        if not all(p.get('text_read') is True and p.get('visual_review') is True for p in pages):errors.append('Unread or visually unchecked page')
        if not re.fullmatch('[a-f0-9]{64}',d['sha256']):errors.append('Missing source hash')
    items=declared_review_assets(c,errors)
    # Source-private page inventories may retain only a source hash/label.
    # Validate every delivered asset; a pathless provenance object is not an
    # image delivery and must not be converted into an invented public path.
    items += [{'id':item['id'], 'public_asset':a['public_asset'], 'public_asset_sha256':a.get('public_asset_sha256', a.get('display_asset_sha256', a.get('sha256')))} for s in c.get('reader_sections',[]) for item in s.get('items',[]) for a in item.get('original_assets',[]) if a.get('public_asset')]
    for f in items:
        a=f.get('public_asset')
        if not a:errors.append('Missing figure asset: '+str(f.get('id')));continue
        p=(ROOT/'dist'/a).resolve()
        if not p.is_relative_to((ROOT/'dist').resolve()):errors.append('Asset path leaves publication directory: '+a);continue
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=f.get('public_asset_sha256'):errors.append('Figure hash mismatch: '+a)
    for item in c['recipe_inventory']:
        for rid in item.get('record_ids',[]):
            if not (ROOT/'data/records'/(rid+'.json')).is_file():errors.append('Unresolved recipe link: '+rid)
    return errors

def main():
    index=[]
    for p in sorted(DATA.glob('*.json')):
        c=display_view(read(p),ROOT,p.stem+'-private-asset-provenance.json');stage_reader_evidence(c);errors=validate(c)
        if errors:raise ValueError(p.name+': '+repr(errors))
        scope=source_review_scope(c)
        c['review_scope_label']=scope['label']
        write(ROOT/'dist/data/paper-reviews'/p.name,c)
        index.append({'id':c['paper_id'],'doi':c['doi'],'title':c['title'],'review_scope':scope['scope'],'review_scope_label':scope['label'],'si_status':scope['si_status'],'pages_read':sum(d['page_count'] for d in c['documents']),'figures':len(c['figures']),'tables':len(c.get('tables',[])),'record_ids':sorted({rid for x in c['recipe_inventory'] for rid in x.get('record_ids',[])}),'independent_audit':c.get('independent_audit','pending'),'url':'paper-review.html?id='+c['paper_id']})
    write(ROOT/'dist/data/paper-review-index.json',{'schema_version':'1.0','papers':index,'scope':'Full supplied-document reading and visual coverage; omitted experimental details and raw-data gaps remain explicit. This status is not an exact-structure training eligibility label.'})
    print('Validated and published coverage ledgers:',len(index))
if __name__=='__main__':main()
