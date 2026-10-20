# Check STOR files against the BG2EE store layout (header 0x9c, item 0x1c, drink 0x14, spell 0xc):
# every section offset/count must fit the file and sections must tile it exactly.
#   python stocheck.py <game dir>
import sys, os, struct, collections

G = sys.argv[1]
k = open(os.path.join(G, 'chitin.key'), 'rb').read()
nb, nr, ob, orr = struct.unpack_from('<IIII', k, 8)
bifs = []
for i in range(nb):
    ln, fo, fl, loc = struct.unpack_from('<IIHH', k, ob + 12 * i)
    bifs.append(k[fo:fo + fl].rstrip(b'\0').decode().replace(chr(92), '/'))
cache = {}
res = collections.Counter(); bad = []
for i in range(nr):
    name, typ, loc = struct.unpack_from('<8sHI', k, orr + 14 * i)
    if typ != 0x3f6:
        continue
    bi = loc >> 20
    if bi not in cache:
        cache[bi] = open(os.path.join(G, bifs[bi]), 'rb').read()
    b = cache[bi]
    nf, nt, off = struct.unpack_from('<III', b, 8)
    l, o, sz, t = struct.unpack_from('<IIIH', b, off + 16 * (loc & 0x3fff))
    d = b[o:o + sz]
    h = lambda x: struct.unpack_from('<I', d, x)[0]
    secs = [(h(0x2c), h(0x30), 0x4), (h(0x34), h(0x38), 0x1c), (h(0x4c), h(0x50), 0x14), (h(0x70), h(0x74), 0xc)]
    # buy types (4 bytes each), items (0x1c), drinks (0x14), spells (0xc); offsets relative to file start
    ok = all(c == 0 or (0x9c <= o_ and o_ + c * e <= sz) for o_, c, e in secs)
    used = 0x9c + sum(c * e for o_, c, e in secs)
    res[(d[:8], ok, used == sz)] += 1
    if not ok or used != sz:
        bad.append((name.rstrip(b'\0').decode(), sz, used, secs))
print(dict(res))
for x in bad[:10]:
    print(' ', x)
