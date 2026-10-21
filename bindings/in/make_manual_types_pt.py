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
# Torment signatures of engine functions bound for Lua (tools/argcheck.py; argument values seen at the
# Torment call sites, PTEE AUDIT.md). Lua callers must pass the new arguments (phase 5).
SIG = [
    # CAIObjectType::GetShare(caller, checkBackList, bIgnoreRangeAndLOS): non-zero = range 10000, no LOS
    # check (PT 0x12b340); 21 of 24 callers pass 0
    ('\tCGameObject* GetShare(CGameAIBase* caller, int checkBackList);\n',
     '\tCGameObject* GetShare(CGameAIBase* caller, int checkBackList, int bIgnoreRangeAndLOS);\n'),
    # CGameAIBase::GetTargetShare / GetTargetShareType(byte) forward it (PT 0x1731c0 / 0x173440)
    ('\tCGameObject* GetTargetShare();\n', '\tCGameObject* GetTargetShare(int bIgnoreRangeAndLOS);\n'),
    ('CGameObject* GetTargetShareType(byte type);\n', 'CGameObject* GetTargetShareType(byte type, int bIgnoreRangeAndLOS);\n'),
    # CGameSprite::ReadyOffInternalList takes a button index in Torment (movsx rdx; imul 0x34, PT 0x3da700)
    ('\tvoid ReadyOffInternalList(CButtonData* button, bool firstCall);\n', '\tvoid ReadyOffInternalList(short buttonIndex, bool firstCall);\n'),
    # CProjectile::DecodeProjectile: third value stored in the new projectile (+0x260); CGameSprite::Spell /
    # SpellPoint pass sprite+0x49aa, FireSpell / Swing / UseItem pass 1 (PT 0x27c4a0)
    ('\tstatic CProjectile* DecodeProjectile(ushort wProjectileType, CGameAIBase* pSprite);\n',
     '\tstatic CProjectile* DecodeProjectile(ushort wProjectileType, CGameAIBase* pSprite, ushort nLevel);\n'),
    # CVidFont::GetStringHeight / GetStringLength: extra bool (r9b), callers pass false (PT 0x49b8d0 / 0x49b980)
    ('\t$nobinding int GetStringHeight(const CString* text, int w);\n', '\t$nobinding int GetStringHeight(const CString* text, int w, bool bFlag);\n'),
    ('\t$nobinding int GetStringLength(const CString* str, int w);\n', '\t$nobinding int GetStringLength(const CString* str, int w, bool bFlag);\n'),
    # CAIScript::CAIScript(CResRef): Torment's constructor has no playerscript argument; it calls
    # CAIScript::Read(resref, 0) itself (PT 0x176d80 -> 0x12d240)
    ('$constructor_fake Construct(CResRef cNewResRef, int playerscript);\n', '$constructor_fake Construct(CResRef cNewResRef);\n'),
]
for old, new in SIG:
    assert s.count(old) == 1, old
    s = s.replace(old, new)
open(os.path.join(HERE, 'manual_types_pt.txt'), 'w', encoding='utf-8', newline='\n').write(s)
print('manual_types_pt.txt written')
