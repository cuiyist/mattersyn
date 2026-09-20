"""Round-trip and leakage checks independent of the preparation script."""
import json,hashlib
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent
def read(n):return json.loads((R/n).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
d=read('pbs2019-benchmark.json');s=read('pbs2019-selected-100.json');sel=read('pbs2019-sample-selection.json')
rep=read('pbs2019-baseline-report.json');split=read('pbs2019-baseline-splits.json');models=read('pbs2019-baseline-models.json');preds=read('pbs2019-baseline-predictions.json')
raw=np.loadtxt(R/'pbs2019-benchmark-original'/'full.dat');records=d['records'];fields=[v['name'] for v in d['inputFeatureDefinitions']]
assert len(fields)==9 and len(records)==2552 and len({v['id'] for v in records})==2552
X=np.array([[r['inputFeatures'][f] for f in fields] for r in records]);encoded=np.array([[r['sourceEncodedOutcomes']['absorption_peak_wavelength_nm'],r['sourceEncodedOutcomes']['absorption_peak_valley_ratio']] for r in records])
assert np.array_equal(np.column_stack([X,encoded]),raw)
failure=(raw[:,9]==650)&(raw[:,10]==.5);assert failure.sum()==23
byid={r['id']:i for i,r in enumerate(records)};groups={r['id']:tuple(X[i,1:9]) for i,r in enumerate(records)}
for i,r in enumerate(records):
    assert r['sourceRowNumber']==i+1 and r['failurePlaceholder']==bool(failure[i])
    assert (r['outcomes']['absorption_peak_wavelength']['value'] is None)==bool(failure[i])
    assert (r['outcomes']['absorption_peak_valley_ratio']['value'] is None)==bool(failure[i])
    assert r['continuousRegressionEligible']!=bool(failure[i])
    assert r['authorRuleCohort']==('historical_pre_ml' if X[i,1] in [18,4.5,7,19] else 'ml_guided')
assert len(s['records'])==100 and sum(r['failurePlaceholder'] for r in s['records'])==5
assert sel['selectedRecordIds']==[r['id'] for r in s['records']]
assert sel['selectedSourceRowNumbers']==[r['sourceRowNumber'] for r in s['records']]
assert all(r==records[byid[r['id']]] for r in s['records'])
assert sel['fullDatasetJsonSha256']==sha(R/'pbs2019-benchmark.json')
assert sel['selectedDatasetJsonSha256']==sha(R/'pbs2019-selected-100.json')
assert rep['splitFileSha256']==sha(R/'pbs2019-baseline-splits.json')
assert rep['modelFileSha256']==sha(R/'pbs2019-baseline-models.json')
checks={}
for name,sp in split['splits'].items():
    train=sp['trainRecordIds'];test=sp['testRecordIds'];tr=np.array([byid[i] for i in train]);te=np.array([byid[i] for i in test]);mod=models['models'][name]
    assert not(set(train)&set(test));assert not({groups[i] for i in train}&{groups[i] for i in test})
    assert not failure[tr].any() and not failure[te].any()
    assert mod['trainingRecordIds']==train
    mu=X[tr].mean(axis=0);sd=X[tr].std(axis=0);sd[sd==0]=1
    assert np.allclose(mu,mod['normalization']['mean']) and np.allclose(sd,mod['normalization']['std_population'])
    fold_validation=[]
    for fold in sp['innerCrossValidationFolds']:
        ft=fold['trainRecordIds'];fv=fold['validationRecordIds'];assert set(ft)|set(fv)==set(train)
        assert not({groups[i] for i in ft}&{groups[i] for i in fv});assert not(set(test)&(set(ft)|set(fv)))
        fold_validation.extend(fv)
    assert len(fold_validation)==len(train) and set(fold_validation)==set(train)
    p=preds['predictions'][name];assert [r['recordId'] for r in p]==test
    yr=mod['intercept_nm']+((X[te]-mu)/sd)@np.asarray(mod['standardizedCoefficients_nm'])
    assert np.allclose(yr,[r['ridge'] for r in p],rtol=1e-9,atol=1e-7)
    # Independent direct-distance kNN reproduces reported predictions.
    zz=(X-mu)/sd;k=rep['evaluations'][name]['chosenK'];kn=[]
    for i in te:
        distance=np.linalg.norm(zz[tr]-zz[i],axis=1);nearest=np.argsort(distance,kind='stable')[:k]
        w=1/np.maximum(distance[nearest],1e-12);kn.append(float(np.sum(w*raw[tr[nearest],9])/w.sum()))
    assert np.allclose(kn,[r['distance_weighted_knn'] for r in p],rtol=1e-7,atol=1e-4)
    for method in ['training_mean','ridge','distance_weighted_knn']:
        mae=float(np.mean(abs(np.array([r[method] for r in p])-raw[te,9])))
        assert abs(mae-rep['evaluations'][name]['metrics'][method]['mae_nm'])<1e-8
    checks[name]={'trainRows':len(train),'testRows':len(test),'outerRecipeOverlap':0,'cvPartitionAndNoTestContamination':True,'trainingOnlyNormalizationVerified':True,'ridgePredictionsReproduced':True,'knnDirectDistancePredictionsReproduced':True,'maeRecomputed':True}
for fn in ['pbs2019-benchmark.json','pbs2019-selected-100.json','pbs2019-sample-selection.json','pbs2019-baseline-report.json','pbs2019-baseline-models.json']:
    t=(R/fn).read_text(encoding='utf-8');assert 'C:\\' not in t and 'C:/' not in t and '/Users/' not in t
out={'status':'passed','sourceDataSha256':sha(R/'pbs2019-benchmark-original'/'full.dat'),'checks':{'all2552RowsRoundTripExactly':True,'nineInputsAndTwoOutcomes':True,'failureTargetsNullAndRawEncodingPreserved':True,'authorRuleCohortsVerified':True,'selected100MatchCanonicalRows':True,'allReferencedHashesMatch':True,'noAbsoluteLocalPathsInPublicCandidateJson':True},'evaluations':checks}
(R/'pbs2019-benchmark-validation.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out,indent=2))
