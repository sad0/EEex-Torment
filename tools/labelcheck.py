# Cross-check of every ported pattern label against the function map: the BG label value (port2.json
# bg_key, the upstream pattern resolved in our BG exe) is mapped to Torment
# through fmap.json (function entries) and compared with the ported Torment value (gen_report.json addr).
# Labels inside functions are compared by containing function. Disagreements are listed with the code
# similarity of the BG function against both Torment candidates (tools/fdiff.py).
import json, re, io, contextlib, struct
from ilib import parse_db, UP_DB
from fmap import BG, PT
from fdiff import diff

G = json.load(open('gen_report.json')); R = json.load(open('port2.json'))
F = {int(k, 16): int(v[0], 16) for k, v in json.load(open('fmap.json')).items()}
UP = parse_db(UP_DB)


def apply_ops(pe, site, ops):
    """InfinityLoader pattern Operations: ADD n, PUSH, READ DWORD/BYTE/QWORD, ADD (pop + add)."""
    cur, stack = site, []
    for op in [o.strip() for o in ops.split(',') if o.strip()]:
        p = op.split()
        if p[0] == 'ADD' and len(p) == 2:
            cur += int(p[1], 0)
        elif p[0] == 'ADD':
            cur += stack.pop()
        elif p[0] == 'PUSH':
            stack.append(cur)
        elif p[0] == 'READ':
            size = {'BYTE': 1, 'WORD': 2, 'DWORD': 4, 'QWORD': 8}[p[1]]
            v = int.from_bytes(pe.read(cur, size), 'little', signed=(size == 4))
            cur = v
        else:
            return None
    return cur


def func(pe, a):
    fr = pe.rfunc(a)
    return fr[0] if fr else None


if __name__ == '__main__':
    bad, ok, unk = [], 0, 0
    for k, g in G.items():
        if g.get('status') != 'ported' or k.startswith(('Hook-', 'Data-')) or k not in R:
            continue
        site = R[k].get('bg_key'); p = g.get('addr')
        if not site or not p:
            continue
        site, p = int(site, 16), int(p, 16)
        b = site  # port2.json bg_key is the resolved BG label value, or the rel32 of a call/jmp to it
        if BG.read(site - 1, 1) in (bytes([0xe8]), bytes([0xe9])):
            b = site + 4 + struct.unpack('<i', BG.read(site, 4))[0]
        fb, fp = func(BG, b), func(PT, p)
        if fb is None or fp is None or fb not in F:
            unk += 1
            continue
        if F[fb] == fp:
            ok += 1
            continue
        with contextlib.redirect_stdout(io.StringIO()):
            r_lab = diff(fb, fp, show=False)
            r_map = diff(fb, F[fb], show=False)
        bad.append((k, hex(b), hex(p), hex(F[fb]), round(r_lab, 3), round(r_map, 3)))
    print('labels consistent', ok, 'unknown', unk, 'disagree', len(bad))
    for x in sorted(bad, key=lambda x: x[4] - x[5]):
        print(f'  {x[0]:55} BG {x[1]}  label {x[2]} ({x[4]})  fmap {x[3]} ({x[5]})')
