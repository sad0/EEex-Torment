# EEex_Keybinds.lua: Torment's CGameSprite::ReadyOffInternalList takes an index into the sprite's CButtonData array
# at +0x3610 (PT 0x3da700: movsx rax, dx; imul 0x34), while GetInternalButtonList builds its list from the CPtrList at
# +0x4c30 (PT 0x3c6c3c): no proven mapping from a list entry to that index, so casting off the internal (op214)
# list from a keybind is not available in Torment (same as patches/B3Hotkey.py); normal quick-spell keybinds work.
PATCHES = [
    ('''		if bOffInternal then
			sprite:ReadyOffInternalList(buttonData, false)''',
     '''		if bOffInternal then
			do return true end -- EEex-PTEE: not available in Torment (ReadyOffInternalList takes an array index)
			sprite:ReadyOffInternalList(buttonData, false)'''),
]
