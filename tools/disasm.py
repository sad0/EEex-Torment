# Annotated disassembly of a range: names (bgnames/ptnames/pattern DB), strings, globals.
#   python disasm.py BG|PT <start> <end>
import sys, re, json
import capstone
from ilib import PE, BG_EXE
which, a0, a1 = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3], 16)
pe = PE(BG_EXE) if which == 'BG' else PE('E:/Enhanced Edition/Environnement de test/PTEE (EEex dev)/Torment.exe')
names = {int(k, 16): v for k, v in json.load(open('bgnames.json' if which == 'BG' else 'ptnames.json')).items()}
G = json.load(open('gen_report.json')); R = json.load(open('port2.json'))
if which == 'PT':
    names.update({int(v['addr'], 16): k for k, v in G.items() if isinstance(v, dict) and v.get('addr')})
else:
    names.update({int(v['bg_key'], 16): k for k, v in R.items() if v.get('bg_key')})
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)


def cstr(a):
    o = pe.off(a)
    if o is None:
        return ''
    b = pe.d[o:o + 60].split(b'\0')[0]
    return '"' + b.decode('latin-1') + '"' if len(b) >= 2 and all(32 <= c < 127 for c in b) else ''


for i in md.disasm(pe.tbytes(a0, a1 - a0), a0):
    x = ''
    m = re.search(r'rip \+ (0x[0-9a-f]+)', i.op_str)
    if m:
        a = i.address + i.size + int(m.group(1), 16)
        val = ''
        if 'byte ptr [rip' in i.op_str or 'word ptr [rip' in i.op_str and 'dword' not in i.op_str:
            o = pe.off(a)
            if o is not None:
                n = 1 if 'byte ptr' in i.op_str else 2
                val = f'={int.from_bytes(pe.d[o:o + n], "little"):#x}'
        elif 'dword ptr [rip' in i.op_str and 'cmp' not in i.mnemonic:
            o = pe.off(a)
            if o is not None:
                val = f'={int.from_bytes(pe.d[o:o + 4], "little"):#x}'
        x = f'@{a:x}{val} {cstr(a)} {names.get(a, "")}'
    if i.mnemonic in ('call', 'jmp') and i.op_str.startswith('0x'):
        x = names.get(int(i.op_str, 16), '')
    print(f'{i.address:x} {i.mnemonic:6} {i.op_str:45} {x}')
