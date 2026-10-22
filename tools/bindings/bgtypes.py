# BG2EE type model from the generated bindings header + compiled layout dump.
#   structs[name] = Struct(name, size, bases, fields=[Field(name, type, off, size)])
#   field_at(struct, off) -> innermost (path, Field, type) covering an absolute offset
#   member_sigs: {(struct, fn): [arg types]}, free_sigs: {fn: [arg types]}, ret types
#   globals: {name: type}  (pointer to the global object, i.e. the extern's declared type)
import re, collections

HDR = r'E:\Enhanced Edition\EEex-PSTEE\build\bgout\Baldur_generated.h'
LAY = r'E:\Enhanced Edition\EEex-PSTEE\build\bgout\bg_layout.txt'

Field = collections.namedtuple('Field', 'name type off size')


class Struct:
    def __init__(s, name):
        s.name, s.size, s.bases, s.fields = name, None, [], []


def clean_type(t):
    t = re.sub(r'\b(const|volatile|struct|enum|union)\b', '', t)
    return re.sub(r'\s+', ' ', t).strip()


def parse_type(t):
    """('ptr', inner) / ('arr', inner, n) / ('named', name) / ('prim', name)"""
    t = clean_type(t)
    if t.endswith('*'):
        return ('ptr', parse_type(t[:-1]))
    m = re.fullmatch(r'(?:ConstArray|Array)<(.+),\s*(\d+)>', t)
    if m:
        return ('arr', parse_type(m.group(1)), int(m.group(2)))
    return ('named', t)


txt = open(HDR, encoding='utf-8', errors='ignore').read()
structs = {}
member_sigs, free_sigs, rets = {}, {}, {}
vtbl_sigs = {}

for m in re.finditer(r'^(?:struct|union) ([A-Za-z_][\w:<>,* ]*?)(?: : ([^\n{]+))?\n\{\n(.*?)^\};', txt, re.M | re.S):
    name, bases, body = m.group(1).strip(), m.group(2), m.group(3)
    st = structs.setdefault(name, Struct(name))
    st.bases = [b.strip() for b in re.split(r',(?![^<]*>)', bases)] if bases else []
    st.ftypes = {}
    depth = 0
    invt = False
    for line in body.split('\n'):
        s = line.strip()
        if depth == 0 and line.startswith('\t') and not line.startswith('\t\t'):
            fm = re.match(r'^([\w:<>,*& ]+?[\s*&])([A-Za-z_]\w*)(\[([^\]]+)\])?;$', s)
            if fm and '(' not in s and not s.startswith(('static', 'typedef', 'using', 'friend', 'return')):
                ty = fm.group(1).strip()
                if fm.group(4):
                    ty = f'Array<{ty},{fm.group(4)}>'
                st.ftypes[fm.group(2)] = ty
            tm = re.match(r'^typedef (.+?) \(__\w+ \*type_(\w+)\)\((.*)\);$', s)
            if tm:
                member_sigs[(name, tm.group(2))] = [a.strip() for a in re.split(r',(?![^<]*>)', tm.group(3)) if a.strip()]
                rets[(name, tm.group(2))] = tm.group(1)
        if s.startswith('struct vtbl'):
            invt = True
        if invt and depth == 1:
            vm = re.match(r'^(.+?) \(__\w+ \*(\w+)\)\((.*)\);$', s)
            if vm:
                vtbl_sigs.setdefault(name, []).append((vm.group(2), [a.strip() for a in re.split(r',(?![^<]*>)', vm.group(3)) if a.strip()], vm.group(1)))
        depth += line.count('{') - line.count('}')
        if invt and depth <= 0 and '}' in line:
            invt = False

for tm in re.finditer(r'^typedef (.+?) \((?:__\w+ )?\*type_(\w+)\)\((.*)\);$', txt, re.M):
    free_sigs[tm.group(2)] = [a.strip() for a in re.split(r',(?![^<]*>)', tm.group(3)) if a.strip()]
    rets[(None, tm.group(2))] = tm.group(1)

globals_ = {}
for gm in re.finditer(r'^extern (.+?)\s*\*\s*p_(\w+);$', txt, re.M):
    globals_[gm.group(2)] = gm.group(1)

for line in open(LAY):
    p = line.split()
    if len(p) != 4:
        continue
    sname, fname, off, size = p[0], p[1], int(p[2], 16), int(p[3], 16)
    st = structs.setdefault(sname, Struct(sname))
    if fname == '__size':
        st.size = off
    else:
        st.fields.append(Field(fname, st.ftypes.get(fname, '?') if hasattr(st, 'ftypes') else '?', off, size))
for st in structs.values():
    st.fields.sort(key=lambda f: f.off)


def all_fields(sname, depth=0):
    """Own fields plus fields of the primary base chain (single inheritance, base at offset 0)."""
    st = structs.get(sname)
    if not st or depth > 12:
        return []
    out = []
    if st.bases:
        b = st.bases[0]
        if b in structs:
            out += all_fields(b, depth + 1)
    return out + st.fields


def base_struct(t):
    """struct name for a parsed named type, resolving typedef-ish names present in structs."""
    if t[0] == 'named' and t[1] in structs:
        return t[1]
    return None


def field_at(sname, off, depth=0):
    """Innermost field covering absolute offset off in struct sname.
    Returns (path list of (struct, field)), field, rel offset into that field)."""
    st = structs.get(sname)
    if not st or depth > 12:
        return None
    best = None
    for f in all_fields(sname):
        if f.off <= off < f.off + max(f.size, 1):
            best = f
    if best is None:
        # inherited fields are flattened in the layout dump (offsetof works through bases)
        return None
    rel = off - best.off
    pt = parse_type(best.type)
    inner = base_struct(pt)
    if inner and rel < (structs[inner].size or 0):
        sub = field_at(inner, rel, depth + 1)
        if sub:
            return ([(sname, best.name)] + sub[0], sub[1], sub[2])
    return ([(sname, best.name)], best, rel)


if __name__ == '__main__':
    print(len(structs), 'structs;', len(member_sigs), 'member sigs;', len(free_sigs), 'free sigs;', len(globals_), 'globals;', len(vtbl_sigs), 'vtbls')
    print(structs['CGameSprite'].size, [f for f in structs['CGameSprite'].fields[:5]])
    print(field_at('CGameSprite', 0x1120 + 0xc58))
    print(globals_.get('g_pBaldurChitin'), member_sigs.get(('CGameSprite', 'GetKitMask')))
    print(vtbl_sigs.get('CGameObject', [])[:3])
