# Tiny concrete/symbolic x86-64 emulator (capstone) for switch-dispatch functions: run a function with
# given integer arguments and report the memory accesses made through symbolic pointers (this,
# globals). Used to map "option id -> struct field" in BG and PT and compare them.
import capstone
from capstone import x86_const as X

MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64); MD.detail = True
MASK = (1 << 64) - 1
R64 = {}
for full in ['RAX', 'RBX', 'RCX', 'RDX', 'RSI', 'RDI', 'RBP', 'RSP'] + [f'R{i}' for i in range(8, 16)]:
    R64[getattr(X, 'X86_REG_' + full)] = (full, 8)
for a, b, n in [('EAX', 'RAX', 4), ('EBX', 'RBX', 4), ('ECX', 'RCX', 4), ('EDX', 'RDX', 4), ('ESI', 'RSI', 4), ('EDI', 'RDI', 4),
                ('EBP', 'RBP', 4), ('ESP', 'RSP', 4), ('AX', 'RAX', 2), ('CX', 'RCX', 2), ('DX', 'RDX', 2), ('BX', 'RBX', 2),
                ('AL', 'RAX', 1), ('CL', 'RCX', 1), ('DL', 'RDX', 1), ('BL', 'RBX', 1), ('SIL', 'RSI', 1), ('DIL', 'RDI', 1)] + \
        [(f'R{i}D', f'R{i}', 4) for i in range(8, 16)] + [(f'R{i}W', f'R{i}', 2) for i in range(8, 16)] + \
        [(f'R{i}B', f'R{i}', 1) for i in range(8, 16)]:
    R64[getattr(X, 'X86_REG_' + a)] = (b, n)


class Sym:
    """Symbolic pointer: name + offset."""
    def __init__(s, name, off=0):
        s.name, s.off = name, off

    def __add__(s, k):
        return Sym(s.name, s.off + k)

    def __repr__(s):
        return f'{s.name}+{s.off:#x}'


class Stop(Exception):
    pass


def run(pe, f, regs, derefs, max_steps=400, stop_on=None, skip_calls=False):
    """regs: {'RCX': value or Sym}; derefs: {(sym name, off): Sym} values of [sym+off] loads.
    Returns list of (kind, Sym, size, insn address) memory accesses through symbols."""
    R = {k: 0 for k in ['RAX', 'RBX', 'RCX', 'RDX', 'RSI', 'RDI', 'RBP', 'RSP'] + [f'R{i}' for i in range(8, 16)]}
    R['RSP'] = Sym('stack', 0)
    R.update(regs)
    flags = {}
    acc = []
    pc = f
    stack = {}

    def get(op, i):
        if op.type == X.X86_OP_IMM:
            return op.imm
        if op.type == X.X86_OP_REG:
            name, n = R64[op.reg]
            v = R[name]
            return v if isinstance(v, Sym) else v & ((1 << (8 * n)) - 1)
        return load(op, i)

    def addr(op, i):
        m = op.mem
        if m.base == X.X86_REG_RIP:
            return i.address + i.size + m.disp
        b = R[R64[m.base][0]] if m.base else 0
        ix = R[R64[m.index][0]] if m.index else 0
        if isinstance(ix, Sym):
            raise Stop('symbolic index')
        if isinstance(b, Sym):
            return b + (m.disp + ix * m.scale)
        return (b + ix * m.scale + m.disp) & MASK

    def load(op, i):
        a = addr(op, i)
        n = op.size
        if isinstance(a, Sym):
            acc.append(('read', a, n, i.address))
            if a.name == 'stack':
                return stack.get(a.off, 0)
            if stop_on and stop_on(a):
                raise Stop('hit')
            v = derefs.get((a.name, a.off))
            if v is None:
                return Sym(f'[{a}]')
            return v
        if op.mem.base == X.X86_REG_RIP and n == 8:
            return Sym(f'g{a:x}')   # global pointer: symbolic
        if a < pe.base:
            a += pe.base
        rva = a - pe.base
        b = pe.read(rva, n)
        if b is None:
            raise Stop(f'unmapped {a:#x}')
        return int.from_bytes(b, 'little')

    def put(op, v, i, n=None):
        if op.type == X.X86_OP_REG:
            name, sz = R64[op.reg]
            if isinstance(v, Sym):
                R[name] = v; return
            if sz == 4:
                R[name] = v & 0xffffffff
            elif sz == 8:
                R[name] = v & MASK
            else:
                old = R[name] if not isinstance(R[name], Sym) else 0
                m = (1 << (8 * sz)) - 1
                R[name] = (old & ~m) | (v & m)
        else:
            a = addr(op, i)
            if isinstance(a, Sym):
                acc.append(('write', a, op.size, i.address))
                if a.name == 'stack':
                    stack[a.off] = v

    def setflags(res, n, a=None, b=None, sub=False):
        m = (1 << (8 * n)) - 1
        r = res & m
        flags['ZF'] = r == 0
        flags['SF'] = bool(r >> (8 * n - 1))
        if sub and a is not None:
            flags['CF'] = (a & m) < (b & m)
            sa = a & m; sb = b & m
            sa = sa - (1 << 8 * n) if sa >> (8 * n - 1) else sa
            sb = sb - (1 << 8 * n) if sb >> (8 * n - 1) else sb
            flags['OF'] = not (-(1 << (8 * n - 1)) <= sa - sb < (1 << (8 * n - 1)))
        else:
            flags['CF'] = False; flags['OF'] = False

    COND = {'je': lambda: flags['ZF'], 'jne': lambda: not flags['ZF'], 'ja': lambda: not flags['CF'] and not flags['ZF'],
            'jae': lambda: not flags['CF'], 'jb': lambda: flags['CF'], 'jbe': lambda: flags['CF'] or flags['ZF'],
            'jg': lambda: not flags['ZF'] and flags['SF'] == flags['OF'], 'jge': lambda: flags['SF'] == flags['OF'],
            'jl': lambda: flags['SF'] != flags['OF'], 'jle': lambda: flags['ZF'] or flags['SF'] != flags['OF'],
            'js': lambda: flags['SF'], 'jns': lambda: not flags['SF']}
    try:
        for _ in range(max_steps):
            i = next(iter(MD.disasm(pe.tbytes(pc, 16), pc)), None)
            if i is None:
                raise Stop('decode')
            mn, ops = i.mnemonic, i.operands
            nxt = i.address + i.size
            if mn in ('mov', 'movzx', 'movsxd', 'movsx'):
                v = get(ops[1], i)
                if mn in ('movsxd', 'movsx') and not isinstance(v, Sym):
                    n = ops[1].size
                    if v >> (8 * n - 1):
                        v -= 1 << (8 * n)
                    v &= MASK
                put(ops[0], v, i)
            elif mn == 'lea':
                put(ops[0], addr(ops[1], i), i)
            elif mn in ('add', 'sub'):
                a, b = get(ops[0], i), get(ops[1], i)
                if isinstance(a, Sym) and not isinstance(b, Sym):
                    put(ops[0], a + (b if mn == 'add' else -b), i)
                elif isinstance(b, Sym) and mn == 'add' and not isinstance(a, Sym):
                    put(ops[0], b + a, i)
                elif isinstance(a, Sym) or isinstance(b, Sym):
                    raise Stop('sym arith')
                else:
                    r = a + b if mn == 'add' else a - b
                    setflags(r, ops[0].size, a, b, sub=(mn == 'sub')); put(ops[0], r, i)
            elif mn in ('dec', 'inc'):
                a = get(ops[0], i)
                if isinstance(a, Sym):
                    raise Stop('sym inc')
                r = a - 1 if mn == 'dec' else a + 1
                cf = flags.get('CF', False)
                setflags(r, ops[0].size, a, 1, sub=(mn == 'dec')); flags['CF'] = cf; put(ops[0], r, i)
            elif mn in ('cmp', 'test', 'and', 'or', 'xor'):
                a, b = get(ops[0], i), get(ops[1], i)
                if isinstance(a, Sym) or isinstance(b, Sym):
                    if mn == 'xor' and ops[0].type == ops[1].type == X.X86_OP_REG and ops[0].reg == ops[1].reg:
                        put(ops[0], 0, i); setflags(0, ops[0].size)
                    elif mn in ('xor', 'and', 'or'):
                        put(ops[0], Sym(f'{mn}{i.address:x}'), i)   # e.g. stack cookie
                    else:
                        raise Stop('sym cmp')
                elif mn == 'cmp':
                    setflags(a - b, ops[0].size, a, b, sub=True)
                else:
                    r = a & b if mn in ('test', 'and') else (a | b if mn == 'or' else a ^ b)
                    setflags(r, ops[0].size)
                    if mn != 'test':
                        put(ops[0], r, i)
            elif mn in COND:
                if COND[mn]():
                    nxt = ops[0].imm
            elif mn == 'jmp':
                t = get(ops[0], i)
                if isinstance(t, Sym):
                    raise Stop('sym jmp')
                nxt = t - pe.base if t >= pe.base else t
            elif mn in ('push', 'pop', 'nop', 'int3'):
                pass
            elif mn == 'ret':
                break
            elif mn == 'call':
                if not skip_calls:
                    raise Stop(f'call {i.op_str}')
                for r_ in ('RAX', 'RCX', 'RDX', 'R8', 'R9', 'R10', 'R11'):
                    R[r_] = Sym(f'call{i.address:x}.{r_}')
            else:
                # anything else (SSE, setcc, cmov, shifts...): destination becomes unknown; stores
                # through symbols are still recorded, loads through symbols too
                for op in ops[1:]:
                    if op.type == X.X86_OP_MEM:
                        a_ = addr(op, i)
                        if isinstance(a_, Sym):
                            acc.append(('read', a_, op.size, i.address))
                if ops and ops[0].type == X.X86_OP_REG and ops[0].reg in R64:
                    put(ops[0], Sym(f'{mn}{i.address:x}'), i)
                elif ops and ops[0].type == X.X86_OP_MEM:
                    put(ops[0], 0, i)
                if mn.startswith(('cmp', 'test', 'ucomis', 'comis', 'bt')):
                    raise Stop(f'unknown flags {mn}')
            pc = nxt
    except Stop as e:
        acc.append(('stop', str(e), 0, pc))
    return acc
