from pathlib import Path
import json
B=Path(__file__).resolve().parent;P=B.parent/'ja036811v';S=B.parents[3]/'recipe-atlas'
scope='All seven supplied main pages text-read and visually inspected, including five figures, model equations and 67 references. Independent source, canonical, molecular, crystal, reader and apparatus audits preserve individual/assembly/device/model scopes. SI not located or verified; cited full texts not independently inspected.'
p=B/'visuals/sashchiuk2004-protocol.mjs';t=p.read_text(encoding='utf8').replace("particles=false,solid=false,label=''","particles=false,solid=false,assembly=false,label=''")
t=t.replace("+(particles?dots(x,y+(solid?37:7),solid):'')","+(particles?(assembly?`<circle cx=\"${x}\" cy=\"${y+8}\" r=\"29\" fill=\"#cadde6\" stroke=\"${C.line}\"/>`:'')+dots(x,y+(solid?37:7),solid):'')")
t=t.replace("['30 / 35 / 40 min series','Separate optical aliquots'],{particles:true}","['30 / 35 / 40 min series','Separate optical aliquots'],{particles:true,assembly:true}")
p.write_text(t,encoding='utf8')
t=(P/'run_build.py').read_text(encoding='utf8').replace('schwartz2003','sashchiuk2004');(B/'run_build.py').write_text(t,encoding='utf8')
t=(P/'build_inventory_actual.py').read_text(encoding='utf8').replace('schwartz','sashchiuk').replace('sashchiuk2003','sashchiuk2004')
t=t.replace("'review_status':'full_supplied_main_and_matched_si_review'","'review_status':'full_supplied_main_review_si_unverified'")
start=t.index("'review_scope':",t.index("row={'source_group'"));end=t.index(",'documents':",start);t=t[:start]+"'review_scope':"+repr(scope)+t[end:]
t=t.replace("'page_count':14","'page_count':7").replace(",{'role':'si','page_count':4,'all_text_read':True,'all_visually_reviewed':True}",'').replace("'si_status':'matched_and_reviewed'","'si_status':'not_located_or_verified'")
start=t.index("'notes':[",t.index("row={'source_group'"));end=t.index('\ninv[',start)
t=t[:start]+"'notes':['Four growth routes preserve mass-ratio and caption conflicts; stock amounts are not supplied.','All five source figures and eight excerpts retained, including original SAED, absorption and electrical data.','Ideal crystal references and author calculations are not measured sample atomic coordinates or exact-structure training targets.']}"+t[end:]
(B/'build_inventory_actual.py').write_text(t,encoding='utf8')
# Prepare the explicit addition to the existing scientific reference validator.
t=(S/'scripts/check_quality.py').read_text(encoding='utf8')
t=t.replace('CRYSTALS = {','CRYSTALS = {\n    "sashchiuk-2004-pbse-ideal-reference": (1, "451a51951af70a8ce50b5e6d0b4db53f67a2a3647901f5784de5c44c62961b0a", {"Pb": 4, "Se": 4}),')
t=t.replace('Eight independently reviewed crystal references changed','Nine independently reviewed crystal references changed')
needle='            else:\n                self.check(bool(e.get("scope")) and e.get("sourceUrl", "").startswith("https://www.crystallography.net/cod/"), f"{cid}: source/scope absent")'
addition='''            elif cid == "sashchiuk-2004-pbse-ideal-reference":
                self.check(e.get("sourceUrl") == "https://doi.org/10.1021/nl0345116" and e.get("referenceType") == "locally_constructed_ideal_reference" and e.get("measuredSampleStructure") is False, f"{cid}: ideal reference scope changed")
                self.check(set(e.get("record_ids",[])) == {"sashchiuk-2004-"+x for x in ["individual-low","sphere-intermediate","wire-intermediate","wire-high"]}, f"{cid}: wrong source scopes")
                self.check(e.get("prototypeSpaceGroupNumber") == 225 and e.get("spaceGroupNumber") == 1, f"{cid}: expanded P1 export/prototype confusion")
'''
assert needle in t;t=t.replace(needle,addition+needle)
needle='            else:\n                self.check(m["source"]["sha256"] == expected_hash, f"{cid}: model derives from wrong CIF")'
addition='''            elif cid == "sashchiuk-2004-pbse-ideal-reference":
                self.check(m.get("source",{}).get("source_sha256") == "72684e3bf22a2ef173ea1d6d6e31648a1222b2b15bc069bb8fe6cef8d1876a33" and m.get("cell",{}).get("a") == 6.1 and m.get("evidence_type") == "illustrative", f"{cid}: reference source or rounded parameter changed")
                self.check(e.get("modelSha256") == "94a827b12f1f464e07fb01d1a125afc0e6fa0680ed35cd3dc3f4b07c655f1127", f"{cid}: audited ideal unit cell changed")
                fp = self.asset(base,e.get("finiteModelPath"),e.get("finiteModelSha256"),cid+"/finite-model")
                self.check(e.get("finiteModelSha256") == "cc9bf5594ffd16a28ee829de0b9bc6f404bdd111272785676da73a3ffa90a4e4", f"{cid}: audited finite block changed")
                if fp:
                    fm=load(fp)
                    self.check(fm.get("periodic") is False and fm.get("training_eligible") is False and fm.get("measured_sample_structure") is False and fm.get("evidence_type") == "illustrative",f"{cid}: finite model scope changed")
                    self.check(Counter(x["element"] for x in fm["atoms"]) == {"Pb":2048,"Se":2048},f"{cid}: finite block composition changed")
                for download in e.get("additionalDownloads",[]):self.asset(base,download["path"],download["sha256"],cid+"/download")
'''
assert needle in t;t=t.replace(needle,addition+needle)
(B/'check_quality-proposal.py').write_text(t,encoding='utf8')
print('Prepared delivery helpers and explicit PbSe reference validator extension; Site unchanged.')
