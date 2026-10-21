# Untyped aligned-access scan: for BG displacements D (hex list), find aligned BG/PT function pairs where an
# instruction using [reg + D] maps to a PT instruction using [reg + D'] and report D -> D' per function.
#   python dispscan.py 0xb60 0xb64 ...   (restricts to functions whose BG body has such a displacement)
import sys, json, re, collections
from fmap import BG, PT, align
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone import x86_const as X
md = Cs(CS_ARCH_X86, CS_MODE_64); md.detail = True
F = {int(k, 16): int(v[0], 16) for k, v in json.load(open('fmap.json')).items()}
BN = {int(k, 16): v for k, v in json.load(open('bgnames.json')).items()}
want = {int(x, 16) for x in sys.argv[1:]}
pat = re.compile(r'\+ (0x[0-9a-f]+)\]')
res = collections.defaultdict(lambda: collections.defaultdict(set))
cand = collections.defaultdict(set)
t = bytes(BG.text)
for d in want:
    for k in (4, 1):
        b = d.to_bytes(k, 'little') if d < 0x80 or k == 4 else None
        if b is None: continue
        for m in re.finditer(re.escape(b), t):
            fr = BG.rfunc(m.start() + BG.tva)
            if fr and fr[0] in F:
                cand[fr[0]].add(d)
for f in cand:
    mp, r, A, _ = align(f, F[f])
    if r < 0.6:
        continue
    for a, sz, n, mn, ops in A:
        mm = pat.search(ops)
        if not mm or int(mm.group(1), 16) not in want or 'rip' in ops or a not in mp:
            continue
        pi = next(iter(md.disasm(PT.tbytes(mp[a], 16), mp[a])), None)
        if pi is None:
            continue
        pm = pat.search(pi.op_str)
        if pm:
            res[int(mm.group(1), 16)][int(pm.group(1), 16)].add(f)
for d in sorted(res):
    print(hex(d), {hex(p): [BN.get(f, hex(f)) for f in sorted(fs)][:6] + ([f'... {len(fs)}'] if len(fs) > 6 else []) for p, fs in res[d].items()})
