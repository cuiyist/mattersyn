"""Pure chemical identity/context selection; no network, RDKit or I/O on import."""
import collections, copy, re, unicodedata, hashlib, json
from formula_equivalence import formula_equivalent, parse_formula

CORE_IDENTITY_SOURCE_SHA256 = '1ae5e3563d906fa093af61796d36ab6a195f08929fcd3b0b05530c08c2b56978'

COMPONENT_SCOPE = 'Independent molecular components only. No geometry between ions, crystal packing, hydration shell or solution speciation is assigned.'
FIXED_NAMES = {'hexane': 'hexane', 'n-hexane': 'hexane', 'ode': '1-octadecene', '1-octadecene': '1-octadecene', 'oa': 'oleic-acid', 'oleic acid': 'oleic-acid', 'ola': 'oleylamine', 'oleylamine': 'oleylamine', 'top': 'top', 'trioctylphosphine': 'top', 'tri-n-octylphosphine': 'top', 'topo': 'topo', 'trioctylphosphine oxide': 'topo', 'tri-n-octylphosphine oxide': 'topo'}
FIXED_NAMES.update({'octane': 'octane', 'n-octane': 'octane'})
FIXED_NAMES.update({'1-octadecene (ode)': '1-octadecene', 'oleic acid (oa)': 'oleic-acid', 'oleylamine (ola)': 'oleylamine', 'trioctylphosphine (top)': 'top', 'trioctylphosphine oxide (topo)': 'topo'})
# Exact bounded new-lookup codes without their own CID/formula/connectivity.
UNPROVEN_BARE_ABBREVIATIONS = frozenset(['achn', 'aibn', 'ano', 'apba', 'aptes', 'aptms', 'ctab', 'ctac', 'ddab', 'ddt', 'dmap', 'dmso', 'dotap', 'edta', 'f4-tcnq', 'fitc', 'gsh', 'meh-ppv', 'mps', 'mpts', 'nhs', 'nmp', 'np-5', 'oam', 'od', 'opa', 'opv', 'p3ht', 'pbg', 'pdda', 'pfbt', 'pmdeta', 'smcc', 'tdpa', 'teos', 'tga', 'tmaoh', 'toa', 'toab', 'tops', 'ttab', 'usy'])
TDPA_FULL_NAMES = {'tetradecylphosphonic acid (tdpa)', '1-tetradecylphosphonic acid (tdpa)'}
FIXED_NAMES.update({name:'tetradecylphosphonic-acid' for name in TDPA_FULL_NAMES})
STANDARD_ABBREVIATION_IDENTITIES = {'ctab': {'name': 'Cetyltrimethylammonium bromide', 'cid': 5974, 'formula': 'C19H42BrN', 'reference_sha256': '17da16cd7ece01c7fe0f603874673c410e169dac839f3f1ce793cd3737efad4f'}, 'dmso': {'name': 'Dimethyl sulfoxide', 'cid': 679, 'formula': 'C2H6OS', 'reference_sha256': 'fd203badea9b7ff8056717283dcdf0bba8f0be8ff5f756dadf53c3315f11afb6'}, 'gsh': {'name': 'Reduced L-glutathione', 'cid': 124886, 'formula': 'C10H17N3O6S', 'reference_sha256': 'a455d135d303ceb41f2c356b6c1149017a70757eb0f861032580968acba63ace'}, 'nmp': {'name': '1-Methyl-2-pyrrolidinone', 'cid': 13387, 'formula': 'C5H9NO', 'reference_sha256': '3361cbe5b512324a4266c11798dc01e065fd669bead738d8c7dbdaa47b30e4fe'}, 'aibn': {'name': 'Azobisisobutyronitrile', 'cid': 6547, 'formula': 'C8H12N4', 'reference_sha256': 'a92bf978ad96578fcd567a323fb54273a8db420007904967211c5c914c5f5e5c'}, 'dmap': {'name': '4-(Dimethylamino)pyridine', 'cid': 14284, 'formula': 'C7H10N2', 'reference_sha256': 'fd1197c0d83961eb62c9f7e09e2795de40b3f676dcf662b1f01080b977117d07'}, 'edta': {'name': 'Ethylenediaminetetraacetic acid', 'cid': 6049, 'formula': 'C10H16N2O8', 'reference_sha256': '466f6e1bbd29a7af2b0c1f433bb4614846a439b8543971c09a98600232967f90'}, 'toab': {'name': 'Tetraoctylammonium bromide', 'cid': 2734117, 'formula': 'C32H68BrN', 'reference_sha256': '59a47aaa64a6e074f52a4ae3933a135061d01669511905c1d4c22c7422e13f6a'}, 'ttab': {'name': 'Tetradecyltrimethylammonium bromide', 'cid': 14250, 'formula': 'C17H38BrN', 'reference_sha256': '76d846642c18cdedf0278dda8bfce2e137e5df93b43d3b88cc389cf7e1037687'}, 'aptes': {'name': '(3-Aminopropyl)triethoxysilane', 'cid': 13521, 'formula': 'C9H23NO3Si', 'reference_sha256': 'cde6cea876c854de59752b6f9c7f5fbb06ab7d28bb2f3e62be634513aaf81ee3'}, 'aptms': {'name': '(3-Aminopropyl)trimethoxysilane', 'cid': 83756, 'formula': 'C6H17NO3Si', 'reference_sha256': '7e45101e5ba3bba555ee9001035bce78d25b1d714d9ae20258f60d27e1758519'}, 'ctac': {'name': 'Cetyltrimethylammonium chloride', 'cid': 8154, 'formula': 'C19H42ClN', 'reference_sha256': 'a923ed2cf0a15f71d6500eeb2142eea1b62701e88307035b3ea9aed0ba3a3469'}, 'f4-tcnq': {'name': '2,3,5,6-Tetrafluoro-7,7,8,8-tetracyanoquinodimethane', 'cid': 2733307, 'formula': 'C12F4N4', 'reference_sha256': 'd1a750a142f66d7f477230c9fd7194941cda08eb06814c7f2d0c1205e8246a82'}, 'nhs': {'name': 'N-Hydroxysuccinimide', 'cid': 80170, 'formula': 'C4H5NO3', 'reference_sha256': 'a9a4e7feb317cb37173bc8878cc8ff96a6505bc543604a7359860c93d4160d83'}, 'pmdeta': {'name': 'N,N,N′,N′′,N′′-Pentamethyldiethylenetriamine', 'cid': 18196, 'formula': 'C9H23N3', 'reference_sha256': 'a2b07c048f86b1bb3a3ff7e9bf4f8d117877323e69b9172536ee9466026532e2'}, 'teos': {'name': 'Tetraethyl orthosilicate', 'cid': 6517, 'formula': 'C8H20O4Si', 'reference_sha256': '4a79a27fc4455193eecc6a8dc29bd847d3e75d640136739bfa5b2f95d455a2ab'}, 'tmaoh': {'name': 'Tetramethylammonium hydroxide', 'cid': 60966, 'formula': 'C4H13NO', 'reference_sha256': 'bf868f0bbd1e99b077ea4cd73ce4426c27135581eef77c3253d4ee2eaee7271f'}}

WHOLE_CONTEXT_KINDS = {'mixture', 'specimen', 'support', 'surface', 'composite', 'equipment', 'supported-particles', 'analytical-data', 'unresolved-identity', 'material-context', 'sample-context', 'host', 'material_identity', 'author_hypothesis', 'symbolic_context', 'symbolic_identity', 'context', 'identity_only', 'symbolic', 'polymer'}

def key(s):
    return re.sub('\\s+', ' ', unicodedata.normalize('NFKC', str(s)).strip()).casefold()

def rotatable(e):
    return bool(e.get('model3dPath') or e.get('component3dModels'))

def unresolved_lookup_abbreviation(e):
    name = str(e.get('name','')).strip()
    if (re.fullmatch('[A-Z][A-Z0-9-]{1,11}',name) is None and key(name) not in UNPROVEN_BARE_ABBREVIATIONS) or key(name) in FIXED_NAMES or key(name) in STANDARD_ABBREVIATION_IDENTITIES:
        return False
    if e.get('pubchemCid') is not None or e.get('formula') or e.get('model2dPath') or rotatable(e) or (e.get('provenance') or {}).get('smiles') or e.get('connectivitySmiles'):
        return False
    if any(alias != name and ' ' in alias and re.search('[a-z]{4}',alias) and not re.search('source|abbreviation|unreported|unspecified',alias,re.I) for alias in e.get('aliases',[])):
        return False
    # A formula explicitly written as the label is identity metadata; the exact
    # bounded collisions remain held even when their letters also parse as atoms.
    return key(name) in UNPROVEN_BARE_ABBREVIATIONS or parse_formula(name) is None

def material_context_reason(e):
    hard_kinds={'mixture','specimen','support','surface','composite','equipment','supported-particles','analytical-data','material-context','sample-context','host'}
    name=key(e.get('name',''))
    if e.get('depictionKind') in hard_kinds:
        return 'whole_context'
    # Purpose qualifiers do not change a defined reagent into its target specimen.
    entity_name=re.split(r'\b(?:for|used in|used as)\b',name,maxsplit=1)[0].strip()
    # Own entity wording only: no source-paper or product-phase inference.
    pattern=r'\b(?:films?|wafers?|substrates?|nanocrystals?|nanocrystalline|nanoclusters?|nanoparticles?|nanowires?|nanorods?|nanosheets?|nanoprisms?|microbeads?|aunps?|colloids?|colloidal|sols?|electrodes?|anodes?|cathodes?|contacts?|coatings?|grids?|knudsen cells?|heaters?|markers?|doped|functionalized|capped|modified|unannealed)\b|\bnano[- ]|\bas[- ](?:synthesized|prepared|grown|deposited)\b'
    if re.search(pattern,entity_name) or (' ' in entity_name and re.search(r'\b(?:qds?|ncs|nps)\b',entity_name)):
        return 'whole_context'
    return None

def context_reason(e):
    name = key(e.get('name', ''))
    entity_context=material_context_reason(e)
    if entity_context:
        return entity_context
    if unresolved_lookup_abbreviation(e):
        return 'unresolved_abbreviation'
    if name in TDPA_FULL_NAMES and e.get('depictionKind') in WHOLE_CONTEXT_KINDS:
        return 'whole_context'
    if re.search('\\b(?:hexanes|octanes)\\b|^octadecene$|\\b(?:mixed isomers|isomer mixture)\\b', name):
        return 'ambiguous_isomer'
    if name in {'octane', 'n-octane'} and e.get('depictionKind') in WHOLE_CONTEXT_KINDS - {'symbolic_context', 'unresolved-identity'}:
        return 'whole_context'
    if name in STANDARD_ABBREVIATION_IDENTITIES:
        if e.get('depictionKind') in WHOLE_CONTEXT_KINDS - {'symbolic_context','unresolved-identity'}:
            return 'whole_context'
        return None
    if name in FIXED_NAMES:
        return None
    if e.get('depictionKind') in WHOLE_CONTEXT_KINDS:
        return 'whole_context'
    if re.search('\\b(?:pvp|peg|pva|pdms|pei|polyethylene glycol|polyvinylpyrrolidone|polyvinyl alcohol|polymer)\\b', name):
        return 'undefined_identity'
    free_water_component = e.get('pubchemCid') == 962 and e.get('formula') == 'H2O' and re.match('^water(?:\\b|[- ])', name)
    entity_name = re.split(r'\b(?:for|used in|used as)\b', name, maxsplit=1)[0].strip()
    if not free_water_component and re.search(r'\b(?:mixtures?|formulations?)\b', entity_name):
        return 'whole_context'
    if not free_water_component and re.search('\\b(?:stock|solutions?|dispersions?|quantum dots?|nanocrystals?|nanoparticles?|specimens?|substrates?|wafer|pooled)\\b', name):
        return 'whole_context'
    if re.search('\\b(?:unspecified|undefined|unknown|not reported)\\b', name):
        return 'undefined_identity'
    return None

def identity(e):
    if e.get('pubchemCid') is not None:
        return ('CID', e['pubchemCid'])
    sm = (e.get('provenance') or {}).get('smiles') or e.get('connectivitySmiles')
    return ('smiles', sm) if sm else ('entry', e['id'])

def unqualified_bulk_hold(e):
    name = key(e.get('name', ''))
    formula = e.get('formula') or ''
    aliases = {'selenium': 'Se', 'sulfur': 'S', 'carbon': 'C', 'phosphorus': 'P', 'lead oxide': 'PbO', 'lead(ii) oxide': 'PbO', 'titanium dioxide': 'TiO2'}
    formula = formula or aliases.get(name) or (e.get('name') if e.get('name') in {'Se', 'S', 'C', 'P', 'PbO', 'TiO2'} else '')
    return formula in {'Se', 'S', 'C', 'P', 'PbO', 'TiO2'}

class ReferenceIndex:

    def __init__(self, entries):
        self.entries = {e['id']: e for e in entries}
        self.cids = collections.defaultdict(list)
        self.names = collections.defaultdict(list)
        for e in entries:
            if not rotatable(e):
                continue
            if e.get('pubchemCid') is not None:
                self.cids[e['pubchemCid']].append(e)
            for n in {key(e.get('name', '')), *(key(x) for x in e.get('aliases', []))} - {''}:
                self.names[n].append(e)

    @staticmethod
    def choose(rows):
        return sorted(rows, key=lambda e: (not bool(e.get('model3dPath')), bool(re.search('(?:19|20)\\d\\d', e['id'])), len(e['id']), e['id']))[0]

    def existing(self, e, resolved_cid=None):
        name = key(e.get('name', ''))
        cid = resolved_cid if resolved_cid is not None else e.get('pubchemCid')
        if name in FIXED_NAMES:
            hit = self.entries.get(FIXED_NAMES[name])
            if hit and rotatable(hit):
                if cid is not None and cid != hit.get('pubchemCid'):
                    return (None, 'identity_conflict')
                return (hit, 'owner_fixed_named_identity')
        if cid is not None and self.cids.get(cid):
            return (self.choose(self.cids[cid]), 'identical_CID')
        hits = self.names.get(name, [])
        formula_like = bool(re.fullmatch('(?:[A-Z][a-z]?\\d*)+', str(e.get('name', ''))))
        if hits and (not formula_like) and (len({identity(x) for x in hits}) == 1):
            if cid is not None and any((x.get('pubchemCid') != cid for x in hits)):
                return (None, 'identity_conflict')
            return (self.choose(hits), 'unique_exact_compound_name')
        return (None, None)

def reference_from_existing(target, reason):
    common = {'reason': reason, 'referenceRegistryId': target['id'], 'referenceName': target['name'], 'referenceFormula': target.get('formula'), 'referenceOnly': True, 'trainingEligible': False, 'caption': target.get('caption', ''), 'limitations': copy.deepcopy(target.get('limitations', [])), 'sourceUrls': copy.deepcopy(target.get('sourceUrls', []))}
    if target.get('model3dPath'):
        return {**common, 'route': 'molecule_reference', 'model3dPath': target['model3dPath'], 'model3dSha256': target['assetHashes']['model3dPath']}
    return {**common, 'route': 'independent_component_references', 'component3dModels': copy.deepcopy(target['component3dModels']), 'component3dScope': target.get('component3dScope') or COMPONENT_SCOPE}

REUSED_REFERENCE_REASONS = frozenset({'identical_CID', 'unique_exact_compound_name', 'owner_fixed_named_identity'})

def reused_reference_errors(source_entry, reference, index, resolved_proof=None):
    """Check a claimed reused reference against original exact identity/bytes."""
    if context_reason(source_entry)is not None:return ['original context/isomer identity excludes a 3D reference']
    if reference.get('reason')=='resolved_exact_name_identical_CID':
        proof=resolved_proof or {};cid=proof.get('cid')
        if (proof.get('entry_id')!=source_entry.get('id')or proof.get('query_field')!='chemical_name' or proof.get('query')!=source_entry.get('name')
            or type(cid)is not int or cid<=0 or proof.get('status')!='UNIQUE_CID_CONNECTIVITY_CANDIDATE'
            or not re.fullmatch('[0-9a-f]{64}',str(proof.get('cache_sha256','')))
            or proof.get('source_url')!='https://pubchem.ncbi.nlm.nih.gov/compound/'+str(cid)):
            return ['exact reported-name PubChem CID proof absent or stale']
        target, reason = index.existing(source_entry,cid)
        if target is not None and target.get('pubchemCid')!=cid:return ['resolved CID and reused identity disagree']
        reason='resolved_exact_name_identical_CID'
    else:target, reason = index.existing(source_entry)
    if target is None:
        return ['no unique exact original identity match']
    errors = []
    if source_entry.get('formula') and target.get('formula') and (not formula_equivalent(source_entry['formula'], target['formula'])):
        errors.append('original and reused formula conflict')
    expected = reference_from_existing(target, reason)
    for field in ('route', 'reason', 'referenceRegistryId', 'referenceName', 'referenceFormula', 'caption', 'limitations', 'sourceUrls'):
        if reference.get(field) != expected.get(field):
            errors.append('reused reference differs from exact original ' + field)
    for field in ('model3dPath', 'model3dSha256', 'component3dModels', 'component3dScope'):
        if field=='component3dScope' and isinstance(expected.get(field),str) and reference.get(field)==expected[field]+' '+COMPONENT_SCOPE:
            continue  # Exact additive reference-only qualifier; original scope remains intact.
        if reference.get(field) != expected.get(field):
            errors.append('reused reference differs from exact original ' + field)
    return errors

def requires_connected_molecule_reference(e):
    """The known CdMe2 disconnected representation is not its molecule."""
    return e.get('pubchemCid') == 10479 or key(e.get('name','')) in {'dimethylcadmium','dimethylcadmium (cdme2)','dimethylcadmium (me2cd)','cdme2','me2cd'}


def standard_abbreviation_reference_errors(source_entry, reference, proof, entries):
    """Fixed standard names only; every existing reference byte identity stays pinned."""
    expected = STANDARD_ABBREVIATION_IDENTITIES.get(key(source_entry.get('name','')))
    if expected is None or context_reason(source_entry) is not None:
        return ['no fixed unambiguous standard chemical identity']
    proof = proof or {}
    if proof.get('entry_id') != source_entry.get('id') or proof.get('reported_name') != source_entry.get('name') or proof.get('fixed_identity') != expected:
        return ['fixed-standard identity proof absent or stale']
    cid = source_entry.get('pubchemCid')
    if cid is not None and (type(cid) is not int or cid != expected['cid']):
        return ['reported CID conflicts with fixed standard compound']
    if source_entry.get('formula') and not formula_equivalent(source_entry['formula'], expected['formula']):
        return ['reported formula conflicts with fixed standard compound']
    named = proof.get('named_identity_entry') or {}
    actual = entries.get(named.get('id'))
    if not isinstance(actual,dict) or any(actual.get(k) != value for k,value in named.items()):
        return ['original named identity metadata changed']
    template = proof.get('reference')
    try:
        digest = hashlib.sha256(json.dumps(template,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    except (TypeError,ValueError):
        return ['invalid fixed-standard reference metadata']
    if digest != expected['reference_sha256']:
        return ['fixed-standard reference/model identity changed']
    actual_reference = {k:v for k,v in reference.items() if k not in {'chemicalUseCount','buttonLabel'}}
    if actual_reference != template:
        return ['reference differs from exact fixed-standard named reference']
    return []
