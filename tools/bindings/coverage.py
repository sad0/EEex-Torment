# Layout coverage report for every struct emitted in the Torment header.
# Field classes:
#   proven   - direct code evidence or hand-verified (manual_fields.json)
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


def classify(s):
    lay = L[s]
    items = sorted(((n, i) for n, i in lay['items'].items()), key=lambda x: x[1]['bg'])
    out = {}
    anchors = [(-1, 0, 0)]  # (index, bg, pt) of proven boundaries; struct start counts as one
    for k, (n, i) in enumerate(items):
        if i['pt'] is None:
            out[n] = 'absent'
        elif i['how'] in PROVEN:
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
    for n, i in items:
        out.setdefault(n, 'unproven')
    return out


report = {}
tot = collections.Counter()
for s in emitted:
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
