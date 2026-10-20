# Extend fmap.json using link order: MSVC keeps the function order of each object file, so an
# unmapped BG function lying between two mapped neighbours maps into the same PT address gap.
# Equal-size gaps map ordinally (checked by alignment); otherwise best alignment ratio wins.
import json, bisect, collections
import fmap
from fmap import BG, PT, align, func_insns
from globalmap import funcs


def main():
    J = json.load(open('fmap.json'))
    known = {int(k, 16): int(v[0], 16) for k, v in J.items()}
    meth = {int(k, 16): v[1] for k, v in J.items()}
    bf, pf = funcs(BG), funcs(PT)
    for it in range(6):
        used = set(known.values())
        mapped = sorted(f for f in bf if f in known)
        added = 0
        for i in range(len(mapped) - 1):
            p, q = mapped[i], mapped[i + 1]
            P, Q = known[p], known[q]
            if not (P < Q) or Q - P > 0x40000:
                continue
            lo = bisect.bisect_right(bf, p); hi = bisect.bisect_left(bf, q)
            gap_b = [f for f in bf[lo:hi] if f not in known]
            if not gap_b:
                continue
            lo2 = bisect.bisect_right(pf, P); hi2 = bisect.bisect_left(pf, Q)
            gap_p = [f for f in pf[lo2:hi2] if f not in used]
            if not gap_p:
                continue
            if len(gap_b) == len(gap_p):
                for f, g in zip(gap_b, gap_p):
                    r = align(f, g)[1]
                    if r >= 0.35:
                        known[f] = g; meth[f] = f'order({r:.2f})'; used.add(g); added += 1
            else:
                for f in gap_b:
                    sc = sorted(((align(f, g)[1], g) for g in gap_p if g not in used), reverse=True)
                    if not sc:
                        continue
                    r, g = sc[0]; r2 = sc[1][0] if len(sc) > 1 else 0
                    if r >= 0.5 and r - r2 >= 0.1:
                        known[f] = g; meth[f] = f'gap({r:.2f})'; used.add(g); added += 1
        print('order iter', it, 'added', added, 'total', len(known))
        if not added:
            break
    json.dump({hex(k): [hex(v), meth[k]] for k, v in known.items()}, open('fmap.json', 'w'), indent=0)


if __name__ == '__main__':
    main()
