# Generate a C++ TU that prints offsetof/sizeof for every data member of every struct in a generated
# bindings header (e.g. Baldur_generated.h). Build with cl, run, get "<struct> <field> <offset> <size>".
# Usage: python layout_dump.py <header> <out.cpp>
import re, sys

BS = chr(92)
src, out = sys.argv[1], sys.argv[2]
txt = open(src, encoding='utf-8', errors='ignore').read()
structs = []
for m in re.finditer(r'^(struct|union) ([A-Za-z_][\w:<>,* ]*?)(?: : [^\n{]+)?\n\{\n(.*?)^\};', txt, re.M | re.S):
    name, body = m.group(2).strip(), m.group(3)
    prev = txt[max(0, m.start() - 200):m.start()].rstrip().splitlines()[-1:] or ['']
    prev = prev[0]
    if '<' in name or prev.startswith('template'):
        continue  # templates: their instantiations are dumped through their users
    fields = []
    depth = 0
    for line in body.split('\n'):
        s = line.strip()
        if line.startswith('\t') and not line.startswith('\t\t') and depth == 0:
            fm = re.match(r'^[\w:<>,*& ]+?[\s*&]([A-Za-z_]\w*)(\[[^\]]+\])*;$', s)
            if fm and not s.startswith(('static', 'typedef', 'using', 'friend', 'return')) and '(' not in s:
                fields.append(fm.group(1))
        depth += line.count('{') - line.count('}')
    structs.append((name, fields))

L = []
L.append('#include <cstdio>')
L.append('#include <cstddef>')
L.append('#include "lua_bindings_core_api.h"')
L.append('#include "' + src.replace(BS, '/').split('/')[-1] + '"')
L.append('#undef printf')
L.append('#pragma warning(disable: 4996 4200 4624)')
L.append('#define EEXD_NL "' + BS + 'n"')
L.append('#define EEXD_OFF(S,F) printf(#S " " #F " %zx %zx" EEXD_NL, offsetof(S,F), sizeof(((S*)0)->F));')
L.append('int main(){')
for name, fields in structs:
    L.append(f'printf("{name} __size %zx 0" EEXD_NL, sizeof({name}));')
    for fl in fields:
        L.append(f'EEXD_OFF({name},{fl})')
L.append('return 0;}')
open(out, 'w').write('\n'.join(L) + '\n')
print(len(structs), 'structs', sum(len(x[1]) for x in structs), 'fields')
