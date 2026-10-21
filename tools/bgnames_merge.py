# bgnames.json = bgnames.py output (bgnames_raw.json) corrected by funcnames.py's stricter resolution
# (bgnames_eeex.json: EEex symbol kept only between two anchors of the same delta, three consecutive
# anchors agreeing). Strict names win where both exist (bgnames.py snapped some symbols onto the wrong
# function, e.g. 0x3c8e70 "Infinity_GetListHeight" is an INI getter); raw-only names are kept.
import json
raw = {int(k, 16): v for k, v in json.load(open('bgnames_raw.json')).items()}
strict = {int(k, 16): v for k, v in json.load(open('bgnames_eeex.json')).items()}
out = dict(raw)
fixed = [a for a in raw if a in strict and strict[a] != raw[a]]
out.update(strict)
# a name moved by the correction must not stay at its old (wrong) address
names = {}
for a, n in sorted(out.items()):
    names.setdefault(n, []).append(a)
for n, addrs in names.items():
    if len(addrs) > 1:
        for a in addrs:
            if a in raw and a not in strict and raw[a] == n:
                del out[a]
json.dump({hex(k): v for k, v in sorted(out.items())}, open('bgnames.json', 'w'), indent=0)
print('raw', len(raw), 'strict', len(strict), 'corrected', len(fixed), 'merged', len(out))
