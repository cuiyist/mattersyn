"""Read-only future-ledger partition from explicit immutable cutoff membership.

Writes only a requested private partition JSON; never edits ledger or source files.
The result proposes scope membership, never scientific pairing or completion.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json
TERMINAL={'complete','no_synthesis_recipe','no_useful_information'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def path_id(p):return str(Path(p).resolve()).replace('\\','/').casefold()
def canonical(ledger,key):
    seen=set()
    while key in ledger.get('group_aliases',{}) or ledger.get('groups',{}).get(key,{}).get('alias_of'):
        if key in seen:raise ValueError('Cyclic group aliases')
        seen.add(key);key=ledger.get('group_aliases',{}).get(key) or ledger['groups'][key]['alias_of']
    return key
def partition(ledger,inventory,mapping):
    roots=ledger['source_paths'];files=ledger['files'];groups=ledger['groups']
    cutoff={path_id(e['absolute_path']):e for e in inventory['entries'] if e.get('monitor_eligible')}
    seed={g['group_id']:g for g in mapping['groups'] if g['cutoff_present_file_keys']}
    included={canonical(ledger,k) for k in seed};reasons={k:['mapped included scope in immutable cutoff ledger'] for k in included}
    fileinfo=[];mapped_paths=set();mapped_new=[];changed=[]
    for key,item in files.items():
        alias=item.get('source_id','incoming');absolute=Path(roots[alias])/item.get('relative_filename',key)
        pid=path_id(absolute);gid=canonical(ledger,item['group_id']);cut=cutoff.get(pid)
        if cut:
            included.add(gid);reasons.setdefault(gid,[])
            if 'verified membership path present at cutoff' not in reasons[gid]:reasons[gid].append('verified membership path present at cutoff')
            mapped_paths.add(pid)
            if cut['last_known_canonical_group_id'] is None:mapped_new.append({'cutoff_path':cut['absolute_path'],'current_file_key':key,'current_group_id':gid})
            changed_stat=tuple(item.get(k) for k in ('size','mtime_ns','birthtime_ns'))!=tuple(cut.get(k) for k in ('size_bytes','mtime_ns','birthtime_ns'))
            if changed_stat:changed.append({'file_key':key,'group_id':gid,'role':item.get('role'),'reason':'Current ledger stat differs from cutoff membership; fresh content fingerprint and dependent generation review required.'})
        fileinfo.append({'file_key':key,'path':str(absolute),'group_id':gid,'role':item.get('role'),'exists':item.get('exists',False),'in_cutoff_membership':bool(cut),'last_seen_at':item.get('last_seen_at') or item.get('last_observed_ns')})
    present_canonical={canonical(ledger,gid) for gid,g in groups.items() if not g.get('alias_of')}
    included_current=sorted(included & present_canonical);missing_seed=sorted(included-present_canonical)
    after=[f for f in fileinfo if not f['in_cutoff_membership'] and f['exists']]
    evidence_updates=[dict(f,review_gate='Mapped evidence candidate of an included paper; verify pairing, fingerprint and reopen dependent review if source generation changed. Not a new-paper exclusion.') for f in after if f['group_id'] in included]
    later=[f for f in after if f['group_id'] not in included]
    late_groups=sorted({f['group_id'] for f in later})
    rows=[]
    for gid in included_current:
        g=groups[gid];status=g.get('review',{}).get('status');pending=g.get('needs_recheck',False) or status not in TERMINAL
        previous=[s['source_generation'] for k,s in seed.items() if canonical(ledger,k)==gid]
        newevidence=any(f['group_id']==gid for f in evidence_updates);stat_changed=any(f['group_id']==gid for f in changed)
        generation_changed=bool(previous) and any(g.get('generation')!=n for n in previous)
        rows.append({'group_id':gid,'source_generation':g.get('generation'),'cutoff_mapped_generations':sorted(set(previous)),'queue_order':g.get('queue_order'),'review_status':status,'pending_in_current_ledger':pending,'requires_generation_reopen_consistency_check':bool(newevidence or stat_changed or generation_changed),'post_cutoff_evidence_candidates':sum(f['group_id']==gid for f in evidence_updates),'inclusion_reasons':reasons.get(gid,[])})
    return {'schema':'mattersyn-deadline-scope-partition/1','status':'scope_partition_only_no_queue_or_scientific_approval','cutoff_at':inventory['cutoff_at'],'included_canonical_group_ids':included_current,'included_pending_group_ids':[r['group_id'] for r in rows if r['pending_in_current_ledger']],'included_groups':rows,'missing_current_cutoff_scope_ids':missing_seed,'unmapped_cutoff_files':[{'source_id':e['source_id'],'absolute_path':e['absolute_path'],'relative_path':e['relative_path'],'filename_group_candidate_not_verified':e.get('filename_group_candidate_not_verified'),'filename_role_candidate':e.get('filename_role_candidate')} for pid,e in cutoff.items() if pid not in mapped_paths],'cutoff_files_newly_mapped_since_capture':mapped_new,'nested_cutoff_candidates_held_for_scope_review':inventory['nested_document_candidates'],'changed_cutoff_membership_signatures':changed,'post_cutoff_included_paper_evidence_candidates':evidence_updates,'later_arrival_group_ids':late_groups,'later_arrival_file_candidates':later,'counts':{'included_known_canonical_groups':len(included_current),'included_pending_scopes':sum(r['pending_in_current_ledger'] for r in rows),'included_terminal_scopes':sum(not r['pending_in_current_ledger'] for r in rows),'unmapped_cutoff_files':len(cutoff)-len(mapped_paths),'nested_cutoff_candidates_held':len(inventory['nested_document_candidates']),'post_cutoff_included_evidence_candidates':len(evidence_updates),'later_arrival_group_candidates':len(late_groups),'later_arrival_file_candidates':len(later),'generation_reopen_checks':sum(r['requires_generation_reopen_consistency_check'] for r in rows)},'scientific_rules':['Membership uses exact cutoff paths and stored authoritative group/alias mapping; no filename/DOI-only sample or SI join is performed.','A path is file membership, not a content fingerprint. Ordinary stable-source hashing/generation/pairing checks remain mandatory.','This filter never sets complete/no-recipe status or alters current claims. Current monitor priority/readiness and reopened evidence gates remain in force.','Post-cutoff SI/main evidence assigned to an included scope is a review-update candidate; root must verify source pairing and reopen changed dependencies.','A new group represented solely by post-cutoff files is held in the separate later-arrival queue.'],'ledger_mutated':False,'filter_activated':False}
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--cutoff-manifest',type=Path,required=True);parser.add_argument('--ledger',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);a=parser.parse_args()
    root=Path(__file__).resolve().parent;out=a.output.resolve()
    if not out.is_relative_to(root):raise ValueError('Output must stay in the private deadline directory')
    if out.exists():raise ValueError('Preserve existing partition; use a new output filename')
    manifest=read(a.cutoff_manifest);base=a.cutoff_manifest.parent
    for p,h in manifest['bound_files'].items():
        if sha(p)!=h:raise ValueError('Cutoff bound file changed: '+p)
    ledger_bytes=a.ledger.read_bytes();ledger=json.loads(ledger_bytes)
    p=partition(ledger,read(base/'file-inventory.json'),read(base/'last-authoritative-group-mapping.json'))
    p.update(generated_at=datetime.now(timezone.utc).isoformat(),ledger_last_scan_at=ledger['last_scan_at'],cutoff_manifest_path=str(a.cutoff_manifest.resolve()),cutoff_manifest_sha256=sha(a.cutoff_manifest),partition_ledger_path=str(a.ledger.resolve()),partition_ledger_sha256=hashlib.sha256(ledger_bytes).hexdigest(),generator_sha256=sha(__file__))
    p['current_claims_preserved']=ledger.get('current_batch') or ledger.get('current_paper')
    out.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'path':str(out),'sha256':sha(out),'counts':p['counts']}))
if __name__=='__main__':main()
