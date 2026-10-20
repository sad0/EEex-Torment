# Minimal minidump reader: exception code/address, faulting thread registers, module of RIP,
# and a raw stack scan for return addresses inside known modules.
#   python dumpinfo.py <dump.dmp>
import sys, struct

d = open(sys.argv[1], 'rb').read()
sig, ver, nstreams, dir_rva = struct.unpack_from('<IIII', d, 0)
streams = {}
for i in range(nstreams):
    t, size, rva = struct.unpack_from('<III', d, dir_rva + 12 * i)
    streams[t] = (size, rva)


def mdstr(rva):
    n = struct.unpack_from('<I', d, rva)[0]
    return d[rva + 4:rva + 4 + n].decode('utf-16le')


mods = []
size, rva = streams[4]
n = struct.unpack_from('<I', d, rva)[0]
for i in range(n):
    o = rva + 4 + 108 * i
    base, msize = struct.unpack_from('<QI', d, o)
    name_rva = struct.unpack_from('<I', d, o + 20)[0]
    mods.append((base, msize, mdstr(name_rva).split('\\')[-1]))


def where(a):
    for b, s, nm in mods:
        if b <= a < b + s:
            return f'{nm}+{a - b:#x}'
    return None


mem = []  # Memory64List (9) or MemoryList (5)
if 9 in streams:
    size, rva = streams[9]
    nr, base_rva = struct.unpack_from('<QQ', d, rva)
    off = base_rva
    for i in range(nr):
        start, sz = struct.unpack_from('<QQ', d, rva + 16 + 16 * i)
        mem.append((start, sz, off)); off += sz
if 5 in streams:
    size, rva = streams[5]
    nr = struct.unpack_from('<I', d, rva)[0]
    for i in range(nr):
        start, sz, mrva = struct.unpack_from('<QII', d, rva + 4 + 16 * i)
        mem.append((start, sz, mrva))


def read(a, n):
    for s, sz, off in mem:
        if s <= a and a + n <= s + sz:
            return d[off + a - s:off + a - s + n]
    return None


size, rva = streams[6]
tid = struct.unpack_from('<I', d, rva)[0]
code, flags, rec, addr, nparams = struct.unpack_from('<IIQQI', d, rva + 8)
params = struct.unpack_from('<15Q', d, rva + 8 + 32)
ctx_size, ctx_rva = struct.unpack_from('<II', d, rva + 8 + 152)
print(f'exception {code:#x} at {addr:#x} ({where(addr)}) params {[hex(p) for p in params[:nparams]]}')
c = ctx_rva
regs = ['rax', 'rcx', 'rdx', 'rbx', 'rsp', 'rbp', 'rsi', 'rdi', 'r8', 'r9', 'r10', 'r11', 'r12', 'r13', 'r14', 'r15']
vals = struct.unpack_from('<16Q', d, c + 0x78)
rip = struct.unpack_from('<Q', d, c + 0xf8)[0]
print('rip', hex(rip), where(rip))
for r, v in zip(regs, vals):
    print(f'  {r}={v:#x} {where(v) or ""}')
rsp = vals[4]
print('stack return-address candidates:')
for i in range(0, 0x800, 8):
    b = read(rsp + i, 8)
    if b:
        v = struct.unpack('<Q', b)[0]
        w = where(v)
        if w and not w.startswith(('ntdll', 'KERNEL')):
            print(f'  rsp+{i:#x} {v:#x} {w}')
code_bytes = read(rip - 16, 32)
if code_bytes:
    print('code around rip:', code_bytes.hex())
