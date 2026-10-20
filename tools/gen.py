# Write resolved Torment patterns into poc/InfinityLoader.db.
# Sources: final.json (automatic), manual.json (hand-resolved: {name: {"addr": "0x..", "note": ..}
# or {"unsupported": true, "note": ..}}). Entries whose current DB pattern already resolves to the
# chosen address are left untouched. Writes gen_report.json for PATTERNS.md.
import json, re, sys, os
from ilib import *
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

md = Cs(CS_ARCH_X86, CS_MODE_64)
PT = PE(PT_EXE)
UP = parse_db(UP_DB)


def ptname(n):
    return '!ExeSwitch-Torment.exe-' + n if UP.get(n, {}).get('ExeSwitch') == '1' else n


def upentry(n):
    return UP.get('!ExeSwitch-Baldur.exe-' + n) if UP.get(n, {}).get('ExeSwitch') == '1' else UP.get(n, {})


def unique_at(a, maxlen=48):
    """Unique pattern starting at a, or preceding a (returns pattern, start)."""
    for L in range(6, maxlen):
        b = PT.tbytes(a, L)
        if PT.count(b) == 1:
            return b.hex().upper(), a
    for d in range(1, 96):
        for L in range(6, 40):
            b = PT.tbytes(a - d, L)
            if PT.count(b) == 1 and PT.text.find(b) == a - d - PT.tva:
                return b.hex().upper(), a - d
    return None, None


mdd = Cs(CS_ARCH_X86, CS_MODE_64); mdd.detail = True


def field_at(pe, key):
    """Instructions (start, insn) whose 32-bit disp or imm field starts exactly at key."""
    out = []
    for d in range(1, 12):
        i = next(iter(mdd.disasm(pe.tbytes(key - d, 16), key - d)), None)
        if not i:
            continue
        e = i.encoding
        if (e.disp_size == 4 and e.disp_offset == d) or (e.imm_size == 4 and e.imm_offset == d):
            out.append((d, i))
    return out


def field_site(n, key):
    """Snap a B/C key to the nearest PT field whose instruction mnemonic matches BG's."""
    bk = BG_KEY.get(n)
    bi = field_at(BGPE, bk) if bk is not None else []
    want = bi[0][1].mnemonic if bi else None
    for dk in sorted(range(-10, 11), key=abs):
        for d, i in field_at(PT, key + dk):
            if want is None or i.mnemonic == want:
                return key + dk, d
    return None


def make(n, key, delta):
    """Build Pattern/Operations for entry n whose key (A: final addr, B/C: field site) is key."""
    up = upentry(n); ops = up.get('Operations', '')
    kind, k = classify(ops)
    anchor = key - delta
    p, start = unique_at(anchor)
    if not p:
        return None
    off = key - start
    if kind == 'A':
        nops = f'ADD {off}' if off else ''
    elif kind in 'BC':
        nops = re.sub(r'^ADD -?\d+', f'ADD {off}', ops)
    else:
        nops = re.sub(r'^ADD -?\d+', f'ADD {off}', ops)
    # verify
    h = PT.find(p)
    assert h and h[0] == start, n
    return {'Pattern': p, 'Operations': nops}


BGPE = PE(BG_EXE)
FM = {int(k, 16): int(v[0], 16) for k, v in json.load(open('fmap.json')).items()}
FMM = {int(k, 16): v[1] for k, v in json.load(open('fmap.json')).items()}
BG_KEY = {n: int(r['bg_key'], 16) for n, r in json.load(open('port2.json')).items() if 'bg_key' in r}


def sec_of(pe, rva):
    for nm, va, vs, ra, rs in pe.secs:
        if va <= rva < va + max(vs, rs):
            return nm
    return None


def bg_final(n):
    e = upentry(n)
    if not e.get('Pattern'):
        return None
    h = BGPE.find(e['Pattern'])
    if not h:
        return None
    try:
        return eval_ops(BGPE, h[0], e.get('Operations', ''))
    except Exception:
        return None


def final_of(e):
    """Final value an entry resolves to in Torment (first match + Operations), or None."""
    if not e or not e.get('Pattern') or e.get('Unsupported') == '1':
        return None
    h = PT.find(e['Pattern'])
    if not h:
        return None
    try:
        return eval_ops(PT, h[0], e.get('Operations', ''))
    except Exception:
        return None


def resolve_cur(n):
    return final_of(DB.get(ptname(n), {}))


def write_db(changes):
    txt = open(PT_DB, encoding='utf-8').read()
    for name, kv in changes.items():
        blk = re.compile(r'(^\[' + re.escape(name) + r'\]\s*\n)((?:(?!\[)[^\n]*\n?)*)', re.M)
        body = ''.join(f'{k}={v}\n' for k, v in kv.items() if v != '')
        m = blk.search(txt)
        if m:
            old = m.group(2)
            # keep non-pattern keys (ExeSwitch, Type, ...) but drop old Pattern/Operations/Unsupported/Cached*
            keep = ''.join(l + '\n' for l in old.splitlines() if l and not re.match(r'(Pattern|Operations|Unsupported|CachedAddress)=', l))
            txt = txt[:m.start(2)] + body + keep + '\n' + txt[m.end(2):]
        else:
            txt = txt.rstrip('\n') + f'\n\n[{name}]\n{body}'
    open(PT_DB, 'w', encoding='utf-8', newline='').write(txt)


if __name__ == '__main__':
    X = json.load(open('final.json'))
    M = json.load(open('manual.json')) if os.path.exists('manual.json') else {}
    DB = parse_db(PT_DB)
    changes, report = {}, {}
    for n, v in X.items():
        src = M.get(n)
        rep = {'kind': v.get('kind')}
        if src and src.get('unsupported'):
            changes[ptname(n)] = {'Unsupported': '1'}
            rep.update(status='unsupported', method='manual', conf='-', note=src.get('note', ''))
            report[n] = rep; continue
        if src:
            key = int(src['addr'], 16); method = 'manual: ' + src.get('method', 'ghidra'); conf = src.get('conf', 'medium')
            note = src.get('note', '')
        elif v['result'] == 'ok':
            key = int(v['addr'], 16); method = '+'.join(sorted(set(w.split('(')[0] for w in v['methods']))); conf = v['conf']; note = ''
        else:
            rep.update(status='unresolved', method='-', conf='-', note=v.get('why') or v.get('align_note') or '')
            report[n] = rep; continue
        delta = 0
        kind = v.get('kind') or classify(upentry(n).get('Operations', ''))[0]
        if kind in 'BC':
            fs = field_site(n, key)
            if fs is None:
                rep.update(status='unresolved', method=method, conf=conf, note='no matching rel32/imm field near key', addr=hex(key)); report[n] = rep; continue
            key, delta = fs
        e = make(n, key, delta)
        if not e:
            rep.update(status='unresolved', method=method, conf=conf, note='no unique pattern'); report[n] = rep; continue
        fin = final_of(e)
        cur = resolve_cur(n)
        # sanity: final value must live in the same kind of section as in BG, and agree with fmap
        bgfin = bg_final(n)
        why = None
        if bgfin is not None and sec_of(BGPE, bgfin) != sec_of(PT, fin):
            why = f'section mismatch BG {sec_of(BGPE, bgfin)} vs PT {sec_of(PT, fin)}'
        elif bgfin is not None and bgfin != BG_KEY.get(n) and bgfin in FM and FM[bgfin] != fin and not src:
            why = f'fmap says callee {hex(FM[bgfin])}'
        if why:
            rep.update(status='unresolved', method=method, conf=conf, note=why, addr=hex(fin)); report[n] = rep; continue
        rep.update(status='ported', method=method, conf=conf, note=note, addr=hex(fin))
        if cur == fin:
            rep['method'] += ' (db pattern kept)'
        else:
            if cur is not None:
                rep['replaced'] = hex(cur)
            changes[ptname(n)] = e
        report[n] = rep
    # post-pass: unresolved rel32 entries whose BG target is a mapped function -> direct pattern
    for n, rep in report.items():
        if rep['status'] != 'unresolved' or (M.get(n) or {}).get('unsupported'):
            continue
        bgfin = bg_final(n)
        tgt = None
        if M.get(n, {}).get('target'):
            tgt = int(M[n]['target'], 16); how = 'manual target'
        elif bgfin is not None and sec_of(BGPE, bgfin) == '.text' and bgfin in FM and classify(upentry(n).get('Operations', ''))[0] == 'B':
            tgt = FM[bgfin]; how = 'fmap(callee) ' + FMM.get(bgfin, '')
        if tgt is None:
            continue
        p, start = unique_at(tgt)
        if not p:
            continue
        e = {'Pattern': p, 'Operations': f'ADD {tgt - start}' if tgt != start else ''}
        cur = resolve_cur(n)
        rep.update(status='ported', method=how, conf=M.get(n, {}).get('conf', 'high' if 'sig' in how or 'prop' in how else 'medium'),
                   note=(rep.get('note') or '') + ' -> direct callee pattern', addr=hex(tgt))
        if cur != tgt:
            changes[ptname(n)] = e
            if cur is not None: rep['replaced'] = hex(cur)
    if '-n' not in sys.argv:
        write_db(changes)
    json.dump(report, open('gen_report.json', 'w'), indent=1)
    import collections
    print(len(changes), 'changes', collections.Counter(r['status'] for r in report.values()))
