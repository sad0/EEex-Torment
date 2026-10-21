# Labels labelcheck.py cannot judge (leaf functions without .pdata, data labels):
#  - functions: whole-body similarity BG vs PT (tools/fdiff.py);
#  - data: every BG RIP-relative reference to the BG address, inside an fmap-aligned function, must map to a
#    PT instruction referencing the PT label (votes for / against).
import sys, json, io, contextlib, struct, collections, re
import numpy as np
import capstone
from fmap import BG, PT, align
from fdiff import diff

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64); md.detail = True
G = json.load(open('gen_report.json')); R = json.load(open('port2.json'))
F = {int(k, 16): int(v[0], 16) for k, v in json.load(open('fmap.json')).items()}


def riprefs(pe, target):
    a = np.frombuffer(pe.text, dtype=np.uint8)
    d = (a[:-3].astype(np.int64) | (a[1:-2].astype(np.int64) << 8) | (a[2:-1].astype(np.int64) << 16) | (a[3:].astype(np.int64) << 24))
    d = np.where(d >= 2**31, d - 2**32, d)
    pos = np.arange(len(d)) + pe.tva
    out = []
    for k in range(4, 9):
        for p in np.nonzero(pos + k + d == target)[0]:
            for back in range(7, 0, -1):
                s = int(p) + pe.tva - back
                try:
                    i = next(md.disasm(pe.tbytes(s, 16), s))
                except StopIteration:
                    continue
                if i.address + i.size == int(p) + pe.tva + k and 'rip' in i.op_str:
                    out.append(i.address); break
    return sorted(set(out))


def target_of(pe, a):
    i = next(md.disasm(pe.tbytes(a, 16), a))
    for o in i.operands:
        if o.type == capstone.x86_const.X86_OP_MEM and o.mem.base == capstone.x86_const.X86_REG_RIP:
            return i.address + i.size + o.mem.disp
    return None


if __name__ == '__main__':
    out = []
    for k, g in G.items():
        if g.get('status') != 'ported' or k.startswith(('Hook-', 'Data-')) or k not in R:
            continue
        site = R[k].get('bg_key'); p = g.get('addr')
        if not site or not p:
            continue
        b, p = int(site, 16), int(p, 16)
        if BG.read(b - 1, 1) in (bytes([0xe8]), bytes([0xe9])):
            b = b + 4 + struct.unpack('<i', BG.read(b, 4))[0]
        if R[k].get('bg_target'):
            b = int(R[k]['bg_target'], 16)
        if BG.rfunc(b) and BG.rfunc(b)[0] in F:
            continue  # judged by labelcheck.py
        in_text = BG.tva <= b < BG.tva + BG.tsize
        if in_text:
            with contextlib.redirect_stdout(io.StringIO()):
                r = diff(b, p, show=False)
            out.append((k, 'func', round(r, 3)))
            continue
        votes = collections.Counter()
        for ref in riprefs(BG, b)[:40]:
            fr = BG.rfunc(ref)
            if not fr or fr[0] not in F:
                continue
            mp, ratio, _, _ = align(fr[0], F[fr[0]])
            if ref not in mp:
                continue
            t = target_of(PT, mp[ref])
            votes['ok' if t is not None and abs(t - p) < 0x100 and t - p == (b - b) + (t - p) and t == p else ('near' if t is not None and abs(t - p) < 0x40 else 'other')] += 1
        out.append((k, 'data', dict(votes)))
    bad = [o for o in out if (o[1] == 'func' and o[2] < 0.9) or (o[1] == 'data' and (o[2].get('ok', 0) == 0 or o[2].get('other', 0) > o[2].get('ok', 0)))]
    print('checked', len(out), 'suspicious', len(bad))
    for o in out:
        print(('!! ' if o in bad else '   '), o)
