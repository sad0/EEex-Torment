# Phase 5 audit of every EEex Lua hook site: for each EEex_Hook*/EEex_JITAt/... call on an EEex_Label,
# compare the BG2EE site (port2.json bg_key) with the Torment site (gen_report.json addr):
#  - overwritten bytes: instruction kinds and lengths in the patched region (short vs near jumps,
#    restore sizes that would split a Torment instruction);
#  - registers and frame slots the hook code reads: BG -> Torment register / stack mapping taken from the
#    aligned instructions around the site (same instruction shape, registers abstracted);
#  - hard-coded struct offsets in the hook assembly ([reg + 0x...]): to be checked against the PT layout.
#   python luahooks.py            -> luahooks.json + summary of the hooks needing a Torment change
import re, json, glob, os, difflib, collections
import capstone
from capstone import x86_const as X
from ilib import REPO
from fmap import BG, PT

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64); md.detail = True
SRC = REPO + r'\ref\EEex\EEex\copy\EEex_scripts'
G = json.load(open('gen_report.json')); R = json.load(open('port2.json'))
F = {int(k, 16): int(v[0], 16) for k, v in json.load(open('fmap.json')).items()}

REG64 = {}
for full, parts in {
    'rax': 'eax ax al ah', 'rbx': 'ebx bx bl bh', 'rcx': 'ecx cx cl ch', 'rdx': 'edx dx dl dh',
    'rsi': 'esi si sil', 'rdi': 'edi di dil', 'rbp': 'ebp bp bpl', 'rsp': 'esp sp spl'}.items():
    REG64[full] = full
    for p in parts.split():
        REG64[p] = full
for n in range(8, 16):
    for suf in ('', 'd', 'w', 'b'):
        REG64[f'r{n}{suf}'] = f'r{n}'
for n in range(16):
    REG64[f'xmm{n}'] = f'xmm{n}'
REG_RX = re.compile(r'\b(' + '|'.join(sorted(REG64, key=len, reverse=True)) + r')\b')

HOOK_FN = re.compile(r'\b(EEex_(?:Hook[A-Za-z]*|JITAt|ForceJump|ReplaceCall|Write\d+|WriteU?\d+|WriteArgs|'
                     r'WriteAssembly|HookIntegrityWatchdog_[A-Za-z]+))\(\s*EEex_Label\(\s*("([^"]+)"|[A-Za-z_]+)\s*\)')


def call_text(s, i):
    """Text of the call whose '(' is at s[i]: balanced parentheses, skipping [[...]] strings and comments."""
    depth, j = 0, i
    while j < len(s):
        if s.startswith('[[', j):
            j = s.index(']]', j) + 2; continue
        if s.startswith('--', j):
            if s.startswith('--[[', j):
                j = s.index(']]', j) + 2
            else:
                j = s.index('\n', j)
            continue
        if s[j] == '"':
            j = s.index('"', j + 1) + 1; continue
        c = s[j]
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                return s[i:j + 1]
        j += 1
    return s[i:]


def loop_labels(s, pos, var):
    """`for _, var in ipairs({ "A", "B" }) do` preceding pos -> the label names."""
    m = None
    for m in re.finditer(r'for\s+_\s*,\s*' + var + r'\s+in\s+ipairs\(\s*\{(.*?)\}\s*\)\s*do', s[:pos], re.S):
        pass
    return re.findall(r'"([^"]+)"', m.group(1)) if m else []


def numeric_args(text):
    """Numbers following the EEex_Label(...) argument, before the first table/function argument."""
    m = re.search(r'EEex_Label\(\s*(?:"[^"]*"|[A-Za-z_]+)\s*\)\s*,(.*)', text, re.S)
    if not m:
        return []
    out = []
    for tok in m.group(1).split(','):
        tok = tok.strip()
        if re.fullmatch(r'-?(0x[0-9a-fA-F]+|\d+)', tok):
            out.append(int(tok, 0))
        else:
            break
    return out


def addr_of(label):
    g = G.get(label); r = R.get(label)
    pt = int(g['addr'], 16) if g and g.get('addr') else None
    bg = int(r['bg_key'], 16) if r and r.get('bg_key') else None
    if bg and pt and PT.rfunc(pt) and PT.rfunc(pt)[0] == pt and BG.read(bg - 1, 1) in (b'\xe8', b'\xe9'):
        # port2.json keys a function-entry label by the rel32 of a call / jmp to it
        bg = bg + 4 + int.from_bytes(BG.read(bg, 4), 'little', signed=True)
    return bg, pt, (g or {}).get('status'), (g or {}).get('note', '')


def insns(pe, a, n):
    return list(md.disasm(pe.tbytes(a, 16 * n), a))[:n]


def region(pe, a, size):
    """Instructions starting in [a, a+size) and the byte end of the last one."""
    out, cur = [], a
    while cur < a + size:
        i = next(md.disasm(pe.tbytes(cur, 16), cur), None)
        if i is None:
            break
        out.append(i); cur += i.size
    return out, cur


def shape(i):
    """Instruction with registers and constants abstracted (for alignment across register allocation)."""
    ops = []
    for o in i.operands:
        if o.type == X.X86_OP_REG:
            ops.append('r%d' % o.size)
        elif o.type == X.X86_OP_IMM:
            ops.append('i')
        else:
            ops.append('m%d%s' % (o.size, 'rip' if o.mem.base == X.X86_REG_RIP else ''))
    return i.mnemonic + ' ' + ','.join(ops)


def func_body(pe, a):
    fr = pe.rfunc(a)
    if not fr:
        return []
    from fdiff import body
    return body(pe, fr[0])


def regmap(bg, pt, window=40):
    """BG register / frame slot -> Torment counterpart from the aligned instructions around the sites.
    Returns {bg_reg: [(distance, pt_reg)]}, {('rsp'|'rbp', bg_disp): [(distance, (base, pt_disp))]}."""
    A, B = func_body(BG, bg), func_body(PT, pt)
    if not A or not B:
        return {}, {}, 0
    ka = min(range(len(A)), key=lambda k: abs(A[k].address - bg))
    kb = min(range(len(B)), key=lambda k: abs(B[k].address - pt))
    A2, B2 = A[max(0, ka - window):ka + window], B[max(0, kb - window):kb + window]
    sm = difflib.SequenceMatcher(None, [shape(i) for i in A2], [shape(i) for i in B2], autojunk=False)
    regs, slots = collections.defaultdict(list), collections.defaultdict(list)
    for i1, j1, k in sm.get_matching_blocks():
        for t in range(k):
            x, y = A2[i1 + t], B2[j1 + t]
            d = x.address - bg
            for ox, oy in zip(x.operands, y.operands):
                if ox.type == X.X86_OP_REG:
                    rx, ry = REG64.get(x.reg_name(ox.reg)), REG64.get(y.reg_name(oy.reg))
                    if rx and ry:
                        regs[rx].append((d, ry))
                elif ox.type == X.X86_OP_MEM:
                    if ox.mem.base and oy.mem.base:
                        rx, ry = REG64.get(x.reg_name(ox.mem.base)), REG64.get(y.reg_name(oy.mem.base))
                        if rx and ry:
                            regs[rx].append((d, ry))
                            if rx in ('rsp', 'rbp'):
                                slots[(rx, ox.mem.disp)].append((d, (ry, oy.mem.disp)))
    return regs, slots, round(sm.ratio(), 2)


def nearest(lst):
    """Closest mappings to the site (before the site preferred: the value live at the hook)."""
    if not lst:
        return None
    best = sorted(lst, key=lambda x: (abs(x[0]), x[0] > 0))[:3]
    vals = collections.Counter(v for _, v in best)
    return vals.most_common(1)[0][0], len(set(vals)) > 1


# hook kinds: bytes overwritten at the label
def patched_size(fn, nums, bgi):
    if 'Call' in fn and 'Restore' not in fn:
        return 5
    if 'ConditionalJump' in fn:
        return bgi.size + (nums[0] if nums else 0)
    if 'Restore' in fn and nums:
        d1 = nums[0]
        if 'Between' in fn and len(nums) >= 5:
            return max(nums[4], nums[2] + nums[3])
        return max(nums[2] if len(nums) > 2 else 0, d1 + (nums[1] if len(nums) > 1 else 0))
    if 'NOPs' in fn and nums:
        return nums[0]
    if 'RelativeJump' in fn or 'ForceJump' in fn:
        return bgi.size
    return 5


def asm_refs(text):
    """Registers and memory operands named in the hook text (assembly + generated Lua-call args)."""
    asm = ' '.join(re.findall(r'\[\[(.*?)\]\]', text, re.S)) + ' ' + ' '.join(re.findall(r'"([^"]*)"', text))
    asm = re.sub(r';[^\n]*', '', asm)
    regs = sorted({REG64[r] for r in REG_RX.findall(asm)})
    mems = sorted(set(re.findall(r'\[[^\]]*\]', asm)))
    offs = [m for m in mems if re.search(r'\b(r(?:[a-d]x|si|di|8|9|1[0-5]))\s*[+-]\s*(0x[0-9a-fA-F]+|[0-9][0-9a-fA-F]*h?)\b', m)
            and 'SHADOW_SPACE' not in m and '#$' not in m]
    frame = [m for m in mems if re.search(r'\b(rsp|rbp)\b', m) and 'SHADOW_SPACE_BOTTOM' not in m and '#$(' not in m]
    return regs, offs, frame


def main():
    hooks = []
    for path in sorted(glob.glob(SRC + r'\*.lua')):
        s = open(path, encoding='utf-8').read()
        for m in HOOK_FN.finditer(s):
            fn = m.group(1)
            text = call_text(s, s.index('(', m.start()))
            labels = [m.group(3)] if m.group(3) else loop_labels(s, m.start(), m.group(2))
            line = s.count('\n', 0, m.start()) + 1
            for lab in labels:
                hooks.append((os.path.basename(path), line, fn, lab, text))
    out, flagged = [], 0
    for fname, line, fn, lab, text in hooks:
        bg, pt, status, note = addr_of(lab)
        e = {'file': fname, 'line': line, 'fn': fn, 'label': lab, 'status': status, 'note': note,
             'bg': hex(bg) if bg else None, 'pt': hex(pt) if pt else None, 'issues': []}
        out.append(e)
        if status != 'ported' or not bg or not pt:
            e['issues'].append('label not ported: ' + str(status))
            flagged += 1
            continue
        if 'Watchdog' in fn:
            continue
        nums = numeric_args(text)
        e['args'] = nums
        bi, pi = insns(BG, bg, 1), insns(PT, pt, 1)
        if not bi or not pi:
            e['issues'].append('no instruction at site'); flagged += 1; continue
        size = patched_size(fn, nums, bi[0])
        rb, endb = region(BG, bg, size)
        rp, endp = region(PT, pt, size)
        e['bg_region'] = [f'{i.address:x} {i.mnemonic} {i.op_str}' for i in rb]
        e['pt_region'] = [f'{i.address:x} {i.mnemonic} {i.op_str}' for i in rp]
        if [(i.mnemonic, i.size) for i in rb] != [(i.mnemonic, i.size) for i in rp] or endb - bg != endp - pt:
            e['issues'].append('patched region differs')
        # restored bytes are copied verbatim (EEex_StoreBytesAssembly): no RIP-relative operand / relative branch
        if 'Restore' in fn or 'ConditionalJump' in fn:
            first = bi[0].size if 'ConditionalJump' in fn else 0
            for i in rp:
                if i.address >= pt + first and ('rip' in i.op_str or (i.mnemonic.startswith('j') or i.mnemonic == 'call')
                                                 and i.operands and i.operands[0].type == X.X86_OP_IMM):
                    e['issues'].append(f'restored PT bytes not relocatable: {i.mnemonic} {i.op_str}')
        if 'Call' in fn and 'Restore' not in fn and not (bi[0].mnemonic == 'call' and pi[0].mnemonic == 'call'):
            e['issues'].append(f'call hook on {bi[0].mnemonic}/{pi[0].mnemonic}')
        if 'ConditionalJump' in fn and not (pi[0].mnemonic.startswith('j') and pi[0].mnemonic != 'jmp'):
            e['issues'].append('jcc hook on ' + pi[0].mnemonic)
        if 'ConditionalJump' in fn and bi[0].mnemonic != pi[0].mnemonic:
            e['issues'].append(f'jcc condition {bi[0].mnemonic} -> {pi[0].mnemonic}')
        # call target / jump target counterparts
        for x, y in zip(rb, rp):
            if x.mnemonic in ('call', 'jmp') or x.mnemonic.startswith('j'):
                if x.operands and x.operands[0].type == X.X86_OP_IMM and y.operands and y.operands[0].type == X.X86_OP_IMM:
                    tx, ty = x.operands[0].imm, y.operands[0].imm
                    if x.mnemonic == 'call' and tx in F and F[tx] != ty:
                        e['issues'].append(f'call target {tx:#x} -> fmap {F[tx]:#x}, PT calls {ty:#x}')
        regs, offs, frame = asm_refs(text)
        rm, sm_, ratio = regmap(bg, pt)
        e['ctx_ratio'] = ratio
        e['regs'] = {}
        for r in regs:
            if r in ('rsp',):
                continue
            n = nearest(rm.get(r, []))
            e['regs'][r] = n[0] if n else None
            if n and (n[0] != r or n[1]):
                e['issues'].append(f'register {r} -> {n[0]}' + (' (ambiguous)' if n[1] else ''))
        if offs:
            e['struct_offsets'] = offs
            e['issues'].append('hard-coded offsets ' + ' '.join(offs))
        if frame:
            e['frame_refs'] = frame
            e['frame_map'] = {f'{k[0]}{k[1]:+#x}': '{}{:+#x}'.format(*nearest(v)[0]) for k, v in sorted(sm_.items())}
            e['issues'].append('frame refs ' + ' '.join(frame))
        if e['issues']:
            flagged += 1
    json.dump(out, open('luahooks.json', 'w'), indent=1)
    print('hook uses', len(out), 'flagged', flagged)
    by = collections.Counter(e['file'] for e in out if e['issues'])
    print(dict(by))


if __name__ == '__main__':
    main()
