from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import json,hashlib,math,re
B=Path(__file__).resolve().parent;V=B/'visuals'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def check(name,ok,note=''):checks.append({'check':name,'passed':bool(ok),'note':note})
entries=read(V/'registry-additions.json')['entries'];by={e['id']:e for e in entries}
expected={'carbon-dioxide':'CO2','perfluorooctanethiol':'C8H5F13S','perfluorodecanethiol':'C10H5F17S','heptane':'C7H16','dodecanethiol':'C12H26S','octanethiol':'C8H18S','hexanethiol':'C6H14S','trichlorotrifluoroethane':'C2Cl3F3','identity-shah-agno3':'AgNO3','identity-shah-ag-acac':'C5H7AgO2','identity-shah-pt-precursor':None,'identity-shah-fluorinert':None,'identity-shah-ag':'Ag','identity-shah-ir':'Ir','identity-shah-pt':'Pt','identity-shah-tem-grid':None,'identity-shah-metal-dispersion':None,'identity-shah-size-data':None}
unit_map={'carbon-dioxide':['chemical-co2'],'perfluorooctanethiol':['chemical-ligand'],'perfluorodecanethiol':['fig7-ii'],'heptane':['chemical-heptane'],'dodecanethiol':['fig7-iii'],'octanethiol':['comparison-octanethiol-spacing'],'hexanethiol':['scope-no-precursor-preparation'],'trichlorotrifluoroethane':['chemical-freon'],'identity-shah-agno3':['fig7-ii','fig7-iii'],'identity-shah-ag-acac':['chemical-ag'],'identity-shah-pt-precursor':['chemical-pt','conflict-pt-identity'],'identity-shah-fluorinert':['chemical-fluorinert'],'identity-shah-ag':['fig2c','fig11a'],'identity-shah-ir':['ir-conditions','fig8a'],'identity-shah-pt':['pt-conditions','fig8b'],'identity-shah-tem-grid':['chemical-tem-grid'],'identity-shah-metal-dispersion':['synthesis-variant-inheritance'],'identity-shah-size-data':['characterization-size-analysis']}
check('18-distinct-reference-entries',set(by)==set(expected))
for e in entries:
 i=e['id'];check(i+'/formula',e['formula']==expected[i]);check(i+'/unmeasured',e['provenance']['measuredCoordinates'] is False);check(i+'/not-training',e['provenance']['eligible_training'] is False)
 check(i+'/source-hash',e['provenance']['sourceSha256']=='2e6310ab5f5c6102ffa46e91dc3ccc2a180e6a6d17fd6a82ef448867edd79967')
 for field,h in e['assetHashes'].items():check(i+'/'+field+'/hash',sha(V/e[field])==h)
 if e['depictionKind']=='molecule':
  target=Counter({el:int(n or 1) for el,n in re.findall(r'([A-Z][a-z]?)(\d*)',e['formula'])})
  for field in ['model2dPath','model3dPath']:
   m=read(V/e[field]);atoms=m['atoms'];got=Counter(a['element'] for a in atoms)
   got['H']+=sum(a.get('implicitHydrogenCount',0) for a in atoms)
   if got['H']==0:del got['H']
   check(i+'/'+field+'/elemental-count',got==target,str(dict(got)))
   check(i+'/'+field+'/finite-coordinates',all(math.isfinite(a.get(axis,0)) for a in atoms for axis in ['x','y','z']))
   check(i+'/'+field+'/valid-bonds',all(0<=b['a']<len(atoms) and 0<=b['b']<len(atoms) for b in m['bonds']))
   check(i+'/'+field+'/not-training',m['eligible_training'] is False)
   for g in m['functionalGroups']:
    check(i+'/'+field+'/'+g['label']+'/indices',all(0<=a<len(atoms) for a in g['atomIndices']) and all(0<=b<len(m['bonds']) for b in g['bondIndices']))
    if g['label']=='Thiol group':check(i+'/'+field+'/thiol-is-S',all(atoms[a]['element']=='S' for a in g['atomIndices']))
    if g['label']=='Fluorinated segment':check(i+'/'+field+'/fluoro-is-C-or-F',all(atoms[a]['element'] in ['C','F'] for a in g['atomIndices']))
  check(i+'/caption-free-reference','Neither drawing nor conformer is a measured' in e['caption'])
 else:check(i+'/no-guessed-geometry',e['model2dPath'] is None and e['model3dPath'] is None)
ir_path=B.parents[3]/'recipe-atlas/dist/assets/chemical-registry/registry.json'
ir=next(e for e in read(ir_path)['entries'] if e['id']=='ir-mecp-cod')
check('reused-ir/formula',ir['formula']=='C14H19Ir')
check('reused-ir/no-guessed-haptic-bonds',ir['model2dPath'] is None and ir['model3dPath'] is None and ir['depictionKind']=='formula')
check('reused-ir/limited-caption','No discrete metal coordination' in ir['caption'])
irsvg=ir_path.parent/ir['svgPath'];check('reused-ir/asset-hash',sha(irsvg)==ir['assetHashes']['svgPath'])
reuse=read(V/'reused-reference-audit-input.json')['entries']
reuse_formulas={'hydrogen':'H2','acetone':'C3H6O','ir-mecp-cod':'C14H19Ir','water':'H2O','chloroform':'CHCl3','hexane':'C6H14','ethanol':'C2H6O'}
check('seven-reused-reference-identities',set(reuse)==set(reuse_formulas))
for name,wrapper in reuse.items():
 e=wrapper['entry'];check(name+'/reused-formula',e['formula']==reuse_formulas[name])
 for field,h in wrapper['assetHashes'].items():check(name+'/'+field+'/reused-hash',sha(ir_path.parent/e[field])==h)
 check(name+'/reused-caption-limited','measured' in e['caption'] or 'No discrete metal coordination' in e['caption'])
bindings=read(V/'bindings-additions.json');product_bindings=read(V/'product-reference-proposal.json')
expected_bindings={'agacac':'identity-shah-ag-acac','ir-precursor':'ir-mecp-cod','pt-precursor':'identity-shah-pt-precursor','c8-thiol':'perfluorooctanethiol','co2':'carbon-dioxide','hydrogen':'hydrogen','acetone':'acetone','heptane':'heptane','fluorinert':'identity-shah-fluorinert','freon':'trichlorotrifluoroethane','c10-thiol':'perfluorodecanethiol','dodecanethiol':'dodecanethiol','octanethiol':'octanethiol','hexanethiol':'hexanethiol','ag-no3':'identity-shah-agno3','water':'water','chloroform':'chloroform','hexane':'hexane','ethanol':'ethanol','grid':'identity-shah-tem-grid','specimen':'identity-shah-metal-dispersion','distributions':'identity-shah-size-data'}
binding_count=0
for p in (B/'canonical-drafts').glob('*.json'):
 r=read(p);rid=r['record_id'];mapping=bindings['recordBindings'][rid]
 check(rid+'/binding-record-hash',sha(p)==bindings['sourceRecordSha256'][rid])
 check(rid+'/all-materials-bound',set(mapping)=={m['id'] for m in r['materials']})
 for m in r['materials']:
  binding_count+=1;check(rid+'/'+m['id']+'/identity-map',mapping[m['id']]==expected_bindings[m['id']])
check('99-material-bindings',binding_count==99)
expected_products={'shah-2001-ag-'+c:'identity-shah-ag' for c in 'abcdefghi'}
expected_products.update({'shah-2001-ag-structure':'identity-shah-ag','shah-2001-ag-typical-framework':'identity-shah-ag','shah-2001-ir':'identity-shah-ir','shah-2001-pt':'identity-shah-pt'})
check('13-source-specific-product-cards',product_bindings['recordBindings']==expected_products)
semantic=[
 'All 18 names, formulas, captions and scope distinctions were read against the complete supplied article; all three contact sheets were independently visually inspected. Updated sheets 2/3 including AgNO3 were inspected after the 18-entry regeneration.',
 'The C8 reagent is C6F13C2H4SH (C8H5F13S); the C10 prior comparator is C8F17C2H4SH (C10H5F17S). They remain different chemical identities and source roles. The drawings correctly show the two nonfluorinated carbons and terminal SH.',
 'Heptane and named straight-chain alkanethiols are reference connectivities. Their computed conformers do not prove the solution conformation or a surface adsorption geometry; no such measured-coordinate claim is made.',
 'The depicted 1,1,2-trichlorotrifluoroethane connectivity has two carbon atoms, three chlorine and three fluorine atoms with the specified chlorine substitution pattern.',
 'Ag(acac) is formula-only; the paper does not establish a discrete coordination geometry. The Pt name is ambiguous as printed and remains unresolved without a guessed formula or cyclooctadiene substitution.',
 'The reused Ir identity matches the explicitly named (methylcyclopentadienyl)(1,5-cyclooctadiene)iridium reagent, C14H19Ir. Existing formula-only reference correctly avoids guessed ordinary covalent bonds for haptic coordination. Its original provenance cites a different paper; present-source binding must cite Shah independently.',
 'The added AgNO3 card correctly identifies prior Figure 7 optical comparisons. It is explicitly excluded from the current Ag(acac)/scCO2 reaction precursor role.',
 'Fluorinert has no invented grade or single formula. TEM grid, generic separate-metal specimen, analytical-data input and product cards are not fictitious molecules or mixed-metal alloys. Ag/Ir/Pt cards are not solved crystal structures.',
 'Computed 2D and 3D asset elemental counts, coordinates, bond endpoints, highlighted-group indices and hashes pass independent checks. The contact sheets visually show 2D drawings/cards; this audit does not claim interactive 3D browser testing.'
 ,'All 99 material bindings across 19 canonical records preserve source material identities and source roles. Seven reused references (H2, acetone, Ir precursor, water, chloroform, hexane and ethanol) have matching formulas and preserved asset hashes. Current H2/acetone roles are distinct from cited aqueous/chloroform/hexane comparisons and ethanol discussion.'
 ,'Thirteen product cards identify only the Ag A–I routes, typical Ag framework, Ag structural context, Ir and Pt. No mixed specimen, optical comparator or theoretical-model record is assigned a false single product structure.'
]
failed=[c for c in checks if not c['passed']]
report={'schema':'mattersyn-independent-molecular-source-audit-1','source_id':'shah2001','status':'passed_with_reference_limits' if not failed else 'failed','checked_utc':datetime.now(timezone.utc).isoformat(),'registry_sha256':sha(V/'registry-additions.json'),'entry_count':len(entries),'computed_molecules':8,'reference_only_cards':10,'source_inventory_sha256':sha(B/'source-audit.json'),'semantic_review':semantic,'check_count':len(checks),'failure_count':len(failed),'checks':checks,'failures':failed,'visual_coverage':[{'file':str(V/'review'/('molecular-contact-'+str(n)+'.png')),'sha256':sha(V/'review'/('molecular-contact-'+str(n)+'.png')),'actually_viewed':True} for n in [1,2,3]],'reused_ir_registry_sha256':sha(ir_path),'reused_ir_entry':ir,'reused_ir_svg_sha256':sha(irsvg),'publication_or_browser_verified':False}
report.update(binding_count=binding_count,product_binding_count=len(expected_products),reused_reference_count=7,bindings_sha256=sha(V/'bindings-additions.json'),product_bindings_sha256=sha(V/'product-reference-proposal.json'),reused_reference_input_sha256=sha(V/'reused-reference-audit-input.json'))
(B/'molecular-source-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(B/'molecular-source-audit.md').write_text('# Independent molecular source audit: Shah et al. (2001)\n\nStatus: '+report['status']+'. Eighteen new references and one reused Ir identity reviewed; '+str(len(checks))+' checks, '+str(len(failed))+' failures.\n\n'+'\n\n'.join(semantic)+'\n\nExact hashes are retained in molecular-source-audit.json.\n',encoding='utf8')
print(json.dumps({'status':report['status'],'checks':len(checks),'failures':failed,'audit_sha256':sha(B/'molecular-source-audit.json')}))
