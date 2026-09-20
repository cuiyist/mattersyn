from pathlib import Path
import json,hashlib
from datetime import datetime,timezone
A=Path(__file__).resolve().parent;G=A.parent
def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
freeze=load(G/'package-freeze.json');checks=load(A/'mechanical-checks-v1.json')
assert freeze['revision']==1 and not checks['failed']
findings=[
 {'id':'GHOSH-SOURCE-01','status':'open','severity':'bounded_locator','object':'ghosh2012-no-added-amine','finding':'The containing fact cites main p.6 for both precipitation and faceting; the >6 ML faceting statement is in main p.4 Table2 row6. The typed quantity already correctly cites p.4. Add the p.4 locator at fact level and propagate derived references. No value correction.'},
 {'id':'GHOSH-SOURCE-02','status':'open','severity':'bounded_scientific_wording','objects':['ghosh2012-lifetime-detection','equation-average-main'],'finding':'The expression sum(A*tau^2)/sum(A*tau) is labelled amplitude-weighted average lifetime. The conventional amplitude-weighted average is sum(A*tau)/sum(A). Preserve the printed expression and use neutral source wording: reported average lifetime computed from amplitude and lifetime coefficients. No formula/value correction.'},
 {'id':'GHOSH-SOURCE-03','status':'open','severity':'bounded_crop_padding','objects':['figure-1','figure-s4'],'finding':'Right crop boundary crowds/cuts the final 1300 and 90 tick glyphs. Independent enlarged source margins establish the full glyphs. Add a small right margin using the same original PDFium renderer; preserve all other crop bounds/content.'}
]
scopes=[
 'Independently read all 10 main and 9 SI pages as native text and viewed every native page before author-facts comparison; checkpoint and independent table readings were saved first.',
 'Verified matching main/SI title/byline, DOI, source generation 2 and all four incoming/legacy original copies. No added documents or citations treated as fully read.',
 'Read all 71 fact claims/194 typed quantities, 25 materials, 3 stocks and all 15 protocol scopes/33 operations. Distinct core branches and missing upstream stock procedures retained.',
 'Checked optimized 1 h post-S/2.5 h post-Cd schedule versus five separate comparison schedules; first 5–8 cycles and evolving 1:4/1:10 Cd:OA remain uncertain exact switch.',
 'Checked 1%/10% withdrawals as solution fractions with unchanged subsequent planned precursor doses, not direct molar precursor excess. Constant-sulfur route and extreme dilution remain separate comparisons.',
 'Checked all five table contexts/44 rows/272 cells: all 180 SI S1 numeric tokens, 25 main Table1 values, 36 Table2 cells, 20 Table3 cells and 11 OA reference cells. No source numeric discrepancy.',
 'Compared all 10 original-image table cells to their source rows; 10 nm bars retained. Table3 moderately thick-shell TEM is not certified as the same specimen/thickness as >15 ML QY.',
 'Read all 81 source contexts with physical_sample_identity_verified=false. No fabricated batch identity or joins between 16.9 ML SI S7/S8 and 15.57 ML TableS1.',
 'Read all 13 figures including graphical abstract, one scheme, six equations and 23 numbered references/24 works. All 36 selected crops actually viewed, not inferred from author contact sheets.',
 'Independent PDFium replay of each selected crop reproduced exact pixels from retained original PDFs; two tight right margins still require source-faithful padding. Native caption resolves dioctylamine spelling; true NH2/oleylamine versus secondary-amine conflict retained.',
 'Checked extraction distinguishes semiquantitative WZ:ZB weight ratios from refined coordinates and conceptual ligand/dipole/termination models from measurements. No CIF/atomistic pair/training approval.',
 'Checked >99% versus >=99%, approximate 750 nm^3 and 65 ns trends/3 nm exception, fitted/rounded SI amplitudes and unavailable raw trajectory/fit data. No recalculated means substituted.',
 'Confirmed C1–C6 and G1–G8 preserve missingness, source discrepancies, source-citation limits and incomplete practical SOP details.'
]
bound=dict(freeze['bound_files']);bound[str(G/'package-freeze.json')]=sha(G/'package-freeze.json')
for p in A.iterdir():
 if p.is_file() and p.name not in ['independent-audit-v1.json','independent-audit-v1.md']:bound[str(p)]=sha(p)
r={'schema':'mattersyn-independent-source-audit/1','source_id':'ghosh2012','doi':'10.1021/ja212032q','created_at':datetime.now(timezone.utc).isoformat(),'reviewer':'/root/norberg2004_extract','extraction_author':'/root/backlog_eta','status':'open_findings','source_package_revision':1,'proposal_freeze_sha256':sha(G/'package-freeze.json'),'source_facts_sha256':sha(G/'source-facts.json'),'source_tables_sha256':sha(G/'source-tables.json'),'scope':'Full supplied main and SI scientific extraction, numerical table and selected-crop audit; canonical, training, molecule, apparatus, site/browser/publication excluded.','checked_counts':freeze['counts'],'mechanical_check_count':len(checks['checks']),'mechanical_failed_count':0,'manual_scopes':scopes,'findings':findings,'open_findings':findings,'unread_supplied_pages':[],'bound_files':bound,'approval_limits':{'canonical':False,'training':False,'exact_structure_recipe_pair':False,'molecular_reference':False,'apparatus':False,'site_browser':False,'publication':False},'audit_helper_notes':['Initial crop replay used PyMuPDF, producing expected renderer differences; final pixel test used documented PDFium independently. No source-fidelity finding was inferred from cross-renderer pixel differences.','Independent source transcription normalizes line-break hyphenation and nu/delta notation only for comparison; raw author values and source originals retained.']}
(A/'independent-audit-v1.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(A/'independent-audit-v1.md').write_text('# Ghosh 2012 independent source audit — revision 1\n\nStatus: three bounded findings remain. All 19 supplied pages and 36 selected crops were independently read/viewed; all 272 table cells agree with the original source. '+str(len(checks['checks']))+' independent consistency checks pass.\n\n'+ '\n'.join('- '+v['id']+': '+v['finding'] for v in findings)+'\n\n'+ '\n'.join('- '+s for s in scopes)+'\n\nThis source audit does not approve canonical records, training, exact atomic structure pairs, rendered apparatus/molecules, browser integration or publication.\n',encoding='utf-8')
print(sha(A/'independent-audit-v1.json'))
