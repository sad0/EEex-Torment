# Map INI key name -> stored field displacement in an options loader (e.g. CBaldurChitin::LoadOptions),
# for BG and PT, and compare by key name. A key is the last rip-relative ASCII string loaded before
# the store that follows a call; stores are "mov [reg+disp], r32/r8/imm" with disp >= 0x100.
#   python inikeys.py <bg fn> <pt fn> [bg base] [pt base]
import sys, re, collections
import capstone
from capstone import x86_const as X
from ilib import PE, BG_EXE

BG = PE(BG_EXE); PT = PE('E:/Enhanced Edition/Environnement de test/PTEE (EEex dev)/Torment.exe')
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64); md.detail = True


def cstr(pe, rva):
    b = pe.read(rva, 64)
    if not b:
        return None
    s = b.split(b'\0')[0]
    return s.decode('latin-1') if len(s) >= 3 and all(32 <= c < 127 for c in s) else None


def save_keys(pe, f, size):
    """Option savers: the field read (disp >= 0x100) most recently before a call that gets a key in rdx."""
    out = collections.defaultdict(list)
    key, rd = None, None
    for i in md.disasm(pe.tbytes(f, size), f):
        if i.mnemonic == 'lea' and i.operands[1].type == X.X86_OP_MEM and i.operands[1].mem.base == X.X86_REG_RIP:
            s = cstr(pe, i.address + i.size + i.operands[1].mem.disp)
            if s and i.operands[0].reg == X.X86_REG_RDX:
                key = s
        elif i.mnemonic in ('mov', 'movzx', 'movsx', 'cmp') and len(i.operands) == 2 and i.operands[1].type == X.X86_OP_MEM:
            m = i.operands[1].mem
            if m.base not in (X.X86_REG_RSP, X.X86_REG_RBP, X.X86_REG_RIP) and m.disp >= 0x100:
                rd = m.disp
        elif i.mnemonic == 'call':
            # value formatting calls (sprintf) come between the read and the key write
            if key and rd is not None:
                out[key].append(rd)
                key, rd = None, None
    return out


def keys(pe, f, size):
    out = collections.defaultdict(list)
    strs = []      # strings loaded since last call
    last = None    # key in effect after the most recent call
    for i in md.disasm(pe.tbytes(f, size), f):
        if i.mnemonic == 'lea' and i.operands[1].type == X.X86_OP_MEM and i.operands[1].mem.base == X.X86_REG_RIP:
            s = cstr(pe, i.address + i.size + i.operands[1].mem.disp)
            if s and i.operands[0].reg == X.X86_REG_RDX:
                strs = [s]
        elif i.mnemonic == 'call':
            # GetPrivateProfile*(section in rcx, key in rdx, ...): the key is the string loaded into rdx
            last = strs[0] if strs else None
            strs = []
        elif i.mnemonic == 'mov' and i.operands[0].type == X.X86_OP_MEM and last:
            m = i.operands[0].mem
            if m.base not in (X.X86_REG_RSP, X.X86_REG_RBP, X.X86_REG_RIP) and m.disp >= 0x100:
                out[last].append(m.disp)
                last = None
        if i.mnemonic == 'ret' and i.address > f + 0x40:
            pass
    return out


if __name__ == '__main__':
    bf, pf = int(sys.argv[1], 16), int(sys.argv[2], 16)
    args = [a for a in sys.argv if not a.startswith('--')]
    bb = int(args[3], 16) if len(args) > 3 else 0
    pb = int(args[4], 16) if len(args) > 4 else 0
    fn = save_keys if '--save' in sys.argv else keys
    B, P = fn(BG, bf, 0x3000), fn(PT, pf, 0x3000)
    common = sorted(set(B) & set(P), key=lambda k: B[k][0])
    for k in common:
        print(f'{k:40} bg {B[k][0] - bb:#7x} pt {P[k][0] - pb:#7x}  delta {(P[k][0] - pb) - (B[k][0] - bb):+#x}')
    print('BG only', [k for k in B if k not in P][:30])
    print('PT only', [k for k in P if k not in B][:30])
