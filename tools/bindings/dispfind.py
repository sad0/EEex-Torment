# Find BG instructions using displacement D in functions that also use the given companion
# displacements (identifies methods of one class), and show the aligned PT instruction.
# Usage: python bindings/dispfind.py <disp> <companion disp> [...]   (hex, run from tools/)
import sys, os, json, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone import x86_const as X
from fmap import BG, PT, align, fragments, func_insns
from local import anchor2

md = Cs(CS_ARCH_X86, CS_MODE_64); md.detail = True
F = {int(k, 16): int(v[0], 16) for k, v in json.load(open('fmap.json')).items()}
D = int(sys.argv[1], 16); comp = [int(x, 16) for x in sys.argv[2:]]


def disps(f):
    out = []
    for g in fragments('BG', f):
        for a, sz, n, mn, ops in func_insns('BG', g):
            i = next(iter(md.disasm(BG.tbytes(a, sz), a)), None)
            for op in (i.operands if i else []):
                if op.type == X.X86_OP_MEM and op.mem.base not in (X.X86_REG_RIP, X.X86_REG_RSP, 0):
                    out.append((a, op.mem.disp, i))
    return out


votes = collections.Counter()
for f, g in F.items():
    ds = disps(f)
    s = {d for _, d, _ in ds}
    if D not in s or not all(c in s for c in comp):
        continue
    mp, r, _, _ = align(f, g)
    for a, d, i in ds:
        if d != D:
            continue
        pa = mp.get(a); how = 'align'
        if pa is None:
            a2 = anchor2(BG.rfunc(a)[0] if BG.rfunc(a) else f, a, g)
            if not a2 or a2[1] < 0.5:
                continue
            pa, how = a2[0], f'anchor2 {a2[1]:.2f}'
        pi = next(iter(md.disasm(PT.tbytes(pa, 16), pa)), None)
        if not pi:
            continue
        pd = [op.mem.disp for op in pi.operands if op.type == X.X86_OP_MEM]
        print(f'{f:x}->{g:x} {a:x} {i.mnemonic} {i.op_str:38} | {pa:x} {pi.mnemonic} {pi.op_str:38} [{how}]')
        if pd and pi.mnemonic == i.mnemonic:
            votes[pd[0]] += 1
print('votes', [(hex(a), c) for a, c in votes.most_common(5)])
