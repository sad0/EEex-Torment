# Integrity checks on gen_report.json results (no DB access needed):
#  - function-start keys must land on PT function starts
#  - mid-function keys: same normalized instruction at key (BG vs PT)
#  - rel32 code targets must be PT function starts
#  - distinct entries resolving to the same PT address (except known aliases)
import json, re, collections
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from ilib import *
from gen import bg_final, upentry

md = Cs(CS_ARCH_X86, CS_MODE_64)
BG, PT = PE(BG_EXE), PE(PT_EXE)
G = json.load(open('gen_report.json')); R = json.load(open('port2.json'))


def is_fstart(pe, a):
    f = pe.rfrag(a)
    if f and f[0] == a:
        return True
    p = pe.tbytes(a - 1, 1)
    return p in (b'\xcc', b'\x90', b'\xc3')


def norm(pe, a):
    i = next(iter(md.disasm(pe.tbytes(a, 16), a)), None)
    return (i.mnemonic + ' ' + re.sub(r'0x[0-9a-f]+', 'N', i.op_str)) if i else None


issues = []
for n, r in G.items():
    if r['status'] != 'ported':
        continue
    kind = r.get('kind') or classify(upentry(n).get('Operations', ''))[0]
    a = int(r['addr'], 16)
    bk = int(R[n]['bg_key'], 16) if n in R and 'bg_key' in R[n] else None
    bf = bg_final(n)
    if kind == 'A' and bk is not None:
        if is_fstart(BG, bk) and not is_fstart(PT, a):
            issues.append((n, 'BG fn start, PT not', hex(a), r['conf'], r['method'][:30]))
        elif not is_fstart(BG, bk):
            nb, np_ = norm(BG, bk), norm(PT, a)
            if nb and np_ and nb.split()[0] != np_.split()[0]:
                issues.append((n, f'insn {nb} vs {np_}', hex(a), r['conf'], r['method'][:30]))
    if bf is not None and BG.tva <= bf < BG.tva + BG.tsize and kind == 'B':
        if is_fstart(BG, bf) and not is_fstart(PT, a):
            issues.append((n, 'B target not PT fn start', hex(a), r['conf'], r['method'][:30]))
by = collections.defaultdict(list)
for n, r in G.items():
    if r['status'] == 'ported':
        by[r['addr']].append(n)
for a, ns in by.items():
    base = {re.sub(r'^(Hardcoded_|Hook-)|\(\)-FirstInstruction$|::FirstInstruction', '', x) for x in ns}
    if len(ns) > 1 and len(base) > 1 and not all(x.startswith(('Hardcoded_', 'lua', 'tolua')) for x in ns):
        issues.append((','.join(ns), 'shared address', a, '', ''))
for i in issues:
    print(i)
print(len(issues), 'issues')
