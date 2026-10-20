# Per-function inventory of the EEex.dll sources compiled for Torment: engine calls, struct fields,
# numeric constants. Feeds the semantic audit (AUDIT.md). Output: audit_functions.json
import os, re, json
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC = [os.path.join(REPO, r'eeexdll\generated\src\EEex.cpp')] + [
    os.path.join(REPO, r'ref\InfinityLoader\EEex-Core-Shared-Files\source', f) for f in
    ('common.cpp', 'coordinate_util.cpp', 'font_util.cpp', 'lua_util.cpp', 'menu_util.cpp', 'profiler.cpp',
     'script_folder.cpp', 'util.cpp', 'main.cpp')]
HDR = open(os.path.join(REPO, r'eeexdll\generated\Baldur_generated.h'), encoding='utf-8', errors='ignore').read()
ENGINE_FN = set(re.findall(r'\b(?:p_)?([A-Za-z_]\w*)\s*\(', HDR))

FUNC_RE = re.compile(r'^(?!\s)(?:[\w:<>*&,\s]+?)\b((?:[A-Za-z_]\w*::)*[A-Za-z_~]\w*)\s*\(([^;{]*?)\)\s*(?:const\s*)?\{', re.M)


def bodies(text):
    for m in FUNC_RE.finditer(text):
        name = m.group(1)
        if name in ('if', 'for', 'while', 'switch', 'return'):
            continue
        i = m.end() - 1; depth = 0
        for j in range(i, len(text)):
            if text[j] == '{':
                depth += 1
            elif text[j] == '}':
                depth -= 1
                if depth == 0:
                    yield name, text[i:j + 1], text.count('\n', 0, m.start()) + 1
                    break


out = {}
for path in SRC:
    text = open(path, encoding='utf-8', errors='ignore').read()
    for name, body, line in bodies(text):
        code = re.sub(r'//[^\n]*|/\*.*?\*/', '', body, flags=re.S)
        code_nostr = re.sub(r'"(?:\\.|[^"\\])*"', '""', code)
        calls = sorted(set(m.group(1) for m in re.finditer(r'(?:->|\.|::)?\b([A-Za-z_]\w*)\s*\(', code_nostr)))
        fields = sorted(set(re.findall(r'(?:->|\.)\s*(m_\w+|\w+)\b(?!\s*\()', code_nostr)))
        nums = sorted(set(int(x, 0) for x in re.findall(r'(?<![\w.])(0x[0-9A-Fa-f]+|\d+)(?![\w.])', code_nostr) if int(x, 0) > 2))
        out[f'{os.path.basename(path)}:{name}'] = {'line': line, 'calls': calls, 'fields': fields, 'consts': nums,
                                                   'lines': body.count('\n') + 1}
json.dump(out, open(os.path.join(REPO, r'tools\audit_functions.json'), 'w'), indent=0)
print(len(out), 'functions')
