# Engine members used by the EEex Lua that the Torment bindings do not expose: tolua registrations of the
# BG2EE v2.6.6.0 LuaBindings vs ours (bindings/generated/EEexLua_generated.cpp), per usertype, then every
# `.name` / `:name(` in the EEex Lua whose name some BG usertype exposes but its Torment counterpart does not
# (unproven fields are opaque padding in Torment, absent fields are gone).
#   python luafields.py   -> luafields.json + summary
import re, glob, json, os, collections
from ilib import REPO

BG_CPP = REPO + r'\ref\InfinityLoader\LuaBindings-v2.6.6.0\source\LuaBindings-v2.6.6.0\Generated\EEexLua_generated.cpp'
PT_CPP = REPO + r'\bindings\generated\EEexLua_generated.cpp'
LUA = REPO + r'\ref\EEex\EEex\copy'


def registrations(path):
    s = open(path, encoding='utf-8', errors='ignore').read()
    out = collections.defaultdict(set)
    stack = []
    for m in re.finditer(r'tolua_beginmodule\(L, "([^"]+)"\)|tolua_endmodule\(L\)|tolua_(?:variable|function|array|constant)\(L, "([^"]+)"', s):
        if m.group(1):
            stack.append(m.group(1))
        elif m.group(0).startswith('tolua_endmodule'):
            if stack:
                stack.pop()
        elif stack:
            out[stack[-1]].add(m.group(2))
    return out


if __name__ == '__main__':
    BGR, PTR = registrations(BG_CPP), registrations(PT_CPP)
    missing = collections.defaultdict(set)  # name -> BG types that have it but whose PT type lacks it
    for t, names in BGR.items():
        for n in names - PTR.get(t, set()):
            missing[n].add(t)
    pt_all = set().union(*PTR.values())
    uses = collections.defaultdict(list)
    for path in glob.glob(LUA + r'\**\*.lua', recursive=True):
        lines = open(path, encoding='utf-8', errors='ignore').read().split('\n')
        for k, line in enumerate(lines, 1):
            code = line.split('--', 1)[0]
            for m in re.finditer(r'[.:]([A-Za-z_][A-Za-z0-9_]*)', code):
                n = m.group(1)
                if n in missing:
                    uses[n].append(f'{os.path.basename(path)}:{k}')
    out = {n: {'bg_types': sorted(missing[n]), 'in_other_pt_types': n in pt_all, 'uses': v} for n, v in sorted(uses.items())}
    json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'luafields.json'), 'w'), indent=1)
    print('BG types', len(BGR), 'PT types', len(PTR), 'names missing somewhere', len(missing), 'used by EEex Lua', len(out))
    for n, e in out.items():
        print(f"{n:40} {'(also elsewhere)' if e['in_other_pt_types'] else '':16} {','.join(e['bg_types'])[:60]:60} {len(e['uses'])} {e['uses'][:3]}")
