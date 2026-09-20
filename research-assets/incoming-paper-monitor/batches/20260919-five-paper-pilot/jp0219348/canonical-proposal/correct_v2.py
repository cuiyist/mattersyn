"""Preserved v2 corrections after independent v1 review. Never rewrites v1."""
from pathlib import Path
import copy,json,hashlib,shutil,sys,re,datetime
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;H=P.parent;A=P/'v1';B=P/'v2';S=H.parents[4]/'recipe-atlas'
sys.path.insert(0,str(S/'scripts'))
from dataset_lib import validate_record,eligibility
import build_paper_reviews
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def ptr(d,p):
 for k in p.strip('/').split('/') if p else []:
  k=k.replace('~1','/').replace('~0','~');d=d[int(k)] if isinstance(d,list) else d[k]
 return d
checks=[]
def ck(ok,label):
 checks.append({'check':label,'passed':bool(ok)})
 if not ok:raise AssertionError(label)

# Only reader display prose is rewritten. Exact source/canonical tokens stay intact.
PROSE={
'exchange-reagent':'The dynamic ion-exchange feed is aqueous thallous acetate supplied by Aldrich Chemical Co. with a stated purity of 99.99%.',
'exchange-stock':'The aqueous thallous-acetate feed has a reported concentration of 0.1 mol/L.',
'exchange-ph':'The reported pH of the aqueous thallous-acetate feed is 6.4.',
'indium-metal':'Indium metal from Aldrich Chemical Co., with a stated purity of 99.999%, is used for redox ion exchange. The metal mass and metal-to-zeolite ratio are unreported.',
'h2s-reagent':'The treatment gas is zeolitically dried H2S from Aldrich Chemical Co., with a stated purity of 99.999%. The drying apparatus, zeolite identity and drying procedure are not supplied.',
'capillary':'The crystals are handled in a fine Pyrex capillary. Its bore, wall thickness and the crystal count per treatment are unreported.',
'exchange-method':'Na-X is converted to Tl-X by dynamic ion exchange using a flow method. The flow rate and whether the Table 1 volume of 10 mL denotes total throughput or reservoir volume remain unresolved.',
'exchange-duration':'Table 1 gives an ion-exchange duration of 4 days. The experimental prose does not state this duration.',
'exchange-volume':'Table 1 lists 10 mL for ion exchange. Its volume basis does not establish a flow rate or circulation arrangement.',
'exchange-temperature':'Table 1 gives an ion-exchange temperature of 298 K.',
'tl-product':'The product after ion exchange is described nominally as Tl92Si100Al92O384. The suitability of stoichiometric exchange is supported by cited earlier work, rather than a new chemical-analysis table for each crystal.',
'initial-dehydration-prose-t':'The experimental prose gives 623 K for the initial Tl-X dehydration. Table 1 gives 673 K; this conflict remains unresolved.',
'initial-dehydration-prose-time':'The experimental prose gives 48 h for the initial Tl-X dehydration. Table 1 gives 3 days; this conflict remains unresolved.',
'dehydration-vacuum':'The prose reports 1 × 10⁻⁶ Torr for both dehydration steps. This pressure is not automatically assigned to the later indium-contact stage.',
'initial-dehydration-table-t':'Table 1 gives 673 K for initial Tl-X dehydration, in conflict with the 623 K stated in the prose.',
'initial-dehydration-table-time':'Table 1 gives 3 days for initial Tl-X dehydration, in conflict with the 48 h stated in the prose.',
'redox-t':'The source gives 623 K for contact with indium. It describes the crystals as somewhat cooler than the metal in the coaxial ovens, but supplies no separate setpoints.',
'redox-prose-time':'The prose gives an indium-contact duration of 96 h. Table 1 gives 5 days; these conflicting descriptions do not establish two separately demonstrated routes.',
'redox-table-time':'Table 1 gives an indium-contact duration of 5 days, in conflict with the 96 h stated in the prose.',
'redox-pressure':'The indium-contact stage is described as occurring under vacuum, without a numerical pressure. The dehydration pressure and cited equilibrium metal vapor pressures are separate quantities.',
'redox-ovens':'Coaxially connected cylindrical ovens are used. Indium condenses around crystals described as somewhat cooler than the metal, and droplets are observed near the crystals. Detailed geometry, the temperature gradient, metal mass and actual vacuum pressure are unreported.',
'black-reactant':'The crystal appears black after contact with indium. One crystal is selected, exposed to the atmosphere and washed; this appearance does not describe the optical color of a particle dispersion.',
'wash':'The selected black crystal is exposed to the atmosphere and washed with deionized water. The authors intend to remove surface thallium and indium residues, but report no quantified removal yield.',
'wash-time':'Table 1 gives a duration of 1 day for the deionized-water wash.',
'wash-volume':'Table 1 gives a volume of 10 mL for the deionized-water wash.',
'redehydrate-prose-t':'The prose gives 623 K for redehydration, in conflict with the 673 K in Table 1.',
'redehydrate-prose-time':'The prose gives 48 h for redehydration, in conflict with the 3 days in Table 1.',
'redehydrate-table-t':'Table 1 gives 673 K for redehydration, in conflict with the 623 K in the prose.',
'redehydrate-table-time':'Table 1 gives 3 days for redehydration, in conflict with the 48 h in the prose.',
'washed-parent':'The washed and redehydrated parent is described nominally as In87Si100Al92O384, with identity linked to reference 34. It remains distinct from the current H2S-treated In66-X product.',
'h2s-pressure':'The H2S exposure pressure is reported as 0.5 atm.',
'h2s-t':'The H2S exposure temperature is reported as 673 K.',
'h2s-time':'The H2S exposure duration is reported as 12 h.',
'evacuate-final':'After H2S treatment, the crystal is evacuated for 10 min at 673 K. The numerical vacuum pressure is not restated.',
'seal':'The crystal is sealed off from the vacuum line at room temperature for X-ray measurements, followed by EPXMA and XPS handling. No numerical cooling rate, sealing temperature or long-term storage instruction is supplied.',
'xrd-instrument':'Single-crystal diffraction uses a CAD4/Turbo diffractometer with a rotating-anode generator, graphite monochromator and Mo radiation.',
'xrd-t':'The reported diffraction acquisition temperature is 294 K.',
'unit-cell':'The refined cubic lattice constant is 24.942(4) Å, corresponding to an estimated standard deviation of 0.004 Å in the reported notation. This is the unit-cell length, not a finite-dot dimension.',
'cell-reflections':'The unit-cell determination uses 25 intense reflections from diverse reciprocal-space regions. These are not the complete reflection dataset.',
'background-count':'At each scan endpoint, the background is counted for half the scan time. This relative duration does not specify an absolute counting time.',
'xrd-monitor':'Three reflections from diverse reciprocal-space regions are checked every 3 h. Only small random intensity fluctuations are reported.',
'reflection-conditions':'The source reports hkl conditions h + k, k + l and l + h = 2n; for 0kl, k + l = 4n; and equal intensities for hkl and khl. These printed observations do not replace validation of the space-group origin and setting.',
'epxma-instrument':'The atmosphere-exposed product is examined using an EDAX 9100 EDS system attached to a Phillips 515 scanning electron microscope.',
'epxma-parent-control':'A fresh surface of an intentionally broken parent In87-X crystal is examined as an additional control. Indium is identified as its only nonframework element; this control is distinct from the H2S-treated product.',
'xps-instrument':'XPS is acquired with a VG ESCALAB 250 instrument.',
'xps-excitation':'The XPS acquisition uses Al Kα excitation at 1486.7 eV.',
'xps-power-voltage':'The reported XPS source voltage is 15 kV.',
'xps-current':'The reported XPS source current is 10 mA.',
'sputter-voltage':'The reported ion-gun voltage for XPS depth profiling is 3 kV.',
'sputter-rate':'The reported sputtering rate is 0.6 Å/s.',
'sputter-step':'The Figure 3 caption reports approximately 10 s of sputtering after each measurement. This is an interval in the displayed series, not a total sputtering duration or depth.',
'in-metal-xps':'For the indium-metal reference in Figure 2A, the approximate 3d3/2 and 3d5/2 energies are 451.8 and 444.3 eV, respectively.',
'xps-splitting':'The approximate indium 3d doublet splitting is 7.5 eV.',
'epxma-tl':'For the current product in Figure 1A, the absence of additional Tl L lines at 10.26 and 12.21 keV supports the assignment of the 2.31 keV feature to sulfur rather than the overlapping 2.27 keV thallium feature.'
}

def main():
 if B.exists():raise RuntimeError('v2 already exists; preserve it and use a new revision.')
 initial=read(A/'proposal-package-manifest.json')
 ck(sha(A/'proposal-package-manifest.json')=='bdf431a74cb75e08e3dfac9a630c90ded580aad0bb9dd0fc2c4e1669a105c948','Original v1 manifest')
 for p,h in initial['files'].items():ck(sha(A/p)==h,'Frozen v1 input '+p)
 shutil.copytree(A,B)
 oldreader=read(A/'public-review-proposal/heo2003.json');reader=copy.deepcopy(oldreader)
 items={x['id']:x for section in reader['reader_sections'] for x in section['items']}
 records={p.stem:read(p) for p in (B/'canonical-drafts').glob('*.json')}
 original_records=copy.deepcopy(records)
 xps=records['heo-2003-xps-acquisition']
 oldev=copy.deepcopy(xps['materials'][1]['evidence'])
 ev={'source_id':'heo2003','locator':'Main PDF p. 5 (printed p. 1124), XPS Analyses: argon sputtering'}
 xps['materials'][1]['evidence']=[ev]
 xps['operations'][1]['environment']['evidence'].append(ev)
 ck(xps['operations'][1]['parameters']==original_records[xps['record_id']]['operations'][1]['parameters'],'Ion-gun numerical conditions and p.2 settings evidence unchanged')
 dedup=[]
 for x in items.values():
  links=x['sample_scope']['canonical_sample_links'];seen=set();out=[]
  for v in links:
   key=(v['record_id'],v['sample_id'])
   if key not in seen:out.append(v);seen.add(key)
  if out!=links:dedup.append({'item_id':x['id'],'before':links,'after':out})
  x['sample_scope']['canonical_sample_links']=out
 ck(len(dedup)==42,'Exactly 42 redundant sample-link lists deduplicated')
 figure_populated=[]
 for number in range(1,8):
  x=items[f'asset-heo2003-figure-{number}'];ck(not x['sample_scope']['canonical_sample_links'],'Figure sample list initially empty '+str(number))
  links=[];seen=set()
  for v in x['canonical_links']:
   if 'sample_id' not in v:continue
   ck(ptr(records[v['record_id']],v['json_pointer'])['sample_id']==v['sample_id'],'Figure source-supported sample pointer '+str(number))
   key=(v['record_id'],v['sample_id'])
   if key not in seen:links.append(copy.deepcopy(v));seen.add(key)
  ck(bool(links),'Figure has supported prior associations '+str(number));x['sample_scope']['canonical_sample_links']=links
  figure_populated.append({'item_id':x['id'],'source':'existing canonical_links only','links':links})
 reader['si_aggregate_evidence']['audit_path']='../source-payloads/si-complete-candidate/independent-audit.json'
 resolved=B/'public-review-proposal'/reader['si_aggregate_evidence']['audit_path']
 ck(resolved.is_file(),'Corrected relative audit path exists')
 # Payload copy was normalized by v1; status remains bound to original hash, not its reserialization.
 ck(read(resolved)==read(H/'si-complete-candidate/independent-audit.json'),'Exact parsed independent SI audit payload')
 items['inventory-remaining_gaps-0']['text']='Historical extraction checkpoint: the original inventory recorded numerical SI transcription as pending. That statement is retained in the immutable source payload. The subsequent, separately passed aggregate audit covers all 1,209 reflection rows and 7,254 numeric positions; 7,252 signed values are resolved and two signs remain explicitly unknown. This reader references that audit without independently recertifying it.'
 items['inventory-remaining_gaps-9']['text']='Historical extraction checkpoint: reader authoring, canonical records and presentation work were still pending when the original inventory was frozen. The present package now contains private canonical and reader drafts. Their independent review, visual binding, integration and publication remain separate gates.'
 prose_changes=[]
 for short,text in PROSE.items():
  x=items['fact-'+short];prose_changes.append({'item_id':x['id'],'before':x['text'],'after':text});x['text']=text
 items['fact-exchange-ph']['title']='Feed pH'
 items['fact-outlook']['text']='Very high density information storage is proposed as a possible application if the individual clusters could be tagged electronically or magnetically, as the source states. No memory device, optical response or transport performance is demonstrated in this paper.'
 gap_updates={1:'Table 1 conflicts with the experimental prose on both dehydration temperatures and durations, and on indium-contact duration. These unresolved descriptions do not establish a unique executable route or a training pair between conditions and a target.',2:'Table 2 represents an average structure with partial occupancies and disordered Si/Al. The nominal formula, scattering-factor representation and charge-compensation hypotheses remain distinct.',4:'In66-X is an extended zeolite containing a cluster array. The approximate 0.15 mm host-crystal cross-section and 3.5 Å cluster radius describe different length scales.',5:'The full upstream host synthesis and cited parent or refinement-comparison papers were not inspected in this source package. No external source completion is claimed.',7:'The final gray surface phase and proposed hydrogen or oxygen charge-compensation species remain unverified. No sulfide phase, defect recipe or extra coordinate set is assigned.',8:'The supplied source does not report TEM/SAED, Raman, optical absorption/photoluminescence, device transport or a functioning storage experiment. Potential applications remain outlook.'}
 for i,t in gap_updates.items():items[f'inventory-remaining_gaps-{i}']['text']=t
 for i,c in enumerate(reader['evidence_conflicts']):c['description']=items[f'inventory-evidence_conflicts-{i}']['text']
 ax=items['material-heo-2003-xps-acquisition-argon'];ax['evidence']=[dict(ev,document_role='main')];ax['source_locators']=[ev['locator']]
 # The canonical records change only two evidence arrays; no scientific value, label or scope is changed.
 for rid,r in records.items():save(B/'canonical-drafts'/f'{rid}.json',r)
 cm=read(B/'canonical-record-manifest.json');cm['version']=2
 cm['record_hashes']={rid:sha(B/'canonical-drafts'/f'{rid}.json') for rid in records}
 for r in cm['records']:r['path']=str(B/'canonical-drafts'/f"{r['record_id']}.json")
 save(B/'canonical-record-manifest.json',cm)
 binding=read(B/'public-review-proposal/canonical-measurement-coverage.json');binding['canonical_hashes']=cm['record_hashes']
 save(B/'public-review-proposal/canonical-measurement-coverage.json',binding)
 save(B/'public-review-proposal/heo2003.json',reader)
 deltas=[]
 def diff(a,b,p):
  if type(a)!=type(b):deltas.append({'path':p,'before':a,'after':b})
  elif isinstance(a,dict):
   ck(set(a)==set(b),'Same dictionary keys '+p)
   for k in a:diff(a[k],b[k],p+'/'+k)
  elif isinstance(a,list):
   if len(a)!=len(b):deltas.append({'path':p,'before':a,'after':b})
   else:
    for i,(x,y) in enumerate(zip(a,b)):diff(x,y,p+'/'+str(i))
  elif a!=b:deltas.append({'path':p,'before':a,'after':b})
 for rid,r in records.items():diff(original_records[rid],r,rid)
 allowed={xps['record_id']+'/materials/1/evidence/0/locator',xps['record_id']+'/operations/1/environment/evidence'}
 ck({d['path'] for d in deltas}==allowed,'Only two canonical evidence changes')
 save(B/'canonical-evidence-delta.json',{'schema':'mattersyn-canonical-evidence-only-delta/1','original_manifest_sha256':sha(A/'canonical-record-manifest.json'),'deltas':deltas,'numeric_and_scientific_payloads_unchanged':True})
 # Every reader fact and exact typed quantity remains identical, including raw text/uncertainty.
 olditems={x['id']:x for s in oldreader['reader_sections'] for x in s['items']}
 for iid,x in items.items():
  ck(x['facts']==olditems[iid]['facts'],'All exact reader quantity payloads unchanged '+iid)
  ck(x['canonical_links']==olditems[iid]['canonical_links'],'Canonical field links unchanged '+iid)
  oldset={(q['record_id'],q['sample_id']) for q in olditems[iid]['sample_scope']['canonical_sample_links']};newset={(q['record_id'],q['sample_id']) for q in x['sample_scope']['canonical_sample_links']}
  expected={(q['record_id'],q['sample_id']) for q in olditems[iid]['canonical_links'] if 'sample_id' in q} if iid.startswith('asset-heo2003-figure-') else oldset
  ck(expected==newset,'Distinct supported specimen associations preserved '+iid)
 for rid,r in records.items():
  ck(not validate_record(r),'Schema and semantics '+rid)
  ck(not any(v['eligible'] for v in eligibility(r).values()),'No training eligibility '+rid)
 for b in binding['bindings']:ck(ptr(records[b['record_id']],b['json_pointer'])==b['canonical_quantity'],'Typed canonical object '+b['item_id']+b['json_pointer'])
 # Source, figures, table/SI payloads and coverage sidecars remain byte-identical.
 for p in (A/'source-payloads').rglob('*'):
  if p.is_file():ck(sha(p)==sha(B/p.relative_to(A)),'Exact source sidecar '+str(p.relative_to(A)))
 for name in ['source-fact-coverage.json','source-inventory-coverage.json','table-field-coverage.json','si-row-coverage.json','si-chunk-dependencies.json','public-review-proposal/source-item-coverage.json','public-review-proposal/reader-original-assets-manifest.json']:
  ck(sha(A/name)==sha(B/name),'Exact source/coverage sidecar '+name)
 ck(reader['figures']==oldreader['figures'] and reader['tables']==oldreader['tables'],'All original figure/table associations unchanged')
 for r in records.values():save(B/'reader-compatibility-projection/data/records'/f"{r['record_id']}.json",r)
 oldroot=build_paper_reviews.ROOT
 try:build_paper_reviews.ROOT=B/'reader-compatibility-projection';errors=build_paper_reviews.validate(reader)
 finally:build_paper_reviews.ROOT=oldroot
 ck(not errors,'Actual Site reader validator against private v2 projection')
 save(B/'reader-compatibility-check.json',{'status':'passed','errors':errors,'reader_sha256':sha(B/'public-review-proposal/heo2003.json'),'validator_path':str(S/'scripts/build_paper_reviews.py'),'validator_sha256':sha(S/'scripts/build_paper_reviews.py'),'projection_path':str(B/'reader-compatibility-projection'),'scope':'Structural validation only; independent scientific and runtime review pending.'})
 save(B/'reader-correction-delta.json',{'schema':'mattersyn-reader-bounded-corrections/1','original_reader_sha256':sha(A/'public-review-proposal/heo2003.json'),'corrected_reader_sha256':sha(B/'public-review-proposal/heo2003.json'),'deduplicated_items':dedup,'figure_sample_lists_populated':figure_populated,'prose_changes':prose_changes,'other_allowed_edits':['SI audit relative link','Historical inventory status labels','Global conflict display wording copied from existing readable conflict cards','Feed pH title','Argon identity evidence locator','Outlook retains source wording tagged electronically or magnetically'],'source_raw_payloads_unchanged':True,'reader_typed_facts_unchanged':True,'original_assets_and_supported_associations_unchanged':True})
 ck(all(sha(A/n)==h for n,h in initial['files'].items()),'Every frozen v1 file remains unchanged')
 validation={'schema':'mattersyn.private_proposal_author_validation.v2','status':'passed_author_checks_pending_distinct_reaudit','author':'/root/peng1998_reader_assets','counts':cm['counts'],'check_count':len(checks),'checks':checks,'failures':[],'preserved_v1_manifest_sha256':sha(A/'proposal-package-manifest.json'),'schema_sha256':sha(S/'dist/data/record.schema.json'),'limits':['Bounded author correction only; the original independent reviewer must verify v2.','Molecular binding proposal based on the old XPS record hash needs a separate bounded rebind before integration.','No Site, source, frozen v1, training or publication modification.']}
 save(B/'public-review-proposal/proposal-validation.json',validation)
 with (B/'README.md').open('a',encoding='utf-8') as f:f.write('\n## Preserved correction revision 2\n\nThe independent v1 review identified redundant sample links, a broken private SI-audit relative path, historical source-inventory progress text, compressed display prose and an argon identity locator. This revision corrects those issues while preserving all canonical values, condition conflicts, raw table/SI payloads and distinct specimen associations. Only the XPS material and sputter-environment evidence arrays change in canonical data; p. 2 ion-gun settings remain intact and p. 5 now supplies the explicit argon identity. Independent re-audit is required.\n')
 files={str(p.relative_to(B)):sha(p) for p in sorted(B.rglob('*')) if p.is_file() and p.name!='proposal-package-manifest.json'}
 save(B/'proposal-package-manifest.json',{'schema':'mattersyn.private_proposal_package.v2','version':2,'source_id':'heo2003','author':'/root/peng1998_reader_assets','status':'frozen_author_correction_pending_independent_reaudit','counts':cm['counts'],'files':files,'external_input_hashes':initial['external_input_hashes'],'builder_sha256':sha(__file__),'prior_package_manifest_sha256':sha(A/'proposal-package-manifest.json')})
 print(json.dumps({'status':validation['status'],'check_count':len(checks),'manifest_sha256':sha(B/'proposal-package-manifest.json'),'reader_sha256':sha(B/'public-review-proposal/heo2003.json'),'canonical_manifest_sha256':sha(B/'canonical-record-manifest.json'),'changed_record_sha256':cm['record_hashes']['heo-2003-xps-acquisition']},indent=2))

if __name__=='__main__':main()
