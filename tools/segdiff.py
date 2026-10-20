# Normalized instruction diff of two address ranges (BG vs PT), printing only differing blocks.
#   python segdiff.py <bg start> <bg end> <pt start> <pt end>
import sys, difflib
import capstone
from ilib import PE, BG_EXE
from fmap import norm
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
BG = PE(BG_EXE); PT = PE('E:/Enhanced Edition/Environnement de test/PTEE (EEex dev)/Torment.exe')
b0, b1, p0, p1 = (int(x, 16) for x in sys.argv[1:5])
a = list(md.disasm(BG.tbytes(b0, b1 - b0), b0)); b = list(md.disasm(PT.tbytes(p0, p1 - p0), p0))
na = [norm(i) for i in a]; nb = [norm(i) for i in b]
for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, na, nb, autojunk=False).get_opcodes():
    if tag == 'equal':
        continue
    print(f'--- {tag}')
    for i in a[i1:i2]:
        print(f'  BG {i.address:x} {i.mnemonic} {i.op_str}')
    for i in b[j1:j2]:
        print(f'  PT {i.address:x} {i.mnemonic} {i.op_str}')
