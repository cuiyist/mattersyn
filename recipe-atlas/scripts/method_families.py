"""Pure conservative Reader method-family metadata; records are never modified.

Only a record's own route, reported source names/formulae, roles and exact
input/stock/state links are used. No paper, model, registry or amount-based guess.
"""
import hashlib,re
from collections import Counter,defaultdict
from route_labels import completeness,route_label
from formula_equivalence import formula_equivalent

ELEMENT_NAMES={'Cd':'cadmium','Zn':'zinc','In':'indium','Pb':'lead','Au':'gold','Se':'selenium','S':'sulfur','As':'arsenic','P':'phosphorus','O':'oxygen','Si':'silicon','Te':'tellurium'}
METALS=set('Li Be Na Mg Al K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Fr Ra Ac Th Pa U'.split())
ROUTE_ALIASES={'hot-injection':'Hot injection','hot injection':'Hot injection','heat up':'Heat-up','heat-up':'Heat-up','mbe':'Molecular beam epitaxy','molecular-beam epitaxy':'Molecular beam epitaxy','molecular beam epitaxy':'Molecular beam epitaxy','mocvd':'Metal-organic chemical vapor deposition','metal organic chemical vapor deposition':'Metal-organic chemical vapor deposition','metal-organic chemical vapor deposition':'Metal-organic chemical vapor deposition','movpe':'Metal-organic vapor phase epitaxy','cvd':'Chemical vapor deposition','sol-gel':'Sol-gel','sol\u2013gel':'Sol-gel','sol gel':'Sol-gel','silar':'Successive ionic layer adsorption and reaction','pld':'Pulsed laser deposition','solid source mbe':'Solid-source molecular beam epitaxy','solid-source molecular beam epitaxy':'Solid-source molecular beam epitaxy','solid source molecular beam epitaxy':'Solid-source molecular beam epitaxy','solid-source molecular beam epitaxy':'Solid-source molecular beam epitaxy'}
def norm(value):return re.sub(r'[^a-z0-9]+','',str(value or '').casefold())
ALIASES={}
def alias(display,elements,*names):
 for name in (display,*names):ALIASES[norm(name)]={'key':norm(display),'label':display,'elements':set(elements)}
alias('CdO',{'Cd','O'},'cadmium oxide','Cd oxide')
alias('Cd metal',{'Cd'},'Cd','cadmium','cadmium metal','elemental cadmium')
alias('Me2Cd',{'Cd','C','H'},'dimethylcadmium','dimethyl cadmium','Cd(CH3)2','(CH3)2Cd')
alias('Cd acetate',{'Cd'},'cadmium acetate','Cd(OAc)2')
alias('Cd acetate dihydrate',{'Cd'},'cadmium acetate dihydrate','Cd(OAc)2.2H2O')
alias('Cd oleate',{'Cd'},'cadmium oleate')
alias('Cd stearate',{'Cd'},'cadmium stearate')
alias('CdCl2',{'Cd','Cl'},'cadmium chloride','cadmium(II) chloride')
alias('ZnO',{'Zn','O'},'zinc oxide','Zn oxide')
alias('Zn acetate',{'Zn'},'zinc acetate')
alias('Zn stearate',{'Zn'},'zinc stearate')
alias('Zn oleate',{'Zn'},'zinc oleate')
alias('ZnCl2',{'Zn','Cl'},'zinc chloride','zinc(II) chloride')
alias('InCl3',{'In','Cl'},'indium chloride','indium(III) chloride')
alias('In acetate',{'In'},'indium acetate','indium(III) acetate')
alias('TMIn',{'In','C','H'},'trimethylindium','trimethyl indium')
alias('PbO',{'Pb','O'},'lead oxide','lead(II) oxide')
alias('PbCl2',{'Pb','Cl'},'lead chloride','lead(II) chloride')
alias('Pb nitrate',{'Pb','N','O'},'lead nitrate','lead(II) nitrate','Pb(NO3)2')
alias('Pb oleate',{'Pb'},'lead oleate','lead(II) oleate')
alias('HAuCl4',{'Au','H','Cl'},'chloroauric acid','tetrachloroauric acid')
alias('HAuCl4 trihydrate',{'Au','H','Cl','O'},'HAuCl4.3H2O','chloroauric acid trihydrate')
alias('Se',{'Se'},'selenium','selenium powder','Se powder','elemental selenium','Selenium pellets','Se elemental precursor')
alias('S',{'S'},'sulfur','sulphur','sulfur powder','elemental sulfur','S elemental precursor')
alias('TOP-Se',{'Se','P'},'TOPSe','TOP Se','TOP-Se solution','TOPSe solution','trioctylphosphine selenide','trioctylphosphine selenium','Se-TOP','selenium in TOP','Se in TOP','selenium in trioctylphosphine','selenium/TOP solution','Se/TOP feed')
alias('TBP-Se',{'Se','P'},'TBPSe','tributylphosphine selenide')
alias('(TMS)2S',{'S','Si'},'bis(trimethylsilyl)sulfide','bis(trimethylsilyl) sulfide','hexamethyldisilathiane','(Me3Si)2S')
alias('(TMS)2Se',{'Se','Si'},'bis(trimethylsilyl)selenide','bis(trimethylsilyl) selenide')
alias('Na2S',{'Na','S'},'sodium sulfide','sodium sulphide')
alias('H2S',{'H','S'},'hydrogen sulfide','hydrogen sulphide')
alias('(TMS)3As',{'As','Si'},'tris(trimethylsilyl)arsine','tris(trimethylsilyl) arsine')
alias('TBA',{'As'},'tert-butylarsine','tert Butylarsine')
alias('AsH3',{'As','H'},'arsine')
alias('As4',{'As'},'As4 flux')
alias('As2',{'As'},'As2 flux')
alias('As(NMe2)3',{'As','N'},'tris(dimethylamino)arsine','tris(dimethylamino) arsine')
# Fixed reported-chemical names/formulae, not inferred reaction identities.
alias('Cd acetate',{'Cd'},'Cd(CH3COO)2','Cd(C2H3O2)2','cadmium(II) acetate')
alias('Cd nitrate',{'Cd','N','O'},'Cd(NO3)2','cadmium nitrate','cadmium(II) nitrate')
alias('Cd perchlorate',{'Cd','Cl','O'},'Cd(ClO4)2','cadmium perchlorate')
alias('Zn acetate',{'Zn'},'Zn(OAc)2','Zn(CH3COO)2','Zn(C2H3O2)2')
alias('ZnSO4',{'Zn','S','O'},'zinc sulfate','zinc sulphate')
alias('ZnI2',{'Zn','I'},'zinc iodide')
alias('Zn metal',{'Zn'},'Zn','zinc metal','elemental zinc')
alias('Et2Zn',{'Zn','C','H'},'diethylzinc','diethyl zinc','Zn(C2H5)2')
alias('In metal',{'In'},'In','indium metal','elemental indium')
alias('Pb acetate',{'Pb'},'Pb(OAc)2','Pb(CH3COO)2','Pb(C2H3O2)2','Pb(II) acetate','lead acetate','lead(II) acetate')
alias('Pb acetate trihydrate',{'Pb'},'lead acetate trihydrate','Pb(OAc)2.3H2O')
alias('PbBr2',{'Pb','Br'},'lead bromide','lead(II) bromide')
alias('Pb(OH)Cl',{'Pb','O','H','Cl'},'lead hydroxychloride')
alias('AuCl3',{'Au','Cl'},'gold(III) chloride','gold trichloride')
alias('Au acetate',{'Au'},'gold acetate','gold(III) acetate')
alias('Na2Se',{'Na','Se'},'sodium selenide')
alias('Thiourea',{'C','H','N','S'},'CH4N2S','thiocarbamide')
alias('Thioacetamide',{'C','H','N','S'},'C2H5NS')
# Reject roles and explicit names that describe media, ligands, supplied samples
# or apparatus; a formula in such a field does not establish a precursor.
EXCLUDED_SOURCE_ROLE=re.compile(r'\b(?:solvent|antisolvent|ligand|surfactant|capping|medium|media|vessel|substrate|seed|catalyst|reducing agent|reductant|washing|wash|workup|product|photoabsorber|dispersion|suspension|matrix|host component|film forming)\b',re.I)
EXCLUDED_SOURCE_NAME=re.compile(r'\b(?:nanocrystals?|quantum dots?|qds?|cores?|shells?|nanowires?|nanorods?|nanoparticles?|preformed|dispersion|suspension|substrate|capping layer|seed|film)\b',re.I)

def excluded_source(material):
 role=re.sub(r'[_-]+',' ',str(material.get('role') or ''));name=str(material.get('name') or '')
 inventory=re.sub(r'[_-]+',' ',role+' '+name)
 return bool(EXCLUDED_SOURCE_ROLE.search(role) or EXCLUDED_SOURCE_NAME.search(name) or re.search(r'\binventory only\b|\bnot (?:used|charged|added)\b',inventory,re.I))

SOURCE_ELEMENT_BY_LABEL={name:element for element,names in {
 'Cd':['CdO','Cd metal','Me2Cd','Cd acetate','Cd acetate dihydrate','Cd oleate','Cd stearate','CdCl2','Cd nitrate','Cd perchlorate'],
 'Zn':['ZnO','Zn acetate','Zn stearate','Zn oleate','ZnCl2','ZnSO4','ZnI2','Zn metal','Et2Zn'],
 'In':['InCl3','In acetate','TMIn','In metal'],
 'Pb':['PbO','PbCl2','Pb nitrate','Pb oleate','Pb acetate','Pb acetate trihydrate','PbBr2','Pb(OH)Cl'],
 'Au':['HAuCl4','HAuCl4 trihydrate','AuCl3','Au acetate'],
 'Se':['Se','TOP-Se','TBP-Se','(TMS)2Se','Na2Se'],
 'S':['S','(TMS)2S','Na2S','H2S','Thiourea','Thioacetamide'],
 'As':['(TMS)3As','TBA','AsH3','As4','As2','As(NMe2)3']
}.items() for name in names}

def fixed_name_alias(name):
 hit=ALIASES.get(norm(name))
 if hit:return hit,False
 suffix=re.fullmatch(r'(.+?)\s+\(([^()]{1,30})\)',str(name).strip())
 if suffix:
  full=ALIASES.get(norm(suffix[1]));short=ALIASES.get(norm(suffix[2]))
  if full and short:
   return (full,False) if full['key']==short['key'] else (None,True)
 return None,False

def fixed_source_identity(material):
 if excluded_source(material):return None
 name=str(material.get('name') or '').strip();formula=str(material.get('formula') or '').strip()
 named,conflict=fixed_name_alias(name)
 if conflict:return None
 normalized=source_identity(material)
 if not named and normalized and normalized['label']in SOURCE_ELEMENT_BY_LABEL:
  return {**normalized,'source_elements':{SOURCE_ELEMENT_BY_LABEL[normalized['label']]}}
 if named:
  found=source_identity(material)
  return {**found,'source_elements':{SOURCE_ELEMENT_BY_LABEL[named['label']]}} if found else None
 # An unambiguous fixed formula is usable even if the material has a generic
 # reagent name; product compounds such as InAs/CdSe/PbS are absent deliberately.
 formula_base=re.sub(r'[.\u00b7]\d*H2O$','',formula)
 known=ALIASES.get(norm(formula_base)) if formula else None
 if known and not re.search(r'\b(?:unresolved|unknown|unspecified|source-defined|stock|solution|feed|mixture|dispersion|suspension)\b|\bin\s+',name,re.I):
  return {**known,'source_elements':{SOURCE_ELEMENT_BY_LABEL[known['label']]}}
 return None


TOP_CARRIER_NAMES={norm(x) for x in ('TOP','trioctylphosphine','tri-n-octylphosphine','trioctylphosphine (TOP)','tri-n-octylphosphine (TOP)','trioctylphosphine for selenium precursor')}
TOP_SE_FEED={'key':norm('TOP-Se'),'label':'Se/TOP feed','elements':{'Se','P'}}

NONCOMPETING_DILUENT_NAMES={norm(x)for x in ('ODE','1-octadecene','1-Octadecene for selenium stock')}

def composition_feed_materials(parts,material):
 if not parts or any(m is None for m in parts):return None
 if material['id']not in {m['id']for m in parts}:return None
 source=fixed_source_identity(material)
 if not source or source['key']!=norm('Se'):return None
 solutes=[m for m in parts if m['id']==material['id']]
 carriers=[m for m in parts if norm(m.get('name'))in TOP_CARRIER_NAMES]
 if len(solutes)!=1 or len(carriers)!=1 or carriers[0]['id']==material['id']:return None
 # A reported ODE diluent does not change the main Se/TOP feed identity.
 # Other chalcogen/phosphine feeds and unrecognized components are not folded.
 if any(m['id']not in {material['id'],carriers[0]['id']} and norm(m.get('name'))not in NONCOMPETING_DILUENT_NAMES for m in parts):return None
 return TOP_SE_FEED

def competing_feed_materials(parts,material):
 if not parts or any(m is None for m in parts)or material['id']not in {m['id']for m in parts}:return False
 if not any(norm(m.get('name'))in TOP_CARRIER_NAMES for m in parts):return False
 for m in parts:
  if m['id']==material['id']:continue
  if norm(m.get('name'))in {norm(x)for x in ('TBP','tributylphosphine','tri-n-butylphosphine')}:return True
  source=fixed_source_identity(m)
  if source and source['source_elements']&{'Se','S','Te','As','P'}:return True
 return False

def composition_stock_feed(record,stock,material):
 mats={m['id']:m for m in record.get('materials',[])}
 return composition_feed_materials([mats.get(c.get('material_id'))for c in stock.get('components',[])],material)

def operation_prepared_feed(record,material):
 # Exact own operation evidence only. Do not expand carried reaction states
 # into new additions or infer a feed from Se and TOP merely co-listed.
 mats={m['id']:m for m in record.get('materials',[])};operations=record.get('operations',[])
 for index,op in enumerate(operations):
  own=str(op.get('action')or'')+' '+str(op.get('label')or'')
  if not re.search(r'\b(?:prepar\w*|dissolv\w*)\b',own,re.I):continue
  if not re.search(r'\b(?:Se|selenium|chalcogen)\b',own,re.I)or not re.search(r'\b(?:precursor|feed|stock|solution)\b',own,re.I):continue
  if re.search(r'\b(?:not|without|avoid|instead)\b',own,re.I):continue
  direct=[mats[x]for x in dict.fromkeys(op.get('inputs',[]))if x in mats]
  ambiguous=competing_feed_materials(direct,material)
  feed=composition_feed_materials(direct,material)
  if not feed and not ambiguous:continue
  outputs=set(op.get('outputs',[]))
  for injection in operations[index+1:]:
   label=str(injection.get('label')or'')
   if not re.fullmatch(r'inject(?:ion)?',str(injection.get('action')or''),re.I):continue
   if not outputs.intersection(injection.get('inputs',[])):continue
   if not re.search(r'\b(?:Se|selenium|chalcogen)\b',label,re.I)or not re.search(r'\b(?:precursor|feed|stock|solution)\b',label,re.I):continue
   return {'ambiguous':True}if ambiguous else feed
 return None

GENERIC_SOURCE=re.compile(r'^(?:unknown|unspecified|not reported|source[- ]defined(?: composition)?|(?:main |metal |nonmetal |chalcogen |cadmium |selenium |sulfur |arsenic )?(?:source|precursor|salt)(?: solution| stock)?)$',re.I)
MADE=re.compile(r'\b(?:preformed|already[- ]made|previously (?:prepared|synthesized)|nanocrystals?|quantum dots?|qds|core dispersion)\b',re.I)
PROCESS=re.compile(r'\b(?:ligand[- ]exchange|surface functional\w*|coat(?:ing)?|encapsulat\w*|shell[- ](?:over)?growth|grow\w*(?:\s+\S+){0,4}\s+shell|spin[- ]coat\w*|drop[- ]cast\w*|self[- ]assembly|device (?:fabrication|assembly)|film (?:fabrication|assembly|deposition))\b',re.I)

def primary_source(record):
 return next((s for s in record.get('sources',[]) if s.get('id')==record.get('lineage',{}).get('source_group')),None)
def paper_key(record):
 s=primary_source(record) or {};doi=re.sub(r'^https?://(?:dx\.)?doi\.org/','',str(s.get('doi') or '').strip(),flags=re.I).lower()
 return 'doi:'+doi if doi else 'source:'+str(s['id']) if s.get('id') else None
def year(record):
 value=(primary_source(record) or {}).get('year');return value if type(value) is int and 1500<=value<=2200 else 9999
def record_key(record):
 return (record.get('quality',{}).get('review_status')=='source_extracted',-completeness(record),year(record))
def route(record,override=None):
 raw_method=str(record.get('method')or'').strip().replace('_',' ')
 value=str(override or route_label(record) or raw_method).strip().replace('_',' ')
 # Explicit rejection/negation/conflict is never a missing-label fallback.
 for explicit in (raw_method,value):
  if any(re.search(pattern,explicit,re.I)for _,pattern in NAMED_METHODS+ROUTE_CLASSES)and not route_class(explicit):return ''
 result=route_class(value)
 if route_class(raw_method):return result
 # Missing/generic route labels may use only this record's reported system.
 # Aggregate every field so conflicting systems cannot be selected by order.
 own=[]
 for op in record.get('operations',[]):
  own += [str(op.get('label')or''),str(op.get('vessel')or''),str(op.get('system')or'')]
  env=op.get('environment')or{}
  if env.get('status')=='reported':own.append(str(env.get('value')or''))
  for key,q in (op.get('parameters')or{}).items():
   if isinstance(q,dict)and q.get('status')=='reported'and re.search(r'system|apparatus|vessel',key,re.I):own.append(str(q.get('value')or''))
 systems=set()
 if result in {name for name,_ in ROUTE_CLASSES[7:10]}:systems.add(result)
 for label in own:
  found=route_class(label,systems_only=True)
  if not found and any(re.search(pattern,label,re.I)for _,pattern in ROUTE_CLASSES[7:10]):return ''
  if found:systems.add(found)
 if len(systems)>1:return ''
 return result or(next(iter(systems))if systems else'')

def target_sources(formula):
 if re.search(r'[/,:]|\bx\b',formula):return None
 els=list(dict.fromkeys(re.findall(r'[A-Z][a-z]?',formula)));metal=[e for e in els if e in METALS]
 if len(metal)!=1:return None
 nonmetal=[e for e in els if e!=metal[0]]
 return (metal[0],nonmetal) if len(nonmetal)<=1 else None
def source_identity(material):
 name=str(material.get('name')or'').strip();formula=str(material.get('formula')or'').strip()
 named,conflict=fixed_name_alias(name)
 if conflict:return None
 # J2 ignores hydrate water for family grouping only; record/chemical models stay exact.
 if not named:
  base=re.sub(r'\s*\(?\b(?:mono|di|tri|tetra|penta|hexa|hepta|octa|nona|deca)?hydrate\)?\s*$','',name,flags=re.I).strip()
  named=ALIASES.get(norm(base))
 if named:return family_source(named)
 if not name or GENERIC_SOURCE.fullmatch(name)or '\ufffd'in name or re.search(r'\b(?:precursor|unresolved|unknown|unspecified|undefined|source-defined|stock|solution)\b',name,re.I):return None
 return {'key':norm(name),'label':name,'elements':set(re.findall(r'[A-Z][a-z]?',formula or(name if re.fullmatch(r'[A-Za-z0-9().+\u00b7-]+',name)else'')))}
def role_matches(material,element,metal):
 role=re.sub(r'[_-]+',' ',str(material.get('role') or '')).strip().casefold()
 word=ELEMENT_NAMES.get(element,'').casefold();symbol=element.casefold()
 prefixes={word,symbol}|({'metal','host'} if metal else {'chalcogen','nonmetal','metalloid'})
 for prefix in prefixes:
  if prefix and re.fullmatch(r'(?:gas phase |aqueous |main |initial )?'+re.escape(prefix)+r' (?:(?:precursor|source)(?: (?:solute|feed|component|stock component|reagent))?|(?:stock|feed) (?:component|solute|precursor))',role):return True
 return not metal and element=='S' and role=='sulfide reagent gas'
def contains_element(material,identity,element):
 if element in identity['elements']:return True
 role=re.sub(r'[_-]+',' ',str(material.get('role') or '')).casefold()
 name=str(material.get('name') or '').casefold();word=ELEMENT_NAMES.get(element,'')
 return bool(word and (re.search(r'\b'+re.escape(word)+r'\b',name) or re.search(r'\b'+re.escape(word)+r' (?:source|precursor)\b',role)))
def used_materials(record):
 mats={m['id']:m for m in record.get('materials',[])};stocks={s['id']:s for s in record.get('stocks',[])};states={s['id']:s for s in record.get('material_states',[])};used=set();used_stocks=set();seen=set()
 def follow(key):
  if key in seen:return
  seen.add(key)
  if key in mats:used.add(key)
  elif key in stocks:
   used_stocks.add(key)
   for component in stocks[key].get('components',[]):follow(component.get('material_id'))
  elif key in states:
   for parent in states[key].get('parent_ids',[]):follow(parent)
 for op in record.get('operations',[]):
  if op.get('stage')=='synthesis':
   for key in op.get('inputs',[])+op.get('optional_inputs',[]):follow(key)
 return used,used_stocks
def processing(record):
 used,_=used_materials(record)
 supplied=[m for m in record.get('materials',[]) if not used or m['id'] in used]
 def given_core(m):
  name=str(m.get('name') or '')
  return bool(re.search(r'\bcores?\b',name,re.I) and not re.search(r'\b(?:precursor|source|reaction)\b',name,re.I))
 given=any(str(m.get('role') or '').casefold()=='seed' or MADE.search(str(m.get('name') or '')) or MADE.search(str(m.get('role') or '')) or given_core(m) for m in supplied)
 own=' '.join([str(record.get('method') or '')]+[str(o.get('action') or '').replace('_',' ')+' '+str(o.get('label') or '') for o in record.get('operations',[])])
 shell_overgrowth=record.get('material',{}).get('architecture')=='core_shell' and any(given_core(m)or str(m.get('role')or'').casefold()=='seed'for m in supplied) and re.search(r'\b(?:overgrowth|seeded growth|shell growth)\b',own,re.I)
 return bool(given and (PROCESS.search(own) or shell_overgrowth))
def pick_source(record,element,metal,identity_context=None):
 used,used_stocks=used_materials(record);candidates=[]
 for m in record.get('materials',[]):
  if excluded_source(m):continue
  typed=role_matches(m,element,metal)
  fixed=fixed_source_identity(m)
  pinned=pinned_source_identity(record,m,identity_context)
  if not fixed and pinned and pinned.get('source_elements'):fixed=pinned
  if not typed and (not fixed or element not in fixed['source_elements']):continue
  identity=fixed or pinned or source_identity(m)
  if not identity:
   explicit=set(re.findall(r'[A-Z][a-z]?',str(m.get('formula') or '')))
   if not explicit or element in explicit:return None,'unresolved_source_identity'
   continue
  if not contains_element(m,identity,element):
   if not identity['elements']:return None,'unresolved_source_element'
   continue
  if identity['key']==norm('TOP-Se'):identity=TOP_SE_FEED
  candidates.append((m,identity))
 # An explicitly named nonmetal feed may resolve an exact used stock link.
 # TOP plus elemental Se alone never implies TOP-Se.
 if not metal and element not in {'Se','S'}:
  stocks={s['id']:s for s in record.get('stocks',[])}
  for i,(m,identity) in enumerate(candidates):
   feeds={}
   # Old partial input graphs may omit stock IDs. A unique explicitly
   # declared stock still supplies composition; an explicit used stock wins.
   for sid in (used_stocks or set(stocks)):
    st=stocks[sid];named=ALIASES.get(norm(st.get('name')))
    mats={x['id']:x for x in record.get('materials',[])}
    if element=='Se'and competing_feed_materials([mats.get(c.get('material_id'))for c in st.get('components',[])],m):return None,'ambiguous_named_stock_feeds'
    if named and element in named['elements'] and any(c.get('material_id')==m['id'] for c in st.get('components',[])):
     feed=TOP_SE_FEED if named['key']==norm('TOP-Se') else named;feeds[feed['key']]=feed
    composition=composition_stock_feed(record,st,m) if element=='Se' else None
    if composition:feeds[composition['key']]=composition
   prepared=operation_prepared_feed(record,m)if element=='Se'else None
   if prepared and prepared.get('ambiguous'):return None,'ambiguous_named_stock_feeds'
   if prepared:feeds[prepared['key']]=prepared
   if len(feeds)>1:return None,'ambiguous_named_stock_feeds'
   if feeds:candidates[i]=(m,next(iter(feeds.values())))
 identities={family_source(identity)['key']:family_source(identity)for _,identity in candidates}
 if len(identities)!=1:return None,'missing_source' if not identities else 'multiple_sources'
 value=family_source(next(iter(identities.values())));return {'key':value['key'],'label':value['label']},None
def sparse_core_shell_context(record):
 """A sparse named component feed cannot establish the other components' origin."""
 material=record.get('material',{})
 parts=[part.strip() for part in str(material.get('formula')or'').split('/')]
 if material.get('architecture')not in {'core_shell','unresolved'} or len(parts)<2 or material.get('components')!=parts:return None
 component=parts[-1];sources=target_sources(component)
 if not sources:return None
 additions=[];workup={'precipitate','centrifuge','wash','filter','redisperse','dry','isolate','collect','decant','separate'}
 states={state.get('id')for state in record.get('material_states',[])}
 for operation in record.get('operations',[]):
  action=str(operation.get('action')or'').casefold().replace('_',' ')
  own=' '.join(str(operation.get(key)or'')for key in ('label','description'))
  explicit_core_creation=re.search(r'\b(?:form|grow|synthesi[sz]e|nucleat)\w*\b.{0,50}\bcores?\b|\bcore (?:formation|growth|synthesis|nucleation)\b',own,re.I)
  if explicit_core_creation and not re.search(r'\b(?:no|not|without|avoid|prevent)\b|core[- /]shell',own,re.I):return None
  if action in {'add','inject'} and operation.get('stage')=='synthesis':additions.append(operation)
  elif action in {'cool','quench'}:continue
  elif action in {'heat','hold','stir','wait'} and all(key in states for key in operation.get('inputs',[])+operation.get('optional_inputs',[])):continue
  elif operation.get('stage')=='workup' and action in workup:continue
  else:return None
 if len(additions)!=1:return None
 operation=additions[0];own=' '.join(str(operation.get(key)or'')for key in ('label','description'))
 if not re.search(r'(?<![A-Za-z0-9])'+re.escape(component)+r'(?![A-Za-z0-9])',own,re.I):return None
 if not re.search(r'\b(?:solution|precursor|feed|shell|overgrowth|coating)\b',own,re.I):return None
 used,_=used_materials(record)
 supplied=[item for item in record.get('materials',[])if item.get('id')in used]
 given=any(str(item.get('role')or'').casefold()=='seed' or MADE.search(str(item.get('name')or'')) or MADE.search(str(item.get('role')or'')) or (re.search(r'\bcores?\b',str(item.get('name')or''),re.I)and not re.search(r'\b(?:precursor|source|reaction)\b',str(item.get('name')or''),re.I))for item in supplied)
 if given:return 'processing'
 # Other explicitly consumed precursor sources may make an integrated product;
 # this narrow sparse-feed fallback does not override that own-record evidence.
 allowed={sources[0],*sources[1]}
 for item in supplied:
  role=str(item.get('role')or'').replace('_',' ')
  if not re.search(r'\b(?:precursor|source|reagent|feed|solute)\b',role,re.I):continue
  identity=source_identity(item)
  if not identity or not identity.get('elements') or identity['elements']-allowed:return None
 return 'other'

def classify_record(record,formula,method_label=None,identity_context=None):
 if post_processing(record):return {'kind':'processing','key':'processing','label':'Processing of material'}
 if component_product(record,formula):return {'kind':'component','key':'component','label':formula+' as shell or component'}
 name=route(record,method_label)
 if not name:return {'kind':'other','key':'other','label':'Other methods','reason':'missing_route'}
 target=target_sources(formula)
 if not target:return {'kind':'synthesis','key':name.casefold()+'|sources-not-listed','label':name+', sources not listed','route':name,'reason':'unsupported_target'}
 metal,nonmetals=target;m,reason=pick_source(record,metal,True,identity_context)
 n=None;why='metal_'+reason if reason else None
 if not reason and nonmetals:
  n,reason=pick_source(record,nonmetals[0],False,identity_context)
  if reason:why='nonmetal_'+reason
 if reason:return {'kind':'synthesis','key':name.casefold()+'|sources-not-listed','label':name+', sources not listed','route':name,'reason':why}
 key='|'.join([name.casefold(),m['key'],n['key']if n else'not-applicable'])
 return {'kind':'synthesis','key':key,'label':name+' - '+m['label']+(' + '+n['label']if n else''),'route':name,'metal_source':m['label'],'nonmetal_source':n['label']if n else None}
def author_label(authors,publication_year=None):
 if isinstance(authors,list):names=[str(a).strip() for a in authors if str(a).strip()]
 else:
  text=str(authors or '').strip()
  if re.search(r'\bet al\.?',text,re.I):base=text
  else:
   names=[x.strip() for x in text.split(';') if x.strip()] if ';' in text else [x.strip() for x in re.split(r',\s+(?=[A-Z])|\s+and\s+',text) if x.strip()]
   # Commas inside inverted-name citations are not author separators.
   if any(re.fullmatch(r'(?:[A-Z]\.\s*)+',x) for x in names):names=[text]
   base=(names[0]+' et al.') if len(names)>2 else ' and '.join(names)
  return (base or 'Source')+(' ('+str(publication_year)+')' if publication_year is not None and publication_year!=9999 else '')
 base=names[0]+' et al.' if len(names)>2 else ' and '.join(names)
 return (base or 'Source')+(' ('+str(publication_year)+')' if publication_year is not None and publication_year!=9999 else '')
def build_method_families(records,formula,method_labels=None,identity_context=None):
 identity_context=load_identity_context()if identity_context is None else identity_context
 input_order={r['record_id']:i for i,r in enumerate(records)}
 method_labels=method_labels or {};byid={r['record_id']:r for r in records}
 if len(byid)!=len(records):raise ValueError('Duplicate supplied record ID')
 groups={};diagnostics=Counter()
 for r in records:
  classified=classify_record(r,formula,method_labels.get(r['record_id']),identity_context);key=classified['kind']+'|'+classified['key'];g=groups.setdefault(key,{'descriptor':classified,'records':[]});g['records'].append(r)
  if classified.get('reason'):diagnostics[classified['reason']]+=1
 # A detailed source family supported by only one distinct paper becomes a
 # route-local other-sources group. Variants never inflate adoption.
 folded={}
 for key,g in groups.items():
  descriptor=g['descriptor']
  if descriptor['kind']=='synthesis'and'metal_source'in descriptor and len({paper_key(r)for r in g['records']})==1:
   route_name=descriptor['route'];descriptor={'kind':'synthesis','key':route_name.casefold()+'|other-sources','label':route_name+', other sources','route':route_name}
  target_key=descriptor['kind']+'|'+descriptor['key']
  destination=folded.setdefault(target_key,{'descriptor':descriptor,'records':[]});destination['records']+=g['records']
 groups=folded
 families=[]
 for key,g in groups.items():
  g['records'].sort(key=lambda r:input_order[r['record_id']])
  ordered=sorted(g['records'],key=record_key);papers=defaultdict(list)
  for r in ordered:
   pk=paper_key(r)
   if pk is None:raise ValueError('Supplied record lacks explicit source identity')
   papers[pk].append(r)
  cards=[]
  for pk,variants in papers.items():
   representative=variants[0];source=primary_source(representative);earliest=min(year(v) for v in variants)
   cards.append({'paper_key':pk,'source_id':source['id'],'doi':source.get('doi'),'year':None if earliest==9999 else earliest,'citation':author_label(source.get('authors'),earliest),'default_record_id':representative['record_id'],'record_ids':[r['record_id'] for r in variants]})
  cards.sort(key=lambda p:record_key(byid[p['default_record_id']]))
  descriptor=g['descriptor'];families.append({'id':'method-family-'+hashlib.sha256(key.encode()).hexdigest()[:12],'kind':descriptor['kind'],'label':descriptor['label'],**{k:descriptor[k] for k in ('route','metal_source','nonmetal_source') if k in descriptor},'paper_count':len(cards),'record_count':len(ordered),'record_ids':[r['record_id'] for r in ordered],'default_record_id':ordered[0]['record_id'],'earliest_year':min((year(r) for r in ordered),default=9999),'papers':cards})
 # Reader interpretation: identified synthesis families compete by adoption;
 # Other is the unclassified fallback, then explicitly-last Processing.
 # If no identified synthesis family exists, Other supplies the default.
 families.sort(key=lambda g:({'synthesis':0,'other':1,'component':2,'processing':3}[g['kind']],-g['paper_count'],g['earliest_year'],g['label'].casefold(),g['id']))
 return {'schema':'mattersyn-method-families/1','material_formula':formula,'paper_count_unique':len({paper_key(r) for r in records}),'record_count':len(records),'default_record_id':families[0]['default_record_id'] if families else None,'families':families,'diagnostics_record_counts':dict(diagnostics)}



# J presentation-only source normalization. Hydrates do not create new families.
alias('Me2Cd',{'Cd','C','H'},'CdMe2','dimethylcadmium (CdMe2)','dimethylcadmium (Me2Cd)')
alias('Cd acetate',{'Cd'},'Cd(Ac)2','cadmium acetate hydrate','cadmium acetate dihydrate')
alias('HAuCl4',{'Au','H','Cl'},'HAuCl4.3H2O','HAuCl4·3H2O','chloroauric acid trihydrate','hydrogen tetrachloroaurate trihydrate')
for symbol,word in [('Cd','cadmium'),('Zn','zinc'),('Pb','lead'),('In','indium')]:
 for ligand in ('myristate','palmitate','stearate','oleate'):
  label=symbol+' '+ligand
  if norm(label)not in ALIASES:alias(label,{symbol},word+' '+ligand,word+'(II) '+ligand if symbol!='In'else word+'(III) '+ligand)
  SOURCE_ELEMENT_BY_LABEL[label]=symbol
alias('Se',{'Se'},'selenium shot','selenium shots','Se shots','Se in ODE','selenium in ODE','selenium in 1-octadecene','Se/TOP feed','Se/TBP feed')
alias('S',{'S'},'sulfur shots','sulfur in ODE','S in ODE','S/TOP feed','TOP-S','TOPS','TBP-S','TBPS','trioctylphosphine sulfide','tributylphosphine sulfide')

ROUTE_CLASSES=[
 ('Hot injection',r'\bhot[- ]?inject\w*\b'),
 ('Heat-up',r'\bheat[- ]?up\b|\bnon[- ]?inject\w*\b|\bone[- ]pot\b'),
 ('SILAR',r'\bsilar\b|successive ionic layer'),
 ('Solvothermal or hydrothermal',r'\b(?:solvo|hydro)thermal\b'),
 ('Aqueous or colloidal precipitation',r'\baqueous\b|\bcolloidal\b|\bprecipitat\w*\b'),
 ('Sol-gel',r'\bsol[- \u2013]gel\b'),
 ('Solid state',r'\bsolid[- ]state\b|\bsolid[- ]phase\b|\bball[- ]mill\w*\b|\bmechanochem\w*\b'),
 ('Molecular beam epitaxy',r'\bmbe\b|molecular[- ]beam epitax\w*'),
 ('Chemical vapour deposition',r'\b(?:mocvd|movpe|mcvd|cvd)\b|metal[- ]?organic (?:chemical )?vapou?r|chemical vapou?r deposition'),
 ('Other vapour or physical deposition',r'(?<!organic )vapou?r[- ]phase epitax|\b(?:sputter\w*|evaporat\w* deposition|physical vapou?r|pulsed[- ]laser deposition|pld|chemical[- ]beam epitaxy|liquid[- ]phase epitaxy|droplet epitaxy)\b'),
 ('Electrochemical',r'\belectrochem\w*|\belectrodeposit\w*'),
 ('Microwave',r'\bmicrowave\w*'),
]
NAMED_METHODS=[('Brust',r'\bbrust(?:[- ]schiffrin)?\b'),('Turkevich/citrate reduction',r'\bturkevich\b|\bcitrate[- ](?:reduction|reducing)\b'),('St\u00f6ber',r'\bst[o\u00f6]ber\b'),('Pechini',r'\bpechini\b'),('Polyol',r'\bpolyol\b'),('Thermal decomposition',r'\bthermal(?:ly)? decompos\w*\b'),('Chemical reduction',r'\bchemical reduction\b'),('Seed-mediated growth',r'\bseed[- ]mediated growth\b'),('Cation exchange',r'\bcation[- ]exchange\b'),('Reflux',r'\breflux\b'),('Microemulsion',r'\bmicroemulsion\b'),('Chemical bath deposition',r'chemical bath deposition|\bcbd\b'),('Microfluidic',r'\bmicrofluidic\b')]
NEGATED_ROUTE=re.compile(r'\b(?:no|not|without|avoid\w*|instead of|rather than|unlike|compar\w*|versus|vs)\b',re.I)

def route_class(value,systems_only=False):
 value=str(value or'').strip().replace('_',' ')
 if not value:return ''
 table=ROUTE_CLASSES[7:10]if systems_only else NAMED_METHODS+ROUTE_CLASSES
 found=[]
 for label,pattern in table:
  for match in re.finditer(pattern,value,re.I):
   left=max(value.rfind(mark,0,match.start())for mark in ';.!?')+1
   end=[i for mark in ';.!?'if(i:=value.find(mark,match.end()))>=0]
   clause=value[left:min(end)if end else len(value)]
   if NEGATED_ROUTE.search(clause):return ''
   found.append(label)
 # Hot injection owns a generic colloidal/aqueous qualifier; named methods own
 # their general class. Conflicting explicit routes remain unclassified.
 named=[name for name,_ in NAMED_METHODS if name in found]
 kinds=set(found)
 if named and not re.search(r'\b(?:or|and|versus|vs)\b',value,re.I):kinds.discard('Aqueous or colloidal precipitation')
 if 'Hot injection'in kinds:
  kinds.discard('Aqueous or colloidal precipitation')
  if not re.search(r'heat[- ]?up|non[- ]?inject',value,re.I):kinds.discard('Heat-up')
 if 'Microwave'in kinds:kinds.discard('Solvothermal or hydrothermal')
 if 'Sol-gel'in kinds:kinds.discard('Aqueous or colloidal precipitation')
 return next(iter(kinds))if len(kinds)==1 else ''

def family_source(identity):
 value=dict(identity);label=value['label']
 replacements={'Cd acetate dihydrate':'Cd acetate','HAuCl4 trihydrate':'HAuCl4','Pb acetate trihydrate':'Pb acetate','Se/TOP feed':'Se','TOP-Se':'Se','TBP-Se':'Se'}
 label=replacements.get(label,label)
 value.update(label=label,key=norm(label)if label!=identity['label']else value['key'])
 return value

def component_product(record,formula):
 material=record.get('material',{});own=str(material.get('formula')or'').strip()
 components={str(x).strip()for x in material.get('components',[])if str(x).strip()}
 if own and not formula_equivalent(own,formula):return True
 if len(components)>1:return True
 if material.get('architecture')in {'core_shell','heterostructure','composite','doped_host','doped','phase_mixture','coated'}:return True
 for product in record.get('products',[]):
  composition=product.get('composition')or{}
  value=str(composition.get('value')or'').strip()
  if composition.get('status')=='reported'and re.fullmatch(r'[A-Za-z0-9()/,:.+-]+',value)and not formula_equivalent(value,formula):return True
 return False

def post_processing(record):
 if not processing(record):return False
 own=' '.join([str(record.get('method')or'')]+[str(o.get('action')or'').replace('_',' ')+' '+str(o.get('label')or'')for o in record.get('operations',[])])
 return bool(re.search(r'ligand[- ]exchange|surface functional\w*|spin[- ]coat\w*|drop[- ]cast\w*|self[- ]assembly|device (?:fabrication|assembly)|film (?:fabrication|assembly|deposition)',own,re.I))

def identity_context_from_chemistry(registry,bindings,overlay):
 """Index H's already pinned whole-compound identities once, not per recipe."""
 entries={entry['id']:entry for entry in registry.get('entries',[])};result={}
 for rid,materials in bindings.get('recordBindings',{}).items():
  rows={}
  for mid,eid in materials.items():
   entry=entries.get(eid,{})
   ref=overlay.get('entries',{}).get(eid,{})
   if ref.get('route')=='flat':continue
   candidate=entry
   if ref.get('route')=='molecule_reference'and ref.get('referenceOnly')is True and ref.get('reason')in {'identical_CID','unique_exact_compound_name','owner_fixed_named_identity','resolved_exact_name_identical_CID'}:
    candidate=entries.get(ref.get('referenceRegistryId'),entry)
   cid=candidate.get('pubchemCid')
   if type(cid)is not int or cid<=0:continue
   # Never turn independent ligand/component references into a compound CID.
   if ref and ref.get('route')not in {'molecule_reference','independent_component_references','ambient_crystal_reference'}:continue
   named,_=fixed_name_alias(candidate.get('name'))
   if named:identity=family_source(named)
   else:identity={'key':'cid:'+str(cid),'label':str(candidate.get('name')or entry.get('name')),'elements':set(re.findall(r'[A-Z][a-z]?',str(entry.get('formula')or'')))}
   if named and named['label']in SOURCE_ELEMENT_BY_LABEL:identity['source_elements']={SOURCE_ELEMENT_BY_LABEL[named['label']]}
   rows[mid]=identity
  if rows:result[rid]=rows
 return result

def pinned_source_identity(record,material,context):
 return (context or{}).get(record['record_id'],{}).get(material['id'])

from functools import lru_cache
@lru_cache(maxsize=1)
def load_identity_context():
 """Use existing H input pins once per build; no registry/model/network lookup."""
 import json
 from pathlib import Path
 from chemical_reference_overlay import enrich_registry
 base=Path(__file__).resolve().parents[1]/'static/assets/chemical-registry'
 paths=[base/name for name in ('registry.json','bindings.json','reader-3d-reference-overrides.json')]
 if not any(path.exists()for path in paths):return {}
 if not all(path.is_file()for path in paths):raise ValueError('Incomplete H chemistry inputs')
 raw=[path.read_bytes()for path in paths];registry,bindings,overlay=map(json.loads,raw)
 enrich_registry(registry,bindings,overlay,hashlib.sha256(raw[0]).hexdigest(),hashlib.sha256(raw[1]).hexdigest())
 return identity_context_from_chemistry(registry,bindings,overlay)
