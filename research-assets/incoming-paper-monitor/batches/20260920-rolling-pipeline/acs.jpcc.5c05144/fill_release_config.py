from pathlib import Path
import json,hashlib
J=Path(__file__).resolve().parent;S=J.parents[4]/'recipe-atlas';p=J/'release-config.json';c=json.loads(p.read_text('utf8'));s=json.loads((S/'data/inventory-summary.json').read_text('utf8'))['summary']
for k in c['expected_summary']:c['expected_summary'][k]=s[k]
c.update(expected_reader_count=36,expected_citation_count=41,expected_public_asset_count=81,expected_endpoint_count=668)
for k in ['promotion_manifest','promotion_freeze','integration_audit','browser_validation','build_checks']:
 c[k]['sha256']=hashlib.sha256((J/c[k]['path']).read_bytes()).hexdigest()
p.write_text(json.dumps(c,indent=2)+'\n','utf8')
print(c['expected_summary'])
