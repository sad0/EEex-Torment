# Audit: which unproven struct fields does EEex.dll (C++) use?
# Member names accessed in the compiled EEex.dll sources (->x / .x) are matched against fields of
# the solved PT layout whose placement is not 'evidence'/'manual'. Output: audit.json + summary.
import os, re, json, collections, sys
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
SRC = os.path.join(REPO, r'ref\InfinityLoader\EEex-Core-Shared-Files\source')
SKIP = {'uncap_fps.cpp', 'visibility_map.cpp', 'engine_reimplementations.cpp', 'debug.cpp'}
L = json.load(open(os.path.join(HERE, 'ptlayout.json')))

used = collections.Counter()
for f in os.listdir(SRC):
    if f.endswith('.cpp') and f not in SKIP:
        for m in re.finditer(r'(?:->|\.)\s*([A-Za-z_]\w*)\b(?!\s*\()', open(os.path.join(SRC, f), encoding='utf-8', errors='ignore').read()):
            used[m.group(1)] += 1

rows = []
for s, l in L.items():
    for n, it in l['items'].items():
        if n in used:
            rows.append((s, n, it['how'], it['bg'], it['pt'], used[n], l['bg_size']))
proven = [r for r in rows if r[2] in ('evidence', 'manual')]
unproven = [r for r in rows if r[2] not in ('evidence', 'manual')]
json.dump({'unproven': unproven, 'proven': proven}, open(os.path.join(HERE, 'audit.json'), 'w'), indent=0)
print(len(rows), 'field matches;', len(proven), 'proven;', len(unproven), 'unproven')
c = collections.Counter(r[0] for r in unproven)
print('unproven by struct:', c.most_common(40))
if '-v' in sys.argv:
    for r in sorted(unproven):
        print(f'  {r[0]}.{r[1]} how={r[2]} bg={r[3]:#x} pt={r[4] if r[4] is None else hex(r[4])} uses={r[5]}')
