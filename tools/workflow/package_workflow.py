"""Local-only gold-package checks, diff scopes, queue ranking and event metrics.

No network calls, canonical mutation, scientific approval, or deployment.
The current canonical validator and release/importer gates remain mandatory.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from datetime import datetime
import hashlib
import importlib
import json
from pathlib import Path, PurePosixPath
import re
import sys

sys.dont_write_bytecode = True
VERSION = 'mattersyn-gold-paper-package/1'
VERSION_WITH_SCOPE_KIND = 'mattersyn-gold-paper-package/2'
SCOPED_INDEPENDENT_AUDIT = 'scoped_independent_audit'
SHA = re.compile(r'^[0-9a-f]{64}$')
CHECKLIST = ('document_scope', 'recipe_and_variants', 'quantities_units_conditions',
             'chemical_identities', 'sample_structure_links', 'conflicts_missingness',
             'evidence_locators', 'asset_provenance')
TOP_KEYS = {'schema_version','package_id','revision','source','documents','records',
            'locators','assets','reagent_bindings','scope','audit','presentation','derived_files'}
STAGES = {'claimed','extraction_started','extraction_frozen','audit_started',
          'audit_accepted','changes_requested','integration_passed','merged',
          'deployed','live_verified','blocked','error','presentation_completed'}

def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',',':'), allow_nan=False).encode()).hexdigest()

def clone(value):
    return json.loads(json.dumps(value))

def jsonlines(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8-sig').splitlines() if line.strip()]

def safe_file(root, rel):
    if not isinstance(rel,str) or not rel or '\\' in rel or ':' in rel:
        raise ValueError('noncanonical relative path: '+str(rel))
    posix = PurePosixPath(rel)
    if posix.is_absolute() or any(p in ('','.','..') for p in rel.split('/')):
        raise ValueError('unsafe relative path: '+rel)
    root = Path(root).resolve()
    path = root.joinpath(*posix.parts)
    if not path.resolve().is_relative_to(root):
        raise ValueError('path leaves package: '+rel)
    if any(p.is_symlink() for p in [path,*path.parents] if p.is_relative_to(root)):
        raise ValueError('symlink in package: '+rel)
    if not path.is_file():
        raise ValueError('missing package file: '+rel)
    return path

def canonical_science(record):
    """Narrow explicit exclusions: never exclude conditions, identity or evidence."""
    result = clone(record)
    result.pop('revision', None)
    result.pop('updated_at', None)
    quality = result.get('quality', {})
    quality.pop('reviewed_at', None)
    quality.pop('reviewer', None)
    return result

def science_payload(package, root):
    records = {}
    for row in package['records']:
        records[row['record_id']] = canonical_science(load(safe_file(root,row['path'])))
    # Locator/asset changes are scientific. Derived display and administrative audit
    # fields do not invalidate unchanged science; existing build/browser gates check them.
    scoped = {key:clone(package[key]) for key in ('source','documents','locators','assets','scope')}
    for doc in scoped['documents']:
        doc.pop('screened_pass_receipt_id',None)
    for loc in scoped['locators']:
        loc.pop('quote_check',None)  # Check receipt identity is administrative; locator itself remains bound.
    return scoped | {
        'records':records,
        'reagent_bindings': [load(safe_file(root,row['path'])) for row in package['reagent_bindings']]
    }

def pointer(value, ptr):
    if ptr == '': return value
    if not isinstance(ptr,str) or not ptr.startswith('/'):
        raise ValueError('field_pointer must be a JSON Pointer')
    for part in ptr[1:].split('/'):
        if re.search(r'~(?:[^01]|$)',part): raise ValueError('malformed JSON Pointer escape')
        part = part.replace('~1','/').replace('~0','~')
        if isinstance(value,list) and not re.fullmatch(r'(?:0|[1-9][0-9]*)',part):
            raise ValueError('noncanonical JSON Pointer array index')
        value = value[int(part)] if isinstance(value,list) else value[part]
    return value

def accepted_audit(audit,science_hash):
    checklist=audit.get('checklist',{})
    return bool(audit.get('status')=='accepted' and audit.get('scientific_sha256')==science_hash
                and isinstance(audit.get('author_id'),str) and audit['author_id'].strip()
                and isinstance(audit.get('reviewer_id'),str) and audit['reviewer_id'].strip()
                and audit['author_id'].strip()!=audit['reviewer_id'].strip()
                and isinstance(audit.get('receipt_id'),str) and audit['receipt_id'].strip()
                and set(checklist)==set(CHECKLIST)
                and all(v=='passed' or isinstance(v,str) and v.startswith('not_applicable: ') and len(v)>25 for v in checklist.values()))

def validate(package, root, record_validator=None, base_package=None, base_root=None):
    errors = []
    def need(condition,message):
        if not condition: errors.append(message)
    if not isinstance(package,dict): return {'passed':False,'errors':['package must be an object']}
    need(set(package)==TOP_KEYS, 'top-level fields must exactly match package contract')
    version = package.get('schema_version')
    need(version in (VERSION, VERSION_WITH_SCOPE_KIND),'unsupported package schema')
    need(bool(package.get('package_id')),'missing package_id')
    need(isinstance(package.get('revision'),int) and package['revision']>0,'revision must be a positive integer')
    source=package.get('source',{})
    need(set(source)=={'primary_source_id','identity_status','doi','title'},'source fields mismatch')
    need(source.get('identity_status') in ('verified','document_only'),'source identity status missing')
    need(bool(source.get('primary_source_id')) and bool(source.get('title')),'source identity/title missing')
    documents=package.get('documents',[])
    need(isinstance(documents,list) and bool(documents),'at least one independently screened document is required')
    doc_ids=set()
    for doc in documents:
        need(set(doc)=={'document_id','role','sha256','screened_pass_receipt_id','coverage'},'document fields mismatch')
        did=doc.get('document_id'); need(did and did not in doc_ids,'duplicate/empty document_id'); doc_ids.add(did)
        need(doc.get('role') in ('main','si','unknown'),'invalid document role')
        need(bool(SHA.fullmatch(doc.get('sha256',''))),'invalid document SHA-256')
        need(bool(doc.get('screened_pass_receipt_id')),'document needs an actual screened-pass receipt id')
        coverage=doc.get('coverage',{})
        need(set(coverage)=={'status','reviewed_pages','page_count','exclusions'},'coverage fields mismatch')
        need(coverage.get('status') in ('reviewed_scoped','partial','not_reviewed'),'invalid coverage status')
        pages=coverage.get('reviewed_pages',[])
        need(isinstance(pages,list) and all(type(p)==int and p>0 for p in pages),'invalid reviewed pages')
        need(len(pages)==len(set(pages)),'duplicate reviewed pages')
        total=coverage.get('page_count')
        need(total is None or type(total)==int and total>0,'invalid page count')
        need(not pages or total is None or max(pages)<=total,'reviewed page exceeds source page count')
        need(coverage.get('status')!='not_reviewed' or not pages,'unreviewed document cannot claim reviewed pages')
        need(isinstance(coverage.get('exclusions'),list),'coverage exclusions must be explicit list')
    scope=package.get('scope',{})
    expected_scope_fields = {'unit','omissions','companion_required'}
    if version == VERSION_WITH_SCOPE_KIND:
        expected_scope_fields.add('review_scope_kind')
    need(set(scope)==expected_scope_fields,'scope fields mismatch')
    if version == VERSION_WITH_SCOPE_KIND:
        need(scope.get('review_scope_kind')==SCOPED_INDEPENDENT_AUDIT,
             'scoped package is not independently audited')
    need(scope.get('unit') in ('main_text','si_standalone','mixed_scoped'),'invalid minimum publishable scope')
    need(scope.get('companion_required') is False,'main/SI pairing is not a package prerequisite')
    need(isinstance(scope.get('omissions'),list),'scope omissions required')
    if scope.get('unit')=='main_text': need(any(d.get('role')=='main' for d in documents),'main-text package needs main document')
    if scope.get('unit')=='si_standalone': need(any(d.get('role')=='si' for d in documents),'SI-only package needs SI document')
    declared=set(); records={}
    for category in ('records','assets','reagent_bindings','derived_files'):
        rows=package.get(category,[])
        need(isinstance(rows,list),category+' must be an array')
        for row in rows:
            rel=row.get('path')
            need(rel not in declared,'duplicate package file declaration: '+str(rel)); declared.add(rel)
            try:
                path=safe_file(root,rel)
                need(bool(SHA.fullmatch(row.get('sha256',''))),'invalid file hash: '+str(rel))
                need(sha(path)==row.get('sha256'),'file hash mismatch: '+str(rel))
                if category=='records':
                    record=load(path); rid=row.get('record_id')
                    need(set(row)=={'record_id','path','sha256'},'record file fields mismatch')
                    need(bool(rid) and rid not in records,'duplicate/empty record_id')
                    need(record.get('record_id')==rid,'record id differs from exact canonical file')
                    need(record.get('lineage',{}).get('source_group')==source.get('primary_source_id'),'record source group mismatch')
                    records[rid]=record
                    if record_validator:
                        errors.extend('canonical: '+e for e in record_validator(record))
                if category=='assets':
                    need(set(row)=={'path','sha256','kind','document_id','source_locator','record_ids','rights_status'},'asset fields mismatch')
                    need(row.get('document_id') in doc_ids,'asset document unresolved')
                    need(bool(row.get('source_locator')),'asset source locator missing')
                    need(bool(row.get('rights_status')),'asset rights status must be stated, not presumed')
                    need(row.get('kind') in ('source_figure','molecular','coordinate','authored_illustration'),'asset kind unknown')
                if category=='derived_files':
                    need(set(row)=={'path','sha256','derived_from_science'},'derived file fields mismatch')
                    need(row.get('derived_from_science') is True,'derived files cannot introduce unaudited scientific claims')
                if category=='reagent_bindings': need(set(row)=={'path','sha256'},'reagent binding fields mismatch')
            except (OSError,ValueError,TypeError,KeyError,IndexError) as e: errors.append(str(e))
    need(bool(records),'at least one exact canonical record is required')
    need(package.get('derived_files')==[], 'derived_files must be empty: build outputs are generated outside the scientific input package')
    if Path(root).exists():
        for file in Path(root).rglob('*'):
            if file.is_file() and file.relative_to(root).as_posix() != 'package.json':
                need(file.relative_to(root).as_posix() in declared,'undeclared package file: '+file.relative_to(root).as_posix())
    locator_ids=set(); covered=set()
    for loc in package.get('locators',[]):
        need(set(loc)=={'id','document_id','record_id','field_pointer','source_locator','page','quote_check'},'locator fields mismatch')
        lid=loc.get('id'); need(lid and lid not in locator_ids,'duplicate/empty locator id'); locator_ids.add(lid)
        need(loc.get('document_id') in doc_ids,'locator document unresolved')
        need(loc.get('record_id') in records,'locator record unresolved')
        need(bool(loc.get('source_locator')),'source locator missing')
        need(type(loc.get('page'))==int and loc['page']>0,'locator page must be positive integer')
        doc=next((d for d in documents if d.get('document_id')==loc.get('document_id')), {})
        need(loc.get('page') in doc.get('coverage',{}).get('reviewed_pages',[]),'locator page outside explicitly reviewed scope')
        qc=loc.get('quote_check',{})
        need(set(qc)=={'status','receipt_id'},'quote-check metadata fields mismatch')
        need(qc.get('status') in ('passed','not_required_nontext'),'quote check not accepted')
        need(bool(qc.get('receipt_id')),'private quote check or nontext source-check receipt required')
        try:
            pointer(records[loc['record_id']],loc['field_pointer']); covered.add(loc['record_id'])
        except (KeyError,ValueError,IndexError,TypeError): errors.append('locator field pointer does not resolve')
    need(set(records)<=covered,'every record requires a scoped source locator')
    for row in package.get('assets',[]):
        need(set(row.get('record_ids',[]))<=set(records),'asset record assignment unresolved')
    presentation=package.get('presentation',{})
    need(set(presentation)=={'state','missing_components'},'presentation fields mismatch')
    need(presentation.get('state') in ('pending','complete'),'invalid presentation state')
    need(isinstance(presentation.get('missing_components'),list),'presentation missing components required')
    need(presentation.get('state')!='complete' or not presentation.get('missing_components'),'complete presentation lists missing components')
    science_hash=None
    if not errors:
        science_hash=digest(science_payload(package,root))
    audit=package.get('audit',{})
    need(set(audit)=={'author_id','reviewer_id','status','scientific_sha256','base_scientific_sha256','scope','checklist','receipt_id'},'audit fields mismatch')
    need(audit.get('status') in ('pending','changes_requested','accepted'),'invalid audit status')
    if audit.get('status')=='accepted':
        need(bool(audit.get('author_id')) and bool(audit.get('reviewer_id')),'audit identities missing')
        need(audit.get('author_id')!=audit.get('reviewer_id'),'accepted audit must be independent of author')
        need(audit.get('scope') in ('entire_scoped_package','scientific_diff'),'invalid audit scope')
        need(set(audit.get('checklist',{}))==set(CHECKLIST),'fixed scientific checklist incomplete')
        need(all(v=='passed' or isinstance(v,str) and v.startswith('not_applicable: ') and len(v)>25 for v in audit.get('checklist',{}).values()),'scientific checklist not accepted or missing N/A reason')
        need(bool(audit.get('receipt_id')),'accepted private audit receipt id missing')
        need(science_hash is not None and audit.get('scientific_sha256')==science_hash,'audit does not bind current scoped science')
        need(accepted_audit(audit,science_hash),'accepted audit identity/checklist binding is incomplete')
        if audit.get('scope')=='scientific_diff':
            need(bool(SHA.fullmatch(audit.get('base_scientific_sha256') or '')),'diff audit requires accepted base science hash')
            need(base_package is not None and base_root is not None,'diff audit requires supplied accepted base package')
            if base_package is not None and base_root is not None:
                prior=base_package.get('audit',{})
                old_hash=digest(science_payload(base_package,base_root))
                need(accepted_audit(prior,old_hash),
                     'diff base is not an independently accepted scientific package')
                need(audit.get('base_scientific_sha256')==old_hash,'diff audit base hash mismatch')
    return {'schema':'mattersyn-package-validation/1','passed':not errors,'errors':errors,
            'scientific_sha256':science_hash,'canonical_validator_run':record_validator is not None,
            'scientific_acceptance_supplied_not_inferred':audit.get('status')=='accepted',
            'scientific_package_ready_for_existing_integration_gates':not errors and record_validator is not None and audit.get('status')=='accepted',
            'presentation_state':presentation.get('state'),'publication_authorized':False,
            'record_count':len(records),'document_count':len(documents)}

def paths_changed(a,b,path=''):
    if type(a) is not type(b): return [path or '/']
    if isinstance(a,dict):
        return [p for k in sorted(set(a)|set(b)) for p in
                ([path+'/'+k] if k not in a or k not in b else paths_changed(a[k],b[k],path+'/'+k))]
    if isinstance(a,list):
        if len(a)!=len(b): return [path or '/']
        return [p for i,(av,bv) in enumerate(zip(a,b)) for p in paths_changed(av,bv,path+'/'+str(i))]
    return [] if a==b else [path or '/']

def diff_packages(before,broot,after,aroot):
    old=science_payload(before,broot); new=science_payload(after,aroot)
    changed=paths_changed(old,new)
    prior=before.get('audit',{})
    accepted=accepted_audit(prior,digest(old))
    return {'schema':'mattersyn-scientific-diff/1','base_scientific_sha256':digest(old),
            'scientific_sha256':digest(new),'scientific_review_required':bool(changed) or not accepted,
            'prior_scoped_science_accepted':accepted,
            'changed_scientific_paths':changed,'presentation_changed':before['presentation']!=after['presentation'],
            'mechanical_changes_require_build_and_browser_checks':True,
            'note':'No audit is created or accepted by computing this diff.'}

# Quantum-dot / colloidal-nanocrystal scope (owner decision, 2026-09-30). Screening material labels are
# unnormalized free text, so classification uses explicit wording only and keeps doubtful units visible.
QD_IN = re.compile(r'quantum[- ]dots?|\bqds?\b|nanocrystals?|colloid|hot[- ]injection|heat[- ]up|nanoplatelets?|'
                   r'nanorods?|tetrapods?|magic[- ]size|core[/ -]shell|ligand|oleylamine|oleic acid|oleate|'
                   r'trioctylphosphine|\btopo?\b|octadecene|\bode\b|capped|nanoparticles? (?:dispersion|solution)', re.I)
QD_COMPOSITION = re.compile(r'\b(?:cd|pb|zn|hg)(?:s|se|te)\b|\bin(?:p|as|sb)\b|\bcu(?:in|ga)?(?:s|se)2\b|\bag(?:in)?(?:s|se)2\b|'
                            r'\bcspb(?:br|cl|i)3\b|perovskite nano|\bag2(?:s|se)\b|\bcu2-?x?(?:s|se)\b|carbon dots?|'
                            r'(?:silicon|germanium) (?:nanocrystals?|quantum)', re.I)
SEMICONDUCTOR_QD_COMPOSITION = re.compile(
    r'\b(?:cd|pb|zn|hg)(?:s|se|te|o)\b|\bin(?:p|as|sb)\b|'
    r'\b(?:cu|ag)(?:in|ga|bi|znin)?(?:s|se|te)2?\b|\b(?:ag|cu)2(?:s|se|te)\b|'
    r'\bcspb(?:br|cl|i)3\b|perovskite nano|carbon dots?|'
    r'(?:silicon|germanium) (?:nanocrystals?|quantum)', re.I)
QD_OUT = re.compile(r'thin[- ]films?|chemical vapou?r|\bcvd\b|sputter|epitax|single[- ]crystals?|\bbulk\b|ceramic|'
                    r'sinter|solid[- ]state reaction|calcin|\bglass(?:es)?\b|melt[- ]quench|ball[- ]mill|wafer|'
                    r'electrodeposit|monolith|cement|alloy ribbon', re.I)

def quantum_dot_scope(row):
    """Return ('in'|'ambiguous'|'out', reason) from the screen's own wording; never opens a paper."""
    text=' '.join(str(row.get(k) or '') for k in ('material','preparation_summary','structure_summary'))
    colloid=QD_IN.search(text); comp=QD_COMPOSITION.search(text); out=QD_OUT.search(text)
    if colloid and not out: return 'in', 'colloidal/QD wording: '+colloid.group(0)
    if comp and not out: return 'in', 'QD composition: '+comp.group(0)
    if out and not (colloid or comp): return 'out', 'non-colloidal wording: '+out.group(0)
    if colloid or comp: return 'ambiguous', 'mixed wording: '+(colloid or comp).group(0)+' / '+out.group(0)
    return 'ambiguous', 'no scope wording in screen summary'


def semiconductor_qd_priority(row, family):
    """Conservatively prefer identified semiconductor dots over elemental metal NCs.

    This is queue order only; a screen label never establishes scientific eligibility.
    Generic 'quantum dot' or 'nanocrystal' wording does not promote Ag/Au/etc.
    """
    composition = ' '.join(str(value or '') for value in (family, row.get('material')))
    context = ' '.join(str(row.get(key) or '') for key in
                       ('preparation_summary', 'structure_summary'))
    return bool(SEMICONDUCTOR_QD_COMPOSITION.search(composition) or
                re.search(r'\bsemiconductor\s+(?:quantum\s+dot|nanocrystal)',
                          context, re.I))

def rank_queue(rows, identities=None, live_sources=(), scope=None):
    """Rank retained screen evidence, never upgrade it to accepted extraction."""
    identities=identities or {}; groups={}; excluded=Counter(); seen=set()
    for row in rows:
        if row.get('decision')!='pass': excluded['not_pass']+=1; continue
        h=row.get('source_sha256','')
        if not SHA.fullmatch(h): excluded['invalid_document_hash']+=1; continue
        if h in seen: excluded['duplicate_document_content']+=1; continue
        seen.add(h)
        scope_decision=scope_reason=None
        if scope=='quantum-dot':
            scope_decision,scope_reason=quantum_dot_scope(row)
            if scope_decision=='out': excluded['outside_quantum_dot_scope']+=1; continue
        identity=identities.get(h,{})
        verified=identity.get('verified') is True and bool(identity.get('primary_source_id'))
        primary=identity.get('primary_source_id') if verified else None
        if primary in live_sources: excluded['already_live_verified_source']+=1; continue
        key='source:'+primary if verified else 'document:'+h
        role=identity.get('role','unknown') if verified else 'unknown'
        has_recipe=bool(row.get('preparation_locator') and row.get('preparation_summary'))
        has_structure=bool(row.get('structure_locator') and row.get('structure_summary'))
        # Main-text evidence is preferred only when document role is actually verified.
        # A screen receipt alone does not establish recipe completeness or sample linkage.
        score=40*has_recipe+40*has_structure+10*(role=='main')
        flags=row.get('audit_flags',[])
        score-=min(15,3*len(flags))
        family=identity.get('family') or row.get('material') or 'unclassified'
        doc={'document_sha256':h,'primary_source_id':primary,'identity_status':'verified' if verified else 'document_only',
             'role':role,'queue_index':row.get('queue_index'),
             'preparation_locator':row.get('preparation_locator'), 'structure_locator':row.get('structure_locator'),
             'screen_receipt':row.get('decision_file'), 'priority_score':score,'audit_flags':flags,
             'complete_recipe_not_established_by_screen':True,'sample_linkage_status':'requires_extraction_and_audit',
             'scope_decision':scope_decision,'scope_reason':scope_reason}
        if key not in groups:
            groups[key]={'queue_key':key,'primary_source_id':primary,'family':family,
                         'family_is_normalized':bool(identity.get('family')),'documents':[],
                         'priority_score':score,'main_si_pairing_required':False,
                         'scope_check_required':scope_decision=='ambiguous',
                         'semiconductor_qd_priority':False}
        groups[key]['documents'].append(doc)
        groups[key]['priority_score']=max(groups[key]['priority_score'],score)
        groups[key]['semiconductor_qd_priority'] |= (
            scope_decision != 'ambiguous' and semiconductor_qd_priority(row,family))
        if scope_decision=='in': groups[key]['scope_check_required']=False
    values=list(groups.values())
    # Family grouping within the same score band prevents a low-evidence family from
    # outranking a source with both preparation and structural evidence.
    # Clearly in-scope units come before units whose scope still needs a quick human check.
    values.sort(key=lambda r:(not r['semiconductor_qd_priority'],bool(r.get('scope_check_required')),
                              -r['priority_score']//10,str(r['family']).casefold(),
                              -r['priority_score'],r['queue_key']))
    for i,row in enumerate(values,1): row['rank']=i
    return {'schema':'mattersyn-ranked-local-queue/1','ranked_units':values,'excluded':dict(excluded),
            'unique_document_contents':sum(len(r['documents']) for r in values),
            'verified_primary_source_groups':sum(r['primary_source_id'] is not None for r in values),
            'unresolved_document_units':sum(r['primary_source_id'] is None for r in values),
            'scope':scope or 'all','scope_check_required_units':sum(bool(r.get('scope_check_required')) for r in values),
            'not_training_eligibility':True,'not_a_complete_recipe_assessment':True,
            'family_labels_are_not_silver_popularity_calibration':True}

DEEP_AUDIT_PERCENT = 10

def deep_audit_selected(scientific_sha256, percent=DEEP_AUDIT_PERCENT):
    """Deterministic sample keyed to the frozen scientific fingerprint: authors cannot pick it
    without changing the science, and anyone can reproduce the selection."""
    if not SHA.fullmatch(scientific_sha256 or ''): raise ValueError('scientific_sha256 must be a SHA-256 hex digest')
    if not 0 < percent <= 100: raise ValueError('percent must be in (0, 100]')
    return int(scientific_sha256[:8], 16) % 100 < percent

def audit_sample(package, root, percent=DEEP_AUDIT_PERCENT):
    science=digest(science_payload(package, root))
    return {'schema':'mattersyn-deep-audit-sample/1','package_id':package.get('package_id'),
            'scientific_sha256':science,'percent':percent,'deep_audit_required':deep_audit_selected(science,percent),
            'rule':'deep audit iff int(scientific_sha256[:8], 16) % 100 < percent; computed after extraction is frozen',
            'quick_audit_still_required':True}

def log_event(ledger, stage, package_id, at=None, pull_request=None, note=None):
    """Append one stage event to the private ledger. live_verified is written only by release_batch.py."""
    if stage not in STAGES: raise ValueError('unknown stage: '+str(stage))
    if stage=='live_verified': raise ValueError('live_verified events come from tools/publication/release_batch.py')
    if not isinstance(package_id,str) or not package_id.strip(): raise ValueError('package_id is required')
    at=at or datetime.now().astimezone().isoformat(timespec='seconds')
    if datetime.fromisoformat(at.replace('Z','+00:00')).tzinfo is None: raise ValueError('at must include a timezone')
    event={'event_id':f'{stage}:{package_id}:{at}','at':at,'stage':stage,'package_id':package_id.strip()}
    if pull_request: event['pull_request']=pull_request
    if note: event['note']=note
    with Path(ledger).open('a',encoding='utf-8') as f: f.write(json.dumps(event,ensure_ascii=False)+'\n')
    return event

def live_sources(site_checkout):
    """Primary source IDs already published on the site (from built records), for rank --live-sources."""
    found=set()
    for path in sorted((Path(site_checkout)/'data'/'records').glob('*.json')):
        record=load(path); source=(record.get('lineage') or {}).get('source_group')
        if isinstance(source,str) and source.strip(): found.add(source.strip())
    if not found: raise ValueError('no published records found under data/records')
    return sorted(found)

def identities_from_reviews(directory):
    """Reuse explicit current Reader identity receipts; filenames/DOI guesses do not qualify."""
    identities={}; conflicts=set(); skipped=[]
    for file in sorted(Path(directory).glob('*.json')):
        review=load(file)
        if review.get('source_review_promoted') is not True or not review.get('document_identity_verification'):
            skipped.append(file.name); continue
        source=review.get('source_group') or review.get('paper_id')
        if not source: continue
        for doc in review.get('documents',[]):
            h=doc.get('sha256',''); role=doc.get('role')
            if not SHA.fullmatch(h) or role not in ('main','si'): continue
            value={'verified':True,'primary_source_id':source,'role':role,
                   'existing_identity_receipt':file.name,'receipt_sha256':sha(file),
                   'scope':'Reused explicit source-review and document-identity receipt; no new source review performed.'}
            if h in identities and (identities[h]['primary_source_id'],identities[h]['role'])!=(source,role):
                conflicts.add(h)
            else: identities[h]=value
    for h in conflicts: identities.pop(h,None)
    return identities, {'identity_count':len(identities),'conflicting_hashes_withheld':sorted(conflicts),
                        'reviews_without_explicit_promoted_identity_receipt':skipped}

def timestamp(value):
    result=datetime.fromisoformat(value.replace('Z','+00:00'))
    if result.tzinfo is None: raise ValueError('timestamps must include a timezone')
    return result

def event_metrics(events,start,end):
    start=timestamp(start); end=timestamp(end)
    if end<=start: raise ValueError('end must follow start')
    unique={}; paper_seen=set(); tier_seen=set(); records_seen=set(); errors=[]
    for event in events:
        eid=event.get('event_id')
        if not eid: errors.append('missing event_id'); continue
        if eid in unique and unique[eid]!=event: errors.append('conflicting duplicate event: '+eid); continue
        unique[eid]=event
    if errors: raise ValueError('; '.join(errors))
    ordered=sorted(unique.values(),key=lambda e:(timestamp(e['at']),e['event_id']))
    new_papers=set(); new_records=set(); new_by_tier=defaultdict(set); events_by_stage=Counter()
    latest={}; live_event_ids=[]; invalid=[]; pr_packages={}
    for e in ordered:
        t=timestamp(e['at'])
        if t>=end: continue
        stage=e.get('stage'); package=e.get('package_id'); source=e.get('primary_source_id')
        if stage not in STAGES or not package: raise ValueError('unknown stage or missing package_id: '+e['event_id'])
        pr=e.get('pull_request')
        if pr:
            if pr in pr_packages and pr_packages[pr]!=package: raise ValueError('one PR maps to multiple packages: '+pr)
            pr_packages[pr]=package
        latest[package]=e
        if t>=start: events_by_stage[stage]+=1
        if stage!='live_verified': continue
        verification=e.get('verification',{})
        ids=e.get('record_ids')
        if not (isinstance(source,str) and source.strip() and e.get('source_identity_verified') is True
                and isinstance(ids,list) and all(isinstance(r,str) and r.strip() for r in ids)
                and e.get('tier') in ('gold','silver')
                and verification.get('anonymous') is True and verification.get('passed') is True
                and SHA.fullmatch(verification.get('receipt_sha256',''))
                and re.fullmatch(r'(?:[0-9a-f]{40}|[0-9a-f]{64})',e.get('commit',''))
                and str(e.get('url','')).startswith('https://')):
            invalid.append(e['event_id']); continue
        first=source not in paper_seen; first_tier=(e['tier'],source) not in tier_seen
        record_ids=set(ids)
        if t>=start:
            if first: new_papers.add(source)
            if first_tier: new_by_tier[e['tier']].add(source)
            new_records.update(record_ids-records_seen)
            live_event_ids.append(e['event_id'])
        paper_seen.add(source); tier_seen.add((e['tier'],source)); records_seen.update(record_ids)
    elapsed=(end-start).total_seconds()/3600
    return {'schema':'mattersyn-pr-event-metrics/1','start':start.isoformat(),'end_exclusive':end.isoformat(),
            'elapsed_hours':elapsed,'new_distinct_source_papers':len(new_papers),
            'new_primary_source_ids':sorted(new_papers),'papers_per_elapsed_hour':len(new_papers)/elapsed,
            'new_gold_source_contributions':len(new_by_tier['gold']),
            'new_silver_source_contributions':len(new_by_tier['silver']),
            'tier_promotions_are_not_new_distinct_papers':True,
            'cumulative_distinct_live_sources':len(paper_seen),'new_record_count':len(new_records),
            'new_record_ids':sorted(new_records),'stage_event_counts':dict(events_by_stage),
            'latest_package_stage_counts':dict(Counter(e['stage'] for e in latest.values())),
            'accepted_live_event_ids':live_event_ids,'unverified_live_events_excluded':invalid,
            'assumes_complete_supplied_event_history':True,
            'active_worker_time_not_inferred_from_wall_clock':True}

def canonical_validator(checkout):
    scripts=Path(checkout)/'recipe-atlas'/'scripts'
    sys.path.insert(0,str(scripts))
    return importlib.import_module('dataset_lib').validate_record

def write_result(path,value):
    target=Path(path)
    if target.exists(): raise ValueError('output exists; preserve receipts and choose a new path')
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='command',required=True)
    p=commands.add_parser('validate'); p.add_argument('manifest'); p.add_argument('--checkout',required=True); p.add_argument('--base-package'); p.add_argument('--output',required=True)
    p=commands.add_parser('diff'); p.add_argument('before'); p.add_argument('after'); p.add_argument('--output',required=True)
    p=commands.add_parser('rank'); p.add_argument('screened_pass_jsonl'); p.add_argument('--identities'); p.add_argument('--live-sources'); p.add_argument('--scope',choices=['all','quantum-dot'],default='all'); p.add_argument('--output',required=True)
    p=commands.add_parser('log-event'); p.add_argument('ledger'); p.add_argument('--stage',required=True,choices=sorted(STAGES-{'live_verified'})); p.add_argument('--package-id',required=True); p.add_argument('--at'); p.add_argument('--pull-request'); p.add_argument('--note')
    p=commands.add_parser('live-sources'); p.add_argument('site_checkout'); p.add_argument('--output',required=True)
    p=commands.add_parser('audit-sample'); p.add_argument('manifest'); p.add_argument('--percent',type=int,default=DEEP_AUDIT_PERCENT); p.add_argument('--output',required=True)
    p=commands.add_parser('metrics'); p.add_argument('events_jsonl'); p.add_argument('--start',required=True); p.add_argument('--end',required=True); p.add_argument('--output',required=True)
    p=commands.add_parser('identity-map'); p.add_argument('review_directory'); p.add_argument('--output',required=True); p.add_argument('--report',required=True)
    args=parser.parse_args()
    if args.command=='validate':
        result=validate(load(args.manifest),Path(args.manifest).parent,canonical_validator(args.checkout),
                        load(args.base_package) if args.base_package else None,
                        Path(args.base_package).parent if args.base_package else None)
    elif args.command=='diff':
        result=diff_packages(load(args.before),Path(args.before).parent,load(args.after),Path(args.after).parent)
    elif args.command=='rank':
        result=rank_queue(jsonlines(args.screened_pass_jsonl),load(args.identities) if args.identities else {},load(args.live_sources) if args.live_sources else [],None if args.scope=='all' else args.scope)
    elif args.command=='log-event':
        print(json.dumps(log_event(args.ledger,args.stage,args.package_id,args.at,args.pull_request,args.note),ensure_ascii=False)); return 0
    elif args.command=='live-sources':
        sources=live_sources(args.site_checkout); write_result(args.output,sources); print(json.dumps({'live_sources':len(sources)})); return 0
    elif args.command=='audit-sample': result=audit_sample(load(args.manifest),Path(args.manifest).parent,args.percent)
    elif args.command=='metrics': result=event_metrics(jsonlines(args.events_jsonl),args.start,args.end)
    else:
        result,report=identities_from_reviews(args.review_directory)
        write_result(args.report,report)
    write_result(args.output,result)
    print(json.dumps({'identity_count':len(result)} if args.command=='identity-map' else {k:v for k,v in result.items() if k not in ('ranked_units','new_record_ids','errors','new_primary_source_ids')},ensure_ascii=False))
    return 1 if result.get('passed') is False else 0

if __name__=='__main__':
    try: sys.exit(main())
    except (ValueError,OSError,KeyError,TypeError) as exc:
        print(str(exc),file=sys.stderr); sys.exit(2)
