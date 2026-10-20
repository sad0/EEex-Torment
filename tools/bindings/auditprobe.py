# Probe every unproven field EEex.dll uses (audit.json) in game structs; classify against the solved
# layout: confirmed / conflict / nosites. Output: auditprobe.json. Run from tools/.
import sys, os, json, collections, io, contextlib
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import bindings.fieldprobe as FP

A = json.load(open('bindings/audit.json'))
skip_prefix = ('SDL_', 'stbrp', 'd3d', 'vertex', 'DP_', '_')
out = {}
for s, n, how, bg, pt, uses, bgsize in A['unproven']:
    if s.startswith(skip_prefix) or not s[:1].isupper() and s not in ('uiItem', 'uiMenu', 'slicedRect', 'font_t'):
        continue
    with contextlib.redirect_stdout(io.StringIO()):
        v = FP.probe(s, n, verbose=False)
    if not v:
        st = 'nosites'; top = None
    else:
        top, c = v.most_common(1)[0]
        st = 'confirmed' if top == pt else 'conflict'
    out[f'{s}.{n}'] = {'status': st, 'how': how, 'bg': hex(bg), 'pt': pt if pt is None else hex(pt),
                       'votes': [(hex(a), c) for a, c in (v.most_common(3) if v else [])]}
    print(f'{st:9} {s}.{n:32} how={how} bg={bg:#x} pt={pt if pt is None else hex(pt)} votes={out[f"{s}.{n}"]["votes"]}')
json.dump(out, open('bindings/auditprobe.json', 'w'), indent=1)
print(collections.Counter(v['status'] for v in out.values()))
