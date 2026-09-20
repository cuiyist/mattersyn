"""Offline authoring of qualified Ribeiro reference/component depictions."""
from pathlib import Path
import sys, json, hashlib, html, copy, re
from datetime import datetime, timezone
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent; B=OUT.parent.parent; ROOT=B.parents[4]
sys.path[:0]=[str(ROOT/'research-assets/rdkit-runtime'),str(ROOT/'research-assets/corpus-20260917/runtime')]
import rdkit
from rdkit import Chem
from rdkit.Chem import rdDepictor, rdMolDescriptors
from rdkit.Chem.Draw import rdMolDraw2D
import pymupdf
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def dump(p,o):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def esc(s):return html.escape(str(s),quote=True)
for name in ['svg','models','review','reference-base']: (OUT/name).mkdir(parents=True,exist_ok=True)
plan=read(B/'visual-preparation-plan.json');audit=read(B/'visual-reuse-audit.json')
assert sha(B/'visual-preparation-plan.json')=='b9751dabb6dd97068bce5bea101eee30243ddb2c05b08808d7aad183872c0a74'
assert audit['status']=='passed_bounded_reference_qualification'
registry=ROOT/'recipe-atlas/dist/assets/chemical-registry/registry.json'
assert sha(registry)==plan['registry_sha256']
base={e['id']:e for e in read(registry)['entries']}
records={rid:read(B/'canonical-drafts'/f'{rid}.json') for rid in plan['record_hashes']}
inputs=[B/x for x in ['visual-preparation-plan.json','visual-reuse-audit.json','source-facts.json','source-inventory.json','source-scientific-audit.json','canonical-record-manifest.json','canonical-records-audit.json','reader-source-audit.json']]+list((B/'canonical-drafts').glob('*.json'))+[registry,B/'reader-assets/experimental-procedure.png']
input_hashes={str(p):sha(p) for p in inputs}
saved=OUT/'input-hashes-before.json'
if saved.exists():assert read(saved)==input_hashes
else:dump(saved,input_hashes)
for rid,digest in plan['record_hashes'].items():assert sha(B/'canonical-drafts'/f'{rid}.json')==digest
def snapshot(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True)
    if dst.exists():assert sha(src)==sha(dst)
    else:dst.write_bytes(src.read_bytes())
snapshot(registry,OUT/'reference-base/registry.json')
for eid in ['ethanol','water']:
    dump(OUT/'reference-base/entries'/f'{eid}.json',base[eid])
    for key in ['svgPath','model2dPath','model3dPath']:
        if base[eid].get(key):snapshot(registry.parent/base[eid][key],OUT/'reference-base'/base[eid][key])
    q=ROOT/'research-assets/quality-20260918/molecules'
    for suffix in ['-properties.json','-pubchem-2d.sdf','-lookup.json']:
        snapshot(q/'raw'/(eid+suffix),OUT/'reference-base/raw'/(eid+suffix))

def source(slug,rep='2d'):
    p=OUT/'raw'/f'{slug}-pubchem-{rep}.sdf'
    m=Chem.SDMolSupplier(str(p),removeHs=False)[0];assert m is not None
    return Chem.RemoveHs(m)
def prop(slug):return read(OUT/'raw'/f'{slug}-properties.json')['PropertyTable']['Properties'][0]
def groups(m,kind):
    out=[]
    if kind=='tin':
        for a in m.GetAtoms():
            labels={'Sn':'Formal tin(II) center','Cl':'Chloride component','O':'Water of hydration'}
            out.append({'label':labels[a.GetSymbol()],'atomIndices':[a.GetIdx()],'bondIndices':[]})
    elif kind=='tbaoh':
        for a in m.GetAtoms():
            if a.GetSymbol()=='N':out.append({'label':'Quaternary ammonium center','atomIndices':[a.GetIdx()],'bondIndices':[]})
            if a.GetSymbol()=='O':out.append({'label':'Hydroxide counterion','atomIndices':[a.GetIdx()],'bondIndices':[]})
    elif kind=='nitric':
        out=[{'label':'Nitric-acid reference / resonance representation','atomIndices':list(range(m.GetNumAtoms())),'bondIndices':list(range(m.GetNumBonds()))}]
    return out
def model(m,e,rep,kind):
    c=m.GetConformer()
    return {'id':e['id'],'name':e['name'],'formula':e['formula'],'pubchemCid':e.get('pubchemCid'),'representation':rep,'has3D':rep=='3d','allowRotation':rep=='3d','indexConvention':'zero-based','coordinateUnits':'angstrom' if rep=='3d' else 'drawing units',
      'atoms':[{'index':a.GetIdx(),'element':a.GetSymbol(),'x':round(c.GetAtomPosition(a.GetIdx()).x,7),'y':round(c.GetAtomPosition(a.GetIdx()).y,7),'z':round(c.GetAtomPosition(a.GetIdx()).z,7),'formalCharge':a.GetFormalCharge(),'isotope':a.GetIsotope(),'implicitHydrogenCount':a.GetTotalNumHs(),'chiralTag':str(a.GetChiralTag())} for a in m.GetAtoms()],
      'bonds':[{'a':b.GetBeginAtomIdx(),'b':b.GetEndAtomIdx(),'order':b.GetBondTypeAsDouble(),'stereo':str(b.GetStereo()),'stereoAtoms':list(b.GetStereoAtoms())} for b in m.GetBonds()],
      'functionalGroups':groups(m,kind),'connectivitySmiles':Chem.MolToSmiles(m,True),'caption':e['caption'],'notes':e['limitations'],'eligible_training':False}
def text(x,y,s,size=20,anchor='middle',color='#294f61'):
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="Arial,sans-serif" font-size="{size}" fill="{color}">{esc(s)}</text>'
def frame(e,body,footer):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="900" height="440" viewBox="0 0 900 440" role="img"><title>{esc(e["name"])}</title><desc>{esc(e["caption"])}</desc><rect width="900" height="440" rx="15" fill="#fff"/>{text(30,39,e["name"],24,"start")}<path d="M30 60H870" stroke="#d6e5eb"/>{text(450,92,e["displayFormula"],22)}{body}<rect x="26" y="378" width="848" height="43" rx="9" fill="#edf5f7"/>{text(450,405,footer,15)}</svg>'
def drawmol(m,kind):
    drawer=rdMolDraw2D.MolDraw2DSVG(840,270);opt=drawer.drawOptions();opt.clearBackground=False;opt.padding=.13;opt.bondLineWidth=2.5;opt.minFontSize=19;opt.maxFontSize=31
    gg=groups(m,kind);aa=sorted({i for g in gg for i in g['atomIndices']});bb=sorted({i for g in gg for i in g['bondIndices']})
    drawer.DrawMolecule(m,highlightAtoms=aa,highlightBonds=bb,highlightAtomColors={i:(.78,.9,.91) for i in aa},highlightBondColors={i:(.55,.78,.8) for i in bb});drawer.FinishDrawing();s=drawer.GetDrawingText()
    s=s[s.index('<svg'):];return '<g transform="translate(30,103)">'+s[s.index('>')+1:s.rindex('</svg>')]+'</g>'
entries=[]
def make(e,m=None,m3=None,kind=None,body=None,footer=''):
    if m is not None:
        counts=lambda value:{element:int(n or 1) for element,n in re.findall(r'([A-Z][a-z]?)(\d*)',value)}
        assert counts(rdMolDescriptors.CalcMolFormula(m))==counts(e['formula'])
        rdDepictor.Compute2DCoords(m)
        if kind=='tin':
            # Independent component spacing is a drawing layout, never coordination.
            ids=sorted(range(m.GetNumAtoms()),key=lambda i:{'Sn':0,'Cl':1,'O':2}[m.GetAtomWithIdx(i).GetSymbol()])
            for j,i in enumerate(ids):m.GetConformer().SetAtomPosition(i,((j-2)*4.0,0.0,0.0))
        m2=model(m,e,'2d',kind);m2.update(modelType='Reference connectivity / 2D drawing',coordinateSource='RDKit 2D layout from exact cached PubChem graph',computedBy='RDKit '+rdkit.__version__)
        e['model2dPath']='models/'+e['id']+'-2d.json';dump(OUT/e['model2dPath'],m2);e['functionalGroups']=m2['functionalGroups'];body=drawmol(m,kind)
        if kind=='tin':
            body=''.join(f'<rect x="{45+165*i}" y="166" width="150" height="123" rx="17" fill="#e9f4f5" stroke="#a9cbd3"/>'+text(120+165*i,221,label,36)+text(120+165*i,262,role,13) for i,(label,role) in enumerate([('Sn²⁺','Tin(II) center'),('Cl⁻','Chloride'),('Cl⁻','Chloride'),('H₂O','Hydration water'),('H₂O','Hydration water')]))+text(450,337,'Disconnected stoichiometric components; positions are arbitrary',18)
    if m3 is not None:
        assert m3.GetConformer().Is3D() and Chem.MolToSmiles(m3,True)==Chem.MolToSmiles(m,True)
        d=model(m3,e,'3d',kind);d.update(modelType='PubChem computed reference conformer',coordinateSource='PubChem3D cached SDF',sourceType='database-computed; not experimental',caption='One PubChem computed nitric-acid reference conformer. It is not measured reagent geometry or the species distribution of an aqueous acid.',rawSourcePath='raw/nitric-acid-pubchem-3d.sdf',rawSourceSha256=sha(OUT/'raw/nitric-acid-pubchem-3d.sdf'))
        e['model3dPath']='models/'+e['id']+'-3d.json';dump(OUT/e['model3dPath'],d)
    e['svgPath']='svg/'+e['id']+'.svg';(OUT/e['svgPath']).write_text(frame(e,body,footer),encoding='utf-8')
    e['assetHashes']={k:sha(OUT/e[k]) for k in ['svgPath','model2dPath','model3dPath'] if e.get(k)}
    doc=pymupdf.open(stream=(OUT/e['svgPath']).read_bytes(),filetype='svg');doc[0].get_pixmap(matrix=pymupdf.Matrix(1.35,1.35),alpha=False).save(str(OUT/'review'/f'{e["id"]}.png'))
    entries.append(e)
def entry(eid,name,formula,display,kind,caption,limits,urls):
    return {'id':eid,'name':name,'aliases':[name],'formula':formula,'displayFormula':display,'depictionKind':kind,'pubchemCid':None,'svgPath':None,'model2dPath':None,'model3dPath':None,'functionalGroups':[],'caption':caption,'limitations':limits,'sourceUrls':urls,'provenance':{},'independentScientificAudit':'pending','published':False,'eligible_training':False}

configs=[
 ('tin-dihydrate-ionic','tin','reference-tin-ii-chloride-dihydrate','Tin(II) chloride dihydrate','SnCl₂ · 2H₂O','ionic_components',
  'Formal Sn²⁺, two Cl⁻ components and two waters of hydration. This stoichiometric component layout does not assign a lattice, Sn–O/Sn–Cl coordination or dissolved species.',
  ['The two waters belong to the named hydrate; they do not specify added hydrolysis water.','No connected isolated SnCl2 molecule or 3D arrangement is assigned.'],
  'Two hydration waters retained · coordination and 3D unavailable'),
 ('nitric-acid','nitric','reference-nitric-acid','Nitric acid','HNO₃','molecule',
  'Nitric-acid reference connectivity in one formal-charge/resonance representation. An undissociated reference molecule does not establish the species distribution in an aqueous acid.',
  ['Aqueous proton transfer, nitrate resonance and solvent structure are not determined by this one reference.','Concentration, supplier and dose belong to the source-specific binding.'],
  'Reference molecule · aqueous speciation and acid dose remain source-specific'),
 ('tbaoh','tbaoh','reference-tetrabutylammonium-hydroxide','Tetrabutylammonium hydroxide','[N(C₄H₉)₄]⁺  OH⁻','ionic_components',
  'Tetrabutylammonium cation and hydroxide counterion as separate reference components. Layout does not specify ion-pair geometry, hydration or a solution structure.',
  ['This hydroxide reference contains no bromide.','Solvent water is a separate component with no fixed solute:water stoichiometry; no salt 3D model is assigned.'],
  'Correct hydroxide counterion · aqueous solvent is a separate reference')]
for slug,kind,eid,name,display,depiction,caption,limits,footer in configs:
    pr=prop(slug);m=source(slug)
    assert Chem.MolToSmiles(m,True)==Chem.MolToSmiles(Chem.MolFromSmiles(pr['ConnectivitySMILES']),True)
    e=entry(eid,name,pr['MolecularFormula'],display,depiction,caption,limits,[f'https://pubchem.ncbi.nlm.nih.gov/compound/{pr["CID"]}']);e['pubchemCid']=pr['CID'];e['iupacName']=pr['IUPACName']
    e['provenance']={'connectivitySource':'Exact cached PubChem 2D SDF; independent property/SMILES agreement','smiles':Chem.MolToSmiles(m,True),'depictionSoftware':'RDKit '+rdkit.__version__,'reference2d':{'path':f'raw/{slug}-pubchem-2d.sdf','sha256':sha(OUT/'raw'/f'{slug}-pubchem-2d.sdf')},'referenceProperties':{'path':f'raw/{slug}-properties.json','sha256':sha(OUT/'raw'/f'{slug}-properties.json')}}
    if kind=='tin':
        assert len(Chem.GetMolFrags(m))==5 and Chem.GetFormalCharge(m)==0
        e['provenance']['alternateNotUsed']={'cid':61436,'smiles':prop('tin-dihydrate-alternate')['SMILES'],'reason':'Connected Cl–Sn–Cl reference would suggest an isolated neutral unit; the selected formal-component record avoids asserting solid or dissolved coordination. Both records have the same hydrate stoichiometry.','properties_sha256':sha(OUT/'raw/tin-dihydrate-alternate-properties.json')}
    if kind=='tbaoh':assert len(Chem.GetMolFrags(m))==2 and not any(a.GetSymbol()=='Br' for a in m.GetAtoms())
    make(e,m,source(slug,'3d') if kind=='nitric' else None,kind,footer=footer)

paper='https://doi.org/10.1021/jp0473669'
e=entry('identity-ribeiro-carbon-copper-grid','Carbon-coated copper TEM grid',None,'Carbon coating / copper support','support','Source-named carbon-coated copper support for TEM specimen preparation. The schematic does not specify mesh, coating thickness, Formvar or atomic geometry.',['A support is not a discrete molecule. Geometry and colors are explanatory.'],[paper])
e['provenance']={'sourceDoi':'10.1021/jp0473669','sourceSha256':'fc10a7101b4acb74f15398a530b8f916641f89b171fad065dd789747204eee88','sourceLocators':['Main PDF p. 2, Experimental Procedure'],'measuredCoordinates':False}
make(e,body='<ellipse cx="450" cy="232" rx="150" ry="71" fill="#c99267" stroke="#a77855" stroke-width="4"/><ellipse cx="450" cy="219" rx="136" ry="59" fill="#435d6d" opacity="0.8"/>'+text(450,326,'Carbon coating on copper · no mesh or thickness assigned',18),footer='Support identity only · no molecular or atomic-coordinate model')
e=entry('identity-ribeiro-proposed-tin-hydroxide','Proposed tin hydroxide intermediate','Sn(OH)4','Sn(OH)₄','formula','Sn(OH)4 is the authors’ proposed solution intermediate, not an isolated reagent or measured speciation. Formula display does not assign coordination geometry.',['The Sn(II)-to-Sn(IV) pathway is not established by the proposed formula.','No molecular connectivity, crystal structure or unique mechanistic sequence is assigned.'],[paper]);e['provenance']={'sourceDoi':'10.1021/jp0473669','sourceLocators':['Main PDF p. 3, Section 3.1 polycondensation discussion'],'measuredCoordinates':False,'modelStatus':'author-proposed intermediate'}
make(e,body=text(450,224,'Sn(OH)₄',66)+text(450,279,'Author-proposed intermediate',23)+text(450,322,'Formula only · species and coordination unresolved',18),footer='Proposed mechanism context · not an isolated or measured molecular structure')
e=entry('identity-ribeiro-sno2-colloid','Tin dioxide colloidal specimen','SnO2','SnO₂','specimen','Nominal tin-dioxide colloid identity. Particle symbols identify the material class, not atom positions, measured radius, shape or the same physical sample across techniques.',['The source assigns cassiterite in prose; a corresponding XRD trace is not supplied in the inspected main article.','No SAED, CIF, lattice parameter or atomic-coordinate model is supplied.','Each canonical specimen/measurement context remains distinct; no cross-technique batch join is approved.'],[paper]);e['provenance']={'sourceDoi':'10.1021/jp0473669','sourceLocators':['Main PDF p. 2, Experimental Procedure and source-specific characterization contexts'],'measuredCoordinates':False,'representation':'Nominal composition icon; pixel symbols are not a particle model'}
circles=''.join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#6f9dad" stroke="#417183" stroke-width="2"/>' for x,y,r in [(350,207,25),(449,186,19),(534,232,23),(399,275,20),(483,286,16)])
make(e,body=circles+text(450,344,'Composition symbols · no size scale or atomic lattice',18),footer='Separate specimen contexts · original TEM images remain the measured evidence')
dump(OUT/'registry-additions.json',{'schemaVersion':'1.0.0','status':'private_author_proposal_pending_independent_audit','entries':entries})

mapping={'sncl2-dihydrate':'reference-tin-ii-chloride-dihydrate','ethanol':'ethanol','hydrolysis-water':'water','dialysis-water':'water','carbon-copper-grid':'identity-ribeiro-carbon-copper-grid','sno2-colloid':'identity-ribeiro-sno2-colloid','nitric-acid':'reference-nitric-acid','tbaoh-aqueous':'reference-tetrabutylammonium-hydroxide','sn-hydroxide-model':'identity-ribeiro-proposed-tin-hydroxide'}
notes={x['material_id']:x['reason'] for x in audit['slot_dispositions']}
notes.update({'sncl2-dihydrate':'Tin(II) chloride dihydrate, Mallinckrodt. Preserve both hydration waters. Absolute precursor charge and solvent volume are not reported; hydrate waters are not the hydrolysis-water dose.',
 'nitric-acid':'Dilute nitric acid, Synth. Acid concentration and volume are not reported. Reference connectivity does not resolve aqueous nitrate/proton populations. Acid-set treatment pH must be distinguished from final measurement pH after TBAOH.',
 'tbaoh-aqueous':'Aqueous tetrabutylammonium hydroxide, J. T. Baker, 0.4 mol/L stock. Stock concentration is not final sample concentration; added volume and final measurement pH are unreported. Water is a separate solvent reference with unspecified grade.',
 'carbon-copper-grid':'Carbon-coated copper grid. One colloid drop wets the support for 20 s, followed by air drying. No mesh, Formvar, thickness, drying duration or bulk-powder workup is assigned.',
 'sno2-colloid':'Nominal SnO2 colloid identity for this canonical context only. No common physical batch, atomic coordinates, fitted size, phase refinement or unreported structure is inferred from the shared composition icon.',
 'sn-hydroxide-model':'The authors propose Sn(OH)4 as an intermediate. It is not a measured species, isolated reagent or verified coordination structure; the Sn(II)-to-Sn(IV) pathway remains unresolved.'})
bindings={rid:{} for rid in records};bindingnotes={rid:{} for rid in records};slots=[]
for slot in plan['material_slots']:
    rid=slot['record_id'];m=slot['source_material'];mid=m['id'];eid=mapping[mid];bindings[rid][mid]=eid
    note=notes[mid]
    row={'source_material_id':mid,'registry_id':eid,'json_pointer':slot['json_pointer'],'canonical_sha256':plan['record_hashes'][rid],'source_name':m['name'],'source_role':m['role'],'source_stage':m['stage'],'canonical_evidence':m['evidence'],'canonical_quantities':m['quantities'],'display_scope':note,'viewOverrides':{'name':m['name'],'caption':note,'limitations':[note],'modelNotes':[note]},'binding_approved':False,'independent_scientific_audit':'pending'}
    bindingnotes[rid][mid]=row;slots.append({'record_id':rid,**row})
dump(OUT/'molecule-bindings-proposal.json',{'schemaVersion':'1.0.0','status':'private_author_proposal_pending_independent_audit','recordBindings':bindings,'bindingNotes':bindingnotes,'slots':slots,'source_group':'ribeiro2004','counts':{'slots':13,'unique_source_material_ids':9,'registry_ids':8,'new_entries':6,'reused_entries':2},'baseRegistrySha256':sha(registry)})
components=[{'context':'initial ethanolic tin(II) precursor stock','canonical_record_id':'ribeiro-2004-hydrolysis','canonical_stock_pointer':'/stocks/0','components':[{'registry_id':mapping['sncl2-dihydrate'],'role':'named precursor hydrate','material_pointer':'/materials/0'},{'registry_id':'ethanol','role':'solvent','material_pointer':'/materials/1'}],'scope':'Initial 0.0025–0.1 mol/L tin precursor range; not final aqueous particle concentration.'},
 {'context':'aqueous nitric acid reagent','canonical_record_id':'ribeiro-2004-ph-treatment','canonical_material_pointer':'/materials/1','components':[{'registry_id':'reference-nitric-acid','role':'acid reference'},{'registry_id':'water','role':'aqueous solvent','source_grade':'not reported'}],'scope':'Component references only; no acid:water ratio, solution species fractions or reagent concentration supplied.'},
 {'context':'aqueous TBAOH stock reagent','canonical_record_id':'ribeiro-2004-ph-treatment','canonical_material_pointer':'/materials/2','components':[{'registry_id':'reference-tetrabutylammonium-hydroxide','role':'solute components'},{'registry_id':'water','role':'aqueous solvent','source_grade':'not reported'}],'scope':'0.4 mol/L TBAOH stock; solvent water has no fixed stoichiometric count in this depiction. Final concentration, dose and measurement pH remain unknown.'}]
dump(OUT/'component-view-proposal.json',{'status':'private_pending_component_binding_and_browser_audit','components':components,'no_new_canonical_stocks_created':True,'binding_approved':False})
outputs={str(p.relative_to(OUT)):sha(p) for folder in ['svg','models','review','raw','reference-base'] for p in (OUT/folder).rglob('*') if p.is_file()}
outputs.update({p.name:sha(p) for p in [OUT/'registry-additions.json',OUT/'molecule-bindings-proposal.json',OUT/'component-view-proposal.json',Path(__file__)]})
assert all(sha(Path(p))==digest for p,digest in input_hashes.items())
dump(OUT/'generation-manifest.json',{'schema':'mattersyn-private-reference-generation/1','created_at':datetime.now(timezone.utc).isoformat(),'source_id':'ribeiro2004','author':'/root/backlog_eta','status':'author_generated_pending_validation_and_independent_audit','counts':{'entries':6,'molecular_2d_models':3,'molecular_3d_models':1,'svg_assets':6,'previews':6,'material_bindings':13},'input_hashes':input_hashes,'files':outputs,'scientific_boundaries':['Component stoichiometry is not a solid or solution geometry.','SnCl2 dihydrate retains both hydration waters.','TBAOH contains OH−, not Br−; solvent separate.','HNO3 3D is database-computed and not measured.','Shared SnO2 icon cannot join separate specimens.','SI unverified; no crystal/SAED/XRD asset invented.']})
print(json.dumps({'entries':len(entries),'slots':len(slots),'manifest_sha256':sha(OUT/'generation-manifest.json')}))
