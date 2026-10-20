# Collect BG->PT field offset evidence.
# For every mapped function pair (BG f -> PT F[f]) we run a light forward type tracker on the BG
# instructions (roots: typed globals, typed function parameters, vtable methods' this, typed call
# returns, field pointer loads). Each memory access through a typed base whose instruction is
# exactly aligned with a PT instruction yields (struct, BG absolute offset, size) -> PT absolute offset.
# Output: field_evidence.json
import sys, os, re, json, collections
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.chdir(os.path.join(os.path.dirname(__file__), '..'))
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone import x86_const as X
import fmap
from fmap import BG, PT, align, fragments
from ilib import parse_db, UP_DB
import bindings.bgtypes as T

md = Cs(CS_ARCH_X86, CS_MODE_64); md.detail = True
F = {int(k, 16): int(v[0], 16) for k, v in json.load(open('fmap.json')).items()}
R = json.load(open('port2.json'))
G = json.load(open('gen_report.json'))
from gen import bg_final

VOL = {X.X86_REG_RAX, X.X86_REG_RCX, X.X86_REG_RDX, X.X86_REG_R8, X.X86_REG_R9, X.X86_REG_R10, X.X86_REG_R11}
ARGREGS = [X.X86_REG_RCX, X.X86_REG_RDX, X.X86_REG_R8, X.X86_REG_R9]
R64 = {}  # sub-register -> 64-bit register
for full in ['RAX', 'RBX', 'RCX', 'RDX', 'RSI', 'RDI', 'RBP', 'RSP'] + [f'R{i}' for i in range(8, 16)]:
    R64[getattr(X, 'X86_REG_' + full)] = getattr(X, 'X86_REG_' + full)
for a, b in [('EAX', 'RAX'), ('EBX', 'RBX'), ('ECX', 'RCX'), ('EDX', 'RDX'), ('ESI', 'RSI'), ('EDI', 'RDI'), ('EBP', 'RBP')] + \
        [(f'R{i}D', f'R{i}') for i in range(8, 16)] + [(f'R{i}W', f'R{i}') for i in range(8, 16)] + [(f'R{i}B', f'R{i}') for i in range(8, 16)] + \
        [('AX', 'RAX'), ('BX', 'RBX'), ('CX', 'RCX'), ('DX', 'RDX'), ('SI', 'RSI'), ('DI', 'RDI'), ('AL', 'RAX'), ('BL', 'RBX'), ('CL', 'RCX'), ('DL', 'RDX'), ('SIL', 'RSI'), ('DIL', 'RDI')]:
    R64[getattr(X, 'X86_REG_' + a)] = getattr(X, 'X86_REG_' + b)


def ptr_struct(tstr):
    """struct name if tstr is 'S*' for a known struct S."""
    if not tstr:
        return None
    t = T.parse_type(tstr.replace('pThis', '').strip())
    if t[0] == 'ptr' and T.base_struct(t[1]):
        return t[1][1]
    return None


def argtype(arg):
    """Drop a trailing parameter name: 'const CResRef* cNew' -> 'const CResRef*'."""
    arg = arg.strip()
    m = re.match(r'^(.*?[\s*&])([A-Za-z_]\w*)$', arg)
    if m and not arg.endswith('*') and m.group(1).strip():
        return m.group(1).strip()
    return arg


# ---- typed roots -------------------------------------------------------------------------------
UP = parse_db(UP_DB)
entry_types = {}   # BG function -> {reg: struct}
ret_types = {}     # BG function -> struct returned by pointer
for (cls, fn), args in T.member_sigs.items():
    cands = [n for n in UP if n == f'{cls}::{fn}' or n.startswith(f'{cls}::{fn}(')]
    if len(cands) != 1:
        continue
    a = bg_final(cands[0])
    if a is None:
        continue
    regs = {}
    for k, arg in enumerate(args[:4]):
        s = ptr_struct(argtype(arg))
        if s:
            regs[ARGREGS[k]] = s
    entry_types[a] = regs
    rs = ptr_struct(T.rets.get((cls, fn)))
    if rs:
        ret_types[a] = rs
for fn, args in T.free_sigs.items():
    if fn not in UP:
        continue
    a = bg_final(fn)
    if a is None:
        continue
    regs = {}
    for k, arg in enumerate(args[:4]):
        s = ptr_struct(argtype(arg))
        if s:
            regs[ARGREGS[k]] = s
    entry_types.setdefault(a, regs)
    rs = ptr_struct(T.rets.get((None, fn)))
    if rs:
        ret_types[a] = rs
# vtables: slot k of S's vtable is a method whose first argument type is declared in S::vtbl
import struct as _st
for n in UP:
    if not n.endswith('::VFTable'):
        continue
    cls = n[:-9]
    vt = bg_final(n)
    slots = T.vtbl_sigs.get(cls)
    if vt is None or not slots:
        continue
    for k, (sname, args, ret) in enumerate(slots):
        b = BG.read(vt + 8 * k, 8)
        if not b:
            break
        f = _st.unpack('<Q', b)[0] - BG.base
        if not (BG.tva <= f < BG.tva + BG.tsize):
            break
        s = ptr_struct(args[0]) if args else None
        if s:
            entry_types.setdefault(f, {})[X.X86_REG_RCX] = s
# typed globals: address of the pointer/object -> (kind, struct)
glob = {}
for gname, gtype in T.globals_.items():
    if gname not in UP:
        continue
    a = bg_final(gname)
    if a is None:
        continue
    t = T.parse_type(gtype)
    if t[0] == 'ptr' and T.base_struct(t[1]):
        glob[a] = ('load', t[1][1])      # mov reg, [rip+g] -> S*
    elif T.base_struct(t):
        glob[a] = ('lea', t[1])          # lea reg, [rip+g] -> S*

print('roots: typed functions', len(entry_types), 'returns', len(ret_types), 'globals', len(glob), file=sys.stderr)

# ---- evidence ----------------------------------------------------------------------------------
EV = collections.defaultdict(collections.Counter)   # (struct, bg_abs, size) -> Counter(pt_abs)
CALLARGS = collections.defaultdict(collections.Counter)  # (callee, argreg) -> Counter(struct)
SITES = collections.defaultdict(list)  # (struct, bg_abs) -> [(bg fn, pt fn, bg insn, bg base off, pt base off)]


def type_at(sname, off):
    """Pointer target struct of the field at absolute offset off (exact field start) or None."""
    r = T.field_at(sname, off)
    if not r:
        return None
    path, fld, rel = r
    if rel != 0:
        return None
    t = T.parse_type(fld.type)
    if t[0] == 'ptr' and T.base_struct(t[1]):
        return t[1][1]
    return None


def mem_op(ins):
    for op in ins.operands:
        if op.type == X.X86_OP_MEM:
            return op
    return None


def run(bgf, ptf, roots):
    a = [i for g in fragments('BG', bgf) for i in md.disasm(BG.tbytes(g, (BG.rfrag(g) or (g, g + 0x4000))[1] - g), g)]
    mp, ratio, _, _ = align(bgf, ptf)
    if ratio < 0.4:
        return 0
    ptc = {}
    st = {r: (s, 0, 0) for r, s in roots.items()}
    stack = {}
    n = 0
    for i in a:
        if i.mnemonic == 'int3':
            break
        pa = mp.get(i.address)
        pi = None
        if pa is not None:
            pi = next(iter(md.disasm(PT.tbytes(pa, 16), pa)), None)
        mop = mem_op(i)
        pmop = mem_op(pi) if pi is not None else None
        # evidence for memory accesses through a typed base
        if mop is not None and mop.mem.index == 0 and mop.mem.base in st:
            s, ob, op_ = st[mop.mem.base]
            bg_abs = ob + mop.mem.disp
            sl = SITES[(s, bg_abs)]
            if len(sl) < 40:
                sl.append((bgf, ptf, i.address, ob, op_))
            if pmop is not None and op_ is not None and pmop.mem.base == mop.mem.base and i.mnemonic != 'lea':
                EV[(s, bg_abs, mop.size)][op_ + pmop.mem.disp] += 1
                n += 1
        # transfer function
        regs_w = set()
        try:
            _, w = i.regs_access()
            regs_w = {R64.get(r, r) for r in w}
        except Exception:
            pass
        newval = None
        dst = i.operands[0] if i.operands else None
        dreg = R64.get(dst.reg, dst.reg) if dst is not None and dst.type == X.X86_OP_REG else None
        if i.mnemonic == 'mov' and dreg is not None and len(i.operands) == 2:
            src = i.operands[1]
            if src.type == X.X86_OP_REG and R64.get(src.reg) in st and dst.size == 8:
                newval = st[R64[src.reg]]
            elif src.type == X.X86_OP_MEM and dst.size == 8:
                if src.mem.base == X.X86_REG_RIP:
                    g = i.address + i.size + src.mem.disp
                    if glob.get(g, (None,))[0] == 'load':
                        newval = (glob[g][1], 0, 0)
                elif src.mem.base == X.X86_REG_RSP and src.mem.index == 0:
                    newval = stack.get(src.mem.disp)
                elif src.mem.base in st and src.mem.index == 0:
                    s, ob, op_ = st[src.mem.base]
                    tgt = type_at(s, ob + src.mem.disp)
                    if tgt:
                        newval = (tgt, 0, 0)
        elif i.mnemonic == 'lea' and dreg is not None:
            src = i.operands[1]
            if src.mem.base == X.X86_REG_RIP:
                g = i.address + i.size + src.mem.disp
                if glob.get(g, (None,))[0] == 'lea':
                    newval = (glob[g][1], 0, 0)
            elif src.mem.base in st and src.mem.index == 0:
                s, ob, op_ = st[src.mem.base]
                ptd = pmop.mem.disp if (pmop is not None and pi.mnemonic == 'lea' and pmop.mem.base == src.mem.base and op_ is not None) else None
                newval = (s, ob + src.mem.disp, (op_ + ptd) if ptd is not None else None)
        elif i.mnemonic == 'mov' and dst is not None and dst.type == X.X86_OP_MEM and dst.mem.base == X.X86_REG_RSP and dst.mem.index == 0:
            src = i.operands[1]
            if src.type == X.X86_OP_REG and R64.get(src.reg) in st:
                stack[dst.mem.disp] = st[R64[src.reg]]
            else:
                stack.pop(dst.mem.disp, None)
        if i.mnemonic == 'call':
            if i.operands and i.operands[0].type == X.X86_OP_IMM:
                tgt = i.operands[0].imm
                for k, r in enumerate(ARGREGS):
                    v = st.get(r)
                    if v is None:
                        continue
                    s_, ob, _ = v
                    if ob == 0:
                        CALLARGS[(tgt, r)][s_] += 1
                    else:
                        fa = T.field_at(s_, ob)
                        if fa and fa[2] == 0:
                            u = T.base_struct(T.parse_type(fa[1].type))
                            if u:
                                CALLARGS[(tgt, r)][u] += 1
            for r in VOL:
                st.pop(r, None)
            if i.operands and i.operands[0].type == X.X86_OP_IMM and i.operands[0].imm in ret_types:
                st[X.X86_REG_RAX] = (ret_types[i.operands[0].imm], 0, 0)
            continue
        for r in regs_w:
            st.pop(r, None)
        if newval is not None and dreg is not None:
            st[dreg] = newval
        if i.mnemonic in ('push', 'pop', 'sub', 'add') and X.X86_REG_RSP in regs_w:
            stack.clear()
    return n


if __name__ == '__main__':
    for rnd in range(4):
        EV.clear(); CALLARGS.clear(); SITES.clear()
        tot = 0; nf = 0
        for bgf, ptf in F.items():
            roots = entry_types.get(bgf, {})
            try:
                k = run(bgf, ptf, roots)
            except Exception as e:
                continue
            if k:
                nf += 1; tot += k
        added = 0
        for (tgt, r), c in CALLARGS.items():
            s_, n = c.most_common(1)[0]
            if n >= 2 and n >= 0.9 * sum(c.values()) and r not in entry_types.get(tgt, {}):
                entry_types.setdefault(tgt, {})[r] = s_; added += 1
        print('round', rnd, 'functions with evidence', nf, 'observations', tot, 'keys', len(EV), 'new typed args', added, file=sys.stderr)
        if not added:
            break
    print('functions with evidence', nf, 'observations', tot, 'keys', len(EV), file=sys.stderr)
    json.dump({f'{s}|{hex(o)}|{z}': {hex(a): c for a, c in v.items()} for (s, o, z), v in EV.items()}, open('bindings/field_evidence.json', 'w'), indent=0)
    json.dump({f'{s}|{hex(o)}': [[hex(a) if a is not None else None for a in t] for t in v] for (s, o), v in SITES.items()},
              open('bindings/field_sites.json', 'w'), indent=0)
