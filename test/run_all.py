"""Tüm testleri çalıştırır. Kullanım: python3 test/run_all.py
Gerekli: pip install playwright && playwright install chromium (ya da CHROME=/yol/chrome)"""
import subprocess, sys, pathlib, re
d = pathlib.Path(__file__).resolve().parent
import os
files = sorted(d.glob('t*.py'), key=lambda p: int(re.sub(r'\D', '', p.stem)))
if os.environ.get('PAGE', 'index.html') != 'index.html':
    # önizleme v12: duvar iki bağımsız çizgi — eski "referans + hesaplanan yüz" testleri sadece ana uygulama için
    V11 = {'t2','t3','t4','t5','t7','t8','t9','t10','t11','t12','t13','t16','t17','t20','t21','t22','t23','p5','p6','p7','p8','p11'}
    files = [f for f in files if f.stem not in V11] + sorted(f for f in d.glob('p*.py') if f.stem not in V11) + sorted(d.glob('q*.py'))
bad = 0
for f in files:
    r = subprocess.run([sys.executable, str(f)], capture_output=True, text=True, timeout=600)
    out = r.stdout + r.stderr; tot = [l for l in out.splitlines() if l.startswith('TOPLAM')]
    fails = [l for l in out.splitlines() if l.startswith('FAIL')]
    ok = r.returncode == 0 and tot and not fails
    print(f"{f.stem:5} {'OK ' if ok else 'HATA'} {tot[0] if tot else out[-300:]}")
    for l in fails: print('      ' + l[:200])
    bad += 0 if ok else 1
print('Hepsi geçti' if not bad else f'{bad} dosyada hata'); sys.exit(1 if bad else 0)
