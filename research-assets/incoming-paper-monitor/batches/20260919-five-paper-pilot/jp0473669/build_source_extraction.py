"""Source-bound Ribeiro 2004 extraction. No publication or training admission."""
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
import pypdfium2 as pdfium

P = Path(__file__).resolve().parent
SID = "ribeiro2004"
SHA = "fc10a7101b4acb74f15398a530b8f916641f89b171fad065dd789747204eee88"
manifest = json.loads((P / "intake-manifest.json").read_bytes())
for document in manifest["documents"]:
    assert hashlib.sha256(Path(document["path"]).read_bytes()).hexdigest() == SHA
source = Path(manifest["documents"][0]["path"])
now = dt.datetime.now(dt.timezone.utc).isoformat()

def save(name, value):
    (P / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def ev(page, section):
    return {"source_id": SID + "-main", "source_sha256": SHA, "pdf_page": page,
            "printed_page": 15611 + page, "section": section}

facts = []
def f(key, page, section, scope, prop, value, unit=None, status="reported", qualifier="", approximate=False):
    facts.append({"id": SID + "-fact-" + key, "sample_scope": scope, "property": prop,
                  "value": value, "unit": unit, "status": status, "approximate": approximate,
                  "qualifier": qualifier, "evidence": [ev(page, section)], "eligible_training": False})

f("sn-precursor",2,"Experimental Procedure","all concentration-series syntheses","precursor identity","SnCl2·2H2O; tin(II) chloride dihydrate; Mallinckrodt")
f("solvent",2,"Experimental Procedure","all concentration-series syntheses","solvent identity","absolute ethanol; Merck")
f("temperature",2,"Experimental Procedure","hydrolysis","reaction temperature","room temperature",status="reported_qualitative",qualifier="No numerical temperature or controlled atmosphere is specified.")
f("concentration-range",2,"Experimental Procedure","initial ethanolic Sn(II) precursor solution","Sn2+ concentration range",[0.0025,0.1],"mol/L",qualifier="Range, not a fully enumerated list of experiments. Not final aqueous SnO2 concentration.")
f("water-ratio",3,"3.1 discussion of hydrolysis","hydrolysis reaction","water/Sn2+ ratio",[500,1],"ratio; basis unreported",approximate=True,qualifier="Reported in Results, not the brief experimental paragraph; no water dose, addition order/rate or ratio basis supplied. Do not silently convert this to a batch recipe.")
f("white-product",2,"Experimental Procedure","immediately after hydrolysis","appearance","white turbid suspension")
f("dialysis-water",2,"Experimental Procedure","hydrolysis suspension purification","operation","dialysis in deionized water to cleanse chloride ions",qualifier="Membrane, exchanges, water volumes, duration and endpoint test unreported.")
f("final-dispersion",2,"Experimental Procedure","after dialysis","appearance and state","clear colloidal suspension of nanocrystalline tin dioxide")
f("final-ph",2,"Experimental Procedure","as-prepared colloidal suspension","pH",8.5,approximate=True)
f("stability",2,"Experimental Procedure","as-prepared colloidal suspensions","observed absence of agglomeration",12,"months; up to",qualifier="Observation on aged samples, not an instructed synthesis hold or guaranteed shelf life; storage conditions absent.")
f("phase",2,"Experimental Procedure","final product, general synthesis series","XRD phase assignment","cassiterite SnO2",qualifier="XRD result stated in prose; no original XRD trace, acquisition parameters, refined coordinates or CIF supplied in this main paper.")
f("parent-ph-series",2,"Experimental Procedure","parent synthesis for pH/agglomeration experiments","initial Sn2+ precursor concentration",0.025,"mol/L",qualifier="Initial ethanolic concentration; no measured final colloidal concentration stated.")
f("acid",2,"Experimental Procedure","pH modification","reagent","dilute nitric acid; Synth",qualifier="No acid concentration, volume or addition rate reported.")
f("ph-range",2,"Experimental Procedure","separate modified-pH samples","reported pH range",[1.5,8.5],qualifier="Starting pH approximately8.5 is lowered with nitric acid. Range does not enumerate every dose or every independent batch.")
f("age-before-redispersion",2,"Experimental Procedure","modified-pH samples","interval before redispersion",24,"h",qualifier="Reported 'After24h'; no explicit hold-temperature or atmosphere specified.")
f("tbaoh",2,"Experimental Procedure","redispersion for spectroscopic measurement","surfactant identity","tetrabutylammonium hydroxide; J. T. Baker")
f("tbaoh-stock",2,"Experimental Procedure","commercial redispersion reagent","stock concentration",0.4,"mol/L",qualifier="Aqueous stock; dose and final pH after adding the base are unreported. Do not equate treatment pH with final measurement pH.")
f("sonicate",2,"Experimental Procedure","redispersed modified-pH optical samples","ultrasonic probe treatment duration",2,"min",qualifier="Power, probe geometry and final volume unreported.")
f("tem-instrument",2,"Experimental Procedure","TEM characterization","microscope","Philips CM200")
f("tem-voltage",2,"Experimental Procedure","TEM characterization","accelerating voltage",200,"kV")
f("tem-n",2,"Experimental Procedure","each reported size distribution as method scope","particles measured",200,"particles; at least",qualifier="Particle count lower bound, not synthesis replicates.")
f("grid",2,"Experimental Procedure","TEM specimen preparation","substrate","carbon-coated copper grid")
f("grid-drop",2,"Experimental Procedure","TEM specimen preparation","wetting","one drop of colloidal suspension",qualifier="Drop volume unreported. TBAOH/probe treatment explicitly described for spectroscopy; not automatically assigned to every TEM specimen.")
f("grid-wet-duration",2,"Experimental Procedure","TEM specimen preparation","grid wetting duration",20,"s")
f("grid-dry",2,"Experimental Procedure","TEM specimen preparation","drying","in air",qualifier="No drying duration or numerical temperature given; this is specimen preparation, not isolation of the entire batch as powder.")
f("zeta-instrument",2,"Experimental Procedure","0.025M-origin suspension","zeta-potential instrument","Brookhaven Instruments Zetaplus")
f("pl-instrument",2,"Experimental Procedure","PL acquisition","instrument","Jobin-Yvon Fluorolog FL3-12; Xe-lamp excitation; photomultiplier-tube detector")
f("pl-excitation",2,"Experimental Procedure","PL acquisition","excitation wavelength",250,"nm")
f("pl-range",2,"Experimental Procedure","PL acquisition","collected emission interval",[250,400],"nm",qualifier="Figure1b displayed axis starts near280nm; display interval differs from acquisition interval.")
f("uv-instrument",2,"Experimental Procedure","UV-vis acquisition","instrument","Perkin-Elmer; model unreported")
f("uv-range",2,"Experimental Procedure","UV-vis acquisition","wavelength interval",[220,360],"nm",qualifier="Figure1a displayed interval is narrower; no path length or dilution specified.")
f("optical-state",2,"Experimental Procedure","all optical measurements","specimen and temperature","colloidal suspensions at room temperature")
f("bulk-gap",2,"3.1 effective-mass analysis","bulk SnO2 reference","band gap",3.6,"eV",status="cited_reference",approximate=True,qualifier="Reference constant used in authors' analysis, not the measured gap of each nanoparticle sample.")
f("bohr-radius",3,"3.1 effective-mass discussion","SnO2 reference/model","exciton Bohr radius",2.7,"nm",status="cited_reference",approximate=True)
f("gap-radius-model",2,"Equation1","authors' optical-size analysis","effective-mass equation","E_g^eff = E_g + hbar^2*pi^2/(2*mu*R^2)",status="author_model",qualifier="R is radius, mu effective reduced mass. No numerical mu supplied here. Absorption-onset and emission-peak estimates remain distinct; no reconstructed radii generated.")
f("optical-trend",2,"Figure1 and Section3.1","initial-concentration series","optical trend","higher initial Sn2+ concentrations shift absorption and PL toward longer wavelengths",status="reported_qualitative",qualifier="No per-curve numerical peak table or full concentration legend. Original normalized plots retained; no invented exact peak positions.")
f("abs-pl-gap",3,"3.1 optical-size analysis","two optical analysis methods","gap comparison","absorption-onset inferred gaps exceed emission-derived gaps",status="reported_qualitative")
f("pl-preference",3,"3.1 optical-size analysis","authors' interpretation","preferred size estimate","authors consider PL-derived radii more reliable using prior Lee et al. ref28 calibration",status="author_interpretation",qualifier="Not a new calibration or independently verified equivalence of PL and TEM specimens in this paper.")
f("density",3,"Equation2 discussion","cassiterite reference","density",7.02,"g/cm^3",status="cited_reference")
f("critical-radius",3,"Equation2","classical nucleus model","critical radius","R_c = 2*M*gamma_bar/[R*T*rho*ln(a/a0)]",status="author_model",qualifier="Here R is gas constant, unlike radius R in Equation1; M molecular weight, gamma_bar interface energy perarea, rho density. Activity ratio approximated by concentration ratio/S; no numerical nucleation calculation supplied.")
f("monitor-low",3,"3.1 nucleation discussion","0.0025M-origin suspension","absorbance monitoring interval",2,"h; up to",qualifier="Absorbance changes only slightly from initial stages. An observation window, not an instructed synthesis reaction time.")
f("nucleation-fast",3,"3.1 nucleation discussion","authors' kinetic interpretation","nucleation/growth timing","very fast; most supersaturation-driven nucleation/growth occurs in early reaction stages",status="author_interpretation",qualifier="No numerical nucleation duration measured.")
f("supersaturation-assumptions",3,"3.1 after Equation2","authors' nucleation model","supersaturation and mean nucleus size assumptions","Authors infer that all studied concentrations exceed saturation because precipitation occurs. They assume that rapid nucleation makes S independent of concentration in dilute suspensions, and consequently the mean nucleus size is concentration-independent; final particle-size differences are attributed to growth/coarsening.",status="author_interpretation",qualifier="These are the authors' explicit assumptions and deductions, not measured saturation concentrations or validated nucleation kinetics. S denotes their supersaturation ratio.")
f("intermediate",3,"3.1 growth mechanism","authors' proposed pathway","intermediate","Sn(OH)4 formed by hydrolysis and SnO2 formed by polycondensation",status="author_interpretation",qualifier="Not an independently isolated precursor stock or measured speciation. SnII-to-SnIV redox details are not specified by this paper.")
f("dilute-model",3,"3.1 growth/coarsening discussion","dilute suspensions","growth interpretation","polycondensation growth dominates; low SnO2 solubility and reduced collisions disfavor Ostwald ripening and oriented attachment",status="author_interpretation",qualifier="Author assumptions and mechanistic reasoning, not direct kinetic rate measurements.")
f("number-equation",3,"Equation3","authors' particle-number estimate","equation","N = c*M/(rho*alpha*R_p^3)",status="author_model",qualifier="c initial concentration, R_p particle radius; alpha=4*pi/3 for sphere. Numberperliter inferred, not directly counted; concentration/density/radius units require consistent conversion.")
f("number-linear-scope",4,"Equation4 discussion","particle number estimated from optical radii","range of approximately linear behavior",0.04,"mol/L; below",status="author_derived",qualifier="Deviations at higher concentration are attributed to coarsening; do not extrapolate the fitted equation to all concentrations.")
f("number-fit-intercept",4,"Equation4","PL-derived linear number estimate","intercept",2.16e18,"particles/L implied by preceding text",status="author_derived",qualifier="Printed uncertainty ±0.14e18; original equation retained.")
f("number-fit-slope",4,"Equation4","PL-derived linear number estimate","slope",1.15e20,"coefficient multiplying c in mol/L",status="author_derived",qualifier="Printed uncertainty ±0.07e20; c basis must be retained. N=(2.16±0.14)*10^18+(1.15±0.07)*10^20*c.")
f("oa-scheme",3,"Figure3","conceptual collision model","oriented attachment","incompatible faces do not coalesce; compatible collisions can form perfect or imperfect attachments with defects",status="author_model",qualifier="Cartoon is a mechanism schematic, not TEM or a measured structural configuration.")
f("hrtem-concentrations",4,"Figure4 caption","Figure4a versus4b","initial precursor concentrations",[0.1,0.0025],"mol/L",qualifier="Panel a=0.1M, b=0.0025M. Nearby prose mistakenly references Figure3a/b; preserve caption/actual Figure4 association and disclose typo.")
f("hrtem-scale",4,"Figure4 panels","both HRTEM images","scale bars",4,"nm",qualifier="Scale-bar length, not nanoparticle size or lattice spacing.")
f("hrtem-defects",4,"Figure4 caption and discussion","concentration comparison","microstructural observation","coalesced particles and imperfect attachment defects including dislocations and twin boundaries; more frequent in0.1M than0.0025M",status="reported_qualitative",qualifier="No defect-density table, lattice-spacing labels or atomic-coordinate refinement supplied.")
f("tem-histogram-cohorts",4,"Figure5","three TEM size distributions","initial precursor concentrations",[0.0025,0.005,0.025],"mol/L",qualifier="Horizontal axis says Particle radius(nm), despite generic size language in caption. No tabulated fitted mean, width or raw particle measurements.")
f("tem-histogram-trend",4,"Figure5 and discussion","concentration-series TEM","trend","higher concentration broadens radius distribution and shifts average toward larger radius",status="reported_qualitative",qualifier="Preserve original histograms; no numerical fit coefficients read off as exact values.")
f("isoelectric",5,"Figure6a and Section3.2","0.025M-origin colloids","estimated isoelectric point",3.1,"pH",approximate=True,qualifier="Not the initial synthesis pH; electrokinetic result from pH-dependent zeta potential.")
f("ph-growth",5,"Figure6b and Section3.2","modified-pH optical samples","trend","growth/coarsening near isoelectric conditions; very acidic treatment produces large additional growth",status="reported_qualitative",qualifier="Figure6b ordinate says Size(nm), but caption explicitly says particle radius calculated from PL. Preserve radius interpretation with labeling caveat, not a measured TEM diameter.")
f("ph-hrtem",5,"Figure7 caption","0.025M-origin samples in Figure7","treatment pH by panel",[6.0,2.7],qualifier="a=6.0, b=2.7. No explicit post-redispersion measurement pH is supplied.")
f("ph-hrtem-scale",5,"Figure7","both panels","scale bars",4,"nm",qualifier="Image scale bars, not an assigned sample size.")
f("ph-hrtem-observation",5,"Figure7 and discussion","pH2.7 compared to6.0","morphology","pH2.7 agglomerated sample has larger irregular particles and imperfect attachment-like defects; pH6.0 resembles original0.025M suspension",status="reported_qualitative")
f("ph-mechanism",5,"Section3.2 discussion","authors' agglomeration mechanism","interpretation","aggregation increases collisions and allows relative rotation, crystallographic alignment and coalescence",status="author_interpretation")
f("summary-mechanism",6,"conclusion continuation","study-wide interpretation","mechanistic summary","concentration changes growth by supersaturation-related processes; agglomeration promotes coarsening",status="author_interpretation",qualifier="Conclusion uses ion-deposition language while p3 specifically proposes polycondensation; retain both rather than claiming direct observation of a unique microscopic pathway.")
f("prior-range",1,"Introduction, refs7/25","cited earlier Leite route","reported prior size range",[2,6],"nm",status="cited_prior_work",qualifier="Prior nearly spherical cassiterite particles, not this paper's per-variant measured size range; radius/diameter wording only says sizes.")

materials = [
 {"id":"sncl2-dihydrate","name":"Tin(II) chloride dihydrate","formula":"SnCl2·2H2O","role":"precursor","supplier":"Mallinckrodt","amount_status":"absolute charge unreported","evidence":[ev(2,"Experimental Procedure")]},
 {"id":"ethanol","name":"Absolute ethanol","formula":"C2H6O","role":"synthesis solvent","supplier":"Merck","amount_status":"volume unreported","evidence":[ev(2,"Experimental Procedure")]},
 {"id":"hydrolysis-water","name":"Water for hydrolysis","formula":"H2O","role":"hydrolysis reagent","amount_status":"approximately500:1 water/Sn2+ ratio, unspecified basis; actual dose/order absent","evidence":[ev(3,"3.1 water/Sn2+ statement")]},
 {"id":"dialysis-water","name":"Deionized water","formula":"H2O","role":"dialysis medium","amount_status":"volume/exchange schedule unreported","evidence":[ev(2,"Experimental Procedure")]},
 {"id":"nitric-acid","name":"Dilute nitric acid","formula":"HNO3","role":"pH adjustment","supplier":"Synth","amount_status":"dose/concentration unreported","evidence":[ev(2,"Experimental Procedure")]},
 {"id":"tbaoh-aqueous","name":"Tetrabutylammonium hydroxide aqueous solution","formula":"[N(C4H9)4]+ OH- in H2O","role":"redispersion reagent, called surfactant by authors","supplier":"J.T.Baker","stock_concentration":{"value":0.4,"unit":"mol/L"},"amount_status":"addition volume/final pH unreported","evidence":[ev(2,"Experimental Procedure")]},
 {"id":"carbon-copper-grid","name":"Carbon-coated copper grid","formula":"C coating on Cu","role":"TEM substrate","evidence":[ev(2,"Experimental Procedure")]},
 {"id":"sno2-colloid","name":"Cassiterite tin dioxide colloid","formula":"SnO2","role":"product suspension","evidence":[ev(2,"Experimental Procedure")]},
 {"id":"sn-hydroxide-model","name":"Tin(IV) hydroxide, authors' proposed intermediate","formula":"Sn(OH)4","role":"mechanistic intermediate, not an isolated reagent","evidence":[ev(3,"3.1 polycondensation discussion")]}
]
protocols = [
 {"id":SID+"-hydrolysis","kind":"synthesis_variant_family","method":"Controlled hydrolysis","scope":"Initial ethanolic Sn2+ concentration0.0025–0.1M; explicit image/histogram cohorts0.0025,0.005,0.025,0.1M, without a fully enumerated set of batch recipes","steps":[
  {"id":"dissolve","operation":"dissolve","inputs":["sncl2-dihydrate","ethanol"],"description":"Prepare the reported initial ethanolic tin(II) precursor concentration; absolute charges and volumes absent.","evidence":[ev(2,"Experimental Procedure")]},
  {"id":"hydrolyze","operation":"hydrolysis","inputs":["hydrolysis-water"],"description":"Hydrolysis at room temperature yields white turbid suspension. Water/Sn2+ approximately500:1 is mentioned in Results; basis, dosing sequence, mixing and numerical time absent.","evidence":[ev(2,"Experimental Procedure"),ev(3,"3.1 hydrolysis discussion")]},
  {"id":"dialyze","operation":"dialysis","inputs":["dialysis-water"],"description":"Dialysis in deionized water removes chloride ions and yields clear colloid, pHapproximately8.5; retain nanoparticles. No full membrane/exchange schedule or chloride endpoint test.","evidence":[ev(2,"Experimental Procedure")]}
 ],"product":"sno2-colloid","upstream_references":[7,25],"completeness":"partial; main paper explicitly delegates fuller preparation to refs7/25"},
 {"id":SID+"-ph-treatment","kind":"post_synthesis_variant_family","method":"Acid-induced agglomeration and redispersion","parent":SID+"-hydrolysis","parent_constraint":"initial Sn2+0.025M","steps":[
  {"id":"acidify","operation":"pH adjustment","inputs":["nitric-acid"],"description":"Lower starting pHapproximately8.5 to a range of values down to1.5; specific HRTEM treatment states6.0 and2.7.","evidence":[ev(2,"Experimental Procedure"),ev(5,"Figure7")]},
  {"id":"age","operation":"hold","description":"After24h, proceed to redispersion. Temperature and atmosphere unreported.","evidence":[ev(2,"Experimental Procedure")]},
  {"id":"redisperse","operation":"add surfactant","inputs":["tbaoh-aqueous"],"description":"Add0.4M aqueous tetrabutylammonium hydroxide for redispersion before spectroscopy; unknown dose and final pH.","evidence":[ev(2,"Experimental Procedure")]},
  {"id":"sonicate","operation":"probe sonication","description":"Ultrasonic probe for2min for spectroscopic measurements; no power/geometry given.","evidence":[ev(2,"Experimental Procedure")]}
 ],"completeness":"partial; treatment and measurement states must remain distinct"},
 {"id":SID+"-tem-preparation","kind":"characterization_preparation","method":"Drop preparation on microscopy grid","steps":[
  {"id":"wet-grid","operation":"deposit droplet","inputs":["carbon-copper-grid"],"description":"Wet carbon-coated copper grid with one colloid drop for20s.","evidence":[ev(2,"Experimental Procedure")]},
  {"id":"air-dry","operation":"dry","description":"Dry in air; unspecified time. Do not use this as a bulk-powder workup.","evidence":[ev(2,"Experimental Procedure")]}
 ],"completeness":"partial specimen-preparation protocol"}
]
figures = [
 (1,2,"Optical concentration series","Normalized absorption and PL; precursor range0.0025–0.1M, no full numerical curve-to-concentration key.",["properties"]),
 (2,3,"Model-derived radii and particle numbers","a: absorption-onset radii; b: PL-derived radii; insets author-derived particle-number estimates.",["properties","chemical_intuition"]),
 (3,3,"Oriented-attachment mechanism schematic","Conceptual incompatible/compatible collision cartoons, including perfect and imperfect coalescence. Not measured structure.",["chemical_intuition"]),
 (4,4,"HRTEM concentration comparison","a0.1M and b0.0025M;4nm scale bars; defect markings. Prose Figure3 reference is inconsistent with actual Figure4.",["final_structures"]),
 (5,4,"TEM radius distributions","Histograms at0.025,0.005,0.0025M; horizontal axis is radius, not diameter. No raw table or fit parameters supplied.",["final_structures"]),
 (6,5,"pH-dependent electrokinetic and optical behavior","a zeta potential with isoelectric pH3.1; b PL-derived particle radius, ordinate generically Size; inset PL. Original treatment pH differs from unreported post-base measurement pH.",["properties","chemical_intuition"]),
 (7,5,"HRTEM agglomeration comparison","0.025M-origin colloids, a pH6.0 and b pH2.7;4nm scale bars. Treatment state assigned; exact final pH not supplied.",["final_structures"])
]
boxes = {
 "figure-1":(2,(495,66,936,785)), "figure-2":(3,(77,69,480,714)),
 "figure-3":(3,(497,67,930,359)), "figure-4":(4,(78,66,478,934)),
 "figure-5":(4,(498,68,893,532)), "figure-6":(5,(76,66,475,755)),
 "figure-7":(5,(498,66,934,927)), "equation-1":(2,(520,1040,926,1100)),
 "equation-2":(3,(107,1099,478,1190)), "equation-3":(3,(645,1150,926,1214)),
 "equation-4":(4,(99,1107,478,1140)), "experimental-procedure":(2,(78,110,480,948)),
 "water-ratio-context":(3,(497,374,929,846)), "references":(6,(78,225,480,530)),
 "references-continuation":(6,(498,65,931,530))
}
assets = []
(P/"reader-assets").mkdir(exist_ok=True)
pdf = pdfium.PdfDocument(str(source))
for name, (page, box) in boxes.items():
    p = pdf[page-1]
    image = p.render(scale=3).to_pil()
    actual_box = tuple(round(v * (image.width/978 if i%2==0 else image.height/1265)) for i,v in enumerate(box))
    out = P/"reader-assets"/(name+".png")
    image.crop(actual_box).save(out)
    assets.append({"id":SID+"-"+name,"filename":str(out.relative_to(P)),"sha256":hashlib.sha256(out.read_bytes()).hexdigest(),"source_sha256":SHA,"pdf_page":page,"printed_page":15611+page,"crop_reference_pixels":{"width":978,"height":1265,"box":list(box)},"status":"original source region rendered and cropped; not recreated or digitized"})
    p.close()
pdf.close()

refs_text=(P/"main-06.txt").read_text(encoding="utf-8").split("References and Notes",1)[1]
references=[]
for num, body in re.findall(r"\((\d+)\)\s*(.*?)(?=\(\d+\)|Study of Synthesis Variables|\Z)",refs_text,re.S):
    references.append({"number":int(num),"raw_bibliographic_text":" ".join(body.split()),"source_access":"citation in supplied main only; external full text not inspected here","evidence":[ev(6,"References and Notes")]})
assert len(references)==31
gaps=[
 "Main-only review; matched SI not located/verified and existence remains unverified. No SI supplied or inferred absent.",
 "Refs7/25 contain fuller upstream synthesis; their full procedures have not been inspected in this extraction. No external downloads performed.",
 "Absolute precursor and ethanol/water charges, water-ratio basis/order/rate, mixing, vessel, atmosphere, hydrolysis duration and oxidation conditions absent.",
 "Dialysis membrane, water volume/exchange schedule, duration and chloride-removal endpoint absent.",
 "Acid concentration/dose, TBAOH addition volume, post-redispersion pH, sonication power and final colloid concentration absent.",
 "No numerical full spectral curves, tabulated peak/radius values, histogram particle list, or uncertainties for optical-derived radii. Original plots retained without invented digitization.",
 "Cassiterite assignment is source-reported XRD prose; no XRD trace or SAED pattern supplied. No unit-cell constants, measured atom coordinates, CIF, surface ligands or full-particle atom model supplied.",
 "No powder-isolation protocol, quantitative yield, PL quantum yield/lifetime, Raman data or sensor/device test supplied.",
 "Mechanistic conclusions involve author assumptions, models and cited studies; sample atomistic dynamics and solution oxidation/speciation were not directly measured."
]
conflicts=[
 {"id":"hrtem-reference-typo","description":"Discussion identifies Figure4 HRTEM but parenthetical references say Figure3a/b; actual Figure3 is schematic. Figure4 captions and panels establish the imaging assignment.","evidence":[ev(3,"Figure3"),ev(4,"Figure4 and discussion")]},
 {"id":"radius-size-wording","description":"Figure5 ordinate-independent horizontal variable is particle radius; Figure6b axis says Size but caption says radius from PL. Preserve radius and original labels, never silently use diameter.","evidence":[ev(4,"Figure5"),ev(5,"Figure6b")]},
 {"id":"treatment-measurement-ph","description":"The paper describes acid-set pH, then adds basic TBAOH after24h for spectra without reporting final pH. Treat plotted labels as treatment labels, not verified final measurement pH.","evidence":[ev(2,"Experimental Procedure"),ev(5,"Figure6")]},
 {"id":"growth-language","description":"p3 proposes polycondensation rather than direct ion deposition, while conclusion p6 uses ion-deposition phrasing; these are retained author interpretations, not a resolved measured mechanism.","evidence":[ev(3,"3.1"),ev(6,"conclusion")]}]
coverage={"source_id":SID,"author":"/root","status":"all_supplied_main_pages_text_read_and_visually_inspected; independent audit pending","at":now,"documents":[{"role":"main","sha256":SHA,"page_count":6,"pages":[{"pdf_page":i,"printed_page":15611+i,"text_read":True,"visually_inspected":True} for i in range(1,7)]}],"supporting_information":"not_located_or_verified","raw_plot_digitization":False,"references_full_texts_inspected":False}
inventory={"source_id":SID,"doi":"10.1021/jp0473669","title":"Study of Synthesis Variables in the Nanocrystal Growth Behavior of Tin Oxide Processed by Controlled Hydrolysis","authors":["Caue Ribeiro","Eduardo J.H.Lee","Tania R.Giraldi","Elson Longo","Jose A.Varela","Edson R.Leite"],"journal":"Journal of Physical Chemistry B","year":2004,"volume":108,"issue":40,"pages":"15612–15617","online_publication_date":"2004-09-08","received":"2004-06-17","final_form":"2004-07-28","source_sha256":SHA,"source_scope":"all6 supplied main pages; SI unverified","materials":materials,"protocols":protocols,"figures":[{"id":SID+"-figure-"+str(n),"number":n,"pdf_page":pg,"title":title,"scope":scope,"sections":sections,"disposition":"original asset retained with source-bound interpretation; raw plot numbers not digitized"} for n,pg,title,scope,sections in figures],"tables":[],"schemes":[{"id":SID+"-figure-3","note":"Numbered as Figure3 by source, not a separate extra scheme"}],"equations":[{"number":i,"pdf_page":pg,"asset_id":SID+"-equation-"+str(i),"disposition":"transcribed as author-model equation with original crop"} for i,pg in [(1,2),(2,3),(3,3),(4,4)]],"references":references,"acknowledgment":{"funders":["FAPESP","CNPq"],"evidence":[ev(6,"Acknowledgment")]},"assets":assets,"remaining_gaps":gaps,"evidence_conflicts":conflicts,"source_pages": [{"pdf_page":i,"text_path":f"main-{i:02d}.txt","render_path":f"main-{i}.png","sections":s} for i,s in [(1,["identity","abstract","introduction","cited background"]),(2,["experimental","Figure1","Equation1","optical model"]),(3,["Figure2","Figure3","Equations2/3","hydrolysis-ratio and mechanism discussion"]),(4,["Figure4","Figure5","Equation4","growth/coarsening discussion"]),(5,["Figure6","Figure7","pH and mechanism discussion"]),(6,["conclusion","acknowledgment","31references"])]]}
save("source-facts.json",{"source_id":SID,"source_sha256":SHA,"si_sha256":None,"scope":"Complete supplied main extraction; candidate facts require independent audit and canonical integration; no training admission", "facts":facts})
save("source-inventory.json",inventory)
save("page-coverage.json",coverage)
save("source-extraction-summary.json",{"at":now,"author":"/root","main_pages":6,"si_pages":0,"typed_facts":len(facts),"material_entries":len(materials),"protocol_groups":len(protocols),"operations":sum(len(x["steps"]) for x in protocols),"figures":7,"equations":4,"references":31,"original_assets":len(assets),"independent_audit":"pending","published":False})
(P/"extraction-notes.md").write_text("# Ribeiro2004 complete supplied-main extraction\n\nAll6 main pages were text-read and visually inspected by /root. SI and the fuller cited preparations remain unverified; no downloads. The extraction includes the water/Sn ratio from Results, pH aging/redispersion protocol, all7 original figures,4 equations and31 references.\n\nThe key boundaries are initial precursor concentration versus final colloid concentration; room-temperature qualitative settings versus invented numerical temperatures; radius versus diameter; treatment pH versus unreported post-base pH; optical-model radii versus TEM measurements; and theoretical particle numbers versus directly counted synthesis outcomes. Powder isolation is not supplied. XRD assignment is reported in prose without a supplied trace. No SAED, measured atomic coordinates or structure-recipe pairs are created.\n\nFull independent scientific audit, canonical records, reader sections, molecule/apparatus illustrations, integration and publication remain pending.\n",encoding="utf-8")
print(json.dumps(json.loads((P/"source-extraction-summary.json").read_bytes())))
