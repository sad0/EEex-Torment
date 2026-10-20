# Compare solved PT layout (ptlayout.json) against the compiled generated header (pt_layout.txt).
import json, sys, collections
L = json.load(open(sys.argv[1])); C = collections.defaultdict(dict); size = {}
for line in open(sys.argv[2]):
    p = line.split()
    if len(p) == 4:
        if p[1] == '__size': size[p[0]] = int(p[2], 16)
        else: C[p[0]][p[1]] = int(p[2], 16)
bad = 0
for s, l in L.items():
    if s not in size: continue
    errs = []
    if l['pt_size'] is not None and size[s] != l['pt_size']:
        errs.append(f'size {size[s]:#x} != {l["pt_size"]:#x}')
    for n, it in sorted(l['items'].items(), key=lambda x: x[1]['bg']):
        if it['pt'] is not None and n in C[s] and C[s][n] != it['pt']:
            errs.append(f'{n} {C[s][n]:#x} != {it["pt"]:#x}'); break
    if errs:
        bad += 1
        if len(sys.argv) < 4 or s in sys.argv[3:]: print(s, errs)
print(bad, 'structs differ')
