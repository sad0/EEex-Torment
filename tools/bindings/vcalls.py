# Virtual-call slot evidence: in aligned BG/PT functions, pair `call qword ptr [reg + D]` instructions and
# count (BG slot -> PT slot) pairs. A slot that keeps its displacement everywhere is unchanged; a
# shifted slot shows consistent pairs. Typed by the struct the tracker assigned to the vtable register
# when available (field_sites.json is not needed: we read the instruction that loaded the vtable).
# Output: vcalls.json {"D_bg": {"D_pt": count}}
import sys, os, json, collections, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import capstone
from fmap import BG, PT, align, fragments, func_insns

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
F = {int(k, 16): int(v[0], 16) for k, v in json.load(open('fmap.json')).items()}
RX = re.compile(r'^qword ptr \[(r\w+) \+ (0x[0-9a-f]+)\]$')
pairs = collections.defaultdict(collections.Counter)
nf = 0
for f, g in F.items():
    calls = [(a, ops) for x in fragments('BG', f) for a, sz, n, mn, ops in func_insns('BG', x) if mn == 'call' and RX.match(ops)]
    if not calls:
        continue
    mp, r, _, _ = align(f, g)
    if r < 0.7:
        continue
    nf += 1
    for a, ops in calls:
        pa = mp.get(a)
        if pa is None:
            continue
        pi = next(iter(md.disasm(PT.tbytes(pa, 16), pa)), None)
        if pi is None or pi.mnemonic != 'call':
            continue
        mb, mp_ = RX.match(ops), RX.match(pi.op_str)
        if mb and mp_:
            pairs[int(mb.group(2), 16)][int(mp_.group(2), 16)] += 1
json.dump({hex(k): {hex(a): c for a, c in v.items()} for k, v in sorted(pairs.items())}, open('bindings/vcalls.json', 'w'), indent=0)
print('functions', nf)
changed = {k: v for k, v in pairs.items() if v.most_common(1)[0][0] != k}
print('displacements', len(pairs), 'with a different dominant PT displacement', len(changed))
for k in sorted(pairs):
    v = pairs[k]
    top = v.most_common(3)
    flag = '' if top[0][0] == k else '  <-- shifted'
    print(f'  {k:#6x} (slot {k // 8:3}): {[(hex(a), c) for a, c in top]}{flag}')
