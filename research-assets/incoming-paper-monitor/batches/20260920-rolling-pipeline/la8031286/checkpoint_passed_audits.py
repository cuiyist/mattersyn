from pathlib import Path
import hashlib,json,sys
P=Path(__file__).resolve().parent;MON=P.parents[2]
sys.path.insert(0,str(MON));import monitor
paths=[P/'source-independent-audit/independent-audit-v1.json',P/'canonical-reader-independent-audit/independent-audit-v2.json',P/'visuals/apparatus-independent-audit/independent-audit.json',P/'visuals/molecules-independent-audit/independent-audit-v2.json',P/'product-context-independent-audit/independent-audit.json']
for p in paths:assert json.loads(p.read_text('utf8'))['status']=='passed'
ledger=monitor.read_ledger(MON/'ledger.json');g=ledger['groups']['10.1021_la8031286']
assert g['generation']==1 and not g.get('needs_recheck')
evidence=[str(p) for p in paths]
result=monitor.checkpoint(MON/'ledger.json','mattersyn-primary',group_id='10.1021_la8031286',note='Pati source, canonical/reader and all three visual-package audits passed. Preserved nitrate-label correction resolved. Website integration, mounted browser and publication remain pending.',data={'current_step':'Preparing root-owned Site integration from independently passed Pati packages','independent_audits':[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths],'effective_molecular_map':str(P/'visuals/molecules/annotation-correction-v2/effective-file-map.json')},milestones={'audit':{'status':'complete','evidence':evidence,'note':'Distinct source/canonical/molecular/apparatus/product audits passed. No publication or exact atomistic training approval is inferred.'}})
print(json.dumps({'status':'audit_milestone_complete','paper':'pati2009','scientific_records_imported':False,'publication':'pending'}))
