#!/usr/bin/env python3
"""Append exact source_extracted crop/artwork rights; retain all prior registry rows/rules.

Uses canonical record identities and public Reader sidecars, never pass/pair files.
Default is a dry run. Normal source preparation, allowlist and release gates follow.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def serialized(path, data):
    before = Path(path).read_bytes()
    text = json.dumps(data, ensure_ascii=False, indent=2) + ('\n' if before.endswith(b'\n') else '')
    return text.replace('\n', '\r\n').encode('utf-8') if b'\r\n' in before else text.encode('utf-8')


def public_asset(atlas, path, expected):
    if not isinstance(path, str) or '\\' in path or not path.startswith('assets/') or any(p in ('', '.', '..') for p in path.split('/')):
        raise ValueError('invalid public asset path')
    target = atlas / 'static' / path
    target.resolve().relative_to((atlas / 'static').resolve())
    raw = target.read_bytes()
    if digest(raw) != expected: raise ValueError(f'asset checksum differs: {path}')
    return raw


def register(repo, record_ids, recorded_at, direction_id, reviewer, guard, apply=False):
    repo = Path(repo); atlas = repo / 'recipe-atlas'
    registry_path = repo / 'publication/asset-rights-registry.json'
    policy_path = repo / 'publication/public-release-policy.json'
    registry, policy = read(registry_path), read(policy_path)
    original_assets, original_rules = copy.deepcopy(registry['assets']), copy.deepcopy(policy['path_rules'])
    if policy.get('asset_rights_registry_sha256') != digest(registry_path.read_bytes()):
        raise ValueError('existing registry checksum is not pinned')
    guard._registry_assets(registry)
    side = read(atlas / 'data/reader-presentation-reviewed.json')
    chemical_base = atlas / 'static/assets/chemical-registry'
    chemistry = {e['id']: e for e in read(chemical_base / 'registry.json')['entries']}
    chemical_bindings = read(chemical_base / 'bindings.json')['recordBindings']
    candidates = {}

    def add(path, expected, classification, binding, provenance, rights, record_status=None):
        raw = public_asset(atlas, path, expected)
        key = (path, digest(raw))
        if key not in candidates:
            asset = {'asset_hash': digest(raw), 'classification': classification,
                     'delivery_paths': [{'repo': 'mattersyn', 'path': 'recipe-atlas/static/' + path, 'bytes': len(raw)},
                                        {'repo': 'mattersyn-site', 'path': path, 'bytes': len(raw)}],
                     'source_bindings': [], 'provenance_bindings': [], 'rights': rights}
            if record_status: asset['record_status'] = record_status
            candidates[key] = (asset, raw)
        asset, _ = candidates[key]
        if binding not in asset['source_bindings']: asset['source_bindings'].append(binding)
        if provenance not in asset['provenance_bindings']: asset['provenance_bindings'].append(provenance)

    for rid in sorted(set(record_ids)):
        if not re.fullmatch(r'[a-z0-9][a-z0-9_-]*', rid): raise ValueError('invalid record id')
        record_path = atlas / 'data/records' / (rid + '.json'); record = read(record_path)
        if record.get('record_id') != rid or (record.get('quality') or {}).get('review_status') != 'source_extracted':
            raise ValueError(f'not an extracted record: {rid}')
        sid = (record.get('lineage') or {}).get('source_group')
        source = next((s for s in record.get('sources') or [] if s.get('id') == sid), {})
        doi = source.get('doi')
        if not re.fullmatch(r'10\.\d{4,9}/\S+', str(doi or '')): raise ValueError(f'DOI missing: {rid}')
        meta = side['records'].get(rid, {})
        if meta.get('source_id') != sid: raise ValueError(f'Reader source differs: {rid}')
        provenance = {'paper_id': sid, 'doi': doi, 'record_ids': [rid], 'review_status': 'source_extracted',
                      'source_record_sha256': digest(record_path.read_bytes()), 'note': 'Source-extracted facts and page locators; no independent audit asserted.'}
        base_binding = {'doi': doi, 'url': 'https://doi.org/' + doi}
        for fig in meta.get('figures') or []:
            path, expected = fig.get('public_asset'), fig.get('public_asset_sha256')
            locator = fig.get('source_locator') or {}
            match = re.fullmatch(r'assets/paper-reviews/([a-z0-9][a-z0-9_-]*)/((?:figure|table|scheme|chart)-s?[1-9][0-9]*[a-z]?)\.(?:png|jpe?g|webp)', path or '')
            printed = re.sub(r'\W+', '-', str(locator.get('figure') or '').lower()).strip('-')
            if not match or match[1] != sid or printed != match[2] or locator.get('document_role') != 'main' or type(locator.get('page')) is not int or locator['page'] < 1:
                raise ValueError(f'figure locator differs: {rid}')
            fig_provenance = fig.get('provenance') or {}
            if fig_provenance.get('asset_sha256') != expected or not fig_provenance.get('render_tool'):
                raise ValueError(f'figure provenance missing: {rid}')
            binding = dict(base_binding, locators={'document_role': 'main', 'page': locator['page'], 'id': match[2]},
                           crop={'asset_sha256': expected, 'render_tool': fig_provenance['render_tool']})
            if fig_provenance.get('source_pdf_sha256'):
                binding['locators']['source_sha256'] = fig_provenance['source_pdf_sha256']
            for key in ('render_dpi', 'page_size_pdf_points', 'crop_box_pdf_points', 'pixel_size'):
                if key in fig_provenance: binding['crop'][key] = fig_provenance[key]
            rights = {'status': 'user_directed_display', 'copyright_permission_verified': False,
                      'license_id': None, 'license_evidence': [], 'permission_status': 'permission_not_established',
                      'attribution': f'DOI {doi}, {locator["figure"]}, main PDF page {locator["page"]}.',
                      'user_direction': {'record_id': direction_id, 'recorded_at': recorded_at,
                                         'scope': 'display_source_figures_for_source_extracted_papers',
                                         'paper_id': sid, 'doi': doi, 'asset_hash': expected, 'previous_delivery': []}}
            add(path, expected, 'source_figure', binding, provenance, rights, 'source_extracted')
        art = meta.get('protocol_art') or {}
        operations = {o['id']: o for o in record.get('operations') or []}
        for item in art.get('bindings') or []:
            opid = item.get('operation_id')
            if art.get('record_id') != rid or opid not in operations: raise ValueError(f'diagram operation differs: {rid}')
            path = item.get('asset_path')
            if path != f'assets/protocol/{rid}-{opid}.svg': raise ValueError(f'diagram path differs: {rid}')
            page_match = re.fullmatch(r'Main PDF p\.(\d+)', str(item.get('source_locator') or ''))
            locators = {'document_role': 'main', 'id': opid}
            if page_match: locators['page'] = int(page_match[1])
            add(path, item.get('asset_sha256'), 'generated_artwork', dict(base_binding, locators=locators), provenance,
                {'status': 'not_source_derived', 'attribution': 'MatterSyn authored conceptual action diagram; no measured apparatus asserted.'})
        for eid in set((chemical_bindings.get(rid) or {}).values()):
            if not eid.startswith('name-card-'): continue
            entry = chemistry.get(eid)
            if not entry or entry.get('depictionKind') != 'formula' or entry.get('model3dPath'):
                raise ValueError(f'name card differs: {rid}')
            path = 'assets/chemical-registry/' + entry['svgPath']
            add(path, entry['assetHashes']['svgPath'], 'generated_artwork', base_binding, provenance,
                {'status': 'not_source_derived', 'attribution': 'MatterSyn authored chemical name card; no molecular connectivity asserted.'})

    index = guard._build_asset_indexes(registry)[1]
    added_assets = added_rules = 0
    for (path, asset_hash), (asset, raw) in sorted(candidates.items()):
        matches = [index.get((asset_hash, d['repo'], d['path']), []) for d in asset['delivery_paths']]
        if any(matches):
            if not all(len(m) == 1 and m[0] is matches[0][0] for m in matches):
                raise ValueError(f'ambiguous or incomplete prior delivery: {path}')
        else:
            registry['assets'].append(asset); added_assets += 1
        for delivery in asset['delivery_paths']:
            _, reason = guard._approved_rule(delivery['repo'], delivery['path'], policy)
            if reason == 'path_not_allowlisted':
                policy['path_rules'].append({'rule_id': 'simple-extracted-asset-' + digest((delivery['repo'] + ':' + delivery['path']).encode())[:16],
                                            'repo': delivery['repo'], 'path_glob': delivery['path'], 'content_class': 'site_asset',
                                            'decision': 'allow', 'review_status': 'approved', 'reviewer': reviewer,
                                            'requires_source_refs': True})
                added_rules += 1
            elif reason: raise ValueError(f'existing path rule blocks {delivery["path"]}: {reason}')
    assert registry['assets'][:len(original_assets)] == original_assets
    assert policy['path_rules'][:len(original_rules)] == original_rules
    config = dict(policy, asset_rights_registry=registry)
    for (path, _), (asset, raw) in candidates.items():
        for delivery in asset['delivery_paths']:
            result = guard.history_project(delivery['repo'], delivery['path'], raw, config)
            if result.get('action') != 'allow' or result.get('content') != raw:
                raise ValueError(f'unchanged release guard rejects {delivery["path"]}: {result.get("reason")}')
    registry_bytes = serialized(registry_path, registry)
    policy['asset_rights_registry_sha256'] = digest(registry_bytes)
    policy_bytes = serialized(policy_path, policy)
    if apply:
        if registry_bytes != registry_path.read_bytes(): registry_path.write_bytes(registry_bytes)
        if policy_bytes != policy_path.read_bytes(): policy_path.write_bytes(policy_bytes)
    refs = {'recipe-atlas/static/' + path: [{'url': b['url']} for b in asset['source_bindings'] if b.get('url')]
            for (path, _), (asset, _) in candidates.items()}
    return {'records': len(set(record_ids)), 'assets_checked': len(candidates), 'new_assets': added_assets,
            'new_exact_path_rules': added_rules, 'asset_rights_registry_sha256': digest(registry_bytes),
            'source_refs_by_source_path': refs, 'applied': apply}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True); parser.add_argument('--record-id', action='append', required=True)
    parser.add_argument('--recorded-at', required=True); parser.add_argument('--direction-id', required=True)
    parser.add_argument('--reviewer', required=True); parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    guard_path = Path(args.repo) / 'tools/mattersyn-release/public_release_guard.py'
    spec = importlib.util.spec_from_file_location('batch_asset_guard', guard_path)
    guard = importlib.util.module_from_spec(spec); spec.loader.exec_module(guard)
    print(json.dumps(register(args.repo, args.record_id, args.recorded_at, args.direction_id, args.reviewer, guard, args.apply), indent=2))


if __name__ == '__main__':
    main()
