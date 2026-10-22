# EEex_UncapFPS_Patch.lua: Torment instruction layouts at three hook sites (phase 4d, tested in game through
# bindings/test/make_uncap_test.py; same changes here, without the test header/tail).
# Reviewed hooks without a change (eeexlua/notes/EEex_UncapFPS_Patch.md): every FirstInstruction JIT override
# (PT function starts, no branch into the patched head), drawTop fade jle (near, identical block PT 0x4521f3),
# OnMouseMove edge-scroll (rbx = CGameArea, PT 0x19d825), EngineDeactivated first call (no-argument
# function PT 0x4585f0), OnDeactivation (same 6 prologue bytes, rcx = pArea), screen-shake jne (near,
# rbx = CInfinity in PT helper 0x3078c0), DrawInit (al), SynchronousUpdate Flip tail jmp (5 bytes, PT 0x4a62b2).
PATCHES = [
    # CScreenWorld::OnEvent: Torment's middle-mouse check is a short je (PT 0x35ba0a, 2 bytes; BG near je, 6 bytes):
    # restore the next instruction `add rbx, 0x5d8` (PT 0x35ba0c, 7 bytes, relocatable). pEvent stays in rdi
    # (PT 0x35ba4b add r8d, [rdi+0x1c]).
    ('EEex_HookConditionalJumpOnFailWithLabels(EEex_Label("Hook-CScreenWorld::OnEvent()-OnHandleMiddleMouseDragJmp"), 0, {',
     'EEex_HookConditionalJumpOnFailWithLabels(EEex_Label("Hook-CScreenWorld::OnEvent()-OnHandleMiddleMouseDragJmp"), 7, { -- EEex-PSTEE: short je, restore add rbx, 0x5d8'),
    # Screen-shake post block (Torment helper PT 0x307a50): the jne is near (PT 0x307a88, 6 bytes; BG short jne +
    # 3 restored bytes): nothing to restore. pInfinity in rbx (PT 0x307a5d mov rbx, rcx); jmp_success = the
    # helper's epilogue (PT 0x307b0e), whose caller (PT 0x19efd6) does not use rax.
    ('EEex_HookConditionalJumpOnFailWithLabels(EEex_Label("Hook-CInfinity::Render()-HandleScreenShakePostJmp"), 3, {',
     'EEex_HookConditionalJumpOnFailWithLabels(EEex_Label("Hook-CInfinity::Render()-HandleScreenShakePostJmp"), 0, { -- EEex-PSTEE: near jne'),
    # CGameArea::OnActivation: BG tail-jumps to CScreenMap's area-activated handler (jmp, pArea in rdx); Torment
    # calls it (PT 0x19d3ca call 0x33c6e0) and keeps pArea in rdi (callee-saved, PT 0x19d3c0 mov rdx, rdi,
    # still read at PT 0x19d3d4). Volatile registers are dead after the call (PT 0x19d3cf..0x19d42b write them
    # before any read; rax unused).
    ('''	EEex_HookRelativeJumpWithLabels(EEex_Label("Hook-CGameArea::OnActivation()-LastCall"), {
		{"stack_mod", 8},
		{"hook_integrity_watchdog_ignore_registers", {
			EEex_HookIntegrityWatchdogRegister.RAX, EEex_HookIntegrityWatchdogRegister.RCX, EEex_HookIntegrityWatchdogRegister.RDX,
			EEex_HookIntegrityWatchdogRegister.R8, EEex_HookIntegrityWatchdogRegister.R9, EEex_HookIntegrityWatchdogRegister.R10,
			EEex_HookIntegrityWatchdogRegister.R11
		}},
		{"manual_continue", true}},
		{[[
			#MAKE_SHADOW_SPACE(8)
			mov qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-8)], rdx

			call #L(original)

			mov rcx, qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-8)] ; pArea
			call #L(EEex::UncapFPS_Hook_OnAfterAreaActivated)

			#DESTROY_SHADOW_SPACE
			#MANUAL_HOOK_EXIT(0)
			ret
		]]}
	)''',
     '''	-- EEex-PSTEE: Torment calls the map engine (no tail jump) and keeps pArea in rdi
	EEex_HookAfterCallWithLabels(EEex_Label("Hook-CGameArea::OnActivation()-LastCall"), {
		{"hook_integrity_watchdog_ignore_registers", {
			EEex_HookIntegrityWatchdogRegister.RAX, EEex_HookIntegrityWatchdogRegister.RCX, EEex_HookIntegrityWatchdogRegister.RDX,
			EEex_HookIntegrityWatchdogRegister.R8, EEex_HookIntegrityWatchdogRegister.R9, EEex_HookIntegrityWatchdogRegister.R10,
			EEex_HookIntegrityWatchdogRegister.R11
		}}},
		{[[
			mov rcx, rdi ; EEex-PSTEE: pArea in rdi
			call #L(EEex::UncapFPS_Hook_OnAfterAreaActivated)
		]]}
	)'''),
]
