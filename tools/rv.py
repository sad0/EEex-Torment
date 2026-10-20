# Review helper: python rv.py <regex> [n]  -> BG context + context at every candidate address
import sys, re, json, subprocess
G = json.load(open('gen_report.json')); L = json.load(open('local.json')); X = json.load(open('final.json')); R = json.load(open('port2.json'))
n = int(sys.argv[2]) if len(sys.argv) > 2 else 12
from show import lines, BG, PT
for name, r in G.items():
    if not re.search(sys.argv[1], name) or r['status'] != 'unresolved':
        continue
    c = [L.get(name, {}).get('addr'), X.get(name, {}).get('addr')] + [a[0] for a in X.get(name, {}).get('alts', [])]
    c = list(dict.fromkeys(x for x in c if x))
    print('#####', name, '|', r['note'][:80])
    print('\n'.join(lines(BG, int(R[name]['bg_key'], 16), n, False, True)))
    for a in c:
        print('  --- PT', a)
        print('\n'.join(lines(PT, int(a, 16), n, False, True)))
