import json,hashlib,shutil
from pathlib import Path
OUT=Path(__file__).resolve().parent;L=OUT.parent.parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
manifest=json.loads((L/'canonical-proposal/v1/record-manifest.json').read_text(encoding='utf-8'))
records={r['record_id']:json.loads(Path(r['path']).read_text(encoding='utf-8')) for r in manifest['records']}
bindings=[]
for rid,sid,phase in [('lian-2021-bulk-a-route','bulk-a','A'),('lian-2021-bulk-b-route','bulk-b','B'),('lian-2021-bulk-characterization','bulk-a-crystal','A'),('lian-2021-bulk-characterization','bulk-b-crystal','B')]:
    record=records[rid];idx=next(i for i,p in enumerate(record['products']) if p['sample_id']==sid)
    entry=next(r for r in manifest['records'] if r['record_id']==rid)
    stem='lian2021-bulk-'+phase.lower()+'-non-h'
    bindings.append({'record_id':rid,'sample_id':sid,'phase':phase,'source_id':'lian2021','source_record_path':entry['path'],'source_record_sha256':sha(entry['path']),'product_pointer':f'/products/{idx}','product_snapshot':record['products'][idx],'model_public_path':'assets/crystal-references/'+stem+'.json','model_sha256':sha(OUT/(stem+'.json')),'cif_public_path':'assets/crystal-references/'+stem+'-partial.cif','cif_sha256':sha(OUT/(stem+'-partial.cif')),'binding_role':'source_linked_bulk_refinement_context','same_physical_batch_verified':False,'caption':'Published non-hydrogen coordinates for bulk '+phase+'. The source refinement is linked by compound identity, without establishing that its diffraction crystal is the same physical synthesis aliquot. Occupancies and hydrogen positions were not supplied. This is a partial table reconstruction, not an NC/film or DFT model.','requested_tasks':[],'eligible_as_measured_label':False,'atomic_training_eligible':False,'independent_approval':False})
excluded=[{'record_id':rid,'reason':'Outside the exact four bulk sample/refinement bindings; matching composition alone does not establish scope.'} for rid in records if rid not in {b['record_id'] for b in bindings}]
write(OUT/'product-bindings-proposal.json',{'schema':'mattersyn.lian_bulk_binding_proposal.v1','status':'private_author_proposal_pending_independent_audit','bindings':bindings,'excluded_records':excluded,'canonical_mutation_required':False,'promotion_note':'Mount the source-linked bulk context adapter without altering frozen products, structure_assets, eligibility or requested_tasks. Any future canonical display metadata is a separately audited promotion.'})
write(OUT/'canonical-record-snapshots.json',records)
deps=[L/'source-tables.json',L/'source-facts.json',L/'source-inventory.json',L/'package-freeze.json',L/'source-independent-audit/independent-audit-v2.json',L/'canonical-proposal/v1/package-manifest.json',L/'canonical-proposal/v1/record-manifest.json',L/'canonical-reader-independent-audit/independent-audit-v1.json',L/'public-review-proposal/v1/lian2021.json']+[Path(r['path']) for r in manifest['records']]
pdfs=[Path('[local path redacted]'+suffix+'.pdf') for suffix in ['', '_si_1']]
deps+=pdfs
assert sha(pdfs[0])=='4a351221c8398d31f804d2af3d9f8327931c43e6e275e481ce84d7a67522a692'
assert sha(pdfs[1])=='a98d80fda37e0d7fd148e5da33b318ba382dd179117613c80f04b01c52659bf4'
write(OUT/'input-bindings.json',{'bound_files':{str(p):sha(p) for p in deps},'source_documents_verified_unchanged':True,'frozen_inputs_modified':False})
public=[{'source':str(OUT/f),'target':target,'sha256':sha(OUT/f)} for f,target in [('lian2021-bulk-viewer.mjs','lian2021-bulk-viewer.mjs'),('lian2021-bulk-viewer.css','lian2021-bulk-viewer.css')]+[(f' lian2021-bulk-{p}-non-h{s}'.strip(),f'assets/crystal-references/lian2021-bulk-{p}-non-h{s}') for p in ['a','b'] for s in ['.json','-partial.cif']]]
write(OUT/'public-asset-proposal.json',{'status':'pending_independent_audit','files':public,'excluded':'Original PDFs/SI, full-page renders, private canonical snapshots, complete source payloads, local preview and vendor files are not proposed for publication.'})
vendor=OUT/'preview-vendor';vendor.mkdir(exist_ok=True)
old=Path('[local path redacted]')
for f in ['3Dmol-min.js','3Dmol-min.js.LICENSE.txt']:shutil.copyfile(old/f,vendor/f)
write(OUT/'preview-vendor-provenance.json',{'scope':'private preview only; integration uses existing shared viewer dependency','files':{str(old/f):{'sha256':sha(old/f),'copy_sha256':sha(vendor/f)} for f in ['3Dmol-min.js','3Dmol-min.js.LICENSE.txt']}})
print(json.dumps({'bindings':len(bindings),'excluded_records':len(excluded),'public_files':len(public),'dependencies':len(deps)}))
