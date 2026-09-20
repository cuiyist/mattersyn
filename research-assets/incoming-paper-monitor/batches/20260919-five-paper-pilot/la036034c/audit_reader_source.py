"""Independent Nagasaki reader audit. Reads author files; writes separate audit only."""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
from copy import deepcopy
import hashlib,json,re,sys
sys.dont_write_bytecode=True
B=Path(__file__).resolve().parent;O=B/'public-review-proposal'
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def esc(s):return s.replace('~','~0').replace('/','~1')
def resolve(o,p):
    for s in p.strip('/').split('/') if p else []:
        s=s.replace('~1','/').replace('~0','~');o=o[int(s)] if isinstance(o,list) else o[s]
    return o
def display(q):
    if q.get('value') is not None:return q['value']
    a,b=q.get('minimum'),q.get('maximum')
    if a is not None and b is not None:return f'{a:g}–{b:g}'
    if a is not None:return ('> ' if q.get('minimum_exclusive') else '≥ ')+f'{a:g}'
    if b is not None:return ('< ' if q.get('maximum_exclusive') else '≤ ')+f'{b:g}'
    return 'Not reported' if q.get('status')=='not_reported' else q.get('raw_text') or q.get('status','Unspecified')
R=read(O/'nagasaki2004.json');M=read(O/'reader-proposal-manifest.json');C=read(O/'source-item-coverage.json');CM=read(O/'canonical-measurement-coverage.json');BI=read(O/'reader-bindings-proposal.json');F=read(B/'source-facts.json');I=read(B/'source-inventory.json');CC=read(B/'canonical-source-coverage.json');CA=read(B/'canonical-records-audit.json');SA=read(B/'source-scientific-audit.json');MAN=read(B/'canonical-record-manifest.json')
RECS={p.stem:read(p) for p in (B/'canonical-drafts').glob('*.json')};ITEMS={x['id']:x for s in R['reader_sections'] for x in s['items']};CHECKS=[]
def ck(ok,label,detail=None):CHECKS.append({'passed':bool(ok),'check':label,**({'details':detail} if detail is not None else {})})
BOUND={**M['bound_inputs'],**M['files'],str(O/'reader-proposal-manifest.json'):sha(O/'reader-proposal-manifest.json'),str(O/'operation-prose-correction.json'):sha(O/'operation-prose-correction.json')}
for n in ['main-02.png','main-03.txt','main-04.txt','main-05.txt','si-01.png']:BOUND[str(B/n)]=sha(B/n)
for p,h in BOUND.items():ck(sha(p)==h,'Exact frozen input: '+p)
ck(M['reader_sha256']==sha(O/'nagasaki2004.json') and BI['reader_sha256']==M['reader_sha256'],'Final reader and binding manifest agree')
ck(M['status']=='author_validated_pending_independent_reader_audit' and CA['status']=='passed_with_preserved_source_ambiguities' and SA['status']=='passed_with_preserved_source_ambiguities','Separate source/canonical gates passed with preserved ambiguities; reader remained pending before this audit')
ck(len(ITEMS)==205==sum(len(s['items']) for s in R['reader_sections']),'Unique complete 205-item reader')
ck([s['title'] for s in R['reader_sections']]==['Precursors','Synthesis protocol','Final structures','Properties','Chemical intuition','Sources and limitations'],'Five academic sections and source appendix')
ck(Counter(r['record_type'] for r in RECS.values())=={'procedure':10,'literature_protocol':1,'protocol_variant':1,'observation':4},'One primary preparation, one incomplete variant and supporting contexts')
ck({r['lineage']['source_group'] for r in RECS.values()}=={'nagasaki2004'},'One source group across all records')
ck({x for a in R['recipe_inventory'] for x in a['record_ids']}==set(RECS),'All 16 source-scoped records linked')
for rid,r in RECS.items():
    ck(CM['draft_sha256'][rid]==sha(B/'canonical-drafts'/(rid+'.json')),'Exact audited canonical record: '+rid)
    ck(r['quality']['review_status']=='imported_unreviewed' and not r['quality']['requested_tasks'] and not r['structure_assets'],'No canonical promotion or added atomic structure: '+rid)
ck(R['review_scope']=='supplied_main_and_matched_si' and {d['role']:d['page_count'] for d in R['documents']}=={'main':5,'si':3},'Complete supplied main/SI coverage inherited from passed source audit')
for d in R['documents']:
    ck([p['page'] for p in d['pages']]==list(range(1,d['page_count']+1)) and all(p['text_read'] and p['visual_review'] for p in d['pages']),'Complete prior-reviewed pages: '+d['role'])
    ck(d['sha256']==next(s['source_sha256'] for s in I['documents'] if s['role']==d['role']),'Correct source document hash: '+d['role'])
ck(C['source_inventory_sha256']==sha(B/'source-inventory.json') and C['source_facts_sha256']==sha(B/'source-facts.json') and C['canonical_coverage_sha256']==sha(B/'canonical-source-coverage.json'),'Coverage inputs bound to actual source/canonical files')
ck(set(C['unit_to_reader_items'])=={u['id'] for u in I['source_units']} and len(C['unit_to_reader_items'])==32 and not C['unmapped_units'],'All 32 independently inventoried source units mapped')
for uid,ids in C['unit_to_reader_items'].items():ck(bool(ids) and all(i in ITEMS and uid in ITEMS[i]['source_audit_unit_ids'] for i in ids),'Source-unit mapping: '+uid)

EXPECTED={};EXPECTMAP={k:{} for k in ['measurement_to_reader_item','operation_to_reader_item','operation_parameter_to_reader_item','material_quantity_to_reader_item','stock_quantity_to_reader_item']};MATS={};SAMPLES={};STOCKS={}
def e(mapname,key,rid,p,q=False):
    EXPECTMAP[mapname][key]=(rid,p)
    if q:EXPECTED[(rid,p)]=resolve(RECS[rid],p)
for rid,r in RECS.items():
    for n,m in enumerate(r['measurements']):e('measurement_to_reader_item',rid+'::'+m['id'],rid,f'/measurements/{n}/value',True)
    for n,o in enumerate(r['operations']):
        e('operation_to_reader_item',rid+'::'+o['id'],rid,f'/operations/{n}')
        for k in o['parameters']:e('operation_parameter_to_reader_item',rid+'::'+o['id']+'::'+k,rid,f'/operations/{n}/parameters/'+esc(k),True)
    for n,m in enumerate(r['materials']):
        MATS[rid+'::'+m['id']]=(rid,f'/materials/{n}')
        for k in m['quantities']:e('material_quantity_to_reader_item',rid+'::'+m['id']+'::'+k,rid,f'/materials/{n}/quantities/'+esc(k),True)
    for n,s in enumerate(r['stocks']):
        STOCKS[rid+'::'+s['id']]=(rid,f'/stocks/{n}')
        for k in s['concentrations']:e('stock_quantity_to_reader_item',rid+'::'+s['id']+'::'+k,rid,f'/stocks/{n}/concentrations/'+esc(k),True)
        for j,comp in enumerate(s['components']):
            for k in comp.get('quantities',{}):e('stock_quantity_to_reader_item',rid+'::'+s['id']+'::'+str(j)+'::'+k,rid,f'/stocks/{n}/components/{j}/quantities/'+esc(k),True)
    for n,p in enumerate(r['products']):SAMPLES[rid+'::'+p['sample_id']]=(rid,f'/products/{n}')
ck(len(EXPECTED)==228 and len(MATS)==61 and len(STOCKS)==2 and len(SAMPLES)==28,'Exact quantitative/material/stock/specimen scope counts')
ALLF={};SEEN=[]
for iid,item in ITEMS.items():
    ck(bool(item['text']) and bool(item['title']) and bool(item['evidence']),'Evidenced human reader item: '+iid)
    ck(item['training_eligible'] is False and item['sample_scope']['physical_batch_id'] is None,'No invented reader batch or training approval: '+iid)
    for l in item['canonical_links']:
        try:resolve(RECS[l['record_id']],l['json_pointer']);ok=True
        except (KeyError,IndexError,ValueError,TypeError):ok=False
        ck(ok,'Valid canonical item pointer: '+iid+'/'+l['record_id']+l['json_pointer'])
    for evi in item['evidence']:ck(evi['document_role'] in ['main','si'] and (evi['pdf_page'] is None or 1<=evi['pdf_page']<=({'main':5,'si':3}[evi['document_role']])),'In-bounds source locator: '+iid+'/'+str(evi['locator']))
    for f in item['facts']:
        ck(f['id'] not in ALLF,'Unique fact ID: '+f['id']);ALLF[f['id']]=(iid,f);key=(f['canonical_record_id'],f['json_pointer']);SEEN.append(key);q=f['canonical_quantity']
        ck(key in EXPECTED and q==EXPECTED[key],'Exact unchanged canonical quantity object: '+f['id'])
        ck(f['value']==display(q) and f['status']==q['status'] and f['unit']==q.get('unit') and f['approximate']==q.get('approximate',False),'Exact displayed number, status, unit and approximation: '+f['id'])
        for field in ['qualifier','basis','note']:
            if q.get(field):ck(q[field] in f['qualifier'],'Visible source qualification: '+f['id']+'/'+field)
        ck(f['training_eligible'] is False,'No typed training admission: '+f['id'])
        if f.get('sample_id'):ck(resolve(RECS[f['canonical_record_id']],f['json_pointer'].rsplit('/',1)[0])['sample_id']==f['sample_id'],'Exact specimen associated with measurement: '+f['id'])
    for s in item.get('canonical_sample_contexts',[]):ck(s['sample']==resolve(RECS[s['record_id']],s['json_pointer']),'Complete original canonical sample context: '+iid+'/'+s['record_id']+s['json_pointer'])
    for m in item.get('canonical_material_slots',[]):
        x=resolve(RECS[m['record_id']],m['json_pointer']);ck(all(m[k]==x[k] for k in ['name','formula','role']) and m['material_id']==x['id'],'Source compound/formula/role identity: '+iid+'/'+m['record_id'])
    for s in item['sample_scope']['canonical_sample_links']:ck(resolve(RECS[s['record_id']],s['json_pointer'])['sample_id']==s['sample_id'],'Scoped measurement specimen pointer: '+iid+'/'+s['sample_id'])
ck(Counter(SEEN)==Counter(EXPECTED.keys()),'All 228 source/canonical quantities shown exactly once')
for name,m in EXPECTMAP.items():
    ck(set(CM[name])==set(m),'Complete exact map: '+name)
    for key,(rid,p) in m.items():
        iid=CM[name][key];ck(any(x['record_id']==rid and x['json_pointer']==p for x in ITEMS[iid]['canonical_links']),'Exact target pointer: '+name+'/'+key)
ck(set(CM['canonical_material_slots'])==set(MATS) and set(CM['canonical_sample_contexts'])==set(SAMPLES),'All material and specimen slots mapped')
for name,exp in [('canonical_material_slots',MATS),('canonical_sample_contexts',SAMPLES)]:
    for key,(rid,p) in exp.items():
        c=CM[name][key];ck(c['json_pointer']==p and c['reader_item_id'] in ITEMS,'Slot mapping: '+name+'/'+key)
for key,(rid,p) in EXPECTMAP['operation_to_reader_item'].items():
    op=resolve(RECS[rid],p);item=ITEMS[CM['operation_to_reader_item'][key]];ctx=item['operation_context']
    ck(all(ctx[k]==op[k] for k in ['inputs','outputs','environment','retained_fraction']) and ctx['condition_options']==RECS[rid]['condition_options'],'Exact operation state/atmosphere/retained-fraction context: '+key)
    ck(CM['operation_original_descriptions'][key]==op['description'],'Original canonical operation description preserved in map: '+key)
    ck('Source conditions: {' not in item['text'] and 'Framework relation: {' not in item['text'],'Bounded academic prose correction: '+key)

ck(set(C['fact_to_reader'])=={f['id'] for f in F['facts']},'All 49 original typed source facts represented')
for fc in CC['facts']:
    fid=fc['source_fact_id'];m=C['fact_to_reader'][fid];ck(m['original_source_fact']==fc['source_fact'] and m['source_unit_id']==fc['source_fact']['source_unit_id'],'Exact source fact retained: '+fid)
    ck([{k:v for k,v in b.items() if k not in ['reader_item_id','reader_fact_id']} for b in m['canonical_bindings']]==fc['canonical_bindings'],'All exact source-canonical bindings unchanged: '+fid)
    for b in m['canonical_bindings']:
        iid,f=ALLF[b['reader_fact_id']];ck((iid,f['canonical_record_id'],f['json_pointer'])==(b['reader_item_id'],b['record_id'],b['pointer']) and fid in f['source_fact_ids'],'Exact source fact reaches visible field: '+fid+'/'+b['reader_fact_id'])
ck(len(C['source_objects_to_reader'])==len(CC['source_objects'])==170,'All 170 source-object bindings retained')
def original(cat,key):
    if cat=='bibliography':return {'title':F['title'],'authors':F['authors'],**F['bibliography']}
    if cat=='structure_status':return F['structure_status']
    arr=I[cat] if cat=='administrative_and_footnote_units' else F[cat]
    return next(x for n,x in enumerate(arr) if x.get('id',str(n))==key)
for c,b in zip(C['source_objects_to_reader'],CC['source_objects']):
    ck({k:c[k] for k in ['category','source_object_id','record_id','pointer']}==b,'Original source-object destination: '+c['category']+'/'+c['source_object_id'])
    ck(c['source_object_payload']==original(c['category'],c['source_object_id']),'Full original source-object payload retained: '+c['category']+'/'+c['source_object_id'])
    ck(c['reader_item_id'] in ITEMS and any(x['record_id']==c['record_id'] and x['json_pointer']==c['pointer'] for x in ITEMS[c['reader_item_id']]['canonical_links']),'Source-object reader/canonical link: '+c['category']+'/'+c['source_object_id'])

FIGS={f['id']:f for f in R['figures']};FIS={f['id']:f for f in F['figures']}
ck(len(FIGS)==8 and set(FIGS)=={'nagasaki2004-'+a['id'] for a in I['assets']},'All six main and two SI original figures present')
for a in I['assets']:
    fig=FIGS['nagasaki2004-'+a['id']];orig=FIS[a['id']]
    ck(sha(a['path'])==a['sha256']==fig['public_asset_sha256'],'Original bytes unchanged: '+a['id'])
    ck(fig['document_role']==a['source_role'] and fig['page']==a['pdf_page'] and fig['asset_provenance']['source_sha256']==a['source_sha256'],'Original image source/page identity: '+a['id'])
    ck(set(x['sample_id'] for x in fig['canonical_sample_links'])==set(orig['sample_ids']),'Figure specimens match source inventory: '+a['id'])
    for s in fig['canonical_sample_links']:ck(s['sample_id'] in [p['sample_id'] for p in RECS[s['record_id']]['products']],'Record-scoped figure sample: '+a['id']+'/'+s['sample_id'])
    ck(any(z['id']==fig['id'] for i in ITEMS.values() for z in i['original_assets']),'Original image reachable from academic reader: '+a['id'])
    ck(not fig['reviewed'] and not fig['reader_render_verified'] and not fig['training_eligible'],'Figure binding/browser/training still separate: '+a['id'])
    ck({'Original axes and labels':orig['axes_and_labels']} in fig['notes'],'Complete original axes and labels retained: '+a['id'])
for item in ITEMS.values():
    for a in item['original_assets']:ck((a['public_asset'],a['public_asset_sha256'])==(FIGS[a['id']]['public_asset'],FIGS[a['id']]['public_asset_sha256']),'Exact reader original-image route: '+item['id']+'/'+a['id'])
ck(not any(R[k] for k in ['tables','schemes','equations']),'No invented tables, schemes or numbered equations')
ck(len(R['referenced_methods'])==25 and 'source-reference-note11' in ITEMS,'All 25 external references and substantive note 11 retained')
for x in F['references']:
    ck(ITEMS[x['id']]['text']==x['bibliography_as_printed_normalized_spacing'],'Exact source bibliography: '+x['id'])
for k in ['C1','C2','C3','C4']:ck('conflict-'+k in ITEMS and any(k in str(x) for x in R['evidence_conflicts']),'Unresolved source contradiction visible: '+k)
ck(not BI['publication_approved'] and not BI['molecular_or_apparatus_bindings_approved'] and not R['source_review_promoted'] and not R['training_eligible'],'Reader audit does not grant visual, publication or training approval')
ck(not re.search(r'[A-Z]:[\\/]|file://|miniforge',json.dumps(R,ensure_ascii=False)),'No private filesystem paths in proposed public reader')

# These records document the human scientific reading and image inspection carried
# out before this script; they are not conclusions inferred from passing code.
SCIENCE=[
('Polymer and initiator quantities','Main p2: PDP 1 mmol in THF 45 mL; EO 113.5 mmol then two days, AMA 60 mmol then 60 min ambient. The cooled syringe does not set reactor temperature.'),
('Purification lineage','Protonation precedes THF Soxhlet cleanup; unreported protonating reagent does not inherit assay HCl. Residual PEG leaves with extract.'),
('End-group branching','Acetic acid/water 10:1, 5 h, 35 °C; NaOH neutralization; biocytin hydrazide is added before dialysis, then 2 h and NaBH4. NaBH4 time/charge are missing.'),
('Polymer characterization','4200/15800, Mw/Mn 1.35 and almost quantitative acetal NMR remain polymer facts, not QD size or biotin-loading targets.'),
('Representative synthesis','8 mL is initial polymer solution; CdCl2 then Na2S at stated 2.5e-3 mol/L, 1 h ambient then water dialysis. Added volumes and concentration basis remain unknown.'),
('Amine concentration basis','3.08e-4 mol/L counts amine groups, including the PAMA homopolymer control in Figure1; it does not count whole chains.'),
('Biotin variant','Similar-manner framework remains partial without invented independently quantified charges or SI structural join.'),
('Controls and source counts','No-polymer/PEG precipitation and PAMA salt failure are stabilization outcomes, not no-CdS formation. Assay concentrations do not inflate synthesis counts.'),
('C1 and Figure2','Caption a/b/c concentrations1.16/3.08/4.62e-4 remain distinct from the contrary plotted intensity/prose trend. Absorption d is not assigned to a resolved member.'),
('Optical size','467nm absorption edge and Henglein-derived4.8nm are not an independently quantified TEM distribution. Abstract ca5nm remains separate.'),
('C2 and Figure5','Caption, axis and prose do not resolve which protein concentration varies; exact quantitative competitor targets remain excluded.'),
('C3 and Figure6','Main micromolar curve, approximately linear nanomolar inset and differing intensity scales remain visible; no regression or detection limit manufactured.'),
('C4 and protein identity','Text/captions specify TexasRed-streptavidin while graph abbreviates Tex-Avidin; no protein conformation or loading inferred.'),
('FRET legend','All11 printed labels11400,9116,6837,4558,2279,1593,912,228,159,91.2,22.8nmol/L read directly from originalFigure4. No extra synthesis records.'),
('Assay concentrations','396µmol/L nominalCdS is not particle number; FRET I0.15M is not substituted with7.5mM NaCl zeta electrolyte or0.3M salt challenge.'),
('Zeta region values','pH2–11,+15/−3mV and no coagulation retain assay/region scope without fitted pKa or isoelectric point.'),
('Generic TEM sample','SI1 describes dilute drop on formval-film-coatedCu grid air dried and200kV LEO922; SIfigure1 upper50nm/lower20nm bars remain scale bars, not measured mean sizes.'),
('Generic XRD sample','SI1 gives separate freeze-driedPEG/PAMA andPEG/PAMA–CdS onglass;40kV30mA,CuKα,15–60°2θ,0.02°steps. SIfigure2 has no separately labeled polymer-only trace.'),
('Phase and atomic boundaries','Authors assign hexagonalwurtzite; reader does not provide refinedcoordinates/CIF or link genericSI uniquely to biotin/CHO concentration member.'),
('Interpretation and alternatives','Coordination/segregation/FRET/BSA excluded-volume interpretations remain author-derived; post-CdS ligand installation is unperformed alternative.'),
('Figure completeness and readability','All eight original crops were visually inspected at returned native resolution: captions, scale bars, axes, concentrationlegend andFigure6inset are complete. Browser placement/readability not tested.'),
('Academic prose correction','All36 replacement operation paragraphs were read against original methods and canonical conditions; only operation text changed. Initial rawJSON/compact-token presentation finding is resolved without numeric changes.')]
COR=read(O/'operation-prose-correction.json')
reconstructed=deepcopy(R);previous_items={i['id']:i for s in reconstructed['reader_sections'] for i in s['items']}
ck(COR['new_reader_sha256']==sha(O/'nagasaki2004.json') and COR['changed_fields']==len(COR['changes'])==36,'Bounded operation-prose correction count and final hash')
for c in COR['changes']:
    ck(previous_items[c['item_id']]['text']==c['after'],'Final corrected operation text: '+c['item_id']);previous_items[c['item_id']]['text']=c['before']
reconstructed_hash=hashlib.sha256((json.dumps(reconstructed,ensure_ascii=False,indent=2)+'\n').replace('\n','\r\n').encode()).hexdigest()
ck(reconstructed_hash==COR['prior_reader_sha256'],'Reconstruction proves only36 operation texts changed from initial reader')
for p,h in BOUND.items():ck(sha(p)==h,'Frozen file unchanged during audit: '+p)
errors=[c for c in CHECKS if not c['passed']]
res={'schema':'mattersyn-private-reader-source-audit/1','source_id':'nagasaki2004','doi':'10.1021/la036034c','reviewer':'/root/norberg2004_extract','reader_author':'/root/peng1998_reader_assets','independent':True,'created_at':datetime.now(timezone.utc).isoformat(),'status':'passed' if not errors else 'failed','reader_sha256':sha(O/'nagasaki2004.json'),'manifest_sha256':sha(O/'reader-proposal-manifest.json'),'scope':'Independent full205-card human prose reading, all36 revised operation texts, source/canonical quantity and specimen mappings, all8 original figure/caption inspections, and private reader/source gates. Prior full-source and independent canonical audits remain separate; no rerun or endorsement of author checks substitutes for this review.','counts':R['counts'],'mechanical_checks':len(CHECKS),'scientific_scope_checks':[{'topic':t,'result':'passed','evidence_and_conclusion':v} for t,v in SCIENCE],'actual_reinspection':{'source_fact_ids':[f['id'] for f in F['facts']],'reader_items':[i for i in ITEMS],'source_text_pages_this_audit':{'main':[3,4,5]},'original_full_pages_visually_reopened_this_audit':{'main':[2],'si':[1]},'original_crops_visually_inspected_this_audit':[a['id'] for a in I['assets']],'earlier_full_source_audit_sha256':sha(B/'source-scientific-audit.json'),'earlier_canonical_audit_sha256':sha(B/'canonical-records-audit.json'),'limitation':'No new claim of rereading every original page this audit; full source had already been independently read and the current reader scope was checked with targeted original methods/figures.'},'resolved_findings':[{'id':'NR1','severity':'reader_presentation','issue':'Operation text showed raw inline JSON and compressed canonical tokens.','resolution':'Author replaced all36 operation paragraphs with academic source-specific prose; exact canonical descriptions remain in the private map, quantities and all other reader fields remain unchanged.','correction_report_sha256':sha(O/'operation-prose-correction.json'),'status':'verified_resolved'}],'open_findings':errors,'bound_files':BOUND,'check_results':CHECKS,'source_conflicts_preserved':['C1','C2','C3','C4'],'downstream_boundaries':{'reader_source_science_passed':not errors,'molecular_apparatus_product_binding_approval':False,'mounted_browser_or_layout_approval':False,'training_admission':False,'publication_approval':False,'site_modified':False,'source_canonical_author_files_modified':False}}
(B/'reader-source-audit.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
md=['# Nagasaki 2004: independent reader source audit','',f"Status: **{res['status']}**. Reader author `/root/peng1998_reader_assets`; independent reviewer `/root/norberg2004_extract`.",'',f"Frozen reader SHA256: `{res['reader_sha256']}`.",f"Frozen reader proposal manifest SHA256: `{res['manifest_sha256']}`.",'','The audit read all 205 reader cards and all 36 final operation paragraphs. It verified every one of the 228 displayed canonical quantity objects, all 36 operation links, 61 material slots, two stocks, 28 specimen/context slots, 49 source facts, 32 source units and 170 original-object bindings. These include context and reference entries; they are not counts of distinct experimental measurements or recipes.','',f"The independent checker recorded {len(CHECKS):,} mechanical checks and {len(SCIENCE)} human scientific-scope reviews. The author’s programmatic checks were not substituted for source inspection.",'','The reviewer reopened main methods page 2 and SI methods page 1 visually, read main pages 3–5 text, and visually inspected all eight original figure crops, including captions, axes, legends, both TEM scale bars and the Figure 6 inset. Earlier full-source and canonical scientific audits remain the basis for completed whole-document source coverage.','', '## Scientific review']
md += ['','\n'.join('- **'+t+':** '+v for t,v in SCIENCE),'','## Resolved finding','','NR1: the initial operation descriptions contained compressed source tokens and inline machine JSON. The author rewrote all 36 operation paragraphs. The exact source/canonical data remain unchanged, and the final prose was independently checked. No scientific quantity correction was necessary.','','## Boundaries','','C1–C4 remain unresolved source discrepancies. Missing reaction volumes, biotin branch quantities and SI specimen assignments remain explicit. This audit does not approve molecular, polymer, protein, apparatus or crystal-reference bindings, mounted browser layout, training admission or publication. No author, source, canonical, Site or shared-ledger file was edited.','',f"Open findings: {len(errors)}."]
(B/'reader-source-audit.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
print(json.dumps({'status':res['status'],'checks':len(CHECKS),'scientific_scope_checks':len(SCIENCE),'errors':errors,'bound_files':len(BOUND),'audit_sha256':sha(B/'reader-source-audit.json')},ensure_ascii=False))
raise SystemExit(bool(errors))
