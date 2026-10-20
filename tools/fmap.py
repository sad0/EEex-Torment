# Function-level mapping BG2EE -> Torment: call-graph propagation + instruction alignment.
#  - callers(pe, T): call/jmp rel32 sites targeting T
#  - func_insns(pe, F): linear disassembly of function F up to int3 padding
#  - align(bgF, ptF): normalized-instruction alignment, maps BG instruction addresses to PT
#  - map_func(bgF): Torment function for a BG function, by start-voting and caller propagation
import re, difflib, collections, functools
import numpy as np
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from ilib import *

md = Cs(CS_ARCH_X86, CS_MODE_64)
BG, PT = PE(BG_EXE), PE(PT_EXE)


def norm(i):
    return f"{i.mnemonic} {re.sub(r'0x[0-9a-f]+', 'N', i.op_str)}"


def _calltab(pe):
    a = np.frombuffer(pe.text, dtype=np.uint8)
    rel = a[1:-3].astype(np.int64) | (a[2:-2].astype(np.int64) << 8) | (a[3:-1].astype(np.int64) << 16) | (a[4:].astype(np.int64) << 24)
    rel = np.where(rel >= 2**31, rel - 2**32, rel)
    pos = np.arange(len(rel))
    op = a[:-4]
    m = (op == 0xE8) | (op == 0xE9)
    tgt = pos + 5 + rel + pe.tva
    ok = m & (tgt >= pe.tva) & (tgt < pe.tva + pe.tsize)
    tab = collections.defaultdict(list)
    for p, t, o in zip(pos[ok], tgt[ok], op[ok]):
        tab[int(t)].append((int(p) + pe.tva, int(o)))
    return tab


CT = {}


def callers(pe, t):
    if id(pe) not in CT:
        CT[id(pe)] = _calltab(pe)
    return CT[id(pe)].get(t, [])


@functools.lru_cache(maxsize=None)
def func_insns(pe_name, f, limit=20000):
    pe = BG if pe_name == 'BG' else PT
    out = []
    fr = pe.rfrag(f)
    if fr and fr[0] == f:
        limit = fr[1] - f
    for i in md.disasm(pe.tbytes(f, limit), f):
        if i.mnemonic == 'int3':
            break
        out.append((i.address, i.size, norm(i), i.mnemonic, i.op_str))
    return tuple(out)


def align(bgF, ptF):
    """Map each BG instruction address to PT (exact block matches only). Returns dict, ratio."""
    a, b = func_insns('BG', bgF), func_insns('PT', ptF)
    sm = difflib.SequenceMatcher(None, [x[2] for x in a], [x[2] for x in b], autojunk=False)
    mp = {}
    for i, j, n in sm.get_matching_blocks():
        for k in range(n):
            mp[a[i + k][0]] = b[j + k][0]
    return mp, sm.ratio(), a, b


def map_key(bgF, ptF, key):
    """Map BG address key (instruction start or inside one) into PT using function alignment."""
    mp, r, a, b = align(bgF, ptF)
    ins = next((x for x in a if x[0] <= key < x[0] + x[1]), None)
    if ins is None:
        return None, r, 'key outside BG function'
    if ins[0] in mp:
        return mp[ins[0]] + (key - ins[0]), r, 'aligned'
    # nearest aligned neighbours (for reporting)
    return None, r, 'key in unmatched region'


def call_targets_in(pe_name, f):
    """Ordered list of direct call targets made by function f."""
    pe = BG if pe_name == 'BG' else PT
    out = []
    for adr, sz, n, mn, ops in func_insns(pe_name, f):
        if mn == 'call' and re.fullmatch(r'0x[0-9a-f]+', ops):
            out.append((adr, int(ops, 16)))
    return out


def map_by_callers(bgT, known):
    """Votes for PT address of BG function bgT using call sites inside already-mapped callers.
    known: {bgF: ptF} for mapped functions."""
    v = collections.Counter()
    for site, op in callers(BG, bgT):
        f = BG.fstart(site)
        if f not in known:
            continue
        mp, r, a, b = align(f, known[f])
        if site in mp:
            ps = mp[site]
            t = ps + 5 + PT.i32(ps + 1)
            if PT.tbytes(ps, 1)[0] in (0xE8, 0xE9):
                v[t] += 1
    return v


def map_by_callees(bgF, known):
    """Votes for PT function start of bgF using its already-mapped callees: each mapped callee's
    PT callers' functions vote."""
    v = collections.Counter()
    for site, t in call_targets_in('BG', bgF):
        if t in known:
            for ps, op in callers(PT, known[t]):
                v[PT.fstart(ps)] += 1
    return v


_FR = {}


def fragments(pe_name, f):
    """Primary fragment start f plus every chained fragment whose primary is f."""
    pe = BG if pe_name == 'BG' else PT
    if pe_name not in _FR:
        d = collections.defaultdict(list)
        for b, e, u in pe.rf:
            p = pe.rfunc(b)
            if p and p[0] != b:
                d[p[0]].append(b)
        _FR[pe_name] = d
    return [f] + sorted(_FR[pe_name].get(f, []))


def whole_ratio(bgf, ptf):
    """Alignment ratio over the whole function (primary + cold fragments, concatenated)."""
    a = [x[2] for g in fragments('BG', bgf) for x in func_insns('BG', g)]
    b = [x[2] for g in fragments('PT', ptf) for x in func_insns('PT', g)]
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio(), len(a), len(b)
