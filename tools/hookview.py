# BG / Torment instructions around a pattern label (or explicit rvas), for reviewing hook sites.
#   python hookview.py <label> [before] [after]
#   python hookview.py 0x<bg> 0x<pt> [before] [after]
import sys
from luahooks import addr_of, func_body, BG, PT


def around(pe, a, before, after):
    A = func_body(pe, a)
    k = min(range(len(A)), key=lambda k: abs(A[k].address - a)) if A else 0
    return A[max(0, k - before):k + after + 1]


if __name__ == '__main__':
    args = sys.argv[1:]
    if args[0].startswith('0x'):
        bg, pt = int(args[0], 16), int(args[1], 16); args = args[2:]
    else:
        bg, pt, st, note = addr_of(args[0]); args = args[1:]
        print(st, note)
    before = int(args[0]) if args else 12
    after = int(args[1]) if len(args) > 1 else 8
    A, B = around(BG, bg, before, after), around(PT, pt, before, after)
    for k in range(max(len(A), len(B))):
        x = f'{"*" if A[k].address == bg else " "}{A[k].address:x} {A[k].mnemonic} {A[k].op_str}' if k < len(A) else ''
        y = f'{"*" if B[k].address == pt else " "}{B[k].address:x} {B[k].mnemonic} {B[k].op_str}' if k < len(B) else ''
        print(f'{x[:62]:62} | {y[:70]}')
