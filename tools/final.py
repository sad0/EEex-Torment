# Merge evidence (byte-window votes, context score, global function map + alignment, current DB)
# into one Torment key address per entry. Output: final.json.
import json, collections, sys
import fmap
from fmap import BG, PT, align, func_insns, map_key
from decide import score, fwd, md

R = json.load(open('port2.json'))
D = json.load(open('decide.json'))
F = {int(k, 16): int(v[0], 16) for k, v in json.load(open('fmap.json')).items()}
FM = {int(k, 16): v[1] for k, v in json.load(open('fmap.json')).items()}


def bg_ins(key):
    fs = BG.fstart(key)
    return next((i for i in md.disasm(BG.tbytes(fs, key - fs + 16), fs) if i.address <= key < i.address + i.size), None)


_frags = None


def pt_frags(primary):
    global _frags
    if _frags is None:
        _frags = collections.defaultdict(list)
        for b, e, u in PT.rf:
            p = PT.rfunc(b)
            if p and p[0] != b:
                _frags[p[0]].append(b)
    return _frags.get(primary, [])


def frag_map(key):
    """Map the BG cold fragment containing key to a PT fragment of the mapped parent function."""
    fr = BG.rfrag(key); pr = BG.rfunc(key)
    if not fr or not pr or fr[0] == pr[0] or pr[0] not in F:
        return None, 0
    best = (None, 0)
    for g in pt_frags(F[pr[0]]):
        r = align(fr[0], g)[1]
        if r > best[1]:
            best = (g, r)
    return best


def containing(key):
    """BG function containing key: nearest mapped function start at or below key whose body covers key."""
    fs = BG.fstart(key)
    if fs in F:
        ins = func_insns('BG', fs)
        if ins and ins[-1][0] + ins[-1][1] > key:
            return fs
    return fs


def resolve(n, r, d):
    out = {'name': n, 'kind': r.get('kind')}
    if r.get('status') != 'voted' and r.get('status') != 'novote':
        out['result'] = 'manual'; out['why'] = r.get('status'); return out
    key = int(r['bg_key'], 16)
    bi = bg_ins(key)
    delta = key - bi.address if bi else 0
    cands = collections.defaultdict(list)
    # 1) global map / alignment
    f = containing(key)
    if f not in F:
        g, fr = frag_map(key)
        if g is not None and fr >= 0.4:
            F[f] = g; out['frag'] = f'{hex(f)}->{hex(g)} ({fr:.2f})'
    if f in F:
        if key == f:
            cands[F[f]].append('fmap')
        else:
            a, ratio, how = map_key(f, F[f], key)
            out['falign'] = round(ratio, 2)
            if a is not None:
                cands[a].append(f'align({ratio:.2f})')
            else:
                out['align_note'] = how
    # 2) votes + decide
    if d.get('addr'):
        cands[int(d['addr'], 16)].append('vote:' + d['decision'])
    if d.get('cur'):
        cands[int(d['cur'], 16)].append('curdb')
    if not cands:
        out['result'] = 'manual'; out['why'] = 'no candidate'; return out
    sc = []
    for a, why in cands.items():
        s, fw, bw = score(bi.address, a - delta)
        sc.append((a, round(s, 2), why))
    # rank: number of agreeing methods, then context score
    sc.sort(key=lambda x: (-len([w for w in x[2] if w != 'curdb']), -x[1]))
    best = sc[0]
    out['addr'] = hex(best[0]); out['score'] = best[1]; out['methods'] = best[2]
    out['alts'] = [(hex(a), s, w) for a, s, w in sc[1:]]
    m = best[2]
    strong_vote = any(w in ('vote:confirmed', 'vote:ported') for w in m)
    struct = any(w == 'fmap' or w.startswith('align') for w in m)
    if struct and strong_vote:
        out['result'], out['conf'] = 'ok', 'high'
    elif struct and best[1] >= 0.5:
        out['result'], out['conf'] = 'ok', 'medium'
    elif strong_vote and best[1] >= 0.7:
        out['result'], out['conf'] = 'ok', 'medium'
    elif best[1] >= 0.85 and len(m) >= 1:
        out['result'], out['conf'] = 'ok', 'low'
    else:
        out['result'], out['conf'] = 'manual', 'low'
    if any(a for a, s, w in sc[1:] if s >= best[1] and set(w) - {'curdb'}):
        out['conflict'] = True
    return out


if __name__ == '__main__':
    res = {n: resolve(n, R[n], D.get(n, {})) for n in R}
    json.dump(res, open('final.json', 'w'), indent=1)
    print(collections.Counter((v['result'], v.get('conf'), bool(v.get('conflict'))) for v in res.values()))
