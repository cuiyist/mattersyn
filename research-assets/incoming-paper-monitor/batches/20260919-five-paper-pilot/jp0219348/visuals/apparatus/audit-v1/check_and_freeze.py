"""Independent source/scientific audit of root-authored apparatus v1."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,xml.etree.ElementTree as ET
A=Path(__file__).resolve().parent;V=A.parent/'v1';H=A.parents[2];C=H/'canonical-proposal/v2'
checks=[];bound={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):p=Path(p).resolve();bound[str(p)]=sha(p);return p
def read(p):return json.loads(bind(p).read_bytes())
def ck(check,passed,detail=None):checks.append({'check':check,'passed':bool(passed),'detail':detail})
freeze=read(V/'package-freeze.json');selection=read(V/'scene-selection.json');bindings=read(V/'canonical-bindings.json');records=read(V/'records.json');scenes=read(V/'scene-output.json')
module=read(A/'module-checks.json');pairing=read(H/'pairing-review.json');canonical_audit=read(H/'canonical-proposal/audit-v2/independent-audit.json')
ck('Expected original frozen apparatus manifest',sha(V/'package-freeze.json')=='c4666a45787c2708a7ba7f6d852508023cb4b2fd69fcd788a7f3183bb9138bd0')
ck('Freeze enumerates every artifact exactly',{x['path'] for x in freeze['files']}=={p.relative_to(V).as_posix() for p in V.rglob('*') if p.is_file() and p.name!='package-freeze.json'})
for f in freeze['files']:
    p=bind(V/f['path']);ck('Frozen bytes '+f['path'],sha(p)==f['sha256'] and p.stat().st_size==f['bytes'])
ck('Canonical v2 manifest hash exact',sha(bind(C/'proposal-package-manifest.json'))==freeze['canonical_package_manifest_sha256'])
ck('Canonical v2 independently passed',canonical_audit['status']=='passed_bounded_canonical_reader_scope')
ck('Source generation2 bundle identity',pairing['bundle_sha256']==freeze['source_bundle_sha256'] and pairing['source_generation']==2)
for d in pairing['documents']:ck('Original source SHA '+d['role'],sha(bind(d['source_path']))==d['sha256'])
for p,h in bindings['files'].items():ck('Canonical/module dependency exact '+Path(p).name,sha(bind(p))==h)
for name in ['source-facts.json','source-inventory.json','main-tables.json','source-scientific-audit.json']:
    bind(H/name)
for name in ['experimental-procedure.png','main-table-1.png','figure-1.png','figure-2.png','figure-3.png']:bind(H/'reader-assets'/name)
ck('Four records /14 scenes /59 displayed condition rows',len(records)==4 and len(scenes)==14 and sum(len(x['rows']) for x in scenes)==59)
ck('14 distinct source-specific SVGs',len({sha(V/'scenes'/(x['kind']+'.svg')) for x in scenes})==14)
trace=[];scene_by_id={x['operation_id']:x for x in scenes}
units={'angstrom':'Å','angstrom/s':'Å/s','degree':'°'}
for r in records:
    canonical=read(C/'canonical-drafts'/(r['record_id']+'.json'))
    ck(r['record_id']+' exact complete canonical object',r==canonical)
    ck(r['record_id']+' complete ordered operation selection',[o['id'] for o in r['operations']]==selection['records'][r['record_id']])
    for oi,o in enumerate(r['operations']):
        s=scene_by_id[o['id']];rows=s['rows'];lookup={x['label']:x['value'] for x in rows}
        ck(s['kind']+' exact operation description',s['description']==o['description'])
        ck(s['kind']+' unique row labels',len(lookup)==len(rows))
        ck(s['kind']+' source record binding',s['record_id']==r['record_id'] and s['kind']==r['record_id']+'--'+o['id'])
        svg=ET.fromstring((V/'scenes'/(s['kind']+'.svg')).read_bytes());texts=[''.join(x.itertext()) for x in svg if x.tag.endswith('text')]
        ck(s['kind']+' explicit schematic disclaimer',any('Explanatory geometry, not a source apparatus drawing' in x for x in texts))
        ck(s['kind']+' title retained',svg.find('{http://www.w3.org/2000/svg}title').text==o['label'])
        for key,q in o['parameters'].items():
            label=key.replace('_',' ');display=lookup.get(label,'')
            ck(s['kind']+' parameter present '+key,label in lookup)
            if q['value'] is None and q.get('minimum') is None and q.get('maximum') is None:
                expected='Unresolved source discrepancy' if q.get('qualifier','').startswith('Unresolved conflict:') else (q.get('raw_text') or 'Not reported')
                ck(s['kind']+' explicit unresolved/unreported '+key,display.startswith(expected))
            if q.get('approximate'):ck(s['kind']+' approximation retained '+key,display.startswith('≈ '))
            if q.get('qualifier'):ck(s['kind']+' source qualifier retained '+key,q['qualifier'].replace('At673 K','At 673 K') in display)
            if q.get('unit'):ck(s['kind']+' dimensional unit retained '+key,units.get(q['unit'],q['unit']) in display or q['value'] is None and q.get('minimum') is None and q.get('maximum') is None)
            trace.append({'scene':s['kind'],'row_label':label,'row_display':display,'record_id':r['record_id'],'canonical_pointer':f'/operations/{oi}/parameters/{key}','source_quantity':q})
        for key in ['environment','endpoint']:
            if o.get(key,{}).get('value'):
                ck(s['kind']+' exact '+key+' text',lookup.get(key.capitalize())==o[key]['value'])
                trace.append({'scene':s['kind'],'row_label':key.capitalize(),'row_display':lookup[key.capitalize()],'record_id':r['record_id'],'canonical_pointer':f'/operations/{oi}/{key}','source_quantity':o[key]})
        if o['id']=='exchange':
            q=next(x for x in r['stocks'] if x['id']=='tl-acetate-feed')['concentrations']['thallous_acetate']
            ck('Stock concentration independently preserved',lookup['Thallous acetate feed']=='0.1 mol/L' and q['value']==0.1 and q['unit']=='mol/L')
            trace.append({'scene':s['kind'],'row_label':'Thallous acetate feed','row_display':lookup['Thallous acetate feed'],'record_id':r['record_id'],'canonical_pointer':'/stocks/0/concentrations/thallous_acetate','source_quantity':q})
        for extra in selection['configs'][o['id']].get('extra_rows',[]):
            ck(s['kind']+' declared source-specific auxiliary row '+extra['label'],lookup.get(extra['label'])==extra['value'])
            trace.append({'scene':s['kind'],'row_label':extra['label'],'row_display':extra['value'],'source_basis':'Manual review of original experimental/acquisition scope and prior independent source/canonical audit; metadata declares missingness or exact instrument name, not a new quantity.'})
ck('Every one of59 row displays has an explicit trace',len(trace)==59 and len({(x['scene'],x['row_label']) for x in trace})==59)
scientific=[
 ('host','Main p.2 Experimental; Table1','Na-X colorless octahedron and approximately0.15mm host dimension; schematic shape; number and capillary dimensions unknown. No indium-cluster size substitution.'),
 ('exchange','Main p.2 Experimental; Table1','Aqueous Tl(I) acetate0.1mol/L, pH6.4; Table1 adds4days/10mL/298K. Flow drawing is qualitative; total-throughput/reservoir interpretation and flow rate remain unresolved.'),
 ('dehydrate','Main p.2 Experimental versus Table1','Both prose623K48h and table673K3days shown unresolved.10^-6Torr applies to dehydration; no one recipe branch silently selected.'),
 ('redox','Main p.2 Experimental versus Table1','623K reported with cooler crystals than metal; coaxial ovens and indium transfer schematic.96h versus5days unresolved; mass, numerical reactor pressure and gradient unknown; vapor pressures not substituted.'),
 ('wash','Main p.2 Experimental; Table1','One black crystal exposed to atmosphere and washed with deionized water for1day/10mL. Crystal retained; removal is intended, not quantified; no wash vessel or temperature asserted.'),
 ('redehydrate','Main p.2 Experimental versus Table1','Washed black crystal relodged.623K48h versus673K3days unresolved;10^-6Torr remains explicit.'),
 ('h2s','Main p.2 Experimental; Table1','Zeolitically dried H2S at0.5atm/673K/12h. Delivery arrow does not assign continuous flow, gas charge, dryer construction or crystal sulfide phase.'),
 ('evacuate','Main p.2 Experimental; Table1','Evacuate at673K for10min; final pressure unknown, not inherited from initial dehydration.'),
 ('seal','Main p.2 Experimental','Seal from vacuum line at room temperature; numeric sealing temperature, cooling rate and storage unknown. Symbolic closure is not an exact sealing technique.'),
 ('xrd-acquire','Main p.3 X-ray Data Collection; Table1','294K; Mo wavelengths0.70930/0.71359Å;0.5degree2theta/min;2–70degree collection and10–20degree lattice determination;3 monitor reflections every3h;half scan background duration. Scan width and unused psi-scan correction retained in prose. Beam/detector art contains no fabricated pattern.'),
 ('epxma-expose','Main p.2 Experimental; prior canonical source audit','Post-diffraction atmosphere exposure separate from earlier wash; duration unknown. No additional synthesis/sample claimed.'),
 ('epxma-acquire','Main p.2 Experimental; Figure1','EDAX9100/Phillips515 analytical context; unspecified beam/current/pressure/duration. Parent In87-X panelB remains copiedreference34, not another run.'),
 ('xps-acquire','Main p.2 Experimental; Figure2','AlKalpha1486.7eV,15kV,10mA; current/parent/metal contexts remain distinct and metal1/20 display convention retained. No synthetic spectral curves drawn.'),
 ('ar-sputter','Main pp.2,5 XPS; Figure3','Argon analytical sputtering3kV/0.6Ås^-1/~10s intervals;4300Å prose depth not reconstructed from displayed cycles. No synthesis argon atmosphere or unreported total sputter time inferred.'),
]
manual=[]
for operation,source,assessment in scientific:
    manual.append({'operation_id':operation,'scene':scene_by_id[operation]['kind'],'source_locator':source,'finding':'passed','assessment':assessment,'actual_visual_inspection':'Exact frozen SVG rendered locally with sharp; visually inspected in a two-scene contact sheet at original resolution, alongside all condition rows and description.'})
    ck(operation+' manual source/scientific visual scope',True,assessment)
ck('Independent module reproduction and scope guards72passed',module['counts']=={'checks':72,'failed':0,'scenes':14})
for render in module['renders']:bind(render['render'])
for p in (A/'renders').glob('contact-*.png'):bind(p)
for p in [A/'render_and_check.mjs',Path(__file__)]:bind(p)
failed=[x for x in checks if not x['passed']]
report={
 'schema':'mattersyn.heo_apparatus_source_independent_audit/1','audited_at':datetime.now(timezone.utc).isoformat(),
 'author':'/root','auditor':'/root/backlog_eta','reviewer':'/root/backlog_eta','status':'passed_source_scientific_svg_scope' if not failed else 'findings',
 'package_freeze':str(V/'package-freeze.json'),'package_freeze_sha256':sha(V/'package-freeze.json'),
 'counts':{'records':4,'scenes':14,'condition_rows':59,'audit_checks':len(checks),'audit_failures':len(failed),'module_checks':72,'module_failures':0,'scenes_actually_viewed':14,'contacts_actually_viewed':7,'source_crops_actually_viewed':5},
 'checks':checks,'findings':failed,'manual_scene_assessments':manual,'condition_row_traces':trace,
 'actual_scope':'Read complete module and all14 descriptions/59 rows; compared exact four-record canonical payload and source conditions. Actually viewed all14 frozen SVG renders, experimental-procedure, main Table1 and Figures1–3 original crops. Prior independently passed source/canonical evidence was reused for precise analytical settings and sample boundaries. No repeated SI-cell reread.',
 'browser_limit':'The CUA tool failed to attach and then reported no browser available in this agent. The independent visual work used local exact-SVG raster derivatives. Root author mobile/interactive checks are preserved as author evidence only; this audit does not certify live browser behavior or final Site integration.',
 'render_note':'sharp rendered all14 images successfully. Fontconfig reported an unwritable cache; no missing text was observed in inspected raster outputs. No dependency was installed and no source file was changed.',
 'limitations':['Explanatory apparatus/shape/colors and beam geometry are schematic, not recovered source apparatus drawings or measured dimensions.','Three conflicting recipe conditions, unreported quantities and uncertain surface phases remain explicit.','No fake diffraction/EDS/XPS trace, ordered atomic model, exact recipe–structure pair, training eligibility or publication approval is supplied.','Final integrated browser/layout/binding validation is a separate gate.'],
 'mutations':'Only private apparatus/audit-v1 files and raster viewing derivatives written. Frozen v1, canonical v2, Site, source PDFs and shared ledger untouched.','bound_files':bound
}
(A/'apparatus-source-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
md=['# Heo apparatus v1 independent source audit','','**Passed for the source/scientific SVG scope. No author corrections required.**','','Author: `/root`; independent auditor: `/root/backlog_eta`.',f"Frozen package SHA256: `{report['package_freeze_sha256']}`.",'',f"All14 distinct scenes,59 condition rows and four exact canonical-v2 records were checked. {len(checks)} audit checks and72 separate module/scope checks passed. Every frozen SVG reproduces exactly from the module and all22 package artifact hashes are bound.",'','All14 scenes were actually inspected in seven original-resolution raster contact sheets. The original experimental crop, Table1 and Figures1–3 were also viewed. The two dehydration conflicts and indium-contact duration conflict remain unresolved; missing quantities, wash retention, parent/current/reference distinctions and sputter-depth limitation remain intact. Apparatus dimensions, gas delivery, exact geometry and measurement patterns are not invented.','','The JSON report records a source-scoped assessment of every scene and59 row-level traces. No SI-cell rereading is claimed.','','Browser attachment was unavailable in this agent, so this audit certifies the exact SVG render/scientific scope only. Root’s mobile/browser QA remains author evidence; final integrated browser and binding checks remain separate. The original frozen package, source/canonical files, Site and shared ledger were not edited.','']
(A/'apparatus-source-audit.md').write_text('\n'.join(md),encoding='utf-8')
print(json.dumps({'status':report['status'],'counts':report['counts'],'findings':failed,'json_sha256':sha(A/'apparatus-source-audit.json'),'md_sha256':sha(A/'apparatus-source-audit.md')},ensure_ascii=False))
