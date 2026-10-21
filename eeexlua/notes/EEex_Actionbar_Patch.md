# EEex_Actionbar_Patch.lua (Torment review)

| Hook (label) | Verdict | Evidence |
|---|---|---|
| Hook-CInfButtonArray::SetState()-SaveArg | patched | PT 0x2c8a5c (BG 0x26603d). State argument is in edi (PT 0x2c8a40 mov edi, edx; untouched until the site), BG r15d. Spill slot [rsp+0x70] = rcx home slot of Torment's frame (push rbx/rsi/rdi/r13 + sub 0x48 + ret = 0x70), never accessed by PT SetState. |
| Hook-CInfButtonArray::SetState()-CInfButtonArray::UpdateButtons() | patched | PT 0x2ca37f (BG 0x2675aa): `this` in rbx (PT 0x2ca37c mov rcx, rbx; BG r14) -> `mov rcx, rbx`. Same rsp as SaveArg (fixed frame), so [rsp+0x70] / #LAST_FRAME_TOP(70h) read the saved state. Switch range: PT `lea eax, [rdi-1]; cmp eax, 0x78` (PT 0x2c8ab5), BG 0x71 -> hook uses 78h. UpdateButtons (PT 0x2ca5f0) takes only rcx. |
| Data-CInfButtonArray::SetState()-IndirectJumpTable | used as is | PT 0x2ca438 (121 bytes). Configs 0..30 map to the same states as BG (1..18, 20, 21, 101..114); Torment adds configs 31..37 = states 115..121; the default config is 38 (BG 31). |
| Hook-CInfButtonArray::UpdateButtons()-LastCall | unchanged | PT 0x2cd8cf (__security_check_cookie before the epilogue, BG 0x26a526). The hook clobbers rax (return value: PT eax = r15d, BG 1); no PT caller of UpdateButtons (31 call sites) reads eax afterwards. |
| Hook-CInfButtonArray::OnLButtonPressed()-HasFullThieving | patched | PT 0x2c6e1e (BG 0x2647e6): same 11 bytes (mov rcx, [rax+0x10c8] 7 / je 2 / mov dl, 0x24 2); restored 7 bytes are relocatable; returns to the call at PT 0x2c6e29 (CInfGame SetTempCursor(rcx, dl), body identical to BG 0x265e20). Sprite slot [rsp+0x40] (PT 0x2c6dfc / 0x2c6e3c), BG [rsp+0x48] -> #LAST_FRAME_TOP(40h). Cursor values 0x24 / 0x28 are Torment's own constants at this site. |
| Hook-CAIGroup::IsPartyLeader()-Override | patched (upstream bug) | PT 0x12853a, code identical to BG 0x11ac1a. rbx = leader object id (PT 0x128500 movsxd rbx, [rax+0x10], head node data of m_memberList), not a CGameSprite*: upstream pushes the id as a CGameSprite and EEex_Actionbar_Hook_IsPartyLeader calls sprite:getClass() on it. The hook now resolves the id with CGameObjectArray::GetShare (PT 0x2db2d0, ecx = id, rdx = &out, as PT 0x2c6a37) into rbx (only popped after the site, PT 0x12854d / 0x128555); unresolved -> false. RBX added to the watchdog ignore list. |
| Hook-CScreenWorld::OnKeyDown()-ThievingHotkeyPressSpecialAbilitiesCall | unchanged | PT 0x35d090 (BG 0x2f42c5): rcx = rbx = &m_cButtonArray, edx = button index (movzx edx, al) as in BG; rcx / rdx saved before, after-call code reloads edx / rcx (PT 0x35d095 / 0x35d09a). |

Label fixes needed: none.

BG-only features: none disabled.

Open questions / for other files:
- EEex_Actionbar.lua (not this file): its config documentation and any listener comparing configs must know Torment's extra configs 31..37 (states 115..121) and the default config 38. B3Hotkey's `config == 28` (state 111, internal list) is the same in Torment.
- Torment's state ordinals 1..21 map to PST classes, not BG's class list (EEex_Actionbar_GetState docs).
