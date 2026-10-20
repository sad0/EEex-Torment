# Align named BG/PT function pairs and list PT-BG displacement deltas for memory operands whose BG
# displacement is in [lo, hi] (constructors/operator= give whole-struct layouts).
# Usage (from tools/): python bindings/dispdelta.py <lo> <hi> <BG function name> [...]
import sys, os, json, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import capstone
from capstone import x86_const as X
from fmap import BG, PT, align

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64); md.detail = True
F = {int(k, 16): int(v[0], 16) for k, v in json.load(open('fmap.json')).items()}
NAMES = collections.defaultdict(list)
for a, n in json.load(open('bgnames.json')).items():
    NAMES[n].append(int(a, 16))


def disp(pe, a):
    i = next(iter(md.disasm(pe.tbytes(a, 16), a)), None)
    for op in (i.operands if i else []):
        if op.type == X.X86_OP_MEM and op.mem.base not in (X.X86_REG_RIP, X.X86_REG_RSP):
            return op.mem.disp
    return None


def deltas(lo, hi, names):
    out = collections.defaultdict(collections.Counter)  # bg disp -> Counter(delta)
    for name in names:
        for bf in NAMES.get(name, []):
            if bf not in F:
                print(f'  {name} {bf:#x}: unmapped'); continue
            mp, r, _, _ = align(bf, F[bf])
            print(f'  {name} {bf:#x} -> {F[bf]:#x} ratio {r:.2f}')
            if r < 0.6:
                continue
            for a, pa in mp.items():
                b, p = disp(BG, a), disp(PT, pa)
                if b is not None and p is not None and lo <= b <= hi:
                    out[b][p - b] += 1
    return out


if __name__ == '__main__':
    lo, hi = int(sys.argv[1], 16), int(sys.argv[2], 16)
    res = deltas(lo, hi, sys.argv[3:])
    prev = None
    for b in sorted(res):
        d, c = res[b].most_common(1)[0]
        flag = '' if len(res[b]) == 1 else f'  (also {dict(res[b])})'
        if d != prev or flag:
            print(f'{b:#x}: {d:+#x} x{c}{flag}')
        prev = d
