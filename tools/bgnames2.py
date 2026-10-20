# Map EEex's BG2EE v2.6.6.0 symbol table (function_names.db, from a slightly different build) onto our
# Baldur_bg2ee.exe by sequence alignment. Both builds keep the link order, so between two trusted
# anchors (DB symbol <-> our function start, from the verified pattern DB) the DB symbols are matched
# monotonically to our function starts (.pdata starts + leaf starts after int3/ret padding) by dynamic
# programming: matching consecutive symbols costs |DB gap - our gap|, skipping one of our starts is
# cheap (cold fragments, unnamed thunks), skipping a DB symbol costs SKIP_DB.
# Output: bgnames.json {bg_rva: name}, ptnames.json {pt_rva: name} (through fmap.json).
import json, bisect, re, collections
from ilib import *

BG = PE(BG_EXE)
SYM = REPO + r'\ref\EEex\EEex\loader\v2.6.6.0\bg2ee\function_names.db'
SKIP_DB = 48
syms = []
for line in open(SYM, encoding='utf-8', errors='ignore'):
    p = line.rstrip('\r\n').split('\t')
    if len(p) == 2 and p[0].startswith('0x'):
        syms.append((int(p[0], 16) - 0x140000000, p[1]))
syms.sort()
byname = collections.defaultdict(list)
for a, n in syms:
    byname[n].append(a)

starts = set(b for b, e, u in BG.rf)
text = BG.text
for k in range(1, len(text) - 1):   # leaf functions without unwind data
    if text[k - 1] in (0xcc, 0xc3) and text[k] not in (0xcc, 0x00) and (text[k - 2] == 0xcc or text[k - 1] == 0xc3):
        pass  # candidates are added lazily below (too many to keep all)
cand = sorted(starts)

# anchors: upstream pattern-DB functions resolved on our BG exe whose name is a unique DB symbol
R = json.load(open('port2.json'))
anchors = []
for n, r in R.items():
    if 'bg_key' not in r:
        continue
    base = re.sub(r'\(.*$', '', n)
    if base in byname and len(byname[base]) == 1:
        k = int(r['bg_key'], 16)
        if BG.fstart(k) == k:
            anchors.append((byname[base][0], k))
anchors = sorted(set(anchors))
# keep a monotonic anchor chain
chain = []
for a, t in anchors:
    if not chain or (a > chain[-1][0] and t > chain[-1][1]):
        chain.append((a, t))
print('anchors', len(anchors), 'monotonic', len(chain))


def leaf_starts(lo, hi):
    out = []
    for t in range(max(lo, BG.tva + 2), min(hi, BG.tva + BG.tsize - 1)):
        k = t - BG.tva
        if text[k - 1] in (0xcc, 0xc3) and text[k] not in (0xcc, 0x00):
            out.append(t)
    return out


def align_segment(S, C):
    """S: [(db addr, name)], C: [our start] (both sorted; S[0]/C[0] and S[-1]/C[-1] are the anchors).
    Returns {our start: name}."""
    m, k = len(S), len(C)
    INF = float('inf')
    # dp[i][j]: min cost with S[i] matched to C[j]
    dp = [[INF] * k for _ in range(m)]
    back = [[None] * k for _ in range(m)]
    dp[0][0] = 0
    for i in range(1, m):
        for j in range(1, k):
            best, arg = INF, None
            # previous matched pair (pi, pj), skipping DB symbols pi+1..i-1 and our starts pj+1..j-1
            for pi in range(max(0, i - 4), i):
                for pj in range(max(0, j - 12), j):
                    c = dp[pi][pj]
                    if c == INF:
                        continue
                    c += abs((S[i][0] - S[pi][0]) - (C[j] - C[pj])) + SKIP_DB * (i - pi - 1)
                    if c < best:
                        best, arg = c, (pi, pj)
            dp[i][j], back[i][j] = best, arg
    out = {}
    i, j = m - 1, k - 1
    if dp[i][j] == INF:
        return out
    while back[i][j] is not None:
        out[C[j]] = S[i][1]
        i, j = back[i][j]
    out[C[0]] = S[0][1]
    return out


out = {}
bad_segments = 0
for (a0, t0), (a1, t1) in zip(chain, chain[1:]):
    S = [(a, n) for a, n in syms if a0 <= a <= a1]
    C = sorted(set([c for c in cand if t0 <= c <= t1] + leaf_starts(t0, t1)))
    if not S or not C or C[0] != t0 or C[-1] != t1 or len(S) > 400 or len(C) > 1500:
        bad_segments += 1
        continue
    seg = align_segment(S, C)
    if not seg:
        bad_segments += 1
    out.update(seg)
print('mapped', len(out), 'of', len(syms), 'segments skipped', bad_segments)
json.dump({hex(k): v for k, v in sorted(out.items())}, open('bgnames.json', 'w'), indent=0)
F = {int(k, 16): int(v[0], 16) for k, v in json.load(open('fmap.json')).items()}
pt = {hex(F[a]): n for a, n in out.items() if a in F}
json.dump(pt, open('ptnames.json', 'w'), indent=0)
print('PT names', len(pt))
for n in ('CRes::Demand', 'CResFont::GetFont', 'CChitin::OnResizeWindow', 'CInfGame::RemoveCharacterFromFamiliars', 'CInfGame::RemoveCharacterFromAllies'):
    print(n, [hex(k) for k, v in out.items() if v == n])
