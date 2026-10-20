# Iterate autoprove over every struct with unproven fields (BG disp >= 0x100) until no new proof.
import sys, os, json, subprocess
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, 'bindings')
import autoprove as A
D = A.bg_disps()
for rnd in range(6):
    subprocess.run([sys.executable, 'bindings/ptlayout.py'], capture_output=True)
    subprocess.run([sys.executable, 'bindings/ptheader.py'], capture_output=True)
    subprocess.run([sys.executable, 'bindings/coverage.py'], capture_output=True)
    Lall = json.load(open('bindings/ptlayout.json')); Call = json.load(open('bindings/coverage.json'))
    d = json.load(open('bindings/manual_fields.json'))
    new = 0
    for S, C in Call.items():
        if not any(v in ('unproven', 'absent') for n, v in C.items() if Lall[S]['items'][n]['bg'] >= 0x100):
            continue
        V, nf = A.validated_votes(D, S, Lall[S]['items'], C, 0x100)
        m = d['fields'].setdefault(S, {})
        for n, v in V.items():
            if len(v) == 1 and n not in m:
                m[n] = {'pt': hex(v.most_common(1)[0][0]), 'why': 'autoprove: unanimous votes from aligned functions whose accesses to proven fields of this struct all match (bindings/autoprove.py)'}
                new += 1
                print(rnd, S, n, hex(v.most_common(1)[0][0]), dict(v), flush=True)
    json.dump(d, open('bindings/manual_fields.json', 'w'), indent=1)
    print('round', rnd, 'new', new, flush=True)
    if not new:
        break
