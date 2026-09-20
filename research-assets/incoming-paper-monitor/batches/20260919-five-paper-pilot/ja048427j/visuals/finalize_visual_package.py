from pathlib import Path
import json,hashlib,math,collections,sys
sys.dont_write_bytecode=True
sys.path.insert(0,r'[local path redacted]')
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
V=Path(__file__).resolve().parent;N=V.parent;M=V/'molecules';P=V/'products';A=V/'apparatus'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();dump=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
checks=[]
def ck(ok,label):
    checks.append({'passed':bool(ok),'label':label})
    if not ok:raise AssertionError(label)
expected={'canonical-record-manifest.json':'185ae1359ba2aab1e2091e877cc2b72f929cfb14128fc7ae56ddffe067a0d609','canonical-records-audit.json':'1e1d79e95c44adbce86684069ebed2c4e904686e3ecbdec92cd44f80aeb56f89','source-facts.json':'1b26d583abde0b61b496a56548c55321099a61b0a0303668ec7bbd2750fbb3a9','source-inventory.json':'59b71bb8461af9d7c387019ee0dc6ce48ec04b33fa7e1793515c0e4658352387','source-scientific-audit.json':'82d7dfef2315f3aa5512680b0a127e1c752a1104b7d800de163838f711db8507','public-review-proposal/norberg2004.json':'0e2b4b3593e1fc8a86868c438ee7bb47eca57ff2a742f527a8b2129f32053629','reader-source-audit.json':'ef6d69e01c7e12b094869caaf826fbfa171b84def0b8f8e7f4b4a04916288084'}
upstream=[]
for f,h in expected.items():ck(sha(N/f)==h,'Frozen upstream '+f);upstream.append({'path':str(N/f),'sha256':h})
mf=read(N/'canonical-record-manifest.json');records={}
for row in mf['records']:
    p=Path(row.get('path',N/'canonical-drafts'/f"{row['record_id']}.json"));ck(sha(p)==row['sha256'],'Frozen canonical '+row['record_id']);records[row['record_id']]=read(p);upstream.append({'path':str(p),'sha256':sha(p)})
prose=N/'public-review-proposal/operation-reader-prose.json';upstream.append({'path':str(prose),'sha256':sha(prose)})
entries=read(M/'registry-additions.json')['entries'];products=read(P/'product-registry-additions.json')['entries'];reuse=read(M/'reuse-qualification.json')['entries'];reg={e['id']:e for e in entries+products};reg.update({e['registry_id']:e['registry_entry']for e in reuse})
ck(len(reg)==49,'49 distinct chemical and specimen reference IDs')
for e in entries+products:
    folder=M if e in entries else P
    for key,h in e.get('assetHashes',{}).items():ck(sha(folder/e[key])==h,'Asset hash '+e['id']+'/'+key)
for e in reuse:
    for a in e['assets']:ck(sha(Path(a['private_path']))==a['source_sha256']==sha(Path(a['source_path'])),'Byte-exact reused '+e['registry_id']+'/'+a['key'])
bindings=read(M/'bindings-additions.json');coverage=read(M/'material-slot-coverage.json')['slots'];actual=[]
for rid,r in records.items():
    ck(bindings['sourceRecordSha256'][rid]==sha(N/'canonical-drafts'/f'{rid}.json'),'Binding canonical '+rid)
    for i,m in enumerate(r['materials']):
        mid=m['id'];target=bindings['recordBindings'][rid][mid];ck(target in reg,'Known material reference '+rid+'/'+mid)
        note=bindings['bindingNotes'][rid][mid];ck(note['binding_approved']is False and note['canonical_pointer']==f'/materials/{i}','Scoped pending override '+rid+'/'+mid)
        c=next(c for c in coverage if c['record_id']==rid and c['material_id']==mid);ck(c['pointer']==f'/materials/{i}' and c['registry_id']==target and c['source_formula']==m['formula'] and c['source_evidence']==m.get('evidence',[]),'Exact material coverage '+rid+'/'+mid);actual.append((rid,mid))
ck(len(actual)==73 and len(set(actual))==73 and len(coverage)==73,'All and only 73 unique material slots')
for rid,target in read(P/'product-reference-proposal.json')['recordBindings'].items():ck(rid in records and target in reg,'Product binding '+rid)
for e in entries[:4]:
    model=read(M/e['model2dPath']);rw=Chem.RWMol()
    for a in model['atoms']:
        atom=Chem.Atom(a['element']);atom.SetFormalCharge(a['formalCharge']);rw.AddAtom(atom)
        ck(math.isfinite(a['x']) and math.isfinite(a['y']) and a['z']==0,'Finite 2D ion coordinate '+e['id']+'/'+str(a['index']))
    for b in model['bonds']:rw.AddBond(b['a'],b['b'],{1:Chem.BondType.SINGLE,2:Chem.BondType.DOUBLE}[b['order']])
    mol=rw.GetMol();Chem.SanitizeMol(mol);reference=Chem.MolFromSmiles(e['provenance']['smiles'])
    ck(Chem.MolToSmiles(mol)==Chem.MolToSmiles(reference),'Ionic graph '+e['id']);ck(sum(a['formalCharge']for a in model['atoms'])==0,'Ionic net neutrality '+e['id']);ck(rdMolDescriptors.CalcMolFormula(mol)==model['formula'],'Ionic formula '+e['id'])
    ck(e['model3dPath']is None and model['has3D']is False,'No invented ionic 3D '+e['id'])
    for g in e['functionalGroups']:
        ck(all(0<=i<len(model['atoms'])for i in g['atomIndices']) and all(0<=i<len(model['bonds'])for i in g['bondIndices']),'Valid functional-group indices '+e['id'])
    if 'tetrahydrate'in e['id']:ck(len(Chem.GetMolFrags(mol))==7 and sum(a['element']=='O' and a['implicitHydrogenCount']==2 for a in model['atoms'])==4,'Four unbound hydrate water components')
    if 'nitrate'in e['id']:ck(e['formula']is None and 'x not reported'in e['displayFormula'],'Unknown nitrate hydrate retained')
topo=next(e for e in entries if e['id']=='norberg2004-topo-component');base=next(e for e in reuse if e['registry_id']=='topo')
for key in ['model2dPath','model3dPath']:
    x=read(M/topo[key]);y=read(Path(next(a for a in base['assets']if a['key']==key)['private_path']));ck(x['atoms']==y['atoms'] and x['bonds']==y['bonds'],'TOPO exact reference geometry '+key)
cell=read(P/'models/norberg-undoped-zno-unit-cell.json');finite=read(P/'models/norberg-undoped-zno-finite-reference.json');atoms=finite['atoms'];vec=cell['cellVectors'];site={a['site']:a for a in cell['atoms']}
original=read(P/'reference-origin/zno-wurtzite-original-metadata.json');allowed={'id','name','scope','caption','originalReferenceModel'}
ck({k:v for k,v in cell.items()if k not in allowed}=={k:v for k,v in original.items()if k not in allowed},'Host model metadata-only normalization; atomic and cell data unchanged')
ck(sha(P/'reference-origin/zno-wurtzite-original-metadata.json')=='8a89a3a821dd1e31e1014e662774216f341a857633b387e6310210eaa9b155d5','Original host model preserved byte-exact')
nitrogen=next(e for e in entries if e['id']=='norberg2004-nitrogen-reference');nm=read(M/nitrogen['model3dPath']);ck(abs(math.dist([nm['atoms'][0][q]for q in ['x','y','z']],[nm['atoms'][1][q]for q in ['x','y','z']])-1.09768)<1e-9 and nm['bonds'][0]['order']==3,'Qualified NIST dinitrogen length and bond order')
ck('1.09768_{5}'in (M/'raw/nitrogen-nist-web-tool-excerpt.txt').read_text(encoding='utf-8'),'Retained original NIST constant row')
ck(all(x['registry_id']!='nitrogen'for x in reuse),'Rejected old nitrogen model not qualified')
ck(finite['periodic']is False and finite['measured_sample_structure']is False and finite['training_eligible']is False,'Finite reference exclusions')
ck(collections.Counter(a['element']for a in atoms)=={'Zn':96,'O':96} and len(atoms)==192,'192 undoped host atoms')
translations=[]
for a in atoms:
    s=site[a['properties']['reference_site']];ijk=a['properties']['cell_translation'];raw=[s[q]+sum(ijk[l]*vec[l][i]for l in range(3))for i,q in enumerate(['x','y','z'])];translations.append([raw[i]-a[q]for i,q in enumerate(['x','y','z'])]);ck(a['element']==s['element'],'Host species '+str(a['serial']))
    ck(len(a['bonds'])==len(a['bondOrder']) and all(a['bondOrder'][i]==1 for i in range(len(a['bonds']))),'Finite visual links '+str(a['serial']))
    for j in a['bonds']:
        b=atoms[j];d=math.dist([a[q]for q in ['x','y','z']],[b[q]for q in ['x','y','z']]);ck(a['serial']-1 in b['bonds'] and a['element']!=b['element'] and 1.7<d<2.2,'Reciprocal host visualization link '+str(a['serial'])+'/'+str(j))
ck(all(max(abs(x-y)for x,y in zip(t,translations[0]))<1e-10 for t in translations),'Only common centering translation after exact host-cell replication')
ck(len({tuple(round(a[q],8)for q in ['x','y','z'])for a in atoms})==192,'No duplicate finite coordinates')
xyz=(P/'downloads/norberg-undoped-zno-finite-reference.xyz').read_text().splitlines();ck(int(xyz[0])==192 and len(xyz)==194,'XYZ full atom count')
for row,a in zip(xyz[2:],atoms):
    f=row.split();ck(f[0]==a['element'] and max(abs(float(f[i+1])-a[q])for i,q in enumerate(['x','y','z']))<1e-8,'XYZ exact serialized geometry '+str(a['serial']))
sm=read(A/'scene-manifest.json');rv=read(A/'render-validation.json');rp=read(V/'reference-preview-manifest.json');ck(len(sm['scenes'])==47 and all(c['passed']for c in sm['checks']),'47 scenes and 279 module checks')
for s in sm['scenes']:
    r=records[s['record_id']];o=r['operations'][int(s['operation_pointer'].split('/')[-1])];ck(o['id']==s['operation_id'],'Operation pointer '+o['id'])
    for k in ['parameters','environment','inputs','outputs']:ck(s[k]==o[k],'Exact canonical scene '+o['id']+'/'+k)
    ck(sha(A/s['svg_file'])==s['svg_sha256'],'Scene SVG hash '+o['id'])
ck(not rv['text_overflows'] and not rp['text_overflows'],'No out-of-viewport text in 106 previews')
for x in rv['scenes']:ck(sha(A/x['png_file'])==x['png_sha256'],'Apparatus PNG '+x['scene_kind'])
for x in rp['outputs']:ck(sha(Path(x['svg']))==x['svg_sha256'] and sha(Path(x['png']))==x['png_sha256'],'Reference preview '+x['label'])
review={'status':'author_visual_review_passed_pending_independent_audit','scope':'All 47 apparatus SVG/PNG scenes, all 58 molecular/product/host previews and their 28 contact sheets inspected. Programmatic checks are distinct from actual visual inspection.','apparatus_contacts':rv['contact_sheets'],'reference_contacts':rp['contacts'],'corrections':['Open-air controls drawn open; named comparison specimens; spin-coating layout spaced.','Powder tray particles moved onto sample tray.','Manganese acetate tetrahydrate components separated; ASCII SVG formula avoids missing Unicode font glyphs.','Product bindings separate cleaned, surface-control, TOPO and growth-series contexts.','Unit-cell preview displays the actual cell-vector frame; finite ZnO is an external illustrative undoped crop.'],'final_targeted_reinspection':['apparatus/review/contact-11.png','products/review/host-reference-contact-01.png'],'no_browser_or_independent_approval':True}
dump(V/'author-visual-review.json',review)
review['scope']='All 47 apparatus SVG/PNG scenes, all 59 molecular/product/host previews and their 28 contact sheets inspected. Consistency checks are distinct from actual visual inspection.'
review['corrections']+=['Rejected old 1.460 Å nitrogen 3D candidate; use retained NIST 1.09768 Å geometry with source-scoped labels.','Normalized inherited Fu/S1 host metadata; original reference preserved, geometry unchanged.']
review['final_targeted_reinspection']+=['molecules/review/molecule-2d-contact-03.png','molecules/review/molecule-2d-contact-04.png','molecules/review/molecule-3d-contact-02.png']
dump(V/'author-visual-review.json',review)
dump(V/'visual-author-validation.json',{'schema':'mattersyn.private-visual-author-validation.v1','status':'passed_author_checks_pending_independent_audit','checks':checks,'counts':{'checks':len(checks),'module_checks':len(sm['checks']),'reference_builder_checks':len(read(P/'reference-author-checks.json')['checks']),'canonical_records':19,'operations':47,'material_slots':73,'reused_references':10,'new_molecule_or_identity_entries':8,'specimen_context_entries':30,'product_record_bindings':10,'reference_previews':58,'apparatus_previews':47,'contact_sheets':28,'measured_norberg_atomic_structures':0},'upstream':upstream})
validation=read(V/'visual-author-validation.json');validation['counts'].update({'new_molecule_or_identity_entries':len(entries),'reference_previews':len(rp['outputs'])});dump(V/'visual-author-validation.json',validation)
files=[{'path':str(p),'relative_path':p.relative_to(V).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size,'role':'rejected_not_for_integration'if 'rejected-nitrogen-candidate'in p.parts else 'author_proposal_or_evidence'}for p in sorted(V.rglob('*'))if p.is_file() and p.name!='visual-package-manifest.json']
out={'schema':'mattersyn.private-visual-package.v1','source_id':'norberg2004','status':'frozen_author_proposal_pending_independent_audit','counts':read(V/'visual-author-validation.json')['counts'],'files':files,'upstream':upstream,'canonical_quantity_mapping':'apparatus/scene-manifest.json retains exact operation pointers, canonical parameters, materials and source evidence; source-specific labels and prose derive from the frozen reader operation prose.','operation_prose_source':{'path':str(prose),'sha256':sha(prose)},'integration_instructions':'README.md','source_or_canonical_or_reader_or_site_edits':False,'publication_approved':False,'independent_audit':'pending','browser_check':'pending'}
dump(V/'visual-package-manifest.json',out);print(json.dumps({'files':len(files),'checks':len(checks),'manifest_sha256':sha(V/'visual-package-manifest.json'),'validation_sha256':sha(V/'visual-author-validation.json')}))
