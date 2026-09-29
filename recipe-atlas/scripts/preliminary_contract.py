"""Public preliminary catalog contract; stdlib only, no private evidence imports."""
import hashlib
import re
import unicodedata

SCHEMA = 'mattersyn-preliminary-synthesis/1'
EVIDENCE_SCHEMA = 'mattersyn-preliminary-evidence/1'
MAP_SCHEMA = 'mattersyn-preliminary-page-map/1'
ELEMENTS = set('H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og'.split())
DOI = re.compile(r'10\.\d{4,9}/[^\s<>"' + chr(92)*2 + r'?#]+\Z')
SHA = re.compile(r'[a-f0-9]{64}\Z')
PRIVATE = re.compile(r'(?:[a-zA-Z]:[\\/]|file:|\\\\|/(?:Users|home|tmp|research-assets)/|(?:^|\s)\.\.[\\/])')
NUMBER = re.compile(r'(?<![A-Za-z0-9.])[-+−]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?')
UNITS = re.compile(r'(?<![A-Za-z])(?:°C|℃|°(?!\s*[A-Za-z](?![A-Za-z]))|K|mL|µL|μL|uL|L|mmol|µmol|μmol|mol|mg|µg|μg|kg|g|nm|µm|μm|mm|cm|m|s|min|h|rpm|GPa|MPa|kPa|Pa|torr|atm|bar|eV|keV|V|mV|A|Å|wt%|%|mM|M|µM|μM|uM|nM|hours|minutes|seconds|days|particles|cycles|layers)(?![A-Za-z])')
REVIEW = {'tier':'preliminary','author_source_checked':True,'independent_audit':'pending','accuracy':'unmeasured','training_ready':False}
ENTRY_KEYS = set('source_id doi title citation document_sha256 document_role source_pages inspected_pages material method_label scope deferred precursors operations outcome missing_fields review extraction evidence_fingerprint'.split())

def source_id(doi):
    return 'prelim-' + hashlib.sha256(doi.encode('utf-8')).hexdigest()[:16]

def norm(text):
    return ' '.join(unicodedata.normalize('NFKC', text).split())

def _text(value, limit=240):
    return isinstance(value, str) and bool(value.strip()) and len(value) <= limit and not PRIVATE.search(value) and not any(ord(c)<32 or ord(c)==127 for c in value)

def _int(x):
    return type(x) is int

def _keys(x, names):
    return isinstance(x, dict) and set(x) == set(names.split() if isinstance(names,str) else names)

def validate_catalog(document):
    """Return concise errors; only this exact public allowlist is accepted."""
    errors=[]
    def require(ok, message):
        if not ok: errors.append(message)
    if not _keys(document,'schema entries') or document.get('schema') != SCHEMA or not isinstance(document.get('entries'),list):
        return ['document: expected exact schema and entries keys']
    require(len(document['entries']) <= 20000,'entries: too many')
    seen=set()
    for i,e in enumerate(document['entries']):
        pre=f'entries/{i}'
        if not _keys(e,ENTRY_KEYS):
            errors.append(pre+': entry keys differ from public allowlist');continue
        doi=e['doi']; validdoi=isinstance(doi,str) and len(doi)<=200 and doi==doi.lower() and DOI.fullmatch(doi)
        require(bool(validdoi),pre+': canonical bare lowercase DOI required')
        if validdoi:
            require(e['source_id']==source_id(doi),pre+': source_id mismatch')
            require(doi not in seen,pre+': duplicate DOI/source');seen.add(doi)
        for k in ['title','citation','scope']: require(_text(e[k],600),pre+'/'+k+': invalid text')
        require(_text(e['method_label']),pre+'/method_label: invalid text')
        require(isinstance(e['document_sha256'],str) and bool(SHA.fullmatch(e['document_sha256'])),pre+': invalid PDF hash')
        require(e['document_role'] in ['main','si'],pre+': invalid document role')
        n=e['source_pages']; require(_int(n) and 1<=n<=5000,pre+': invalid page count')
        pages=e['inspected_pages']; validpages=isinstance(pages,list) and 1<=len(pages)<=5000 and all(_int(p) and _int(n) and 1<=p<=n for p in pages) and len(set(pages))==len(pages)
        require(validpages,pre+': invalid inspected pages')
        page_set=set(pages) if validpages else set()
        def locators(loc,where):
            require(isinstance(loc,list) and 1<=len(loc)<=32,where+': locators required')
            if isinstance(loc,list):
                for a in loc:
                    require(_keys(a,'page section') and _int(a.get('page')) and a.get('page') in page_set and _text(a.get('section'),160),where+': invalid/uninspected locator')
        m=e['material'];require(_keys(m,'label elements existing_hub_id'),pre+': material keys invalid')
        if _keys(m,'label elements existing_hub_id'):
            require(_text(m['label']),pre+': material label invalid')
            el=m['elements'];require(isinstance(el,list) and 1<=len(el)<=118 and all(isinstance(x,str) and x in ELEMENTS for x in el) and len(set(el))==len(el),pre+': invalid elements')
            hub=m['existing_hub_id'];require(hub is None or isinstance(hub,str) and len(hub)<=100 and re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',hub),pre+': invalid hub slug')
        for k in ['deferred','missing_fields']:
            require(isinstance(e[k],list) and len(e[k])<=64 and all(_text(x) for x in e[k]),pre+'/'+k+': invalid list')
        require(e['review']==REVIEW and all(type(e['review'].get(k)) is type(v) for k,v in REVIEW.items()) if isinstance(e['review'],dict) else False,pre+': controlled review values required')
        ex=e['extraction'];require(_keys(ex,'origin recipe_scope_complete omitted_variants source_identity_checked') and ex.get('origin') in ['assistant_source_checked','local_model_source_checked'] and ex.get('recipe_scope_complete') is True and ex.get('source_identity_checked') is True and _text(ex.get('omitted_variants'),600),pre+': extraction/scope fields invalid')
        quantitative=False;ps=e['precursors'];require(isinstance(ps,list) and 1<=len(ps)<=64,pre+': precursor count invalid')
        if isinstance(ps,list):
            for j,p in enumerate(ps):
                where=f'{pre}/precursors/{j}'
                if not _keys(p,'name amount role locators'):errors.append(where+': invalid keys');continue
                require(_text(p['name']) and _text(p['role']) and (p['amount'] is None or _text(p['amount'])),where+': invalid scientific text');locators(p['locators'],where)
                quantitative |= isinstance(p['amount'],str) and bool(NUMBER.search(p['amount']))
        ops=e['operations'];require(isinstance(ops,list) and 2<=len(ops)<=100,pre+': at least two ordered operations required')
        if isinstance(ops,list):
            actions=[]
            for j,op in enumerate(ops):
                where=f'{pre}/operations/{j}'
                if not _keys(op,'order action conditions locators'):errors.append(where+': invalid keys');continue
                require(_int(op['order']) and op['order']==j+1,where+': noncontiguous order')
                require(_text(op['action']) and len(re.findall(r'[A-Za-z]',op['action']))>=4,where+': meaningful action required');actions.append(op['action']) if isinstance(op['action'],str) else None;locators(op['locators'],where)
                cs=op['conditions'];require(isinstance(cs,list) and len(cs)<=32,where+': invalid conditions')
                if isinstance(cs,list):
                    for c in cs:
                        require(_keys(c,'parameter reported') and _text(c.get('parameter'),120) and _text(c.get('reported')),where+': invalid condition')
                        quantitative |= isinstance(c,dict) and isinstance(c.get('reported'),str) and bool(NUMBER.search(c['reported']))
            require(len(set(actions))>=2,pre+': duplicate-only operation actions')
        require(quantitative,pre+': quantitative amount or condition required')
        o=e['outcome'];require(_keys(o,'sample_label link_basis descriptors locators'),pre+': outcome keys invalid')
        if _keys(o,'sample_label link_basis descriptors locators'):
            require(_text(o['sample_label']) and _text(o['link_basis'],600) and len(o['link_basis'].strip())>=16,pre+': explicit sample link required');locators(o['locators'],pre+'/outcome')
            ds=o['descriptors'];require(isinstance(ds,list) and 1<=len(ds)<=32,pre+': structural outcome required')
            if isinstance(ds,list):
                for d in ds:
                    require(_keys(d,'kind reported technique locators') and d.get('kind') in ['phase','composition','morphology','size','architecture'] and _text(d.get('reported'),320) and _text(d.get('technique'),160),pre+': invalid descriptor')
                    if isinstance(d,dict):locators(d.get('locators'),pre+'/descriptor')
        require(isinstance(e['evidence_fingerprint'],str) and bool(SHA.fullmatch(e['evidence_fingerprint'])),pre+': invalid evidence fingerprint')
    return errors
