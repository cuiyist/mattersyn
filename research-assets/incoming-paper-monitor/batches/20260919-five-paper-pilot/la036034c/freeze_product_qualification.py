from pathlib import Path
import json,hashlib,datetime
B=Path(__file__).resolve().parent;O=B/'visuals/products';C=B/'visuals/components'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
save=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if (O/'package-freeze.json').exists():raise RuntimeError('Already frozen; preserve previous boundary for any correction.')
author=read(O/'author-validation.json');preview=read(O/'preview-author-check.json')
assert not author['failures'] and not preview['failures']
inputs=dict(author['bound_inputs'])
for p,h in inputs.items():assert sha(Path(p))==h,p
source=read(B/'source-inventory.json')
for d in source['documents']:
 p=Path(d['original_path']);assert sha(p)==d['source_sha256'];inputs[str(p)]=sha(p)
views=[]
for n in ['contact-05.png','contact-06.png','contact-07.png']:
 p=C/'review'/n;inputs[str(p)]=sha(p);views.append(str(p))
visual={'source_id':'nagasaki2004','author':'/root/peng1998_reader_assets','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Author qualification only. All ten reused symbolic depictions were reread/viewed on these three existing component contact sheets; exact copied SVG hashes are retained. Both unchanged original SI figure PNGs were actually viewed individually. This does not approve the separate molecular package or its new models.','contact_sheets_actually_viewed':views,'originals_actually_viewed':[str(O/'originals/si-figure1.png'),str(O/'originals/si-figure2.png')],'checks':['SI TEM keeps both image fields, 50/20 nm bars and caption; no particle histogram or atomic reconstruction.','SI XRD retains original trace, sticks, axes and caption; no peak card/indexing or phase re-fit generated.','All ten copied symbols explicitly state no atomic coordinates/scale; no protein, chain, surface or lattice geometry.','Only si-xrd-cds has an author-derived phase label. All other context phase objects remain their canonical unknown values.','No CIF/XYZ/VESTA output or atomistic model is generated.'],'live_browser_layout_or_interaction_performed':False,'independent_product_audit':'pending'}
save(O/'author-visual-scope.json',visual)
for f in ['build_product_qualification.py','validate_product_preview.mjs','freeze_product_qualification.py']:inputs[str(B/f)]=sha(B/f)
outputs={str(p.relative_to(O)).replace('\\','/'):sha(p) for p in sorted(O.rglob('*')) if p.is_file() and p.name!='package-freeze.json'}
manifest={'schema':'mattersyn.private-product-qualification-freeze/1','source_id':'nagasaki2004','author':'/root/peng1998_reader_assets','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'author_proposal_frozen_pending_independent_audit','counts':author['counts']|{'preview_checks':preview['counts']['checks'],'frozen_output_files':len(outputs)},'atomic_reference_qualification':'No qualified CdS coordinate reference identified in inspected caches; no atomic assets created.','bound_inputs':inputs,'output_files':outputs,'independent_audit':'pending','publication_approved':False,'training_admission_approved':False,'site_changes':False}
save(O/'package-freeze.json',manifest)
print(json.dumps({'package_sha256':sha(O/'package-freeze.json'),'context_mapping_sha256':sha(O/'product-context-bindings-proposal.json'),'crystal_proposal_sha256':sha(O/'crystal-reference-proposal.json'),'counts':manifest['counts']},indent=2))
