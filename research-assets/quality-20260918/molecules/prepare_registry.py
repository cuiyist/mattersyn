"""Local, auditable molecular registry; only primary PubChem API data are fetched."""
import sys,json,hashlib,time,urllib.request,urllib.parse,urllib.error,copy,re,math,collections
from pathlib import Path
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent
SITE=OUT.parents[2]/'recipe-atlas'
RESEARCH=OUT.parents[1]
for p in ['raw','svg','models']: (OUT/p).mkdir(parents=True,exist_ok=True)

# Name matches are explicit, not formula-only identity inference.
SPECS=[
 ('oleic-acid','Oleic acid','Oleic acid','molecule',['oleic acid'],445639),
 ('oleylamine','Oleylamine','Oleylamine','molecule',['oleylamine','Technical oleylamine'],5356789),
 ('1-octadecene','1-Octadecene','1-Octadecene','molecule',['1-octadecene','Degassed 1-octadecene'],8217),
 ('1-butanol','1-Butanol','1-butanol','molecule',['1-butanol'],263),
 ('1-propanol','1-Propanol','1-propanol','molecule',['1-propanol'],None),
 ('ethanol','Ethanol','ethanol','molecule',['ethanol'],None),
 ('water','Water','water','molecule',['water','Milli-Q water'],None),
 ('ammonia','Ammonia','ammonia','molecule',['ammonia'],None),
 ('diethanolamine','Diethanolamine','diethanolamine','molecule',['diethanolamine'],None),
 ('toluene','Toluene','toluene','molecule',['toluene'],1140),
 ('hexane','n-Hexane','hexane','molecule',['hexane','n-hexane'],8058),
 ('chloroform','Chloroform','chloroform','molecule',['chloroform'],6212),
 ('hexadecane-1-2-diol','1,2-Hexadecanediol','1,2-hexadecanediol','molecule',['1,2-Hexadecanediol'],None),
 ('1-decene','1-Decene','1-decene','molecule',['1-decene'],None),
 ('decane','Decane','decane','molecule',['decane'],None),
 ('cyclohexane','Cyclohexane','cyclohexane','molecule',['cyclohexane'],None),
 ('dioctyl-ether','Dioctyl ether','dioctyl ether','molecule',['dioctyl ether'],None),
 ('ethyl-acetate','Ethyl acetate','ethyl acetate','molecule',['ethyl acetate'],None),
 ('benzoyl-bromide','Benzoyl bromide','benzoyl bromide','molecule',['benzoyl bromide'],None),
 ('bis-trimethylsilyl-sulfide','Bis(trimethylsilyl)sulfide','bis(trimethylsilyl)sulfide','molecule',['Bis(trimethylsilyl)sulfide'],None),
 ('tetradecylphosphonic-acid','Tetradecylphosphonic acid','tetradecylphosphonic acid','molecule',['Tetradecylphosphonic acid'],None),
 ('tris-diethylamino-phosphine','Tris(diethylamino)phosphine','tris(diethylamino)phosphine','molecule',['Tris(diethylamino)phosphine'],None),
 ('top','Trioctylphosphine','trioctylphosphine','molecule',['Trioctylphosphine','Trioctylphosphine (TOP)'],20851),
 ('topo','Trioctylphosphine oxide','trioctylphosphine oxide','molecule',['Trioctylphosphine oxide'],65577),
 ('hydrogen','Hydrogen','hydrogen','molecule',['hydrogen'],None),
 ('nitrogen','Nitrogen','nitrogen','molecule',['nitrogen'],None),
 ('toab','Tetraoctylammonium bromide','tetraoctylammonium bromide','ionic_components',['Tetraoctylammonium bromide (TOAB)'],None),
 ('topb','Tetraoctylphosphonium bromide','tetraoctylphosphonium bromide','ionic_components',['Tetraoctylphosphonium bromide (TOPB)'],None),
 ('zinc-nitrate-hexahydrate','Zinc nitrate hexahydrate','zinc nitrate hexahydrate','ionic_components',['zinc nitrate hexahydrate'],None),
 ('cesium-carbonate','Cesium carbonate','cesium carbonate','ionic_components',['Cesium carbonate'],None),
 ('lead-acetate-trihydrate','Lead(II) acetate trihydrate','lead acetate trihydrate','ionic_components',['Lead(II) acetate trihydrate'],None),
 ('indium-chloride','Indium(III) chloride','indium trichloride','formula',['Indium(III) chloride'],None),
 ('zinc-chloride','Zinc(II) chloride','zinc chloride','formula',['Zinc(II) chloride'],None),
 ('hydrochloric-acid','Hydrochloric acid','hydrochloric acid','formula',['hydrochloric acid'],None),
 ('sodium-carbonate','Sodium carbonate','sodium carbonate','ionic_components',['sodium carbonate'],None),
 ('iron-sulfate-heptahydrate','Iron(II) sulfate heptahydrate','iron(II) sulfate heptahydrate','ionic_components',['iron(II) sulfate heptahydrate'],None),
 ('iron-iii-sulfate-hydrate','Iron(III) sulfate hydrate','iron(III) sulfate hydrate','formula',['iron(III) sulfate hydrate'],None),
 ('iron-ii-carbonate','Iron(II) carbonate','iron(II) carbonate','formula',['prepared iron(II) carbonate source'],None),
 ('lead-oleate','Lead oleate stock','lead oleate','formula',['Lead oleate stock'],None),
 ('silver-behenate','Silver behenate','silver behenate','formula',['Silver behenate'],None),
 ('ir-mecp-cod','(Methylcyclopentadienyl)(1,5-cyclooctadiene)iridium','(methylcyclopentadienyl)(1,5-cyclooctadiene)iridium','formula',['(Methylcyclopentadienyl)(1,5-cyclooctadiene)iridium'],None),
 ('cobalt-acetate','Cobalt(II) acetate','cobalt(II) acetate','formula',['Cobalt(II) acetate','Co(ac)2'],None),
 ('iron-acetate','Iron(II) acetate','iron(II) acetate','formula',['Iron(II) acetate','Fe(ac)2'],None),
 ('argon','Argon','argon','single_atom',['argon'],23968),
 ('dimethylcadmium','Dimethylcadmium','dimethylcadmium','formula',['dimethylcadmium'],10479),
 ('oleyl-alcohol','Oleyl alcohol','oleyl alcohol','molecule',['Oleyl alcohol'],None),
 ('cadmium-oxide','Cadmium oxide','cadmium oxide','formula',['Cadmium oxide','Cd oxide'],None),
 ('zinc-oxide','Zinc oxide','zinc oxide','formula',['Zinc oxide','Zn oxide'],None),
 ('selenium-element','Selenium','selenium','formula',['selenium','Black selenium powder','Se elemental precursor'],None),
 ('sulfur-element','Sulfur','sulfur','formula',['S elemental precursor'],None),
]

def sha(b):return hashlib.sha256(b).hexdigest()
def save(path,x):path.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def fetch(url,path):
    if path.exists():return path.read_bytes()
    req=urllib.request.Request(url,headers={'User-Agent':'MatterSynResearch/1.0 (source-linked chemical depiction)'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req,timeout=35) as response:data=response.read()
            path.write_bytes(data);time.sleep(.25);return data
        except urllib.error.HTTPError as e:
            if e.code not in [429,500,502,503] or attempt==2:raise
            time.sleep(2+attempt*3)
        except (TimeoutError,urllib.error.URLError):
            if attempt==2:raise
            time.sleep(2)

def prepare():
    rows=[]
    for id,name,query,kind,aliases,cid in SPECS:
        row={'id':id,'name':name,'query':query,'depictionKind':kind,'aliases':aliases,'pubchemCid':cid,'fetchStatus':'pending'}
        try:
            if cid is None:
                u='https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/'+urllib.parse.quote(query,safe='')+'/cids/JSON'
                q=json.loads(fetch(u,OUT/'raw'/(id+'-lookup.json')))
                ids=q['IdentifierList']['CID'];row['lookupCids']=ids;row['lookupUrl']=u
                if len(ids)!=1:raise ValueError('Ambiguous name query returned '+str(ids))
                cid=ids[0]
            row['pubchemCid']=cid;row['source']='https://pubchem.ncbi.nlm.nih.gov/compound/'+str(cid)
            u='https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/'+str(cid)+'/property/MolecularFormula,IUPACName,IsomericSMILES/JSON'
            raw=fetch(u,OUT/'raw'/(id+'-properties.json'));row['propertiesUrl']=u;row['properties']=json.loads(raw)['PropertyTable']['Properties'][0];row['propertiesSha256']=sha(raw)
            if kind in ['molecule','ionic_components']:
                u='https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/'+str(cid)+'/SDF?record_type=2d'
                raw=fetch(u,OUT/'raw'/(id+'-pubchem-2d.sdf'));row['sdfUrl']=u;row['sdfSha256']=sha(raw)
            row['fetchStatus']='verified_api_record'
        except Exception as e:row['fetchStatus']='unresolved';row['error']=str(e)
        rows.append(row);save(OUT/'source-catalog.json',rows)
        print(id,row['fetchStatus'],row.get('pubchemCid'),row.get('properties',{}).get('MolecularFormula'),row.get('error',''),flush=True)
    return rows

if __name__=='__main__':prepare()
