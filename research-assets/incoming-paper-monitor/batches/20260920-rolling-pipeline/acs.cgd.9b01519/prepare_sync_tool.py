from pathlib import Path
N=Path(__file__).resolve().parent
t=(N.parent/'ja212032q/sync_release_delta.py').read_text('utf8')
t=t.replace("'research-assets/incoming-paper-monitor/deadline-20260920/admission-20260920T095744Z/scope-partition.json','research-assets/incoming-paper-monitor/deadline-20260920/ghosh-release-scope-20260920.json'","'research-assets/incoming-paper-monitor/deadline-20260920/active-cutoff.json'")
t=t.replace("folders=[L,L.parent/'acs.cgd.9b01519',L.parent/'intake-20260920T095744Z',", "folders=[L,L.parent/'acsanm.2c04342',L.parent/'intake-20260920T111852Z',MON/'deadline-20260920/admission-20260920T111852Z',")
t=t.replace("'research-assets/verify_public_delivery.py',","'research-assets/verify_public_delivery.py','research-assets/incoming-paper-monitor/deadline-20260920/sommer-release-scope-20260920.json',")
(N/'sync_release_delta.py').write_text(t,'utf8')
print('Prepared policy-filtered, bounded project sync; no copy or push yet.')
