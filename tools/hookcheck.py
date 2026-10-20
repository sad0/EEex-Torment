# Semantic check of ported addresses: compare normalized instruction context (BG2 vs Torment)
# around each key and the instruction kind EEex expects at hook labels (call / jcc / jmp).
# Input: port2.json (or final.json). Output: hookcheck.json + text summary.
import sys, re, json, difflib, glob
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from ilib import *

md = Cs(CS_ARCH_X86, CS_MODE_64); md.detail = True
BG, PT = PE(BG_EXE), PE(PT_EXE)

# how EEex Lua uses each label -> expected instruction at the label
USE = {}
for f in glob.glob(REPO + r'\ref\EEex\EEex\copy\**\*.lua', recursive=True):
    for fn, lab in re.findall(r'(EEex_[A-Za-z]+)\(EEex_Label\("([^"]+)"\)', open(f, encoding='utf-8', errors='ignore').read()):
        USE.setdefault(lab, set()).add(fn)


def expect(fns):
    s = ' '.join(fns)
    if 'Call' in s: return 'call'
    if 'ConditionalJump' in s: return 'jcc'
    if 'RelativeJump' in s or 'ForceJump' in s: return 'jmp'
    return None


def ctx(pe, rva, before=6, after=10):
    fs = pe.fstart(rva)
    ins = list(md.disasm(pe.tbytes(fs, rva - fs + 200), fs))
    k = next((i for i, x in enumerate(ins) if x.address <= rva < x.address + x.size), None)
    if k is None: return [], None
    return ins[max(0, k - before):k + after], ins[k]


def norm(i):
    op = re.sub(r'0x[0-9a-f]+', 'N', i.op_str)
    return f'{i.mnemonic} {op}'


def check(bg, pt):
    a, ia = ctx(BG, bg); b, ib = ctx(PT, pt)
    if not a or not b: return None
    na, nb = [norm(x) for x in a], [norm(x) for x in b]
    ratio = difflib.SequenceMatcher(None, na, nb).ratio()
    # exact (constants included) equality outside rel/rip fields: shows struct-offset drift
    drift = [(x.mnemonic + ' ' + x.op_str, y.mnemonic + ' ' + y.op_str) for x, y in zip(a, b)
             if norm(x) == norm(y) and x.op_str != y.op_str and 'rip' not in x.op_str
             and not (x.group(1) or x.group(2))]
    return {'ratio': round(ratio, 2), 'same_ins': norm(ia) == norm(ib), 'bg': norm(ia), 'pt': norm(ib),
            'drift': drift[:6], 'bg_ctx': [f'{x.address:x} {x.mnemonic} {x.op_str}' for x in a],
            'pt_ctx': [f'{x.address:x} {x.mnemonic} {x.op_str}' for x in b]}


if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else 'port2.json'
    R = json.load(open(src)); out = {}
    for n, r in R.items():
        if r.get('status') != 'voted' or not r.get('votes'): continue
        bg = int(r['bg_key'], 16); pt = int(r['votes'][0][0], 16)
        c = check(bg, pt)
        if not c: continue
        e = expect(USE.get(n, ()))
        if e:
            c['expect'] = e
            m = c['pt'].split()[0]
            c['expect_ok'] = (e == 'call' and m == 'call') or (e == 'jcc' and m.startswith('j') and m != 'jmp') or (e == 'jmp' and m == 'jmp')
        out[n] = c
    json.dump(out, open('hookcheck.json', 'w'), indent=1)
    bad = [(n, c['ratio'], c['bg'], c['pt']) for n, c in out.items() if c['ratio'] < 0.7 or not c['same_ins'] or c.get('expect_ok') is False]
    print(len(out), 'checked;', len(bad), 'suspicious')
    for b in bad: print(b)
