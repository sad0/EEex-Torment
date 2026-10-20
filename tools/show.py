# Side-by-side BG2EE / Torment disassembly with annotations (known EEex names, fmap, strings).
# Usage: python show.py <bg_rva> <pt_rva> [count] [--from-key]   (rva hex, function or any address)
import sys, json, re
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from ilib import *
import fmap
from fmap import BG, PT

md = Cs(CS_ARCH_X86, CS_MODE_64)
F = {int(k, 16): int(v[0], 16) for k, v in json.load(open('fmap.json')).items()}
RF = {v: k for k, v in F.items()}
NAMES_BG = {}
try:
    for n, r in json.load(open('port2.json')).items():
        if 'bg_key' in r:
            NAMES_BG[int(r['bg_key'], 16)] = n
        if r.get('bg_target'):
            NAMES_BG.setdefault(int(r['bg_target'], 16), n)
except Exception:
    pass


def string_at(pe, rva):
    b = pe.read(rva, 80)
    if not b:
        return None
    s = b.split(b'\0')[0]
    if len(s) >= 3 and all(32 <= c < 127 for c in s):
        return s.decode()
    return None


def annot(pe, i):
    out = []
    m = re.search(r'rip \+ (0x[0-9a-f]+)', i.op_str) or re.search(r'rip - (0x[0-9a-f]+)', i.op_str)
    if m:
        d = int(m.group(1), 16) * (-1 if 'rip -' in i.op_str else 1)
        t = i.address + i.size + d
        s = string_at(pe, t)
        out.append(f'@{t:x}' + (f' "{s[:40]}"' if s else ''))
    if i.mnemonic in ('call', 'jmp') and i.op_str.startswith('0x'):
        t = int(i.op_str, 16)
        if pe is BG:
            nm = NAMES_BG.get(t)
            out.append((nm or '') + (f' ->PT {F[t]:x}' if t in F else ''))
        else:
            b = RF.get(t)
            out.append((f'<-BG {b:x} ' + (NAMES_BG.get(b) or '')) if b is not None else '')
    return ' '.join(x for x in out if x)


def lines(pe, a, n, from_key, around=False):
    start = a if from_key else pe.fstart(a)
    res = []
    if around:
        ins = list(md.disasm(pe.tbytes(start, a - start + 200), start))
        k = next((j for j, i in enumerate(ins) if i.address <= a < i.address + i.size), 0)
        sel = ins[max(0, k - n // 2):k + n // 2]
        return [('>>' if i.address <= a < i.address + i.size else '  ') + f"{i.address:x} {i.mnemonic} {i.op_str}"[:62]
                + ('  ; ' + annot(pe, i) if annot(pe, i) else '') for i in sel]
    for i in md.disasm(pe.tbytes(start, n * 15), start):
        mark = '>>' if i.address <= a < i.address + i.size else '  '
        res.append(f"{mark}{i.address:x} {i.mnemonic} {i.op_str}"[:62] + ('  ; ' + annot(pe, i) if annot(pe, i) else ''))
        if len(res) >= n:
            break
    return res


if __name__ == '__main__':
    bg, pt = int(sys.argv[1], 16), int(sys.argv[2], 16)
    n = int(sys.argv[3]) if len(sys.argv) > 3 and not sys.argv[3].startswith('-') else 40
    fk = '--from-key' in sys.argv
    ar = '--around' in sys.argv
    A, B = lines(BG, bg, n, fk, ar), lines(PT, pt, n, fk, ar)
    print('BG', '-' * 60); print('\n'.join(A))
    print('PT', '-' * 60); print('\n'.join(B))
