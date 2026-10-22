# sizeof(S) in Torment from allocation sites: `mov ecx, N; call operator new; ...; call S::S` where
# S::S is a named constructor (bgnames.json / ptnames.json). Collected independently in BG and PT
# (BG N must equal the BG struct size, which validates the pattern). Output: allocsizes.json
# {S: {"bg": [sizes], "pt": [sizes]}} and a summary of proven PT sizes.
import sys, os, json, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import capstone
from capstone import x86_const as X
from ilib import PE, BG_EXE
import bgtypes as T

BG = PE(BG_EXE); PT = PE('E:/Enhanced Edition/Environnement de test/PSTEE (EEex dev)/Torment.exe')
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
NEW = {'BG': 0x4f7a88, 'PT': 0x580078}


def ctors(names):
    out = {}
    for a, n in names.items():
        if '::' in n:
            c, f = n.rsplit('::', 1)
            if c == f and c in T.structs:
                out[int(a, 16)] = c
    return out


def scan(pe, new, ct):
    res = collections.defaultdict(list)
    for b, e, u in pe.rf:
        size, after_new = None, 0
        for i in md.disasm(pe.tbytes(b, e - b), b):
            if i.mnemonic == 'mov' and i.op_str.startswith('ecx, 0x'):
                try:
                    size = int(i.op_str.split(', ')[1], 16); after_new = 0
                except ValueError:
                    pass
            elif i.mnemonic == 'call' and i.op_str.startswith('0x'):
                t = int(i.op_str, 16)
                if t == new and size is not None:
                    after_new = 12          # the constructor must follow within a few instructions
                    pending = size
                    continue
                if after_new and t in ct:
                    res[ct[t]].append(pending)
                after_new = 0
            if after_new:
                after_new -= 1
    return res


B = scan(BG, NEW['BG'], ctors(json.load(open('bgnames.json'))))
P = scan(PT, NEW['PT'], ctors(json.load(open('ptnames.json'))))
out = {}
proven = {}
for s in sorted(set(B) | set(P)):
    bs, ps = sorted(set(B.get(s, []))), sorted(set(P.get(s, [])))
    out[s] = {'bg': bs, 'pt': ps}
    st = T.structs.get(s)
    if st and bs == [st.size] and len(ps) == 1:
        proven[s] = ps[0]
json.dump(out, open('bindings/allocsizes.json', 'w'), indent=0)
L = json.load(open('bindings/ptlayout.json'))
diff = [(s, hex(T.structs[s].size), hex(p), L.get(s, {}).get('pt_size') and hex(L[s]['pt_size'])) for s, p in proven.items()]
print('structs with allocation sites', len(out), 'proven PT sizes', len(proven))
for d in diff:
    if d[2] != d[3]:
        print('  solver disagrees', d)
if '--write' in sys.argv:
    p = 'bindings/manual_fields.json'; d = json.load(open(p))
    for s, sz in proven.items():
        if s not in d['sizes']:
            d['sizes'][s] = {'pt': hex(sz), 'why': 'allocation size: mov ecx, N; call operator new; call S::S (BG N == BG sizeof) in BG and PT (bindings/allocsizes.py)'}
    json.dump(d, open(p, 'w'), indent=1)
    print('written')
