# Probe the Torment offset of specific fields: every recorded BG access site of the field
# (field_sites.json, from fieldmap.py) is located in the mapped PT function (exact alignment,
# else anchor2) and the PT instruction's displacement votes for the field offset.
# Usage: python bindings/fieldprobe.py Struct.field [Struct.field ...]   (run from tools/)
import sys, os, json, re, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone import x86_const as X
from fmap import BG, PT, align
from local import anchor2
import bindings.bgtypes as T

md = Cs(CS_ARCH_X86, CS_MODE_64); md.detail = True
SITES = json.load(open('bindings/field_sites.json'))


def mem(i):
    for op in i.operands:
        if op.type == X.X86_OP_MEM:
            return op
    return None


def field_info(s, f):
    for fl in T.all_fields(s):
        if fl.name == f:
            return fl
    return None


def probe(s, f, verbose=True):
    fl = field_info(s, f)
    if not fl:
        print(s, f, 'unknown field'); return None
    votes = collections.Counter(); shown = 0
    # sites typed as s or any class derived from s
    keys = [k for k in SITES if s in chain(k.split('|')[0])]
    for k in keys:
        o = int(k.split('|')[1], 16)
        if not (fl.off <= o < fl.off + max(fl.size, 1)):
            continue
        rel = o - fl.off
        for bgf, ptf, ins, ob, op_ in SITES[k]:
            bgf, ptf, ins = int(bgf, 16), int(ptf, 16), int(ins, 16)
            op_ = int(op_, 16) if op_ else (0 if ob in (None, '0x0') else None)
            if op_ is None:
                continue
            mp, r, _, _ = align(bgf, ptf)
            pa = mp.get(ins)
            how = 'align'
            if pa is None:
                a2 = anchor2(BG.rfunc(ins)[0] if BG.rfunc(ins) else bgf, ins, ptf)
                if not a2 or a2[1] < 0.5:
                    continue
                pa, how = a2[0], f'anchor2({a2[1]:.2f})'
            bi = next(iter(md.disasm(BG.tbytes(ins, 16), ins)), None)
            pi = next(iter(md.disasm(PT.tbytes(pa, 16), pa)), None)
            if not bi or not pi or bi.mnemonic != pi.mnemonic:
                continue
            bm, pm = mem(bi), mem(pi)
            if not bm or not pm or pm.mem.index != bm.mem.index:
                continue
            cand = op_ + pm.mem.disp - rel
            votes[cand] += 1
            if verbose and shown < 6:
                shown += 1
                print(f'   {ins:x} {bi.mnemonic} {bi.op_str:40} | {pa:x} {pi.mnemonic} {pi.op_str:40} -> {cand:#x} [{how}]')
    print(f'{s}.{f} bg={fl.off:#x} votes={[(hex(a), c) for a, c in votes.most_common(4)]}')
    return votes


def chain(s):
    out = []
    while s and s in T.structs and len(out) < 20:
        out.append(s)
        st = T.structs[s]
        s = st.bases[0] if st.bases else None
    return out


if __name__ == '__main__':
    for a in sys.argv[1:]:
        s, f = a.split('.', 1)
        probe(s, f)
