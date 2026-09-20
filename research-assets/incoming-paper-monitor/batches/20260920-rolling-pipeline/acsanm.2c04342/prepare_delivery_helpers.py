from pathlib import Path
import json
A=Path(__file__).resolve().parent;M=A.parents[4];T=A.parent/'acs.cgd.9b01519'
read=lambda p:json.loads(p.read_text('utf8'))
p=M/'research-assets/verify_public_delivery.py';text=p.read_text('utf8')
assert "data/paper-reviews/matuhina2023.json" not in text
assets=read(A/'site-integration-proposal/v2/promotion-manifest.json')['public_assets']
records=read(A/'canonical-proposal/v1/record-manifest.json')['records']
extra=['data/paper-reviews/matuhina2023.json']+[a['public_path'] for a in assets]
extra += [prefix+r['record_id']+suffix for r in records for prefix,suffix in [('records/','.html'),('data/records/','.json')]]
assert len(extra)==len(set(extra))
text=text.replace('assert len(paths)==len(set(paths))',"if (D/'data/paper-reviews/matuhina2023.json').exists():\n paths += "+repr(extra)+"\nassert len(paths)==len(set(paths))")
text=text.replace('withheld_checks=[',"if (D/'data/paper-reviews/matuhina2023.json').exists():withheld += ['assets/figures/matuhina2023/pages/main-01.png','assets/figures/matuhina2023/pages/si-01.png']\nwithheld_checks=[")
p.write_text(text,'utf8')
text=(T/'sync_release_delta.py').read_text('utf8').replace("L.parent/'acsanm.2c04342'","L.parent/'acs.cgd.9b01519'").replace('sommer-release-scope-20260920.json','matuhina-review-scope-20260920.json')
(A/'sync_release_delta.py').write_text(text,'utf8')
count=94+len(extra)
text=(T/'finalize_reader_publication.py').read_text('utf8').replace('sommer2020','matuhina2023').replace('0.29.0','0.30.0').replace('==37','==38').replace('==94',f'=={count}').replace('==12','==14')
# Retain all previous withheld checks and add the new source.
text=text.replace("'ghosh2012','matuhina2023']", "'ghosh2012','sommer2020','matuhina2023']")
(A/'finalize_reader_publication.py').write_text(text,'utf8')
text=(T/'prepare_publication_rule.py').read_text('utf8').replace('sommer2020','matuhina2023').replace('0.29.0','0.30.0').replace('37citations,94allowlisted',f'38citations,{count}allowlisted').replace(' Declared SI remains locally unlocated and unverified.',' Complete supplied main and matched SI reviewed; source conflicts remain explicit.')
(A/'prepare_publication_rule.py').write_text(text,'utf8')
print(json.dumps({'endpoint_count':count,'new_endpoints':len(extra),'science_not_published':True}))
