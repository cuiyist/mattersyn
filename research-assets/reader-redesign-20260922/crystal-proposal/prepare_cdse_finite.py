"""Adapt the existing Figure 6 CdSe illustration; no new atomic geometry."""
from pathlib import Path
from collections import Counter
import json,hashlib,math,shutil,difflib
ROOT=Path(__file__).parent
SITE=Path(r'[local path redacted]')
SOURCE=SITE/'assets/cdse-structures'
OUT=ROOT/'cdse-finite-assets/crystal-references'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
manifest=read(SOURCE/'download-manifest.json')
xyzfile='cdse-3p5-by-3p0-nm-illustrative-cluster.xyz'
ciffile='cdse-3p5-by-3p0-nm-illustrative-cluster-vacuum.cif'
for name in [xyzfile,ciffile]:
 item=next(x for x in manifest['downloads'] if x['file']==name)
 assert sha(SOURCE/name)==item['sha256']
 (OUT/'illustrations').mkdir(parents=True,exist_ok=True)
 shutil.copyfile(SOURCE/name,OUT/'illustrations'/name)
shutil.copyfile(SOURCE/'download-manifest.json',OUT/'illustrations/cdse-figure6-original-download-manifest.json')
lines=(SOURCE/xyzfile).read_text().splitlines()
atoms=[]
for i,line in enumerate(lines[2:]):
 element,*values=line.split();x,y,z=map(float,values)
 atoms.append(dict(index=i,serial=i,element=element,elem=element,x=x,y=y,z=z,bonds=[],bondOrder=[],properties={'reference_only':True,'measured_sample':False,'source_context':'Murray1993-Figure6-illustrative-envelope'}))
assert int(lines[0])==len(atoms)==582
assert dict(Counter(a['element'] for a in atoms))=={'Se':294,'Cd':288}
lengths=[]
for i,a in enumerate(atoms):
 for j in range(i):
  b=atoms[j]
  distance=math.sqrt(sum((a[k]-b[k])**2 for k in ['x','y','z']))
  if a['element']!=b['element'] and 2.45<distance<2.75:
   a['bonds'].append(j);a['bondOrder'].append(1);b['bonds'].append(i);b['bondOrder'].append(1);lengths.append(distance)
assert len(lengths)==manifest['validation']['clusterBondCount']==1017
assert len({(a['element'],a['x'],a['y'],a['z']) for a in atoms})==582
caption='Figure 6 context illustration · nominal 3.5 × 3.0 nm ellipsoid, 582 lattice sites. This bulk-lattice crop is not a measured particle or the identified product of Method 1 or Method 2. Cd288Se294 is a geometric boundary artifact; ligands, stacking faults and surface reconstruction are omitted.'
scope='Separate Murray1993 Figure 6 context (printed p. 8710): the original TEM description motivates the nominal 3.5 × 3.0 nm envelope. Atom positions come from independent bulk CdSe COD 9016056 and the existing illustrative crop, not the TEM image. The source does not establish that this Figure 6 specimen is the product of the selected Murray method. No verified recipe-coordinate pair, measured surface stoichiometry or relaxed nanoparticle is asserted. The downloadable CIF uses an artificial 80 Å vacuum box, not the CdSe unit cell.'
id='cdse-murray-figure6-existing-illustrative-ellipsoid'
model=dict(id=id,name='Figure 6 context · illustrative CdSe ellipsoid',formula='CdSe',atoms=atoms,units='angstrom',periodic=False,representation='finite_illustrative_particle',training_eligible=False,measured_sample_structure=False,reference_only=True,sourceType='constructed_source_context_illustration',caption=caption,scope=scope,composition={'Cd':288,'Se':294},nominal_envelope_nm={'c_axis_diameter':3.5,'perpendicular_diameter':3.0},coordinate_extents_angstrom={k:[min(a[k] for a in atoms),max(a[k] for a in atoms)] for k in ['x','y','z']},source_context={'source':'Murray et al. 1993','doi':'10.1021/ja00072a025','figure':6,'printed_page':8710,'role':'TEM envelope context only; not measured atomic coordinates','recipe_product_link':'not established'},provenance={'existing_xyz':'assets/cdse-structures/'+xyzfile,'existing_xyz_sha256':sha(SOURCE/xyzfile),'existing_vacuum_cif_sha256':sha(SOURCE/ciffile),'existing_manifest_sha256':sha(SOURCE/'download-manifest.json'),'parent_bulk_reference':manifest['parentReference'],'coordinate_adaptation':'Read the existing exported XYZ without coordinate transformation. Bond guides use the same unlike-element 2.45–2.75 angstrom rule as the legacy buildCrystal viewer. No new crop, relaxation or physics was introduced.'})
model_file=OUT/'models'/(id+'.json');write(model_file,model)
delta=dict(id='cdse-wurtzite-cod-9016056',merge_instruction='Merge these finite-prefixed fields into the existing CdSe wurtzite entry. Keep its unit-cell assets, record_ids and bindingScopes. The reader helper below restricts the finite view to the two listed routes.',finiteRecordIds=['murray-1993-cdse-method1','murray-1993-cdse-method2'],finiteName='Figure 6 context · illustrative CdSe ellipsoid',finiteModelPath='models/'+model_file.name,finiteModelSha256=sha(model_file),finiteCifPath='illustrations/'+ciffile,finiteCifSha256=sha(OUT/'illustrations'/ciffile),finiteSourceType='constructed_source_context_illustration',finiteReferenceType='locally_constructed_ideal_reference',finiteSourceUrl='https://doi.org/10.1021/ja00072a025',finiteDisplayPolicy='independent_source_context_illustration',finiteScope=scope,finiteCaption=caption,finiteContextNote='This optional Figure 6 illustration is shared source context, not a method-specific product model. It is not the approximately 1.2 nm small-species structure.',finiteAdditionalDownloads=[{'label':'Original illustrative XYZ','path':'illustrations/'+xyzfile},{'label':'Original illustration provenance and validation','path':'illustrations/cdse-figure6-original-download-manifest.json'},{'label':'Parent bulk CdSe CIF','path':'9016056.cif'}])
write(ROOT/'cdse-finite-registry-fields.json',delta)
helper=r'''export function finiteReferencesForRecord(refs,r){
 return refs.filter(ref=>ref.finiteModelPath&&(!Array.isArray(ref.finiteRecordIds)||ref.finiteRecordIds.includes(r.record_id))).map(ref=>({
  ...ref,
  name:ref.finiteName||ref.name,
  sourceType:ref.finiteSourceType||ref.sourceType,
  referenceType:ref.finiteReferenceType||ref.referenceType,
  phaseScope:ref.finiteScope||ref.phaseScope,
  scope:ref.finiteScope||ref.scope,
  sample_context_note:ref.finiteContextNote||ref.sample_context_note,
  displayPolicy:ref.finiteDisplayPolicy||ref.displayPolicy,
  cifPath:ref.finiteCifPath||ref.cifPath,
  cifSha256:ref.finiteCifSha256||ref.cifSha256,
  sourceUrl:ref.finiteSourceUrl||ref.sourceUrl,
  additionalDownloads:ref.finiteAdditionalDownloads||ref.additionalDownloads
 }));
}
'''
source=(SITE/'reader-structures.mjs').read_text(encoding='utf-8-sig')
needle=" const refs=await crystalReferences(r),finite=refs.filter(x=>x.finiteModelPath);if(!host.isConnected)return;"
assert needle in source
proposed=source.replace('export async function mountReaderStructures(host,r,presentation={}){',helper+'export async function mountReaderStructures(host,r,presentation={}){').replace(needle," const refs=await crystalReferences(r),finite=finiteReferencesForRecord(refs,r);if(!host.isConnected)return;")
(ROOT/'cdse-finite-reader.patch').write_text(''.join(difflib.unified_diff(source.splitlines(True),proposed.splitlines(True),fromfile='a/dist/reader-structures.mjs',tofile='b/dist/reader-structures.mjs')),encoding='utf-8')
(ROOT/'cdse-finite-reader.proposed.mjs').write_text(proposed,encoding='utf-8')
(ROOT/'cdse-finite-reader-helper.mjs').write_text(helper,encoding='utf-8')
write(ROOT/'cdse-finite-validation.json',dict(status='pass',atom_count=582,composition={'Cd':288,'Se':294},bond_count=len(lengths),bond_range_angstrom=[min(lengths),max(lengths)],xyz_sha256=sha(SOURCE/xyzfile),copied_xyz_byte_identical=sha(SOURCE/xyzfile)==sha(OUT/'illustrations'/xyzfile),copied_cif_byte_identical=sha(SOURCE/ciffile)==sha(OUT/'illustrations'/ciffile),coordinates_copied_from_existing_xyz=True,new_crops_or_relaxations=False,source_context_separate_from_method_product=True,finite_route_ids=delta['finiteRecordIds'],site_modified=False,network_requests=0))
print('Wrote finite adapter, registry fields, restricted-reader helper/patch and validation.')
