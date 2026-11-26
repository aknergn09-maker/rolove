import pathlib
d=pathlib.Path(__file__).parent
s=(d/'shell.html').read_text().replace('/*CORE*/',(d/'gonye_core.js').read_text().replace("if (typeof module !== 'undefined')","if (typeof module !== 'undefined' && typeof window === 'undefined')")).replace('/*APP*/',(d/'app.js').read_text())
(d.parent/'gonye.html').write_text(s); print('gonye.html',len(s))
