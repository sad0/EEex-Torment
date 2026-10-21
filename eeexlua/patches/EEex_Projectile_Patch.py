# EEex_Projectile_Patch.lua: Torment's CProjectile::DecodeProjectile / AddEffect (tools/hookreview.py, PT disassembly).
# - DecodeProjectile (PT 0x27c4a0) has a third argument nLevel (r8w, PT 0x27c515 movzx edi, r8w): the entry hook
#   used r8 as scratch. Its first instruction is still a 5-byte mov [rsp+0x20], rbx (relocatable).
# - DecodeProjectile LastCall (PT 0x282b85, last CString destructor before the cookie check): projectile in rsi
#   (PT 0x282b8a mov rax, rsi), frame 0x300 + 7 pushes -> return address at [rsp+0x338]. The decoder (rdx) is kept in
#   r14 (PT 0x27c4f1), but the multi-projectile loop reuses r14 as its counter (PT 0x2829c8 movzx r14d, [rbp-0x60]) and
#   Torment keeps no other copy: the entry hook stores rdx into its home slot ([entry rsp+0x10] = [rsp+0x348] in the
#   body, unused by Torment's DecodeProjectile: only [rsp+0x358] = rbx home is referenced).
# - AddEffect is virtual in Torment (vtable +0xC8, every caller uses call [rax+0xC8], no direct call): besides the base
#   CProjectile::AddEffect (PT 0x279a80, same 8 bytes as BG) CProjectileArea (PT 0x279aa0) and CProjectileBAM
#   (PT 0x279b20, inherited by every BAM-derived class) override it (Torment-only opcode 0x16c timing-2 case, else the
#   base body). The 80 projectile vtables of Torment use one of these three. All three are hooked; they start with
#   movzx eax, [rcx+0x60] / add rcx, 0x78 (8 bytes) or cmp dword ptr [rdx+0x10], 0x16c (7 bytes), relocatable; the
#   overrides write r8 / r9 / rax before reading them.
# - getAddEffectAIBase: every Data-...-CProjectile::AddEffect()-RetPtr label is the return address of a
#   call [rax+0xC8] in the equivalent Torment function, with the source object in the same register as BG: rbx
#   (ForceSpell PT 0x17f999, ForceSpellPoint 0x1819f9, Spell 0x42c099, SpellPoint 0x42f7aa, Swing 0x433522, UseItem
#   0x4366c5, UseItemPoint 0x437bcc; only epilogue reloads / error-return movzx later), r14 (FireSpell 0x17daba,
#   FireSpellPoint 0x17e8e1), rbp (FireItem 0x17d3f8), rsi (FireItemPoint 0x17d780), r15 (CBounceList::Add 0x159d1c,
#   identical code). CGameEffect::FireSpell (PT 0x204cc0) has the same prologue (4 pushes, lea rbp, [rsp-0x2f]) and
#   reads the source id from the same [rbp+0x7f]; CGameObjectArray::GetShare (PT 0x2db2d0) has the same signature.
#   FireSpellPoint RetPtr and RetPtr-2 are both PT 0x17eeeb (Torment tail-merges the two calls).
PATCHES = [
    # DecodeProjectile entry: keep nLevel (r8) and store pDecoder in its home slot for the LastCall hook
    ('''		{"hook_integrity_watchdog_ignore_registers", {
			EEex_HookIntegrityWatchdogRegister.RAX, EEex_HookIntegrityWatchdogRegister.R8, EEex_HookIntegrityWatchdogRegister.R9,
			EEex_HookIntegrityWatchdogRegister.R10, EEex_HookIntegrityWatchdogRegister.R11
		}},
		{"manual_hook_integrity_exit", true}},
		{[[
			#MAKE_SHADOW_SPACE(16)
			mov qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-8)], rcx
			mov qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-16)], rdx
''',
     '''		{"hook_integrity_watchdog_ignore_registers", {
			EEex_HookIntegrityWatchdogRegister.RAX, EEex_HookIntegrityWatchdogRegister.R9, -- EEex-PTEE: r8 (nLevel) is preserved
			EEex_HookIntegrityWatchdogRegister.R10, EEex_HookIntegrityWatchdogRegister.R11
		}},
		{"manual_hook_integrity_exit", true}},
		{[[
			#MAKE_SHADOW_SPACE(24)
			mov qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-8)], rcx
			mov qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-16)], rdx
			mov qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-24)], r8 ; EEex-PTEE: Torment third argument (nLevel, r8w)
			mov qword ptr ss:[rsp+#LAST_FRAME_TOP(16)], rdx      ; EEex-PTEE: pDecoder into its home slot, read by the LastCall hook
'''),
    ('''			mov cx, ax ; Override projectile type

			mov rdx, qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-16)]''',
     '''			mov cx, ax ; Override projectile type

			mov r8, qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-24)] ; EEex-PTEE: nLevel
			mov rdx, qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-16)]'''),
    ('''			#RESUME_SHADOW_ENTRY
			mov rdx, qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-16)]
			mov rcx, qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-8)]
			#DESTROY_SHADOW_SPACE
			#MANUAL_HOOK_EXIT(0)''',
     '''			#RESUME_SHADOW_ENTRY
			mov r8, qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-24)] ; EEex-PTEE: nLevel
			mov rdx, qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-16)]
			mov rcx, qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-8)]
			#DESTROY_SHADOW_SPACE
			#MANUAL_HOOK_EXIT(0)'''),
    ('''		EEex_HookIntegrityWatchdogRegister.RAX, EEex_HookIntegrityWatchdogRegister.RCX, EEex_HookIntegrityWatchdogRegister.R8,
		EEex_HookIntegrityWatchdogRegister.R9, EEex_HookIntegrityWatchdogRegister.R10, EEex_HookIntegrityWatchdogRegister.R11
	})''',
     '''		EEex_HookIntegrityWatchdogRegister.RAX, EEex_HookIntegrityWatchdogRegister.RCX, -- EEex-PTEE: r8 (nLevel) is preserved
		EEex_HookIntegrityWatchdogRegister.R9, EEex_HookIntegrityWatchdogRegister.R10, EEex_HookIntegrityWatchdogRegister.R11
	})'''),
    # DecodeProjectile LastCall (PT 0x282b85)
    ('''			mov r8, qword ptr ss:[rsp+408]               ; pRetPtr
			mov rdx, rsi                                 ; pDecoder
			mov rcx, rbx                                 ; pProjectile''',
     '''			mov r8, qword ptr ss:[rsp+824]               ; pRetPtr     ; EEex-PTEE: frame 0x300 + 7 pushes (PT 0x27c4a5..0x27c4b8)
			mov rdx, qword ptr ss:[rsp+840]              ; pDecoder    ; EEex-PTEE: home slot written by the entry hook (r14 is reused, PT 0x2829c8)
			mov rcx, rsi                                 ; pProjectile ; EEex-PTEE: rsi (PT 0x282b8a mov rax, rsi)'''),
    # AddEffect: hook the base function and Torment's two overrides (vtable slot +0xC8)
    ('''	EEex_HookBeforeRestoreWithLabels(EEex_Label("CProjectile::AddEffect"), 0, 8, 8, {''',
     '''	-- EEex-PTEE: AddEffect is virtual in Torment; CProjectileArea / CProjectileBAM (and every BAM-derived class)
	-- override it (PT 0x279aa0 / 0x279b20): hook all three bodies, entered directly by the callers' call [rax+0xC8].
	local ptAddEffectHooked = {}
	for _, ptAddEffect in ipairs({
		{EEex_Label("CProjectile::AddEffect"),                         8, 0x0F}, -- movzx eax, word ptr [rcx+0x60]; add rcx, 0x78
		{EEex_ReadPtr(EEex_Label("CProjectileArea::VFTable") + 0xC8), 7, 0x81}, -- cmp dword ptr [rdx+0x10], 0x16C
		{EEex_ReadPtr(EEex_Label("CProjectileBAM::VFTable") + 0xC8),  7, 0x81}, -- cmp dword ptr [rdx+0x10], 0x16C
	})
	do
	if not ptAddEffectHooked[ptAddEffect[1]] then
	ptAddEffectHooked[ptAddEffect[1]] = true
	if EEex_ReadU8(ptAddEffect[1]) ~= ptAddEffect[3] then
		EEex_Error("[EEex-PTEE] Unexpected CProjectile::AddEffect body at "..EEex_ToHex(ptAddEffect[1]))
	end
	EEex_HookBeforeRestoreWithLabels(ptAddEffect[1], 0, ptAddEffect[2], ptAddEffect[2], {'''),
    ('''			mov rdx, qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-16)]
			mov rcx, qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-8)]
			#DESTROY_SHADOW_SPACE
		]]}
	)

	EEex_EnableCodeProtection()''',
     '''			mov rdx, qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-16)]
			mov rcx, qword ptr ss:[rsp+#SHADOW_SPACE_BOTTOM(-8)]
			#DESTROY_SHADOW_SPACE
		]]}
	)
	end
	end -- EEex-PTEE: AddEffect bodies

	EEex_EnableCodeProtection()'''),
]
