"""Record the author's completed actual image inspection, not a scientific audit."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
O=Path(__file__).resolve().parent;P=O.parents[1]
assert not(O/'package-freeze.json').exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
files=[p for d in ['previews','stock-previews','conformer-previews']for p in sorted((O/d).glob('*.png'))]
assert len(files)==37
report={'schema':'mattersyn-author-visual-inspection/1','author':'/root/peng1998_reader_assets','created_at':datetime.now(timezone.utc).isoformat(),'status':'passed_author_visual_review','actual_scope':{'identity_previews':28,'stock_previews':7,'unchanged_conformer_previews':2,'total_previews':37,'source_pages_visually_reopened':[2,7,8],'source_text_pages_read':[2,7,8]},'method':'Actual image-tool viewing of six contact sheets containing all 28 identity and seven stock cards; improved final Al nitrate card and corrected NaOH stock were separately reopened at full size. Final Zn nitrate was viewed in its contact sheet. Both conformer projections were separately viewed at full size. The source images for main pages 2, 7 and 8 were actually reopened.','observations':[
'The initial automatic disconnected-hydrate drawings were crowded. Both final hydrate cards use readable coefficients, an explicit cation, one large nitrate group and the stated hydrate-water count. The full stoichiometric fragments remain in their 2D JSON.',
'Zn2+ + 2 nitrate + 6 water and Al3+ + 3 nitrate + 9 water are explicitly disconnected formula references. No metal-ligand bonds or hydration shells are depicted.',
'NaOH is separate Na+ and OH-; nitrate displays a conventional resonance form. The drawing does not turn the source PDF correlation into a measured molecular bond length.',
'Water-grade cards and 96% versus 99% ethanol remain visibly distinct. Free-water/ethanol conformer projections are labeled illustrative and their unchanged arrays are checked separately.',
'The revised NaOH-stock card carries only the delivered 1.00 mL aliquot and explicitly separates the mixed-reaction nitrate aliquot and Zn/Al concentrations.',
'The laboratory stock distinguishes 20 mL charged water from the in situ stock 30.0 mL solution volume. Alternative laboratory base formulations visibly retain inheritance and missing charge amounts.',
'Purchased ZnO powder, reaction-generated ZnO, Al(OH)3 starting solid, AlOOH impurity and ZnAl2O4 family have separate symbolic labels; no product sample or atomic structure is claimed.',
'The proposed zinc aquo entities and aluminum dimer are symbolic and state unresolved protonation/hydration/association. No exact complex is reconstructed.',
'Calibration standards and capillary/grid/vessel supports are symbolic. No unreported composition, phase, surface or polymer geometry is inferred.',
'All reviewed identity and stock cards are readable with no visible text clipping or overlap. The two static coordinate projections have visible atom labels and bonds.'
],'reviewed_previews':{str(p.relative_to(O)):sha(p)for p in files},'source_images':{str(P/'source-render'/f'main-{n:02}.png'):sha(P/'source-render'/f'main-{n:02}.png')for n in [2,7,8]},'not_claimed':['Independent scientific audit','Mounted browser testing','Source full-paper re-extraction','Product atomic structure or training approval','Publication approval']}
(O/'author-visual-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'status':report['status'],'previews':len(files)}))
