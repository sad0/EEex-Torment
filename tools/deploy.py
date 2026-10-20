# Deploy poc/InfinityLoader.db to the dev game. With --stub-unresolved, entries still unresolved in
# gen_report.json get Unsupported=1 in the deployed copy only (test aid, never committed).
import json, re, sys, shutil, os
from ilib import parse_db, PT_DB, UP_DB

GAME = r'E:\Enhanced Edition\Environnement de test\PTEE (EEex dev)'
dst = os.path.join(GAME, 'InfinityLoader.db')
txt = open(PT_DB, encoding='utf-8').read()
if '--stub-unresolved' in sys.argv:
    up = parse_db(UP_DB)
    rep = json.load(open('gen_report.json'))
    n = 0
    for name, r in rep.items():
        if r['status'] != 'unresolved':
            continue
        sec = '!ExeSwitch-Torment.exe-' + name if up.get(name, {}).get('ExeSwitch') == '1' else name
        m = re.search(r'^\[' + re.escape(sec) + r'\]\s*\n', txt, re.M)
        if m:
            txt = txt[:m.end()] + 'Unsupported=1\n' + txt[m.end():]
        else:
            txt += f'\n[{sec}]\nUnsupported=1\n'
        n += 1
    print('stubbed', n)
if os.path.exists(dst) and not os.path.exists(dst + '.bak'):
    shutil.copy(dst, dst + '.bak')
open(dst, 'w', encoding='utf-8', newline='').write(txt)
print('deployed', dst)
