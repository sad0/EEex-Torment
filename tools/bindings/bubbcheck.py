# Cross-check our Torment layouts against the named fields of Bubb's 2022 LuaBindings-PSTEE header
# (ref/InfinityLoader/LuaBindings-PSTEE/scripts/generate_bindings/in/engine_structs.h, older exe).
# Offsets of named fields are inferred from the surrounding `nobinding undefined _0xNNN` markers.
import os, re, json
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, r'..\..\ref\InfinityLoader\LuaBindings-PSTEE\scripts\generate_bindings\in\engine_structs.h')
L = json.load(open(os.path.join(HERE, 'ptlayout.json')))
C = json.load(open(os.path.join(HERE, 'coverage.json')))
txt = open(SRC, encoding='utf-8', errors='ignore').read()
res = {'agree': [], 'differ': [], 'unknown': []}
for m in re.finditer(r'^struct (\w+)[^\n]*\n\{\n(.*?)^\};', txt, re.M | re.S):
    s, body = m.group(1), m.group(2)
    prev = None  # offset just after the last undefined byte
    for line in body.split('\n'):
        u = re.search(r'nobinding (?:undefined|byte) _0x([0-9A-Fa-f]+);', line)
        if u:
            prev = int(u.group(1), 16) + 1
            continue
        f = re.search(r'(\w+)(\[\d+\])?;\s*$', line.strip())
        if not f or prev is None:
            continue
        name = f.group(1)
        off = prev
        it = L.get(s, {}).get('items', {}).get(name)
        if it is None:
            res['unknown'].append((s, name, hex(off)))
        elif it['pt'] == off:
            res['agree'].append((s, name, hex(off), C.get(s, {}).get(name)))
        else:
            res['differ'].append((s, name, 'bubb', hex(off), 'ours', it['pt'] if it['pt'] is None else hex(it['pt']), C.get(s, {}).get(name)))
        prev = None
for k, v in res.items():
    print(k, len(v))
for x in res['differ']:
    print('  differ', x)
