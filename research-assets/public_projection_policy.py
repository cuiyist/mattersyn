"""Import-safe source-document exclusion policy for MatterSyn public projections.

No filesystem or Git mutation occurs here.  Source archives and scientific audit
claims remain unchanged; this module only qualifies a separately built projection.
"""
from pathlib import Path, PurePosixPath
from functools import lru_cache
import hashlib
import json
import re

POLICY_VERSION = '2026-09-20.2'
REPORT_RELATIVE = 'incoming-paper-monitor/batches/20260919-five-paper-pilot/public-repository-exclusion-proposal-20260920.json'
EXPECTED_REPORT_SHA256 = '572ae70749f8fac09451154a565e8ede9ac486ba5f39d595bfa903d94334ae82'
EXPECTED_EXCLUDED_PATHS = 12556
PRIVATE_FIELD = 'firstPagePreviewPrivate'
class ProjectionError(ValueError):
    """A safe message that never includes a source-text or credential value."""

def normalize_path(rel):
    if not isinstance(rel,str) or not rel or '\x00' in rel:
        raise ProjectionError('Invalid projection path')
    p=rel.replace('\\','/')
    if p.startswith('/') or re.match(r'^[a-zA-Z]:',p) or any(x in ('','..','.') for x in p.split('/')):
        raise ProjectionError('Projection path must be relative without traversal')
    return p

@lru_cache(maxsize=1)
def _baseline():
    path=Path(__file__).resolve().parent/REPORT_RELATIVE
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=EXPECTED_REPORT_SHA256:
        raise ProjectionError('Exclusion report hash does not match the reviewed policy')
    d=json.loads(raw)
    rows=d['excluded_paths'];paths={normalize_path(x['path']):x['category'] for x in rows}
    if len(rows)!=EXPECTED_EXCLUDED_PATHS or len(paths)!=EXPECTED_EXCLUDED_PATHS:
        raise ProjectionError('Unexpected exclusion path count or duplicate')
    return paths,frozenset(d['explicit_retained_txt_paths'])

def policy_metadata():
    paths,allow=_baseline()
    return {'version':POLICY_VERSION,'report_relative_path':REPORT_RELATIVE,'report_sha256':EXPECTED_REPORT_SHA256,'baseline_excluded_path_count':len(paths),'recursive_removed_field':PRIVATE_FIELD,'source_page_attachment_rule':'Remove public_asset keys whose URL contains /norberg2004/pages/; retain their objects, facts, notes and locators.','credential_gate':'High-confidence credential patterns; errors contain detector names and paths only. No general PII guarantee.','scientific_audit_scope':'Public projection only. Scientific audit hashes refer to retained local originals, not recertified transformed bytes.'}

def exclude_path(rel):
    """Return a reviewed omission reason, or None; never delete the input path."""
    p=normalize_path(rel);low=p.lower();name=PurePosixPath(low).name;ext=PurePosixPath(low).suffix
    paths,allow=_baseline()
    if any(x=='.git' for x in low.split('/')):return 'git_metadata_never_copied'
    if p in paths:return paths[p]
    if ext in ('.pdf','.doc','.docx','.ppt','.pptx','.zip','.xls','.xlsx'):
        return 'original_document_or_archive_local_only'
    if p in allow or name.endswith('.license.txt'):return None
    if any(s in low for s in ('/private/text/','/cache/text/','/first-page-text/')):
        return 'raw_full_or_page_text_cache'
    if low.startswith('research-assets/') and ext=='.txt':return 'individual_raw_source_text'
    if name=='complete-source-payloads.json':return 'private_complete_source_text_payload'
    if ext not in ('.png','.jpg','.jpeg','.webp'):return None
    if '/source-render/' in low or '/audit-pages/' in low or '/norberg2004/pages/' in low:return 'source_page_render'
    if name.startswith('pages-contact-') or ('/pages/' in low and name.startswith('contact-')):return 'source_page_contact_sheet'
    if '/jp0219348/reader-assets/si-' in low and re.fullmatch(r'(?:si-\d+|p\d+)-(?:native|header|left-(?:top|bottom)|right-(?:top|bottom)|[lr](?:top|bottom))\.png',name):
        return 'complete_SI_scan_or_tiled_page_equivalent'
    if re.search(r'(?:^|[-_])(?:main|si|page)[-_]?(?:page[-_]?)?\d+(?:\.png|\.jpg|\.jpeg|\.webp)$',name):return 'source_page_render'
    if name in ('peng2000-source-1.png','peng2000-source-2.png'):return 'source_page_render'
    return None

SECRET_PATTERNS={
 'github_classic_token':re.compile(rb'gh[pousr]_[A-Za-z0-9]{30,}'),
 'github_fine_grained_token':re.compile(rb'github_pat_[A-Za-z0-9_]{50,}'),
 'openai_key_shape':re.compile(rb'\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{35,}'),
 'aws_access_key_shape':re.compile(rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
 'private_key_pem_header':re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'),
 'slack_token_shape':re.compile(rb'\bxox[baprs]-[A-Za-z0-9-]{20,}'),
}
def reject_credentials(rel,raw):
    for name,pat in SECRET_PATTERNS.items():
        if pat.search(raw):raise ProjectionError('Credential-pattern review required: '+name+' in '+rel)

def is_withheld_page_url(value):
    return isinstance(value,str) and '/norberg2004/pages/' in ('/'+value.replace('\\','/')).lower()

def _walk_project(obj,stats):
    if isinstance(obj,dict):
        out={}
        for key,value in obj.items():
            if key==PRIVATE_FIELD:
                stats['private_fields_removed']+=1
                continue
            if key=='public_asset' and is_withheld_page_url(value):
                stats['page_attachments_removed']+=1
                continue
            out[key]=_walk_project(value,stats)
        return out
    if isinstance(obj,list):return [_walk_project(v,stats) for v in obj]
    return obj

def project_bytes(rel,raw):
    """Return projected bytes and non-sensitive counts; unchanged bytes stay exact."""
    rel=normalize_path(rel)
    if not isinstance(raw,bytes):raise TypeError('Projection input must be bytes')
    if exclude_path(rel):raise ProjectionError('Excluded source path cannot be transformed for publication: '+rel)
    if raw.lstrip().startswith(b'%PDF-'):raise ProjectionError('Unclassified PDF content requires local retention: '+rel)
    stats={'private_fields_removed':0,'page_attachments_removed':0,'json_parsed':False,'changed':False}
    # Parse every declared JSON, including escaped key spellings. Embedded JSON
    # requiring filtering is also fail-closed if its filename is nonstandard.
    ext=PurePosixPath(rel).suffix.lower()
    required=ext in ('.json','.jsonl','.ndjson') or '.json.' in rel.lower() or PRIVATE_FIELD.encode() in raw
    if required and (ext in ('.jsonl','.ndjson')):
        try:
            rows=[json.loads(x) for x in raw.splitlines() if x.strip()]
            clean=[_walk_project(x,stats) for x in rows];stats['json_parsed']=True
        except (ValueError,UnicodeError,RecursionError):raise ProjectionError('Invalid JSON-lines payload requires review: '+rel) from None
        if stats['private_fields_removed'] or stats['page_attachments_removed']:
            raw=('\n'.join(json.dumps(x,ensure_ascii=False,separators=(',',':')) for x in clean)+'\n').encode('utf-8');stats['changed']=True
    elif required:
        # Code/documentation can name this field without being a JSON payload.
        declared=ext=='.json' or '.json.' in rel.lower()
        looks_json=raw.lstrip().startswith((b'{',b'[',b'\xef\xbb\xbf{',b'\xef\xbb\xbf['))
        if declared or looks_json:
            try:obj=json.loads(raw)
            except (ValueError,UnicodeError,RecursionError):raise ProjectionError('Invalid JSON payload requires review: '+rel) from None
            stats['json_parsed']=True;clean=_walk_project(obj,stats)
            if stats['private_fields_removed'] or stats['page_attachments_removed']:
                raw=(json.dumps(clean,ensure_ascii=False,indent=2)+'\n').encode('utf-8');stats['changed']=True
    reject_credentials(rel,raw)
    return raw,stats

def transform_bytes(rel,raw):
    """Root synchronization API: apply source-field projection or fail safely."""
    return project_bytes(rel,raw)[0]
