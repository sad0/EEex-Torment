# Vtables of BG2EE and Torment classes from their constructors, and the BG -> PT slot map.
# A constructor stores its class vtable: the last `lea reg, [rip + X]` written to [this] (rcx/rbx/rdi/rsi
# saved from rcx). Constructors: named S::S in bgnames.json, PT counterpart through fmap.json.
# Slot tokens: the fmap counterpart of the BG function, else a hash of its normalized code (so shared
# stubs compare by body); BG and PT slot lists are aligned with difflib.
# Output: vtables.json {S: {"bg_vt", "pt_vt", "bg_slots", "pt_slots", "map": [pt slot or null per BG slot]}}
import sys, os, json, re, struct, hashlib, difflib
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import capstone
from capstone import x86_const as X
from fmap import BG, PT, norm

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64); md.detail = True
F = {int(k, 16): int(v[0], 16) for k, v in json.load(open('fmap.json')).items()}
BN = {int(k, 16): v for k, v in json.load(open('bgnames.json')).items()}


def ctor_vtable(pe, f):
    """vtable stored into [this] by the constructor at f."""
    this = {X.X86_REG_RCX}
    last_lea = {}
    vt = None
    for i in md.disasm(pe.tbytes(f, 0x200), f):
        if i.mnemonic == 'ret' or i.mnemonic == 'int3':
            break
        ops = i.operands
        if i.mnemonic == 'mov' and len(ops) == 2 and ops[0].type == X.X86_OP_REG and ops[1].type == X.X86_OP_REG and ops[1].reg in this:
            this.add(ops[0].reg)
        if i.mnemonic == 'lea' and ops[1].type == X.X86_OP_MEM and ops[1].mem.base == X.X86_REG_RIP:
            last_lea[ops[0].reg] = i.address + i.size + ops[1].mem.disp
        if i.mnemonic == 'mov' and len(ops) == 2 and ops[0].type == X.X86_OP_MEM and ops[0].mem.base in this \
                and ops[0].mem.disp == 0 and ops[0].mem.index == 0 and ops[1].type == X.X86_OP_REG and ops[1].reg in last_lea:
            vt = last_lea[ops[1].reg]
        if i.mnemonic == 'call':
            for r in (X.X86_REG_RAX, X.X86_REG_RCX, X.X86_REG_RDX, X.X86_REG_R8, X.X86_REG_R9, X.X86_REG_R10, X.X86_REG_R11):
                last_lea.pop(r, None)
            this &= {X.X86_REG_RBX, X.X86_REG_RSI, X.X86_REG_RDI, X.X86_REG_R12, X.X86_REG_R13, X.X86_REG_R14, X.X86_REG_R15}
    return vt


def slots(pe, vt, n=200):
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


_h = {}


def body_hash(pe, f):
    k = (id(pe), f)
    if k not in _h:
        ins = []
        for i in md.disasm(pe.tbytes(f, 0x80), f):
            ins.append(norm(i))
            if i.mnemonic in ('ret', 'jmp') or len(ins) > 24:
                break
        _h[k] = 'h' + hashlib.md5('|'.join(ins).encode()).hexdigest()[:10]
    return _h[k]


def token_bg(f):
    return ('f', F[f]) if f in F else ('h', body_hash(BG, f))


def token_pt(f):
    return ('f', f)


def slot_map(bs, ps):
    tb = [token_bg(f) for f in bs]
    tp_f = [('f', f) for f in ps]
    tp_h = [('h', body_hash(PT, f)) for f in ps]
    # compare a BG token against the PT slot by function identity, or by body hash for unmapped ones
    tp = [tp_f[k] if any(t == tp_f[k] for t in tb) else tp_h[k] for k in range(len(ps))]
    m = [None] * len(bs)
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, tb, tp, autojunk=False).get_opcodes():
        if tag == 'equal':
            for d in range(i2 - i1):
                m[i1 + d] = j1 + d
    return m


if __name__ == '__main__':
    ctors = {}
    for a, n in BN.items():
        if '::' in n:
            c, f = n.rsplit('::', 1)
            if c == f:
                ctors.setdefault(c, []).append(a)
    out = {}
    for c, addrs in sorted(ctors.items()):
        for a in addrs:
            if a not in F:
                continue
            bvt, pvt = ctor_vtable(BG, a), ctor_vtable(PT, F[a])
            if bvt and pvt:
                bs, ps = slots(BG, bvt), slots(PT, pvt)
                if bs and ps:
                    out[c] = {'bg_vt': hex(bvt), 'pt_vt': hex(pvt), 'bg_slots': [hex(x) for x in bs],
                              'pt_slots': [hex(x) for x in ps], 'map': slot_map(bs, ps)}
                    break
    json.dump(out, open('bindings/vtables.json', 'w'), indent=0)
    changed = {c: v for c, v in out.items() if any(m != k for k, m in enumerate(v['map']))}
    print('classes with vtables', len(out), 'with moved/missing slots', len(changed))
    for c, v in sorted(changed.items())[:60]:
        diffs = [(k, m) for k, m in enumerate(v['map']) if m != k]
        print(f'  {c:32} bg {len(v["bg_slots"])} pt {len(v["pt_slots"])} first diffs {diffs[:6]}')
