"""Selected original evidence; never a whole-paper coverage claim."""
from pathlib import Path
import json,hashlib
import pypdfium2 as pdfium
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SITE=ROOT/'recipe-atlas'
PAPERS=ROOT/'downloaded_papers'
def build(sid,doi,items,intuition):
    out=SITE/'dist/assets/selected-evidence'/sid;out.mkdir(parents=True,exist_ok=True)
    figs=[]
    for name,role,page,box,label,summary,scope in items:
        file=PAPERS/(doi.replace('/','_')+('_si_1' if role=='si' else '')+'.pdf')
        doc=pdfium.PdfDocument(file);img=doc[page-1].render(scale=3).to_pil();w,h=img.size
        pixels=tuple(round(v*(w if i%2==0 else h)) for i,v in enumerate(box));asset=out/(name+'.png');img.crop(pixels).save(asset)
        figs.append({'id':name,'label':label,'document_role':role,'page':page,'summary':summary,'sample_assignments':scope,'public_asset':asset.relative_to(SITE/'dist').as_posix(),'public_asset_sha256':hashlib.sha256(asset.read_bytes()).hexdigest(),'source_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'source_file':file.name,'crop_normalized':box,'render_scale':3,'raw_data_digitized':False,'eligible_training':False})
    record={'paper_id':sid,'doi':doi,'coverage_status':'selected_figures_only','eligible_training':False,'scope':'Selected source pages and figures visually inspected for the existing recipe. This is not full main/SI review. Related variants remain distinct.','figures':figs,'chemical_intuition':intuition}
    dest=SITE/'dist/data/recipe-figures'/(sid+'.json');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    (HERE/(sid+'.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
build('tessier2015','10.1021/acs.chemmater.5b02138',[
('figure-1','main',2,(.512,.576,.903,.94),'Figure 1','InP and InP/ZnS, InP/ZnSe: original absorption/PL and TEM; scale bars 20 nm.','Panel c and the middle absorption trace concern the InP core; b and d concern core/shell particles. Main p.4894 assigns the displayed InP characterization to a 20-minute reaction, while Reference 1 preparation runs for 30 minutes. The core/shell PL quantum yields are not assigned to the bare-core record.'),
('figure-s3','si',8,(.25,.10,.76,.37),'Figure S3','InP size histogram for a first-exciton absorption peak at 570 nm; displayed mean 3.24 nm.','Spectral/size context from SI p.8. The histogram is not asserted to be the exact 30-minute recipe specimen.'),
('figure-s4','si',9,(.08,.14,.88,.70),'Figure S4','XRD for InP, InP/ZnSe and InP/ZnS, with separate bulk-reference reflections and reported peak positions.','Panel a concerns InP. Panels b and c concern shell-grown products. The bulk-reference reflections are comparison references, not atom-resolved measurements of these nanocrystals.')
],[{'claim':'The primary amine supplies solvent/ligand functions. The authors use ZnCl2 to facilitate later shell growth and report reduced size dispersion; this does not prove that every InP core is a homogeneous In(Zn)P alloy.','type':'authors interpretation','locator':'Main p.4894, Results and Discussion'},{'claim':'The authors motivate aminophosphine precursors through cost and handling considerations and prefer tris(diethylamino)phosphine partly because its boiling point exceeds the 180 °C reaction temperature.','type':'authors rationale','locator':'Main pp.4893–4894'}])
build('zhang2019','10.1021/acs.chemmater.9b03529',[
('table-1','main',3,(.093,.084,.905,.208),'Table 1','Ligand formulations, colloidal stability, reported size, PL peak, width, PLQY and lifetime parameters.','Use only the TDPA row for the TDPA-only formulation. Other rows are comparison formulations; size is not relabeled diameter.'),
('figure-1','main',3,(.093,.212,.904,.535),'Figure 1','Original TEM comparison, DLS distributions, representative XRD and absorption/PL.','Panel d is TDPA-only TEM. Panel e includes the blue TDPA DLS trace; this is solvated hydrodynamic size. Panels f and g are the TDPA–ODPA 3:1 representative sample, not the TDPA-only record.'),
('figure-s2','si',3,(.117,.095,.883,.407),'Figure S2','Original absorption/PL and XRD for three ligand formulations.','Panels c and f explicitly identify TDPA-only; a/d and b/e are distinct mixed-ligand formulations. Bulk bars are ICSD 98751.'),
('figure-s3','si',4,(.132,.09,.855,.533),'Figure S3','Time-resolved PL decays and author fits for four plotted ligand formulations.','Plot d is labeled TDPA; plot c is TDPA:ODPA=3:1. The caption incorrectly calls TDPA panel c and omits the fourth panel. Preserve the plot/caption discrepancy.'),
('table-s1','si',4,(.111,.669,.875,.802),'Table S1','Reported multi-exponential lifetime fits and fractional amplitudes.','TDPA-only: tau1 4.3 ns (99.1%), tau2 23.8 ns (0.9%). These are fitted components, not two independent sample lifetimes or a calculated ensemble mean.'),
('figure-s9','si',9,(.11,.088,.876,.357),'Figure S9','FTIR of free TDPA and TDPA-only CsPbBr3 nanocrystals.','The authors interpret changes in P–OH/P=O bands and the new P–OM band as evidence of surface phosphonate binding. This is a binding interpretation; it does not uniquely reconstruct every ligand site.')
],[{'claim':'Heating to 220 °C was reported as necessary for complete precursor solubilization before benzoyl bromide injection at 160 °C.','type':'authors rationale','locator':'Main p.9142, Synthesis and Structural Characterization'},{'claim':'The authors link ligand chain length and phosphonic-acid combinations to colloidal stability. The TDPA-only formulation must remain separate from mixed-ligand samples.','type':'authors interpretation','locator':'Main p.9142 and Table 1'},{'claim':'FTIR changes are interpreted as phosphonate coordination to the nanocrystal surface, including a P–OM band at 1157 cm−1. Cited mechanistic references were not independently read for this extraction.','type':'authors interpretation','locator':'SI p.S9, Figure S9'}])
print('Built 9 original selected-evidence images with specimen scope and source hashes.')
