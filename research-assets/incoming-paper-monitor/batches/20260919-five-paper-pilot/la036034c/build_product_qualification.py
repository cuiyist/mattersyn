"""Private source-specific product qualification. No atomic coordinates are invented."""
from pathlib import Path
import json,hashlib,datetime,shutil,html
B=Path(__file__).resolve().parent
O=B/'visuals/products'
C=B/'visuals/components'
S=Path(r'[local path redacted]')
R=S/'dist/assets/crystal-references'
for d in [O,O/'originals',O/'svg',O/'reference-inputs']:d.mkdir(parents=True,exist_ok=True)
if (O/'package-freeze.json').exists():raise RuntimeError('Frozen product proposal exists; preserve it before an intentional correction.')
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
save=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
bound={}
def bind(p):bound[str(p)]=sha(p);return bound[str(p)]
checks=[]
def check(name,c):checks.append({'check':name,'passed':bool(c)})
for p in [R/'registry.json',S/'dist/crystal-viewer.mjs',C/'registry-additions.json',C/'package-freeze.json',B/'source-inventory.json',B/'source-facts.json',B/'canonical-record-manifest.json',B/'canonical-records-audit.json',B/'public-review-proposal/nagasaki2004.json',B/'reader-source-audit.json']:bind(p)
registry=read(R/'registry.json');save(O/'reference-inputs/crystal-registry-snapshot.json',registry)
inventory=[]
for e in registry['entries']:
 files=[]
 for key,hashkey in [('cifPath','cifSha256'),('modelPath','modelSha256'),('finiteModelPath','finiteModelSha256')]:
  if e.get(key):
   p=R/e[key];h=bind(p);check(e['id']+' '+key+' matches recorded digest',h==e[hashkey]);files.append({'path':str(p),'sha256':h,'field':key})
 inventory.append({'id':e['id'],'formula':e['formula'],'name':e['name'],'reference_type':e.get('referenceType','independent_reference'),'source_url':e.get('sourceUrl'),'eligible_for_nagasaki_CdS':e['formula']=='CdS','disposition':'Different chemical composition; not a CdS lattice. No element substitution permitted.','files':files})
check('Current registry has no CdS lattice entry',not any(x['eligible_for_nagasaki_CdS'] for x in inventory))
save(O/'cached-reference-inventory.json',{'source_id':'nagasaki2004','registry_path':str(R/'registry.json'),'registry_sha256':sha(R/'registry.json'),'entries':inventory,'exact_CdS_reference_count':0,'supplementary_cache_search':{'root':r'[local path redacted]','method':'rg --files for *.cif and CdS/unit/wurtzite filenames; visible retained structure caches inspected','result':'No CdS coordinate file identified in the accessible retained structure cache. CdSe, CdO, elemental Se, ZnO, Ir, InP, CsPbBr3, CoO, CoFe2O4, Si and PbSe files are different compositions.','limitations':'Runtime/package directories returned read-denied messages; no claim about arbitrary inaccessible files or sources outside these inspected caches.'},'network_reference_lookup_performed':False,'new_paper_downloads':False})
source=read(B/'source-facts.json');reader=read(B/'public-review-proposal/nagasaki2004.json')
components={x['id']:x for x in read(C/'registry-additions.json')['entries']}
records={}
for p in sorted((B/'canonical-drafts').glob('*.json')):records[read(p)['record_id']]=(p,read(p));bind(p)
audited=read(B/'canonical-records-audit.json')
# Snapshot every relevant source object verbatim; quantities and source conflicts are not re-authored here.
evidence=[]
for figure in reader['figures']:
 if figure['id'] not in {'nagasaki2004-si-figure1','nagasaki2004-si-figure2'}:continue
 p=B/'reader-assets'/Path(figure['public_asset']).name;bind(p)
 check(figure['id']+' matches audited reader original hash',sha(p)==figure['public_asset_sha256'])
 out=O/'originals'/p.name;shutil.copy2(p,out)
 evidence.append({'reader_figure':figure,'private_copy':'originals/'+p.name,'sha256':sha(out),'association':'Only the explicitly named canonical_sample_links carry specimen evidence. Display elsewhere only as a clearly labeled paper-level comparison, never as a measured outcome of the selected route.'})
save(O/'original-evidence-proposal.json',{'source_id':'nagasaki2004','assets':evidence,'all_copies_identical':True,'new_cropping_or_image_editing':False})
sample_ref={
 'biotin-cds-generic':'biotin-cds-specimen','abstract-size-context':'cds','cho-cds-representative':'cds',
 'cho-cds-low-amine':'cds','cho-cds-mid-amine':'cds','cho-cds-high-amine':'cds','figure2-series-context':'cds',
 'figure4-fret-series':'biotin-cds-specimen','figure6-response-series':'biotin-cds-specimen',
 'figure2-absorption-sample-unresolved':'uv-specimen','cho-cds-generic':'cds','biotin-cds-optical-context':'biotin-cds-specimen',
 'figure5-competition-series':'biotin-cds-specimen','figure5-bsa-series':'biotin-cds-specimen',
 'cho-cds-salt-challenge':'salt-cho-specimen','figure1-label-context':'cds',
 'no-polymer-control':'salt-no-polymer-specimen','peg-control':'salt-peg-specimen','pama-control':'salt-pama-specimen',
 'si-tem-grid':'si-tem-dispersion','si-xrd-cds':'si-xrd-cds-dispersion','zeta-series':'zeta-dispersion'}
contexts=[];excluded=[];used={}
for rid,(p,r) in records.items():
 for index,sample in enumerate(r['products']):
  key=rid+'::'+sample['sample_id'];ptr='/products/'+str(index)
  if sample['composition'].get('value')!='CdS':
   excluded.append({'record_id':rid,'sample_id':sample['sample_id'],'canonical_pointer':ptr,'canonical_composition':sample['composition'],'reason':'No CdS product geometry is assigned to a polymer-only or unassigned interpretation/source context.'});continue
  ref='nagasaki2004-'+sample_ref[sample['sample_id']]+'-reference';entry=components[ref]
  check(key+' reference is symbolic, not an atomic model',not entry.get('model3dPath') and not entry.get('model2dPath'))
  used[ref]=entry
  phase=sample['phase'];originals=[x['reader_figure']['id'] for x in evidence if any(y['record_id']==rid and y['sample_id']==sample['sample_id'] for y in x['reader_figure']['canonical_sample_links'])]
  measurements=[]
  for mi,m in enumerate(r['measurements']):
   if m['sample_id']==sample['sample_id'] and m['property'] in {'abstract_cds_size','band_gap_theory_derived_cds_size','reported_absorption_edge','upper_lower_tem_scale_bars'}:
    measurements.append({'canonical_pointer':'/measurements/'+str(mi),'measurement':m})
  if sample['sample_id']=='si-xrd-cds':
   caption='The authors assign hexagonal wurtzite CdS to the PEG/PAMA–CdS powder-XRD context. This diagram shows composition only. The source supplies no refined lattice parameters or atomic coordinates, and the current local cache has no qualified CdS unit-cell reference.'
  elif sample['sample_id']=='si-tem-grid':
   caption='The supplied TEM images show a PEG/PAMA–CdS deposit with 50 nm and 20 nm scale bars. The diagram has no calibrated particle diameter, lattice or polymer conformation. The functional end group and exact preparation/optical/XRD specimen links remain unresolved.'
  elif sample['sample_id']=='figure2-absorption-sample-unresolved':
   caption='The source reports a 467 nm absorption edge and a band-gap-theory-derived 4.8 nm size for this optical context. Those values do not establish a measured TEM distribution or the diameter of the SI XRD specimen. No atomic particle is constructed from the estimate.'
  elif sample['sample_id']=='abstract-size-context':
   caption='The abstract gives an approximate 5 nm CdS size. This summary is distinct from the 4.8 nm optical-model estimate and does not identify a biotin-specific TEM or XRD specimen. The symbol carries no numerical particle scale.'
  elif rid in {'nagasaki-2004-fret','nagasaki-2004-recognition-controls'}:
   caption='A symbolic biotin-PEG/PAMA–CdS donor reference within this separately labeled biological assay context. It is not a model of the entire protein mixture, dye loading, molecular conformation, particle size or crystal lattice. Assay controls are not new synthesis specimens.'
  else:
   caption='A source-labeled CdS composition or stabilization-context diagram. Its geometry, particle count and polymer arrangement are explanatory symbols, not measured dimensions, a unique experimental batch or atomic coordinates. The source does not assign the SI XRD phase to this exact context.'
  contexts.append({'record_id':rid,'sample_id':sample['sample_id'],'context_id':key,'canonical_pointer':ptr,'canonical_record_sha256':sha(p),'canonical_product':sample,'registry_id':ref,'private_svg':'svg/'+Path(entry['svgPath']).name,'depiction_kind':'symbolic_composition_reference','source_caption':caption,'canonical_phase':phase,'model_phase':None,'unit_cell_asset':None,'finite_atomic_asset':None,'cif_download':None,'vesta_download':None,'direct_original_figure_ids':originals,'associated_source_measurements':measurements,'binding_approved':False,'independent_audit':'pending','training_eligible':False})
check('All 22 CdS source contexts mapped exactly',len(contexts)==22 and len({x['context_id'] for x in contexts})==22)
check('Other six contexts explicitly excluded from CdS mapping',len(excluded)==6)
check('Only SI XRD carries the author-derived phase assignment',[x['sample_id'] for x in contexts if x['canonical_phase'].get('value')]==['si-xrd-cds'])
for e in used.values():
 p=C/e['svgPath'];bind(p);dst=O/'svg'/Path(e['svgPath']).name;shutil.copy2(p,dst)
 check(e['id']+' component SVG matches its frozen metadata',sha(p)==e['assetHashes']['svgPath'])
save(O/'reference-inputs/component-entry-snapshots.json',{'source_registry':str(C/'registry-additions.json'),'entries':list(used.values()),'qualification_state':'Component identity depictions are frozen author assets awaiting their separate scientific audit. This product proposal does not approve those assets by reuse.'})
save(O/'product-context-bindings-proposal.json',{'schema':'mattersyn.private-product-context-bindings/1','source_id':'nagasaki2004','contexts':contexts,'excluded_contexts':excluded,'scope':'Every product binding is record-plus-sample scoped. No record-level default may silently merge multiple contexts. Symbolic identity only; no crystal registry binding is approved.','publication_approved':False})
defaults={rid:contexts[[x['record_id'] for x in contexts].index(rid)]['registry_id'] for rid in ['nagasaki-2004-cho-cds','nagasaki-2004-biotin-cds','nagasaki-2004-tem','nagasaki-2004-xrd']}
save(O/'product-reference-proposal.json',{'scope':'Optional record-level overview only for four preparation/technique pages; the 22 precise context mappings and their captions remain authoritative. The abstract size context must still be separate on the biotin page. No implicit specimen joins.','recordBindings':defaults,'requires_context_caption_support':True,'publicationApproved':False,'bindingApproved':False})
atomic={'schema':'mattersyn.private-crystal-qualification/1','source_id':'nagasaki2004','status':'no_qualified_local_CdS_coordinate_reference','entries':[],'source_phase_evidence':records['nagasaki-2004-xrd'][1]['products'][0]['phase'],'source_phase_pointer':{'record_id':'nagasaki-2004-xrd','pointer':'/products/0/phase'},'source_structure_status':source['structure_status'],'missing_fields':['Nagasaki numerical unit-cell parameters and uncertainties','Nagasaki atom sites, fractional coordinates, occupancies or refinement','Locally retained independent CdS wurtzite reference CIF and primary provenance','Exact connection between SI XRD, SI TEM, optical estimate and each preparation/assay context'],'forbidden_substitutions':['CdSe or ZnO coordinates relabeled as CdS','Cubic CdS substituted for the author wurtzite assignment','A nominal 4.8 nm optical estimate used as a measured SI particle envelope','Invented PEG/PAMA/biotin geometry or surface coverage','Unidentified XRD reference sticks assigned a database card'],'current_delivery':{'original_TEM':True,'original_XRD':True,'symbolic_product_contexts':22,'unit_cell_model':False,'finite_atomic_model':False,'CIF_download':False,'VESTA_download':False},'future_qualification_requirements':['Obtain a primary CdS wurtzite structural reference with exact formula, citation and retained CIF bytes; review temperature/pressure, phase and occupancies. No assumption that this is the measured Nagasaki specimen.','Validate symmetry expansion, lattice units, finite coordinates, unique sites, element counts and periodic neighbors against original CIF; preserve original and clearly labeled expanded files.','Choose any finite illustrative envelope separately from measured source sizes and label it as a visualization choice. Do not construct ligand/protein surface coordinates.','Independently audit the new reference and sample-scope captions; then the site owner may integrate with unit-cell/extended-lattice controls and reference-only downloads.'],'independent_audit':'pending','publicationApproved':False,'trainingEligible':False}
save(O/'crystal-reference-proposal.json',atomic)
save(O/'implementation-proposal.json',{'source_id':'nagasaki2004','current_renderer':str(S/'dist/crystal-viewer.mjs'),'current_renderer_sha256':sha(S/'dist/crystal-viewer.mjs'),'observed_limits':['Source-group guard currently excludes nagasaki2004.','Product identity defaults are record-level and do not consume record-plus-sample context captions.','Absence of a crystal registry entry currently returns without a generic source-specific availability notice.'],'proposed_owner_changes':['Add Nagasaki to the allowed product-identity sources only after independent component/product approval.','Show a source-context selector using product-context-bindings-proposal.json; preserve canonical phase/status and source caption for the selected record-plus-sample. Record-level overview cards must not propagate phase or size.','Show the original SI TEM and XRD as their named structural contexts; on recipe pages explicitly say the exact structural sample join is unresolved.','Display the source-specific structure-availability note and omit CIF/VESTA/atomic controls while the qualified reference is absent.','Keep a distinct reference-only crystal section available for a future independently qualified CdS wurtzite CIF.'], 'changes_applied':False})
payload=json.dumps({'contexts':contexts,'originals':evidence},ensure_ascii=False).replace('</',r'<\/')
page=r'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Nagasaki 2004 · Product evidence</title><style>body{font:17px/1.6 system-ui;margin:0;background:#f6f9fb;color:#193b49}main{max-width:1160px;margin:auto;padding:35px}h1{font-size:38px}h2{font-size:25px}small{color:#526977}select{width:100%;padding:12px;font:inherit;background:white;border:1px solid #a9bdc6;border-radius:8px}article,.notice{background:white;border:1px solid #d3e0e6;padding:24px;border-radius:15px;margin:22px 0}.grid{display:grid;grid-template-columns:1fr 1fr;gap:24px}img{max-width:100%;max-height:650px;object-fit:contain}.tag{color:#226d70}pre{white-space:pre-wrap;font:15px/1.5 system-ui}a{color:#0a697c}button{padding:8px 14px;border:1px solid #a9bdc6;background:white;border-radius:6px;font:inherit}@media(max-width:700px){.grid{grid-template-columns:1fr}main{padding:20px}}</style><main><small>PRIVATE PROPOSAL · independent product/reference review pending</small><h1>Final structures</h1><p>Nagasaki et al. (2004), <em>Novel Molecular Recognition via Fluorescent Resonance Energy Transfer Using a Biotin-PEG/Polyamine Stabilized CdS Quantum Dot</em>.</p><p><a href="https://doi.org/10.1021/la036034c">Source DOI</a> · Supplied main article and matched supporting information</p><label for="context">Source specimen or study context</label><select id="context"></select><article><h2 id="title"></h2><div class="grid"><div><img id="diagram" alt="Symbolic composition reference"><p class="tag">Composition illustration · no atomic coordinates or scale</p></div><div><h3>Source scope</h3><p id="caption"></p><p id="phase"></p><pre id="measurements"></pre><p id="lineage"></p></div></div></article><section class="notice"><h2>Atomic structure availability</h2><p>The authors assign hexagonal wurtzite CdS to the powder-XRD context. No refined lattice parameters, atomic coordinates or CIF are supplied. No qualified CdS coordinate reference was found in the inspected local crystal cache, so unit-cell, finite atomic-particle and CIF/VESTA controls remain unavailable.</p><p>The 4.8 nm optical-model estimate, approximate 5 nm abstract summary and SI structural specimens remain separate. Neither CdSe nor ZnO coordinates are substituted.</p></section><h2>Original structural evidence</h2><p>These are source-defined SI specimens. Selecting another context does not establish that its sample is identical to either specimen.</p><div id="originals" class="grid"></div></main><script id="data" type="application/json">PAYLOAD</script><script>const d=JSON.parse(document.getElementById('data').textContent),select=document.getElementById('context');for(const c of d.contexts){const o=document.createElement('option');o.value=c.context_id;o.textContent=c.record_id+' · '+c.sample_id;select.append(o)}function render(){const c=d.contexts.find(x=>x.context_id===select.value);document.getElementById('title').textContent=c.sample_id.replaceAll('-',' ');document.getElementById('diagram').src=c.private_svg;document.getElementById('caption').textContent=c.source_caption;document.getElementById('phase').textContent=c.canonical_phase.value?'Source phase: '+c.canonical_phase.value+' ('+c.canonical_phase.status+').':'Phase: not assigned to this exact context.';document.getElementById('measurements').textContent=c.associated_source_measurements.map(x=>{const m=x.measurement,q=m.value;return m.property.replaceAll('_',' ')+': '+(q.approximate?'approximately ':'')+q.value+' '+(q.unit||'')+' ('+q.status+'). '+(q.qualifier||'')}).join('\n\n');document.getElementById('lineage').textContent='Exact physical batch, cross-technique specimen identity and atomic coordinates are not established.';}select.addEventListener('change',render);render();for(const x of d.originals){const a=document.createElement('article'),h=document.createElement('h3'),p=document.createElement('p'),l=document.createElement('a'),im=document.createElement('img'),n=document.createElement('p');h.textContent=x.reader_figure.label;p.textContent='Specimen: '+x.reader_figure.sample_scope;l.href=x.private_copy;l.target='_blank';im.src=x.private_copy;im.alt=x.reader_figure.label;l.append(im);n.textContent=x.reader_figure.caption_paraphrase+' Click to enlarge the unchanged original.';a.append(h,p,l,n);document.getElementById('originals').append(a)}</script></html>'''.replace('PAYLOAD',payload)
(O/'preview.html').write_text(page,encoding='utf-8')
check('Preview embeds exact 22 contexts',payload in page)
check('No atomic-coordinate or CIF asset is generated',not list(O.rglob('*.cif')) and not list(O.rglob('*.xyz')))
for p,h in bound.items():check('Frozen inspected input unchanged: '+p,sha(Path(p))==h)
save(O/'author-validation.json',{'source_id':'nagasaki2004','status':'passed_author_checks' if all(x['passed'] for x in checks) else 'findings','counts':{'source_products':28,'CdS_product_contexts':len(contexts),'excluded_non_CdS_contexts':len(excluded),'symbolic_identity_assets':len(used),'original_images':len(evidence),'qualified_coordinate_references':0,'checks':len(checks)},'checks':checks,'failures':[x for x in checks if not x['passed']],'bound_inputs':bound,'independent_product_reference_audit':'pending','live_browser_validation':'not performed'})
(O/'README.md').write_text('''# Nagasaki CdS product-reference qualification

The private preview exposes 22 distinct CdS product/measurement contexts and the two unchanged original SI structural figures. Six polymer-only or unassigned contexts are explicitly excluded from CdS geometry. Source-specific captions preserve the optical-size, abstract-size, TEM and XRD boundaries. Symbolic diagrams are reused as frozen component assets; their separate scientific approval remains pending.

No usable CdS coordinate reference was present in the nine-entry local crystal registry or the accessible retained CIF cache. The original paper provides an author wurtzite assignment but no numerical lattice parameters, sites or refined coordinates. `crystal-reference-proposal.json` therefore has no entries, no CIF download and no invented finite lattice. It lists the exact missing data and a future qualification path.

`product-context-bindings-proposal.json` is the sample-scoped mapping. `product-reference-proposal.json` only proposes four optional record-level overview cards; it cannot assign phase, size or SI specimen identity. `implementation-proposal.json` identifies the current renderer boundaries without editing Site files.

Open `preview.html` from a local preview server. Its context switcher and original-image links are real controls; live-browser testing and independent product/reference audit remain separate pending gates. Source PDFs, canonical records, the audited reader and shared registries are unchanged.
''',encoding='utf-8')
print(json.dumps({'output':str(O),'counts':read(O/'author-validation.json')['counts'],'failures':read(O/'author-validation.json')['failures']},ensure_ascii=False,indent=2))
