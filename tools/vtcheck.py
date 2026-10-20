# Locate vtables in Torment by slot content: every BG vtable slot is mapped through fmap.json and
# compared position-by-position with each Torment vtable (.rdata addresses loaded by a RIP-relative
# LEA in code, bounded by the next such address). Usage: vt_match(bg_vt_rva) -> (pt_rva, score, n)
import json, struct, re, bisect
import numpy as np
from ilib import *

BG, PT = PE(BG_EXE), PE(PT_EXE)
F = {int(k, 16): int(v[0], 16) for k, v in json.load(open('fmap.json')).items()}


def lea_targets(pe):
    a = np.frombuffer(pe.text, dtype=np.uint8)
    rex = (a[:-6] == 0x48) | (a[:-6] == 0x4C)
    lea = a[1:-5] == 0x8D
    modrm = (a[2:-4] & 0xC7) == 0x05
    d = a[3:-3].astype(np.int64) | (a[4:-2].astype(np.int64) << 8) | (a[5:-1].astype(np.int64) << 16) | (a[6:].astype(np.int64) << 24)
    d = np.where(d >= 2**31, d - 2**32, d)
    pos = np.nonzero(rex & lea & modrm)[0]
    t = pos + pe.tva + 7 + d[pos]
    rd = [s for s in pe.secs if s[0] == '.rdata'][0]
    t = t[(t >= rd[1]) & (t < rd[1] + rd[4])]
    return sorted(set(int(x) for x in t))


def slots(pe, rva, end):
    out = []
    while rva < end:
        v = struct.unpack('<Q', pe.read(rva, 8))[0] - pe.base
        if not (pe.tva <= v < pe.tva + pe.tsize):
            break
        out.append(v); rva += 8
    return out


class VT:
    def __init__(s, pe):
        s.pe = pe; s.starts = lea_targets(pe)

    def get(s, rva):
        i = bisect.bisect_right(s.starts, rva)
        end = s.starts[i] if i < len(s.starts) else rva + 8 * 300
        return slots(s.pe, rva, min(end, rva + 8 * 300))


BV, PV = VT(BG), VT(PT)
PT_VTS = None


def vt_match(bgvt):
    global PT_VTS
    if PT_VTS is None:
        PT_VTS = [(a, PV.get(a)) for a in PV.starts]
        PT_VTS = [(a, s) for a, s in PT_VTS if len(s) >= 2]
    bs = BV.get(bgvt)
    if len(bs) < 2:
        return None, 0, len(bs)
    import difflib
    m = [F.get(f, ('bg', f)) for f in bs]
    known = sum(1 for f in bs if f in F)
    sm = difflib.SequenceMatcher(autojunk=False); sm.set_seq2(m)
    best = []
    for a, ps in PT_VTS:
        if abs(len(ps) - len(bs)) > max(8, len(bs) // 3):
            continue
        sm.set_seq1(ps)
        hit = sum(n for i, j, n in sm.get_matching_blocks())
        # slots unique to this class weigh more than inherited ones
        sc = hit / max(1, known)
        best.append((sc, hit, a, len(ps)))
    best.sort(reverse=True)
    return best[:3], len(bs)
