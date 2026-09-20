"""Read-only qualification of nine existing Gu molecular assets; no model generation."""
from pathlib import Path
from collections import Counter, deque
from datetime import datetime, timezone
import json, hashlib, math, re, sys, xml.etree.ElementTree as ET
sys.dont_write_bytecode=True
B=Path(__file__).resolve().parent
RESEARCH=Path(r'[local path redacted]')
REG=Path(r'[local path redacted]')
RAW=RESEARCH/'quality-20260918/molecules/raw'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,d): Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
plan=read(B/'visual-reuse-plan.json'); reg=read(REG/'registry.json'); inv=read(B/'source-inventory.json')
entries={e['id']:e for e in reg['entries']}; sources={m['id']:m for m in inv['materials']}
checks=[]; asset_hashes={}; results=[]
frozen={str(p):sha(p) for p in (B/'canonical-drafts').glob('*.json')}
def ck(condition,label,issues):
    checks.append({'passed':bool(condition),'check':label})
    if not condition:issues.append(label)
def formula(atoms):
    c=Counter(a['element'] for a in atoms)
    c['H']+=sum(a.get('implicitHydrogenCount',0) for a in atoms)
    return {k:v for k,v in c.items() if v}
def formula_text(raw): return {k:int(v or 1) for k,v in re.findall(r'([A-Z][a-z]?)(\d*)',raw)}
def edges(m,heavy=True):
    return sorted((min(b['a'],b['b']),max(b['a'],b['b']),float(b['order'])) for b in m['bonds']
        if not heavy or m['atoms'][b['a']]['element']!='H' and m['atoms'][b['b']]['element']!='H')
def sdf(path):
    ls=Path(path).read_text(encoding='utf-8').splitlines();na=int(ls[3][:3]);nb=int(ls[3][3:6])
    aa=[{'index':i,'element':s[31:34].strip(),'x':float(s[:10]),'y':float(s[10:20]),'z':float(s[20:30])} for i,s in enumerate(ls[4:4+na])]
    bb=[{'a':int(s[:3])-1,'b':int(s[3:6])-1,'order':int(s[6:9])} for s in ls[4+na:4+na+nb]]
    return {'atoms':aa,'bonds':bb}
def norm_heavy(m):
    inds=[i for i,a in enumerate(m['atoms']) if a['element']!='H'];mp={v:i for i,v in enumerate(inds)}
    return [m['atoms'][i]['element'] for i in inds],sorted((min(mp[a],mp[b]),max(mp[a],mp[b]),o) for a,b,o in edges(m) )
def adjacency(m):
    d={i:[] for i in range(len(m['atoms']))}
    for b in m['bonds']:
        d[b['a']].append((b['b'],b['order']));d[b['b']].append((b['a'],b['order']))
    return d
def stereo_cos(m):
    bb=[b for b in m['bonds'] if b['order']==2 and m['atoms'][b['a']]['element']==m['atoms'][b['b']]['element']=='C']
    if len(bb)!=1:return None
    b=bb[0];a,z=b['a'],b['b'];ad=adjacency(m)
    x=next(i for i,o in ad[a] if i!=z and m['atoms'][i]['element']!='H')
    y=next(i for i,o in ad[z] if i!=a and m['atoms'][i]['element']!='H')
    def vec(i,j):return [m['atoms'][i][k]-m['atoms'][j][k] for k in ['x','y','z']]
    def dot(a,b):return sum(x*y for x,y in zip(a,b))
    axis=vec(z,a);den=dot(axis,axis)
    v=vec(x,a);w=vec(y,z)
    v=[v[i]-dot(v,axis)/den*axis[i] for i in range(3)]
    w=[w[i]-dot(w,axis)/den*axis[i] for i in range(3)]
    return dot(v,w)/(dot(v,v)*dot(w,w))**.5

global_issues=[]
ck(sha(B/'source-inventory.json')==plan['source_inventory_sha256'],'Plan source-inventory hash matches',global_issues)
ck(sha(REG/'registry.json')==plan['registry_sha256'],'Plan registry hash matches',global_issues)
for cand in plan['materials']:
    if not cand['candidate_registry_id']:continue
    cid=cand['candidate_registry_id'];e=entries[cid];issues=[];models={};stats={}
    ck(cand['source_material_id'] in sources,cid+' source material resolves',issues)
    ck(e['formula']==cand['candidate_formula'] and e['name']==cand['candidate_name'],cid+' planned identity matches registry',issues)
    for key in ['svgPath','model2dPath','model3dPath']:
        p=(REG/e[key]).resolve();ck(p.is_relative_to(REG) and p.exists(),cid+' safe existing '+key,issues)
        digest=sha(p);asset_hashes[str(p)]=digest
        ck(digest==cand['asset_hashes'][key]==e['assetHashes'][key],cid+' exact plan/registry/current hash '+key,issues)
        if key!='svgPath':models[key]=read(p)
    svg=(REG/e['svgPath']).read_text(encoding='utf-8');root=ET.fromstring(svg)
    ck(root.tag.endswith('svg') and ('viewBox' in root.attrib or 'width' in root.attrib),cid+' valid declared SVG',issues)
    ck(not re.search(r'<script|onload=|javascript:|(?:href|src)=[\"\']https?://',svg,re.I),cid+' passive self-contained SVG',issues)
    props_path=RAW/(cid+'-properties.json');sdf_path=RAW/(cid+'-pubchem-2d.sdf')
    props=read(props_path)['PropertyTable']['Properties'][0];original=sdf(sdf_path)
    for p in [props_path,sdf_path]:asset_hashes[str(p)]=sha(p)
    ck(sha(props_path)==e['provenance']['sourcePropertiesSha256'],cid+' cached property provenance hash',issues)
    ck(sha(sdf_path)==e['provenance']['source2dSha256'],cid+' cached SDF provenance hash',issues)
    ck(props['CID']==e['pubchemCid'] and props['MolecularFormula']==e['formula'],cid+' cached PubChem identity/formula',issues)
    # The diol's two strings differ only in branch traversal at the same terminal
    # secondary carbon: (CO)O and (O)CO both mean CH(OH)-CH2OH, with no stereo tag.
    diol_branch_equivalent=(cid=='hexadecane-1-2-diol' and
        {props['SMILES'],e['provenance']['smiles']}=={'CCCCCCCCCCCCCCC(CO)O','CCCCCCCCCCCCCCC(O)CO'})
    ck(props['SMILES']==e['provenance']['smiles'] or diol_branch_equivalent,cid+' cached stereochemical connectivity string (identical or manually verified diol branch traversal)',issues)
    for key,m in models.items():
        aa=m['atoms'];bb=m['bonds'];n=len(aa);ad=adjacency(m);d3=key=='model3dPath'
        ck([a['index'] for a in aa]==list(range(n)),cid+' consecutive zero-based atom indices '+key,issues)
        ck(all(all(math.isfinite(a[k]) for k in ['x','y','z']) for a in aa),cid+' finite coordinates '+key,issues)
        ck(all(0<=b['a']<n and 0<=b['b']<n and b['a']!=b['b'] and b['order'] in [1,2,3,1.5] for b in bb),cid+' valid bonds '+key,issues)
        ck(len(edges(m,False))==len(set(edges(m,False))),cid+' no duplicate edges '+key,issues)
        ck(formula(aa)==formula_text(e['formula']),cid+' actual atom/implicit-H formula '+key,issues)
        ck(norm_heavy(m)==norm_heavy(original),cid+' heavy connectivity matches retained PubChem SDF '+key,issues)
        ck(m['formula']==e['formula'] and m['pubchemCid']==e['pubchemCid'],cid+' model identity metadata '+key,issues)
        ck(m['representation']==('3d' if d3 else '2d') and m['has3D']==d3 and m['allowRotation']==d3,cid+' dimensional controls '+key,issues)
        ck(m['coordinateUnits']==('angstrom' if d3 else 'drawing units'),cid+' coordinate units '+key,issues)
        if not d3:ck(all(abs(a['z'])<1e-9 for a in aa),cid+' 2D geometry is labeled as planar '+key,issues)
        for g in m['functionalGroups']:
            gs=set(g['atomIndices']);ck(all(0<=i<n for i in gs),cid+' group atom indices '+g['label']+' '+key,issues)
            ck(all(0<=i<len(bb) and {bb[i]['a'],bb[i]['b']}<=gs for i in g['bondIndices']),cid+' group bond indices '+g['label']+' '+key,issues)
            els=Counter(aa[i]['element'] for i in gs)
            orders=sorted(bb[i]['order'] for i in g['bondIndices'])
            expected={'Amine nitrogen':({'N':1},[]),'Alkene':({'C':2},[2]),
                'Carboxylic acid':({'C':1,'O':2},[1,2]),'Alcohol group':({'O':1,'C':1},[1]),
                'Ether oxygen':({'O':1,'C':2},[1,1]),'Phosphine oxide':({'P':1,'O':1},[2])}
            ck(g['label'] in expected and dict(els)==expected[g['label']][0] and orders==expected[g['label']][1],cid+' functional-group chemical semantics '+g['label']+' '+key,issues)
        ck(all(abs(sum(o for j,o in ad[i])+a.get('implicitHydrogenCount',0)-{'H':1,'C':4,'N':3,'O':2,'P':5}[a['element']])<1e-6 for i,a in enumerate(aa)),cid+' neutral valence and hydrogen consistency '+key,issues)
        if cid in ['oleylamine','oleic-acid']:
            cos=stereo_cos(m);ck(cos is not None and cos>.9,cid+' alkene substituents are Z/cis '+key,issues)
        else:cos=None
        lengths=[math.dist([aa[b['a']][k] for k in ['x','y','z']],[aa[b['b']][k] for k in ['x','y','z']]) for b in bb]
        stats[key]={'atoms':n,'bonds':len(bb),'formula_counts':formula(aa),'functional_groups':m['functionalGroups'],
            'bond_length_min':min(lengths) if lengths else None,'bond_length_max':max(lengths) if lengths else None,
            'units':m['coordinateUnits'],'alkene_same_side_cosine':cos}
        if d3:
            ck(all(.7<d<2.1 for d in lengths),cid+' gross bond-length bounds (not bond-specific certification)',issues)
            pairs={(a,b) for a,b,o in edges(m,False)}
            nonbond=[math.dist([aa[i][k] for k in ['x','y','z']],[aa[j][k] for k in ['x','y','z']]) for i in range(n) for j in range(i+1,n) if (i,j) not in pairs]
            ck(not nonbond or min(nonbond)>.7,cid+' no gross nonbonded overlap',issues)
            stats[key]['minimum_nonbonded_distance']=min(nonbond) if nonbond else None
            ck('not' in m.get('caption','').lower() and ('computed' in m.get('modelType','').lower() or 'illustrative' in m.get('modelType','').lower()),cid+' model origin and nonexperimental caption',issues)
            if m.get('coordinateSource')=='local-rdkit':
                cg=m.get('conformerGeneration',{});ck('randomSeed' in cg and 'forceField' in cg and 'minimizationReturnCode' in cg,cid+' recorded conformer generation provenance',issues)
    ck(e['functionalGroups']==models['model2dPath']['functionalGroups'],cid+' registry group indices are for 2D model',issues)
    # The 3D model may reorder bond indices. Compare group-selected edges, not raw index values.
    for a,b in zip(models['model2dPath']['functionalGroups'],models['model3dPath']['functionalGroups']):
        ck(set(a['atomIndices'])==set(b['atomIndices']),cid+' 2D/3D group atom correspondence '+a['label'],issues)
    if cid in ['oleylamine','oleic-acid','hexane']:
        paths={'oleylamine':RESEARCH/'oleylamine-pubchem-5356789-3d.sdf',
               'oleic-acid':RESEARCH/'oleic-acid-pubchem-445639-3d.sdf',
               'hexane':RESEARCH/'new-molecular-assets/hexane-pubchem-8058-3d.sdf'}
        p=paths[cid];orig3=sdf(p);asset_hashes[str(p)]=sha(p);m=models['model3dPath']
        ck([a['element'] for a in m['atoms']]==[a['element'] for a in orig3['atoms']] and edges(m,False)==edges(orig3,False),cid+' 3D original SDF atom/bond correspondence',issues)
        ck(all(abs(a[k]-b[k])<1e-6 for a,b in zip(m['atoms'],orig3['atoms']) for k in ['x','y','z']),cid+' stored reference conformer coordinates unchanged',issues)
    results.append({'source_material_id':cand['source_material_id'],'registry_id':cid,'source_identity':sources[cand['source_material_id']],
        'registry_identity':{k:e[k] for k in ['name','formula','iupacName','pubchemCid','sourceUrls']},
        'registry_limitations':e.get('limitations',[]),'provenance':e['provenance'],
        'technical_integrity': 'passed' if not issues else 'blocked','technical_findings':issues,
        'model_checks':stats,'binding_approved':False,'publication_approved':False,
        'caveats':[],'qualification':'pending_source_specific_assessment'})

ASSESS={
 'oleylamine':('blocked_pending_source_specific_label',[
    'Connectivity and both conformers are a Z/cis oleylamine reference. The paper reports 97% oleylamine and no geometric-isomer fractions.',
    'The reusable registry limitation mentions technical/70% oleylamine from another context; do not expose that as Gu reagent grade.',
    'Reuse only as a named reference molecule, with Gu-specific 97% grade and no pure-Z assay or surface-bound conformation claim.']),
 'oleic-acid':('qualified_named_molecule_reference',[
    'The Z-octadec-9-enoic-acid identity matches the named oleic-acid reference. Retain Gu 99% grade separately.',
    'Show a free neutral acid reference, not a measured FePt-bound oleate or unique solution species.']),
 'hexadecane-1-2-diol':('blocked_pending_component_label',[
    'The reference is a 16-carbon chain with terminal 1,2-diol connectivity and unassigned stereochemistry.',
    'Gu uses technical 90% reagent; the pure-component C16H34O2 model cannot represent the entire reagent or an assigned R/S batch.',
    'Reuse only with named-component and unassigned-stereochemistry labels. The 195 mg and 105 mg additions remain separate.']),
 'dioctyl-ether':('qualified_named_molecule_reference',[
    'Cached reference identity is 1-octoxyoctane: two unbranched eight-carbon groups joined by oxygen, matching the named dioctyl ether.',
    'Retain Gu 99% grade. This structure does not supply the omitted numeric boiling temperature, pressure or unique solution conformation.']),
 'topo':('blocked_pending_component_label',[
    'Model connectivity is a pure trioctylphosphine-oxide component, with three C8 groups on P and a P=O bond.',
    'Gu doses technical 90% TOPO with unquantified impurities. Do not replace the mixture record by the pure-molecule formula.',
    'Reuse as the named component only; distinguish this from reagent assay, surface coordination or solution speciation.']),
 'water':('qualified_named_molecule_reference',[
    'H2O reference identity and connectivity are valid. DI qualification belongs to precursor dissolution only; recrystallization water is not explicitly called DI.',
    'One illustrative water molecule is not a liquid-water configuration or a solution complex.']),
 'ethanol':('qualified_named_molecule_reference',[
    'Ethanol connectivity is C–C–O with an alcohol group. Source gives no purity and no ethanol/water recrystallization ratio.',
    'Retain different recrystallization and antisolvent roles; no concentration or mixture structure is established by the molecular asset.']),
 'hexane':('blocked_pending_isomer_specificity_label',[
    'The existing candidate is unbranched n-hexane, while the paper says hexane without an isomer assay or supplier specification.',
    'A registry alias alone does not independently verify the historical solvent-isomer composition.',
    'Direct exact-reagent binding is blocked. An explicitly illustrative n-hexane reference may be used later without claiming source-verified isomer purity.']),
 'nitrogen':('blocked_3d_geometry_use_2d_only',[
    'N2 and the N≡N graph are correct. Final storage is explicitly nitrogen; the general inert reaction gas must remain unspecified.',
    'The current 3D N–N distance is 1.460 Å despite bond order 3. This is a bond-specific plausibility failure requiring independent physical-geometry review; generic bounds and MMFF convergence do not qualify it.',
    'The 2D N≡N connectivity depiction is qualified. Do not reuse this 3D asset until corrected or independently justified by a suitable reference. No correction was made here.']),
}
for r in results:
    status,caveats=ASSESS[r['registry_id']];r['qualification']=status;r['caveats']=caveats
    if r['technical_findings']:r['qualification']='blocked_technical_integrity'
    r['reuse_2d_as_reference']=not r['technical_findings']
    r['reuse_3d_as_reference']=not r['technical_findings'] and r['registry_id']!='nitrogen'
    r['requires_source_specific_label_before_binding']=r['qualification'].startswith('blocked_pending')
    if r['registry_id']=='nitrogen':
        r['model_checks']['model3dPath']['bond_specific_qualification']='blocked: N≡N at 1.460 Å; no physical reference justification in local asset provenance'

# Render exact existing SVG bytes for inspection; these previews are not new chemical models.
preview_paths=[]
sys.path.insert(0,str(RESEARCH/'corpus-20260917/runtime'))
import pymupdf
PREV=B/'visual-reuse-previews';PREV.mkdir(exist_ok=True)
for r in results:
    cid=r['registry_id'];p=REG/entries[cid]['svgPath'];doc=pymupdf.open(stream=p.read_bytes(),filetype='svg')
    target=PREV/(cid+'.png');doc[0].get_pixmap(alpha=False).save(str(target));doc.close()
    preview_paths.append({'registry_id':cid,'path':str(target),'sha256':sha(target),'source_svg_sha256':sha(p)})
sys.path.insert(0,str(RESEARCH/'rdkit-runtime'))
from PIL import Image,ImageDraw,ImageFont
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20)
canvas=Image.new('RGB',(1680,2000),'white');draw=ImageDraw.Draw(canvas)
for i,p in enumerate(preview_paths):
    im=Image.open(p['path']).convert('RGB');im.thumbnail((830,355));x=(i%2)*840;y=(i//2)*400
    canvas.paste(im,(x,y+35));draw.text((x+12,y+7),p['registry_id'],font=font,fill='#172b37')
contact=PREV/'all-nine.png';canvas.save(contact)
for path,digest in frozen.items():ck(sha(path)==digest,'Frozen canonical file unchanged: '+Path(path).name,global_issues)
report={'schema':'mattersyn-private-visual-reuse-audit/1','source_id':'gu2004','reviewer':'/root/peng1998_reader_assets',
    'at':datetime.now(timezone.utc).isoformat(),'status':'completed_with_blocked_reuse',
    'scope':'Local-only identity/connectivity/formula, finite-coordinate/index/group/provenance and Gu-specific reuse qualification. No new models, Site writes, binding or publication audit.',
    'plan_sha256':sha(B/'visual-reuse-plan.json'),'registry_sha256':sha(REG/'registry.json'),'source_inventory_sha256':sha(B/'source-inventory.json'),
    'source_facts_sha256':sha(B/'source-facts.json'),'plan_path':str(B/'visual-reuse-plan.json'),
    'checked_candidates':len(results),'new_depictions_pending':8,'checks':len(checks),'failed_integrity_checks':[c for c in checks if not c['passed']],
    'global_issues':global_issues,'results':results,'inspected_asset_hashes':asset_hashes,
    'previews':preview_paths,'contact_sheet':{'path':str(contact),'sha256':sha(contact)},
    'actual_svg_visual_inspection':'All nine SVG-derived previews actually inspected together at readable scale: graph shapes, functional-group highlights and labels match the reference identities. Water is shown by its formula. No 3D viewer/runtime inspection is claimed.',
    'provenance_normalization_note':'Diol cached SMILES CCCCCCCCCCCCCCC(CO)O and registry CCCCCCCCCCCCCCC(O)CO use equivalent branch traversal, independently checked against the matching retained SDF/model graph; this is not a stereochemical assignment.',
    'provenance_limit':'Official-reference URLs, cached API properties and original SDF bytes were checked locally. No website was fetched and no fresh external-source verification is claimed.',
    'all_binding_approvals':False,'published':False,'training_eligible':False,
    'frozen_canonical_hashes_unchanged':True,'full_binding_or_runtime_audit':False}
write(B/'visual-reuse-audit.json',report)
print(json.dumps({'candidates':len(results),'checks':len(checks),'failed_integrity_checks':len(report['failed_integrity_checks']),
    'qualification_counts':dict(Counter(r['qualification'] for r in results))},ensure_ascii=False))
