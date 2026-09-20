"""Private source-scoped product diagrams; never atomic coordinates or CIFs."""
from pathlib import Path
from html import escape
from collections import Counter
import hashlib,json,datetime
import xml.etree.ElementTree as ET

B=Path(__file__).resolve().parent
V=B/'visuals'/'products'
(V/'svg').mkdir(parents=True,exist_ok=True)
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
facts=read(B/'source-facts.json')
F={x['id']:x for x in facts['facts']}
def text(x,y,value,size=22,color='#223c51',weight=400,anchor='start'):
    return f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{color}" text-anchor="{anchor}">{escape(value)}</text>'
def circle(x,y,r,color):return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}" stroke="#426176" stroke-width="2"/>'
def fact_value(key):return F['gu2004-fact-'+key]['value']
def quantity(key):
    f=F['gu2004-fact-'+key]
    raw=str(f['value']) if f['value'] is not None else f"{f['minimum']}–{f['maximum']}"
    return ('≈ ' if f.get('approximate') else '')+raw+' '+f['unit']
def panel(title,body,footer):
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 840 480" role="img"><title>'+escape(title)+'</title><desc>'+escape(footer)+'</desc><rect width="840" height="480" fill="#f6fafc"/><g font-family="Arial, sans-serif">'+text(34,47,title,28,weight=600)+body+text(34,451,footer,17,color='#567084')+'</g></svg>'

entries=[]
def entry(rid,name,formula,body,caption,locators,source_facts=(),footer='Composition diagram; no measured atomic coordinates.'):
    svg=V/'svg'/(rid+'.svg')
    svg.write_text(panel(name,body,footer),encoding='utf-8')
    ET.parse(svg)
    for fid in source_facts:assert fid in F,fid
    entries.append({'id':rid,'name':name,'aliases':[name],'formula':formula,'displayFormula':formula,
        'depictionKind':'specimen','pubchemCid':None,'sourceUrls':['https://doi.org/10.1021/ja0496423'],
        'svgPath':'svg/'+svg.name,'model2dPath':None,'model3dPath':None,'functionalGroups':[],
        'caption':caption,'limitations':['The diagram is not a coordinate model, a measured specimen image or an exact structure–recipe label.'],
        'provenance':{'sourceDoi':'10.1021/ja0496423','sourceSha256':facts['source_sha256'],'siSha256':facts['si_sha256'],
            'identitySource':'Audited local main article and supporting information, with locators retained below.',
            'sourceLocators':locators,'sourceFactIds':list(source_facts),'measuredCoordinates':False,'eligible_training':False,
            'representation':'Source-scoped composition/domain diagram; pixel geometry is illustrative and is not in angstroms.'},
        'assetHashes':{'svgPath':sha(svg)}})

fept_body=circle(195,234,84,'#83a8bc')+text(195,244,'FePt',29,weight=600,anchor='middle')
fept_body+=text(336,182,'Source label 1',23,weight=600)+text(336,225,'Reported mean diameter: '+quantity('fept-1-average-diameter'),21)
fept_body+=text(336,270,'Before sulfur addition',21)+text(336,310,'Separate FePt comparison specimens',19,color='#567084')
entry('identity-gu-fept-1','FePt nanocrystals · source 1','FePt',fept_body,
      'FePt 1 is the precursor particle and the source-labeled optical/magnetic comparator. The reported average diameter is 2.5 nm. A domain icon does not establish an ordered Fe/Pt atomic arrangement, a ligand geometry or an identical physical batch across techniques.',
      ['Main PDF p. 1, one-pot overview','Main PDF p. 2, Figure 1A','SI PDF p. 2, Figures S-2 and S-3'],['gu2004-fact-fept-1-average-diameter'])

hetero=circle(274,226,67,'#83a8bc')+circle(441,226,100,'#e1b56d')
hetero+=text(274,235,'FePt',25,weight=600,anchor='middle')+text(441,235,'CdS',29,weight=600,anchor='middle')
hetero+=text(665,182,'Source label 4',23,weight=600,anchor='middle')+text(665,223,'Two joined domains',20,anchor='middle')
hetero+=text(665,261,'Schematic contact',18,color='#567084',anchor='middle')
hetero+=text(70,366,'FePt: '+quantity('final-fept-component-diameter')+' · disordered FCC',20)
hetero+=text(440,366,'CdS: '+quantity('final-cds-component-diameter')+' · zinc blende',20)
hetero+=text(70,405,'Phase assignments: original SAED, Figure 1D.',19,color='#567084')
entry('identity-gu-fept-cds-4','FePt–CdS heterodimers · source 4','FePt/CdS',hetero,
      'Two joined FePt and CdS domains represent the source-assigned heterodimer architecture. The component sizes and phases are source reports; the domain colors, shapes and contact in this diagram are illustrative. No atom positions, interface orientation, surface-ligand positions or refined CIF are supplied. The overall approximately 7 nm description is a separate source-wide metric, not calculated from this diagram.',
      ['Main PDF p. 1, one-pot overview and Scheme 1','Main PDF p. 2, Figure 1B–D'],
      ['gu2004-fact-final-fept-component-diameter','gu2004-fact-final-cds-component-diameter','gu2004-fact-final-fept-phase','gu2004-fact-final-cds-phase'],
      'Domain diagram, not to scale; no measured atomic interface.')

for number,formula,line1,line2 in [
    (2,'FePt/S','FePt after the sulfur-addition stage','A sulfur-covered precursor is proposed.'),
    (3,'FePt/CdS','FePt after cadmium-precursor addition','An amorphous CdS-covered intermediate is proposed.')]:
    body=text(52,135,formula,42,weight=600)+text(52,196,line1,25)
    body+=text(52,242,line2,22)+text(52,303,'An intact shell was not successfully isolated.',22,weight=600)
    body+=text(52,351,'The isolated microscopy specimen does not establish shell geometry.',20,color='#567084')
    entry(f'identity-gu-isolated-{number}',f'Isolated intermediate · source {number}',formula,body,
          f'The composition label belongs to source intermediate {number}. Scheme 1 proposes a covered intermediate, but the paper reports failure to isolate intact shell structures. This identity card deliberately leaves the isolated particle morphology, layer thickness and atomic positions unassigned.',
          ['Main PDF p. 1, Scheme 1 and intermediate-isolation discussion',f'SI PDF p. 3, Figure S-{number+2}'])

body=''
for y,label,note in [(128,'1 · FePt','Precursor and separate FePt comparator contexts'),(205,'2 · FePt/S','Isolated intermediate; intact sulfur layer unverified'),(282,'3 · FePt/CdS','Isolated intermediate; intact CdS shell unverified'),(359,'4 · FePt–CdS','TEM, HRTEM and SAED final-product contexts')]:
    body+=f'<line x1="35" y1="{y+21}" x2="803" y2="{y+21}" stroke="#d8e5ed"/>'+text(48,y,label,25,weight=600)+text(280,y,note,19)
entry('identity-gu-microscopy-context','Microscopy and diffraction specimens','FePt/CdS',body,
      'This record collects source-labeled specimens 1–4. It is not a single measured batch or one common atomic model. The main Figure 1A and SI Figure S-4/S-5 isolate the precursor/intermediate contexts; main Figure 1B–D carries final heterodimer microscopy and SAED. Cross-technique physical aliquot identity remains unresolved.',
      ['Main PDF p. 2, Figure 1A–D','SI PDF p. 3, Figures S-4/S-5'])

specimen={
 'gu-2004-fept-control':{'fept-1':'identity-gu-fept-1'},
 'gu-2004-magnetometry':{'product-4':'identity-gu-fept-cds-4'},
 'gu-2004-microscopy':{'precursor-1':'identity-gu-fept-1','isolated-2':'identity-gu-isolated-2','isolated-3':'identity-gu-isolated-3','product-4':'identity-gu-fept-cds-4'},
 'gu-2004-optical':{'product-4':'identity-gu-fept-cds-4'},
 'gu-2004-xrf':{'product-4':'identity-gu-fept-cds-4'}}
products={'gu-2004-cdacac-preparation':'gu2004-cadmium-acac-reference','gu-2004-heterodimer':'identity-gu-fept-cds-4','gu-2004-fept-control':'identity-gu-fept-1','gu-2004-microscopy':'identity-gu-microscopy-context',
          **{rid:'identity-gu-fept-cds-4' for rid in ['gu-2004-magnetometry','gu-2004-optical','gu-2004-xrf']}}
records={p.stem:read(p) for p in (B/'canonical-drafts').glob('*.json')}
for rid,slots in specimen.items():
    materials={m['id']:m for m in records[rid]['materials']}
    for mid,eid in slots.items():assert materials[mid]['role']=='specimen' and eid in {e['id'] for e in entries}
assert sum(map(len,specimen.values()))==8
save(V/'product-registry-additions.json',{'schemaVersion':'1.0.0','entries':entries})
save(V/'specimen-bindings-additions.json',{'sourceRecordSha256':{rid:sha(B/'canonical-drafts'/(rid+'.json')) for rid in specimen},'recordBindings':specimen,
     'bindingNotes':{rid:{mid:'Source-labeled composition/domain reference; physical batch, atomic arrangement and interface/ligand geometry are not inferred.' for mid in slots} for rid,slots in specimen.items()},'bindingApproved':False})
save(V/'product-reference-proposal.json',{'scope':'Source-labeled product composition/domain diagrams; no atomistic coordinates. Precursor-product Cd(acac)2 points to a separately verified formal-component reference, not measured coordination geometry.','recordBindings':products,'publicationApproved':False})
save(V/'crystal-reference-proposal.json',{'entries':[],'files':[],'source_id':'gu2004','status':'no_locally_verified_atomic_reference_available',
    'scope':'Original SAED supports disordered FCC FePt and zinc-blende CdS in final heterodimers. The supplied main/SI give no numerical lattice parameter, atomic coordinates or source CIF. No verified FePt/CdS CIF was found in the existing local reference collection. Existing CdSe or other-material coordinates must not substitute. Original TEM/HRTEM/SAED and source-scoped domain diagrams remain available.',
    'measuredSampleStructure':False,'trainingEligible':False,'generatedCif':False,'source_facts_sha256':sha(B/'source-facts.json')})
save(V/'product-author-checks.json',{'status':'passed_author_checks_pending_independent_audit','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'entry_count':len(entries),'specimen_slots':8,'product_record_bindings':len(products),'svg_xml_valid':True,'atomic_coordinate_files':0,
    'source_facts_sha256':sha(B/'source-facts.json'),'source_inventory_sha256':sha(B/'source-inventory.json'),
    'bound_files':{name:sha(V/name) for name in ['product-registry-additions.json','specimen-bindings-additions.json','product-reference-proposal.json','crystal-reference-proposal.json']},
    'assets':{e['svgPath']:e['assetHashes']['svgPath'] for e in entries},'requires_visual_preview':True,'independent_audit':False})
print(json.dumps({'entries':len(entries),'specimen_slots':8,'product_bindings':len(products),'atomic_coordinate_files':0,'site_modified':False}))
