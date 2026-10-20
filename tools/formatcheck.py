# Validate Torment's game files against the BG2EE file-format structs (sizes from the BG type model):
# every section (offset, count) of every file must lie inside the file, after the header.
#   python formatcheck.py <game dir>
import sys, os, struct, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bindings'))
import bgtypes as T

G = sys.argv[1]
SZ = lambda s: T.structs[s].size
# type: (signature, header struct, header size incl. signature, [(name, off field, count field, count bytes, entry struct or size)])
FMT = {
    0x3f1: ('CRE V1.0', 'CCreatureFileHeader', 0x2d4, [
        ('known spells', 0x2a0, 0x2a4, 4, 'CCreatureFileKnownSpell'),
        ('memorized levels', 0x2a8, 0x2ac, 4, 'CCreatureFileMemorizedSpellLevel'),
        ('memorized spells', 0x2b0, 0x2b4, 4, 'CCreatureFileMemorizedSpell'),
        ('items', 0x2bc, 0x2c0, 4, 'CCreatureFileItem'),
        ('effects', 0x2c4, 0x2c8, 4, 0x108)]),
    0x3ed: ('ITM V1  ', 'Item_Header_st', 0x72, [
        ('abilities', 0x64, 0x68, 2, 'Item_ability_st'),
        ('effects', 0x6a, 0x70, 2, 'Item_effect_st')]),
    0x3ee: ('SPL V1  ', 'Spell_Header_st', 0x72, [
        ('abilities', 0x64, 0x68, 2, 'Spell_ability_st'),
        ('effects', 0x6a, 0x70, 2, 'Item_effect_st')]),
    0x3f2: ('AREAV1.0', 'CAreaFileHeader', 0x11c, [
        ('actors', 0x54, 0x58, 2, 0x110), ('regions', 0x5c, 0x5a, 2, 0xc4),
        ('spawns', 0x60, 0x64, 4, 'CAreaFileRandomMonsterSpawningPoint'),
        ('entrances', 0x68, 0x6c, 4, 'CAreaFileCharacterEntryPoint'),
        ('containers', 0x70, 0x74, 2, 'CAreaFileContainer'), ('items', 0x78, 0x76, 2, 0x14),
        ('vertices', 0x7c, 0x80, 2, 4), ('ambients', 0x84, 0x82, 2, 'CAreaFileSoundObject'),
        ('variables', 0x88, 0x8c, 4, 0x54), ('doors', 0xa8, 0xa4, 4, 0xc8),
        ('animations', 0xb0, 0xac, 4, 'CAreaFileStaticObject'), ('tiled objects', 0xb8, 0xb4, 4, 0x6c),
        ('songs', 0xbc, None, 0, 'CAreaSoundsAndMusic'), ('rest', 0xc0, None, 0, 'CAreaFileRestEncounter'),
        ('notes', 0xc4, 0xc8, 4, 'CAreaUserNote'), ('traps', 0xcc, 0xd0, 4, 'CAreaFileProjectileObject')]),
}


def entry_size(e):
    return e if isinstance(e, int) else SZ(e)


k = open(os.path.join(G, 'chitin.key'), 'rb').read()
nb, nr, ob, orr = struct.unpack_from('<IIII', k, 8)
bifs = []
for i in range(nb):
    ln, fo, fl, loc = struct.unpack_from('<IIHH', k, ob + 12 * i)
    bifs.append(k[fo:fo + fl].rstrip(b'\0').decode().replace(chr(92), '/'))
cache = {}
stats = collections.defaultdict(collections.Counter)
bad = collections.defaultdict(list)
for t, (sig, hs, hsz, secs) in FMT.items():
    m = SZ(hs) if hs in T.structs else None
    print(f'{sig}: header struct {hs} BG size {m if m is None else hex(m)} (file header {hsz:#x});',
          ', '.join(f'{n}={entry_size(e):#x}' for n, _, _, _, e in secs))
for i in range(nr):
    name, typ, loc = struct.unpack_from('<8sHI', k, orr + 14 * i)
    if typ not in FMT:
        continue
    bi = loc >> 20
    if bi not in cache:
        p = os.path.join(G, bifs[bi])
        cache[bi] = open(p, 'rb').read() if os.path.exists(p) else None
    b = cache[bi]
    if not b:
        continue
    nf, nt, off = struct.unpack_from('<III', b, 8)
    l, o, sz, tt = struct.unpack_from('<IIIH', b, off + 16 * (loc & 0x3fff))
    d = b[o:o + sz]
    sig, hs, hsz, secs = FMT[typ]
    if d[:8] != sig.encode():
        stats[sig]['other version ' + d[:8].decode('latin-1')] += 1
        continue
    ok = True
    for n, fo_, fc, cb, e in secs:
        so = struct.unpack_from('<I', d, fo_)[0]
        cnt = 1 if fc is None else struct.unpack_from('<I' if cb == 4 else '<H', d, fc)[0]
        if fc is None and so == 0:
            continue
        if cnt and not (hsz <= so and so + cnt * entry_size(e) <= sz):
            ok = False; bad[sig].append((name.rstrip(b'\0').decode('latin-1'), n, so, cnt, sz))
    stats[sig]['ok' if ok else 'bad'] += 1
for s, c in stats.items():
    print(s, dict(c), bad[s][:4])
