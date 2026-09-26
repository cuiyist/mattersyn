"""Read-only integration checks shared by all new-paper packages.

Run against an isolated merged candidate before the expensive build. This does
not review chemistry, approve source reading, import files, or authorize release.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import time

sys.dont_write_bytecode = True

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def objects(value):
    if isinstance(value,dict):
        yield value
        for child in value.values():yield from objects(child)
    elif isinstance(value,list):
        for child in value:yield from objects(child)

def record_contract_errors(record):
    rid=record.get('record_id','?');errors=[]
    if record.get('collection')!='reviewed_literature':errors.append(rid+': collection must be reviewed_literature')
    if record.get('quality',{}).get('review_status')!='source_reviewed':errors.append(rid+': source review is not accepted')
    return errors

def chemical_errors(record, bindings, registry_ids, record_hash):
    rid=record['record_id']; errors=[]
    expected={m['id'] for m in record['materials']}
    expected.update(o['chemical_material_id'] for o in record['condition_options'] if o.get('chemical_material_id'))
    actual=bindings.get('recordBindings',{}).get(rid)
    if not isinstance(actual,dict) or set(actual)!=expected:
        errors.append(rid+': reagent bindings must equal materials and chemical alternatives; keep process states separate')
    elif not set(actual.values()) <= registry_ids:
        errors.append(rid+': unresolved chemical registry identity')
    if bindings.get('sourceRecordSha256',{}).get(rid)!=record_hash:
        errors.append(rid+': stale chemical source-record digest')
    states=bindings.get('recordStateBindings',{}).get(rid,{})
    if not isinstance(states,dict) or not set(states)<={s['id'] for s in record['material_states']}:
        errors.append(rid+': invalid process-state binding namespace')
    elif not set(states.values()) <= registry_ids:
        errors.append(rid+': unresolved process-state registry identity')
    return errors

def review_link_errors(review, records):
    errors=[]; paper=review.get('paper_id','?')
    items={item['id'] for section in review.get('reader_sections',[]) for item in section.get('items',[])}
    chars=review.get('characterization_inventory',[])
    if not isinstance(chars,(dict,list)):
        return [paper+': unsupported characterization inventory']
    if isinstance(chars,dict) and not isinstance(chars.get('reader_item_ids'),list):
        errors.append(paper+': missing characterization reader-item list')
    for inventory in (review.get('recipe_inventory',[]),chars):
        for row in objects(inventory):
            if 'reader_item_ids' in row:
                ids=row['reader_item_ids']
                if not isinstance(ids,list) or not set(ids)<=items:
                    errors.append(paper+': unresolved characterization Reader item')
            ids=row.get('record_ids',[])
            if 'record_id' in row:ids=[*ids,row['record_id']]
            for rid in ids:
                if rid not in records:
                    errors.append(paper+': unresolved record '+str(rid));continue
                if review['doi'].lower() not in {s.get('doi','').lower() for s in records[rid]['sources']}:
                    errors.append(paper+': record belongs to a different source: '+rid)
    return errors

def route_membership_errors(record, materials, route, slug):
    rid=record['record_id']
    actual={hid for hid,view in materials.items() if rid in view.get('record_ids',[])}
    expected=set()
    if route(record):
        formula=record['material']['formula']
        expected={slug(f) for f in {formula,*record['material'].get('components',[formula])}}
    return [] if actual==expected else [rid+': Reader route membership mismatch; contextual observations are not synthesis routes']

def run(candidate, base, new_ids):
    started=time.perf_counter();errors=[];inputs={}
    root=candidate/'recipe-atlas'; oldroot=base/'recipe-atlas'
    sys.path.insert(0,str(root/'scripts'))
    from dataset_lib import validate_record
    from build_atlas import synthesis_route, slug
    from build_reader_metadata import validate_reader_view
    from review_scope import source_review_scope
    def checked(path):
        inputs[path.relative_to(candidate).as_posix()]=sha(path)
        return read(path)
    for name in ('dataset_lib.py','schema_definition.py','build_atlas.py','build_reader_metadata.py','review_scope.py'):
        p=root/'scripts'/name;inputs[p.relative_to(candidate).as_posix()]=sha(p)
    new_ids=set(new_ids)
    if not new_ids or not all(isinstance(rid,str) and re.fullmatch(r'[a-z0-9][a-z0-9-]*',rid) for rid in new_ids):
        raise ValueError('Supply a nonempty list of safe canonical record IDs')
    current_paths={p.stem:p for p in (root/'data/records').glob('*.json')}
    old_paths={p.stem:p for p in (oldroot/'data/records').glob('*.json')}
    if set(current_paths)-set(old_paths)!=new_ids or set(old_paths)-set(current_paths):
        errors.append('Candidate record additions differ from the declared set, or remove a prior record')
    for rid,path in old_paths.items():
        if rid in current_paths and path.read_bytes()!=current_paths[rid].read_bytes():
            errors.append('Prior canonical record changed: '+rid)
    records={rid:checked(path) for rid,path in current_paths.items()}
    reader=checked(root/'data/reader-presentation-reviewed.json')
    bindings=checked(root/'static/assets/chemical-registry/bindings.json')
    registry=checked(root/'static/assets/chemical-registry/registry.json')
    registry_ids={x['id'] for x in registry['entries']}
    new_dois=set()
    for rid in sorted(new_ids):
        if rid not in records:errors.append('Missing new record: '+rid);continue
        record=records[rid]; validation=validate_record(record);errors.extend(validation)
        if validation:continue
        errors.extend(record_contract_errors(record))
        new_dois.update(s.get('doi','').lower() for s in record['sources'][:1])
        view=reader.get('records',{}).get(rid)
        if not isinstance(view,dict):errors.append(rid+': missing Reader view');continue
        try:validate_reader_view(rid,view)
        except ValueError as exc:errors.append(str(exc))
        if view.get('source_id')!=record['lineage']['source_group']:errors.append(rid+': Reader source-group mismatch')
        errors.extend(chemical_errors(record,bindings,registry_ids,sha(current_paths[rid])))
        errors.extend(route_membership_errors(record,reader['materials'],synthesis_route,slug))
        for ref in objects(view):
            rel=ref.get('data_path');digest=ref.get('input_sha256')
            if not isinstance(rel,str) or not digest:continue
            rel=re.sub(r'^dist/','',rel)
            if not rel.startswith(('data/records/','data/paper-reviews/')):continue
            path=(root/rel).resolve()
            if not path.is_relative_to(root.resolve()) or not path.is_file() or sha(path)!=digest:
                errors.append(rid+': stale or unsafe Reader input pointer '+rel)
        samples={x['sample_id'] for x in record['products']}
        for context in view.get('productContexts',[]):
            if context.get('record_id',rid)==rid and context.get('sample_id') not in samples:
                errors.append(rid+': unresolved Reader sample context')
    matched=set()
    for path in sorted((root/'data/paper-reviews').glob('*.json')):
        review=read(path)
        if review.get('doi','').lower() not in new_dois:continue
        checked(path);matched.add(review['doi'].lower())
        try:source_review_scope(review)
        except (KeyError,ValueError) as exc:errors.append(review.get('paper_id','?')+': '+str(exc))
        errors.extend(review_link_errors(review,records))
        for document in review.get('documents',[]):
            pages=document.get('pages',[])
            if sorted(x.get('page',0) for x in pages)!=list(range(1,document.get('page_count',0)+1)) or not pages:
                errors.append(review['paper_id']+': incomplete page inventory')
            if not all(x.get('text_read') is True and x.get('visual_review') is True for x in pages):
                errors.append(review['paper_id']+': source page reading not complete')
            if not re.fullmatch('[a-f0-9]{64}',document.get('sha256','')):errors.append(review['paper_id']+': missing document digest')
    if matched!=new_dois:errors.append('Not every new primary source has a reviewed document ledger')
    return {'schema':'mattersyn-additive-preflight/1','status':'failed' if errors else 'passed',
            'elapsed_seconds':round(time.perf_counter()-started,3),'new_records':len(new_ids),
            'new_primary_sources':len(new_dois),'prior_records_checked':len(old_paths),
            'errors':errors,'input_sha256':inputs,
            'scope':'Read-only compatibility and additive integrity. Scientific audit, image inspection, full builder/eligibility comparisons, public-boundary checks and browser/publication verification remain required.',
            'publication_approved':False}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',required=True,type=Path)
    parser.add_argument('--base',required=True,type=Path)
    parser.add_argument('--new-records',required=True,type=Path,help='Private JSON array of accepted new record IDs')
    parser.add_argument('--report',required=True,type=Path,help='Private receipt path; must be outside both checkouts')
    args=parser.parse_args();candidate=args.candidate.resolve();base=args.base.resolve();report=args.report.resolve()
    if any(report.is_relative_to(p) for p in (candidate,base)):parser.error('Write the private receipt outside both checkouts')
    result=run(candidate,base,read(args.new_records))
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({k:v for k,v in result.items() if k!='input_sha256'}))
    return bool(result['errors'])

if __name__=='__main__':sys.exit(main())
