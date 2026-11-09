"""Finite L1/L2/L3/L5/L6 Reader identity plans. Pure: no I/O, network or RDKit.

Original registry entries/formulas are never changed. Component references do
not establish a whole salt, stock, hydration shell or solution structure.
"""
import copy
import hashlib
import json
import re
import unicodedata

import chemical_reference_identity as identity
from formula_equivalence import formula_equivalent, parse_formula

SCHEMA = 'MatterSyn-L-reference-identity-pins/1'
REASON = 'L_owner_named_reference'
COMPONENT_SCOPE = ('Independent named molecular components only. No geometry between ions or '
                   'components, hydration shell, metal coordination or solution speciation is assigned.')
DEFAULT_LINE = 'The form normally used is shown as a reference; the source does not state this form.'
HYDRATE_LINE = 'The acetate component is an independent reference; hydration and metal coordination are not assigned.'
HASH = re.compile(r'[a-f0-9]{64}')
MODEL = re.compile(r'models/[A-Za-z0-9][A-Za-z0-9._/-]*\.json')
HARD_KINDS = {'specimen','support','surface','composite','equipment','supported-particles',
              'analytical-data','material-context','sample-context','host','polymer'}
ENTITY = re.compile(r'\b(?:films?|wafer|substrates?|nanocrystals?|nanoparticles?|nanowires?|nanorods?|'
                    r'nanosheets?|quantum dots?|cores?|seeds?|specimens?|electrodes?|knudsen cells?|cells?|'
                    r'undefined|unknown|unnamed|pooled|formulation not restated)\b', re.I)
SUPPLIERS = r'(?:sigma(?:[- ]aldrich)?|aldrich|alfa aesar|strem|acros(?: organics)?|merck|tci)'
PURITY = r'(?:[<>≤≥~]?\s*\d+(?:\.\d+)?\s*%|technical(?:[- ]grade)?|analytical(?:[- ]grade)?|reagent[- ]grade|as printed|anhydrous)'
FORMULA_NAMES = {'InCl3':('Indium(III) chloride','InCl3'),
                 'HAuCl4':('Hydrogen tetrachloroaurate(III)','HAuCl4'),
                 'PbBr2':('Lead(II) bromide','PbBr2')}
DEFAULTS = {'ode':('1-Octadecene','1-octadecene',8217,'C18H36'),
            'octadecene':('1-Octadecene','1-octadecene',8217,'C18H36'),
            'octadecene (ode; positional isomer unspecified)':('1-Octadecene','1-octadecene',8217,'C18H36')}
SOLVENTS = {'water':('Water','H2O'),'ethanol':('Ethanol','C2H6O'),
            'methanol':('Methanol','CH4O'),'toluene':('Toluene','C7H8'),
            'hexane':('Hexane','C6H14'),'1-octadecene':('1-Octadecene','C18H36'),
            'ode':('1-Octadecene','C18H36'),'octadecene':('1-Octadecene','C18H36'),
            'oleylamine':('Oleylamine','C18H37N'),'oleic acid':('Oleic acid','C18H34O2'),
            'top':('Trioctylphosphine','C24H51P')}
ACETATE_BASES = {'cadmium':'Cd(C2H3O2)2','indium':'In(C2H3O2)3'}


def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,
                                     separators=(',',':'),allow_nan=False).encode()).hexdigest()


def clean_name(value):
    """Only finite nonidentity qualifiers and complete trailing abbreviations."""
    name = re.sub(r'\s+',' ',unicodedata.normalize('NFKC',str(value or ''))).strip()
    steps = []
    def replace(pattern, replacement, label, flags=re.I):
        nonlocal name
        after = re.sub(pattern,replacement,name,flags=flags).strip(' ,;')
        if after != name:steps.append(label);name=after
    # Parentheses are removed only when every token is an identified qualifier.
    qualifier = rf'(?:{PURITY}|{SUPPLIERS})'
    replace(rf'\(\s*{qualifier}(?:\s*[,;]\s*{qualifier})*\s*\)',' ','grade_or_supplier')
    replace(rf'(?<!\w){PURITY}(?!\w)',' ','grade_or_purity')
    replace(rf'(?:,\s*|\bfrom\s+){SUPPLIERS}\s*$','','supplier')
    replace(r'(?<!\w)\d+(?:\.\d+)?\s*(?:mM|M|mol\s*/\s*L)\b',' ','concentration',flags=0)
    replace(r'\b(indium|cadmium|lead|zinc|copper|iron|tin|gold|silver)\s+(iii|ii|iv|vi|v|i)\b',
            lambda m:m[1]+'('+m[2].upper()+')','roman_oxidation_state')
    # A chemical suffix such as (III), (E) or (R) is not an abbreviation.
    replace(r'\s+\(([A-Z][A-Z0-9-]{1,15})\)\s*$',
            lambda m:m[0] if m[1] in {'II','III','IV','VI','VII','VIII'} else '',
            'trailing_abbreviation',flags=0)
    name=re.sub(r'\s+',' ',name).strip(' ,;')
    return name,steps


def _hold(entry, reason):
    return {'kind':'hold','entry_id':entry.get('id'),'reason':reason,'ownerpart':None,'lookups':[]}


def _lookup(name, formula=None, *, eid='compound', cid=None, component=None, references=(),routes=(),source_cid=None):
    return {'id':eid,'name':name,'formula':formula,'pubchemCid':cid,
            'query_kind':'cid' if cid is not None else 'name',
            'query_field':'pubchem_CID' if cid is not None else 'chemical_name',
            'query':str(cid) if cid is not None else name,
            'reference_component_formula':component,'preferred_reference_ids':list(references),
            'allowed_routes':list(routes or ('molecule_reference','independent_component_references')),
            'source_cid_constraint':source_cid}


def _plan(entry, kind, part, reason, lookups, transformations=(), disclaimer=''):
    return {'kind':kind,'entry_id':entry.get('id'),'ownerpart':part,'reason':reason,
            'reported_name':entry.get('name'),'reported_formula':entry.get('formula'),
            'lookups':lookups,'transformations':list(transformations),
            'default_disclaimer':disclaimer,'component_scope':COMPONENT_SCOPE if kind=='independent_components' else ''}


def _formula_ok(entry, expected, hydrate=False):
    actual=entry.get('formula')
    if not actual:return True
    if hydrate:
        # Water removal is ONLY for the acetate-component plan. The general
        # formula_equivalent parser deliberately keeps hydrate differences.
        actual=re.sub(r'[.·]\s*(?:\d+)?H2O\s*$','',str(actual))
        # Ac/OAc means acetate ONLY inside the explicitly named Cd/In acetate
        # component plan. Never teach the general formula parser this alias.
        aliases = {
            ACETATE_BASES['cadmium']:{'CdOAc2','Cd(OAc)2','CdAc2','Cd(Ac)2'},
            ACETATE_BASES['indium']:{'InOAc3','In(OAc)3','InAc3','In(Ac)3'},
        }
        if actual in aliases.get(expected,set()):return True
    return formula_equivalent(actual,expected)


def _single_name_allowed(name):
    return bool(name and len(name)<=300 and not re.search(
        r'\b(?:stock|solutions?|mixtures?|formulations?|dispersions?|specimens?|substrates?|'
        r'precursors?|reagents?|solvent|medium|compound|material|identity|context|growth|synthesis|samples?|products?|unknown|undefined|unresolved|'
        r'unspecified|unidentified|various|polymer|blend|and|with|or)\b',name,re.I)
        and not re.search(r'[;\n\r]|\.(?:\s|$)',name))


def _explicit_mixture(entry):
    context=' '.join(str(x)for x in [entry.get('caption',''),*entry.get('limitations',[])])
    return bool(re.search(r'\b(?:mixture of|blend of|mixed with|contains? unspecified|unspecified components?)\b',context,re.I))


def _stock_lookup(name, entry, alone, index):
    acetate=re.fullmatch(r'(cadmium(?:\(II\))?|indium(?:\(III\))?) acetate',name,re.I)
    oleate=re.fullmatch(r'(lead|cadmium|indium|zinc)(?:\((?:II|III)\))? oleate',name,re.I)
    if acetate:
        metal=acetate[1].split('(')[0].casefold()
        if alone and (entry.get('pubchemCid')is not None or not _formula_ok(entry,ACETATE_BASES[metal],hydrate=True)):return None
        return _lookup('Acetate ion','C2H3O2-',eid='acetate-'+str(index),component='C2H3O2-',
                       references=['cadmium-acetate-dihydrate','friedfeld2019-indium-acetate-reference'])
    if oleate:
        metal=oleate[1].casefold();expected={'lead':'Pb(C18H33O2)2','cadmium':'Cd(C18H33O2)2','indium':'In(C18H33O2)3','zinc':'Zn(C18H33O2)2'}[metal]
        if alone and (entry.get('pubchemCid')not in(None,{'lead':6435829}.get(metal))or not _formula_ok(entry,expected)):return None
        return _lookup('Oleate ion','C18H33O2-',eid='oleate-'+str(index),component='C18H33O2-')
    if not _single_name_allowed(name):return None
    n,f=SOLVENTS.get(name.casefold(),(name,entry.get('formula')if alone else None));routes=[]
    if name.casefold()=='top-se':n='Trioctylphosphine selenide'
    if name in FORMULA_NAMES:
        n,f=FORMULA_NAMES[name]
        if f in {'InCl3','PbBr2'}:routes=['independent_component_references']
    elif re.fullmatch(r'(?:[A-Z][a-z]?\d*|\([^)]*\)\d*)+[xyz]?',name)and name.casefold()not in SOLVENTS:return None
    if name.casefold()in DEFAULTS:
        n,rid,cid,f=DEFAULTS[name.casefold()]
        return _lookup(n,f,eid='named-'+str(index),cid=cid,references=[rid],routes=['molecule_reference'])
    return _lookup(n,f,eid='named-'+str(index),source_cid=entry.get('pubchemCid')if alone else None,routes=routes)


def plan_identity(entry):
    """Runner filters L1 to old flat lookup_failed; the other parts are finite."""
    if not isinstance(entry,dict) or not entry.get('id'):return _hold({},'missing_registry_identity')
    raw=str(entry.get('name') or '').strip();name,steps=clean_name(raw);key=name.casefold()
    if entry.get('depictionKind') in HARD_KINDS or ENTITY.search(raw):return _hold(entry,'protected_entity_context')
    if not name or len(name)>300 or '\n' in raw or '\r' in raw:return _hold(entry,'unsafe_name')
    if re.search(r'\b(?:hexanes|octanes|mixed isomers|isomer mixture|polymer)\b',key):return _hold(entry,'ambiguous_or_polymeric')
    # Exact legacy Reader annotation on the fixed H6(a) hexane name only.
    # Plural hexanes, an actual mixture, a different CID/formula or a named
    # different isomer are not aliases of this independent n-hexane reference.
    if key=='hexane: source isomer unspecified':
        if identity.material_context_reason(entry) is not None or _explicit_mixture(entry) or entry.get('pubchemCid') not in (None,8058) or not _formula_ok(entry,'C6H14'):
            return _hold(entry,'annotated_hexane_identity_or_mixture_conflict')
        return _plan(entry,'single_compound','L6','fixed_H_hexane_reference',
                     [_lookup('n-Hexane','C6H14',cid=8058,references=['hexane'],routes=['molecule_reference'])],
                     [*steps,'fixed_H_hexane_reader_annotation'])
    # These defaults are explicitly qualified rather than asserted as source identity.
    default=DEFAULTS.get(key)
    amine_name=re.sub(r'[;,\s]+',' ',name).strip().casefold()
    exact_technical_annotation=re.sub(r'\s+',' ',raw).strip().casefold()=='oleylamine; stereochemistry and technical composition unspecified'
    if exact_technical_annotation and entry.get('depictionKind')!='formula':
        return _hold(entry,'technical_amine_annotation_context_conflict')
    technical_amine=bool((amine_name in {'oleylamine','oleylamine stereochemistry and mixture unresolved'}
                          or exact_technical_annotation) and re.search(r'%|technical|grade',raw,re.I))
    if default or technical_amine:
        value=default or ('Oleylamine','oleylamine',5356789,'C18H37N')
        target,rid,cid,formula=value
        symbolic_formula=str(entry.get('formula')or'').strip().casefold()
        alias_formula=symbolic_formula in ({'ode'}if formula=='C18H36'else{'ola','oam'})
        if entry.get('pubchemCid') not in (None,cid) or not (alias_formula or _formula_ok(entry,formula)):return _hold(entry,'default_identity_conflict')
        return _plan(entry,'single_compound','L3','qualified_field_default',
                     [_lookup(target,formula,cid=cid,references=[rid],routes=['molecule_reference'])],steps,DEFAULT_LINE)
    # Only the named acetate is shown. No hydration, cation arrangement or
    # coordination state is inferred from the independent acetate conformer.
    acetate=re.fullmatch(r'(cadmium(?:\(II\))?|indium(?:\(III\))?) acetate(?:,? (?:dihydrate|hydrate|hydration unspecified))?',name,re.I)
    if acetate:
        metal=acetate[1].split('(')[0].casefold()
        if entry.get('pubchemCid')is not None:return _hold(entry,'acetate_parent_CID_requires_own_compound_proof')
        if not _formula_ok(entry,ACETATE_BASES[metal],hydrate=True):return _hold(entry,'acetate_parent_formula_conflict')
        return _plan(entry,'independent_components','L2','named_acetate_component',
                     [_lookup('Acetate ion','C2H3O2-',eid='acetate',component='C2H3O2-',
                              references=['cadmium-acetate-dihydrate','friedfeld2019-indium-acetate-reference'])],steps,HYDRATE_LINE)
    # Exact named stocks only. Remove an existing presentation qualification,
    # never a source statement specifying additional unnamed components.
    stock_name=re.sub(r';\s*solution speciation unresolved\s*$','',name,flags=re.I)
    stock=bool(re.search(r'\s+(?:stock|solution)$',stock_name,re.I) or re.search(r'\s+in\s+',stock_name,re.I))
    if stock:
        parts=re.split(r'\s+in\s+',re.sub(r'\s+(?:stock|solution)$','',stock_name,flags=re.I),flags=re.I)
        if len(parts)>2:return _hold(entry,'ambiguous_stock_components')
        parent_text=re.sub(r'\s+(?:stock|solution)$','',parts[0].strip(),flags=re.I)
        parents=re.split(r'\s+(?:and|\+)\s+',parent_text,flags=re.I)
        solvents=re.split(r'\s+(?:and|\+)\s+',parts[1].strip(),flags=re.I)if len(parts)==2 else[]
        # H6(b)'s two explicit solvent abbreviations only, inside a named stock.
        # This is not a general slash splitter (core/shell and unknown blends
        # keep their existing holds). No component ratio is assigned.
        solvent_pairs={'oa/ode':['oleic acid','ODE'],'ode/oa':['ODE','oleic acid']}
        if len(solvents)==1 and solvents[0].casefold() in solvent_pairs:
            solvents=solvent_pairs[solvents[0].casefold()]
            steps=[*steps,'fixed_named_OA_ODE_stock_solvents']
        lookups=[];disclaimer=''
        for index,component_name in enumerate(parents+solvents):
            component_name=re.sub(r'\s+(?:stock|solution)$','',component_name.strip(),flags=re.I)
            alone=len(parents)==1 and not solvents
            lookup=_stock_lookup(component_name,entry,alone,index)
            if lookup is None:return _hold(entry,'stock_component_not_named_or_identity_conflict')
            lookups.append(lookup)
            if component_name.casefold()in DEFAULTS or component_name.casefold()=='oleylamine'and re.search(r'%|technical|grade',raw,re.I):disclaimer=DEFAULT_LINE
        return _plan(entry,'independent_components','L5','explicit_named_stock_components',lookups,steps,disclaimer)
    if key=='squalane':
        if _explicit_mixture(entry):
            return _hold(entry,'single_name_has_explicit_mixture_evidence')
        if entry.get('formula') and not _formula_ok(entry,'C30H62'):
            return _hold(entry,'single_compound_identity_conflict')
        return _plan(entry,'single_compound','L6','exact_squalane_not_whole_context',[_lookup('Squalane','C30H62',source_cid=entry.get('pubchemCid'),routes=['molecule_reference'])],steps)
    fixed_formula=name in FORMULA_NAMES
    formula_query=None
    context_reason=identity.context_reason(entry)
    soft_context=entry.get('depictionKind')in identity.WHOLE_CONTEXT_KINDS-HARD_KINDS
    if not fixed_formula and context_reason is not None:
        formula_like=bool(re.fullmatch(r'(?:[A-Z][a-z]?\d*|\([^)]*\)\d*)+[xyz]?',name))
        if (context_reason=='whole_context' and soft_context and _single_name_allowed(name) and not formula_like
            and not _explicit_mixture(entry) and identity.unresolved_lookup_abbreviation(entry)is False):
            return _plan(entry,'single_compound','L6','exact_single_compound_context_lookup',
                         [_lookup(name,entry.get('formula'),source_cid=entry.get('pubchemCid'))],steps)
        return _hold(entry,'existing_identity_or_context_hold')
    if key=='top-se':name='Trioctylphosphine selenide';steps.append('owner_TOP_Se_identity')
    formula=entry.get('formula') or None
    if name in FORMULA_NAMES:
        formula_name=name
        name,expected=FORMULA_NAMES[name]
        if formula and not formula_equivalent(formula,expected):return _hold(entry,'formula_name_conflict')
        formula=expected;steps.append('fixed_unique_formula_name')
        # Distinct bounded formula-as-name query after the longer normalized
        # name returned404. Exact successful CID/connectivity/formula proof is
        # still required; no failed lookup is converted into a reference.
        if formula_name=='HAuCl4' and entry.get('pubchemCid') is None:
            formula_query='HAuCl4';steps.append('fixed_unique_formula_as_name_query')
    elif (parse_formula(name) is not None and re.fullmatch(r'[A-Za-z0-9().+·-]+',name)
          or re.fullmatch(r'(?:[A-Z][a-z]?\d*|\([^)]*\)\d*)+[xyz]?',name)):
        return _hold(entry,'formula_name_not_fixed')
    routes=['independent_component_references']if fixed_formula and formula in {'InCl3','PbBr2'}else[]
    lookup=_lookup(name,formula,cid=entry.get('pubchemCid'),routes=routes)
    if formula_query is not None:lookup['query']=formula_query
    return _plan(entry,'single_compound','L1','bounded_normalized_name',[lookup],steps)


def eligible_owner_scope(entry, old_reference, plan=None):
    """Selection only: never a broad retry of all historical flat reasons."""
    plan=plan or plan_identity(entry)
    if plan.get('kind')=='hold' or not isinstance(old_reference,dict) or old_reference.get('route')!='flat':return False
    if plan['ownerpart']=='L1':return old_reference.get('reason')=='lookup_failed'
    if plan['ownerpart']=='L6':return old_reference.get('reason')=='whole_context'
    return plan['ownerpart'] in {'L2','L3','L5','L6'}


def field_default_qualification(entry, reference=None):
    """Qualification only; never creates/changes an existing reference route."""
    plan=plan_identity(entry)
    if plan.get('ownerpart')!='L3' or plan['kind']=='hold':return None
    if reference is None:
        if not entry.get('model3dPath'):return None
        route={'route':'existing_molecule','model3dPath':entry['model3dPath'],
               'model3dSha256':entry.get('assetHashes',{}).get('model3dPath')}
        if not _model_ref(route):return None
    else:
        if reference.get('route')!='molecule_reference' or not _model_ref(reference):return None
        if reference.get('referenceOnly')is not True or reference.get('trainingEligible')is not False:return None
        route=reference
    return {'source_entry_sha256':digest(entry),'reference_sha256':digest(route),'qualification':DEFAULT_LINE}


def qualify_registry_for_reader(registry, overlay):
    mapping=overlay.get('lFieldQualifications',{})
    if not isinstance(mapping,dict):raise ValueError('L field qualifications must be an identity mapping')
    entries={e['id']:e for e in registry['entries']}
    for eid,value in mapping.items():
        expected=field_default_qualification(entries[eid],overlay.get('entries',{}).get(eid))if eid in entries else None
        if expected is None or value!=expected:
            raise ValueError('L field-default qualification identity/reference differs')
    if not mapping:return registry
    return {**registry,'entries':[{**e,'readerFieldDefaultQualification':DEFAULT_LINE}if e['id']in mapping else e for e in registry['entries']]}


def normalized_lookup_entry(entry, plan, index=0):
    if plan!=plan_identity(entry) or plan.get('kind')=='hold':raise ValueError('No exact admitted identity plan')
    lookup=plan['lookups'][index]
    # Deliberately minimal temporary DTO: no conflicting inherited CID or
    # whole-context declaration is laundered into this independent reference.
    return {'id':entry['id']+'--L-'+lookup['id'],'name':lookup['name'],
            'formula':lookup['formula'],'pubchemCid':lookup['pubchemCid'],
            'depictionKind':'formula','model3dPath':None}


def registry_group_reference(lookup, registry_id, entries, reference_index=None):
    """Select exact original reference bytes, including one named component."""
    target=entries[registry_id]
    if lookup['preferred_reference_ids'] and registry_id not in lookup['preferred_reference_ids']:raise ValueError('Wrong fixed reference')
    if lookup['reference_component_formula']:
        if not lookup['preferred_reference_ids']:
            parent_name=str(target.get('name')or'').strip().casefold()
            if lookup['reference_component_formula']!='C18H33O2-' or re.fullmatch(r'(?:lead|cadmium|indium|zinc) oleate(?: stock)?',parent_name)is None:
                raise ValueError('No fixed named-parent component identity')
        matches=[c for c in target.get('component3dModels',[]) if formula_equivalent(c.get('formula'),lookup['reference_component_formula'])]
        if len(matches)!=1:raise ValueError('No unique exact named component')
        return {'route':'independent_component_references','reason':'exact_registry_component',
                'referenceOnly':True,'trainingEligible':False,'component3dModels':[copy.deepcopy(matches[0])],
                'component3dScope':COMPONENT_SCOPE,'sourceUrls':copy.deepcopy(target.get('sourceUrls',[]))}
    source={'id':'lookup','name':lookup['name'],'formula':lookup['formula'],'pubchemCid':lookup['pubchemCid']}
    index=reference_index if reference_index is not None else identity.ReferenceIndex(entries.values())
    if index.entries.get(registry_id)!=target:raise ValueError('Stale reference index target')
    hit,reason=index.existing(source)
    if hit is None or hit['id']!=registry_id:raise ValueError('No unique exact normalized reference identity')
    if lookup['source_cid_constraint']is not None and target.get('pubchemCid')!=lookup['source_cid_constraint']:raise ValueError('Named reference and original CID conflict')
    if source['formula'] and target.get('formula') and not formula_equivalent(source['formula'],target['formula']):raise ValueError('Reference formula conflict')
    return identity.reference_from_existing(target,reason)


# Previously accepted H ligand asset: reuse does not rerun a failed ion query
# or describe the parent salt/stock as one molecule. The source URL names the
# original cadmium-oleate connectivity source, not a free-ion PubChem claim.
EXISTING_OLEATE_SOURCE = {
    'id':'nguyen2024-colossal-cdse-cds-acsnano4c06961-cadmium-oleate',
    'name':'Cadmium oleate','formula':'C36H66CdO4',
    'pubchemCid':None,'depictionKind':'formula',
}
EXISTING_OLEATE_MODEL = {
    'id':'h-reader-9fdc890972c4e6330b03','name':'C18H33O2-',
    'formula':'C18H33O2-',
    'model3dPath':'models/h-reader-9fdc890972c4e6330b03-3d.json',
    'model3dSha256':'9ca1e70d48a3aca580ebe0dfc4805712db856707e10b2d64627b4b763b28b0b2',
    'caption':'Computed illustrative conformer, not measured and not PubChem3D. No solvent, surface or unique conformational state is asserted.',
}


# One explicit L1 HAuCl4 case reuses only the accepted H hydrate's AuCl4-
# component. The hydrate's proton, three waters and formula count are omitted.
EXISTING_AUCL4_SOURCE = {
    'id':'sigman2004-auag-la035405m-identity-13',
    'name':'Hydrogen tetrachloroaurate(III) trihydrate',
    'formula':'HAuCl4·3H2O','pubchemCid':None,'depictionKind':'formula',
}
EXISTING_AUCL4_MODEL = {
    'id':'h-reader-dac633ec45bced30c4d6','name':'AuCl4-','formula':'AuCl4-',
    'model3dPath':'models/h-reader-dac633ec45bced30c4d6-3d.json',
    'model3dSha256':'06f986fadfb4f7363cb1c87bf2eb305f078cd791adfe5be738db37191a3327e5',
    'caption':'Computed illustrative conformer, not measured and not PubChem3D. No solvent, surface or unique conformational state is asserted.',
}


def _existing_aucl4_component_group(lookup, entries):
    expected=_lookup('Hydrogen tetrachloroaurate(III)','HAuCl4',eid='compound')
    if lookup.get('query') not in {'HAuCl4',expected['query']}:return None
    expected['query']=lookup['query']
    if lookup!=expected:return None
    source=entries.get(EXISTING_AUCL4_SOURCE['id'])
    if not isinstance(source,dict) or any(source.get(k)!=v for k,v in EXISTING_AUCL4_SOURCE.items()):
        raise ValueError('Existing named tetrachloroaurate source identity differs')
    return {
        'lookup':copy.deepcopy(lookup),'basis':'existing_named_component',
        'evidence':{
            'source_registry_identity':copy.deepcopy(EXISTING_AUCL4_SOURCE),
            'accepted_reference_sha256':'11b7a611c48dfff525cf47ef714043ef112b2a42a0fb4f7720912198fa842631',
            'model_bytes':2930,
            'scope':'Existing accepted AuCl4- component only; not a whole HAuCl4 molecule, hydrate geometry or a new free-ion PubChem claim.',
        },
        'reference':{
            'route':'independent_component_references','reason':'exact_existing_named_component',
            'referenceOnly':True,'trainingEligible':False,
            'component3dModels':[copy.deepcopy(EXISTING_AUCL4_MODEL)],
            'component3dScope':'Independent tetrachloroaurate anion only. No proton, water, hydration shell, relative-ion arrangement or solution speciation is assigned.',
            'sourceUrls':['https://pubchem.ncbi.nlm.nih.gov/compound/21863413'],
        },
    }


def existing_named_component_group(lookup, entries):
    """Two exact existing H components only; returns None for other queries.

    Model file size/hash and normal rights remain checked by the usual asset
    validator. No parent stoichiometry, metal, water or intercomponent geometry
    is transferred. This function is pure and performs no lookup/generation.
    """
    if not isinstance(lookup,dict):return None
    expected=_lookup('Oleate ion','C18H33O2-',eid=lookup.get('id'),component='C18H33O2-')
    if lookup!=expected:return _existing_aucl4_component_group(lookup,entries)
    source=entries.get(EXISTING_OLEATE_SOURCE['id'])
    if not isinstance(source,dict) or any(source.get(k)!=v for k,v in EXISTING_OLEATE_SOURCE.items()):
        raise ValueError('Existing named oleate source identity differs')
    return {
        'lookup':copy.deepcopy(lookup),'basis':'existing_named_component',
        'evidence':{
            'source_registry_identity':copy.deepcopy(EXISTING_OLEATE_SOURCE),
            'accepted_reference_sha256':'c7270c678ba4a2752456cece81bba00affc4bbae9f5db96d69215e9c0e242263',
            'model_bytes':18234,
            'scope':'Existing accepted oleate ligand only; not whole cadmium or lead oleate, solution speciation or a PubChem free-ion identity.',
        },
        'reference':{
            'route':'independent_component_references','reason':'exact_existing_named_component',
            'referenceOnly':True,'trainingEligible':False,
            'component3dModels':[copy.deepcopy(EXISTING_OLEATE_MODEL)],
            'component3dScope':COMPONENT_SCOPE,
            'sourceUrls':['https://pubchem.ncbi.nlm.nih.gov/compound/6437734'],
        },
    }


def _model_ref(value):
    return (isinstance(value,dict) and isinstance(value.get('model3dPath'),str)
            and MODEL.fullmatch(value['model3dPath']) is not None
            and not any(p in {'.','..'} for p in value['model3dPath'].split('/'))
            and HASH.fullmatch(str(value.get('model3dSha256',''))) is not None)


def compose_L_reference(entry, plan, groups):
    if plan!=plan_identity(entry) or plan['kind']=='hold' or len(groups)!=len(plan['lookups']):raise ValueError('Incomplete exact plan/groups')
    if any(g['reference'].get('route')not in q['allowed_routes']for q,g in zip(plan['lookups'],groups)):raise ValueError('Reference route differs from named chemical scope')
    if plan['kind']=='single_compound':
        result=copy.deepcopy(groups[0]['reference'])
        if result.get('route') not in {'molecule_reference','independent_component_references'}:raise ValueError('Not a molecular reference')
    else:
        components=[]
        for lookup,group in zip(plan['lookups'],groups):
            ref=group['reference']
            if ref.get('route')=='molecule_reference':
                values=[{'id':ref.get('id') or ref.get('referenceRegistryId') or lookup['id'],
                         'name':lookup['name'],'formula':lookup['formula'],'model3dPath':ref['model3dPath'],
                         'model3dSha256':ref['model3dSha256'],'caption':ref['caption']}]
            elif ref.get('route')=='independent_component_references':values=copy.deepcopy(ref['component3dModels'])
            else:raise ValueError('Stock cannot be one aggregate geometry')
            if lookup['reference_component_formula'] and any(not formula_equivalent(c.get('formula'),lookup['reference_component_formula']) for c in values):raise ValueError('Unrequested ligand/cation/water component')
            # A borrowed parent's formula count is not the source stock ratio
            # or another metal acetate's stoichiometry. Display one component.
            for c in values:c.pop('multiplicityInReferenceFormula',None)
            components.extend(values)
        unique={}
        for c in components:unique.setdefault((c['model3dPath'],c['model3dSha256']),c)
        result={'route':'independent_component_references','referenceOnly':True,'trainingEligible':False,
                'component3dModels':list(unique.values()),'component3dScope':COMPONENT_SCOPE,
                'sourceUrls':list(dict.fromkeys(u for g in groups for u in g['reference'].get('sourceUrls',[])))}
    result['reason']=REASON;result['lIdentityPlanSha256']=digest(plan)
    if plan['default_disclaimer']:
        result['caption']=' '.join(filter(None,[result.get('caption'),plan['default_disclaimer']]))
        result['limitations']=list(dict.fromkeys([*result.get('limitations',[]),plan['default_disclaimer']]))
    return result


def validate_L_reference(entry, reference, proof, entries, reference_index=None):
    errors=[];plan=plan_identity(entry)
    if plan['kind']=='hold':return ['L identity/context plan is held']
    if not isinstance(proof,dict) or proof.get('schema')!=SCHEMA or proof.get('entry_id')!=entry.get('id') or proof.get('source_entry_sha256')!=digest(entry) or proof.get('plan')!=plan:return ['L original identity/plan proof absent or stale']
    groups=proof.get('groups')
    if not isinstance(groups,list) or len(groups)!=len(plan['lookups']):return ['L exact query/reference group count differs']
    for lookup,group in zip(plan['lookups'],groups):
        if not isinstance(group,dict):errors.append('L malformed group');continue
        ref=group.get('reference',{})
        if group.get('lookup')!=lookup:errors.append('L query differs from finite plan')
        if group.get('basis')=='existing_registry':
            try:
                expected=registry_group_reference(lookup,group.get('registry_id'),entries,reference_index=reference_index)
                if ref!=expected:errors.append('L reused reference bytes/scope differ')
            except (KeyError,TypeError,ValueError):errors.append('L existing reference identity/component mismatch')
        elif group.get('basis')=='existing_named_component':
            try:
                expected=existing_named_component_group(lookup,entries)
                if expected is None or group!=expected:errors.append('L existing named component proof differs')
            except (KeyError,TypeError,ValueError):errors.append('L existing named component source differs')
        elif group.get('basis')=='pubchem_metadata':
            evidence=group.get('evidence',{})
            if (evidence.get('query_type')!=lookup['query_kind'] or evidence.get('query')!=lookup['query']
                or evidence.get('status')!='UNIQUE_CID_CONNECTIVITY_CANDIDATE'
                or type(evidence.get('cid'))is not int or evidence['cid']<=0
                or not HASH.fullmatch(str(evidence.get('cache_sha256','')))
                or evidence.get('source_url')!='https://pubchem.ncbi.nlm.nih.gov/compound/'+str(evidence.get('cid'))):errors.append('L exact normalized lookup proof invalid')
            if lookup['pubchemCid'] is not None and evidence.get('cid')!=lookup['pubchemCid']:errors.append('L fixed/source CID conflict')
            if lookup['source_cid_constraint']is not None and evidence.get('cid')!=lookup['source_cid_constraint']:errors.append('L named lookup and original CID conflict')
            if lookup['formula'] and not formula_equivalent(lookup['formula'],evidence.get('formula')):errors.append('L lookup formula conflict')
            if ref.get('route')=='molecule_reference' and not formula_equivalent(ref.get('formula')or ref.get('referenceFormula'),evidence.get('formula')):errors.append('L molecular reference formula differs from resolved identity')
        else:errors.append('L reference has no pinned identity basis')
        values=[ref]if ref.get('route')=='molecule_reference'else ref.get('component3dModels',[])if ref.get('route')=='independent_component_references'else[]
        if not values or not all(_model_ref(c) and c.get('caption') for c in values):errors.append('L reference route/model pin/caption invalid')
        if ref.get('referenceOnly')is not True or ref.get('trainingEligible')is not False:errors.append('L reference flags differ')
        if lookup['reference_component_formula'] and any(not formula_equivalent(c.get('formula'),lookup['reference_component_formula']) for c in values):errors.append('L named component formula differs')
    try:
        expected=compose_L_reference(entry,plan,groups)
        actual={k:v for k,v in reference.items()if k not in {'chemicalUseCount','buttonLabel'}}
        if actual!=expected:errors.append('L reference differs from exact composed proof')
        if proof.get('reference_sha256')!=digest(expected):errors.append('L composed reference pin differs')
    except (KeyError,TypeError,ValueError):errors.append('L reference composition invalid')
    return errors
