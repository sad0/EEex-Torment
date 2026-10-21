# B3Hotkey.lua: no hooks / labels, but one engine call whose Torment signature differs.
# CGameSprite::ReadyOffInternalList takes a button index in Torment (PT 0x3da700: movsx rax, dx; imul rdx, rax,
# 0x34; add rdx, [rcx+0x3610], i.e. an index into the sprite's quick-spell CButtonData array, which
# ~CGameSprite frees with [rcx+0x3608] / [rcx+0x3618], PT 0x3b3ccd..0x3b3d11), not a CButtonData* (BG 0x3686a0
# copies *rdx). The bindings declare ReadyOffInternalList(short buttonIndex, bool) (manual_types_pt.txt), so
# `sprite:ReadyOffInternalList(buttonData, false)` raises a tolua argument error, and there is no proven mapping
# from a GetInternalButtonList() entry to that index. B3Hotkey_CastOffInternal (two-step casts through an op214
# list, only used by the commented-out examples) is disabled; B3Hotkey_CastTwoStep's second step then does nothing.
PATCHES = [
    ('''function B3Hotkey_CastOffInternal(resref)
''',
     '''function B3Hotkey_CastOffInternal(resref)
	-- EEex-PTEE: Torment's ReadyOffInternalList takes a quick-spell slot index (PT 0x3da700), not a CButtonData
	do return false end
'''),
]
