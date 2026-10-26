"""Optional post-normal-build selection. Default inert; no converter write commands.

The retained original private pair folder is shared with records and sync. This
adapter copies only existing complete normal public_pair objects to a fresh
quote-free export. Compact public positions never determine canonical IDs.
"""
import argparse
import copy
import hashlib
import json
import pathlib
import types

import to_site as converter
import mattersyn_simple as simple


def need(value, reason):
    if not value:
        raise ValueError(reason)



def has_quotes(value):
    if isinstance(value, dict):
        return any(str(k).lower() in ('quote', 'quotes') or has_quotes(v) for k, v in value.items())
    return isinstance(value, list) and any(has_quotes(v) for v in value)


def select_export(public_documents, original_inputs, converter=converter, simple=simple):
    """Pure projection: original_inputs holds doc, original ordinals, and RIDs."""
    need(isinstance(public_documents, list), 'Normal export document list')
    need(len(public_documents) == len(original_inputs), 'Exact normal export/input membership')
    need(all(isinstance(d, dict) and isinstance(d.get('doi'), str) for d in public_documents), 'Exact public DOI identities')
    by_doi = {d['doi']: d for d in public_documents}
    need(len(by_doi) == len(public_documents), 'Unique public DOI documents')
    need(len({x['doc']['doi'] for x in original_inputs}) == len(original_inputs), 'Unique original input DOI documents')
    selected, mapping = [], []
    for entry in original_inputs:
        doc, ordinals = entry['doc'], entry['original_ordinals']
        expected = simple.public_document(doc)
        public = by_doi.get(doc['doi'])
        need(json.dumps(public, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',', ':')) ==
             json.dumps(expected, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',', ':')),
             'Built full public document equals unchanged normal public_document projection')
        need(not has_quotes(public), 'Normal quote-free public schema')
        _, records = converter.records_of(doc, original_ordinals=ordinals)
        record_ids = [r['record_id'] for r in records]
        need(record_ids == entry['record_ids'] and len(record_ids) == len(ordinals), 'One exact original record ID per selected public pair')
        pairs = converter.original_ordinal_pairs(public, ordinals)
        narrowed = copy.deepcopy(public)
        narrowed['pairs'] = [copy.deepcopy(pair) for _, pair in pairs]
        need(set(narrowed) == set(public), 'Public document schema unchanged')
        need(all(new == public['pairs'][old - 1] for new, (old, _) in zip(narrowed['pairs'], pairs)), 'Whole existing public_pair objects only')
        selected.append(narrowed)
        mapping.append(dict(doi=doc['doi'], document_id=public['id'],
                            source_id=converter.Builder(doc).source_id,
                            entries=[dict(public_array_ordinal=new, source_original_ordinal=old,
                                          original_pair_pointer='/pairs/' + str(old - 1), canonical_record_id=rid)
                                     for new, ((old, _), rid) in enumerate(zip(pairs, record_ids), 1)]))
    need(not has_quotes(selected), 'No quoted public output')
    return selected, mapping


def run(a):
    need(a.pairs and a.built_public_json and a.original_ordinals and a.out and a.private_mapping, 'Explicit private input/output paths')
    need(a.out != a.private_mapping and not a.out.exists() and not a.private_mapping.exists(), 'Fresh distinct no-overwrite outputs')
    with a.original_ordinals.open('rb') as f:
        selection_raw = f.read(1048577)
    need(len(selection_raw) <= 1048576, 'Bounded shared ordinal selector')
    selection = json.loads(selection_raw.decode('utf-8-sig'), object_pairs_hook=converter.unique_selection_object)
    rows = selection.get('papers')
    need(selection.get('schema') == 'normal-original-ordinal-selection/1' and
         isinstance(rows, list) and rows and
         all(isinstance(r, dict) and isinstance(r.get('doi'), str) and isinstance(r.get('source_id'), str) for r in rows) and
         len({r['doi'] for r in rows}) == len(rows) and len({r['source_id'] for r in rows}) == len(rows),
         'Exact shared ordinal selector schema and unique identities')
    control = types.SimpleNamespace(original_ordinals=a.original_ordinals, include_optical=False,
                                    _original_ordinal_selection=selection)
    inputs = []
    for path in sorted(a.pairs.glob('*.pairs.json')):
        doc, ordinals = converter.selected_pair_input(control, path)
        row = next(x for x in control._original_ordinal_selection['papers'] if x['doi'] == doc['doi'])
        inputs.append(dict(doc=doc, original_ordinals=ordinals, record_ids=row['record_ids']))
    need(inputs and len(inputs) == len(control._original_ordinal_selection['papers']), 'Exact selected original input membership')
    with a.built_public_json.open('rb') as f:
        raw = f.read(16 * 2**20 + 1)
    need(len(raw) <= 16 * 2**20, 'Bounded normal quote-free build export')
    public = json.loads(raw.decode('utf-8-sig'), object_pairs_hook=converter.unique_selection_object)
    selected, mapping = select_export(public, inputs, converter, simple)
    public_raw = json.dumps(selected, ensure_ascii=False).encode()
    private = dict(schema='normal-quote-free-export-original-ordinal-mapping/1',
                   original_ordinals_control=dict(path=str(a.original_ordinals), bytes=len(selection_raw),
                                                  sha256=hashlib.sha256(selection_raw).hexdigest()),
                   original_full_public_export=dict(path=str(a.built_public_json), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()),
                   selected_public_export=dict(path=str(a.out), bytes=len(public_raw), sha256=hashlib.sha256(public_raw).hexdigest()),
                   papers=mapping, compact_array_positions_must_not_rederive_canonical_IDs=True,
                   public_schema_unchanged=True)
    private_raw = (json.dumps(private, ensure_ascii=False, indent=2) + '\n').encode()
    need(len(public_raw) + len(private_raw) <= 4 * 2**20, 'Bounded selected export and private mapping')
    with a.out.open('xb') as f:
        f.write(public_raw)
    with a.private_mapping.open('xb') as f:
        f.write(private_raw)
    print(json.dumps(dict(papers=len(selected), selected_public_pair_entries=sum(len(d['pairs']) for d in selected),
                          metadata_mapping_only=True, apply_authority=None, publication_credit=0)))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--select', action='store_true')
    for name in ('pairs', 'built-public-json', 'original-ordinals', 'out', 'private-mapping'):
        p.add_argument('--' + name, type=pathlib.Path)
    a = p.parse_args()
    if a.select:
        run(a)
    else:
        print('DEFAULT_INERT: no input, output, canonical or network operations')
