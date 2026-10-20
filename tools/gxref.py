# Resolve data targets (globals, vtables, tables) by voting over every BG instruction that references
# the target RIP-relatively: each reference inside a mapped function is located in PT (exact
# alignment, else anchor2) and the PT instruction's own RIP target votes.
# Usage: python gxref.py [name-regex]  -> gxref.json {name: {target, votes, n}}
import sys, re, json, collections
import numpy as np
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
import fmap
from fmap import BG, PT, align
from local import anchor2, F
from gen import bg_final, upentry
from ilib import classify

mdd = Cs(CS_ARCH_X86, CS_MODE_64); mdd.detail = True


def riprefs(pe, t):
    a = np.frombuffer(pe.text, dtype=np.uint8).astype(np.int64)
    x = a[:-3] | (a[1:-2] << 8) | (a[2:-1] << 16) | (a[3:] << 24)
    x = np.where(x >= 2**31, x - 2**32, x)
    pos = np.arange(len(x)) + pe.tva
    out = []
    for p in pos[(pos + 4 + x) == t]:   # disp is last field of the insn (no trailing imm)
        out.append((int(p), 0))
    for tail in (1, 2, 4):               # disp followed by an immediate of `tail` bytes
        for p in pos[(pos + 4 + tail + x) == t]:
            out.append((int(p), tail))
    return out


def insn_at_field(pe, p):
    for d in range(1, 12):
        i = next(iter(mdd.disasm(pe.tbytes(p - d, 16), p - d)), None)
        if i and i.encoding.disp_offset == d and i.encoding.disp_size == 4:
            return i
    return None


def pt_target_of(i):
    return i.address + i.size + i.disp if i is not None else None


def resolve(bgt):
    votes = collections.Counter(); n = 0
    for p, tail in riprefs(BG, bgt):
        bi = insn_at_field(BG, p)
        if bi is None or bi.address + bi.size + bi.disp != bgt:
            continue
        bp = BG.rfunc(bi.address); bp = bp[0] if bp else BG.fstart(bi.address)
        if bp not in F:
            continue
        n += 1
        mp, r, a, b = align(bp, F[bp])
        ps = mp.get(bi.address)
        if ps is None:
            a2 = anchor2(bp, bi.address, F[bp])
            if not a2 or a2[1] < 0.5:
                continue
            ps = a2[0]
        pi = next(iter(mdd.disasm(PT.tbytes(ps, 16), ps)), None)
        if pi is None or pi.mnemonic != bi.mnemonic or not (pi.encoding.disp_size == 4 and 'rip' in pi.op_str):
            continue
        votes[pt_target_of(pi)] += 1
    return votes, n


if __name__ == '__main__':
    G = json.load(open('gen_report.json'))
    rx = sys.argv[1] if len(sys.argv) > 1 else None
    out = {}
    for name, r in G.items():
        if rx and not re.search(rx, name):
            continue
        bt = bg_final(name)
        if bt is None or BG.tva <= bt < BG.tva + BG.tsize:
            continue
        v, n = resolve(bt)
        out[name] = {'bg_target': hex(bt), 'votes': [(hex(a), c) for a, c in v.most_common(3)], 'refs': n}
        if v:
            # pick a PT site with the same instruction form as the BG pattern site
            bk = None
            try:
                bk = int(json.load(open('port2.json'))[name]['bg_key'], 16)
            except Exception:
                pass
            bi = insn_at_field(BG, bk) if bk else None
            ops = upentry(name).get('Operations', '')
            m = re.search(r'READ DWORD, ADD, ADD (\d+)((?:, ADD -?\d+)*)$', ops)
            need_tail = int(m.group(1)) if m else None
            extra = sum(int(x) for x in re.findall(r', ADD (-?\d+)', m.group(2))) if m else 0
            t = v.most_common(1)[0][0] - extra  # address the pattern site must reference
            sites = []
            for p, tail in riprefs(PT, t):
                pi = insn_at_field(PT, p)
                if pi is None or pi.address + pi.size + pi.disp != t:
                    continue
                if need_tail is not None and pi.size - pi.encoding.disp_offset != need_tail:
                    continue
                if bi is not None and pi.mnemonic != bi.mnemonic:
                    continue
                sites.append(hex(p))
            out[name]['sites'] = sites[:8]
        print(f"{name[:50]:50} bg={hex(bt)} refs={n} {out[name]['votes']}")
    json.dump(out, open('gxref.json', 'w'), indent=1)
