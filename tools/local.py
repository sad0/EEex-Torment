# Second-pass resolver for entries gen.py left unresolved: local window search.
#  - find the PT function for the BG function containing the key (fmap, cold fragment parent, or the
#    callee reached by locally matching a BG call site inside a mapped caller);
#  - slide a normalized-instruction window (BG key +/- W) over the PT function, keep the best match.
# Output: local.json {name: {addr, ratio, func, how}}
import json, difflib, collections, sys
import fmap
from fmap import BG, PT, func_insns, callers, align
from ilib import classify

F = {int(k, 16): int(v[0], 16) for k, v in json.load(open('fmap.json')).items()}
R = json.load(open('port2.json'))
G = json.load(open('gen_report.json'))


def ins_list(name, f):
    return list(func_insns(name, f))


def local_search(bgf, key, ptf, w=8):
    a = ins_list('BG', bgf); b = ins_list('PT', ptf)
    k = next((i for i, x in enumerate(a) if x[0] <= key < x[0] + x[1]), None)
    if k is None or not b:
        return None
    lo, hi = max(0, k - w), min(len(a), k + w + 1)
    win = [x[2] for x in a[lo:hi]]
    pos_in = k - lo
    best = []
    bn = [x[2] for x in b]
    sm = difflib.SequenceMatcher(autojunk=False)
    sm.set_seq2(win)
    for s in range(0, max(1, len(b) - len(win) + 1)):
        seg = bn[s:s + len(win)]
        if seg[pos_in:pos_in + 1] != win[pos_in:pos_in + 1]:
            continue  # the key instruction itself must match
        sm.set_seq1(seg)
        best.append((sm.ratio(), s + pos_in))
    if not best:
        return None
    best.sort(reverse=True)
    r, j = best[0]
    r2 = best[1][0] if len(best) > 1 else 0
    return b[j][0] + (key - a[k][0]), r, r2


def pt_func_for(bgf):
    if bgf in F:
        return F[bgf], 'fmap'
    fr = BG.rfrag(bgf); pr = BG.rfunc(bgf)
    if fr and pr and fr[0] != pr[0] and pr[0] in F:
        # cold fragment: best-matching fragment of the mapped parent
        best = None
        for b, e, u in PT.rf:
            p = PT.rfunc(b)
            if p and p[0] == F[pr[0]] and p[0] != b:
                r = align(fr[0], b)[1]
                if not best or r > best[1]:
                    best = (b, r)
        if best and best[1] >= 0.3:
            return best[0], f'frag({best[1]:.2f})'
    # via callers: locate the call site in the mapped caller by local search
    v = collections.Counter()
    for site, op in callers(BG, bgf):
        g = BG.fstart(site)
        if g not in F:
            continue
        res = local_search(g, site, F[g])
        if res and res[1] >= 0.6 and res[1] - res[2] >= 0.1:
            ps = res[0]
            if PT.tbytes(ps, 1)[0] in (0xE8, 0xE9):
                v[ps + 5 + PT.i32(ps + 1)] += 1
    if v:
        (t, c), = v.most_common(1)
        return t, f'callers({c}/{sum(v.values())})'
    return None, None


def call_anchor(bgf, key, ptf):
    """Key at (or right after) a direct call to T: find the matching call to F[T] in the PT function.
    Returns (addr, how) or None."""
    a = ins_list('BG', bgf); b = ins_list('PT', ptf)
    k = next((i for i, x in enumerate(a) if x[0] <= key < x[0] + x[1]), None)
    if k is None:
        return None
    after = False
    x = a[k]
    if not (x[3] == 'call' and x[4].startswith('0x')):
        if k > 0 and a[k - 1][3] == 'call' and a[k - 1][4].startswith('0x') and a[k - 1][0] + a[k - 1][1] == key:
            x = a[k - 1]; after = True; k -= 1
        else:
            return None
    t = int(x[4], 16)
    if t not in F:
        return None
    bt = [i for i, y in enumerate(a) if y[3] == 'call' and y[4] == x[4]]
    pt = [i for i, y in enumerate(b) if y[3] == 'call' and y[4] == hex(F[t])]
    if not pt:
        return None
    if len(pt) == 1:
        j = pt[0]; how = 'call-anchor(unique)'
    elif len(pt) == len(bt):
        j = pt[bt.index(k)]; how = f'call-anchor(ordinal {bt.index(k) + 1}/{len(bt)})'
    else:
        # pick the PT call whose local context matches best
        win = [y[2] for y in a[max(0, k - 6):k + 7]]
        sc = []
        for j in pt:
            seg = [y[2] for y in b[max(0, j - 6):j + 7]]
            sc.append((difflib.SequenceMatcher(None, win, seg, autojunk=False).ratio(), j))
        sc.sort(reverse=True)
        if len(sc) > 1 and sc[0][0] - sc[1][0] < 0.1:
            return None
        j = sc[0][1]; how = f'call-anchor(ctx {sc[0][0]:.2f}, {len(bt)}bg/{len(pt)}pt)'
    y = b[j]
    addr = y[0] + y[1] if after else y[0] + (key - a[k][0])
    return addr, how


def main():
    X = json.load(open('final.json'))
    out = {}
    for n, rep in G.items():
        # everything the main pipeline could not settle (or gen rejected), independent of local.json
        if n not in R or 'bg_key' not in R[n]:
            continue
        if X.get(n, {}).get('result') == 'ok' and not (rep['status'] == 'unresolved') and not rep.get('fnconflict'):
            continue
        key = int(R[n]['bg_key'], 16)
        bgf = BG.fstart(key)
        ptf, how = pt_func_for(bgf)
        if ptf is None:
            out[n] = {'how': 'no PT function'}; continue
        if key == bgf:
            out[n] = {'addr': hex(ptf), 'how': how, 'ratio': None}; continue
        bp = BG.rfunc(key); bp = bp[0] if bp else bgf
        if bp in F:
            a2 = anchor2(bp, key, F[bp])
            if a2 and (a2[3] == 1 and a2[1] >= 0.5 or a2[1] >= 0.5 and a2[1] - a2[2] >= 0.1):
                out[n] = {'addr': hex(a2[0]), 'how': f'anchor2({a2[1]:.2f}/{a2[2]:.2f},{a2[3]})', 'func': hex(F[bp]), 'ratio': 'anchor'}; continue
        ca = call_anchor(bgf, key, ptf)
        if ca:
            out[n] = {'addr': hex(ca[0]), 'how': how + ' / ' + ca[1], 'func': hex(ptf), 'ratio': 'call'}; continue
        res = local_search(bgf, key, ptf)
        if not res:
            out[n] = {'how': how + ' / key instr not found', 'func': hex(ptf)}; continue
        out[n] = {'addr': hex(res[0]), 'ratio': round(res[1], 2), 'second': round(res[2], 2), 'how': how, 'func': hex(ptf)}
    json.dump(out, open('local.json', 'w'), indent=1)
    c = collections.Counter()
    for n, v in out.items():
        print(f"{n[:60]:60} {v}")


def all_insns(name, f):
    pe = BG if name == 'BG' else PT
    out = []
    for g in fmap.fragments(name, f):
        out += list(func_insns(name, g))
    return out


def callee(x):
    if x[3] == 'call' and x[4].startswith('0x'):
        return int(x[4], 16)
    return None


def anchor2(bgp, key, ptp, reach=40):
    """Locate key between the nearest mapped direct calls around it (whole function incl. fragments)."""
    a = all_insns('BG', bgp); b = all_insns('PT', ptp)
    k = next((i for i, x in enumerate(a) if x[0] <= key < x[0] + x[1]), None)
    if k is None:
        return None
    p = next((i for i in range(k - 1, max(-1, k - reach), -1) if callee(a[i]) in F), None)
    q = next((i for i in range(k + (0 if callee(a[k]) not in F else 1), min(len(a), k + reach)) if callee(a[i]) in F), None)
    if p is None and q is None:
        return None
    lo = p if p is not None else max(0, k - 8)
    hi = q if q is not None else min(len(a) - 1, k + 8)
    seg = [x[2] for x in a[lo:hi + 1]]
    cands = []
    Ps = [i for i, y in enumerate(b) if p is not None and callee(y) == F[callee(a[p])]] if p is not None else [None]
    Qs = [i for i, y in enumerate(b) if q is not None and callee(y) == F[callee(a[q])]] if q is not None else [None]
    span = hi - lo
    for P in Ps:
        for Q in Qs:
            if P is not None and Q is not None and not (0 < Q - P <= 2 * span + 10):
                continue
            s = P if P is not None else max(0, Q - span)
            e = Q if Q is not None else min(len(b) - 1, P + span)
            seg2 = [x[2] for x in b[s:e + 1]]
            sm = difflib.SequenceMatcher(None, seg, seg2, autojunk=False)
            mp = {}
            for i, j, n in sm.get_matching_blocks():
                for t in range(n):
                    mp[i + t] = j + t
            if (k - lo) in mp:
                cands.append((sm.ratio(), b[s + mp[k - lo]][0] + (key - a[k][0]), P, Q))
    if not cands:
        return None
    cands.sort(reverse=True)
    r = cands[0][0]; r2 = cands[1][0] if len(cands) > 1 else 0
    return cands[0][1], r, r2, len(cands)


if __name__ == '__main__':
    main()
