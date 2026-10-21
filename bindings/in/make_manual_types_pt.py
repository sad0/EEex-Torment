# Torment copy of upstream generate_bindings/in/manual_types.txt (inline engine helpers).
# CMessageAddEffect has no m_CommType in PTEE (Run/Unmarshal: m_noSave at 0x18), so Construct()
# must not write it. CInfinity::SetZoom has Torment's signature. Writes bindings/in/manual_types_pt.txt.
import os
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, r'..\..\ref\InfinityLoader\Core-Shared-Files\generate_bindings\in\manual_types.txt')
s = open(SRC, encoding='utf-8').read()
old = '\t\tm_CommType = commType;\n'
assert s.count(old) == 1, 'upstream changed'
s = s.replace(old, '\t\t// EEex-PTEE: no m_CommType in Torment\'s CMessageAddEffect\n')
# Torment's CInfinity::SetZoom takes a third argument (PT 0x3096b0: bForce, r8b): without it, "Zoom Lock"
# snaps the zoom back to the option value unless the world screen is auto-zooming. Vanilla callers pass false.
old = '\tvoid SetZoom(float fZoom);\n'
assert s.count(old) == 1, 'upstream changed'
s = s.replace(old, '\tvoid SetZoom(float fZoom, bool bForce);\n')
open(os.path.join(HERE, 'manual_types_pt.txt'), 'w', encoding='utf-8', newline='\n').write(s)
print('manual_types_pt.txt written')
