# Locate C2DArray members of CRuleTables (or any struct loaded by resource name): for each string,
# find RIP-relative references in BG and PT and print the nearest `lea rcx, [reg + off]` before it.
# Usage: python bindings/strtable.py DEXMOD WSPECIAL ...   (run from tools/)
import sys, os, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import numpy as np
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from fmap import BG, PT

md = Cs(CS_ARCH_X86, CS_MODE_64)


def str_rva(pe, s):
    d = pe.d; out = []
    i = -1
    while True:
        i = d.find(s + b'\0', i + 1)
        if i < 0:
            break
        if d[i - 1] == 0:
            for n, va, vs, ra, rs in pe.secs:
                if ra <= i < ra + rs:
                    out.append(i - ra + va)
    return out


def refs(pe, t):
    a = np.frombuffer(pe.text, dtype=np.uint8).astype(np.int64)
    x = a[:-3] | (a[1:-2] << 8) | (a[2:-1] << 16) | (a[3:] << 24)
    x = np.where(x >= 2**31, x - 2**32, x)
    pos = np.arange(len(x)) + pe.tva
    return [int(p) for p in pos[(pos + 4 + x) == t]]


for name in sys.argv[1:]:
    for pe, tag in ((BG, 'BG'), (PT, 'PT')):
        for t in str_rva(pe, name.encode()):
            for p in refs(pe, t)[:6]:
                start = p - 60
                ins = list(md.disasm(pe.tbytes(start, 90), start))
                ctx = [i for i in ins if i.address < p + 4][-6:]
                leas = [f'{i.mnemonic} {i.op_str}' for i in ctx if i.mnemonic == 'lea' and 'rip' not in i.op_str]
                print(f'{tag} {name} ref {p:x}: {leas[-2:]}')
