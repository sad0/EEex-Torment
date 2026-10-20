# Cross-check every ported function entry with a caller vote: each BG direct call to the BG function,
# located in PT via anchor2 inside the mapped caller, votes for its PT callee.
import json, collections
from local import anchor2, F
from fmap import BG, PT, callers
from gen import bg_final, upentry
from ilib import classify

G = json.load(open('gen_report.json')); R = json.load(open('port2.json'))
out = {}
for n, r in G.items():
    if r['status'] != 'ported':
        continue
    kind = r.get('kind') or classify(upentry(n).get('Operations', ''))[0]
    if kind == 'A' and n in R and 'bg_key' in R[n]:
        t = int(R[n]['bg_key'], 16)
    elif kind == 'B':
        t = bg_final(n)
    else:
        continue
    if t is None or not (BG.tva <= t < BG.tva + BG.tsize) or BG.fstart(t) != t:
        continue
    v = collections.Counter(); seen = 0
    for s, o in callers(BG, t)[:40]:
        bp = BG.rfunc(s); bp = bp[0] if bp else BG.fstart(s)
        if bp not in F:
            continue
        a = anchor2(bp, s, F[bp])
        if not a or a[1] < 0.6:
            continue
        seen += 1
        ps = a[0]
        if PT.tbytes(ps, 1)[0] in (0xE8, 0xE9):
            v[ps + 5 + PT.i32(ps + 1)] += 1
    if not v:
        continue
    top, c = v.most_common(1)[0]
    mine = int(r['addr'], 16)
    out[n] = {'mine': hex(mine), 'top': hex(top), 'votes': c, 'seen': seen, 'mine_votes': v.get(mine, 0)}
    if top != mine and c >= 2 and c > 2 * v.get(mine, 0):
        print(f"{n[:60]:60} mine={hex(mine)} ({v.get(mine,0)}) callers say {hex(top)} ({c}/{seen}) {r['conf']} {r['method'][:30]}")
json.dump(out, open('callercheck.json', 'w'), indent=1)
print(len(out), 'checked')
