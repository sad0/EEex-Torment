# Prove fields of embedded structs through their containers: for every container S with an embedded
# member E (type U) at a proven offset, aligned functions validated on S (bindings/autoprove.py rule)
# vote, for each unproven field f of U, the PT offset of [S + E + f]. A field of U is accepted when the
# votes agree (unanimous, or >= 97% of >= 10 votes from >= 5 functions), come from >= 2 functions and
# fit its proven neighbours.
# Usage (from tools/): python bindings/embedprove.py [--write]
import sys, os, json, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, 'bindings')
import autoprove as A
from fmap import align

L = json.load(open('bindings/ptlayout.json')); C = json.load(open('bindings/coverage.json'))
D = A.bg_disps()
PROV = ('proven', 'span')

# embedded members at proven offsets: (container, member bg, member pt, type)
emb = collections.defaultdict(list)
for S, l in L.items():
    for n, i in l['items'].items():
        t = i['type'].strip()
        if t in L and C.get(S, {}).get(n) in PROV and i['pt'] is not None:
            emb[S].append((i['bg'], i['pt'], t))

votes = collections.defaultdict(collections.Counter)
funcs = collections.defaultdict(set)
for S, members in emb.items():
    proven = {i['bg']: i['pt'] for n, i in L[S]['items'].items() if C.get(S, {}).get(n) in PROV and i['pt'] is not None and i['bg'] >= 0x40}
    targets = {}
    for mb, mp_, U in members:
        for f, fi in L[U]['items'].items():
            if C.get(U, {}).get(f) in ('unproven', 'absent'):
                targets[mb + fi['bg']] = (U, f, mp_)
    if not targets or len(proven) < 2:
        continue
    for fn, s in D.items():
        pk = [d for d in s if d in proven]
        tk = [d for d in s if d in targets]
        if len(pk) < 2 or not tk:
            continue
        mp, r, _, _ = align(fn, A.F[fn])
        if r < 0.6:
            continue
        good = bad = 0
        for d in pk:
            for a in s[d]:
                pa = mp.get(a)
                if pa is None:
                    continue
                bi, bo = A.mem(A.BG, a); pi, po = A.mem(A.PT, pa)
                if not bo or not po or bi.mnemonic != pi.mnemonic:
                    continue
                good += po.mem.disp == proven[d]; bad += po.mem.disp != proven[d]
        if good < 2 or bad:
            continue
        for d in tk:
            U, f, mpt = targets[d]
            for a in s[d]:
                pa = mp.get(a)
                if pa is None:
                    continue
                bi, bo = A.mem(A.BG, a); pi, po = A.mem(A.PT, pa)
                if bo and po and bi.mnemonic == pi.mnemonic and bo.size == po.size:
                    votes[(U, f)][po.mem.disp - mpt] += 1
                    funcs[(U, f)].add(fn)

acc = {}
for (U, f), v in sorted(votes.items()):
    top, cnt = v.most_common(1)[0]; tot = sum(v.values())
    dominant = cnt >= 10 and cnt >= 0.97 * tot and len(funcs[(U, f)]) >= 5
    from collections import Counter as _C
    ok = A.acceptable(L[U]['items'], C[U], f, v if not dominant else _C({top: cnt}), len(funcs[(U, f)]))
    print(f'{U}.{f:30} bg {L[U]["items"][f]["bg"]:#x} votes {dict((hex(k), c) for k, c in v.items())} fns {len(funcs[(U, f)])}' + ('  ACCEPT' if ok else ''))
    if ok:
        acc[(U, f)] = v.most_common(1)[0][0]
if '--write' in sys.argv:
    p = 'bindings/manual_fields.json'; d = json.load(open(p))
    for (U, f), pt in acc.items():
        m = d['fields'].setdefault(U, {})
        if f not in m:
            m[f] = {'pt': hex(pt), 'why': f'embedprove: {sum(votes[(U, f)].values())} unanimous votes from {len(funcs[(U, f)])} functions through containers at proven member offsets (bindings/embedprove.py)'}
    json.dump(d, open(p, 'w'), indent=1)
    print('written', len(acc))
