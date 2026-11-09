"""Pure finite owner-L4 reference selection. No I/O, lookup or geometry generation."""
import copy,re
from chemical_reference_identity import material_context_reason
from formula_equivalence import formula_equivalent
PREFIX='recipe-atlas/static/assets/crystal-references/'
REGISTRY=PREFIX+'registry.json'
FIXED={
 'CdO':('cdo-rocksalt-cod-9006671',225,{'cdo','cadmium oxide','cadmium(ii) oxide','cadmium ii oxide'}),
 'Na2S':('na2s-antifluorite-cod-9009064',225,{'na2s','sodium sulfide','sodium sulphide'}),
 'NaCl':('nacl-rocksalt-cod-9003308',225,{'nacl','sodium chloride'}),
 'KBr':('kbr-rocksalt-cod-9008650',225,{'kbr','potassium bromide'}),
 'CuI':('cui-sphalerite-cod-9013920',216,{'cui','copper iodide','copper(i) iodide','copper i iodide','cuprous iodide'}),
 'CdCl2':('cdcl2-layered-cod-9009125',166,{'cdcl2','cadmium chloride','cadmium(ii) chloride','cadmium ii chloride'}),
 'Se':('se-trigonal-cod-9012501',152,{'se','se powder','selenium','selenium powder','grey selenium','gray selenium','trigonal selenium','trigonal selenium powder'}),
}
def _literal_reference_for_entry(entry,admittedProof,crystalEntries):
 """Return one verified existing reference DTO, or None; never infer sample phase.

 The caller supplies the actual hash-bound Root admission proof, separate from
 the original H map. Only literal own compound names/formulas are selected.
 """
 if not isinstance(entry,dict)or material_context_reason(entry)or entry.get('depictionKind')in {'substrate','cell','electrode','matrix'}:return None
 name=re.sub(r'\s+',' ',str(entry.get('name','')).strip()).casefold()
 name=re.sub(r'\banhydrous\b','',name);name=re.sub(r'\s+',' ',name).strip()
 if re.search(r'\b(?:stock|solutions?|dispersions?|mixtures?|hydrates?|amorphous|red selenium|black selenium)\b',name):return None
 chosen=next(((formula,data)for formula,data in FIXED.items()if name in data[2]),None)
 if not chosen:return None
 formula,(refid,sg,_)=chosen
 own_formula=entry.get('formula')
 if own_formula and not formula_equivalent(own_formula,formula):return None
 for key in ['phase','polymorph','allotrope']:
  own=entry.get(key)
  if isinstance(own,dict):own=own.get('value')if own.get('status')=='reported'else None
  if own:return None # explicit own-phase routing remains with the existing path
 if not isinstance(admittedProof,dict)or admittedProof.get('schema')!='MatterSyn-L4-admitted-fixed-ambient-proof/1':return None
 proof=admittedProof.get('formulas',{}).get(formula)
 if not isinstance(proof,dict)or proof.get('reference_id')!=refid or proof.get('formula')!=formula or proof.get('space_group_number')!=sg:return None
 if proof.get('owner_authorized_ambient_default')is not True or proof.get('referenceOnly')is not True or proof.get('trainingEligible')is not False:return None
 rows=crystalEntries.values()if isinstance(crystalEntries,dict)else crystalEntries
 matches=[row for row in rows if row.get('id')==refid]
 if len(matches)!=1:return None
 ref=matches[0]
 if ref.get('formula')!=formula or ref.get('spaceGroupNumber')!=sg or ref.get('referenceOnly')is not True or ref.get('trainingEligible')is not False or ref.get('defaultForSample')is not False:return None
 if proof.get('registry_path')!=REGISTRY or not re.fullmatch('[a-f0-9]{64}',str(proof.get('registry_sha256',''))):return None
 if proof.get('cif_path')!=PREFIX+str(ref.get('cifPath'))or proof.get('model_path')!=PREFIX+str(ref.get('modelPath')):return None
 if proof.get('cif_sha256')!=ref.get('cifSha256')or proof.get('model_sha256')!=ref.get('modelSha256'):return None
 if any(type(proof.get(k))is not int or proof[k]<=0 for k in ['registry_bytes','cif_bytes','model_bytes']):return None
 return copy.deepcopy(ref)
def validate_l4_reference_binding(entry,reference_id,admittedProof,crystalEntries):
 """Normal overlay-validator hook; selection must still follow own-field guards."""
 selected=l4_reference_for_entry(entry,admittedProof,crystalEntries)
 if selected is None or selected['id']!=reference_id:raise ValueError('L4 reference binding lacks the exact admitted own-identity match')
 return True


# L late defaults share the already reviewed pure cleaner. Original entries and
# source constraints are always checked before the temporary name projection.
import chemical_L_identity as L_rules
S8_REASON='L_owner_elemental_sulfur_S8_reference'
S8_SCHEMA='MatterSyn-L4-S8-reference-proof/1'
S8_CAPTION=('Cyclooctasulfur (S8) is an independent reference for elemental sulfur; '
            'it is not a measured sample structure or a source-assigned allotrope.')
S8_NAMES={'s','s8','sulfur','sulphur','elemental sulfur','elemental sulphur',
          'sulfur powder','sulphur powder','cyclooctasulfur'}

def _original_default_guard(entry):
 if not isinstance(entry,dict)or material_context_reason(entry):return False
 if entry.get('depictionKind')in {'mixture','specimen','substrate','cell','electrode','matrix','polymer'}:return False
 raw=str(entry.get('name',''))
 if L_rules.ENTITY.search(raw)or re.search(r'\b(?:stock|solutions?|dispersions?|mixtures?|hydrates?|amorphous|polymeric|red selenium|black selenium)\b',raw,re.I):return False
 for key in ['phase','polymorph','allotrope']:
  value=entry.get(key)
  if isinstance(value,dict):value=value.get('value')if value.get('status')=='reported'else None
  if value:return False
 return True

def _clean_entry(entry):
 if not _original_default_guard(entry):return None
 raw=str(entry.get('name',''))
 # Percent is an explicit grade/concentration qualifier even when a source
 # label omits the separating space. No locant/formula digit is removed.
 spaced=re.sub(r'(?<=[A-Za-z)])(?=[<>≤≥~]?\d+(?:\.\d+)?\s*%)',' ',raw)
 name,steps=L_rules.clean_name(spaced)
 if spaced!=raw:steps=['purity_percentage_spacing',*steps]
 if not name:return None
 return {**entry,'name':name},steps

def l4_name_proof(entry,reference_id):
 cleaned=_clean_entry(entry)
 if not cleaned:return None
 temporary,steps=cleaned;name=re.sub(r'\s+',' ',temporary['name']).strip().casefold()
 selected=next(((formula,data)for formula,data in FIXED.items()if name in data[2]),None)
 if not selected:return None
 formula,(refid,sg,_)=selected
 if refid!=reference_id or entry.get('formula')and not formula_equivalent(entry['formula'],formula):return None
 return {'schema':'MatterSyn-L4-own-name-normalization/1','entry_id':entry.get('id'),
         'source_entry_sha256':L_rules.digest(entry),'reported_name':entry.get('name'),
         'cleaned_name':temporary['name'],'transformations':steps,'reference_id':refid}

def l4_reference_for_entry(entry,admittedProof,crystalEntries):
 cleaned=_clean_entry(entry)
 if not cleaned:return None
 selected=_literal_reference_for_entry(cleaned[0],admittedProof,crystalEntries)
 return selected if selected and l4_name_proof(entry,selected['id'])else None

def validate_l4_reference_binding(entry,reference_id,admittedProof,crystalEntries):
 selected=l4_reference_for_entry(entry,admittedProof,crystalEntries)
 if selected is None or selected['id']!=reference_id:raise ValueError('L4 normalized reference lacks original-scope/admitted identity')
 return True

def s8_plan_for_entry(entry):
 cleaned=_clean_entry(entry)
 if not cleaned:return None
 temporary,steps=cleaned
 if temporary['name'].strip().casefold()not in S8_NAMES:return None
 if entry.get('formula')and entry['formula']not in {'S','S8'}:return None
 lookup={'id':'S8-reference','name':'Cyclooctasulfur','formula':'S8','pubchemCid':None,
         'query_kind':'name','query_field':'chemical_name','query':'Cyclooctasulfur',
         'reference_component_formula':None,'preferred_reference_ids':[],
         'allowed_routes':['molecule_reference'],'source_cid_constraint':None}
 return {'kind':'s8_reference','ownerpart':'L4','reason':'explicit_elemental_S8_reference',
         'entry_id':entry.get('id'),'reported_name':entry.get('name'),
         'reported_formula':entry.get('formula'),'cleaned_name':temporary['name'],
         'transformations':steps,'lookups':[lookup],'reference_qualification':S8_CAPTION}

def s8_lookup_entry(entry,plan,index=0):
 if plan!=s8_plan_for_entry(entry)or index!=0:raise ValueError('Exact S8 reference plan required')
 return {'id':entry['id']+'--L-S8-reference','name':'Cyclooctasulfur','formula':'S8',
         'pubchemCid':None,'depictionKind':'formula','model3dPath':None}

def _s8_ring(smiles):
 atom=r'(?:S|\[S\])'
 return isinstance(smiles,str)and re.fullmatch(atom+r'(?P<ring>[1-9])(?:-?'+atom+r'){7}(?P=ring)',smiles)is not None

def compose_s8_reference(entry,plan,groups):
 if plan!=s8_plan_for_entry(entry)or len(groups)!=1:raise ValueError('Exact elemental S8 plan/group required')
 reference=groups[0]['reference']
 if reference.get('route')!='molecule_reference'or not formula_equivalent(reference.get('formula')or reference.get('referenceFormula'),'S8'):raise ValueError('Only the independent neutral S8 molecule is admitted')
 result=copy.deepcopy(reference);result['reason']=S8_REASON
 result['lSulfurPlanSha256']=L_rules.digest(plan)
 result['caption']=' '.join(filter(None,[result.get('caption'),S8_CAPTION]))
 result['limitations']=list(dict.fromkeys([*result.get('limitations',[]),S8_CAPTION]))
 return result

def validate_s8_reference(entry,reference,proof,entries,reference_index=None):
 plan=s8_plan_for_entry(entry)
 if plan is None:return ['S8 original elemental identity/context is not admitted']
 if not isinstance(proof,dict)or proof.get('schema')!=S8_SCHEMA or proof.get('entry_id')!=entry.get('id')or proof.get('source_entry_sha256')!=L_rules.digest(entry)or proof.get('plan')!=plan:return ['S8 original-entry/plan proof differs']
 groups=proof.get('groups')
 if not isinstance(groups,list)or len(groups)!=1:return ['S8 requires one exact independent reference group']
 group=groups[0];lookup=plan['lookups'][0];ref=group.get('reference',{});errors=[]
 if group.get('lookup')!=lookup:errors.append('S8 query differs from exact named reference')
 if group.get('basis')=='existing_registry':
  try:
   expected=L_rules.registry_group_reference(lookup,group.get('registry_id'),entries,reference_index=reference_index)
   if ref!=expected:errors.append('S8 existing identity/model/scope differs')
  except (KeyError,TypeError,ValueError):errors.append('S8 exact existing identity absent')
 elif group.get('basis')=='pubchem_metadata':
  e=group.get('evidence',{})
  if e.get('query_type')!='name'or e.get('query')!='Cyclooctasulfur'or e.get('status')!='UNIQUE_CID_CONNECTIVITY_CANDIDATE'or type(e.get('cid'))is not int or e['cid']<=0 or not re.fullmatch('[a-f0-9]{64}',str(e.get('cache_sha256','')))or e.get('source_url')!='https://pubchem.ncbi.nlm.nih.gov/compound/'+str(e.get('cid')):errors.append('S8 exact unique-CID metadata proof differs')
  if not formula_equivalent(e.get('formula'),'S8')or not _s8_ring(e.get('connectivity_smiles')):errors.append('S8 metadata is not one neutral eight-sulfur ring')
 else:errors.append('S8 identity basis absent')
 if ref.get('route')!='molecule_reference'or ref.get('referenceOnly')is not True or ref.get('trainingEligible')is not False:errors.append('S8 route/reference flags differ')
 if not L_rules._model_ref(ref)or not ref.get('caption'):errors.append('S8 exact model SHA/path/caption absent')
 if not formula_equivalent(ref.get('formula')or ref.get('referenceFormula'),'S8'):errors.append('S8 reference molecular formula differs')
 try:
  expected=compose_s8_reference(entry,plan,groups)
  if {k:v for k,v in reference.items()if k not in {'chemicalUseCount','buttonLabel'}}!=expected or proof.get('reference_sha256')!=L_rules.digest(expected):errors.append('S8 composed reference pin differs')
 except (KeyError,TypeError,ValueError):errors.append('S8 reference composition invalid')
 return errors
