# Layout coverage report for every struct emitted in the Torment header.
# Field classes:
#   proven   - hand-verified (manual_fields.json) or direct code evidence from >= 2 aligned functions
#              (evidence from a single function is only a candidate: it becomes 'span' when it fits a
#              closed span, e.g. CGameArea.INIFile was misplaced by one mispaired access)
#   span     - placed between two proven neighbours (or struct start / proven size) whose PT gap equals
#              the BG gap, all items in between keeping the BG relative layout: no room for a change
#   unproven - anything else (placed by interpolation / adjacency / BG assumption without a closed span)
#   absent   - not placed (opaque padding in the header)
# Output: coverage.json + summary; -v lists unproven fields of the given structs.
import os, sys, json, collections
HERE = os.path.dirname(os.path.abspath(__file__))
L = json.load(open(os.path.join(HERE, 'ptlayout.json')))
R = json.load(open(os.path.join(HERE, 'ptheader_report.json')))
M = json.load(open(os.path.join(HERE, 'manual_fields.json')))
emitted = [r[0] for r in R['rewritten']] + [r[0] if isinstance(r, list) else r for r in R.get('kept', [])]
PROVEN = {'evidence', 'manual'}


def nfun(s, i):
    # distinct aligned functions behind the evidence (ptlayout.py, from field_evidence_funcs.json)
    return i.get('nfun') or 0


def classify(s):
    lay = L[s]
    items = sorted(((n, i) for n, i in lay['items'].items()), key=lambda x: x[1]['bg'])
    out = {}
    anchors = [(-1, 0, 0)]  # (index, bg, pt) of proven boundaries; struct start counts as one
    for k, (n, i) in enumerate(items):
        if i['pt'] is None:
            out[n] = 'absent'
        elif i['how'] == 'manual' or (i['how'] == 'evidence' and nfun(s, i) >= 2):
            out[n] = 'proven'
    # closed spans: between consecutive proven items (or start / proven end)
    proven_idx = [k for k, (n, i) in enumerate(items) if out.get(n) == 'proven']
    size_proven = s in M.get('sizes', {}) or s in M.get('same_as_bg', {})
    bounds = [(-1, 0, 0)] + [(k, items[k][1]['bg'], items[k][1]['pt']) for k in proven_idx]
    if size_proven and lay['pt_size'] is not None:
        bounds.append((len(items), lay['bg_size'], lay['pt_size']))
    for (k0, b0, p0), (k1, b1, p1) in zip(bounds, bounds[1:]):
        mid = items[k0 + 1:k1]
        if not mid:
            continue
        if b1 - b0 != p1 - p0:
            continue
        if all(i['pt'] is not None and i['pt'] - p0 == i['bg'] - b0 for _, i in mid):
            for n, _ in mid:
                out.setdefault(n, 'span')
    # single-function evidence: accepted when its BG->PT delta equals the delta of the nearest strongly
    # proven item on either side (struct start counts as delta 0)
    strong = [(-1, 0)] + [(k, items[k][1]['pt'] - items[k][1]['bg']) for k in proven_idx]
    for k, (n, i) in enumerate(items):
        if n in out or i['how'] != 'evidence' or i['pt'] is None:
            continue
        d = i['pt'] - i['bg']
        before = [x for x in strong if x[0] < k]
        after = [x for x in strong if x[0] > k]
        if (before and before[-1][1] == d) or (after and after[0][1] == d):
            out[n] = 'span'
    for n, i in items:
        out.setdefault(n, 'unproven')
    return out


report = {}
tot = collections.Counter()
# every solved struct (not only last run's emitted ones: a struct made opaque once would never come back)
for s in sorted(set(emitted) | set(L)):
    if s not in L:
        continue
    c = classify(s)
    report[s] = c
    tot.update(c.values())
json.dump(report, open(os.path.join(HERE, 'coverage.json'), 'w'), indent=0)
print('fields:', dict(tot), 'structs', len(report))
worst = sorted(report, key=lambda s: -sum(1 for v in report[s].values() if v == 'unproven'))
print('most unproven:', [(s, sum(1 for v in report[s].values() if v == 'unproven')) for s in worst[:40]])
if '-v' in sys.argv:
    for s in sys.argv[sys.argv.index('-v') + 1:]:
        for n, v in report.get(s, {}).items():
            if v in ('unproven', 'absent'):
                i = L[s]['items'][n]
                print(f'  {s}.{n} {v} bg={i["bg"]:#x} pt={i["pt"] if i["pt"] is None else hex(i["pt"])} how={i["how"]}')
