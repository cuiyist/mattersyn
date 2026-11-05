"""Copy an independently reviewed presentation projection, without regenerating claims.

The previous builder mixed classification logic with build output as source input.
The reviewed sidecar is now an explicit immutable source input, including Chen's
exact record/figure scopes. New contributions update and audit that sidecar first.
"""
import hashlib,json
from pathlib import Path
from asset_display import display_view
from build_reader_shards import main as write_reader_shards
from reader_presentation_registry import load_reviewed_reader, source_paths
from public_reader_registry import public_parts
from route_labels import route_label
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
    data=load_reviewed_reader(source)
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
    # Records whose method is the generic extraction phrase get a route name derived
    # from their own steps and materials (route_labels.py); the record is unchanged.
    labels={rid:route_label(records[rid]) for rid,entry in view['records'].items() if not entry.get('method_label')}
    labels={rid:label for rid,label in labels.items() if label}
    # A labelled copy is a new object, so the unchanged-bytes shortcut below never applies to it.
    if labels:view={**view,'records':{rid:({**entry,'method_label':labels[rid]} if rid in labels else entry) for rid,entry in view['records'].items()}}
    legacy_raw=source.read_bytes() if view is data and len(source_paths(source))==1 else (json.dumps(view,ensure_ascii=False,separators=(',',':'))+'\n').encode('utf-8')
    payloads=public_parts(view,legacy_raw)
    for name,raw in payloads.items():(target.parent/name).write_bytes(raw)
    # Per-record and per-material files for the page loaders (build_reader_shards.py).
    write_reader_shards(ROOT)
    print(json.dumps({'reader_projection_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'records':len(data['records']),'materials':len(data['materials']),'route_labels_added':len(labels),'scientific_values_modified':False}))
if __name__=='__main__':main()
