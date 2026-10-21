# Whole-function normalized diff BG vs PT. The body is rebuilt by recursive descent from the entry
# (jumps and jump tables followed, calls not), so chained / split fragments are included; a jmp to
# another function's entry is a tail call and ends the path.
#   python fdiff.py <BG name | BG rva> [PT rva]       (PT defaults to the fmap counterpart)
import sys, json, difflib, struct
import capstone
from capstone import x86_const as X
from fmap import BG, PT, norm

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64); md.detail = True


def body(pe, entry):
    starts = set(pe.rf_beg)
    seen, todo, out = set(), [entry], {}
    while todo:
        a = todo.pop()
        while a not in seen:
            if a != entry and a in starts and pe.rfunc(a) and pe.rfunc(a)[0] == a and a not in out:
                # entry of another primary function: tail call
                if pe.rfunc(entry) and pe.rfunc(a)[0] != pe.rfunc(entry)[0]:
                    break
            try:
                i = next(md.disasm(pe.tbytes(a, 16), a))
            except StopIteration:
                break
            seen.add(a); out[a] = i
            if i.mnemonic in ('ret', 'int3', 'ud2'):
                break
            if i.mnemonic.startswith('j'):
                op = i.operands[0]
                if op.type == X.X86_OP_IMM:
                    t = op.imm
                    if i.mnemonic == 'jmp':
                        fr = pe.rfunc(t)
                        if fr and fr[0] == t and t != entry:
                            break  # tail call
                        a = t; continue
                    todo.append(t)
                else:
                    todo.extend(t for t in jump_table(pe, out, i) if same_func(pe, entry, t))  # indirect jmp: switch table targets
                    break
            a = i.address + i.size
    return [out[k] for k in sorted(out)]


def same_func(pe, entry, t):
    a, b = pe.rfunc(entry), pe.rfunc(t)
    return bool(a and b and a[0] == b[0])


def jump_table(pe, out, jmp):
    """Targets of an MSVC x64 switch: `cmp r, N; ja ...; lea rB, [rip - base]; mov ecx, [rB + r*4 + T];
    add rcx, rB; jmp rcx` (T = table rva, entries = rva). Looks back over the preceding instructions."""
    prev = [out[k] for k in sorted(out) if k < jmp.address][-12:]
    table = count = None
    for i in reversed(prev):
        for o in i.operands:
            if table is None and o.type == X.X86_OP_MEM and o.mem.scale == 4 and o.mem.index and o.mem.disp > 0x1000:
                table = o.mem.disp
        if count is None and i.mnemonic == 'cmp' and len(i.operands) == 2 and i.operands[1].type == X.X86_OP_IMM:
            count = i.operands[1].imm + 1
    if table is None or count is None or count > 512:
        return []
    out_t = []
    for k in range(count):
        v = pe.read(table + 4 * k, 4)
        if not v:
            break
        t = struct.unpack('<I', v)[0]
        if pe.tva <= t < pe.tva + pe.tsize:
            out_t.append(t)
    return out_t


def resolve(n):
    BN = {v: int(k, 16) for k, v in json.load(open('bgnames.json')).items()}
    return BN[n] if n in BN else int(n, 16)


def diff(a, p, show=True):
    A, B = body(BG, a), body(PT, p)
    na, nb = [norm(i) for i in A], [norm(i) for i in B]
    sm = difflib.SequenceMatcher(None, na, nb, autojunk=False)
    if show:
        print(f'BG {a:#x} PT {p:#x} ratio {sm.ratio():.3f} insns {len(A)}/{len(B)}')
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == 'equal':
                continue
            print('---', tag)
            for i in A[i1:i2]:
                print(f'  BG {i.address:x} {i.mnemonic} {i.op_str}')
            for i in B[j1:j2]:
                print(f'  PT {i.address:x} {i.mnemonic} {i.op_str}')
    return sm.ratio()


if __name__ == '__main__':
    F = {int(k, 16): int(v[0], 16) for k, v in json.load(open('fmap.json')).items()}
    a = resolve(sys.argv[1])
    p = int(sys.argv[2], 16) if len(sys.argv) > 2 else F[a]
    diff(a, p)


def imm_diffs(a, p):
    """Matched instructions (same normalized form) whose immediate operands differ: constants the
    normalized diff hides. Returns [(bg insn, pt insn)]."""
    A, B = body(BG, a), body(PT, p)
    sm = difflib.SequenceMatcher(None, [norm(i) for i in A], [norm(i) for i in B], autojunk=False)
    out = []
    for i1, j1, k in sm.get_matching_blocks():
        for t in range(k):
            x, y = A[i1 + t], B[j1 + t]
            if x.mnemonic.startswith('j') or x.mnemonic == 'call':
                continue
            ix = [o.imm for o in x.operands if o.type == X.X86_OP_IMM]
            iy = [o.imm for o in y.operands if o.type == X.X86_OP_IMM]
            if ix != iy:
                out.append((x, y))
    return out


def data_diffs(a, p):
    """Matched instructions reading RIP-relative data whose initial bytes differ between the two exes
    (engine constants / tables, e.g. Torment's sprite update mask). Returns [(bg insn, pt insn, bg, pt)]."""
    A, B = body(BG, a), body(PT, p)
    sm = difflib.SequenceMatcher(None, [norm(i) for i in A], [norm(i) for i in B], autojunk=False)
    out = []
    for i1, j1, k in sm.get_matching_blocks():
        for t in range(k):
            x, y = A[i1 + t], B[j1 + t]
            if x.mnemonic in ('lea', 'call') or x.mnemonic.startswith('j'):
                continue
            mx = [o for o in x.operands if o.type == X.X86_OP_MEM and o.mem.base == X.X86_REG_RIP]
            my = [o for o in y.operands if o.type == X.X86_OP_MEM and o.mem.base == X.X86_REG_RIP]
            if not mx or not my:
                continue
            sz = mx[0].size or 8
            ta, tb = x.address + x.size + mx[0].mem.disp, y.address + y.size + my[0].mem.disp
            va, vb = BG.read(ta, sz) or bytes(sz), PT.read(tb, sz) or bytes(sz)  # .bss reads as zeros
            if sz == 8:
                qa, qb = struct.unpack('<Q', va)[0], struct.unpack('<Q', vb)[0]
                if BG.base <= qa < BG.base + 0x10000000 and PT.base <= qb < PT.base + 0x10000000:
                    continue  # both are pointers into their image (vtables, strings...): compared by fmap
            if va != vb:
                out.append((x, y, va.hex() if va else None, vb.hex() if vb else None))
    return out


def disp_diffs(a, p):
    """Matched instructions whose non-RIP memory displacements differ (field offsets that moved)."""
    A, B = body(BG, a), body(PT, p)
    sm = difflib.SequenceMatcher(None, [norm(i) for i in A], [norm(i) for i in B], autojunk=False)
    out = []
    for i1, j1, k in sm.get_matching_blocks():
        for t in range(k):
            x, y = A[i1 + t], B[j1 + t]
            dx = [o.mem.disp for o in x.operands if o.type == X.X86_OP_MEM and o.mem.base != X.X86_REG_RIP]
            dy = [o.mem.disp for o in y.operands if o.type == X.X86_OP_MEM and o.mem.base != X.X86_REG_RIP]
            if dx != dy:
                out.append((x, y))
    return out
