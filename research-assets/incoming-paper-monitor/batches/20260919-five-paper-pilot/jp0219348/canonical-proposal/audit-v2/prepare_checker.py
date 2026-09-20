from pathlib import Path
A=Path(__file__).resolve().parent
text=(A.parent/'audit-v1/check_transport.py').read_text(encoding='utf-8')
text=text.replace("V=A.parent/'v1'", "V=A.parent/'v2'")
text=text.replace('frozen Heo canonical/reader v1','frozen Heo canonical/reader v2')
text=text.replace('mattersyn.heo_v1_transport_checks/1','mattersyn.heo_v2_transport_checks/1')
(A/'check_transport.py').write_text(text,encoding='utf-8')
