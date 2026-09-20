import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
const B=path.dirname(fileURLToPath(import.meta.url)),P=path.join(B,'visuals/products');
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const products=read(path.join(P,'product-registry-additions.json'));
const slots=read(path.join(P,'specimen-bindings-additions.json'));
const cards=read(path.join(P,'product-reference-proposal.json'));
const crystal=read(path.join(P,'crystal-reference-proposal.json'));
const author=read(path.join(P,'product-author-checks.json'));
const preview=read(path.join(P,'preview-manifest.json'));
const facts=read(path.join(B,'source-facts.json'));
const inventory=read(path.join(B,'source-inventory.json'));
const canonical=read(path.join(B,'canonical-record-manifest.json'));
const canonicalAudit=read(path.join(B,'canonical-records-audit.json'));
const molecules=read(path.join(B,'visuals/molecules/registry-additions.json'));
const entries=new Map(products.entries.map(x=>[x.id,x]));
const checks=[],bindings=[],bound={};
function bind(p){bound[path.relative(B,p).replaceAll('\\','/')]=sha(p);}
function check(ok,id,detail){checks.push({id,passed:!!ok,detail});if(!ok)throw Error(id+': '+detail);}
for(const p of ['source-facts.json','source-inventory.json','source-scientific-audit.json','canonical-record-manifest.json','canonical-records-audit.json','visuals/molecules/registry-additions.json'])bind(path.join(B,p));
for(const [p,h] of Object.entries(author.bound_files)){const full=path.join(P,p);check(sha(full)===h,'frozen-'+p,'Author-declared product-file hash matches actual file.');bind(full);}
for(const p of ['product-author-checks.json','preview-manifest.json'])bind(path.join(P,p));
check(author.source_facts_sha256===sha(path.join(B,'source-facts.json'))&&author.source_inventory_sha256===sha(path.join(B,'source-inventory.json')),'source-extraction-binding','Product proposal is bound to unchanged audited source facts and inventory.');
check(canonicalAudit.status==='passed'&&canonicalAudit.bound_files['canonical-record-manifest.json']===sha(path.join(B,'canonical-record-manifest.json')),'canonical-audit-binding','Passed independent canonical audit is bound to the current manifest.');
for(const e of products.entries){
 check(e.provenance.sourceSha256===facts.source_sha256&&e.provenance.siSha256===facts.si_sha256,e.id+'-source','Original main/SI hashes match the audited extraction.');
 check(e.model2dPath===null&&e.model3dPath===null&&e.provenance.measuredCoordinates===false&&e.provenance.eligible_training===false,e.id+'-non-atomic','Specimen diagram has no coordinate models or training admission.');
 check(e.provenance.sourceFactIds.every(id=>facts.facts.some(f=>f.id===id)),e.id+'-facts','All explicit fact IDs resolve. Empty lists on qualitative cards are complemented by original locators and audit source-unit bindings below.');
 const svg=path.join(P,e.svgPath);check(sha(svg)===e.assetHashes.svgPath&&sha(svg)===author.assets[e.svgPath],e.id+'-svg','Actual SVG matches registry and author hashes.');bind(svg);
}
for(const p of preview.previews){check(sha(p.path)===p.sha256,'preview-'+path.basename(p.path),'Actual viewed PNG matches frozen preview hash.');const e=products.entries.find(e=>path.basename(e.svgPath,'.svg')===path.basename(p.path,'.png'));check(e?.assetHashes.svgPath===p.source_svg_sha256,'preview-source-'+e?.id,'PNG manifest identifies the matching frozen SVG.');bind(p.path);}
check(sha(preview.contact_sheet)===preview.contact_sha256,'contact-hash','Actually viewed five-card contact sheet matches manifest.');bind(preview.contact_sheet);
for(const [rid,map] of Object.entries(slots.recordBindings)){
 const row=canonical.records.find(x=>x.record_id===rid),record=read(row.path);
 check(sha(row.path)===row.sha256&&slots.sourceRecordSha256[rid]===row.sha256,rid+'-frozen','Specimen map binds the exact canonical record.');bind(row.path);
 for(const [slot,target] of Object.entries(map)){
  const material=record.materials.find(x=>x.id===slot),entry=entries.get(target);
  check(!!material&&!!entry&&material.role==='specimen',rid+'/'+slot+'-exists','Specimen slot and target identity exist.');
  check(material.formula===entry.formula,rid+'/'+slot+'-formula','Nominal composition matches canonical specimen; this does not establish stoichiometric atomic coordinates.');
  bindings.push({record_id:rid,material_id:slot,pointer:`/materials/${record.materials.findIndex(x=>x.id===slot)}`,target,source_evidence:material.evidence,scope:'nominal source specimen label; not an identical physical aliquot across techniques'});
 }
}
for(const [rid,target] of Object.entries(cards.recordBindings)){
 const row=canonical.records.find(x=>x.record_id===rid);check(!!row&&sha(row.path)===row.sha256,rid+'-product-record','Product-card record exists at its frozen hash.');bind(row.path);
 check(entries.has(target)||molecules.entries.some(x=>x.id===target),rid+'-product-target','Product target resolves to source specimen card or separately proposed precursor reference.');
}
const cdacac=molecules.entries.find(x=>x.id==='gu2004-cadmium-acac-reference');
check(cdacac.formula==='C10H14CdO4'&&cdacac.depictionKind==='ionic_components'&&cdacac.model3dPath===null,'cdacac-product-reference','Cd(acac)2 is an explicitly qualified formal-component reference; no measured coordination geometry is assigned. Detailed molecule audit remains separate.');
check(crystal.entries.length===0&&crystal.files.length===0&&!crystal.generatedCif&&!crystal.measuredSampleStructure&&!crystal.trainingEligible,'crystal-gap','No invented crystal files or exact structure–recipe training pairs.');
check(slots.bindingApproved===false&&cards.publicationApproved===false,'unapproved-gates','Source audit does not enable final binding/publication/training gates.');
const sourceMap=[
 {id:'identity-gu-fept-1',units:['gu2004-figure-1a','gu2004-fept-saed-claim'],facts:['gu2004-fact-fept-1-average-diameter'],judgment:'Source 1 average diameter 2.5 nm belongs to precursor before sulfur. Figure 1A shows that precursor. Diagram avoids claiming atomic Fe/Pt ordering or transferring product-4 SAED to 1.'},
 {id:'identity-gu-fept-cds-4',units:['gu2004-scheme-stages','gu2004-final-saed-phases','gu2004-final-cds-crystallinity','gu2004-figure-1b','gu2004-figure-1c','gu2004-figure-1d'],facts:['gu2004-fact-final-fept-component-diameter','gu2004-fact-final-cds-component-diameter','gu2004-fact-final-fept-phase','gu2004-fact-final-cds-phase','gu2004-fact-overall-size-description'],judgment:'Product 4 is two joined FePt/CdS domains. 2.5 nm FePt and approximately 3–4 nm CdS are separate component reports. Disordered FCC FePt and zinc-blende CdS derive from actual Figure 1D, with no lattice constant, atomic positions or measured interface. Around 7 nm remains an independent source-wide description, not a diagram-derived sum.'},
 {id:'identity-gu-isolated-2',units:['gu2004-scheme-stages','gu2004-intermediate-isolation-failure','gu2004-figure-s4'],facts:[],judgment:'Nominal FePt/S intermediate 2 and SI S-4 are correctly linked. Proposed sulfur coverage is separate from the isolated specimen; no intact shell or thickness is depicted.'},
 {id:'identity-gu-isolated-3',units:['gu2004-scheme-stages','gu2004-intermediate-isolation-failure','gu2004-figure-s5'],facts:[],judgment:'Nominal FePt/CdS intermediate 3 and SI S-5 are correctly linked. Proposed amorphous coverage is separate from isolated specimen; no crystalline final CdS phase or intact shell geometry is assigned.'},
 {id:'identity-gu-microscopy-context',units:['gu2004-figure-1a','gu2004-figure-1b','gu2004-figure-1c','gu2004-figure-1d','gu2004-figure-s4','gu2004-figure-s5','gu2004-gap-sample-link-limits'],facts:[],judgment:'Card is an explicit collection of distinct labels 1–4, not a homogeneous specimen. Its nominal FePt/CdS overview formula is a family label; individual slot identities remain distinct, including FePt/S for 2. Physical aliquot identity across techniques is not implied.'}
];
for(const row of sourceMap){check(row.units.every(id=>inventory.units.some(x=>x.id===id)),row.id+'-source-units','All scientific source-unit bindings resolve.');check(row.facts.every(id=>facts.facts.some(x=>x.id===id)),row.id+'-source-facts','All scientific fact bindings resolve.');}
for(const name of ['scheme-1.png','figure-1.png','figure-s4.png','figure-s5.png'])bind(path.join(B,'reader-assets',name));
const report={schema:'mattersyn.private-product-source-audit.v1',status:'passed',auditor:'norberg2004_extract',audited_at:new Date().toISOString(),source_id:'gu2004',scope:'Independent bounded scientific audit of the five product identity diagrams, eight specimen bindings and seven product-card bindings. This is not a repeated complete-source audit or Site/publication approval.',bound_files:bound,counts:{registry_entries:products.entries.length,specimen_bindings:bindings.length,product_card_bindings:Object.keys(cards.recordBindings).length,product_previews_viewed:5,original_source_crops_viewed:4,checks:checks.length},checks,source_to_product_bindings:sourceMap,specimen_bindings:bindings,product_card_bindings:cards.recordBindings,actual_visual_inspection:{product_contact_sheet:path.relative(B,preview.contact_sheet).replaceAll('\\','/'),all_five_cards_viewed:true,source_crops:['reader-assets/scheme-1.png','reader-assets/figure-1.png','reader-assets/figure-s4.png','reader-assets/figure-s5.png'],source_text_rechecked:['main-01.txt','main-02.txt','si-03.txt'],findings:'No label, size/phase scope, specimen identity or unsupported atomic/shell claim found. Text is legible and captions carry the key limitations.'},open_findings:[],limitations:['FePt/CdS and FePt/S are nominal constituent labels, not resolved unit-cell formulae.','CIF/coordinate absence is supported for supplied main/SI; this audit does not certify an exhaustive external database search.','Cadmium acetylacetonate product link is checked for formal composition and stated scope only; molecular graph correctness belongs to the separate molecule audit.','No source or canonical record was modified.','Final integrated browser rendering and publication/training gates remain pending.'],independent_source_audit_passed:true,site_visual_audit_passed:false,publication_approved:false,training_approved:false};
fs.writeFileSync(path.join(B,'product-source-audit.json'),JSON.stringify(report,null,2)+'\n');
fs.writeFileSync(path.join(B,'product-source-audit.md'),`# Gu 2004 product source audit\n\nStatus: **passed**, bounded private source/identity audit.\n\nIndependently checked five source-scoped product cards, eight specimen-slot mappings and seven record-card mappings. All ${checks.length} identity/hash/source-binding checks passed. Opened and inspected all five rendered cards and original Scheme 1, Figure 1 and SI Figures S-4/S-5; reread the relevant main article and SI text. Exact file hashes and explicit source-unit/fact bindings are in the JSON report.\n\nThe diagrams preserve 2.5 nm precursor/component FePt, approximately 3–4 nm product CdS, and final-product disordered FCC FePt / zinc-blende CdS assignments. Overall approximately 7 nm remains separate. Intermediate 2 and 3 cards identify proposed coverage while leaving intact isolated shell morphology unassigned. Source specimen labels do not imply identical cross-technique aliquots.\n\nThe upstream Cd(acac)₂ link remains a qualified formal-component reference, not a measured coordination structure. No CIF, atomic model, structure–recipe training admission or publication approval is created. A final integrated browser visual audit remains pending.\n`);
console.log(JSON.stringify({status:report.status,checks:checks.length,bindings:bindings.length,bound_files:Object.keys(bound).length,audit_sha256:sha(path.join(B,'product-source-audit.json')),markdown_sha256:sha(path.join(B,'product-source-audit.md'))}));
