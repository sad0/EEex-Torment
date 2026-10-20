# Count file signatures/versions per resource type in a game's BIFs (chitin.key) + override.
#   python filesigs.py <game dir> [max per type]
import sys, os, struct, collections

G = sys.argv[1]
MAXN = int(sys.argv[2]) if len(sys.argv) > 2 else 400
T = {0x3f1: 'CRE', 0x3f2: 'ARE', 0x3ed: 'ITM', 0x3ee: 'SPL', 0x3f6: 'STO', 0x3e9: 'WED', 0x3f7: 'WMP', 0x3fd: 'PRO',
     0x3e8: 'BAM', 0x3ec: 'MOS', 0x3f8: 'EFF', 0x3fb: 'VVC', 0x3f9: 'VEF', 0x3ea: 'CHU', 0x3f3: 'DLG', 0x3fc: 'VEF?', 0x3eb: 'TIS', 0x006: 'PLT', 0x3f5: 'BS', 0x3fe: 'WFX', 0x3f4: '2DA', 0x3f0: 'IDS'}
k = open(os.path.join(G, 'chitin.key'), 'rb').read()
nb, nr, ob, orr = struct.unpack_from('<IIII', k, 8)
bifs = []
for i in range(nb):
    ln, fo, fl, loc = struct.unpack_from('<IIHH', k, ob + 12 * i)
    bifs.append(k[fo:fo + fl].rstrip(b'\0').decode().replace(chr(92), '/'))
want = collections.defaultdict(list)
for i in range(nr):
    name, typ, loc = struct.unpack_from('<8sHI', k, orr + 14 * i)
    if typ in T and len(want[typ]) < MAXN:
        want[typ].append((name.rstrip(b'\0').decode('latin-1'), loc))
cache = {}
sig = collections.defaultdict(collections.Counter)
sizes = collections.defaultdict(collections.Counter)


def bif(bi):
    if bi not in cache:
        p = os.path.join(G, bifs[bi])
        cache[bi] = open(p, 'rb').read() if os.path.exists(p) else None
    return cache[bi]


for typ, lst in want.items():
    for name, loc in lst:
        b = bif(loc >> 20)
        if not b or b[:4] != b'BIFF':
            continue
        nf, nt, off = struct.unpack_from('<III', b, 8)
        idx = loc & 0x3fff
        if idx >= nf:
            continue
        l, o, sz, t = struct.unpack_from('<IIIH', b, off + 16 * idx)
        sig[T[typ]][b[o:o + 8]] += 1
for t, c in sorted(sig.items()):
    print(t, dict(c.most_common(5)))
