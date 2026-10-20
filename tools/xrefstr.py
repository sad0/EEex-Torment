# Functions referencing given strings (rip-relative lea), in BG and PT, with the ordered string
# sequence inside each function: used to align two versions of a function by their messages.
#   python xrefstr.py "<string>" [...]
import sys, re, collections
import capstone
from ilib import PE, BG_EXE
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
EXES = {'BG': PE(BG_EXE), 'PT': PE('E:/Enhanced Edition/Environnement de test/PTEE (EEex dev)/Torment.exe')}


def cstr(pe, a):
    o = pe.off(a)
    if o is None:
        return None
    b = pe.d[o:o + 80].split(b'\0')[0]
    return b.decode('latin-1') if len(b) >= 2 and all(32 <= c < 127 for c in b) else None


def seq(pe, f, size=0x6000):
    out = []
    end = None
    for b, e, u in pe.rf:
        if b == f:
            end = e
    for i in md.disasm(pe.tbytes(f, (end or f + size) - f), f):
        m = re.search(r'rip \+ (0x[0-9a-f]+)', i.op_str)
        if m and i.mnemonic == 'lea':
            s = cstr(pe, i.address + i.size + int(m.group(1), 16))
            if s:
                out.append((i.address, s))
    return out


if __name__ == '__main__':
    targets = sys.argv[1:]
    for name, pe in EXES.items():
        hits = collections.defaultdict(list)
        for b, e, u in pe.rf:
            for a, s in seq(pe, b):
                if s in targets:
                    hits[pe.rfunc(b)[0] if pe.rfunc(b) else b].append((a, s))
        print(name, {hex(k): v[:3] for k, v in hits.items()})
