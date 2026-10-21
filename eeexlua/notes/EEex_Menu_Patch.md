# EEex_Menu_Patch.lua (Torment review)

BG sites of the extra-DB labels (not in port2.json) were found in Baldur_bg2ee.exe with the v2.7.3.0 extra
patterns: AfterEnabledCheck 0x3d12cf, CheckScrollbarContentHeight 0x3d326f, FixForcedScrollbarDivideByZero2 0x3d356b,
OnResizeWindow()-B3Scale 0x41a942 (FixForcedScrollbarDivideByZero1 0x3d33a1 and CheckApplyTextHardcodedScrollbarPad
0x3d2b62 from InfinityLoader.db). Torment's drawItem (PT 0x44ea70) keeps the uiItem in r13 (PT 0x44ea9f mov r13, rcx;
BG r15). No jump target lies inside any patched byte range (checked for every site below).

| Hook (label) | Verdict | Evidence |
|---|---|---|
| Hook-uiRefreshMenu()-saveMenuStack() | unchanged | PT 0x45a7ac, same prologue as BG 0x3db0ac; EEex.dll call only. |
| Hook-uiRefreshMenu()-restoreMenuStack() | unchanged | PT 0x45a9b6 tail `jmp` (E9), stack_mod 8 as in BG 0x3db2a6. |
| Hook-dimmInit()-uiLoadMenu() | unchanged | PT 0x140ead (BG 0x404fc4): rcx (file buffer, PT rdi) saved / restored by the hook; return value unused (PT 0x140eb2 reloads rcx). |
| Hook-Infinity_InstanceAnimation()-TemplateMenuOverride | unchanged | PT 0x4468cd: same 12 bytes (mov rax, [rbp+8] / mov [rdx+8], rax / mov rax, [rbp+8]), rdx = new item (= rax, PT 0x44682f), [rbp+8] = menu, next instruction reads [rax+0x28]. |
| Hook-Infinity_DestroyAnimation()-TemplateMenuOverride | patched (upstream bug) | PT 0x444634: same 4 + 3 restored bytes. rbx is the item iterator ([rbx+0x20] name, [rbx+0x3a8] next, PT 0x444650 / 0x444654); upstream sets rbx = override uiMenu*. Now rbx = [override+0x28] (uiMenu.items, as PT 0x444634 / 0x4468d9). |
| Hook-saveMenus()-CheckItemSave | unchanged | PT 0x43f72c: short jne + 5 bytes `sub eax, ebp; movsxd rdx, ebp` (relocatable); r14 = &menu.items (uiMenu+0x28) -> [r14-0x28] = uiMenu; rbx = item; rax saved. |
| Hook-RenderListCallback()-drawItem() | patched | PT 0x44aee1: list item in rdi (PT 0x44a5d2 mov rdi, [rcx+0x10], read-only afterwards; BG rsi). drawItem has the same 5 args (5th = menu at [rsp+0x20], PT 0x44ea98). |
| Hook-drawItem()-FixForcedScrollbarDivideByZero1 | unchanged | PT 0x450fbe: `mov eax, [r13+0x1cc]; sub eax, [r13+0x4c]` = 11 relocatable bytes, eax = divisor stored at [rbp-0x80]. |
| Hook-drawItem()-FixForcedScrollbarDivideByZero2 | unchanged | PT 0x451199: `mov dword ptr [rbp+0x28], 0x12; sub eax, [r13+0x4c]` = 11 relocatable bytes. |
| Hook-drawItem()-AfterEnabledCheck | patched | PT 0x44eb2b: 5 restored bytes `movups xmm0, [r13+0x40]` (restored after the hook). Lua arg r15 -> r13. |
| Hook-CChitin::OnResizeWindow()-B3Scale | unchanged | PT 0x4a41af: after SDL_GL_GetDrawableSize (Torment calls SDL_GetWindowSize first, PT 0x4a419a); SCREENWIDTH / HEIGHT already stored (PT 0x4a417b / 0x4a4187); rax and volatile registers rewritten before use. EEex.dll UncapFPS_Hook_OnAfterWindowResized calls EEex_Menu_LuaHook_OnWindowSizeChanged (B3Scale). |
| Hook-continueEditCapture()-ActionHandlerCall | unchanged | PT 0x44c63a: item in rdi (PT 0x44c634 mov ecx, [rdi+0x2f8]). |
| Hook-continueTextCapture()-ActionHandlerCall | unchanged | PT 0x44e3a7: item in rax (PT 0x44e3a1 mov ecx, [rax+0x2f8]). |
| Hook-uiDoFile()-FirstInstruction | unchanged | PT 0x456d60: whole function replaced by EEex.dll Override_uiDoFile. |
| Hook-drawItem()-CheckScrollbarContentHeight | patched (logic) | BG: `cmp r13d, [r15+0x4c]; jle <hidden>` (near). PT 0x450daf `cmp esi, [r13+0x4c]`, PT 0x450db3 short `jg 0x450dc9` (visible); content that fits still shows the scrollbar when the forced-scrollbar expression is true: PT 0x450db5 mov rcx, [r13+0x1b0] (7 bytes), call 0x440500, test eax, eax, PT 0x450dc3 `je 0x45122a` (hidden, near). Upstream's restore 0 on a 2-byte jcc would also overwrite 3 bytes too few. Now two hooks: (1) ConditionalJumpOnSuccess on the jg, restore 7 (the relocatable mov): bVisible = 1, hide -> the je's target (read with EEex_GetJmpInfo); (2) upstream's hook (r13) on the je at label + 0x10, restore 0: success = hidden (bVisible 0), fail = visible (bVisible 1). Byte checks guard both sites. |
| Hook-Infinity_DestroyAnimation()-free() | unchanged | PT 0x44469a: rcx = rbx = item. |
| Hook-drawItem()-CheckApplyTextHardcodedScrollbarPad | patched | PT 0x4504cf: `and ecx, 0x12; sub r8d, ecx; mov [rbp+0x48], r8d` (10 bytes; BG `and eax, 0x10; sub [rbp-0x18], eax`). Area at [rbp+0x40] (x / y / w stored at +0x40 / +0x44 / +0x48). HookNOPs(5) replaces the 10 bytes: store unpadded w, call Menu_Hook_CheckApplyTextScrollbarPad(r13, &area), subtract 2 more when it padded (Torment's pad is 18), keep rdx (scrollbar bam, read at PT 0x4504d9 / 0x4504de). Byte check of the 9 opcode bytes, w offset read from the instruction. |

Label fixes needed: none (all 17 labels verified at the equivalent instruction).

BG-only features: none disabled.

Open questions / couplings:
- EEex.dll Menu_Hook_CheckApplyTextScrollbarPad hard-codes BG's 16-pixel pad; the Lua hook adds Torment's extra 2.
  If EEex.dll is changed to 18 for Torment, drop the `sub ..., 2` here. Its visibility test (`area.h <
  contentHeight`) ignores Torment's forced-scrollbar expression ([item+0x1b0]), so with
  Menu_UniversalScrollbarPadCollapsing a forced scrollbar on content that fits loses its pad.
- CheckScrollbarContentHeight hook (1) jumps straight to Torment's hidden path: with the hook integrity watchdog
  loaded, that exit skips #MANUAL_HOOK_EXIT (same pattern as the reference SetCursor patch).
- B3Scale (EEex_Menu.lua / B3Scale.lua) scales SCREENWIDTH / HEIGHT around a 768-pixel base height; Torment's UI
  base layout needs checking in the UI step.
