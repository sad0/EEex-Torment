# Map "resource name -> member displacement" for C2DArray::Load (or any loader) calls inside a
# function, in BG and PT, then compare by name. For each call to the loader, the member is the last
# `lea rcx, [reg + disp]` and the name the last rip-relative ASCII string loaded before it.
#   python loadmap.py <bg fn> <pt fn> <bg loader> <pt loader> [size]
import sys, collections
from capstone import x86_const as X
from inikeys import BG, PT, md, cstr


CSTR_CTOR = {'BG': 0x3fd6b0, 'PT': 0x484330}   # CString::Construct(char*)


def statics(pe, ctor):
    """Static CString initializers: lea rdx, "NAME"; lea rcx, [rip + G]; call CString(char*) -> {G: NAME}."""
    g = {}
    for b, e, u in pe.rf:
        if e - b > 0x40:
            continue
        name, glob = None, None
        for i in md.disasm(pe.tbytes(b, e - b), b):
            if i.mnemonic == 'lea' and i.operands[1].type == X.X86_OP_MEM and i.operands[1].mem.base == X.X86_REG_RIP:
                a = i.address + i.size + i.operands[1].mem.disp
                if i.operands[0].reg == X.X86_REG_RDX:
                    name = cstr(pe, a)
                elif i.operands[0].reg == X.X86_REG_RCX:
                    glob = a
            elif i.mnemonic == 'call':
                if i.operands[0].type == X.X86_OP_IMM and i.operands[0].imm == ctor and name and glob:
                    g[glob] = name
                break
    return g


GLOB = {}


def scan(pe, f, loader, size):
    gl = GLOB.get(id(pe))
    if gl is None:
        gl = GLOB[id(pe)] = statics(pe, CSTR_CTOR['BG' if pe is BG else 'PT'])
    out = collections.defaultdict(list)
    name, member = None, None
    for i in md.disasm(pe.tbytes(f, size), f):
        if i.mnemonic == 'lea' and i.operands[1].type == X.X86_OP_MEM:
            m = i.operands[1].mem
            if m.base == X.X86_REG_RIP:
                a = i.address + i.size + m.disp
                s = gl.get(a) or cstr(pe, a)
                if s:
                    name = s
            elif i.operands[0].reg == X.X86_REG_RCX and m.base not in (X.X86_REG_RSP, X.X86_REG_RBP):
                member = m.disp
        elif i.mnemonic == 'call':
            if i.operands[0].type == X.X86_OP_IMM and i.operands[0].imm == loader and name and member is not None:
                out[name].append(member)
            if i.operands[0].type == X.X86_OP_IMM and i.operands[0].imm == loader:
                name, member = None, None
    return out


if __name__ == '__main__':
    bf, pf, bl, pl = (int(a, 16) for a in sys.argv[1:5])
    size = int(sys.argv[5], 16) if len(sys.argv) > 5 else 0x8000
    B, P = scan(BG, bf, bl, size), scan(PT, pf, pl, size)
    for k in sorted(set(B) & set(P), key=lambda k: B[k][0]):
        print(f'{k:12} bg {B[k][0]:#7x} pt {P[k][0]:#7x}  delta {P[k][0] - B[k][0]:+#x}' + ('' if len(B[k]) == len(P[k]) == 1 else f'  (bg {[hex(x) for x in B[k]]} pt {[hex(x) for x in P[k]]})'))
    print('BG only', sorted((k, hex(v[0])) for k, v in B.items() if k not in P))
    print('PT only', sorted((k, hex(v[0])) for k, v in P.items() if k not in B))
