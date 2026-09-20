"""Author extraction from the completely read local main/SI pair. Private outputs only."""
from pathlib import Path
from datetime import datetime,timezone
from decimal import Decimal
import json,re,hashlib,copy,math
from PIL import Image,ImageDraw,ImageOps
import pypdfium2
import source_author_data as A
P=Path(__file__).resolve().parent
NOW=datetime.now(timezone.utc).isoformat();SID='lian2021';DOI='10.1021/acsami.1c18038';GROUP='legacy::10.1021_acsami.1c18038'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(n,o):(P/n).write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
payload=json.loads((P/'complete-source-payloads.json').read_bytes());docs={d['document_id']:d for d in payload['documents']}
def ev(role,page,locator):return {'source_id':SID+'-'+role,'document_role':role,'source_sha256':docs[role]['source_sha256'],'pdf_page':page,'printed_page':58907+page if role=='main' else 'S-'+str(page),'locator':locator}
def q(raw,unit,meaning,role,page,loc,scale=1,flags=()):
 s=str(raw).strip();t=s.replace('−','-').replace('–','-');value=error=None;rg=None;cmp=None;approx=False;status='reported';parts=None
 if unit=='1e-4':unit='dimensionless';scale=1e-4
 if t.startswith(('about ','approximately ')):
  t=t.split(' ',1)[1];approx=True
 m=re.match(r'^(>=|<=|>|<|≥|≤)',t)
 if m:cmp={'≥':'>=','≤':'<='}.get(m[1],m[1]);t=t[len(m[1]):].strip()
 if re.fullmatch(r'[+-]?\d+(?:\.\d+)?\(\d+\)',t):
  v,e=t.split('(');value=float(Decimal(v)*Decimal(str(scale)));error=float(Decimal(e[:-1])*Decimal(10)**(-len(v.split('.')[1])if'.'in v else 0)*Decimal(str(scale)))
 elif '±'in t:
  v,e=t.split('±');value=float(Decimal(v.strip())*Decimal(str(scale)));error=float(Decimal(e.strip())*Decimal(str(scale)))
 elif re.fullmatch(r'[+-]?\d+(?:\.\d+)?',t):value=float(Decimal(t)*Decimal(str(scale)))
 elif re.fullmatch(r'\d+(?:\.\d+)?-\d+(?:\.\d+)?',t):rg=dict(zip(['min','max'],[float(Decimal(x)*Decimal(str(scale)))for x in t.split('-')]))
 elif unit=='mass_ratio_parts':parts=[int(x)for x in t.split('/')];status='reported_ratio_parts'
 elif unit=='mesh':parts=[int(x)for x in t.split('x')];status='reported_mesh'
 else:status='reported_text'
 if unit=='identifier':value=None;status='reported_identifier'
 return {'raw_text':s,'value':value,'unit':unit,'uncertainty':error,'uncertainty_definition':'not specified'if'±'in s else 'parenthesized standard uncertainty'if'('in s and error is not None else None,'range':rg,'comparison':cmp,'approximate':approx,'components':parts,'status':status,'printed_to_value_scale':scale,'meaning':meaning,'evidence':[ev(role,page,loc)],'conflict_ids':[f for f in flags if f.startswith('C')],'gap_ids':[f for f in flags if f.startswith('G')]}
for f in payload['source_copies']:assert sha(f['source_path'])==f['sha256']
facts=[]
for fid,role,page,loc,title,claim,scope,qs,flags in A.FACTS:
 facts.append({'id':SID+'-'+fid,'title':title,'claim':claim,'sample_scope':scope,'claim_class':'author_interpretation'if scope.startswith('author-')else'cited_context'if scope.startswith('cited-')else'reported_source_evidence','evidence':[ev(role,page,loc)],'quantities':[q(raw,unit,name,role,page,loc,flags=flags)for name,raw,unit in qs],'conflict_ids':[f for f in flags if f.startswith('C')],'gap_ids':[f for f in flags if f.startswith('G')],'independent_audit_status':'pending'})
fb={f['id'].removeprefix(SID+'-'):f for f in facts}
materials=[{'id':i,'name':n,'source_formula_or_abbreviation':form,'role':role,'scope_note':note,'evidence':[ev('main',7 if i in ['nitrogen','liquid-nitrogen']else 6,'4.5'if i in ['nitrogen','liquid-nitrogen']else'4.1–4.4')]}for i,n,form,role,note in A.MATERIALS]
def op(i,action,ins,outs,fs,retained=None,missing=()):
 return {'id':i,'action':action,'inputs':ins,'outputs':outs,'retained_fraction':retained,'source_fact_ids':[SID+'-'+f for f in fs],'quantities':[copy.deepcopy(qv)for f in fs for qv in fb[f]['quantities']],'evidence':[e for f in fs for e in fb[f]['evidence']],'missing_fields':list(missing),'independent_audit_status':'pending'}
specs=[
('bulk-a-route','Bulk A solvent-evaporation synthesis','synthesis',[
 ('a-dissolve-filter','Dissolve and filter',['tpa-cl','sbcl3','dmf'],['a-feed'],['bulk-a-charge'],None,['filter specification','vessel']),
 ('a-evaporate','Slow room-temperature evaporation',['a-feed'],['bulk-a'],['bulk-a-growth'],'bulk-a',['absolute temperature','yield'])]),
('bulk-b-route','Bulk B stoichiometric variant','synthesis_variant',[
 ('b-dissolve-filter','Use 1 mmol cation salt in the otherwise inherited procedure',['tpa-cl','sbcl3','dmf'],['b-feed'],['bulk-b-variant'],None,['filter specification','vessel']),
 ('b-evaporate','Inherited slow room-temperature evaporation',['b-feed'],['bulk-b'],['bulk-b-variant'],'bulk-b',['absolute temperature','yield'])]),
('nc-a-route','A nanocrystal LARP synthesis','synthesis',[
 ('nc-dissolve-filter','Prepare clear filtered stock',['tpa-cl','sbcl3','dmf'],['nc-feed'],['nc-stock'],None,['final solution volume','filter']),
 ('nc-inject','Rapid injection into vigorously stirred antisolvent/ligand',['nc-feed','toluene','oleic-acid'],['nc-crude'],['nc-injection'],None,['temperature','injection duration','stir rate','aging duration']),
 ('nc-centrifuge','Centrifuge and collect powder',['nc-crude'],['nc-a'],['nc-recovery'],'nc-a',['wash','drying','yield'])]),
('composite-film-series','Five phosphor/nanocrystal/PS film formulations','film_processing',[
 ('film-blend','Blend ratio series with PS/toluene and stir',['blue-phosphor','nc-a','ps','toluene'],['film-mixtures'],['composite-mixing'],None,['masses','PS concentration','toluene volume']),
 ('film-cast','Drop-cast, evaporate in fume hood, peel',['film-mixtures','glass'],['composite-film'],['composite-casting'],'composite-film',['drying time/temperature','dimensions','thickness'])]),
('spincoat-film-route','Separate precursor spin-coating procedure','film_processing',[
 ('spin-feed','Dissolve salts and filter clear',['tpa-cl','sbcl3','dmf'],['spin-feed'],['spincoat-stock'],None,['filter specification']),
 ('spin-deposit','Spin-coat then anneal',['spin-feed','glass'],['spincoat-film'],['spincoat-deposit'],'spincoat-film',['atmosphere','film thickness'])]),
('bulk-characterization','Bulk diffraction/XPS/TGA/optical characterization','characterization',[
 ('bulk-xray','Acquire PXRD and SCXRD',['bulk-a','bulk-b'],['bulk-diffraction-data'],['acquisition-xray'],None,['scan details','original ZIP']),
 ('bulk-xps-tga','Acquire XPS and TGA under N2',['bulk-a','bulk-b','nitrogen'],['bulk-xps-tga-data'],['acquisition-xps-tga'],None,['ramp','N2 flow']),
 ('bulk-optics','Acquire PL/PLE/TCSPC/temperature spectra',['bulk-a','bulk-b','liquid-nitrogen'],['bulk-optical-data'],['acquisition-pl'],None,['specific batch join']),
 ('bulk-plqe','Baseline then integrate crystal PLQE',['bulk-a'],['bulk-plqe-data'],['acquisition-plqe'],None,['mass'])]),
('nc-characterization','Nanocrystal microscopy/optical characterization','characterization',[
 ('nc-tem','Acquire EFTEM images',['nc-a'],['nc-microscopy-data'],['acquisition-tem'],None,['grid','deposition']),
 ('nc-optics','Acquire PL/PLE and decay',['nc-a'],['nc-optical-data'],['acquisition-pl'],None,['sample-state details for non-PLQE spectra']),
 ('nc-plqe','Baseline then integrate dried-powder PLQE',['nc-a'],['nc-plqe-data'],['acquisition-plqe','nc-plqe'],None,['drying protocol','mass'])]),
('film-beta-characterization','Film PL and bulk/film beta excitation','characterization',[
 ('film-pl','Acquire composite-film and spincoat PL',['composite-film','spincoat-film'],['film-optical-data'],['acquisition-pl'],None,['thickness']),
 ('beta-irradiate','Irradiate crystals and NC composite film; collect RL',['bulk-a','composite-film'],['rl-data'],['acquisition-beta'],None,['exposure duration','exact beta-film ratio','absolute yield'])]),
('dft-calculation','Composition-specific relaxed DFT calculations','calculation',[
 ('dft-relax','PAW/PBE/HSE06 calculations and full lattice/position relaxation',['bulk-a','bulk-b'],['calculated-structures-bands'],['dft-method'],None,['relaxed coordinate files','complete convergence settings'])])]
protocols=[{'id':i,'title':t,'kind':k,'operations':[op(*o)for o in ops],'complete_laboratory_sop':False,'independent_audit_status':'pending'}for i,t,k,ops in specs]
# Inherited B amounts only accompany solution preparation; duration only accompanies evaporation.
for pr in protocols:
 for o in pr['operations']:
  if o['id']=='b-evaporate':o['quantities']=[x for x in o['quantities']if x['unit']=='day']
  if o['id']=='b-dissolve-filter':o['quantities']=[x for x in o['quantities']if x['unit']!='day']
stocks=[]
for i,fid in [('a-feed','bulk-a-charge'),('b-feed','bulk-b-variant'),('nc-feed','nc-stock'),('spin-feed','spincoat-stock')]:
 stocks.append({'id':i,'components':[{'material_id':'tpa-cl','role':'solute'},{'material_id':'sbcl3','role':'solute'},{'material_id':'dmf','role':'solvent'}],'source_fact_id':SID+'-'+fid,'quantities':[copy.deepcopy(x)for x in fb[fid]['quantities']if x['unit']!='day'],'concentration':None,'scope':'Solvent charge is known; final solution volume and dissolved speciation are not. No exact aliquot mmol is inferred.'})
stocks.append({'id':'ps-toluene','components':[{'material_id':'ps','role':'polymer_solute'},{'material_id':'toluene','role':'solvent'}],'quantities':[],'concentration':None,'evidence':[ev('main',6,'4.4')],'scope':'No polymer mass or solvent volume specified.'})

tables=[]
def table(i,title,cols,rows,pages,scope,notes):
 for ir,r in enumerate(rows):
  for ic,c in enumerate(r['cells']):c['id']=f'{i}-r{ir+1:03}-c{ic+1:02}'
 t={'id':i,'title':title,'columns':cols,'rows':rows,'sample_scope':scope,'evidence':[ev('si',p,i)for p in pages],'notes':notes,'author_transcription':'Native PDF text parsed with all rows visually read by extraction author. Distinct numerical audit pending.','independent_numerical_audit':'pending'};tables.append(t);return t
t1=[
('empirical formula','C24H56Cl5N2Sb','C12H28Cl4NSb',None,13),('molecular weight','671.7','449.9','g/mol',13),('temperature','296.05(10)','296.25(10)','K',13),('crystal system','triclinic','monoclinic',None,13),('space group','P-1','P21/c',None,13),
('a','10.7745(3)','18.19840(10)','angstrom',13),('b','10.8437(2)','15.74030(10)','angstrom',13),('c','16.3565(3)','13.67940(10)','angstrom',13),('alpha','76.301(2)','90','deg',13),('beta','75.451(2)','91.5970(10)','deg',13),('gamma','72.701(2)','90','deg',13),('volume','1738.68(7)','3916.92(4)','angstrom^3',13),('Z','2','8','count',13),('calculated density','1.283','1.526','g/cm^3',13),('mu','9.92','16.08','mm^-1',13),
('2theta lower exclusive','5.67','4.858','deg',13),('2theta upper exclusive','147.82','147.98','deg',13),
('h lower inclusive','-13','-13','index',14),('h upper inclusive','13','22','index',14),('k lower inclusive','-13','-19','index',14),('k upper inclusive','13','19','index',14),('l lower inclusive','-20','-16','index',14),('l upper inclusive','20','17','index',14),
('reflections collected','20675','48777','count',14),('reflections unique','6814','7852','count',14),('Rint','0.0383','0.0698','dimensionless',14),('data','6814','7852','count',14),('restraints','0','0','count',14),('parameters','297','334','count',14),('goodness of fit F^2','1.045','1.028','dimensionless',14),('R1 I>=2sigma(I)','0.0313','0.0331','dimensionless',14),('wR2 I>=2sigma(I)','0.0812','0.0879','dimensionless',14),('R1 all data','0.0320','0.0363','dimensionless',14),('wR2 all data','0.0819','0.0900','dimensionless',14),('largest difference peak','0.49','0.94','e/angstrom^3',14),('largest difference hole','-1.24','-0.74','e/angstrom^3',14)]
rows=[]
for name,a,b,u,p in t1:
 cells=[{'column':col,**q(v,u,name+' '+col,'si',p,'Table S1 '+name)}for col,v in [('A',a),('B',b)]]
 for c in cells:
  if 'lower'in name:c['comparison']='>'if'exclusive'in name else'>='
  if 'upper'in name:c['comparison']='<'if'exclusive'in name else'<='
 rows.append({'row_label':name,'cells':cells})
table('table-s1','Single-crystal diffraction and refinement',['A','B'],rows,[13,14],'bulk-a-and-b',['A='+A.A,'B='+A.B,'Compound heading retained; combined source rows decomposed into explicit typed fields without new measurements.','I>=2sigma(I) literal threshold; two-theta ranges exclusive; index ranges inclusive.','Cu Kalpha from main; no numerical wavelength or hydrogen model specified.'])
# Parse successive tables with their actual page and left/right block preserved.
active=None;rawrows={n:[]for n in range(2,10)}
for p in range(14,27):
 for il,line in enumerate(docs['si']['pages'][p-1]['text'].splitlines(),1):
  m=re.match(r'^Table S(\d+)\.',line.strip())
  if m:active=int(m[1]);continue
  if line.strip()=='References':active=None
  if active not in rawrows:continue
  toks=line.split()
  if not toks or not re.fullmatch(r'(?:Sb|Cl|N|C)[0-9A-Z]+',toks[0]):continue
  rawrows[active].append((p,il,line,toks))
for n,atoms,want in [(2,2,29),(3,2,32),(4,3,38),(5,3,40)]:
 rows=[]
 for p,il,line,toks in rawrows[n]:
  width=atoms+1;assert len(toks)in[width,width*2],(n,p,line)
  for block in range(len(toks)//width):
   ts=toks[block*width:(block+1)*width];label='–'.join(ts[:atoms]);raw=ts[-1]
   assert re.fullmatch(r'\d+(?:\.\d+)?\(\d+\)',raw),(n,line)
   rows.append({'row_label':label,'atoms':ts[:atoms],'printed_block':'left'if block==0 else'right','source_line':il,'source_raw_line':line,'cells':[{'column':'distance'if atoms==2 else'angle',**q(raw,'angstrom'if atoms==2 else'deg',label,'si',p,f'Table S{n} {label}')} ]})
 assert len(rows)==want,(n,len(rows),want)
 table(f'table-s{n}','Bond lengths'if atoms==2 else'Bond angles',['atoms','distance'if atoms==2 else'angle'],rows,sorted({p for p,*_ in rawrows[n]}),'bulk-a-crystal'if n in[2,4]else'bulk-b-crystal',['Both printed side-by-side blocks retained; exact atom names and standard uncertainties preserved.','No intermolecular contacts or hydrogen geometry invented.'])
for n,cols,want in [(6,['x','y','z','Ueq'],32),(7,['x','y','z','Ueq'],36),(8,['U11','U22','U33','U23','U13','U12'],32),(9,['U11','U22','U33','U23','U13','U12'],36)]:
 rows=[]
 for p,il,line,toks in rawrows[n]:
  assert len(toks)==len(cols)+1,(n,p,line)
  cells=[]
  for col,raw in zip(cols,toks[1:]):
   assert re.fullmatch(r'-?\d+(?:\.\d+)?\(\d+\)',raw),(n,col,raw)
   cells.append({'column':col,**q(raw,'fractional_coordinate'if col in['x','y','z']else'angstrom^2',toks[0]+' '+col,'si',p,f'Table S{n} {toks[0]} {col}',1e-4 if col in['x','y','z'] else 1e-3)})
  rows.append({'row_label':toks[0],'source_line':il,'source_raw_line':line,'cells':cells})
 assert len(rows)==want,(n,len(rows),want)
 table(f'table-s{n}','Atomic coordinates and Ueq'if n<8 else'Anisotropic displacement parameters',cols,rows,sorted({p for p,*_ in rawrows[n]})+([18]if n==6 else[]),'bulk-a-crystal'if n in[6,8]else'bulk-b-crystal',['Coordinates printed ×10^4, converted to fractional units without wrapping; no occupancy/H coordinates supplied.'if n<8 else'Literal U11,U22,U33,U23,U13,U12 order. Exponent -2*pi^2[h^2*a*^2*U11+...+2*h*k*a*b*U12].','Displacement parameters printed Å²×10^3; converted by10^-3; uncertainties scaled identically.','Ueq=one-third trace of orthogonalized Uij.'if n<8 else'No independent physical ADP/model qualification is claimed.'])
write('source-tables.json',{'schema':'mattersyn-source-tables/1','source_id':SID,'author':'/root/backlog_eta','created_at':NOW,'tables':tables,'independent_audit_status':'pending','structure_model_qualification':False})

equations=[
 {'id':'equation-1','expression':'I(T) = I0 / [1 + A exp(-Ea/(kB T))]','meaning':'Thermally activated intensity fit; A prefactor unspecified; I0 emission at0K; I(T) atT.','scope':'author-activation-model','evidence':[ev('main',4,'Equation 1')]},
 {'id':'equation-2','expression':'FWHM = 2.36 sqrt(S) hbar*omega_phonon sqrt(coth(hbar*omega_phonon/(2*kB*T)))','meaning':'Huang–Rhys/phonon fit. Source typography separates cot h; original equation crop retained.','scope':'author-phonon-model','evidence':[ev('main',4,'Equation 2')]},
 {'id':'si-angle-four','expression':'sigma^2 = (1/4) sum_(i=1)^5 (alpha_i - 90deg)^2','meaning':'Four-coordinate selected-angle convention exactly as printed.','scope':'author-distortion-model','evidence':[ev('si',2,'Four coordination angle variance')]},
 {'id':'si-angle-five','expression':'sigma^2 = (1/7) sum_(i=1)^8 (alpha_i - 90deg)^2','meaning':'Five-coordinate selected-angle convention exactly as printed.','scope':'author-distortion-model','evidence':[ev('si',2,'Five coordination angle variance')]},
 {'id':'si-length-four','expression':'Delta_d = (1/4) sum_(n=1)^4 ((d_n-dbar)/dbar)^2','meaning':'Four-coordinate relative bond-length variance.','scope':'author-distortion-model','evidence':[ev('si',3,'Four coordination bond-length distortion')]},
 {'id':'si-length-five','expression':'Delta_d = (1/5) sum_(n=1)^5 ((d_n-dbar)/dbar)^2','meaning':'Five-coordinate relative bond-length variance.','scope':'author-distortion-model','evidence':[ev('si',3,'Five coordination bond-length distortion')]}]
references=[]
for role,pp,start,expected in [('main',[7,8],'■ REFERENCES',27),('si',[26],'References',3)]:
 text='\n'.join(docs[role]['pages'][p-1]['text'].split('ACS Applied Materials & Interfaces www.acsami.org Research Article')[0]for p in pp)
 text=text.split(start,1)[1]
 matches=list(re.finditer(r'(?m)^\s*\((\d+)\)\s',text))
 for i,m in enumerate(matches):
  raw=text[m.end():matches[i+1].start()if i+1<len(matches)else len(text)].strip()
  raw=re.sub(r'(?m)^S-26\s*$','',raw).strip()
  page=7 if role=='main'and int(m[1])==1 else 8 if role=='main'else 26
  references.append({'id':role+'-reference-'+m[1],'number':int(m[1]),'document_role':role,'raw_text':raw,'citation':' '.join(raw.split()),'full_text_read':False,'evidence':[ev(role,page,'References '+m[1])]})
 assert len(matches)==expected,(role,len(matches))
figures=[{'id':i,'title':t,'sample_scope':s,'scope_note':note,'evidence':[ev(role,p,i+' artwork'),ev(role,cp,i+' caption')],'asset_id':i}for role,p,cp,i,t,s,note in A.FIGURES]
schemes=[{'id':'scheme-1','title':'Stoichiometric crystal synthesis','sample_scope':'bulk-a-and-b','scope_note':'2:1 versus1:1 C12H28NCl:SbCl3 in DMF, slow evaporation at room temperature. Cation drawing is not a measured atomic structure.','evidence':[ev('main',2,'Scheme 1')],'asset_id':'scheme-1'}]
conflicts=[{'id':i,'title':t,'description':d,'resolution':'Retained unresolved or explicitly qualified; no source number overwritten.'}for i,t,d in A.CONFLICTS]
gaps=[{'id':i,'title':t,'description':d,'status':'retained'}for i,t,d in A.GAPS]
samples=[]
for i,name,physical,parents,units in [
 ('bulk-a','Bulk A single crystals','single crystal',[],['figure-1','figure-2','figure-s1','figure-s2','figure-s3','figure-s4','figure-s5','figure-s6','figure-s7','figure-s8','figure-s9','figure-s10','figure-s15']),
 ('bulk-b','Bulk B single crystals','single crystal',[],['figure-1','figure-2','figure-s1','figure-s2','figure-s3']),
 ('nc-a','A nanocrystal family','nanocrystal powder/dispersion contexts',[],['figure-4','figure-s11']),
 ('nc-a-dried-powder','Dried A nanocrystal powder','dry powder',['nc-a'],['figure-s12']),
 ('nc-a-colloid-vs-dry','Toluene dispersion/settling','colloid',['nc-a'],['figure-s13']),
 ('film-spincoat','Precursor spin-coated A film','supported film',[],['figure-s14']),
 ('beta-nc-film','A NC flexible composite beta test','flexible composite',['nc-a'],['figure-5']),
 ('dft-a','Relaxed A computational structure','calculation',['bulk-a'],['figure-3']),('dft-b','Relaxed B computational structure','calculation',['bulk-b'],['figure-3'])]:
 samples.append({'id':i,'name':name,'physical_context':physical,'composition_lineage':parents,'source_unit_ids':units,'physical_batch_identity':'not reported across techniques','identity_join_limit':'Composition/explicit figure association only; lineage is not a proved same physical specimen.'})
for idx,ratio in enumerate(['1/0','1/3','1/2','2/3','0/1'],1):samples.append({'id':'film-blend-'+str(idx),'name':'Figure5 a/b film '+str(idx),'blue_yellow_mass_parts':[int(v)for v in ratio.split('/')],'source_unit_ids':['figure-5'],'physical_context':'PS composite film','evidence':[ev('main',6,'Figure 5 a/b and4.4')],'identity_join_limit':'Photo/spectrum association explicit; no beta-test assignment inferred.'})

# Rectangles normalized against native full-page canvas; original-only crops, never synthetic figure redraws.
CROPS=[
('graphical-abstract','main',1,(.548,.316,.909,.457)),('scheme-1','main',2,(.094,.699,.482,.804)),
('figure-1','main',3,(.095,.078,.906,.466)),('figure-2','main',3,(.094,.477,.907,.883)),
('figure-3','main',4,(.094,.078,.907,.316)),('figure-4','main',5,(.094,.078,.907,.457)),('figure-5','main',6,(.094,.268,.484,.648)),
('equation-1','main',4,(.108,.653,.483,.700)),('equation-2','main',4,(.110,.813,.483,.862)),
('si-distortion-angles','si',2,(.110,.628,.901,.912)),('si-distortion-lengths','si',3,(.285,.118,.765,.235)),
('figure-s1','si',3,(.235,.482,.776,.820)),('figure-s1-caption','si',4,(.113,.097,.889,.164)),
('figure-s2','si',4,(.112,.198,.89,.556)),('figure-s3','si',4,(.230,.58,.77,.905)),('figure-s3-caption','si',5,(.113,.098,.889,.126)),
('figure-s4','si',5,(.114,.135,.891,.555)),('figure-s5','si',5,(.228,.567,.775,.89)),('figure-s5-caption','si',6,(.114,.097,.89,.159)),
('figure-s6','si',6,(.114,.18,.891,.599)),('figure-s7','si',7,(.114,.080,.891,.501)),('figure-s8','si',7,(.231,.519,.777,.846)),('figure-s8-caption','si',8,(.113,.097,.89,.16)),
('figure-s9','si',8,(.114,.176,.891,.594)),('figure-s10','si',9,(.114,.08,.891,.520)),('figure-s11','si',9,(.23,.55,.775,.874)),('figure-s11-caption','si',10,(.113,.097,.89,.159)),
('figure-s12','si',10,(.114,.178,.891,.59)),('figure-s13','si',10,(.125,.621,.889,.886)),('figure-s13-caption','si',11,(.113,.097,.89,.242)),
('figure-s14','si',11,(.114,.266,.89,.594)),('figure-s15','si',12,(.114,.096,.89,.426)),
('table-s1-a','si',13,(.112,.252,.89,.86)),('table-s1-b','si',14,(.112,.082,.89,.359)),
('table-s2-a','si',14,(.112,.61,.89,.879)),('table-s2-b','si',15,(.112,.090,.857,.475)),
('table-s3-a','si',15,(.112,.535,.862,.878)),('table-s3-b','si',16,(.112,.088,.89,.433)),
('table-s4-a','si',16,(.112,.494,.89,.866)),('table-s4-b','si',17,(.112,.088,.89,.505)),
('table-s5-a','si',17,(.112,.578,.89,.881)),('table-s5-b','si',18,(.112,.088,.89,.619)),
('table-s6-heading','si',18,(.112,.801,.901,.910)),('table-s6-a','si',19,(.112,.082,.801,.897)),('table-s6-b','si',20,(.112,.081,.802,.394)),
('table-s7-a','si',20,(.112,.452,.891,.900)),('table-s7-b','si',21,(.112,.082,.804,.89)),('table-s7-c','si',22,(.112,.082,.804,.199)),
('table-s8-a','si',23,(.112,.15,.901,.909)),('table-s8-b','si',24,(.112,.086,.871,.558)),
('table-s9-a','si',24,(.112,.620,.901,.909)),('table-s9-b','si',25,(.112,.087,.871,.889)),('table-s9-c','si',26,(.112,.088,.871,.36))]
(P/'reader-assets').mkdir(exist_ok=True)
assets=[];pdfs={role:pypdfium2.PdfDocument(d['source_path'])for role,d in docs.items()}
for aid,role,page,box in CROPS:
 pg=pdfs[role][page-1];im=pg.render(scale=4).to_pil();w,h=im.size;rect=[round(v*(w if k%2==0 else h))for k,v in enumerate(box)];crop=im.crop(rect);path=P/'reader-assets'/f'{aid}.png';crop.save(path)
 assets.append({'id':aid,'path':str(path),'sha256':sha(path),'kind':'original_source_crop','whole_source_page':False,'source_role':role,'pdf_page':page,'source_sha256':docs[role]['source_sha256'],'bbox_normalized':list(box),'bbox_pixels_at_render':rect,'render_scale':4,'pixel_dimensions':list(crop.size),'evidence':[ev(role,page,aid)],'manual_visual_review':'pending until final crop inspection','public_import_approval':False})
 pg.close()
for pdf in pdfs.values():pdf.close()
for t in tables:t['asset_ids']=[a['id']for a in assets if a['id'].startswith(t['id']+'-')]
for f in figures:f['asset_ids']=[a['id']for a in assets if a['id']in[f['id'],f['id']+'-caption']]
for e in equations:e['asset_ids']=[e['id']]if e['id'].startswith('equation-')else['si-distortion-angles'if e['id'].startswith('si-angle')else'si-distortion-lengths']
write('source-tables.json',{'schema':'mattersyn-source-tables/1','source_id':SID,'author':'/root/backlog_eta','created_at':NOW,'tables':tables,'independent_audit_status':'pending','structure_model_qualification':False})
write('original-assets-manifest.json',{'schema':'mattersyn-original-source-assets/1','source_id':SID,'author':'/root/backlog_eta','created_at':NOW,'assets':assets,'private_full_page_images':[{'document_role':role,'path':pg['render_path'],'sha256':sha(pg['render_path']),'whole_source_page':True,'public_import_approval':False}for role,d in docs.items()for pg in d['pages']],'independent_audit_status':'pending'})
# Legibility contact sheets supplement actual source-page review; final author records the views separately.
for start in range(0,len(assets),6):
 subset=assets[start:start+6];out=Image.new('RGB',(1800,660*((len(subset)+1)//2)),'#e4e8ec');draw=ImageDraw.Draw(out)
 for j,a in enumerate(subset):
  im=Image.open(a['path']);im.thumbnail((880,618));x=(j%2)*900;y=(j//2)*660;out.paste(im,(x+(900-im.width)//2,y+30));draw.text((x+10,y+5),a['id'],fill='black')
 out.save(P/'private'/f'crop-contact-{start//6+1:02}.png')

pairing={'schema':'mattersyn-source-pairing/1','source_id':SID,'paper_id':GROUP,'source_generation':1,'bundle_sha256':payload['bundle_sha256'],'author':'/root/backlog_eta','reviewed_at':NOW,'status':'content_verified_by_extraction_author_independent_audit_pending','title':A.TITLE,'authors':A.AUTHORS,'main_pages':8,'si_pages':26,'main_sha256':docs['main']['source_sha256'],'si_sha256':docs['si']['source_sha256'],'original_file_copies':payload['source_copies'],'checks':[
 {'criterion':'Main bibliographic identity','result':'Title/byline/DOI10.1021/acsami.1c18038,ACS Applied Materials & Interfaces2021,13,58908–58915.','evidence':[ev('main',1,'Title/byline/DOI')]},
 {'criterion':'SI content identity','result':'Same complete title and nine authors on S1; matching compound formulas, FiguresS1–S15 and TablesS1–S9 continue the main.','evidence':[ev('si',1,'Title/byline'),ev('main',7,'Associated Content'),ev('main',2,'S1–S9 reference')]},
 {'criterion':'Actual local source bytes','result':'All2copies hashed;2unique documents. No duplicate experiments inferred.'},
 {'criterion':'Additional local attachment check','result':'rg --files across both supplied source roots, filtered for1c18038/am1c18038, returned only main and SI PDF. No named ZIP/MP4 found; filename search cannot rule out unrelated unnamed attachments.'}],
 'pairing_gaps':[],'source_scope_gaps':['Main declares crystal ZIP and beta-scintillation MP4 not supplied in the local intake or found by exact identifier search.'],'independent_audit':False}
write('pairing-review.json',pairing)
write('relevance-screening.json',{'schema':'mattersyn-evidenced-synthesis-screening/1','source_id':SID,'group_id':GROUP,'source_generation':1,'bundle_sha256':payload['bundle_sha256'],'author':'/root/backlog_eta','screened_at':NOW,'decision':'retain_for_full_curation','status':'recipe_present_full_supplied_pdf_extraction_author_complete_independent_audit_pending','recipe_evidence':[ev('main',6,'4.2–4.4')],'reason':'Quantitative two-composition crystal growth, LARP nanocrystal growth and distinct composite/spincoating procedures; structural and optical evidence present.','no_recipe_claim':False,'independent_audit':False,'pairing_review_sha256':sha(P/'pairing-review.json'),'scope_limit':'Local main and SI PDF only; cited ZIP/MP4 unavailable.'})
coverage=[]
for role,d in docs.items():
 assert len(A.PAGE_NOTES[role])==d['page_count']
 for pg,note in zip(d['pages'],A.PAGE_NOTES[role]):
  coverage.append({'document_role':role,'pdf_page':pg['pdf_page'],'printed_page':pg['printed_page'],'source_sha256':d['source_sha256'],'text_read_in_full':True,'native_page_image_visually_inspected':True,'read_by':'/root/backlog_eta','scope_notes':note,'text_path':pg['text_path'],'text_sha256':sha(pg['text_path']),'render_path':pg['render_path'],'render_sha256':sha(pg['render_path']),'public_full_page_reuse_approved':False,'independent_audit':False})
write('page-coverage.json',{'schema':'mattersyn-page-coverage/1','source_id':SID,'created_at':NOW,'author':'/root/backlog_eta','pages':coverage,'supplied_pdf_pages_read':34,'supplied_pdf_pages_visually_inspected':34,'unread_supplied_pdf_pages':[],'unavailable_external_attachments':['crystal ZIP','scintillation MP4'],'independent_audit_status':'pending'})
counts={'facts':len(facts),'fact_quantities':sum(len(f['quantities'])for f in facts),'materials':len(materials),'stocks':len(stocks),'protocols':len(protocols),'operations':sum(len(p['operations'])for p in protocols),'tables':len(tables),'table_rows':sum(len(t['rows'])for t in tables),'table_cells':sum(len(r['cells'])for t in tables for r in t['rows']),'numeric_table_cells':sum(c['value']is not None for t in tables for r in t['rows']for c in r['cells']),'figures_including_graphical_abstract':len(figures),'schemes':len(schemes),'equations':len(equations),'references':len(references),'sample_contexts':len(samples),'original_crops':len(assets),'page_count':34}
src={'schema':'mattersyn-source-facts/1','source_id':SID,'doi':DOI,'title':A.TITLE,'authors':A.AUTHORS,'author':'/root/backlog_eta','created_at':NOW,'source_generation':1,'bundle_sha256':payload['bundle_sha256'],'source_documents':[{'role':r,'sha256':d['source_sha256'],'pages':d['page_count']}for r,d in docs.items()],'review_status':'author_extracted_independent_audit_pending','complete_scope':'All supplied8main+26SI PDF pages; absent citedZIP/MP4 remain gaps.','counts':counts,'facts':facts,'tables':tables,'materials':materials,'stocks':stocks,'protocols':protocols,'samples':samples,'figures':figures,'schemes':schemes,'equations':equations,'references':references,'conflicts':conflicts,'gaps':gaps,'training_admission':{'approved':False,'requested_tasks':[],'exact_recipe_structure_pair':False,'atomistic_model_qualified':False}}
write('source-facts.json',src)
units=[]
for key,kind in [('facts','fact'),('tables','table'),('materials','material'),('stocks','stock'),('protocols','protocol'),('samples','sample_context'),('figures','figure'),('schemes','scheme'),('equations','equation'),('references','reference')]:
 for i,item in enumerate(src[key]):units.append({'id':item['id'],'type':kind,'json_pointer':'/'+key+'/'+str(i),'evidence':item.get('evidence',[]),'source_fact_ids':item.get('source_fact_ids',[])})
write('source-inventory.json',{'schema':'mattersyn-source-inventory/1','source_id':SID,'author':'/root/backlog_eta','created_at':NOW,'counts':counts,'inventory_units':units,**{k:src[k]for k in ['materials','stocks','protocols','samples','figures','schemes','equations','references','conflicts','gaps']},'table_inventory':[{'id':t['id'],'rows':len(t['rows']),'cells':sum(len(r['cells'])for r in t['rows']),'scope':t['sample_scope'],'evidence':t['evidence'],'notes':t['notes']}for t in tables],'notes':['No raw plot digitization or independently supplied crystallographic ZIP is claimed.','Negative/non-emission/settling outcomes and all five film ratios are retained.','Page payloads and page renders remain private.'],'independent_audit_status':'pending'})
print(json.dumps(counts,ensure_ascii=False))
