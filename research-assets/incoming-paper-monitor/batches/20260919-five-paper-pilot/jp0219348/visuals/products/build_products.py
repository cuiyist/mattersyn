"""Private Heo public-view data projections; no source, Site or canonical writes."""
from pathlib import Path
from collections import Counter
import copy,csv,hashlib,json,math
P=Path(__file__).resolve().parent;H=P.parents[1];R=H/'si-reader-proposal';C=H/'canonical-proposal/v2';A=H/'structure-candidate';S=H.parents[4]/'recipe-atlas'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def ptr(d,p):
 for k in p.strip('/').split('/') if p else []:d=d[int(k)] if isinstance(d,list) else d[k]
 return d
assert not (P/'package-manifest.json').exists(),'Preserve frozen package.'
R.mkdir(exist_ok=True)
base=read(A/'average-model.json');audit=read(A/'independent-audit-addendum.json');si=read(H/'si-complete-candidate/all-reflections.json');sia=read(H/'si-complete-candidate/independent-audit.json')
checks=[]
def ck(ok,label):
 checks.append({'check':label,'passed':bool(ok)})
 if not ok:raise AssertionError(label)
ck(base['cif']['sha256']==sha(A/'heo2003-average-position-occupancy.cif'),'Audited CIF hash')
ck(sha(A/'average-model.json')=='990eb81a939e2c638dd519a5f64c12ba9184cabfbd4c9f72a9782f1b86af0d20','Audited average model hash')
ck(sia['status']=='passed_aggregate_reconciliation_with_two_preserved_source_sign_uncertainties','Passed SI aggregate scope')
notes=[
'This is a curator-transcribed average position and fixed-occupancy model from the source Tables 1–2, not an author-supplied CIF or a unique ordered atomic specimen.',
'The mixed T sites contain statistical Si 0.5 / Al 0.5 components. They are not assigned an ordered Si/Al pattern. The weighted average Si96Al96O384In66 differs from the nominal source In66Si100Al92O384.',
'The In(II) and In(IIa) positions are split alternatives with occupancies 25/32 and 1/32. Their approximately 0.721 Å separation is not a simultaneous pair of fully occupied atoms. Local occupation correlations are unknown.',
'All anisotropic displacement parameters are omitted. Source O(2), O(3) and O(4) tensors show site-symmetry inconsistencies; no silent tensor repair or thermal-ellipsoid reconstruction is made.',
'The printed coordinates give O(2)–In(IIa)–O(2) = 107.1602°, while Table 3 gives 111.7(20)°: a 4.5398° difference (2.27 reported ESDs). The other 22 Table 3 geometries agree within one ESD or rounding. A three-ESD screening threshold does not resolve this discrepancy.',
'The position/occupancy export does not reproduce charge-dependent scattering factors, anomalous-dispersion treatment or calculated reflection intensities. No sulfur, hydrogen, vacancies, ligands, oxide/sulfide residue or charge-compensation coordinates are supplied.',
'The synthesis-condition conflicts remain unresolved. Exact structure–recipe pairing, atomically ordered structures, DFT-input eligibility and training approval are false.'
]
groups=[]
for label in dict.fromkeys(x['source_label'] for x in base['fractionalSites']):
 sites=[x for x in base['fractionalSites'] if x['source_label']==label]
 groups.append({'label':label,'positions_per_cell':len(sites),'components':sites[0]['components'],'occupancy_sum':sites[0]['occupancy_sum']})
colors={'(Si,Al)':'#9166b0','O(1)':'#b6455f','O(2)':'#c66570','O(3)':'#d07d85','O(4)':'#dfa0a4','In(U)':'#167f91','In(I′)':'#1c9b99','In(II)':'#b07820','In(IIa)':'#d06a23'}
model={'schema':'mattersyn-source-average-view/1','source_id':'heo2003','model_id':'heo2003-average-position-occupancy','title':'In66-X · average periodic position and occupancy model',
 'source':{'doi':'10.1021/jp0219348','main_sha256':read(H/'source-inventory.json')['source_documents']['main']['sha256'] if 'main' in read(H/'source-inventory.json')['source_documents'] else '03e6f3be5375a0e2023a6850c1c6931904be8e3c85c37e0c30effdf6ecf73c01','locators':['Main Table 1: unit cell','Main Table 2, PDF p. 5 / printed p. 1124: final fixed positions and occupancies','Main Table 3: source geometry comparison'],'average_input_sha256':sha(A/'average-model.json'),'independent_geometry_audit_sha256':sha(A/'independent-audit.json'),'independent_addendum_sha256':sha(A/'independent-audit-addendum.json')},
 'cell':{'a':base['a'],'b':base['a'],'c':base['a'],'alpha':90,'beta':90,'gamma':90,'length_unit':'angstrom','a_raw':'24.942(4)'},'cellVectors':[[base['a'],0,0],[0,base['a'],0],[0,0,base['a']]],
 'spaceGroup':base['spaceGroup'],'spaceGroupNumber':227,'origin_choice':2,'coordinate_scope':base['coordinate_scope'],'fractionalSites':copy.deepcopy(base['fractionalSites']),'asymmetric_sites':copy.deepcopy(base['asymmetric_sites']),
 'groups':groups,'colors':colors,'weighted_counts':base['refinement_weighted_counts'],'distinct_positions':680,'species_components':872,'weighted_atoms':642,
 'nominal_source_formula':'In66Si100Al92O384','average_formula':'Si96Al96O384In66','limitations':notes,'depiction_policy':'One marker per averaged position; no bonds or random occupation. Marker color identifies a source site, not oxidation state. In(II)/In(IIa) layer controls only hide average positions; they do not select a physical microstate.',
 'unique_ordered_microstate':False,'exact_structure_recipe_eligible':False,'dft_input_eligible':False,'training_approved':False,'finite_particle':None,'surface_ligands':None}
for a,b in zip(base['fractionalSites'],model['fractionalSites']):ck(a==b,'Exact source-average position '+a['id'])
ck(len(model['fractionalSites'])==680,'680 distinct positions')
ck(sum(len(x['components']) for x in model['fractionalSites'])==872,'872 statistical species components')
weighted=Counter()
for s in model['fractionalSites']:
 for c in s['components']:weighted[c['element']]+=c['occupancy']
ck(dict(weighted)==base['refinement_weighted_counts'],'Weighted formula unchanged')
save(P/'heo2003-average-view.json',model)
(P/'heo2003-average-position-occupancy.cif').write_bytes((A/'heo2003-average-position-occupancy.cif').read_bytes())
cm=read(C/'canonical-record-manifest.json');bindings=[]
for rid,sid,relation in [('heo-2003-in66-route','final','Final source product; model is the downstream average diffraction outcome, not an exact synthesis target.'),('heo-2003-single-crystal-acquisition','final','Sealed diffraction specimen; position/occupancy average only.'),('heo-2003-average-structure','average-model','The final average model context, not earlier refinement iterations or an ordered microstate.')]:
 record=read(C/'canonical-drafts'/f'{rid}.json');i=next(i for i,x in enumerate(record['products']) if x['sample_id']==sid)
 bindings.append({'record_id':rid,'sample_id':sid,'canonical_json_pointer':f'/products/{i}','canonical_record_sha256':cm['record_hashes'][rid],'canonical_sample':record['products'][i],'relation':relation,'model_id':model['model_id'],'source_id':'heo2003','binding_approved':False,'exact_structure_recipe_eligible':False})
save(P/'product-viewer-proposal.json',{'schema':'mattersyn-private-source-average-product-proposal/1','source_id':'heo2003','status':'author_candidate_pending_distinct_review','model_path':'heo2003-average-view.json','model_sha256':sha(P/'heo2003-average-view.json'),'cif_path':'heo2003-average-position-occupancy.cif','cif_sha256':sha(P/'heo2003-average-position-occupancy.cif'),'bindings':bindings,'excluded_record_ids':[r for r in cm['record_hashes'] if r not in {b['record_id'] for b in bindings}],'exclusion_reason':'Do not assign final averaged coordinates to parent/reagent, exposed EPXMA, sputtered XPS, alternative refinement, reference-radius, topology or mechanistic contexts. They may link to the structural analysis as context without inheriting sample coordinates.','runtime_adapter':'heo2003-average-viewer.mjs','runtime_contract':'mountHeoAverage(host,record,{modelUrl,cifUrl}) returns false for unsupported source/record; call before generic reference display and avoid generic fully occupied-atom rendering for this entry.','binding_approved':False,'published':False})
save(P/'registry-entry-proposal.json',{'id':model['model_id'],'name':model['title'],'record_ids':[b['record_id'] for b in bindings],'scope':'Source-derived average refinement; not an independent bulk reference or ordered specimen. Requires the average-occupancy adapter.','sourceUrl':'https://doi.org/10.1021/jp0219348','sourceLinkLabel':'Source paper','spaceGroup':base['spaceGroup'],'modelPath':'heo2003-average-view.json','modelSha256':sha(P/'heo2003-average-view.json'),'cifPath':'heo2003-average-position-occupancy.cif','cifSha256':sha(P/'heo2003-average-position-occupancy.cif'),'viewerKind':'source_average_occupancy','mixedOccupancy':True,'mixedOccupancyLabel':'Statistical Si 0.5 / Al 0.5 on T sites','finiteModelPath':None,'requiresSourceSpecificAdapter':True,'binding_approved':False,'dft_input_eligible':False,'exact_structure_recipe_eligible':False})
# Public SI contains typed factual table data and locators, not source pages/private paths.
removed=[]
def public_value(x,path=''):
 if isinstance(x,dict):
  out={}
  for k,v in x.items():
   if k in ('source_path','original_crop_path','path','transcription_path'):
    removed.append(path+'/'+k);continue
   out[k]=public_value(v,path+'/'+k)
  return out
 if isinstance(x,list):return [public_value(v,path+'/'+str(i)) for i,v in enumerate(x)]
 return x
rows=[];mapping=[]
for i,row in enumerate(si['rows']):
 r={k:public_value(row[k],f'/rows/{i}/{k}') for k in ['row_id','source_sample_label','hkl','raw_cells','cells']}
 rows.append(r);mapping.append({'row_id':row['row_id'],'source_json_pointer':f'/rows/{i}','public_json_pointer':f'/rows/{i}','cell_ids':[c['cell_id'] for c in row['cells']]})
 for a,b in zip(row['cells'],r['cells']):
  for k in ['cell_id','raw_text','numeric_value','unit','unit_status','visible_digits','magnitude_value','signed_value_candidates','sign_status','raw_text_includes_editorial_annotation','editorial_annotation','uncertainty_note']:
   ck(a.get(k)==b.get(k),'Exact reflection scientific field '+a['cell_id']+'/'+k)
 ck(row['raw_cells']==r['raw_cells'] and row['hkl']==r['hkl'],'Raw row unchanged '+row['row_id'])
public={'schema':'mattersyn-public-source-reflections/1','source_id':'heo2003','doi':'10.1021/jp0219348','source_document_sha256':si['source_sha256'],'title':si['title_as_printed'],'source_table':'Supporting Table 1; SI PDF pages 1–14','counts':si['counts'],'rows':rows,'unresolved_cells':public_value(si['unresolved_cells'],'/unresolved_cells'),'aggregate_provenance':{'source_json_sha256':sha(H/'si-complete-candidate/all-reflections.json'),'separate_independent_audit_sha256':sha(H/'si-complete-candidate/independent-audit.json'),'audit_scope':sia['status'],'source_generation':2},'scientific_limits':['Raw tokens and source precision are retained; [sign_unresolved] is an editorial label, not printed source text. Two signed values remain null with their clear magnitudes and both sign candidates.','Negative observed values and the one zero remain unchanged. No clipping, rescaling, symmetry expansion, equivalence merging or index transformation is performed.','The o-like marker is transcribed but its meaning is not established by the supplied table. Source scale/physical units for squared factors and ESDs are unreported.','These are source-reported calculated and observed squared factors; this website does not recompute or fit them from its positions/occupancy-only model.','This typed table is not a new synthesis sample, exact structure–recipe training example, complete reproduction of the refinement or an ordered DFT input.'],'training_approved':False,'public_projection_independent_audit':'pending'}
text=json.dumps(public,ensure_ascii=False)
ck('C:\\' not in text and 'Users\\' not in text,'No local absolute paths in public SI JSON')
ck(len(rows)==1209,'All 1209 reflection rows retained')
numeric=[c for row in rows for c in row['cells'] if c['evidence']['column_key']!='marker']
ck(len(numeric)==7254 and sum(c['numeric_value'] is None for c in numeric)==2,'7254 numeric positions and exactly two null signs')
ck(sum(c['numeric_value']<0 for c in numeric if c['numeric_value'] is not None and c['evidence']['column_key']=='Fobs2')==137,'All 137 negative observed values retained')
save(R/'heo2003-reflections.json',public)
headers=['row_id','pdf_page','block','row_in_block','h','k','l','Fcal2_raw','Fobs2_raw','sigma_Fobs2_raw','marker_raw','Fcal2_numeric','Fobs2_numeric','sigma_Fobs2_numeric','Fcal2_sign_status','Fobs2_sign_status']
with (R/'heo2003-reflections.tsv').open('w',encoding='utf-8',newline='') as out:
 writer=csv.writer(out,delimiter='\t',lineterminator='\n');writer.writerow(headers)
 for r in rows:
  cells={c['evidence']['column_key']:c for c in r['cells']};ev=r['cells'][0]['evidence'];raw=r['raw_cells']
  writer.writerow([r['row_id'],ev['pdf_page'],ev['column_block'],ev['row_in_block'],raw['h'],raw['k'],raw['l'],raw['Fcal2'],raw['Fobs2'],raw['sigma_Fobs2'],raw['marker'],cells['Fcal2']['numeric_value'],cells['Fobs2']['numeric_value'],cells['sigma_Fobs2']['numeric_value'],cells['Fcal2'].get('sign_status','resolved'),cells['Fobs2'].get('sign_status','resolved')])
save(R/'private-projection-map.json',{'source_json_sha256':sha(H/'si-complete-candidate/all-reflections.json'),'public_json_sha256':sha(R/'heo2003-reflections.json'),'rows':mapping,'removed_private_metadata_fields':removed,'policy':'Only local paths and duplicate private audit file wrappers are excluded. All row/cell IDs, raw tokens, values, uncertainties, source locators/hashes and scoped audit status remain. No source-page images or whole SI PDF are included.'})
save(R/'reader-integration-proposal.json',{'source_id':'heo2003','data_path':'heo2003-reflections.json','data_sha256':sha(R/'heo2003-reflections.json'),'tsv_path':'heo2003-reflections.tsv','tsv_sha256':sha(R/'heo2003-reflections.tsv'),'adapter':'heo2003-reflection-viewer.mjs','reader_item_id':'inventory-supporting_tables-0','record_id':'heo-2003-refinement-comparison','relation':'Source reflection table context only; not per-row samples or recomputed intensities.','mount_contract':'mountHeoReflections(host,{dataUrl,tsvUrl})','features':['Search exact hkl or row ID','Source-page filter','All/negative/zero/unresolved filters','Pagination with source order preserved','Raw and numeric downloadable values with explicit null signs'],'binding_approved':False,'published':False})
# Readable source-derived 2D fallback thumbnail; no invented lattice or atom choices.
cx,cy,scale=290,275,9
project=lambda q:(cx+(q[0]-q[1])*.707*scale,cy+(q[0]+q[1])*.35*scale-q[2]*.85*scale)
svg=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 640"><rect width="720" height="640" fill="#f6fafc"/><text x="28" y="36" font-family="Arial" font-size="22" fill="#203c50">In66-X · average unit cell</text>']
for site in sorted(model['fractionalSites'],key=lambda q:sum(q['cartesian'])):
 x,y=project(site['cartesian']);label=site['source_label'];radius=2 if label.startswith('O') else 2.7 if label=='(Si,Al)' else 4
 svg.append(f'<circle cx="{x+40:.3f}" cy="{y+125:.3f}" r="{radius}" fill="{colors[label]}" fill-opacity="0.78"/>')
for axis in range(3):
 for b in [0,base['a']]:
  for c in [0,base['a']]:
   start=[b,c];start.insert(axis,0);end=start.copy();end[axis]=base['a'];x,y=project(start);u,v=project(end);svg.append(f'<path d="M{x+40:.3f},{y+125:.3f} L{u+40:.3f},{v+125:.3f}" stroke="#688898" stroke-width="1"/>')
svg.append('<text x="28" y="573" font-family="Arial" font-size="15" fill="#284758">Purple: mixed Si/Al sites. Colored In markers: source site labels.</text><text x="28" y="600" font-family="Arial" font-size="15" fill="#284758">Partial and split positions are averages, not simultaneous full atoms.</text></svg>')
(P/'heo2003-average-cell.svg').write_text(''.join(svg),encoding='utf-8')
save(P/'data-author-validation.json',{'status':'passed_data_projection_author_checks','author':'/root/peng1998_reader_assets','check_count':len(checks),'checks':checks,'source_model_sha256':sha(A/'average-model.json'),'source_cif_sha256':sha(A/'heo2003-average-position-occupancy.cif'),'source_si_sha256':sha(H/'si-complete-candidate/all-reflections.json'),'independent_review':'pending','runtime_visual_checks':'pending'})
print(json.dumps({'product_positions':680,'reflection_rows':len(rows),'checks':len(checks),'model_sha256':sha(P/'heo2003-average-view.json'),'si_json_sha256':sha(R/'heo2003-reflections.json'),'cif_sha256':sha(P/'heo2003-average-position-occupancy.cif')}))
