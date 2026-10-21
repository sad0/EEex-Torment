# Torment definition of `struct uiItem` (and its anonymous nested member structs) from the proofs in
# manual_fields_uiitem.json (eeexlua/notes/uiItem_layout.md): every member at its proven Torment offset, BG members
# proven absent dropped, unproven ones and Torment-only members as opaque padding. ptheader.py substitutes it for
# the generic rewrite (which places top-level members only and keeps BG nested layouts).
import re, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(HERE, 'manual_fields_uiitem.json')))
FIELDS, SIZES = P['fields'], P['sizes']


def split_items(body):
    """Top-level members of a struct body: (name, text) with nested anonymous structs kept whole."""
    out, cur, depth = [], [], 0
    for line in body.split('\n'):
        if not line.strip():
            continue
        cur.append(line)
        depth += line.count('{') - line.count('}')
        if depth == 0 and line.rstrip().endswith(';'):
            m = re.search(r'([A-Za-z_]\w*)\s*(\[[^\]]*\])?\s*;\s*$', line)
            out.append((m.group(1) if m else None, cur)); cur = []
    return out


NESTED = {}


def pad(off, n, indent):
    return f'{indent}nobinding unsigned __int8 _ptpad_{off:x}[{n}];'


def emit(members, offs, size, indent):
    """members: [(name, lines)]; offs: {name: off or 'none'}; returns lines laid out at Torment offsets."""
    placed = []
    for name, lines in members:
        o = offs.get(name)
        if isinstance(o, dict):
            o = o['pt']
        if o is None or o == 'none' or name.startswith('_ptpad'):
            continue
        placed.append((int(o, 16), name, lines))
    placed.sort()
    out, cur = [], 0
    for o, name, lines in placed:
        if o < cur:
            raise SystemExit(f'uiItem layout overlap at {name} {o:#x} < {cur:#x}')
        if o > cur:
            out.append(pad(cur, o - cur, indent))
        nested = len(lines) > 1
        if nested:
            sub = '\n'.join(lines[2:-1])  # between "struct ... {" and "} name;"
            key = 'uiItem::' + name + '_t'
            subsize = int(SIZES[key]['pt'], 16)
            sublines = emit(split_items(sub), FIELDS.get(key, {}), subsize, indent + '\t')
            NESTED[name] = [l[1:] for l in sublines]  # same members, one tab less, for the separate definition
            out += [f'{indent}struct', f'{indent}{{'] + sublines + [f'{indent}}} {name};']
            cur = o + subsize
        else:
            out += [l.replace('__declspec(align(8)) ', '') for l in lines]
            cur = o + member_size(lines[0])
    if size > cur:
        out.append(pad(cur, size - cur, indent))
    return out


def member_size(line):
    t = line.strip().rstrip(';')
    m = re.search(r'\[(\d+)\]$', t)
    n = int(m.group(1)) if m else 1
    if '*' in t:
        return 8 * n
    base = {'int': 4, 'unsigned int': 4, 'uiItemType': 4, 'float': 4, 'SDL_Rect': 16, 'Marker': 24, '__int64': 8}
    for k, v in sorted(base.items(), key=lambda kv: -len(kv[0])):
        if re.match(rf'(const\s+)?{re.escape(k)}\b', t):
            return v * n
    raise SystemExit('unknown member size: ' + line)


def rewrite(text, src):
    """text: generated header; src: the BG input header (uiItem members with BG nested layouts)."""
    body = re.search(r'^struct uiItem\s*\{\n(.*?)\n\};', src, re.S | re.M).group(1)
    m = re.search(r'^struct uiItem\n\{\n(.*?)\n\};', text, re.S | re.M)
    lines = emit(split_items(body), FIELDS['uiItem'], int(SIZES['uiItem']['pt'], 16), '\t')
    new = 'struct uiItem\n{\n' + '\n'.join(lines) + '\n\n\tuiItem() = delete;\n};'
    text = text[:m.start()] + new + text[m.end():]
    # the bindings generator reads the nested types from their separate IDA definitions: rewrite those too
    for name, sub in NESTED.items():
        rx = re.compile(r'^struct (?:__declspec\(align\(8\)\) )?uiItem::<unnamed_type_' + name + r'>\n\{\n.*?\n\};', re.S | re.M)
        n = len(rx.findall(text))
        if n != 1:
            raise SystemExit(f'uiItem::<unnamed_type_{name}>: {n} definitions')
        text = rx.sub(lambda _: f'struct uiItem::<unnamed_type_{name}>\n{{\n' + '\n'.join(sub) + '\n};', text)
    return text
