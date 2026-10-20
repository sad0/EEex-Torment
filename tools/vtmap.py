# Vtable slot correspondence BG -> PT for classes with a VFTable pattern: for every BG slot, the PT
# slot holding the fmap counterpart of the BG function (shifted / reordered virtuals show up).
#   python vtmap.py <Class> [...]
import sys, json, struct, re
import capstone
from ilib import PE, BG_EXE
R = json.load(open('port2.json')); G = json.load(open('gen_report.json'))
BG = PE(BG_EXE); PT = PE('E:/Enhanced Edition/Environnement de test/PTEE (EEex dev)/Torment.exe')
F = {int(k, 16): int(v[0], 16) for k, v in json.load(open('fmap.json')).items()}
BN = {int(k, 16): v for k, v in json.load(open('bgnames.json')).items()}
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)


def bg_vt(k):
    a = int(R[k]['bg_key'], 16)
    for off in range(0, 8):
        for i in md.disasm(BG.tbytes(a - off, 16), a - off):
            m = re.search(r'rip \+ (0x[0-9a-f]+)', i.op_str)
            if m and i.mnemonic in ('lea', 'mov'):
                return i.address + i.size + int(m.group(1), 16)
            break


def slots(pe, vt, n=80):
    out = []
    for s in range(n):
        v = pe.read(vt + 8 * s, 8)
        if not v:
            break
        f = struct.unpack('<Q', v)[0] - pe.base
        if not (pe.tva <= f < pe.tva + pe.tsize):
            break
        out.append(f)
    return out


def vmap(cls):
    k = f'{cls}::VFTable'
    b, p = bg_vt(k), int(G[k]['addr'], 16)
    bs, ps = slots(BG, b), slots(PT, p)
    inv = {}
    for t, f in enumerate(ps):
        inv.setdefault(f, []).append(t)
    return bs, ps, [(s, BN.get(f, hex(f)), inv.get(F.get(f), [])) for s, f in enumerate(bs)]


if __name__ == '__main__':
    for cls in sys.argv[1:]:
        bs, ps, m = vmap(cls)
        print(f'== {cls}: BG {len(bs)} slots, PT {len(ps)} slots')
        for s, n, t in m:
            print(f'  {s:3} {n[:50]:50} -> PT {t}')
