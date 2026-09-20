"""Sommer phase-component display proposal. No source/canonical/Site mutation."""
from pathlib import Path
from copy import deepcopy
from datetime import datetime,timezone
import argparse,json,hashlib,html,textwrap,sys
O=Path(__file__).resolve().parent;P=O.parent;M=P.parents[4]
sys.dont_write_bytecode=True;sys.path.insert(0,str(M/'research-assets/corpus-20260917/runtime'));sys.path.insert(0,str(M/'research-assets/rdkit-runtime'))
import pymupdf
from PIL import Image,ImageDraw
ap=argparse.ArgumentParser();ap.add_argument('--canonical-manifest',type=Path,required=True);ap.add_argument('--canonical-audit',type=Path);args=ap.parse_args()
assert not(O/'package-freeze.json').exists(),'Preserve a frozen revision.'
for d in ['svg','previews']:(O/d).mkdir(parents=True,exist_ok=True)
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,x):(O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def jsha(x):return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def tx(x,y,s,size=22,anchor='start'):return f'<text x="{x}" y="{y}" fill="#244756" font-family="Arial,sans-serif" font-size="{size}" text-anchor="{anchor}">{html.escape(s)}</text>'
def wrap(s,x,y,width=90,size=20):return ''.join(tx(x,y+28*i,t,size)for i,t in enumerate(textwrap.wrap(s,width)))
sf=read(P/'source-facts.json');facts={f['id']:f for f in sf['facts']};manifest=read(args.canonical_manifest);records={};rpaths={};checks=[]
def ck(label,ok):checks.append({'check':label,'passed':bool(ok)});assert ok,label
for r in manifest['records']:
 p=Path(r['path']);ck('Record hash '+r['record_id'],sha(p)==r['sha256']);records[r['record_id']]=read(p);rpaths[r['record_id']]=p
sourceaudit=P/'source-independent-audit/independent-audit-v2.json';ck('Source audit passed',read(sourceaudit)['status'].startswith('passed'))
phases={'spinel':('ZnAl2O4','Zinc aluminate spinel phase identity'),'zno':('ZnO','Zinc oxide phase identity'),'alooh':('AlOOH','Boehmite phase identity')}
entries=[]
for key,(formula,title)in phases.items():
 eid='sommer2020-'+key+'-observed-phase-symbol';caption='Symbolic phase-component identity only. The selected source context determines whether this phase is a major product, impurity, transient phase or precursor. No whole-specimen composition or atomic coordinates are assigned.'
 body=tx(50,55,title,30)+tx(550,225,formula,68,'middle')+tx(550,330,'One phase component',29,'middle')+tx(550,390,'Not an atomic model or a whole-specimen formula',23,'middle')+wrap(caption,55,515,95,19)
 svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="700" viewBox="0 0 1100 700"><title>{html.escape(title)}</title><desc>{html.escape(caption)}</desc><rect x="1" y="1" width="1098" height="698" rx="20" fill="white" stroke="#b9ced8"/><path d="M45 92H1055" stroke="#bdcfd8"/>{body}</svg>'
 rel='svg/'+eid+'.svg';(O/rel).write_text(svg,encoding='utf8');doc=pymupdf.open(stream=svg.encode(),filetype='svg');doc[0].get_pixmap(alpha=False).save(str(O/'previews'/(eid+'.png')));doc.close()
 entries.append({'id':eid,'name':title,'formula':formula,'displayFormula':formula,'depictionKind':'symbolic_context','svgPath':rel,'model2dPath':None,'model3dPath':None,'functionalGroups':[],'caption':caption,'limitations':['No measured CIF, atomic coordinates, finite nanocrystal, surface geometry or exact training pair is supplied.','Phase evidence is source-context-specific; this reference is not a universal synthesis target or purity claim.'],'sourceUrls':['https://doi.org/10.1021/acs.cgd.9b01519'],'assetHashes':{'svgPath':sha(O/rel)},'binding_approved':False,'published':False,'eligible_training':False})
bykey={k:next(e for e in entries if e['formula']==v[0])for k,v in phases.items()}
SPECS={}
def spec(ids,phasekeys,fid,note):
 for sid in ids.split():SPECS[sid]={'phases':phasekeys.split(),'source_fact_id':'sommer2020-'+fid,'scope_note':note}
spec('m1','spinel alooh','mw-lowbase-outcome','M1 is reported as a ZnAl2O4/AlOOH mixture, with no ZnO detected. Each card identifies one observed phase; phase fractions remain in the separately linked source result.')
spec('m2','spinel alooh','mw-middle-outcome','M2 is called almost phase-pure or phase-pure in the paper, but a small AlOOH peak is present below reliable quantification. The trace is not converted into zero impurity.')
spec('m3','spinel zno alooh','mw-highbase-outcome','M3 contains spinel together with reported ZnO and AlOOH impurities. These are separate phases rather than one molecular formula.')
spec('m4 m5 m6 m7','spinel alooh','mw-time-outcome','The stated M4–M7 comparison contains ZnAl2O4 and AlOOH. The source gives different impurity fractions for individual specimens; M5 has no exact printed fraction and no common phase fraction is assigned here.')
spec('s1','spinel','scf-outcome','S1 is reported as phase-pure ZnAl2O4. This is the source phase assignment, not a new coordinate refinement or a batch-equivalence claim.')
spec('s2','spinel zno','scf-outcome','S2 retains a reported ZnO impurity alongside ZnAl2O4. The Methods/Results temperature conflict remains in the reader; the S1 outcome is not transferred to S2.')
spec('a1','spinel alooh','acs-outcome','The prose identifies A1 as almost phase-pure ZnAl2O4 with AlOOH below the quantification limit. Figure 11 has sample-marker/time and caption-color conflicts; this card follows the explicitly scoped prose without repairing the original plot.')
spec('a2','spinel','acs-outcome','The prose identifies A2 as phase-pure ZnAl2O4 after the long synthesis. Figure 11 has sample-marker/time and caption-color conflicts; this phase context follows the explicit prose and does not alter the original figure.')
spec('a3 a6','spinel zno','acs-outcome','The prose reports ZnO impurity alongside the target spinel for this sample. A3 and A6 retain their different source amounts and times; no common phase fraction is imposed.')
spec('a4','alooh','acs-outcome','The explicit prose reports only AlOOH for A4, with no ZnAl2O4 present. The intended spinel target is not shown as an observed A4 phase. Figure 11 marker/time and caption-color conflicts remain unresolved.')
spec('a5','spinel alooh','acs-outcome','The prose reports AlOOH impurity alongside ZnAl2O4 for A5. Figure 11 marker/time and caption-color conflicts remain unresolved; this card does not reassign the plotted points.')
spec('i1 i2','spinel alooh','insitu-lowbase','These are time-dependent in situ phase observations: ZnAl2O4 and AlOOH coexist initially, and AlOOH is consumed after heating is raised. The Figure 6 seconds/minutes conflict remains explicit; the cards are not one fixed endpoint mixture.')
spec('i3','spinel','insitu-lowbase','I3 is described as showing only ZnAl2O4 at the experiment time resolution. Capillary turbulence prevents quantitative refinement, so no numerical purity or complete atomic structure is implied.')
spec('i4 i5 i6','spinel','insitu-middle','I4–I6 are reported to give phase-pure ZnAl2O4 under their separate Table 1 conditions. The card does not collapse their temperatures or trajectories into one experiment.')
spec('i9 i10 i11','spinel zno','insitu-highbase','ZnAl2O4 and ZnO occur on heating in these separate in situ experiments. ZnO consumption varies with temperature; no exact completion time or universal final phase purity is inferred.')
spec('i12 i13','spinel','insitu-nobase','The high-temperature I12/I13 cases are reported as phase-pure ZnAl2O4 at low yield. Low yield is not relabeled low crystallinity, and this outcome is not extended to I14.')
spec('i15','spinel','insitu-oxide-outcome','I15 is reported to reach phase-pure ZnAl2O4 after extended reaction. The purchased ZnO feed and this observed outcome remain separate, with no exact completion time assigned.')
spec('i16','spinel zno','insitu-oxide-outcome','I16 gives partial conversion with residual ZnO. The retained ZnO phase is not a claim that the purchased feed keeps its original particle size or coordinates.')
spec('d2','zno','d2-pdf','D2 is a room-temperature precursor-solution PDF context with ZnO correlations and separate unresolved aluminum/nitrate contributions. This ZnO card is not synthesized spinel, an isolated pure product, or the cited heated ZnO experiment.')
allowed_records={
'mw-route':set('m1 m2 m3 m4 m5 m6 m7'.split()),'scf-route':{'s1','s2'},'acs-route':set('a1 a2 a3 a4 a5 a6'.split()),
'insitu-nitrate':set('i1 i2 i3 i4 i5 i6 i9 i10 i11 i12 i13'.split()),'insitu-oxide':{'i15','i16'},
'phase-size-results':set('m1 m2 m3 m4 m6 m7 s1 s2 a1 a2 a3 a5 a6 i15 i16'.split()),'precursor-structures':{'d2'},'pdf-procedure':{'d2'}}
contexts={};excluded=[];boundrows=[]
for rid,r in records.items():
 suffix=rid.removeprefix('sommer-2020-');rows=[]
 for i,prod in enumerate(r['products']):
  sid=prod['sample_id']
  if sid not in allowed_records.get(suffix,set()):
   reason='No explicit product-component dispatch for this combined, analytical, stock, source or model context; do not infer an outcome from the parent formula or a nominal target.'
   if sid in ['m8','m9']:reason='Table 1 conditions are present, but no resolved individual phase outcome is assigned from nominal target or neighboring samples.'
   if sid in ['i7','i8']:reason='The source gives conflicting early phase-history statements; no unique phase-component assignment is selected.'
   if sid=='i14':reason='The high-temperature I12/I13 outcome cannot be inherited by I14 at its different Table 1 condition.'
   excluded.append({'record_id':rid,'sample_id':sid,'canonical_product_pointer':f'/products/{i}','canonical_product':deepcopy(prod),'reason':reason});continue
  sp=SPECS[sid];fid=sp['source_fact_id'];f=facts[fid]
  claimant='sommer-2020-precursor-structures'if sid=='d2'else'sommer-2020-phase-size-results';cr=records[claimant];ci=next(j for j,m in enumerate(cr['measurements'])if m['id']==fid+'-claim');claim=cr['measurements'][ci]
  ck(rid+'/'+sid+' exact source claim',claim['value']['value']==f['claim'])
  for phase in sp['phases']:
   e=bykey[phase];formula=e['formula'];label=sid.upper()+' · '+formula+' phase component';caption=sp['scope_note']+' This symbolic card identifies only the selected reported phase component. It is not a measured whole-specimen composition, a new synthesis target, a size/shape model or an atomic structure.'
   phaseobj={'value':formula+' (reported phase component)','status':'reported','evidence':deepcopy(claim['value']['evidence']),'note':sp['scope_note']+' Whole-specimen canonical composition/phase fields are preserved separately, including unknown values.'}
   row={'sample_id':sid,'label':label,'registry_id':e['id'],'caption':caption,'phase':phaseobj,'canonical_product_pointer':f'/products/{i}','canonical_product_snapshot':deepcopy(prod),'composition_evidence':deepcopy(claim['value']['evidence']),'morphology':deepcopy(prod['morphology']),'source_fact_id':fid,'source_fact_pointer':'/facts/'+str(next(j for j,x in enumerate(sf['facts'])if x['id']==fid)),'canonical_claim_link':{'record_id':claimant,'json_pointer':f'/measurements/{ci}','measurement_id':claim['id'],'canonical_measurement':deepcopy(claim)},'projection_kind':'reported_phase_component_not_whole_specimen_composition','phase_component_formula':formula,'evidence_join_basis':'Exact printed specimen ID is explicitly named in the cited source claim; shared physical aliquots across techniques are not asserted.','training_eligible':False,'atomic_model':False,'binding_approved':False}
   rows.append(row);boundrows.append({'record_id':rid,'sample_id':sid,'registry_id':e['id'],'canonical_record_sha256':sha(rpaths[rid]),'product_pointer':row['canonical_product_pointer'],'product_sha256':jsha(prod),'source_fact_id':fid,'source_fact_sha256':jsha(f),'claim_record_sha256':sha(rpaths[claimant]),'canonical_claim_pointer':f'/measurements/{ci}','entry_sha256':jsha(e)})
 if rows:contexts[rid]=rows
ck('All exact mapped pairs seen',all(set(s['sample_id']for s in contexts['sommer-2020-'+rid])==ids for rid,ids in allowed_records.items()))
ck('A4 only AlOOH',all(row['phase_component_formula']=='AlOOH'for rows in contexts.values()for row in rows if row['sample_id']=='a4'))
ck('No ambiguous or nominal-only dispatch',not any(row['sample_id']in ['m8','m9','i7','i8','i14']for rows in contexts.values()for row in rows))
ck('No coordinate references',all(not e['model2dPath']and not e['model3dPath']for e in entries))
notice='These cards identify explicitly reported phase components for named source specimens or precursor contexts. A mixture may therefore have several component cards. They do not overwrite unknown canonical composition fields, convert intended ZnAl2O4 targets into observed products, or establish shared batches across reactors/techniques. Source conflicts, transient phases and unquantified traces remain qualified. No supplied-main atomic coordinate set, measured CIF, finite nanocrystal, DFT-ready structure or eligible training pair is claimed; the declared SI remains unlocated/unverified.'
save('registry-additions.json',{'schemaVersion':'1.0','source_id':'sommer2020','entries':entries,'binding_approved':False})
save('product-contexts-additions.json',{'recordContexts':contexts,'sourceNotices':{'sommer2020':notice}})
save('bindings.json',{'author':'/root/peng1998_reader_assets','status':'private_author_proposal_pending_distinct_review','canonical_manifest':{'path':str(args.canonical_manifest),'sha256':sha(args.canonical_manifest)},'canonical_audit':{'path':str(args.canonical_audit),'sha256':sha(args.canonical_audit)}if args.canonical_audit else None,'source_freeze_sha256':sha(P/'package-freeze.json'),'source_audit_sha256':sha(sourceaudit),'source_facts_sha256':sha(P/'source-facts.json'),'source_record_sha256':{str(p):sha(p)for p in rpaths.values()},'source_phase_specifications':SPECS,'exact_allowed_record_samples':{k:sorted(v)for k,v in allowed_records.items()},'bindings':boundrows,'excluded_contexts':excluded,'scientific_record_fields_unchanged':True,'no_coordinate_files_added':True,'independent_approval':False})
save('author-validation.json',{'status':'passed_author_checks_pending_distinct_audit','checks':checks,'check_count':len(checks),'counts':{'contexts':len(boundrows),'mapped_products':sum(len(set(x['sample_id']for x in rows))for rows in contexts.values()),'records':len(contexts),'excluded_products':len(excluded),'symbolic_cards':3,'atomic_models':0},'actual_targeted_source_reading':{'text_pages':[2,3,4,5,6,7,8],'visual_pages':[2,3,4,5,6,7,8]},'visual_card_inspection':'pending','canonical_audit_provided':bool(args.canonical_audit),'source_files_untouched':True})
canvas=Image.new('RGB',(1100,2100),'white')
for i,p in enumerate(sorted((O/'previews').glob('*.png'))):canvas.paste(Image.open(p),(0,i*700))
canvas.save(O/'contact.png')
print(json.dumps({'contexts':len(boundrows),'records':len(contexts),'excluded_products':len(excluded),'status':'private_author_proposal_not_frozen'}))
