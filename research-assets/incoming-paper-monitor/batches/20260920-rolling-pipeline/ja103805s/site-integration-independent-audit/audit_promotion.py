import json, hashlib, copy, re, sys, shutil
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
from inspect_delta import load,diff
O=Path(__file__).resolve().parent;E=O.parent;P=E/'site-integration-proposal/v1';Q=E/'site-integration-proposal/v2'
C=E/'canonical-proposal/v3';R=E/'public-review-proposal/v3';M=E/'visuals/molecules';A=E/'visuals/apparatus/v1'
S=Path(r'[local path redacted]')
V1='aadd9f771d9a1d73e5453e3dd237e248b3f5d72877390a745596d3e8c1d6a87f';V2='1a512c3089df906dbf499761ad79ca88ee8872bcd744c30350990b75e02cbebd'
checks=[];findings=[];bound={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bind(p):
    p=Path(p); h=sha(p);bound[str(p)]={'path':str(p),'sha256':h,'bytes':p.stat().st_size};return h
def check(ok,label):
    checks.append({'check':label,'passed':bool(ok)})
    if not ok:findings.append({'id':f'PROMO-{len(findings)+1:02}','finding':label})
def read(p):bind(p);return load(p)
def restore(new,old,paths):
    z=copy.deepcopy(new)
    for p in paths:
        a=z;b=old; parts=p.strip('/').split('/')
        for k in parts[:-1]:a=a[int(k)] if isinstance(a,list) else a[k];b=b[int(k)] if isinstance(b,list) else b[k]
        k=parts[-1]
        if isinstance(a,list):a[int(k)]=copy.deepcopy(b[int(k)])
        elif k not in b:del a[k]
        else:a[k]=copy.deepcopy(b[k])
    return z
for base,expected in [(P,V1),(Q,V2)]:
    f=read(base/'package-freeze.json');check(sha(base/'package-freeze.json')==expected,'Freeze '+base.name)
    listed=set()
    for x in f['files']:
        p=base/x['path'];listed.add(x['path'].replace('\\','/'))
        check(p.is_relative_to(base),'Frozen path within proposal '+x['path']);check(bind(p)==x['sha256'],'Frozen hash '+base.name+'/'+x['path']);check(p.stat().st_size==x['bytes'],'Frozen bytes '+base.name+'/'+x['path'])
    actual={p.relative_to(base).as_posix() for p in base.rglob('*') if p.is_file()}-{'package-freeze.json'}
    check(actual==listed,'Freeze lists every payload '+base.name)
pm=read(Q/'promotion-manifest.json');prior_bound={}
for name,h in pm['source_audits'].items():
    d=read(E/name);check(sha(E/name)==h,'Prior audit binding '+name)
    check(d.get('status') in {'passed','passed_independent_source_scientific_audit_revision_2'},'Prior audit passed '+name)
    bf=d.get('bound_files',{})
    if isinstance(bf,dict):prior_bound.update({str(Path(k)):v if isinstance(v,str) else v['sha256'] for k,v in bf.items()})
    else:prior_bound.update({str(Path(v['path'])):v['sha256'] for v in bf})
record_paths={'/collection','/reader_role','/quality/review_status','/quality/missing_fields','/quality/review_scope','/sources/0/main_status','/sources/0/si_status','/sources/0/reuse_status'}
records={};record_deltas={};roles=Counter();stale='Canonical independent scientific audit is pending; the source audit passed separately.'
route_ids={'evans-2010-pbse-msc-family','evans-2010-pbse-qd','evans-2010-cdse-qd'}
for entry in pm['records']:
    rid=entry['record_id'];old=read(C/(rid+'.json'));p1=read(P/'records'/(rid+'.json'));new=read(Q/'records'/(rid+'.json'));records[rid]=new
    paths={x[0] for x in diff(old,p1)};record_deltas[rid]=sorted(paths);check(paths==record_paths,'Only approved v1 metadata paths '+rid)
    check(restore(p1,old,paths)==old,'Restored v1 record exact '+rid)
    check(p1['quality']['missing_fields']==[v for v in old['quality']['missing_fields'] if v!=stale],'Only stale audit gap removed '+rid)
    check(new['quality']['requested_tasks']==[],'No requested training tasks '+rid)
    check(new['collection']=='reviewed_literature' and new['quality']['review_status']=='source_reviewed','Review promotion '+rid)
    check(sha(C/(rid+'.json'))==entry['original_sha256'] and sha(Q/'records'/(rid+'.json'))==entry['promoted_sha256'],'Record manifest binds before/after '+rid)
    roles[new['reader_role']]+=1
    check((new['reader_role']=='synthesis_route')==(rid in route_ids),'Three specific QD/MSC routes '+rid)
    d2=diff(p1,new)
    if rid in {'evans-2010-species9-crystallization','evans-2010-molecular9-structure'}:
        check([d[0] for d in d2]==['/structure_assets'],'Only source-model link added '+rid)
        st=new['structure_assets'];check(len(st)==1 and st[0]['role']=='measured_sample' and st[0]['eligible_as_measured_label'] is False,'Molecular measured sample but no training label '+rid)
        expected_sample='species9-crystallization' if rid.endswith('crystallization') else 'species9-cif'
        check(st[0]['sample_id']==expected_sample and any(v['sample_id']==expected_sample for v in new['products']),'Molecular sample ID resolves '+rid)
        check('not a CdSe/PbSe quantum dot' in st[0]['description'] and '20H' in st[0]['description'] and 'not the original CIF' in st[0]['description'],'Explicit model limits '+rid)
        check(st[0]['url']=='/assets/chemical-registry/models/evans2010-species9-reference-3d.json','Exact qualified model URL '+rid)
    else:check(p1==new,'Other v2 record unchanged '+rid)
check(roles==Counter(synthesis_route=3,supporting_procedure=13,contextual_observation=16),'3/13/16 record categories')
old=read(R/'evans2010.json');reader=read(Q/'reader/evans2010.json');reader_ds=diff(old,reader)
top={'/audit_details','/coverage_status','/independent_audit','/presentation_gates','/publication_status','/review_state','/source_review_promoted','/training_note'}
for p,a,b in reader_ds:
    allowed=p in top or re.fullmatch(r'/(equations|figures|schemes|source_notes|tables)/\d+/reviewed',p) or re.fullmatch(r'/recipe_inventory/\d+/(gaps|status)',p)
    check(allowed,'Reader delta permitted '+p)
    if p.endswith('/reviewed'):check(b is True,'Reader source-review flag '+p)
    if p.endswith('/gaps'):check(b==[v for v in a if v!=stale],'Reader only stale audit gap removed '+p)
    if p.endswith('/status'):check(b=='source_reviewed','Reader recipe review flag '+p)
check(restore(reader,old,[d[0] for d in reader_ds])==old,'Reader scientific content exact after metadata restoration')
check(sha(Q/'reader/evans2010.json')==sha(P/'reader/evans2010.json'),'Reader identical v1 to v2')
check(reader['presentation_gates']=={'canonical_source_audit':True,'reader_source_audit':True,'molecular_bindings':True,'apparatus_bindings':True,'exact_qd_atomic_structure_binding':False,'site_integration':False,'browser_render':False,'publication':False},'Reader gates scoped to completed independent reviews')
check(reader['audit_details']['audit_sha256']==pm['source_audits'] and reader['audit_details']['source_conflicts_resolved'] is False and reader['audit_details']['training_promotions']==0,'Reader audit provenance and unresolved conflicts')
reg0=read(M/'registry-additions.json');reg=read(Q/'molecules/registry-additions.json');reg_ds=diff(reg0,reg)
for p,a,b in reg_ds:
    check(p=='/status' or re.fullmatch(r'/entries/\d+/(binding_approved|independentScientificAudit)',p),'Registry metadata-only delta '+p)
check(len(reg_ds)==101 and restore(reg,reg0,[d[0] for d in reg_ds])==reg0,'50 registry identities/graphs unchanged except status')
for entry in reg['entries']:check(entry['binding_approved'] is True and entry['published'] is False and entry['eligible_training'] is False,'Reference approval is not publication/training '+entry['id'])
b0=read(M/'revision-2/bindings-proposal.json');b=read(Q/'molecules/bindings-additions.json');b_ds=diff(b0,b)
for p,a,z in b_ds:
    check(p in {'/sourceRecordSha256','/status','/binding_approved'} or re.fullmatch(r'/bindingNotes/[^/]+/[^/]+/(binding_approved|independent_scientific_audit)',p),'Binding metadata-only delta '+p)
check(len(b_ds)==249 and restore(b,b0,[d[0] for d in b_ds])==b0,'123 molecular assignments and scoped captions unchanged')
check(b['published'] is False and b['eligible_training'] is False and b['binding_approved'] is True,'Bindings not publication/training approval')
check(set(b['sourceRecordSha256'])==set(records),'Promoted record-hash map covers all32')
slot_count=0
for rid,r in records.items():
    check(b['sourceRecordSha256'][rid]==sha(Q/'records'/(rid+'.json')),'Effective record hash '+rid)
    notes=b['bindingNotes'].get(rid,{})
    check(set(notes)=={m['id'] for m in r['materials']},'All actual material slots '+rid)
    for m in r['materials']:
        n=notes[m['id']];slot_count+=1
        check(n['canonical_record_sha256']==sha(C/(rid+'.json')),'Original audited canonical hash retained '+rid+'/'+m['id'])
        check(n['canonical_identity']=={k:m[k] for k in n['canonical_identity']},'Binding exact material identity '+rid+'/'+m['id'])
        check(b['recordBindings'][rid][m['id']]==n['registry_id'],'Assignment exact '+rid+'/'+m['id'])
check(slot_count==123,'123 bound material slots')
read(M/'stock-component-map.json');check(sum(len(s['components']) for r in records.values() for s in r['stocks'])==41,'41 unchanged stock components')
assets=pm['public_assets'];allow={}
critical=[C/(rid+'.json') for rid in records]+[R/'evans2010.json',M/'registry-additions.json',M/'revision-2/bindings-proposal.json']+[Path(x['source_path']) for x in assets]
for p in critical:check(str(p) in prior_bound and sha(p)==prior_bound.get(str(p)),'Actual baseline is bound to passed independent audit '+str(p.relative_to(E)))
for x in read(R/'reader-bindings-proposal.json')['original_assets']:allow[x['public_asset']]=x['sha256']
for x in read(M/'public-asset-proposal.json')['assets']:allow['assets/chemical-registry/'+x['registry_relative_path']]=x['sha256']
allow['evans2010-protocol.mjs']=bind(A/'evans2010-protocol.mjs')
check(len(allow)==109 and len(assets)==109,'Exactly109 qualified public assets')
check({x['public_path']:x['sha256'] for x in assets}==allow,'Public assets equal independent qualified allowlist')
check({p.relative_to(Q/'dist').as_posix() for p in (Q/'dist').rglob('*') if p.is_file()}==set(allow),'No extra public payload files')
for x in assets:
    check(bind(Q/'dist'/x['public_path'])==allow[x['public_path']]==bind(Path(x['source_path'])),'Asset unchanged from audited origin '+x['public_path'])
check(sum(x['kind']=='selected_original_scientific_crop' for x in assets)==25,'25 selected crops only')
public_json=[Q/'reader/evans2010.json',Q/'molecules/registry-additions.json',Q/'molecules/bindings-additions.json',Q/'record-structural-measurements.json']+list((Q/'records').glob('*.json'))
public_text=public_json+[p for p in (Q/'dist').rglob('*') if p.is_file() and p.suffix in {'.json','.mjs','.svg'}]
for p in public_text:
    t=p.read_text(encoding='utf-8-sig');check(not re.search(r'(?<![A-Za-z0-9])[A-Za-z]:[\\/](?!/)|file://|/Users/|\\Users\\|AppData|research-assets/incoming-paper-monitor',t),'No absolute private path '+p.relative_to(Q).as_posix())
check(not any(p.suffix.lower() in {'.pdf','.cif','.txt'} for p in (Q/'dist').rglob('*') if p.is_file()),'No original source binaries or raw-text files')
display=read(Q/'record-structural-measurements.json');expected={rid:set() for rid in records}
for section in old['reader_sections']:
    if section['id']!='structures':continue
    for item in section['items']:
        for link in item.get('canonical_links',[]):
            mt=re.match(r'^/measurements/(\d+)(?:/|$)',link['json_pointer'])
            if mt:expected[link['record_id']].add(records[link['record_id']]['measurements'][int(mt[1])]['id'])
check({k:set(v) for k,v in display.items()}==expected,'Display classification exactly follows audited structures reader links')
check(sum(len(v) for v in display.values())==3127 and all(len(v)==len(set(v)) for v in display.values()),'3127 unique record-scoped structural measurement IDs')
check(set(k for k,v in display.items() if v)=={'evans-2010-molecular9-structure','evans-2010-pbse-tem'},'Only molecular crystal and PbSe TEM contexts classified')
sys.path.insert(0,str(S/'scripts'));import dataset_lib,build_paper_reviews
for name in ['dataset_lib.py','schema_definition.py','build_paper_reviews.py','review_scope.py']:bind(S/'scripts'/name)
for rid,r in records.items():
    errs=dataset_lib.validate_record(r);check(not errs,'Current schema/semantics '+rid+(' '+repr(errs) if errs else ''))
    check(not any(v['eligible'] for v in dataset_lib.eligibility(r).values()),'Current training admission zero '+rid)
check(len(set(dataset_lib.build_groups(list(records.values())).values()))==1,'Single leakage-resistant source split')
proj=O/'validation-projection';(proj/'data/records').mkdir(parents=True,exist_ok=True)
for f in (Q/'records').glob('*.json'):shutil.copyfile(f,proj/'data/records'/f.name)
for x in assets:
    if x['kind']=='selected_original_scientific_crop':
        p=proj/'dist'/x['public_path'];p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(Q/'dist'/x['public_path'],p)
build_paper_reviews.ROOT=proj
errs=build_paper_reviews.validate(reader);check(not errs,'Current actual reader validation '+repr(errs))
model=read(Q/'dist/assets/chemical-registry/models/evans2010-species9-reference-3d.json')
check(sha(Q/'dist/assets/chemical-registry/models/evans2010-species9-reference-3d.json')==sha(M/'models/evans2010-species9-reference-3d.json'),'Molecular source coordinates unchanged')
for p,h in [(P/'package-freeze.json',V1),(Q/'package-freeze.json',V2)]:check(sha(p)==h,'Freeze remained unchanged '+p.parent.name)
out={'schema':'mattersyn.independent_promotion_delta_audit/1','created_at':datetime.now(timezone.utc).isoformat(),'status':'open_findings' if findings else 'passed','author_of_proposal':'/root','independent_auditor':'/root/norberg2004_extract','proposal_freeze_sha256':V2,'preserved_initial_proposal_freeze_sha256':V1,'scope':'Exact promotion/projection deltas against previously independently passed source, canonical/reader, molecules and apparatus. This audit does not freshly re-read every source fact or certify an installed Site, browser rendering or publication.','counts':{'records':32,'routes':3,'supporting_procedures':13,'observations':16,'operations':sum(len(r['operations']) for r in records.values()),'material_slots':slot_count,'stock_components':41,'registry_entries':50,'public_assets':109,'selected_source_crops':25,'chemical_assets':83,'apparatus_modules':1,'source_molecular_structure_links':2,'record_scoped_structural_measurement_ids':3127,'training_tasks_admitted':0,'exact_qd_structure_recipe_pairs':0,'checks':len(checks),'failed_checks':sum(not c['passed'] for c in checks)},'delta_summary':{'v1_records':'Exactly eight approved metadata paths per record; removing them restores every audited original scientific record.','reader':'109 review-status/gap metadata changes only; full prose, quantities, canonical pointers, source/sample links and selected-crop references unchanged.','registry':'101 approval/status changes only; all50 identities and asset references unchanged.','bindings':'249 metadata leaves only; all123 assignments/captions unchanged from effective molecule revision2. Original canonical hashes identify audited input; sourceRecordSha256 identifies effective promoted record.','v2':'Two existing molecular species9 structure references added, both non-training. Their record-hash map entries updated. Reader unchanged. The3127 structural-display IDs derive only from the audited structures section; they are record-scoped.'},'manual_scientific_scope':['Three QD/MSC route families remain separate from precursor preparation, distillation/control and analytical observations.','The v3 residual-pot/distillate distinction and all source conflicts remain unchanged.','Both new source-model links resolve to isolated molecular species9 products and the previously qualified asymmetric-unit model; calculated riding hydrogens and coordinate-transform limits are disclosed. No QD coordinate model or exact pair is asserted.','PbSe TEM structural display is source microscopy context, not an atomic model or inferred specimen join.','Selected figure/table/scheme crops and structured scientific quantities are allowed; original PDFs/SI/CIF, full-page scans and raw full-text caches are not projected.','Completed source/chemical/apparatus reviews do not imply mounted-browser or deployment approval.'],'gates_not_approved':['shared Site integration','mounted browser rendering','anonymous deployed website verification','new training task eligibility'],'findings':findings,'bound_files':sorted(bound.values(),key=lambda x:x['path'])}
(O/'promotion-delta-checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(O/'promotion-delta-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(O/'promotion-delta-audit.md').write_text('# Evans promotion/projection independent audit\n\nStatus: **'+out['status']+'**. Final proposal v2 freeze: `'+V2+'`. Initial v1 remains preserved.\n\n32 records retain all audited scientific quantities, protocols, missingness, source conflicts and specimen identities. Record categories remain 3 synthesis routes, 13 supporting procedures and 16 observations. No training task is admitted. Two explicitly scoped molecular species9 viewer links add the existing reviewed source-coordinate model; they do not create QD structures or measured training labels.\n\nThe projected109 assets are exactly25 selected source crops,83 qualified chemical assets and one apparatus module. No original document, complete page rendering, raw text file or absolute private path is included. The new3127-entry display classification is derived from exact audited reader links and scoped to two Evans records.\n\n'+str(len(checks))+' consistency/schema/provenance checks; '+str(len(findings))+' open findings. This is a metadata/projection audit using the prior independent source, canonical/reader and visual audits. Installed Site behavior, mounted browser review and deployment remain separate gates.\n'+('\nFindings: '+repr(findings) if findings else ''),encoding='utf-8')
print(json.dumps({'status':out['status'],'checks':len(checks),'findings':findings,'bound_files':len(bound),'audit_sha256':sha(O/'promotion-delta-audit.json')},ensure_ascii=False))
