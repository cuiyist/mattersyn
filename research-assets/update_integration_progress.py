"""Advance mutable progress indexes to the already audited work, without closing claims."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
ROOT=Path('[local path redacted]')
B=ROOT/'research-assets/incoming-paper-monitor/batches/20260919-five-paper-pilot'
H=B/'jp0219348';now=datetime.now(timezone.utc).isoformat()
def read(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf8')
def binding(p):return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
s=read(H/'si-numerical-progress-index.json')
for first,last,neg,expected in [(9,10,25,'b802dfd6de998a7f25eadd5b10501ed222a6754acb7ed56c1170d978c6172532'),(11,12,36,'bb87e62d1b76d8eb7351c876a7830508d504072e6f193d8ddf851871f5d8b031')]:
    audit=H/f'si-pages-{first}-{last}-independent-audit.json'
    assert binding(audit)['sha256']==expected
    if not any(c['pages']==[first,last] for c in s['chunks']):
        s['chunks'].append({'pages':[first,last],
            'transcription':binding(H/f'si-pages{first:02}-{last:02}-transcription.json'),
            'audit':binding(audit),'audit_status':'passed_scoped_with_explicit_unresolved_signs' if first==11 else 'passed_after_bounded_author_corrections',
            'rows':180,'numeric_cells':1080,'resolved_numeric_values':1078 if first==11 else 1080,
            'uncertain_signs':2 if first==11 else 0,'markers':180,'negative_Fobs2':neg})
s.update({'at':now,'transcribed_and_independently_audited_pages':list(range(1,13)),
    'remaining_untranscribed_and_unaudited_pages':[13,14], 'remaining_row_count':None,
    'rows':1070,'numeric_cells':6420,'resolved_numeric_values':6418,'uncertain_signs':2,
    'markers':1070,'negative_Fobs2':115,'complete_SI_numerical_review':False,'exact_structure_pair_created':False,
    'progress_note':'Pages1-12 independently audited. Two source-unreadable signs retain null signed values and both candidates. Pages13-14 remain pending; no complete SI/CIF approval.',
    'latest_correction_history':str(H/'si-pages11-12-correction-history.json')})
write(H/'si-numerical-progress-index.json',s)
w=read(B/'workflow-state.json');w['updated_at']=now
w['status']='Gu_published_v29;three_contributions_integrated_and_audited_publication_pending;Heo_SI1_12_audited_13_14_pending'
w['next_action']='Finish GitHub Pages publication of the audited dataset0.23.0 candidate and private project backup; then resume Heo SI13-14 and evidence-priority review. No source claim is closed by this checkpoint.'
w['github_destination']={'project':'cuiyist/mattersyn','project_visibility':'private','site':'cuiyist/mattersyn-site','site_visibility':'public','raw_papers_si':'local_only'}
for p in w['papers']:
    if p['group_id']=='10.1021_jp0219348':p['si_numerical_progress']=s
    elif p['group_id'] in {'10.1021_la036034c','10.1021_jp0473669','10.1021_ja048427j'}:
        p['full_extraction']='source_canonical_reader_visuals_integrated_local_candidate'
        p['full_scientific_audit']='passed_source_canonical_reader_visual_and_integration_scopes;source_missingness_retained'
        p['publication']='pending_GitHub_Pages_deployment_verification'
write(B/'workflow-state.json',w)
print('Updated mutable workflow and Heo progress indexes; all source claims and published-version records remain unchanged.')
