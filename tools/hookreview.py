# Review sheet of every hook of one EEex Lua file (luahooks.json): hook call, registers / offsets / frame
# references of its code, the BG -> Torment register map, and the BG / Torment sites side by side.
#   python hookreview.py EEex_Sprite_Patch.lua [before] [after]
import sys, json, io, contextlib
import hookview

if __name__ == '__main__':
    name = sys.argv[1]
    before = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    after = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    for e in json.load(open('luahooks.json')):
        if e['file'] != name:
            continue
        print('=' * 140)
        print(f"{e['line']} {e['fn']} {e['label']} args={e.get('args')} bg={e['bg']} pt={e['pt']}")
        print('  regs', e.get('regs'), '| offs', e.get('struct_offsets'), '| frame', e.get('frame_refs'))
        if e.get('frame_map'):
            print('  frame map', {k: v for k, v in e['frame_map'].items()})
        if e['issues']:
            print('  ISSUES', ' ; '.join(e['issues']))
        if e['bg'] and e['pt'] and 'Watchdog' not in e['fn']:
            bg, pt = int(e['bg'], 16), int(e['pt'], 16)
            A, B = hookview.around(hookview.BG, bg, before, after), hookview.around(hookview.PT, pt, before, after)
            for k in range(max(len(A), len(B))):
                x = f'{"*" if A[k].address == bg else " "}{A[k].address:x} {A[k].mnemonic} {A[k].op_str}' if k < len(A) else ''
                y = f'{"*" if B[k].address == pt else " "}{B[k].address:x} {B[k].mnemonic} {B[k].op_str}' if k < len(B) else ''
                print(f'  {x[:62]:62} | {y[:70]}')
