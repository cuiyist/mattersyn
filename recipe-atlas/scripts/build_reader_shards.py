"""Split the public Reader presentation so a page loads only what it shows.

Called at the end of build_reader_metadata.py (and runnable on its own) with
that builder's root; reads its public output (dist/data/reader-presentation.json
and, when split, its part) and writes:

  dist/data/reader/records/<record>.json    one record's presentation view
  dist/data/reader/materials/<material>.json one material's view and method labels
  dist/data/reader/index.json               record -> materials, for record pages
  dist/data/reader/chemicals/<record>.json  the chemical registry entries, bindings and
                                            solution contexts that record uses

A material page loads its material file and then only the record it opens.
The combined reader-presentation files stay unchanged, and no view, figure or
record is rewritten: each file holds the exact objects of the combined view.
"""
import hashlib
import json
import re
import shutil
from pathlib import Path

from public_reader_registry import BASE, PART
from reader_presentation_registry import MARKER, _merge

ROOT = Path(__file__).resolve().parents[1]
SAFE_ID = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]*$')
INDEX_SCHEMA = 'mattersyn-reader-index/1'
MATERIAL_SCHEMA = 'mattersyn-reader-material/1'
CHEMICAL_SCHEMA = 'mattersyn-reader-chemicals/1'
BINDING_TABLES = ('recordBindings', 'bindingNotes', 'recordStateBindings', 'stateBindingNotes',
                  'currentRoleSource', 'sourceRecordSha256')


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, separators=(',', ':')) + '\n').encode('utf-8')


def load_public_view(data):
    base = json.loads((data / BASE).read_bytes())
    if MARKER not in base:
        return base
    marker = base[MARKER]
    raw = (data / marker['part']).read_bytes()
    if marker.get('part') != PART or hashlib.sha256(raw).hexdigest() != marker.get('sha256'):
        raise ValueError('Public Reader part differs from its marker')
    logical = dict(base)
    logical.pop(MARKER)
    return _merge(logical, json.loads(raw))


def shards(view):
    """Return {relative path: bytes} for the per-record, per-material and index files."""
    records, materials = view['records'], view['materials']
    out, owners = {}, {rid: [] for rid in records}
    for rid, entry in records.items():
        if not SAFE_ID.match(rid):
            raise ValueError('Unsafe Reader record id: ' + rid)
        out['records/' + rid + '.json'] = encoded(entry)
    for mid, entry in materials.items():
        if not SAFE_ID.match(mid):
            raise ValueError('Unsafe Reader material id: ' + mid)
        ids = entry.get('record_ids') or []
        missing = [rid for rid in ids if rid not in records]
        if missing:
            raise ValueError('Reader material lists a record without a view: ' + mid)
        for rid in ids:
            owners[rid].append(mid)
        labels = {rid: records[rid]['method_label'] for rid in ids if records[rid].get('method_label')}
        out['materials/' + mid + '.json'] = encoded({'schema': MATERIAL_SCHEMA, 'material': entry, 'method_labels': labels})
    out['index.json'] = encoded({'schema': INDEX_SCHEMA, 'record_materials': {rid: sorted(set(m)) for rid, m in sorted(owners.items())}})
    return out


def chemical_slices(view, chemistry):
    """{relative path: bytes}: per record, every registry entry the reader can look up for it
    (material and state bindings, solution-component contexts, product bindings and the
    presentation's precursor-product references), in the registry's own shapes."""
    registry, bindings = chemistry['registry'], chemistry['bindings']
    contexts, products = chemistry['solution_contexts'], chemistry['product_bindings']
    entries = {e['id']: e for e in registry['entries']}
    by_record = {}
    for context in contexts.get('contexts', []):
        by_record.setdefault(context.get('record_id'), []).append(context)
    records = set(bindings.get('recordBindings', {})) | set(view['records'])
    out = {}
    for rid in sorted(records):
        if not SAFE_ID.match(rid):
            raise ValueError('Unsafe chemical record id: ' + rid)
        tables = {name: {rid: bindings[name][rid]} for name in BINDING_TABLES if rid in bindings.get(name, {})}
        ids = set((bindings.get('recordBindings', {}).get(rid) or {}).values())
        ids |= set((bindings.get('recordStateBindings', {}).get(rid) or {}).values())
        ids |= {c.get('registry_id') for context in by_record.get(rid, []) for c in context.get('components') or []}
        product = products.get('recordBindings', {}).get(rid)
        ids |= set(product.values()) if isinstance(product, dict) else {product} if isinstance(product, str) else set(product or [])
        ids |= {ref.get('registry_id') for ref in (view['records'].get(rid) or {}).get('precursorProductReferences') or []}
        kept = [entries[i] for i in sorted(i for i in ids if isinstance(i, str) and i in entries)]
        out['chemicals/' + rid + '.json'] = encoded({
            'schema': CHEMICAL_SCHEMA,
            'registry': {'schemaVersion': registry.get('schemaVersion'), 'entries': kept},
            'bindings': {'schemaVersion': bindings.get('schemaVersion'), **tables},
            'solutionContexts': by_record.get(rid, [])})
    return out


def load_chemistry(dist):
    base = dist / 'assets/chemical-registry'
    read = lambda name: json.loads((base / name).read_bytes()) if (base / name).is_file() else {}
    return {'registry': read('registry.json'), 'bindings': read('bindings.json'),
            'solution_contexts': read('solution-components.json'), 'product_bindings': read('product-bindings.json')}


def main(root=ROOT):
    data = Path(root) / 'dist/data'
    view = load_public_view(data)
    target = data / 'reader'
    if target.exists():
        shutil.rmtree(target)
    files = shards(view)
    chemistry = load_chemistry(Path(root) / 'dist')
    if chemistry['registry'].get('entries'):
        files.update(chemical_slices(view, chemistry))
    for rel, raw in files.items():
        path = target / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    # Every per-record view is the exact object of the combined view.
    for rid, entry in view['records'].items():
        if json.loads((target / 'records' / (rid + '.json')).read_bytes()) != entry:
            raise ValueError('Reader record shard differs from the combined view: ' + rid)
    print(json.dumps({'reader_record_files': len(view['records']), 'reader_material_files': len(view['materials']),
                      'chemical_record_files': sum(rel.startswith('chemicals/') for rel in files),
                      'bytes': sum(len(raw) for raw in files.values()), 'scientific_values_modified': False}))


if __name__ == '__main__':
    main()
