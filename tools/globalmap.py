# Build a global BG2EE -> Torment function map.
# 1) seeds: functions whose masked first instructions are unique on both sides and equal;
# 2) propagation: call sites inside mapped functions (via alignment) map their callees,
#    repeated until no progress. Output: fmap.json {bg_rva_hex: [pt_rva_hex, method]}.
import json, collections
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
import fmap
from fmap import BG, PT, callers, align, func_insns

mdd = Cs(CS_ARCH_X86, CS_MODE_64); mdd.detail = True


def msig(pe, f, n=10):
    b = bytearray(); cnt = 0
    for i in mdd.disasm(pe.tbytes(f, 160), f):
        if i.mnemonic == 'int3':
            break
        x = bytearray(i.bytes); e = i.encoding
        rip = any(op.type == 3 and op.mem.base == 41 for op in i.operands)
        if e.disp_size and rip:
            x[e.disp_offset:e.disp_offset + e.disp_size] = b'\0' * e.disp_size
        if e.imm_size == 4 and (i.group(1) or i.group(2) or i.group(7)):
            x[e.imm_offset:e.imm_offset + 4] = b'\0' * 4
        b += x; cnt += 1
        if cnt >= n:
            break
    return bytes(b) if len(b) >= 20 else None


def funcs(pe):
    fmap.callers(pe, 0)
    s = {t for t in fmap.CT[id(pe)] if pe.tbytes(t - 1, 1) == b'\xcc'}
    s |= {b for b, e, u in pe.rf if pe.rfunc(b) == (b, e)}  # primary pdata entries
    return sorted(s)


def main():
    bf, pf = funcs(BG), funcs(PT)
    print('functions', len(bf), len(pf))
    bs = collections.defaultdict(list); ps = collections.defaultdict(list)
    for f in bf:
        s = msig(BG, f)
        if s: bs[s].append(f)
    for f in pf:
        s = msig(PT, f)
        if s: ps[s].append(f)
    known = {}
    meth = {}
    for s, l in bs.items():
        if len(l) == 1 and len(ps.get(s, ())) == 1:
            known[l[0]] = ps[s][0]; meth[l[0]] = 'sig'
    print('seeds', len(known))
    propagate(known, meth, dict(known))
    json.dump({hex(k): [hex(v), meth[k]] for k, v in known.items()}, open('fmap.json', 'w'), indent=0)


def propagate(known, meth, todo, tag='prop'):
    """Map callees through exactly-aligned call sites of mapped functions (in place)."""
    votes = collections.defaultdict(collections.Counter)
    for it in range(12):
        new = {}
        for f, g in list(todo.items()):
            mp, r, a, b = align(f, g)
            if r < 0.5:
                continue
            for adr, sz, n, mn, ops in a:
                if mn in ('call', 'jmp') and ops.startswith('0x') and sz == 5 and adr in mp:
                    t = int(ops, 16)
                    if t in known or not (BG.tva <= t < BG.tva + BG.tsize):
                        continue
                    pa = mp[adr]
                    if PT.tbytes(pa, 1)[0] in (0xE8, 0xE9):
                        votes[t][pa + 5 + PT.i32(pa + 1)] += 1
        used = collections.Counter(known.values())
        for t, v in votes.items():
            if t in known:
                continue
            (c, n), *rest = v.most_common(2) + [(None, 0)]
            n2 = rest[0][1] if rest else 0
            if n >= 1 and n > 2 * n2 and c not in used:
                new[t] = c; used[c] += 1
        for t, c in new.items():
            known[t] = c; meth[t] = f'{tag}{it}'
        todo = new
        print('iter', it, 'new', len(new), 'total', len(known))
        if not new:
            break


if __name__ == '__main__':
    main()
