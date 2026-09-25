"""Copy an independently reviewed presentation projection, without regenerating claims.

The previous builder mixed classification logic with build output as source input.
The reviewed sidecar is now an explicit immutable source input, including Chen's
exact record/figure scopes. New contributions update and audit that sidecar first.
"""
import hashlib,json
from pathlib import Path
from asset_display import display_view
ROOT=Path(__file__).resolve().parents[1]

def validate_reader_view(rid,view):
    # The browser consumes per-record figure objects, not figures_by_source.
    # An explicit empty list is valid; a missing field otherwise silently hides
    # reviewed figures while the source-level gallery remains populated.
    if not isinstance(view.get('figures'),list):
        raise ValueError('Reader requires an explicit per-record figure list: '+rid)
    if any(not isinstance(f,dict) or not f.get('id') for f in view['figures']):
        raise ValueError('Reader figures must be complete objects, not ID references: '+rid)
    if not isinstance(view.get('scopeLabel'),str) or not view['scopeLabel'].strip():
        raise ValueError('Reader requires a visible source/sample scope: '+rid)

def main():
    source=ROOT/'data/reader-presentation-reviewed.json'
    if not source.is_file():raise SystemExit('Missing reviewed Reader sidecar; do not regenerate it from an older classification table.')
    data=json.loads(source.read_text(encoding='utf-8-sig'))
    records={p.stem:json.loads(p.read_text(encoding='utf-8-sig'))for p in (ROOT/'data/records').glob('*.json')}
    for rid,view in data['records'].items():
        if rid not in records:raise ValueError('Unknown Reader record: '+rid)
        if view['source_id']!=records[rid]['lineage']['source_group']:raise ValueError('Reader source mismatch: '+rid)
        validate_reader_view(rid,view)
    hubs={p.stem:json.loads(p.read_text(encoding='utf-8-sig'))for p in (ROOT/'dist/data/materials').glob('*.json')}
    if set(hubs)!=set(data['materials']):raise ValueError('Reviewed Reader material set differs from rebuilt atlas')
    for hid,view in data['materials'].items():
        if view['record_ids']!=hubs[hid]['record_ids']:raise ValueError('Reviewed Reader method scope differs: '+hid)
        if not set(view['record_ids']).issubset(data['records']):raise ValueError('Missing Reader method: '+hid)
    target=ROOT/'dist/data/reader-presentation.json';target.parent.mkdir(parents=True,exist_ok=True)
    view=display_view(data,ROOT,'reader-private-asset-provenance.json')
    target.write_bytes(source.read_bytes())if view is data else target.write_text(json.dumps(view,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'reader_projection_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'records':len(data['records']),'materials':len(data['materials']),'scientific_values_modified':False}))
if __name__=='__main__':main()
