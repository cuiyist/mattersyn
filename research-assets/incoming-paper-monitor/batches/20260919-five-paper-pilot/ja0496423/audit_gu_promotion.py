"""Independent private promotion audit. Reads source/drafts/runtime; writes this audit only."""
from pathlib import Path
from copy import deepcopy
from collections import Counter
import json, sys, hashlib, datetime

B=Path(__file__).resolve().parent
S=B.parents[4]/'recipe-atlas'
sys.path.insert(0,str(S/'scripts'))
from dataset_lib import validate_record, eligibility, training_view, build_groups

def read(p): return json.loads(p.read_bytes())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,obj): p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

checks=[]; findings=[]; bound={}; per_record=[]
def bind(p):
    p=Path(p)
    try: key=p.relative_to(B).as_posix()
    except ValueError: key=str(p)
    bound[key]=sha(p)
def check(ok,cid,detail):
    checks.append({'id':cid,'passed':bool(ok),'detail':detail})
    if not ok: findings.append({'id':cid,'detail':detail})
def differences(a,b,p=''):
    if type(a)!=type(b): return [p]
    if isinstance(a,dict):
        out=[]
        for k in sorted(set(a)|set(b)):
            if k not in a or k not in b: out.append(p+'/'+k)
            else: out+=differences(a[k],b[k],p+'/'+k)
        return out
    if isinstance(a,list):
        if len(a)!=len(b): return [p]
        return sum((differences(x,y,p+'/'+str(i)) for i,(x,y) in enumerate(zip(a,b))),[])
    return [] if a==b else [p]

O=B/'promotion-proposal'
manifest=read(O/'promotion-manifest.json')
preview=read(O/'training-export-preview.json')
canonical_manifest=read(B/'canonical-record-manifest.json')
audit=read(B/'canonical-records-audit.json')
source_audit=read(B/'source-scientific-audit.json')
for p in [O/'promotion-manifest.json',O/'training-export-preview.json',B/'prepare_promotion.py',B/'canonical-record-manifest.json',B/'canonical-records-audit.json',B/'canonical-source-coverage.json',B/'source-scientific-audit.json',B/'source-facts.json',B/'source-inventory.json',S/'scripts/dataset_lib.py',S/'scripts/schema_definition.py']:
    bind(p)
check(audit['status']=='passed' and not audit['open_findings'],'canonical-audit-pass','Frozen canonical scientific audit passes without open findings.')
check(source_audit['status']=='passed','source-audit-pass','Complete-source scientific audit passes.')
check(manifest['source_canonical_audit_sha256']==sha(B/'canonical-records-audit.json'),'promotion-audit-hash','Proposal binds the exact independent canonical audit.')
for file,h in audit['bound_files'].items():
    check(sha(B/file)==h,'canonical-bound-'+file,'Canonical audit input has not changed.')
for field,file in [('training_export_preview_sha256','training-export-preview.json')]:
    check(manifest[field]==sha(O/file),'preview-hash','Frozen training preview matches actual bytes.')
allowed={'/collection','/quality/review_status','/quality/review_scope','/quality/requested_tasks','/sources/0/main_status'}
tasks={'gu-2004-heterodimer':['precursor_selection','partial_protocol'],'gu-2004-cdacac-preparation':['partial_protocol']}
forbidden={'exact_structure_recipe','size_conditioned_recipe','optical_outcome','success_prediction'}
originals=[]; proposals=[]; recomputed=[]
files=sorted((O/'records').glob('*.json'))
check(len(files)==10 and len(manifest['records'])==10,'record-count','Exactly ten promoted records and ten manifest entries.')
check({p.stem for p in files}=={x['record_id'] for x in canonical_manifest['records']},'record-set','Promoted record set equals frozen canonical set.')
for p in files:
    src=B/'canonical-drafts'/p.name
    old=read(src); new=read(p); rid=old['record_id']
    originals.append(old);proposals.append(new);bind(src);bind(p)
    row=next(x for x in manifest['records'] if x['record_id']==rid)
    check(sha(src)==audit['bound_record_files'][p.name]==row['source_sha256'],rid+'-original-hash','Original record matches canonical audit and proposal manifest.')
    check(sha(p)==row['proposal_sha256'],rid+'-proposal-hash','Promoted record matches proposal manifest.')
    diff=differences(old,new)
    check(all(any(d==a or d.startswith(a+'/') for a in allowed) for d in diff),rid+'-field-diff','Every changed leaf belongs to the five authorized metadata fields.')
    restored=deepcopy(new)
    restored['collection']=old['collection']
    for key in ['review_status','review_scope','requested_tasks']: restored['quality'][key]=old['quality'][key]
    restored['sources'][0]['main_status']=old['sources'][0]['main_status']
    check(restored==old,rid+'-scientific-equality','Restoring only the five allowed metadata fields gives exact nested equality to the frozen original; other quality fields are not replaced wholesale.')
    check(new['collection']=='reviewed_literature' and new['quality']['review_status']=='source_reviewed',rid+'-review-state','Only the intended collection/review state is proposed.')
    check(new['quality']['requested_tasks']==tasks.get(rid,[]),rid+'-task-request','Requested tasks match the authorized per-record list, including empty lists for eight non-synthesis contexts.')
    errors=validate_record(new)
    check(not errors,rid+'-schema-semantic','Current Draft 2020-12 schema plus all semantic/source/lineage/quantity constraints pass: '+str(errors))
    eligible=eligibility(new)
    selected=[t for t,v in eligible.items() if v['eligible']]
    check(set(selected)==set(tasks.get(rid,[]))==set(row['eligible_tasks']),rid+'-eligibility','Recomputed gated eligibility equals requested proposal tasks.')
    check(not any(eligible[t]['eligible'] for t in forbidden),rid+'-forbidden-tasks','No exact-coordinate, size-conditioned, optical benchmark or success-prediction task is eligible.')
    for task in selected: recomputed.append(training_view(new,task))
    per_record.append({'record_id':rid,'source_sha256':sha(src),'proposal_sha256':sha(p),'changed_leaf_paths':diff,'scientific_content_exact_after_metadata_restore':restored==old,'schema_errors':errors,'eligible_tasks':selected,'blocked_tasks':sorted(forbidden)})
key=lambda row:(row['record_id'],row['task'])
check(sorted(recomputed,key=key)==sorted(preview['exports'],key=key),'export-exact-equality','All training-preview inputs, outputs and provenance exactly equal independent regeneration with the current training_view function.')
counts=Counter(x['task'] for x in recomputed)
check(dict(counts)=={'partial_protocol':2,'precursor_selection':1} and len(recomputed)==3,'export-counts','Exactly two partial-protocol rows and one precursor-selection row.')
check(preview['status']=='private_proposal_only' and preview['published'] is False and manifest['publication_approved'] is False,'private-only','Preview and proposal remain unpublished and do not claim publication approval.')
for row in recomputed:
    check(set(row['input'])=={'composition','method'},row['record_id']+'-'+row['task']+'-inputs','Recipe inputs include only composition and method; no measured outcome, diffraction, phase/size label or diagram leaks into target inputs.')
    original=next(r for r in originals if r['record_id']==row['record_id'])
    if row['task']=='partial_protocol':
        expected=[o for o in original['operations'] if o['stage']!='characterization']
        check(row['output']['operations']==expected,row['record_id']+'-protocol-operations','Exported operations preserve frozen source quantities, approximation, atmosphere, endpoints, dependencies and retained fractions.')
        check(row['output']['missing_fields']==original['quality']['missing_fields'] and bool(row['output']['missing_fields']),row['record_id']+'-missingness','Unreported/conflicting fields stay explicit; partial protocol is not represented as a complete executable SOP.')
        check(all(o['stage']!='characterization' for o in row['output']['operations']),row['record_id']+'-no-acquisition','Measurement operations are excluded from protocol supervision.')
    else:
        names={m['name'] for m in row['output']['precursors']}
        check(names=={'Pt(acac)2','Fe(CO)5','Elemental sulfur powder','Cd(acac)2'},'precursor-set','Only the four source synthesis precursors are selected; ligands, solvents, process additives, upstream CdCl2 and measurement standards are excluded.')
groups=build_groups(proposals); old_groups=build_groups(originals)
check(groups==old_groups and len(set(groups.values()))==1,'source-split-group','All ten records retain exactly the same one source split group as frozen originals.')
check(all(r['lineage']==o['lineage'] for r,o in zip(proposals,originals)),'lineage-exact','DOI/source group, recipe family, parent and duplicate lineage are unchanged.')
protocol_counts={r['record_id']:len(r['output']['operations']) for r in recomputed if r['task']=='partial_protocol'}
check(protocol_counts=={'gu-2004-cdacac-preparation':6,'gu-2004-heterodimer':15},'protocol-operation-counts','Six upstream preparation operations and fifteen one-pot operations remain separate rows; no extra synthesis route is created.')
for key_,expected in [('record_count',10),('proposed_precursor_selection_rows',1),('proposed_partial_protocol_rows',2),('proposed_exact_structure_pairs',0),('proposed_size_conditioned_rows',0),('proposed_optical_rows',0),('proposed_success_labels',0)]:
    check(manifest[key_]==expected,'manifest-'+key_,'Manifest task/count claim matches independently recomputed scope.')
result={'schema':'mattersyn.private-promotion-source-audit.v1','status':'passed' if not findings else 'failed','auditor':'norberg2004_extract','source_id':'gu2004','audited_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Independent metadata-only private promotion audit against frozen canonical science, current schema/semantic validator and current training task gates. Not publication proof or integrated Site approval.','bound_files':bound,'checks':checks,'records':per_record,'split_groups':groups,'counts':{'records':len(proposals),'training_preview_rows':len(recomputed),'precursor_selection':counts.get('precursor_selection',0),'partial_protocol':counts.get('partial_protocol',0),'exact_structure_recipe':counts.get('exact_structure_recipe',0),'size_conditioned_recipe':counts.get('size_conditioned_recipe',0),'optical_outcome':counts.get('optical_outcome',0),'success_prediction':counts.get('success_prediction',0),'checks':len(checks)},'partial_protocol_operation_counts':protocol_counts,'private_promotion_approved':not findings,'scientific_content_changed':False if all(x['scientific_content_exact_after_metadata_restore'] for x in per_record) else True,'open_findings':findings,'limitations':['Approval is bound to these exact ten proposal files and the hashed current schema/gate code.','Only one precursor-selection row and two partial-protocol rows are approved in this private proposal.','Partial protocol supervision retains missing fields; it is not complete SOP or exact-structure recipe supervision.','Separate reader, molecular/apparatus, integrated visual and release checks remain required.','No Site, shared ledger, memory, canonical originals or other visual packages were edited.'],'publication_approved':False,'site_visual_audit_passed':False}
save(B/'promotion-source-audit.json',result)
md='# Gu 2004 private promotion source audit\n\nStatus: **'+result['status']+'**. '+str(len(checks))+' independent checks; '+str(len(findings))+' open findings.\n\nAll ten promoted records pass the current schema and semantic validator. Only collection, review status/scope, requested tasks and primary-source reading status change. Restoring exactly those fields gives complete nested equality to every frozen original; no scientific or other quality field changes.\n\nThe training preview exactly matches independent regeneration: one FePt–CdS precursor-selection row, one 15-operation FePt–CdS partial protocol, and one six-operation Cd(acac)₂ preparation partial protocol. The other eight records request no tasks. There are zero exact structure–recipe, size-conditioned, optical-outcome or success-prediction rows. Missing fields remain explicit and all ten records retain one unchanged source split group.\n\nThis approves the hash-bound **private promotion proposal only**. It does not demonstrate public deployment, complete SOPs, exact atomic structures or final reader/visual approval. Exact input hashes, metadata differences and checks are in the JSON report.\n'
if findings: md+='\nOpen findings:\n'+''.join('- '+f['id']+': '+f['detail']+'\n' for f in findings)
(B/'promotion-source-audit.md').write_text(md,encoding='utf-8')
print(json.dumps({'status':result['status'],'checks':len(checks),'open_findings':len(findings),'source_split_group':sorted(set(groups.values())),'json_sha256':sha(B/'promotion-source-audit.json'),'md_sha256':sha(B/'promotion-source-audit.md')},ensure_ascii=False))
