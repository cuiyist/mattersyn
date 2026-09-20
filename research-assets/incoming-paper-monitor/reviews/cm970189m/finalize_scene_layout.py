from pathlib import Path
p=Path(__file__).resolve().parent/'veinot-protocol.mjs';s=p.read_text(encoding='utf8')
s=s.replace("+note('Vessel geometry is illustrative; no volume of excess anhydride is inferred.');}","+note(p?'Vessel geometry is illustrative; no transient solid composition is inferred.':'Vessel geometry is illustrative; no volume of excess anhydride is inferred.');}")
s=s.replace(":'3b has an unresolved duration conflict; no single operative time is selected.');}",":variant(r)==='3b'?'3b has an unresolved duration conflict; no single operative time is selected.':'Common anhydride method: no absolute charges or concentration are supplied.');}")
s=s.replace("'M245 157L289 112H427V168'","'M245 157L289 112H427V148'").replace('flask(427,245)','flask(427,225)')
s=s.replace("'M163 161H236L313 191H414V218'","'M163 161H236L313 174H414V184'").replace('box(244,155,104,36','box(244,145,104,36').replace('flask(415,294','flask(415,260').replace("'M434 221H502V126'","'M434 187H502V126'")
p.write_text(s,encoding='utf8')
