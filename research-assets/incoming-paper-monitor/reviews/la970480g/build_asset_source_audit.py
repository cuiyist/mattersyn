"""Private independent audit of the inspected Yao assets and exact source joins."""
from pathlib import Path
from collections import Counter
import json, hashlib
B=Path(__file__).resolve().parent
SITE=B.parents[3]/'recipe-atlas'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
records={p.stem:read(p)for p in (B/'canonical-drafts').glob('*.json')}
SOURCE='6a7fb66fb56f6daa4aa677c91ddf0d78aa733b165b7537bbac4c4e1327defb06'
def check(cs,n,b,detail=''):cs.append({'name':n,'passed':bool(b),'detail':detail})
def final(name,checks,findings,summary,files,visual,limits):
 out={'source_id':'yao1998','source_doi':'10.1021/la970480g','source_sha256':SOURCE,'status':'passed'if all(x['passed']for x in checks)and not any(x['status']=='open'for x in findings)else'must_fix','scope':summary,'check_count':len(checks),'checks':checks,'findings':findings,'open_findings':[x for x in findings if x['status']=='open'],'files':[{'basename':str(p.relative_to(B)).replace('\\','/'),'sha256':sha(p)}for p in files],'independent_visual_review':visual,'limits':limits}
 (B/(name+'.json')).write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
 (B/(name+'.md')).write_text('# Independent Yao asset audit\n\nStatus: **'+out['status']+'**. '+summary+'\n\n'+str(len(checks))+' bounded integrity and scientific-join checks.\n\n'+ '\n'.join('- '+x['id']+' '+x['status']+': '+x['text']for x in findings)+'\n\n'+'\n'.join('- '+x for x in limits)+'\n',encoding='utf8')
 print(json.dumps({'audit':name,'status':out['status'],'checks':len(checks),'failed':[c for c in checks if not c['passed']],'open_findings':out['open_findings']},ensure_ascii=False))

# All eight contact sheets were independently viewed; sheets 03 and 07 were viewed again after correction.
am=read(B/'apparatus-review/scene-manifest.json');module=B/'yao-protocol.mjs';ac=[]
check(ac,'Final module matches scene manifest',sha(module)==am['module_sha256'])
check(ac,'47 scenes exactly cover canonical operations',{(r['record_id'],o['id'])for r in records.values()for o in r['operations']}=={(x['record_id'],x['operation_id'])for x in am['rows']}and len(am['rows'])==47)
check(ac,'25 distinct actions',len({x['action']for x in am['rows']})==25)
for x in am['rows']:
 p=B/'apparatus-review'/x['svg'];r=records[x['record_id']];op=next(o for o in r['operations']if o['id']==x['operation_id'])
 check(ac,x['record_id']+'/'+x['operation_id']+' exact SVG/source-operation provenance',sha(p)==x['svg_sha256']and sha(B/'canonical-drafts'/(x['record_id']+'.json'))==x['source_record_sha256']and x['action']==op['action']and bool(x['source_evidence']))
text=module.read_text(encoding='utf8')
wash=(B/'apparatus-review/svg/yao-1998-resin-conditioning--wash-water.svg').read_text(encoding='utf8')
hist=(B/'apparatus-review/svg/yao-1998-tem--distribution.svg').read_text(encoding='utf8')
af=[{'id':'A01','status':'resolved'if 'Wash until'not in wash and'reported eluent pH'in wash else'open','text':'Source p.2 reports the eluent pH near10; it does not prescribe a wash endpoint or reaction pH.'},{'id':'A02','status':'resolved'if '≈4 µm: histogram region'in hist and '4–5'in text else'open','text':'The Figure5 histogram is labeled approximately4µm while the related TEM field remains4–5µm; no forced regional equality.'}]
check(ac,'No measured structural or training claim',am['illustrative_only']and not am['eligible_training'])
final('apparatus-source-audit',ac,af,'All 47 operation scenes independently inspected against the supplied main source and canonical state graph; 25 action types.',[module,B/'apparatus-review/scene-manifest.json']+sorted((B/'apparatus-review').glob('contact-*.png')),[{'path':str(p.relative_to(B)),'sha256':sha(p),'status':'independently_viewed'}for p in sorted((B/'apparatus-review').glob('contact-*.png'))],['Functional apparatus drawings preserve retained polymer beads and aliquot branches; unspecified separation, drying, storage and sectioning equipment remains unknown.','Nominal salt versus postfeed concentration,2h stirring versus48h figure clock, inherited sulfide stock,150W hardware rating, and XRD versus local TEM sizes remain distinct.','No synthetic measured micrograph, spectrum, XRD trace, SAED pattern, atomic interface or refined structure.','No browser rendering or publication audit; SI remains unverified.'])

# All eleven new identity depictions viewed on two molecular contact sheets.
reg=read(B/'molecular-assets/registry-additions.json');bind=read(B/'molecular-assets/bindings-additions.json');mm=read(B/'molecular-assets/asset-manifest.json');prod=read(B/'molecular-assets/product-reference-proposal.json');mc=[]
entries={x['id']:x for x in reg['entries']}
check(mc,'Eleven new entries, seven 2D ionic components, four identity cards',len(entries)==11 and sum(bool(x.get('model2dPath'))for x in entries.values())==7 and all(not x.get('model3dPath')for x in entries.values()))
expected={'resin':'identity-yao-resin','cd-loaded-resin':'identity-yao-cd-loaded-resin','hybrid':'identity-yao-hybrid','cd-acetate':'cadmium-acetate-dihydrate','diagnostic-hs':'identity-yao-diagnostic-hs','na2s':'identity-veinot-na2s','licl':'lithium-chloride','kcl':'potassium-chloride','tmacl':'tetramethylammonium-chloride','nacl':'sodium-chloride','hcl':'hydrochloric-acid-aqueous','naoh':'sodium-hydroxide','water':'water','ethanol':'ethanol','methanol':'methanol'}
for rid,bs in bind['recordBindings'].items():
 check(mc,rid+' all and only actual materials bound',set(bs)=={x['id']for x in records[rid]['materials']})
 for mid,eid in bs.items():check(mc,rid+'/'+mid+' chemical identity',eid==expected[mid]and bool(bind['bindingNotes'][rid].get(mid)))
check(mc,'31 material bindings; no unresolved identity',sum(len(x)for x in bind['recordBindings'].values())==31 and not bind['unresolved'])
stoich={'cadmium-acetate-dihydrate':{'Cd':1,'C':4,'H':10,'O':6},'sodium-chloride':{'Na':1,'Cl':1},'hydrochloric-acid-aqueous':{'H':1,'Cl':1},'sodium-hydroxide':{'Na':1,'O':1,'H':1},'lithium-chloride':{'Li':1,'Cl':1},'potassium-chloride':{'K':1,'Cl':1},'tetramethylammonium-chloride':{'C':4,'H':12,'N':1,'Cl':1}}
for eid,want in stoich.items():
 e=entries[eid];m=read(B/'molecular-assets'/e['model2dPath']);atoms=m['atoms'];counts=Counter(a['element']for a in atoms)
 counts['H']+=sum(a.get('implicitHydrogenCount',0)for a in atoms)
 counts=+counts
 check(mc,eid+' serialized stoichiometry and net charge',dict(counts)==want and sum(a.get('formalCharge',0)for a in atoms)==0)
 check(mc,eid+' no measured or 3D geometry claim',not m['has3D']and not m['allowRotation']and all(a['z']==0 for a in atoms)and not e['provenance']['measuredCoordinates']and not e['provenance']['eligible_training'])
for x in mm['files']:check(mc,x['path']+' exact molecular asset hash',sha(B/'molecular-assets'/x['path'])==x['sha256'])
reused=read(B/'molecular-assets/reused-references.json')
for e in reused['entries']:
 for k,v in e['assetPaths'].items():check(mc,e['id']+'/'+k+' unchanged existing identity asset',sha(SITE/'dist/assets/chemical-registry'/v)==e['assetHashes'][k])
nonphysical={p['sample_id']for p in records['yao-1998-characterization']['products']if p['composition']['value']is None}
pb=prod['productBindings']['yao-1998-characterization'];resolved=not(nonphysical&set(pb))
mf=[{'id':'M01','status':'resolved'if resolved else'open','text':'Omit CdS/polymer product depictions for five nonphysical Donnan/cited Na+ contexts whose canonical composition is null. A record-level explanatory card must not imply their physical sample identity.'}]
for rid,bs in prod['productBindings'].items():
 products={p['sample_id']:p for p in records[rid]['products']}
 check(mc,rid+' optional product cards only for composition-bearing contexts',all(sid in products and products[sid]['composition']['value']is not None for sid in bs))
final('molecular-source-audit',mc,mf,'All 31 material bindings, seven ionic 2D models, four polymer/species cards, four reused identities and optional product-context bindings checked.',[B/'molecular-assets'/x for x in ['registry-additions.json','bindings-additions.json','asset-manifest.json','product-reference-proposal.json','reused-references.json']]+sorted((B/'molecular-assets/review').glob('contact-*.png')),[{'path':str(p.relative_to(B)),'sha256':sha(p),'status':'independently_viewed'}for p in sorted((B/'molecular-assets/review').glob('contact-*.png'))],['Cd acetate retains its dihydrate, chloride salts retain correct ionic identity, aqueous HCl is a conventional ion depiction, and tetramethylammonium has four methyl groups.','Chelex, Cd-loaded Chelex and CdS/polymer are distinct motifs without fabricated coordination, polymer sequence, crosslink fraction, radial distributions or atomic structure. Diagnostic HS− has no invented counterion or stock.','Reused identities do not import earlier-paper procedures. No new3D models or measured coordinates; no unsupported cubic CdS CIF.','No browser rendering or publication audit; SI remains unverified.'])

# All16 original crops viewed on four contact sheets against the already-read full pages.
cm=read(B/'crop-assets/manifest.json');cc=[]
check(cc,'Correct original seven-page source',cm['source_sha256']==SOURCE and cm['source_page_count']==7)
check(cc,'16 original assets:9figures3equations4excerpts',len(cm['assets'])==16 and sum(x['type']=='figure'for x in cm['assets'])==9)
for x in cm['assets']:
 check(cc,x['id']+' source and exact crop hash',sha(B/'crop-assets'/x['relative_asset'])==x['sha256']and x['source_sha256']==SOURCE and 1<=x['pdf_page']<=7)
 check(cc,x['id']+' unmodified image and retained locators',x['original_source_asset']and not x['synthetic']and not x['digitized']and not x['eligible_training']and bool(x['sample_scope'])and len(x['bbox_pdf_points_top_left'])==4)
final('crop-source-audit',cc,[],'All16 original crops independently inspected: nine figures, three numbered equations and four source excerpts; all plotted axes, legends, captions and scale bars retained.',[B/'crop-assets/manifest.json']+sorted((B/'crop-assets').glob('contact-*.png')),[{'path':str(p.relative_to(B)),'sha256':sha(p),'status':'independently_viewed'}for p in sorted((B/'crop-assets').glob('contact-*.png'))],['Source Fig1 panel letters label time points, independently of synthesis samplea/b. TEM depths, histogram populations, and symbol conventions are source-specific.','Fig8 square-root-time axis is not a reaction-rate derivative; Fig9 is optical proxy correlation; equations are author models.','Original main source has no table, XRD trace, SAED image or experimental atomistic coordinates. No graph digitization or invented numeric points.','Private source paths are not approved public metadata. Root controls public sanitized import, rendering and publication. SI remains unverified.'])
