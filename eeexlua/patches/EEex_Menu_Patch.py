# EEex_Menu_Patch.lua: Torment UI hook sites (tools/hookreview.py, hookview.py; BG sites of the extra-DB labels
# found with the v2.7.3.0 extra patterns: AfterEnabledCheck 0x3d12cf, CheckScrollbarContentHeight 0x3d326f,
# FixForcedScrollbarDivideByZero2 0x3d356b, OnResizeWindow()-B3Scale 0x41a942).
# Reviewed without a change: uiRefreshMenu saveMenuStack (PT 0x45a7ac, same prologue, EEex.dll call) /
# restoreMenuStack (PT 0x45a9b6, tail jmp), dimmInit()-uiLoadMenu (PT 0x140ead; rcx saved / restored by the hook,
# return value unused), Infinity_InstanceAnimation()-TemplateMenuOverride (PT 0x4468cd: same 12 bytes, rdx = new
# item, [rbp+8] = menu, [rax+0x28] items), saveMenus()-CheckItemSave (PT 0x43f72c: short jne + `sub eax, ebp; movsxd rdx, ebp`; r14 = &menu.items
# (uiMenu+0x28, as in BG), rbx = item, rax saved), drawItem FixForcedScrollbarDivideByZero1/2 (PT 0x450fbe /
# 0x451199: same 11 restored bytes, eax = divisor), OnResizeWindow()-B3Scale (PT 0x4a41af, after
# SDL_GL_GetDrawableSize; rax / volatile registers rewritten before use), continueEditCapture (PT 0x44c63a, item in
# rdi: PT mov ecx, [rdi+0x2f8]) / continueTextCapture (PT 0x44e3a7, item in rax: PT mov ecx, [rax+0x2f8]) action
# handler calls, uiDoFile()-FirstInstruction (PT 0x456d60, EEex.dll override), Infinity_DestroyAnimation()-free()
# (PT 0x44469a, rcx = rbx = item).
PATCHES = [
    # Infinity_DestroyAnimation()-TemplateMenuOverride (PT 0x444634, same bytes as BG 0x3c7b94): rbx is the item
    # iterator of the template search (restored `mov rbx, [rcx+0x28]` = menu.items; the loop reads item fields
    # [rbx+0x20] name and [rbx+0x3a8] next, PT 0x444650 / 0x444654). Upstream stores the override uiMenu* itself in
    # rbx, so an override would walk a uiMenu as if it were a uiItem (upstream bug, BG too). Use the override menu's
    # first item (uiMenu+0x28, as PT 0x4468d9 / 0x444634 read it).
    ('''			mov rbx, rax ; Override menu''',
     '''			mov rbx, qword ptr ds:[rax+0x28] ; Override menu ; EEex-PSTEE: its first item (uiMenu.items, PT 0x444634)'''),
    # RenderListCallback()-drawItem() (PT 0x44aee1): the list item is in rdi (PT 0x44a5d2 mov rdi, [rcx+0x10], only
    # read afterwards; BG rsi). drawItem has the same 5 arguments (PT 0x44ea98 reads the 5th, menu, at [rbp+0x3b0]).
    ('''				mov qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-40)], rsi''',
     '''				mov qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-40)], rdi ; EEex-PSTEE: Torment keeps the list in rdi (PT 0x44a5d2)'''),
    # drawItem()-AfterEnabledCheck (PT 0x44eb2b): the 5 restored bytes are `movups xmm0, [r13+0x40]`; Torment's
    # drawItem keeps the uiItem in r13 (PT 0x44ea9f mov r13, rcx; BG r15).
    ('''					function(rspOffset) return {"mov qword ptr ss:[rsp+#$(1)], r15", {rspOffset}, "#ENDL"}, "uiItem" end,''',
     '''					function(rspOffset) return {"mov qword ptr ss:[rsp+#$(1)], r13", {rspOffset}, "#ENDL"}, "uiItem" end, -- EEex-PSTEE: r13'''),
    # drawItem()-CheckScrollbarContentHeight: BG `cmp r13d, [r15+0x4c]; jle <hidden>` (near). Torment
    # (PT 0x450daf cmp esi, [r13+0x4c]) jumps with a short `jg <visible>` (PT 0x450db3 -> 0x450dc9), and when the
    # content fits it still shows the scrollbar if the item's forced-scrollbar expression ([r13+0x1b0]) is true:
    # PT 0x450db5 mov rcx, [r13+0x1b0] (7 bytes); call; test eax, eax; PT 0x450dc3 je <hidden> (near, 0x45122a).
    # Upstream's 0-byte restore would also be 3 bytes short for a 2-byte jcc. Two hooks give EEex.dll Torment's
    # final decision: (1) jg success (content taller -> visible): ask with bVisible = 1, hide -> Torment's hidden
    # path; (2) the je, with upstream's exact logic (success = hidden, fail = visible).
    ('''	EEex_HookConditionalJumpWithLabels(EEex_Label("Hook-drawItem()-CheckScrollbarContentHeight"), 0, {
		{"hook_integrity_watchdog_ignore_registers_0", {''',
     '''	-- EEex-PSTEE: Torment's check is a short `jg <visible>` followed by the forced-scrollbar test
	-- (mov rcx, [r13+0x1b0]; call; test eax, eax; je <hidden>), see eeexlua/notes/EEex_Menu_Patch.md
	local pstee_scrollbarCheck = EEex_Label("Hook-drawItem()-CheckScrollbarContentHeight")
	if EEex_ReadU8(pstee_scrollbarCheck) ~= 0x7F or EEex_ReadU8(pstee_scrollbarCheck + 0x2) ~= 0x49
		or EEex_ReadU8(pstee_scrollbarCheck + 0x10) ~= 0x0F or EEex_ReadU8(pstee_scrollbarCheck + 0x11) ~= 0x84
	then
		EEex_Error("Unexpected instructions at [Hook-drawItem()-CheckScrollbarContentHeight] (EEex-PSTEE)")
	end
	local _, pstee_scrollbarHidden = EEex_GetJmpInfo(pstee_scrollbarCheck + 0x10)

	EEex_HookConditionalJumpOnSuccessWithLabels(pstee_scrollbarCheck, 7, {
		{"pstee_scrollbar_hidden", pstee_scrollbarHidden},
		{"hook_integrity_watchdog_ignore_registers", {
			EEex_HookIntegrityWatchdogRegister.RAX, EEex_HookIntegrityWatchdogRegister.RCX, EEex_HookIntegrityWatchdogRegister.RDX,
			EEex_HookIntegrityWatchdogRegister.R8, EEex_HookIntegrityWatchdogRegister.R9, EEex_HookIntegrityWatchdogRegister.R10,
			EEex_HookIntegrityWatchdogRegister.R11
		}}},
		{[[
			mov rcx, r13                                         ; pItem
			mov rdx, 1                                           ; bVisible
			call #L(EEex::Fix_Hook_OnUIItemCheckRenderScrollbar)
			test al, al
			jz #L(pstee_scrollbar_hidden)
		]]}
	)

	EEex_HookConditionalJumpWithLabels(pstee_scrollbarCheck + 0x10, 0, {
		{"hook_integrity_watchdog_ignore_registers_0", {'''),
    ('''			mov rcx, r15                                         ; pItem
			mov rdx, 1                                           ; bVisible''',
     '''			mov rcx, r13                                         ; pItem ; EEex-PSTEE: r13
			mov rdx, 1                                           ; bVisible'''),
    ('''			mov rcx, r15                                         ; pItem
			xor rdx, rdx                                         ; bVisible''',
     '''			mov rcx, r13                                         ; pItem ; EEex-PSTEE: r13
			xor rdx, rdx                                         ; bVisible'''),
    # drawItem()-CheckApplyTextHardcodedScrollbarPad (PT 0x4504cf): Torment keeps the item width in r8d and applies
    # an 18-pixel pad: `and ecx, 0x12; sub r8d, ecx; mov [rbp+0x48], r8d` (83 E1 12 44 2B C1 44 89 45 48, 10 bytes;
    # BG `and eax, 0x10; sub [rbp-0x18], eax`). The SDL_Rect area is at [rbp+0x40] (x r9d / y r10d / w r8d stored at
    # +0x40 / +0x44 / +0x48, PT 0x4504a3 / 0x450488 / 0x4504d5). rdx (scrollbar bam, PT 0x4504c0) is read right after
    # the site (PT 0x4504d9 test rdx, rdx; 0x4504de cmp [r13+0x1a0], rdx): the hook keeps it. EEex.dll's
    # Menu_Hook_CheckApplyTextScrollbarPad subtracts BG's 16 (+ extra pad): the hook adds Torment's 2 extra pixels
    # whenever the pad was applied.
    ('''	-- v2.6 and v2.7 store the UI item's SDL_Rect area in different stack locations.
	-- Have to look up the offset dynamically by parsing a surrounding instruction.
	local paddingHookStart = EEex_Label("Hook-drawItem()-CheckApplyTextHardcodedScrollbarPad")

	if EEex_ReadU8(paddingHookStart + 0x3) ~= 0x29 or EEex_ReadU8(paddingHookStart + 0x4) ~= 0x45 then
		EEex_Error("Unexpected instruction when reading stack offset for [Hook-drawItem()-CheckApplyTextHardcodedScrollbarPad]")
	end

	local itemAreaOffsetFromRbp = EEex_Read8(paddingHookStart + 0x5) - EEex_OffsetOf("SDL_Rect.w")

	EEex_HookNOPsWithLabels(paddingHookStart, 1, {
		{"hook_integrity_watchdog_ignore_registers", {
			EEex_HookIntegrityWatchdogRegister.RAX, EEex_HookIntegrityWatchdogRegister.RCX, EEex_HookIntegrityWatchdogRegister.RDX,
			EEex_HookIntegrityWatchdogRegister.R8, EEex_HookIntegrityWatchdogRegister.R9, EEex_HookIntegrityWatchdogRegister.R10,
			EEex_HookIntegrityWatchdogRegister.R11
		}}},
		{[[
			mov rcx, r15                                                      ; pItem
			lea rdx, qword ptr ss:[rbp+#$(1)] ]], {itemAreaOffsetFromRbp}, [[ ; pItemArea
			call #L(EEex::Menu_Hook_CheckApplyTextScrollbarPad)
		]]}
	)''',
     '''	-- EEex-PSTEE: Torment applies an 18-pixel pad to the width kept in r8d, then stores it:
	-- and ecx, 0x12; sub r8d, ecx; mov dword ptr [rbp+0x48], r8d (83 E1 12 44 2B C1 44 89 45 48)
	local paddingHookStart = EEex_Label("Hook-drawItem()-CheckApplyTextHardcodedScrollbarPad")

	for i, expectedByte in ipairs({0x83, 0xE1, 0x12, 0x44, 0x2B, 0xC1, 0x44, 0x89, 0x45}) do
		if EEex_ReadU8(paddingHookStart + i - 1) ~= expectedByte then
			EEex_Error("Unexpected instruction when reading stack offset for [Hook-drawItem()-CheckApplyTextHardcodedScrollbarPad] (EEex-PSTEE)")
		end
	end

	local itemAreaWOffsetFromRbp = EEex_Read8(paddingHookStart + 0x9)
	local itemAreaOffsetFromRbp = itemAreaWOffsetFromRbp - EEex_OffsetOf("SDL_Rect.w")

	EEex_HookNOPsWithLabels(paddingHookStart, 5, {
		{"hook_integrity_watchdog_ignore_registers", {
			EEex_HookIntegrityWatchdogRegister.RAX, EEex_HookIntegrityWatchdogRegister.RCX,
			EEex_HookIntegrityWatchdogRegister.R8, EEex_HookIntegrityWatchdogRegister.R9, EEex_HookIntegrityWatchdogRegister.R10,
			EEex_HookIntegrityWatchdogRegister.R11
		}}},
		{[[
			#MAKE_SHADOW_SPACE(16)
			mov qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-8)], rdx                     ; scrollbar bam, tested after the site
			mov dword ptr ss:[rbp+#$(1)], r8d ]], {itemAreaWOffsetFromRbp}, [[ ; area.w without the pad
			mov dword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-16)], r8d
			mov rcx, r13                                                             ; pItem
			lea rdx, qword ptr ss:[rbp+#$(1)] ]], {itemAreaOffsetFromRbp}, [[ ; pItemArea
			call #L(EEex::Menu_Hook_CheckApplyTextScrollbarPad)
			mov eax, dword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-16)]
			cmp eax, dword ptr ss:[rbp+#$(1)] ]], {itemAreaWOffsetFromRbp}, [[ ; pad applied?
			je pstee_no_pad
			sub dword ptr ss:[rbp+#$(1)], 2 ]], {itemAreaWOffsetFromRbp}, [[ ; Torment's pad is 18, EEex.dll applies 16
			pstee_no_pad:
			mov rdx, qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-8)]
			#DESTROY_SHADOW_SPACE
		]]}
	)'''),
]
