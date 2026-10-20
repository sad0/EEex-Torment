# Extend fmap.json with fuzzy matches for functions PST modified: candidates come from the call
# neighbourhood (callees of mapped callers, callers of mapped callees) and are ranked by
# normalized-instruction alignment ratio.
import json, collections
import fmap
from fmap import BG, PT, align, func_insns, call_targets_in, callers
from globalmap import funcs


def main():
    J = json.load(open('fmap.json'))
    known = {int(k, 16): int(v[0], 16) for k, v in J.items()}
    meth = {int(k, 16): v[1] for k, v in J.items()}
    bf = funcs(BG)
    for it in range(6):
        used = set(known.values())
        # BG caller map: callee -> callers (function starts)
        new = {}
        for f in bf:
            if f in known:
                continue
            cand = collections.Counter()
            for site, op in callers(BG, f):
                g = BG.fstart(site)
                if g in known:
                    for ps, t in call_targets_in('PT', known[g]):
                        if t not in used:
                            cand[t] += 1
            for site, t in call_targets_in('BG', f):
                if t in known:
                    for ps, op in callers(PT, known[t]):
                        h = PT.fstart(ps)
                        if h not in used:
                            cand[h] += 1
            if not cand:
                continue
            na = len(func_insns('BG', f))
            if na < 4:
                continue
            sc = []
            for c, n in cand.most_common(6):
                nb = len(func_insns('PT', c))
                if nb < 4 or not (0.4 < nb / na < 2.5):
                    continue
                sc.append((align(f, c)[1], n, c))
            if not sc:
                continue
            sc.sort(reverse=True)
            r, n, c = sc[0]
            r2 = sc[1][0] if len(sc) > 1 else 0
            if r >= 0.5 and r - r2 >= 0.1:
                new[f] = (c, r)
        # resolve collisions: keep best ratio per PT function
        byp = {}
        for f, (c, r) in new.items():
            if c not in byp or byp[c][1] < r:
                byp[c] = (f, r)
        n_add = 0
        for c, (f, r) in byp.items():
            known[f] = c; meth[f] = f'fuzzy{it}({r:.2f})'; n_add += 1
        print('fuzzy iter', it, 'added', n_add, 'total', len(known))
        if not n_add:
            break
    json.dump({hex(k): [hex(v), meth[k]] for k, v in known.items()}, open('fmap.json', 'w'), indent=0)


if __name__ == '__main__':
    main()
