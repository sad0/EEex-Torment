# Prove PT offsets of unproven fields of a struct from aligned BG/PT functions that are validated
# for that struct: every aligned access they make to already-proven fields of the struct (BG disp
# >= min) lands on the proven PT offset (>= 2 confirmations, no contradiction). Their accesses to
# the unproven fields then vote; a field is accepted when all votes agree, come from >= 2 functions,
# and the offset fits between its nearest proven neighbours.
# Usage (from tools/): python bindings/autoprove.py <struct> [min bg disp, default 0x400] [--write]
import sys, os, json, collections, pickle
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import capstone
from capstone import x86_const as X
from fmap import BG, PT, align, fragments, func_insns

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64); md.detail = True
F = {int(k, 16): int(v[0], 16) for k, v in json.load(open('fmap.json')).items()}
CACHE = 'bindings/autoprove_disps.pickle'


def mem(pe, a, n=16):
    i = next(iter(md.disasm(pe.tbytes(a, n), a)), None)
    for op in (i.operands if i else []):
        if op.type == X.X86_OP_MEM and op.mem.base not in (X.X86_REG_RIP, X.X86_REG_RSP, 0):
            return i, op
    return i, None


def bg_disps():
    if os.path.exists(CACHE):
        return pickle.load(open(CACHE, 'rb'))
    D = {}
    for f in F:
        s = collections.defaultdict(list)
        for g in fragments('BG', f):
            for a, sz, n, mn, ops in func_insns('BG', g):
                i, op = mem(BG, a)
                if op is not None:
                    s[op.mem.disp].append(a)
        D[f] = dict(s)
    pickle.dump(D, open(CACHE, 'wb'))
    return D


def validated_votes(D, S, L, C, minbig=0x400):
    """Functions whose aligned accesses to proven fields of S (BG disp >= minbig) all hit the proven
    PT offsets (>= 2 confirmations, no contradiction) vote for the other fields of S they touch."""
    proven = {i['bg']: i['pt'] for n, i in L.items() if C.get(n) in ('proven', 'span') and i['pt'] is not None and i['bg'] >= minbig}
    targets = {i['bg']: n for n, i in L.items() if C.get(n) in ('unproven', 'absent') and i['bg'] >= minbig}
    votes = collections.defaultdict(collections.Counter)
    funcs = collections.defaultdict(set)   # field -> functions that voted
    nf = 0
    for f, s in D.items():
        pk = [d for d in s if d in proven]
        tk = [d for d in s if d in targets]
        if len(pk) < 2 or not tk:
            continue
        mp, r, _, _ = align(f, F[f])
        if r < 0.6:
            continue
        good = bad = 0
        for d in pk:
            for a in s[d]:
                pa = mp.get(a)
                if pa is None:
                    continue
                bi, bo = mem(BG, a); pi, po = mem(PT, pa)
                if not bo or not po or bi.mnemonic != pi.mnemonic:
                    continue
                if po.mem.disp == proven[d]:
                    good += 1
                else:
                    bad += 1
        if good < 2 or bad:
            continue
        nf += 1
        for d in tk:
            for a in s[d]:
                pa = mp.get(a)
                if pa is None:
                    continue
                bi, bo = mem(BG, a); pi, po = mem(PT, pa)
                if not bo or not po or bi.mnemonic != pi.mnemonic or bo.size != po.size:
                    continue
                votes[targets[d]][po.mem.disp] += 1
                funcs[targets[d]].add(f)
    return votes, nf, funcs


def acceptable(L, C, n, v, nfuncs):
    """Unanimous, >= 2 votes from >= 2 functions, and the offset fits between the nearest proven
    neighbours (BG order kept, no overlap with any proven field)."""
    if len(v) != 1 or sum(v.values()) < 2 or nfuncs < 2:
        return False
    p = v.most_common(1)[0][0]
    it = L[n]
    proven = sorted((i['bg'], i['pt'], i['size']) for m, i in L.items() if C.get(m) in ('proven', 'span') and i['pt'] is not None)
    prev = [x for x in proven if x[0] < it['bg']]
    nxt = [x for x in proven if x[0] > it['bg']]
    if prev and p < prev[-1][1] + prev[-1][2]:
        return False
    if nxt and p + it['size'] > nxt[0][1]:
        return False
    return not any(q <= p < q + sz or p <= q < p + it['size'] for b, q, sz in proven)


if __name__ == '__main__':
    S = sys.argv[1]
    minbig = int(sys.argv[2], 16) if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else 0x400
    L = json.load(open('bindings/ptlayout.json'))[S]['items']
    C = json.load(open('bindings/coverage.json'))[S]
    D = bg_disps()
    V, nf, FN = validated_votes(D, S, L, C, minbig)
    print('validated functions', nf)
    res = {}
    for n in sorted(V, key=lambda n: L[n]['bg']):
        v = V[n]; top = v.most_common(1)[0]
        ok = acceptable(L, C, n, v, len(FN[n]))
        print(f'{n:36} bg {L[n]["bg"]:#7x} solved {L[n]["pt"] if L[n]["pt"] is None else hex(L[n]["pt"])} votes {[(hex(a), c) for a, c in v.most_common(3)]}' + ('  ACCEPT' if ok else ''))
        if ok:
            res[n] = top[0]
    if '--write' in sys.argv and res:
        p = 'bindings/manual_fields.json'; d = json.load(open(p))
        m = d['fields'].setdefault(S, {})
        for n, pt in res.items():
            if n not in m:
                m[n] = {'pt': hex(pt), 'why': 'autoprove: unanimous votes from aligned functions whose accesses to proven fields of this struct all match (bindings/autoprove.py)'}
        json.dump(d, open(p, 'w'), indent=1)
        print('written', len(res))
