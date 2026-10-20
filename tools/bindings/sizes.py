# PT struct sizes from aligned allocation sites: BG `mov ecx, sizeof(S); call operator_new`
# followed by S's constructor call (typed member function) or S's vtable store; the aligned PT
# `mov ecx, imm` gives sizeof(S) in Torment. Output: bindings/sizes.json {S: {pt_size: votes}}
import sys, os, json, collections, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.chdir(os.path.join(os.path.dirname(__file__), '..'))
import bindings.fieldmap as FM
from fmap import BG, PT, align, fragments, func_insns
from ilib import parse_db, UP_DB
from gen import bg_final

NEW_BG, NEW_PT = 0x4f7a88, 0x580078
UP = parse_db(UP_DB)
vt2s = {}
for n in UP:
    if n.endswith('::VFTable'):
        a = bg_final(n)
        if a is not None:
            vt2s[a] = n[:-9]
ctor2s = {f: r[FM.X.X86_REG_RCX] for f, r in FM.entry_types.items() if FM.X.X86_REG_RCX in r}
SZ = collections.defaultdict(collections.Counter)
for bgf, ptf in FM.F.items():
    a = [x for g in fragments('BG', bgf) for x in func_insns('BG', g)]
    if not any(x[3] == 'call' and x[4] == hex(NEW_BG) for x in a):
        continue
    mp, ratio, _, _ = align(bgf, ptf)
    for k, x in enumerate(a):
        if not (x[3] == 'call' and x[4] == hex(NEW_BG)):
            continue
        # size: nearest preceding mov ecx, imm
        sz = None
        for j in range(k - 1, max(-1, k - 6), -1):
            m = re.fullmatch(r'ecx, (0x[0-9a-f]+|\d+)', a[j][4]) if a[j][3] == 'mov' else None
            if m:
                sz = (j, int(m.group(1), 0)); break
        if not sz or a[sz[0]][0] not in mp:
            continue
        pa = mp[a[sz[0]][0]]
        pi = next(iter(FM.md.disasm(PT.tbytes(pa, 16), pa)), None)
        if not pi or pi.mnemonic != 'mov' or not pi.op_str.startswith('ecx, '):
            continue
        ptsz = int(pi.op_str.split(', ')[1], 0)
        cls = None
        for y in a[k + 1:k + 14]:
            if y[3] == 'call' and y[4].startswith('0x') and int(y[4], 16) in ctor2s:
                cls = ctor2s[int(y[4], 16)]; break
            m = re.search(r'\[rip ([+-]) (0x[0-9a-f]+)\]', y[4])
            if y[3] == 'lea' and m:
                t = y[0] + y[1] + int(m.group(2), 16) * (1 if m.group(1) == '+' else -1)
                if t in vt2s:
                    cls = vt2s[t]; break
        if cls:
            SZ[cls][(sz[1], ptsz)] += 1
out = {}
for c, v in SZ.items():
    out[c] = {f'{hex(b)}->{hex(p)}': n for (b, p), n in v.items()}
    print(c, out[c])
json.dump(out, open('bindings/sizes.json', 'w'), indent=1)
