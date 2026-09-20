from pathlib import Path
B=Path(__file__).resolve().parent;P=B.parent/'nl015685v'
t=(P/'finalize_publication.py').read_text(encoding='utf-8')
for a,b in [('nl015685v','jp0208743'),('besson2002','dantas2002'),('0.16.0','0.17.0'),('CdS/SiO2','PbS/glass'),('14294e7c0409a36f1aa08d7f494ef0a3cf26ff06c99f22e87ac9a3c2d5a781c3','a44f927e3c2b3e9f75925e1e47cd105acc652c443b4ace1ab471cf3cac603a41'),('9f1b5b781e7a36f1ec109eb14ee724bb6c99a8156b4bc6899cfffe8ab613c357','c8fd35a429bf636fcccc5dfeb3211cea44299e911fbfc80e1a308c75b7b04917'),('original_figures=4','original_figures=7'),('len(records)==12','len(records)==16'),("p['synthesis_routes']==3","p['synthesis_routes']==6"),("p['operations']==36","p['operations']==48")]:t=t.replace(a,b)
(B/'finalize_publication.py').write_text(t,encoding='utf-8')
print('Private finalization helper prepared; not executed.')
