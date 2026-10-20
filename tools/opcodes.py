# Effect opcode table of BG2EE vs Torment from CGameEffect::DecodeEffect's jump table: for every
# opcode, the constructor called after operator new in each exe. An opcode is "same" when the PT
# constructor is the fmap counterpart of the BG one. Output: opcodes.json + summary.
import json, struct
import capstone
from ilib import PE, BG_EXE
from fmap import whole_ratio

BG = PE(BG_EXE); PT = PE('E:/Enhanced Edition/Environnement de test/PTEE (EEex dev)/Torment.exe')
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
F = {int(k, 16): int(v[0], 16) for k, v in json.load(open('fmap.json')).items()}
BN = {int(k, 16): v for k, v in json.load(open('bgnames.json')).items()}
PN = {int(k, 16): v for k, v in json.load(open('ptnames.json')).items()}
CFG = {'BG': (BG, 0x1e2770, 0x16f, 0x4f7a88), 'PT': (PT, 0x2030e8, 0x17f, 0x580078)}


def table(name):
    pe, tab, maxop, new = CFG[name]
    out = {}
    for op in range(maxop + 1):
        tgt = struct.unpack('<i', pe.read(tab + 4 * op, 4))[0]
        size, ctor = None, None
        seen_new = False
        for i in md.disasm(pe.tbytes(tgt, 0x80), tgt):
            if i.mnemonic == 'mov' and i.op_str.startswith('ecx, 0x'):
                size = int(i.op_str.split(', ')[1], 16)
            if i.mnemonic == 'call' and i.op_str.startswith('0x'):
                t = int(i.op_str, 16)
                if t == new:
                    seen_new = True; continue
                if seen_new:
                    ctor = t; break
            if i.mnemonic in ('jmp', 'ret') and not i.op_str.startswith('0x1') and seen_new is False and i.address > tgt + 4:
                break
        out[op] = (tgt, size, ctor)
    return out


def vtable(pe, ctor):
    """vtable written by a constructor: last `lea reg, [rip + X]` followed by a store to [rcx/rbx/rdi]."""
    vt = None
    for i in md.disasm(pe.tbytes(ctor, 0x100), ctor):
        if i.mnemonic == 'lea' and 'rip' in i.op_str:
            d = int(i.op_str.split('+ ')[1].rstrip(']'), 16) if '+ ' in i.op_str else None
            if d is not None:
                cand = i.address + i.size + d
        elif i.mnemonic == 'mov' and i.op_str.startswith('qword ptr [r') and '], r' in i.op_str and 'cand' in dir():
            vt = cand
        if i.mnemonic == 'ret':
            break
    return vt


def slot(pe, vt, k):
    return struct.unpack('<Q', pe.read(vt + 8 * k, 8))[0] - pe.base


B, P = table('BG'), table('PT')
# ApplyEffect slot: the BG vtable slot named *::ApplyEffect (same for every effect class)
AE = None
for op, (t, sz, c) in B.items():
    vt = c and vtable(BG, c)
    if vt:
        for k in range(40):
            n = BN.get(slot(BG, vt, k), '')
            if n.endswith('::ApplyEffect'):
                AE = k; break
    if AE is not None:
        break
print('ApplyEffect vtable slot', AE)
ratio = {}
res = {}
cnt = {'same': 0, 'changed': 0, 'pt_only': 0, 'bg_only': 0, 'none': 0}
for op in range(max(len(B), len(P))):
    b = B.get(op); p = P.get(op)
    bc = b[2] if b else None; pc = p[2] if p else None
    if bc is None and pc is None:
        st = 'none'
    elif bc is None:
        st = 'pt_only'
    elif pc is None:
        st = 'bg_only'
    else:
        bv, pv = vtable(BG, bc), vtable(PT, pc)
        ba = slot(BG, bv, AE) if bv else None
        pa = slot(PT, pv, AE) if pv else None
        st = 'same' if (F.get(bc) == pc or (ba is not None and F.get(ba) == pa)) else 'changed'
        if st == 'changed' and ba is not None and pa is not None and BN.get(ba) and PN.get(pa) == BN.get(ba):
            st = 'same'
        if st == 'changed' and ba is not None and pa is not None:
            r = whole_ratio(ba, pa)[0]
            ratio[op] = r
            if r >= 0.9:
                st = 'same'
    cnt[st] += 1
    res[op] = {'status': st, 'bg_ctor': bc and hex(bc), 'bg_name': BN.get(bc) if bc else None,
               'pt_ctor': pc and hex(pc), 'pt_name': PN.get(pc) if pc else None,
               'bg_size': b[1] if b else None, 'pt_size': p[1] if p else None, 'apply_ratio': ratio.get(op)}
json.dump(res, open('opcodes.json', 'w'), indent=0)
print(cnt)
for op, r in res.items():
    if r['status'] not in ('same', 'none'):
        print(op, r['status'], r['bg_name'] or r['bg_ctor'], '->', r['pt_name'] or r['pt_ctor'], 'ApplyEffect ratio', r['apply_ratio'] and round(r['apply_ratio'], 2))
shared = {}
for op, r in res.items():
    shared.setdefault(r['pt_ctor'], []).append(op)
print('PT constructors shared by several opcodes:', {k: v for k, v in shared.items() if len(v) > 1})
