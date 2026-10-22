# Torment function_names.db for EEex's profiler (EEex_scripts/profiler/function_names.db: "0x<VA>\t<name>").
# EEex ships the file for its BG2EE v2.6.6.0 build, whose code is shifted against our reference BG2EE exe.
#  1. Anchors: names present in both EEex's file and bgnames.json -> delta = our rva - their rva.
#  2. The delta is piecewise constant along the code: an anchor is kept only when its delta equals the
#     delta of its previous and next anchors (isolated deltas are wrong names on one side).
#  3. Every name of EEex's file lying between two kept anchors with the same delta gets that delta, and
#     must land on a function start (.pdata) of our exe.
#  4. bgnames_merge.py merges these names into bgnames.json; BG -> PT through fmap.json; Torment-only
#     names from port_extra.py's PSTEE- labels.
# Output: poc/profiler/function_names.db, report on stdout.
import os, json, bisect
from ilib import *
from fmap import BG, PT, callers

SRC = os.path.join(REPO, r'ref\EEex\EEex\loader\v2.6.6.0\bg2ee\function_names.db')
OUT = os.path.join(REPO, r'poc\profiler\function_names.db')
BASE = 0x140000000

theirs = []
for line in open(SRC, encoding='utf-8', errors='replace'):
    line = line.rstrip('\r\n')
    if '\t' in line:
        a, n = line.split('\t', 1)
        theirs.append((int(a, 16) - BASE, n))
theirs.sort()
BN = {int(k, 16): v for k, v in json.load(open('bgnames_raw.json')).items()}
ours = {}
for a, n in BN.items():
    ours.setdefault(n, []).append(a)
F = {int(k, 16): int(v[0], 16) for k, v in json.load(open('fmap.json')).items()}

# 1. anchors (unique names only)
cnt = {}
for a, n in theirs:
    cnt[n] = cnt.get(n, 0) + 1
anchors = [(a, n, ours[n][0] - a) for a, n in theirs if cnt[n] == 1 and len(ours.get(n, [])) == 1]
# 2. locally consistent anchors
kept = [anchors[i] for i in range(1, len(anchors) - 1)
        if anchors[i - 1][2] == anchors[i][2] == anchors[i + 1][2]]
print('EEex names', len(theirs), 'anchors', len(anchors), 'consistent', len(kept))
ka = [k[0] for k in kept]
starts = set(BG.rf_beg)
bg_named = {}
rej = {'no bracket': 0, 'delta break': 0, 'not a function start': 0}
for a, n in theirs:
    i = bisect.bisect_right(ka, a)
    if i == 0 or i >= len(kept):
        rej['no bracket'] += 1; continue
    lo, hi = kept[i - 1], kept[i]
    if lo[0] == a:
        d = lo[2]
    elif lo[2] != hi[2]:
        rej['delta break'] += 1; continue
    else:
        d = lo[2]
    r = a + d
    if r not in starts and not callers(BG, r) and BG.tbytes(r - 1, 1) != bytes([0xcc]):
        rej['not a function start'] += 1; continue
    bg_named[r] = n
print('BG names resolved', len(bg_named), 'rejected', rej)
# anchors that contradict their neighbours: bgnames entries to distrust
bad = [(hex(ours[n][0]), n) for a, n, d in anchors if n in ours and bg_named.get(ours[n][0]) not in (None, n)]
print('bgnames entries contradicted by EEex names', len(bad))
json.dump({hex(r): n for r, n in sorted(bg_named.items())}, open('bgnames_eeex.json', 'w'), indent=0)
json.dump([[a, n, bg_named.get(int(a, 16))] for a, n in bad], open('bgnames_contradicted.json', 'w'), indent=0)
# names of the merged table (bgnames_merge.py: strict names + uncontradicted bgnames.py names)
pt = {}
merged = {int(k, 16): v for k, v in json.load(open('bgnames.json')).items()} if os.path.exists('bgnames.json') else bg_named
for r, n in merged.items():
    if r in F:
        pt.setdefault(F[r], n)
# Torment-only engine functions bound by EEex-PSTEE (port_extra.py LABELS 'PSTEE-<name>': rva)
import re
for n, a in re.findall(r"'PSTEE-([\w:]+)': (0x[0-9a-f]+)", open('port_extra.py').read()):
    pt[int(a, 16)] = n
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', newline='\r\n') as f:
    for a in sorted(pt):
        f.write(f'0x{a + BASE:X}\t{pt[a]}\n')
print('Torment names', len(pt), '->', OUT)
