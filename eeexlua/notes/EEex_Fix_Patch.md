# EEex_Fix_Patch.lua (Torment review)

Patch: `eeexlua/patches/EEex_Fix_Patch.py` (12 replacements, `python build.py` OK). PT = Torment.exe RVA, BG = BG2EE RVA.

## Hooks and label uses

| # | Label / site | Verdict | Evidence |
|---|---|---|---|
| 1 | `Hook-CGameSprite::CheckCombatStatsWeapon()-NonZeroWeapProfCall` (AfterCall) | **patched** (r14 -> rbx) | PT 0x3bd35c call CString::Format (BG 0x34ccb3). Sprite: BG r14, PT rbx (0x3bd01b `mov rbx, rcx`, 0x3bd36e `[rbx+0x794]`). r12w = proficiency level in both (PT 0x3bd281). `[rbp+0x50]` = r8d home (bOffHand), same prologue (PT 0x3bcff5, used at 0x3bd0a7). rax clobber: next use is a new call (0x3bd369). EEex.dll body is empty on PT (no SPEED column); hook kept so the call path is correct. |
| 2 | `Hook-CGameEffectSaveVsDeath::ApplyEffect()-ImmediateSaveWriteOffset` (EEex_WriteU32) | **not portable: guarded** (`EEex_TryLabel`) | Label unsupported (PATTERNS.md): PT op33 is a different 6-case implementation without BG's `sub [rdi+1136h]`; bug absent. |
| 3 | `Hook-CGameEffectSetSnare::ApplyEffect()-SetSnareTrapCapCompareJmp` (EEex_WriteU8 0x7E -> 0x7C) | unchanged | PT 0x1e3809 short `jle` (0x7E) after `cmp ebx, eax`, ebx = [rax+0x1070]+[rax+0x106c] (BG +0x1050/+0x104c), eax = TRAPLIMT limit (call 0x2a7600). Same off-by-one, same fix. |
| 4 | `Hook-CGameEffect::CheckAdd()-FixSpellImmunityShouldSkipItemIndexing` (CondJumpOnFail) | **not portable: guarded** | Label unsupported: PT CheckAdd (0x1eba60) has a single immunity lookup (0x1ebfd9 call 0x21bd30 = BG 0x1f8c90) then shows `[rbx+8]` directly (0x1ebfef); no 0xF00074/0xF00080 test, no source item-list indexing: bug absent. |
| 5 | `Hook-CGameSprite::AddSpecialAbility()-LastCall` (AfterCall, Lua) | unchanged | PT 0x3ba447 (BG 0x349bc7), identical function: push rbx/rbp/rsi, sub rsp 0x60, rsi = sprite (0x3ba267), CSpell at [rsp+0x48] (0x3ba290, 0x3ba442), LAST_FRAME_TOP(48h) valid. Epilogue after the call reads nothing volatile. |
| 6 | `Hook-CGameSprite::Spell()-CheckDirectionJmp` (CondJumpOnFail, restore 3) | **patched** (point) | PT 0x42c462 short `je` (BG 0x3b455f). Restored `cmp r15, rbx` = 3 bytes (PT 0x42c464), relocatable. rbx = sprite. BG point = r14 = r15+0xC; PT computes it in rax/[rbp-0x40] (0x42c44c/0x42c453) and rax is the GetDirection result at the hook -> `lea rdx, [r15+0xC]` (r15 live, used by the restored cmp). Fail path (0x42c469..) and success target (0x42c4c4) read no volatile register before writing it (0x42c47e reloads [rbp-0x40]). |
| 7 | `Hook-CGameSprite::SpellPoint()-CheckDirectionJmp` (CondJumpOnFail, restore 5) | **patched** (frame slot) | PT 0x42f895 short `je` (BG 0x3b5fe2). Restored `mov ecx, 0x18` = 5 bytes. Point: BG [rsp+0x60], PT [rsp+0x70] (0x42f885 GetDirection arg, 0x42f8ac). rbx = sprite. Success target 0x42f8ec (saves rsi/r14 there: PT shrink-wrap, same state on the forced path). |
| 8 | `Hook-CGameSprite::Spell()-ApplyCastingEffect()` (AfterCall) | unchanged | PT 0x42d140 call 0x3fb660 = ApplyCastingEffect (fmap of BG 0x387930; PT passes a 5th stack arg, irrelevant after the call). rbx = sprite (0x42d13d). After: rdx/r8/rcx reloaded, esi nonvolatile. |
| 9 | `Hook-CGameSprite::SpellPoint()-ApplyCastingEffect()` (AfterCall) | unchanged | PT 0x43065b, same: rbx = sprite (0x430658), no volatile read after. |
| 10 | `Hook-CRuleTables::IsProtectedFromSpell()-CompareStatCall` (BeforeCall) | **patched** (r13w -> r12w) | PT 0x2ab3df call Compare 0x299e20 (BG 0x23a6b0, identical code + jump table, relations 0..5 same). PT registers: stat id r12 (0x2aac85, 0x2ab3c4 `movzx edx, r12w`), constant r13d -> r8d, relation r15d -> r9d; edx = GetAtOffset result. return_skip continues at `jmp 0x2aad9c` (epilogue, eax = result). r11 scratch: dead. |
| 11 | `Hook-CGameEffectApplyEffectEquipItem::ApplyEffect()-CheckRetVal` (BeforeCondJump, restore 0) | unchanged | PT 0x1c103e near `je` (6 bytes, as BG 0x1a6f8e) after `test ax, ax` of FindItemPersonal (PT 0x3c4da0). PT FindItemPersonal is restructured but still returns -1 (0x3c4f39 `mov r13d, -1` -> `movzx eax, r13w`) on failure, slot otherwise: `cmp ax, -1` correct. |
| 12 | `Hook-CGameEffect::CheckAdd()-FixShouldTransformSpellImmunityStrref` (+`...Body`, `...Else`) (AfterRestore) | **not portable: guarded** | Labels unsupported (same CheckAdd block, see #4): PT always passes the immunity's own strref (0x1ebfef), so neither v2.6 regression (op206 param1 only for 0xF00074/80, op232/256 message) exists. |
| 13 | `Hook-CGameArea::AddClairvoyanceObject(CGameSprite*,CPoint,int)-FirstInstruction` (JITAt) | unchanged | PT 0x18fc60 identical prologue; = PSTEE_VisMapTest.lua (in-game tested). |
| 14 | `Hook-CGameSprite::CheckIfVisible()-FirstInstruction` (JITAt) | unchanged | PT 0x3be370; same as VisMapTest. |
| 15 | `Hook-CGameSprite::SetVisualRange()-FirstInstruction` (JITAt) | unchanged | PT 0x42bd70; same as VisMapTest. |
| 16 | `Hook-CVisibilityMap::AddCharacter()-FirstInstruction` (JITAt) | unchanged | PT 0x2b7a30; same as VisMapTest. |
| 17 | `Hook-CVisibilityMap::IsCharacterIdOnMap()-FirstInstruction` (JITAt) | unchanged | PT 0x2b88c0, byte-identical 31-byte leaf (BG 0x256780). |
| 18 | `Hook-CVisibilityMap::RemoveCharacter()-FirstInstruction` (JITAt) | unchanged | PT 0x2b8bd0; same as VisMapTest. |
| 19 | `Hook-CVisibilityMap::UpDate()-FirstInstruction` (JITAt) | unchanged | PT 0x2b95e0; same as VisMapTest. |
| 20 | `Hook-CVisibilityMap::Construct()-FirstInstruction` (BeforeRestore 0,5,5, stack_mod 8) | unchanged | PT 0x2b7680: `mov rax, rsp` (3) + `push rbx` + `push rbp` = 5 bytes, relocatable; rax computed after the restore. Same as VisMapTest. |
| 21 | `Hook-CVisibilityMap::Destruct()-FirstInstruction` (BeforeRestore, stack_mod 8) | **patched** (5,5 -> 6,6) | PT 0x2b79d0: `push rsi` (40 56) + `sub rsp, 0x20` (48 83 EC 20) = 6 bytes; BG starts with a 5-byte `mov [rsp+18h], rbx`. Restoring 5 bytes would copy half of `sub rsp, 0x20` and return into its middle (0x2b79d5): crash on the first vismap destruction. Function confirmed: PT body = BG's second half (frees the 15 trees at +0x60; BG's extra +0x68 array is absent in PT). **PSTEE_VisMapTest.lua has the same 5,5 bug** (see open questions). |
| 22 | `Hook-CGameSprite::ProcessEffectList()-FirstRandCall` (BeforeCall) + `-AfterRandCalls` (jmp) + `IgnoreRegistersForInstance` | unchanged | PT 0x423528..0x423613: identical 9 rand blocks writing [rsi+0x49a0..0x49a8] (BG +0x4c80..), skipped `mov edx, [rsi+0x48]` / `mov edi, r12d` identical (PT 0x4235f9 / 0x423601). After 0x423613: rax/rcx reloaded, edx consumed by call 0x2db140. |
| 23 | `Hook-CChitin::SynchronousUpdate()-FirstInstruction` (JITAt) | unchanged | PT 0x4a6120; BG/PT whole function ratio 1.00 (AUDIT: reimplementation valid). |
| 24 | `Hook-uiKillCapture()-FirstInstruction` (BeforeRestore 0,6,6, stack_mod 8) | unchanged | PT 0x4585f0: `push rbx` (40 53) + `sub rsp, 0x20` = 6 bytes, relocatable (BG `sub rsp, 0x28; xor eax, eax` = 6). Note: PT's own uiKillCapture already calls stopEditCapture (0x4562e0) when no screen keyboard and the capture callback is 0x44c590 (BG 0x3cf490, presumably the edit-capture handler); stopEditCapture zeroes that callback (0x4564ba, same 0x7b8290 struct), so EEex's earlier call never causes a double stop. |
| 25 | `Hook-uiEventMenuStack()-FirstInstruction` (JITAt) | unchanged | PT 0x457b40 (fmap of BG 0x3d8b10); EEex.dll override rewritten for PT (AUDIT). |
| 26 | `EEex_CScreenMap.VFTable.reference_OnLButtonDblClk` (vtable write, .rdata RW) | unchanged | `CScreenMap::VFTable` PT 0x63fe30, CWarp::vtbl slot 28 = OnLButtonDblClk in the PT-order header, slot content PT 0x33b770 (`pActiveEngine->OnLeftPanelButtonClick(0)`, AUDIT). Torment.exe has a `.rdata` section containing it. Label `CScreenMap::Override_OnLButtonDblClk` = EEex.dll export. |
| 27 | `Hook-CGameText::Render()-FirstInstruction` (JITAt) | **not portable: disabled** (commented out) | PT 0x215600 is a different renderer (similarity 0.11, AUDIT); EEex.dll's Override_Render is a log-once no-op on PT, so the jump would remove all floating text. |
| 28 | `Hook-bsearchrange()-FirstInstruction` (JITAt) | unchanged | PT 0x4879b0, BG/PT ratio 1.00 (143/143). |
| 29 | `Hook-CGameEffectPolymorph::ApplyEffect()-FormToFormUnequipAllBugJne` (2 NOPs) | unchanged | PT 0x1d95b5 short `jne` (2 bytes). `mov edx, esi` (0) / `cmp [rbx+0x1088], esi` / `jne` / `mov edx, edi` (1): esi = 0 (0x1d9580), edi = 1 (0x1d9459, not reassigned on this path); [rbx+0x1088] = derived stats 0xfe8 + 0xa0 = m_bPolymorphed (stat 59, PT GetAtOffset `[rcx+0xa0]`). NOPs force UnequipAll(animationOnly=1) as upstream. |

Also used: `EEex_OffsetOf("CGameSprite.m_derivedStats.m_nSaveVSDeath")` (only inside guarded #2, field exists in PT header).

## Label fixes needed
None (all ported labels sit at the equivalent instruction; the 4 unsupported CheckAdd/op33 labels are guarded).

## BG-only fixes that cannot work in Torment
- op33 immediate save target (#2), op206/318/324 item indexing (#4), op206/232/256 strref transform (#12): the bugs do not exist in Torment's code; guarded with `if EEex_TryLabel(...) then ... end` so the file loads and the fix is skipped.
- CGameText::Render zoom fix (#27): not installed (different Torment routine).
- WSPECIAL SPEED column (#1): hook installed with the Torment register, but EEex.dll does nothing (Torment's WSPECIAL.2DA has no SPEED column).

## Cross-file notes
- `EEex_Fix.lua` `EEex_Fix_Private_SignedSplprotStatIDs` (used by #10): checked against PT CDerivedStats::GetAtOffset (0x15f1f0): for every stat id 1..202 the load kind (movsx word / movzx / dword) is the same as BG's (0x151bc0), except 146, which upstream already excludes. The list is valid as is for Torment (signedness by id; Torment's DMWW reuse of 166+ keeps the same storage types).
- `EEex_Fix.lua` Lua callbacks of #5/#6/#8: `CMessageSetDirection` (VFTable PT 0x622a10, same 0x18-byte layout built inline at PT 0x42c469) and `CGameSprite::CheckQuickLists` (PT 0x3bebd0) are ported; signatures to be checked by the EEex_Fix.lua review.

## Open questions
1. `bindings/test/PSTEE_VisMapTest.lua` installs CVisibilityMap::Destruct with restore 5,5: in Torment that splits `sub rsp, 0x20` and should crash the first time a visibility map is destroyed (area unload, load game, quit). Was that path exercised in the phase 4d test? The test file should use 6,6 like this patch.
2. CheckDirectionJmp fixes (#6/#7) depend on EEex_Fix.lua's Lua side (casting-glow flag in UDAux, CMessageSetDirection construct); in-game test: cast at a target while facing an odd direction and get hit (disruption).
