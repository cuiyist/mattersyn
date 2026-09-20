from pathlib import Path
p=Path(__file__).resolve().parent/'visuals/schwartz2003-protocol.mjs';t=p.read_text(encoding='utf8')
fixes={'uses90mL of0.101M':'uses 90 mL of 0.101 M','print0.554M':'print 0.554 M','is30mL base into90mL metal stock, reported1.8equiv':'is 30 mL base into 90 mL metal stock, reported 1.8 equiv','of0.101M':'of 0.101 M','approximately10mg':'approximately 10 mg','a1cm':'a 1 cm','at300K':'at 300 K','and2%Co':'and 2% Co','the2%Co':'the 2% Co','with1mg':'with 1 mg','>0.4g/mL':' >0.4 g/mL','a prescribed80°C':'a prescribed 80 °C','FigureS2':'Figure S2','FigureS4':'Figure S4','Figure1c':'Figure 1c','Figure5':'Figure 5','Figure10':'Figure 10','Figure8':'Figure 8','<1.5–300K and0–7T':'<1.5–300 K and 0–7 T','measures3.6%Co':'measures 3.6% Co','Their4.9/5.0nm':'Their 4.9/5.0 nm','TC>350K':'TC > 350 K','loss of size dispersity':'loss of size uniformity'}
for a,b in fixes.items():t=t.replace(a,b)
p.write_text(t,encoding='utf8')
print('Applied source-audited scientific and text corrections.')
