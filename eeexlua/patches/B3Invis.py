# B3Invis.lua: CGameSprite::IsOver / RenderMarkers / Render invisibility checks.
# Reviewed without a change: IsOver()-B3Invis (PT 0x3d1ab9: short jbe + the same 7-byte relocatable
# `cmp byte ptr [rbx+0x3c8d], 0`; rbx / rdi preserved, rax / rcx rewritten before use on both paths),
# Render()-B3Invis (PT 0x3dd99e: near jne + `test ecx, ecx; cmove rbx, r13` = 6 bytes; rcx / rdx saved by the hook;
# r8 / r9 / r10 / r11 / rax are rewritten before any read after the site, PT 0x3dd9b6 / 0x3dd9bb / 0x3dda50).
# Torment's RenderMarkers keeps the area pointer ([rsi+0x18]) in r8 (PT 0x3e1add mov r8, [rsi+0x18]; read after
# both hooks at PT 0x3e1be7 mov eax, [r8+0x654]), where BG keeps it in r9: the hooks must preserve r8, not r9
# (r9 is dead in Torment: next access PT 0x3e1e15 lea r9, ...).
PATCHES = [
    # Render()-B3Invis (PT 0x3dd99e): the jne is near (0F 85, 6 bytes), so the hook needs no restored bytes. With
    # upstream's 6 (`test ecx, ecx; cmove rbx, r13`), PT 0x3dd9a4 (the restored `test`) becomes a NOP, but it is the
    # target of PT 0x3dd98f jbe / 0x3dd998 je: those paths would skip the cmove and keep rbx = 0x11e0 (PT 0x3dd87b)
    # instead of the r13 stats offset (0x1e90) when [rsi+0x4bbc] == 0. Same latent bug in BG (0x36bb76 targeted by
    # 0x36bb61 / 0x36bb6a). Restore 0: the fail path returns to PT 0x3dd9a4 and runs the engine's own instructions.
    ('''		EEex_HookConditionalJumpOnSuccessWithLabels(EEex_Label("Hook-CGameSprite::Render()-B3Invis"), 6, {''',
     '''		EEex_HookConditionalJumpOnSuccessWithLabels(EEex_Label("Hook-CGameSprite::Render()-B3Invis"), 0, { -- EEex-PTEE: near jne, PT 0x3dd9a4 is a jump target'''),
    # RenderMarkers()-B3Invis1 (PT 0x3e1b2f: short jbe + 7-byte `cmp byte ptr [rsi+0x3c8d], dil`)
    ('''	EEex_HookConditionalJumpOnFailWithLabels(EEex_Label("Hook-CGameSprite::RenderMarkers()-B3Invis1"), 7, {
		{"hook_integrity_watchdog_ignore_registers", {
			EEex_HookIntegrityWatchdogRegister.RAX, EEex_HookIntegrityWatchdogRegister.RCX, EEex_HookIntegrityWatchdogRegister.RDX,
			EEex_HookIntegrityWatchdogRegister.R8, EEex_HookIntegrityWatchdogRegister.R10, EEex_HookIntegrityWatchdogRegister.R11''',
     '''	EEex_HookConditionalJumpOnFailWithLabels(EEex_Label("Hook-CGameSprite::RenderMarkers()-B3Invis1"), 7, {
		{"hook_integrity_watchdog_ignore_registers", {
			EEex_HookIntegrityWatchdogRegister.RAX, EEex_HookIntegrityWatchdogRegister.RCX, EEex_HookIntegrityWatchdogRegister.RDX,
			EEex_HookIntegrityWatchdogRegister.R9, EEex_HookIntegrityWatchdogRegister.R10, EEex_HookIntegrityWatchdogRegister.R11 -- EEex-PTEE: r8 kept, r9 dead'''),
    ('''				#MAKE_SHADOW_SPACE(40)
				mov qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-8)], r9''',
     '''				#MAKE_SHADOW_SPACE(40)
				mov qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-8)], r8 ; EEex-PTEE: Torment keeps the area in r8 (PT 0x3e1add)'''),
    ('''				mov r9, qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-8)]
				#DESTROY_SHADOW_SPACE
				jnz #L(jmp_success)''',
     '''				mov r8, qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-8)] ; EEex-PTEE: r8
				#DESTROY_SHADOW_SPACE
				jnz #L(jmp_success)'''),
    # RenderMarkers()-B3Invis2 (PT 0x3e1bb5: 6-byte relocatable `mov eax, [rcx+0xb558]`; flags of PT 0x3e1bae cmp,
    # edx = 6, rcx = game, rsi = sprite, as in BG). Only used when B3Invis_Private_RenderAsInvisible is false.
    ('''			{"hook_integrity_watchdog_ignore_registers", {
				EEex_HookIntegrityWatchdogRegister.R8, EEex_HookIntegrityWatchdogRegister.R10, EEex_HookIntegrityWatchdogRegister.R11
			}}},''',
     '''			{"hook_integrity_watchdog_ignore_registers", {
				EEex_HookIntegrityWatchdogRegister.R9, EEex_HookIntegrityWatchdogRegister.R10, EEex_HookIntegrityWatchdogRegister.R11 -- EEex-PTEE: r8 kept
			}}},'''),
    ('''					mov qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-32)], r9''',
     '''					mov qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-32)], r8 ; EEex-PTEE: Torment keeps the area in r8'''),
    ('''					mov r9, qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-32)]''',
     '''					mov r8, qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-32)] ; EEex-PTEE: r8'''),
]
