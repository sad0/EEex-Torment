# Runtime layout check on a running Torment.exe (read-only, ReadProcessMemory). Starting from
# g_pBaldurChitin, follow only pointers/lists stored in PROVEN fields to collect live instances of
# each struct, then check every field of those instances against its type:
#   pointer  -> null or readable committed memory (vtable pointer -> inside the exe image)
#   CString  -> pointer to readable NUL-terminated text
#   resref   -> printable ASCII / NUL padded
#   list     -> CPtrList whose head/tail/count are consistent with its node chain
#   bool     -> 0 or 1
# Proven fields are the control group (must pass). Unproven fields that pass type checks of strong
# types (pointer, string, resref, list) on every instance become runtime anchors.
# Output: memprobe.json {S: {field: {"checked": n, "ok": n, "kind": k}}}
import sys, os, json, ctypes, collections, re
from ctypes import wintypes
HERE = os.path.dirname(os.path.abspath(__file__))
L = json.load(open(os.path.join(HERE, 'ptlayout.json')))
C = json.load(open(os.path.join(HERE, 'coverage.json')))
G_BALDURCHITIN = 0x72c278   # rva of g_pBaldurChitin in Torment.exe v3.2.2.0
k32 = ctypes.WinDLL('kernel32', use_last_error=True)
psapi = ctypes.WinDLL('psapi')


class MBI(ctypes.Structure):
    _fields_ = [('BaseAddress', ctypes.c_void_p), ('AllocationBase', ctypes.c_void_p), ('AllocationProtect', wintypes.DWORD),
                ('PartitionId', wintypes.WORD), ('RegionSize', ctypes.c_size_t), ('State', wintypes.DWORD),
                ('Protect', wintypes.DWORD), ('Type', wintypes.DWORD)]


def find_pid(name='Torment.exe'):
    arr = (wintypes.DWORD * 4096)(); n = wintypes.DWORD()
    psapi.EnumProcesses(arr, ctypes.sizeof(arr), ctypes.byref(n))
    for pid in arr[:n.value // 4]:
        h = k32.OpenProcess(0x0410, False, pid)
        if not h:
            continue
        buf = ctypes.create_unicode_buffer(260)
        psapi.GetModuleBaseNameW(h, None, buf, 260)
        k32.CloseHandle(h)
        if buf.value.lower() == name.lower():
            return pid
    sys.exit('Torment.exe not running')


PID = find_pid()
H = k32.OpenProcess(0x0410, False, PID)   # QUERY_INFORMATION | VM_READ
mods = (ctypes.c_void_p * 1024)(); need = wintypes.DWORD()
psapi.EnumProcessModules(H, mods, ctypes.sizeof(mods), ctypes.byref(need))
BASE = mods[0]


class ModInfo(ctypes.Structure):
    _fields_ = [('lpBaseOfDll', ctypes.c_void_p), ('SizeOfImage', wintypes.DWORD), ('EntryPoint', ctypes.c_void_p)]


mi = ModInfo(); psapi.GetModuleInformation(H, ctypes.c_void_p(BASE), ctypes.byref(mi), ctypes.sizeof(mi))
IMG = (BASE, BASE + mi.SizeOfImage)
_region = {}


def readable(a, n=1):
    if not a or a < 0x10000 or a > 0x7fffffffffff:
        return False
    m = MBI()
    if not k32.VirtualQueryEx(H, ctypes.c_void_p(a), ctypes.byref(m), ctypes.sizeof(m)):
        return False
    if m.State != 0x1000 or m.Protect & 0x101 or not (m.Protect & 0xee):
        return False
    return a + n <= m.BaseAddress + m.RegionSize


def read(a, n):
    buf = ctypes.create_string_buffer(n); got = ctypes.c_size_t()
    if not k32.ReadProcessMemory(H, ctypes.c_void_p(a), buf, n, ctypes.byref(got)) or got.value != n:
        return None
    return buf.raw


def q(a):
    b = read(a, 8)
    return int.from_bytes(b, 'little') if b else None


PROVEN = ('proven', 'span')
STRUCT_RE = re.compile(r'^(?:struct )?(\w+)$')
LIST_RE = re.compile(r'CTypedPtrList<CPtrList,\s*(\w+)\s*\*>|^CPtrList$|^CObList$')


def ptr_target(t):
    m = re.match(r'^(?:const )?(?:struct )?(\w+) ?\*$', t.strip())
    return m.group(1) if m and m.group(1) in L else None


def check_list(a):
    """CPtrList at a: [vtbl][head][tail][count][free][blocks][blocksize] (MFC CObList layout, 8-byte ptrs)."""
    vt, head, tail = q(a), q(a + 8), q(a + 16)
    cnt_b = read(a + 24, 4)
    if vt is None or cnt_b is None:
        return False, []
    cnt = int.from_bytes(cnt_b, 'little')
    if not (IMG[0] <= vt < IMG[1]) or cnt > 100000:
        return False, []
    if cnt == 0:
        return head == 0 and tail == 0, []
    node, seen, data, last = head, 0, [], 0
    while node and seen <= cnt:
        if not readable(node, 24):
            return False, []
        nxt, prv, d = q(node), q(node + 8), q(node + 16)
        if prv != last:
            return False, []
        data.append(d); last = node; node = nxt; seen += 1
    return seen == cnt and last == tail, data


def check_field(kind, a, size, t):
    if kind == 'ptr':
        p = q(a)
        return p is not None and (p == 0 or readable(p))
    if kind == 'vtbl':
        p = q(a)
        return p is not None and IMG[0] <= p < IMG[1]
    if kind == 'cstring':
        p = q(a)
        if p is None or not readable(p):
            return False
        s = read(p, 64) or b''
        z = s.find(b'\0')
        return z >= 0 and all(32 <= c < 127 or c in (9, 10, 13) or c >= 0x80 for c in s[:z])
    if kind == 'resref':
        b = read(a, 8)
        if b is None:
            return False
        z = b.find(b'\0')
        z = 8 if z < 0 else z
        return all(32 < c < 127 for c in b[:z])   # bytes after the NUL may be stale
    if kind == 'list':
        return check_list(a)[0]
    if kind == 'bool':
        b = read(a, size)
        return b is not None and int.from_bytes(b, 'little') in (0, 1)
    return None


def kind_of(n, t, size):
    t = t.strip()
    if n == '__vftable' or t.endswith('_vtbl *'):
        return 'vtbl'
    if t.endswith('*'):
        return 'ptr'
    if t == 'CString':
        return 'cstring'
    if t.startswith('Array<'):
        return None
    if LIST_RE.search(t):
        return 'list'
    if 'CResRef' in t or t in ('char[8]', 'Array<char,8>', 'Array<unsigned __int8,8>') and 'res' in n.lower():
        return 'resref'
    if LIST_RE.search(t):
        return 'list'
    if re.match(r'm_b[A-Z]', n) and size in (1, 4) and t in ('int', 'unsigned __int8', 'bool', 'unsigned int'):
        return 'bool'
    return None


sys.path.insert(0, HERE)
import bgtypes as T


def primary_base(s):
    st = T.structs.get(s)
    return st.bases[0] if st and st.bases else None


ARR_RE = re.compile(r'^Array<(.+),(\d+)>$')


# ---- collect instances by walking proven pointers --------------------------------------------------
inst = collections.defaultdict(set)
todo = []
chitin = q(BASE + G_BALDURCHITIN)
todo.append(('CBaldurChitin', chitin))
# game objects: static CGameObjectArray (PT rva 0x72d860, 16-byte entries {id, pad, CGameObject*},
# entry count word at 0x72d858), typed by CGameObject::m_objectType (byte at +8)
OBJTYPE = {0x01: 'CGameAIBase', 0x10: 'CGameSound', 0x11: 'CGameContainer', 0x20: 'CGameSpawning', 0x21: 'CGameDoor',
           0x30: 'CGameStatic', 0x31: 'CGameSprite', 0x40: 'CObjectMarker', 0x41: 'CGameTrigger', 0x51: 'CGameTiledObject',
           0x60: 'CGameTemporal', 0x61: 'CGameAIArea', 0x70: 'CGameFireball3d', 0x71: 'CGameAIGame'}
nobj = int.from_bytes(read(BASE + 0x72d858, 2) or bytes(2), 'little')
for k in range(min(nobj, 20000)):
    p = q(BASE + 0x72d860 + 16 * k + 8)
    if p and readable(p, 16):
        ty = (read(p + 8, 1) or bytes(1))[0]
        if ty in OBJTYPE:
            todo.append((OBJTYPE[ty], p))
print('object array entries', nobj)
LIMIT = 40
while todo:
    s, a = todo.pop()
    if s not in L or a in inst[s] or len(inst[s]) >= LIMIT or not readable(a, max(8, L[s]['pt_size'] or 8)):
        continue
    inst[s].add(a)
    b = primary_base(s)
    if b:
        todo.append((b, a))
    for n, it in L[s]['items'].items():
        if it['pt'] is None or C.get(s, {}).get(n) not in PROVEN:
            continue
        fa = a + it['pt']; t = it['type'].strip()
        tg = ptr_target(t)
        if tg:
            p = q(fa)
            if p:
                todo.append((tg, p))
        elif t in L:                       # embedded struct
            todo.append((t, fa))
        elif ARR_RE.match(t):
            et, cnt = ARR_RE.match(t).groups(); cnt = int(cnt)
            etg = ptr_target(et)
            if etg:
                for k in range(min(cnt, LIMIT)):
                    p = q(fa + 8 * k)
                    if p:
                        todo.append((etg, p))
            elif et.strip() in L and L[et.strip()]['pt_size']:
                for k in range(min(cnt, LIMIT)):
                    todo.append((et.strip(), fa + k * L[et.strip()]['pt_size']))
        else:
            m = LIST_RE.search(t)
            if m and m.group(1) and m.group(1) in L:
                ok, data = check_list(fa)
                if ok:
                    todo.extend((m.group(1), d) for d in data[:LIMIT] if d)
print('instances:', {s: len(v) for s, v in sorted(inst.items(), key=lambda x: -len(x[1]))[:40]})

# ---- check fields ----------------------------------------------------------------------------------
res = {}
ctl = collections.Counter()
for s, addrs in inst.items():
    for n, it in L[s]['items'].items():
        if it['pt'] is None:
            continue
        k = kind_of(n, it['type'], it['size'])
        if not k:
            continue
        r = [check_field(k, a + it['pt'], it['size'], it['type']) for a in addrs]
        r = [x for x in r if x is not None]
        if not r:
            continue
        cls = C.get(s, {}).get(n)
        res.setdefault(s, {})[n] = {'kind': k, 'checked': len(r), 'ok': sum(r), 'class': cls}
        ctl[(cls in PROVEN, k, all(r))] += 1
json.dump(res, open(os.path.join(HERE, 'memprobe.json'), 'w'), indent=0)
print('control (proven fields) pass/fail by kind:', {f'{k}:{"ok" if a else "FAIL"}': v for (p, k, a), v in ctl.items() if p})
print('unproven fields pass/fail by kind:', {f'{k}:{"ok" if a else "FAIL"}': v for (p, k, a), v in ctl.items() if not p})
for s, fs in res.items():
    for n, v in fs.items():
        if v['ok'] < v['checked']:
            print(f'  FAIL {s}.{n} {v}')
