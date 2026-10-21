# B3Hotkey.lua (Torment review)

No hooks or labels. One engine call with a different Torment signature (brief point 5):

| Item | Verdict | Evidence |
|---|---|---|
| sprite:ReadyOffInternalList(buttonData, false) in B3Hotkey_UseCGameButtonList (via B3Hotkey_CastOffInternal) | not portable, disabled | PT 0x3da700 takes a short index: `movsx rax, dx; imul rdx, rax, 0x34; add rdx, [rcx+0x3610]` (0x34 = sizeof(CButtonData); [sprite+0x3610] is one of three CButtonData arrays freed by ~CGameSprite at PT 0x3b3ccd..0x3b3d11, a quick-spell list). BG 0x3686a0 copies a CButtonData*. Bindings: `ReadyOffInternalList(short buttonIndex, bool firstCall)`, so passing a CButtonData raises a tolua error. B3Hotkey_CastOffInternal now returns false at once. |

Unaffected: GetQuickButtons(2 / 4, false), ReadySpell(CButtonData*, false) (PT 0x3daa00 copies the pointer like BG), CInfGame OnPortraitLDblClick / SelectCharacter / SelectToolbar / UnselectAll, OnActionButtonClickGround, virtual_OnActionButton / OnPortraitLClick (bindings). Actionbar config 28 = state 111 in Torment too.

Open questions:
- Label check: PT 0x3da700 behaves like BG ReadyOffInternalList's body (same tail: PT 0x3da765 call 0x3da0c0 / test bl / test eax, BG 0x3686f0 call 0x367f50 / test bl / test eax) but takes a quick-slot index; its PT callers are CInfButtonArray::OnLButtonPressed (PT 0x2c6a4d, index = button id - 0x1a) and a quick-slot handler next to CGameSprite::ReadyItem (PT 0x2c7fd6). If Torment has a separate CButtonData* variant of "ready off internal list", the label should point to it; otherwise op214-style two-step casts cannot be driven from Lua without mapping a GetInternalButtonList() entry to its slot index.
- Hotkey examples use BG spell resrefs (SPWI112 etc.); the default hotkey table is empty.
