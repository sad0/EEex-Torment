# EEex_Stats_Patch.lua: Torment code layout at the hook sites (tools/hookreview.py, notes/EEex_Stats_Patch.md).
# Reviewed hooks without a change: CDerivedStats::Construct FirstCall (rsi = this, PT 0x15c001), Destruct FirstCall
# (rdi = this, PT 0x1bb9df), QuickLoad Reload (rdi = sprite, PT 0x3d9dc4 mov rcx, rdi; stats at sprite+0xfe8),
# Unmarshal Reload-1/-2 (rbx = sprite, PT 0x3edfc2 lea r12, [rbx+0xfe8] / 0x3ee6ad lea r9, [rbx+0xb78]),
# ProcessEffectList Reload (rsi = sprite, PT 0x423d33 lea rcx, [rsi+0xfe8]), operator= FirstCall (r14 = this,
# rsi = other: PT 0x15c67e / 0x15c683), operator+= FirstCall (rbx = this, rdi = other: PT 0x15d593 / 0x15d59a;
# first call of both functions), GetSpellState / SetSpellState JITs (whole functions replaced, >= 5 bytes).
PATCHES = [
    # CDerivedStats::GetAtOffset (PT 0x15f1f0): Torment's version opens a 0x38-byte frame before the bounds check
    # (sub rsp, 0x38; movsx eax, dx; dec eax; cmp eax, 0xc9; ja 0x15fb55), BG's has none. The hook site is therefore
    # 16-byte aligned (no stack_mod) and the early `ret` must drop the frame first (PT 0x15fb57 add rsp, 0x38; ret).
    # rax = id - 1 and rcx = this as in BG; same bound 0xc9 (engine stats 1..202).
    ('''	EEex_HookConditionalJumpOnSuccessWithLabels(EEex_Label("Hook-CDerivedStats::GetAtOffset()-OutOfBoundsJmp"), 0, {
		{"stack_mod", 8},''',
     '''	EEex_HookConditionalJumpOnSuccessWithLabels(EEex_Label("Hook-CDerivedStats::GetAtOffset()-OutOfBoundsJmp"), 0, {
		-- EEex-PSTEE: no stack_mod, Torment's GetAtOffset already did sub rsp, 38h (site 16-byte aligned)'''),
    ('''				#DESTROY_SHADOW_SPACE
				#MANUAL_HOOK_EXIT(0)
				ret''',
     '''				#DESTROY_SHADOW_SPACE
				#MANUAL_HOOK_EXIT(0)
				add rsp, 38h ; EEex-PSTEE: Torment's GetAtOffset frame (PT 0x15fb57)
				ret'''),
    # Torment has a 5th CDerivedStats::Reload caller that BG lacks: a Torment-only sprite routine reached from
    # CGameAIBase::ExecuteAction (PT 0x1711cb -> 0x173c00), call at PT 0x17421e with the sprite in r15
    # (PT 0x174217 lea rcx, [r15+0xfe8]; 0x174229 mov rcx, r15). Label in the version
    # extra DB (tools/port_extra.py, poc/extra_pattern_dbs/pstee.db).
    ('''	EEex_HookAfterCallWithLabels(EEex_Label("Hook-CGameSprite::ProcessEffectList()-CDerivedStats::Reload()"), {
		{"hook_integrity_watchdog_ignore_registers", {EEex_HookIntegrityWatchdogRegister.RAX}}},
		statsReloadTemplate("rsi")
	)''',
     '''	EEex_HookAfterCallWithLabels(EEex_Label("Hook-CGameSprite::ProcessEffectList()-CDerivedStats::Reload()"), {
		{"hook_integrity_watchdog_ignore_registers", {EEex_HookIntegrityWatchdogRegister.RAX}}},
		statsReloadTemplate("rsi")
	)

	-- EEex-PSTEE: Torment-only CDerivedStats::Reload() call (PT 0x17421e, sprite in r15)
	EEex_HookAfterCallWithLabels(EEex_Label("Hook-PSTEE-ExecuteActionHelper()-CDerivedStats::Reload()"), {
		{"hook_integrity_watchdog_ignore_registers", {EEex_HookIntegrityWatchdogRegister.RAX}}},
		statsReloadTemplate("r15")
	)'''),
]
