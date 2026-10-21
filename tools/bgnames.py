# Map EEex's BG2EE v2.6.6.0 symbol table (EEex/loader/v2.6.6.0/bg2ee/function_names.db, from a
# slightly different build) onto our Baldur_bg2ee.exe, then onto Torment.exe through fmap.json.
# Anchors: DB entries whose BG resolution is a function start (name known on both sides) give the
# local address delta; every symbol is moved by the interpolated delta and snapped to a .pdata
# function start (exact delta matches only). Output: bgnames.json {bg_rva: name}, ptnames.json {pt_rva: name}
import json, bisect, re, collections
from ilib import *

BG = PE(BG_EXE)
SYM = REPO + r'\ref\EEex\EEex\loader\v2.6.6.0\bg2ee\function_names.db'
syms = []
for line in open(SYM, encoding='utf-8', errors='ignore'):
    p = line.rstrip('\r\n').split('\t')
    if len(p) == 2 and p[0].startswith('0x'):
        syms.append((int(p[0], 16) - 0x140000000, p[1]))
syms.sort()
byname = collections.defaultdict(list)
for a, n in syms:
    byname[n].append(a)

# anchors: our resolved BG function starts for DB entries named like symbols
R = json.load(open('port2.json'))
anchors = []
for n, r in R.items():
    if 'bg_key' not in r:
        continue
    base = re.sub(r'\(.*$', '', n)
    if base in byname and len(byname[base]) == 1:
        k = int(r['bg_key'], 16)
        if BG.fstart(k) == k:
            anchors.append((byname[base][0], k - byname[base][0]))
anchors.sort()
print('anchors', len(anchors))
aa = [a for a, d in anchors]

starts = set(b for b, e, u in BG.rf)


def delta_near(a):
    i = bisect.bisect_left(aa, a)
    cands = [anchors[j][1] for j in range(max(0, i - 2), min(len(anchors), i + 2))]
    return cands


out = {}
for a, n in syms:
    for d in delta_near(a):
        if a + d in starts:
            out[a + d] = n; break
print('mapped', len(out), 'of', len(syms))
json.dump({hex(k): v for k, v in out.items()}, open('bgnames_raw.json', 'w'), indent=0)
F = {int(k, 16): int(v[0], 16) for k, v in json.load(open('fmap.json')).items()}
pt = {hex(F[a]): n for a, n in out.items() if a in F}
json.dump(pt, open('ptnames.json', 'w'), indent=0)
print('PT names', len(pt))
for n in ('CRes::Demand', 'CResFont::GetFont', 'CChitin::OnResizeWindow', 'CInfinity::SetScrollDest', 'CGameSprite::GetKitMask'):
    print(n, [hex(k) for k, v in out.items() if v == n], [k for k, v in pt.items() if v == n])
