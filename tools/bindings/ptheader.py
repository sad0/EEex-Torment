# Emit Torment-v3.2.2.0.h: the BG IDA header with every solved struct rewritten to its Torment layout.
# Placed items keep their original declaration line(s); everything else becomes opaque
# `nobinding unsigned __int8 _ptpad_<off>[n];` bytes. Rewritten structs are packed to 1 so the
# explicit padding fully defines the layout. Also writes packing_pt.txt and a report.
import sys, os, re, json
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
IDA = os.path.join(REPO, r'ref\InfinityLoader\Core-Shared-Files\generate_bindings\in\Baldur-v2.6.6.0.h')
PACK = os.path.join(REPO, r'ref\InfinityLoader\Core-Shared-Files\generate_bindings\in\packing.txt')
OUTD = os.path.join(REPO, r'bindings\in')
os.makedirs(OUTD, exist_ok=True)
L = json.load(open(os.path.join(HERE, 'ptlayout.json')))
# STRICT=1: only fields proven by evidence or by hand stay visible (audit build for EEex.dll);
# small structs (<= 0x40 bytes) may keep assumed-identical fields.
STRICT = os.environ.get('PTEE_STRICT') == '1'
if STRICT:
    OUTD = os.path.join(REPO, r'bindings\in_strict'); os.makedirs(OUTD, exist_ok=True)
MANUALF = json.load(open(os.path.join(HERE, 'manual_fields.json'))).get('fields', {}) if os.path.exists(os.path.join(HERE, 'manual_fields.json')) else {}
PROVEN = {'evidence', 'manual'}


def visible(lay, it):
    if not STRICT:
        return True
    if it.get('how') in PROVEN:
        return True
    return (lay['bg_size'] or 0) <= 0x40 and it.get('how') in ('assumed', None) and it['pt'] == it['bg']

txt = open(IDA, encoding='utf-8', errors='ignore').read()
hdr_rx = re.compile(r'^(struct|union) (__cppobj )?(__declspec\(align\(\d+\)\) )?([^\n:{]+?)( : ([^\n{]+))?\n\{\n(.*?)^\};', re.M | re.S)


def items_of(body):
    """Split a struct body into depth-1 items: (name or None, [lines])."""
    out, cur, depth = [], [], 0
    for line in body.split('\n'):
        if not line.strip():
            continue
        cur.append(line)
        depth += line.count('{') - line.count('}')
        if depth == 0 and line.rstrip().endswith(';'):
            m = re.search(r'([A-Za-z_~]\w*)\s*(\[[^\]]*\])*\s*(:\s*\d+)?\s*(/\*.*\*/)?\s*;\s*$', line)
            name = m.group(1) if m else None
            if len(cur) > 1 and name in ('}',):
                name = None
            out.append((name, cur)); cur = []
    return out


report = {'rewritten': [], 'opaque': [], 'kept': []}
packed = []


def psize(item, lay):
    """PT size of an item (primitive: BG size; embedded struct: its PT size)."""
    t = item['type']
    m = re.fullmatch(r'(?:ConstArray|Array)<(.+),\s*(\d+)>', t.strip())
    inner, n = (m.group(1).strip(), int(m.group(2))) if m else (t.strip(), 1)
    inner = re.sub(r'\b(const|struct|enum|union)\b', '', inner).strip()
    if inner.endswith('*'):
        return item['size']
    if inner in L:
        ps = L[inner]['pt_size']
        return ps * n if ps is not None else None
    return item['size']


def rewrite(m):
    kind, cpp, align, name, _, bases, body = m.groups()
    name = name.strip()
    lay = L.get(name)
    if not lay or kind != 'struct':
        return m.group(0)
    items = lay['items']
    same = lay['pt_size'] == lay['bg_size'] and all(v['pt'] == v['bg'] and visible(lay, v) for v in items.values())
    if same:
        report['kept'].append(name)
        return m.group(0)
    if lay['pt_size'] is None:
        report['opaque'].append(name)
    base = bases.split(',')[0].strip() if bases else None
    cur = 0
    if base:
        bl = L.get(base)
        if not bl or bl['pt_size'] is None:
            # unknown base size: no field can be placed safely -> fully opaque (pointer use only)
            report['opaque'].append(name); packed.append(name)
            return f'{kind} {cpp or ""}{name}{(" : " + bases) if bases else ""}' + '\n{\n\tnobinding unsigned __int8 _ptopaque[8];\n};'

        cur = bl['pt_size']
    lines = []
    placed = 0
    for iname, ilines in items_of(body):
        it = items.get(iname)
        if iname == '__vftable' and cur == 0:
            lines += ilines; cur = 8; placed += 1; continue
        if not it or it['pt'] is None or not visible(lay, it):
            continue
        mt = MANUALF.get(name, {}).get(iname, {})
        if isinstance(mt, dict) and mt.get('type'):
            # hand-verified type change (e.g. inline array in BG, pointer in PTEE)
            it = dict(it, size=int(mt['size'], 16), type=mt['type'])
            ilines = [f'	{mt["type"]} {iname};']
        sz = psize(it, lay)
        if sz is None or it['pt'] < cur:
            continue
        if it['pt'] > cur:
            lines.append(f'\tnobinding unsigned __int8 _ptpad_{cur:x}[{it["pt"] - cur}];')
        lines += [l.replace('__declspec(align(8)) ', '') for l in ilines]
        cur = it['pt'] + sz; placed += 1
    end = lay['pt_size'] if lay['pt_size'] is not None else max(cur, lay['bg_size'] or 0)
    if end > cur:
        lines.append(f'\tnobinding unsigned __int8 _ptpad_{cur:x}[{end - cur}];')
    report['rewritten'].append((name, placed, len(items)))
    packed.append(name)
    head = f'{kind} {cpp or ""}{name}{(" : " + bases) if bases else ""}'
    return head + '\n{\n' + '\n'.join(lines) + '\n};'


new = hdr_rx.sub(rewrite, txt)
open(os.path.join(OUTD, 'Torment-v3.2.2.0.h'), 'w', encoding='utf-8', newline='\n').write(new)
pk = open(PACK).read()  # natural alignment: explicit pads already sit on aligned PT offsets
open(os.path.join(OUTD, 'packing_pt.txt'), 'w', newline='\n').write(pk)
json.dump(report, open(os.path.join(HERE, 'ptheader_report.json'), 'w'), indent=0)
print('rewritten', len(report['rewritten']), 'kept', len(report['kept']), 'size unknown', len(report['opaque']))
