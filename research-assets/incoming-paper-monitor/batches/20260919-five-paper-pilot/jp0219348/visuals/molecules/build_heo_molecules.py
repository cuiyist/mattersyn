"""Local-only Heo identity/component proposal; never writes outside this private folder."""
from pathlib import Path
from datetime import datetime,timezone
from copy import deepcopy
from collections import Counter
import hashlib,json,html,math,re,sys
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;H=O.parents[1];ROOT=H.parents[4]
sys.path.insert(0,str(ROOT/'research-assets/corpus-20260917/runtime'))
import pymupdf
R=ROOT/'recipe-atlas/dist/assets/chemical-registry';Q=ROOT/'research-assets/quality-20260918/molecules'
if (O/'package-freeze.json').exists():raise SystemExit('Frozen author package: preserve a revision before rebuilding.')
for folder in ['svg','models','review','reference-base/entries','reference-base/raw','reference-base/audits']:(O/folder).mkdir(parents=True,exist_ok=True)
def load(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,v):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
inputs={}
def snapshot(src,dest):
    src=Path(src);dest=Path(dest);dest.parent.mkdir(parents=True,exist_ok=True)
    inputs[str(src)]=sha(src)
    if dest.exists():assert dest.read_bytes()==src.read_bytes(),dest
    else:dest.write_bytes(src.read_bytes())
    return {'original_path':str(src),'original_sha256':sha(src),'snapshot_path':str(dest.relative_to(O)),'snapshot_sha256':sha(dest)}
inv=load(H/'source-inventory.json');facts=load(H/'source-facts.json');audit=load(H/'source-scientific-audit.json')
for n in ['source-inventory.json','source-facts.json','source-scientific-audit.json','main-tables.json']:
    inputs[str(H/n)]=sha(H/n)
for d in inv['source_documents'].values():assert sha(d['path'])==d['sha256'];inputs[d['path']]=d['sha256']
for row in audit['audited_artifacts']:
    if Path(row['path']).name in ['source-facts.json','source-inventory.json']:assert sha(row['path'])==row['sha256']
snapshot(R/'registry.json',O/'reference-base/registry.json')
base={e['id']:e for e in load(R/'registry.json')['entries']};reused=[];snapshots=[]
for eid in ['water','hydrogen-sulfide','argon','norberg2004-sodium-acetate']:
    e=base[eid];dump(O/'reference-base/entries'/f'{eid}.json',e)
    for key in ['svgPath','model2dPath','model3dPath']:
        if e.get(key):
            assert sha(R/e[key])==e['assetHashes'][key]
            snapshots.append(snapshot(R/e[key],O/'reference-base'/e[key]))
    if eid!='norberg2004-sodium-acetate':reused.append(deepcopy(e))
for n in ['water-properties.json','water-pubchem-2d.sdf','water-lookup.json','argon-properties.json']:
    snapshots.append(snapshot(Q/'raw'/n,O/'reference-base/raw'/n))
for p in [ROOT/'research-assets/incoming-paper-monitor/reviews/jp010002l/build_molecular_assets.py',ROOT/'research-assets/incoming-paper-monitor/reviews/jp010002l/molecular-source-audit.json',H.parent/'ja048427j/visual-source-audit.json']:
    snapshots.append(snapshot(p,O/'reference-base/audits'/p.name))

def esc(x):return html.escape(str(x),quote=True)
def txt(x,y,s,size=22,anchor='middle',color='#253f50',weight=400):return f'<text x="{x}" y="{y}" font-family="Arial,sans-serif" font-size="{size}" font-weight="{weight}" fill="{color}" text-anchor="{anchor}">{esc(s)}</text>'
def frame(name,caption,formula,body,footer):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="510" viewBox="0 0 1000 510" role="img"><title>{esc(name)}</title><desc>{esc(caption)}</desc><rect x="1" y="1" width="998" height="508" rx="20" fill="#fff" stroke="#d7e4ea"/>{txt(40,49,name,27,"start",weight=600)}<path d="M40 72H960" stroke="#d7e4ea"/>{txt(500,115,formula,23,color="#416679")}{body}<rect x="35" y="437" width="930" height="49" rx="10" fill="#edf5f7"/>{txt(500,467,footer,17)}</svg>'
def entry(eid,name,formula,display,kind,caption,limitations):
    return {'id':eid,'name':name,'aliases':[name],'formula':formula,'displayFormula':display,'depictionKind':kind,'pubchemCid':None,'svgPath':'svg/'+eid+'.svg','model2dPath':None,'model3dPath':None,'functionalGroups':[],'caption':caption,'limitations':limitations,'sourceUrls':['https://doi.org/10.1021/jp0219348'],'provenance':{'sourceDoi':'10.1021/jp0219348','sourceSha256':facts['source_sha256'],'sourceLocators':['Main PDF p. 2, printed p. 1121, Experimental Section'],'identitySource':'Source-named identity; symbolic or formal connectivity reference, not recovered specimen coordinates','measuredCoordinates':False},'independentScientificAudit':'pending','binding_approved':False,'published':False,'eligible_training':False}
entries=[]
def save(e,body,footer):
    (O/e['svgPath']).write_text(frame(e['name'],e['caption'],e['displayFormula'] or 'Composition and geometry unspecified',body,footer),encoding='utf-8')
    e['assetHashes']={k:sha(O/e[k]) for k in ['svgPath','model2dPath','model3dPath'] if e.get(k)}
    doc=pymupdf.open(stream=(O/e['svgPath']).read_bytes(),filetype='svg');doc[0].get_pixmap(matrix=pymupdf.Matrix(1.2,1.2),alpha=False).save(str(O/'review'/f'{e["id"]}.png'))
    entries.append(e)

caption='Thallous acetate as formal disconnected Tl+ and acetate− components. The localized carboxylate drawing is one resonance representation; it does not assign a Tl–O coordination bond, ion-pair geometry, hydrate, crystal packing or dissolved speciation.'
e=entry('heo2003-thallous-acetate','Thallous acetate · formal components','C2H3O2Tl','Tl⁺  [CH₃COO]⁻','ionic_components',caption,['The source calls the reagent thallous acetate, 99.99%; no hydrate is specified.','2D drawing units are arbitrary. A 3D salt or coordination model is unavailable.','The aqueous feed is 0.1 mol/L and pH 6.4; solvent water is separately selectable without fixed stoichiometry.'])
prior=load(O/'reference-base/models/norberg2004-sodium-acetate-2d.json')
m=deepcopy(prior)
m.update(id=e['id'],name=e['name'],formula=e['formula'],caption=e['caption'],source={'doi':'10.1021/jp0219348','sourceSha256':facts['source_sha256'],'connectivityBasis':'Curator formal components: Tl+ from source thallous designation plus the unchanged acetate subgraph from the retained, independently audited local acetate model. No PubChem thallous-acetate lookup or measured geometry claimed.'},connectivitySmiles='[Tl+].CC(=O)[O-]',modelType='Formal ion and acetate connectivity; arbitrary 2D layout',computedBy='Deterministic local adaptation of retained acetate 2D graph; no 3D optimization',notes=e['limitations'])
m['atoms'][0]['element']='Tl';m['atoms'][0]['x']=-4.2;m['atoms'][0]['y']=0.0
m['functionalGroups']=[{'label':'Thallium(I) component','atomIndices':[0],'bondIndices':[]},{'label':'Acetate component','atomIndices':[1,2,3,4],'bondIndices':[0,1,2]},{'label':'Carboxylate group · one resonance form','atomIndices':[2,3,4],'bondIndices':[1,2]}]
e['functionalGroups']=m['functionalGroups'];e['model2dPath']='models/'+e['id']+'-2d.json';dump(O/e['model2dPath'],m)
e['provenance'].update({'referenceFragment':{'referenceId':'norberg2004-sodium-acetate-2d','sha256':sha(O/'reference-base/models/norberg2004-sodium-acetate-2d.json')},'transformation':'Replace only the disconnected Na+ identity by source-named Tl+ and move that isolated drawing symbol. Acetate atoms, bond endpoints/orders, charges and implicit hydrogen counts are unchanged. Source-specific Norberg wording is removed.','referenceSmiles':'[Tl+].CC(=O)[O-]','stereochemistry':'No stereogenic center or specified stereoisomer. Localized carboxylate resonance form is not a distinct measured species.'})
body='<rect x="86" y="176" width="228" height="186" rx="20" fill="#edf5f7" stroke="#bfd5dd"/>'+txt(200,256,'Tl⁺',66)+txt(200,323,'Thallium(I)',20)
body+='<rect x="372" y="160" width="542" height="224" rx="20" fill="#fbfbf8" stroke="#dce3dd"/><path d="M615 257L675 202M625 268L686 212M620 270L705 322" stroke="#deaa42" stroke-width="15" opacity=".25" stroke-linecap="round"/>'
body+='<path d="M520 267L608 267M624 255L676 205M635 265L687 215M628 279L704 320" stroke="#354b56" stroke-width="3.5" fill="none"/>'+txt(474,280,'CH₃',34)+txt(620,280,'C',34)+txt(704,202,'O',34,color='#b33e42')+txt(735,342,'O⁻',34,color='#b33e42')+txt(640,411,'Acetate · carboxylate highlighted',18)
save(e,body,'Separate formal components · no Tl–O bond or salt 3D geometry')

symbolics=[
 ('identity-heo2003-na-x','Sodium zeolite X · starting host','Na92Si100Al92O384','Na₉₂Si₁₀₀Al₉₂O₃₈₄','host','Source-named starting zeolite X, nominal composition per unit cell. This identity panel is not an atomic structure or an independently verified synthesis of the starting host.',['Reference 28 host preparation was not inspected.','The paper describes colorless octahedra about 0.15 mm across; no Na-X atomic coordinates are supplied by the new In66-X model.'],'Starting host','Na-X','Host identity only · no parent coordinates or lattice reconstructed'),
 ('identity-heo2003-tl-x','Thallium-exchanged zeolite X','Tl92Si100Al92O384','Tl₉₂Si₁₀₀Al₉₂O₃₈₄','host','Nominal Tl-X ion-exchange intermediate. A label for this source-defined state does not supply a Tl-X lattice or a measured Tl coordination environment.',['Stoichiometric exchange suitability is discussed with cited prior work.','No parent lattice is derived by replacing In atoms in the final product model.'],'Exchange intermediate','Tl-X','Nominal intermediate · lattice and site coordinates unavailable'),
 ('identity-heo2003-in87-x','In87-X · parent reference','In87Si100Al92O384','In₈₇Si₁₀₀Al₉₂O₃₈₄','specimen','Nominal washed/redehydrated parent In87-X identity. Parent control and copied reference spectra remain distinct from the H2S-treated final product.',['Reference 34 parent coordinates are not supplied by this proposal.','Shared nominal identity does not establish that every parent comparison is the same physical crystal.'],'Parent / comparison','In87-X','Parent reference only · no borrowed In66-X coordinates'),
 ('identity-heo2003-in66-x','In66-X · final specimen context','In66Si100Al92O384','Nominal In₆₆Si₁₀₀Al₉₂O₃₈₄','specimen','Source-named final H2S-treated indium zeolite X. This panel is symbolic: the separately audited average position/occupancy candidate is not a unique ordered or charge-balanced atomic microstate.',['Table 2 represents average Si96Al96 while the nominal source formula is Si100Al92; the difference is unresolved.','No sulfur, hydrogen, oxygen-vacancy or residue coordinates are assigned.','Diffraction, atmosphere-exposed EDS and sputtered XPS sample states require their own canonical links.'],'Final sample','In66-X','Nominal identity ≠ average Si₉₆Al₉₆ model or ordered microstate'),
 ('identity-heo2003-indium-metal','Indium metal','In','In','single_atom','Elemental indium identity for source reagent or analytical metal-reference context. The symbol is not a metal crystal, cluster coordinate model or single isolated atom measurement.',['The redox reagent is 99.999% In; mass and metal-to-host ratio are unreported.','A metal XPS reference has a distinct role from the synthesis charge.'],'Elemental identity','In','No atomic lattice, particle size or coordinate model'),
 ('identity-heo2003-pyrex','Pyrex capillary · apparatus',None,None,'support','Source-named fine Pyrex capillary. The outline is a generic apparatus schematic, not a specified glass composition, molecular structure, bore or wall thickness.',['Do not treat glass as an indium precursor or host dopant.','Capillary dimensions and exact glass composition are unreported.'],'Apparatus identity','Pyrex','Generic capillary outline · composition and dimensions unreported'),
 ('identity-heo2003-surface-residue','Unidentified gray surface residue',None,None,'specimen','Metallic gray surface powder was observed. In2O, In2S, InS and finely divided In are proposed identities, not confirmed products or a measured phase assignment.',['Formula and atomic geometry remain null.','The appearance-based possibilities do not create separate sulfide synthesis routes.'],'Observed residue','Unidentified','Appearance observed · phase and formula unresolved')]
for eid,name,formula,display,kind,caption,limits,label,center,footer in symbolics:
    e=entry(eid,name,formula,display,kind,caption,limits)
    e['provenance']['representation']='Symbolic source identity or generic apparatus outline; no atom coordinates'
    if 'in66' in eid:
        e['provenance']['separateAverageModelAudit']={'referenceId':'heo2003-average-position-occupancy-independent-audit-addendum','sha256':sha(H/'structure-candidate/independent-audit-addendum.json'),'bindingStatus':'Separate candidate; no reader integration or model binding performed here'}
        e['provenance']['sourceLocators'].append('Main PDF p. 4, printed p. 1123, Table 2 and footnote c')
        inputs[str(H/'structure-candidate/independent-audit-addendum.json')]=sha(H/'structure-candidate/independent-audit-addendum.json')
    if 'pyrex' in eid:
        body='<path d="M245 223H749Q799 223 799 256Q799 289 749 289H245" fill="#e8f4f8" stroke="#8db4c3" stroke-width="5"/><path d="M248 240H749Q775 240 775 256Q775 272 749 272H248" fill="#fff" stroke="#bfd8e0" stroke-width="2"/><path d="M246 220V292" stroke="#638d9d" stroke-width="5"/>'+txt(500,359,'Fine capillary · schematic only',24)
    else:
        body='<rect x="220" y="164" width="560" height="220" rx="24" fill="#f1f6f8" stroke="#b7cfd8"/>'+txt(500,212,label,20,color='#587a89')+txt(500,292,center,57,weight=500)
        if 'in66' in eid:body+=txt(500,347,'Average refinement: Si₉₆ / Al₉₆ · separate context',18)
        else:body+=txt(500,347,'Source identity · no atomic geometry',18)
    save(e,body,footer)

# Preserve exact qualified reference assets; source-specific behavior lives in pending binding notes.
for e in reused:
    for key in ['svgPath','model2dPath','model3dPath']:
        if e.get(key):snapshot(R/e[key],O/'reused'/e[key])
    doc=pymupdf.open(stream=(O/'reused'/e['svgPath']).read_bytes(),filetype='svg');doc[0].get_pixmap(matrix=pymupdf.Matrix(1,1),alpha=False).save(str(O/'review'/f'reused-{e["id"]}.png'))
dump(O/'registry-additions.json',{'schemaVersion':'1.0.0','source_id':'heo2003','status':'private_author_proposal_pending_independent_audit_and_canonical_binding','entries':entries})
dump(O/'reused-references.json',{'status':'candidate_reuse_after_author_checks_pending_independent_review','entries':reused,'immutable_snapshots':snapshots,'notes':['Water aliases include historical Milli-Q wording, but name/captions/models are source-neutral. Do not use that alias to infer Heo water grade.','H2S reference is locally computed ETKDGv3/UFF, not measured gas geometry or PubChem3D; its original DOI is retained as provenance only, without importing that paper’s gas/aqueous recipe.','Norberg sodium acetate is only a graph-fragment reference. Its sodium, control role, hydration and source-specific wording are not reused as Heo facts.']})
route='heo-2003-in66-route'
mapping={'na-x':'identity-heo2003-na-x','tl-acetate':'heo2003-thallous-acetate','feed-water':'water','wash-water':'water','in-metal':'identity-heo2003-indium-metal','h2s':'hydrogen-sulfide','pyrex':'identity-heo2003-pyrex','final-crystal':'identity-heo2003-in66-x','parent-reference':'identity-heo2003-in87-x','indium-reference':'identity-heo2003-indium-metal','argon':'argon'}
notes={'na-x':'Sodium zeolite X starting host. Nominal Na92Si100Al92O384; referenced host synthesis is uninspected and no Na-X coordinates are inferred.',
 'tl-acetate':'Thallous acetate, Aldrich, 99.99%. Formal salt connectivity only; no hydrate, Tl–O bond, coordination geometry or unique aqueous speciation assigned.',
 'feed-water':'Water component of the 0.1 mol/L aqueous thallous-acetate feed, pH 6.4. Water grade is unspecified; it is not identified as deionized or Milli-Q.',
 'wash-water':'Explicitly deionized wash water. Table 1 reports 10.0 mL and one day for washing; these are separate from the feed volume and stock preparation.',
 'in-metal':'Indium metal reagent, Aldrich, 99.999%. Mass, ratio and detailed temperature gradient are unreported; no bulk lattice or isolated-atom model assigned.',
 'h2s':'Zeolitically dried hydrogen sulfide, Aldrich, 99.999%, 0.5 atm at 673 K for 12 h. Drying medium identity and procedure, gas quantity and flow are unreported. Free-molecule reference only; no aqueous-delivery recipe or measured gas geometry is imported.',
 'pyrex':'Fine Pyrex capillary apparatus. No dimensions or exact glass composition are supplied; not a chemical precursor.',
 'final-crystal':'Final In66-X specimen context. Nominal Si100Al92 differs from the average Si96Al96 refinement. Sealed diffraction, atmosphere-exposed EDS and sputtered XPS states stay distinct; this shared icon cannot establish sample joins.',
 'parent-reference':'In87-X parent comparison. Figure 1B was copied from reference 34; no parent atomic structure or same-crystal join is supplied by the final In66-X model.',
 'indium-reference':'Indium metal XPS reference in Figure 2A; displayed spectral intensity is scaled by the source caption. This analytical reference is separate from the synthesis reagent charge.',
 'argon':'Argon used for XPS ion sputtering. It is not reported as the synthesis atmosphere.'}
slots=[]
for mid,eid in mapping.items():
    slots.append({'record_id':route if mid in ['na-x','tl-acetate','feed-water','wash-water','in-metal','h2s','pyrex'] else None,'record_scope':'announced route material' if mid in ['na-x','tl-acetate','feed-water','wash-water','in-metal','h2s','pyrex'] else 'analytical contexts; exact canonical record IDs pending','source_material_id':mid,'registry_id':eid,'json_pointer':None,'canonical_sha256':None,'display_scope':notes[mid],'viewOverrides':{'name':{'feed-water':'Water · aqueous-feed solvent','wash-water':'Deionized water · wash','argon':'Argon · XPS sputtering'}.get(mid,next((e['name'] for e in entries+reused if e['id']==eid),mid)),'caption':notes[mid],'limitations':[notes[mid]]},'binding_approved':False,'independent_scientific_audit':'pending','canonical_binding_status':'await actual frozen canonical proposal'})
dump(O/'molecule-binding-plan.json',{'schemaVersion':'1.0.0','source_id':'heo2003','status':'provisional_stable_ids_only_not_final_bindings','slots':slots,'extra_state_references':[{'registry_id':'identity-heo2003-tl-x','scope':'Tl-X intermediate; bind only if a corresponding canonical state/material context exists'},{'registry_id':'identity-heo2003-surface-residue','scope':'Unidentified gray residue; never assign a candidate sulfide as confirmed composition'}],'final_record_bindings_created':False,'binding_approved':False})
components={'schema':'mattersyn-component-view-proposal/1','status':'private_author_proposal_pending_canonical_and_independent_review','record_id':route,'stock_id':'tl-acetate-feed','stock_json_pointer':None,'canonical_sha256':None,'label':'Aqueous thallous-acetate feed','scope':'0.1 mol/L; pH 6.4. Table 1 reports 10.0 mL but reservoir/total-passed/stock-preparation basis is unresolved. No fixed salt:water count, hydrate, ion-pair geometry or solution species distribution is assigned.','components':[{'registry_id':'heo2003-thallous-acetate','material_id':'tl-acetate','role':'source-named salt; formal ionic connectivity','viewOverrides':{'name':'Thallous acetate · salt reference','caption':notes['tl-acetate'],'limitations':[notes['tl-acetate']]}},{'registry_id':'water','material_id':'feed-water','role':'aqueous solvent, grade unspecified','viewOverrides':{'name':'Water · aqueous-feed solvent','caption':notes['feed-water'],'limitations':[notes['feed-water']]}}],'binding_approved':False,'source_stock_preparation_created':False}
dump(O/'component-view-proposal.json',components)
htmlpage='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Heo · aqueous feed components</title><style>body{font:18px/1.55 Arial,sans-serif;color:#203b4a;background:#f4f8fa;max-width:1060px;margin:40px auto;padding:0 24px}h1{font-weight:550;font-size:32px}.sub{color:#547182}nav{display:flex;gap:12px;margin:26px 0}button{font:inherit;background:white;border:1px solid #b5ced9;border-radius:10px;padding:12px 20px;cursor:pointer}button[aria-pressed=true]{background:#dceef3;border-color:#477f93}figure{margin:0;background:#fff;border:1px solid #d5e4e9;border-radius:18px;padding:16px}img{width:100%;max-height:510px;object-fit:contain}#note{min-height:82px}.badge{font-size:14px;letter-spacing:.07em;text-transform:uppercase;color:#557786}.scope{padding:20px;background:#e8f1f5;border-radius:12px}</style><p class="badge">Private author proposal · final binding pending</p><h1>Aqueous thallous-acetate feed</h1><p class="sub">0.1 mol/L · pH 6.4 · separate salt and solvent references</p><nav aria-label="Choose stock component"><button type="button" data-key="salt" aria-pressed="true">Salt reference</button><button type="button" data-key="water" aria-pressed="false">Solvent water</button></nav><figure><img id="depiction" src="svg/heo2003-thallous-acetate.svg" alt="Formal thallium(I) and acetate components"><figcaption id="note"></figcaption></figure><p class="scope">The selector explains named components. It does not show a hydrate, Tl–O coordination, a fixed salt:water ratio, measured solution geometry or a drying recipe. Feed-water grade is unspecified; the separately used wash water is explicitly deionized.</p><script>const data={salt:{src:'svg/heo2003-thallous-acetate.svg',alt:'Formal disconnected Tl+ and acetate− components',note:'Thallous acetate, 99.99%. The acetate carboxylate group is highlighted. This is one resonance representation, with no Tl–O bond or 3D salt geometry.'},water:{src:'reused/svg/water.svg',alt:'Water molecular reference',note:'Water is the aqueous-feed solvent. Its grade is not specified. The reference molecule does not establish hydration number, salt solvation or a measured liquid structure.'}};function select(k){const d=data[k];document.getElementById('depiction').src=d.src;document.getElementById('depiction').alt=d.alt;document.getElementById('note').textContent=d.note;for(const b of document.querySelectorAll('button[data-key]'))b.setAttribute('aria-pressed',String(b.dataset.key===k));}for(const b of document.querySelectorAll('button[data-key]'))b.addEventListener('click',()=>select(b.dataset.key));select('salt');</script></html>'''
(O/'component-preview.html').write_text(htmlpage,encoding='utf-8')
dump(O/'generation-manifest.json',{'schema':'mattersyn-private-molecular-author-generation/1','source_id':'heo2003','author':'/root/backlog_eta','at':datetime.now(timezone.utc).isoformat(),'status':'author_generated_validation_and_independent_review_pending','counts':{'new_entries':len(entries),'reused_entries':len(reused),'new_2d_models':1,'reused_2d_models':2,'reused_3d_models':2,'new_3d_models':0,'svg_depictions':len(entries)+len(reused),'announced_material_slots':len(slots),'stock_component_selectors':1},'input_hashes':inputs,'provenance_snapshots':snapshots,'files':{str(p.relative_to(O)):sha(p) for p in O.rglob('*') if p.is_file() and p.name not in ['generation-manifest.json','author-validation.json','package-freeze.json']},'no_external_lookup':True,'no_paper_download':True,'no_site_or_shared_mutation':True,'final_canonical_binding_pending':True})
assert all(sha(p)==h for p,h in inputs.items())
print(json.dumps({'generated_entries':len(entries),'reused':len(reused),'svg_previews':len(entries)+len(reused),'slots_planned':len(slots),'status':'author_previews_ready_for_actual_visual_inspection'}))
