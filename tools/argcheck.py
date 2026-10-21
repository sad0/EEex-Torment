# Signature check of every function binding (pattern DB labels resolved to a function entry): the argument
# registers (rcx, rdx, r8, r9, xmm0-3) and stack arguments a function reads before writing them, BG vs PT.
# A register Torment reads that BG does not (or the reverse) means a changed signature (e.g. Torment's
# CInfinity::SetZoom gained `bool bForce` in r8b). Walks the body in address order until the first call.
#   python argcheck.py            -> list of mismatches
import json, collections
import capstone
from capstone import x86_const as X
from fmap import BG, PT
from fdiff import body

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64); md.detail = True
ARG = {}
for base, names in ((X.X86_REG_RCX, ('rcx', 'ecx', 'cx', 'cl')), (X.X86_REG_RDX, ('rdx', 'edx', 'dx', 'dl')),
                    (X.X86_REG_R8, ('r8', 'r8d', 'r8w', 'r8b')), (X.X86_REG_R9, ('r9', 'r9d', 'r9w', 'r9b'))):
    for n in names:
        ARG[md.reg_name and n] = base
GP = {'rcx': 'rcx', 'ecx': 'rcx', 'cx': 'rcx', 'cl': 'rcx', 'ch': 'rcx', 'rdx': 'rdx', 'edx': 'rdx', 'dx': 'rdx', 'dl': 'rdx', 'dh': 'rdx',
      'r8': 'r8', 'r8d': 'r8', 'r8w': 'r8', 'r8b': 'r8', 'r9': 'r9', 'r9d': 'r9', 'r9w': 'r9', 'r9b': 'r9',
      'xmm0': 'xmm0', 'xmm1': 'xmm1', 'xmm2': 'xmm2', 'xmm3': 'xmm3'}


def args_read(pe, f, limit=80):
    """Argument registers read before written, plus stack argument slots [entry rsp + 0x28 + 8k]."""
    read, written = set(), set()
    stack = set()
    depth = 0  # bytes pushed / allocated since entry
    rbp = None  # entry-rsp offset of rbp when used as frame pointer
    for n, i in enumerate(body(pe, f)):
        if n > limit or i.mnemonic in ('call', 'ret') or i.mnemonic.startswith('j') and i.mnemonic != 'jmp':
            if i.mnemonic in ('call', 'ret'):
                break
        try:
            regs_r, regs_w = i.regs_access()
        except capstone.CsError:
            continue
        rn = {GP.get(i.reg_name(r)) for r in regs_r} - {None}
        wn = {GP.get(i.reg_name(r)) for r in regs_w} - {None}
        # xor r, r is a write, not a read
        if i.mnemonic in ('xor', 'xorps', 'pxor') and len(i.operands) == 2 and i.operands[0].type == X.X86_OP_REG \
                and i.operands[1].type == X.X86_OP_REG and i.operands[0].reg == i.operands[1].reg:
            rn = set()
        read |= rn - written
        written |= wn
        if i.mnemonic == 'push':
            depth += 8
        elif i.mnemonic == 'sub' and i.op_str.startswith('rsp, ') and i.operands[1].type == X.X86_OP_IMM:
            depth += i.operands[1].imm
        if i.mnemonic == 'lea' and i.op_str.startswith('rbp, [rsp'):
            rbp = i.operands[1].mem.disp - depth
        elif i.mnemonic == 'mov' and i.op_str == 'rbp, rsp':
            rbp = -depth
        for o in i.operands:
            if o.type == X.X86_OP_MEM and i.mnemonic != 'lea' and o.access & capstone.CS_AC_READ:
                if o.mem.base == X.X86_REG_RSP:
                    off = o.mem.disp - depth
                elif o.mem.base == X.X86_REG_RBP and rbp is not None:
                    off = o.mem.disp + rbp
                else:
                    continue
                if 0x28 <= off < 0x100:
                    stack.add(off)
        if i.mnemonic == 'jmp' and i.operands[0].type != X.X86_OP_IMM:
            break
    return read, stack


if __name__ == '__main__':
    G = json.load(open('gen_report.json')); R = json.load(open('port2.json'))
    out = []
    seen = set()
    for k, g in G.items():
        if g.get('status') != 'ported' or '-' in k.split('::')[0] or k.startswith(('Hook-', 'Data-')):
            continue
        b = R.get(k, {}).get('bg_key'); p = g.get('addr')
        if not b or not p:
            continue
        b, p = int(b, 16), int(p, 16)
        fb, fp = BG.rfunc(b), PT.rfunc(p)
        if not fb or not fp or fb[0] != b or fp[0] != p or (b, p) in seen:
            continue  # not a function entry
        seen.add((b, p))
        rb, sb = args_read(BG, b)
        rp, sp = args_read(PT, p)
        if rb != rp or sb != sp:
            out.append((k, hex(b), hex(p), sorted(rb), sorted(rp), sorted(map(hex, sb)), sorted(map(hex, sp))))
    print('functions checked', len(seen), 'mismatches', len(out))
    for o in out:
        print(o)
