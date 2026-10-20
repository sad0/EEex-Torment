# Validate fmap.json: whole-function alignment ratio per mapping; drop weak ones (and PT collisions).
import json, collections, sys
from fmap import whole_ratio
J = json.load(open('fmap.json'))
thr = float(sys.argv[1]) if len(sys.argv) > 1 else 0.3
out, drop, rs = {}, [], {}
for k, (v, m) in J.items():
    try:
        r, na, nb = whole_ratio(int(k, 16), int(v, 16))
    except Exception:
        r, na, nb = 0, 0, 0
    rs[k] = r
    if r < thr and not (na <= 3 and nb <= 3):
        drop.append((k, v, m, round(r, 2), na, nb))
    else:
        out[k] = [v, m]
# PT collisions: keep the best ratio
byp = collections.defaultdict(list)
for k, (v, m) in out.items():
    byp[v].append(k)
for v, ks in byp.items():
    if len(ks) > 1:
        ks.sort(key=lambda k: -rs[k])
        for k in ks[1:]:
            drop.append((k, v, out[k][1], round(rs[k], 2), 'collision', ks[0])); del out[k]
import os
if os.path.exists('fmap_manual.json'):
    for k, v in json.load(open('fmap_manual.json')).items():
        out = {kk: vv for kk, vv in out.items() if vv[0] != v[0]}
        out[k] = v
json.dump(out, open('fmap.json', 'w'), indent=0)
json.dump(rs, open('fmap_ratio.json', 'w'))
print('kept', len(out), 'dropped', len(drop), collections.Counter(d[2].rstrip('0123456789().') for d in drop))
