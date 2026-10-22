# Map CGameOptions fields BG -> PT through CGameOptions::GetOption(id, category): for every
# (category, id) the first field read through the game object in BG and in PT.
import sys, collections
from ilib import PE, BG_EXE
from swemu import run, Sym
BG = PE(BG_EXE); PT = PE('E:/Enhanced Edition/Environnement de test/PSTEE (EEex dev)/Torment.exe')


def table(pe, f, gamekey, kindw='read', extra=None, skip=False):
    out = {}
    for cat in range(0, 16):
        for oid in range(0, 260):
            regs = {'RCX': Sym('this'), 'RDX': oid, 'R8': cat}
            if kindw != 'read':   # SetOption(this, id, value, category)
                regs = {'RCX': Sym('this'), 'RDX': oid, 'R8': 1, 'R9': cat}
            acc = run(pe, f, regs, {}, max_steps=3000, skip_calls=skip)
            for kind, a, n, ia in acc:
                if kind in ('read', 'write') and isinstance(a, Sym) and gamekey in a.name:
                    out[(cat, oid)] = (a.off, n); break
    return out


MODE = sys.argv[2] if len(sys.argv) > 2 else 'get'
if MODE == 'get':
    B = table(BG, 0x1ed070, '+0x1090]')
    P = table(PT, 0x20e010, '+0x10c8]')
else:
    B = table(BG, 0x1ee850, '+0x1090]', 'write', {'R9': 1}, True)
    P = table(PT, 0x20fb50, '+0x10c8]', 'write', {'R9': 1}, True)
print('cases BG', len(B), 'PT', len(P))
pairs = collections.Counter()
for k in sorted(set(B) & set(P)):
    pairs[(B[k], P[k])] += 1
for (b, p), c in sorted(pairs.items()):
    print(f'BG {b[0]:#x}/{b[1]} -> PT {p[0]:#x}/{p[1]}  delta {p[0] - b[0]:+#x}  x{c}')
only = [(k, B[k]) for k in B if k not in P][:10]
print('BG only', only)
print('PT only', [(k, P[k]) for k in P if k not in B][:20])
