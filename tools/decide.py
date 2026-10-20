# Pick the Torment address for each entry among vote candidates and the current DB resolution,
# scoring normalized instruction context (BG2 vs Torment). Output: decide.json.
import json, re, difflib, collections
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from ilib import *

md = Cs(CS_ARCH_X86, CS_MODE_64)
BG, PT = PE(BG_EXE), PE(PT_EXE)


def norm(i):
    return f"{i.mnemonic} {re.sub(r'0x[0-9a-f]+', 'N', i.op_str)}"


def fwd(pe, a, n=12):
    return [norm(i) for i in list(md.disasm(pe.tbytes(a, 120), a))[:n]]


def bwd(pe, a, n=6):
    fs = pe.fstart(a)
    if fs >= a or a - fs > 4000:
        return []
    ins = list(md.disasm(pe.tbytes(fs, a - fs), fs))
    if not ins or ins[-1].address + ins[-1].size != a:
        return []  # desync: no clean boundary
    return [norm(i) for i in ins[-n:]]


def ratio(x, y):
    return difflib.SequenceMatcher(None, x, y).ratio() if x and y else 0.0


def score(bg_ins, pt_ins):
    f = ratio(fwd(BG, bg_ins), fwd(PT, pt_ins))
    b1, b2 = bwd(BG, bg_ins), bwd(PT, pt_ins)
    if bg_ins == BG.fstart(bg_ins) or not b1 or not b2:
        return f, f, None
    b = ratio(b1, b2)
    return 0.7 * f + 0.3 * b, f, b


def ins_start(pe, key, delta):
    return key - delta


PTDB = parse_db(PT_DB)
PTNAME = {}
for _n, _kv in parse_db(UP_DB).items():
    PTNAME[_n] = '!ExeSwitch-Torment.exe-' + _n if _kv.get('ExeSwitch') == '1' else _n


def main():
    R = json.load(open('port2.json'))
    out = {}
    for n, r in R.items():
        if r.get('status') != 'voted':
            out[n] = {'decision': 'manual', 'why': r.get('status')}
            continue
        bgk = int(r['bg_key'], 16)
        # BG instruction start containing key
        fs = BG.fstart(bgk)
        bi = next((i for i in md.disasm(BG.tbytes(fs, bgk - fs + 16), fs) if i.address <= bgk < i.address + i.size), None)
        delta = bgk - bi.address if bi else 0
        cands = collections.OrderedDict()
        for a, c in r['votes']:
            cands[int(a, 16)] = c
        cur = None
        e = PTDB.get(PTNAME.get(n, n), {})
        if e.get('Pattern'):
            h = PT.find(e['Pattern'])
            kind, k = classify(e.get('Operations', ''))
            if h and kind in 'ABC':
                cur = h[0] + k  # key: final address for A, field site for B/C
        if cur is not None:
            cands.setdefault(cur, 0)
        scored = []
        for a, c in cands.items():
            s, f, b = score(bi.address, a - delta)
            scored.append((round(s, 3), c, a, round(f, 2), b if b is None else round(b, 2)))
        scored.sort(key=lambda x: (-x[0], -x[1]))
        best = scored[0]
        top_votes = r['votes'][0][1]
        d = {'scored': [(hex(a), s, c, f, b) for s, c, a, f, b in scored], 'addr': hex(best[2]),
             'cur': hex(cur) if cur is not None else None, 'conf_vote': r['conf']}
        s = best[0]
        top = best[1] == top_votes
        if best[2] == cur and (s >= 0.8 or (top and r['conf'] != 'weak')):
            d['decision'] = 'confirmed'
        elif top and r['conf'] != 'weak' and s >= 0.7:
            d['decision'] = 'ported'
        elif s >= 0.6:
            d['decision'] = 'probable'
        else:
            d['decision'] = 'manual'
        out[n] = d
    json.dump(out, open('decide.json', 'w'), indent=1)
    print(collections.Counter(v['decision'] for v in out.values()))


if __name__ == '__main__':
    main()
