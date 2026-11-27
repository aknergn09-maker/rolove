import pathlib
d=pathlib.Path(__file__).parent
s=(d/'shell.html').read_text()
geo=(d/'cad_geo.js').read_text().replace("if (typeof module !== 'undefined')","if (typeof module !== 'undefined' && typeof window === 'undefined')")
s=s.replace('/*ICONS*/',(d/'icons.json').read_text()).replace('/*GEO*/',geo+'\n'+(d/'cad_ops.js').read_text()+'\n'+(d/'cad_meas.js').read_text()+'\n'+(d/'cad_proj.js').read_text()).replace('/*APP*/',(d/'cad_app.js').read_text())
(d.parent/'cad.html').write_text(s); print('cad.html', len(s))
