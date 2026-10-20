# Extract one resource from the game's chitin.key / BIFF V1 archives (override folder first).
#   python bifextract.py <game dir> <RESREF> <ext>     e.g. ITMSLOTS 2da  -> prints / writes it
import sys, os, struct

EXT = {'2da': 0x3f4, 'ids': 0x3f0, 'itm': 0x3ed, 'spl': 0x3ee, 'cre': 0x3f1, 'bcs': 0x3ef, 'menu': 0x408, 'lua': 0x409}
game, ref, ext = sys.argv[1], sys.argv[2].upper(), sys.argv[3].lower()
ov = os.path.join(game, 'override', f'{ref}.{ext}')
if os.path.exists(ov):
    data = open(ov, 'rb').read()
else:
    k = open(os.path.join(game, 'chitin.key'), 'rb').read()
    nb, nr, ob, orr = struct.unpack_from('<IIII', k, 8)
    bifs = []
    for i in range(nb):
        ln, fo, fl, loc = struct.unpack_from('<IIHH', k, ob + 12 * i)
        bifs.append(k[fo:fo + fl].rstrip(b'\0').decode().replace('\\', os.sep))
    data = None
    for i in range(nr):
        name, typ, loc = struct.unpack_from('<8sHI', k, orr + 14 * i)
        if name.rstrip(b'\0').decode('latin-1').upper() == ref and typ == EXT[ext]:
            b = open(os.path.join(game, bifs[loc >> 20]), 'rb').read()
            nf, nt, off = struct.unpack_from('<III', b, 8)
            for j in range(nf):
                l, o, sz, t = struct.unpack_from('<IIIH', b, off + 16 * j)
                if (l & 0x3fff) == (loc & 0x3fff):
                    data = b[o:o + sz]
            break
    if data is None:
        sys.exit('not found')
sys.stdout.write(data.decode('latin-1'))
