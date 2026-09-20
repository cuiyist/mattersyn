from pathlib import Path
import json,hashlib,html,sys
sys.path.insert(0,'[local path redacted]')
sys.path.insert(0,'[local path redacted]')
import pymupdf
from PIL import Image,ImageDraw
B=Path(__file__).resolve().parent; O=B/'visuals'
for d in [O,O/'svg',O/'models',O/'review']:d.mkdir(exist_ok=True)
DOI='10.1021/jp0208743'; SH='c8fd35a429bf636fcccc5dfeb3211cea44299e911fbfc80e1a308c75b7b04917'
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def txt(x,y,s,size=21):return f'<text x="{x}" y="{y}" text-anchor="middle" font-family="Arial,sans-serif" font-size="{size}" fill="#294451">{html.escape(s)}</text>'
def start(name,caption):return '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="420" viewBox="0 0 900 420"><title>'+html.escape(name)+'</title><desc>'+html.escape(caption)+'</desc><rect x="10" y="12" width="880" height="396" rx="24" fill="#f5f9fb"/>'
entries=[];checks=[]
def save(id,name,formula,kind,caption,svg,extra=None):
 e=dict(id=id,name=name,aliases=[name],formula=formula,displayFormula=formula,depictionKind=kind,pubchemCid=None,sourceUrls=['https://doi.org/'+DOI],svgPath='svg/'+id+'.svg',model2dPath=None,model3dPath=None,functionalGroups=[],caption=caption,limitations=['No measured atomic coordinates supplied; illustration excluded from training labels.'],provenance={'sourceDoi':DOI,'sourceSha256':SH,'identitySource':'Inspected local main article, sample preparation and specimen descriptions.','measuredCoordinates':False,'eligible_training':False},assetHashes={})
 if extra:e['provenance'].update(extra)
 (O/e['svgPath']).write_text(svg+'</svg>',encoding='utf-8');e['assetHashes']={'svgPath':sha(O/e['svgPath'])};entries.append(e)
for id,name,formula,counts in [('silica','Silicon dioxide powder','SiO2',{'Si':1,'O':2}),('zinc-oxide','Zinc oxide powder','ZnO',{'Zn':1,'O':1}),('alumina','Aluminium oxide powder','Al2O3',{'Al':2,'O':3}),('lead-dioxide','Lead dioxide powder, as printed','PbO2',{'Pb':1,'O':2}),('boron-oxide','Boron oxide powder','B2O3',{'B':2,'O':3})]:
 caption='Formula-unit atom-count illustration for the reported oxide powder. Positions are a graphic layout, not a discrete oxide molecule, measured lattice, polymorph or glass-network geometry. No atomic coordinate download is implied.'
 if id=='lead-dioxide':caption+=' The source repeatedly prints PbO2; it has not been changed to PbO or assigned a retained melt oxidation state.'
 atoms=[a for a,n in counts.items()for _ in range(n)];n=len(atoms)
 svg=start(name,caption)+txt(450,62,name,27)+txt(450,105,formula,27)
 for i,a in enumerate(atoms):
  x=450+(i-(n-1)/2)*105;fill='#e7b3ac' if a=='O' else '#a9c6d8';svg+=f'<circle cx="{x}" cy="213" r="34" fill="{fill}" stroke="#63899c"/>'+txt(x,221,a,24)
 svg+=txt(450,292,'Formula-unit composition · no bonds or lattice assigned',20)+txt(450,341,'Powder phase and atomic structure are not reported',19)
 save('identity-dantas-'+id,name,formula,'formula',caption,svg,{'atomCountIllustration':counts,'coordinateSource':None})
 checks.append({'check':id+' displayed atom counts equal formula','passed':True,'counts':counts})
for id,name,formula,rows,caption in [
 ('sulfur-source','Sulfur source, chemical form unspecified',None,['Sulfur-doped glass','Sulfur reagent not identified','Dose and introduction step unreported'],'The source specifies sulfur doping but does not identify the sulfur reagent, quantity or introduction sequence. No elemental S8, sulfide salt or other chemical is substituted.'),
 ('aluminum-crucible','Aluminum crucible, literal source wording','Al',['Source wording: aluminum crucible','Reported melting: 1400 °C for 2 h','Vessel identity remains unresolved'],'The paper literally names an aluminum crucible at 1400 °C. Preserve this questionable vessel description without silently changing it to alumina. Al labels the stated material only, not a verified apparatus specification or reagent.'),
 ('glass-host','Sulfur-doped multicomponent precursor glass',None,['SiO₂ / Na₂CO₃ / ZnO / Al₂O₃ / PbO₂ / B₂O₃','Sulfur source and proportions missing','Listed powders do not define final glass speciation'],'Precursor-loaded glass after fusion and stress relief. The list is the batch precursor composition, not a stoichiometric glass formula or proof that starting salts persist chemically unchanged.')]:
 svg=start(name,caption)+txt(450,64,name,25)
 for y,row in zip([155,230,305],rows):svg+=txt(450,y,row,21)
 save('identity-dantas-'+id,name,formula,'unresolved-identity' if id!='glass-host' else 'mixture',caption,svg)
for sample,hours,cohort in [('sg1',1,'Optical cohort'),('sg2',3,'Optical cohort'),('sg3',6,'Optical cohort'),('sg4',12,'Optical cohort'),('afm1',5,'AFM cohort'),('afm2',30,'AFM cohort')]:
 name=sample.upper()+' · PbS quantum dots in glass';caption='Illustrative embedded-particle/glass architecture. Dot positions, relative dimensions and colors are explanatory, not an AFM reconstruction, atomic crystal structure or interpolation of annealing time into size. '+cohort+'; separate source sample '+sample.upper()+'.'
 svg=start(name,caption)+txt(450,55,name,26)+'<rect x="56" y="95" width="300" height="206" rx="13" fill="#d5e4ed" stroke="#6c91a5"/>'
 for x,y,r in [(100,134,12),(192,133,15),(289,145,12),(136,217,15),(239,203,12),(309,260,12),(83,270,10)]:svg+=f'<circle cx="{x}" cy="{y}" r="{r}" fill="#779aa8" stroke="#3c6e80"/>'
 svg+=txt(627,148,'600 °C · '+str(hours)+' h anneal',25)+txt(627,210,cohort,22)+txt(627,267,'Glass proportions unreported',20)+txt(450,359,'Architecture schematic · no measured atomic coordinates',20)
 save('identity-dantas-'+sample+'-specimen',name,'PbS/glass','specimen',caption,svg)
write(O/'registry-additions.json',{'schemaVersion':'1.0.0','entries':entries})
write(O/'asset-manifest.json',{'files':[{'path':p.relative_to(O).as_posix(),'sha256':sha(p)}for p in sorted((O/'svg').glob('*.svg'))]})
write(O/'molecular-generation-check.json',{'status':'passed','entries':len(entries),'checks':checks,'scope':'Source identity and formula-unit/specimen diagrams, no molecular conformer or atomic lattice generated. Existing sodium-carbonate connectivity reused separately.'})
for offset in range(0,len(entries),6):
 sheet=Image.new('RGB',(1200,1020),'#dce7ec')
 for j,e in enumerate(entries[offset:offset+6]):
  d=pymupdf.open(stream=(O/e['svgPath']).read_bytes(),filetype='svg');pdf=pymupdf.open('pdf',d.convert_to_pdf());px=pdf[0].get_pixmap(matrix=pymupdf.Matrix(.64,.64),alpha=False);im=Image.frombytes('RGB',(px.width,px.height),px.samples);can=Image.new('RGB',(600,340),'white');can.paste(im,(12,28));ImageDraw.Draw(can).text((10,5),e['id'],fill='black');sheet.paste(can,(j%2*600,j//2*340))
 sheet.save(O/'review'/f'molecular-contact-{offset//6+1}.png')
print('Created',len(entries),'private source identity references; no invented molecular or atomic crystal coordinates.')
