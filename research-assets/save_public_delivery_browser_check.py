from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
R=Path(__file__).resolve().parent.parent
D=R.parent/'mattersyn-github-public-clean/mattersyn-site'
out={'checked_at':datetime.now(timezone.utc).isoformat(),'scope':'Actual CUA browser checks of local public projection; no new scientific approval.',
 'base_url':'http://127.0.0.1:5189/mattersyn-site/',
 'progress':{'loaded':True,'records':470,'routes':97,'collections':42,'readers':26,'batch_published':4,'batch_total':5,'target_labeled_unverified':True,'snapshot_generation_time_distinct_from_scan':True,'fixed_cutoff_note_present':True,'console_errors_observed':[]},
 'norberg':{'reader_loaded':True,'complete_source_scope_and_gaps_visible':True,'full_page_asset_links_in_DOM':0,'selected_figure_3_dialog_opened':True,'image_natural_width':803,'image_natural_height':1031,'TEM_XRD_axes_and_scale_bars_visually_checked':True,'console_errors_observed':[]},
 'earlier_same_frontend_mobile_check':{'width':390,'horizontal_overflow':False,'note':'Previous local prefix preview before deadline-text edits; no responsive CSS changed since that check.'},
 'bound_files':{p:hashlib.sha256((D/p).read_bytes()).hexdigest() for p in ['progress.html','progress.mjs','progress.css','data/review-progress.json','data/paper-reviews/norberg2004.json','assets/figures/norberg2004/figure-3.png']}}
(R/'research-assets/github-public-browser-check.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
print('Saved actual browser-check scope and file hashes.')
