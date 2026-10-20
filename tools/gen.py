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


FMR = json.load(open('fmap_ratio.json')) if os.path.exists('fmap_ratio.json') else {}


def fn_conflict(n, site):
    """PT function expected from fmap for the BG function holding the key, if site is elsewhere."""
    bk = BG_KEY.get(n)
    if bk is None:
        return None
    bp = BGPE.rfunc(bk); bp = bp[0] if bp else BGPE.fstart(bk)
    if bp not in FM or bp == bk or FMR.get(hex(bp), 1) < 0.5:
        return None
    pp = PT.rfunc(site); pp = pp[0] if pp else PT.fstart(site)
    return hex(FM[bp]) if pp != FM[bp] else None


def data_sites(n, t):
    """PT .text sites whose RIP-relative disp32 targets t with the instruction tail upstream ops expect."""
    import numpy as np
    ops = upentry(n).get('Operations', '')
    m = re.search(r'READ DWORD, ADD, ADD (\d+)((?:, ADD -?\d+)*)$', ops)
    tail = int(m.group(1)) if m else 4
    extra = sum(int(x) for x in re.findall(r', ADD (-?\d+)', m.group(2))) if m else 0
    a = np.frombuffer(PT.text, dtype=np.uint8).astype(np.int64)
    x = a[:-3] | (a[1:-2] << 8) | (a[2:-1] << 16) | (a[3:] << 24)
    x = np.where(x >= 2**31, x - 2**32, x)
    pos = np.arange(len(x)) + PT.tva
    out = []
    for p in pos[(pos + tail + x) == t - extra][:16]:
        if field_at(PT, int(p)):
            out.append(int(p))
    return out


def local_ok(l):
    """Confidence for a local.py result, or None if not acceptable."""
    if not l or 'addr' not in l:
        return None
    how = l['how']
    fm = 'high' if how.startswith('fmap') and False else 'medium'
    if 'call-anchor(unique)' in how or 'call-anchor(ordinal' in how:
        return 'medium'
    if how.startswith('anchor2'):
        return 'medium'
    if 'call-anchor(ctx' in how:
        return 'low'
    if l.get('ratio') is None:  # function start mapped through fmap / callers
        return 'medium'
    if isinstance(l.get('ratio'), float) and l['ratio'] >= 0.7 and l['ratio'] - l.get('second', 0) >= 0.15:
        return 'low'
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
    L = json.load(open('local.json')) if os.path.exists('local.json') else {}
    GX = json.load(open('gxref.json')) if os.path.exists('gxref.json') else {}
    DB = parse_db(PT_DB)
    changes, report = {}, {}
    for n, v in X.items():
        src = M.get(n)
        rep = {'kind': v.get('kind')}
        if src and src.get('unsupported'):
            changes[ptname(n)] = {'Unsupported': '1'}
            rep.update(status='unsupported', method='manual', conf='-', note=src.get('note', ''))
            report[n] = rep; continue
        cands = []
        if src and src.get('data_target'):
            for site in data_sites(n, int(src['data_target'], 16)):
                cands.append((site, 'manual: ' + src.get('method', 'ghidra'), src.get('conf', 'medium'), src.get('note', ''), 'site'))
        if src and src.get('addr'):
            cands.append((int(src['addr'], 16), 'manual: ' + src.get('method', 'ghidra'), src.get('conf', 'medium'), src.get('note', ''), True))
        if not src:
            gx = GX.get(n)
            if gx and gx.get('votes') and gx.get('sites'):
                t, c = gx['votes'][0]; tot = sum(x[1] for x in gx['votes'])
                if c >= 3 and c >= 0.8 * tot:  # strong global-reference vote outranks local evidence
                    for site in gx['sites']:
                        cands.append((int(site, 16), f'gxref({c}/{gx["refs"]})', 'high' if c >= 10 else 'medium', '', 'site'))
            if v['result'] == 'ok':
                cands.append((int(v['addr'], 16), '+'.join(sorted(set(w.split('(')[0] for w in v['methods']))), v['conf'], '', False))
            if local_ok(L.get(n)):
                l = L[n]; cands.append((int(l['addr'], 16), 'local: ' + l['how'], local_ok(l), '', False))
        kind = v.get('kind') or classify(upentry(n).get('Operations', ''))[0]
        last = v.get('why') or v.get('align_note') or ''
        done = False
        for key, method, conf, note, forced in cands:
            delta = 0
            if forced == 'site':
                fa = field_at(PT, key)
                if not fa:
                    continue
                delta = fa[0][0]
            elif kind in 'BC':
                fs = field_site(n, key)
                if fs is None:
                    last = f'{method}: no matching rel32/imm field near {hex(key)}'; continue
                key, delta = fs
            e = make(n, key, delta)
            if not e:
                last = f'{method}: no unique pattern'; continue
            fin = final_of(e)
            bgfin = bg_final(n)
            why = None
            if bgfin is not None and sec_of(BGPE, bgfin) != sec_of(PT, fin):
                why = f'section mismatch BG {sec_of(BGPE, bgfin)} vs PT {sec_of(PT, fin)}'
            elif forced == 'site' and int((src or {}).get('data_target') or GX[n]['votes'][0][0], 16) != fin:
                why = f'gxref site resolves {hex(fin)}'
            elif not forced and bgfin is not None and bgfin != BG_KEY.get(n) and bgfin in FM and FM[bgfin] != fin:
                why = f'fmap says callee {hex(FM[bgfin])}'
            elif forced is not True and forced != 'site' and fn_conflict(n, key):
                why = f'site {hex(key)} outside mapped PT function {fn_conflict(n, key)}'
            if why:
                last = f'{method}: {why}'; continue
            cur = resolve_cur(n)
            rep.update(status='ported', method=method, conf=conf, note=note, addr=hex(fin), site=hex(key))
            if cur == fin:
                rep['method'] += ' (db pattern kept)'
            else:
                if cur is not None:
                    rep['replaced'] = hex(cur)
                changes[ptname(n)] = e
            done = True
            break
        if not done:
            rep.update(status='unresolved', method='-', conf='-', note=last)
            if 'outside mapped PT function' in last:
                rep['fnconflict'] = True
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
