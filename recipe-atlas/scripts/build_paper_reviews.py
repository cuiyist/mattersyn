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
    items=c['figures']+[f for category in ['tables','equations','schemes','source_notes'] for f in c.get(category,[]) if f.get('public_asset')]
    # Source-private page inventories may retain only a source hash/label.
    # Validate every delivered asset; a pathless provenance object is not an
    # image delivery and must not be converted into an invented public path.
    items += [{'id':item['id'], 'public_asset':a['public_asset'], 'public_asset_sha256':a.get('public_asset_sha256', a.get('display_asset_sha256', a.get('sha256')))} for s in c.get('reader_sections',[]) for item in s.get('items',[]) for a in item.get('original_assets',[]) if a.get('public_asset')]
    for f in items:
        a=f.get('public_asset')
        if not a:errors.append('Missing figure asset: '+str(f.get('id')));continue
        p=(ROOT/'dist'/a).resolve()
        if not p.is_relative_to((ROOT/'dist').resolve()):errors.append('Asset path leaves publication directory: '+a);continue
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=f['public_asset_sha256']:errors.append('Figure hash mismatch: '+a)
    for item in c['recipe_inventory']:
        for rid in item.get('record_ids',[]):
            if not (ROOT/'data/records'/(rid+'.json')).is_file():errors.append('Unresolved recipe link: '+rid)
    return errors

def main():
    index=[]
    for p in sorted(DATA.glob('*.json')):
        c=display_view(read(p),ROOT,p.stem+'-private-asset-provenance.json');errors=validate(c)
        if errors:raise ValueError(p.name+': '+repr(errors))
        scope=source_review_scope(c)
        c['review_scope_label']=scope['label']
        write(ROOT/'dist/data/paper-reviews'/p.name,c)
        index.append({'id':c['paper_id'],'doi':c['doi'],'title':c['title'],'review_scope':scope['scope'],'review_scope_label':scope['label'],'si_status':scope['si_status'],'pages_read':sum(d['page_count'] for d in c['documents']),'figures':len(c['figures']),'tables':len(c.get('tables',[])),'record_ids':sorted({rid for x in c['recipe_inventory'] for rid in x.get('record_ids',[])}),'independent_audit':c.get('independent_audit','pending'),'url':'paper-review.html?id='+c['paper_id']})
    write(ROOT/'dist/data/paper-review-index.json',{'schema_version':'1.0','papers':index,'scope':'Full supplied-document reading and visual coverage; omitted experimental details and raw-data gaps remain explicit. This status is not an exact-structure training eligibility label.'})
    print('Validated and published coverage ledgers:',len(index))
if __name__=='__main__':main()
