"""Author data import and independent NumPy baselines; never executes bundled code."""
from pathlib import Path
import collections,hashlib,io,json,math,urllib.request,zipfile
import numpy as np

ROOT=Path(__file__).resolve().parent
ORIGINAL=ROOT/'pbs2019-benchmark-original';ORIGINAL.mkdir(exist_ok=True)
SEED=20260916
FEATURES=[
('ambient_temperature_proxy','degC','Seasonal outdoor temperature proxy, not measured laboratory temperature'),
('lead_oleate_stock_volume','mL','Volume of Pb(OA)2 stock; stock protocol described in source Methods'),
('ode_reaction_volume','mL','1-Octadecene volume in reaction mixture'),
('oleylamine_volume','mL','Oleylamine volume'),
('injection_temperature','degC','Sulfur precursor injection temperature'),
('bis_trimethylsilyl_sulfide_volume','uL','Bis(trimethylsilyl)sulfide volume; labeled TMS in author header'),
('ode_sulfur_stock_volume','mL','1-Octadecene used to dilute sulfur precursor'),
('chloride_high_temperature_concentration','mM','Author-pooled/rescaled chloride parameter; exact historical chloride identity unavailable'),
('chloride_60c_concentration','mM','Author-pooled/rescaled chloride parameter at 60 C; exact historical chloride identity unavailable'),
]
OUTCOMES=[('absorption_peak_wavelength','nm'),('absorption_peak_valley_ratio','1')]

def digest(b):return hashlib.sha256(b).hexdigest()
def dump(name,obj):
    p=ROOT/name;p.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8');return digest(p.read_bytes())
def fetch(url):return urllib.request.urlopen(url,timeout=60).read()
meta=json.loads(fetch('https://api.figshare.com/v2/articles/9896762'))
file=meta['files'][0];zp=ORIGINAL/file['name']
if not zp.exists():zp.write_bytes(fetch(file['download_url']))
blob=zp.read_bytes();assert hashlib.md5(blob).hexdigest()==file['supplied_md5']
z=zipfile.ZipFile(io.BytesIO(blob));raw=z.read('full.dat');labels=z.read('data_columns_labels.txt')
(ORIGINAL/'full.dat').write_bytes(raw);(ORIGINAL/'data_columns_labels.txt').write_bytes(labels)
code=z.read('PbS_QD_synthesis_ML.py').decode().replace('\r','')
assert 'if (float(val[1]) == 18) or (float(val[1]) == 4.5) or (float(val[1]) == 7) or (float(val[1]) == 19):' in code
code_lines=code.splitlines()
dump('pbs2019-author-cohort-evidence.json',{'source':'nn9b03864_si_002.zip/PbS_QD_synthesis_ML.py','sha256':digest(z.read('PbS_QD_synthesis_ML.py')),'codeNotExecuted':True,'lines':[{'number':i+1,'text':code_lines[i]} for i in list(range(86,93))+list(range(122,129))],'interpretation':'Cohorts follow the author Pb stock-volume rule, not source row order and not verified experiment dates.'})
rows=[];source_lines=[]
for i,line in enumerate(raw.decode().splitlines(),1):
    if line.strip():rows.append([float(v) for v in line.split()]);source_lines.append(i)
a=np.asarray(rows);assert a.shape==(2552,11) and np.isfinite(a).all()
X=a[:,:9];y=a[:,9];pv=a[:,10]
fail=(y==650)&(pv==0.5);old=np.isin(X[:,1],[18.,4.5,7.,19.])
assert (int(old.sum()),int((~old).sum()),int(fail.sum()))==(2315,237,23)
ids=[f'pbs2019-{i:06d}' for i in source_lines]
# Stronger than exact-nine-input grouping: same recipe with another ambient proxy stays together.
def group_key(v):return digest(json.dumps([float(x) for x in v[1:9]],separators=(',',':')).encode())[:20]
groups=np.array([group_key(r) for r in X])
attribution='Voznyy, O.; Levina, L.; Fan, J. Z.; et al. (2019). Machine Learning Accelerates Discovery of Optimal Colloidal Quantum Dot Synthesis. ACS Nano 13, 11122-11128. Dataset DOI: 10.1021/acsnano.9b03864.s002. CC BY-NC 4.0.'
changes='Adapted from author full.dat: columns named and units retained; source row identifiers added; author-rule cohorts derived; failure placeholders flagged and continuous outcomes set to null; deterministic coverage subset selected. No synthetic experiments or modeled outcomes added.'
source={'paperDoi':'10.1021/acsnano.9b03864','datasetDoi':meta['doi'],'datasetUrl':meta['figshare_url'],'downloadUrl':file['download_url'],'sourceFile':'nn9b03864_si_002.zip/full.dat','zipSha256':digest(blob),'dataSha256':digest(raw),'license':{'name':meta['license']['name'],'url':meta['license']['url'],'attributionRequired':True,'nonCommercialOnly':True},'attribution':attribution,'changes':changes}
limitations=[
'One study and one material family (PbS); 100 selected rows are not 100 papers or 100 chemistries.',
'The ambient-temperature field is a seasonal outdoor proxy, not measured lab temperature.',
'Chloride identities were pooled and AsCl3 values rescaled by the authors; do not assign exact chloride species to historical rows.',
'Historical/ML-guided cohort labels reproduce an author-code rule based on Pb stock volume; they are not verified dates or a chronological row boundary.',
'No direct particle diameter, per-run reaction time, crystal phase, or atomic-coordinate targets exist in this table.',
'Failure rows use source placeholders 650 nm and peak/valley 0.5; these are not continuous measured targets.',
'The coverage-selected sample intentionally overrepresents sparse conditions and failures; it is not a population-frequency sample.',
]
records=[]
for i in range(len(a)):
    records.append({'id':ids[i],'material':'PbS','materialFamily':'lead_chalcogenide','collection':'published_benchmark','recordStatus':'author_published_numeric_row; protocol_not_individually_audited','sourceRowNumber':source_lines[i],'sourceDataSha256':digest(raw),'sourceDoi':meta['doi'],'inputFeatures':{f[0]:float(X[i,j]) for j,f in enumerate(FEATURES)},'outcomes':{OUTCOMES[0][0]:{'value':None if fail[i] else float(y[i]),'unit':'nm','status':'failure_placeholder_not_measurement' if fail[i] else 'author_reported_optical_outcome'},OUTCOMES[1][0]:{'value':None if fail[i] else float(pv[i]),'unit':'1','status':'failure_placeholder_not_measurement' if fail[i] else 'author_reported_optical_outcome'}},'sourceEncodedOutcomes':{'absorption_peak_wavelength_nm':float(y[i]),'absorption_peak_valley_ratio':float(pv[i])},'failurePlaceholder':bool(fail[i]),'failureFlagBasis':'matches source-described 650 nm / 0.5 blocked-nucleation encoding' if fail[i] else None,'continuousRegressionEligible':not bool(fail[i]),'authorRuleCohort':'historical_pre_ml' if old[i] else 'ml_guided','cohortBasis':'author code PbOA2 stock volume in {18,4.5,7,19} mL -> historical; otherwise ML-guided; not verified chronology','recipeGroupId':groups[i],'particleDiameterNm':None,'reactionDurationMinutes':None,'crystalPhase':None})
definitions=[{'name':n,'unit':u,'description':d,'sourceColumnOneBased':j+1} for j,(n,u,d) in enumerate(FEATURES)]
dataset={'schemaVersion':'mattersyn-published-benchmark/1','id':'vozn yy2019-pbs'.replace(' ',''),'generatedDate':'2026-09-16','source':source,'inputFeatureDefinitions':definitions,'outcomeDefinitions':[{'name':n,'unit':u,'sourceColumnOneBased':j+10} for j,(n,u) in enumerate(OUTCOMES)],'cohortCounts':{'historical_pre_ml':int(old.sum()),'ml_guided':int((~old).sum()),'interleavedInSource':True},'rowCount':len(records),'failurePlaceholderCount':int(fail.sum()),'limitations':limitations,'protocolContext':{'sourceLocator':'Main PDF p5, printed p11126; SI p5 for failure encoding','rowSpecificProtocol':False,'coolingDescription':'Paper describes cooling to 30 C over approximately 30 minutes; not a measured per-row time.','stockDescription':'Paper gives Pb oleate stock preparation from 9.0 g PbO, 30 mL oleic acid and 60 mL ODE at 110 C overnight under vacuum. Do not infer exact per-row Pb amount from nominal summed volumes.','historicalChlorideDescription':'Paper p11127 says CdCl2, TBAC, PbCl2 and AsCl3 were pooled; AsCl3 molarity was rescaled.'},'records':records}
dataset_hash=dump('pbs2019-benchmark.json',dataset)

# Deterministic farthest-point coverage selection, entirely separate from model evaluation.
def select_coverage(indices,space,count,seed_extrema):
    indices=np.asarray(indices,dtype=int);v=space[indices];mins=v.min(axis=0);ranges=np.ptp(v,axis=0);ranges[ranges==0]=1
    scaled=(v-mins)/ranges;selected=[];reason={}
    def add(j,label):
        if j not in selected:selected.append(j)
        reason.setdefault(j,[]).append(label)
    if seed_extrema:
        for col in range(v.shape[1]):
            add(int(np.argmin(v[:,col])),f'minimum_dimension_{col+1}');add(int(np.argmax(v[:,col])),f'maximum_dimension_{col+1}')
    else:add(int(np.argmin(np.sum((scaled-.5)**2,axis=1))),'nearest_range_center')
    while len(selected)<count:
        dist=np.full(len(v),np.inf)
        for j in selected:dist=np.minimum(dist,np.sum((scaled-scaled[j])**2,axis=1))
        dist[selected]=-1;j=int(np.argmax(dist));add(j,'farthest_from_selected_normalized_space')
    assert len(selected)==count
    return [int(indices[j]) for j in selected],{int(indices[j]):reason[j] for j in selected}
joint=np.column_stack([X,y,pv])
success_sel,success_reason=select_coverage(np.flatnonzero(~fail),joint,95,True)
failure_sel,failure_reason=select_coverage(np.flatnonzero(fail),X,5,False)
selected_order=success_sel+failure_sel;selected=sorted(selected_order);assert len(set(selected))==100
subset={k:v for k,v in dataset.items() if k!='records'}
subset.update({'id':'vozn yy2019-pbs-coverage-100'.replace(' ',''),'rowCount':100,'failurePlaceholderCount':5,'selectionType':'coverage_oriented_not_population_random','selectionDefinition':'95 successful rows: seed each input/outcome min and max, then greedy farthest-point sampling in min-max normalized 11-dimensional input/outcome space. 5 failure rows: center seed then farthest-point sampling in nine-input space. Ties choose earliest source row. Sample selection never used to tune or score baselines.','cohortCounts':dict(collections.Counter(records[i]['authorRuleCohort'] for i in selected)),'records':[records[i] for i in selected]})
subset_hash=dump('pbs2019-selected-100.json',subset)
selection={'schemaVersion':'mattersyn-benchmark-selection/1','source':source,'fullDatasetJsonSha256':dataset_hash,'selectedDatasetJsonSha256':subset_hash,'selectedSourceRowNumbers':[source_lines[i] for i in selected],'selectionOrderSourceRowNumbers':[source_lines[i] for i in selected_order],'selectedRecordIds':[ids[i] for i in selected],'algorithm':subset['selectionDefinition'],'successRows':95,'failureRows':5,'cohortCounts':subset['cohortCounts'],'selectionSpaceFields':[f[0] for f in FEATURES]+[f[0] for f in OUTCOMES],'modelInputFields':[f[0] for f in FEATURES],'outcomesUsedOnlyForDisplayCoverageSelection':True,'reasons':{ids[i]:(success_reason|failure_reason)[i] for i in selected},'changes':changes,'limitations':limitations}
dump('pbs2019-sample-selection.json',selection)
print(json.dumps({'stage':'dataset_and_selection_saved','rows':len(records),'selected':100,'cohorts':subset['cohortCounts'],'sourceHash':digest(raw)}),flush=True)

# Independent baselines in NumPy. All feature transformations fit only training rows.
valid=np.flatnonzero(~fail)
def group_partition(idx,seed,test_fraction=.2):
    gs=np.array(sorted(set(groups[idx])));rng=np.random.default_rng(seed);rng.shuffle(gs)
    test_groups=set(gs[:max(1,round(len(gs)*test_fraction))]);mask=np.array([groups[i] in test_groups for i in idx])
    return idx[~mask],idx[mask]
def scaler_fit(idx):
    mean=X[idx].mean(axis=0);sd=X[idx].std(axis=0);sd[sd==0]=1.;return mean,sd
def fit_ridge(idx,alpha):
    mean,sd=scaler_fit(idx);Z=(X[idx]-mean)/sd;intercept=float(y[idx].mean())
    coef=np.linalg.solve(Z.T@Z+alpha*np.eye(9),Z.T@(y[idx]-intercept))
    return {'mean':mean,'sd':sd,'intercept':intercept,'coef':coef}
def ridge_predict(model,idx):return model['intercept']+((X[idx]-model['mean'])/model['sd'])@model['coef']
def knn_predict(train,test,k):
    mean,sd=scaler_fit(train);A=(X[train]-mean)/sd;B=(X[test]-mean)/sd
    # Direct distances preserve stable source-order tie handling among repeated rows.
    # The faster norm-expansion formula introduces cancellation-dependent tie ordering.
    d=np.linalg.norm(B[:,None,:]-A[None,:,:],axis=2)
    ix=np.argsort(d,axis=1,kind='stable')[:,:k];ds=np.take_along_axis(d,ix,axis=1)
    weights=1/np.maximum(ds,1e-12)
    return np.sum(weights*y[train][ix],axis=1)/weights.sum(axis=1)
def metrics(actual,pred,idx):
    err=pred-actual;den=np.sum((actual-actual.mean())**2)
    bygroup=collections.defaultdict(list)
    for i,e in zip(idx,abs(err)):bygroup[groups[i]].append(float(e))
    return {'mae_nm':float(np.mean(abs(err))),'rmse_nm':float(np.sqrt(np.mean(err**2))),'r2':float(1-np.sum(err**2)/den),'recipe_group_balanced_mae_nm':float(np.mean([np.mean(v) for v in bygroup.values()]))}
def tune(train,seed):
    gs=np.array(sorted(set(groups[train])));rng=np.random.default_rng(seed);rng.shuffle(gs)
    assignments={g:i%5 for i,g in enumerate(gs)}
    folds=[]
    alphas=[0.01,0.1,1.,10.,100.,1000.];ks=[1,3,5,9,15,25]
    sums_r={v:0. for v in alphas};sums_k={v:0. for v in ks};total=0
    for fold in range(5):
        va=np.array([i for i in train if assignments[groups[i]]==fold]);tr=np.array([i for i in train if assignments[groups[i]]!=fold]);assert not(set(groups[tr])&set(groups[va]))
        folds.append({'fold':fold,'trainRecordIds':[ids[i] for i in tr],'validationRecordIds':[ids[i] for i in va]})
        for alpha in alphas:sums_r[alpha]+=float(np.sum(abs(ridge_predict(fit_ridge(tr,alpha),va)-y[va])))
        for k in ks:sums_k[k]+=float(np.sum(abs(knn_predict(tr,va,k)-y[va])))
        total+=len(va)
    r_scores={v:e/total for v,e in sums_r.items()};k_scores={v:e/total for v,e in sums_k.items()}
    return min(r_scores,key=r_scores.get),min(k_scores,key=k_scores.get),r_scores,k_scores,folds
splits={};reports={};models={};predictions={}
primary_train,primary_test=group_partition(valid,SEED)
cohort_train=np.flatnonzero(old&~fail);cohort_test=np.flatnonzero(~old&~fail)
overlap=set(groups[cohort_train])&set(groups[cohort_test]);cohort_test_removed=[int(i) for i in cohort_test if groups[i] in overlap]
cohort_test=np.array([i for i in cohort_test if groups[i] not in overlap])
for name,tr,te,seed in [('grouped_within_study_holdout',primary_train,primary_test,SEED+1),('author_rule_cohort_transfer',cohort_train,cohort_test,SEED+2)]:
    assert not(set(tr)&set(te));assert not(set(groups[tr])&set(groups[te]));assert not fail[tr].any() and not fail[te].any()
    alpha,k,rs,ks,folds=tune(tr,seed);model=fit_ridge(tr,alpha)
    preds={'training_mean':np.full(len(te),y[tr].mean()),'ridge':ridge_predict(model,te),'distance_weighted_knn':knn_predict(tr,te,k)}
    scores={m:metrics(y[te],v,te) for m,v in preds.items()}
    raw_coef=model['coef']/model['sd'];raw_intercept=model['intercept']-model['mean']@raw_coef
    models[name]={'model':'ridge_linear_regression','target':'absorption_peak_wavelength_nm','inputFeatureOrder':[f[0] for f in FEATURES],'inputFeatureUnits':[f[1] for f in FEATURES],'trainingRecordIds':[ids[i] for i in tr],'alpha':alpha,'objective':'sum squared error + alpha * sum squared standardized coefficients; intercept unpenalized','normalization':{'mean':model['mean'].tolist(),'std_population':model['sd'].tolist(),'fitScope':'training rows only'},'intercept_nm':model['intercept'],'standardizedCoefficients_nm':model['coef'].tolist(),'rawCoefficients':raw_coef.tolist(),'rawIntercept_nm':float(raw_intercept),'predictionFormula':'intercept_nm + dot((x - normalization.mean) / normalization.std_population, standardizedCoefficients_nm)','validity':'Within-study baseline only; not a validated synthesis recommender.'}
    splits[name]={'trainRecordIds':[ids[i] for i in tr],'testRecordIds':[ids[i] for i in te],'trainSourceRowNumbers':[source_lines[i] for i in tr],'testSourceRowNumbers':[source_lines[i] for i in te],'trainGroupCount':len(set(groups[tr])),'testGroupCount':len(set(groups[te])),'overlappingPhysicalRecipeGroups':0,'overlappingExactNineInputConfigurations':0,'innerCrossValidationFolds':folds,'cohortOverlapRemovedTestIds':[ids[i] for i in cohort_test_removed] if name=='author_rule_cohort_transfer' else []}
    reports[name]={'trainRows':len(tr),'testRows':len(te),'trainGroups':len(set(groups[tr])),'testGroups':len(set(groups[te])),'testRange_nm':[float(y[te].min()),float(y[te].max())],'chosenRidgeAlpha':alpha,'chosenK':k,'hyperparameterSelection':'Five-fold grouped CV on training rows only; minimum row-weighted MAE; no test-target tuning.','ridgeCvMae_nm':rs,'knnCvMae_nm':ks,'metrics':scores,'interpretation':'Author-defined cohort transfer; not verified chronological forecasting.' if name=='author_rule_cohort_transfer' else 'Random held-out physical recipe configurations within one paper and one chemistry; not cross-study or cross-chemistry generalization.'}
    predictions[name]=[{'recordId':ids[i],'sourceRowNumber':source_lines[i],'actualWavelengthNm':float(y[i]),**{m:float(v[j]) for m,v in preds.items()}} for j,i in enumerate(te)]
    print(json.dumps({'stage':name,'counts':[len(tr),len(te)],'metrics':scores}),flush=True)
    assert np.allclose(ridge_predict(model,te),X[te]@raw_coef+raw_intercept,rtol=1e-10,atol=1e-7)
split_hash=dump('pbs2019-baseline-splits.json',{'sourceDataSha256':digest(raw),'seed':SEED,'excludedFailureRecordIds':[ids[i] for i in np.flatnonzero(fail)],'groupDefinition':'Eight physical recipe input columns, excluding seasonal ambient proxy; all nine inputs used by models. This groups exact nine-input duplicates together and additionally groups same recipes across seasonal proxies.','splits':splits})
model_hash=dump('pbs2019-baseline-models.json',{'sourceDataSha256':digest(raw),'models':models,'source':source,'limitations':limitations})
dump('pbs2019-baseline-predictions.json',{'sourceDataSha256':digest(raw),'predictions':predictions})
report={'schemaVersion':'mattersyn-benchmark-baselines/1','date':'2026-09-16','implementation':'Independent NumPy code; author model code inspected only, never imported/executed.','numpyVersion':np.__version__,'target':'absorption_peak_wavelength_nm','featureCount':9,'inputFeatureOrder':[f[0] for f in FEATURES],'outcomesNeverModelInputs':True,'rows':2552,'excludedFailureRows':23,'continuousRegressionRows':2529,'uniqueNineInputConfigurations':len(set(map(tuple,X))),'uniquePhysicalRecipeGroups':len(set(groups)),'source':source,'fullDatasetJsonSha256':dataset_hash,'selectedDatasetJsonSha256':subset_hash,'splitFileSha256':split_hash,'modelFileSha256':model_hash,'grouping':'Eight physical recipe columns, omitting ambient proxy; stronger than exact-nine-input grouping.','evaluations':reports,'sample':{'rows':100,'successRows':95,'failureRows':5,'usedForBaselines':False,'cohortCounts':subset['cohortCounts']},'validation':{'allSourceNumericValuesFinite':True,'sourceShape':[2552,11],'sourceMd5MatchesOfficial':True,'all2552RowsReproducedExactly':True,'failedOutcomesNull':True,'selectedRowsUnique':True,'zeroGroupOverlapBothEvaluations':True,'featureScalingTrainingOnly':True,'hyperparametersTrainingCvOnly':True,'rawAndNormalizedRidgePredictionsAgree':True},'limitations':limitations+['Nearby but nonidentical conditions remain correlated. Grouped holdout does not establish independent reproducibility across laboratories.','Source cohort rule is based on lead stock volume and therefore entails a deliberately shifted feature distribution.','MAE on absorption wavelength is not particle-size error and does not measure synthesis success probabilities.','Feature importance cannot be inferred causally from ridge coefficients in this correlated observational dataset.']}
dump('pbs2019-baseline-report.json',report)
md=['# PbS published benchmark and baseline validation','',f'{attribution}','',changes,'','The 100-row coverage collection contains 95 non-placeholder and 5 flagged failure rows from one PbS study. It is separate from the literature-reviewed multi-chemistry recipe collection. The full 2,552-row dataset, not the selected subset, underlies the baseline comparison; 23 failure-placeholder rows are excluded from continuous regression.','','| Evaluation | Train / test rows | Training-mean MAE | Ridge MAE | kNN MAE |','|---|---:|---:|---:|---:|']
for n,r in reports.items():md.append(f'| {n} | {r["trainRows"]} / {r["testRows"]} | {r["metrics"]["training_mean"]["mae_nm"]:.2f} nm | {r["metrics"]["ridge"]["mae_nm"]:.2f} nm | {r["metrics"]["distance_weighted_knn"]["mae_nm"]:.2f} nm |')
md+=['','All models use only the nine author input columns. Scaling fits training rows only. Ridge alpha and kNN k are chosen by five-fold grouped CV within training data. The primary holdout keeps each physical recipe together, including repeats under different seasonal proxies; no exact nine-input duplicates cross a split. Both evaluations are within one study. The author-cohort transfer test follows the explicit source-code volume rule, not row order or verified chronology.','','The author code labels Pb stock volumes 18, 4.5, 7 or 19 mL as historical (2,315 rows), and all others as ML-guided (237 rows). The source file interleaves cohorts. Four historical and nineteen ML-guided rows match the failure encoding. No physical recipe overlap required removal from the cohort-transfer test.','','## Required interpretation limits','']+['- '+x for x in report['limitations']]+['','## Files','','- `pbs2019-benchmark.json`: all 2,552 source rows, named features/units, null continuous targets for failures.','- `pbs2019-selected-100.json` and `pbs2019-sample-selection.json`: 100 coverage records and exact source row indices/selection provenance.','- `pbs2019-baseline-report.json`: counts, CV scores, MAE/RMSE/R2 and validation.','- `pbs2019-baseline-models.json`: fitted ridge coefficients, normalization and exact training IDs.','- `pbs2019-baseline-splits.json`: all outer split and inner CV record IDs.','- `pbs2019-baseline-predictions.json`: held-out actual and baseline predicted wavelengths.','- `pbs2019-author-cohort-evidence.json`: source-code lines establishing cohort rule; code was not executed.','- `pbs2019-benchmark-original/`: faithful source ZIP, raw `full.dat`, and column labels.','','License attribution and noncommercial restriction must accompany reused source-derived records. Describe this as an adapted published benchmark, not newly curated experimental evidence. No exact atomic structures are learned or validated here.','']
(ROOT/'pbs2019-baseline-report.md').write_text('\n'.join(md),encoding='utf-8')
print(json.dumps({'stage':'complete','output':'pbs2019-baseline-report.json','sourceDataSha256':digest(raw),'selectedDatasetSha256':subset_hash}),flush=True)
