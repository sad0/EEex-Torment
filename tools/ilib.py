# Shared helpers: PE image access, InfinityLoader.db parsing, pattern search and operation evaluation.
import re, struct, collections

GAME = r'C:\Users\jnthn\Tools\gproj'
BG_EXE = GAME + r'\Baldur_bg2ee.exe'
PT_EXE = GAME + r'\Torment.exe'
REPO = r'E:\Enhanced Edition\EEex-PTEE'
UP_DB = REPO + r'\ref\EEex\EEex\loader\InfinityLoader.db'
PT_DB = REPO + r'\poc\InfinityLoader.db'


class PE:
    def __init__(s, path):
        s.path = path
        s.d = d = open(path, 'rb').read()
        pe = struct.unpack_from('<I', d, 0x3c)[0]
        n = struct.unpack_from('<H', d, pe + 6)[0]
        osz = struct.unpack_from('<H', d, pe + 20)[0]
        s.base = struct.unpack_from('<Q', d, pe + 24 + 24)[0]
        s.secs = []
        for i in range(n):
            o = pe + 24 + osz + i * 40
            name = d[o:o + 8].rstrip(b'\0').decode()
            vs, va, rs, ra = struct.unpack_from('<IIII', d, o + 8)
            s.secs.append((name, va, vs, ra, rs))
        t = [x for x in s.secs if x[0] == '.text'][0]
        s.tva, s.tsize = t[1], min(t[2], t[4])
        s.text = d[t[3]:t[3] + s.tsize]   # .text bytes, index = rva - tva
        s._pdata(pe)

    def _pdata(s, pe):
        """x64 exception directory: exact function ranges (chained entries folded to their parent)."""
        import bisect
        magic = struct.unpack_from('<H', s.d, pe + 24)[0]
        dd = pe + 24 + (112 if magic == 0x20b else 96)
        rva, size = struct.unpack_from('<II', s.d, dd + 3 * 8)
        o = s.off(rva); fr = []
        for k in range(size // 12):
            b, e, u = struct.unpack_from('<III', s.d, o + k * 12)
            fr.append((b, e, u))
        s.rf = fr
        s.rf_beg = [x[0] for x in fr]
        s._bis = bisect

    def rfrag(s, rva):
        """(begin, end) of the RUNTIME_FUNCTION fragment containing rva (no chain folding)."""
        i = s._bis.bisect_right(s.rf_beg, rva) - 1
        if i < 0 or not (s.rf[i][0] <= rva < s.rf[i][1]):
            return None
        return s.rf[i][:2]

    def rfunc(s, rva):
        """(begin, end) of the primary RUNTIME_FUNCTION containing rva, or None."""
        i = s._bis.bisect_right(s.rf_beg, rva) - 1
        if i < 0 or not (s.rf[i][0] <= rva < s.rf[i][1]):
            return None
        b, e, u = s.rf[i]
        for _ in range(8):  # follow UNW_FLAG_CHAININFO to the primary entry
            uo = s.off(u & ~1 if u & 1 else u)
            if uo is None:
                break
            ver_flags, _, cnt = s.d[uo], s.d[uo + 1], s.d[uo + 2]
            if not (ver_flags >> 3) & 4:
                break
            co = uo + 4 + ((cnt + 1) & ~1) * 2
            b, e, u = struct.unpack_from('<III', s.d, co)
        return b, e

    def off(s, rva):
        for n, va, vs, ra, rs in s.secs:
            if va <= rva < va + rs:
                return rva - va + ra

    def read(s, rva, n):
        o = s.off(rva)
        return s.d[o:o + n] if o is not None else None

    def i32(s, rva):
        return struct.unpack('<i', s.read(rva, 4))[0]

    def tbytes(s, rva, n):
        return s.text[rva - s.tva:rva - s.tva + n]

    def find(s, pat):
        """All .text RVAs matching a db pattern (hex with ?? wildcards)."""
        return [m.start() + s.tva for m in re.finditer(pat_rx(pat), s.text)]

    def count(s, b, limit=2):
        """Number of occurrences of raw bytes in .text, capped at limit."""
        c, i = 0, -1
        while c < limit:
            i = s.text.find(b, i + 1)
            if i < 0:
                break
            c += 1
        return c

    def fstart(s, rva):
        """Function start: .pdata when available, else scan back to int3 padding."""
        f = s.rfrag(rva)
        if f:
            return f[0]
        i = rva - s.tva
        while i > 2 and not (s.text[i - 1] == 0xCC and s.text[i - 2] == 0xCC):
            i -= 1
        return i + s.tva


_rx = {}


def pat_rx(pat):
    if pat not in _rx:
        parts = []
        for i in range(0, len(pat), 2):
            h = pat[i:i + 2]
            parts.append(b'.' if h == '??' else re.escape(bytes([int(h, 16)])))
        _rx[pat] = re.compile(b''.join(parts), re.S)
    return _rx[pat]


def parse_db(path):
    """Ordered dict: section -> dict of keys (keeps raw block text too)."""
    out = collections.OrderedDict()
    cur = None
    for line in open(path, encoding='utf-8-sig', errors='ignore').read().splitlines():
        m = re.match(r'^\[([^\]]+)\]\s*$', line)
        if m:
            cur = out.setdefault(m.group(1), {})
            continue
        if cur is not None and '=' in line and not line.startswith(';'):
            k, v = line.split('=', 1)
            cur[k.strip()] = v.strip()
    return out


def eval_ops(pe, addr, ops):
    """Evaluate Operations on an RVA (image semantics, READ DWORD = signed int32)."""
    st = [addr]
    for op in [o.strip() for o in ops.split(',')] if ops else []:
        if op.startswith('ADD '):
            v = int(op[4:])
            st[-1] += v - pe.base if v >= pe.base else v  # 'ADD <imagebase>' turns an RVA back into a VA
        elif op == 'PUSH':
            st.append(st[-1])
        elif op == 'READ DWORD':
            st[-1] = pe.i32(st[-1])
        elif op == 'ADD':
            a = st.pop(); st[-1] += a
        else:
            raise ValueError(op)
    return st[-1]


def classify(ops):
    """A: plain ADD (code address); B: rel32 deref; C: read immediate/rva."""
    if not ops or re.fullmatch(r'ADD -?\d+', ops):
        return 'A', int(ops[4:]) if ops else 0
    m = re.fullmatch(r'ADD (-?\d+), PUSH, READ DWORD, ADD, ADD 4', ops)
    if m:
        return 'B', int(m.group(1))
    m = re.fullmatch(r'ADD (-?\d+), READ DWORD, ADD (\d+)', ops)
    if m:
        return 'C', int(m.group(1))
    return '?', None
