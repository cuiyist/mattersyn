# MatterSyn

MatterSyn organizes reviewed synthesis procedures, material characterization and properties with source and sample attribution. The website is a view of the structured records. Reader publication does not imply that a record is eligible for model training or has sample-specific atomic coordinates.

[Open the atlas](https://cuiyist.github.io/mattersyn-site/) · [Synthesis catalogue](https://cuiyist.github.io/mattersyn-site/dataset.html)

Both `cuiyist/mattersyn` and `cuiyist/mattersyn-site` are public at the owner's
request. The project repository contains code, reviewed records, project memory,
reusable skills and cleaned project history; the separate site repository contains
the public atlas. Complete papers and SI, raw extraction caches, detailed private
audits and original history bundles remain in the local research workspace. A
public repository branch does not guarantee that every old GitHub object or cached
URL has been removed; previously cited old raw source content was anonymously
reachable again after the repository was made public on 2026-09-24.

## Scaling workflow

The [adopted workflow](skills/mattersyn-paper-to-site/references/scaling-workflow-v2.md)
separates independently audited **gold**, **calibrated silver**, and an explicitly
unreviewed **experimental silver display**. Calibrated silver still requires
held-out 98% / 95% / 90% field thresholds and independent calibration approval.
Experimental display carries partial machine-extracted evidence with accuracy
unmeasured and training excluded; it earns no complete-paper, complete-recipe,
gold or verified-pair credit. Publication requires the normal evidence, privacy,
build, CI and anonymous-access checks. Output-rate targets are not measured results.

- [Scoped packages and event metrics](tools/workflow/README.md)
- [Local extraction and calibration](tools/silver/README.md)
- [Silver sampling, error monitoring and stop rules](tools/silver/MONITORING.md)
- [Separate silver Reader integration](recipe-atlas/scripts/SILVER_READER.md)
- [Single-commit release preparation](tools/publication/SINGLE_COMMIT_RELEASE.md)

Morning and two-hour reports are disabled; progress is on request while quiet
continuation remains active. Inventory counts and memberships derive from reviewed
inputs at build time. The calibrated silver Reader/monitor remain disabled pending
calibration and admission; the separately labelled experimental display has its own
release path and never changes gold or training eligibility. Batch safe public
postpublication administrative updates with the next ready substantive source
transaction, preserving exact private proof events immediately and running all
fresh checks on the combined payload. No automatic publication or capacity claim
follows from this sequencing change.

## Local workspace organization

Keep the active source and site checkouts together under `repos/mattersyn` and `repos/mattersyn-site` in the existing local MatterSyn workspace. Private research files and temporary builds belong under that workspace's `research-assets`; preserved historical checkouts belong under `archive`. These paths describe the local workspace, not additional folders to upload. Current project memory and skills remain versioned in this source repository. The local WORKSPACE.md contains the historical move map.

## Reproduce a review candidate

Use Python 3.11 or later with the dependencies pinned in [requirements-data.txt](recipe-atlas/requirements-data.txt). No GPU is needed to build the static website. The input snapshot binds reviewed files and record membership. The selected original source figures remain available in the reader at the user's explicit direction, with citations and supported sample attribution; that display choice does not mean publisher permission was verified. Original papers and SI, extracted full text/OCR, page renders and private working crops remain local.

From a clean, committed repository root, first bind the portable blueprint to
the current Git commit. Keep the generated runtime snapshot outside the checkout
so the committed source never contains a reference to its own future commit:

```shell
python recipe-atlas/scripts/make_runtime_snapshot.py --root . --blueprint publication/build-inputs.json --output ../mattersyn-runtime-snapshot.json
```

Use a new output directory:

```shell
python recipe-atlas/scripts/build_release.py --candidate --output ../build-candidate --snapshot ../mattersyn-runtime-snapshot.json --registry publication/asset-rights-registry.json --artifact-transform tools/publication/source_link_artifacts.py
```

The committed publication registry binds reviewed asset hashes and provenance. The hook generates display mappings during the isolated build. The selected original source figures are reader-facing assets under the user's explicit project preference; keep their recorded permission status unresolved unless specific evidence supports a clearance claim. Full papers/SI, extracted text/OCR, page renders and private working crops are not required as public build inputs. The source-link hook also requires its `safe_paths.py` helper. The artifact appears in `build-candidate/project/recipe-atlas/dist`. This command runs scientific/data tests and site validators and emits an **UNAPPROVED** candidate manifest. It does not publish or authorize release. See [the detailed build guide](recipe-atlas/README.md) and [publication controls](PUBLICATION.md).

## Release checks

The candidate must be inspected before preparing its exact output allowlist. A final clean build requires `--gate`, `--policy`, `--allowlist` and `--registry` instead of `--candidate`; publication is a separate action. The final source and artifact gates must reject unlisted files as well as mismatched hashes. Snapshot validation checks listed input hashes; it is not, by itself, an exact directory-membership approval. The final artifact must match the reviewed release snapshot and pass the public content and asset-rights boundary.

Public citations are generated below from the same dataset snapshot used by the website. Earlier operational notes are retained in [CHANGELOG.md](recipe-atlas/CHANGELOG.md).

## Reviewed source scopes and experimental evidence

- Haber, J. A.; Gibbons, P. C.; Buhro, W. E. (1997). *Morphological Control of Nanocrystalline Aluminum Nitride: Aluminum Chloride-Assisted Nanowhisker Growth*. [DOI 10.1021/ja963368y](https://doi.org/10.1021/ja963368y). Both supplied main pages independently audited through R3; fourteen source-scoped records, thirteen preparation views and two source figures. Nitrogen admission at 1 atm before heating is distinct from unreported hot pressure. SI and cited full texts unreviewed; presentation refinements pending.

- Qiu et al. (2006). *Silver nanocrystal superlattices: Self-assembly and optical emission*. [DOI 10.1063/1.2192645](https://doi.org/10.1063/1.2192645). All four supplied pages, including cover and three main article pages, independently audited; one synthesis record and three source figures. SI and cited full texts unreviewed; presentation refinements pending.

- Li, B.; Xie, Y.; Liu, Y.; Huang, J.; Qian, Y. (2001). *Sonochemical Synthesis of Nanocrystalline Silver Tellurides Ag2Te and Ag7Te4*. Journal of Solid State Chemistry 158,260–263. [DOI 10.1006/jssc.2001.9103](https://doi.org/10.1006/jssc.2001.9103). Experimental partial display of eight reagent-amount fields from two method excerpts. Not a full-paper scientific review or complete recipe–structure pair; accuracy unmeasured and training excluded.

- Lu et al. (1999). *A Low Temperature Nitridation Route for Nanocrystalline AlN*. [DOI 10.1246/cl.1999.1239](https://doi.org/10.1246/cl.1999.1239). Both supplied main pages independently audited; four recipe/outcome variants, twelve measurements and four source figures. SI and cited methods unreviewed; visual refinements pending.

- Jinke Tang; Kai-Ying Wang; Weilie Zhou (2001). *Magnetic properties of nanocrystalline Fe3O4 films*. [DOI 10.1063/1.1358350](https://doi.org/10.1063/1.1358350). Four supplied PDF pages, including the publisher cover and three article pages, independently source-audited; SI and cited references remain unreviewed.
- Qingyi Lu; Junqing Hu; Kaibin Tang; Yitai Qian; Guien Zhou; Xianming Liu (1999). *The Solvothermal Synthesis for Nanocrystalline FeIn2S4 at Low Temperature*. [DOI 10.1246/cl.1999.481](https://doi.org/10.1246/cl.1999.481). All 2 supplied main pages independently source-audited; SI and cited references remain unreviewed.

Experimental silver only: Wang, L.-Z.; Shi, J.-L.; Zhang, W.-H.; Ruan, M.-L.; Yu, J.; Yan, D.-S. Chem. Mater. 1999, 11, 3015–3017. *Self-Organization of Ordered Silver Nanocrystal Arrays on Cubic Mesoporous Silica Surfaces*. [DOI 10.1021/cm990228p](https://doi.org/10.1021/cm990228p). Partial Ag/MCM-48 evidence from three supplied main-text pages; not independently scientifically reviewed, completeness unassessed, accuracy unmeasured, figures/SI unreviewed and training excluded. Engineering/privacy review passed; this partial evidence adds no reviewed-paper, complete-recipe or verified-pair credit.

<!-- mattersyn-generated-references:start -->
## Papers used in the published website

Dataset **0.41.2** · **72 primary source groups** · release `mattersyn-gold-yang2005-20260928`. Records are not independent experiments.

- Haiming Zhu; Nianhui Song; William Rodríguez-Córdoba; Tianquan Lian (year unrecorded). Wave Function Engineering for Efficient Extraction of up to Nineteen Electrons from One CdSe/CdS Quasi-Type II Quantum Dot — supporting information. *Journal of the American Chemical Society*. [10.1021/ja210312s](https://doi.org/10.1021/ja210312s). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=zhu2012-ja210312s-si).

- K. A. Littau; P. J. Szajowski; A. J. Muller; A. R. Kortan; L. E. Brus (1993). A Luminescent Silicon Nanocrystal Colloid via a High-Temperature Aerosol Reaction. *The Journal of Physical Chemistry*, 97, 1224–1230. [10.1021/j100108a019](https://doi.org/10.1021/j100108a019). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=littau1993).

- C. B. Murray; D. J. Norris; M. G. Bawendi (1993). Synthesis and Characterization of Nearly Monodisperse CdE (E = S, Se, Te) Semiconductor Nanocrystallites. [10.1021/ja00072a025](https://doi.org/10.1021/ja00072a025). Review scope remains stated in the linked website records.

- Yanchun Zhou; Richard J. Phillips; Jay A. Switzer (1995). Electrochemical Synthesis and Sintering of Nanocrystalline Cerium(IV) Oxide Powders. *Journal of the American Ceramic Society*, 78, 981–985. [10.1111/j.1151-2916.1995.tb08425.x](https://doi.org/10.1111/j.1151-2916.1995.tb08425.x). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=zhou1995-ceo2-tb08425).

- J. R. Heath; R. S. Williams; J. J. Shiang; S. J. Wind; J. Chu; C. D’Emic; W. Chen; C. L. Stanis; J. J. Bucchignano (1996). Spatially Confined Chemistry: Fabrication of Ge Quantum Dot Arrays. *The Journal of Physical Chemistry*, 100, 3144–3149. [10.1021/jp951903v](https://doi.org/10.1021/jp951903v). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=heath1996).

- Michal Danek; Klavs F. Jensen; Chris B. Murray; Moungi G. Bawendi (1996). Synthesis of Luminescent Thin-Film CdSe/ZnSe Quantum Dot Composites Using CdSe Quantum Dots Passivated with an Overlayer of ZnSe. *Chemistry of Materials*, 8, 173–180. [10.1021/cm9503137](https://doi.org/10.1021/cm9503137). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=danek1996).

- B. O. Dabbousi; J. Rodriguez-Viejo; F. V. Mikulec; J. R. Heine; H. Mattoussi; R. Ober; K. F. Jensen; M. G. Bawendi (1997). (CdSe)ZnS Core–Shell Quantum Dots: Synthesis and Characterization of a Size Series of Highly Luminescent Nanocrystallites. *The Journal of Physical Chemistry B*, 101, 9463–9475. [10.1021/jp971091y](https://doi.org/10.1021/jp971091y). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=dabbousi1997).

- Jonathan G. C. Veinot; Madlen Ginzburg; William J. Pietro (1997). Surface Functionalization of Cadmium Sulfide Quantum-Confined Nanoclusters. 3. Formation and Derivatives of a Surface Phenolic Quantum Dot. *Chemistry of Materials*, 9, 2117–2122. [10.1021/cm970189m](https://doi.org/10.1021/cm970189m). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=veinot1997).

- Shu-Hong Yu; Yong-Sheng Wu; Jian Yang; Zhao-Hui Han; Yi Xie; Yi-Tai Qian; Xian-Ming Liu (1998). A Novel Solventothermal Synthetic Route to Nanocrystalline CdE (E = S, Se, Te) and Morphological Control. *Chemistry of Materials*, 10, 2309–2312. [10.1021/cm980181s](https://doi.org/10.1021/cm980181s). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=yu1998cde).

- Hiroshi Yao; Yukako Takada; Noboru Kitamura (1998). Electrolyte Effects on CdS Nanocrystal Formation in Chelate Polymer Particles: Optical and Distribution Properties. *Langmuir*, 14, 595–601. [10.1021/la970480g](https://doi.org/10.1021/la970480g). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=yao1998).

- Xiaogang Peng; J. Wickham; A. P. Alivisatos (1998). Kinetics of II-VI and III-V Colloidal Semiconductor Nanocrystal Growth: “Focusing” of Size Distributions. *Journal of the American Chemical Society*, 120, 5343–5344. [10.1021/ja9805425](https://doi.org/10.1021/ja9805425). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=peng1998).

- Yadong Li; Xiangfeng Duan; Hongwei Liao; Yitai Qian (1998). Self-Regulation Synthesis of Nanocrystalline ZnGa2O4 by Hydrothermal Reaction. *Chemistry of Materials*, 10, 17–18. [10.1021/cm970557m](https://doi.org/10.1021/cm970557m). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=li1998znga2o4).

- Paul Wagner; Osamu Terasaki; Stephan Ritsch; Jose Geraldo Nery; Stacey I. Zones; Mark E. Davis; Kenji Hiraga (1999). Electron Diffraction Structure Solution of a Nanocrystalline Zeolite at Atomic Resolution. *The Journal of Physical Chemistry B*, 103, 8245-8250. [10.1021/jp991389j](https://doi.org/10.1021/jp991389j). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=wagner1999-ssz48).

- J. H. Zhan; Y. Xie; X. G. Yang; W. X. Zhang; Y. T. Qian (1999). Hydrazine-Assisted Low-Temperature Hydrothermal Preparation of Nanocrystalline Jaipurite. [10.1006/jssc.1999.8299](https://doi.org/10.1006/jssc.1999.8299). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=zhan1999jaipurite).

- R. M. Stiger; S. Gorer; B. Craft; R. M. Penner (1999). Investigations of Electrochemical Silver Nanocrystal Growth on Hydrogen-Terminated Silicon(100). *Langmuir*, 15, 790–798. [10.1021/la980800b](https://doi.org/10.1021/la980800b). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=stiger1999).

- X. Peng; L. Manna; W. Yang; J. Wickham; E. Scher; A. Kadavanich; A. P. Alivisatos (2000). Shape control of CdSe nanocrystals. [10.1038/35003535](https://doi.org/10.1038/35003535). Review scope remains stated in the linked website records.

- Bin Li, Yi Xie, Jiaxing Huang, and Yitai Qian (2000). Synthesis, Characterization, and Properties of Nanocrystalline Cu2SnS3. [10.1006/jssc.2000.8772](https://doi.org/10.1006/jssc.2000.8772). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=li2000cu2sns3).

- Parag S. Shah; Shabbir Husain; Keith P. Johnston; Brian A. Korgel (2001). Nanocrystal Arrested Precipitation in Supercritical Carbon Dioxide. *Journal of Physical Chemistry B*, 105, 9433–9440. [10.1021/jp011815c](https://doi.org/10.1021/jp011815c). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=shah2001).

- Daniele Gerion; Fabien Pinaud; Shara C. Williams; Wolfgang J. Parak; Daniela Zanchet; Shimon Weiss; A. Paul Alivisatos (2001). Synthesis and Properties of Biocompatible Water-Soluble Silica-Coated CdSe/ZnS Semiconductor Quantum Dots. *Journal of Physical Chemistry B*, 105, 8861–8871. [10.1021/jp0105488](https://doi.org/10.1021/jp0105488). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=gerion2001).

- Markus Braun; Clemens Burda; Mostafa A. El-Sayed (2001). Variation of the Thickness and Number of Wells in the CdS/HgS/CdS Quantum Dot Quantum Well System. *Journal of Physical Chemistry A*, 105, 5548–5551. [10.1021/jp010002l](https://doi.org/10.1021/jp010002l). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=braun2001).

- Sophie Besson; Thierry Gacoin; Christian Ricolleau; Catherine Jacquiod; Jean-Pierre Boilot (2002). 3D Quantum Dot Lattice Inside Mesoporous Silica Films. *Nano Letters*, 2, 409–414. [10.1021/nl015685v](https://doi.org/10.1021/nl015685v). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=besson2002).

- Noelio Oliveira Dantas; Fanyao Qu; R. S. Silva; Paulo César Morais (2002). Anti-Stokes Photoluminescence in Nanocrystal Quantum Dots. *Journal of Physical Chemistry B*, 106, 7453–7457. [10.1021/jp0208743](https://doi.org/10.1021/jp0208743). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=dantas2002).

- Brian L. Wehrenberg; Congjun Wang; Philippe Guyot-Sionnest (2002). Interband and Intraband Optical Studies of PbSe Colloidal Quantum Dots. *Journal of Physical Chemistry B*, 106, 10634–10640. [10.1021/jp021187e](https://doi.org/10.1021/jp021187e). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=wehrenberg2002-jp021187e).

- Guangshun Yi; Baoquan Sun; Fengzhen Yang; Depu Chen; Yuxiang Zhou; Jing Cheng (2002). Synthesis and Characterization of High-Efficiency Nanocrystal Up-Conversion Phosphors: Ytterbium and Erbium Codoped Lanthanum Molybdate. *Chemistry of Materials*, 14, 2910–2914. [10.1021/cm0115416](https://doi.org/10.1021/cm0115416). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=yi2002).

- Sarbajit Banerjee; Stanislaus S. Wong (2003). In Situ Quantum Dot Growth on Multiwalled Carbon Nanotubes. *Journal of the American Chemical Society*, 125, 10342–10350. [10.1021/ja035980c](https://doi.org/10.1021/ja035980c). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=banerjee2003).

- Dana A. Schwartz; Nick S. Norberg; Quyen P. Nguyen; Jason M. Parker; Daniel R. Gamelin (2003). Magnetic Quantum Dots: Synthesis, Spectroscopy, and Magnetism of Co2+- and Ni2+-Doped ZnO Nanocrystals. *Journal of the American Chemical Society*, 125, 13205–13218. [10.1021/ja036811v](https://doi.org/10.1021/ja036811v). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=schwartz2003).

- Nam Ho Heo; Jong Sam Park; Young Joo Kim; Woo Taik Lim; Sung Wook Jung; Karl Seff (2003). Spatially Ordered Quantum Dot Array of Indium Nanoclusters in Fully Indium-Exchanged Zeolite X. *Journal of Physical Chemistry B*, 107, 1120–1128. [10.1021/jp0219348](https://doi.org/10.1021/jp0219348). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=heo2003).

- Hongwei Gu; Rongkun Zheng; XiXiang Zhang; Bing Xu (2004). Facile One-Pot Synthesis of Bifunctional Heterodimers of Nanoparticles: A Conjugate of Quantum Dot and Magnetic Nanoparticles. *Journal of the American Chemical Society*, 126, 5664–5665. [10.1021/ja0496423](https://doi.org/10.1021/ja0496423). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=gu2004).

- Yukio Nagasaki; Takehiko Ishii; Yuka Sunaga; Yousuke Watanabe; Hidenori Otsuka; Kazunori Kataoka (2004). Novel Molecular Recognition via Fluorescent Resonance Energy Transfer Using a Biotin-PEG/Polyamine Stabilized CdS Quantum Dot. *Langmuir*, 20, 6396-6400. [10.1021/la036034c](https://doi.org/10.1021/la036034c). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=nagasaki2004).

- A. Sashchiuk; L. Amirav; M. Bashouti; M. Krueger; U. Sivan; E. Lifshitz (2004). PbSe Nanocrystal Assemblies: Synthesis and Structural, Optical, and Electrical Characterization. *Nano Letters*, 4, 159–165. [10.1021/nl0345116](https://doi.org/10.1021/nl0345116). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=sashchiuk2004).

- Caue Ribeiro; Eduardo J.H.Lee; Tania R.Giraldi; Elson Longo; Jose A.Varela; Edson R.Leite (2004). Study of Synthesis Variables in the Nanocrystal Growth Behavior of Tin Oxide Processed by Controlled Hydrolysis. *Journal of Physical Chemistry B*, 108, 15612–15617. [10.1021/jp0473669](https://doi.org/10.1021/jp0473669). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=ribeiro2004).

- Nick S. Norberg; Kevin R. Kittilstved; James E. Amonette; Ravi K. Kukkadapu; Dana A. Schwartz; Daniel R. Gamelin (2004). Synthesis of Colloidal Mn2+:ZnO Quantum Dots and High-TC Ferromagnetic Nanocrystalline Thin Films. *Journal of the American Chemical Society*, 126, 9387–9398. [10.1021/ja048427j](https://doi.org/10.1021/ja048427j). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=norberg2004).

- Cynthia A. Stowell and Brian A. Korgel (2005). Iridium Nanocrystal Synthesis and Surface Coating-Dependent Catalytic Activity. *Nano Letters*, 5, 1203–1207. [10.1021/nl050648f](https://doi.org/10.1021/nl050648f). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=stowell2005).

- Ali Ghezelbash; Brian A. Korgel (2005). Nickel Sulfide and Copper Sulfide Nanocrystal Synthesis and Polymorphism. [10.1021/la051196p](https://doi.org/10.1021/la051196p). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=ghezelbash2005-main).

- Yongan Andrew Yang; Huimeng Wu; Kathryn R. Williams; Y. Charles Cao (2005). Synthesis of CdSe and CdTe Nanocrystals without Precursor Injection. *Angewandte Chemie International Edition*, 44, 6712–6715. [10.1002/anie.200502279](https://doi.org/10.1002/anie.200502279). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=yang2005-anie200502279).

- Einat Tirosh; Gabriel Shemer; Gil Markovich (2006). Optimizing Cobalt Ferrite Nanocrystal Synthesis Using a Magneto-optical Probe. *Chemistry of Materials*, 18, 465–470. [10.1021/cm052401p](https://doi.org/10.1021/cm052401p). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=tirosh2006).

- Ying-Song Fu; Xi-Wen Du; Sergei A. Kulinich; Jian-Sheng Qiu; Wen-Jing Qin; Rui Li; Jing Sun; Jim Liu (2007). Stable Aqueous Dispersion of ZnO Quantum Dots with Strong Blue Emission via Simple Solution Route. [10.1021/ja075604i](https://doi.org/10.1021/ja075604i). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=fu2007).

- Yue Wu, Cyrus Wadia, Wanli Ma, Bryce Sadtler, A. Paul Alivisatos (2008). Synthesis and Photovoltaic Application of Copper(I) Sulfide Nanocrystals. [10.1021/nl801817d](https://doi.org/10.1021/nl801817d). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=wu2008).

- Minjie Li; Jianying Ouyang; Christopher I. Ratcliffe; Laetitia Pietri; Xiaohua Wu; Donald M. Leek; Igor Moudrakovski; Quan Lin; Bai Yang; Kui Yu (2009). CdS Magic-Sized Nanocrystals Exhibiting Bright Band Gap Photoemission via Thermodynamically Driven Formation. *ACS Nano*, 3, 3832–3838. [10.1021/nn9009455](https://doi.org/10.1021/nn9009455). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=li2009-nn9009455).

- Ranjan K. Pati; Ivan C. Lee; Karen J. Gaskell; Sheryl H. Ehrman (2009). Precipitation of Nanocrystalline CeO2 Using Triethanolamine. *Langmuir*, 25, 67–70. [10.1021/la8031286](https://doi.org/10.1021/la8031286). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=pati2009).

- Shi Hu; Xun Wang (2010). Fullerene-like Colloidal Nanocrystal of Nickel Hydroxychloride. *Journal of the American Chemical Society*, 132, 9573–9575. [10.1021/ja103607q](https://doi.org/10.1021/ja103607q). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=hu2010nichydroxychloride).

- Christopher M. Evans; Meagan E. Evans; Todd D. Krauss (2010). Mysteries of TOPSe Revealed: Insights into Quantum Dot Nucleation. *Journal of the American Chemical Society*, 132, 10973–10975. [10.1021/ja103805s](https://doi.org/10.1021/ja103805s). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=evans2010).

- Jordan W. Thomson; Ludovico Cademartiri; Mark MacDonald; Srebri Petrov; Gianluca Calestani; Peng Zhang; Geoffrey A. Ozin (2010). Ultrathin Bi2S3 Nanowires: Surface and Core Structure at the Cluster-Nanocrystal Transition. [10.1021/ja101908k](https://doi.org/10.1021/ja101908k). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=thomson2010ja101908k).

- Ming Li; Qiaoyi Wang; Xiaodong Shi; Lawrence A. Hornak; Nianqiang Wu (2011). Detection of Mercury(II) by Quantum Dot/DNA/Gold Nanoparticle Ensemble Based Nanosensor Via Nanometal Surface Energy Transfer. *Analytical Chemistry*, 83, 7061–7065. [10.1021/ac2019014](https://doi.org/10.1021/ac2019014). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=li2011-ac2019014).

- Jonghun Lee; Sunghwan Lee; Guanglai Li; Melissa A. Petruska; David C. Paine; Shouheng Sun (2012). A Facile Solution-Phase Approach to Transparent and Conducting ITO Nanocrystal Assemblies. *Journal of the American Chemical Society*, 134, 13410–13414. [10.1021/ja3044807](https://doi.org/10.1021/ja3044807). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=lee2012-ja3044807).

- Amber Nagy; Andrea Steinbrück; Jun Gao; Norman Doggett; Jennifer A. Hollingsworth; Rashi Iyer (2012). Comprehensive Analysis of the Effects of CdSe Quantum Dot Size, Surface Charge, and Functionalization on Primary Human Lung Cells. *ACS Nano*, 6, 4748–4762. [10.1021/nn204886b](https://doi.org/10.1021/nn204886b). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=nagy2012nn204886b).

- Weiwei Zheng; Kedar Singh; Zhenxing Wang; Joshua T. Wright; Johan van Tol; Naresh S. Dalal; Robert W. Meulenberg; Geoffrey F. Strouse (2012). Evidence of a ZnCr2Se4 Spinel Inclusion at the Core of a Cr-Doped ZnSe Quantum Dot. *Journal of the American Chemical Society*, 134, 5577–5585. [10.1021/ja210285p](https://doi.org/10.1021/ja210285p). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=zheng2012-ja210285p).

- Yagnaseni Ghosh; Benjamin D. Mangum; Joanna L. Casson; Darrick J. Williams; Han Htoon; Jennifer A. Hollingsworth (2012). New Insights into the Complexities of Shell Growth and the Strong Influence of Particle Volume in Nonblinking “Giant” Core/Shell Nanocrystal Quantum Dots. *Journal of the American Chemical Society*, 134, 9634–9643. [10.1021/ja212032q](https://doi.org/10.1021/ja212032q). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=ghosh2012).

- Dylan C. Gary; Benjamin A. Glassy; Brandi M. Cossairt (2014). Investigation of Indium Phosphide Quantum Dot Nucleation and Growth Utilizing Triarylsilylphosphine Precursors. *Chemistry of Materials*, 26, 1734-1744. [10.1021/cm500102q](https://doi.org/10.1021/cm500102q). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=gary-cossairt-2014).

- Karthik Ramasamy; Hunter Sims; William H. Butler; Arunava Gupta (2014). Selective Nanocrystal Synthesis and Calculated Electronic Structure of All Four Phases of Copper-Antimony-Sulfide. [10.1021/cm5005642](https://doi.org/10.1021/cm5005642). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=ramasamy2014cusb).

- Mickael D. Tessier, Dorian Dupont, Kim De Nolf, Jonathan De Roo, Zeger Hens (2015). Economic and Size-Tunable Synthesis of InP/ZnE (E = S, Se) Colloidal Quantum Dots. [10.1021/acs.chemmater.5b02138](https://doi.org/10.1021/acs.chemmater.5b02138). Review scope remains stated in the linked website records.

- Xudong Yao; Shangjing Liu; Yajing Chang; Guopeng Li; Longfei Mi; Xiaoming Wang; Yang Jiang (2015). PbS Quantum-Dot Depleted Heterojunction Solar Cells Employing CdS Nanorod Arrays as the Electron Acceptor with Enhanced Efficiency. *ACS Applied Materials & Interfaces*, 7, 23117–23123. [10.1021/acsami.5b06857](https://doi.org/10.1021/acsami.5b06857). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=yao2015acsami).

- S. Costanzo; G. Simon; J. Richardi; Ph. Colomban; I. Lisiecki (2016). Solvent Effects on Cobalt Nanocrystal Synthesis—A Facile Strategy To Control the Size of Co Nanocrystals. [10.1021/acs.jpcc.6b07293](https://doi.org/10.1021/acs.jpcc.6b07293). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=costanzo2016co).

- Calynn E. Morrison; Fudong Wang; Nigam P. Rath; Brian M. Wieliczka; Richard A. Loomis; William E. Buhro (2017). Cadmium Bis(phenyldithiocarbamate) as a Nanocrystal Shell-Growth Precursor. *Inorganic Chemistry*, 56, 12920–12929. [10.1021/acs.inorgchem.7b01711](https://doi.org/10.1021/acs.inorgchem.7b01711). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=morrison2017).

- Igor Nakonechnyi; Michael Sluydts; Yolanda Justo; Jacek Jasieniak; Zeger Hens (2017). Mechanistic Insights in Seeded Growth Synthesis of Colloidal Core/Shell Quantum Dots. *Chemistry of Materials*, 29, 4719-4727. [10.1021/acs.chemmater.7b00354](https://doi.org/10.1021/acs.chemmater.7b00354). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=nakonechnyi2017).

- Ya-Meng Chen; Yang Zhou; Qing Zhao; Jun-Ying Zhang; Ju-Ping Ma; Tong-Tong Xuan; Shao-Qiang Guo; Zi-Jun Yong; Jing Wang; Yoshihiro Kuroiwa; Chikako Moriyoshi; Hong-Tao Sun (2018). Cs4PbBr6/CsPbBr3 Perovskite Composites with Near-Unity Luminescence Quantum Yield: Large-Scale Synthesis, Luminescence and Formation Mechanism, and White Light-Emitting Diode Application. *ACS Applied Materials & Interfaces*, 10, 15905-15912. [10.1021/acsami.8b04556](https://doi.org/10.1021/acsami.8b04556). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=chen2018ami).

- Baowei Zhang, Luca Goldoni, Juliette Zito, Zhiya Dang, Guilherme Almeida, Francesco Zaccaria, Jur de Wit, Ivan Infante, Luca De Trizio, Liberato Manna (2019). Alkyl Phosphonic Acids Deliver CsPbBr3 Nanocrystals with High Photoluminescence Quantum Yield and Truncated Octahedron Shape. [10.1021/acs.chemmater.9b03529](https://doi.org/10.1021/acs.chemmater.9b03529). Review scope remains stated in the linked website records.

- Artur Feld; Agnes Weimer; Andreas Kornowski; Naomi Winckelmans; Jan-Philip Merkl; Hauke Kloust; Robert Zierold; Christian Schmidtke; Theo Schotten; Maria Riedner; Sara Bals; Horst Weller (2019). Chemistry of Shape-Controlled Iron Oxide Nanocrystal Formation. [10.1021/acsnano.8b05032](https://doi.org/10.1021/acsnano.8b05032). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=feld2019).

- Max R. Friedfeld; Dane A. Johnson; Brandi M. Cossairt (2019). Conversion of InP Clusters to Quantum Dots. *Inorganic Chemistry*, 58, 803–810. [10.1021/acs.inorgchem.8b02945](https://doi.org/10.1021/acs.inorgchem.8b02945). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=friedfeld2019).

- Avijit Saha; Siddhartha Sohoni; Ranjani Viswanatha (2019). Interface Modeling Leading to Giant Exchange Bias from the CoO/CoFe2O4 Quantum Dot Heterostructure. *Journal of Physical Chemistry C*, 123, 2421–2427. [10.1021/acs.jpcc.8b11124](https://doi.org/10.1021/acs.jpcc.8b11124). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=saha2019).

- Voznyy, O.; Levina, L.; Fan, J. Z.; et al. (2019). Machine Learning Accelerates Discovery of Optimal Colloidal Quantum Dot Synthesis. [10.1021/acsnano.9b03864](https://doi.org/10.1021/acsnano.9b03864). Review scope remains stated in the linked website records.

- Sanna Sommer; Espen D. Bøjesen; Hazel Reardon; Bo B. Iversen (2020). Atomic Scale Design of Spinel ZnAl2O4 Nanocrystal Synthesis. *Crystal Growth & Design*, 20, 1789–1799. [10.1021/acs.cgd.9b01519](https://doi.org/10.1021/acs.cgd.9b01519). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=sommer2020).

- Siddhant Basel; Karishma Bhardwaj; Sajan Pradhan; Anand Pariyar; Sudarsan Tamang (2020). DBU-Catalyzed One-Pot Synthesis of Nearly Any Metal Salt of Fatty Acid (M-FA): A Library of Metal Precursors to Semiconductor Nanocrystal Synthesis. *ACS Omega*, 5, 6666–6675. [10.1021/acsomega.9b04448](https://doi.org/10.1021/acsomega.9b04448). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=basel2020).

- Yanyan Li; Parth Vashishtha; Zhicong Zhou; Zhi Li; Sunil B. Shivarudraiah; Chao Ma; Junkai Liu; Kam Sing Wong; Haibin Su; Jonathan E. Halpert (2020). Room Temperature Synthesis of Stable, Printable Cs3Cu2X5 (X = I, Br/I, Br, Br/Cl, Cl) Colloidal Nanocrystals with Near-Unity Quantum Yield Green Emitters (X = Cl). [10.1021/acs.chemmater.0c00280](https://doi.org/10.1021/acs.chemmater.0c00280). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=li2020cs3cu2x5).

- Linyuan Lian; Peng Zhang; Xiuwen Zhang; Qi Ye; Wei Qi; Long Zhao; Jianbo Gao; Daoli Zhang; Jianbing Zhang (2021). Realizing Near-Unity Quantum Efficiency of Zero-Dimensional Antimony Halides through Metal Halide Structural Modulation. *ACS Applied Materials & Interfaces*, 13, 58908–58915. [10.1021/acsami.1c18038](https://doi.org/10.1021/acsami.1c18038). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=lian2021).

- E. M. Williamson; B. A. Tappan; L. Mora-Tamez; G. Barim; R. L. Brutchey (2021). Statistical Multiobjective Optimization of Thiospinel CoNi2S4 Nanocrystal Synthesis via Design of Experiments. *ACS Nano*, 15, 9422–9433. [10.1021/acsnano.1c00502](https://doi.org/10.1021/acsnano.1c00502). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=williamson2021).

- Evert Dhaene; Rohan Pokratath; Olivia Aalling-Frederiksen; Kirsten M. Ø. Jensen; Philippe F. Smet; Klaartje De Buysser; Jonathan De Roo (2022). Monoalkyl Phosphinic Acids as Ligands in Nanocrystal Synthesis. *ACS Nano*, 16, 7361-7372. [10.1021/acsnano.1c08966](https://doi.org/10.1021/acsnano.1c08966). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=dhaene2022-main).

- Anastasia Matuhina; G. Krishnamurthy Grandhi; Fang Pan; Maning Liu; Harri Ali-Löytty; Hussein M. Ayedh; Antti Tukiainen; Jan-Henrik Smått; Ville Vähänissi; Hele Savin; Jingrui Li; Patrick Rinke; Paola Vivo (2023). Role of CsMnCl3 Nanocrystal Structure on Its Luminescence Properties. *ACS Applied Nano Materials*, 6, 953–965. [10.1021/acsanm.2c04342](https://doi.org/10.1021/acsanm.2c04342). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=matuhina2023).

- Surendra Saini; Pratibha Saini; Krishan Kumar; Mukul Sethi; Priyanka Meena; Aditya Gurjar; Anshu Dandia; Tanya Dhuria; Vijay Parewa (2023). Unlocking the Molecular Behavior of Natural Amine-Targeted Carbon Quantum Dots for the Synthesis of Diverse Pharmacophore Scaffolds via an Unusual Nanoaminocatalytic Route. *ACS Applied Materials & Interfaces*, 15, 49083–49094. [10.1021/acsami.3c08812](https://doi.org/10.1021/acsami.3c08812). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=saini2023).

- Xuerong Song; Yue Qin; Qian Wang; Jiajia Ning (2024). Alloyed Zinc Chalcogenide Magic-Sized Nanoclusters and Their Transformation to Alloyed Quantum Dots. *Inorganic Chemistry*, 63, 17100–17107. [10.1021/acs.inorgchem.4c02738](https://doi.org/10.1021/acs.inorgchem.4c02738). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=song2024zincchalcogenide).

- Nurwarrohman Andre Sasongko; Safira Arta Paramita; Jaeseong Heo; Eugene Park; Sebastian E. Reyes-Lillo; Joonkyung Jang; Myeongkee Park (2025). High-Temperature Photoluminescence Enhancement up to 350 K of Monophase α-FAPbI3 Quantum Dots Synthesized via Tailored Hot Injection. *The Journal of Physical Chemistry C*, 129, 15342–15350. [10.1021/acs.jpcc.5c05144](https://doi.org/10.1021/acs.jpcc.5c05144). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=sasongko2025).

- Pascal Rusch; Ann Mary Antony; Meenakshi Pegu; Meysoun Jabrane; Gabriele Saleh; Arghyadeep Garai; Aswin Asaithambi; Simone Lauciello; Sergio Marras; Serena De Negri; Pavlo Solokha; Liberato Manna (2026). Nanocrystal Synthesis Derived Approach to Silver Bismuth Iodide Layered Double Perovskites with Aliphatic Amines: (CnH(2n+1)NH3)4AgBiI8. *Chemistry of Materials*, 38, 900–909. [10.1021/acs.chemmater.5c02845](https://doi.org/10.1021/acs.chemmater.5c02845). [Source review and scope](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=rusch2026).

## Additional contextual sources

These are contextual/upstream references, not extra reviewed synthesis contributions.

- Williamson, E. M.; Tappan, B. A.; Mora-Tamez, L.; Barim, G.; Brutchey, R. L. (2021). Statistical Multi-Objective Optimization of Thiospinel CoNi2S4 Nanocrystal Synthesis via Design of Experiments. [Source](https://doi.org/10.1021/acsnano.1c00502). Review scope remains stated in the linked website records.

## Crystal reference models

Reference structures are distinguished from sample-resolved synthesis targets. Provenance and qualifications remain in the website registry.

- [ZnO wurtzite bulk reference](https://www.crystallography.net/cod/9004178.html). literature bulk reference.

- [FCC iridium bulk reference](https://www.crystallography.net/cod/9008470.html). literature bulk reference.

- [Zinc-blende InP bulk reference](https://www.crystallography.net/cod/1010146.html). literature bulk reference.

- [Orthorhombic CsPbBr3 bulk reference](https://www.crystallography.net/cod/4510745.html). Qualified reference.

- [Rocksalt CoO bulk reference](https://www.crystallography.net/cod/1533087.html). Qualified reference.

- [Partially inverse CoFe2O4 bulk reference](https://www.crystallography.net/cod/1533163.html). Qualified reference.

- [Ideal diamond-Si bulk comparison reference](https://doi.org/10.1021/j100108a019). Qualified reference.

- [Bulk wurtzite CdSe reference · core comparison](https://www.crystallography.net/cod/9016056.html). literature bulk reference.

- [Ideal rock-salt PbSe reference](https://doi.org/10.1021/nl0345116). constructed lattice reference.

- [CeO2 fluorite reference](https://www.crystallography.net/cod/9009008.html). literature bulk reference.

- [Ag face-centered cubic reference](https://www.crystallography.net/cod/9008459.html). literature bulk reference.

- [Ge diamond cubic reference](https://www.crystallography.net/cod/9008567.html). literature bulk reference.

- [FAPbI3 computed pseudo-cubic framework (P1 ordered model) reference](https://github.com/WMD-group/hybrid-perovskites/blob/master/2014_cubic_halides_PBEsol/FAPbI3.cif). computed reference.

- [CdS wurtzite reference](https://www.crystallography.net/cod/9008862.html). literature bulk reference.

- [CdS zinc blende reference](https://www.crystallography.net/cod/9000067.html). literature bulk reference.

- [Pt face-centered cubic reference](https://www.crystallography.net/cod/9008480.html). literature bulk reference.

- [SnO2 cassiterite (rutile type) reference](https://www.crystallography.net/cod/9009082.html). literature bulk reference.

- [ZnAl2O4 normal spinel reference](https://www.crystallography.net/cod/9015620.html). literature bulk reference.

- [PbS rock salt reference](https://www.crystallography.net/cod/9013403.html). literature bulk reference.

- [ZnS zinc blende reference](https://www.crystallography.net/cod/1100043.html). literature bulk reference.

- [ZnS wurtzite reference](https://www.crystallography.net/cod/1100044.html). literature bulk reference.

- [ZnSe zinc blende reference](https://www.crystallography.net/cod/9008857.html). literature bulk reference.

- [ZnSe wurtzite reference](https://www.crystallography.net/cod/9008879.html). literature bulk reference.

- [InAs zinc blende reference](https://www.crystallography.net/cod/9008851.html). literature bulk reference.

- [CsMnCl3 rhombohedral R-3m, hexagonal axes reference](https://www.crystallography.net/cod/2107040.html). literature bulk reference.

- [Si diamond cubic reference](https://www.crystallography.net/cod/9008565.html). literature bulk reference.

- [Constructed zinc-blende CdSe reference](https://researchconnect.buffalo.edu/en/publications/growth-of-cubic-zinc-blende-cdse-by-molecular-beam-epitaxy/). constructed lattice reference.

- [CdTe zinc blende (alternative phase) reference](https://www.crystallography.net/cod/9008840.html). literature bulk reference.

- [ZnTe zinc-blende bulk reference](https://www.crystallography.net/cod/9008858.html). literature bulk reference.

- [HgS metacinnabar (zinc-blende) reference](https://www.crystallography.net/cod/1011368.html). literature bulk reference.

- [HgS cinnabar alternative bulk phase](https://www.crystallography.net/cod/9012082.html). literature bulk reference.

- [Cs4PbBr6 rhombohedral bulk reference](https://www.crystallography.net/cod/1538416.html). literature bulk reference.

- [Co face-centred cubic reference](https://www.crystallography.net/cod/9008466.html). literature bulk reference.

- [Co hexagonal close-packed reference](https://www.crystallography.net/cod/9010967.html). literature bulk reference.

- [CuSbS2 chalcostibite reference](https://www.crystallography.net/cod/9003580.html). literature bulk reference.

- [Cu3SbS4 famatinite reference](https://www.crystallography.net/cod/8104122.html). literature bulk reference.

- [Cu12Sb4S13 tetrahedrite reference](https://www.crystallography.net/cod/2101865.html). literature bulk reference.

- [Cu3SbS3 monoclinic skinnerite reference](https://www.crystallography.net/cod/9004360.html). literature bulk reference.

- [CuS covellite reference](https://www.crystallography.net/cod/9000523.html). literature bulk reference.

- [Cu1.8S rhombohedral digenite reference](https://www.crystallography.net/cod/1536218.html). literature bulk reference.

- [Cu2S high-chalcocite average reference](https://www.crystallography.net/cod/1529746.html). literature bulk reference.

- [Ni3S4 polydymite reference](https://www.crystallography.net/cod/9009863.html). literature bulk reference.

- [Metallic Ni FCC reference](https://www.crystallography.net/cod/9008476.html). literature bulk reference.

- [NiS millerite reference](https://www.crystallography.net/cod/9004078.html). literature bulk reference.

- [ZnGa2O4 bulk spinel reference](https://www.crystallography.net/cod/4001767.html). literature bulk reference.

- [Bi2S3 bismuthinite reference at ambient pressure](https://www.crystallography.net/cod/9007398.html). literature bulk reference.

- [CoNi2S4 neutron-refined spinel reference](https://www.crystallography.net/cod/9009852.html). literature bulk reference.

- [CoS NiAs-type jaipurite reference](https://www.crystallography.net/cod/1011037.html). literature bulk reference.

- [FePt ordered tetragonal alternative reference](https://www.crystallography.net/cod/9004222.html). literature bulk reference.

- [Graphite 2H planar-layer reference](https://www.crystallography.net/cod/9011577.html). literature bulk reference.

- [Cs3Cu2Cl5 Pnma alternative reference](https://www.crystallography.net/cod/7246298.html). literature bulk reference.

- [Cu2SnS3 monoclinic alternative reference](https://www.crystallography.net/cod/1526187.html). literature bulk reference.

- [La2(MoO4)3 monoclinic bulk alternative](https://www.crystallography.net/cod/2107003.html). literature bulk reference.

- [Fe3O4 magnetite bulk comparator](https://www.crystallography.net/cod/9005812.html). literature bulk reference.

- [Fe2O3 hematite bulk comparator](https://www.crystallography.net/cod/9000139.html). literature bulk reference.

- [Fe2O3 maghemite average bulk comparator](https://www.crystallography.net/cod/9006316.html). literature bulk reference.

- [PbI2 layered 2H bulk reference](https://www.crystallography.net/cod/9009114.html). literature bulk reference.

- [FAPbI3 hexagonal non-H average reference](https://www.crystallography.net/cod/4335640.html). literature bulk reference.

- [CsBr CsCl-type bulk reference](https://www.crystallography.net/cod/9008788.html). literature bulk reference.

- [AlOOH boehmite non-H reference](https://www.crystallography.net/cod/9012252.html). literature bulk reference.

- [CdTe wurtzite constructed reference](https://stars.library.ucf.edu/fsec/1898/). constructed reference.

- [Calcined SSZ-48 partial Si/O framework](https://doi.org/10.1021/jp991389j). source table partial framework.

A citation does not grant reuse rights to third-party figures or source text. The separate release boundary gate controls public delivery.

<!-- mattersyn-generated-references:end -->

- Haiming Zhu; Nianhui Song; William Rodríguez-Córdoba; Tianquan Lian. *Wave Function Engineering for Efficient Extraction of up to Nineteen Electrons from One CdSe/CdS Quasi-Type II Quantum Dot*. Journal of the American Chemical Society. [10.1021/ja210312s](https://doi.org/10.1021/ja210312s). [Standalone SI source review](https://cuiyist.github.io/mattersyn-site/paper-review.html?id=zhu2012-ja210312s-si). Supplied 31-page SI reviewed; main article and publication year unverified in that document.
