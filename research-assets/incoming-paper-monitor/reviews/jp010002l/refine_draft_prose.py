from pathlib import Path
p=Path(__file__).with_name('build_records.py');s=p.read_text(encoding='utf8')
replacements={
 'I has3 spectra, II5, III6':'I has 3 spectra, II has 5, and III has 6',
 'not15 independent fully specified syntheses':'not 14 independent fully specified syntheses',
 'separate440nm PL':'separate 440 nm PL',
 'states3µm(21fs)':'states 3 µm (21 fs)',
 'Figure4':'Figure 4','Figure1':'Figure 1',
 'both820nm and II950nm':'both 820 nm and II at 950 nm',
 'pH7.9':'pH 7.9','about30s':'about 30 s','with111 facets':'with {111} facets',
 'reference18':'reference 18','reference13':'reference 13','reference15':'reference 15','reference2 (':'reference 2 (','reference3 (':'reference 3 (','Reference19':'Reference 19',
 'SystemIII':'System III',
 'J. Phys. Chem.1994,98,934':'J. Phys. Chem. 1994, 98, 934',
 'Phys. Rev. B1996,53,R13242':'Phys. Rev. B 1996, 53, R13242',
 'J. Phys. Chem. B1999,103,6870':'J. Phys. Chem. B 1999, 103, 6870',
 'Phys. Rev. B1998,57,R4237':'Phys. Rev. B 1998, 57, R4237',
 'Phys. Rev. B1998,57,9780':'Phys. Rev. B 1998, 57, 9780',
 "[], 'probe-light',EXP":"[], None,EXP",
 "['ta-cell','probe-light'],'ta-excited'":"['ta-cell'],'ta-excited'",
}
for a,b in replacements.items():
 assert a in s,a
 s=s.replace(a,b)
p.write_text(s,encoding='utf8')
