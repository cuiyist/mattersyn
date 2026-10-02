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
                group=records[rid].get('lineage',{}).get('source_group')
                if group and review.get('source_group',paper)!=group:
                    errors.append(paper+': missing or different source-group join: '+rid)
    return errors

def route_membership_errors(record, materials, route, slug, component_elements=None, symbols=None):
    rid=record['record_id']
    actual={hid for hid,view in materials.items() if rid in view.get('record_ids',[])}
    expected=set()
    if route(record):
        formula=record['material']['formula']
        expected={slug(formula)}
        for component in record['material'].get('components',[formula]):
            # Match build_atlas.ensure(): descriptive component labels without a
            # valid element inventory are not standalone material hubs.
            elements=(component_elements or {}).get(component,re.findall('[A-Z][a-z]?',component))
            if symbols is None or (elements and set(elements)<=symbols):
                expected.add(slug(component))
    return [] if actual==expected else [rid+': Reader route membership mismatch; contextual observations are not synthesis routes']

def changed_paths(before, after, pointer=''):
    if type(before) is not type(after):return {pointer or '/'}
    if isinstance(before,dict):
        return set().union(*(changed_paths(before[k],after[k],pointer+'/'+k) if k in before and k in after else {pointer+'/'+k}
                             for k in set(before)|set(after)))
    if isinstance(before,list):
        if len(before)!=len(after):return {pointer or '/'}
        return set().union(*(changed_paths(a,b,pointer+'/'+str(i)) for i,(a,b) in enumerate(zip(before,after))))
    return set() if before==after else {pointer or '/'}

def scoped_audit_reviewer_matches(audit, package_audit):
    """Accept either receipt spelling, never a conflicting alias or self-review."""
    reviewer=package_audit.get('reviewer_id');author=package_audit.get('author_id')
    aliases=[audit[key] for key in ('reviewer_id','auditor_id') if key in audit]
    return (isinstance(reviewer,str) and bool(reviewer) and isinstance(author,str) and bool(author)
            and author!=reviewer and audit.get('author_id')==author and bool(aliases)
            and all(isinstance(name,str) and name==reviewer for name in aliases))

def scoped_audit_decision_accepted(audit):
    """The private quick-audit receipt uses decision; older receipts use verdict."""
    decisions=[audit[key] for key in ('verdict','decision') if key in audit]
    return bool(decisions) and all(value=='ACCEPTED_SCOPED_CONTENT' for value in decisions)

def scoped_audit_identity_matches(audit, package):
    """Some private quick audits name the paper ID rather than the package ID."""
    aliases=[audit[key] for key in ('package_id','paper_id') if key in audit]
    return (bool(aliases) and all(value==package.get('package_id') for value in aliases)
            and audit.get('package_revision')==package.get('revision'))

def scoped_audit_receipt_matches(audit, package_audit, audit_path, package, science):
    """Allow an auditor's pinned normalization of a legacy accepted quick audit."""
    original_name=package_audit.get('receipt_id')
    if original_name==audit_path.name:return True
    if (audit.get('schema')!='mattersyn-independent-scoped-acceptance-addendum/1'
            or not isinstance(original_name,str)
            or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*',original_name)
            or audit.get('original_audit_receipt')!='receipts/'+original_name
            or audit.get('package_id')!=package.get('package_id')
            or audit.get('package_revision')!=package.get('revision')
            or audit.get('scientific_sha256')!=science):
        return False
    original_path=audit_path.parent/original_name
    if (not original_path.is_file()
            or sha(original_path)!=audit.get('original_audit_receipt_sha256')):
        return False
    original=read(original_path)
    return (original.get('schema')=='mattersyn-independent-quick-audit/1'
            and original.get('decision')=='accepted'
            and original.get('package_id')==package.get('package_id')
            and original.get('scientific_sha256')==science
            and scoped_audit_reviewer_matches(original,package_audit)
            and audit.get('frozen_package_manifest_sha256')==original.get('accepted_package_manifest_sha256'))

def scoped_context_link_drop_only(before, after, source_id, doi, candidate):
    """Allow removal of one fictitious formal Reader link, retaining the DOI link byte-for-byte."""
    old=before.get('context_links');new=after.get('context_links')
    if not isinstance(old,list) or not isinstance(new,list) or len(old)!=2 or len(new)!=1:
        return False
    primary=new[0]
    if (not isinstance(primary,dict) or primary.get('relation')!='primary_source'
            or str(primary.get('url','')).lower()!=f'https://doi.org/{doi}'.lower()
            or old.count(primary)!=1):
        return False
    dropped=[link for link in old if link!=primary]
    if len(dropped)!=1 or dropped[0]!={'label':'Source review',
                                        'url':f'paper-review.html?id={source_id}',
                                        'relation':'source_review'}:
        return False
    # A real Reader cannot be silently unlinked. The scoped inventory is checked
    # separately and must truthfully have paper_review_url: null.
    return not (candidate/'recipe-atlas/data/paper-reviews'/(source_id+'.json')).exists()

def scoped_record_changes_allowed(before, after, source_id, doi, candidate):
    changes=changed_paths(before,after)
    allowed={'/revision','/sources/0/main_status','/quality/review_status','/quality/review_scope',
             '/sources/1/si_status','/context_links'}
    sources=before.get('sources',[])
    si_source=(isinstance(sources,list) and len(sources)>1 and isinstance(sources[1],dict)
               and isinstance(sources[1].get('id'),str) and sources[1]['id'].endswith('-si'))
    return changes, not (changes-allowed) and ('/sources/1/si_status' not in changes or si_source) and ('/context_links' not in changes or
            scoped_context_link_drop_only(before,after,source_id,doi,candidate))

def valid_scoped_status_promotion(before, after, changes=None, changes_allowed=False):
    """Accept audited status promotion, including older metadata-only packages.

    A same-revision promotion remains limited to the independently checked
    imported-unreviewed context-link cleanup.
    """
    old_status=before.get('quality',{}).get('review_status')
    if after.get('quality',{}).get('review_status')!='source_reviewed':
        return False
    old_revision=before.get('revision');new_revision=after.get('revision')
    if not isinstance(old_revision,int) or isinstance(old_revision,bool):
        return False
    if old_status=='source_reviewed':
        admin={'/revision','/sources/0/main_status','/sources/1/si_status','/quality/review_scope'}
        return (new_revision==old_revision+1 and changes_allowed
                and changes is not None and '/revision' in changes
                and bool(changes&{'/sources/0/main_status','/quality/review_scope'})
                and not (changes-admin))
    if old_status not in {'imported_unreviewed','metadata_only'}:
        return False
    if new_revision==old_revision+1:
        return True
    return (old_status=='imported_unreviewed' and new_revision==old_revision
            and changes_allowed and changes is not None and '/context_links' in changes)

def scoped_review_errors(entry, candidate, records, inventory, validate_record):
    """Private accepted v5 package replaces a *formal* Reader only for its scoped source."""
    errors=[]
    required={'package_path','package_sha256','validation_receipt_path','validation_receipt_sha256',
              'audit_receipt_path','audit_receipt_sha256'}
    base_keys={'accepted_base_package_path','accepted_base_package_sha256'}
    supplied_base=bool(set(entry)&base_keys)
    if (set(entry)-{'status_delta_receipts'}!=required|(base_keys if supplied_base else set())
            or (supplied_base and not base_keys<=set(entry))):
        return set(),['Scoped acceptance entry fields mismatch']
    deltas=entry.get('status_delta_receipts',[])
    if not isinstance(deltas,list):return set(),['Scoped status-delta receipts must be an array']
    paths={key:Path(entry[key]).resolve() for key in ('package_path','validation_receipt_path','audit_receipt_path')}
    for key,path in paths.items():
        if not path.is_file() or sha(path)!=entry[key.replace('_path','_sha256')]:
            return set(),['Scoped acceptance missing/stale private '+key]
    package=read(paths['package_path']); validation=read(paths['validation_receipt_path']); audit=read(paths['audit_receipt_path'])
    sys.path.insert(0,str(candidate/'tools/workflow'))
    from package_workflow import validate as validate_package
    base_package=None; base_root=None
    if package.get('audit',{}).get('scope')=='scientific_diff':
        if not supplied_base:
            return set(),['Scoped scientific diff lacks an exact accepted base package']
        base_root=Path(entry['accepted_base_package_path']).resolve()
        if not base_root.is_file() or sha(base_root)!=entry['accepted_base_package_sha256']:
            return set(),['Scoped accepted base package missing or stale']
        base_package=read(base_root)
        if (base_package.get('package_id')!=package.get('package_id')
                or base_package.get('source',{}).get('doi')!=package.get('source',{}).get('doi')):
            return set(),['Scoped accepted base package identity differs']
        base_root=base_root.parent
    elif supplied_base:
        return set(),['Scoped non-diff package has unexpected accepted base']
    result=validate_package(package,paths['package_path'].parent,validate_record,base_package,base_root)
    if not result.get('scientific_package_ready_for_existing_integration_gates') or result.get('errors'):
        errors.append('Scoped package scientific/schema validation failed')
    science=result.get('scientific_sha256');pa=package.get('audit',{})
    if not (validation.get('passed') is True and validation.get('canonical_validator_run') is True
            and validation.get('scientific_package_ready_for_existing_integration_gates') is True
            and validation.get('scientific_sha256')==science):
        errors.append('Scoped validation receipt does not bind accepted science')
    if not (scoped_audit_decision_accepted(audit) and audit.get('scientific_sha256')==science
            and scoped_audit_reviewer_matches(audit,pa)
            and scoped_audit_receipt_matches(audit,pa,paths['audit_receipt_path'],package,science)):
        errors.append('Scoped independent audit receipt missing, unbound or self-reviewed')
    source=package.get('source',{});sid=source.get('primary_source_id');doi=str(source.get('doi') or '').lower()
    if not scoped_audit_identity_matches(audit,package):
        errors.append('Scoped audit receipt package identity or revision differs')
    rows=[p for p in inventory.get('per_paper',[]) if p.get('source_group')==sid]
    if len(rows)!=1 or rows[0].get('review_status')!='selected_recipe_and_figure_review':
        errors.append('Scoped inventory evidence missing or incorrectly promoted to formal review')
        row={}
    else:row=rows[0]
    if row.get('doi','').lower()!=doi or row.get('paper_review_url') is not None or not row.get('review_scope'):
        errors.append('Scoped inventory identity or truthful nonformal review scope missing')
    if row.get('paper_id')!=sid or row.get('title')!=source.get('title'):
        errors.append('Scoped inventory paper identity/title differs from accepted source')
    pdocs=package.get('documents',[]);idocs=row.get('documents',[])
    if len(pdocs)!=len(idocs):errors.append('Scoped inventory document coverage missing')
    else:
        for doc,inv in zip(pdocs,idocs):
            coverage=doc.get('coverage',{});pages=coverage.get('reviewed_pages',[]);count=coverage.get('page_count')
            if (doc.get('role')!=inv.get('role') or count!=inv.get('page_count')
                    or pages!=inv.get('pages_read') or not pages or inv.get('all_text_read') is not False
                    or inv.get('all_visually_reviewed') is not False):
                errors.append('Scoped inventory page coverage differs from package or falsely claims full review')
    if not package.get('scope',{}).get('omissions'):
        errors.append('Scoped package has no explicit exclusions')
    used_deltas=set()
    for declared in package.get('records',[]):
        rid=declared.get('record_id');actual=records.get(rid)
        if not actual:
            errors.append('Scoped record missing: '+str(rid));continue
        frozen_path=paths['package_path'].parent/declared['path']
        package_record=read(frozen_path)
        canonical_path=candidate/'recipe-atlas/data/records'/(rid+'.json')
        if not canonical_path.is_file() or read(canonical_path)!=actual:
            errors.append('Scoped canonical record bytes/object mismatch: '+rid);continue
        if not record_contract_errors(actual):
            pass
        else:
            errors.append('Scoped canonical record contract failed: '+rid)
        if not actual.get('sources') or actual['sources'][0].get('doi','').lower()!=doi:
            errors.append('Scoped canonical record primary DOI differs from accepted source: '+rid)
        if not package_record.get('sources') or package_record['sources'][0].get('doi','').lower()!=doi:
            errors.append('Scoped frozen record primary DOI differs from accepted source: '+rid)
        changes,changes_allowed=scoped_record_changes_allowed(package_record,actual,sid,doi,candidate)
        if not changes_allowed:
            errors.append('Scoped canonical record changes unaccepted science: '+rid)
        if actual.get('lineage',{}).get('source_group')!=sid:
            errors.append('Scoped canonical record source-group join is invalid: '+rid)
        if not changes:
            # Routine v5 path: the accepted package already contains the final reviewed record.
            if actual.get('quality',{}).get('review_status')!='source_reviewed':
                errors.append('Scoped unchanged package record is not source-reviewed: '+rid)
            continue
        if not valid_scoped_status_promotion(package_record,actual,changes,changes_allowed):
            errors.append('Scoped canonical record review promotion is invalid: '+rid)
        old_hash=sha(frozen_path);new_hash=sha(canonical_path)
        matches=[]
        for index,item in enumerate(deltas):
            if not isinstance(item,dict) or set(item)!={'path','sha256'}:
                errors.append('Scoped status-delta receipt entry fields mismatch');continue
            path=Path(item['path']).resolve()
            if not path.is_file() or sha(path)!=item['sha256']:
                errors.append('Scoped status-delta receipt missing or stale');continue
            receipt=read(path)
            if receipt.get('old_record_sha256')==old_hash:
                matches.append((index,receipt))
        if len(matches)!=1:
            errors.append('Scoped promoted record lacks one exact pinned status-delta audit: '+rid)
            continue
        index,delta=matches[0];used_deltas.add(index)
        if not (delta.get('schema')=='mattersyn-independent-status-delta-audit/1'
                and delta.get('verdict')=='ACCEPTED_STATUS_ONLY'
                and delta.get('paper_id')==sid
                and delta.get('new_record_sha256')==new_hash
                and delta.get('accepted_deep_audit_sha256')==entry['audit_receipt_sha256']
                and delta.get('reviewer_id') and delta.get('author_id')
                and delta.get('reviewer_id')!=delta.get('author_id')
                and delta.get('reviewer_id')!=pa.get('author_id')
                and set(delta.get('changed_pointers',[]))==changes):
            errors.append('Scoped status-delta audit does not bind exact promoted record: '+rid)
    if len(used_deltas)!=len(deltas):
        errors.append('Scoped acceptance contains unused or duplicate status-delta receipts')
    return {doi},errors

def run(candidate, base, new_ids, scoped_manifest=None):
    started=time.perf_counter();errors=[];inputs={}
    root=candidate/'recipe-atlas'; oldroot=base/'recipe-atlas'
    sys.path.insert(0,str(root/'scripts'))
    from dataset_lib import validate_record
    from build_atlas import synthesis_route, slug, COMPONENT_ELEMENTS, SYMBOLS
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
    inventory=checked(root/'data/inventory-evidence.json')
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
        errors.extend(route_membership_errors(record,reader['materials'],synthesis_route,slug,COMPONENT_ELEMENTS,SYMBOLS))
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
    scoped_dois=set()
    if scoped_manifest is not None:
        scoped=read(scoped_manifest)
        if scoped.get('schema')!='mattersyn-private-scoped-acceptance/1' or not isinstance(scoped.get('packages'),list):
            errors.append('Invalid private scoped acceptance manifest')
        else:
            for entry in scoped['packages']:
                try:
                    accepted,problems=scoped_review_errors(entry,candidate,records,inventory,validate_record)
                    scoped_dois.update(accepted);errors.extend(problems)
                except (OSError,ValueError,TypeError,KeyError,ImportError) as exc:
                    errors.append('Scoped acceptance validation failed: '+str(exc))
    if matched & scoped_dois:errors.append('Source cannot have both formal and scoped review promotion')
    if matched|scoped_dois!=new_dois:errors.append('Not every new primary source has a formal or independently accepted scoped document ledger')
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
    parser.add_argument('--scoped-acceptance',type=Path,help='Private pinned v5 scoped package, validation and independent-audit receipts')
    args=parser.parse_args();candidate=args.candidate.resolve();base=args.base.resolve();report=args.report.resolve()
    if any(report.is_relative_to(p) for p in (candidate,base)):parser.error('Write the private receipt outside both checkouts')
    if args.scoped_acceptance and any(args.scoped_acceptance.resolve().is_relative_to(p) for p in (candidate,base)):
        parser.error('Keep scoped acceptance receipts outside both checkouts')
    result=run(candidate,base,read(args.new_records),args.scoped_acceptance)
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({k:v for k,v in result.items() if k!='input_sha256'}))
    return bool(result['errors'])

if __name__=='__main__':sys.exit(main())
