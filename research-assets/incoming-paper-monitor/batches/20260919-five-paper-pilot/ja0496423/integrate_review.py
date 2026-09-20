"""Root-only exact-audit-gated import into the existing MatterSyn Site."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil,copy
B=Path(__file__).resolve().parent
S=Path('[local path redacted]')
V=B/'visuals';M=V/'molecules';P=V/'products';A=V/'apparatus';O=B/'inventory-proposal'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
audits={}
for name in ['reader','molecular','apparatus','product','promotion']:
    path=B/(name+'-source-audit.json');a=read(path)
    assert a['status'].startswith('passed'),(name,a['status'])
    assert not a.get('open_findings'),name
    for rel,h in a['bound_files'].items():
        p=Path(rel);p=p if p.is_absolute() else B/p
        assert sha(p)==h,('stale audit',name,str(p))
    audits[name]=sha(path)
for rel,h in read(M/'package-freeze.json')['files'].items():assert sha(M/rel)==h,rel
assert not (S/'data/paper-reviews/gu2004.json').exists(),'Already imported; inspect current integration rather than overwrite'
O.mkdir(exist_ok=True);shutil.copy2(S/'data/inventory-summary.json',O/'base-inventory-summary.json')
before_records={p.name:sha(p) for p in (S/'data/records').glob('*.json')};write(O/'base-record-hashes.json',before_records)
records={p.stem:read(p) for p in (B/'promotion-proposal/records').glob('*.json')};assert len(records)==10
for rid,r in records.items():write(S/'data/records'/(rid+'.json'),r)
scope='All two main and three matched SI pages text-read and visually inspected, with independent source, canonical, reader, molecular, apparatus, product and training-task audits. Source stages, physical sample identity limits, failed intermediate isolation, author models and the unresolved main/SI XRF discrepancy remain explicit.'
r=read(B/'public-review-proposal/gu2004.json')
r.update(coverage_status='supplied_main_and_matched_si_review_complete',source_review_promoted=True,independent_audit=scope,publication_status='Reviewed contribution for the existing MatterSyn atlas; deployment tracked separately.',training_note='One heterodimer route and one upstream Cd(acac)2 preparation supply one precursor-selection and two partial-protocol rows. Analytical records and author models are separate contexts. Missing conditions and the unresolved XRF discrepancy remain explicit. No measured atomic structure or exact structure–recipe pair is supplied.')
r['remaining_gaps']=[g for g in r['remaining_gaps'] if g!='Molecular, apparatus and crystal-context presentation/bindings are separate pending stages; this reader does not approve or claim those assets.']
for category in ['figures','tables','schemes','equations','source_notes']:
    for item in r[category]:item['reviewed']=True
for item in r['recipe_inventory']:
    item['status']='source_reviewed'
    item['gaps']=[x for x in item['gaps'] if x!='Presentation and source-to-reader binding review pending.']
for sec in r['reader_sections']:
    for item in sec['items']:
        if item.get('material_identity'):item['material_identity']['exact_molecular_asset_binding_approved']=True
write(S/'data/paper-reviews/gu2004.json',r)
for a in read(B/'reader-assets/crop-manifest.json')['assets']:
    p=Path(a['path']);assert sha(p)==a['sha256'];dest=S/'dist/assets/figures/gu2004'/p.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
dst=S/'dist/assets/chemical-registry';reg=read(dst/'registry.json')
norm=read(M/'oleylamine-metadata-normalization-proposal.json');old=next(e for e in reg['entries'] if e['id']=='oleylamine');new=norm['normalizedEntry'];assert {k:v for k,v in old.items() if k!='limitations'}=={k:v for k,v in new.items() if k!='limitations'}
assert sha(dst/'registry.json')==norm['baseRegistrySha256'];old['limitations']=new['limitations']
entries=[]
for root,file in [(M,'registry-additions.json'),(P,'product-registry-additions.json')]:
    for e in read(root/file)['entries']:
        entries.append(e)
        for key in ['svgPath','model2dPath','model3dPath']:
            if e.get(key):
                p=root/e[key];assert sha(p)==e['assetHashes'][key];dest=dst/e[key];assert not dest.exists();dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
assert len(entries)==14 and not {e['id'] for e in entries}&{e['id'] for e in reg['entries']};reg['entries']+=entries;write(dst/'registry.json',reg)
bindings=read(dst/'bindings.json');delta=read(M/'molecule-bindings-proposal.json');spec=read(P/'specimen-bindings-additions.json')
for rid,record in records.items():
    bb=copy.deepcopy(delta['recordBindings'].get(rid,{}));ss=spec['recordBindings'].get(rid,{})
    assert not set(bb)&set(ss);bb.update(ss);assert set(bb)=={m['id'] for m in record['materials']},rid
    notes=copy.deepcopy(delta['bindingNotes'].get(rid,{}));notes.update(spec['bindingNotes'].get(rid,{}))
    for note in notes.values():
        if isinstance(note,dict):note['binding_approved']=True;note['independent_scientific_audit']='Passed Gu molecular source audit; exact private inputs bound separately.'
    bindings['recordBindings'][rid]=bb;bindings.setdefault('bindingNotes',{})[rid]=notes;bindings['sourceRecordSha256'][rid]=sha(S/'data/records'/(rid+'.json'))
write(dst/'bindings.json',bindings)
products=read(dst/'product-bindings.json');products['recordBindings'].update(read(P/'product-reference-proposal.json')['recordBindings']);write(dst/'product-bindings.json',products)
assert not read(P/'crystal-reference-proposal.json')['entries'],'No unverified crystal coordinates to import'
shutil.copy2(A/'gu2004-protocol.mjs',S/'dist/gu2004-protocol.mjs')
p=S/'dist/protocol-visuals.mjs';t=p.read_text(encoding='utf8')
t="import {buildGu2004Scene,createGu2004Art} from './gu2004-protocol.mjs';\n"+t
replacements=[('const sourceArt=createSashchiuk2004Art','const sourceArt=createGu2004Art(o,r)||createSashchiuk2004Art'),('sashchiuk=buildSashchiuk2004Scene(o,r);','sashchiuk=buildSashchiuk2004Scene(o,r),gu=buildGu2004Scene(o,r);'),('sashchiuk?.caption||','gu?.caption||sashchiuk?.caption||'),('||schwartz||sashchiuk){','||schwartz||sashchiuk||gu){'),('||schwartz||sashchiuk)?','||schwartz||sashchiuk||gu)?')]
for old,new in replacements:assert old in t,old;t=t.replace(old,new)
p.write_text(t,encoding='utf8')
p=S/'dist/crystal-viewer.mjs';t=p.read_text(encoding='utf8');assert t.count("'schwartz2003','sashchiuk2004']")==3
t=t.replace("'schwartz2003','sashchiuk2004']","'schwartz2003','sashchiuk2004','gu2004']")
t=t.replace(" if(r.lineage?.source_group==='sashchiuk2004'&&entryId)"," if(r.lineage?.source_group==='gu2004'&&entryId)host.append(el('p','Original TEM and final-product SAED support the reported FePt and CdS domains. These illustrations show source-labeled composition, not atomic coordinates or an inferred interface. No verified local CdS/FePt CIF is available for this contribution. Intact shells of intermediates 2 and 3 were not successfully isolated.','guide-notice'));\n if(r.lineage?.source_group==='sashchiuk2004'&&entryId)")
p.write_text(t,encoding='utf8')
p=S/'dist/chemical-viewer.mjs';t=p.read_text(encoding='utf8')
old="export function chemicalEntry(data,recordId,materialId){return data.entries.get(data.bindings.recordBindings[recordId]?.[materialId]);}"
new="""export function chemicalEntry(data,recordId,materialId){
 const entry=data.entries.get(data.bindings.recordBindings[recordId]?.[materialId]);
 const note=data.bindings.bindingNotes?.[recordId]?.[materialId],overrides=note?.binding_approved?note.viewOverrides:null;
 if(!entry||!overrides)return entry;
 const scoped={...entry};for(const key of ['name','caption','limitations'])if(overrides[key]!==undefined)scoped[key]=overrides[key];
 scoped.sourceBindingCaption=overrides.caption;return scoped;
}"""
assert old in t;t=t.replace(old,new)
old="dialog.append(controls,el('p',depictionCaption));for(const note"
new="dialog.append(controls,el('p',depictionCaption));if(entry.sourceBindingCaption&&entry.sourceBindingCaption!==depictionCaption)dialog.append(el('p',entry.sourceBindingCaption,'guide-notice'));for(const note"
assert old in t;t=t.replace(old,new);p.write_text(t,encoding='utf8')
struct=set()
for sec in r['reader_sections']:
    if sec['id']!='structures':continue
    for item in sec['items']:
        for link in item['canonical_links']:
            pp=link['json_pointer'].strip('/').split('/')
            if pp[0]=='measurements':struct.add(records[link['record_id']]['measurements'][int(pp[1])]['property'])
p=S/'data/measurement-display.json';d=read(p);d['structural_properties']=list(dict.fromkeys(d['structural_properties']+sorted(struct)));write(p,d);write(B/'structural-property-additions.json',sorted(struct))
p=S/'scripts/build_atlas.py';t=p.read_text(encoding='utf8');anchor="NAMES['PbSe']='Lead selenide nanocrystals and assemblies'";assert anchor in t
t=t.replace(anchor,anchor+"\nNAMES['FePt/CdS']='Iron–platinum / cadmium sulfide heterodimers'\nNAMES['FePt']='Iron–platinum · heterodimer-component context'");p.write_text(t,encoding='utf8')
p=S/'scripts/build_dataset.py';t=p.read_text(encoding='utf8');assert "'dataset_version':'0.21.0'" in t;p.write_text(t.replace("'dataset_version':'0.21.0'","'dataset_version':'0.22.0'"),encoding='utf8')
for p in list((S/'scripts').glob('build_*.py'))+list((S/'dist').glob('*.mjs'))+list((S/'dist').glob('*.html')):
    t=p.read_text(encoding='utf8');n=t.replace('0.21.0-r1','0.22.0-r1')
    if n!=t:p.write_text(n,encoding='utf8')
assert all(sha(S/'data/records'/name)==h for name,h in before_records.items())
write(B/'integration-manifest.json',{'status':'integrated_pending_build_browser_publication','at':datetime.now(timezone.utc).isoformat(),'source_id':'gu2004','audits':audits,'records':{rid:sha(S/'data/records'/(rid+'.json')) for rid in records},'reader_sha256':sha(S/'data/paper-reviews/gu2004.json'),'private_reader_sha256':sha(B/'public-review-proposal/gu2004.json'),'apparatus_sha256':sha(S/'dist/gu2004-protocol.mjs'),'new_entries':14,'material_slots':28,'original_assets':12,'old_records_unchanged':len(before_records),'atomic_structures_imported':0})
print('Gu import complete: 10 records, 14 reference entries, 28 material slots and 12 original crops. Build/browser/publication pending.')
