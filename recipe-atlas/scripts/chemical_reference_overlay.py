"""Pure per-entry enrichment for build_reader_shards.load_chemistry; no I/O."""
import re

def enrich_registry(registry,bindings,overlay,registry_sha256,bindings_sha256):
    if overlay.get('schema')!='MatterSyn-reader-chemical-reference-overlay/1':raise ValueError('chemical reference overlay schema')
    if overlay.get('originalRegistrySha256')!=registry_sha256 or overlay.get('originalBindingsSha256')!=bindings_sha256:raise ValueError('chemical overlay stale input hashes')
    entries={e['id']:e for e in registry['entries']};rows=overlay.get('entries',{})
    if not isinstance(rows,dict)or set(rows)-set(entries):raise ValueError('unknown chemical overlay identity')
    for eid,row in rows.items():
        if not isinstance(row,dict)or row.get('route')not in{'flat','molecule_reference','independent_component_references','ambient_crystal_reference'}:raise ValueError('chemical overlay route')
        if row['route']=='flat':
            if not isinstance(row.get('whyNo3d'),str)or not row['whyNo3d'].strip():raise ValueError('flat entry lacks one-line reason')
        elif row.get('referenceOnly')is not True or row.get('trainingEligible')is not False:raise ValueError('chemical reference eligibility flags')
        # Model path/hash safety and actual byte/rights verification remain in
        # the focused generator/quality/publication gates; no gate is bypassed.
    result=dict(registry)
    result['entries']=[{**entry,'readerReference3d':rows[entry['id']]}if entry['id']in rows else entry for entry in registry['entries']]
    return result
