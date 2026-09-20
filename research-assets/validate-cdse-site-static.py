"""Read-only static check of material-centered Site; report outside checkout."""
import collections,hashlib,json,math,re,subprocess,urllib.parse
from html.parser import HTMLParser
from pathlib import Path
ROOT=Path(r'[local path redacted]')
OUT=Path(__file__).resolve().parent/'cdse-site-static-validation.json'
NODE=r'[local path redacted]'
PAGES=['index.html','murray-1993-method-1.html','murray-1993-method-2.html']
errors=[];warnings=[];counts=collections.Counter();detail={}
def fail(message):errors.append(message)
class Doc(HTMLParser):
    def __init__(self,file):
        super().__init__(convert_charrefs=True);self.file=file;self.ids=[];self.urls=[];self.compounds=[];self.stocks=[];self.idrefs=[];self.method=None
        self.feed(file.read_text(encoding='utf-8'))
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if a.get('id'):self.ids.append(a['id'])
        for attr in ['href','src']:
            if a.get(attr):self.urls.append((attr,a[attr]))
        if 'data-compound' in a:self.compounds.append(a['data-compound'])
        if 'data-stock' in a:self.stocks.append(a['data-stock'])
        for attr in ['aria-labelledby','aria-describedby','for']:
            if a.get(attr):self.idrefs.extend(a[attr].split())
        if tag=='body':self.method=a.get('data-method')
    handle_startendtag=handle_starttag
docs={name:Doc(ROOT/name) for name in PAGES}
def localurl(url,base):
    p=urllib.parse.urlsplit(url)
    if p.scheme or p.netloc:return None
    path=urllib.parse.unquote(p.path)
    target=(ROOT/path.lstrip('/') if path.startswith('/') else base.parent/path) if path else base
    return target.resolve(),urllib.parse.unquote(p.fragment)
for name,doc in docs.items():
    duplicates=[x for x,n in collections.Counter(doc.ids).items() if n>1]
    if duplicates:fail(f'{name}: duplicate IDs {duplicates}')
    counts['htmlPages']+=1;counts['uniqueHtmlIds']+=len(set(doc.ids))
    for ref in doc.idrefs:
        counts['ariaAndLabelIdReferences']+=1
        if ref not in doc.ids:fail(f'{name}: missing ARIA/label target #{ref}')
    for attr,url in doc.urls:
        r=localurl(url,ROOT/name)
        if r is None:counts['externalUrlsNotFetched']+=1;continue
        target,fragment=r;counts['localHtmlUrls']+=1
        if not target.exists():fail(f'{name}: missing local {attr} {url}');continue
        if fragment and target.suffix.lower()=='.html':
            counts['htmlFragmentTargets']+=1
            targetdoc=docs.get(target.name) if target.parent==ROOT else None
            targetdoc=targetdoc or Doc(target)
            if fragment not in targetdoc.ids:fail(f'{name}: missing fragment {url}')
    detail[name]={'ids':len(doc.ids),'localOrExternalHrefSrc':len(doc.urls),'dataCompoundCount':len(doc.compounds),'dataStockCount':len(doc.stocks),'method':doc.method}

# JSON decode and accidental local-path disclosure checks.
jsonfiles=list((ROOT/'assets').rglob('*.json'));data={}
localpath=re.compile(r'(?<![A-Za-z])[A-Za-z]:[\\/]|file://|/(?:Users|home|mnt|tmp|workspace)/')
def walk(value,path='$'):
    if isinstance(value,str):yield path,value
    elif isinstance(value,list):
        for i,v in enumerate(value):yield from walk(v,f'{path}[{i}]')
    elif isinstance(value,dict):
        for k,v in value.items():yield from walk(v,f'{path}.{k}')
for f in jsonfiles:
    try:data[f]=json.loads(f.read_text(encoding='utf-8-sig'));counts['jsonFilesParsed']+=1
    except Exception as ex:fail(f'{f.relative_to(ROOT)}: invalid JSON {ex}');continue
    for key,value in walk(data[f]):
        if localpath.search(value):fail(f'{f.relative_to(ROOT)}: local filesystem path at {key}: {value[:180]}')
for name in PAGES+['material-app.mjs','material-data.mjs']:
    for i,line in enumerate((ROOT/name).read_text(encoding='utf-8').splitlines(),1):
        if localpath.search(line):fail(f'{name}:{i}: possible local filesystem path')

molecules=data[ROOT/'assets/cdse-molecular-structures.json'];ids=[m['id'] for m in molecules];idset=set(ids)
if len(idset)!=len(ids):fail('Duplicate molecule IDs')
for m in molecules:
    ident=m['id'];atoms=m.get('atoms',[]);bonds=m.get('bonds',[])
    counts['molecules']+=1;counts['molecularAtoms']+=len(atoms);counts['molecularBonds']+=len(bonds)
    if not atoms and m.get('representation')!='formula-only':fail(f'{ident}: empty atom list without formula-only representation')
    for i,a in enumerate(atoms):
        if a.get('index',i)!=i:fail(f'{ident}: mismatched atom index {i}')
        if not (a.get('element') or a.get('elem')):fail(f'{ident}: missing element at {i}')
        if not all(isinstance(a.get(d),(int,float)) and math.isfinite(a[d]) for d in ['x','y','z']):fail(f'{ident}: nonfinite coordinate at {i}')
    for j,b in enumerate(bonds):
        if not all(isinstance(b.get(k),int) and 0<=b[k]<len(atoms) for k in ['a','b']):fail(f'{ident}: invalid bond endpoints {j}')
        elif b['a']==b['b']:fail(f'{ident}: self bond {j}')
        if b.get('order') not in [1,2,3,4,1.5]:fail(f'{ident}: invalid bond order {j}')
    for g in m.get('functionalGroups',[]):
        counts['functionalGroups']+=1
        if not all(isinstance(i,int) and 0<=i<len(atoms) for i in g.get('atomIndices',[])):fail(f'{ident}: invalid group atom indices')
        if not all(isinstance(i,int) and 0<=i<len(bonds) for i in g.get('bondIndices',[])):fail(f'{ident}: invalid group bond indices')
        else:
            selected=set(g.get('atomIndices',[]))
            for i in g.get('bondIndices',[]):
                if not {bonds[i]['a'],bonds[i]['b']}<=selected:fail(f'{ident}: highlighted bond {i} has endpoint outside group')
for name,doc in docs.items():
    for ident in doc.compounds:
        counts['htmlCompoundReferences']+=1
        if ident not in idset:fail(f'{name}: unresolved data-compound {ident}')

# Import data-only module in Node, not the DOM-driven app module.
uri=(ROOT/'material-data.mjs').as_uri()
code=f"import * as d from {json.dumps(uri)}; console.log(JSON.stringify({{stocks:d.stocks,inventory:d.inventory,auxiliaryInventory:d.auxiliaryInventory}}));"
loaded=subprocess.run([NODE,'--input-type=module','-e',code],capture_output=True,text=True,encoding='utf-8')
if loaded.returncode:fail('material-data.mjs import failed: '+loaded.stderr)
else:
    exported=json.loads(loaded.stdout)
    for method,stocks in exported['stocks'].items():
        for stock in stocks:
            counts['stocks']+=1
            for key in ['solute','secondSolute','solvent']:
                if key in stock:
                    counts['stockComponentReferences']+=1
                    if stock[key] not in idset:fail(f'{method}/{stock["id"]}: unresolved {key} {stock[key]}')
    for name,doc in docs.items():
        for value in doc.stocks:
            if not doc.method or not value.isdecimal() or int(value)>=len(exported['stocks'].get(doc.method,[])):fail(f'{name}: invalid stock button {value}')
    for item in sum(exported['inventory'].values(),[])+exported['auxiliaryInventory']:
        counts['inventoryReferences']+=1
        if item['id'] not in idset:fail('Unresolved inventory ID '+item['id'])

# All local top-level module syntax and dependencies; app literal asset paths.
for module in ROOT.glob('*.mjs'):
    p=subprocess.run([NODE,'--check',str(module)],capture_output=True,text=True,encoding='utf-8')
    counts['javascriptModulesSyntaxChecked']+=1
    if p.returncode:fail(f'{module.name}: syntax error {p.stderr}')
    source=module.read_text(encoding='utf-8')
    for url in re.findall(r'(?:from\s*|import\s*)[\'\"](\.[^\'\"]+)[\'\"]',source):
        counts['moduleImports']+=1
        if not (module.parent/url).is_file():fail(f'{module.name}: missing import {url}')
    if module.name in ['material-app.mjs','material-data.mjs']:
        for url in re.findall(r'[\'\"](assets/[^\'\"]+)[\'\"]',source):
            counts['literalAppAssetReferences']+=1
            if not (ROOT/url).is_file():fail(f'{module.name}: missing asset {url}')

manifestfile=ROOT/'assets/cdse-structures/download-manifest.json';manifest=data[manifestfile];hashes=[]
for download in manifest['downloads']:
    file=manifestfile.parent/download['file'];actual=hashlib.sha256(file.read_bytes()).hexdigest()
    counts['crystalDownloadHashesChecked']+=1
    if actual!=download['sha256']:fail(f'{download["file"]}: SHA256 mismatch')
    if file.stat().st_size!=download['bytes']:fail(f'{download["file"]}: size mismatch')
    hashes.append({'file':download['file'],'sha256':actual,'matchesManifest':actual==download['sha256']})

# Unit-cell AtomSpec indexing is separate from molecule JSON schema.
cell=data[ROOT/'assets/cdse-structures/cdse-unit-cell-viewer.json']
for key in ['atoms','atomsWithPeriodicNeighborContext']:
    values=cell[key]
    for i,a in enumerate(values):
        if a['index']!=i or len(a['bonds'])!=len(a['bondOrder']):fail(f'unit cell {key}: atom index/bond-order mismatch {i}')
        if not all(0<=j<len(values) for j in a['bonds']):fail(f'unit cell {key}: invalid neighbor index {i}')
        for j in a['bonds']:
            if i not in values[j]['bonds']:fail(f'unit cell {key}: asymmetric bond {i}-{j}')
    counts['unitCellAtomSpecsChecked']+=len(values)
if len(cell['unitCellEdges'])!=12:fail('Unit cell does not contain 12 edges')

report={'scope':'Read-only static validation, no browser or network','status':'passed' if not errors else 'failed','counts':dict(counts),'pages':detail,'downloadHashes':hashes,'errors':errors,'warnings':warnings,
 'limits':['Does not execute DOM interactions or revalidate scientific claims.','External HTTP links were classified but not fetched.','Faithful original CIF retains its original COD repository URL comment; JSON/HTML/module assets were checked for accidental local filesystem paths.']}
OUT.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
raise SystemExit(bool(errors))
