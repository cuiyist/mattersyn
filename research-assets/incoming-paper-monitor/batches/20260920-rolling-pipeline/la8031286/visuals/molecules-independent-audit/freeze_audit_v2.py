from pathlib import Path
import json,hashlib,datetime,copy
A=Path(__file__).resolve().parent;V=A.parent/'molecules';D=V/'annotation-correction-v2';N=A.parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text('utf8'))
old=read(A/'independent-audit-v1.json');delta=read(A/'delta-checks-v2.json');consumer=read(A/'consumer-checks-v2.json');freeze=read(D/'package-freeze.json')
assert not delta['failures']and consumer['status']=='passed'and all(x['passed']for x in consumer['checks'])
bound={**old['bound_files'],**freeze['bound_files'],**delta['bound_files'],**consumer['bound_files']}
for p in [D/'package-freeze.json',A/'independent-audit-v1.json',A/'delta-checks-v2.json',A/'consumer-checks-v2.json',A/'check_delta_v2.py',A/'check_consumer_effective_v2.mjs',Path(__file__)]:bound[str(p)]=sha(p)
for p,h in bound.items():assert sha(p)==h,p
r=copy.deepcopy(old);r.update({'status':'passed','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'revision':'effective_annotation_v2','proposal_freeze_sha256':sha(D/'package-freeze.json'),'base_proposal_freeze_sha256':old['proposal_freeze_sha256'],'initial_audit_sha256':sha(A/'independent-audit-v1.json'),'check_count':old['check_count']+delta['check_count']+consumer['check_count'],'check_count_definition':'1817 initial executed checks included three manifestations of one finding; 533 bounded correction checks and 885 independently re-executed effective consumer checks all pass. No initial failure is erased.','initial_failed_checks_resolved':3,'failed_check_count':0,'open_findings':[],'effective_metadata_map':{'path':str(D/'effective-file-map.json'),'sha256':sha(D/'effective-file-map.json')},'effective_public_assets':{'path':str(D/'effective-public-assets.json'),'sha256':sha(D/'effective-public-assets.json')},'bound_files':bound})
r['findings'][0]['status']='resolved_in_preserved_annotation_overlay_v2'
r['findings'][0]['resolution']='Independently reconstructed expected corrected model and registry and deep-compared exact equality. Only the three false nitrate amine annotations are removed, the affected model hash and eight mirrored entry hashes update, and the asset allowlist selects the corrected model. All 169 original frozen files, all SVG/PNG/3D bytes, molecular graphs, canonical quantities and stock assignments are unchanged.'
r['manual_scopes'].append({'scope':'Final annotation-only delta','result':'Corrected model has three nitrate-resonance groups, one Ce formula ion and six water formula groups. Original TEA tertiary-amine annotation remains. All graph atoms/bonds/coordinates are identical. Exact effective registry/model and corresponding digest mirrors verified; existing visual preview review remains valid because all image bytes are unchanged.'})
r['manual_scope_count']=len(r['manual_scopes'])
r['downstream_gates']={'molecular_identity_and_reference_binding_audit':'passed','canonical_v2_byte_bridge':'passed','installed_site_binding_audit':'not_performed','mounted_browser_audit':'not_performed','publication':'not_approved_by_this_audit','training_and_exact_structure_pairing':'not_approved_by_this_audit'}
data=json.dumps(r,ensure_ascii=False,indent=2)+'\n'
for name in ['independent-audit-v2.json','independent-audit.json']:(A/name).write_text(data,'utf8')
md='''# Pati molecular independent audit — effective annotation revision 2

Status: **passed**, with no open findings.

Reviewed all 20 chemical identities, 45 canonical material slots, six stocks/twelve components, eight chemical graphs, six retained conformers and 32 preview panels. The unchanged 19-record canonical v2 receipt is explicitly bound.

The preserved initial finding was three nitrate N+ atoms incorrectly classified as tertiary amines. The final overlay removes only those annotations and updates dependent hashes. All original files, atom/bond/coordinate arrays, formulas, source quantities, stock assignments and SVG/PNG/3D assets remain unchanged. The actual TEA tertiary-amine group remains.

Executed checks: 1,817 initial checks (three manifestations of the resolved finding), 533 independent delta checks, and 885 repeated effective consumer checks, totaling 3,235. The consumer tests execute the actual current viewer with a minimal DOM and a 3Dmol data sink; they are not a mounted-browser/WebGL visual approval. All six contact sheets were actually viewed in the initial audit; image bytes are unchanged.

Effective proposal freeze: `35311cb254b6b9970a39f929a1e59380cd78cc1379927f245849aedeb5859c70`.

Use the annotation-correction-v2 effective-file-map and effective-public-assets map. The original freeze remains immutable. Exact inputs and thirteen manual scopes are recorded in the JSON. Website integration, browser, publication, training and exact structure-recipe gates remain separate.
'''
for name in ['independent-audit-v2.md','independent-audit.md']:(A/name).write_text(md,'utf8')
print(json.dumps({'status':r['status'],'path':str(A/'independent-audit-v2.json'),'sha256':sha(A/'independent-audit-v2.json'),'check_count':r['check_count'],'bound_files':len(bound)}))
