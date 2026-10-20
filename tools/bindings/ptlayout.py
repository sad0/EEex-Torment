# Solve Torment.exe struct layouts from BG layouts + field evidence.
# For each struct S (top-level items in declaration order, BG offsets from bg_layout.txt):
#   pt_off[S][item] from evidence (direct, or through embedded/base structs) and delta interpolation,
#   pt_size[S] from consecutive embedded items / array strides / tail delta.
# Items without a proven PT offset are left out (they become opaque padding when emitting).
# Output: bindings/ptlayout.json and a report.
import sys, os, json, re, collections
sys.path.insert(0, os.path.dirname(__file__))
import bgtypes as T

HERE = os.path.dirname(__file__)
EV = json.load(open(os.path.join(HERE, 'field_evidence.json')))

# ---- evidence per struct: bg_abs -> Counter(pt_abs) ------------------------------------------
ev = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
for k, v in EV.items():
    s, o, z = k.split('|')
    for a, c in v.items():
        ev[s][int(o, 16)][int(a, 16)] += c


def best(counter, minfrac=0.8):
    tot = sum(counter.values())
    a, c = max(counter.items(), key=lambda x: x[1])
    return a if c >= minfrac * tot else None


def own_items(s):
    """Own (non-inherited) items of s: fields declared by s itself, BG offsets."""
    st = T.structs.get(s)
    return list(st.fields) if st else []


def primary_base(s):
    st = T.structs.get(s)
    if st and st.bases and st.bases[0] in T.structs:
        return st.bases[0]
    return None


def bg_size(s):
    st = T.structs.get(s)
    return st.size if st else None


def item_struct(f):
    t = T.parse_type(f.type)
    if t[0] == 'named' and t[1] in T.structs:
        return t[1], 1
    if t[0] == 'arr' and t[1][0] == 'named' and t[1][1] in T.structs:
        return t[1][1], t[2]
    return None, None


# derived -> base evidence: offsets inside the primary base region belong to the base too
for s in list(T.structs):
    b = primary_base(s)
    while b:
        bs = bg_size(b) or 0
        for o, c in list(ev.get(s, {}).items()):
            if o < bs:
                for a, n in c.items():
                    ev[b][o][a] += n
        b = primary_base(b)

# base-typed accesses beyond the base size belong to a derived class: attribute when only one
# derived class is large enough to contain the offset
derived = collections.defaultdict(set)
for s in T.structs:
    b = primary_base(s)
    while b:
        derived[b].add(s); b = primary_base(b)
for b in list(ev):
    bs = bg_size(b) or 0
    for o, c in list(ev[b].items()):
        if o < bs:
            continue
        cands = [d for d in derived.get(b, ()) if (bg_size(d) or 0) > o and not any(primary_base(x) == d and (bg_size(x) or 0) > o for x in derived.get(b, ()))]
        if len(cands) == 1:
            for a, n in c.items():
                ev[cands[0]][o][a] += n

pt_off = collections.defaultdict(dict)   # s -> item name -> pt offset
pt_size = {}
how = collections.defaultdict(dict)

# hand-verified fields/sizes (manual_fields.json): {"fields": {S: {f: off}}, "sizes": {S: size}}
MANUAL = {'fields': {}, 'sizes': {}}
if os.path.exists(os.path.join(HERE, 'manual_fields.json')):
    MANUAL = json.load(open(os.path.join(HERE, 'manual_fields.json')))
for _s, _fs in MANUAL.get('fields', {}).items():
    for _f, _v in _fs.items():
        if not _f.startswith('_'):
            pt_off[_s][_f] = int(_v['pt'], 16) if isinstance(_v, dict) else int(_v, 16)
            how[_s][_f] = 'manual'
# manual item size change (BG inline array -> PTEE pointer): MSIZE[S][f]
MSIZE = collections.defaultdict(dict)
for _s, _fs in MANUAL.get('fields', {}).items():
    for _f, _v in _fs.items():
        if isinstance(_v, dict) and 'size' in _v:
            MSIZE[_s][_f] = int(_v['size'], 16)
for _s, _v in MANUAL.get('sizes', {}).items():
    pt_size[_s] = int(_v['pt'], 16) if isinstance(_v, dict) else int(_v, 16)


def flat(s, r, depth=0):
    """PT relative offset for BG relative offset r inside struct s, if known."""
    if depth > 10:
        return None
    if s not in ev and pt_size.get(s, bg_size(s)) == bg_size(s) and not any(primary_base(x) == s for x in ()):
        # no evidence at all for s (typically small template/list types): identity layout
        st = T.structs.get(s)
        if st is not None and (not st.fields or primary_base(s) is None):
            return r
    b = primary_base(s)
    if b and r < (bg_size(b) or 0):
        return flat(b, r, depth + 1)
    for f in own_items(s):
        if f.off <= r < f.off + max(f.size, 1):
            if f.name not in pt_off[s]:
                return None
            base = pt_off[s][f.name]
            u, n = item_struct(f)
            if u:
                us = bg_size(u)
                k, rr = divmod(r - f.off, us) if us else (0, r - f.off)
                inner = flat(u, rr, depth + 1)
                if inner is None or (k and u not in pt_size):
                    return None
                return base + k * pt_size.get(u, us) + inner
            return base + (r - f.off) if r - f.off < f.size else None
    return None


def solve_struct(s):
    items = own_items(s)
    changed = False
    for f in items:
        if f.name in pt_off[s]:
            continue
        cand = collections.Counter()
        u, n = item_struct(f)
        for o, c in ev.get(s, {}).items():
            if not (f.off <= o < f.off + max(f.size, 1)):
                continue
            if u is None:
                if o == f.off or (T.parse_type(f.type)[0] == 'arr'):
                    for a, k in c.items():
                        cand[a - (o - f.off)] += k
            else:
                us = bg_size(u)
                kk, rr = divmod(o - f.off, us) if us else (0, o - f.off)
                inner = flat(u, rr)
                if inner is not None and (kk == 0 or u in pt_size):
                    for a, k in c.items():
                        cand[a - inner - kk * pt_size.get(u, us)] += k
        if cand:
            b = best(cand)
            if b is not None:
                pt_off[s][f.name] = b; how[s][f.name] = 'evidence'; changed = True
    return changed


def interpolate(s):
    items = own_items(s)
    changed = False
    known = [(i, f) for i, f in enumerate(items) if f.name in pt_off[s]]
    for i, f in enumerate(items):
        if f.name in pt_off[s]:
            continue
        prev = [(j, g) for j, g in known if j < i]
        nxt = [(j, g) for j, g in known if j > i]
        if not prev or not nxt:
            ref = nxt[0] if nxt else (prev[-1] if prev else None)
            if ref is None or not EXTRAP:
                continue
            j0, g0 = ref
            if abs(g0.off - f.off) > 0x100:
                continue
            lo, hi = (i, j0) if nxt else (j0, i + 1)
            ok = all(not item_struct(m)[0] or pt_size.get(item_struct(m)[0], bg_size(item_struct(m)[0])) == bg_size(item_struct(m)[0]) for m in items[lo:hi])
            if ok:
                pt_off[s][f.name] = f.off + (pt_off[s][g0.name] - g0.off); how[s][f.name] = 'extrap'; changed = True
            continue
        j, g = prev[-1]; k, h = nxt[0]
        d1 = pt_off[s][g.name] - g.off; d2 = pt_off[s][h.name] - h.off
        if d1 != d2:
            continue
        # every item between must keep its size
        ok = True
        for m in items[j:k]:
            u, n = item_struct(m)
            if u and pt_size.get(u, bg_size(u)) != bg_size(u):
                ok = False
        if ok:
            pt_off[s][f.name] = f.off + d1; how[s][f.name] = 'interp'; changed = True
    return changed


def adjacency(s):
    """BG-adjacent neighbours: next = this + PT size(this), when one of them is known."""
    items = own_items(s)
    changed = False
    for a, b in zip(items, items[1:]):
        if a.off + a.size != b.off:
            continue
        ua, na = item_struct(a)
        sa = MSIZE[s].get(a.name) or ((pt_size[ua] * na if ua in pt_size else None) if ua else a.size)
        if sa is None:
            continue
        if a.name in pt_off[s] and b.name not in pt_off[s]:
            pt_off[s][b.name] = pt_off[s][a.name] + sa; how[s][b.name] = 'adjacent'; changed = True
        elif b.name in pt_off[s] and a.name not in pt_off[s]:
            pt_off[s][a.name] = pt_off[s][b.name] - sa; how[s][a.name] = 'adjacent'; changed = True
    return changed


def infer_sizes():
    changed = False
    for s, st in T.structs.items():
        items = own_items(s)
        for a, b in zip(items, items[1:]):
            u, n = item_struct(a)
            if u and u not in pt_size and a.name in pt_off[s] and b.name in pt_off[s]:
                gap = pt_off[s][b.name] - pt_off[s][a.name]
                if n and gap % n == 0 and abs(gap // n - bg_size(u)) < 0x400:
                    pt_size[u] = gap // n; changed = True
    return changed


def infer_sizes2():
    """Base size from a derived class's first own item; size from last item + BG tail padding."""
    changed = False
    for s, st in T.structs.items():
        b = primary_base(s)
        items = own_items(s)
        if b and b not in pt_size and items and items[0].name in pt_off[s] and items[0].off == bg_size(b):
            pt_size[b] = pt_off[s][items[0].name]; changed = True
        if s not in pt_size and items and items[-1].name in pt_off[s]:
            last = items[-1]
            u, n = item_struct(last)
            lsz = MSIZE[s].get(last.name) or ((pt_size.get(u) * n if u in pt_size else None) if u else last.size)
            if lsz is not None:
                tail = st.size - (last.off + last.size)
                if 0 <= tail < 16:
                    pt_size[s] = pt_off[s][last.name] + lsz + tail; changed = True
    return changed


def same_layout(s):
    """No contradicting evidence anywhere in s: keep BG layout (flagged 'assumed')."""
    for o, c in ev.get(s, {}).items():
        b = best(c, 0.5)
        if b is not None and b != o:
            return False
    return True


EXTRAP = False
for it in range(24):
    if it == 12:
        EXTRAP = True  # second phase: extend deltas to struct ends
    ch = False
    for s in T.structs:
        ch |= solve_struct(s)
    ch |= infer_sizes()
    ch |= infer_sizes2()
    if EXTRAP:
        for s in T.structs:
            ch |= adjacency(s)
    for s in T.structs:
        ch |= interpolate(s)
    if not ch and it >= 12:
        break

# ---- consistency: PT order must follow BG order, no overlaps, size covers all items ----------
RANK = {'manual': -1, 'evidence': 0, 'interp': 1, 'adjacent': 2, 'extrap': 3, 'assumed': 4}


def isize(s, f):
    if f.name in MSIZE[s]:
        return MSIZE[s][f.name]
    u, n = item_struct(f)
    if u:
        return pt_size[u] * n if u in pt_size else None
    return f.size


_al = {}
PACKED = set()
for _l in open(os.path.join(HERE, '..', '..', 'ref', 'InfinityLoader', 'Core-Shared-Files', 'generate_bindings', 'in', 'packing.txt')):
    if _l.strip():
        PACKED.add(_l.rsplit(' ', 1)[0].strip())


def align_of_type(tstr, depth=0):
    t = T.parse_type(tstr)
    while t[0] == 'arr':
        t = t[1]
    if t[0] == 'ptr':
        return 8
    name = t[1]
    if name in T.structs and depth < 20:
        if name not in _al:
            _al[name] = 1
            a = 1
            b = primary_base(name)
            if b:
                a = max(a, align_of_type(b, depth + 1))
            for f in own_items(name):
                a = max(a, align_of_type(f.type, depth + 1) if f.type != '?' else 1)
            _al[name] = a
        return _al[name]
    prim = {'char': 1, 'bool': 1, '__int8': 1, 'unsigned __int8': 1, 'byte': 1, 'sbyte': 1, '__int16': 2, 'unsigned __int16': 2,
            'short': 2, 'ushort': 2, 'int': 4, 'unsigned int': 4, 'uint': 4, '__int32': 4, 'unsigned __int32': 4, 'float': 4,
            'long': 4, 'unsigned long': 4, 'double': 8, '__int64': 8, 'unsigned __int64': 8, 'size_t': 8}
    if name in prim:
        return prim[name]
    # unknown named types (templates, lists, handles): assume pointer alignment when large
    return 8 if re.search(r'List|Array|Map|<|\*|CString|Plex|POSITION', name) else 4


def consistency():
    dropped = 0
    for s in T.structs:
        items = [f for f in own_items(s) if f.name in pt_off[s]]
        # base region
        b = primary_base(s)
        floor = pt_size.get(b, 0) if b else 0
        ok = []
        for f in items:
            sz = isize(s, f)
            p = pt_off[s][f.name]
            if sz is None or p < floor or p % align_of_type(f.type) != 0:
                del pt_off[s][f.name]; dropped += 1; continue
            if ok:
                g = ok[-1]
                if pt_off[s][g.name] + isize(s, g) > p:
                    # overlap / order violation: keep the better-ranked one
                    if RANK.get(how[s].get(f.name), 5) < RANK.get(how[s].get(g.name), 5):
                        del pt_off[s][g.name]; ok.pop(); dropped += 1
                    else:
                        del pt_off[s][f.name]; dropped += 1; continue
            ok.append(f)
        if s in pt_size and pt_size[s] is not None and s not in PACKED:
            a = align_of_type(s)
            if pt_size[s] % a:
                pt_size[s] += a - pt_size[s] % a
        if ok and s in pt_size:
            end = pt_off[s][ok[-1].name] + isize(s, ok[-1])
            if pt_size[s] < end:
                tail = (T.structs[s].size or 0) - (ok[-1].off + ok[-1].size)
                pt_size[s] = end + max(0, tail)
    return dropped



# structs with no contradicting evidence keep their BG layout
assumed = []


def depth_of(s, d=0):
    b = primary_base(s)
    return depth_of(b, d + 1) if b and d < 20 else d


for s in sorted(T.structs, key=depth_of):
    st = T.structs[s]
    if s in ev and not same_layout(s):
        continue
    b = primary_base(s)
    delta = 0
    if b:
        if pt_size.get(b) is None:
            continue
        delta = pt_size[b] - (bg_size(b) or 0)
    if all(pt_off[s][f.name] == f.off + delta for f in own_items(s) if f.name in pt_off[s]):
        for f in own_items(s):
            if f.name not in pt_off[s]:
                pt_off[s][f.name] = f.off + delta; how[s][f.name] = 'assumed'
        if st.size is not None and (s not in pt_size or (b and delta and pt_size[s] == st.size)):
            pt_size[s] = st.size + delta
        assumed.append(s)

for _ in range(60):
    d = consistency()
    if not d:
        break

out = {s: {'bg_size': T.structs[s].size, 'pt_size': pt_size.get(s),
           'items': {f.name: {'bg': f.off, 'pt': pt_off[s].get(f.name), 'size': MSIZE[s].get(f.name, f.size), 'type': f.type, 'how': how[s].get(f.name)} for f in own_items(s)}}
       for s in T.structs}
json.dump(out, open(os.path.join(HERE, 'ptlayout.json'), 'w'), indent=0)
if __name__ == '__main__':
    tot = sum(len(own_items(s)) for s in T.structs)
    known = sum(len(pt_off[s]) for s in T.structs)
    print(f'items {tot}, placed {known} ({sum(1 for s in T.structs for v in how[s].values() if v == "evidence")} evidence, '
          f'{sum(1 for s in T.structs for v in how[s].values() if v == "interp")} interp, {sum(1 for s in T.structs for v in how[s].values() if v == "assumed")} assumed); '
          f'assumed structs {len(assumed)}; sizes {len(pt_size)}')
    for s in sys.argv[1:]:
        print('==', s, 'bg', hex(T.structs[s].size), 'pt', pt_size.get(s) and hex(pt_size[s]))
        for f in own_items(s):
            p = pt_off[s].get(f.name)
            print(f'  {f.off:#7x} {f.name:40} -> {p and hex(p)} {how[s].get(f.name)}')
