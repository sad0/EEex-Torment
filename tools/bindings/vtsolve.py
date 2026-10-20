# BG -> PT virtual slot map for every class with a vtable struct in the header.
#  1. BG vtable of class S: constructor store (vtables.json), else the .rdata vtable (RIP-LEA target,
#     bounded by the next one) whose slots carry the header's method names (bgnames.json), with at
#     least one slot named S:: (own override) and a unique best score.
#  2. PT vtable of S: constructor counterpart, else votes of BG LEA sites loading the BG vtable, mapped
#     to PT through fmap + instruction alignment (the aligned PT instruction must be a LEA too).
#  3. Slot map: difflib on slot tokens (fmap counterpart / PT identity, body hash for unmapped), equal
#     gaps between anchors filled positionally, inherited prefix forced to the base class' map, typed
#     virtual-call evidence (vtable_evidence.json, from fieldmap.py) checked against the map.
# Output: bindings/vtmap.json {S: {"bg_vt", "pt_vt", "n", "map": [pt slot | null], "proof": [...], "pt_only": [...]}}
import sys, os, json, re, struct, collections, difflib
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import capstone
from fmap import BG, PT, align
from vtcheck import BV, PV
from vtfind import ctor_vtable, body_hash

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64); md.detail = True
F = {int(k, 16): int(v[0], 16) for k, v in json.load(open('fmap.json')).items()}
BN = {int(k, 16): v for k, v in json.load(open('bgnames.json')).items()}
HDR = '../ref/InfinityLoader/Core-Shared-Files/generate_bindings/in/Baldur-v2.6.6.0.h'
RX_ENTRY = re.compile(r'\(__\w+ \*([~\w]+)\)\((?:const )?(\w+) \*this')


def header_vtbls(text):
    """{S: [(method, this_type, line)]} and base class of S."""
    out, base = {}, {}
    for m in re.finditer(r'struct /\*VFT\*/ (\w+)_vtbl\n\{\n(.*?)\n\};', text, re.S):
        ents = []
        for ln in m.group(2).split('\n'):
            e = RX_ENTRY.search(ln)
            ents.append((e.group(1), e.group(2), ln) if e else (None, None, ln))
        out[m.group(1)] = ents
    for m in re.finditer(r'struct __cppobj (?:/\*VFT\*/ )?(?:__declspec\(align\(\d+\)\) )?(\w+) : (\w+)', text):
        base[m.group(1)] = m.group(2)
    return out, base


def meth(n):
    m = n.rsplit('::', 1)
    dt = m[-1].startswith('~') or 'destructor' in m[-1]
    return ('~' if dt else m[-1]), (m[0] if len(m) == 2 else '')


def bg_vtable(S, ents, ctor):
    if S in ctor:
        return int(ctor[S]['bg_vt'], 16), 'ctor'
    n = len(ents)
    # constructors / destructors named in bgnames store the vtable into [this]
    stores = collections.Counter()
    for a, nm in BN.items():
        c, _, f = nm.rpartition('::')
        if c == S and f in (S, '~' + S):
            v = ctor_vtable(BG, a)
            if v:
                stores[v] += 1
    if len(stores) == 1:
        v = next(iter(stores))
        if len(BV.get(v)) >= n:
            return v, 'ctor/dtor store'
    best = []
    for v in BV.starts:
        sl = BV.get(v)
        if len(sl) < n:
            continue
        hits = own = bad = 0
        for k, (name, this, _) in enumerate(ents):
            if name is None or sl[k] not in BN:
                continue
            mn, cls = meth(BN[sl[k]])
            want = '~' if name.startswith('~') else name
            if mn == want:
                hits += 1
                own += cls == S
            else:
                bad += 1
        if own and bad * 4 <= hits:
            best.append((own, hits - bad, v))
    if not best:
        return None, 'no named vtable'
    best.sort(reverse=True)
    top = [b for b in best if b[:2] == best[0][:2]]
    if len(set(tuple(BV.get(b[2])[:n]) for b in top)) > 1:
        return None, f'ambiguous {[hex(b[2]) for b in top[:3]]}'
    return best[0][2], f'names {best[0][1]}/{n} own {best[0][0]}'


LEA = None


def lea_sites(pe):
    """{rdata target: [instruction address]} for REX LEA reg, [rip + d]."""
    import numpy as np
    a = np.frombuffer(pe.text, dtype=np.uint8)
    rex = (a[:-6] == 0x48) | (a[:-6] == 0x4C)
    m = rex & (a[1:-5] == 0x8D) & ((a[2:-4] & 0xC7) == 0x05)
    d = a[3:-3].astype(np.int64) | (a[4:-2].astype(np.int64) << 8) | (a[5:-1].astype(np.int64) << 16) | (a[6:].astype(np.int64) << 24)
    d = np.where(d >= 2**31, d - 2**32, d)
    pos = np.nonzero(m)[0]
    out = collections.defaultdict(list)
    for p, t in zip(pos, pos + pe.tva + 7 + d[pos]):
        out[int(t)].append(int(p) + pe.tva)
    return out


def pt_vtable(S, bvt, ctor, n):
    global LEA
    if S in ctor and int(ctor[S]['bg_vt'], 16) == bvt:
        return int(ctor[S]['pt_vt'], 16), 'ctor'
    if LEA is None:
        LEA = lea_sites(BG)
    votes = collections.Counter()
    for site in LEA.get(bvt, []):
        fr = BG.rfunc(site)
        if not fr or fr[0] not in F:
            continue
        mp, r, _, _ = align(fr[0], F[fr[0]])
        pa = mp.get(site)
        if pa is None or r < 0.6:
            continue
        i = next(iter(md.disasm(PT.tbytes(pa, 16), pa)), None)
        if i is None or i.mnemonic != 'lea' or 'rip' not in i.op_str:
            continue
        votes[i.address + i.size + i.operands[1].mem.disp] += 1
    if not votes:
        return content_match(bvt, n)
    (a, c), *rest = votes.most_common()
    if rest and rest[0][1] * 3 > c:
        return None, f'split lea votes {votes.most_common(3)}'
    return a, f'lea votes {c}/{sum(votes.values())}'


IDX = None


def content_match(bvt, n):
    """PT vtable holding the fmap counterparts of the BG slots, weighted by how specific each slot is."""
    global IDX
    if IDX is None:
        bocc, pidx = collections.Counter(), collections.defaultdict(set)
        for v in BV.starts:
            for f in set(BV.get(v)):
                bocc[f] += 1
        for v in PV.starts:
            for f in PV.get(v):
                pidx[f].add(v)
        IDX = bocc, pidx
    bocc, pidx = IDX
    bs = BV.get(bvt)[:n]
    sc = collections.Counter()
    spec = 0
    for f in set(bs):
        if f in F and bocc[f] <= 3:
            spec += 1
            for v in pidx.get(F[f], ()):
                sc[v] += 1.0 / bocc[f]
    if not sc:
        return None, 'no content match'
    (a, c), *rest = sc.most_common()
    if rest and rest[0][1] >= c * 0.8:
        return None, f'content ambiguous {[(hex(x), round(y, 2)) for x, y in sc.most_common(3)]}'
    if c < 1:
        return None, f'content weak {round(c, 2)}'
    return a, f'content {round(c, 2)} of {spec} specific slots'


def token_bg(f):
    return ('f', F[f]) if f in F else ('h', body_hash(BG, f))


def slot_map(bs, ps):
    tb = [token_bg(f) for f in bs]
    bgf = set(t for t in tb if t[0] == 'f')
    tp = [('f', f) if ('f', f) in bgf else ('h', body_hash(PT, f)) for f in ps]
    m, proof = [None] * len(bs), [None] * len(bs)
    ops = difflib.SequenceMatcher(None, tb, tp, autojunk=False).get_opcodes()
    for tag, i1, i2, j1, j2 in ops:
        if tag == 'equal':
            for d in range(i2 - i1):
                m[i1 + d], proof[i1 + d] = j1 + d, 'same function' if tb[i1 + d][0] == 'f' else 'same body'
    # equal-size gaps between two anchors (or before the first / after the last when the PT list continues)
    for tag, i1, i2, j1, j2 in ops:
        if tag == 'replace' and i2 - i1 == j2 - j1 and i1 > 0:
            for d in range(i2 - i1):
                m[i1 + d], proof[i1 + d] = j1 + d, 'gap'
        if tag == 'delete' and i2 < len(bs):
            # BG slots with no PT slot between two anchors: virtual removed in Torment
            for d in range(i1, i2):
                proof[d] = 'removed'
    # slot 0 = virtual destructor of the root class (scalar deleting destructor: tests the delete flag)
    if m and m[0] is None and ps and is_dtor(PT, ps[0]) and is_dtor(BG, bs[0]):
        m[0], proof[0] = 0, 'destructor'
    return m, proof


def is_dtor(pe, f, depth=0):
    for i in md.disasm(pe.tbytes(f, 0x100), f):
        if i.mnemonic in ('test', 'and') and i.op_str.endswith(', 1') and i.op_str.split(',')[0] in ('dl', 'edx', 'bl', 'ebx', 'sil', 'esi', 'dil', 'edi', 'r8b', 'r8d', 'bpl', 'ebp'):
            return True
        if i.mnemonic == 'jmp' and depth < 2 and i.operands[0].type == capstone.x86_const.X86_OP_IMM:
            return is_dtor(pe, i.operands[0].imm, depth + 1)
        if i.mnemonic in ('ret', 'int3'):
            return False
    return False


def main():
    text = open(HDR, encoding='utf-8', errors='replace').read()
    vt, base = header_vtbls(text)
    ctor = json.load(open('bindings/vtables.json'))
    ev = {}
    if os.path.exists('bindings/vtable_evidence.json'):
        for k, v in json.load(open('bindings/vtable_evidence.json')).items():
            s, d = k.split('|')
            ev[(s, int(d, 16) // 8)] = {int(a, 16) // 8: c for a, c in v.items()}
    out = {}
    order = []

    def depth(S):
        n = 0
        while S in base:
            S = base[S]; n += 1
        return n
    for S in sorted(vt, key=depth):
        ents = vt[S]
        n = len(ents)
        bvt, why = bg_vtable(S, ents, ctor)
        rec = {'n': n, 'bg_why': why}
        out[S] = rec
        if bvt is None:
            continue
        pvt, pwhy = pt_vtable(S, bvt, ctor, n)
        rec.update(bg_vt=hex(bvt), pt_why=pwhy)
        if pvt is None:
            continue
        rec['pt_vt'] = hex(pvt)
        bs, ps = BV.get(bvt)[:n], PV.get(pvt)
        m, proof = slot_map(bs, ps)
        # inherited prefix: the base class' slots must map like the base
        B = base.get(S)
        while B and B not in vt:
            B = base.get(B)
        if B and out.get(B, {}).get('map'):
            bm, bp = out[B]['map'], out[B]['proof']
            for k in range(min(len(bm), n)):
                if bp[k] == 'removed' and m[k] is None:
                    proof[k] = 'removed'
                elif bm[k] is not None and m[k] is None and bp[k] != 'unresolved':
                    m[k], proof[k] = bm[k], 'base class'
                elif bm[k] != m[k] and m[k] is not None and bm[k] is not None:
                    proof[k] = f'conflict with base {bm[k]}'
        # typed virtual-call evidence
        for k in range(n):
            e = ev.get((S, k))
            if e:
                top = max(e, key=e.get)
                if m[k] is None and e[top] >= 2 and e[top] >= 0.9 * sum(e.values()):
                    m[k], proof[k] = top, f'vcalls {e[top]}'
                elif m[k] is not None and top != m[k] and e[top] >= 2:
                    proof[k] = f'conflict vcalls {e}'
        rec.update(map=m, proof=[p or 'unresolved' for p in proof], pt_len=len(ps))
    json.dump(out, open('bindings/vtmap.json', 'w'), indent=0)
    full = [S for S, r in out.items() if r.get('map') and not any(p == 'unresolved' or 'conflict' in p for p in r['proof'])]
    print('vtbl classes', len(out), 'BG vt', sum('bg_vt' in r for r in out.values()), 'PT vt', sum('pt_vt' in r for r in out.values()), 'fully mapped', len(full))
    moved = [S for S in full if any(x != k for k, x in enumerate(out[S]['map']))]
    print('fully mapped with moved slots', len(moved))
    bad = collections.Counter(r['bg_why'].split()[0] for r in out.values() if 'bg_vt' not in r)
    print('no BG vtable', dict(bad))
    print('no PT vtable', collections.Counter(r['pt_why'].split()[0] for r in out.values() if 'bg_vt' in r and 'pt_vt' not in r))


if __name__ == '__main__':
    main()
