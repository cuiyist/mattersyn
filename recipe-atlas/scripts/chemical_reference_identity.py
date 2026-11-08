"""Pure chemical identity/context selection; no network, RDKit or I/O on import."""
import collections, copy, re, unicodedata
from formula_equivalence import formula_equivalent

CORE_IDENTITY_SOURCE_SHA256 = '1ae5e3563d906fa093af61796d36ab6a195f08929fcd3b0b05530c08c2b56978'

COMPONENT_SCOPE = 'Independent molecular components only. No geometry between ions, crystal packing, hydration shell or solution speciation is assigned.'
FIXED_NAMES = {'hexane': 'hexane', 'n-hexane': 'hexane', 'ode': '1-octadecene', '1-octadecene': '1-octadecene', 'oa': 'oleic-acid', 'oleic acid': 'oleic-acid', 'ola': 'oleylamine', 'oleylamine': 'oleylamine', 'top': 'top', 'trioctylphosphine': 'top', 'tri-n-octylphosphine': 'top', 'topo': 'topo', 'trioctylphosphine oxide': 'topo', 'tri-n-octylphosphine oxide': 'topo'}
FIXED_NAMES.update({'octane': 'octane', 'n-octane': 'octane'})
FIXED_NAMES.update({'1-octadecene (ode)': '1-octadecene', 'oleic acid (oa)': 'oleic-acid', 'oleylamine (ola)': 'oleylamine', 'trioctylphosphine (top)': 'top', 'trioctylphosphine oxide (topo)': 'topo'})
WHOLE_CONTEXT_KINDS = {'mixture', 'specimen', 'support', 'surface', 'composite', 'equipment', 'supported-particles', 'analytical-data', 'unresolved-identity', 'material-context', 'sample-context', 'host', 'material_identity', 'author_hypothesis', 'symbolic_context', 'symbolic_identity', 'context', 'identity_only', 'symbolic', 'polymer'}

def key(s):
    return re.sub('\\s+', ' ', unicodedata.normalize('NFKC', str(s)).strip()).casefold()

def rotatable(e):
    return bool(e.get('model3dPath') or e.get('component3dModels'))

def context_reason(e):
    name = key(e.get('name', ''))
    if re.search('\\b(?:hexanes|octanes)\\b|^octadecene$|\\b(?:mixed isomers|isomer mixture)\\b', name):
        return 'ambiguous_isomer'
    if name in {'octane', 'n-octane'} and e.get('depictionKind') in WHOLE_CONTEXT_KINDS - {'symbolic_context', 'unresolved-identity'}:
        return 'whole_context'
    if name in FIXED_NAMES:
        return None
    if e.get('depictionKind') in WHOLE_CONTEXT_KINDS:
        return 'whole_context'
    if re.search('\\b(?:pvp|peg|pva|pdms|pei|polyethylene glycol|polyvinylpyrrolidone|polyvinyl alcohol|polymer)\\b', name):
        return 'undefined_identity'
    free_water_component = e.get('pubchemCid') == 962 and e.get('formula') == 'H2O' and re.match('^water(?:\\b|[- ])', name)
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
