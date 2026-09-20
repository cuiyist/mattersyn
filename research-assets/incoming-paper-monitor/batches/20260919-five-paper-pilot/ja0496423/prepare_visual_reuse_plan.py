"""Read-only registry matching for the next visual phase; no bindings admitted."""
from pathlib import Path
import json,hashlib,datetime as dt
P=Path(__file__).resolve().parent
S=P.parents[4]/'recipe-atlas'
reg_path=S/'dist/assets/chemical-registry/registry.json'
registry=json.loads(reg_path.read_bytes())
entries={e['id']:e for e in registry['entries']}
source=json.loads((P/'source-inventory.json').read_bytes())
reuse={'oleylamine':'oleylamine','oleic-acid':'oleic-acid','diol':'hexadecane-1-2-diol','dioctyl-ether':'dioctyl-ether','topo':'topo','water':'water','ethanol':'ethanol','hexane':'hexane','nitrogen':'nitrogen'}
rows=[]
for m in source['materials']:
 key=m['id'].removeprefix('gu2004-');candidate=reuse.get(key)
 row={'source_material_id':m['id'],'source_name':m['name_as_reported'],'role':m['role'],'candidate_registry_id':candidate,'status':'candidate_for_identity_and_asset_audit' if candidate else 'new_scientific_depiction_required','binding_approved':False}
 if candidate:
  e=entries[candidate]
  row.update(candidate_name=e['name'],candidate_formula=e['formula'],candidate_assets={k:e.get(k) for k in ['svgPath','model2dPath','model3dPath']},asset_hashes=e.get('assetHashes'))
 row['source_scope_note']=m.get('identity_notes')
 if key=='hexane':row['additional_note']='Existing asset is n-hexane; source says hexane. Verify accepted identity/alias or label as an illustrative solvent molecule without asserting solvent-isomer assay.'
 if key=='topo':row['additional_note']='Pure TOPO connectivity can illustrate the named molecule; actual reagent is technical90% grade with unspecified impurities. Keep grade and molecular idealization separate.'
 if key=='cadmium-chloride':row['additional_note']='Printed CdCl2 at80.5% has unspecified hydration/assay basis; no hydrate shell or corrected mass should be added.'
 if key=='sulfur':row['additional_note']='Source says elemental sulfur powder, not a measured S8 allotrope or monatomic gas. Label any molecular/allotrope illustration as a reference representation.'
 if key=='cadmium-acac':row['additional_note']='Depict verified ligand/connectivity context with explicit coordination-model provenance; source supplies no atomic precursor structure or hydration assignment.'
 rows.append(row)
data={'source_id':'gu2004','created_at':dt.datetime.now(dt.timezone.utc).isoformat(),'source_inventory_sha256':hashlib.sha256((P/'source-inventory.json').read_bytes()).hexdigest(),'registry_sha256':hashlib.sha256(reg_path.read_bytes()).hexdigest(),'registry_path':str(reg_path),'scope':'Private preparation for visual authoring; names/roles checked against supplied SI, candidate assets have not been independently validated or bound to records. No Site edit.','materials':rows,'candidate_reuse_count':sum(bool(r['candidate_registry_id']) for r in rows),'new_depiction_count':sum(not r['candidate_registry_id'] for r in rows),'product_visual_requirements':['Show FePt1 before sulfur addition, tentative isolation-damaged2/3 and final heterodimer4 as separate states.','Use supplied TEM/HRTEM/SAED originals for measured structure. Any FCCFePt/zinc-blendeCdS atomic model is illustrative; no measured CIF is supplied.','FePt2.5nm and CdS~3–4nm component dimensions are source reports; a chosen single display diameter and interface geometry must not look like a refined atomic nanocrystal.'],'protocol_visual_requirements':['Separate precursor dissolution/chelation/precipitation/filtration/recrystallization/vacuum drying from the one-pot synthesis.','Show heat/hold,cooling,sulfur addition,Cd precursor addition,crystallization,dewetting concept and purification with appropriate stage-specific scenes.','Keep the first pellet,clarified hexane dispersion and final pellet distinct; source boiling point remains qualitative.','Pressure,temperatures,durations and volumes must come from the canonical operation state; unknown reactor pressure,gas identity and centrifuge settings stay unknown.'],'published':False}
(P/'visual-reuse-plan.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'reuse_candidates':data['candidate_reuse_count'],'new_depictions_needed':data['new_depiction_count'],'site_modified':False}))
