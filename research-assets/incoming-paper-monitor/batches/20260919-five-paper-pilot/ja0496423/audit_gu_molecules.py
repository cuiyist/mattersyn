"""Independent read-only Gu molecular/reference and reagent-binding audit.
Run only after the author freezes the package; reports are private in this folder.
"""
from pathlib import Path
from collections import Counter
from copy import deepcopy
from datetime import datetime,timezone
import hashlib,json,math,re,sys,xml.etree.ElementTree as ET
sys.dont_write_bytecode=True
B=Path(__file__).resolve().parent;M=B/'visuals/molecules'
R=Path(r'[local path redacted]')
sys.path.insert(0,str(R/'rdkit-runtime'))
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors

def read(p):return json.loads(Path(p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks=[];files={};stats={}
def ck(ok,label,detail=None):checks.append({'passed':bool(ok),'check':label,**({'detail':detail} if detail else {})})
def bind(p):files[str(p)]=sha(p);return p
def atom_formula(m):
    c=Counter(a['element'] for a in m['atoms']);c['H']+=sum(a.get('implicitHydrogenCount',0) for a in m['atoms'])
    return {k:v for k,v in c.items() if v}
def parseformula(s):return {e:int(n or 1) for e,n in re.findall(r'([A-Z][a-z]?)(\d*)',s)}
def edges(m):return sorted((min(b['a'],b['b']),max(b['a'],b['b']),float(b['order'])) for b in m['bonds'])
def rd_edges(m):return sorted((min(b.GetBeginAtomIdx(),b.GetEndAtomIdx()),max(b.GetBeginAtomIdx(),b.GetEndAtomIdx()),b.GetBondTypeAsDouble()) for b in m.GetBonds())
def rd_sig(m):return ([(a.GetSymbol(),a.GetFormalCharge(),a.GetTotalNumHs()) for a in m.GetAtoms()],rd_edges(m))
def model_sig(m):return ([(a['element'],a.get('formalCharge',0),a.get('implicitHydrogenCount',0)) for a in m['atoms']],edges(m))
def sdf(p):
    mol=Chem.MolFromMolBlock(Path(p).read_text(encoding='utf8'),removeHs=True,sanitize=True)
    assert mol is not None,p
    return mol
def components(m):
    ad={i:set() for i in range(len(m['atoms']))}
    for a,b,o in edges(m):ad[a].add(b);ad[b].add(a)
    unseen=set(ad);cc=[]
    while unseen:
        todo=[min(unseen)];v=set()
        while todo:
            i=todo.pop()
            if i in v:continue
            v.add(i);todo.extend(ad[i]-v)
        cc.append(sorted(v));unseen-=v
    return cc
def component_sig(m,ids):
    remap={n:i for i,n in enumerate(ids)}
    return ([(m['atoms'][i]['element'],m['atoms'][i].get('formalCharge',0),m['atoms'][i].get('implicitHydrogenCount',0)) for i in ids],
            sorted((min(remap[a],remap[b]),max(remap[a],remap[b]),o) for a,b,o in edges(m) if a in remap and b in remap))

reg=read(bind(M/'registry-additions.json'));entries={e['id']:e for e in reg['entries']}
bindings=read(bind(M/'molecule-bindings-proposal.json'));plan=read(bind(B/'visual-reuse-plan.json'))
inv=read(bind(B/'source-inventory.json'));facts=read(bind(B/'source-facts.json'))
reuse=read(bind(B/'visual-reuse-audit.json'));audit=read(bind(B/'canonical-records-audit.json'))
before=read(bind(M/'input-hashes-before.json'))
models={};expected={'triethylamine':'C6H15N','acetylacetone':'C5H8O2','dibromoanthracene':'C14H8Br2','platinum-acac':'C10H14O4Pt','cadmium-acac':'C10H14CdO4','iron-pentacarbonyl':'C5FeO5','cadmium-chloride':'CdCl2','sulfur-element':'S','nitrogen':'N2'}
ck(set(entries)=={'gu2004-'+k+'-reference' for k in expected},'Exactly eight missing references plus nitrogen replacement')
for e in entries.values():
    cid=e['id'];key=cid.removeprefix('gu2004-').removesuffix('-reference')
    ck(parseformula(e['formula'])==parseformula(expected[key]),'Reference formula: '+cid)
    ck(not e['published'] and not e['eligible_training'],'Private nontraining reference: '+cid)
    sv=M/e['svgPath'];bind(sv);ck(sha(sv)==e['assetHashes']['svgPath'],'Exact SVG hash: '+cid)
    xml=ET.fromstring(sv.read_text(encoding='utf8'));svtext=sv.read_text(encoding='utf8')
    ck(xml.tag.endswith('svg') and 'viewBox' in xml.attrib,'Parseable SVG view box: '+cid)
    ck(not re.search(r'<script|onload=|javascript:|(?:href|src)=[\"\']https?://',svtext,re.I),'Passive local SVG: '+cid)
    prev=M/'review'/f'{cid}.png';bind(prev)
    ck(prev.is_file(),'Actually inspected original SVG preview present: '+cid)
    for dim in ['2d','3d']:
        field='model'+dim+'Path'
        if not e.get(field):continue
        p=M/e[field];m=read(bind(p));models[(key,dim)]=m
        ck(sha(p)==e['assetHashes'][field],'Exact model hash: '+cid+' '+dim)
        ck(m['id']==cid and parseformula(m['formula'])==parseformula(e['formula']),'Model identity: '+cid+' '+dim)
        aa=m['atoms'];bb=m['bonds'];n=len(aa)
        ck([a['index'] for a in aa]==list(range(n)),'Zero-based complete indices: '+cid+' '+dim)
        ck(all(math.isfinite(a[k]) for a in aa for k in ['x','y','z']),'Finite coordinates: '+cid+' '+dim)
        ck(all(0<=b['a']<n and 0<=b['b']<n and b['a']!=b['b'] and b['order'] in [1,1.5,2,3] for b in bb),'Valid bond endpoints/orders: '+cid+' '+dim)
        ck(len(edges(m))==len(set(edges(m))),'No duplicate graph edges: '+cid+' '+dim)
        ck(atom_formula(m)==parseformula(e['formula']),'Actual formula including implicit H: '+cid+' '+dim)
        ck(sum(a.get('formalCharge',0) for a in aa)==0,'Overall neutral stoichiometric reference: '+cid+' '+dim)
        ck(m['representation']==dim and m['has3D']==(dim=='3d') and m['allowRotation']==(dim=='3d'),'Truthful dimensional controls: '+cid+' '+dim)
        ck(m['coordinateUnits']==('angstrom' if dim=='3d' else 'drawing units'),'Coordinate units: '+cid+' '+dim)
        ck(not m['eligible_training'],'Reference model not admitted to training: '+cid+' '+dim)
        if dim=='2d':ck(all(abs(a['z'])<1e-9 for a in aa),'2D is visibly and explicitly planar: '+cid)
        for g in m['functionalGroups']:
            ids=g['atomIndices'];bs=g['bondIndices'];label=g['label']
            ck(ids and len(ids)==len(set(ids)) and all(0<=i<n for i in ids),'Group atom indices: '+cid+' '+dim+' '+label)
            ck(all(0<=i<len(bb) and {bb[i]['a'],bb[i]['b']}<=set(ids) for i in bs),'Group bond indices: '+cid+' '+dim+' '+label)
            els=Counter(aa[i]['element'] for i in ids);orders=[bb[i]['order'] for i in bs]
            if label=='Tertiary amine center':good=els=={'N':1,'C':3} and orders==[1,1,1]
            elif label=='Ketone carbonyl':good=els=={'O':1,'C':3} and sorted(orders)==[1,1,2]
            elif label=='Aryl bromide':good=els=={'Br':1,'C':1} and orders==[1]
            elif label=='Acetylacetonate resonance fragment':good=els=={'C':3,'O':2} and sorted(orders)==[1,1,2,2]
            elif label=='Formal metal center':good=len(ids)==1 and aa[ids[0]]['element'] in ['Cd','Pt','Fe'] and not bs
            elif label=='Carbon monoxide ligand fragment':good=els=={'C':1,'O':1} and orders==[3]
            elif label=='Chloride ion':good=els=={'Cl':1} and aa[ids[0]]['formalCharge']==-1 and not bs
            elif label=='Dinitrogen triple bond':good=els=={'N':2} and orders==[3]
            else:good=False
            ck(good,'Chemical group semantics: '+cid+' '+dim+' '+label)
        if dim=='3d':
            lengths=[]
            for b in bb:
                a,z=aa[b['a']],aa[b['b']];pair='-'.join(sorted([a['element'],z['element']]))
                d=math.dist([a[k] for k in ['x','y','z']],[z[k] for k in ['x','y','z']]);lengths.append(d)
                low,high={'C-C':(1.15,1.8),'C-O':(1.1,1.45),'C-N':(1.2,1.7),'Br-C':(1.7,2.1),'N-N':(1.09,1.11)}[pair]
                ck(low<d<high,'Bond-specific plausibility: '+cid+' '+str(b['a'])+'-'+str(b['b']),{'angstrom':d,'element_pair':pair})
            occupied={(a,b) for a,b,o in edges(m)}
            ds=[math.dist([aa[a][k] for k in ['x','y','z']],[aa[b][k] for k in ['x','y','z']]) for a in range(n) for b in range(a+1,n) if (a,b) not in occupied]
            ck(not ds or min(ds)>1.0,'No gross nonbonded collision: '+cid)
            stats[cid]={'atoms':n,'bonds':len(bb),'bond_min':min(lengths),'bond_max':max(lengths),'minimum_nonbonded':min(ds) if ds else None}
    if e.get('model2dPath'):ck(e['functionalGroups']==models[(key,'2d')]['functionalGroups'],'Registry groups refer to actual 2D model: '+cid)
    # Every referenced file digest must resolve inside this private package.
    def provenance_files(x):
        if isinstance(x,dict):
            if 'path' in x and 'sha256' in x:
                p=M/x['path'];bind(p);ck(p.resolve().is_relative_to(M) and sha(p)==x['sha256'],'Cached provenance hash: '+cid+' '+x['path'])
            for y in x.values():provenance_files(y)
        elif isinstance(x,list):
            for y in x:provenance_files(y)
    provenance_files(e['provenance'])

# Independently read SDF graphs with chemistry sanitization; no asset-author
# helper or serialized claim is used as the connectivity oracle.
for name in ['triethylamine','acetylacetone','dibromoanthracene']:
    props=read(bind(M/'raw'/f'{name}-properties.json'))['PropertyTable']['Properties'][0]
    e=entries['gu2004-'+name+'-reference']
    ck(props['CID']==e['pubchemCid'] and parseformula(props['MolecularFormula'])==parseformula(e['formula']),'Cached primary identity: '+name)
    for dim in ['2d','3d']:
        p=bind(M/'raw'/f'{name}-pubchem-{dim}.sdf');mol=sdf(p);m=models[(name,dim)]
        ck(rd_sig(mol)==model_sig(m),'Exact retained reference graph/charge/H: '+name+' '+dim)
        if dim=='3d':
            conf=mol.GetConformer()
            ck(all(abs(m['atoms'][i][k]-getattr(conf.GetAtomPosition(i),k))<1e-6 for i in range(mol.GetNumAtoms()) for k in ['x','y','z']),'Exact original computed 3D coordinates: '+name)
            ck(m['rawSourceSha256']==sha(p) and 'pubchem' in m['coordinateSource'].lower(),'3D computed-reference provenance: '+name)
    ck(model_sig(models[(name,'2d')])==model_sig(models[(name,'3d')]),'2D/3D identity and bond-order equivalence: '+name)
ligand=sdf(bind(M/'raw/acetylacetonate-pubchem-2d.sdf'))
ck(rdMolDescriptors.CalcMolFormula(ligand)=='C5H7O2-','Acetylacetonate anion formula independently computed')
for name,metal in [('platinum-acac','Pt'),('cadmium-acac','Cd')]:
    m=models[(name,'2d')];cc=components(m);single=[x for x in cc if len(x)==1];ls=[x for x in cc if len(x)>1]
    ck(len(cc)==3 and len(single)==1 and len(ls)==2,'Two ligand fragments plus separate metal: '+name)
    ck(m['atoms'][single[0][0]]['element']==metal and m['atoms'][single[0][0]]['formalCharge']==2,'Formal divalent metal component: '+name)
    for ids in ls:ck(component_sig(m,ids)==rd_sig(ligand),'Exact deprotonated ligand graph copy: '+name+' '+str(ids[0]))
    ck(not entries['gu2004-'+name+'-reference']['model3dPath'],'No invented metal coordination/3D: '+name)
co=sdf(bind(M/'raw/iron-pentacarbonyl-pubchem-2d.sdf'));m=models[('iron-pentacarbonyl','2d')]
ck(model_sig(m)==rd_sig(co),'Fe(CO)5 exact disconnected primary reference graph')
ck(sorted(len(x) for x in components(m))==[1,2,2,2,2,2] and len(m['bonds'])==5,'Fe plus five CO fragments only')
m=models[('cadmium-chloride','2d')]
ck(not m['bonds'] and Counter((a['element'],a['formalCharge']) for a in m['atoms'])=={('Cd',2):1,('Cl',-1):2},'CdCl2 formal ions, no invented linear coordination/lattice')
ck(entries['gu2004-sulfur-element-reference']['model2dPath'] is None and entries['gu2004-sulfur-element-reference']['model3dPath'] is None,'Sulfur remains unassigned elemental identity, no S8 or monatomic molecule')
nit=read(bind(M/'raw/nitrogen-nist-extracted-reference.json'));nm=models[('nitrogen','3d')]
nd=math.dist([nm['atoms'][0][k] for k in ['x','y','z']],[nm['atoms'][1][k] for k in ['x','y','z']])
ck(abs(nd-nit['depiction_value_angstrom'])<1e-12 and abs(nd-1.09768)<1e-12,'N2 replacement equals stated reference-distance construction')
ck(nm['referenceIsotopologue']=='14N2','Reference isotopologue retained, not Gu isotope assay')
ck(abs(nd-1.46)>0.3,'Old suspect nitrogen geometry not reused')
nist_excerpt_path=bind(M/'raw/nitrogen-nist-web-tool-excerpt.txt')
nist_excerpt=nist_excerpt_path.read_text(encoding='utf8')
ck(all(s in nist_excerpt for s in ['X ^{1}Σ_{g}^{+}','1.09768_{5}','internuclear distance (Å)','Diatomic constants for ^{14}N_{2}','r_{e}  | Trans.']),
   'Actual returned NIST ground-state row, isotope and column units independently inspected')

# Reagent-binding identity is checked independently against every canonical slot
# and the source material inventory. Product specimen slots stay explicitly out.
allrecs={p.stem:read(bind(p)) for p in (B/'canonical-drafts').glob('*.json')}
source_materials={m['id']:m for m in inv['materials']};bound=[]
for rid,ms in bindings['recordBindings'].items():
    mats={m['id']:m for m in allrecs[rid]['materials']}
    ck(bindings['sourceRecordSha256'][rid]==sha(B/'canonical-drafts'/f'{rid}.json'),'Binding uses frozen canonical record: '+rid)
    for mid,aid in ms.items():
        bound.append((rid,mid));note=bindings['bindingNotes'][rid][mid]
        ck(mid in mats and mats[mid]['role']!='specimen','Existing non-specimen canonical slot: '+rid+' / '+mid)
        ck(note['source_material_id'] in source_materials and note['registry_id']==aid,'Source inventory identity resolves: '+rid+' / '+mid)
        ck(note['source_name']==mats[mid]['name'] and note['source_role']==mats[mid]['role'] and note['source_stage']==mats[mid]['stage'],'Canonical identity/role/stage preserved: '+rid+' / '+mid)
        ck(note['canonical_evidence']==mats[mid]['evidence'] and note['source_notes']==mats[mid]['notes'],'Exact source evidence and caveats retained: '+rid+' / '+mid)
        ck(note['viewOverrides']['caption']==note['display_scope'] and note['display_scope'] in note['viewOverrides']['limitations'],'Source-specific scope reaches view override: '+rid+' / '+mid)
        ck(not note['binding_approved'],'Draft binding does not self-approve: '+rid+' / '+mid)
expected_slots={(rid,m['id']) for rid,r in allrecs.items() for m in r['materials'] if m['role']!='specimen'}
uncovered={(v['record_id'],v['material_id']) for v in bindings['uncovered_specimen_slots']}
ck(set(bound)==expected_slots and len(bound)==20,'All twenty reagent slots covered exactly')
ck(uncovered=={(rid,m['id']) for rid,r in allrecs.items() for m in r['materials'] if m['role']=='specimen'} and len(uncovered)==8,'Eight specimen slots separately assigned to root')
ck(set(bindings['inventoryMaterialReferences'])==set(source_materials),'All seventeen source chemical identities represented')
def scope(rid,mid):return bindings['bindingNotes']['gu-2004-'+rid][mid]['display_scope']
for rid,mid,words in [('heterodimer','oleylamine',['97%','cis/Z','unassayed']),('heterodimer','diol',['technical 90%','Stereochemistry']),('heterodimer','topo',['90%','mixture']),('cdacac-preparation','water',['initial dissolution','recrystallization water not explicitly DI']),('heterodimer','hexane',['n-hexane','unreported']),('heterodimer','iron-pentacarbonyl',['98% must not be transferred']),('heterodimer','nitrogen',['storage','reaction gas']),('optical','dibromoanthracene',['standard','not a synthesis reagent'])]:
    ck(all(w in scope(rid,mid) for w in words),'Required source-specific display caveat: '+mid)
ck(bindings['recordBindings']['gu-2004-heterodimer']['nitrogen']=='gu2004-nitrogen-reference','Final-storage binding uses only new N2 reference')

snap=read(bind(M/'reference-base/registry.json'));base={e['id']:e for e in snap['entries']}
ck(sha(M/'reference-base/registry.json')==plan['registry_sha256'],'Base registry snapshot matches previously audited hash')
for aid in set(a for ms in bindings['recordBindings'].values() for a in ms.values())-set(entries):
    ck(aid in base,'Reused registry ID exists: '+aid)
    for key in ['svgPath','model2dPath','model3dPath']:
        if base[aid].get(key):
            p=bind(M/'reference-base'/base[aid][key]);ck(sha(p)==base[aid]['assetHashes'][key],'Exact qualified reused asset bytes: '+aid+' '+key)
normal=read(bind(M/'oleylamine-metadata-normalization-proposal.json'));old=base['oleylamine'];new=normal['normalizedEntry']
ck({k:v for k,v in old.items() if k!='limitations'}=={k:v for k,v in new.items() if k!='limitations'},'Oleylamine normalization changes limitations only')
ck('70%' not in json.dumps(new['limitations']) and 'source-specific' in json.dumps(new['limitations']),'No old grade transferred into normalized reference metadata')
ck(bindings['registryAdditionsSha256']==sha(M/'registry-additions.json'),'Binding package matches exact new registry hash')
for p,h in before.items():ck(sha(p)==h,'Original audited/shared input unchanged: '+Path(p).name)
for p in (M/'raw').glob('*'):
    if p.is_file():bind(p)
freeze=read(bind(M/'package-freeze.json'))
ck(freeze['status']=='frozen_for_independent_audit','Package author explicitly froze final bytes')
for rel,digest in freeze['files'].items():
    p=bind(M/rel);ck(p.resolve().is_relative_to(M) and sha(p)==digest,'Frozen package file unchanged: '+rel)
three_d=read(bind(M/'molecules-3d.json'))
ck({m['id'] for m in three_d}=={e['id'] for e in entries.values() if e.get('model3dPath')},'3D index includes exactly four qualified new 3D references')
for m in three_d:
    ck(m==read(M/entries[m['id']]['model3dPath']),'3D index carries exact inspected model: '+m['id'])

errors=[c for c in checks if not c['passed']]
result={'schema':'mattersyn-independent-molecular-binding-audit/1','source_id':'gu2004','reviewer':'/root/peng1998_reader_assets',
        'at':datetime.now(timezone.utc).isoformat(),'status':'passed' if not errors else 'failed','scope':'Independent new-reference graph, charge/formula, groups, coordinate and source-specific reagent-binding audit. Nine actual 2D previews inspected. No source batch geometry, UI runtime or publication approval is implied.',
        'checked_entries':9,'new_2d_models':8,'new_3d_models':4,'new_svg_previews_viewed':9,'source_materials':17,'reagent_bindings':20,'specimen_bindings_out_of_scope':8,
        'package_freeze_sha256':sha(M/'package-freeze.json'),'registry_additions_sha256':sha(M/'registry-additions.json'),'molecule_bindings_sha256':sha(M/'molecule-bindings-proposal.json'),
        'checks':len(checks),'failure_count':len(errors),'failures':errors,'check_details':checks,'asset_and_input_hashes':files,'bound_files':files,'three_dimensional_geometry':stats,
        'nitrogen_reference_verification':'Actual returned NIST parsed table excerpt independently read: X 1Σg+ row, r_e=1.09768 with final subscript digit 5, angstrom header and 14N2 identity. Reference-distance construction checked. Direct raw HTML retrieval failed and is not claimed; the retained tool excerpt is bound by hash.',
        'binding_application_requirement':'Source-specific viewOverrides must be consumed by the final runtime, and final integration must use these exact hashes. Separate actual-renderer/browser audit still required.',
        'independent_final_binding_runtime_audit':False,'publication_approved':False,'training_eligible':False}
(B/'molecular-source-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':result['status'],'checks':len(checks),'failures':errors},ensure_ascii=False))
