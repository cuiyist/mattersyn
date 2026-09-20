from pathlib import Path
from collections import Counter, deque
from datetime import datetime, timezone
import json, hashlib, math, re
B=Path(__file__).resolve().parent;V=B/'visuals';N=B/'neutralized-references'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
C=[]
def check(name,ok,note=''):C.append({'check':name,'passed':bool(ok),'note':note})
E=read(V/'registry-additions.json')['entries'];by={e['id']:e for e in E}
expected={'mps-trimethoxy':'C6H16O3SSi','aps-trimethoxy':'C6H17NO3Si','mercaptopropionic-acid':'C3H6O2S','dimethylaminopyridine':'C7H10N2','dtnb':'C14H8N2O8S2','mes-buffer-acid':'C6H13NO4S','glycerol':'C3H8O3','tetramethylammonium-hydroxide':'C4H13NO','tetramethylammonium-hydroxide-pentahydrate':'C4H23NO6','dipotassium-hydrogen-phosphate':'HK2O4P','potassium-dihydrogen-phosphate':'H2KO4P','identity-gerion-phosphonate':None,'identity-gerion-pb':None,'identity-gerion-tbe':None,'identity-gerion-agarose':None,'identity-gerion-sephadex':None,'identity-gerion-carbon-grid':None,'identity-gerion-mica':None,'identity-gerion-zns-precursors':None,'identity-gerion-specimens':None,'identity-gerion-hplc-phase':None,'identity-gerion-siloxane-complexes':None,'identity-gerion-mps-primed':None,'identity-gerion-cdse-zns':'CdSe/ZnS','identity-gerion-siloxane':'CdSe/ZnS/siloxane','identity-gerion-mpa':'CdSe/ZnS'}
check('26 distinct added references',set(by)==set(expected))
model_graphs={}
for e in E:
    ident=e['id'];check(ident+'/identity-formula',e['formula']==expected[ident])
    check(ident+'/not-measured',e['provenance']['measuredCoordinates'] is False)
    check(ident+'/not-training',e['provenance']['eligible_training'] is False)
    check(ident+'/source-hash',e['provenance']['sourceSha256']==read(B/'source-identity.json')['source_sha256'])
    for field,h in e['assetHashes'].items():check(ident+'/'+field+'/hash',sha(V/e[field])==h)
    for field in ['model2dPath','model3dPath']:
        if not e.get(field):continue
        m=read(V/e[field]);A=m['atoms'];bonds=m['bonds'];graph={i:set() for i in range(len(A))}
        for b in bonds:graph[b['a']].add(b['b']);graph[b['b']].add(b['a'])
        got=Counter(a['element'] for a in A);got['H']+=sum(a.get('implicitHydrogenCount',0) for a in A)
        if not got['H']:del got['H']
        formula=Counter({a:int(n or 1) for a,n in re.findall(r'([A-Z][a-z]?)(\d*)',e['formula'])})
        check(ident+'/'+field+'/elemental-count',got==formula,str(dict(got)))
        check(ident+'/'+field+'/coordinates-finite',all(math.isfinite(a[k]) for a in A for k in ['x','y','z']))
        check(ident+'/'+field+'/bond-indices',all(0<=b['a']<len(A) and 0<=b['b']<len(A) and b['a']!=b['b'] for b in bonds))
        check(ident+'/'+field+'/not-training',m['eligible_training'] is False)
        for g in m['functionalGroups']:
            check(ident+'/'+field+'/'+g['label']+'/indices',all(0<=i<len(A) for i in g['atomIndices']) and all(0<=i<len(bonds) for i in g['bondIndices']))
            if g['label'] in ['Thiol','Disulfide bridge']:check(ident+'/'+field+'/'+g['label']+'/element',all(A[i]['element']=='S' for i in g['atomIndices']))
            if g['label']=='Primary amine':check(ident+'/'+field+'/amine-element',all(A[i]['element']=='N' for i in g['atomIndices']))
        model_graphs[(ident,field)]=(A,graph,bonds)
    if e['depictionKind']=='ionic_components':check(ident+'/no-ion-pair-3D',e['model3dPath'] is None)
    if not e.get('model2dPath'):check(ident+'/no-guessed-molecular-model',e['model3dPath'] is None)

def distance(graph,a,b):
    q=deque([(a,0)]);seen={a}
    while q:
        x,n=q.popleft()
        if x==b:return n
        for y in graph[x]-seen:seen.add(y);q.append((y,n+1))
    return None
for field in ['model2dPath','model3dPath']:
    A,G,bonds=model_graphs[('dtnb',field)]
    ring={b['a'] for b in bonds if b['order']==1.5}|{b['b'] for b in bonds if b['order']==1.5}
    RG={i:G[i]&ring for i in ring}
    carboxyl=[];nitro=[];sulfur=[]
    for i in ring:
        for j in G[i]-ring:
            el=A[j]['element'];nei=Counter(A[k]['element'] for k in G[j])
            if el=='C' and nei['O']==2:carboxyl.append(i)
            if el=='N' and nei['O']==2:nitro.append(i)
            if el=='S' and nei['S']==1:sulfur.append(i)
    check('dtnb/'+field+'/two-complete-substituted-rings',len(carboxyl)==len(nitro)==len(sulfur)==2)
    for k,c in enumerate(carboxyl,1):
        ns=[n for n in nitro if distance(RG,c,n) is not None];ss=[s for s in sulfur if distance(RG,c,s) is not None]
        check('dtnb/'+field+f'/ring{k}-nitro-ortho',len(ns)==1 and distance(RG,c,ns[0])==1)
        check('dtnb/'+field+f'/ring{k}-disulfide-meta',len(ss)==1 and distance(RG,c,ss[0])==2)
        check('dtnb/'+field+f'/ring{k}-nitro-disulfide-para',len(ns)==len(ss)==1 and distance(RG,ns[0],ss[0])==3)
for ident,end in [('mps-trimethoxy','S'),('aps-trimethoxy','N')]:
    A,G,_=model_graphs[(ident,'model2dPath')];si=next(i for i,a in enumerate(A) if a['element']=='Si');tail=next(i for i,a in enumerate(A) if a['element']==end)
    check(ident+'/propyl-link-length',distance(G,si,tail)==4)
    check(ident+'/three-methoxy-groups',sum(A[j]['element']=='O' and any(A[k]['element']=='C' for k in G[j]-{si}) for j in G[si])==3)
A,G,_=model_graphs[('dimethylaminopyridine','model2dPath')]
n=[i for i,a in enumerate(A) if a['element']=='N'];check('DMAP/para-aminopyridine',distance(G,*n)==4)
check('phosphonate/unresolved-formula',by['identity-gerion-phosphonate']['formula'] is None and not by['identity-gerion-phosphonate']['model2dPath'])

dmf=read(N/'registry-updates.json');before=dmf['before_entries'][0];after=dmf['entries'][0]
reg=B.parents[3]/'recipe-atlas/dist/assets/chemical-registry'
check('DMF/identity-unchanged',before['id']==after['id']=='dimethylformamide' and before['formula']==after['formula']=='C3H7NO')
check('DMF/provenance-unchanged',before['provenance']==after['provenance'])
check('DMF/neutral-caption','QDOH' not in after['caption'] and 'measured' in after['caption'])
dmf_asset_hashes={}
for f in dmf['files']:
    old=reg/f['path'];new=N/f['path'];check('DMF/'+f['path']+'/old-hash',sha(old)==f['before_sha256']);check('DMF/'+f['path']+'/new-hash',sha(new)==f['sha256'])
    check('DMF/'+f['path']+'/removed-stale-scope','QDOH clear colloidal suspension' not in new.read_text(encoding='utf-8'))
    if new.suffix=='.json':
        a=read(old);b=read(new)
        for k in ['atoms','bonds','functionalGroups']:check('DMF/'+f['path']+'/'+k+'-unchanged',a.get(k)==b.get(k))
    dmf_asset_hashes[f['path']]=sha(new)

semantics=[
    'All 26 added names/formulas/captions were independently compared with the supplied main article. All five updated molecular contact sheets were actually visually inspected; this is not an interactive browser test.',
    'A positional-isomer error was found in the first DTNB graph even though its elemental formula was correct. The corrected model now has nitro ortho to carboxyl and disulfide at ring position5 on BOTH rings. Graph-distance checks are independent of formula checks; fresh 2D and computed 3D models were tested.',
    'Free trimethoxy MPS and APS have three methoxy groups and three-carbon thiol/amine tethers. They are not the hydrolyzed silanol depiction in Figure1. MPA is the neutral free-acid reference, not a fixed bound/protonated state. DMAP has the required para relationship; MES and glycerol connectivity match their names.',
    'TMAH and its pentahydrate retain separate ionic/water components with no inferred 3D ion-pair or crystal geometry. Both phosphate salts have correct neutral formula totals but are depicted as ions; no PB mixing ratio is supplied.',
    'The phosphorus reagent remains an identity card without formula/model because Figure1 draws propyl–P(=O)(O−)–CH3 whereas the source name says methylphosphonate; no counterion or P–O–CH3 substitution is assumed.',
    'Buffer, gel, chromatography medium, carbon grid, mica and unresolved shell precursors remain mixtures/supports/identity cards. Hardware dimensions and analytical substrates do not become product composition. The text card describing Sephadex as cross-linked dextran is reference context, not a source-measured polymer structure.',
    'Architecture cards distinguish original TOPO coating, MPS-primed intermediate, siloxane and MPA surface states. Drawings are not measured atomistic or uniformly single-core reconstructions. Exact particle phase and shell homogeneity remain unverified.',
    'Shared DMF metadata no longer assigns a Veinot-specific QDOH role. Both model atoms, bonds and functional groups are unchanged; original reference provenance is retained. Actual DMF role/amount in Gerion belongs to record bindings.',
    'No ligand conformer, buffer speciation, ionic arrangement or illustrative shell is eligible for measured-structure training labels. Record/material binding audit is pending canonical completion and is not implied by this asset-only audit.'
]
failed=[c for c in C if not c['passed']]
report={'schema':'mattersyn-independent-molecular-source-audit-1','source_id':'gerion2001','status':'passed_added_references_and_DMF_metadata_binding_audit_pending' if not failed else 'failed','checked_utc':datetime.now(timezone.utc).isoformat(),'registry_sha256':sha(V/'registry-additions.json'),'source_inventory_sha256':sha(B/'source-audit.json'),'entry_count':len(E),'computed_molecules':7,'ionic_2d_references':4,'identity_cards':15,'semantic_review':semantics,'resolved_findings':[{'id':'DTNB-ring-positions','severity':'scientific_identity_error','status':'corrected_and_independently_rechecked','scope':'Both rings in 2D/3D graph and visible corrected drawing.'}],'check_count':len(C),'failure_count':len(failed),'checks':C,'failures':failed,'visual_coverage':[{'path':str(V/'review'/f'molecular-contact-{i}.png'),'sha256':sha(V/'review'/f'molecular-contact-{i}.png'),'actually_viewed':True} for i in range(1,6)],'dmf_update_sha256':sha(N/'registry-updates.json'),'dmf_asset_hashes':dmf_asset_hashes,'binding_audit_complete':False,'browser_verified':False,'site_mutated':False}
(B/'molecular-source-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(B/'molecular-source-audit.md').write_text('# Gerion2001 independent molecular audit\n\nStatus: '+report['status']+f'. {len(C)} checks, {len(failed)} failures.\n\n'+'\n\n'.join(semantics)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'checks':len(C),'failures':failed,'report_sha256':sha(B/'molecular-source-audit.json')},indent=2))
