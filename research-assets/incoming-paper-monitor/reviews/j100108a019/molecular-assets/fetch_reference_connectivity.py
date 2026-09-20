"""Fetch only bounded, named PubChem chemical references; never articles or Site files."""
import hashlib,json,time,urllib.request,urllib.parse,urllib.error
from pathlib import Path
OUT=Path(__file__).resolve().parent
(OUT/'raw').mkdir(exist_ok=True)
SPECS=[
 ('disilane','Disilane','disilane','molecule','Si2H6'),
 ('helium','Helium','helium','single_atom','He'),
 ('oxygen','Oxygen','oxygen','molecule','O2'),
 ('ethylene-glycol','Ethylene glycol','ethylene glycol','molecule','C2H6O2'),
 ('dichlorosilane','Dichlorosilane','dichlorosilane','molecule','SiH2Cl2'),
 ('sulfuric-acid','Sulfuric acid','sulfuric acid','molecule','H2SO4'),
 ('sodium-methoxide','Sodium methoxide','sodium methoxide','ionic_components','CH3NaO'),
 ('tetrabutylammonium-bromide','Tetrabutylammonium bromide','tetrabutylammonium bromide','ionic_components','C16H36BrN'),
 ('potassium-bromide','Potassium bromide','potassium bromide','ionic_components','KBr'),
 ('acetone','Acetone','acetone','molecule','C3H6O'),
 ('ethylene-dichloride','1,2-Dichloroethane','ethylene dichloride','molecule','C2H4Cl2')]
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def fetch(url,path):
 if path.exists():return path.read_bytes()
 for attempt in range(2):
  try:
   request=urllib.request.Request(url,headers={'User-Agent':'MatterSyn chemical reference curation/1.0'})
   with urllib.request.urlopen(request,timeout=25) as res:data=res.read()
   path.write_bytes(data);time.sleep(.3);return data
  except urllib.error.HTTPError as err:
   if err.code not in [429,500,502,503] or attempt==1:raise
   time.sleep(2)
  except (TimeoutError,urllib.error.URLError):
   if attempt==1:raise
   time.sleep(2)
rows=[]
for id,name,query,kind,formula in SPECS:
 row={'id':id,'name':name,'query':query,'depictionKind':kind,'expectedFormula':formula,'status':'pending'}
 try:
  lookup='https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/'+urllib.parse.quote(query,safe='')+'/cids/JSON'
  raw=fetch(lookup,OUT/'raw'/(id+'-lookup.json'));cids=json.loads(raw)['IdentifierList']['CID']
  row.update({'lookupUrl':lookup,'lookupSha256':sha(raw),'lookupCids':cids})
  if len(cids)!=1:raise ValueError('Name does not resolve uniquely: '+str(cids))
  cid=cids[0];row['pubchemCid']=cid;row['sourceUrl']='https://pubchem.ncbi.nlm.nih.gov/compound/'+str(cid)
  url='https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/'+str(cid)+'/property/MolecularFormula,IUPACName,CanonicalSMILES,IsomericSMILES,Charge/JSON'
  raw=fetch(url,OUT/'raw'/(id+'-properties.json'));row['properties']=json.loads(raw)['PropertyTable']['Properties'][0]
  row.update({'propertiesUrl':url,'propertiesSha256':sha(raw)})
  url='https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/'+str(cid)+'/SDF?record_type=2d'
  raw=fetch(url,OUT/'raw'/(id+'-pubchem-2d.sdf'))
  row.update({'sdfUrl':url,'sdfSha256':sha(raw),'status':'verified_api_record'})
 except Exception as err:row.update({'status':'unresolved','error':str(err)})
 rows.append(row);dump(OUT/'source-catalog.json',rows)
 print(id,row['status'],row.get('pubchemCid'),row.get('properties',{}),row.get('error',''),flush=True)
