# Port InfinityLoader.db entries from BG2EE (Baldur.exe v2.6.6.0) to Torment.exe v3.2.2.0.
# For each entry: resolve the key address in BG2 (target for code patterns, rel32/imm field site
# otherwise), then vote for its Torment location with masked instruction windows (capstone):
# rel32 branches and RIP-relative displacements are wildcarded, so moved code still matches.
# Output: port2.json {name: {...}}; run with -j N for multiprocessing.
import sys, re, json, collections, multiprocessing as mp
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from ilib import *

md = Cs(CS_ARCH_X86, CS_MODE_64); md.detail = True
BG = PT = None


def init():
    global BG, PT
    BG, PT = PE(BG_EXE), PE(PT_EXE)


def disasm(pe, start, end):
    code = pe.tbytes(start, end - start)
    return list(md.disasm(code, start))


def masked(ins, loose):
    """Regex for one instruction with relocatable fields wildcarded."""
    b = bytearray(ins.bytes); mask = [False] * len(b)
    def m(o, n):
        for i in range(o, o + n):
            if 0 <= i < len(b): mask[i] = True
    try:
        e = ins.encoding
        rel = ins.group(7) or ins.group(1) or ins.group(2)  # relative / jump / call
        rip = any(op.type == 3 and op.mem.base == 41 for op in ins.operands)  # X86_REG_RIP = 41
        if e.disp_size and (rip or (loose and e.disp_size == 4)):
            m(e.disp_offset, e.disp_size)
        if e.imm_size and (rel and e.imm_size == 4 or loose and e.imm_size == 4 and not rel):
            m(e.imm_offset, e.imm_size)
        if loose and e.disp_size == 1 and not rip:
            m(e.disp_offset, 1)
    except Exception:
        pass
    return b''.join(b'.' if mask[i] else re.escape(bytes([b[i]])) for i in range(len(b)))


def vote(key, span=40, lens=(4, 6, 9)):
    """Vote for the Torment RVA of BG RVA `key` (inside or at an instruction)."""
    fs = BG.fstart(key)
    lo = max(fs, key - 400)
    # disassemble from function start (instruction boundaries), keep a window around key
    ins = disasm(BG, fs, key + 600)
    ins = [i for i in ins if i.address >= lo]
    idx = next((k for k, i in enumerate(ins) if i.address <= key < i.address + i.size), None)
    if idx is None:
        return None, []
    votes = collections.Counter()
    for loose in (False, True):
        sig = [masked(i, loose) for i in ins]
        for L in lens:
            for s in range(max(0, idx - span), min(len(ins) - L, idx + span) + 1):
                w = b''.join(sig[s:s + L])
                if len(ins[s + L - 1].bytes) + ins[s + L - 1].address - ins[s].address < 10:
                    continue
                hits = itertools_islice(re.finditer(w, PT.text, re.S), 2)
                if len(hits) != 1:
                    continue
                h = hits[0]
                if s <= idx < s + L:
                    # window covers the key: masked fields keep lengths, offset is exact
                    cand = h.start() + PT.tva + (key - ins[s].address)
                    wgt = 4 if not loose else 2
                elif s > idx:
                    cand = h.start() + PT.tva + (key - ins[s].address)
                    wgt = 1
                else:
                    end = ins[s + L - 1].address + ins[s + L - 1].size
                    cand = h.end() + PT.tva + (key - end)
                    wgt = 1
                votes[cand] += wgt
    votes = refine(ins[idx], key, ins, idx, votes)
    return ins[idx], votes.most_common(3)


def refine(ib, key, ins, idx, votes):
    """Snap candidates to a Torment instruction semantically equal to the BG key instruction."""
    if not votes:
        return votes
    fstart = key == BG.fstart(key)
    want = norm(ib); delta = key - ib.address
    out = collections.Counter()
    for cand, c in votes.items():
        best = None
        for d in sorted(range(-40, 41), key=abs):
            a = cand + d - delta
            if fstart and not (PT.tbytes(a - 1, 1) == b'\xcc'):
                continue
            i = next(iter(md.disasm(PT.tbytes(a, 16), a)), None)
            if i and norm(i) == want:
                best = a + delta; break
        out[best if best is not None else cand] += c
    return out


def itertools_islice(it, n):
    out = []
    for x in it:
        out.append(x)
        if len(out) >= n: break
    return out


def ins_at(pe, rva):
    fs = pe.fstart(rva)
    for i in md.disasm(pe.tbytes(fs, rva - fs + 16), fs):
        if i.address <= rva < i.address + i.size:
            return i
        if i.address > rva:
            break
    return None


def norm(i):
    """Instruction text with hex constants dropped, for semantic comparison."""
    return (i.mnemonic + ' ' + re.sub(r'0x[0-9a-f]+', 'N', i.op_str)) if i else None


def unique_pat(key, kind, inner=0):
    """Smallest unique Torment pattern for key (pattern start + ADD offset)."""
    # try starting at key, then at preceding offsets (positive ADD), then following
    for L in range(6, 48):
        b = PT.tbytes(key, L)
        if PT.count(b) == 1:
            return b.hex().upper(), 0
    for d in range(1, 64):
        for L in range(6, 40):
            b = PT.tbytes(key - d, L)
            if PT.count(b) == 1:
                return b.hex().upper(), d
    return None, None


def work(name):
    up = UPE[name]; pat, ops = up.get('Pattern'), up.get('Operations', '')
    r = {'name': name}
    if not pat:
        r['status'] = 'nopattern'; return r
    kind, k = classify(ops)
    r['kind'] = kind
    hs = BG.find(pat)
    if len(hs) == 0:
        r['status'] = 'bg-missing'; return r
    m = hs[0]
    if kind == 'A':
        key = m + k
    elif kind in 'BC':
        key = m + k  # rel32 / imm field site
    else:
        r['status'] = 'ops?'; return r
    r['bg_key'] = hex(key)
    if kind == 'B':
        r['bg_target'] = hex(eval_ops(BG, m, ops))
    i_bg, v = vote(key)
    r['votes'] = [(hex(a), c) for a, c in v]
    # current DB pattern resolution in Torment
    cur = PTDB.get(PTNAME[name], {})
    if cur.get('Pattern'):
        th = PT.find(cur['Pattern'])
        r['cur_hits'] = len(th)
        if th:
            try:
                r['cur_final'] = hex(eval_ops(PT, th[0], cur.get('Operations', '')))
            except Exception:
                r['cur_final'] = None
    if not v:
        r['status'] = 'novote'; return r
    best, c = v[0]
    second = v[1][1] if len(v) > 1 else 0
    r['conf'] = confof(v)
    i_pt = next(iter(md.disasm(PT.tbytes(best - (key - i_bg.address), 16), best - (key - i_bg.address))), None) if i_bg else None
    r['bg_ins'], r['pt_ins'] = (f'{i_bg.mnemonic} {i_bg.op_str}' if i_bg else None), (f'{i_pt.mnemonic} {i_pt.op_str}' if i_pt else None)
    r['same_ins'] = norm(i_bg) == norm(i_pt) and (i_bg.address - key) == (i_pt.address - best)
    if kind == 'B':
        r['pt_target'] = hex(best + 4 + PT.i32(best))
        bt = int(r['bg_target'], 16)
        if BG.tva <= bt < BG.tva + BG.tsize:
            # code target: also vote the callee directly
            _, tv = vote(bt)
            r['tvotes'] = [(hex(a), c) for a, c in tv]
            r['tconf'] = confof(tv)
            if tv:
                r['target_agrees'] = tv[0][0] == int(r['pt_target'], 16)
                p, d = unique_pat(tv[0][0], 'A')
                if p:
                    r['new_direct'] = {'Pattern': p, 'Operations': f'ADD {d}' if d else ''}
    r['pt_final'] = r.get('pt_target') or (hex(best) if kind == 'A' else None)
    if kind == 'C':
        r['bg_val'], r['pt_val'] = hex(BG.i32(key)), hex(PT.i32(best))
    # new pattern: anchored at the instruction start for B/C, at key for A
    anchor = i_pt.address if (kind in 'BC' and i_pt) else best
    p, d = unique_pat(anchor, kind)
    if p:
        add = (best - anchor) + d
        if kind == 'A':
            nops = f'ADD {add}' if add else ''
        elif kind == 'B':
            nops = f'ADD {add}, PUSH, READ DWORD, ADD, ADD 4'
        else:
            nops = re.sub(r'^ADD -?\d+', f'ADD {add}', ops)
        r['new'] = {'Pattern': p, 'Operations': nops}
        # self-check: new pattern resolves to the same address in Torment
        hh = PT.find(p)
        r['selfcheck'] = len(hh) == 1 and hh[0] == anchor - d
    r['status'] = 'voted'
    return r


def confof(v):
    if not v:
        return 'none'
    c = v[0][1]; second = v[1][1] if len(v) > 1 else 0
    return 'strong' if c >= 12 and c >= 3 * second else ('ok' if c >= 6 and c >= 2 * second else 'weak')


def pinit():
    init()


UPE = parse_db(UP_DB)
PTDB = parse_db(PT_DB)
# map upstream section name -> name in Torment db (ExeSwitch entries)
PTNAME = {}
for n, kv in list(UPE.items()):
    if kv.get('ExeSwitch') == '1':
        UPE[n] = UPE.get('!ExeSwitch-Baldur.exe-' + n, {})
        PTNAME[n] = '!ExeSwitch-Torment.exe-' + n
    else:
        PTNAME[n] = n

if __name__ == '__main__':
    names = [n for n in UPE if not n.startswith('!')]
    if len(sys.argv) > 1 and sys.argv[1] != '-all':
        names = [n for n in names if re.search(sys.argv[1], n)]
    with mp.Pool(8, pinit) as pool:
        res = pool.map(work, names, chunksize=4)
    json.dump({r['name']: r for r in res}, open('port2.json', 'w'), indent=1)
    print(collections.Counter((r.get('status'), r.get('conf')) for r in res))
